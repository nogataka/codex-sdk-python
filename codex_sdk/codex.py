"""
Main Codex class for interacting with the Codex agent.

Corresponds to: src/codex.ts
"""

from __future__ import annotations

from .codex_options import CodexOptions
from .exec import CodexExec
from .thread import Thread
from .thread_options import ThreadOptions


class Codex:
    """
    Codex is the main class for interacting with the Codex agent.

    Use the `start_thread()` method to start a new thread or
    `resume_thread()` to resume a previously started thread.

    Example:
        ```python
        from codex_sdk import Codex

        codex = Codex()
        thread = codex.start_thread()
        result = await thread.run("Hello, world!")
        print(result.final_response)
        ```
    """

    def __init__(self, options: CodexOptions | None = None) -> None:
        """
        Initialize the Codex client.

        Args:
            options: Optional configuration for the Codex client.
        """
        options = options or {}
        self._exec = CodexExec(
            executable_path=options.get("codex_path_override"),
            env=options.get("env"),
            config_overrides=options.get("config"),
        )
        self._options = options

    def start_thread(self, options: ThreadOptions | None = None) -> Thread:
        """
        Starts a new conversation with an agent.

        Args:
            options: Optional thread-specific configuration.

        Returns:
            A new Thread instance.
        """
        options = options or {}
        return Thread(self._exec, self._options, options)

    def resume_thread(
        self,
        thread_id: str,
        options: ThreadOptions | None = None,
    ) -> Thread:
        """
        Resumes a conversation with an agent based on the thread id.

        Threads are persisted in ~/.codex/sessions.

        Args:
            thread_id: The id of the thread to resume.
            options: Optional thread-specific configuration.

        Returns:
            A Thread instance connected to the existing conversation.
        """
        options = options or {}
        return Thread(self._exec, self._options, options, thread_id)
