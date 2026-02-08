# Codex SDK vs Claude Agent SDK 機能比較

このドキュメントでは、OpenAI Codex SDK と Anthropic Claude Agent SDK の機能を比較します。

## 概要

| 項目 | Codex SDK | Claude Agent SDK |
|------|-----------|------------------|
| **提供元** | OpenAI | Anthropic |
| **対象CLI** | `codex` CLI | `claude` CLI (Claude Code) |
| **バイナリ** | 別途インストール or バンドル | バンドル (PyPIパッケージに同梱) |
| **通信方式** | JSONL over stdin/stdout | JSONL over stdin/stdout |
| **非同期** | asyncio (Python) / async generators (TS) | anyio / async generators |

## パッケージ

| 項目 | Codex SDK | Claude Agent SDK |
|------|-----------|------------------|
| **Python (公式)** | `@openai/codex-sdk` (未公開) | [`claude-agent-sdk`](https://pypi.org/project/claude-agent-sdk/) |
| **TypeScript (公式)** | [`@openai/codex-sdk`](https://www.npmjs.com/package/@openai/codex-sdk) | [`@anthropic-ai/claude-agent-sdk`](https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk) |
| **Python (軽量版)** | [`codex-sdk-py`](https://pypi.org/project/codex-sdk-py/) | - |
| **TypeScript (軽量版)** | [`codex-sdk-ts`](https://www.npmjs.com/package/codex-sdk-ts) | - |

## API設計

### Codex SDK

```python
# メインクラス
from codex_sdk import Codex

codex = Codex()
thread = codex.start_thread()

# 同期的な実行
turn = await thread.run("Do something")
print(turn.final_response)

# ストリーミング実行
streamed = await thread.run_streamed("Do something")
async for event in streamed.events:
    print(event)
```

### Claude Agent SDK

```python
# シンプルAPI
from claude_agent_sdk import query

async for message in query(prompt="Do something"):
    print(message)

# 双方向ストリーミング
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(...)
async with ClaudeSDKClient(options=options) as client:
    await client.query("Do something")
    async for msg in client.receive_response():
        print(msg)
```

## コンセプトの対応

| Codex SDK | Claude Agent SDK | 説明 |
|-----------|------------------|------|
| `Codex` | `ClaudeSDKClient` | メインクライアントクラス |
| `Thread` | - | 会話スレッド管理 |
| `Turn` | - | 1回の実行結果 |
| `ThreadEvent` | `Message` | イベント/メッセージ |
| `ThreadItem` | `ContentBlock` | コンテンツ単位 |
| `CodexOptions` | `ClaudeAgentOptions` | 設定オプション |

## イベント/メッセージ型

### Codex SDK (8種)

| イベント | 説明 |
|----------|------|
| `ThreadStartedEvent` | スレッド開始 |
| `TurnStartedEvent` | ターン開始 |
| `TurnCompletedEvent` | ターン完了 |
| `TurnFailedEvent` | ターン失敗 |
| `ItemStartedEvent` | アイテム開始 |
| `ItemUpdatedEvent` | アイテム更新 |
| `ItemCompletedEvent` | アイテム完了 |
| `ThreadErrorEvent` | エラー発生 |

### Claude Agent SDK (4種)

| メッセージ | 説明 |
|------------|------|
| `AssistantMessage` | Claude の応答 |
| `UserMessage` | ユーザー入力 |
| `SystemMessage` | システム指示 |
| `ResultMessage` | ツール実行結果 |

## アイテム/コンテンツブロック

### Codex SDK (8種)

| アイテム | 説明 |
|----------|------|
| `AgentMessageItem` | エージェントの応答テキスト |
| `ReasoningItem` | 推論サマリー |
| `CommandExecutionItem` | シェルコマンド実行 |
| `FileChangeItem` | ファイル変更 |
| `McpToolCallItem` | MCP ツール呼び出し |
| `WebSearchItem` | Web 検索 |
| `TodoListItem` | タスクリスト |
| `ErrorItem` | エラー情報 |

### Claude Agent SDK (3種)

| コンテンツブロック | 説明 |
|--------------------|------|
| `TextBlock` | テキスト応答 |
| `ToolUseBlock` | ツール呼び出し要求 |
| `ToolResultBlock` | ツール実行結果 |

## 設定オプション

### Codex SDK

```python
codex = Codex({
    "codex_path_override": "/path/to/codex",  # CLI パス
    "base_url": "https://api.openai.com",      # API ベース URL
    "api_key": "...",                          # API キー
    "env": {"PATH": "/usr/local/bin"},         # 環境変数
    "config": {                                 # CLI 設定オーバーライド
        "mcp_servers": {...},
        "show_raw_agent_reasoning": True,
    },
})

thread = codex.start_thread({
    "model": "gpt-4o",
    "sandbox_mode": SandboxMode.WORKSPACE_WRITE,
    "working_directory": "/path/to/project",
    "approval_policy": ApprovalMode.ON_FAILURE,
    "web_search_mode": WebSearchMode.LIVE,
})
```

### Claude Agent SDK

```python
options = ClaudeAgentOptions(
    cli_path="/path/to/claude",           # CLI パス
    system_prompt="You are a helper",     # システムプロンプト
    max_turns=10,                         # 最大ターン数
    allowed_tools=["Read", "Write"],      # 許可ツール
    permission_mode='acceptEdits',        # 権限モード
    cwd="/path/to/project",               # 作業ディレクトリ
    mcp_servers={...},                    # MCP サーバー
    hooks={...},                          # フック
)
```

## MCP サーバー設定

### Codex SDK

```python
codex = Codex({
    "config": {
        "mcp_servers": {
            "playwright": {
                "command": "npx",
                "args": ["-y", "@playwright/mcp@latest"]
            }
        }
    }
})
```

### Claude Agent SDK

```python
# 外部 MCP サーバー
options = ClaudeAgentOptions(
    mcp_servers={
        "playwright": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"]
        }
    }
)

# インプロセス SDK MCP サーバー (Claude 専用機能)
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("greet", "Greet a user", {"name": str})
async def greet_user(args):
    return {"content": [{"type": "text", "text": f"Hello, {args['name']}!"}]}

server = create_sdk_mcp_server(
    name="my-tools",
    version="1.0.0",
    tools=[greet_user]
)

options = ClaudeAgentOptions(
    mcp_servers={"tools": server}
)
```

## 固有機能

### Codex SDK のみ

| 機能 | 説明 |
|------|------|
| **Thread/Turn モデル** | 会話を Thread として管理し、各実行を Turn として追跡 |
| **Resume Thread** | `resume_thread(thread_id)` で過去の会話を再開 |
| **Web Search** | `WebSearchMode` による Web 検索機能 |
| **Structured Output** | JSON スキーマによる出力形式指定 |
| **Model Reasoning Effort** | 推論の深さを調整 (`minimal` ~ `xhigh`) |

### Claude Agent SDK のみ

| 機能 | 説明 |
|------|------|
| **query() 関数** | シンプルなワンショット API |
| **Hooks** | `PreToolUse` / `PostToolUse` フックで処理をカスタマイズ |
| **In-process MCP** | Python 関数を直接 MCP ツールとして登録 |
| **Bundled CLI** | パッケージにバイナリ同梱 (別途インストール不要) |

## エラー処理

### Codex SDK

```python
try:
    turn = await thread.run("...")
except RuntimeError as e:
    print(f"CLI error: {e}")
except asyncio.CancelledError:
    print("Cancelled")
```

### Claude Agent SDK

```python
from claude_agent_sdk import (
    ClaudeSDKError,
    CLINotFoundError,
    CLIConnectionError,
    ProcessError,
    CLIJSONDecodeError,
)

try:
    async for msg in query(...):
        ...
except CLINotFoundError:
    print("Claude Code not installed")
except ProcessError as e:
    print(f"Process error: {e}")
```

## キャンセル機構

### Codex SDK

```python
cancel_event = asyncio.Event()

# 別タスクでキャンセル
asyncio.get_event_loop().call_later(5, cancel_event.set)

turn = await thread.run("...", {"cancel_event": cancel_event})
```

### Claude Agent SDK

```python
# ClaudeSDKClient のコンテキストマネージャーで自動クリーンアップ
async with ClaudeSDKClient(options=options) as client:
    await client.query("...")
    # スコープを抜けると自動的に終了
```

## まとめ

| 観点 | Codex SDK | Claude Agent SDK |
|------|-----------|------------------|
| **API の複雑さ** | シンプル (Thread/Turn) | 2種類の API (query / Client) |
| **設定の柔軟性** | 高い (--config) | 高い (hooks, in-process MCP) |
| **カスタムツール** | 外部 MCP のみ | 外部 MCP + インプロセス |
| **バイナリ配布** | 別途インストール | パッケージに同梱 |
| **会話の永続化** | Thread ID で再開可能 | なし (クライアント側で管理) |

両 SDK とも、それぞれの AI エージェント (Codex / Claude Code) を呼び出すためのラッパーであり、基本的なアーキテクチャは類似しています。主な違いは、カスタムツールの実装方法とセッション管理のアプローチにあります。
