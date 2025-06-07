# OpenManus 新ツール使用ガイド

OpenManus に追加された 20 個の新しいツールの詳細な使用方法とワークフロー例を説明します。

## ツール一覧と主要機能

### 1. Database Manager (`database_manager`)

SQLite データベースの包括的な管理ツール

**主要コマンド:**

- `connect`: データベース接続
- `query`: SELECT クエリ実行
- `execute_sql`: INSERT/UPDATE/DELETE 実行
- `create_table`: テーブル作成
- `backup`: データベースバックアップ
- `export_data`: データエクスポート (CSV, JSON, Excel)

**使用例:**

```python
# データベース接続とテーブル作成
database_manager(command="connect", database_path="./project.db")
database_manager(command="create_table", table_name="users",
                schema={"id": "INTEGER PRIMARY KEY", "name": "TEXT", "email": "TEXT"})

# データ挿入とクエリ
database_manager(command="insert", table="users",
                data={"name": "John Doe", "email": "john@example.com"})
database_manager(command="query", sql="SELECT * FROM users WHERE name LIKE '%John%'")
```

### 2. API Tester (`api_tester`)

REST API の総合テストツール

**主要コマンド:**

- `request`: HTTP リクエスト送信
- `test_endpoint`: エンドポイントテスト
- `load_test`: 負荷テスト
- `health_check`: ヘルスチェック
- `validate_response`: レスポンス検証

**使用例:**

```python
# API エンドポイントテスト
api_tester(command="test_endpoint",
          url="https://api.example.com/users",
          method="GET",
          expected_status=200)

# 負荷テスト実行
api_tester(command="load_test",
          url="https://api.example.com/endpoint",
          concurrent_users=10,
          duration=60)
```

### 3. File Compressor (`file_compressor`)

多形式ファイル圧縮・解凍ツール

**主要コマンド:**

- `compress`: ファイル・ディレクトリ圧縮
- `decompress`: アーカイブ解凍
- `list_contents`: アーカイブ内容表示
- `add_files`: アーカイブにファイル追加

**使用例:**

```python
# ディレクトリ圧縮
file_compressor(command="compress",
               source_path="./project",
               output_path="./project.zip",
               format="zip")

# 圧縮率比較
file_compressor(command="compare_sizes",
               source_path="./data",
               formats=["zip", "tar.gz", "7z"])
```

### 4. Network Scanner (`network_scanner`)

ネットワーク診断・スキャンツール

**主要コマンド:**

- `ping`: ホスト ping テスト
- `port_scan`: ポートスキャン
- `network_scan`: ネットワークスキャン
- `traceroute`: 経路追跡
- `dns_lookup`: DNS 解決

**使用例:**

```python
# ネットワーク診断
network_scanner(command="ping", host="google.com", count=4)
network_scanner(command="port_scan", host="192.168.1.1", ports=[22, 80, 443])

# ローカルネットワークスキャン
network_scanner(command="network_scan", network="192.168.1.0/24")
```

### 5. Code Formatter (`code_formatter`)

多言語コード整形・リファクタリングツール

**主要コマンド:**

- `format_code`: コード整形
- `lint_code`: 静的解析
- `format_directory`: ディレクトリ一括整形
- `detect_language`: 言語自動検出
- `optimize_imports`: import 最適化

**使用例:**

```python
# Python コード整形
code_formatter(command="format_code",
              code="def hello():print('world')",
              language="python")

# プロジェクト全体の整形
code_formatter(command="format_directory",
              directory="./src",
              language="python",
              recursive=True)
```

### 6. Document Generator (`document_generator`)

ドキュメント自動生成ツール

**主要コマンド:**

- `generate_readme`: README 生成
- `generate_api_docs`: API ドキュメント生成
- `create_template`: テンプレート作成
- `convert_format`: フォーマット変換
- `generate_changelog`: 変更履歴生成

**使用例:**

```python
# README 自動生成
document_generator(command="generate_readme",
                  project_path="./project",
                  template="standard")

# API ドキュメント生成
document_generator(command="generate_api_docs",
                  source_files=["./api/*.py"],
                  output_format="markdown")
```

### 7. Task Scheduler (`task_scheduler`)

タスクスケジューリング・自動化ツール

**主要コマンド:**

- `create_task`: タスク作成
- `schedule_task`: スケジュール設定
- `start_scheduler`: スケジューラ開始
- `get_history`: 実行履歴確認

**使用例:**

```python
# 定期タスク作成
task_scheduler(command="create_task",
              task_id="backup_daily",
              command="backup_manager",
              parameters={"source": "./data", "destination": "./backups"})

# cron風スケジュール設定
task_scheduler(command="schedule_task",
              task_id="backup_daily",
              schedule="0 2 * * *")  # 毎日午前2時
```

### 8. Data Validator (`data_validator`)

データ検証・品質チェックツール

**主要コマンド:**

- `validate_data`: データ検証
- `validate_schema`: スキーマ検証
- `check_data_quality`: データ品質チェック
- `detect_anomalies`: 異常値検出

**使用例:**

