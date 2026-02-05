"""
Output schema file utilities.

Corresponds to: src/outputSchemaFile.ts
"""

from __future__ import annotations

import json
import shutil
import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class OutputSchemaFile:
    """Result of creating an output schema file."""

    schema_path: str | None
    """Path to the temporary schema file, or None if no schema was provided."""

    cleanup: Callable[[], Awaitable[None]]
    """Async function to clean up the temporary file."""


def _is_json_object(value: Any) -> bool:
    """Check if value is a plain JSON object (dict)."""
    return isinstance(value, dict)


async def create_output_schema_file(schema: Any | None) -> OutputSchemaFile:
    """
    Create a temporary file containing the JSON schema.

    Args:
        schema: The JSON schema to write, or None if no schema is needed.

    Returns:
        OutputSchemaFile with the path and cleanup function.

    Raises:
        ValueError: If schema is not a plain JSON object.
    """

    async def noop_cleanup() -> None:
        pass

    if schema is None:
        return OutputSchemaFile(schema_path=None, cleanup=noop_cleanup)

    if not _is_json_object(schema):
        raise ValueError("output_schema must be a plain JSON object")

    # Create temporary directory
    schema_dir = Path(tempfile.mkdtemp(prefix="codex-output-schema-"))
    schema_path = schema_dir / "schema.json"

    async def cleanup() -> None:
        try:
            shutil.rmtree(schema_dir, ignore_errors=True)
        except Exception:
            # suppress errors during cleanup
            pass

    try:
        # Write schema to file
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        return OutputSchemaFile(schema_path=str(schema_path), cleanup=cleanup)
    except Exception:
        await cleanup()
        raise
