"""
Thread item type definitions.

Based on item types from codex-rs/exec/src/exec_events.rs

Corresponds to: src/items.ts
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

# Status types
CommandExecutionStatus = Literal["in_progress", "completed", "failed"]
"""The status of a command execution."""

PatchChangeKind = Literal["add", "delete", "update"]
"""Indicates the type of the file change."""

PatchApplyStatus = Literal["completed", "failed"]
"""The status of a file change."""

McpToolCallStatus = Literal["in_progress", "completed", "failed"]
"""The status of an MCP tool call."""


# MCP-related types
class McpContentBlock(TypedDict, total=False):
    """Content block from MCP tool result."""

    type: str
    text: str
    data: str
    mime_type: str


class McpToolResult(TypedDict):
    """Result payload returned by the MCP server for successful calls."""

    content: list[McpContentBlock]
    structured_content: Any


class McpToolError(TypedDict):
    """Error message reported for failed calls."""

    message: str


# Item types
class CommandExecutionItem(TypedDict):
    """A command executed by the agent."""

    id: str
    type: Literal["command_execution"]
    command: str
    """The command line executed by the agent."""
    aggregated_output: str
    """Aggregated stdout and stderr captured while the command was running."""
    status: CommandExecutionStatus
    """Current status of the command execution."""
    exit_code: NotRequired[int]
    """Set when the command exits; omitted while still running."""


class FileUpdateChange(TypedDict):
    """A set of file changes by the agent."""

    path: str
    kind: PatchChangeKind


class FileChangeItem(TypedDict):
    """A set of file changes by the agent. Emitted once the patch succeeds or fails."""

    id: str
    type: Literal["file_change"]
    changes: list[FileUpdateChange]
    """Individual file changes that comprise the patch."""
    status: PatchApplyStatus
    """Whether the patch ultimately succeeded or failed."""


class McpToolCallItem(TypedDict):
    """
    Represents a call to an MCP tool.

    The item starts when the invocation is dispatched and completes
    when the MCP server reports success or failure.
    """

    id: str
    type: Literal["mcp_tool_call"]
    server: str
    """Name of the MCP server handling the request."""
    tool: str
    """The tool invoked on the MCP server."""
    arguments: Any
    """Arguments forwarded to the tool invocation."""
    status: McpToolCallStatus
    """Current status of the tool invocation."""
    result: NotRequired[McpToolResult]
    """Result payload returned by the MCP server for successful calls."""
    error: NotRequired[McpToolError]
    """Error message reported for failed calls."""


class AgentMessageItem(TypedDict):
    """
    Response from the agent.

    Either natural-language text or JSON when structured output is requested.
    """

    id: str
    type: Literal["agent_message"]
    text: str
    """Either natural-language text or JSON when structured output is requested."""


class ReasoningItem(TypedDict):
    """Agent's reasoning summary."""

    id: str
    type: Literal["reasoning"]
    text: str


class WebSearchItem(TypedDict):
    """Captures a web search request. Completes when results are returned to the agent."""

    id: str
    type: Literal["web_search"]
    query: str


class ErrorItem(TypedDict):
    """Describes a non-fatal error surfaced as an item."""

    id: str
    type: Literal["error"]
    message: str


class TodoItem(TypedDict):
    """An item in the agent's to-do list."""

    text: str
    completed: bool


class TodoListItem(TypedDict):
    """
    Tracks the agent's running to-do list.

    Starts when the plan is issued, updates as steps change,
    and completes when the turn ends.
    """

    id: str
    type: Literal["todo_list"]
    items: list[TodoItem]


# Canonical union of thread items and their type-specific payloads
ThreadItem = (
    AgentMessageItem
    | ReasoningItem
    | CommandExecutionItem
    | FileChangeItem
    | McpToolCallItem
    | WebSearchItem
    | TodoListItem
    | ErrorItem
)
