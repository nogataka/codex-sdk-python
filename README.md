# Codex SDK for Python

Embed the Codex agent in your workflows and apps.

The Python SDK wraps the bundled `codex` binary. It spawns the CLI and exchanges JSONL events over stdin/stdout.

## Installation

```bash
pip install codex-sdk
```

Requires Python 3.10+.

## Quickstart

```python
import asyncio
from codex_sdk import Codex

async def main():
    codex = Codex()
    thread = codex.start_thread()
    turn = await thread.run("Diagnose the test failure and propose a fix")

    print(turn.final_response)
    print(turn.items)

asyncio.run(main())
```

Call `run()` repeatedly on the same `Thread` instance to continue that conversation.

```python
next_turn = await thread.run("Implement the fix")
```

### Streaming responses

`run()` buffers events until the turn finishes. To react to intermediate progress—tool calls, streaming responses, and file change notifications—use `run_streamed()` instead, which returns an async generator of structured events.

```python
async def stream_example():
    codex = Codex()
    thread = codex.start_thread()

    streamed = await thread.run_streamed("Diagnose the test failure and propose a fix")

    async for event in streamed.events:
        match event.get("type"):
            case "item.completed":
                print("item", event.get("item"))
            case "turn.completed":
                print("usage", event.get("usage"))
```

### Structured output

The Codex agent can produce a JSON response that conforms to a specified schema. The schema can be provided for each turn as a plain JSON object.

```python
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
```

