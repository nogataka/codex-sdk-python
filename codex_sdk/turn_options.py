"""
Turn options type definitions.

Corresponds to: src/turnOptions.ts
"""

from __future__ import annotations

import asyncio
from typing import Any, TypedDict


class TurnOptions(TypedDict, total=False):
    """Configuration options for individual turns."""

    output_schema: Any
    """JSON schema describing the expected agent output."""

    cancel_event: asyncio.Event
    """
    Event to signal cancellation of the turn.
    Set the event to cancel the ongoing turn.
    This is the Python equivalent of AbortSignal.
    """
