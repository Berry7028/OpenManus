from pathlib import Path
from app.tool.base import BaseTool, ToolResult


class ReplaceInFile(BaseTool):
    name: str = "replace_in_file"
    description: str = "Replace occurrences of a substring in a file."
    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path of the file to modify."},
            "old": {"type": "string", "description": "Substring to replace."},
            "new": {"type": "string", "description": "Replacement substring."},
        },
        "required": ["path", "old", "new"],
    }

    async def execute(self, path: str, old: str, new: str) -> ToolResult:
        try:
            file_path = Path(path)
            if not file_path.exists():
                return ToolResult(error=f"File not found: {path}")
            text = file_path.read_text(encoding="utf-8")
            updated = text.replace(old, new)
            file_path.write_text(updated, encoding="utf-8")
            return ToolResult(output=f"Replaced all occurrences of '{old}' with '{new}' in {path}")
        except Exception as e:
            return ToolResult(error=f"Failed to replace text in file: {e}")
