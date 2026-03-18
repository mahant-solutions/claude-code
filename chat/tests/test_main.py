"""Tests for main module CLI entry point."""

from unittest.mock import ANY, AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from main import app

runner = CliRunner()


def _make_client_mock(healthy: bool = True) -> tuple[MagicMock, AsyncMock]:
    """Return (client_class_mock, client_instance_mock) with health_check preset."""
    mock_client = AsyncMock()
    mock_client.health_check = AsyncMock(return_value=healthy)

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_client)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_class = MagicMock(return_value=mock_ctx)
    return mock_class, mock_client


# ---------------------------------------------------------------------------
# TestCLIFlags
# ---------------------------------------------------------------------------
class TestCLIFlags:
    def test_model_flag_overrides_default(self) -> None:
        mock_client_class, mock_client = _make_client_mock()
        mock_repl = AsyncMock()

        with (
            patch("main.OllamaClient", mock_client_class),
            patch("main.ChatREPL", return_value=mock_repl) as mock_repl_class,
            patch("main.Renderer"),
            patch("main._configure_logging"),
        ):
            runner.invoke(app, ["--model", "mistral"])

        mock_repl_class.assert_called_once_with(client=mock_client, renderer=ANY, model="mistral")

    def test_host_flag_overrides_default(self) -> None:
        mock_client_class, _ = _make_client_mock()

        with (
            patch("main.OllamaClient", mock_client_class),
            patch("main.ChatREPL", return_value=AsyncMock()),
            patch("main.Renderer"),
            patch("main._configure_logging"),
        ):
            runner.invoke(app, ["--host", "http://custom:11434"])

        mock_client_class.assert_called_once_with("http://custom:11434")


# ---------------------------------------------------------------------------
# TestEnvVarFallback
# ---------------------------------------------------------------------------
class TestEnvVarFallback:
    def test_ollama_model_env_used_when_no_flag(self, monkeypatch) -> None:
        monkeypatch.setenv("OLLAMA_MODEL", "qwen3:8b")
        mock_client_class, mock_client = _make_client_mock()

        with (
            patch("main.OllamaClient", mock_client_class),
            patch("main.ChatREPL", return_value=AsyncMock()) as mock_repl_class,
            patch("main.Renderer"),
            patch("main._configure_logging"),
        ):
            runner.invoke(app, [])

        assert mock_repl_class.call_args.kwargs["model"] == "qwen3:8b"

    def test_ollama_base_url_env_used_when_no_flag(self, monkeypatch) -> None:
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://remote:11434")
        mock_client_class, _ = _make_client_mock()

        with (
            patch("main.OllamaClient", mock_client_class),
            patch("main.ChatREPL", return_value=AsyncMock()),
            patch("main.Renderer"),
            patch("main._configure_logging"),
        ):
            runner.invoke(app, [])

        mock_client_class.assert_called_once_with("http://remote:11434")


# ---------------------------------------------------------------------------
# TestStartupHealthCheck
# ---------------------------------------------------------------------------
class TestStartupHealthCheck:
    def test_unhealthy_ollama_exits_with_code_1(self) -> None:
        mock_client_class, _ = _make_client_mock(healthy=False)
        mock_renderer = MagicMock()

        with (
            patch("main.OllamaClient", mock_client_class),
            patch("main.Renderer", return_value=mock_renderer),
            patch("main.ChatREPL") as mock_repl_class,
            patch("main._configure_logging"),
        ):
            result = runner.invoke(app, [])

        mock_repl_class.assert_not_called()
        mock_renderer.render_error.assert_called_once()
        assert result.exit_code == 1

    def test_healthy_ollama_starts_repl(self) -> None:
        mock_client_class, mock_client = _make_client_mock(healthy=True)
        mock_repl = AsyncMock()

        with (
            patch("main.OllamaClient", mock_client_class),
            patch("main.ChatREPL", return_value=mock_repl) as mock_repl_class,
            patch("main.Renderer"),
            patch("main._configure_logging"),
        ):
            runner.invoke(app, [])

        mock_repl_class.assert_called_once()
        mock_repl.run.assert_called_once()
