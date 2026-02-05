"""
Thread class for managing conversations with the Codex agent.

Corresponds to: src/thread.ts
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TypedDict

from .events import ThreadError, ThreadEvent, Usage
from .exec import CodexExec, CodexExecArgs
from .items import ThreadItem
from .output_schema_file import create_output_schema_file

if TYPE_CHECKING:
    from .codex_options import CodexOptions
    from .thread_options import ThreadOptions
    from .turn_options import TurnOptions


# Input types
class TextUserInput(TypedDict):
    """Text input for user messages."""

    type: Literal["text"]
    text: str


class ImageUserInput(TypedDict):
    """Local image input."""

    type: Literal["local_image"]
    path: str


UserInput = TextUserInput | ImageUserInput
"""An input to send to the agent."""

Input = str | list[UserInput]
"""Either a string prompt or a list of user inputs."""


@dataclass
class Turn:
    """Completed turn result."""

    items: list[ThreadItem]
    """All items produced during the turn."""

    final_response: str
    """The agent's final response text."""

    usage: Usage | None
    """Token usage statistics."""


# Alias for Turn to describe the result of run()
RunResult = Turn


@dataclass
class StreamedTurn:
    """The result of the runStreamed method."""

    events: AsyncGenerator[ThreadEvent, None]
    """Async generator yielding events as they are produced."""


# Alias for StreamedTurn to describe the result of run_streamed()
RunStreamedResult = StreamedTurn


def _normalize_input(input_data: Input) -> tuple[str, list[str]]:
    """
    Normalize input to prompt string and image paths.

    Args:
        input_data: Either a string or list of user inputs.

    Returns:
        Tuple of (prompt_string, image_paths).
    """
    if isinstance(input_data, str):
        return input_data, []

    prompt_parts: list[str] = []
    images: list[str] = []

    for item in input_data:
        if item["type"] == "text":
            prompt_parts.append(item["text"])
        elif item["type"] == "local_image":
            images.append(item["path"])

    return "\n\n".join(prompt_parts), images


class Thread:
    """
    Represents a thread of conversation with the agent.

    One thread can have multiple consecutive turns.
    """

    def __init__(
        self,
        exec_instance: CodexExec,
        options: CodexOptions,
        thread_options: ThreadOptions,
        thread_id: str | None = None,
    ) -> None:
        """
        Initialize a Thread instance.

        This is an internal constructor. Use Codex.start_thread() or
        Codex.resume_thread() to create Thread instances.

        Args:
            exec_instance: The CodexExec instance for running CLI commands.
            options: Global Codex options.
            thread_options: Thread-specific options.
            thread_id: Optional thread ID for resuming conversations.
        """
        self._exec = exec_instance
        self._options = options
        self._thread_options = thread_options
        self._id = thread_id

    @property
    def id(self) -> str | None:
        """
        Returns the ID of the thread.

        Populated after the first turn starts.
        """
        return self._id

    async def run_streamed(
        self,
        input_data: Input,
        turn_options: TurnOptions | None = None,
    ) -> StreamedTurn:
        """
        Provides the input to the agent and streams events as they are produced during the turn.

        Args:
            input_data: The user input (string or structured input with images).
            turn_options: Optional turn-specific configuration.

        Returns:
            StreamedTurn containing an async generator of events.
        """
        return StreamedTurn(events=self._run_streamed_internal(input_data, turn_options))

    async def _run_streamed_internal(
        self,
        input_data: Input,
        turn_options: TurnOptions | None = None,
    ) -> AsyncGenerator[ThreadEvent, None]:
        """
        Internal implementation of run_streamed.

        Yields:
            ThreadEvent objects as they are produced.
        """
        turn_options = turn_options or {}

        # Create output schema file if needed
        schema_file = await create_output_schema_file(turn_options.get("output_schema"))

        prompt, images = _normalize_input(input_data)

        exec_args = CodexExecArgs(
            input=prompt,
            base_url=self._options.get("base_url"),
            api_key=self._options.get("api_key"),
            thread_id=self._id,
            images=images if images else None,
            model=self._thread_options.get("model"),
            sandbox_mode=self._thread_options.get("sandbox_mode"),
            working_directory=self._thread_options.get("working_directory"),
            skip_git_repo_check=self._thread_options.get("skip_git_repo_check"),
            output_schema_file=schema_file.schema_path,
            model_reasoning_effort=self._thread_options.get("model_reasoning_effort"),
            cancel_event=turn_options.get("cancel_event"),
            network_access_enabled=self._thread_options.get("network_access_enabled"),
            web_search_mode=self._thread_options.get("web_search_mode"),
            web_search_enabled=self._thread_options.get("web_search_enabled"),
            approval_policy=self._thread_options.get("approval_policy"),
            additional_directories=self._thread_options.get("additional_directories"),
        )

        try:
            async for line in self._exec.run(exec_args):
                try:
                    parsed: ThreadEvent = json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Failed to parse item: {line}") from e

                # Capture thread ID from first event
                if parsed.get("type") == "thread.started":
                    self._id = parsed.get("thread_id")

                yield parsed
        finally:
            await schema_file.cleanup()

    async def run(
        self,
        input_data: Input,
        turn_options: TurnOptions | None = None,
    ) -> Turn:
        """
        Provides the input to the agent and returns the completed turn.

        Args:
            input_data: The user input (string or structured input with images).
            turn_options: Optional turn-specific configuration.

        Returns:
            Turn object with items, final response, and usage.

        Raises:
            RuntimeError: If the turn fails.
        """
        items: list[ThreadItem] = []
        final_response: str = ""
        usage: Usage | None = None
        turn_failure: ThreadError | None = None

        streamed = await self.run_streamed(input_data, turn_options)
        async for event in streamed.events:
            event_type = event.get("type")

            if event_type == "item.completed":
                item = event.get("item")
                if item:
                    if item.get("type") == "agent_message":
                        final_response = item.get("text", "")
                    items.append(item)

            elif event_type == "turn.completed":
                usage = event.get("usage")

            elif event_type == "turn.failed":
                turn_failure = event.get("error")
                break

        if turn_failure:
            raise RuntimeError(turn_failure.get("message", "Turn failed"))

        return Turn(items=items, final_response=final_response, usage=usage)