You can also create a JSON schema from a [Pydantic model](https://docs.pydantic.dev/) using `model_json_schema()`.

```python
from pydantic import BaseModel
from typing import Literal

class StatusResponse(BaseModel):
    summary: str
    status: Literal["ok", "action_required"]

turn = await thread.run(
    "Summarize repository status",
    {"output_schema": StatusResponse.model_json_schema()}
)
print(turn.final_response)
```

### Attaching images

Provide structured input entries when you need to include images alongside text. Text entries are concatenated into the final prompt while image entries are passed to the Codex CLI via `--image`.

```python
turn = await thread.run([
    {"type": "text", "text": "Describe these screenshots"},
    {"type": "local_image", "path": "./ui.png"},
    {"type": "local_image", "path": "./diagram.jpg"},
])
```

### Resuming an existing thread

Threads are persisted in `~/.codex/sessions`. If you lose the in-memory `Thread` object, reconstruct it with `resume_thread()` and keep going.

```python
import os

saved_thread_id = os.environ["CODEX_THREAD_ID"]
thread = codex.resume_thread(saved_thread_id)
await thread.run("Implement the fix")
```

### Working directory controls

Codex runs in the current working directory by default. To avoid unrecoverable errors, Codex requires the working directory to be a Git repository. You can skip the Git repository check by passing the `skip_git_repo_check` option when creating a thread.

```python
thread = codex.start_thread({
    "working_directory": "/path/to/project",
    "skip_git_repo_check": True,
})
```

### Sandbox modes

Control how the agent interacts with your filesystem using `sandbox_mode`.

```python
from codex_sdk import Codex, SandboxMode

thread = codex.start_thread({
    "sandbox_mode": SandboxMode.WORKSPACE_WRITE,
})
```

Available modes:
- `SandboxMode.READ_ONLY` - Agent can only read files
- `SandboxMode.WORKSPACE_WRITE` - Agent can read/write in the workspace
- `SandboxMode.DANGER_FULL_ACCESS` - Full filesystem access (use with caution)

### Approval policies

Control when the agent requires approval for actions.

```python
from codex_sdk import Codex, ApprovalMode

thread = codex.start_thread({
    "approval_policy": ApprovalMode.ON_FAILURE,
})
```

Available modes:
- `ApprovalMode.NEVER` - Never require approval
- `ApprovalMode.ON_REQUEST` - Approve on explicit request
- `ApprovalMode.ON_FAILURE` - Approve after failures
- `ApprovalMode.UNTRUSTED` - Always require approval

### Cancelling a turn

Use `asyncio.Event` to cancel an ongoing turn (equivalent to `AbortSignal` in TypeScript).

```python
import asyncio

async def cancellable_example():
    codex = Codex()
    thread = codex.start_thread()

    cancel_event = asyncio.Event()

    async def cancel_after_delay():
        await asyncio.sleep(5)
        cancel_event.set()

    # Start cancellation timer
    asyncio.create_task(cancel_after_delay())

    try:
        turn = await thread.run(
            "Long running task",
            {"cancel_event": cancel_event}
        )
    except asyncio.CancelledError:
        print("Turn was cancelled")
```

### Controlling the Codex CLI environment

By default, the Codex CLI inherits the Python process environment. Provide the optional `env` parameter when instantiating the `Codex` client to fully control which variables the CLI receives—useful for sandboxed hosts.

```python
codex = Codex({
    "env": {
        "PATH": "/usr/local/bin",
    },
})
```

The SDK still injects its required variables (such as `OPENAI_BASE_URL` and `CODEX_API_KEY`) on top of the environment you provide.

### Passing `--config` overrides

Use the `config` option to provide additional Codex CLI configuration overrides. The SDK accepts a dict, flattens it into dotted paths, and serializes values as TOML literals before passing them as repeated `--config key=value` flags.

```python
codex = Codex({
    "config": {
        "show_raw_agent_reasoning": True,
        "sandbox_workspace_write": {"network_access": True},
    },
})
```

Thread options still take precedence for overlapping settings because they are emitted after these global overrides.

## API Reference

### Classes

#### `Codex`
Main entry point for the SDK.

```python
codex = Codex(options: CodexOptions | None = None)
```

Methods:
- `start_thread(options: ThreadOptions | None = None) -> Thread` - Start a new conversation
- `resume_thread(thread_id: str, options: ThreadOptions | None = None) -> Thread` - Resume an existing conversation

#### `Thread`
Represents a conversation with the agent.

Properties:
- `id: str | None` - Thread ID (populated after first turn)

Methods:
- `async run(input: Input, turn_options: TurnOptions | None = None) -> Turn` - Execute a turn and return results
- `async run_streamed(input: Input, turn_options: TurnOptions | None = None) -> StreamedTurn` - Execute a turn with streaming events

#### `Turn`
Result of a completed turn.

```python
@dataclass
class Turn:
    items: list[ThreadItem]      # All items produced during the turn
    final_response: str          # The agent's final response text
    usage: Usage | None          # Token usage statistics
```

#### `StreamedTurn`
Result of a streamed turn.

```python
@dataclass
class StreamedTurn:
    events: AsyncGenerator[ThreadEvent, None]  # Async generator of events
```

### Types

#### Input Types
- `Input = str | list[UserInput]` - User input (string or structured)
- `TextUserInput` - Text input: `{"type": "text", "text": "..."}`
- `ImageUserInput` - Image input: `{"type": "local_image", "path": "..."}`

#### Event Types
- `ThreadStartedEvent` - Thread started
- `TurnStartedEvent` - Turn started
- `TurnCompletedEvent` - Turn completed (includes usage)
- `TurnFailedEvent` - Turn failed (includes error)
- `ItemStartedEvent` - Item started
- `ItemUpdatedEvent` - Item updated
- `ItemCompletedEvent` - Item completed
- `ThreadErrorEvent` - Unrecoverable error

#### Item Types
- `AgentMessageItem` - Agent's response text
- `ReasoningItem` - Agent's reasoning summary
- `CommandExecutionItem` - Shell command execution
- `FileChangeItem` - File modifications
- `McpToolCallItem` - MCP tool invocation
- `WebSearchItem` - Web search query
- `TodoListItem` - Agent's task list
- `ErrorItem` - Non-fatal error

### Enums

```python
class SandboxMode(StrEnum):
    READ_ONLY = "read-only"
    WORKSPACE_WRITE = "workspace-write"
    DANGER_FULL_ACCESS = "danger-full-access"

class ApprovalMode(StrEnum):
    NEVER = "never"
    ON_REQUEST = "on-request"
    ON_FAILURE = "on-failure"
    UNTRUSTED = "untrusted"

class ModelReasoningEffort(StrEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    XHIGH = "xhigh"

class WebSearchMode(StrEnum):
    DISABLED = "disabled"
    CACHED = "cached"
    LIVE = "live"
```

## License

Apache-2.0
