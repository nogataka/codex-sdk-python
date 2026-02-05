#!/usr/bin/env python3
"""
Image input example for the Codex SDK.

This example demonstrates how to attach images to prompts.

Corresponds to: samples/basic_streaming.ts (image attachment section)
"""

from __future__ import annotations

import asyncio
import sys

from codex_sdk import Codex


async def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python image_input.py <image_path> [image_path2 ...]")
        print("Example: python image_input.py ./screenshot.png ./diagram.jpg")
        sys.exit(1)

    image_paths = sys.argv[1:]

    codex = Codex()
    thread = codex.start_thread()

    # Build structured input with text and images
    user_input = [
        {"type": "text", "text": "Describe these images in detail"},
    ]
    for path in image_paths:
        user_input.append({"type": "local_image", "path": path})

    print(f"Analyzing {len(image_paths)} image(s)...")
    print()

    turn = await thread.run(user_input)
    print(turn.final_response)


if __name__ == "__main__":
    asyncio.run(main())
