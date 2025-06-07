"""
Database Manager Tool

データベース操作・管理を行うツール
接続管理、クエリ実行、スキーマ操作、データ操作などの機能を提供
"""

import asyncio
import json
import sqlite3
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import pandas as pd
from datetime import datetime

from .base import BaseTool

logger = logging.getLogger(__name__)

class DatabaseManager(BaseTool):
    """データベース管理ツール"""

    def __init__(self):
        super().__init__()
        self.connections = {}

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        データベース操作を実行

        Args:
            command: 実行するコマンド
            **kwargs: コマンド固有のパラメータ

        Returns:
            実行結果
        """
        try:
            if command == "connect":
                return await self._connect(**kwargs)
            elif command == "disconnect":
                return await self._disconnect(**kwargs)
            elif command == "query":
                return await self._query(**kwargs)
            elif command == "execute_sql":
                return await self._execute_sql(**kwargs)
            elif command == "create_table":
                return await self._create_table(**kwargs)
            elif command == "drop_table":
                return await self._drop_table(**kwargs)
            elif command == "insert":
                return await self._insert(**kwargs)
            elif command == "update":
                return await self._update(**kwargs)
            elif command == "delete":
                return await self._delete(**kwargs)
            elif command == "backup":
                return await self._backup(**kwargs)
            elif command == "restore":
                return await self._restore(**kwargs)
            elif command == "list_tables":
                return await self._list_tables(**kwargs)
            elif command == "describe_table":
                return await self._describe_table(**kwargs)
            elif command == "export_data":
                return await self._export_data(**kwargs)
            elif command == "import_data":
                return await self._import_data(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "connect", "disconnect", "query", "execute_sql",
                        "create_table", "drop_table", "insert", "update", "delete",
                        "backup", "restore", "list_tables", "describe_table",
                        "export_data", "import_data"
                    ]
                }

        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    async def _connect(self, db_path: str, connection_name: str = "default") -> Dict[str, Any]:
        """データベースに接続"""
        try:
            # SQLiteデータベースに接続
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # 辞書形式でアクセス可能

            self.connections[connection_name] = {
                "connection": conn,
                "db_path": db_path,
                "connected_at": datetime.now().isoformat()
            }

            return {
                "success": True,
                "message": f"Connected to database: {db_path}",
                "connection_name": connection_name,
                "db_path": db_path
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to connect to database: {e}"
            }

    async def _disconnect(self, connection_name: str = "default") -> Dict[str, Any]:
        """データベース接続を切断"""
        try:
            if connection_name not in self.connections:
                return {
                    "success": False,
                    "error": f"Connection '{connection_name}' not found"
                }

            self.connections[connection_name]["connection"].close()
            del self.connections[connection_name]

            return {
                "success": True,
                "message": f"Disconnected from '{connection_name}'"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to disconnect: {e}"
            }

    async def _query(self, sql: str, connection_name: str = "default",
                    params: Optional[List] = None) -> Dict[str, Any]:
        """SQLクエリを実行（SELECT）"""
        try:
            if connection_name not in self.connections:
                return {
                    "success": False,
                    "error": f"Connection '{connection_name}' not found"
                }

            conn = self.connections[connection_name]["connection"]
            cursor = conn.cursor()

            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            rows = cursor.fetchall()

            # 結果を辞書のリストに変換
            result = []
            for row in rows:
                result.append(dict(row))

            return {
                "success": True,
                "data": result,
                "row_count": len(result),
                "sql": sql
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Query failed: {e}",
                "sql": sql
            }

    async def _execute_sql(self, sql: str, connection_name: str = "default",
                          params: Optional[List] = None) -> Dict[str, Any]:
        """SQL文を実行（INSERT, UPDATE, DELETE, CREATE, DROP等）"""
        try:
            if connection_name not in self.connections:
                return {
                    "success": False,
                    "error": f"Connection '{connection_name}' not found"
                }

            conn = self.connections[connection_name]["connection"]
            cursor = conn.cursor()

            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)

            conn.commit()

            return {
                "success": True,
                "message": "SQL executed successfully",
                "rows_affected": cursor.rowcount,
                "sql": sql
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"SQL execution failed: {e}",
                "sql": sql
            }

    async def _create_table(self, table_name: str, columns: Dict[str, str],
                           connection_name: str = "default") -> Dict[str, Any]:
        """テーブルを作成"""
        try:
            # カラム定義を構築
            column_defs = []
            for col_name, col_type in columns.items():
                column_defs.append(f"{col_name} {col_type}")

            sql = f"CREATE TABLE {table_name} ({', '.join(column_defs)})"

            return await self._execute_sql(sql, connection_name)

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create table: {e}"
            }

    async def _drop_table(self, table_name: str,
                         connection_name: str = "default") -> Dict[str, Any]:
        """テーブルを削除"""
        try:
            sql = f"DROP TABLE {table_name}"
            return await self._execute_sql(sql, connection_name)

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to drop table: {e}"
            }

    async def _insert(self, table_name: str, data: Dict[str, Any],
                     connection_name: str = "default") -> Dict[str, Any]:
        """データを挿入"""
        try:
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ", ".join(["?" for _ in values])

            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

            return await self._execute_sql(sql, connection_name, values)

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to insert data: {e}"
            }

    async def _update(self, table_name: str, data: Dict[str, Any],
                     where_clause: str, connection_name: str = "default") -> Dict[str, Any]:
        """データを更新"""
        try:
            set_clauses = []
            values = []

            for col, val in data.items():
                set_clauses.append(f"{col} = ?")
                values.append(val)

            sql = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE {where_clause}"

            return await self._execute_sql(sql, connection_name, values)

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update data: {e}"
            }

    async def _delete(self, table_name: str, where_clause: str,
                     connection_name: str = "default") -> Dict[str, Any]:
        """データを削除"""
        try:
            sql = f"DELETE FROM {table_name} WHERE {where_clause}"
            return await self._execute_sql(sql, connection_name)

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to delete data: {e}"
            }

    async def _list_tables(self, connection_name: str = "default") -> Dict[str, Any]:
        """テーブル一覧を取得"""
        try:
            sql = "SELECT name FROM sqlite_master WHERE type='table'"
            result = await self._query(sql, connection_name)

            if result["success"]:
                tables = [row["name"] for row in result["data"]]
                return {
                    "success": True,
                    "tables": tables,
                    "count": len(tables)
                }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list tables: {e}"
            }

    async def _describe_table(self, table_name: str,
                             connection_name: str = "default") -> Dict[str, Any]:
        """テーブル構造を取得"""
        try:
            sql = f"PRAGMA table_info({table_name})"
            result = await self._query(sql, connection_name)

            if result["success"]:
                return {
                    "success": True,
                    "table_name": table_name,
                    "columns": result["data"]
                }
            else:
                return result

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to describe table: {e}"
            }

    async def _backup(self, connection_name: str = "default",
                     backup_path: str = None) -> Dict[str, Any]:
        """データベースをバックアップ"""
        try:
            if connection_name not in self.connections:
                return {
                    "success": False,
                    "error": f"Connection '{connection_name}' not found"
                }

            source_path = self.connections[connection_name]["db_path"]

            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{source_path}.backup_{timestamp}"

            # ファイルをコピー
            import shutil
            shutil.copy2(source_path, backup_path)

            return {
                "success": True,
                "message": "Database backed up successfully",
                "source_path": source_path,
                "backup_path": backup_path
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Backup failed: {e}"
            }

    async def _restore(self, backup_path: str, target_path: str) -> Dict[str, Any]:
        """バックアップからデータベースを復元"""
        try:
            import shutil
            shutil.copy2(backup_path, target_path)

            return {
                "success": True,
                "message": "Database restored successfully",
                "backup_path": backup_path,
                "target_path": target_path
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Restore failed: {e}"
            }

    async def _export_data(self, table_name: str, output_path: str,
                          format: str = "csv", connection_name: str = "default") -> Dict[str, Any]:
        """データをエクスポート"""
        try:
            # テーブルの全データを取得
            sql = f"SELECT * FROM {table_name}"
            result = await self._query(sql, connection_name)

            if not result["success"]:
                return result

            # DataFrameに変換
            df = pd.DataFrame(result["data"])

            # フォーマットに応じてエクスポート
            if format.lower() == "csv":
                df.to_csv(output_path, index=False)
            elif format.lower() == "json":
                df.to_json(output_path, orient="records", indent=2)
            elif format.lower() == "excel":
                df.to_excel(output_path, index=False)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format}"
                }

            return {
                "success": True,
                "message": f"Data exported to {output_path}",
                "table_name": table_name,
                "format": format,
                "row_count": len(df)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Export failed: {e}"
            }

    async def _import_data(self, table_name: str, input_path: str,
                          format: str = "csv", connection_name: str = "default") -> Dict[str, Any]:
        """データをインポート"""
        try:
            # フォーマットに応じてデータを読み込み
            if format.lower() == "csv":
                df = pd.read_csv(input_path)
            elif format.lower() == "json":
                df = pd.read_json(input_path)
            elif format.lower() == "excel":
                df = pd.read_excel(input_path)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported format: {format}"
                }

            # データベースに挿入
            if connection_name not in self.connections:
                return {
                    "success": False,
                    "error": f"Connection '{connection_name}' not found"
                }

            conn = self.connections[connection_name]["connection"]

            # DataFrameをSQLiteに挿入
            df.to_sql(table_name, conn, if_exists="append", index=False)

            return {
                "success": True,
                "message": f"Data imported from {input_path}",
                "table_name": table_name,
                "format": format,
                "row_count": len(df)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Import failed: {e}"
            }

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """各コマンドのパラメータ定義を返す"""
        return {
            "connect": {
                "db_path": {"type": "string", "required": True, "description": "データベースファイルのパス"},
                "connection_name": {"type": "string", "required": False, "description": "接続名（デフォルト: default）"}
            },
            "disconnect": {
                "connection_name": {"type": "string", "required": False, "description": "切断する接続名"}
            },
            "query": {
                "sql": {"type": "string", "required": True, "description": "実行するSQLクエリ"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"},
                "params": {"type": "array", "required": False, "description": "SQLパラメータ"}
            },
            "execute_sql": {
                "sql": {"type": "string", "required": True, "description": "実行するSQL文"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"},
                "params": {"type": "array", "required": False, "description": "SQLパラメータ"}
            },
            "create_table": {
                "table_name": {"type": "string", "required": True, "description": "作成するテーブル名"},
                "columns": {"type": "object", "required": True, "description": "カラム定義（名前: 型）"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"}
            },
            "drop_table": {
                "table_name": {"type": "string", "required": True, "description": "削除するテーブル名"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"}
            },
            "insert": {
                "table_name": {"type": "string", "required": True, "description": "挿入先テーブル名"},
                "data": {"type": "object", "required": True, "description": "挿入するデータ"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"}
            },
            "update": {
                "table_name": {"type": "string", "required": True, "description": "更新するテーブル名"},
                "data": {"type": "object", "required": True, "description": "更新するデータ"},
                "where_clause": {"type": "string", "required": True, "description": "WHERE条件"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"}
            },
            "delete": {
                "table_name": {"type": "string", "required": True, "description": "削除対象テーブル名"},
                "where_clause": {"type": "string", "required": True, "description": "WHERE条件"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"}
            },
            "backup": {
                "connection_name": {"type": "string", "required": False, "description": "バックアップする接続名"},
                "backup_path": {"type": "string", "required": False, "description": "バックアップファイルのパス"}
            },
            "restore": {
                "backup_path": {"type": "string", "required": True, "description": "復元元バックアップファイル"},
                "target_path": {"type": "string", "required": True, "description": "復元先データベースファイル"}
            },
            "list_tables": {
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"}
            },
            "describe_table": {
                "table_name": {"type": "string", "required": True, "description": "構造を確認するテーブル名"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"}
            },
            "export_data": {
                "table_name": {"type": "string", "required": True, "description": "エクスポートするテーブル名"},
                "output_path": {"type": "string", "required": True, "description": "出力ファイルパス"},
                "format": {"type": "string", "required": False, "description": "出力フォーマット（csv, json, excel）"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"}
            },
            "import_data": {
                "table_name": {"type": "string", "required": True, "description": "インポート先テーブル名"},
                "input_path": {"type": "string", "required": True, "description": "入力ファイルパス"},
                "format": {"type": "string", "required": False, "description": "入力フォーマット（csv, json, excel）"},
                "connection_name": {"type": "string", "required": False, "description": "使用する接続名"}
            }
        }
