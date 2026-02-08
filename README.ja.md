# Codex SDK for Python

OpenAI Codex エージェントをワークフローやアプリに組み込むための Python SDK です。

システムにインストールされた `codex` コマンドを PATH から検索する軽量版です（バイナリ同梱なし）。

## 互換性

| 項目 | バージョン |
|------|---------|
| **ベース** | [@openai/codex-sdk](https://github.com/openai/codex/tree/main/sdk/typescript) @ コミット `9327e99b2` |
| **Codex CLI** | v0.98.0 以上（`--json` フラグのサポートが必要） |
| **Python** | 3.10 以上 |

この SDK は上流の OpenAI Codex SDK と定期的に同期されています。更新状況は [upstream sync workflow](.github/workflows/upstream-sync.yml) をご確認ください。

## 関連 SDK

| 言語 | パッケージ | リポジトリ |
|----------|---------|------------|
| **Python** | [`codex-sdk-py`](https://pypi.org/project/codex-sdk-py/) | [nogataka/codex-sdk-py](https://github.com/nogataka/codex-sdk-py) |
| **TypeScript** | [`codex-sdk-ts`](https://www.npmjs.com/package/codex-sdk-ts) | [nogataka/codex-sdk-ts](https://github.com/nogataka/codex-sdk-ts) |

両 SDK は同一の機能と API 設計を持っています。お好みの言語をお選びください。

## OpenAI 公式 TypeScript SDK との互換性

この Python SDK は [OpenAI 公式 Codex TypeScript SDK](https://github.com/openai/codex/tree/main/sdk/typescript) を完全にポーティングしており、**すべての機能・データ構造・動作が漏れなく実装されています**。

**公式 SDK から完全移植:**
- 全 8 種のイベント型（ThreadStartedEvent, TurnCompletedEvent など）
- 全 8 種のアイテム型（AgentMessageItem, CommandExecutionItem など）
- 全 4 種の Enum（ApprovalMode, SandboxMode, ModelReasoningEffort, WebSearchMode）
- CLI 引数の構築ロジック、環境変数の処理、TOML 設定シリアライズ

**本 SDK 独自の追加機能:**
- バイナリ同梱なしの軽量設計（システムにインストールされた Codex CLI を使用）
- `--config` オーバーライドによる MCP サーバー設定
- 公式 SDK の変更を追跡する Upstream Sync ワークフロー

詳細な比較は [docs/typescript-python-comparison.md](docs/typescript-python-comparison.md) を参照してください。

## インストール

```bash
pip install codex-sdk-py
```

Python 3.10 以上が必要です。

## クイックスタート

```python
import asyncio
from codex_sdk import Codex

async def main():
    codex = Codex()
    thread = codex.start_thread()
    turn = await thread.run("テスト失敗を診断して修正案を提案して")

    print(turn.final_response)
    print(turn.items)

asyncio.run(main())
```

同じ `Thread` インスタンスで `run()` を繰り返し呼び出すことで、会話を継続できます。

```python
next_turn = await thread.run("修正を実装して")
```

### ストリーミングレスポンス

`run()` はターン終了までイベントをバッファリングします。ツール呼び出し、ストリーミングレスポンス、ファイル変更通知などの中間進捗に反応するには、代わりに `run_streamed()` を使用してください。構造化イベントの非同期ジェネレータを返します。

```python
async def stream_example():
    codex = Codex()
    thread = codex.start_thread()

    streamed = await thread.run_streamed("テスト失敗を診断して修正案を提案して")

    async for event in streamed.events:
        match event.get("type"):
            case "item.completed":
                print("item", event.get("item"))
            case "turn.completed":
                print("usage", event.get("usage"))
```

### 構造化出力

Codex エージェントは、指定されたスキーマに準拠した JSON レスポンスを生成できます。スキーマは各ターンにプレーンな JSON オブジェクトとして提供できます。

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

turn = await thread.run("リポジトリのステータスを要約して", {"output_schema": schema})
print(turn.final_response)
```

[Pydantic モデル](https://docs.pydantic.dev/) から `model_json_schema()` を使用して JSON スキーマを作成することもできます。

```python
from pydantic import BaseModel
from typing import Literal

class StatusResponse(BaseModel):
    summary: str
    status: Literal["ok", "action_required"]

turn = await thread.run(
    "リポジトリのステータスを要約して",
    {"output_schema": StatusResponse.model_json_schema()}
)
print(turn.final_response)
```

### 画像の添付

テキストと一緒に画像を含める場合は、構造化入力エントリを提供します。テキストエントリは最終プロンプトに連結され、画像エントリは `--image` 経由で Codex CLI に渡されます。

```python
turn = await thread.run([
    {"type": "text", "text": "これらのスクリーンショットを説明して"},
    {"type": "local_image", "path": "./ui.png"},
    {"type": "local_image", "path": "./diagram.jpg"},
])
```

### 既存スレッドの再開

スレッドは `~/.codex/sessions` に保存されます。メモリ上の `Thread` オブジェクトを失った場合は、`resume_thread()` で再構築して続行できます。

```python
import os

saved_thread_id = os.environ["CODEX_THREAD_ID"]
thread = codex.resume_thread(saved_thread_id)
await thread.run("修正を実装して")
```

### 作業ディレクトリの制御

Codex はデフォルトでカレントディレクトリで実行されます。回復不能なエラーを避けるため、Codex は作業ディレクトリが Git リポジトリであることを要求します。スレッド作成時に `skip_git_repo_check` オプションを渡すことで、Git リポジトリチェックをスキップできます。

```python
thread = codex.start_thread({
    "working_directory": "/path/to/project",
    "skip_git_repo_check": True,
})
```

### サンドボックスモード

`sandbox_mode` を使用して、エージェントがファイルシステムとどのように対話するかを制御します。

```python
from codex_sdk import Codex, SandboxMode

thread = codex.start_thread({
    "sandbox_mode": SandboxMode.WORKSPACE_WRITE,
})
```

利用可能なモード:
- `SandboxMode.READ_ONLY` - エージェントはファイルの読み取りのみ可能
- `SandboxMode.WORKSPACE_WRITE` - エージェントはワークスペース内で読み書き可能
- `SandboxMode.DANGER_FULL_ACCESS` - 完全なファイルシステムアクセス（注意して使用）

### 承認ポリシー

エージェントがアクションに対して承認を必要とするタイミングを制御します。

```python
from codex_sdk import Codex, ApprovalMode

thread = codex.start_thread({
    "approval_policy": ApprovalMode.ON_FAILURE,
})
```

利用可能なモード:
- `ApprovalMode.NEVER` - 承認を必要としない
- `ApprovalMode.ON_REQUEST` - 明示的なリクエスト時に承認
- `ApprovalMode.ON_FAILURE` - 失敗後に承認
- `ApprovalMode.UNTRUSTED` - 常に承認が必要

### ターンのキャンセル

`asyncio.Event` を使用して進行中のターンをキャンセルします（TypeScript の `AbortSignal` に相当）。

```python
import asyncio

async def cancellable_example():
    codex = Codex()
    thread = codex.start_thread()

    cancel_event = asyncio.Event()

    async def cancel_after_delay():
        await asyncio.sleep(5)
        cancel_event.set()

    # キャンセルタイマーを開始
    asyncio.create_task(cancel_after_delay())

    try:
        turn = await thread.run(
            "長時間実行タスク",
            {"cancel_event": cancel_event}
        )
    except asyncio.CancelledError:
        print("ターンがキャンセルされました")
```

### Codex CLI 環境の制御

デフォルトでは、Codex CLI は Python プロセス環境を継承します。`Codex` クライアントのインスタンス化時にオプションの `env` パラメータを提供することで、CLI が受け取る変数を完全に制御できます。サンドボックス化されたホストに便利です。

```python
codex = Codex({
    "env": {
        "PATH": "/usr/local/bin",
    },
})
```

SDK は、提供した環境の上に必要な変数（`OPENAI_BASE_URL` や `CODEX_API_KEY` など）を引き続き注入します。

### `--config` オーバーライドの渡し方

`config` オプションを使用して、追加の Codex CLI 設定オーバーライドを提供します。SDK は dict を受け取り、ドット区切りのパスにフラット化し、値を TOML リテラルとしてシリアル化してから、繰り返しの `--config key=value` フラグとして渡します。

```python
codex = Codex({
    "config": {
        "show_raw_agent_reasoning": True,
        "sandbox_workspace_write": {"network_access": True},
    },
})
```

スレッドオプションは、グローバルオーバーライドの後に出力されるため、重複する設定に対して優先されます。

### MCP サーバー設定

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) サーバーを設定して、外部ツールで Codex の機能を拡張します。

```python
codex = Codex({
    "config": {
        "mcp_servers": {
            "playwright": {
                "command": "npx",
                "args": ["-y", "@playwright/mcp@latest"]
            },
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@anthropic/mcp-server-filesystem@latest", "/path/to/dir"]
            }
        }
    }
})
```

`mcp_servers` 設定はインライン TOML テーブルとしてシリアル化され、グローバル Codex 設定を変更することなく MCP サーバーを動的に設定できます。

## API リファレンス

### クラス

#### `Codex`
SDK のメインエントリーポイント。

```python
codex = Codex(options: CodexOptions | None = None)
```

メソッド:
- `start_thread(options: ThreadOptions | None = None) -> Thread` - 新しい会話を開始
- `resume_thread(thread_id: str, options: ThreadOptions | None = None) -> Thread` - 既存の会話を再開

#### `Thread`
エージェントとの会話を表します。

プロパティ:
- `id: str | None` - スレッド ID（最初のターン後に設定）

メソッド:
- `async run(input: Input, turn_options: TurnOptions | None = None) -> Turn` - ターンを実行して結果を返す
- `async run_streamed(input: Input, turn_options: TurnOptions | None = None) -> StreamedTurn` - ストリーミングイベント付きでターンを実行

#### `Turn`
完了したターンの結果。

```python
@dataclass
class Turn:
    items: list[ThreadItem]      # ターン中に生成されたすべてのアイテム
    final_response: str          # エージェントの最終レスポンステキスト
    usage: Usage | None          # トークン使用統計
```

#### `StreamedTurn`
ストリーミングターンの結果。

```python
@dataclass
class StreamedTurn:
    events: AsyncGenerator[ThreadEvent, None]  # イベントの非同期ジェネレータ
```

### 型

#### 入力型
- `Input = str | list[UserInput]` - ユーザー入力（文字列または構造化）
- `TextUserInput` - テキスト入力: `{"type": "text", "text": "..."}`
- `ImageUserInput` - 画像入力: `{"type": "local_image", "path": "..."}`

#### イベント型
- `ThreadStartedEvent` - スレッド開始
- `TurnStartedEvent` - ターン開始
- `TurnCompletedEvent` - ターン完了（usage を含む）
- `TurnFailedEvent` - ターン失敗（エラーを含む）
- `ItemStartedEvent` - アイテム開始
- `ItemUpdatedEvent` - アイテム更新
- `ItemCompletedEvent` - アイテム完了
- `ThreadErrorEvent` - 回復不能なエラー

#### アイテム型
- `AgentMessageItem` - エージェントのレスポンステキスト
- `ReasoningItem` - エージェントの推論サマリー
- `CommandExecutionItem` - シェルコマンド実行
- `FileChangeItem` - ファイル変更
- `McpToolCallItem` - MCP ツール呼び出し
- `WebSearchItem` - Web 検索クエリ
- `TodoListItem` - エージェントのタスクリスト
- `ErrorItem` - 非致命的エラー

### Enum

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

## 開発

### セットアップ

```bash
# リポジトリをクローン
git clone https://github.com/nogataka/codex-sdk-py.git
cd codex-sdk-py

# 開発依存関係をインストール
pip install -e ".[dev]"
```

### テストの実行

```bash
pytest tests/ -v
```

### リントとフォーマット

```bash
# リント
ruff check codex_sdk/

# フォーマット
ruff format codex_sdk/

# 型チェック
mypy codex_sdk/
```

## リリースプロセス

リリースは GitHub Actions で自動化されています。

### リリースの作成

1. `codex_sdk/__init__.py` のバージョンを更新:
   ```python
   __version__ = "0.1.0"
   ```

2. バージョン変更をコミット:
   ```bash
   git add codex_sdk/__init__.py
   git commit -m "Bump version to 0.1.0"
   ```

3. タグを作成してプッシュ:
   ```bash
   git tag v0.1.0
   git push origin main --tags
   ```

4. GitHub Actions が自動的に以下を実行:
   - パッケージのビルド
   - PyPI への公開
   - GitHub Release の作成

### 必要なシークレット

GitHub リポジトリに以下のシークレットを設定してください:

- `PYPI_TOKEN`: パッケージ公開用の PyPI API トークン

PyPI トークンの作成方法:
1. https://pypi.org/manage/account/token/ にアクセス
2. 「Upload packages」スコープで新しいトークンを作成
3. GitHub リポジトリのシークレットに追加

## ライセンス

Apache-2.0
