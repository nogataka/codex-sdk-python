"""
Codex options type definitions.

Corresponds to: src/codexOptions.ts
"""

from __future__ import annotations

from typing import TypedDict, Union

# Recursive type for config values
CodexConfigValue = Union[
    str,
    int,
    float,
    bool,
    list["CodexConfigValue"],
    "CodexConfigObject",
]


class CodexConfigObject(TypedDict, total=False):
    """A nested configuration object for Codex CLI overrides."""

    pass


class CodexOptions(TypedDict, total=False):
    """Configuration options for the Codex client."""

    codex_path_override: str
    """Custom path to the Codex CLI binary."""

    base_url: str
    """Base URL for the API."""

    api_key: str
    """API key for authentication."""

    config: CodexConfigObject
    """
    Additional --config key=value overrides to pass to the Codex CLI.

    Provide a dict and the SDK will flatten it into dotted paths and
    serialize values as TOML literals so they are compatible with the CLI's
    --config parsing.
    """

    env: dict[str, str]
    """
    Environment variables passed to the Codex CLI process.
    When provided, the SDK will not inherit variables from os.environ.
    """
