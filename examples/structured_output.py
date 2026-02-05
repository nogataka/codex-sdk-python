#!/usr/bin/env python3
"""
Structured output example for the Codex SDK.

This example demonstrates how to use JSON schema to get structured responses.

Corresponds to: samples/structured_output.ts
"""

from __future__ import annotations

import asyncio

from codex_sdk import Codex


async def main() -> None:
    """Main entry point."""
    codex = Codex()
    thread = codex.start_thread()

    # Define JSON schema for structured output
    schema = {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "status": {"type": "string", "enum": ["ok", "action_required"]},
        },
        "required": ["summary", "status"],
        "additionalProperties": False,
    }

    turn = await thread.run("Summarize repository status", {"output_schema": schema})
    print(turn.final_response)


if __name__ == "__main__":
    asyncio.run(main())
