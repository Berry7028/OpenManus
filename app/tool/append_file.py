from pathlib import Path
from app.tool.base import BaseTool, ToolResult


class AppendToFile(BaseTool):
    name: str = "append_file"
    description: str = "Append content to an existing file."
    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path of the file to append to."},
            "content": {"type": "string", "description": "Content to append to the file."},
        },
        "required": ["path", "content"],
    }

    async def execute(self, path: str, content: str) -> ToolResult:
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(error=f"File not found: {path}")
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(output=f"Appended content to {path}")
        except Exception as e:
            return ToolResult(error=f"Failed to append to file: {e}")
