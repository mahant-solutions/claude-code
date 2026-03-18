"""REPL / CLI entry-point loop."""

import typer
from loguru import logger

from chat.client import OllamaClient
from chat.conversation import Conversation
from chat.exceptions import OllamaConnectionError, OllamaModelNotFoundError, OllamaStreamError
from chat.renderer import Renderer


class ChatREPL:
    """Interactive REPL loop for the Ollama Chat CLI.

    Args:
        client: Ollama HTTP client.
        renderer: Terminal output renderer.
        model: Active model name.
    """

    def __init__(self, client: OllamaClient, renderer: Renderer, model: str) -> None:
        self._client = client
        self._renderer = renderer
        self._model = model
        self._conversation = Conversation()

    async def run(self) -> None:
        """Run the main REPL loop until the user exits.

        Handles Ctrl+C (shows hint), Ctrl+D (exits gracefully), and /exit.
        """
        self._renderer.welcome_banner(self._model)
        while True:
            try:
                you_label = typer.style("You", fg=typer.colors.BRIGHT_GREEN, bold=True)
                user_input = input(f"\n{you_label}: ").strip()
            except EOFError:
                self._renderer.render_goodbye()
                break
            except KeyboardInterrupt:
                self._renderer.render_error("Type /exit to quit.")
                continue

            should_continue = await self.handle_input(user_input)
            if not should_continue:
                break

    async def handle_input(self, user_input: str) -> bool:
        """Dispatch a single line of user input.

        Args:
            user_input: The stripped input string from the user.

        Returns:
            True to continue the loop, False to exit.
        """
        if not user_input:
            return True
        if user_input.lower() == "quit":
            self._renderer.render_goodbye()
            return False
        if user_input.startswith("/"):
            return await self.handle_slash_command(user_input)
        await self.handle_chat(user_input)
        return True

    async def handle_chat(self, user_input: str) -> None:
        """Send a user message and stream the assistant response.

        Adds the user message to conversation, streams tokens through the
        renderer, then adds the full assistant response to conversation.
        Handles KeyboardInterrupt, OllamaStreamError, and OllamaModelNotFoundError.

        Args:
            user_input: The user's chat message.
        """
        self._conversation.add_message("user", user_input)
        self._renderer.render_assistant_label()
        full_response = ""
        try:
            async for token in self._client.chat_stream(
                self._model, self._conversation.get_history()
            ):
                self._renderer.render_streaming_response(token)
                full_response += token
        except KeyboardInterrupt:
            self._renderer.render_error("[interrupted]")
            if full_response:
                self._conversation.add_message("assistant", full_response)
            return
        except OllamaStreamError as exc:
            partial = exc.partial_content or full_response
            self._renderer.render_error(
                "Connection lost. Your conversation is preserved — try sending another message."
            )
            if partial:
                self._conversation.add_message("assistant", partial)
            return
        except OllamaModelNotFoundError as exc:
            self._renderer.render_error(str(exc))
            return
        except OllamaConnectionError as exc:
            self._renderer.render_error(str(exc))
            return

        self._renderer.finalize_response(full_response)
        self._conversation.add_message("assistant", full_response)
        logger.debug("Chat response complete, %d chars", len(full_response))

    async def handle_slash_command(self, command: str) -> bool:
        """Handle a /command string.

        Args:
            command: The raw slash command string (e.g. "/model mistral").

        Returns:
            True to continue the loop, False to exit.
        """
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd == "/help":
            self._renderer.render_help()
        elif cmd == "/exit":
            self._renderer.render_goodbye()
            return False
        elif cmd == "/clear":
            self._conversation.clear()
            self._renderer.clear_screen()
        elif cmd == "/models":
            try:
                models = await self._client.list_models()
                self._renderer.render_models_list(models)
            except OllamaConnectionError as exc:
                self._renderer.render_error(str(exc))
        elif cmd == "/model":
            if not arg:
                self._renderer.render_error("Usage: /model <name>")
            else:
                self._model = arg
                self._conversation.clear()
                self._renderer.render_info(f"Switched to model '{arg}'. Conversation reset.")
        else:
            self._renderer.render_error("Unknown command. Type /help.")

        return True
