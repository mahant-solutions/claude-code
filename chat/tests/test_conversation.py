"""Tests for chat.conversation module."""

import pytest

from chat.conversation import VALID_ROLES, Conversation, Message


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------
class TestMessage:
    """Tests for the Message dataclass."""

    @pytest.mark.parametrize("role", sorted(VALID_ROLES))
    def test_creates_message_with_valid_role(self, role: str) -> None:
        msg = Message(role=role, content="hello")  # type: ignore[arg-type]
        assert msg.role == role
        assert msg.content == "hello"

    def test_raises_value_error_for_invalid_role(self) -> None:
        with pytest.raises(ValueError, match="Invalid role 'god'"):
            Message(role="god", content="I am all-knowing")  # type: ignore[arg-type]

    def test_raises_value_error_lists_valid_roles(self) -> None:
        with pytest.raises(ValueError, match="assistant"):
            Message(role="bot", content="beep boop")  # type: ignore[arg-type]

    def test_content_is_preserved_exactly(self) -> None:
        content = "  leading space\nnewline\ttab  "
        msg = Message(role="user", content=content)
        assert msg.content == content


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------
class TestConversation:
    """Tests for the Conversation class."""

    def test_starts_empty(self, conversation: Conversation) -> None:
        assert len(conversation) == 0
        assert conversation.get_history() == []

    def test_add_message_increments_length(self, conversation: Conversation) -> None:
        conversation.add_message("user", "hi")
        assert len(conversation) == 1

    def test_add_message_stores_role_and_content(self, conversation: Conversation) -> None:
        conversation.add_message("user", "What is 2+2?")
        history = conversation.get_history()
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "What is 2+2?"

    def test_get_history_returns_list_of_dicts(self, conversation: Conversation) -> None:
        conversation.add_message("user", "hello")
        history = conversation.get_history()
        assert isinstance(history, list)
        assert isinstance(history[0], dict)
        assert set(history[0].keys()) == {"role", "content"}

    def test_get_history_preserves_insertion_order(self, conversation: Conversation) -> None:
        conversation.add_message("user", "first")
        conversation.add_message("assistant", "second")
        conversation.add_message("user", "third")
        history = conversation.get_history()
        assert history[0]["content"] == "first"
        assert history[1]["content"] == "second"
        assert history[2]["content"] == "third"

    def test_get_history_does_not_mutate_internal_state(self, conversation: Conversation) -> None:
        conversation.add_message("user", "hello")
        history = conversation.get_history()
        history.append({"role": "user", "content": "injected"})
        assert len(conversation) == 1

    def test_clear_removes_all_messages(self, conversation: Conversation) -> None:
        conversation.add_message("user", "msg1")
        conversation.add_message("assistant", "msg2")
        conversation.clear()
        assert len(conversation) == 0
        assert conversation.get_history() == []

    def test_clear_allows_new_messages_after(self, conversation: Conversation) -> None:
        conversation.add_message("user", "old message")
        conversation.clear()
        conversation.add_message("user", "fresh start")
        assert len(conversation) == 1
        assert conversation.get_history()[0]["content"] == "fresh start"

    def test_len_matches_message_count(self, conversation: Conversation) -> None:
        for i in range(5):
            conversation.add_message("user", f"message {i}")
        assert len(conversation) == 5

    def test_add_message_raises_for_invalid_role(self, conversation: Conversation) -> None:
        with pytest.raises(ValueError, match="Invalid role"):
            conversation.add_message("robot", "beep")  # type: ignore[arg-type]

    @pytest.mark.parametrize("role", sorted(VALID_ROLES))
    def test_all_valid_roles_accepted(self, conversation: Conversation, role: str) -> None:
        conversation.add_message(role, f"message from {role}")  # type: ignore[arg-type]
        assert conversation.get_history()[0]["role"] == role

    def test_multi_turn_conversation_full_sequence(self, conversation: Conversation) -> None:
        """Simulate a realistic multi-turn exchange and verify full history."""
        turns = [
            ("system", "You are a helpful assistant."),
            ("user", "What is the capital of France?"),
            ("assistant", "The capital of France is Paris."),
            ("user", "And Germany?"),
            ("assistant", "The capital of Germany is Berlin."),
        ]
        for role, content in turns:
            conversation.add_message(role, content)  # type: ignore[arg-type]

        history = conversation.get_history()
        assert len(history) == 5
        for i, (role, content) in enumerate(turns):
            assert history[i]["role"] == role
            assert history[i]["content"] == content

    def test_repr_shows_message_count(self, conversation: Conversation) -> None:
        conversation.add_message("user", "hello")
        assert "1" in repr(conversation)
