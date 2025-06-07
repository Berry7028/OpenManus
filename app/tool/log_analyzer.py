"""
Log Analyzer Tool for analyzing log files and extracting insights.
"""

import re
import os
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Tuple
import gzip

from app.tool.base import BaseTool, ToolResult


class LogAnalyzer(BaseTool):
    """Tool for analyzing log files and extracting insights."""

    name: str = "log_analyzer"
    description: str = """Analyze log files and extract insights.

    Available commands:
    - analyze: Basic log file analysis
    - search: Search for patterns in log files
    - stats: Generate statistics from log files
    - errors: Find and analyze error patterns
    - timeline: Create timeline of events
    - top_ips: Find top IP addresses (for web logs)
    - filter: Filter log entries by criteria
    - tail: Show last N lines of log file
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["analyze", "search", "stats", "errors", "timeline", "top_ips", "filter", "tail"],
                "type": "string",
            },
            "log_file": {
                "description": "Path to log file.",
                "type": "string",
            },
            "pattern": {
                "description": "Search pattern (regex supported).",
                "type": "string",
            },
            "start_time": {
                "description": "Start time for filtering (YYYY-MM-DD HH:MM:SS).",
                "type": "string",
            },
            "end_time": {
                "description": "End time for filtering (YYYY-MM-DD HH:MM:SS).",
                "type": "string",
            },
            "level": {
                "description": "Log level to filter (ERROR, WARN, INFO, DEBUG).",
                "type": "string",
            },
            "lines": {
                "description": "Number of lines to show (for tail command).",
                "type": "integer",
            },
            "output_file": {
                "description": "Output file for results.",
                "type": "string",
            },
            "case_sensitive": {
                "description": "Case sensitive search.",
                "type": "boolean",
            },
        },
        "required": ["command", "log_file"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        log_file: str,
        pattern: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        level: Optional[str] = None,
        lines: int = 50,
        output_file: Optional[str] = None,
        case_sensitive: bool = False,
        **kwargs
    ) -> ToolResult:
        """Execute log analyzer command."""
        try:
            if not os.path.exists(log_file):
                return ToolResult(error=f"Log file not found: {log_file}")

            if command == "analyze":
                return self._analyze_log(log_file)
            elif command == "search":
                return self._search_log(log_file, pattern, case_sensitive, output_file)
            elif command == "stats":
                return self._generate_stats(log_file)
            elif command == "errors":
                return self._find_errors(log_file)
            elif command == "timeline":
                return self._create_timeline(log_file, start_time, end_time)
            elif command == "top_ips":
                return self._find_top_ips(log_file)
            elif command == "filter":
                return self._filter_log(log_file, level, start_time, end_time, output_file)
            elif command == "tail":
                return self._tail_log(log_file, lines)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing log analyzer command '{command}': {str(e)}")

    def _open_log_file(self, log_file: str):
        """Open log file, handling gzip compression."""
        if log_file.endswith('.gz'):
            return gzip.open(log_file, 'rt', encoding='utf-8', errors='ignore')
        else:
            return open(log_file, 'r', encoding='utf-8', errors='ignore')

    def _analyze_log(self, log_file: str) -> ToolResult:
        """Basic log file analysis."""
        try:
            file_size = os.path.getsize(log_file)
            line_count = 0
            first_line = None
            last_line = None

            # Common log patterns
            timestamp_patterns = [
                r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}',  # YYYY-MM-DD HH:MM:SS
                r'\d{2}/\w{3}/\d{4}:\d{2}:\d{2}:\d{2}',  # DD/MMM/YYYY:HH:MM:SS
                r'\w{3} \d{2} \d{2}:\d{2}:\d{2}',        # MMM DD HH:MM:SS
            ]

            log_levels = Counter()
            timestamps = []

            with self._open_log_file(log_file) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    line_count = line_num

                    if first_line is None:
                        first_line = line
                    last_line = line

                    # Count log levels
                    line_upper = line.upper()
                    for level in ['ERROR', 'WARN', 'WARNING', 'INFO', 'DEBUG', 'TRACE']:
                        if level in line_upper:
                            log_levels[level] += 1
                            break

                    # Extract timestamps
                    for pattern in timestamp_patterns:
                        match = re.search(pattern, line)
                        if match:
                            timestamps.append(match.group())
                            break

            # Calculate file info
            file_size_mb = file_size / (1024 * 1024)

            output = f"Log File Analysis: {log_file}\n"
            output += "=" * 50 + "\n"
            output += f"File Size: {file_size_mb:.2f} MB ({file_size:,} bytes)\n"
            output += f"Total Lines: {line_count:,}\n"

            if first_line:
                output += f"First Line: {first_line[:100]}...\n"
            if last_line:
                output += f"Last Line: {last_line[:100]}...\n"

            # Log levels
            if log_levels:
                output += "\nLog Levels:\n"
                for level, count in log_levels.most_common():
                    percentage = (count / line_count) * 100
                    output += f"  {level}: {count:,} ({percentage:.1f}%)\n"

            # Time range
            if timestamps:
                output += f"\nTime Range:\n"
                output += f"  First Timestamp: {timestamps[0]}\n"
                output += f"  Last Timestamp: {timestamps[-1]}\n"
                output += f"  Total Timestamps Found: {len(timestamps):,}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error analyzing log file: {str(e)}")

    def _search_log(self, log_file: str, pattern: Optional[str], case_sensitive: bool, output_file: Optional[str]) -> ToolResult:
        """Search for patterns in log files."""
        if not pattern:
            return ToolResult(error="Pattern is required for search")

        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)

            matches = []
            total_lines = 0

            with self._open_log_file(log_file) as f:
                for line_num, line in enumerate(f, 1):
                    total_lines = line_num
                    line = line.strip()

                    if regex.search(line):
                        matches.append((line_num, line))

            if output_file:
                with open(output_file, 'w') as f:
                    for line_num, line in matches:
                        f.write(f"{line_num}: {line}\n")

                output = f"Search completed. Found {len(matches)} matches.\n"
                output += f"Results saved to: {output_file}"
            else:
                output = f"Search Results for pattern '{pattern}':\n"
                output += "=" * 50 + "\n"
                output += f"Total lines searched: {total_lines:,}\n"
                output += f"Matches found: {len(matches):,}\n\n"

                # Show first 20 matches
                for line_num, line in matches[:20]:
                    output += f"Line {line_num}: {line}\n"

                if len(matches) > 20:
                    output += f"\n... and {len(matches) - 20} more matches"

            return ToolResult(output=output)
        except re.error as e:
            return ToolResult(error=f"Invalid regex pattern: {str(e)}")
        except Exception as e:
            return ToolResult(error=f"Error searching log file: {str(e)}")

    def _generate_stats(self, log_file: str) -> ToolResult:
        """Generate statistics from log files."""
        try:
            hourly_counts = defaultdict(int)
            daily_counts = defaultdict(int)
            ip_counts = Counter()
            status_codes = Counter()
            user_agents = Counter()

            # Common patterns
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            status_pattern = r'\s([1-5]\d{2})\s'
            user_agent_pattern = r'"([^"]*)"$'

            total_lines = 0

            with self._open_log_file(log_file) as f:
                for line in f:
                    total_lines += 1
                    line = line.strip()

                    # Extract timestamp for hourly/daily stats
                    timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
                    if timestamp_match:
                        timestamp = timestamp_match.group()
                        try:
                            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                            hour_key = dt.strftime('%Y-%m-%d %H:00')
                            day_key = dt.strftime('%Y-%m-%d')
                            hourly_counts[hour_key] += 1
                            daily_counts[day_key] += 1
                        except ValueError:
                            pass

                    # Extract IP addresses
                    ip_matches = re.findall(ip_pattern, line)
                    for ip in ip_matches:
                        ip_counts[ip] += 1

                    # Extract status codes
                    status_match = re.search(status_pattern, line)
                    if status_match:
                        status_codes[status_match.group(1)] += 1

                    # Extract user agents
                    ua_match = re.search(user_agent_pattern, line)
                    if ua_match:
                        user_agents[ua_match.group(1)] += 1

            output = f"Log Statistics: {log_file}\n"
            output += "=" * 50 + "\n"
            output += f"Total Lines: {total_lines:,}\n\n"

            # Top IPs
            if ip_counts:
                output += "Top 10 IP Addresses:\n"
                for ip, count in ip_counts.most_common(10):
                    percentage = (count / total_lines) * 100
                    output += f"  {ip}: {count:,} ({percentage:.1f}%)\n"
                output += "\n"

            # Status codes
            if status_codes:
                output += "HTTP Status Codes:\n"
                for status, count in status_codes.most_common():
                    percentage = (count / total_lines) * 100
                    output += f"  {status}: {count:,} ({percentage:.1f}%)\n"
                output += "\n"

            # Daily activity
            if daily_counts:
                output += "Daily Activity (last 7 days):\n"
                sorted_days = sorted(daily_counts.items())[-7:]
                for day, count in sorted_days:
                    output += f"  {day}: {count:,} entries\n"
                output += "\n"

            # Hourly activity
            if hourly_counts:
                output += "Hourly Activity (last 24 hours):\n"
                sorted_hours = sorted(hourly_counts.items())[-24:]
                for hour, count in sorted_hours:
                    output += f"  {hour}: {count:,} entries\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error generating statistics: {str(e)}")

    def _find_errors(self, log_file: str) -> ToolResult:
        """Find and analyze error patterns."""
        try:
            error_patterns = [
                (r'ERROR', 'ERROR'),
                (r'FATAL', 'FATAL'),
                (r'CRITICAL', 'CRITICAL'),
                (r'Exception', 'Exception'),
                (r'Traceback', 'Traceback'),
                (r'Failed', 'Failed'),
                (r'Error', 'Error'),
                (r'5\d{2}', 'HTTP 5xx'),
                (r'4\d{2}', 'HTTP 4xx'),
            ]

            error_counts = Counter()
            error_examples = defaultdict(list)
            total_lines = 0

            with self._open_log_file(log_file) as f:
                for line_num, line in enumerate(f, 1):
                    total_lines = line_num
                    line = line.strip()

                    for pattern, error_type in error_patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            error_counts[error_type] += 1
                            if len(error_examples[error_type]) < 3:
                                error_examples[error_type].append((line_num, line))

            output = f"Error Analysis: {log_file}\n"
            output += "=" * 50 + "\n"
            output += f"Total Lines: {total_lines:,}\n"
            output += f"Total Errors Found: {sum(error_counts.values()):,}\n\n"

            if error_counts:
                output += "Error Types:\n"
                for error_type, count in error_counts.most_common():
                    percentage = (count / total_lines) * 100
                    output += f"  {error_type}: {count:,} ({percentage:.2f}%)\n"

                    # Show examples
                    if error_examples[error_type]:
                        output += "    Examples:\n"
                        for line_num, line in error_examples[error_type]:
                            output += f"      Line {line_num}: {line[:80]}...\n"
                    output += "\n"
            else:
                output += "No errors found in the log file.\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error analyzing errors: {str(e)}")

    def _create_timeline(self, log_file: str, start_time: Optional[str], end_time: Optional[str]) -> ToolResult:
        """Create timeline of events."""
        try:
            events = []

            # Parse time filters
            start_dt = None
            end_dt = None
            if start_time:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            if end_time:
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

            with self._open_log_file(log_file) as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Extract timestamp
                    timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
                    if timestamp_match:
                        timestamp_str = timestamp_match.group()
                        try:
                            dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

                            # Apply time filters
                            if start_dt and dt < start_dt:
                                continue
                            if end_dt and dt > end_dt:
                                continue

                            # Determine event type
                            event_type = "INFO"
                            if re.search(r'ERROR|FATAL|CRITICAL', line, re.IGNORECASE):
                                event_type = "ERROR"
                            elif re.search(r'WARN', line, re.IGNORECASE):
                                event_type = "WARNING"
                            elif re.search(r'DEBUG', line, re.IGNORECASE):
                                event_type = "DEBUG"

                            events.append((dt, event_type, line_num, line))
                        except ValueError:
                            pass

            # Sort events by timestamp
            events.sort(key=lambda x: x[0])

            output = f"Timeline: {log_file}\n"
            output += "=" * 50 + "\n"

            if start_time or end_time:
                output += f"Time Range: {start_time or 'Beginning'} to {end_time or 'End'}\n"

            output += f"Total Events: {len(events):,}\n\n"

            # Group events by hour
            hourly_events = defaultdict(list)
            for dt, event_type, line_num, line in events:
                hour_key = dt.strftime('%Y-%m-%d %H:00')
                hourly_events[hour_key].append((dt, event_type, line_num, line))

            # Show timeline
            for hour in sorted(hourly_events.keys()):
                hour_events = hourly_events[hour]
                error_count = sum(1 for _, event_type, _, _ in hour_events if event_type == "ERROR")
                warning_count = sum(1 for _, event_type, _, _ in hour_events if event_type == "WARNING")

                output += f"{hour}: {len(hour_events)} events"
                if error_count > 0:
                    output += f" ({error_count} errors"
                if warning_count > 0:
                    output += f", {warning_count} warnings" if error_count > 0 else f" ({warning_count} warnings"
                if error_count > 0 or warning_count > 0:
                    output += ")"
                output += "\n"

                # Show first few events of each hour
                for dt, event_type, line_num, line in hour_events[:3]:
                    output += f"  {dt.strftime('%H:%M:%S')} [{event_type}] {line[:60]}...\n"

                if len(hour_events) > 3:
                    output += f"  ... and {len(hour_events) - 3} more events\n"
                output += "\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error creating timeline: {str(e)}")

    def _find_top_ips(self, log_file: str) -> ToolResult:
        """Find top IP addresses (for web logs)."""
        try:
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ip_counts = Counter()
            ip_details = defaultdict(lambda: {'requests': 0, 'errors': 0, 'bytes': 0})

            with self._open_log_file(log_file) as f:
                for line in f:
                    line = line.strip()

                    # Find IP addresses
                    ip_matches = re.findall(ip_pattern, line)
                    for ip in ip_matches:
                        ip_counts[ip] += 1
                        ip_details[ip]['requests'] += 1

                        # Check for errors
                        if re.search(r'[45]\d{2}', line):
                            ip_details[ip]['errors'] += 1

                        # Extract bytes if available
                        bytes_match = re.search(r'\s(\d+)$', line)
                        if bytes_match:
                            try:
                                bytes_val = int(bytes_match.group(1))
                                ip_details[ip]['bytes'] += bytes_val
                            except ValueError:
                                pass

            output = f"Top IP Addresses: {log_file}\n"
            output += "=" * 60 + "\n"
            output += f"{'IP Address':<15} {'Requests':<10} {'Errors':<8} {'Bytes':<12} {'Error%':<8}\n"
            output += "-" * 60 + "\n"

            for ip, count in ip_counts.most_common(20):
                details = ip_details[ip]
                error_rate = (details['errors'] / details['requests']) * 100 if details['requests'] > 0 else 0
                bytes_mb = details['bytes'] / (1024 * 1024)

                output += f"{ip:<15} {details['requests']:<10} {details['errors']:<8} {bytes_mb:<12.1f} {error_rate:<8.1f}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error finding top IPs: {str(e)}")

    def _filter_log(self, log_file: str, level: Optional[str], start_time: Optional[str],
                   end_time: Optional[str], output_file: Optional[str]) -> ToolResult:
        """Filter log entries by criteria."""
        try:
            filtered_lines = []
            total_lines = 0

            # Parse time filters
            start_dt = None
            end_dt = None
            if start_time:
                start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
            if end_time:
                end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

            with self._open_log_file(log_file) as f:
                for line_num, line in enumerate(f, 1):
                    total_lines = line_num
                    line = line.strip()

                    # Apply level filter
                    if level and level.upper() not in line.upper():
                        continue

                    # Apply time filter
                    if start_dt or end_dt:
                        timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
                        if timestamp_match:
                            timestamp_str = timestamp_match.group()
                            try:
                                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                if start_dt and dt < start_dt:
                                    continue
                                if end_dt and dt > end_dt:
                                    continue
                            except ValueError:
                                continue
                        else:
                            continue

                    filtered_lines.append((line_num, line))

            if output_file:
                with open(output_file, 'w') as f:
                    for line_num, line in filtered_lines:
                        f.write(f"{line}\n")

                output = f"Filtering completed.\n"
                output += f"Total lines processed: {total_lines:,}\n"
                output += f"Filtered lines: {len(filtered_lines):,}\n"
                output += f"Results saved to: {output_file}"
            else:
                output = f"Filtered Log Entries:\n"
                output += "=" * 50 + "\n"
                output += f"Total lines: {total_lines:,}\n"
                output += f"Matching lines: {len(filtered_lines):,}\n\n"

                # Show first 50 filtered lines
                for line_num, line in filtered_lines[:50]:
                    output += f"Line {line_num}: {line}\n"

                if len(filtered_lines) > 50:
                    output += f"\n... and {len(filtered_lines) - 50} more lines"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error filtering log: {str(e)}")

    def _tail_log(self, log_file: str, lines: int) -> ToolResult:
        """Show last N lines of log file."""
        try:
            with self._open_log_file(log_file) as f:
                all_lines = f.readlines()

            last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

            output = f"Last {len(last_lines)} lines of {log_file}:\n"
            output += "=" * 50 + "\n"

            for i, line in enumerate(last_lines, len(all_lines) - len(last_lines) + 1):
                output += f"Line {i}: {line.rstrip()}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error tailing log file: {str(e)}")
