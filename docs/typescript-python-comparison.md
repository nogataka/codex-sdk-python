# TypeScript SDK vs Python SDK 仕様比較

このドキュメントでは、[TypeScript版 Codex SDK](https://github.com/openai/codex/tree/main/sdk/typescript) と Python版 Codex SDK の仕様が完全に一致していることを示します。

## 概要

Python版 SDK は TypeScript版 SDK を1対1でポーティングしており、**全ての機能・データ構造・動作が同一**です。

## ファイル対応表

| TypeScript | Python | 説明 |
|------------|--------|------|
| `src/index.ts` | `codex_sdk/__init__.py` | エクスポート定義 |
| `src/codex.ts` | `codex_sdk/codex.py` | Codex クラス |
| `src/thread.ts` | `codex_sdk/thread.py` | Thread クラス |
| `src/exec.ts` | `codex_sdk/exec.py` | CodexExec クラス |
| `src/events.ts` | `codex_sdk/events.py` | イベント型定義 |
| `src/items.ts` | `codex_sdk/items.py` | アイテム型定義 |
| `src/codexOptions.ts` | `codex_sdk/codex_options.py` | CodexOptions |
| `src/threadOptions.ts` | `codex_sdk/thread_options.py` | ThreadOptions |
| `src/turnOptions.ts` | `codex_sdk/turn_options.py` | TurnOptions |
| `src/outputSchemaFile.ts` | `codex_sdk/output_schema_file.py` | スキーマファイル処理 |

## 詳細比較

### 1. Codex クラス

| 機能 | TypeScript | Python | 状態 |
|------|------------|--------|------|
| コンストラクタ | `new Codex(options?)` | `Codex(options?)` | ✅ 一致 |
| スレッド開始 | `startThread(options?)` | `start_thread(options?)` | ✅ 一致 |
| スレッド再開 | `resumeThread(id, options?)` | `resume_thread(thread_id, options?)` | ✅ 一致 |

### 2. Thread クラス

| 機能 | TypeScript | Python | 状態 |
|------|------------|--------|------|
| ID取得 | `thread.id` | `thread.id` | ✅ 一致 |
| 実行 | `run(input, turnOptions?)` | `run(input_data, turn_options?)` | ✅ 一致 |
| ストリーミング実行 | `runStreamed(input, turnOptions?)` | `run_streamed(input_data, turn_options?)` | ✅ 一致 |

### 3. 入力型 (Input Types)

| 型 | TypeScript | Python | 状態 |
|----|------------|--------|------|
| テキスト入力 | `{ type: "text", text: string }` | `TextUserInput` | ✅ 一致 |
| 画像入力 | `{ type: "local_image", path: string }` | `ImageUserInput` | ✅ 一致 |
| 入力Union | `string \| UserInput[]` | `str \| list[UserInput]` | ✅ 一致 |

### 4. イベント型 (Event Types) - 全8種

| イベント | type値 | 状態 |
|----------|--------|------|
| ThreadStartedEvent | `"thread.started"` | ✅ 一致 |
| TurnStartedEvent | `"turn.started"` | ✅ 一致 |
| TurnCompletedEvent | `"turn.completed"` | ✅ 一致 |
| TurnFailedEvent | `"turn.failed"` | ✅ 一致 |
| ItemStartedEvent | `"item.started"` | ✅ 一致 |
| ItemUpdatedEvent | `"item.updated"` | ✅ 一致 |
| ItemCompletedEvent | `"item.completed"` | ✅ 一致 |
| ThreadErrorEvent | `"error"` | ✅ 一致 |

### 5. アイテム型 (Item Types) - 全8種

| アイテム | type値 | 状態 |
|----------|--------|------|
| AgentMessageItem | `"agent_message"` | ✅ 一致 |
| ReasoningItem | `"reasoning"` | ✅ 一致 |
| CommandExecutionItem | `"command_execution"` | ✅ 一致 |
| FileChangeItem | `"file_change"` | ✅ 一致 |
| McpToolCallItem | `"mcp_tool_call"` | ✅ 一致 |
| WebSearchItem | `"web_search"` | ✅ 一致 |
| TodoListItem | `"todo_list"` | ✅ 一致 |
| ErrorItem | `"error"` | ✅ 一致 |

### 6. Enum値 - 全4種

#### ApprovalMode
| TypeScript | Python | 値 |
|------------|--------|-----|
| `"never"` | `ApprovalMode.NEVER` | `"never"` |
| `"on-request"` | `ApprovalMode.ON_REQUEST` | `"on-request"` |
| `"on-failure"` | `ApprovalMode.ON_FAILURE` | `"on-failure"` |
| `"untrusted"` | `ApprovalMode.UNTRUSTED` | `"untrusted"` |

#### SandboxMode
| TypeScript | Python | 値 |
|------------|--------|-----|
| `"read-only"` | `SandboxMode.READ_ONLY` | `"read-only"` |
| `"workspace-write"` | `SandboxMode.WORKSPACE_WRITE` | `"workspace-write"` |
| `"danger-full-access"` | `SandboxMode.DANGER_FULL_ACCESS` | `"danger-full-access"` |

#### ModelReasoningEffort
| TypeScript | Python | 値 |
|------------|--------|-----|
| `"minimal"` | `ModelReasoningEffort.MINIMAL` | `"minimal"` |
| `"low"` | `ModelReasoningEffort.LOW` | `"low"` |
| `"medium"` | `ModelReasoningEffort.MEDIUM` | `"medium"` |
| `"high"` | `ModelReasoningEffort.HIGH` | `"high"` |
| `"xhigh"` | `ModelReasoningEffort.XHIGH` | `"xhigh"` |

#### WebSearchMode
| TypeScript | Python | 値 |
|------------|--------|-----|
| `"disabled"` | `WebSearchMode.DISABLED` | `"disabled"` |
| `"cached"` | `WebSearchMode.CACHED` | `"cached"` |
| `"live"` | `WebSearchMode.LIVE` | `"live"` |

### 7. CLI引数の構築

両SDKは同一のコマンドライン引数を構築します：

| 引数 | 状態 |
|------|------|
| `exec --experimental-json` | ✅ 一致 |
| `--model` | ✅ 一致 |
| `--sandbox` | ✅ 一致 |
| `--cd` | ✅ 一致 |
| `--add-dir` | ✅ 一致 |
| `--skip-git-repo-check` | ✅ 一致 |
| `--output-schema` | ✅ 一致 |
| `--config model_reasoning_effort="..."` | ✅ 一致 |
| `--config sandbox_workspace_write.network_access=...` | ✅ 一致 |
| `--config web_search="..."` | ✅ 一致 |
| `--config approval_policy="..."` | ✅ 一致 |
| `--image` | ✅ 一致 |
| `resume <thread_id>` | ✅ 一致 |

### 8. 環境変数

| 変数 | 状態 |
|------|------|
| `CODEX_INTERNAL_ORIGINATOR_OVERRIDE` | ✅ 一致 (値のみ異なる: `codex_sdk_ts` vs `codex_sdk_py`) |
| `OPENAI_BASE_URL` | ✅ 一致 |
| `CODEX_API_KEY` | ✅ 一致 |

### 9. TOML設定シリアライズ

設定オブジェクトのTOMLシリアライズロジックは完全に一致：
- ネストされたオブジェクトのドットパス展開
- 文字列、数値、真偽値、配列のTOMLリテラル変換
- キーのクォート処理

### 10. 出力スキーマファイル処理

| 機能 | 状態 |
|------|------|
| 一時ディレクトリ作成 | ✅ 一致 |
| JSONスキーマ書き込み | ✅ 一致 |
| クリーンアップ処理 | ✅ 一致 |

## 言語固有の差異（動作に影響なし）

以下は各言語の慣例に従った差異であり、機能的な違いはありません：

| 項目 | TypeScript | Python | 理由 |
|------|------------|--------|------|
| 命名規則 | `camelCase` | `snake_case` | 言語の慣例 |
| キャンセル機構 | `AbortSignal` | `asyncio.Event` | プラットフォーム標準 |
| エラー型 | `Error` | `RuntimeError` / `ValueError` | 言語標準 |
| Enum実装 | 文字列リテラルUnion | `StrEnum` | 型システムの違い |

## パッケージング方式の違い

| 項目 | TypeScript (npm) | Python (PyPI) |
|------|------------------|---------------|
| バイナリバンドル | `vendor/` にCodexバイナリを同梱 | バイナリは同梱しない |
| バイナリ検索 | バンドルパスのみ | PATHから検索 |

Python版では、Codex CLIをシステムに別途インストールし、PATHに通しておく必要があります。
SDKはシステムの `codex` コマンドを直接呼び出します。

## 結論

Python版 Codex SDK は TypeScript版と**完全に同一の仕様**を実装しています。
どちらのSDKを使用しても、同じ入力に対して同じ出力が得られます。
