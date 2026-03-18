"""Ollama HTTP client — thin wrapper around the Ollama HTTP API."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from chat.exceptions import OllamaConnectionError, OllamaModelNotFoundError, OllamaStreamError


class OllamaClient:
    """Async HTTP client for the Ollama API.

    Args:
        base_url: Base URL of the Ollama server.
    """

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=60.0)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "OllamaClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    async def health_check(self) -> bool:
        """Check whether the Ollama server is reachable.

        Returns:
            True if the server responds, False otherwise.
        """
        try:
            response = await self._client.get("/")
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException, httpx.TransportError):
            return False

    async def list_models(self) -> list[dict[str, Any]]:
        """List locally available Ollama models.

        Returns:
            List of model dicts from the /api/tags endpoint.

        Raises:
            OllamaConnectionError: If the server is unreachable.
        """
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data.get("models", [])
        except (httpx.ConnectError, httpx.TimeoutException, httpx.TransportError) as exc:
            raise OllamaConnectionError("Cannot reach Ollama server.") from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaConnectionError(
                f"Unexpected response from Ollama: {exc.response.status_code}"
            ) from exc

    async def chat_stream(self, model: str, messages: list[dict[str, str]]) -> AsyncIterator[str]:
        """Stream a chat completion from Ollama.

        Args:
            model: The model name to use.
            messages: Conversation history in Ollama format.

        Yields:
            Individual token strings as they arrive.

        Raises:
            OllamaModelNotFoundError: If the model is not found (HTTP 404).
            OllamaStreamError: On mid-stream connection failures.
            OllamaConnectionError: If the server is unreachable.
        """
        payload = {"model": model, "messages": messages, "stream": True}
        try:
            async with self._client.stream("POST", "/api/chat", json=payload) as response:
                if response.status_code == 404:
                    raise OllamaModelNotFoundError(model)
                response.raise_for_status()

                try:
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        chunk: dict[str, Any] = json.loads(line)
                        token: str = chunk.get("message", {}).get("content", "")
                        if token:
                            yield token
                        if chunk.get("done"):
                            break
                except (httpx.ReadError, httpx.RemoteProtocolError) as exc:
                    raise OllamaStreamError(
                        "Connection lost during streaming.", partial_content=""
                    ) from exc

        except OllamaModelNotFoundError:
            raise
        except OllamaStreamError:
            raise
        except (httpx.ConnectError, httpx.TimeoutException, httpx.TransportError) as exc:
            raise OllamaConnectionError("Cannot reach Ollama server.") from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaStreamError(f"Unexpected HTTP error: {exc.response.status_code}") from exc
