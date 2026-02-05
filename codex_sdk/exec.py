"""
Codex CLI execution management.

Corresponds to: src/exec.ts
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import sys
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .codex_options import CodexConfigObject, CodexConfigValue
    from .thread_options import ApprovalMode, ModelReasoningEffort, SandboxMode, WebSearchMode

INTERNAL_ORIGINATOR_ENV = "CODEX_INTERNAL_ORIGINATOR_OVERRIDE"
PYTHON_SDK_ORIGINATOR = "codex_sdk_py"


@dataclass
class CodexExecArgs:
    """Arguments for executing the Codex CLI."""

    input: str
    """The prompt to send to the agent."""

    base_url: str | None = None
    api_key: str | None = None
    thread_id: str | None = None
    images: list[str] | None = None

    # --model
    model: str | None = None
    # --sandbox
    sandbox_mode: SandboxMode | None = None
    # --cd
    working_directory: str | None = None
    # --add-dir
    additional_directories: list[str] | None = None
    # --skip-git-repo-check
    skip_git_repo_check: bool | None = None
    # --output-schema
    output_schema_file: str | None = None
    # --config model_reasoning_effort
    model_reasoning_effort: ModelReasoningEffort | None = None
    # Cancel event to cancel the execution
    cancel_event: asyncio.Event | None = None
    # --config sandbox_workspace_write.network_access
    network_access_enabled: bool | None = None
    # --config web_search
    web_search_mode: WebSearchMode | None = None
    # legacy --config features.web_search_request
    web_search_enabled: bool | None = None
    # --config approval_policy
    approval_policy: ApprovalMode | None = None


class CodexExec:
    """
    Internal class that spawns and manages the Codex CLI process.

    Handles subprocess lifecycle, environment setup, and JSONL streaming.
    """

    def __init__(
        self,
        executable_path: str | None = None,
        env: dict[str, str] | None = None,
        config_overrides: CodexConfigObject | None = None,
    ) -> None:
        """
        Initialize the CodexExec instance.

        Args:
            executable_path: Custom path to the Codex CLI binary.
            env: Environment variables to pass to the subprocess.
            config_overrides: Additional --config overrides.
        """
        self._executable_path = executable_path or _find_codex_path()
        self._env_override = env
        self._config_overrides = config_overrides

    async def run(self, args: CodexExecArgs) -> AsyncGenerator[str, None]:
        """
        Execute the Codex CLI and yield JSONL lines from stdout.

        Args:
            args: Execution arguments including prompt and options.

        Yields:
            JSONL lines from the CLI stdout.

        Raises:
            RuntimeError: If the CLI process fails.
            asyncio.CancelledError: If cancelled via cancel_event.
        """
        command_args = self._build_command_args(args)
        env = self._build_env(args)

        process = await asyncio.create_subprocess_exec(
            self._executable_path,
            *command_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stderr_chunks: list[bytes] = []

        async def read_stderr() -> None:
            """Read stderr in background."""
            if process.stderr:
                while True:
                    chunk = await process.stderr.read(4096)
                    if not chunk:
                        break
                    stderr_chunks.append(chunk)

        stderr_task = asyncio.create_task(read_stderr())

        try:
            # Write input to stdin and close
            if process.stdin:
                process.stdin.write(args.input.encode("utf-8"))
                await process.stdin.drain()
                process.stdin.close()
                await process.stdin.wait_closed()

            # Stream stdout line by line
            if process.stdout:
                buffer = b""
                while True:
                    # Check for cancellation
                    if args.cancel_event and args.cancel_event.is_set():
                        process.terminate()
                        raise asyncio.CancelledError("Turn cancelled by user")

                    chunk = await process.stdout.read(4096)
                    if not chunk:
                        # Process remaining buffer
                        if buffer:
                            yield buffer.decode("utf-8")
                        break

                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        decoded = line.decode("utf-8")
                        if decoded:
                            yield decoded

            # Wait for process to complete
            await process.wait()
            await stderr_task

            # Check for errors
            if process.returncode != 0:
                stderr_output = b"".join(stderr_chunks).decode("utf-8")
                detail = f"code {process.returncode}"
                raise RuntimeError(f"Codex Exec exited with {detail}: {stderr_output}")

        finally:
            stderr_task.cancel()
            try:
                await stderr_task
            except asyncio.CancelledError:
                pass

            if process.returncode is None:
                process.terminate()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()

    def _build_command_args(self, args: CodexExecArgs) -> list[str]:
        """Build command line arguments for the CLI."""
        command_args: list[str] = ["exec", "--experimental-json"]

        # Add config overrides
        if self._config_overrides:
            for override in _serialize_config_overrides(self._config_overrides):
                command_args.extend(["--config", override])

        if args.model:
            command_args.extend(["--model", args.model])

        if args.sandbox_mode:
            command_args.extend(["--sandbox", args.sandbox_mode])

        if args.working_directory:
            command_args.extend(["--cd", args.working_directory])

        if args.additional_directories:
            for dir_path in args.additional_directories:
                command_args.extend(["--add-dir", dir_path])

        if args.skip_git_repo_check:
            command_args.append("--skip-git-repo-check")

        if args.output_schema_file:
            command_args.extend(["--output-schema", args.output_schema_file])

        if args.model_reasoning_effort:
            command_args.extend(
                ["--config", f'model_reasoning_effort="{args.model_reasoning_effort}"']
            )

        if args.network_access_enabled is not None:
            value = "true" if args.network_access_enabled else "false"
            command_args.extend(
                ["--config", f"sandbox_workspace_write.network_access={value}"]
            )

        if args.web_search_mode:
            command_args.extend(["--config", f'web_search="{args.web_search_mode}"'])
        elif args.web_search_enabled is True:
            command_args.extend(["--config", 'web_search="live"'])
        elif args.web_search_enabled is False:
            command_args.extend(["--config", 'web_search="disabled"'])

        if args.approval_policy:
            command_args.extend(["--config", f'approval_policy="{args.approval_policy}"'])

        if args.images:
            for image in args.images:
                command_args.extend(["--image", image])

        if args.thread_id:
            command_args.extend(["resume", args.thread_id])

        return command_args

    def _build_env(self, args: CodexExecArgs) -> dict[str, str]:
        """Build environment variables for the subprocess."""
        env: dict[str, str] = {}

        if self._env_override is not None:
            env.update(self._env_override)
        else:
            for key, value in os.environ.items():
                if value is not None:
                    env[key] = value

        if INTERNAL_ORIGINATOR_ENV not in env:
            env[INTERNAL_ORIGINATOR_ENV] = PYTHON_SDK_ORIGINATOR

        if args.base_url:
            env["OPENAI_BASE_URL"] = args.base_url

        if args.api_key:
            env["CODEX_API_KEY"] = args.api_key

        return env


def _serialize_config_overrides(config_overrides: CodexConfigObject) -> list[str]:
    """Serialize config overrides to CLI format."""
    overrides: list[str] = []
    _flatten_config_overrides(config_overrides, "", overrides)
    return overrides


def _flatten_config_overrides(
    value: CodexConfigValue,
    prefix: str,
    overrides: list[str],
) -> None:
    """Flatten nested config dict to dotted paths."""
    if not _is_plain_object(value):
        if prefix:
            overrides.append(f"{prefix}={_to_toml_value(value, prefix)}")
            return
        else:
            raise ValueError("Codex config overrides must be a plain object")

    entries = list(value.items())
    if not prefix and len(entries) == 0:
        return

    if prefix and len(entries) == 0:
        overrides.append(f"{prefix}={{}}")
        return

    for key, child in entries:
        if not key:
            raise ValueError("Codex config override keys must be non-empty strings")
        if child is None:
            continue
        path = f"{prefix}.{key}" if prefix else key
        if _is_plain_object(child):
            _flatten_config_overrides(child, path, overrides)
        else:
            overrides.append(f"{path}={_to_toml_value(child, path)}")


def _to_toml_value(value: CodexConfigValue, path: str) -> str:
    """Serialize a value as a TOML literal."""
    if isinstance(value, str):
        return json.dumps(value)
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        is_finite = isinstance(value, int) or (
            isinstance(value, float)
            and value != float("inf")
            and value != float("-inf")
            and value == value  # NaN check
        )
        if not is_finite:
            raise ValueError(f"Codex config override at {path} must be a finite number")
        return str(value)
    elif isinstance(value, list):
        rendered = [_to_toml_value(item, f"{path}[{i}]") for i, item in enumerate(value)]
        return f"[{', '.join(rendered)}]"
    elif _is_plain_object(value):
        parts: list[str] = []
        for key, child in value.items():
            if not key:
                raise ValueError("Codex config override keys must be non-empty strings")
            if child is None:
                continue
            parts.append(f"{_format_toml_key(key)} = {_to_toml_value(child, f'{path}.{key}')}")
        return "{" + ", ".join(parts) + "}"
    elif value is None:
        raise ValueError(f"Codex config override at {path} cannot be null")
    else:
        type_name = type(value).__name__
        raise ValueError(f"Unsupported Codex config override value at {path}: {type_name}")


TOML_BARE_KEY_PATTERN = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")


def _format_toml_key(key: str) -> str:
    """Format a key for TOML syntax."""
    if key and all(c in TOML_BARE_KEY_PATTERN for c in key):
        return key
    return json.dumps(key)


def _is_plain_object(value: Any) -> bool:
    """Check if value is a plain object (dict)."""
    return isinstance(value, dict)


def _find_codex_path() -> str:
    """Find the Codex binary path for the current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    target_triple: str | None = None

    if system in ("linux", "android"):
        if machine in ("x86_64", "amd64"):
            target_triple = "x86_64-unknown-linux-musl"
        elif machine in ("arm64", "aarch64"):
            target_triple = "aarch64-unknown-linux-musl"

    elif system == "darwin":
        if machine in ("x86_64", "amd64"):
            target_triple = "x86_64-apple-darwin"
        elif machine in ("arm64", "aarch64"):
            target_triple = "aarch64-apple-darwin"

    elif system == "win32" or system == "windows":
        if machine in ("x86_64", "amd64"):
            target_triple = "x86_64-pc-windows-msvc"
        elif machine in ("arm64", "aarch64"):
            target_triple = "aarch64-pc-windows-msvc"

    if not target_triple:
        raise RuntimeError(f"Unsupported platform: {system} ({machine})")

    # Try to find bundled binary
    script_dir = Path(__file__).parent
    vendor_root = script_dir / "vendor"
    arch_root = vendor_root / target_triple

    binary_name = "codex.exe" if sys.platform == "win32" else "codex"
    binary_path = arch_root / "codex" / binary_name

    if binary_path.exists():
        return str(binary_path)

    # Fall back to PATH
    return "codex"
