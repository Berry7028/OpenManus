"""
Network Scanner Tool

ネットワーク診断・スキャンを行うツール
ポートスキャン、ping、traceroute、ネットワーク情報収集などの機能を提供
"""

import asyncio
import socket
import subprocess
import platform
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import ipaddress
import time
import concurrent.futures

from .base import BaseTool

logger = logging.getLogger(__name__)

class NetworkScanner(BaseTool):
    """ネットワーク診断・スキャンツール"""

    def __init__(self):
        super().__init__()
        self.common_ports = [
            21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995,
            1433, 3306, 3389, 5432, 5900, 8080, 8443, 9090
        ]

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        ネットワーク診断・スキャン操作を実行

        Args:
            command: 実行するコマンド
            **kwargs: コマンド固有のパラメータ

        Returns:
            実行結果
        """
        try:
            if command == "ping":
                return await self._ping(**kwargs)
            elif command == "port_scan":
                return await self._port_scan(**kwargs)
            elif command == "network_scan":
                return await self._network_scan(**kwargs)
            elif command == "traceroute":
                return await self._traceroute(**kwargs)
            elif command == "dns_lookup":
                return await self._dns_lookup(**kwargs)
            elif command == "whois":
                return await self._whois(**kwargs)
            elif command == "get_local_info":
                return await self._get_local_info(**kwargs)
            elif command == "bandwidth_test":
                return await self._bandwidth_test(**kwargs)
            elif command == "service_detection":
                return await self._service_detection(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "ping", "port_scan", "network_scan", "traceroute",
                        "dns_lookup", "whois", "get_local_info", "bandwidth_test",
                        "service_detection"
                    ]
                }

        except Exception as e:
            logger.error(f"Network scan operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    async def _ping(self, host: str, count: int = 4, timeout: int = 5) -> Dict[str, Any]:
        """指定ホストにpingを送信"""
        try:
            # OSに応じてpingコマンドを構築
            system = platform.system().lower()
            if system == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(timeout * 1000), host]
            else:
                cmd = ["ping", "-c", str(count), "-W", str(timeout), host]

            start_time = time.time()

            # pingコマンドを実行
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            end_time = time.time()

            output = stdout.decode('utf-8', errors='ignore')
            error_output = stderr.decode('utf-8', errors='ignore')

            # 結果を解析
            success = process.returncode == 0

            ping_results = {
                "host": host,
                "success": success,
                "packets_sent": count,
                "return_code": process.returncode,
                "total_time_seconds": round(end_time - start_time, 2),
                "raw_output": output,
                "error_output": error_output
            }

            if success:
                # 統計情報を抽出（簡易版）
                lines = output.split('\n')
                response_times = []
                packets_received = 0

                for line in lines:
                    if "time=" in line.lower() or "時間=" in line:
                        try:
                            # 応答時間を抽出
                            if "time=" in line:
                                time_part = line.split("time=")[1].split()[0]
                                response_times.append(float(time_part.replace("ms", "")))
                            packets_received += 1
                        except:
                            continue

                if response_times:
                    ping_results.update({
                        "packets_received": packets_received,
                        "packet_loss_percent": ((count - packets_received) / count) * 100,
                        "min_time_ms": min(response_times),
                        "max_time_ms": max(response_times),
                        "avg_time_ms": round(sum(response_times) / len(response_times), 2)
                    })

            return {
                "success": True,
                "ping_results": ping_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Ping failed: {e}"
            }

    async def _port_scan(self, host: str, ports: Optional[List[int]] = None,
                        timeout: int = 3, scan_type: str = "tcp") -> Dict[str, Any]:
        """指定ホストのポートスキャンを実行"""
        try:
            if ports is None:
                ports = self.common_ports

            # IPアドレスを解決
            try:
                ip_address = socket.gethostbyname(host)
            except socket.gaierror:
                return {
                    "success": False,
                    "error": f"Cannot resolve hostname: {host}"
                }

            scan_results = {
                "host": host,
                "ip_address": ip_address,
                "scan_type": scan_type,
                "total_ports": len(ports),
                "open_ports": [],
                "closed_ports": [],
                "filtered_ports": [],
                "scan_time": datetime.now().isoformat()
            }

            async def scan_port(port):
                try:
                    if scan_type.lower() == "tcp":
                        # TCP接続テスト
                        future = asyncio.open_connection(ip_address, port)
                        reader, writer = await asyncio.wait_for(future, timeout=timeout)
                        writer.close()
                        await writer.wait_closed()
                        return port, "open"
                    else:
                        # UDP スキャン（簡易版）
                        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sock.settimeout(timeout)
                        try:
                            sock.sendto(b'', (ip_address, port))
                            sock.close()
                            return port, "open"
                        except:
                            sock.close()
                            return port, "closed"

                except asyncio.TimeoutError:
                    return port, "filtered"
                except ConnectionRefusedError:
                    return port, "closed"
                except Exception:
                    return port, "filtered"

            # 並行してポートスキャンを実行
            start_time = time.time()

            # セマフォで同時接続数を制限
            semaphore = asyncio.Semaphore(50)

            async def limited_scan(port):
                async with semaphore:
                    return await scan_port(port)

            tasks = [limited_scan(port) for port in ports]
            results = await asyncio.gather(*tasks)

            end_time = time.time()

            # 結果を分類
            for port, status in results:
                if status == "open":
                    scan_results["open_ports"].append(port)
                elif status == "closed":
                    scan_results["closed_ports"].append(port)
                else:
                    scan_results["filtered_ports"].append(port)

            scan_results.update({
                "open_count": len(scan_results["open_ports"]),
                "closed_count": len(scan_results["closed_ports"]),
                "filtered_count": len(scan_results["filtered_ports"]),
                "scan_duration_seconds": round(end_time - start_time, 2)
            })

            return {
                "success": True,
                "port_scan_results": scan_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Port scan failed: {e}"
            }

    async def _network_scan(self, network: str, timeout: int = 2) -> Dict[str, Any]:
        """ネットワーク範囲内のホストスキャン"""
        try:
            # ネットワーク範囲を解析
            try:
                net = ipaddress.ip_network(network, strict=False)
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid network format: {network}"
                }

            # スキャン対象が多すぎる場合は制限
            if net.num_addresses > 256:
                return {
                    "success": False,
                    "error": f"Network too large. Maximum 256 addresses allowed."
                }

            scan_results = {
                "network": str(net),
                "total_hosts": net.num_addresses,
                "alive_hosts": [],
                "dead_hosts": [],
                "scan_time": datetime.now().isoformat()
            }

            async def ping_host(ip):
                try:
                    # 簡易ping（TCP接続テスト）
                    future = asyncio.open_connection(str(ip), 80)
                    reader, writer = await asyncio.wait_for(future, timeout=timeout)
                    writer.close()
                    await writer.wait_closed()
                    return str(ip), True
                except:
                    # ICMPを使用した実際のping
                    try:
                        system = platform.system().lower()
                        if system == "windows":
                            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), str(ip)]
                        else:
                            cmd = ["ping", "-c", "1", "-W", str(timeout), str(ip)]

                        process = await asyncio.create_subprocess_exec(
                            *cmd,
                            stdout=asyncio.subprocess.DEVNULL,
                            stderr=asyncio.subprocess.DEVNULL
                        )

                        await process.communicate()
                        return str(ip), process.returncode == 0
                    except:
                        return str(ip), False

            start_time = time.time()

            # 並行してホストスキャンを実行
            semaphore = asyncio.Semaphore(20)

            async def limited_ping(ip):
                async with semaphore:
                    return await ping_host(ip)

            tasks = [limited_ping(ip) for ip in net.hosts()]
            results = await asyncio.gather(*tasks)

            end_time = time.time()

            # 結果を分類
            for ip, is_alive in results:
                if is_alive:
                    scan_results["alive_hosts"].append(ip)
                else:
                    scan_results["dead_hosts"].append(ip)

            scan_results.update({
                "alive_count": len(scan_results["alive_hosts"]),
                "dead_count": len(scan_results["dead_hosts"]),
                "scan_duration_seconds": round(end_time - start_time, 2)
            })

            return {
                "success": True,
                "network_scan_results": scan_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Network scan failed: {e}"
            }

    async def _traceroute(self, host: str, max_hops: int = 30) -> Dict[str, Any]:
        """指定ホストへのtracerouteを実行"""
        try:
            # OSに応じてtracerouteコマンドを構築
            system = platform.system().lower()
            if system == "windows":
                cmd = ["tracert", "-h", str(max_hops), host]
            else:
                cmd = ["traceroute", "-m", str(max_hops), host]

            start_time = time.time()

            # tracerouteコマンドを実行
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()
            end_time = time.time()

            output = stdout.decode('utf-8', errors='ignore')
            error_output = stderr.decode('utf-8', errors='ignore')

            # 結果を解析
            hops = []
            lines = output.split('\n')

            for line in lines:
                line = line.strip()
                if not line or line.startswith('traceroute') or line.startswith('Tracing'):
                    continue

                # 簡易的なホップ情報抽出
                if any(char.isdigit() for char in line):
                    hops.append(line)

            traceroute_results = {
                "host": host,
                "max_hops": max_hops,
                "total_hops": len(hops),
                "hops": hops,
                "success": process.returncode == 0,
                "execution_time_seconds": round(end_time - start_time, 2),
                "raw_output": output,
                "error_output": error_output
            }

            return {
                "success": True,
                "traceroute_results": traceroute_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Traceroute failed: {e}"
            }

    async def _dns_lookup(self, domain: str, record_type: str = "A") -> Dict[str, Any]:
        """DNS lookup を実行"""
        try:
            import dns.resolver

            resolver = dns.resolver.Resolver()
            resolver.timeout = 10

            dns_results = {
                "domain": domain,
                "record_type": record_type,
                "records": [],
                "query_time": datetime.now().isoformat()
            }

            try:
                answers = resolver.resolve(domain, record_type)

                for answer in answers:
                    dns_results["records"].append(str(answer))

                dns_results["success"] = True
                dns_results["record_count"] = len(dns_results["records"])

            except dns.resolver.NXDOMAIN:
                dns_results["success"] = False
                dns_results["error"] = "Domain not found"
            except dns.resolver.NoAnswer:
                dns_results["success"] = False
                dns_results["error"] = f"No {record_type} records found"
            except Exception as e:
                dns_results["success"] = False
                dns_results["error"] = str(e)

            return {
                "success": True,
                "dns_results": dns_results
            }

        except ImportError:
            # dnspythonが利用できない場合はsocketを使用
            try:
                if record_type.upper() == "A":
                    ip = socket.gethostbyname(domain)
                    return {
                        "success": True,
                        "dns_results": {
                            "domain": domain,
                            "record_type": "A",
                            "records": [ip],
                            "record_count": 1,
                            "success": True,
                            "query_time": datetime.now().isoformat()
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"DNS record type {record_type} not supported without dnspython library"
                    }
            except socket.gaierror as e:
                return {
                    "success": False,
                    "error": f"DNS lookup failed: {e}"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"DNS lookup failed: {e}"
            }

    async def _whois(self, domain: str) -> Dict[str, Any]:
        """WHOIS情報を取得"""
        try:
            # whoisコマンドを実行
            process = await asyncio.create_subprocess_exec(
                "whois", domain,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                whois_data = stdout.decode('utf-8', errors='ignore')

                # 基本的な情報を抽出
                whois_info = {
                    "domain": domain,
                    "raw_data": whois_data,
                    "query_time": datetime.now().isoformat()
                }

                # 簡易的な情報抽出
                lines = whois_data.split('\n')
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip()

                        if key in ['registrar', 'creation_date', 'expiration_date', 'name_server']:
                            whois_info[key] = value

                return {
                    "success": True,
                    "whois_results": whois_info
                }
            else:
                error_output = stderr.decode('utf-8', errors='ignore')
                return {
                    "success": False,
                    "error": f"WHOIS query failed: {error_output}"
                }

        except FileNotFoundError:
            return {
                "success": False,
                "error": "WHOIS command not found. Please install whois utility."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"WHOIS query failed: {e}"
            }

    async def _get_local_info(self) -> Dict[str, Any]:
        """ローカルネットワーク情報を取得"""
        try:
            local_info = {
                "hostname": socket.gethostname(),
                "platform": platform.system(),
                "platform_version": platform.version(),
                "network_interfaces": {},
                "default_gateway": None,
                "dns_servers": [],
                "query_time": datetime.now().isoformat()
            }

            # ネットワークインターフェース情報
            try:
                import psutil

                interfaces = psutil.net_if_addrs()
                for interface_name, addresses in interfaces.items():
                    interface_info = []
                    for addr in addresses:
                        if addr.family == socket.AF_INET:  # IPv4
                            interface_info.append({
                                "type": "IPv4",
                                "address": addr.address,
                                "netmask": addr.netmask,
                                "broadcast": addr.broadcast
                            })
                        elif addr.family == socket.AF_INET6:  # IPv6
                            interface_info.append({
                                "type": "IPv6",
                                "address": addr.address,
                                "netmask": addr.netmask
                            })

                    if interface_info:
                        local_info["network_interfaces"][interface_name] = interface_info

                # ネットワーク統計
                net_stats = psutil.net_io_counters()
                local_info["network_stats"] = {
                    "bytes_sent": net_stats.bytes_sent,
                    "bytes_recv": net_stats.bytes_recv,
                    "packets_sent": net_stats.packets_sent,
                    "packets_recv": net_stats.packets_recv
                }

            except ImportError:
                # psutilが利用できない場合の代替手段
                try:
                    # 基本的なIPアドレス取得
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                    s.close()

                    local_info["primary_ip"] = local_ip
                except:
                    pass

            # デフォルトゲートウェイ取得（簡易版）
            try:
                if platform.system().lower() == "windows":
                    process = await asyncio.create_subprocess_exec(
                        "route", "print", "0.0.0.0",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                else:
                    process = await asyncio.create_subprocess_exec(
                        "ip", "route", "show", "default",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )

                stdout, _ = await process.communicate()
                if process.returncode == 0:
                    output = stdout.decode('utf-8', errors='ignore')
                    # 簡易的なゲートウェイ抽出
                    lines = output.split('\n')
                    for line in lines:
                        if 'default' in line.lower() or '0.0.0.0' in line:
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part in ['via', 'gateway'] and i + 1 < len(parts):
                                    local_info["default_gateway"] = parts[i + 1]
                                    break
                            break
            except:
                pass

            return {
                "success": True,
                "local_network_info": local_info
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get local network info: {e}"
            }

    async def _bandwidth_test(self, host: str = "8.8.8.8", port: int = 53,
                             duration: int = 10, packet_size: int = 1024) -> Dict[str, Any]:
        """簡易帯域幅テスト"""
        try:
            test_results = {
                "host": host,
                "port": port,
                "duration_seconds": duration,
                "packet_size_bytes": packet_size,
                "packets_sent": 0,
                "packets_received": 0,
                "bytes_sent": 0,
                "bytes_received": 0,
                "start_time": datetime.now().isoformat()
            }

            start_time = time.time()
            end_time = start_time + duration

            # テストデータ
            test_data = b'0' * packet_size

            while time.time() < end_time:
                try:
                    # UDP ソケットでテスト
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    sock.settimeout(1)

                    # データ送信
                    sock.sendto(test_data, (host, port))
                    test_results["packets_sent"] += 1
                    test_results["bytes_sent"] += packet_size

                    try:
                        # レスポンス受信（タイムアウトあり）
                        data, addr = sock.recvfrom(packet_size)
                        test_results["packets_received"] += 1
                        test_results["bytes_received"] += len(data)
                    except socket.timeout:
                        pass

                    sock.close()

                    # 短い間隔
                    await asyncio.sleep(0.1)

                except Exception:
                    continue

            actual_duration = time.time() - start_time

            # 統計計算
            if actual_duration > 0:
                test_results.update({
                    "actual_duration_seconds": round(actual_duration, 2),
                    "packets_per_second": round(test_results["packets_sent"] / actual_duration, 2),
                    "bytes_per_second": round(test_results["bytes_sent"] / actual_duration, 2),
                    "kilobytes_per_second": round(test_results["bytes_sent"] / actual_duration / 1024, 2),
                    "packet_loss_percent": round((1 - test_results["packets_received"] / test_results["packets_sent"]) * 100, 2) if test_results["packets_sent"] > 0 else 0
                })

            test_results["end_time"] = datetime.now().isoformat()

            return {
                "success": True,
                "bandwidth_test_results": test_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Bandwidth test failed: {e}"
            }

    async def _service_detection(self, host: str, ports: Optional[List[int]] = None) -> Dict[str, Any]:
        """サービス検出（バナーグラビング）"""
        try:
            if ports is None:
                ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 993, 995]

            service_results = {
                "host": host,
                "detected_services": {},
                "scan_time": datetime.now().isoformat()
            }

            async def detect_service(port):
                try:
                    # TCP接続を試行
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(host, port),
                        timeout=5
                    )

                    service_info = {
                        "port": port,
                        "status": "open",
                        "service": "unknown",
                        "banner": ""
                    }

                    try:
                        # バナー情報を読み取り
                        banner_data = await asyncio.wait_for(
                            reader.read(1024),
                            timeout=3
                        )
                        banner = banner_data.decode('utf-8', errors='ignore').strip()
                        service_info["banner"] = banner

                        # 簡易的なサービス識別
                        banner_lower = banner.lower()
                        if "ssh" in banner_lower:
                            service_info["service"] = "SSH"
                        elif "ftp" in banner_lower:
                            service_info["service"] = "FTP"
                        elif "smtp" in banner_lower:
                            service_info["service"] = "SMTP"
                        elif "http" in banner_lower or "server:" in banner_lower:
                            service_info["service"] = "HTTP"
                        elif "pop3" in banner_lower:
                            service_info["service"] = "POP3"
                        elif "imap" in banner_lower:
                            service_info["service"] = "IMAP"

                    except asyncio.TimeoutError:
                        pass

                    writer.close()
                    await writer.wait_closed()

                    return port, service_info

                except Exception:
                    return port, None

            # 並行してサービス検出を実行
            semaphore = asyncio.Semaphore(10)

            async def limited_detect(port):
                async with semaphore:
                    return await detect_service(port)

            tasks = [limited_detect(port) for port in ports]
            results = await asyncio.gather(*tasks)

            # 結果をまとめる
            for port, service_info in results:
                if service_info:
                    service_results["detected_services"][port] = service_info

            service_results["total_open_ports"] = len(service_results["detected_services"])

            return {
                "success": True,
                "service_detection_results": service_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Service detection failed: {e}"
            }

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """各コマンドのパラメータ定義を返す"""
        return {
            "ping": {
                "host": {"type": "string", "required": True, "description": "ping対象ホスト"},
                "count": {"type": "integer", "required": False, "description": "送信パケット数"},
                "timeout": {"type": "integer", "required": False, "description": "タイムアウト秒数"}
            },
            "port_scan": {
                "host": {"type": "string", "required": True, "description": "スキャン対象ホスト"},
                "ports": {"type": "array", "required": False, "description": "スキャン対象ポートリスト"},
                "timeout": {"type": "integer", "required": False, "description": "接続タイムアウト秒数"},
                "scan_type": {"type": "string", "required": False, "description": "スキャンタイプ（tcp/udp）"}
            },
            "network_scan": {
                "network": {"type": "string", "required": True, "description": "スキャン対象ネットワーク（CIDR形式）"},
                "timeout": {"type": "integer", "required": False, "description": "タイムアウト秒数"}
            },
            "traceroute": {
                "host": {"type": "string", "required": True, "description": "traceroute対象ホスト"},
                "max_hops": {"type": "integer", "required": False, "description": "最大ホップ数"}
            },
            "dns_lookup": {
                "domain": {"type": "string", "required": True, "description": "DNS lookup対象ドメイン"},
                "record_type": {"type": "string", "required": False, "description": "DNSレコードタイプ（A, AAAA, MX, NS, TXT等）"}
            },
            "whois": {
                "domain": {"type": "string", "required": True, "description": "WHOIS検索対象ドメイン"}
            },
            "get_local_info": {},
            "bandwidth_test": {
                "host": {"type": "string", "required": False, "description": "テスト対象ホスト"},
                "port": {"type": "integer", "required": False, "description": "テスト対象ポート"},
                "duration": {"type": "integer", "required": False, "description": "テスト時間（秒）"},
                "packet_size": {"type": "integer", "required": False, "description": "パケットサイズ（バイト）"}
            },
            "service_detection": {
                "host": {"type": "string", "required": True, "description": "サービス検出対象ホスト"},
                "ports": {"type": "array", "required": False, "description": "検出対象ポートリスト"}
            }
        }
