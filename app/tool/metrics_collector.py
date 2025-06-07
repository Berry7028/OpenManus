"""
Metrics Collector Tool

This tool provides comprehensive metrics collection and analysis capabilities including:
- System performance metrics (CPU, memory, disk, network)
- Application metrics monitoring
- Custom metrics collection and tracking
- Time-series data analysis
- Alerting and threshold monitoring
- Metrics visualization and reporting
"""

import asyncio
import json
import time
import psutil
import os
import sys
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import threading
from .base import BaseTool


class MetricsCollector(BaseTool):
    """Tool for comprehensive metrics collection and analysis"""

    def __init__(self):
        super().__init__()
        self.name = "metrics_collector"
        self.description = "Comprehensive metrics collection and analysis tool"

        # Metrics storage
        self.metrics_data = defaultdict(deque)
        self.custom_metrics = {}
        self.alerts = []
        self.thresholds = {}

        # Collection settings
        self.collection_interval = 60  # seconds
        self.max_data_points = 1000
        self.is_collecting = False
        self.collection_thread = None

        # Metric categories
        self.metric_categories = {
            'system': ['cpu_percent', 'memory_percent', 'disk_usage', 'network_io'],
            'process': ['process_cpu', 'process_memory', 'process_threads'],
            'application': ['response_time', 'error_rate', 'throughput'],
            'custom': []
        }

        # Built-in collectors
        self.collectors = {
            'cpu_percent': self._collect_cpu_percent,
            'memory_percent': self._collect_memory_percent,
            'disk_usage': self._collect_disk_usage,
            'network_io': self._collect_network_io,
            'process_cpu': self._collect_process_cpu,
            'process_memory': self._collect_process_memory,
            'load_average': self._collect_load_average,
            'disk_io': self._collect_disk_io
        }

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute metrics collector commands"""
        try:
            if command == "start_collection":
                return await self._start_collection(**kwargs)
            elif command == "stop_collection":
                return await self._stop_collection(**kwargs)
            elif command == "collect_metrics":
                return await self._collect_metrics(**kwargs)
            elif command == "get_metrics":
                return await self._get_metrics(**kwargs)
            elif command == "add_custom_metric":
                return await self._add_custom_metric(**kwargs)
            elif command == "set_threshold":
                return await self._set_threshold(**kwargs)
            elif command == "check_alerts":
                return await self._check_alerts(**kwargs)
            elif command == "analyze_metrics":
                return await self._analyze_metrics(**kwargs)
            elif command == "export_metrics":
                return await self._export_metrics(**kwargs)
            elif command == "metrics_report":
                return await self._metrics_report(**kwargs)
            elif command == "system_health":
                return await self._system_health(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Metrics collector error: {str(e)}"}

    async def _start_collection(self, interval: int = 60,
                              metrics: List[str] = None) -> Dict[str, Any]:
        """Start continuous metrics collection"""
        if self.is_collecting:
            return {"message": "Metrics collection is already running"}

        self.collection_interval = interval
        self.is_collecting = True

        # Default metrics if none specified
        if metrics is None:
            metrics = ['cpu_percent', 'memory_percent', 'disk_usage', 'network_io']

        # Start collection thread
        self.collection_thread = threading.Thread(
            target=self._collection_worker,
            args=(metrics,),
            daemon=True
        )
        self.collection_thread.start()

        return {
            "message": "Metrics collection started",
            "interval": interval,
            "metrics": metrics,
            "started_at": datetime.now().isoformat()
        }

    def _collection_worker(self, metrics: List[str]):
        """Background worker for continuous metrics collection"""
        while self.is_collecting:
            try:
                timestamp = datetime.now()

                for metric_name in metrics:
                    if metric_name in self.collectors:
                        value = self.collectors[metric_name]()

                        # Store metric data point
                        self.metrics_data[metric_name].append({
                            'timestamp': timestamp.isoformat(),
                            'value': value
                        })

                        # Limit data points
                        if len(self.metrics_data[metric_name]) > self.max_data_points:
                            self.metrics_data[metric_name].popleft()

                        # Check thresholds
                        self._check_threshold(metric_name, value, timestamp)

                time.sleep(self.collection_interval)

            except Exception as e:
                print(f"Collection error: {e}")
                time.sleep(self.collection_interval)

    async def _stop_collection(self) -> Dict[str, Any]:
        """Stop continuous metrics collection"""
        if not self.is_collecting:
            return {"message": "Metrics collection is not running"}

        self.is_collecting = False

        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=5)

        return {
            "message": "Metrics collection stopped",
            "stopped_at": datetime.now().isoformat(),
            "total_data_points": sum(len(data) for data in self.metrics_data.values())
        }

    async def _collect_metrics(self, metrics: List[str] = None,
                             duration: int = 300) -> Dict[str, Any]:
        """Collect metrics for a specific duration"""
        if metrics is None:
            metrics = ['cpu_percent', 'memory_percent', 'disk_usage', 'network_io']

        collected_data = defaultdict(list)
        start_time = time.time()
        end_time = start_time + duration

        interval = min(5, duration // 10)  # Collect at least 10 data points

        while time.time() < end_time:
            timestamp = datetime.now()

            for metric_name in metrics:
                if metric_name in self.collectors:
                    value = self.collectors[metric_name]()
                    collected_data[metric_name].append({
                        'timestamp': timestamp.isoformat(),
                        'value': value
                    })

            await asyncio.sleep(interval)

        # Calculate statistics
        statistics_data = {}
        for metric_name, data_points in collected_data.items():
            values = [point['value'] for point in data_points]
            if values:
                statistics_data[metric_name] = {
                    'min': min(values),
                    'max': max(values),
                    'avg': statistics.mean(values),
                    'median': statistics.median(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                    'count': len(values)
                }

        return {
            "metrics": dict(collected_data),
            "statistics": statistics_data,
            "duration": duration,
            "interval": interval,
            "collected_at": datetime.now().isoformat()
        }

    async def _get_metrics(self, metric_name: str = None,
                         time_range: int = 3600) -> Dict[str, Any]:
        """Get collected metrics data"""
        cutoff_time = datetime.now() - timedelta(seconds=time_range)

        if metric_name:
            # Get specific metric
            if metric_name not in self.metrics_data:
                return {"error": f"Metric '{metric_name}' not found"}

            # Filter by time range
            filtered_data = [
                point for point in self.metrics_data[metric_name]
                if datetime.fromisoformat(point['timestamp']) >= cutoff_time
            ]

            return {
                "metric": metric_name,
                "data": filtered_data,
                "count": len(filtered_data),
                "time_range": time_range
            }
        else:
            # Get all metrics
            all_metrics = {}
            for name, data in self.metrics_data.items():
                filtered_data = [
                    point for point in data
                    if datetime.fromisoformat(point['timestamp']) >= cutoff_time
                ]
                all_metrics[name] = {
                    "data": filtered_data,
                    "count": len(filtered_data)
                }

            return {
                "metrics": all_metrics,
                "time_range": time_range,
                "retrieved_at": datetime.now().isoformat()
            }

    async def _add_custom_metric(self, name: str, value: float,
                               tags: Dict[str, str] = None) -> Dict[str, Any]:
        """Add custom metric data point"""
        timestamp = datetime.now()

        metric_data = {
            'timestamp': timestamp.isoformat(),
            'value': value,
            'tags': tags or {}
        }

        self.metrics_data[name].append(metric_data)

        # Limit data points
        if len(self.metrics_data[name]) > self.max_data_points:
            self.metrics_data[name].popleft()

        # Add to custom metrics category
        if name not in self.metric_categories['custom']:
            self.metric_categories['custom'].append(name)

        # Check thresholds
        self._check_threshold(name, value, timestamp)

        return {
            "metric": name,
            "value": value,
            "tags": tags,
            "recorded_at": timestamp.isoformat()
        }

    async def _set_threshold(self, metric_name: str, threshold_type: str,
                           value: float, action: str = "alert") -> Dict[str, Any]:
        """Set threshold for metric monitoring"""
        if metric_name not in self.thresholds:
            self.thresholds[metric_name] = {}

        self.thresholds[metric_name][threshold_type] = {
            'value': value,
            'action': action,
            'created_at': datetime.now().isoformat()
        }

        return {
            "metric": metric_name,
            "threshold_type": threshold_type,
            "value": value,
            "action": action,
            "set_at": datetime.now().isoformat()
        }

    def _check_threshold(self, metric_name: str, value: float, timestamp: datetime):
        """Check if metric value exceeds thresholds"""
        if metric_name not in self.thresholds:
            return

        for threshold_type, threshold_data in self.thresholds[metric_name].items():
            threshold_value = threshold_data['value']
            action = threshold_data['action']

            triggered = False

            if threshold_type == 'max' and value > threshold_value:
                triggered = True
            elif threshold_type == 'min' and value < threshold_value:
                triggered = True
            elif threshold_type == 'exact' and abs(value - threshold_value) < 0.001:
                triggered = True

            if triggered:
                alert = {
                    'metric': metric_name,
                    'threshold_type': threshold_type,
                    'threshold_value': threshold_value,
                    'actual_value': value,
                    'action': action,
                    'timestamp': timestamp.isoformat(),
                    'alert_id': f"{metric_name}_{threshold_type}_{int(time.time())}"
                }

                self.alerts.append(alert)

                # Limit alerts
                if len(self.alerts) > 1000:
                    self.alerts = self.alerts[-1000:]

    async def _check_alerts(self, time_range: int = 3600) -> Dict[str, Any]:
        """Check recent alerts"""
        cutoff_time = datetime.now() - timedelta(seconds=time_range)

        recent_alerts = [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert['timestamp']) >= cutoff_time
        ]

        # Group alerts by metric
        alerts_by_metric = defaultdict(list)
        for alert in recent_alerts:
            alerts_by_metric[alert['metric']].append(alert)

        # Count by severity (assuming action indicates severity)
        severity_count = defaultdict(int)
        for alert in recent_alerts:
            severity_count[alert['action']] += 1

        return {
            "total_alerts": len(recent_alerts),
            "alerts": recent_alerts,
            "alerts_by_metric": dict(alerts_by_metric),
            "severity_breakdown": dict(severity_count),
            "time_range": time_range,
            "checked_at": datetime.now().isoformat()
        }

    async def _analyze_metrics(self, metric_name: str,
                             analysis_type: str = "trend") -> Dict[str, Any]:
        """Analyze metrics data"""
        if metric_name not in self.metrics_data:
            return {"error": f"Metric '{metric_name}' not found"}

        data_points = list(self.metrics_data[metric_name])
        if not data_points:
            return {"error": f"No data available for metric '{metric_name}'"}

        values = [point['value'] for point in data_points]
        timestamps = [datetime.fromisoformat(point['timestamp']) for point in data_points]

        analysis_result = {
            "metric": metric_name,
            "analysis_type": analysis_type,
            "data_points": len(values),
            "time_span": {
                "start": timestamps[0].isoformat() if timestamps else None,
                "end": timestamps[-1].isoformat() if timestamps else None
            },
            "analyzed_at": datetime.now().isoformat()
        }

        if analysis_type == "trend":
            # Simple trend analysis
            if len(values) >= 2:
                first_half = values[:len(values)//2]
                second_half = values[len(values)//2:]

                first_avg = statistics.mean(first_half)
                second_avg = statistics.mean(second_half)

                trend = "increasing" if second_avg > first_avg else "decreasing"
                if abs(second_avg - first_avg) < (first_avg * 0.05):  # Less than 5% change
                    trend = "stable"

                analysis_result["trend"] = {
                    "direction": trend,
                    "first_half_avg": first_avg,
                    "second_half_avg": second_avg,
                    "change_percent": ((second_avg - first_avg) / first_avg * 100) if first_avg != 0 else 0
                }

        elif analysis_type == "statistics":
            # Statistical analysis
            analysis_result["statistics"] = {
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "mode": statistics.mode(values) if len(set(values)) < len(values) else None,
                "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
                "variance": statistics.variance(values) if len(values) > 1 else 0
            }

            # Percentiles
            sorted_values = sorted(values)
            n = len(sorted_values)
            analysis_result["percentiles"] = {
                "p25": sorted_values[n//4],
                "p50": sorted_values[n//2],
                "p75": sorted_values[3*n//4],
                "p90": sorted_values[int(0.9*n)],
                "p95": sorted_values[int(0.95*n)],
                "p99": sorted_values[int(0.99*n)]
            }

        elif analysis_type == "anomaly":
            # Simple anomaly detection
            if len(values) > 10:
                mean_val = statistics.mean(values)
                std_val = statistics.stdev(values)
                threshold = 2 * std_val  # 2 standard deviations

                anomalies = []
                for i, (point, value) in enumerate(zip(data_points, values)):
                    if abs(value - mean_val) > threshold:
                        anomalies.append({
                            "index": i,
                            "timestamp": point['timestamp'],
                            "value": value,
                            "deviation": abs(value - mean_val),
                            "z_score": (value - mean_val) / std_val if std_val > 0 else 0
                        })

                analysis_result["anomaly_detection"] = {
                    "method": "z_score",
                    "threshold": threshold,
                    "anomalies": anomalies,
                    "anomaly_count": len(anomalies),
                    "anomaly_rate": len(anomalies) / len(values) * 100
                }

        return analysis_result

    async def _export_metrics(self, format: str = "json",
                            time_range: int = 3600) -> Dict[str, Any]:
        """Export metrics data"""
        metrics_data = await self._get_metrics(time_range=time_range)

        if format == "json":
            return {
                "format": "json",
                "data": metrics_data,
                "exported_at": datetime.now().isoformat()
            }

        elif format == "csv":
            # Convert to CSV format
            csv_lines = ["timestamp,metric,value"]

            for metric_name, metric_info in metrics_data["metrics"].items():
                for data_point in metric_info["data"]:
                    csv_lines.append(f"{data_point['timestamp']},{metric_name},{data_point['value']}")

            return {
                "format": "csv",
                "content": "\n".join(csv_lines),
                "exported_at": datetime.now().isoformat()
            }

        elif format == "prometheus":
            # Convert to Prometheus format
            prometheus_lines = []

            for metric_name, metric_info in metrics_data["metrics"].items():
                if metric_info["data"]:
                    latest_point = metric_info["data"][-1]
                    prometheus_lines.append(f"# HELP {metric_name} Collected metric")
                    prometheus_lines.append(f"# TYPE {metric_name} gauge")
                    prometheus_lines.append(f"{metric_name} {latest_point['value']}")

            return {
                "format": "prometheus",
                "content": "\n".join(prometheus_lines),
                "exported_at": datetime.now().isoformat()
            }

        else:
            return {"error": f"Unsupported export format: {format}"}

    async def _metrics_report(self, time_range: int = 3600,
                            include_analysis: bool = True) -> Dict[str, Any]:
        """Generate comprehensive metrics report"""
        report = {
            "time_range": time_range,
            "generated_at": datetime.now().isoformat(),
            "summary": {},
            "metrics": {},
            "alerts": {},
            "system_health": {}
        }

        # Get all metrics
        metrics_data = await self._get_metrics(time_range=time_range)
        report["metrics"] = metrics_data

        # Generate summary
        total_data_points = sum(
            metric_info["count"] for metric_info in metrics_data["metrics"].values()
        )
        report["summary"] = {
            "total_metrics": len(metrics_data["metrics"]),
            "total_data_points": total_data_points,
            "collection_status": "running" if self.is_collecting else "stopped",
            "time_range_hours": time_range / 3600
        }

        # Get alerts
        alerts_data = await self._check_alerts(time_range=time_range)
        report["alerts"] = alerts_data

        # System health summary
        health_data = await self._system_health()
        report["system_health"] = health_data

        # Analysis if requested
        if include_analysis:
            report["analysis"] = {}
            for metric_name in metrics_data["metrics"].keys():
                if metrics_data["metrics"][metric_name]["count"] > 0:
                    analysis = await self._analyze_metrics(metric_name, "statistics")
                    if "error" not in analysis:
                        report["analysis"][metric_name] = analysis

        return report

    async def _system_health(self) -> Dict[str, Any]:
        """Get current system health metrics"""
        health_data = {
            "timestamp": datetime.now().isoformat(),
            "status": "healthy",
            "metrics": {},
            "warnings": [],
            "critical_issues": []
        }

        try:
            # CPU
            cpu_percent = psutil.cpu_percent(interval=1)
            health_data["metrics"]["cpu_percent"] = cpu_percent
            if cpu_percent > 90:
                health_data["critical_issues"].append(f"High CPU usage: {cpu_percent}%")
                health_data["status"] = "critical"
            elif cpu_percent > 75:
                health_data["warnings"].append(f"Elevated CPU usage: {cpu_percent}%")
                if health_data["status"] == "healthy":
                    health_data["status"] = "warning"

            # Memory
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            health_data["metrics"]["memory_percent"] = memory_percent
            health_data["metrics"]["memory_available_gb"] = memory.available / (1024**3)

            if memory_percent > 95:
                health_data["critical_issues"].append(f"Critical memory usage: {memory_percent}%")
                health_data["status"] = "critical"
            elif memory_percent > 85:
                health_data["warnings"].append(f"High memory usage: {memory_percent}%")
                if health_data["status"] == "healthy":
                    health_data["status"] = "warning"

            # Disk
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            health_data["metrics"]["disk_percent"] = disk_percent
            health_data["metrics"]["disk_free_gb"] = disk.free / (1024**3)

            if disk_percent > 95:
                health_data["critical_issues"].append(f"Critical disk usage: {disk_percent:.1f}%")
                health_data["status"] = "critical"
            elif disk_percent > 85:
                health_data["warnings"].append(f"High disk usage: {disk_percent:.1f}%")
                if health_data["status"] == "healthy":
                    health_data["status"] = "warning"

            # Load average (Unix systems)
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                health_data["metrics"]["load_average"] = {
                    "1min": load_avg[0],
                    "5min": load_avg[1],
                    "15min": load_avg[2]
                }

                cpu_count = psutil.cpu_count()
                if load_avg[0] > cpu_count * 2:
                    health_data["warnings"].append(f"High load average: {load_avg[0]:.2f}")
                    if health_data["status"] == "healthy":
                        health_data["status"] = "warning"

            # Network
            network = psutil.net_io_counters()
            health_data["metrics"]["network"] = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }

            # Process count
            process_count = len(psutil.pids())
            health_data["metrics"]["process_count"] = process_count

            if process_count > 1000:
                health_data["warnings"].append(f"High process count: {process_count}")
                if health_data["status"] == "healthy":
                    health_data["status"] = "warning"

        except Exception as e:
            health_data["error"] = str(e)
            health_data["status"] = "error"

        return health_data

    # Built-in metric collectors
    def _collect_cpu_percent(self) -> float:
        """Collect CPU usage percentage"""
        return psutil.cpu_percent(interval=0.1)

    def _collect_memory_percent(self) -> float:
        """Collect memory usage percentage"""
        return psutil.virtual_memory().percent

    def _collect_disk_usage(self) -> float:
        """Collect disk usage percentage"""
        disk = psutil.disk_usage('/')
        return (disk.used / disk.total) * 100

    def _collect_network_io(self) -> Dict[str, int]:
        """Collect network I/O statistics"""
        network = psutil.net_io_counters()
        return {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv
        }

    def _collect_process_cpu(self, pid: int = None) -> float:
        """Collect process CPU usage"""
        if pid is None:
            pid = os.getpid()
        try:
            process = psutil.Process(pid)
            return process.cpu_percent()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def _collect_process_memory(self, pid: int = None) -> float:
        """Collect process memory usage"""
        if pid is None:
            pid = os.getpid()
        try:
            process = psutil.Process(pid)
            return process.memory_percent()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return 0.0

    def _collect_load_average(self) -> Dict[str, float]:
        """Collect system load average"""
        if hasattr(os, 'getloadavg'):
            load_avg = os.getloadavg()
            return {
                '1min': load_avg[0],
                '5min': load_avg[1],
                '15min': load_avg[2]
            }
        return {'1min': 0.0, '5min': 0.0, '15min': 0.0}

    def _collect_disk_io(self) -> Dict[str, int]:
        """Collect disk I/O statistics"""
        disk_io = psutil.disk_io_counters()
        if disk_io:
            return {
                'read_bytes': disk_io.read_bytes,
                'write_bytes': disk_io.write_bytes,
                'read_count': disk_io.read_count,
                'write_count': disk_io.write_count
            }
        return {'read_bytes': 0, 'write_bytes': 0, 'read_count': 0, 'write_count': 0}
