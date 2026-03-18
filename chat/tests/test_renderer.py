"""Tests for chat.renderer module."""

from io import StringIO

from rich.console import Console

from chat.renderer import Renderer


def _make_renderer() -> tuple[Renderer, StringIO]:
    """Return a Renderer wired to an in-memory StringIO console."""
    buf = StringIO()
    console = Console(file=buf, highlight=False, markup=True)
    return Renderer(console=console), buf


# ---------------------------------------------------------------------------
# TestWelcomeBanner
# ---------------------------------------------------------------------------
class TestWelcomeBanner:
    def test_contains_model_name(self) -> None:
        renderer, buf = _make_renderer()
        renderer.welcome_banner("llama3.2")
        output = buf.getvalue()
        assert "llama3.2" in output

    def test_contains_help_hint(self) -> None:
        renderer, buf = _make_renderer()
        renderer.welcome_banner("llama3.2")
        output = buf.getvalue()
        assert "/help" in output

    def test_contains_welcome_title(self) -> None:
        renderer, buf = _make_renderer()
        renderer.welcome_banner("mistral")
        output = buf.getvalue()
        assert "Welcome" in output


# ---------------------------------------------------------------------------
# TestAssistantLabel
# ---------------------------------------------------------------------------
class TestAssistantLabel:
    def test_label_contains_assistant(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_assistant_label()
        assert "Assistant" in buf.getvalue()

    def test_label_does_not_end_with_newline(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_assistant_label()
        assert not buf.getvalue().endswith("\n")


# ---------------------------------------------------------------------------
# TestStreamingResponse
# ---------------------------------------------------------------------------
class TestStreamingResponse:
    def test_token_appears_in_output(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_streaming_response("hello")
        assert "hello" in buf.getvalue()

    def test_no_trailing_newline_after_single_token(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_streaming_response("hello")
        assert not buf.getvalue().endswith("\n")

    def test_multiple_tokens_concatenated(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_streaming_response("Hello")
        renderer.render_streaming_response(", ")
        renderer.render_streaming_response("world")
        output = buf.getvalue()
        assert "Hello" in output
        assert "world" in output


# ---------------------------------------------------------------------------
# TestFinalizeResponse
# ---------------------------------------------------------------------------
class TestFinalizeResponse:
    def test_adds_trailing_newline(self) -> None:
        renderer, buf = _make_renderer()
        renderer.finalize_response("anything")
        assert buf.getvalue().endswith("\n")

    def test_does_not_reprint_streamed_text(self) -> None:
        """Regression: response must not appear twice (once streamed, once finalised)."""
        renderer, buf = _make_renderer()
        renderer.render_streaming_response("Hello world")
        renderer.finalize_response("Hello world")
        output = buf.getvalue()
        assert output.count("Hello world") == 1


# ---------------------------------------------------------------------------
# TestRenderError
# ---------------------------------------------------------------------------
class TestRenderError:
    def test_error_message_appears(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_error("something went wrong")
        assert "something went wrong" in buf.getvalue()

    def test_error_label_appears(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_error("oops")
        assert "Error" in buf.getvalue()


# ---------------------------------------------------------------------------
# TestRenderModelsList
# ---------------------------------------------------------------------------
class TestRenderModelsList:
    def test_table_contains_model_names(self) -> None:
        renderer, buf = _make_renderer()
        models = [
            {"name": "llama3.2", "size": 2_000_000_000},
            {"name": "mistral", "size": 4_000_000_000},
        ]
        renderer.render_models_list(models)
        output = buf.getvalue()
        assert "llama3.2" in output
        assert "mistral" in output

    def test_handles_empty_list(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_models_list([])
        output = buf.getvalue()
        assert "No models" in output

    def test_table_contains_size_column(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_models_list([{"name": "llama3.2", "size": 1_073_741_824}])
        output = buf.getvalue()
        assert "Size" in output


# ---------------------------------------------------------------------------
# TestRenderHelp
# ---------------------------------------------------------------------------
class TestRenderHelp:
    def test_lists_exit_command(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_help()
        assert "/exit" in buf.getvalue()

    def test_lists_help_command(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_help()
        assert "/help" in buf.getvalue()

    def test_lists_clear_command(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_help()
        assert "/clear" in buf.getvalue()

    def test_lists_models_command(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_help()
        assert "/models" in buf.getvalue()

    def test_lists_model_switch_command(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_help()
        assert "/model" in buf.getvalue()


# ---------------------------------------------------------------------------
# TestRenderGoodbye
# ---------------------------------------------------------------------------
class TestRenderGoodbye:
    def test_goodbye_message_appears(self) -> None:
        renderer, buf = _make_renderer()
        renderer.render_goodbye()
        assert "Goodbye" in buf.getvalue()
