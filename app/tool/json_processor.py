"""
JSON Processor Tool for handling JSON data operations.
"""

import json
import jsonschema
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from app.tool.base import BaseTool, ToolResult


class JsonProcessor(BaseTool):
    """Tool for processing, validating, and manipulating JSON data."""

    name: str = "json_processor"
    description: str = """Process, validate, and manipulate JSON data.

    Available commands:
    - parse: Parse JSON string or file
    - validate: Validate JSON against schema
    - format: Format/prettify JSON
    - merge: Merge multiple JSON objects
    - extract: Extract specific values using JSONPath
    - transform: Transform JSON structure
    - minify: Minify JSON (remove whitespace)
    - compare: Compare two JSON objects
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["parse", "validate", "format", "merge", "extract", "transform", "minify", "compare"],
                "type": "string",
            },
            "json_data": {
                "description": "JSON string or data to process.",
                "type": "string",
            },
            "json_file": {
                "description": "Path to JSON file.",
                "type": "string",
            },
            "schema": {
                "description": "JSON schema for validation.",
                "type": "string",
            },
            "json_path": {
                "description": "JSONPath expression for extraction.",
                "type": "string",
            },
            "merge_data": {
                "description": "Additional JSON data to merge.",
                "type": "string",
            },
            "output_file": {
                "description": "Output file path.",
                "type": "string",
            },
            "indent": {
                "description": "Indentation for formatting (default: 2).",
                "type": "integer",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        json_data: Optional[str] = None,
        json_file: Optional[str] = None,
        schema: Optional[str] = None,
        json_path: Optional[str] = None,
        merge_data: Optional[str] = None,
        output_file: Optional[str] = None,
        indent: int = 2,
        **kwargs
    ) -> ToolResult:
        """Execute JSON processor command."""
        try:
            if command == "parse":
                return self._parse_json(json_data, json_file)
            elif command == "validate":
                return self._validate_json(json_data, json_file, schema)
            elif command == "format":
                return self._format_json(json_data, json_file, indent, output_file)
            elif command == "merge":
                return self._merge_json(json_data, merge_data, output_file)
            elif command == "extract":
                return self._extract_json(json_data, json_file, json_path)
            elif command == "transform":
                return self._transform_json(json_data, json_file)
            elif command == "minify":
                return self._minify_json(json_data, json_file, output_file)
            elif command == "compare":
                return self._compare_json(json_data, merge_data)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing JSON processor command '{command}': {str(e)}")

    def _parse_json(self, json_data: Optional[str], json_file: Optional[str]) -> ToolResult:
        """Parse JSON data."""
        try:
            if json_file:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif json_data:
                data = json.loads(json_data)
            else:
                return ToolResult(error="Either json_data or json_file must be provided")

            return ToolResult(output=f"JSON parsed successfully:\n{json.dumps(data, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            return ToolResult(error=f"Invalid JSON: {str(e)}")
        except FileNotFoundError:
            return ToolResult(error=f"File not found: {json_file}")

    def _validate_json(self, json_data: Optional[str], json_file: Optional[str], schema: Optional[str]) -> ToolResult:
        """Validate JSON against schema."""
        if not schema:
            return ToolResult(error="Schema is required for validation")

        try:
            # Load JSON data
            if json_file:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif json_data:
                data = json.loads(json_data)
            else:
                return ToolResult(error="Either json_data or json_file must be provided")

            # Load schema
            schema_obj = json.loads(schema)

            # Validate
            jsonschema.validate(data, schema_obj)
            return ToolResult(output="JSON validation successful - data conforms to schema")
        except jsonschema.ValidationError as e:
            return ToolResult(error=f"Validation error: {str(e)}")
        except json.JSONDecodeError as e:
            return ToolResult(error=f"Invalid JSON: {str(e)}")

    def _format_json(self, json_data: Optional[str], json_file: Optional[str], indent: int, output_file: Optional[str]) -> ToolResult:
        """Format JSON with proper indentation."""
        try:
            if json_file:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif json_data:
                data = json.loads(json_data)
            else:
                return ToolResult(error="Either json_data or json_file must be provided")

            formatted = json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)

            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(formatted)
                return ToolResult(output=f"Formatted JSON saved to: {output_file}")
            else:
                return ToolResult(output=f"Formatted JSON:\n{formatted}")
        except json.JSONDecodeError as e:
            return ToolResult(error=f"Invalid JSON: {str(e)}")

    def _merge_json(self, json_data: Optional[str], merge_data: Optional[str], output_file: Optional[str]) -> ToolResult:
        """Merge two JSON objects."""
        if not json_data or not merge_data:
            return ToolResult(error="Both json_data and merge_data are required")

        try:
            data1 = json.loads(json_data)
            data2 = json.loads(merge_data)

            if isinstance(data1, dict) and isinstance(data2, dict):
                merged = {**data1, **data2}
            elif isinstance(data1, list) and isinstance(data2, list):
                merged = data1 + data2
            else:
                return ToolResult(error="Can only merge objects or arrays of the same type")

            result = json.dumps(merged, indent=2, ensure_ascii=False)

            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result)
                return ToolResult(output=f"Merged JSON saved to: {output_file}")
            else:
                return ToolResult(output=f"Merged JSON:\n{result}")
        except json.JSONDecodeError as e:
            return ToolResult(error=f"Invalid JSON: {str(e)}")

    def _extract_json(self, json_data: Optional[str], json_file: Optional[str], json_path: Optional[str]) -> ToolResult:
        """Extract values using JSONPath (simplified implementation)."""
        if not json_path:
            return ToolResult(error="json_path is required for extraction")

        try:
            if json_file:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif json_data:
                data = json.loads(json_data)
            else:
                return ToolResult(error="Either json_data or json_file must be provided")

            # Simple JSONPath implementation (basic dot notation)
            keys = json_path.split('.')
            result = data
            for key in keys:
                if isinstance(result, dict) and key in result:
                    result = result[key]
                elif isinstance(result, list) and key.isdigit():
                    result = result[int(key)]
                else:
                    return ToolResult(error=f"Path not found: {json_path}")

            return ToolResult(output=f"Extracted value:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            return ToolResult(error=f"Invalid JSON: {str(e)}")

    def _transform_json(self, json_data: Optional[str], json_file: Optional[str]) -> ToolResult:
        """Transform JSON structure (example: flatten nested objects)."""
        try:
            if json_file:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif json_data:
                data = json.loads(json_data)
            else:
                return ToolResult(error="Either json_data or json_file must be provided")

            def flatten_dict(d, parent_key='', sep='_'):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_dict(v, new_key, sep=sep).items())
                    else:
                        items.append((new_key, v))
                return dict(items)

            if isinstance(data, dict):
                transformed = flatten_dict(data)
            else:
                transformed = data

            return ToolResult(output=f"Transformed JSON:\n{json.dumps(transformed, indent=2, ensure_ascii=False)}")
        except json.JSONDecodeError as e:
            return ToolResult(error=f"Invalid JSON: {str(e)}")

    def _minify_json(self, json_data: Optional[str], json_file: Optional[str], output_file: Optional[str]) -> ToolResult:
        """Minify JSON by removing whitespace."""
        try:
            if json_file:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif json_data:
                data = json.loads(json_data)
            else:
                return ToolResult(error="Either json_data or json_file must be provided")

            minified = json.dumps(data, separators=(',', ':'), ensure_ascii=False)

            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(minified)
                return ToolResult(output=f"Minified JSON saved to: {output_file}")
            else:
                return ToolResult(output=f"Minified JSON:\n{minified}")
        except json.JSONDecodeError as e:
            return ToolResult(error=f"Invalid JSON: {str(e)}")

    def _compare_json(self, json_data: Optional[str], merge_data: Optional[str]) -> ToolResult:
        """Compare two JSON objects."""
        if not json_data or not merge_data:
            return ToolResult(error="Both json_data and merge_data are required")

        try:
            data1 = json.loads(json_data)
            data2 = json.loads(merge_data)

            if data1 == data2:
                return ToolResult(output="JSON objects are identical")
            else:
                differences = []
                self._find_differences(data1, data2, "", differences)
                return ToolResult(output=f"JSON objects differ:\n" + "\n".join(differences))
        except json.JSONDecodeError as e:
            return ToolResult(error=f"Invalid JSON: {str(e)}")

    def _find_differences(self, obj1, obj2, path, differences):
        """Find differences between two objects."""
        if type(obj1) != type(obj2):
            differences.append(f"{path}: type mismatch ({type(obj1).__name__} vs {type(obj2).__name__})")
            return

        if isinstance(obj1, dict):
            all_keys = set(obj1.keys()) | set(obj2.keys())
            for key in all_keys:
                new_path = f"{path}.{key}" if path else key
                if key not in obj1:
                    differences.append(f"{new_path}: missing in first object")
                elif key not in obj2:
                    differences.append(f"{new_path}: missing in second object")
                else:
                    self._find_differences(obj1[key], obj2[key], new_path, differences)
        elif isinstance(obj1, list):
            if len(obj1) != len(obj2):
                differences.append(f"{path}: length mismatch ({len(obj1)} vs {len(obj2)})")
            for i in range(min(len(obj1), len(obj2))):
                self._find_differences(obj1[i], obj2[i], f"{path}[{i}]", differences)
        elif obj1 != obj2:
            differences.append(f"{path}: value mismatch ({obj1} vs {obj2})")
