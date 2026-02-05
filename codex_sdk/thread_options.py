"""
Thread options type definitions.

Corresponds to: src/threadOptions.ts
"""

from __future__ import annotations

from enum import StrEnum
from typing import TypedDict


class ApprovalMode(StrEnum):
    """Approval policy for agent actions."""

    NEVER = "never"
    ON_REQUEST = "on-request"
    ON_FAILURE = "on-failure"
    UNTRUSTED = "untrusted"


class SandboxMode(StrEnum):
    """Sandbox execution mode for the Codex CLI."""

    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"
    DANGER_FULL_ACCESS = "danger-full-access"


class ModelReasoningEffort(StrEnum):
    """Reasoning effort level for the model."""

    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"


class WebSearchMode(StrEnum):
    """Web search configuration mode."""

    DISABLED = "disabled"
    CACHED = "cached"
    LIVE = "live"


class ThreadOptions(TypedDict, total=False):
    """Configuration options for thread creation."""

    model: str
    """Model to use for the thread."""

    sandbox_mode: SandboxMode
    """Sandbox execution mode."""

    working_directory: str
    """Working directory for the agent."""

    skip_git_repo_check: bool
    """Skip Git repository validation."""

    model_reasoning_effort: ModelReasoningEffort
    """Reasoning effort level."""

    network_access_enabled: bool
    """Enable network access for the agent."""

    web_search_mode: WebSearchMode
    """Web search configuration mode."""

    web_search_enabled: bool
    """Enable web search capability (legacy)."""

    approval_policy: ApprovalMode
    """Approval policy for agent actions."""

    additional_directories: list[str]
    """Additional directories accessible to the agent."""
