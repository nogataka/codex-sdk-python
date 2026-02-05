"""
Thread event type definitions.

Based on event types from codex-rs/exec/src/exec_events.rs

Corresponds to: src/events.ts
"""

from __future__ import annotations

from typing import Literal, TypedDict

from .items import ThreadItem


class Usage(TypedDict):
    """Describes the usage of tokens during a turn."""

    input_tokens: int
    """The number of input tokens used during the turn."""
    cached_input_tokens: int
    """The number of cached input tokens used during the turn."""
    output_tokens: int
    """The number of output tokens used during the turn."""


class ThreadError(TypedDict):
    """Fatal error emitted by the stream."""

    message: str


class ThreadStartedEvent(TypedDict):
    """Emitted when a new thread is started as the first event."""

    type: Literal["thread.started"]
    thread_id: str
    """The identifier of the new thread. Can be used to resume the thread later."""


class TurnStartedEvent(TypedDict):
    """
    Emitted when a turn is started by sending a new prompt to the model.

    A turn encompasses all events that happen while the agent is processing the prompt.
    """

    type: Literal["turn.started"]


class TurnCompletedEvent(TypedDict):
    """Emitted when a turn is completed. Typically right after the assistant's response."""

    type: Literal["turn.completed"]
    usage: Usage


class TurnFailedEvent(TypedDict):
    """Indicates that a turn failed with an error."""

    type: Literal["turn.failed"]
    error: ThreadError


class ItemStartedEvent(TypedDict):
    """
    Emitted when a new item is added to the thread.

    Typically the item is initially 'in progress'.
    """

    type: Literal["item.started"]
    item: ThreadItem


class ItemUpdatedEvent(TypedDict):
    """Emitted when an item is updated."""

    type: Literal["item.updated"]
    item: ThreadItem


class ItemCompletedEvent(TypedDict):
    """Signals that an item has reached a terminal state—either success or failure."""

    type: Literal["item.completed"]
    item: ThreadItem


class ThreadErrorEvent(TypedDict):
    """Represents an unrecoverable error emitted directly by the event stream."""

    type: Literal["error"]
    message: str


# Top-level JSONL events emitted by codex exec
ThreadEvent = (
    ThreadStartedEvent
    | TurnStartedEvent
    | TurnCompletedEvent
    | TurnFailedEvent
    | ItemStartedEvent
    | ItemUpdatedEvent
    | ItemCompletedEvent
    | ThreadErrorEvent
)
