"""Custom exception hierarchy for the Ollama Chat CLI."""


class OllamaError(Exception):
    """Base exception for all Ollama client errors."""


class OllamaConnectionError(OllamaError):
    """Raised when the Ollama server is unreachable."""


class OllamaModelNotFoundError(OllamaError):
    """Raised when the requested model is not available locally.

    Args:
        model: The model name that was not found.
    """

    def __init__(self, model: str) -> None:
        self.model = model
        super().__init__(f"Model '{model}' not found. Run `ollama pull {model}` first.")


class OllamaStreamError(OllamaError):
    """Raised when an error occurs while streaming a response.

    Args:
        message: Description of the stream failure.
        partial_content: Any content received before the failure, if any.
    """

    def __init__(self, message: str, partial_content: str = "") -> None:
        self.partial_content = partial_content
        super().__init__(message)
