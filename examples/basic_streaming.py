#!/usr/bin/env python3
"""
Basic streaming example for the Codex SDK.

This example demonstrates how to use the SDK in an interactive loop,
streaming events as they are produced.

Corresponds to: samples/basic_streaming.ts
"""

from __future__ import annotations

import asyncio
import sys

from codex_sdk import Codex, ThreadEvent, ThreadItem


def handle_item_completed(item: ThreadItem) -> None:
    """Handle a completed item."""
    item_type = item.get("type")

    match item_type:
        case "agent_message":
            print(f"Assistant: {item.get('text', '')}")
        case "reasoning":
            print(f"Reasoning: {item.get('text', '')}")
        case "command_execution":
            exit_code = item.get("exit_code")
            exit_text = f" Exit code {exit_code}." if exit_code is not None else ""
            print(f"Command {item.get('command')} {item.get('status')}.{exit_text}")
        case "file_change":
            for change in item.get("changes", []):
                print(f"File {change.get('kind')} {change.get('path')}")


def handle_item_updated(item: ThreadItem) -> None:
    """Handle an updated item."""
    item_type = item.get("type")

    match item_type:
        case "todo_list":
            print("Todo:")
            for todo in item.get("items", []):
                checkbox = "x" if todo.get("completed") else " "
                print(f"\t [{checkbox}] {todo.get('text', '')}")


def handle_event(event: ThreadEvent) -> None:
    """Handle a thread event."""
    event_type = event.get("type")

    match event_type:
        case "item.completed":
            handle_item_completed(event.get("item"))
        case "item.updated" | "item.started":
            handle_item_updated(event.get("item"))
        case "turn.completed":
            usage = event.get("usage", {})
            print(
                f"Used {usage.get('input_tokens', 0)} input tokens, "
                f"{usage.get('cached_input_tokens', 0)} cached input tokens, "
                f"{usage.get('output_tokens', 0)} output tokens."
            )
        case "turn.failed":
            error = event.get("error", {})
            print(f"Turn failed: {error.get('message', 'Unknown error')}", file=sys.stderr)


async def main() -> None:
    """Main entry point."""
    codex = Codex()
    thread = codex.start_thread()

    print("Codex SDK Interactive Mode")
    print("Type your message and press Enter. Press Ctrl+C to exit.")
    print()

    try:
        while True:
            try:
                # Read input from user
                user_input = input("> ")
            except EOFError:
                break

            trimmed = user_input.strip()
            if not trimmed:
                continue

            # Stream events
            streamed = await thread.run_streamed(trimmed)
            async for event in streamed.events:
                handle_event(event)

            print()  # Add blank line between turns

    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    asyncio.run(main())
