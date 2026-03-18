"""Shared pytest fixtures for the ollama-chat CLI test suite."""

import pytest

from chat.conversation import Conversation


@pytest.fixture
def conversation() -> Conversation:
    """Return a fresh, empty Conversation instance."""
    return Conversation()
