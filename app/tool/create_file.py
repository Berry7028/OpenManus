from pathlib import Path
from app.tool.base import BaseTool, ToolResult


class CreateFile(BaseTool):
    name: str = "create_file"
    description: str = "Create a new file with a given path and content."
    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path of the new file to create."},
            "content": {"type": "string", "description": "Content to write into the file."},
        },
        "required": ["path", "content"],
    }

    async def execute(self, path: str, content: str) -> ToolResult:
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return ToolResult(output=f"File created at {path}")
        except Exception as e:
            return ToolResult(error=f"Failed to create file: {e}")
