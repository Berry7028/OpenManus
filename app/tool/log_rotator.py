"""
Log Rotator Tool

This tool provides comprehensive log rotation and management capabilities including:
- Automatic log file rotation based on size, time, or custom criteria
- Log compression and archiving
- Log retention policies and cleanup
- Log monitoring and alerting
- Multiple log format support
- Real-time log watching and filtering
"""

import asyncio
import os
import gzip
import shutil
import glob
import time
import re
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
import threading
import json
from pathlib import Path
import tempfile
from .base import BaseTool


class LogRotator(BaseTool):
    """Tool for log file rotation and management"""

    def __init__(self):
        super().__init__()
        self.name = "log_rotator"
        self.description = "Comprehensive log rotation and management tool"

        # Active watchers
        self.watchers = {}
        self.watcher_threads = {}

        # Rotation configurations
        self.rotation_configs = {}

        # Default settings
        self.default_config = {
            "max_size": 10 * 1024 * 1024,  # 10MB
            "max_files": 5,
            "compress": True,
            "compress_delay": 1,  # Compress after 1 rotation
            "date_format": "%Y%m%d_%H%M%S",
            "backup_extension": ".{index}",
            "compress_extension": ".gz"
        }

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute log rotator commands"""
        try:
            if command == "rotate_log":
                return await self._rotate_log(**kwargs)
            elif command == "setup_rotation":
                return await self._setup_rotation(**kwargs)
            elif command == "compress_logs":
                return await self._compress_logs(**kwargs)
            elif command == "cleanup_logs":
                return await self._cleanup_logs(**kwargs)
            elif command == "monitor_logs":
                return await self._monitor_logs(**kwargs)
            elif command == "analyze_logs":
                return await self._analyze_logs(**kwargs)
            elif command == "watch_log":
                return await self._watch_log(**kwargs)
            elif command == "stop_watching":
                return await self._stop_watching(**kwargs)
            elif command == "list_watchers":
                return await self._list_watchers(**kwargs)
            elif command == "rotate_status":
                return await self._rotate_status(**kwargs)
            elif command == "archive_logs":
                return await self._archive_logs(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Log rotator error: {str(e)}"}

    async def _rotate_log(self, log_file: str, max_size: Optional[int] = None,
                         max_files: Optional[int] = None, compress: bool = True,
                         force: bool = False) -> Dict[str, Any]:
        """Rotate a log file"""
        if not os.path.exists(log_file):
            return {"error": f"Log file not found: {log_file}"}

        config = self.default_config.copy()
        if max_size is not None:
            config["max_size"] = max_size
        if max_files is not None:
            config["max_files"] = max_files
        config["compress"] = compress

        file_stat = os.stat(log_file)
        current_size = file_stat.st_size

        # Check if rotation is needed
        if not force and current_size < config["max_size"]:
            return {
                "log_file": log_file,
                "rotation_needed": False,
                "current_size": current_size,
                "max_size": config["max_size"],
                "reason": "File size below threshold"
            }

        try:
            # Get base name and directory
            log_dir = os.path.dirname(log_file)
            log_name = os.path.basename(log_file)
            base_name, ext = os.path.splitext(log_name)

            # Find existing rotated files
            pattern = f"{base_name}.*{ext}"
            existing_files = []

            for file_path in glob.glob(os.path.join(log_dir, pattern)):
                if file_path != log_file:
                    # Extract rotation number
                    file_base = os.path.basename(file_path)
                    match = re.search(r'\.(\d+)\.', file_base)
                    if match:
                        rotation_num = int(match.group(1))
                        existing_files.append((file_path, rotation_num))

            # Sort by rotation number
            existing_files.sort(key=lambda x: x[1])

            # Remove oldest files if we exceed max_files
            files_to_remove = []
            if len(existing_files) >= config["max_files"]:
                files_to_remove = existing_files[config["max_files"]-1:]
                for file_path, _ in files_to_remove:
                    os.remove(file_path)

            # Shift existing files
            for file_path, rotation_num in reversed(existing_files):
                if (rotation_num + 1) < config["max_files"]:
                    new_name = f"{base_name}.{rotation_num + 1}{ext}"
                    if compress and rotation_num >= config["compress_delay"]:
                        new_name += config["compress_extension"]

                    new_path = os.path.join(log_dir, new_name)

                    # Compress if needed
                    if compress and rotation_num >= config["compress_delay"] and not file_path.endswith('.gz'):
                        self._compress_file(file_path, new_path)
                        os.remove(file_path)
                    else:
                        shutil.move(file_path, new_path)

            # Move current log to .1
            rotated_name = f"{base_name}.1{ext}"
            rotated_path = os.path.join(log_dir, rotated_name)
            shutil.move(log_file, rotated_path)

            # Create new empty log file
            with open(log_file, 'w') as f:
                pass

            # Preserve original file permissions
            shutil.copystat(rotated_path, log_file)

            return {
                "log_file": log_file,
                "rotation_performed": True,
                "rotated_to": rotated_path,
                "original_size": current_size,
                "files_removed": len(files_to_remove),
                "removed_files": [f[0] for f in files_to_remove],
                "rotated_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Rotation failed: {str(e)}"}

    def _compress_file(self, source_path: str, target_path: str):
        """Compress a file using gzip"""
        with open(source_path, 'rb') as f_in:
            with gzip.open(target_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    async def _setup_rotation(self, log_file: str, schedule: str = "size",
                            max_size: int = 10485760, max_files: int = 5,
                            compress: bool = True, time_interval: str = "daily") -> Dict[str, Any]:
        """Setup automatic log rotation"""
        config = {
            "log_file": log_file,
            "schedule": schedule,  # "size", "time", "both"
            "max_size": max_size,
            "max_files": max_files,
            "compress": compress,
            "time_interval": time_interval,  # "hourly", "daily", "weekly", "monthly"
            "last_rotation": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat()
        }

        self.rotation_configs[log_file] = config

        # Start monitoring thread if not already running
        if log_file not in self.watcher_threads:
            thread = threading.Thread(
                target=self._rotation_monitor_thread,
                args=(log_file,),
                daemon=True
            )
            thread.start()
            self.watcher_threads[log_file] = thread

        return {
            "log_file": log_file,
            "rotation_config": config,
            "monitoring_started": True,
            "setup_at": datetime.now().isoformat()
        }

    def _rotation_monitor_thread(self, log_file: str):
        """Background thread to monitor log file for rotation"""
        while log_file in self.rotation_configs:
            try:
                config = self.rotation_configs[log_file]
                needs_rotation = False

                if os.path.exists(log_file):
                    # Check size-based rotation
                    if config["schedule"] in ["size", "both"]:
                        current_size = os.path.getsize(log_file)
                        if current_size >= config["max_size"]:
                            needs_rotation = True

                    # Check time-based rotation
                    if config["schedule"] in ["time", "both"]:
                        last_rotation = datetime.fromisoformat(config["last_rotation"])
                        now = datetime.now()

                        if config["time_interval"] == "hourly" and (now - last_rotation).seconds >= 3600:
                            needs_rotation = True
                        elif config["time_interval"] == "daily" and (now - last_rotation).days >= 1:
                            needs_rotation = True
                        elif config["time_interval"] == "weekly" and (now - last_rotation).days >= 7:
                            needs_rotation = True
                        elif config["time_interval"] == "monthly" and (now - last_rotation).days >= 30:
                            needs_rotation = True

                    # Perform rotation if needed
                    if needs_rotation:
                        asyncio.run(self._rotate_log(
                            log_file,
                            max_size=config["max_size"],
                            max_files=config["max_files"],
                            compress=config["compress"],
                            force=True
                        ))
                        config["last_rotation"] = datetime.now().isoformat()

                # Sleep for 60 seconds before next check
                time.sleep(60)

            except Exception as e:
                print(f"Rotation monitor error for {log_file}: {e}")
                time.sleep(60)

    async def _compress_logs(self, log_pattern: str, target_dir: Optional[str] = None,
                           remove_original: bool = False, min_age_hours: int = 1) -> Dict[str, Any]:
        """Compress log files matching pattern"""
        log_files = glob.glob(log_pattern)
        compressed_files = []
        errors = []
        total_original_size = 0
        total_compressed_size = 0

        if target_dir and not os.path.exists(target_dir):
            os.makedirs(target_dir)

        min_age = datetime.now() - timedelta(hours=min_age_hours)

        for log_file in log_files:
            try:
                # Check file age
                file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_mtime > min_age:
                    continue  # Skip recent files

                # Skip already compressed files
                if log_file.endswith('.gz'):
                    continue

                original_size = os.path.getsize(log_file)

                # Determine target path
                if target_dir:
                    compressed_name = os.path.basename(log_file) + '.gz'
                    compressed_path = os.path.join(target_dir, compressed_name)
                else:
                    compressed_path = log_file + '.gz'

                # Compress file
                self._compress_file(log_file, compressed_path)
                compressed_size = os.path.getsize(compressed_path)

                compressed_files.append({
                    "original_file": log_file,
                    "compressed_file": compressed_path,
                    "original_size": original_size,
                    "compressed_size": compressed_size,
                    "compression_ratio": round((1 - compressed_size / original_size) * 100, 2)
                })

                total_original_size += original_size
                total_compressed_size += compressed_size

                # Remove original if requested
                if remove_original:
                    os.remove(log_file)

            except Exception as e:
                errors.append(f"Failed to compress {log_file}: {str(e)}")

        return {
            "log_pattern": log_pattern,
            "files_processed": len(compressed_files),
            "total_original_size": total_original_size,
            "total_compressed_size": total_compressed_size,
            "overall_compression_ratio": round((1 - total_compressed_size / total_original_size) * 100, 2) if total_original_size > 0 else 0,
            "compressed_files": compressed_files,
            "errors": errors,
            "compressed_at": datetime.now().isoformat()
        }

    async def _cleanup_logs(self, log_pattern: str, max_age_days: int = 30,
                          max_files: Optional[int] = None, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up old log files"""
        log_files = glob.glob(log_pattern)
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        files_to_delete = []
        total_size_to_free = 0

        # Filter by age
        for log_file in log_files:
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_mtime < cutoff_date:
                    file_size = os.path.getsize(log_file)
                    files_to_delete.append({
                        "file": log_file,
                        "age_days": (datetime.now() - file_mtime).days,
                        "size": file_size,
                        "modified": file_mtime.isoformat()
                    })
                    total_size_to_free += file_size
            except OSError:
                continue

        # Sort by modification time (oldest first)
        files_to_delete.sort(key=lambda x: x["modified"])

        # Apply max_files limit if specified
        if max_files and len(files_to_delete) > max_files:
            files_to_delete = files_to_delete[:max_files]
            total_size_to_free = sum(f["size"] for f in files_to_delete)

        if dry_run:
            return {
                "log_pattern": log_pattern,
                "dry_run": True,
                "files_to_delete": len(files_to_delete),
                "total_size_to_free": total_size_to_free,
                "cutoff_date": cutoff_date.isoformat(),
                "files": files_to_delete
            }

        # Actually delete files
        deleted_files = []
        errors = []

        for file_info in files_to_delete:
            try:
                os.remove(file_info["file"])
                deleted_files.append(file_info)
            except Exception as e:
                errors.append(f"Failed to delete {file_info['file']}: {str(e)}")

        return {
            "log_pattern": log_pattern,
            "dry_run": False,
            "files_deleted": len(deleted_files),
            "total_size_freed": sum(f["size"] for f in deleted_files),
            "deleted_files": deleted_files,
            "errors": errors,
            "cleanup_completed_at": datetime.now().isoformat()
        }

    async def _monitor_logs(self, log_files: List[str], alert_patterns: Optional[List[str]] = None,
                          alert_threshold: int = 10, monitor_duration: int = 300) -> Dict[str, Any]:
        """Monitor log files for patterns and anomalies"""
        if alert_patterns is None:
            alert_patterns = [
                r"ERROR",
                r"CRITICAL",
                r"FATAL",
                r"Exception",
                r"failed",
                r"timeout"
            ]

        compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in alert_patterns]

        monitoring_results = {}
        start_time = time.time()
        end_time = start_time + monitor_duration

        for log_file in log_files:
            if not os.path.exists(log_file):
                continue

            file_results = {
                "file": log_file,
                "alerts": [],
                "pattern_counts": {pattern: 0 for pattern in alert_patterns},
                "total_lines_processed": 0,
                "monitoring_start": datetime.now().isoformat()
            }

            try:
                # Get initial file position
                with open(log_file, 'r') as f:
                    f.seek(0, 2)  # Seek to end
                    initial_position = f.tell()

                # Monitor for new content
                while time.time() < end_time:
                    with open(log_file, 'r') as f:
                        f.seek(initial_position)
                        new_lines = f.readlines()

                        for line in new_lines:
                            file_results["total_lines_processed"] += 1

                            # Check against alert patterns
                            for i, pattern in enumerate(compiled_patterns):
                                if pattern.search(line):
                                    pattern_name = alert_patterns[i]
                                    file_results["pattern_counts"][pattern_name] += 1

                                    # Create alert if threshold exceeded
                                    if file_results["pattern_counts"][pattern_name] == alert_threshold:
                                        file_results["alerts"].append({
                                            "pattern": pattern_name,
                                            "threshold_exceeded": alert_threshold,
                                            "line_sample": line.strip(),
                                            "timestamp": datetime.now().isoformat()
                                        })

                        initial_position = f.tell()

                    await asyncio.sleep(1)

                file_results["monitoring_end"] = datetime.now().isoformat()
                monitoring_results[log_file] = file_results

            except Exception as e:
                monitoring_results[log_file] = {"error": str(e)}

        # Generate summary
        total_alerts = sum(len(result.get("alerts", [])) for result in monitoring_results.values())
        total_lines = sum(result.get("total_lines_processed", 0) for result in monitoring_results.values())

        return {
            "monitored_files": len(log_files),
            "monitor_duration": monitor_duration,
            "alert_patterns": alert_patterns,
            "alert_threshold": alert_threshold,
            "total_alerts_generated": total_alerts,
            "total_lines_processed": total_lines,
            "file_results": monitoring_results,
            "monitoring_completed_at": datetime.now().isoformat()
        }

    async def _analyze_logs(self, log_file: str, analysis_type: str = "summary",
                          start_time: Optional[str] = None, end_time: Optional[str] = None) -> Dict[str, Any]:
        """Analyze log file content"""
        if not os.path.exists(log_file):
            return {"error": f"Log file not found: {log_file}"}

        try:
            analysis_results = {
                "log_file": log_file,
                "analysis_type": analysis_type,
                "file_size": os.path.getsize(log_file),
                "analyzed_at": datetime.now().isoformat()
            }

            if analysis_type == "summary":
                # Basic file statistics
                line_count = 0
                error_count = 0
                warning_count = 0
                info_count = 0

                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line_count += 1
                        line_lower = line.lower()

                        if any(word in line_lower for word in ['error', 'err', 'fail', 'exception']):
                            error_count += 1
                        elif any(word in line_lower for word in ['warn', 'warning']):
                            warning_count += 1
                        elif any(word in line_lower for word in ['info', 'debug', 'trace']):
                            info_count += 1

                analysis_results.update({
                    "total_lines": line_count,
                    "error_lines": error_count,
                    "warning_lines": warning_count,
                    "info_lines": info_count,
                    "error_rate": round(error_count / line_count * 100, 2) if line_count > 0 else 0
                })

            elif analysis_type == "patterns":
                # Pattern analysis
                patterns = {
                    'timestamp': r'\d{4}-\d{2}-\d{2}[\s\T]\d{2}:\d{2}:\d{2}',
                    'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
                    'url': r'https?://[^\s<>"{}|\\^`[\]]+',
                    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    'error_code': r'\b[45]\d{2}\b',
                    'memory_usage': r'\d+(?:\.\d+)?\s*[KMGT]?B',
                    'duration': r'\d+(?:\.\d+)?\s*(?:ms|sec|min|hr)',
                }

                pattern_counts = {name: 0 for name in patterns}
                pattern_samples = {name: [] for name in patterns}

                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        for pattern_name, pattern in patterns.items():
                            matches = re.findall(pattern, line, re.IGNORECASE)
                            pattern_counts[pattern_name] += len(matches)

                            # Store samples
                            if matches and len(pattern_samples[pattern_name]) < 5:
                                pattern_samples[pattern_name].extend(matches[:5])

                analysis_results.update({
                    "pattern_counts": pattern_counts,
                    "pattern_samples": pattern_samples
                })

            elif analysis_type == "timeline":
                # Timeline analysis
                timestamp_pattern = r'(\d{4}-\d{2}-\d{2}[\s\T]\d{2}:\d{2}:\d{2})'
                hourly_counts = {}

                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        match = re.search(timestamp_pattern, line)
                        if match:
                            timestamp_str = match.group(1)
                            try:
                                # Parse timestamp and round to hour
                                if 'T' in timestamp_str:
                                    timestamp = datetime.fromisoformat(timestamp_str.replace('T', ' '))
                                else:
                                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

                                hour_key = timestamp.strftime('%Y-%m-%d %H:00:00')
                                hourly_counts[hour_key] = hourly_counts.get(hour_key, 0) + 1
                            except ValueError:
                                continue

                analysis_results.update({
                    "hourly_activity": dict(sorted(hourly_counts.items())),
                    "peak_hour": max(hourly_counts.items(), key=lambda x: x[1]) if hourly_counts else None
                })

            return analysis_results

        except Exception as e:
            return {"error": f"Log analysis failed: {str(e)}"}

    async def _watch_log(self, log_file: str, filter_pattern: Optional[str] = None,
                        max_lines: int = 100) -> Dict[str, Any]:
        """Start watching a log file in real-time"""
        if not os.path.exists(log_file):
            return {"error": f"Log file not found: {log_file}"}

        watcher_id = f"{log_file}_{int(time.time())}"

        # Compile filter pattern if provided
        filter_regex = None
        if filter_pattern:
            try:
                filter_regex = re.compile(filter_pattern, re.IGNORECASE)
            except re.error as e:
                return {"error": f"Invalid filter pattern: {str(e)}"}

        # Initialize watcher
        self.watchers[watcher_id] = {
            "log_file": log_file,
            "filter_pattern": filter_pattern,
            "filter_regex": filter_regex,
            "max_lines": max_lines,
            "lines": [],
            "started_at": datetime.now().isoformat(),
            "running": True
        }

        # Start watcher thread
        thread = threading.Thread(
            target=self._log_watcher_thread,
            args=(watcher_id,),
            daemon=True
        )
        thread.start()
        self.watcher_threads[watcher_id] = thread

        return {
            "watcher_id": watcher_id,
            "log_file": log_file,
            "filter_pattern": filter_pattern,
            "max_lines": max_lines,
            "started_at": datetime.now().isoformat()
        }

    def _log_watcher_thread(self, watcher_id: str):
        """Background thread to watch log file"""
        watcher = self.watchers[watcher_id]
        log_file = watcher["log_file"]

        try:
            with open(log_file, 'r') as f:
                # Seek to end of file
                f.seek(0, 2)

                while watcher["running"]:
                    line = f.readline()

                    if line:
                        line = line.strip()

                        # Apply filter if specified
                        if watcher["filter_regex"]:
                            if not watcher["filter_regex"].search(line):
                                continue

                        # Add line with timestamp
                        line_entry = {
                            "timestamp": datetime.now().isoformat(),
                            "content": line
                        }

                        watcher["lines"].append(line_entry)

                        # Maintain max_lines limit
                        if len(watcher["lines"]) > watcher["max_lines"]:
                            watcher["lines"] = watcher["lines"][-watcher["max_lines"]:]

                    else:
                        # No new content, sleep briefly
                        time.sleep(0.1)

        except Exception as e:
            watcher["error"] = str(e)
            watcher["running"] = False

    async def _stop_watching(self, watcher_id: Optional[str] = None, log_file: Optional[str] = None) -> Dict[str, Any]:
        """Stop watching a log file"""
        stopped_watchers = []

        # Find watchers to stop
        watchers_to_stop = []
        if watcher_id:
            if watcher_id in self.watchers:
                watchers_to_stop.append(watcher_id)
        elif log_file:
            for w_id, watcher in self.watchers.items():
                if watcher["log_file"] == log_file:
                    watchers_to_stop.append(w_id)
        else:
            # Stop all watchers
            watchers_to_stop = list(self.watchers.keys())

        # Stop the watchers
        for w_id in watchers_to_stop:
            if w_id in self.watchers:
                self.watchers[w_id]["running"] = False

                # Get final results
                watcher_info = {
                    "watcher_id": w_id,
                    "log_file": self.watchers[w_id]["log_file"],
                    "lines_captured": len(self.watchers[w_id]["lines"]),
                    "stopped_at": datetime.now().isoformat()
                }

                stopped_watchers.append(watcher_info)

                # Clean up
                del self.watchers[w_id]
                if w_id in self.watcher_threads:
                    del self.watcher_threads[w_id]

        return {
            "stopped_watchers": len(stopped_watchers),
            "watchers": stopped_watchers
        }

    async def _list_watchers(self) -> Dict[str, Any]:
        """List active log watchers"""
        active_watchers = []

        for watcher_id, watcher in self.watchers.items():
            watcher_info = {
                "watcher_id": watcher_id,
                "log_file": watcher["log_file"],
                "filter_pattern": watcher.get("filter_pattern"),
                "max_lines": watcher["max_lines"],
                "lines_captured": len(watcher["lines"]),
                "started_at": watcher["started_at"],
                "running": watcher["running"],
                "recent_lines": watcher["lines"][-5:] if watcher["lines"] else []
            }

            if "error" in watcher:
                watcher_info["error"] = watcher["error"]

            active_watchers.append(watcher_info)

        return {
            "active_watchers": len(active_watchers),
            "watchers": active_watchers
        }

    async def _rotate_status(self) -> Dict[str, Any]:
        """Get status of all rotation configurations"""
        status_info = {
            "active_rotations": len(self.rotation_configs),
            "active_watchers": len(self.watchers),
            "rotation_configs": []
        }

        for log_file, config in self.rotation_configs.items():
            config_status = config.copy()

            # Add current file status
            if os.path.exists(log_file):
                file_stat = os.stat(log_file)
                config_status.update({
                    "current_size": file_stat.st_size,
                    "size_percentage": round((file_stat.st_size / config["max_size"]) * 100, 2),
                    "last_modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                })
            else:
                config_status.update({
                    "current_size": 0,
                    "size_percentage": 0,
                    "file_exists": False
                })

            status_info["rotation_configs"].append(config_status)

        return status_info

    async def _archive_logs(self, log_pattern: str, archive_dir: str,
                          archive_format: str = "tar.gz", max_age_days: int = 7) -> Dict[str, Any]:
        """Archive old log files"""
        if not os.path.exists(archive_dir):
            os.makedirs(archive_dir)

        log_files = glob.glob(log_pattern)
        cutoff_date = datetime.now() - timedelta(days=max_age_days)

        files_to_archive = []
        for log_file in log_files:
            try:
                file_mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_mtime < cutoff_date:
                    files_to_archive.append(log_file)
            except OSError:
                continue

        if not files_to_archive:
            return {
                "log_pattern": log_pattern,
                "archive_dir": archive_dir,
                "files_archived": 0,
                "message": "No files found matching criteria"
            }

        # Create archive name with timestamp
        archive_name = f"logs_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{archive_format}"
        archive_path = os.path.join(archive_dir, archive_name)

        try:
            if archive_format == "tar.gz":
                import tarfile
                with tarfile.open(archive_path, 'w:gz') as tar:
                    for log_file in files_to_archive:
                        tar.add(log_file, arcname=os.path.basename(log_file))

            elif archive_format == "zip":
                import zipfile
                with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for log_file in files_to_archive:
                        zip_file.write(log_file, os.path.basename(log_file))

            else:
                return {"error": f"Unsupported archive format: {archive_format}"}

            # Remove original files after successful archiving
            for log_file in files_to_archive:
                os.remove(log_file)

            archive_size = os.path.getsize(archive_path)

            return {
                "log_pattern": log_pattern,
                "archive_dir": archive_dir,
                "archive_file": archive_path,
                "archive_format": archive_format,
                "files_archived": len(files_to_archive),
                "archived_files": files_to_archive,
                "archive_size": archive_size,
                "archived_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Archive creation failed: {str(e)}"}
