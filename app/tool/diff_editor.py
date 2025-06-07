"""
DIFF Editor Tool for parsing, analyzing, and modifying unified diff files.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import Field

from app.tool.base import BaseTool, ToolResult


class DiffEditor(BaseTool):
    """Tool for parsing, analyzing, and modifying unified diff files."""

    name: str = "diff_editor"
    description: str = """Parse, analyze, and modify unified diff files (patches).

    Available commands:
    - parse: Parse a diff file and show its structure
    - apply: Apply a diff to target files
    - create: Create a new diff between two files/directories
    - modify: Modify specific hunks in a diff file
    - stats: Show statistics about a diff file
    - extract: Extract specific files or hunks from a diff
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute. Available commands: parse, apply, create, modify, stats, extract.",
                "enum": ["parse", "apply", "create", "modify", "stats", "extract"],
                "type": "string",
            },
            "diff_file": {
                "description": "Path to the diff file to process.",
                "type": "string",
            },
            "target_file": {
                "description": "Target file or directory for apply command.",
                "type": "string",
            },
            "source_file": {
                "description": "Source file for create command.",
                "type": "string",
            },
            "output_file": {
                "description": "Output file path for create, modify, or extract commands.",
                "type": "string",
            },
            "file_filter": {
                "description": "Filter for specific files in modify or extract commands.",
                "type": "string",
            },
            "hunk_index": {
                "description": "Index of the hunk to modify (0-based).",
                "type": "integer",
            },
            "new_content": {
                "description": "New content for modify command.",
                "type": "string",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        diff_file: Optional[str] = None,
        target_file: Optional[str] = None,
        source_file: Optional[str] = None,
        output_file: Optional[str] = None,
        file_filter: Optional[str] = None,
        hunk_index: Optional[int] = None,
        new_content: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """Execute diff editor command."""
        try:
            if command == "parse":
                return self._parse_diff(diff_file)
            elif command == "apply":
                return self._apply_diff(diff_file, target_file)
            elif command == "create":
                return self._create_diff(source_file, target_file, output_file)
            elif command == "modify":
                return self._modify_diff(diff_file, file_filter, hunk_index, new_content, output_file)
            elif command == "stats":
                return self._show_stats(diff_file)
            elif command == "extract":
                return self._extract_from_diff(diff_file, file_filter, output_file)
            else:
                return ToolResult(
                    error=f"Unknown command: {command}. Available commands: parse, apply, create, modify, stats, extract"
                )
        except Exception as e:
            return ToolResult(error=f"Error executing diff editor command '{command}': {str(e)}")

    def _parse_diff(self, diff_file: str) -> ToolResult:
        """Parse a diff file and show its structure."""
        try:
            import unidiff
        except ImportError:
            return ToolResult(error="unidiff library not installed. Please install it with: pip install unidiff")

        if not diff_file or not os.path.exists(diff_file):
            return ToolResult(error=f"Diff file not found: {diff_file}")

        try:
            with open(diff_file, 'r', encoding='utf-8') as f:
                patch = unidiff.PatchSet(f)

            output = []
            output.append(f"Diff file: {diff_file}")
            output.append(f"Number of files: {len(patch)}")
            output.append("")

            for i, patched_file in enumerate(patch):
                output.append(f"File {i + 1}: {patched_file.path}")
                output.append(f"  Source: {patched_file.source_file}")
                output.append(f"  Target: {patched_file.target_file}")
                output.append(f"  Added lines: {patched_file.added}")
                output.append(f"  Removed lines: {patched_file.removed}")
                output.append(f"  Is new file: {patched_file.is_added_file}")
                output.append(f"  Is deleted file: {patched_file.is_removed_file}")
                output.append(f"  Number of hunks: {len(patched_file)}")

                for j, hunk in enumerate(patched_file):
                    output.append(f"    Hunk {j + 1}: {hunk}")
                output.append("")

            return ToolResult(output="\n".join(output))

        except Exception as e:
            return ToolResult(error=f"Error parsing diff file: {str(e)}")

    def _apply_diff(self, diff_file: str, target_dir: Optional[str] = None) -> ToolResult:
        """Apply a diff to target files."""
        try:
            import unidiff
        except ImportError:
            return ToolResult(error="unidiff library not installed. Please install it with: pip install unidiff")

        if not diff_file or not os.path.exists(diff_file):
            return ToolResult(error=f"Diff file not found: {diff_file}")

        target_dir = target_dir or os.getcwd()

        try:
            with open(diff_file, 'r', encoding='utf-8') as f:
                patch = unidiff.PatchSet(f)

            applied_files = []
            errors = []

            for patched_file in patch:
                file_path = os.path.join(target_dir, patched_file.path)

                try:
                    if patched_file.is_added_file:
                        # Create new file
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            for hunk in patched_file:
                                for line in hunk:
                                    if line.is_added:
                                        f.write(line.value)
                        applied_files.append(f"Created: {file_path}")

                    elif patched_file.is_removed_file:
                        # Delete file
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            applied_files.append(f"Deleted: {file_path}")

                    else:
                        # Modify existing file
                        if not os.path.exists(file_path):
                            errors.append(f"Target file not found: {file_path}")
                            continue

                        with open(file_path, 'r', encoding='utf-8') as f:
                            original_lines = f.readlines()

                        # Apply hunks
                        modified_lines = original_lines.copy()
                        offset = 0

                        for hunk in patched_file:
                            # Simple hunk application (basic implementation)
                            start_line = hunk.target_start - 1 + offset

                            # Remove old lines
                            removed_count = 0
                            for line in hunk:
                                if line.is_removed:
                                    removed_count += 1

                            # Add new lines
                            new_lines = []
                            for line in hunk:
                                if line.is_added:
                                    new_lines.append(line.value)

                            # Replace lines
                            modified_lines[start_line:start_line + removed_count] = new_lines
                            offset += len(new_lines) - removed_count

                        # Write modified file
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.writelines(modified_lines)

                        applied_files.append(f"Modified: {file_path}")

                except Exception as e:
                    errors.append(f"Error applying patch to {file_path}: {str(e)}")

            output = []
            if applied_files:
                output.append("Successfully applied changes:")
                output.extend(applied_files)

            if errors:
                output.append("\nErrors encountered:")
                output.extend(errors)

            if not applied_files and not errors:
                output.append("No changes to apply.")

            return ToolResult(output="\n".join(output))

        except Exception as e:
            return ToolResult(error=f"Error applying diff: {str(e)}")

    def _create_diff(self, source_file: str, target_file: str, output_file: Optional[str] = None) -> ToolResult:
        """Create a diff between two files or directories."""
        if not source_file or not target_file:
            return ToolResult(error="Both source_file and target_file are required")

        if not os.path.exists(source_file) or not os.path.exists(target_file):
            return ToolResult(error="Source or target file/directory does not exist")

        try:
            import subprocess

            # Use system diff command to create unified diff
            cmd = ['diff', '-u', source_file, target_file]
            result = subprocess.run(cmd, capture_output=True, text=True)

            diff_content = result.stdout

            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(diff_content)
                return ToolResult(output=f"Diff created and saved to: {output_file}\n\nDiff content:\n{diff_content}")
            else:
                return ToolResult(output=f"Diff between {source_file} and {target_file}:\n\n{diff_content}")

        except Exception as e:
            return ToolResult(error=f"Error creating diff: {str(e)}")

    def _modify_diff(self, diff_file: str, file_filter: Optional[str], hunk_index: Optional[int],
                    new_content: Optional[str], output_file: Optional[str]) -> ToolResult:
        """Modify specific hunks in a diff file."""
        try:
            import unidiff
        except ImportError:
            return ToolResult(error="unidiff library not installed. Please install it with: pip install unidiff")

        if not diff_file or not os.path.exists(diff_file):
            return ToolResult(error=f"Diff file not found: {diff_file}")

        try:
            with open(diff_file, 'r', encoding='utf-8') as f:
                patch = unidiff.PatchSet(f)

            # This is a simplified implementation
            # In a full implementation, you would modify the patch structure
            output = []
            output.append(f"Diff modification requested for: {diff_file}")
            if file_filter:
                output.append(f"File filter: {file_filter}")
            if hunk_index is not None:
                output.append(f"Hunk index: {hunk_index}")
            if new_content:
                output.append(f"New content provided: {len(new_content)} characters")

            output.append("\nNote: Diff modification is a complex operation.")
            output.append("This is a basic implementation. For advanced modifications,")
            output.append("consider using specialized tools or manual editing.")

            return ToolResult(output="\n".join(output))

        except Exception as e:
            return ToolResult(error=f"Error modifying diff: {str(e)}")

    def _show_stats(self, diff_file: str) -> ToolResult:
        """Show statistics about a diff file."""
        try:
            import unidiff
        except ImportError:
            return ToolResult(error="unidiff library not installed. Please install it with: pip install unidiff")

        if not diff_file or not os.path.exists(diff_file):
            return ToolResult(error=f"Diff file not found: {diff_file}")

        try:
            with open(diff_file, 'r', encoding='utf-8') as f:
                patch = unidiff.PatchSet(f)

            total_added = sum(pf.added for pf in patch)
            total_removed = sum(pf.removed for pf in patch)
            total_files = len(patch)
            new_files = sum(1 for pf in patch if pf.is_added_file)
            deleted_files = sum(1 for pf in patch if pf.is_removed_file)
            modified_files = total_files - new_files - deleted_files

            output = []
            output.append(f"Diff Statistics for: {diff_file}")
            output.append("=" * 50)
            output.append(f"Total files affected: {total_files}")
            output.append(f"  - New files: {new_files}")
            output.append(f"  - Deleted files: {deleted_files}")
            output.append(f"  - Modified files: {modified_files}")
            output.append("")
            output.append(f"Total lines added: {total_added}")
            output.append(f"Total lines removed: {total_removed}")
            output.append(f"Net change: {total_added - total_removed:+d} lines")

            return ToolResult(output="\n".join(output))

        except Exception as e:
            return ToolResult(error=f"Error calculating diff stats: {str(e)}")

    def _extract_from_diff(self, diff_file: str, file_filter: Optional[str], output_file: Optional[str]) -> ToolResult:
        """Extract specific files or hunks from a diff."""
        try:
            import unidiff
        except ImportError:
            return ToolResult(error="unidiff library not installed. Please install it with: pip install unidiff")

        if not diff_file or not os.path.exists(diff_file):
            return ToolResult(error=f"Diff file not found: {diff_file}")

        try:
            with open(diff_file, 'r', encoding='utf-8') as f:
                patch = unidiff.PatchSet(f)

            extracted_content = []

            for patched_file in patch:
                if file_filter and file_filter not in patched_file.path:
                    continue

                extracted_content.append(f"--- {patched_file.source_file}")
                extracted_content.append(f"+++ {patched_file.target_file}")

                for hunk in patched_file:
                    extracted_content.append(str(hunk))

            result_content = "\n".join(extracted_content)

            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result_content)
                return ToolResult(output=f"Extracted content saved to: {output_file}\n\nExtracted content:\n{result_content}")
            else:
                return ToolResult(output=f"Extracted content:\n\n{result_content}")

        except Exception as e:
            return ToolResult(error=f"Error extracting from diff: {str(e)}")
