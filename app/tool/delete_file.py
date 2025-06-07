from pathlib import Path
from app.tool.base import BaseTool, ToolResult


class DeleteFile(BaseTool):
    name: str = "delete_file"
    description: str = "Delete a file at the given path."
    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path of the file to delete."},
        },
        "required": ["path"],
    }

    async def execute(self, path: str) -> ToolResult:
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(error=f"File not found: {path}")
            file_path.unlink()
            return ToolResult(output=f"Deleted file at {path}")
        except Exception as e:
            return ToolResult(error=f"Failed to delete file: {e}")
