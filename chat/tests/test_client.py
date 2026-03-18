"""Tests for chat.client module."""

import httpx
import pytest
import respx

from chat.client import OllamaClient
from chat.exceptions import (
    OllamaConnectionError,
    OllamaError,
    OllamaModelNotFoundError,
)

BASE_URL = "http://localhost:11434"


# ---------------------------------------------------------------------------
# TestHealthCheck
# ---------------------------------------------------------------------------
class TestHealthCheck:
    @respx.mock
    async def test_returns_true_when_ollama_responds(self) -> None:
        respx.get(f"{BASE_URL}/").mock(return_value=httpx.Response(200, text="Ollama is running"))
        async with OllamaClient(BASE_URL) as client:
            assert await client.health_check() is True

    @respx.mock
    async def test_returns_false_on_connection_refused(self) -> None:
        respx.get(f"{BASE_URL}/").mock(side_effect=httpx.ConnectError("refused"))
        async with OllamaClient(BASE_URL) as client:
            assert await client.health_check() is False

    @respx.mock
    async def test_returns_false_on_timeout(self) -> None:
        respx.get(f"{BASE_URL}/").mock(side_effect=httpx.TimeoutException("timeout"))
        async with OllamaClient(BASE_URL) as client:
            assert await client.health_check() is False

    @respx.mock
    async def test_returns_false_on_non_200(self) -> None:
        respx.get(f"{BASE_URL}/").mock(return_value=httpx.Response(500))
        async with OllamaClient(BASE_URL) as client:
            assert await client.health_check() is False


# ---------------------------------------------------------------------------
# TestListModels
# ---------------------------------------------------------------------------
class TestListModels:
    @respx.mock
    async def test_returns_parsed_model_list(self) -> None:
        models_payload = {
            "models": [
                {"name": "llama3.2", "size": 2_000_000_000},
                {"name": "mistral", "size": 4_000_000_000},
            ]
        }
        respx.get(f"{BASE_URL}/api/tags").mock(
            return_value=httpx.Response(200, json=models_payload)
        )
        async with OllamaClient(BASE_URL) as client:
            result = await client.list_models()
        assert len(result) == 2
        assert result[0]["name"] == "llama3.2"
        assert result[1]["name"] == "mistral"

    @respx.mock
    async def test_returns_empty_list_when_no_models_key(self) -> None:
        respx.get(f"{BASE_URL}/api/tags").mock(return_value=httpx.Response(200, json={}))
        async with OllamaClient(BASE_URL) as client:
            result = await client.list_models()
        assert result == []

    @respx.mock
    async def test_raises_ollama_connection_error_when_unreachable(self) -> None:
        respx.get(f"{BASE_URL}/api/tags").mock(side_effect=httpx.ConnectError("refused"))
        async with OllamaClient(BASE_URL) as client:
            with pytest.raises(OllamaConnectionError):
                await client.list_models()

    @respx.mock
    async def test_raises_ollama_connection_error_on_server_error(self) -> None:
        respx.get(f"{BASE_URL}/api/tags").mock(return_value=httpx.Response(503))
        async with OllamaClient(BASE_URL) as client:
            with pytest.raises(OllamaConnectionError):
                await client.list_models()


# ---------------------------------------------------------------------------
# TestChatStream
# ---------------------------------------------------------------------------


def _ndjson(*chunks: dict) -> str:
    """Build a newline-delimited JSON string from dicts."""
    import json

    return "\n".join(json.dumps(c) for c in chunks) + "\n"


SAMPLE_STREAM = _ndjson(
    {"message": {"role": "assistant", "content": "Hello"}, "done": False},
    {"message": {"role": "assistant", "content": " world"}, "done": False},
    {"message": {"role": "assistant", "content": "!"}, "done": True},
)

MESSAGES: list[dict[str, str]] = [{"role": "user", "content": "Hi"}]


class TestChatStream:
    @respx.mock
    async def test_yields_tokens_from_ndjson_stream(self) -> None:
        respx.post(f"{BASE_URL}/api/chat").mock(
            return_value=httpx.Response(200, text=SAMPLE_STREAM)
        )
        async with OllamaClient(BASE_URL) as client:
            tokens = [t async for t in client.chat_stream("llama3.2", MESSAGES)]
        assert tokens == ["Hello", " world", "!"]

    @respx.mock
    async def test_raises_model_not_found_on_404(self) -> None:
        respx.post(f"{BASE_URL}/api/chat").mock(return_value=httpx.Response(404))
        async with OllamaClient(BASE_URL) as client:
            with pytest.raises(OllamaModelNotFoundError) as exc_info:
                async for _ in client.chat_stream("ghost-model", MESSAGES):
                    pass
        assert exc_info.value.model == "ghost-model"

    @respx.mock
    async def test_raises_stream_error_on_mid_stream_disconnect(self) -> None:
        respx.post(f"{BASE_URL}/api/chat").mock(side_effect=httpx.ReadError("mid-stream failure"))
        async with OllamaClient(BASE_URL) as client:
            with pytest.raises(OllamaError):
                async for _ in client.chat_stream("llama3.2", MESSAGES):
                    pass

    @respx.mock
    async def test_sends_correct_request_body(self) -> None:
        import json as _json

        respx.post(f"{BASE_URL}/api/chat").mock(
            return_value=httpx.Response(
                200,
                text=_ndjson({"message": {"role": "assistant", "content": "ok"}, "done": True}),
            )
        )
        async with OllamaClient(BASE_URL) as client:
            async for _ in client.chat_stream("mistral", MESSAGES):
                pass

        request = respx.calls.last.request
        body = _json.loads(request.content)
        assert body["model"] == "mistral"
        assert body["messages"] == MESSAGES
        assert body["stream"] is True

    @respx.mock
    async def test_raises_connection_error_when_unreachable(self) -> None:
        respx.post(f"{BASE_URL}/api/chat").mock(side_effect=httpx.ConnectError("refused"))
        async with OllamaClient(BASE_URL) as client:
            with pytest.raises(OllamaConnectionError):
                async for _ in client.chat_stream("llama3.2", MESSAGES):
                    pass


# ---------------------------------------------------------------------------
# TestClientLifecycle
# ---------------------------------------------------------------------------
class TestClientLifecycle:
    @respx.mock
    async def test_context_manager_opens_and_closes(self) -> None:
        respx.get(f"{BASE_URL}/").mock(return_value=httpx.Response(200, text="Ollama is running"))
        async with OllamaClient(BASE_URL) as client:
            assert await client.health_check() is True
        # After exiting context, the underlying httpx client should be closed
        assert client._client.is_closed

    async def test_explicit_close_closes_client(self) -> None:
        client = OllamaClient(BASE_URL)
        assert not client._client.is_closed
        await client.close()
        assert client._client.is_closed
