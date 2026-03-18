"""Tests for chat.repl module."""

from unittest.mock import AsyncMock, MagicMock, patch

from chat.client import OllamaClient
from chat.exceptions import OllamaConnectionError, OllamaModelNotFoundError, OllamaStreamError
from chat.renderer import Renderer
from chat.repl import ChatREPL


def _make_repl(model: str = "llama3.2") -> tuple[ChatREPL, MagicMock, MagicMock]:
    """Return a (ChatREPL, client_mock, renderer_mock) triple."""
    client = MagicMock(spec=OllamaClient)
    renderer = MagicMock(spec=Renderer)
    repl = ChatREPL(client=client, renderer=renderer, model=model)
    return repl, client, renderer


def _async_gen(*tokens: str):
    """Return an async generator function that yields the given tokens."""

    async def _gen(*_args, **_kwargs):
        for token in tokens:
            yield token

    return _gen


def _raising_gen(exc: BaseException, *prefix_tokens: str):
    """Return an async generator that yields prefix tokens then raises exc."""

    async def _gen(*_args, **_kwargs):
        for token in prefix_tokens:
            yield token
        raise exc

    return _gen


# ---------------------------------------------------------------------------
# TestHandleInput
# ---------------------------------------------------------------------------
class TestHandleInput:
    async def test_empty_input_returns_true(self) -> None:
        repl, _, _ = _make_repl()
        assert await repl.handle_input("") is True

    async def test_slash_command_is_dispatched(self) -> None:
        repl, _, renderer = _make_repl()
        result = await repl.handle_input("/help")
        renderer.render_help.assert_called_once()
        assert result is True

    async def test_regular_text_goes_to_handle_chat(self) -> None:
        repl, client, renderer = _make_repl()
        client.chat_stream = _async_gen("Hi!")
        await repl.handle_input("hello")
        renderer.render_streaming_response.assert_called_once_with("Hi!")

    async def test_quit_returns_false(self) -> None:
        repl, _, renderer = _make_repl()
        assert await repl.handle_input("quit") is False
        renderer.render_goodbye.assert_called_once()

    async def test_quit_case_insensitive(self) -> None:
        repl, _, _ = _make_repl()
        assert await repl.handle_input("QUIT") is False


# ---------------------------------------------------------------------------
# TestHandleChat
# ---------------------------------------------------------------------------
class TestHandleChat:
    async def test_user_message_added_to_conversation(self) -> None:
        repl, client, _ = _make_repl()
        client.chat_stream = _async_gen()
        await repl.handle_chat("hello")
        assert repl._conversation.get_history()[0] == {"role": "user", "content": "hello"}

    async def test_chat_stream_called_with_correct_history(self) -> None:
        repl, client, _ = _make_repl()
        captured: list[tuple[str, list]] = []

        async def _capture(model: str, messages: list, **_kwargs):
            captured.append((model, messages))
            yield "ok"

        client.chat_stream = _capture
        await repl.handle_chat("ping")
        assert captured[0][0] == "llama3.2"
        assert captured[0][1][0] == {"role": "user", "content": "ping"}

    async def test_assistant_response_added_to_conversation(self) -> None:
        repl, client, _ = _make_repl()
        client.chat_stream = _async_gen("Hello", " world")
        await repl.handle_chat("hi")
        history = repl._conversation.get_history()
        assert history[-1] == {"role": "assistant", "content": "Hello world"}

    async def test_streaming_tokens_passed_to_renderer(self) -> None:
        repl, client, renderer = _make_repl()
        client.chat_stream = _async_gen("A", "B", "C")
        await repl.handle_chat("hi")
        assert renderer.render_streaming_response.call_count == 3

    async def test_finalize_called_with_full_text(self) -> None:
        repl, client, renderer = _make_repl()
        client.chat_stream = _async_gen("Hello", " world")
        await repl.handle_chat("hi")
        renderer.finalize_response.assert_called_once_with("Hello world")

    async def test_assistant_label_rendered_before_streaming(self) -> None:
        repl, client, renderer = _make_repl()
        call_order: list[str] = []
        renderer.render_assistant_label.side_effect = lambda: call_order.append("label")
        renderer.render_streaming_response.side_effect = lambda t: call_order.append(f"token:{t}")
        client.chat_stream = _async_gen("Hi")
        await repl.handle_chat("hello")
        assert call_order[0] == "label"
        assert call_order[1] == "token:Hi"


