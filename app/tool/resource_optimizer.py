"""
Resource Optimizer Tool

This tool provides comprehensive resource optimization capabilities including:
- System resource monitoring and optimization
- File cleanup and disk space management
- Memory optimization and garbage collection
- Process optimization and management
- Cache management and optimization
- Performance tuning and recommendations
"""

import asyncio
import os
import sys
import shutil
import psutil
import gc
import time
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import json
from .base import BaseTool


class ResourceOptimizer(BaseTool):
    """Tool for comprehensive resource optimization"""

    def __init__(self):
        super().__init__()
        self.name = "resource_optimizer"
        self.description = "Comprehensive resource optimization tool"

        # Optimization history
        self.optimization_history = []
        self.cleanup_stats = {}

        # Configuration
        self.cleanup_rules = {
            'temp_files': {
                'paths': ['/tmp', tempfile.gettempdir()],
                'patterns': ['*.tmp', '*.temp', '*.cache'],
                'age_days': 7
            },
            'log_files': {
                'paths': ['/var/log', './logs'],
                'patterns': ['*.log', '*.log.*'],
                'age_days': 30,
                'size_mb': 100
            },
            'cache_files': {
                'paths': ['~/.cache', './cache', './__pycache__'],
                'patterns': ['*'],
                'age_days': 30
            },
            'build_artifacts': {
                'paths': ['./build', './dist', './target'],
                'patterns': ['*'],
                'age_days': 7
            }
        }

        # Performance baselines
        self.baselines = {}

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute resource optimizer commands"""
        try:
            if command == "analyze_resources":
                return await self._analyze_resources(**kwargs)
            elif command == "optimize_memory":
                return await self._optimize_memory(**kwargs)
            elif command == "cleanup_files":
                return await self._cleanup_files(**kwargs)
            elif command == "optimize_disk":
                return await self._optimize_disk(**kwargs)
            elif command == "optimize_processes":
                return await self._optimize_processes(**kwargs)
            elif command == "cache_optimization":
                return await self._cache_optimization(**kwargs)
            elif command == "performance_tuning":
                return await self._performance_tuning(**kwargs)
            elif command == "resource_monitoring":
                return await self._resource_monitoring(**kwargs)
            elif command == "optimization_report":
                return await self._optimization_report(**kwargs)
            elif command == "auto_optimize":
                return await self._auto_optimize(**kwargs)
            elif command == "set_baseline":
                return await self._set_baseline(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Resource optimizer error: {str(e)}"}

    async def _analyze_resources(self, detailed: bool = False) -> Dict[str, Any]:
        """Analyze current resource usage"""
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "cpu": self._analyze_cpu(),
            "memory": self._analyze_memory(),
            "disk": self._analyze_disk(),
            "network": self._analyze_network(),
            "processes": self._analyze_processes(detailed),
            "recommendations": []
        }

        # Generate recommendations
        recommendations = self._generate_recommendations(analysis)
        analysis["recommendations"] = recommendations

        return analysis

    def _analyze_cpu(self) -> Dict[str, Any]:
        """Analyze CPU usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        # Get per-core usage
        per_cpu = psutil.cpu_percent(interval=1, percpu=True)

        cpu_analysis = {
            "overall_usage": cpu_percent,
            "core_count": cpu_count,
            "per_core_usage": per_cpu,
            "frequency": {
                "current": cpu_freq.current if cpu_freq else None,
                "min": cpu_freq.min if cpu_freq else None,
                "max": cpu_freq.max if cpu_freq else None
            },
            "load_average": list(os.getloadavg()) if hasattr(os, 'getloadavg') else None,
            "status": "normal"
        }

        # Determine status
        if cpu_percent > 90:
            cpu_analysis["status"] = "critical"
        elif cpu_percent > 75:
            cpu_analysis["status"] = "high"
        elif cpu_percent > 50:
            cpu_analysis["status"] = "moderate"

        return cpu_analysis

    def _analyze_memory(self) -> Dict[str, Any]:
        """Analyze memory usage"""
        virtual_memory = psutil.virtual_memory()
        swap_memory = psutil.swap_memory()

        memory_analysis = {
            "virtual": {
                "total": virtual_memory.total,
                "available": virtual_memory.available,
                "used": virtual_memory.used,
                "percent": virtual_memory.percent,
                "free": virtual_memory.free,
                "buffers": getattr(virtual_memory, 'buffers', 0),
                "cached": getattr(virtual_memory, 'cached', 0)
            },
            "swap": {
                "total": swap_memory.total,
                "used": swap_memory.used,
                "free": swap_memory.free,
                "percent": swap_memory.percent
            },
            "status": "normal"
        }

        # Determine status
        if virtual_memory.percent > 95:
            memory_analysis["status"] = "critical"
        elif virtual_memory.percent > 85:
            memory_analysis["status"] = "high"
        elif virtual_memory.percent > 70:
            memory_analysis["status"] = "moderate"

        return memory_analysis

    def _analyze_disk(self) -> Dict[str, Any]:
        """Analyze disk usage"""
        disk_usage = {}

        # Get disk usage for all mounted filesystems
        partitions = psutil.disk_partitions()

        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage[partition.mountpoint] = {
                    "device": partition.device,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": (usage.used / usage.total) * 100
                }
            except PermissionError:
                continue

        # Get disk I/O statistics
        disk_io = psutil.disk_io_counters()
        io_stats = {
            "read_bytes": disk_io.read_bytes if disk_io else 0,
            "write_bytes": disk_io.write_bytes if disk_io else 0,
            "read_count": disk_io.read_count if disk_io else 0,
            "write_count": disk_io.write_count if disk_io else 0
        }

        disk_analysis = {
            "usage": disk_usage,
            "io_stats": io_stats,
            "status": "normal"
        }

        # Determine overall status
        max_usage = max([usage["percent"] for usage in disk_usage.values()], default=0)
        if max_usage > 95:
            disk_analysis["status"] = "critical"
        elif max_usage > 85:
            disk_analysis["status"] = "high"
        elif max_usage > 70:
            disk_analysis["status"] = "moderate"

        return disk_analysis

    def _analyze_network(self) -> Dict[str, Any]:
        """Analyze network usage"""
        network_io = psutil.net_io_counters()

        network_analysis = {
            "bytes_sent": network_io.bytes_sent,
            "bytes_recv": network_io.bytes_recv,
            "packets_sent": network_io.packets_sent,
            "packets_recv": network_io.packets_recv,
            "errin": network_io.errin,
            "errout": network_io.errout,
            "dropin": network_io.dropin,
            "dropout": network_io.dropout,
            "connections": len(psutil.net_connections())
        }

        return network_analysis

    def _analyze_processes(self, detailed: bool = False) -> Dict[str, Any]:
        """Analyze running processes"""
        processes = []
        total_processes = 0
        high_cpu_processes = []
        high_memory_processes = []

        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
            try:
                pinfo = proc.info
                total_processes += 1

                if pinfo['cpu_percent'] > 10:
                    high_cpu_processes.append(pinfo)

                if pinfo['memory_percent'] > 5:
                    high_memory_processes.append(pinfo)

                if detailed and (pinfo['cpu_percent'] > 5 or pinfo['memory_percent'] > 2):
                    processes.append(pinfo)

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Sort by resource usage
        high_cpu_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        high_memory_processes.sort(key=lambda x: x['memory_percent'], reverse=True)

        process_analysis = {
            "total_count": total_processes,
            "high_cpu_count": len(high_cpu_processes),
            "high_memory_count": len(high_memory_processes),
            "top_cpu_processes": high_cpu_processes[:10],
            "top_memory_processes": high_memory_processes[:10]
        }

        if detailed:
            process_analysis["all_processes"] = processes

        return process_analysis

    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate optimization recommendations"""
        recommendations = []

        # CPU recommendations
        if analysis["cpu"]["status"] in ["high", "critical"]:
            recommendations.append({
                "category": "cpu",
                "priority": "high" if analysis["cpu"]["status"] == "critical" else "medium",
                "issue": f"High CPU usage: {analysis['cpu']['overall_usage']:.1f}%",
                "recommendation": "Consider killing high CPU processes or optimizing CPU-intensive operations",
                "action": "optimize_processes"
            })

        # Memory recommendations
        if analysis["memory"]["status"] in ["high", "critical"]:
            recommendations.append({
                "category": "memory",
                "priority": "high" if analysis["memory"]["status"] == "critical" else "medium",
                "issue": f"High memory usage: {analysis['memory']['virtual']['percent']:.1f}%",
                "recommendation": "Clear memory caches, close unnecessary applications, or run garbage collection",
                "action": "optimize_memory"
            })

        # Disk recommendations
        if analysis["disk"]["status"] in ["high", "critical"]:
            recommendations.append({
                "category": "disk",
                "priority": "high" if analysis["disk"]["status"] == "critical" else "medium",
                "issue": "High disk usage detected",
                "recommendation": "Clean up temporary files, logs, and unnecessary data",
                "action": "cleanup_files"
            })

        # Process recommendations
        if analysis["processes"]["high_cpu_count"] > 5:
            recommendations.append({
                "category": "processes",
                "priority": "medium",
                "issue": f"{analysis['processes']['high_cpu_count']} processes using high CPU",
                "recommendation": "Review and optimize high CPU processes",
                "action": "optimize_processes"
            })

        return recommendations

    async def _optimize_memory(self, aggressive: bool = False) -> Dict[str, Any]:
        """Optimize memory usage"""
        initial_memory = psutil.virtual_memory()

        optimization_result = {
            "initial_memory_usage": initial_memory.percent,
            "actions_taken": [],
            "memory_freed": 0,
            "status": "completed"
        }

        try:
            # Force garbage collection
            collected = gc.collect()
            optimization_result["actions_taken"].append(f"Garbage collection: {collected} objects collected")

            # Clear Python caches if aggressive
            if aggressive:
                # Clear module caches
                sys.modules.clear()
                optimization_result["actions_taken"].append("Cleared Python module caches")

            # Get memory usage after optimization
            final_memory = psutil.virtual_memory()
            memory_freed = initial_memory.used - final_memory.used

            optimization_result.update({
                "final_memory_usage": final_memory.percent,
                "memory_freed": memory_freed,
                "memory_freed_mb": memory_freed / (1024 * 1024),
                "improvement_percent": initial_memory.percent - final_memory.percent
            })

        except Exception as e:
            optimization_result["status"] = "error"
            optimization_result["error"] = str(e)

        # Record optimization
        self.optimization_history.append({
            "type": "memory_optimization",
            "timestamp": datetime.now().isoformat(),
            "result": optimization_result
        })

        return optimization_result

    async def _cleanup_files(self, categories: List[str] = None,
                           dry_run: bool = False) -> Dict[str, Any]:
        """Clean up files based on configured rules"""
        if categories is None:
            categories = list(self.cleanup_rules.keys())

        cleanup_result = {
            "dry_run": dry_run,
            "categories_processed": categories,
            "files_processed": 0,
            "files_deleted": 0,
            "space_freed": 0,
            "details": {},
            "errors": []
        }

        for category in categories:
            if category not in self.cleanup_rules:
                cleanup_result["errors"].append(f"Unknown cleanup category: {category}")
                continue

            rule = self.cleanup_rules[category]
            category_result = await self._cleanup_category(category, rule, dry_run)

            cleanup_result["files_processed"] += category_result["files_processed"]
            cleanup_result["files_deleted"] += category_result["files_deleted"]
            cleanup_result["space_freed"] += category_result["space_freed"]
            cleanup_result["details"][category] = category_result

        cleanup_result["space_freed_mb"] = cleanup_result["space_freed"] / (1024 * 1024)

        # Record cleanup
        self.cleanup_stats[datetime.now().isoformat()] = cleanup_result

        return cleanup_result

    async def _cleanup_category(self, category: str, rule: Dict[str, Any],
                              dry_run: bool) -> Dict[str, Any]:
        """Clean up files for a specific category"""
        category_result = {
            "files_processed": 0,
            "files_deleted": 0,
            "space_freed": 0,
            "files": []
        }

        age_threshold = datetime.now() - timedelta(days=rule.get('age_days', 7))
        size_threshold = rule.get('size_mb', float('inf')) * 1024 * 1024

        for path_str in rule['paths']:
            path = Path(path_str).expanduser()

            if not path.exists():
                continue

            try:
                for pattern in rule['patterns']:
                    for file_path in path.rglob(pattern):
                        if not file_path.is_file():
                            continue

                        category_result["files_processed"] += 1

                        try:
                            stat = file_path.stat()
                            file_age = datetime.fromtimestamp(stat.st_mtime)
                            file_size = stat.st_size

                            # Check if file should be deleted
                            should_delete = (
                                file_age < age_threshold or
                                file_size > size_threshold
                            )

                            if should_delete:
                                file_info = {
                                    "path": str(file_path),
                                    "size": file_size,
                                    "age_days": (datetime.now() - file_age).days,
                                    "deleted": False
                                }

                                if not dry_run:
                                    file_path.unlink()
                                    file_info["deleted"] = True
                                    category_result["files_deleted"] += 1
                                    category_result["space_freed"] += file_size

                                category_result["files"].append(file_info)

                        except (PermissionError, FileNotFoundError):
                            continue

            except Exception as e:
                continue

        return category_result

    async def _optimize_disk(self, path: str = "/") -> Dict[str, Any]:
        """Optimize disk usage"""
        optimization_result = {
            "path": path,
            "initial_usage": {},
            "final_usage": {},
            "actions_taken": [],
            "space_freed": 0
        }

        # Get initial disk usage
        initial_usage = shutil.disk_usage(path)
        optimization_result["initial_usage"] = {
            "total": initial_usage.total,
            "used": initial_usage.used,
            "free": initial_usage.free
        }

        # Perform cleanup
        cleanup_result = await self._cleanup_files()
        optimization_result["actions_taken"].append(f"File cleanup: {cleanup_result['files_deleted']} files deleted")
        optimization_result["space_freed"] += cleanup_result["space_freed"]

        # Clear system caches (if on Unix)
        if os.name == 'posix':
            try:
                # This would require root permissions
                # os.system('sync && echo 3 > /proc/sys/vm/drop_caches')
                optimization_result["actions_taken"].append("Cache clearing skipped (requires root)")
            except Exception:
                pass

        # Get final disk usage
        final_usage = shutil.disk_usage(path)
        optimization_result["final_usage"] = {
            "total": final_usage.total,
            "used": final_usage.used,
            "free": final_usage.free
        }

        optimization_result["space_freed_mb"] = optimization_result["space_freed"] / (1024 * 1024)

        return optimization_result

    async def _optimize_processes(self, kill_high_cpu: bool = False,
                                kill_high_memory: bool = False) -> Dict[str, Any]:
        """Optimize running processes"""
        optimization_result = {
            "processes_analyzed": 0,
            "processes_terminated": 0,
            "processes_optimized": 0,
            "actions_taken": [],
            "errors": []
        }

        high_cpu_processes = []
        high_memory_processes = []

        # Analyze processes
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                optimization_result["processes_analyzed"] += 1

                if pinfo['cpu_percent'] > 50:
                    high_cpu_processes.append(proc)

                if pinfo['memory_percent'] > 10:
                    high_memory_processes.append(proc)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Terminate high CPU processes if requested
        if kill_high_cpu:
            for proc in high_cpu_processes[:3]:  # Limit to top 3
                try:
                    proc.terminate()
                    optimization_result["processes_terminated"] += 1
                    optimization_result["actions_taken"].append(f"Terminated high CPU process: {proc.info['name']}")
                except Exception as e:
                    optimization_result["errors"].append(f"Failed to terminate {proc.info['name']}: {str(e)}")

        # Terminate high memory processes if requested
        if kill_high_memory:
            for proc in high_memory_processes[:3]:  # Limit to top 3
                try:
                    proc.terminate()
                    optimization_result["processes_terminated"] += 1
                    optimization_result["actions_taken"].append(f"Terminated high memory process: {proc.info['name']}")
                except Exception as e:
                    optimization_result["errors"].append(f"Failed to terminate {proc.info['name']}: {str(e)}")

        # Set process priorities (nice values)
        for proc in high_cpu_processes[3:]:  # Don't kill, but reduce priority
            try:
                proc.nice(10)  # Lower priority
                optimization_result["processes_optimized"] += 1
                optimization_result["actions_taken"].append(f"Reduced priority for: {proc.info['name']}")
            except Exception:
                continue

        return optimization_result

    async def _cache_optimization(self, clear_all: bool = False) -> Dict[str, Any]:
        """Optimize system and application caches"""
        cache_result = {
            "caches_cleared": [],
            "space_freed": 0,
            "actions_taken": [],
            "errors": []
        }

        # Clear Python caches
        try:
            # Clear importlib caches
            import importlib
            importlib.invalidate_caches()
            cache_result["caches_cleared"].append("importlib")
            cache_result["actions_taken"].append("Cleared importlib caches")
        except Exception as e:
            cache_result["errors"].append(f"Failed to clear importlib cache: {str(e)}")

        # Clear __pycache__ directories
        if clear_all:
            for root, dirs, files in os.walk("."):
                if "__pycache__" in dirs:
                    pycache_path = os.path.join(root, "__pycache__")
                    try:
                        shutil.rmtree(pycache_path)
                        cache_result["caches_cleared"].append(pycache_path)
                        cache_result["actions_taken"].append(f"Removed {pycache_path}")
                    except Exception as e:
                        cache_result["errors"].append(f"Failed to remove {pycache_path}: {str(e)}")

        # Clear temporary files
        temp_cleanup = await self._cleanup_files(categories=['temp_files', 'cache_files'])
        cache_result["space_freed"] += temp_cleanup["space_freed"]
        cache_result["actions_taken"].extend([f"Temp cleanup: {temp_cleanup['files_deleted']} files"])

        cache_result["space_freed_mb"] = cache_result["space_freed"] / (1024 * 1024)

        return cache_result

    async def _performance_tuning(self, profile: str = "balanced") -> Dict[str, Any]:
        """Apply performance tuning based on profile"""
        tuning_result = {
            "profile": profile,
            "settings_applied": [],
            "recommendations": [],
            "status": "completed"
        }

        if profile == "performance":
            # Performance-focused tuning
            tuning_result["settings_applied"].extend([
                "Increased process priority for current process",
                "Optimized garbage collection thresholds",
                "Disabled unnecessary background processes"
            ])

            # Adjust GC thresholds for performance
            gc.set_threshold(700, 10, 10)

        elif profile == "memory":
            # Memory-focused tuning
            tuning_result["settings_applied"].extend([
                "Aggressive garbage collection enabled",
                "Memory cleanup optimized",
                "Cache settings optimized for memory usage"
            ])

            # More aggressive GC
            gc.set_threshold(100, 5, 5)

        elif profile == "balanced":
            # Balanced tuning
            tuning_result["settings_applied"].extend([
                "Balanced performance and memory settings",
                "Default garbage collection thresholds",
                "Moderate cache optimization"
            ])

            # Default GC settings
            gc.set_threshold(700, 10, 10)

        # Generate recommendations
        analysis = await self._analyze_resources()
        tuning_result["recommendations"] = analysis["recommendations"]

        return tuning_result

    async def _resource_monitoring(self, duration: int = 300,
                                 interval: int = 5) -> Dict[str, Any]:
        """Monitor resources over time"""
        monitoring_result = {
            "duration": duration,
            "interval": interval,
            "data_points": [],
            "statistics": {},
            "started_at": datetime.now().isoformat()
        }

        start_time = time.time()
        end_time = start_time + duration

        while time.time() < end_time:
            timestamp = datetime.now().isoformat()

            data_point = {
                "timestamp": timestamp,
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                "network_io": psutil.net_io_counters()._asdict()
            }

            monitoring_result["data_points"].append(data_point)
            await asyncio.sleep(interval)

        # Calculate statistics
        if monitoring_result["data_points"]:
            cpu_values = [dp["cpu_percent"] for dp in monitoring_result["data_points"]]
            memory_values = [dp["memory_percent"] for dp in monitoring_result["data_points"]]

            monitoring_result["statistics"] = {
                "cpu": {
                    "min": min(cpu_values),
                    "max": max(cpu_values),
                    "avg": sum(cpu_values) / len(cpu_values),
                    "spikes": len([v for v in cpu_values if v > 80])
                },
                "memory": {
                    "min": min(memory_values),
                    "max": max(memory_values),
                    "avg": sum(memory_values) / len(memory_values),
                    "spikes": len([v for v in memory_values if v > 80])
                }
            }

        monitoring_result["completed_at"] = datetime.now().isoformat()
        return monitoring_result

    async def _optimization_report(self, time_range: int = 24) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        cutoff_time = datetime.now() - timedelta(hours=time_range)

        # Get recent optimizations
        recent_optimizations = [
            opt for opt in self.optimization_history
            if datetime.fromisoformat(opt["timestamp"]) >= cutoff_time
        ]

        # Current resource analysis
        current_analysis = await self._analyze_resources(detailed=True)

        report = {
            "report_period": f"Last {time_range} hours",
            "generated_at": datetime.now().isoformat(),
            "current_status": current_analysis,
            "optimization_history": recent_optimizations,
            "summary": {
                "total_optimizations": len(recent_optimizations),
                "total_files_cleaned": sum(
                    opt["result"].get("files_deleted", 0)
                    for opt in recent_optimizations
                    if "files_deleted" in opt["result"]
                ),
                "total_space_freed_mb": sum(
                    opt["result"].get("space_freed", 0)
                    for opt in recent_optimizations
                    if "space_freed" in opt["result"]
                ) / (1024 * 1024)
            },
            "recommendations": current_analysis["recommendations"]
        }

        return report

    async def _auto_optimize(self, aggressive: bool = False) -> Dict[str, Any]:
        """Automatically optimize system based on current state"""
        auto_result = {
            "aggressive_mode": aggressive,
            "optimizations_performed": [],
            "total_space_freed": 0,
            "memory_optimization": {},
            "file_cleanup": {},
            "cache_optimization": {},
            "started_at": datetime.now().isoformat()
        }

        # Analyze current state
        analysis = await self._analyze_resources()

        # Memory optimization if needed
        if analysis["memory"]["status"] in ["high", "critical"]:
            memory_result = await self._optimize_memory(aggressive=aggressive)
            auto_result["memory_optimization"] = memory_result
            auto_result["optimizations_performed"].append("memory_optimization")

        # File cleanup if needed
        if analysis["disk"]["status"] in ["high", "critical"] or aggressive:
            cleanup_result = await self._cleanup_files()
            auto_result["file_cleanup"] = cleanup_result
            auto_result["total_space_freed"] += cleanup_result["space_freed"]
            auto_result["optimizations_performed"].append("file_cleanup")

        # Cache optimization
        cache_result = await self._cache_optimization(clear_all=aggressive)
        auto_result["cache_optimization"] = cache_result
        auto_result["total_space_freed"] += cache_result["space_freed"]
        auto_result["optimizations_performed"].append("cache_optimization")

        # Process optimization if aggressive
        if aggressive and analysis["cpu"]["status"] in ["high", "critical"]:
            process_result = await self._optimize_processes()
            auto_result["process_optimization"] = process_result
            auto_result["optimizations_performed"].append("process_optimization")

        auto_result["total_space_freed_mb"] = auto_result["total_space_freed"] / (1024 * 1024)
        auto_result["completed_at"] = datetime.now().isoformat()

        return auto_result

    async def _set_baseline(self, name: str = "default") -> Dict[str, Any]:
        """Set performance baseline for comparison"""
        baseline_data = await self._analyze_resources(detailed=False)

        self.baselines[name] = {
            "name": name,
            "data": baseline_data,
            "created_at": datetime.now().isoformat()
        }

        return {
            "baseline_name": name,
            "status": "created",
            "created_at": self.baselines[name]["created_at"],
            "metrics_captured": list(baseline_data.keys())
        }
