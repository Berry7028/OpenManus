"""
System Monitor Tool for monitoring system resources and performance.
"""

import psutil
import platform
import time
from datetime import datetime
from typing import Optional, Dict, List
import json

from app.tool.base import BaseTool, ToolResult


class SystemMonitor(BaseTool):
    """Tool for monitoring system resources and performance."""

    name: str = "system_monitor"
    description: str = """Monitor system resources and performance.

    Available commands:
    - cpu: Get CPU usage and information
    - memory: Get memory usage and information
    - disk: Get disk usage and information
    - network: Get network statistics
    - processes: List running processes
    - system_info: Get system information
    - monitor: Continuous monitoring for specified duration
    - top_processes: Get top processes by CPU/memory usage
    """

    parameters: dict = {
        "type": "object",
        "properties": {
            "command": {
                "description": "The command to execute.",
                "enum": ["cpu", "memory", "disk", "network", "processes", "system_info", "monitor", "top_processes"],
                "type": "string",
            },
            "duration": {
                "description": "Duration for monitoring in seconds (default: 10).",
                "type": "integer",
            },
            "interval": {
                "description": "Interval between measurements in seconds (default: 1).",
                "type": "integer",
            },
            "sort_by": {
                "description": "Sort processes by (cpu, memory, name, pid).",
                "type": "string",
            },
            "limit": {
                "description": "Limit number of processes to show (default: 10).",
                "type": "integer",
            },
            "disk_path": {
                "description": "Disk path to check (default: /).",
                "type": "string",
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    async def execute(
        self,
        command: str,
        duration: int = 10,
        interval: int = 1,
        sort_by: str = "cpu",
        limit: int = 10,
        disk_path: str = "/",
        **kwargs
    ) -> ToolResult:
        """Execute system monitor command."""
        try:
            if command == "cpu":
                return self._get_cpu_info()
            elif command == "memory":
                return self._get_memory_info()
            elif command == "disk":
                return self._get_disk_info(disk_path)
            elif command == "network":
                return self._get_network_info()
            elif command == "processes":
                return self._get_processes(sort_by, limit)
            elif command == "system_info":
                return self._get_system_info()
            elif command == "monitor":
                return self._monitor_system(duration, interval)
            elif command == "top_processes":
                return self._get_top_processes(sort_by, limit)
            else:
                return ToolResult(error=f"Unknown command: {command}")
        except Exception as e:
            return ToolResult(error=f"Error executing system monitor command '{command}': {str(e)}")

    def _get_cpu_info(self) -> ToolResult:
        """Get CPU usage and information."""
        try:
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_count_logical = psutil.cpu_count(logical=True)

            # Get per-core usage
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)

            # Get CPU frequency
            cpu_freq = psutil.cpu_freq()

            # Get load average (Unix only)
            try:
                load_avg = psutil.getloadavg()
            except AttributeError:
                load_avg = None

            output = "CPU Information:\n"
            output += "=" * 30 + "\n"
            output += f"Overall CPU Usage: {cpu_percent}%\n"
            output += f"Physical Cores: {cpu_count}\n"
            output += f"Logical Cores: {cpu_count_logical}\n"

            if cpu_freq:
                output += f"Current Frequency: {cpu_freq.current:.2f} MHz\n"
                output += f"Min Frequency: {cpu_freq.min:.2f} MHz\n"
                output += f"Max Frequency: {cpu_freq.max:.2f} MHz\n"

            if load_avg:
                output += f"Load Average: {load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}\n"

            output += "\nPer-Core Usage:\n"
            for i, usage in enumerate(cpu_per_core):
                output += f"  Core {i}: {usage}%\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error getting CPU info: {str(e)}")

    def _get_memory_info(self) -> ToolResult:
        """Get memory usage and information."""
        try:
            # Virtual memory
            virtual_mem = psutil.virtual_memory()

            # Swap memory
            swap_mem = psutil.swap_memory()

            def bytes_to_gb(bytes_val):
                return bytes_val / (1024**3)

            output = "Memory Information:\n"
            output += "=" * 30 + "\n"

            output += "Virtual Memory:\n"
            output += f"  Total: {bytes_to_gb(virtual_mem.total):.2f} GB\n"
            output += f"  Available: {bytes_to_gb(virtual_mem.available):.2f} GB\n"
            output += f"  Used: {bytes_to_gb(virtual_mem.used):.2f} GB\n"
            output += f"  Free: {bytes_to_gb(virtual_mem.free):.2f} GB\n"
            output += f"  Percentage: {virtual_mem.percent}%\n"

            output += "\nSwap Memory:\n"
            output += f"  Total: {bytes_to_gb(swap_mem.total):.2f} GB\n"
            output += f"  Used: {bytes_to_gb(swap_mem.used):.2f} GB\n"
            output += f"  Free: {bytes_to_gb(swap_mem.free):.2f} GB\n"
            output += f"  Percentage: {swap_mem.percent}%\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error getting memory info: {str(e)}")

    def _get_disk_info(self, disk_path: str) -> ToolResult:
        """Get disk usage and information."""
        try:
            # Disk usage for specified path
            disk_usage = psutil.disk_usage(disk_path)

            # All disk partitions
            partitions = psutil.disk_partitions()

            def bytes_to_gb(bytes_val):
                return bytes_val / (1024**3)

            output = f"Disk Information for {disk_path}:\n"
            output += "=" * 40 + "\n"
            output += f"Total: {bytes_to_gb(disk_usage.total):.2f} GB\n"
            output += f"Used: {bytes_to_gb(disk_usage.used):.2f} GB\n"
            output += f"Free: {bytes_to_gb(disk_usage.free):.2f} GB\n"
            output += f"Percentage: {(disk_usage.used / disk_usage.total) * 100:.1f}%\n"

            output += "\nAll Partitions:\n"
            for partition in partitions:
                output += f"  Device: {partition.device}\n"
                output += f"  Mountpoint: {partition.mountpoint}\n"
                output += f"  File system: {partition.fstype}\n"

                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    output += f"  Total: {bytes_to_gb(partition_usage.total):.2f} GB\n"
                    output += f"  Used: {bytes_to_gb(partition_usage.used):.2f} GB\n"
                    output += f"  Free: {bytes_to_gb(partition_usage.free):.2f} GB\n"
                    output += f"  Percentage: {(partition_usage.used / partition_usage.total) * 100:.1f}%\n"
                except PermissionError:
                    output += "  Permission denied\n"
                output += "\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error getting disk info: {str(e)}")

    def _get_network_info(self) -> ToolResult:
        """Get network statistics."""
        try:
            # Network I/O statistics
            net_io = psutil.net_io_counters()

            # Network interfaces
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()

            def bytes_to_mb(bytes_val):
                return bytes_val / (1024**2)

            output = "Network Information:\n"
            output += "=" * 30 + "\n"

            output += "Overall Network I/O:\n"
            output += f"  Bytes Sent: {bytes_to_mb(net_io.bytes_sent):.2f} MB\n"
            output += f"  Bytes Received: {bytes_to_mb(net_io.bytes_recv):.2f} MB\n"
            output += f"  Packets Sent: {net_io.packets_sent:,}\n"
            output += f"  Packets Received: {net_io.packets_recv:,}\n"
            output += f"  Errors In: {net_io.errin}\n"
            output += f"  Errors Out: {net_io.errout}\n"
            output += f"  Drops In: {net_io.dropin}\n"
            output += f"  Drops Out: {net_io.dropout}\n"

            output += "\nNetwork Interfaces:\n"
            for interface_name, interface_addresses in net_if_addrs.items():
                output += f"  Interface: {interface_name}\n"

                # Interface statistics
                if interface_name in net_if_stats:
                    stats = net_if_stats[interface_name]
                    output += f"    Status: {'Up' if stats.isup else 'Down'}\n"
                    output += f"    Speed: {stats.speed} Mbps\n"
                    output += f"    MTU: {stats.mtu}\n"

                # Interface addresses
                for addr in interface_addresses:
                    if addr.family.name == 'AF_INET':
                        output += f"    IPv4: {addr.address}\n"
                        output += f"    Netmask: {addr.netmask}\n"
                    elif addr.family.name == 'AF_INET6':
                        output += f"    IPv6: {addr.address}\n"
                    elif addr.family.name == 'AF_PACKET':
                        output += f"    MAC: {addr.address}\n"
                output += "\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error getting network info: {str(e)}")

    def _get_processes(self, sort_by: str, limit: int) -> ToolResult:
        """List running processes."""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
            elif sort_by == "name":
                processes.sort(key=lambda x: x['name'] or '')
            elif sort_by == "pid":
                processes.sort(key=lambda x: x['pid'] or 0)

            # Limit results
            processes = processes[:limit]

            output = f"Running Processes (sorted by {sort_by}, top {limit}):\n"
            output += "=" * 60 + "\n"
            output += f"{'PID':<8} {'Name':<20} {'CPU%':<8} {'Memory%':<10} {'Status':<12}\n"
            output += "-" * 60 + "\n"

            for proc in processes:
                pid = proc['pid'] or 0
                name = (proc['name'] or 'Unknown')[:19]
                cpu = proc['cpu_percent'] or 0
                memory = proc['memory_percent'] or 0
                status = proc['status'] or 'Unknown'

                output += f"{pid:<8} {name:<20} {cpu:<8.1f} {memory:<10.1f} {status:<12}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error getting processes: {str(e)}")

    def _get_system_info(self) -> ToolResult:
        """Get system information."""
        try:
            # System information
            uname = platform.uname()
            boot_time = datetime.fromtimestamp(psutil.boot_time())

            output = "System Information:\n"
            output += "=" * 30 + "\n"
            output += f"System: {uname.system}\n"
            output += f"Node Name: {uname.node}\n"
            output += f"Release: {uname.release}\n"
            output += f"Version: {uname.version}\n"
            output += f"Machine: {uname.machine}\n"
            output += f"Processor: {uname.processor}\n"
            output += f"Boot Time: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}\n"

            # Python version
            output += f"Python Version: {platform.python_version()}\n"

            # Current time and uptime
            current_time = datetime.now()
            uptime = current_time - boot_time
            output += f"Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            output += f"Uptime: {str(uptime).split('.')[0]}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error getting system info: {str(e)}")

    def _monitor_system(self, duration: int, interval: int) -> ToolResult:
        """Continuous monitoring for specified duration."""
        try:
            measurements = []
            start_time = time.time()

            output = f"System Monitoring (Duration: {duration}s, Interval: {interval}s):\n"
            output += "=" * 60 + "\n"
            output += f"{'Time':<12} {'CPU%':<8} {'Memory%':<10} {'Disk%':<8} {'Network(MB/s)':<15}\n"
            output += "-" * 60 + "\n"

            # Initial network counters
            net_io_start = psutil.net_io_counters()

            while time.time() - start_time < duration:
                timestamp = datetime.now().strftime('%H:%M:%S')

                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=0.1)

                # Memory usage
                memory_percent = psutil.virtual_memory().percent

                # Disk usage
                disk_percent = (psutil.disk_usage('/').used / psutil.disk_usage('/').total) * 100

                # Network usage (calculate rate)
                net_io_current = psutil.net_io_counters()
                if len(measurements) > 0:
                    prev_net = measurements[-1]['net_io']
                    bytes_sent_rate = (net_io_current.bytes_sent - prev_net.bytes_sent) / interval / (1024**2)
                    bytes_recv_rate = (net_io_current.bytes_recv - prev_net.bytes_recv) / interval / (1024**2)
                    network_rate = f"{bytes_sent_rate:.1f}↑/{bytes_recv_rate:.1f}↓"
                else:
                    network_rate = "0.0↑/0.0↓"

                # Store measurement
                measurements.append({
                    'timestamp': timestamp,
                    'cpu': cpu_percent,
                    'memory': memory_percent,
                    'disk': disk_percent,
                    'net_io': net_io_current
                })

                output += f"{timestamp:<12} {cpu_percent:<8.1f} {memory_percent:<10.1f} {disk_percent:<8.1f} {network_rate:<15}\n"

                time.sleep(interval)

            # Summary
            if measurements:
                avg_cpu = sum(m['cpu'] for m in measurements) / len(measurements)
                avg_memory = sum(m['memory'] for m in measurements) / len(measurements)
                max_cpu = max(m['cpu'] for m in measurements)
                max_memory = max(m['memory'] for m in measurements)

                output += "\nSummary:\n"
                output += f"Average CPU: {avg_cpu:.1f}%\n"
                output += f"Average Memory: {avg_memory:.1f}%\n"
                output += f"Peak CPU: {max_cpu:.1f}%\n"
                output += f"Peak Memory: {max_memory:.1f}%\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error monitoring system: {str(e)}")

    def _get_top_processes(self, sort_by: str, limit: int) -> ToolResult:
        """Get top processes by CPU/memory usage."""
        try:
            processes = []

            # Get processes with detailed info
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info', 'cmdline']):
                try:
                    proc_info = proc.info
                    # Get memory in MB
                    if proc_info['memory_info']:
                        proc_info['memory_mb'] = proc_info['memory_info'].rss / (1024**2)
                    else:
                        proc_info['memory_mb'] = 0

                    # Get command line (first 50 chars)
                    if proc_info['cmdline']:
                        proc_info['cmdline_short'] = ' '.join(proc_info['cmdline'])[:50]
                    else:
                        proc_info['cmdline_short'] = proc_info['name'] or 'Unknown'

                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            # Sort processes
            if sort_by == "cpu":
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                sort_desc = "CPU Usage"
            elif sort_by == "memory":
                processes.sort(key=lambda x: x['memory_percent'] or 0, reverse=True)
                sort_desc = "Memory Usage"
            else:
                processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
                sort_desc = "CPU Usage"

            # Limit results
            processes = processes[:limit]

            output = f"Top {limit} Processes by {sort_desc}:\n"
            output += "=" * 80 + "\n"
            output += f"{'PID':<8} {'CPU%':<8} {'Memory%':<10} {'Memory(MB)':<12} {'Command':<40}\n"
            output += "-" * 80 + "\n"

            for proc in processes:
                pid = proc['pid'] or 0
                cpu = proc['cpu_percent'] or 0
                memory_pct = proc['memory_percent'] or 0
                memory_mb = proc['memory_mb'] or 0
                command = proc['cmdline_short'] or 'Unknown'

                output += f"{pid:<8} {cpu:<8.1f} {memory_pct:<10.1f} {memory_mb:<12.1f} {command:<40}\n"

            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Error getting top processes: {str(e)}")
