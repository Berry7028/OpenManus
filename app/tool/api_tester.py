"""
API Tester Tool

API テスト・検証を行うツール
HTTPリクエスト送信、レスポンス検証、パフォーマンステスト、負荷テストなどの機能を提供
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import aiohttp
import ssl
from urllib.parse import urljoin, urlparse
import statistics

from .base import BaseTool

logger = logging.getLogger(__name__)

class ApiTester(BaseTool):
    """API テスト・検証ツール"""

    def __init__(self):
        super().__init__()
        self.session = None

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        API テスト操作を実行

        Args:
            command: 実行するコマンド
            **kwargs: コマンド固有のパラメータ

        Returns:
            実行結果
        """
        try:
            if command == "request":
                return await self._request(**kwargs)
            elif command == "test_endpoint":
                return await self._test_endpoint(**kwargs)
            elif command == "load_test":
                return await self._load_test(**kwargs)
            elif command == "health_check":
                return await self._health_check(**kwargs)
            elif command == "validate_response":
                return await self._validate_response(**kwargs)
            elif command == "test_suite":
                return await self._test_suite(**kwargs)
            elif command == "benchmark":
                return await self._benchmark(**kwargs)
            elif command == "monitor":
                return await self._monitor(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "request", "test_endpoint", "load_test", "health_check",
                        "validate_response", "test_suite", "benchmark", "monitor"
                    ]
                }

        except Exception as e:
            logger.error(f"API test operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    async def _get_session(self) -> aiohttp.ClientSession:
        """HTTPセッションを取得"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def _request(self, url: str, method: str = "GET",
                      headers: Optional[Dict[str, str]] = None,
                      data: Optional[Union[Dict, str]] = None,
                      params: Optional[Dict[str, str]] = None,
                      timeout: int = 30,
                      verify_ssl: bool = True) -> Dict[str, Any]:
        """HTTPリクエストを送信"""
        try:
            session = await self._get_session()

            # SSL検証設定
            ssl_context = ssl.create_default_context() if verify_ssl else False

            start_time = time.time()

            async with session.request(
                method=method.upper(),
                url=url,
                headers=headers,
                json=data if isinstance(data, dict) else None,
                data=data if isinstance(data, str) else None,
                params=params,
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:

                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # ミリ秒

                # レスポンスボディを取得
                try:
                    response_text = await response.text()
                    try:
                        response_json = json.loads(response_text)
                    except json.JSONDecodeError:
                        response_json = None
                except Exception:
                    response_text = ""
                    response_json = None

                return {
                    "success": True,
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "response_time_ms": round(response_time, 2),
                    "response_text": response_text,
                    "response_json": response_json,
                    "url": str(response.url),
                    "method": method.upper(),
                    "content_length": len(response_text),
                    "content_type": response.headers.get("content-type", "")
                }

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Request timeout",
                "url": url,
                "method": method
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "method": method
            }

    async def _test_endpoint(self, url: str, method: str = "GET",
                           expected_status: int = 200,
                           expected_headers: Optional[Dict[str, str]] = None,
                           expected_content: Optional[str] = None,
                           **kwargs) -> Dict[str, Any]:
        """エンドポイントをテスト"""
        try:
            # リクエストを送信
            result = await self._request(url, method, **kwargs)

            if not result["success"]:
                return result

            # テスト結果を初期化
            test_results = {
                "status_code_test": False,
                "headers_test": True,
                "content_test": True,
                "overall_success": False
            }

            # ステータスコードをテスト
            test_results["status_code_test"] = result["status_code"] == expected_status

            # ヘッダーをテスト
            if expected_headers:
                for key, expected_value in expected_headers.items():
                    actual_value = result["headers"].get(key.lower())
                    if actual_value != expected_value:
                        test_results["headers_test"] = False
                        break

            # コンテンツをテスト
            if expected_content:
                if expected_content not in result["response_text"]:
                    test_results["content_test"] = False

            # 全体的な成功判定
            test_results["overall_success"] = all([
                test_results["status_code_test"],
                test_results["headers_test"],
                test_results["content_test"]
            ])

            return {
                "success": True,
                "test_results": test_results,
                "response_data": result,
                "expected": {
                    "status_code": expected_status,
                    "headers": expected_headers,
                    "content": expected_content
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Endpoint test failed: {e}"
            }

    async def _load_test(self, url: str, concurrent_requests: int = 10,
                        total_requests: int = 100, method: str = "GET",
                        **kwargs) -> Dict[str, Any]:
        """負荷テストを実行"""
        try:
            results = []
            errors = []

            async def single_request():
                try:
                    result = await self._request(url, method, **kwargs)
                    if result["success"]:
                        results.append(result)
                    else:
                        errors.append(result)
                except Exception as e:
                    errors.append({"error": str(e)})

            # セマフォで同時実行数を制限
            semaphore = asyncio.Semaphore(concurrent_requests)

            async def limited_request():
                async with semaphore:
                    await single_request()

            start_time = time.time()

            # 全リクエストを実行
            tasks = [limited_request() for _ in range(total_requests)]
            await asyncio.gather(*tasks)

            end_time = time.time()
            total_time = end_time - start_time

            # 統計を計算
            if results:
                response_times = [r["response_time_ms"] for r in results]
                status_codes = [r["status_code"] for r in results]

                stats = {
                    "total_requests": total_requests,
                    "successful_requests": len(results),
                    "failed_requests": len(errors),
                    "success_rate": len(results) / total_requests * 100,
                    "total_time_seconds": round(total_time, 2),
                    "requests_per_second": round(total_requests / total_time, 2),
                    "response_time_stats": {
                        "min_ms": min(response_times),
                        "max_ms": max(response_times),
                        "avg_ms": round(statistics.mean(response_times), 2),
                        "median_ms": round(statistics.median(response_times), 2)
                    },
                    "status_code_distribution": {}
                }

                # ステータスコード分布
                for code in set(status_codes):
                    stats["status_code_distribution"][code] = status_codes.count(code)

            else:
                stats = {
                    "total_requests": total_requests,
                    "successful_requests": 0,
                    "failed_requests": len(errors),
                    "success_rate": 0,
                    "total_time_seconds": round(total_time, 2)
                }

            return {
                "success": True,
                "load_test_stats": stats,
                "errors": errors[:10]  # 最初の10個のエラーのみ
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Load test failed: {e}"
            }

    async def _health_check(self, urls: List[str],
                           timeout: int = 10) -> Dict[str, Any]:
        """複数URLのヘルスチェック"""
        try:
            results = {}

            async def check_url(url):
                try:
                    result = await self._request(url, timeout=timeout)
                    return {
                        "status": "healthy" if result["success"] and 200 <= result.get("status_code", 0) < 400 else "unhealthy",
                        "status_code": result.get("status_code"),
                        "response_time_ms": result.get("response_time_ms"),
                        "error": result.get("error")
                    }
                except Exception as e:
                    return {
                        "status": "unhealthy",
                        "error": str(e)
                    }

            # 全URLを並行チェック
            tasks = {url: check_url(url) for url in urls}
            results = await asyncio.gather(*tasks.values())

            # 結果をまとめる
            health_status = {}
            for url, result in zip(urls, results):
                health_status[url] = result

            # 全体的なヘルス状態
            healthy_count = sum(1 for r in results if r["status"] == "healthy")
            overall_health = "healthy" if healthy_count == len(urls) else "degraded" if healthy_count > 0 else "unhealthy"

            return {
                "success": True,
                "overall_health": overall_health,
                "healthy_services": healthy_count,
                "total_services": len(urls),
                "health_ratio": healthy_count / len(urls),
                "service_status": health_status,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Health check failed: {e}"
            }

    async def _validate_response(self, response_data: Dict[str, Any],
                                validation_rules: Dict[str, Any]) -> Dict[str, Any]:
        """レスポンスを検証"""
        try:
            validation_results = {}

            # ステータスコード検証
            if "status_code" in validation_rules:
                expected = validation_rules["status_code"]
                actual = response_data.get("status_code")
                validation_results["status_code"] = {
                    "passed": actual == expected,
                    "expected": expected,
                    "actual": actual
                }

            # レスポンス時間検証
            if "max_response_time_ms" in validation_rules:
                max_time = validation_rules["max_response_time_ms"]
                actual_time = response_data.get("response_time_ms", 0)
                validation_results["response_time"] = {
                    "passed": actual_time <= max_time,
                    "expected_max": max_time,
                    "actual": actual_time
                }

            # ヘッダー検証
            if "headers" in validation_rules:
                headers_passed = True
                header_results = {}

                for header, expected_value in validation_rules["headers"].items():
                    actual_value = response_data.get("headers", {}).get(header.lower())
                    passed = actual_value == expected_value
                    headers_passed = headers_passed and passed

                    header_results[header] = {
                        "passed": passed,
                        "expected": expected_value,
                        "actual": actual_value
                    }

                validation_results["headers"] = {
                    "passed": headers_passed,
                    "details": header_results
                }

            # JSONスキーマ検証
            if "json_schema" in validation_rules and response_data.get("response_json"):
                try:
                    import jsonschema
                    schema = validation_rules["json_schema"]
                    jsonschema.validate(response_data["response_json"], schema)
                    validation_results["json_schema"] = {"passed": True}
                except ImportError:
                    validation_results["json_schema"] = {
                        "passed": False,
                        "error": "jsonschema library not installed"
                    }
                except Exception as e:
                    validation_results["json_schema"] = {
                        "passed": False,
                        "error": str(e)
                    }

            # 全体的な検証結果
            all_passed = all(
                result.get("passed", True)
                for result in validation_results.values()
            )

            return {
                "success": True,
                "validation_passed": all_passed,
                "validation_results": validation_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Response validation failed: {e}"
            }

    async def _test_suite(self, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """テストスイートを実行"""
        try:
            results = []
            passed_count = 0

            for i, test_case in enumerate(test_cases):
                test_name = test_case.get("name", f"Test {i+1}")

                try:
                    # テストケースを実行
                    if "validation_rules" in test_case:
                        # レスポンス検証付きテスト
                        response = await self._request(**test_case.get("request", {}))
                        if response["success"]:
                            validation = await self._validate_response(
                                response, test_case["validation_rules"]
                            )
                            test_result = {
                                "name": test_name,
                                "passed": validation.get("validation_passed", False),
                                "response": response,
                                "validation": validation
                            }
                        else:
                            test_result = {
                                "name": test_name,
                                "passed": False,
                                "error": response.get("error"),
                                "response": response
                            }
                    else:
                        # 基本的なリクエストテスト
                        response = await self._request(**test_case.get("request", {}))
                        test_result = {
                            "name": test_name,
                            "passed": response["success"],
                            "response": response
                        }

                    if test_result["passed"]:
                        passed_count += 1

                    results.append(test_result)

                except Exception as e:
                    results.append({
                        "name": test_name,
                        "passed": False,
                        "error": str(e)
                    })

            return {
                "success": True,
                "test_suite_results": {
                    "total_tests": len(test_cases),
                    "passed_tests": passed_count,
                    "failed_tests": len(test_cases) - passed_count,
                    "success_rate": passed_count / len(test_cases) * 100,
                    "test_results": results
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Test suite execution failed: {e}"
            }

    async def _benchmark(self, url: str, duration_seconds: int = 60,
                        concurrent_requests: int = 10, method: str = "GET",
                        **kwargs) -> Dict[str, Any]:
        """指定時間でのベンチマークテスト"""
        try:
            results = []
            errors = []
            start_time = time.time()
            end_time = start_time + duration_seconds

            async def benchmark_request():
                while time.time() < end_time:
                    try:
                        result = await self._request(url, method, **kwargs)
                        if result["success"]:
                            results.append(result)
                        else:
                            errors.append(result)
                    except Exception as e:
                        errors.append({"error": str(e)})

                    # 短い間隔を空ける
                    await asyncio.sleep(0.01)

            # 並行実行
            tasks = [benchmark_request() for _ in range(concurrent_requests)]
            await asyncio.gather(*tasks)

            actual_duration = time.time() - start_time

            # 統計計算
            if results:
                response_times = [r["response_time_ms"] for r in results]

                benchmark_stats = {
                    "duration_seconds": round(actual_duration, 2),
                    "total_requests": len(results),
                    "failed_requests": len(errors),
                    "requests_per_second": round(len(results) / actual_duration, 2),
                    "response_time_stats": {
                        "min_ms": min(response_times),
                        "max_ms": max(response_times),
                        "avg_ms": round(statistics.mean(response_times), 2),
                        "median_ms": round(statistics.median(response_times), 2),
                        "p95_ms": round(statistics.quantiles(response_times, n=20)[18], 2) if len(response_times) > 20 else max(response_times)
                    }
                }
            else:
                benchmark_stats = {
                    "duration_seconds": round(actual_duration, 2),
                    "total_requests": 0,
                    "failed_requests": len(errors),
                    "requests_per_second": 0
                }

            return {
                "success": True,
                "benchmark_results": benchmark_stats,
                "errors_sample": errors[:5]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Benchmark failed: {e}"
            }

    async def _monitor(self, url: str, interval_seconds: int = 60,
                      duration_minutes: int = 10, **kwargs) -> Dict[str, Any]:
        """継続的なモニタリング"""
        try:
            monitoring_data = []
            start_time = time.time()
            end_time = start_time + (duration_minutes * 60)

            while time.time() < end_time:
                timestamp = datetime.now().isoformat()
                result = await self._request(url, **kwargs)

                monitoring_point = {
                    "timestamp": timestamp,
                    "success": result["success"],
                    "status_code": result.get("status_code"),
                    "response_time_ms": result.get("response_time_ms"),
                    "error": result.get("error")
                }

                monitoring_data.append(monitoring_point)

                # 次の測定まで待機
                await asyncio.sleep(interval_seconds)

            # 統計計算
            successful_requests = [d for d in monitoring_data if d["success"]]

            if successful_requests:
                response_times = [d["response_time_ms"] for d in successful_requests]
                uptime_percentage = len(successful_requests) / len(monitoring_data) * 100

                monitoring_stats = {
                    "total_checks": len(monitoring_data),
                    "successful_checks": len(successful_requests),
                    "failed_checks": len(monitoring_data) - len(successful_requests),
                    "uptime_percentage": round(uptime_percentage, 2),
                    "avg_response_time_ms": round(statistics.mean(response_times), 2),
                    "max_response_time_ms": max(response_times),
                    "min_response_time_ms": min(response_times)
                }
            else:
                monitoring_stats = {
                    "total_checks": len(monitoring_data),
                    "successful_checks": 0,
                    "failed_checks": len(monitoring_data),
                    "uptime_percentage": 0
                }

            return {
                "success": True,
                "monitoring_stats": monitoring_stats,
                "monitoring_data": monitoring_data
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Monitoring failed: {e}"
            }

    async def close(self):
        """リソースをクリーンアップ"""
        if self.session and not self.session.closed:
            await self.session.close()

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """各コマンドのパラメータ定義を返す"""
        return {
            "request": {
                "url": {"type": "string", "required": True, "description": "リクエスト先URL"},
                "method": {"type": "string", "required": False, "description": "HTTPメソッド（デフォルト: GET）"},
                "headers": {"type": "object", "required": False, "description": "リクエストヘッダー"},
                "data": {"type": "object", "required": False, "description": "リクエストボディ"},
                "params": {"type": "object", "required": False, "description": "クエリパラメータ"},
                "timeout": {"type": "integer", "required": False, "description": "タイムアウト秒数"},
                "verify_ssl": {"type": "boolean", "required": False, "description": "SSL証明書検証"}
            },
            "test_endpoint": {
                "url": {"type": "string", "required": True, "description": "テスト対象URL"},
                "method": {"type": "string", "required": False, "description": "HTTPメソッド"},
                "expected_status": {"type": "integer", "required": False, "description": "期待するステータスコード"},
                "expected_headers": {"type": "object", "required": False, "description": "期待するヘッダー"},
                "expected_content": {"type": "string", "required": False, "description": "期待するコンテンツ"}
            },
            "load_test": {
                "url": {"type": "string", "required": True, "description": "負荷テスト対象URL"},
                "concurrent_requests": {"type": "integer", "required": False, "description": "同時リクエスト数"},
                "total_requests": {"type": "integer", "required": False, "description": "総リクエスト数"},
                "method": {"type": "string", "required": False, "description": "HTTPメソッド"}
            },
            "health_check": {
                "urls": {"type": "array", "required": True, "description": "チェック対象URLリスト"},
                "timeout": {"type": "integer", "required": False, "description": "タイムアウト秒数"}
            },
            "validate_response": {
                "response_data": {"type": "object", "required": True, "description": "検証対象レスポンスデータ"},
                "validation_rules": {"type": "object", "required": True, "description": "検証ルール"}
            },
            "test_suite": {
                "test_cases": {"type": "array", "required": True, "description": "テストケースリスト"}
            },
            "benchmark": {
                "url": {"type": "string", "required": True, "description": "ベンチマーク対象URL"},
                "duration_seconds": {"type": "integer", "required": False, "description": "実行時間（秒）"},
                "concurrent_requests": {"type": "integer", "required": False, "description": "同時リクエスト数"},
                "method": {"type": "string", "required": False, "description": "HTTPメソッド"}
            },
            "monitor": {
                "url": {"type": "string", "required": True, "description": "モニタリング対象URL"},
                "interval_seconds": {"type": "integer", "required": False, "description": "チェック間隔（秒）"},
                "duration_minutes": {"type": "integer", "required": False, "description": "モニタリング時間（分）"}
            }
        }
