"""
Workflow Automator Tool

This tool provides comprehensive workflow automation capabilities including:
- Visual workflow creation and execution
- Task orchestration and dependency management
- Conditional logic and branching
- Event-driven automation
- Integration with external systems
- Monitoring and error handling
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import traceback
from .base import BaseTool


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class TriggerType(Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event"
    WEBHOOK = "webhook"
    FILE_WATCH = "file_watch"


@dataclass
class Task:
    id: str
    name: str
    task_type: str
    parameters: Dict[str, Any]
    dependencies: List[str]
    conditions: Dict[str, Any]
    timeout: int
    retry_count: int
    status: TaskStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    result: Optional[Any] = None


@dataclass
class Workflow:
    id: str
    name: str
    description: str
    tasks: List[Task]
    triggers: List[Dict[str, Any]]
    variables: Dict[str, Any]
    status: WorkflowStatus
    created_at: str
    updated_at: str
    execution_count: int = 0
    last_execution: Optional[str] = None


class WorkflowAutomator(BaseTool):
    """Tool for comprehensive workflow automation"""

    def __init__(self):
        super().__init__()
        self.name = "workflow_automator"
        self.description = "Comprehensive workflow automation tool"

        # Workflow storage
        self.workflows = {}
        self.executions = {}
        self.task_handlers = {}

        # Execution state
        self.running_workflows = {}
        self.execution_queue = asyncio.Queue()

        # Built-in task types
        self._register_builtin_tasks()

    def _register_builtin_tasks(self):
        """Register built-in task handlers"""
        self.task_handlers = {
            "delay": self._handle_delay_task,
            "http_request": self._handle_http_request_task,
            "file_operation": self._handle_file_operation_task,
            "shell_command": self._handle_shell_command_task,
            "condition": self._handle_condition_task,
            "notification": self._handle_notification_task,
            "data_transform": self._handle_data_transform_task,
            "database_query": self._handle_database_query_task,
            "api_call": self._handle_api_call_task,
            "loop": self._handle_loop_task
        }

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute workflow automator commands"""
        try:
            if command == "create_workflow":
                return await self._create_workflow(**kwargs)
            elif command == "update_workflow":
                return await self._update_workflow(**kwargs)
            elif command == "delete_workflow":
                return await self._delete_workflow(**kwargs)
            elif command == "run_workflow":
                return await self._run_workflow(**kwargs)
            elif command == "pause_workflow":
                return await self._pause_workflow(**kwargs)
            elif command == "resume_workflow":
                return await self._resume_workflow(**kwargs)
            elif command == "cancel_workflow":
                return await self._cancel_workflow(**kwargs)
            elif command == "list_workflows":
                return await self._list_workflows(**kwargs)
            elif command == "get_execution_status":
                return await self._get_execution_status(**kwargs)
            elif command == "execution_history":
                return await self._execution_history(**kwargs)
            elif command == "validate_workflow":
                return await self._validate_workflow(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Workflow automator error: {str(e)}"}

    async def _create_workflow(self, name: str, description: str = "",
                             tasks: List[Dict[str, Any]] = None,
                             triggers: List[Dict[str, Any]] = None,
                             variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new workflow"""
        workflow_id = str(uuid.uuid4())

        # Convert task dictionaries to Task objects
        task_objects = []
        if tasks:
            for task_data in tasks:
                task = Task(
                    id=task_data.get("id", str(uuid.uuid4())),
                    name=task_data["name"],
                    task_type=task_data["task_type"],
                    parameters=task_data.get("parameters", {}),
                    dependencies=task_data.get("dependencies", []),
                    conditions=task_data.get("conditions", {}),
                    timeout=task_data.get("timeout", 300),
                    retry_count=task_data.get("retry_count", 0),
                    status=TaskStatus.PENDING,
                    created_at=datetime.now().isoformat()
                )
                task_objects.append(task)

        workflow = Workflow(
            id=workflow_id,
            name=name,
            description=description,
            tasks=task_objects,
            triggers=triggers or [],
            variables=variables or {},
            status=WorkflowStatus.DRAFT,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        self.workflows[workflow_id] = workflow

        return {
            "workflow_id": workflow_id,
            "name": name,
            "status": "created",
            "task_count": len(task_objects),
            "created_at": workflow.created_at
        }

    async def _update_workflow(self, workflow_id: str, **updates) -> Dict[str, Any]:
        """Update existing workflow"""
        if workflow_id not in self.workflows:
            return {"error": f"Workflow '{workflow_id}' not found"}

        workflow = self.workflows[workflow_id]

        # Check if workflow is running
        if workflow.status == WorkflowStatus.RUNNING:
            return {"error": "Cannot update running workflow"}

        # Update workflow properties
        for key, value in updates.items():
            if key == "tasks" and value:
                # Convert task dictionaries to Task objects
                task_objects = []
                for task_data in value:
                    task = Task(
                        id=task_data.get("id", str(uuid.uuid4())),
                        name=task_data["name"],
                        task_type=task_data["task_type"],
                        parameters=task_data.get("parameters", {}),
                        dependencies=task_data.get("dependencies", []),
                        conditions=task_data.get("conditions", {}),
                        timeout=task_data.get("timeout", 300),
                        retry_count=task_data.get("retry_count", 0),
                        status=TaskStatus.PENDING,
                        created_at=datetime.now().isoformat()
                    )
                    task_objects.append(task)
                workflow.tasks = task_objects
            elif hasattr(workflow, key):
                setattr(workflow, key, value)

        workflow.updated_at = datetime.now().isoformat()

        return {
            "workflow_id": workflow_id,
            "status": "updated",
            "updated_at": workflow.updated_at
        }

    async def _delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete workflow"""
        if workflow_id not in self.workflows:
            return {"error": f"Workflow '{workflow_id}' not found"}

        workflow = self.workflows[workflow_id]

        # Check if workflow is running
        if workflow.status == WorkflowStatus.RUNNING:
            return {"error": "Cannot delete running workflow"}

        del self.workflows[workflow_id]

        return {
            "workflow_id": workflow_id,
            "status": "deleted",
            "deleted_at": datetime.now().isoformat()
        }

    async def _run_workflow(self, workflow_id: str,
                          input_variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute workflow"""
        if workflow_id not in self.workflows:
            return {"error": f"Workflow '{workflow_id}' not found"}

        workflow = self.workflows[workflow_id]

        # Create execution instance
        execution_id = str(uuid.uuid4())
        execution = {
            "id": execution_id,
            "workflow_id": workflow_id,
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "input_variables": input_variables or {},
            "task_results": {},
            "current_task": None,
            "error": None
        }

        self.executions[execution_id] = execution
        self.running_workflows[execution_id] = workflow

        # Update workflow status
        workflow.status = WorkflowStatus.RUNNING
        workflow.execution_count += 1
        workflow.last_execution = execution["started_at"]

        # Start execution in background
        asyncio.create_task(self._execute_workflow(execution_id))

        return {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "started",
            "started_at": execution["started_at"]
        }

    async def _execute_workflow(self, execution_id: str):
        """Execute workflow tasks"""
        execution = self.executions[execution_id]
        workflow = self.running_workflows[execution_id]

        try:
            # Prepare execution context
            context = {
                "variables": {**workflow.variables, **execution["input_variables"]},
                "task_results": execution["task_results"],
                "execution_id": execution_id
            }

            # Execute tasks in dependency order
            executed_tasks = set()
            while len(executed_tasks) < len(workflow.tasks):
                ready_tasks = [
                    task for task in workflow.tasks
                    if task.id not in executed_tasks and
                    all(dep_id in executed_tasks for dep_id in task.dependencies)
                ]

                if not ready_tasks:
                    # Check for circular dependencies
                    remaining_tasks = [t for t in workflow.tasks if t.id not in executed_tasks]
                    if remaining_tasks:
                        raise Exception("Circular dependency or unresolvable dependencies detected")
                    break

                # Execute ready tasks
                for task in ready_tasks:
                    execution["current_task"] = task.id

                    # Check conditions
                    if not self._evaluate_conditions(task.conditions, context):
                        task.status = TaskStatus.SKIPPED
                        executed_tasks.add(task.id)
                        continue

                    # Execute task
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now().isoformat()

                    try:
                        result = await self._execute_task(task, context)
                        task.status = TaskStatus.COMPLETED
                        task.completed_at = datetime.now().isoformat()
                        task.result = result

                        # Store result in context
                        context["task_results"][task.id] = result
                        execution["task_results"][task.id] = result

                    except Exception as task_error:
                        task.status = TaskStatus.FAILED
                        task.error_message = str(task_error)
                        task.completed_at = datetime.now().isoformat()

                        # Handle task failure
                        if task.retry_count > 0:
                            # Retry logic would go here
                            pass
                        else:
                            # Fail entire workflow
                            raise task_error

                    executed_tasks.add(task.id)

            # Workflow completed successfully
            execution["status"] = "completed"
            execution["completed_at"] = datetime.now().isoformat()
            workflow.status = WorkflowStatus.COMPLETED

        except Exception as e:
            # Workflow failed
            execution["status"] = "failed"
            execution["error"] = str(e)
            execution["completed_at"] = datetime.now().isoformat()
            workflow.status = WorkflowStatus.FAILED

            # Mark remaining tasks as cancelled
            for task in workflow.tasks:
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED

        finally:
            # Clean up
            execution["current_task"] = None
            if execution_id in self.running_workflows:
                del self.running_workflows[execution_id]

    def _evaluate_conditions(self, conditions: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate task conditions"""
        if not conditions:
            return True

        # Simple condition evaluation
        # In a real implementation, this would be more sophisticated
        try:
            for condition_type, condition_value in conditions.items():
                if condition_type == "variable_equals":
                    var_name, expected_value = condition_value["variable"], condition_value["value"]
                    if context["variables"].get(var_name) != expected_value:
                        return False

                elif condition_type == "task_result_equals":
                    task_id, expected_value = condition_value["task"], condition_value["value"]
                    if context["task_results"].get(task_id) != expected_value:
                        return False

                elif condition_type == "expression":
                    # Simple expression evaluation (unsafe - use with caution)
                    expression = condition_value["expression"]
                    # Replace variables in expression
                    for var_name, var_value in context["variables"].items():
                        expression = expression.replace(f"${var_name}", str(var_value))

                    # Evaluate (this is unsafe and should be replaced with a safe evaluator)
                    try:
                        result = eval(expression)
                        if not result:
                            return False
                    except:
                        return False

            return True

        except Exception:
            return False

    async def _execute_task(self, task: Task, context: Dict[str, Any]) -> Any:
        """Execute individual task"""
        if task.task_type not in self.task_handlers:
            raise Exception(f"Unknown task type: {task.task_type}")

        handler = self.task_handlers[task.task_type]

        # Apply timeout
        try:
            result = await asyncio.wait_for(
                handler(task, context),
                timeout=task.timeout
            )
            return result
        except asyncio.TimeoutError:
            raise Exception(f"Task '{task.name}' timed out after {task.timeout} seconds")

    # Built-in task handlers
    async def _handle_delay_task(self, task: Task, context: Dict[str, Any]) -> str:
        """Handle delay task"""
        delay_seconds = task.parameters.get("seconds", 1)
        await asyncio.sleep(delay_seconds)
        return f"Delayed for {delay_seconds} seconds"

    async def _handle_http_request_task(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle HTTP request task"""
        import aiohttp

        url = task.parameters["url"]
        method = task.parameters.get("method", "GET")
        headers = task.parameters.get("headers", {})
        data = task.parameters.get("data")

        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=data) as response:
                return {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "data": await response.text()
                }

    async def _handle_file_operation_task(self, task: Task, context: Dict[str, Any]) -> str:
        """Handle file operation task"""
        operation = task.parameters["operation"]
        file_path = task.parameters["path"]

        if operation == "read":
            with open(file_path, 'r') as f:
                return f.read()
        elif operation == "write":
            content = task.parameters["content"]
            with open(file_path, 'w') as f:
                f.write(content)
            return f"Written to {file_path}"
        elif operation == "delete":
            import os
            os.remove(file_path)
            return f"Deleted {file_path}"
        else:
            raise Exception(f"Unknown file operation: {operation}")

    async def _handle_shell_command_task(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle shell command task"""
        command = task.parameters["command"]
        cwd = task.parameters.get("working_directory")

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )

        stdout, stderr = await process.communicate()

        return {
            "return_code": process.returncode,
            "stdout": stdout.decode(),
            "stderr": stderr.decode()
        }

    async def _handle_condition_task(self, task: Task, context: Dict[str, Any]) -> bool:
        """Handle condition evaluation task"""
        conditions = task.parameters.get("conditions", {})
        return self._evaluate_conditions(conditions, context)

    async def _handle_notification_task(self, task: Task, context: Dict[str, Any]) -> str:
        """Handle notification task"""
        # This would integrate with the notification sender tool
        message = task.parameters["message"]
        recipients = task.parameters.get("recipients", [])
        channel = task.parameters.get("channel", "email")

        # Placeholder implementation
        return f"Notification sent to {recipients} via {channel}: {message}"

    async def _handle_data_transform_task(self, task: Task, context: Dict[str, Any]) -> Any:
        """Handle data transformation task"""
        source_data = task.parameters["source_data"]
        transformation = task.parameters["transformation"]

        # Simple transformations
        if transformation == "json_parse":
            return json.loads(source_data)
        elif transformation == "json_stringify":
            return json.dumps(source_data)
        elif transformation == "uppercase":
            return str(source_data).upper()
        elif transformation == "lowercase":
            return str(source_data).lower()
        else:
            return source_data

    async def _handle_database_query_task(self, task: Task, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle database query task"""
        # Placeholder implementation
        query = task.parameters["query"]
        return [{"result": f"Executed query: {query}"}]

    async def _handle_api_call_task(self, task: Task, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle API call task"""
        # Similar to HTTP request but with API-specific handling
        return await self._handle_http_request_task(task, context)

    async def _handle_loop_task(self, task: Task, context: Dict[str, Any]) -> List[Any]:
        """Handle loop task"""
        items = task.parameters.get("items", [])
        subtasks = task.parameters.get("subtasks", [])
        results = []

        for item in items:
            # Create context for iteration
            loop_context = {**context, "loop_item": item}

            # Execute subtasks for each item
            for subtask_config in subtasks:
                subtask = Task(
                    id=str(uuid.uuid4()),
                    name=subtask_config["name"],
                    task_type=subtask_config["task_type"],
                    parameters=subtask_config.get("parameters", {}),
                    dependencies=[],
                    conditions={},
                    timeout=subtask_config.get("timeout", 300),
                    retry_count=0,
                    status=TaskStatus.PENDING,
                    created_at=datetime.now().isoformat()
                )

                result = await self._execute_task(subtask, loop_context)
                results.append(result)

        return results

    async def _pause_workflow(self, execution_id: str) -> Dict[str, Any]:
        """Pause running workflow"""
        if execution_id not in self.executions:
            return {"error": f"Execution '{execution_id}' not found"}

        execution = self.executions[execution_id]
        if execution["status"] != "running":
            return {"error": "Workflow is not running"}

        execution["status"] = "paused"
        execution["paused_at"] = datetime.now().isoformat()

        return {
            "execution_id": execution_id,
            "status": "paused",
            "paused_at": execution["paused_at"]
        }

    async def _resume_workflow(self, execution_id: str) -> Dict[str, Any]:
        """Resume paused workflow"""
        if execution_id not in self.executions:
            return {"error": f"Execution '{execution_id}' not found"}

        execution = self.executions[execution_id]
        if execution["status"] != "paused":
            return {"error": "Workflow is not paused"}

        execution["status"] = "running"
        execution["resumed_at"] = datetime.now().isoformat()

        # Restart execution
        asyncio.create_task(self._execute_workflow(execution_id))

        return {
            "execution_id": execution_id,
            "status": "resumed",
            "resumed_at": execution["resumed_at"]
        }

    async def _cancel_workflow(self, execution_id: str) -> Dict[str, Any]:
        """Cancel running workflow"""
        if execution_id not in self.executions:
            return {"error": f"Execution '{execution_id}' not found"}

        execution = self.executions[execution_id]
        if execution["status"] not in ["running", "paused"]:
            return {"error": "Workflow is not running or paused"}

        execution["status"] = "cancelled"
        execution["cancelled_at"] = datetime.now().isoformat()

        # Clean up
        if execution_id in self.running_workflows:
            workflow = self.running_workflows[execution_id]
            workflow.status = WorkflowStatus.FAILED
            del self.running_workflows[execution_id]

        return {
            "execution_id": execution_id,
            "status": "cancelled",
            "cancelled_at": execution["cancelled_at"]
        }

    async def _list_workflows(self, status: str = None) -> Dict[str, Any]:
        """List workflows"""
        workflows = list(self.workflows.values())

        if status:
            try:
                status_enum = WorkflowStatus(status)
                workflows = [w for w in workflows if w.status == status_enum]
            except ValueError:
                return {"error": f"Invalid status: {status}"}

        workflow_list = []
        for workflow in workflows:
            workflow_list.append({
                "id": workflow.id,
                "name": workflow.name,
                "description": workflow.description,
                "status": workflow.status.value,
                "task_count": len(workflow.tasks),
                "execution_count": workflow.execution_count,
                "created_at": workflow.created_at,
                "updated_at": workflow.updated_at,
                "last_execution": workflow.last_execution
            })

        return {
            "total_workflows": len(self.workflows),
            "filtered_workflows": len(workflow_list),
            "workflows": workflow_list
        }

    async def _get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status"""
        if execution_id not in self.executions:
            return {"error": f"Execution '{execution_id}' not found"}

        execution = self.executions[execution_id]
        workflow = self.workflows[execution["workflow_id"]]

        # Get task statuses
        task_statuses = {}
        for task in workflow.tasks:
            task_statuses[task.id] = {
                "name": task.name,
                "status": task.status.value,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error_message": task.error_message
            }

        return {
            "execution_id": execution_id,
            "workflow_id": execution["workflow_id"],
            "workflow_name": workflow.name,
            "status": execution["status"],
            "started_at": execution["started_at"],
            "completed_at": execution.get("completed_at"),
            "current_task": execution["current_task"],
            "task_statuses": task_statuses,
            "error": execution.get("error")
        }

    async def _execution_history(self, workflow_id: str = None,
                               limit: int = 100) -> Dict[str, Any]:
        """Get execution history"""
        executions = list(self.executions.values())

        if workflow_id:
            executions = [e for e in executions if e["workflow_id"] == workflow_id]

        # Sort by start time (newest first)
        executions = sorted(executions, key=lambda x: x["started_at"], reverse=True)
        executions = executions[:limit]

        return {
            "total_executions": len(self.executions),
            "filtered_executions": len(executions),
            "executions": executions
        }

    async def _validate_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Validate workflow configuration"""
        if workflow_id not in self.workflows:
            return {"error": f"Workflow '{workflow_id}' not found"}

        workflow = self.workflows[workflow_id]
        validation_errors = []
        warnings = []

        # Check for circular dependencies
        task_ids = {task.id for task in workflow.tasks}

        for task in workflow.tasks:
            # Check if dependencies exist
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    validation_errors.append(f"Task '{task.name}' depends on non-existent task '{dep_id}'")

            # Check task type
            if task.task_type not in self.task_handlers:
                validation_errors.append(f"Task '{task.name}' has unknown type '{task.task_type}'")

            # Check for missing required parameters
            required_params = self._get_required_parameters(task.task_type)
            for param in required_params:
                if param not in task.parameters:
                    validation_errors.append(f"Task '{task.name}' missing required parameter '{param}'")

        # Check for circular dependencies
        if self._has_circular_dependencies(workflow.tasks):
            validation_errors.append("Workflow has circular dependencies")

        is_valid = len(validation_errors) == 0

        return {
            "workflow_id": workflow_id,
            "is_valid": is_valid,
            "validation_errors": validation_errors,
            "warnings": warnings,
            "validated_at": datetime.now().isoformat()
        }

    def _get_required_parameters(self, task_type: str) -> List[str]:
        """Get required parameters for task type"""
        required_params = {
            "delay": ["seconds"],
            "http_request": ["url"],
            "file_operation": ["operation", "path"],
            "shell_command": ["command"],
            "notification": ["message"],
            "data_transform": ["source_data", "transformation"],
            "database_query": ["query"],
            "api_call": ["url"],
            "loop": ["items"]
        }
        return required_params.get(task_type, [])

    def _has_circular_dependencies(self, tasks: List[Task]) -> bool:
        """Check for circular dependencies"""
        # Build dependency graph
        graph = {task.id: task.dependencies for task in tasks}

        # Use DFS to detect cycles
        visited = set()
        rec_stack = set()

        def has_cycle(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task_id in graph:
            if task_id not in visited:
                if has_cycle(task_id):
                    return True

        return False