# ---------------------------------------------------------------------------
# TestSlashCommands
# ---------------------------------------------------------------------------
class TestSlashCommands:
    async def test_help_calls_render_help(self) -> None:
        repl, _, renderer = _make_repl()
        result = await repl.handle_slash_command("/help")
        renderer.render_help.assert_called_once()
        assert result is True

    async def test_exit_returns_false(self) -> None:
        repl, _, renderer = _make_repl()
        result = await repl.handle_slash_command("/exit")
        renderer.render_goodbye.assert_called_once()
        assert result is False

    async def test_clear_resets_conversation_and_screen(self) -> None:
        repl, _, renderer = _make_repl()
        repl._conversation.add_message("user", "test")
        result = await repl.handle_slash_command("/clear")
        assert len(repl._conversation) == 0
        renderer.clear_screen.assert_called_once()
        assert result is True

    async def test_models_displays_model_list(self) -> None:
        repl, client, renderer = _make_repl()
        client.list_models = AsyncMock(return_value=[{"name": "llama3.2", "size": 1}])
        await repl.handle_slash_command("/models")
        renderer.render_models_list.assert_called_once()

    async def test_model_switch_changes_model_and_resets_history(self) -> None:
        repl, _, renderer = _make_repl()
        repl._conversation.add_message("user", "old message")
        result = await repl.handle_slash_command("/model mistral")
        assert repl._model == "mistral"
        assert len(repl._conversation) == 0
        renderer.render_info.assert_called_once()
        assert result is True

    async def test_model_without_arg_shows_error(self) -> None:
        repl, _, renderer = _make_repl()
        await repl.handle_slash_command("/model")
        renderer.render_error.assert_called_once()

    async def test_unknown_command_shows_error(self) -> None:
        repl, _, renderer = _make_repl()
        result = await repl.handle_slash_command("/unknown")
        renderer.render_error.assert_called_once()
        assert result is True

    async def test_models_shows_error_on_connection_failure(self) -> None:
        repl, client, renderer = _make_repl()
        client.list_models = AsyncMock(side_effect=OllamaConnectionError("no server"))
        await repl.handle_slash_command("/models")
        renderer.render_error.assert_called_once()


# ---------------------------------------------------------------------------
# TestQuitAndEOF
# ---------------------------------------------------------------------------
class TestQuitAndEOF:
    async def test_quit_exits(self) -> None:
        repl, _, _ = _make_repl()
        assert await repl.handle_input("quit") is False

    @patch("builtins.input", side_effect=EOFError())
    async def test_eof_exits_gracefully(self, _mock_input) -> None:
        repl, _, renderer = _make_repl()
        await repl.run()
        renderer.render_goodbye.assert_called()


# ---------------------------------------------------------------------------
# TestSignalHandling
# ---------------------------------------------------------------------------
class TestSignalHandling:
    async def test_keyboard_interrupt_during_streaming_shows_interrupted(self) -> None:
        repl, client, renderer = _make_repl()
        client.chat_stream = _raising_gen(KeyboardInterrupt(), "partial")
        await repl.handle_chat("hi")
        renderer.render_error.assert_called_once()
        assert "interrupted" in renderer.render_error.call_args[0][0].lower()

    async def test_keyboard_interrupt_during_streaming_keeps_partial_text(self) -> None:
        repl, client, _ = _make_repl()
        client.chat_stream = _raising_gen(KeyboardInterrupt(), "partial text")
        await repl.handle_chat("hi")
        history = repl._conversation.get_history()
        assert len(history) == 2
        assert history[1] == {"role": "assistant", "content": "partial text"}

    @patch("builtins.input", side_effect=[KeyboardInterrupt(), EOFError()])
    async def test_keyboard_interrupt_at_idle_shows_hint(self, _mock_input) -> None:
        repl, _, renderer = _make_repl()
        await repl.run()
        first_error = renderer.render_error.call_args_list[0][0][0]
        assert "/exit" in first_error

    @patch("builtins.input", side_effect=[KeyboardInterrupt(), EOFError()])
    async def test_keyboard_interrupt_at_idle_continues_loop(self, _mock_input) -> None:
        repl, _, renderer = _make_repl()
        await repl.run()
        # render_goodbye is called for the EOFError, not for the KeyboardInterrupt
        renderer.render_goodbye.assert_called_once()


# ---------------------------------------------------------------------------
# TestMidStreamFailure
# ---------------------------------------------------------------------------
class TestMidStreamFailure:
    async def test_stream_error_shows_inline_error(self) -> None:
        repl, client, renderer = _make_repl()
        client.chat_stream = _raising_gen(OllamaStreamError("Connection lost"), "partial")
        await repl.handle_chat("hi")
        renderer.render_error.assert_called_once()
        assert "connection" in renderer.render_error.call_args[0][0].lower()

    async def test_stream_error_partial_text_preserved_in_conversation(self) -> None:
        repl, client, _ = _make_repl()
        client.chat_stream = _raising_gen(
            OllamaStreamError("Connection lost", partial_content=""),
            "partial text",
        )
        await repl.handle_chat("hi")
        history = repl._conversation.get_history()
        assert len(history) == 2
        assert history[1]["content"] == "partial text"


# ---------------------------------------------------------------------------
# TestModelNotFound
# ---------------------------------------------------------------------------
class TestModelNotFound:
    async def test_model_not_found_shows_friendly_message(self) -> None:
        repl, client, renderer = _make_repl()
        client.chat_stream = _raising_gen(OllamaModelNotFoundError("ghost"))
        await repl.handle_chat("hi")
        renderer.render_error.assert_called_once()
        assert "ghost" in renderer.render_error.call_args[0][0]
