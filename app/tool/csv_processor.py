"""
CSV Processor Tool for handling CSV data operations.
"""

import csv
import pandas as pd
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import io

from app.tool.base import BaseTool, ToolResult


class CsvProcessor(BaseTool):
    """Tool for processing, analyzing, and manipulating CSV data."""

    name: str = "csv_processor"
    description: str = """Process, analyze, and manipulate CSV data.

    Available commands:
    - read: Read and display CSV file
    - analyze: Analyze CSV data (statistics, info)
    - filter: Filter CSV rows based on conditions
    - sort: Sort CSV data
    - group: Group and aggregate CSV data
    - merge: Merge multiple CSV files
    - convert: Convert CSV to other formats (JSON, Excel)
    - clean: Clean CSV data (remove duplicates, handle missing values)
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["read", "analyze", "filter", "sort", "group", "merge", "convert", "clean"],
                "type": "string",
            },
            "csv_file": {
                "description": "Path to CSV file.",
                "type": "string",
            },
            "output_file": {
                "description": "Output file path.",
                "type": "string",
            },
            "columns": {
                "description": "Comma-separated list of columns to work with.",
                "type": "string",
            },
            "filter_condition": {
                "description": "Filter condition (e.g., 'age > 25').",
                "type": "string",
            },
            "sort_by": {
                "description": "Column to sort by.",
                "type": "string",
            },
            "group_by": {
                "description": "Column to group by.",
                "type": "string",
            },
            "aggregate": {
                "description": "Aggregation function (sum, mean, count, etc.).",
                "type": "string",
            },
            "merge_files": {
                "description": "Comma-separated list of CSV files to merge.",
                "type": "string",
            },
            "output_format": {
                "description": "Output format for conversion (json, excel, html).",
                "type": "string",
            },
            "delimiter": {
                "description": "CSV delimiter (default: comma).",
                "type": "string",
            },
            "encoding": {
                "description": "File encoding (default: utf-8).",
                "type": "string",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        csv_file: Optional[str] = None,
        output_file: Optional[str] = None,
        columns: Optional[str] = None,
        filter_condition: Optional[str] = None,
        sort_by: Optional[str] = None,
        group_by: Optional[str] = None,
        aggregate: Optional[str] = None,
        merge_files: Optional[str] = None,
        output_format: Optional[str] = None,
        delimiter: str = ",",
        encoding: str = "utf-8",
        **kwargs
    ) -> ToolResult:
        """Execute CSV processor command."""
        try:
            if command == "read":
                return self._read_csv(csv_file, delimiter, encoding, columns)
            elif command == "analyze":
                return self._analyze_csv(csv_file, delimiter, encoding)
            elif command == "filter":
                return self._filter_csv(csv_file, filter_condition, output_file, delimiter, encoding)
            elif command == "sort":
                return self._sort_csv(csv_file, sort_by, output_file, delimiter, encoding)
            elif command == "group":
                return self._group_csv(csv_file, group_by, aggregate, output_file, delimiter, encoding)
            elif command == "merge":
                return self._merge_csv(merge_files, output_file, delimiter, encoding)
            elif command == "convert":
                return self._convert_csv(csv_file, output_format, output_file, delimiter, encoding)
            elif command == "clean":
                return self._clean_csv(csv_file, output_file, delimiter, encoding)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing CSV processor command '{command}': {str(e)}")

    def _read_csv(self, csv_file: Optional[str], delimiter: str, encoding: str, columns: Optional[str]) -> ToolResult:
        """Read and display CSV file."""
        if not csv_file:
            return ToolResult(error="csv_file is required")

        try:
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding=encoding)

            if columns:
                col_list = [col.strip() for col in columns.split(',')]
                df = df[col_list]

            output = f"CSV File: {csv_file}\n"
            output += f"Shape: {df.shape}\n"
            output += f"Columns: {list(df.columns)}\n\n"
            output += "First 10 rows:\n"
            output += df.head(10).to_string()

            return ToolResult(output=output)
        except FileNotFoundError:
            return ToolResult(error=f"File not found: {csv_file}")
        except Exception as e:
            return ToolResult(error=f"Error reading CSV: {str(e)}")

    def _analyze_csv(self, csv_file: Optional[str], delimiter: str, encoding: str) -> ToolResult:
        """Analyze CSV data."""
        if not csv_file:
            return ToolResult(error="csv_file is required")

        try:
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding=encoding)

            output = f"CSV Analysis: {csv_file}\n"
            output += "=" * 50 + "\n\n"

            # Basic info
            output += f"Shape: {df.shape}\n"
            output += f"Columns: {list(df.columns)}\n"
            output += f"Data types:\n{df.dtypes}\n\n"

            # Missing values
            missing = df.isnull().sum()
            if missing.any():
                output += f"Missing values:\n{missing[missing > 0]}\n\n"

            # Numeric statistics
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                output += f"Numeric statistics:\n{df[numeric_cols].describe()}\n\n"

            # Categorical info
            categorical_cols = df.select_dtypes(include=['object']).columns
            if len(categorical_cols) > 0:
                output += "Categorical columns:\n"
                for col in categorical_cols:
                    unique_count = df[col].nunique()
                    output += f"  {col}: {unique_count} unique values\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error analyzing CSV: {str(e)}")

    def _filter_csv(self, csv_file: Optional[str], filter_condition: Optional[str],
                   output_file: Optional[str], delimiter: str, encoding: str) -> ToolResult:
        """Filter CSV rows based on conditions."""
        if not csv_file or not filter_condition:
            return ToolResult(error="csv_file and filter_condition are required")

        try:
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding=encoding)

            # Simple filter implementation
            filtered_df = df.query(filter_condition)

            if output_file:
                filtered_df.to_csv(output_file, index=False, encoding=encoding)
                return ToolResult(output=f"Filtered CSV saved to: {output_file}\nRows: {len(filtered_df)}")
            else:
                output = f"Filtered results ({len(filtered_df)} rows):\n"
                output += filtered_df.head(20).to_string()
                return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error filtering CSV: {str(e)}")

    def _sort_csv(self, csv_file: Optional[str], sort_by: Optional[str],
                 output_file: Optional[str], delimiter: str, encoding: str) -> ToolResult:
        """Sort CSV data."""
        if not csv_file or not sort_by:
            return ToolResult(error="csv_file and sort_by are required")

        try:
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding=encoding)

            # Handle multiple columns and ascending/descending
            if ',' in sort_by:
                sort_cols = [col.strip() for col in sort_by.split(',')]
            else:
                sort_cols = [sort_by]

            sorted_df = df.sort_values(by=sort_cols)

            if output_file:
                sorted_df.to_csv(output_file, index=False, encoding=encoding)
                return ToolResult(output=f"Sorted CSV saved to: {output_file}")
            else:
                output = f"Sorted by {sort_by}:\n"
                output += sorted_df.head(20).to_string()
                return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error sorting CSV: {str(e)}")

    def _group_csv(self, csv_file: Optional[str], group_by: Optional[str],
                  aggregate: Optional[str], output_file: Optional[str],
                  delimiter: str, encoding: str) -> ToolResult:
        """Group and aggregate CSV data."""
        if not csv_file or not group_by:
            return ToolResult(error="csv_file and group_by are required")

        try:
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding=encoding)

            grouped = df.groupby(group_by)

            if aggregate:
                if aggregate == "count":
                    result = grouped.size().reset_index(name='count')
                elif aggregate == "sum":
                    result = grouped.sum().reset_index()
                elif aggregate == "mean":
                    result = grouped.mean().reset_index()
                elif aggregate == "max":
                    result = grouped.max().reset_index()
                elif aggregate == "min":
                    result = grouped.min().reset_index()
                else:
                    return ToolResult(error=f"Unknown aggregate function: {aggregate}")
            else:
                result = grouped.size().reset_index(name='count')

            if output_file:
                result.to_csv(output_file, index=False, encoding=encoding)
                return ToolResult(output=f"Grouped CSV saved to: {output_file}")
            else:
                output = f"Grouped by {group_by} ({aggregate or 'count'}):\n"
                output += result.to_string()
                return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error grouping CSV: {str(e)}")

    def _merge_csv(self, merge_files: Optional[str], output_file: Optional[str],
                  delimiter: str, encoding: str) -> ToolResult:
        """Merge multiple CSV files."""
        if not merge_files:
            return ToolResult(error="merge_files is required")

        try:
            file_list = [f.strip() for f in merge_files.split(',')]
            dfs = []

            for file_path in file_list:
                df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)
                dfs.append(df)

            merged_df = pd.concat(dfs, ignore_index=True)

            if output_file:
                merged_df.to_csv(output_file, index=False, encoding=encoding)
                return ToolResult(output=f"Merged CSV saved to: {output_file}\nTotal rows: {len(merged_df)}")
            else:
                output = f"Merged CSV ({len(merged_df)} rows):\n"
                output += merged_df.head(20).to_string()
                return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error merging CSV files: {str(e)}")

    def _convert_csv(self, csv_file: Optional[str], output_format: Optional[str],
                    output_file: Optional[str], delimiter: str, encoding: str) -> ToolResult:
        """Convert CSV to other formats."""
        if not csv_file or not output_format:
            return ToolResult(error="csv_file and output_format are required")

        try:
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding=encoding)

            if output_format.lower() == "json":
                if output_file:
                    df.to_json(output_file, orient='records', indent=2)
                    return ToolResult(output=f"CSV converted to JSON: {output_file}")
                else:
                    json_str = df.to_json(orient='records', indent=2)
                    return ToolResult(output=f"JSON output:\n{json_str}")

            elif output_format.lower() == "excel":
                if not output_file:
                    output_file = csv_file.replace('.csv', '.xlsx')
                df.to_excel(output_file, index=False)
                return ToolResult(output=f"CSV converted to Excel: {output_file}")

            elif output_format.lower() == "html":
                if output_file:
                    df.to_html(output_file, index=False)
                    return ToolResult(output=f"CSV converted to HTML: {output_file}")
                else:
                    html_str = df.to_html(index=False)
                    return ToolResult(output=f"HTML output:\n{html_str}")

            else:
                return ToolResult(error=f"Unsupported output format: {output_format}")
        except Exception as e:
            return ToolResult(error=f"Error converting CSV: {str(e)}")

    def _clean_csv(self, csv_file: Optional[str], output_file: Optional[str],
                  delimiter: str, encoding: str) -> ToolResult:
        """Clean CSV data."""
        if not csv_file:
            return ToolResult(error="csv_file is required")

        try:
            df = pd.read_csv(csv_file, delimiter=delimiter, encoding=encoding)
            original_shape = df.shape

            # Remove duplicates
            df = df.drop_duplicates()

            # Handle missing values (simple strategy: drop rows with any NaN)
            df = df.dropna()

            # Strip whitespace from string columns
            string_cols = df.select_dtypes(include=['object']).columns
            for col in string_cols:
                df[col] = df[col].astype(str).str.strip()

            cleaned_shape = df.shape

            if output_file:
                df.to_csv(output_file, index=False, encoding=encoding)
                return ToolResult(output=f"Cleaned CSV saved to: {output_file}\n"
                                        f"Original shape: {original_shape}\n"
                                        f"Cleaned shape: {cleaned_shape}")
            else:
                output = f"CSV cleaned:\n"
                output += f"Original shape: {original_shape}\n"
                output += f"Cleaned shape: {cleaned_shape}\n"
                output += f"Removed {original_shape[0] - cleaned_shape[0]} rows\n\n"
                output += "First 10 rows of cleaned data:\n"
                output += df.head(10).to_string()
                return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error cleaning CSV: {str(e)}")