```python
# CSV データ検証
data_validator(command="validate_data",
              data_source="./data.csv",
              validation_rules={"email": "email_format", "age": "positive_integer"})

# 異常値検出
data_validator(command="detect_anomalies",
              data_source="./metrics.json",
              method="statistical")
```

### 9. Performance Benchmark (`performance_benchmark`)

システムパフォーマンス測定ツール

**主要コマンド:**

- `cpu_benchmark`: CPU ベンチマーク
- `memory_benchmark`: メモリベンチマーク
- `disk_benchmark`: ディスクベンチマーク
- `network_benchmark`: ネットワークベンチマーク
- `stress_test`: ストレステスト

**使用例:**

```python
# システム総合ベンチマーク
performance_benchmark(command="system_info")
performance_benchmark(command="cpu_benchmark", duration=30)
performance_benchmark(command="memory_benchmark", test_size="1GB")

# ベースライン保存・比較
performance_benchmark(command="save_baseline", name="initial")
```

### 10. Security Scanner (`security_scanner`)

セキュリティ脆弱性スキャンツール

**主要コマンド:**

- `scan_file`: ファイルスキャン
- `scan_directory`: ディレクトリスキャン
- `check_password`: パスワード強度チェック
- `encrypt_file`: ファイル暗号化
- `vulnerability_report`: 脆弱性レポート

**使用例:**

```python
# プロジェクトセキュリティスキャン
security_scanner(command="scan_directory",
                directory="./project",
                scan_types=["secrets", "vulnerabilities", "permissions"])

# ファイル暗号化
security_scanner(command="encrypt_file",
                file_path="./sensitive.txt",
                password="strong_password")
```

## ワークフロー例

### 開発環境セットアップワークフロー

```python
# 1. 環境作成
environment_manager(command="create_env", env_name="myproject", python_version="3.9")

# 2. 依存関係インストール
environment_manager(command="install_packages", packages=["flask", "requests", "pytest"])

# 3. 依存関係解析
dependency_checker(command="analyze_dependencies", project_path=".")

# 4. セキュリティチェック
dependency_checker(command="check_vulnerabilities")
```

### CI/CD パイプラインワークフロー

```python
# 1. コード品質チェック
code_formatter(command="format_directory", directory="./src")
code_formatter(command="lint_code", directory="./src")

# 2. テスト実行
test_runner(command="discover_tests", project_path=".")
test_runner(command="run_coverage", min_coverage=80.0)

# 3. セキュリティスキャン
security_scanner(command="scan_directory", directory="./src")

# 4. パフォーマンステスト
performance_benchmark(command="stress_test", duration=300)

# 5. 通知送信
notification_sender(command="send_alert",
                   alert_type="deployment",
                   severity="info",
                   message="CI/CD pipeline completed successfully",
                   recipients=["team@example.com"])
```

### システム保守ワークフロー

```python
# 1. システム状態確認
metrics_collector(command="system_health")
resource_optimizer(command="analyze_resources")

# 2. バックアップ作成
backup_manager(command="create_backup",
              source_paths=["./data", "./config"],
              backup_name="daily_backup")

# 3. ログローテーション
log_rotator(command="rotate_log", log_file="./logs/app.log")
log_rotator(command="cleanup_logs", max_age_days=30)

# 4. リソース最適化
resource_optimizer(command="auto_optimize", aggressive=False)

# 5. メトリクス収集
metrics_collector(command="start_collection", interval=60)
```

### データ処理ワークフロー

```python
# 1. データ検証
data_validator(command="validate_data", data_source="./input.csv")

# 2. データベース処理
database_manager(command="connect", database_path="./analytics.db")
database_manager(command="import_data", source_file="./input.csv", table="raw_data")

# 3. データ変換・分析
database_manager(command="query",
                sql="SELECT category, COUNT(*) FROM raw_data GROUP BY category")

# 4. 結果エクスポート
database_manager(command="export_data",
                table="analysis_results",
                output_file="./results.xlsx",
                format="excel")

# 5. レポート生成
document_generator(command="generate_report",
                  data_source="./results.xlsx",
                  template="analytics_report")
```

## 自動化・統合例

### Workflow Automator を使った複合ワークフロー

```python
# 複雑なワークフローの定義
workflow_automator(command="create_workflow",
                  name="daily_maintenance",
                  description="Daily system maintenance workflow",
                  tasks=[
                      {
                          "name": "system_check",
                          "task_type": "shell_command",
                          "parameters": {"command": "resource_optimizer analyze_resources"},
                          "dependencies": []
                      },
                      {
                          "name": "backup_data",
                          "task_type": "shell_command",
                          "parameters": {"command": "backup_manager create_backup"},
                          "dependencies": ["system_check"]
                      },
                      {
                          "name": "send_notification",
                          "task_type": "notification",
                          "parameters": {"message": "Daily maintenance completed"},
                          "dependencies": ["backup_data"]
                      }
                  ])

# ワークフロー実行
workflow_automator(command="run_workflow", workflow_id="daily_maintenance")
```

このガイドは、OpenManus の新しいツール群を効果的に活用するための包括的なリファレンスです。各ツールの詳細な使用方法については、個別のコマンドヘルプも参照してください。
