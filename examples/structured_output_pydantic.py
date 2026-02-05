#!/usr/bin/env python3
"""
Structured output example using Pydantic models.

This example demonstrates how to use Pydantic models to define
the expected response schema.

Corresponds to: samples/structured_output_zod.ts
"""

from __future__ import annotations

import asyncio
from typing import Literal

from pydantic import BaseModel

from codex_sdk import Codex


class StatusResponse(BaseModel):
    """Expected response structure."""

    summary: str
    status: Literal["ok", "action_required"]


async def main() -> None:
    """Main entry point."""
    codex = Codex()
    thread = codex.start_thread()

    # Use Pydantic model to generate JSON schema
    turn = await thread.run(
        "Summarize repository status",
        {"output_schema": StatusResponse.model_json_schema()},
    )

    print("Raw response:")
    print(turn.final_response)
    print()

    # Parse the response into a Pydantic model
    import json

    response_data = json.loads(turn.final_response)
    response = StatusResponse(**response_data)

    print("Parsed response:")
    print(f"  Summary: {response.summary}")
    print(f"  Status: {response.status}")


if __name__ == "__main__":
    asyncio.run(main())
