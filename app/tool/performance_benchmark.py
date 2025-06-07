"""
Performance Benchmark Tool

This tool provides comprehensive performance benchmarking capabilities including:
- CPU performance testing
- Memory usage analysis
- Disk I/O benchmarking
- Network performance testing
- Application benchmarking
- System resource monitoring
- Performance comparison and reporting
"""

import asyncio
import time
import psutil
import platform
import subprocess
import json
import os
import tempfile
import threading
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import concurrent.futures
from .base import BaseTool


class PerformanceBenchmark(BaseTool):
    """Tool for performance benchmarking and system analysis"""

    def __init__(self):
        super().__init__()
        self.name = "performance_benchmark"
        self.description = "Comprehensive performance benchmarking and system analysis tool"

        # Benchmark results storage
        self.benchmark_results = {}
        self.baseline_results = {}

        # Performance monitoring
        self.monitoring_active = False
        self.monitoring_data = []

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute performance benchmark commands"""
        try:
            if command == "cpu_benchmark":
                return await self._cpu_benchmark(**kwargs)
            elif command == "memory_benchmark":
                return await self._memory_benchmark(**kwargs)
            elif command == "disk_benchmark":
                return await self._disk_benchmark(**kwargs)
            elif command == "network_benchmark":
                return await self._network_benchmark(**kwargs)
            elif command == "system_info":
                return await self._get_system_info(**kwargs)
            elif command == "monitor_performance":
                return await self._monitor_performance(**kwargs)
            elif command == "stress_test":
                return await self._stress_test(**kwargs)
            elif command == "compare_results":
                return await self._compare_results(**kwargs)
            elif command == "generate_report":
                return await self._generate_report(**kwargs)
            elif command == "save_baseline":
                return await self._save_baseline(**kwargs)
            elif command == "load_baseline":
                return await self._load_baseline(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Performance benchmark error: {str(e)}"}

    async def _cpu_benchmark(self, duration: int = 10, threads: Optional[int] = None) -> Dict[str, Any]:
        """Run CPU performance benchmark"""
        if threads is None:
            threads = psutil.cpu_count()

        def cpu_intensive_task(duration: float) -> float:
            """CPU intensive calculation"""
            start_time = time.time()
            end_time = start_time + duration
            operations = 0

            while time.time() < end_time:
                # Perform CPU intensive operations
                for i in range(1000):
                    _ = i ** 2 * 3.14159
                operations += 1000

            return operations

        # Monitor CPU usage during benchmark
        cpu_usage_before = psutil.cpu_percent(interval=1)
        start_time = time.time()

        # Run CPU benchmark with multiple threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
            futures = [
                executor.submit(cpu_intensive_task, duration / threads)
                for _ in range(threads)
            ]

            total_operations = sum(future.result() for future in futures)

        end_time = time.time()
        actual_duration = end_time - start_time
        cpu_usage_after = psutil.cpu_percent(interval=1)

        # Calculate performance metrics
        operations_per_second = total_operations / actual_duration
        cpu_efficiency = (cpu_usage_after - cpu_usage_before) / 100.0

        result = {
            "benchmark_type": "CPU",
            "duration": actual_duration,
            "threads_used": threads,
            "total_operations": total_operations,
            "operations_per_second": operations_per_second,
            "cpu_usage_before": cpu_usage_before,
            "cpu_usage_after": cpu_usage_after,
            "cpu_efficiency": cpu_efficiency,
            "timestamp": datetime.now().isoformat()
        }

        self.benchmark_results["cpu"] = result
        return result

    async def _memory_benchmark(self, size_mb: int = 100, iterations: int = 10) -> Dict[str, Any]:
        """Run memory performance benchmark"""
        memory_info_before = psutil.virtual_memory()

        allocation_times = []
        access_times = []
        deallocation_times = []

        for i in range(iterations):
            # Memory allocation test
            start_time = time.time()
            data = bytearray(size_mb * 1024 * 1024)  # Allocate memory
            allocation_time = time.time() - start_time
            allocation_times.append(allocation_time)

            # Memory access test
            start_time = time.time()
            for j in range(0, len(data), 4096):  # Access every 4KB
                data[j] = j % 256
            access_time = time.time() - start_time
            access_times.append(access_time)

            # Memory deallocation test
            start_time = time.time()
            del data
            deallocation_time = time.time() - start_time
            deallocation_times.append(deallocation_time)

        memory_info_after = psutil.virtual_memory()

        result = {
            "benchmark_type": "Memory",
            "size_mb": size_mb,
            "iterations": iterations,
            "allocation_time_avg": statistics.mean(allocation_times),
            "allocation_time_std": statistics.stdev(allocation_times) if len(allocation_times) > 1 else 0,
            "access_time_avg": statistics.mean(access_times),
            "access_time_std": statistics.stdev(access_times) if len(access_times) > 1 else 0,
            "deallocation_time_avg": statistics.mean(deallocation_times),
            "deallocation_time_std": statistics.stdev(deallocation_times) if len(deallocation_times) > 1 else 0,
            "memory_before_mb": memory_info_before.used / (1024 * 1024),
            "memory_after_mb": memory_info_after.used / (1024 * 1024),
            "memory_available_mb": memory_info_after.available / (1024 * 1024),
            "timestamp": datetime.now().isoformat()
        }

        self.benchmark_results["memory"] = result
        return result

    async def _disk_benchmark(self, file_size_mb: int = 100, test_dir: Optional[str] = None) -> Dict[str, Any]:
        """Run disk I/O performance benchmark"""
        if test_dir is None:
            test_dir = tempfile.gettempdir()

        test_file = os.path.join(test_dir, f"benchmark_test_{int(time.time())}.tmp")
        data = os.urandom(file_size_mb * 1024 * 1024)

        try:
            # Write test
            start_time = time.time()
            with open(test_file, 'wb') as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            write_time = time.time() - start_time

            # Read test
            start_time = time.time()
            with open(test_file, 'rb') as f:
                read_data = f.read()
            read_time = time.time() - start_time

            # Random access test
            start_time = time.time()
            with open(test_file, 'rb') as f:
                for _ in range(100):
                    position = os.urandom(1)[0] % (file_size_mb * 1024 * 1024 - 1024)
                    f.seek(position)
                    f.read(1024)
            random_access_time = time.time() - start_time

            # Calculate performance metrics
            write_speed_mbps = file_size_mb / write_time
            read_speed_mbps = file_size_mb / read_time

            # Get disk usage info
            disk_usage = psutil.disk_usage(test_dir)

            result = {
                "benchmark_type": "Disk I/O",
                "file_size_mb": file_size_mb,
                "test_directory": test_dir,
                "write_time": write_time,
                "read_time": read_time,
                "random_access_time": random_access_time,
                "write_speed_mbps": write_speed_mbps,
                "read_speed_mbps": read_speed_mbps,
                "disk_total_gb": disk_usage.total / (1024**3),
                "disk_used_gb": disk_usage.used / (1024**3),
                "disk_free_gb": disk_usage.free / (1024**3),
                "timestamp": datetime.now().isoformat()
            }

        finally:
            # Clean up test file
            if os.path.exists(test_file):
                os.remove(test_file)

        self.benchmark_results["disk"] = result
        return result

    async def _network_benchmark(self, host: str = "8.8.8.8", port: int = 53, packets: int = 10) -> Dict[str, Any]:
        """Run network performance benchmark"""
        import socket

        # Ping test
        ping_times = []
        for _ in range(packets):
            start_time = time.time()
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    ping_time = (time.time() - start_time) * 1000  # Convert to ms
                    ping_times.append(ping_time)
            except Exception:
                pass

        # DNS resolution test
        dns_times = []
        for _ in range(5):
            start_time = time.time()
            try:
                socket.gethostbyname(host)
                dns_time = (time.time() - start_time) * 1000
                dns_times.append(dns_time)
            except Exception:
                pass

        # Network interface statistics
        net_io = psutil.net_io_counters()

        result = {
            "benchmark_type": "Network",
            "target_host": host,
            "target_port": port,
            "packets_sent": packets,
            "packets_received": len(ping_times),
            "packet_loss_percent": ((packets - len(ping_times)) / packets) * 100,
            "ping_time_avg_ms": statistics.mean(ping_times) if ping_times else 0,
            "ping_time_min_ms": min(ping_times) if ping_times else 0,
            "ping_time_max_ms": max(ping_times) if ping_times else 0,
            "ping_time_std_ms": statistics.stdev(ping_times) if len(ping_times) > 1 else 0,
            "dns_resolution_avg_ms": statistics.mean(dns_times) if dns_times else 0,
            "bytes_sent": net_io.bytes_sent,
            "bytes_received": net_io.bytes_recv,
            "packets_sent_total": net_io.packets_sent,
            "packets_received_total": net_io.packets_recv,
            "timestamp": datetime.now().isoformat()
        }

        self.benchmark_results["network"] = result
        return result

    async def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        # CPU information
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "max_frequency": psutil.cpu_freq().max if psutil.cpu_freq() else None,
            "current_frequency": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        }

        # Memory information
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        memory_info = {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "usage_percent": memory.percent,
            "swap_total_gb": swap.total / (1024**3),
            "swap_used_gb": swap.used / (1024**3),
            "swap_usage_percent": swap.percent
        }

        # Disk information
        disk_info = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "filesystem": partition.fstype,
                    "total_gb": usage.total / (1024**3),
                    "used_gb": usage.used / (1024**3),
                    "free_gb": usage.free / (1024**3),
                    "usage_percent": (usage.used / usage.total) * 100
                })
            except PermissionError:
                continue

        # Network information
        network_info = []
        for interface, addresses in psutil.net_if_addrs().items():
            interface_info = {"interface": interface, "addresses": []}
            for addr in addresses:
                interface_info["addresses"].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
            network_info.append(interface_info)

        # System information
        system_info = {
            "platform": platform.platform(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            "uptime_hours": (time.time() - psutil.boot_time()) / 3600
        }

        return {
            "system": system_info,
            "cpu": cpu_info,
            "memory": memory_info,
            "disk": disk_info,
            "network": network_info,
            "timestamp": datetime.now().isoformat()
        }

    async def _monitor_performance(self, duration: int = 60, interval: int = 1) -> Dict[str, Any]:
        """Monitor system performance over time"""
        self.monitoring_active = True
        self.monitoring_data = []

        start_time = time.time()
        end_time = start_time + duration

        while time.time() < end_time and self.monitoring_active:
            timestamp = datetime.now().isoformat()

            # Collect performance data
            data_point = {
                "timestamp": timestamp,
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {},
                "network_io": psutil.net_io_counters()._asdict(),
                "processes": len(psutil.pids()),
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }

            self.monitoring_data.append(data_point)
            await asyncio.sleep(interval)

        self.monitoring_active = False

        # Calculate statistics
        if self.monitoring_data:
            cpu_values = [d["cpu_percent"] for d in self.monitoring_data]
            memory_values = [d["memory_percent"] for d in self.monitoring_data]

            stats = {
                "duration": duration,
                "data_points": len(self.monitoring_data),
                "cpu_avg": statistics.mean(cpu_values),
                "cpu_max": max(cpu_values),
                "cpu_min": min(cpu_values),
                "cpu_std": statistics.stdev(cpu_values) if len(cpu_values) > 1 else 0,
                "memory_avg": statistics.mean(memory_values),
                "memory_max": max(memory_values),
                "memory_min": min(memory_values),
                "memory_std": statistics.stdev(memory_values) if len(memory_values) > 1 else 0,
                "raw_data": self.monitoring_data
            }
        else:
            stats = {"error": "No monitoring data collected"}

        return stats

    async def _stress_test(self, test_type: str = "cpu", duration: int = 30, intensity: int = 80) -> Dict[str, Any]:
        """Run system stress test"""
        if test_type == "cpu":
            return await self._cpu_stress_test(duration, intensity)
        elif test_type == "memory":
            return await self._memory_stress_test(duration, intensity)
        elif test_type == "disk":
            return await self._disk_stress_test(duration, intensity)
        else:
            return {"error": f"Unknown stress test type: {test_type}"}

    async def _cpu_stress_test(self, duration: int, intensity: int) -> Dict[str, Any]:
        """CPU stress test"""
        num_threads = max(1, int(psutil.cpu_count() * intensity / 100))

        def stress_cpu(duration: float):
            end_time = time.time() + duration
            while time.time() < end_time:
                # CPU intensive operations
                for i in range(10000):
                    _ = i ** 2 * 3.14159

        # Monitor performance during stress test
        start_time = time.time()
        cpu_before = psutil.cpu_percent(interval=1)

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(stress_cpu, duration) for _ in range(num_threads)]

            # Monitor during execution
            max_cpu = 0
            while any(not f.done() for f in futures):
                current_cpu = psutil.cpu_percent()
                max_cpu = max(max_cpu, current_cpu)
                await asyncio.sleep(1)

        cpu_after = psutil.cpu_percent(interval=1)
        actual_duration = time.time() - start_time

        return {
            "test_type": "CPU Stress Test",
            "duration": actual_duration,
            "threads_used": num_threads,
            "intensity_percent": intensity,
            "cpu_before": cpu_before,
            "cpu_after": cpu_after,
            "max_cpu_during_test": max_cpu,
            "timestamp": datetime.now().isoformat()
        }

    async def _memory_stress_test(self, duration: int, intensity: int) -> Dict[str, Any]:
        """Memory stress test"""
        available_memory = psutil.virtual_memory().available
        target_memory = int(available_memory * intensity / 100)
        chunk_size = 10 * 1024 * 1024  # 10MB chunks

        memory_chunks = []
        start_time = time.time()
        end_time = start_time + duration

        try:
            # Allocate memory
            while len(memory_chunks) * chunk_size < target_memory:
                memory_chunks.append(bytearray(chunk_size))

                # Write to memory to ensure allocation
                for i in range(0, chunk_size, 4096):
                    memory_chunks[-1][i] = i % 256

            # Hold memory for remaining duration
            while time.time() < end_time:
                # Access random memory locations
                if memory_chunks:
                    chunk_idx = len(memory_chunks) // 2
                    for i in range(0, len(memory_chunks[chunk_idx]), 8192):
                        memory_chunks[chunk_idx][i] = (memory_chunks[chunk_idx][i] + 1) % 256
                await asyncio.sleep(1)

        except MemoryError:
            pass

        allocated_mb = len(memory_chunks) * chunk_size / (1024 * 1024)
        actual_duration = time.time() - start_time

        # Clean up
        del memory_chunks

        return {
            "test_type": "Memory Stress Test",
            "duration": actual_duration,
            "target_memory_mb": target_memory / (1024 * 1024),
            "allocated_memory_mb": allocated_mb,
            "intensity_percent": intensity,
            "timestamp": datetime.now().isoformat()
        }

    async def _disk_stress_test(self, duration: int, intensity: int) -> Dict[str, Any]:
        """Disk I/O stress test"""
        test_dir = tempfile.gettempdir()
        file_size = max(1, intensity) * 1024 * 1024  # MB based on intensity

        start_time = time.time()
        end_time = start_time + duration
        operations = 0

        try:
            while time.time() < end_time:
                test_file = os.path.join(test_dir, f"stress_test_{operations}.tmp")

                # Write operation
                data = os.urandom(file_size)
                with open(test_file, 'wb') as f:
                    f.write(data)
                    f.flush()
                    os.fsync(f.fileno())

                # Read operation
                with open(test_file, 'rb') as f:
                    _ = f.read()

                # Clean up
                os.remove(test_file)
                operations += 1

                # Brief pause to prevent system overload
                await asyncio.sleep(0.1)

        except Exception as e:
            pass

        actual_duration = time.time() - start_time

        return {
            "test_type": "Disk I/O Stress Test",
            "duration": actual_duration,
            "file_size_mb": file_size / (1024 * 1024),
            "operations_completed": operations,
            "operations_per_second": operations / actual_duration if actual_duration > 0 else 0,
            "intensity_percent": intensity,
            "timestamp": datetime.now().isoformat()
        }

    async def _compare_results(self, baseline_name: str = "baseline") -> Dict[str, Any]:
        """Compare current benchmark results with baseline"""
        if baseline_name not in self.baseline_results:
            return {"error": f"Baseline '{baseline_name}' not found"}

        baseline = self.baseline_results[baseline_name]
        current = self.benchmark_results

        comparison = {}

        for test_type in ["cpu", "memory", "disk", "network"]:
            if test_type in baseline and test_type in current:
                baseline_data = baseline[test_type]
                current_data = current[test_type]

                if test_type == "cpu":
                    ops_improvement = ((current_data["operations_per_second"] - baseline_data["operations_per_second"])
                                     / baseline_data["operations_per_second"]) * 100
                    comparison[test_type] = {
                        "operations_per_second_improvement_percent": ops_improvement,
                        "baseline_ops": baseline_data["operations_per_second"],
                        "current_ops": current_data["operations_per_second"]
                    }

                elif test_type == "memory":
                    alloc_improvement = ((baseline_data["allocation_time_avg"] - current_data["allocation_time_avg"])
                                       / baseline_data["allocation_time_avg"]) * 100
                    comparison[test_type] = {
                        "allocation_time_improvement_percent": alloc_improvement,
                        "baseline_alloc_time": baseline_data["allocation_time_avg"],
                        "current_alloc_time": current_data["allocation_time_avg"]
                    }

                elif test_type == "disk":
                    write_improvement = ((current_data["write_speed_mbps"] - baseline_data["write_speed_mbps"])
                                       / baseline_data["write_speed_mbps"]) * 100
                    read_improvement = ((current_data["read_speed_mbps"] - baseline_data["read_speed_mbps"])
                                      / baseline_data["read_speed_mbps"]) * 100
                    comparison[test_type] = {
                        "write_speed_improvement_percent": write_improvement,
                        "read_speed_improvement_percent": read_improvement,
                        "baseline_write_speed": baseline_data["write_speed_mbps"],
                        "current_write_speed": current_data["write_speed_mbps"],
                        "baseline_read_speed": baseline_data["read_speed_mbps"],
                        "current_read_speed": current_data["read_speed_mbps"]
                    }

                elif test_type == "network":
                    ping_improvement = ((baseline_data["ping_time_avg_ms"] - current_data["ping_time_avg_ms"])
                                      / baseline_data["ping_time_avg_ms"]) * 100
                    comparison[test_type] = {
                        "ping_time_improvement_percent": ping_improvement,
                        "baseline_ping_ms": baseline_data["ping_time_avg_ms"],
                        "current_ping_ms": current_data["ping_time_avg_ms"]
                    }

        return {
            "baseline_name": baseline_name,
            "comparison_timestamp": datetime.now().isoformat(),
            "comparisons": comparison
        }

    async def _generate_report(self, include_raw_data: bool = False) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            "report_timestamp": datetime.now().isoformat(),
            "system_info": await self._get_system_info(),
            "benchmark_results": self.benchmark_results.copy(),
            "summary": {}
        }

        # Generate summary
        if "cpu" in self.benchmark_results:
            cpu_data = self.benchmark_results["cpu"]
            report["summary"]["cpu"] = {
                "operations_per_second": cpu_data["operations_per_second"],
                "efficiency": cpu_data["cpu_efficiency"],
                "performance_rating": self._rate_performance("cpu", cpu_data["operations_per_second"])
            }

        if "memory" in self.benchmark_results:
            memory_data = self.benchmark_results["memory"]
            report["summary"]["memory"] = {
                "allocation_speed": 1 / memory_data["allocation_time_avg"],
                "access_speed": 1 / memory_data["access_time_avg"],
                "performance_rating": self._rate_performance("memory", memory_data["allocation_time_avg"])
            }

        if "disk" in self.benchmark_results:
            disk_data = self.benchmark_results["disk"]
            report["summary"]["disk"] = {
                "write_speed_mbps": disk_data["write_speed_mbps"],
                "read_speed_mbps": disk_data["read_speed_mbps"],
                "performance_rating": self._rate_performance("disk", disk_data["write_speed_mbps"])
            }

        if "network" in self.benchmark_results:
            network_data = self.benchmark_results["network"]
            report["summary"]["network"] = {
                "avg_ping_ms": network_data["ping_time_avg_ms"],
                "packet_loss_percent": network_data["packet_loss_percent"],
                "performance_rating": self._rate_performance("network", network_data["ping_time_avg_ms"])
            }

        if not include_raw_data:
            # Remove raw monitoring data to reduce size
            if "monitoring_data" in report["benchmark_results"]:
                del report["benchmark_results"]["monitoring_data"]["raw_data"]

        return report

    def _rate_performance(self, test_type: str, value: float) -> str:
        """Rate performance based on test type and value"""
        if test_type == "cpu":
            if value > 1000000:
                return "Excellent"
            elif value > 500000:
                return "Good"
            elif value > 100000:
                return "Average"
            else:
                return "Poor"

        elif test_type == "memory":
            if value < 0.001:
                return "Excellent"
            elif value < 0.01:
                return "Good"
            elif value < 0.1:
                return "Average"
            else:
                return "Poor"

        elif test_type == "disk":
            if value > 100:
                return "Excellent"
            elif value > 50:
                return "Good"
            elif value > 10:
                return "Average"
            else:
                return "Poor"

        elif test_type == "network":
            if value < 10:
                return "Excellent"
            elif value < 50:
                return "Good"
            elif value < 100:
                return "Average"
            else:
                return "Poor"

        return "Unknown"

    async def _save_baseline(self, name: str = "baseline") -> Dict[str, Any]:
        """Save current benchmark results as baseline"""
        if not self.benchmark_results:
            return {"error": "No benchmark results to save as baseline"}

        self.baseline_results[name] = self.benchmark_results.copy()

        return {
            "message": f"Baseline '{name}' saved successfully",
            "saved_tests": list(self.benchmark_results.keys()),
            "timestamp": datetime.now().isoformat()
        }

    async def _load_baseline(self, name: str = "baseline") -> Dict[str, Any]:
        """Load baseline results"""
        if name not in self.baseline_results:
            return {"error": f"Baseline '{name}' not found"}

        return {
            "baseline_name": name,
            "baseline_data": self.baseline_results[name],
            "available_tests": list(self.baseline_results[name].keys())
        }
