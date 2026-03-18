"""Conversation state and history management for the Ollama Chat CLI."""

from dataclasses import dataclass
from typing import Literal

VALID_ROLES: frozenset[str] = frozenset({"system", "user", "assistant"})
Role = Literal["system", "user", "assistant"]


@dataclass
class Message:
    """A single message in a conversation.

    Args:
        role: The role of the message sender. Must be 'system', 'user', or 'assistant'.
        content: The text content of the message.

    Raises:
        ValueError: If role is not one of the valid values.
    """

    role: Role
    content: str

    def __post_init__(self) -> None:
        if self.role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{self.role}'. Must be one of: {sorted(VALID_ROLES)}")


class Conversation:
    """Manages in-memory conversation history for a chat session.

    Owns all mutations to the message list — no external module should
    append to history directly.

    Example:
        >>> convo = Conversation()
        >>> convo.add_message("user", "Hello!")
        >>> convo.add_message("assistant", "Hi there!")
        >>> len(convo)
        2
        >>> convo.get_history()
        [{'role': 'user', 'content': 'Hello!'}, {'role': 'assistant', 'content': 'Hi there!'}]
    """

    def __init__(self) -> None:
        self._messages: list[Message] = []

    def add_message(self, role: Role, content: str) -> None:
        """Append a message to the conversation history.

        Args:
            role: The role of the message sender ('system', 'user', or 'assistant').
            content: The text content of the message.

        Raises:
            ValueError: If role is not a valid value.
        """
        self._messages.append(Message(role=role, content=content))

    def get_history(self) -> list[dict[str, str]]:
        """Return the conversation history as a list of dicts.

        Returns the format expected by the Ollama ``/api/chat`` endpoint:
        ``[{"role": "user", "content": "..."}, ...]``.

        Returns:
            List of message dicts with 'role' and 'content' keys.
        """
        return [{"role": msg.role, "content": msg.content} for msg in self._messages]

    def clear(self) -> None:
        """Reset the conversation, removing all messages."""
        self._messages = []

    def __len__(self) -> int:
        """Return the number of messages in the conversation."""
        return len(self._messages)

    def __repr__(self) -> str:
        return f"Conversation(messages={len(self._messages)})"
