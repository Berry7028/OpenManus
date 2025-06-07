"""
Task Scheduler Tool

タスクスケジューリング・自動化を行うツール
cron風スケジューリング、タスク管理、実行履歴管理、条件付き実行などの機能を提供
"""

import asyncio
import json
import logging
import schedule
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time
import uuid

from .base import BaseTool

logger = logging.getLogger(__name__)

class TaskScheduler(BaseTool):
    """タスクスケジューリング・自動化ツール"""

    def __init__(self):
        super().__init__()
        self.tasks = {}
        self.execution_history = []
        self.scheduler_thread = None
        self.running = False
        self.task_storage_file = "scheduled_tasks.json"

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        タスクスケジューリング操作を実行

        Args:
            command: 実行するコマンド
            **kwargs: コマンド固有のパラメータ

        Returns:
            実行結果
        """
        try:
            if command == "create_task":
                return await self._create_task(**kwargs)
            elif command == "schedule_task":
                return await self._schedule_task(**kwargs)
            elif command == "list_tasks":
                return await self._list_tasks(**kwargs)
            elif command == "delete_task":
                return await self._delete_task(**kwargs)
            elif command == "run_task":
                return await self._run_task(**kwargs)
            elif command == "start_scheduler":
                return await self._start_scheduler(**kwargs)
            elif command == "stop_scheduler":
                return await self._stop_scheduler(**kwargs)
            elif command == "get_history":
                return await self._get_history(**kwargs)
            elif command == "update_task":
                return await self._update_task(**kwargs)
            elif command == "pause_task":
                return await self._pause_task(**kwargs)
            elif command == "resume_task":
                return await self._resume_task(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "create_task", "schedule_task", "list_tasks", "delete_task",
                        "run_task", "start_scheduler", "stop_scheduler", "get_history",
                        "update_task", "pause_task", "resume_task"
                    ]
                }

        except Exception as e:
            logger.error(f"Task scheduling operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    async def _create_task(self, name: str, command: str,
                          description: Optional[str] = None,
                          parameters: Optional[Dict[str, Any]] = None,
                          timeout: int = 300,
                          retry_count: int = 0,
                          retry_delay: int = 60) -> Dict[str, Any]:
        """新しいタスクを作成"""
        try:
            task_id = str(uuid.uuid4())

            task = {
                "id": task_id,
                "name": name,
                "command": command,
                "description": description or "",
                "parameters": parameters or {},
                "timeout": timeout,
                "retry_count": retry_count,
                "retry_delay": retry_delay,
                "created_at": datetime.now().isoformat(),
                "status": "created",
                "schedule": None,
                "last_run": None,
                "next_run": None,
                "run_count": 0,
                "success_count": 0,
                "failure_count": 0,
                "paused": False
            }

            self.tasks[task_id] = task
            await self._save_tasks()

            return {
                "success": True,
                "message": f"Task '{name}' created successfully",
                "task_id": task_id,
                "task": task
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Task creation failed: {e}"
            }

    async def _schedule_task(self, task_id: str, schedule_type: str,
                           schedule_value: Union[str, int, Dict[str, Any]],
                           start_time: Optional[str] = None,
                           end_time: Optional[str] = None) -> Dict[str, Any]:
        """タスクをスケジュール"""
        try:
            if task_id not in self.tasks:
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }

            task = self.tasks[task_id]

            # スケジュール設定を作成
            schedule_config = {
                "type": schedule_type,
                "value": schedule_value,
                "start_time": start_time,
                "end_time": end_time,
                "created_at": datetime.now().isoformat()
            }

            # 次回実行時刻を計算
            next_run = self._calculate_next_run(schedule_config)

            task["schedule"] = schedule_config
            task["next_run"] = next_run.isoformat() if next_run else None
            task["status"] = "scheduled"

            await self._save_tasks()

            return {
                "success": True,
                "message": f"Task '{task['name']}' scheduled successfully",
                "task_id": task_id,
                "schedule": schedule_config,
                "next_run": task["next_run"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Task scheduling failed: {e}"
            }

    def _calculate_next_run(self, schedule_config: Dict[str, Any]) -> Optional[datetime]:
        """次回実行時刻を計算"""
        schedule_type = schedule_config["type"]
        schedule_value = schedule_config["value"]
        now = datetime.now()

        try:
            if schedule_type == "once":
                # 一回のみ実行
                if isinstance(schedule_value, str):
                    return datetime.fromisoformat(schedule_value)
                else:
                    return now + timedelta(seconds=schedule_value)

            elif schedule_type == "interval":
                # 間隔実行（秒）
                return now + timedelta(seconds=schedule_value)

            elif schedule_type == "daily":
                # 毎日指定時刻
                if isinstance(schedule_value, str):
                    time_parts = schedule_value.split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1]) if len(time_parts) > 1 else 0

                    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += timedelta(days=1)
                    return next_run

            elif schedule_type == "weekly":
                # 毎週指定曜日・時刻
                if isinstance(schedule_value, dict):
                    weekday = schedule_value.get("weekday", 0)  # 0=月曜日
                    time_str = schedule_value.get("time", "00:00")

                    time_parts = time_str.split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1]) if len(time_parts) > 1 else 0

                    days_ahead = weekday - now.weekday()
                    if days_ahead <= 0:
                        days_ahead += 7

                    next_run = now + timedelta(days=days_ahead)
                    next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    return next_run

            elif schedule_type == "monthly":
                # 毎月指定日・時刻
                if isinstance(schedule_value, dict):
                    day = schedule_value.get("day", 1)
                    time_str = schedule_value.get("time", "00:00")

                    time_parts = time_str.split(":")
                    hour = int(time_parts[0])
                    minute = int(time_parts[1]) if len(time_parts) > 1 else 0

                    next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                    if next_run <= now:
                        # 来月
                        if next_run.month == 12:
                            next_run = next_run.replace(year=next_run.year + 1, month=1)
                        else:
                            next_run = next_run.replace(month=next_run.month + 1)
                    return next_run

            elif schedule_type == "cron":
                # cron形式（簡易版）
                return self._parse_cron(schedule_value, now)

        except Exception as e:
            logger.error(f"Failed to calculate next run: {e}")
            return None

        return None

    def _parse_cron(self, cron_expression: str, base_time: datetime) -> Optional[datetime]:
        """cron式を解析（簡易版）"""
        try:
            # 基本的なcron形式: "分 時 日 月 曜日"
            parts = cron_expression.split()
            if len(parts) != 5:
                return None

            minute, hour, day, month, weekday = parts

            # 次回実行時刻を計算（簡易実装）
            next_run = base_time.replace(second=0, microsecond=0)

            # 分の処理
            if minute != "*":
                target_minute = int(minute)
                if next_run.minute != target_minute:
                    next_run = next_run.replace(minute=target_minute)
                    if next_run <= base_time:
                        next_run += timedelta(hours=1)

            # 時の処理
            if hour != "*":
                target_hour = int(hour)
                if next_run.hour != target_hour:
                    next_run = next_run.replace(hour=target_hour)
                    if next_run <= base_time:
                        next_run += timedelta(days=1)

            return next_run

        except Exception as e:
            logger.error(f"Failed to parse cron expression: {e}")
            return None

    async def _list_tasks(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """タスク一覧を取得"""
        try:
            await self._load_tasks()

            tasks_list = []
            for task_id, task in self.tasks.items():
                if status_filter is None or task["status"] == status_filter:
                    tasks_list.append({
                        "id": task_id,
                        "name": task["name"],
                        "status": task["status"],
                        "next_run": task["next_run"],
                        "last_run": task["last_run"],
                        "run_count": task["run_count"],
                        "success_count": task["success_count"],
                        "failure_count": task["failure_count"],
                        "paused": task["paused"]
                    })

            return {
                "success": True,
                "tasks": tasks_list,
                "total_tasks": len(tasks_list),
                "filter": status_filter
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list tasks: {e}"
            }

    async def _delete_task(self, task_id: str) -> Dict[str, Any]:
        """タスクを削除"""
        try:
            if task_id not in self.tasks:
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }

            task_name = self.tasks[task_id]["name"]
            del self.tasks[task_id]
            await self._save_tasks()

            return {
                "success": True,
                "message": f"Task '{task_name}' deleted successfully",
                "task_id": task_id
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Task deletion failed: {e}"
            }

    async def _run_task(self, task_id: str, force: bool = False) -> Dict[str, Any]:
        """タスクを実行"""
        try:
            if task_id not in self.tasks:
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }

            task = self.tasks[task_id]

            if task["paused"] and not force:
                return {
                    "success": False,
                    "error": f"Task '{task['name']}' is paused"
                }

            # 実行履歴エントリを作成
            execution_id = str(uuid.uuid4())
            execution_start = datetime.now()

            execution_record = {
                "id": execution_id,
                "task_id": task_id,
                "task_name": task["name"],
                "start_time": execution_start.isoformat(),
                "end_time": None,
                "status": "running",
                "result": None,
                "error": None,
                "duration_seconds": None
            }

            self.execution_history.append(execution_record)

            try:
                # タスクを実行
                result = await self._execute_task_command(task)

                execution_end = datetime.now()
                duration = (execution_end - execution_start).total_seconds()

                # 実行記録を更新
                execution_record.update({
                    "end_time": execution_end.isoformat(),
                    "status": "completed",
                    "result": result,
                    "duration_seconds": duration
                })

                # タスク統計を更新
                task["last_run"] = execution_end.isoformat()
                task["run_count"] += 1
                task["success_count"] += 1

                # 次回実行時刻を計算
                if task["schedule"]:
                    next_run = self._calculate_next_run(task["schedule"])
                    task["next_run"] = next_run.isoformat() if next_run else None

                await self._save_tasks()

                return {
                    "success": True,
                    "message": f"Task '{task['name']}' executed successfully",
                    "execution_id": execution_id,
                    "result": result,
                    "duration_seconds": duration
                }

            except Exception as e:
                execution_end = datetime.now()
                duration = (execution_end - execution_start).total_seconds()

                # エラー記録を更新
                execution_record.update({
                    "end_time": execution_end.isoformat(),
                    "status": "failed",
                    "error": str(e),
                    "duration_seconds": duration
                })

                task["failure_count"] += 1
                task["run_count"] += 1
                await self._save_tasks()

                return {
                    "success": False,
                    "error": f"Task execution failed: {e}",
                    "execution_id": execution_id,
                    "duration_seconds": duration
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Task execution failed: {e}"
            }

    async def _execute_task_command(self, task: Dict[str, Any]) -> Any:
        """タスクコマンドを実行"""
        command = task["command"]
        parameters = task["parameters"]
        timeout = task["timeout"]

        if command == "shell":
            # シェルコマンド実行
            import subprocess
            cmd = parameters.get("cmd", "")
            process = await asyncio.create_subprocess_shell(
                cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=timeout
                )

                return {
                    "return_code": process.returncode,
                    "stdout": stdout.decode('utf-8'),
                    "stderr": stderr.decode('utf-8')
                }
            except asyncio.TimeoutError:
                process.kill()
                raise Exception(f"Command timed out after {timeout} seconds")

        elif command == "http_request":
            # HTTP リクエスト
            import aiohttp

            url = parameters.get("url", "")
            method = parameters.get("method", "GET")
            headers = parameters.get("headers", {})
            data = parameters.get("data")

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers=headers, json=data, timeout=timeout
                ) as response:
                    return {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "content": await response.text()
                    }

        elif command == "file_operation":
            # ファイル操作
            operation = parameters.get("operation", "")
            file_path = parameters.get("file_path", "")

            if operation == "delete":
                Path(file_path).unlink(missing_ok=True)
                return {"operation": "delete", "file_path": file_path}

            elif operation == "create":
                content = parameters.get("content", "")
                with open(file_path, 'w') as f:
                    f.write(content)
                return {"operation": "create", "file_path": file_path}

            elif operation == "backup":
                import shutil
                backup_path = f"{file_path}.backup_{int(time.time())}"
                shutil.copy2(file_path, backup_path)
                return {"operation": "backup", "original": file_path, "backup": backup_path}

        elif command == "python_script":
            # Python スクリプト実行
            script = parameters.get("script", "")
            globals_dict = parameters.get("globals", {})

            # セキュリティ上の理由で制限された実行
            allowed_modules = ['os', 'sys', 'datetime', 'json', 'math']
            restricted_globals = {
                '__builtins__': {
                    'print': print,
                    'len': len,
                    'str': str,
                    'int': int,
                    'float': float,
                    'list': list,
                    'dict': dict,
                    'range': range,
                    'enumerate': enumerate
                }
            }
            restricted_globals.update(globals_dict)

            exec(script, restricted_globals)
            return {"script_executed": True}

        else:
            raise Exception(f"Unknown command type: {command}")

    async def _start_scheduler(self) -> Dict[str, Any]:
        """スケジューラーを開始"""
        try:
            if self.running:
                return {
                    "success": False,
                    "error": "Scheduler is already running"
                }

            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()

            return {
                "success": True,
                "message": "Scheduler started successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to start scheduler: {e}"
            }

    async def _stop_scheduler(self) -> Dict[str, Any]:
        """スケジューラーを停止"""
        try:
            if not self.running:
                return {
                    "success": False,
                    "error": "Scheduler is not running"
                }

            self.running = False

            if self.scheduler_thread:
                self.scheduler_thread.join(timeout=5)

            return {
                "success": True,
                "message": "Scheduler stopped successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to stop scheduler: {e}"
            }

    def _scheduler_loop(self):
        """スケジューラーのメインループ"""
        while self.running:
            try:
                current_time = datetime.now()

                for task_id, task in self.tasks.items():
                    if (task["status"] == "scheduled" and
                        not task["paused"] and
                        task["next_run"]):

                        next_run_time = datetime.fromisoformat(task["next_run"])

                        if current_time >= next_run_time:
                            # タスクを非同期で実行
                            asyncio.create_task(self._run_task(task_id))

                time.sleep(10)  # 10秒間隔でチェック

            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(60)  # エラー時は1分待機

    async def _get_history(self, task_id: Optional[str] = None,
                          limit: int = 100) -> Dict[str, Any]:
        """実行履歴を取得"""
        try:
            history = self.execution_history

            if task_id:
                history = [h for h in history if h["task_id"] == task_id]

            # 最新順にソート
            history = sorted(history, key=lambda x: x["start_time"], reverse=True)

            # 制限数まで取得
            history = history[:limit]

            return {
                "success": True,
                "history": history,
                "total_records": len(history),
                "task_filter": task_id,
                "limit": limit
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get history: {e}"
            }

    async def _update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """タスクを更新"""
        try:
            if task_id not in self.tasks:
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }

            task = self.tasks[task_id]

            # 更新可能なフィールド
            updatable_fields = [
                "name", "description", "command", "parameters",
                "timeout", "retry_count", "retry_delay"
            ]

            for field, value in updates.items():
                if field in updatable_fields:
                    task[field] = value

            await self._save_tasks()

            return {
                "success": True,
                "message": f"Task '{task['name']}' updated successfully",
                "task_id": task_id,
                "updated_fields": list(updates.keys())
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Task update failed: {e}"
            }

    async def _pause_task(self, task_id: str) -> Dict[str, Any]:
        """タスクを一時停止"""
        try:
            if task_id not in self.tasks:
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }

            task = self.tasks[task_id]
            task["paused"] = True
            await self._save_tasks()

            return {
                "success": True,
                "message": f"Task '{task['name']}' paused",
                "task_id": task_id
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Task pause failed: {e}"
            }

    async def _resume_task(self, task_id: str) -> Dict[str, Any]:
        """タスクを再開"""
        try:
            if task_id not in self.tasks:
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }

            task = self.tasks[task_id]
            task["paused"] = False
            await self._save_tasks()

            return {
                "success": True,
                "message": f"Task '{task['name']}' resumed",
                "task_id": task_id
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Task resume failed: {e}"
            }

    async def _save_tasks(self):
        """タスクをファイルに保存"""
        try:
            with open(self.task_storage_file, 'w') as f:
                json.dump(self.tasks, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tasks: {e}")

    async def _load_tasks(self):
        """ファイルからタスクを読み込み"""
        try:
            if Path(self.task_storage_file).exists():
                with open(self.task_storage_file, 'r') as f:
                    self.tasks = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load tasks: {e}")
            self.tasks = {}

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """各コマンドのパラメータ定義を返す"""
        return {
            "create_task": {
                "name": {"type": "string", "required": True, "description": "タスク名"},
                "command": {"type": "string", "required": True, "description": "実行コマンドタイプ"},
                "description": {"type": "string", "required": False, "description": "タスクの説明"},
                "parameters": {"type": "object", "required": False, "description": "コマンドパラメータ"},
                "timeout": {"type": "integer", "required": False, "description": "タイムアウト秒数"},
                "retry_count": {"type": "integer", "required": False, "description": "リトライ回数"},
                "retry_delay": {"type": "integer", "required": False, "description": "リトライ間隔（秒）"}
            },
            "schedule_task": {
                "task_id": {"type": "string", "required": True, "description": "タスクID"},
                "schedule_type": {"type": "string", "required": True, "description": "スケジュールタイプ"},
                "schedule_value": {"type": "any", "required": True, "description": "スケジュール値"},
                "start_time": {"type": "string", "required": False, "description": "開始時刻"},
                "end_time": {"type": "string", "required": False, "description": "終了時刻"}
            },
            "list_tasks": {
                "status_filter": {"type": "string", "required": False, "description": "ステータスフィルター"}
            },
            "delete_task": {
                "task_id": {"type": "string", "required": True, "description": "削除するタスクID"}
            },
            "run_task": {
                "task_id": {"type": "string", "required": True, "description": "実行するタスクID"},
                "force": {"type": "boolean", "required": False, "description": "強制実行"}
            },
            "start_scheduler": {},
            "stop_scheduler": {},
            "get_history": {
                "task_id": {"type": "string", "required": False, "description": "特定タスクの履歴"},
                "limit": {"type": "integer", "required": False, "description": "取得件数制限"}
            },
            "update_task": {
                "task_id": {"type": "string", "required": True, "description": "更新するタスクID"},
                "updates": {"type": "object", "required": True, "description": "更新内容"}
            },
            "pause_task": {
                "task_id": {"type": "string", "required": True, "description": "一時停止するタスクID"}
            },
            "resume_task": {
                "task_id": {"type": "string", "required": True, "description": "再開するタスクID"}
            }
        }
