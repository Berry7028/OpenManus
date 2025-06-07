"""
Data Validator Tool

データ検証・バリデーションを行うツール
スキーマ検証、データ品質チェック、異常値検出、整合性チェックなどの機能を提供
"""

import asyncio
import json
import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import statistics
from pathlib import Path

from .base import BaseTool

logger = logging.getLogger(__name__)

class DataValidator(BaseTool):
    """データ検証・バリデーションツール"""

    def __init__(self):
        super().__init__()
        self.validation_rules = {}
        self.custom_validators = {}

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        データ検証操作を実行

        Args:
            command: 実行するコマンド
            **kwargs: コマンド固有のパラメータ

        Returns:
            実行結果
        """
        try:
            if command == "validate_data":
                return await self._validate_data(**kwargs)
            elif command == "validate_schema":
                return await self._validate_schema(**kwargs)
            elif command == "check_data_quality":
                return await self._check_data_quality(**kwargs)
            elif command == "detect_anomalies":
                return await self._detect_anomalies(**kwargs)
            elif command == "validate_format":
                return await self._validate_format(**kwargs)
            elif command == "check_constraints":
                return await self._check_constraints(**kwargs)
            elif command == "validate_relationships":
                return await self._validate_relationships(**kwargs)
            elif command == "create_validation_rule":
                return await self._create_validation_rule(**kwargs)
            elif command == "batch_validate":
                return await self._batch_validate(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "validate_data", "validate_schema", "check_data_quality",
                        "detect_anomalies", "validate_format", "check_constraints",
                        "validate_relationships", "create_validation_rule", "batch_validate"
                    ]
                }

        except Exception as e:
            logger.error(f"Data validation operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    async def _validate_data(self, data: Union[Dict, List],
                           validation_rules: Dict[str, Any],
                           strict_mode: bool = False) -> Dict[str, Any]:
        """データを検証ルールに基づいて検証"""
        try:
            validation_results = {
                "valid": True,
                "errors": [],
                "warnings": [],
                "field_results": {},
                "summary": {
                    "total_fields": 0,
                    "valid_fields": 0,
                    "invalid_fields": 0,
                    "warning_fields": 0
                }
            }

            if isinstance(data, list):
                # リストデータの場合、各要素を検証
                for i, item in enumerate(data):
                    item_result = await self._validate_single_item(
                        item, validation_rules, f"item_{i}", strict_mode
                    )
                    self._merge_validation_results(validation_results, item_result)
            else:
                # 単一オブジェクトの場合
                item_result = await self._validate_single_item(
                    data, validation_rules, "root", strict_mode
                )
                validation_results = item_result

            return {
                "success": True,
                "validation_results": validation_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Data validation failed: {e}"
            }

    async def _validate_single_item(self, data: Dict[str, Any],
                                   validation_rules: Dict[str, Any],
                                   item_prefix: str = "",
                                   strict_mode: bool = False) -> Dict[str, Any]:
        """単一データアイテムを検証"""
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "field_results": {},
            "summary": {
                "total_fields": 0,
                "valid_fields": 0,
                "invalid_fields": 0,
                "warning_fields": 0
            }
        }

        # 必須フィールドチェック
        required_fields = validation_rules.get("required_fields", [])
        for field in required_fields:
            if field not in data:
                error_msg = f"Required field '{field}' is missing"
                results["errors"].append({
                    "field": field,
                    "error": error_msg,
                    "type": "required_field"
                })
                results["valid"] = False
                results["summary"]["invalid_fields"] += 1

        # フィールド別検証
        field_rules = validation_rules.get("fields", {})
        for field_name, field_rule in field_rules.items():
            results["summary"]["total_fields"] += 1

            if field_name in data:
                field_result = await self._validate_field(
                    data[field_name], field_rule, field_name
                )
                results["field_results"][field_name] = field_result

                if not field_result["valid"]:
                    results["valid"] = False
                    results["errors"].extend(field_result["errors"])
                    results["summary"]["invalid_fields"] += 1
                else:
                    results["summary"]["valid_fields"] += 1

                results["warnings"].extend(field_result["warnings"])
                if field_result["warnings"]:
                    results["summary"]["warning_fields"] += 1

            elif field_name in required_fields:
                # 既に必須フィールドチェックで処理済み
                pass
            else:
                # オプションフィールドが存在しない場合
                results["summary"]["valid_fields"] += 1

        # 追加フィールドチェック（strict mode）
        if strict_mode:
            allowed_fields = set(field_rules.keys()) | set(required_fields)
            extra_fields = set(data.keys()) - allowed_fields

            for extra_field in extra_fields:
                warning_msg = f"Unexpected field '{extra_field}' found"
                results["warnings"].append({
                    "field": extra_field,
                    "warning": warning_msg,
                    "type": "unexpected_field"
                })

        return results

    async def _validate_field(self, value: Any, field_rule: Dict[str, Any],
                             field_name: str) -> Dict[str, Any]:
        """個別フィールドを検証"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "value": value
        }

        # データ型チェック
        expected_type = field_rule.get("type")
        if expected_type:
            if not self._check_type(value, expected_type):
                result["valid"] = False
                result["errors"].append({
                    "field": field_name,
                    "error": f"Expected type {expected_type}, got {type(value).__name__}",
                    "type": "type_mismatch"
                })
                return result

        # 値の範囲チェック
        min_value = field_rule.get("min")
        max_value = field_rule.get("max")

        if min_value is not None and value < min_value:
            result["valid"] = False
            result["errors"].append({
                "field": field_name,
                "error": f"Value {value} is less than minimum {min_value}",
                "type": "range_violation"
            })

        if max_value is not None and value > max_value:
            result["valid"] = False
            result["errors"].append({
                "field": field_name,
                "error": f"Value {value} is greater than maximum {max_value}",
                "type": "range_violation"
            })

        # 長さチェック（文字列、リスト等）
        min_length = field_rule.get("min_length")
        max_length = field_rule.get("max_length")

        if hasattr(value, '__len__'):
            length = len(value)

            if min_length is not None and length < min_length:
                result["valid"] = False
                result["errors"].append({
                    "field": field_name,
                    "error": f"Length {length} is less than minimum {min_length}",
                    "type": "length_violation"
                })

            if max_length is not None and length > max_length:
                result["valid"] = False
                result["errors"].append({
                    "field": field_name,
                    "error": f"Length {length} is greater than maximum {max_length}",
                    "type": "length_violation"
                })

        # パターンマッチング
        pattern = field_rule.get("pattern")
        if pattern and isinstance(value, str):
            if not re.match(pattern, value):
                result["valid"] = False
                result["errors"].append({
                    "field": field_name,
                    "error": f"Value '{value}' does not match pattern '{pattern}'",
                    "type": "pattern_mismatch"
                })

        # 許可値チェック
        allowed_values = field_rule.get("allowed_values")
        if allowed_values and value not in allowed_values:
            result["valid"] = False
            result["errors"].append({
                "field": field_name,
                "error": f"Value '{value}' is not in allowed values {allowed_values}",
                "type": "value_not_allowed"
            })

        # 禁止値チェック
        forbidden_values = field_rule.get("forbidden_values")
        if forbidden_values and value in forbidden_values:
            result["valid"] = False
            result["errors"].append({
                "field": field_name,
                "error": f"Value '{value}' is in forbidden values {forbidden_values}",
                "type": "value_forbidden"
            })

        # カスタムバリデーター
        custom_validator = field_rule.get("custom_validator")
        if custom_validator and custom_validator in self.custom_validators:
            try:
                custom_result = self.custom_validators[custom_validator](value)
                if not custom_result:
                    result["valid"] = False
                    result["errors"].append({
                        "field": field_name,
                        "error": f"Custom validation failed for '{custom_validator}'",
                        "type": "custom_validation"
                    })
            except Exception as e:
                result["warnings"].append({
                    "field": field_name,
                    "warning": f"Custom validator error: {e}",
                    "type": "validator_error"
                })

        return result

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """データ型をチェック"""
        type_map = {
            "string": str,
            "integer": int,
            "float": float,
            "boolean": bool,
            "list": list,
            "dict": dict,
            "number": (int, float)
        }

        expected_python_type = type_map.get(expected_type.lower())
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True

    def _merge_validation_results(self, main_result: Dict[str, Any],
                                 item_result: Dict[str, Any]):
        """検証結果をマージ"""
        if not item_result["valid"]:
            main_result["valid"] = False

        main_result["errors"].extend(item_result["errors"])
        main_result["warnings"].extend(item_result["warnings"])

        # サマリーを更新
        for key in main_result["summary"]:
            main_result["summary"][key] += item_result["summary"][key]

    async def _validate_schema(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """JSONスキーマに基づいてデータを検証"""
        try:
            try:
                import jsonschema

                # JSONスキーマ検証
                jsonschema.validate(data, schema)

                return {
                    "success": True,
                    "valid": True,
                    "message": "Data is valid according to schema"
                }

            except ImportError:
                # jsonschemaライブラリが利用できない場合は簡易検証
                return await self._simple_schema_validation(data, schema)

            except jsonschema.ValidationError as e:
                return {
                    "success": True,
                    "valid": False,
                    "error": str(e),
                    "error_path": list(e.path) if hasattr(e, 'path') else [],
                    "schema_path": list(e.schema_path) if hasattr(e, 'schema_path') else []
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Schema validation failed: {e}"
            }

    async def _simple_schema_validation(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """簡易スキーマ検証"""
        errors = []

        # 型チェック
        if "type" in schema:
            expected_type = schema["type"]
            if expected_type == "object" and not isinstance(data, dict):
                errors.append("Expected object, got " + type(data).__name__)
            elif expected_type == "array" and not isinstance(data, list):
                errors.append("Expected array, got " + type(data).__name__)
            elif expected_type == "string" and not isinstance(data, str):
                errors.append("Expected string, got " + type(data).__name__)
            elif expected_type == "number" and not isinstance(data, (int, float)):
                errors.append("Expected number, got " + type(data).__name__)

        # プロパティチェック（オブジェクトの場合）
        if isinstance(data, dict) and "properties" in schema:
            properties = schema["properties"]
            required = schema.get("required", [])

            # 必須プロパティチェック
            for req_prop in required:
                if req_prop not in data:
                    errors.append(f"Required property '{req_prop}' is missing")

            # 各プロパティの検証
            for prop_name, prop_schema in properties.items():
                if prop_name in data:
                    prop_result = await self._simple_schema_validation(data[prop_name], prop_schema)
                    if not prop_result["valid"]:
                        errors.extend([f"{prop_name}: {err}" for err in prop_result.get("errors", [])])

        return {
            "success": True,
            "valid": len(errors) == 0,
            "errors": errors
        }

    async def _check_data_quality(self, data: List[Dict[str, Any]],
                                 quality_checks: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """データ品質をチェック"""
        try:
            if quality_checks is None:
                quality_checks = {
                    "completeness": True,
                    "uniqueness": True,
                    "consistency": True,
                    "validity": True
                }

            quality_results = {
                "overall_score": 0,
                "checks": {},
                "issues": [],
                "recommendations": []
            }

            total_records = len(data)

            # 完全性チェック
            if quality_checks.get("completeness", False):
                completeness_result = await self._check_completeness(data)
                quality_results["checks"]["completeness"] = completeness_result

            # 一意性チェック
            if quality_checks.get("uniqueness", False):
                uniqueness_result = await self._check_uniqueness(data)
                quality_results["checks"]["uniqueness"] = uniqueness_result

            # 一貫性チェック
            if quality_checks.get("consistency", False):
                consistency_result = await self._check_consistency(data)
                quality_results["checks"]["consistency"] = consistency_result

            # 妥当性チェック
            if quality_checks.get("validity", False):
                validity_result = await self._check_validity(data)
                quality_results["checks"]["validity"] = validity_result

            # 全体スコア計算
            scores = [check["score"] for check in quality_results["checks"].values()]
            quality_results["overall_score"] = sum(scores) / len(scores) if scores else 0

            # 問題と推奨事項を集約
            for check_name, check_result in quality_results["checks"].items():
                quality_results["issues"].extend(check_result.get("issues", []))
                quality_results["recommendations"].extend(check_result.get("recommendations", []))

            return {
                "success": True,
                "total_records": total_records,
                "quality_results": quality_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Data quality check failed: {e}"
            }

    async def _check_completeness(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """データの完全性をチェック"""
        if not data:
            return {"score": 0, "issues": ["No data provided"], "recommendations": []}

        all_fields = set()
        for record in data:
            all_fields.update(record.keys())

        field_completeness = {}
        total_records = len(data)

        for field in all_fields:
            non_null_count = sum(1 for record in data if record.get(field) is not None and record.get(field) != "")
            completeness_rate = non_null_count / total_records
            field_completeness[field] = {
                "completeness_rate": completeness_rate,
                "missing_count": total_records - non_null_count
            }

        # 全体の完全性スコア
        overall_completeness = sum(fc["completeness_rate"] for fc in field_completeness.values()) / len(field_completeness)

        # 問題の特定
        issues = []
        recommendations = []

        for field, stats in field_completeness.items():
            if stats["completeness_rate"] < 0.9:
                issues.append(f"Field '{field}' has low completeness: {stats['completeness_rate']:.2%}")
                recommendations.append(f"Improve data collection for field '{field}'")

        return {
            "score": overall_completeness * 100,
            "field_completeness": field_completeness,
            "overall_completeness": overall_completeness,
            "issues": issues,
            "recommendations": recommendations
        }

    async def _check_uniqueness(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """データの一意性をチェック"""
        if not data:
            return {"score": 100, "issues": [], "recommendations": []}

        # 重複レコードの検出
        record_hashes = []
        duplicates = []

        for i, record in enumerate(data):
            record_str = json.dumps(record, sort_keys=True)
            if record_str in record_hashes:
                duplicates.append(i)
            else:
                record_hashes.append(record_str)

        duplicate_rate = len(duplicates) / len(data)
        uniqueness_score = (1 - duplicate_rate) * 100

        issues = []
        recommendations = []

        if duplicates:
            issues.append(f"Found {len(duplicates)} duplicate records ({duplicate_rate:.2%})")
            recommendations.append("Remove or merge duplicate records")

        return {
            "score": uniqueness_score,
            "duplicate_count": len(duplicates),
            "duplicate_rate": duplicate_rate,
            "duplicate_indices": duplicates,
            "issues": issues,
            "recommendations": recommendations
        }

    async def _check_consistency(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """データの一貫性をチェック"""
        if not data:
            return {"score": 100, "issues": [], "recommendations": []}

        consistency_issues = []

        # フィールドタイプの一貫性
        field_types = {}
        for record in data:
            for field, value in record.items():
                if field not in field_types:
                    field_types[field] = set()
                field_types[field].add(type(value).__name__)

        # 複数の型を持つフィールドを特定
        inconsistent_fields = {field: types for field, types in field_types.items() if len(types) > 1}

        for field, types in inconsistent_fields.items():
            consistency_issues.append(f"Field '{field}' has inconsistent types: {', '.join(types)}")

        # フォーマットの一貫性（例：日付、電話番号等）
        format_issues = await self._check_format_consistency(data)
        consistency_issues.extend(format_issues)

        consistency_score = max(0, 100 - len(consistency_issues) * 10)

        recommendations = []
        if inconsistent_fields:
            recommendations.append("Standardize data types for all fields")
        if format_issues:
            recommendations.append("Implement consistent formatting rules")

        return {
            "score": consistency_score,
            "inconsistent_fields": inconsistent_fields,
            "format_issues": format_issues,
            "issues": consistency_issues,
            "recommendations": recommendations
        }

    async def _check_format_consistency(self, data: List[Dict[str, Any]]) -> List[str]:
        """フォーマットの一貫性をチェック"""
        format_issues = []

        # 日付フィールドの検出と一貫性チェック
        date_patterns = {}

        for record in data:
            for field, value in record.items():
                if isinstance(value, str) and self._looks_like_date(value):
                    if field not in date_patterns:
                        date_patterns[field] = set()
                    date_patterns[field].add(self._get_date_pattern(value))

        for field, patterns in date_patterns.items():
            if len(patterns) > 1:
                format_issues.append(f"Field '{field}' has inconsistent date formats: {', '.join(patterns)}")

        return format_issues

    def _looks_like_date(self, value: str) -> bool:
        """文字列が日付のように見えるかチェック"""
        date_indicators = ['-', '/', ':', 'T', 'Z']
        return any(indicator in value for indicator in date_indicators) and any(c.isdigit() for c in value)

    def _get_date_pattern(self, date_str: str) -> str:
        """日付文字列のパターンを取得"""
        # 簡易的なパターン検出
        if 'T' in date_str:
            return "ISO format"
        elif '/' in date_str:
            return "MM/DD/YYYY or DD/MM/YYYY"
        elif '-' in date_str:
            return "YYYY-MM-DD"
        else:
            return "Unknown format"

    async def _check_validity(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """データの妥当性をチェック"""
        if not data:
            return {"score": 100, "issues": [], "recommendations": []}

        validity_issues = []

        # 基本的な妥当性チェック
        for i, record in enumerate(data):
            for field, value in record.items():
                # 空文字列チェック
                if isinstance(value, str) and value.strip() == "":
                    validity_issues.append(f"Record {i}: Field '{field}' contains empty string")

                # 負の値チェック（年齢、価格等で不適切な場合）
                if isinstance(value, (int, float)) and value < 0:
                    if field.lower() in ['age', 'price', 'amount', 'quantity', 'count']:
                        validity_issues.append(f"Record {i}: Field '{field}' has negative value: {value}")

                # 異常に大きな値チェック
                if isinstance(value, (int, float)) and abs(value) > 1e10:
                    validity_issues.append(f"Record {i}: Field '{field}' has unusually large value: {value}")

        validity_score = max(0, 100 - len(validity_issues) * 2)

        recommendations = []
        if validity_issues:
            recommendations.append("Review and clean invalid data values")
            recommendations.append("Implement data validation at input stage")

        return {
            "score": validity_score,
            "invalid_count": len(validity_issues),
            "issues": validity_issues[:10],  # 最初の10個のみ表示
            "recommendations": recommendations
        }

    async def _detect_anomalies(self, data: List[Union[Dict[str, Any], float, int]],
                               method: str = "statistical",
                               threshold: float = 2.0) -> Dict[str, Any]:
        """異常値を検出"""
        try:
            if not data:
                return {
                    "success": False,
                    "error": "No data provided for anomaly detection"
                }

            anomalies = []

            if method == "statistical":
                anomalies = await self._statistical_anomaly_detection(data, threshold)
            elif method == "iqr":
                anomalies = await self._iqr_anomaly_detection(data)
            elif method == "isolation":
                anomalies = await self._isolation_anomaly_detection(data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown anomaly detection method: {method}"
                }

            return {
                "success": True,
                "method": method,
                "threshold": threshold,
                "total_records": len(data),
                "anomaly_count": len(anomalies),
                "anomaly_rate": len(anomalies) / len(data),
                "anomalies": anomalies
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Anomaly detection failed: {e}"
            }

    async def _statistical_anomaly_detection(self, data: List[Union[Dict, float, int]],
                                           threshold: float) -> List[Dict[str, Any]]:
        """統計的手法による異常値検出"""
        anomalies = []

        # 数値データの場合
        if all(isinstance(x, (int, float)) for x in data):
            mean_val = statistics.mean(data)
            std_val = statistics.stdev(data) if len(data) > 1 else 0

            for i, value in enumerate(data):
                if std_val > 0:
                    z_score = abs(value - mean_val) / std_val
                    if z_score > threshold:
                        anomalies.append({
                            "index": i,
                            "value": value,
                            "z_score": z_score,
                            "type": "statistical_outlier"
                        })

        # 辞書データの場合
        elif all(isinstance(x, dict) for x in data):
            # 各数値フィールドについて異常値検出
            numeric_fields = set()
            for record in data:
                for field, value in record.items():
                    if isinstance(value, (int, float)):
                        numeric_fields.add(field)

            for field in numeric_fields:
                field_values = [record.get(field) for record in data if isinstance(record.get(field), (int, float))]

                if len(field_values) > 1:
                    mean_val = statistics.mean(field_values)
                    std_val = statistics.stdev(field_values)

                    for i, record in enumerate(data):
                        value = record.get(field)
                        if isinstance(value, (int, float)) and std_val > 0:
                            z_score = abs(value - mean_val) / std_val
                            if z_score > threshold:
                                anomalies.append({
                                    "index": i,
                                    "field": field,
                                    "value": value,
                                    "z_score": z_score,
                                    "type": "field_outlier"
                                })

        return anomalies

    async def _iqr_anomaly_detection(self, data: List[Union[Dict, float, int]]) -> List[Dict[str, Any]]:
        """IQR（四分位範囲）による異常値検出"""
        anomalies = []

        # 数値データの場合
        if all(isinstance(x, (int, float)) for x in data):
            sorted_data = sorted(data)
            n = len(sorted_data)

            q1 = sorted_data[n // 4]
            q3 = sorted_data[3 * n // 4]
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            for i, value in enumerate(data):
                if value < lower_bound or value > upper_bound:
                    anomalies.append({
                        "index": i,
                        "value": value,
                        "lower_bound": lower_bound,
                        "upper_bound": upper_bound,
                        "type": "iqr_outlier"
                    })

        return anomalies

    async def _isolation_anomaly_detection(self, data: List[Union[Dict, float, int]]) -> List[Dict[str, Any]]:
        """簡易的な分離による異常値検出"""
        # 実装の簡略化のため、統計的手法を使用
        return await self._statistical_anomaly_detection(data, 2.5)

    async def _validate_format(self, data: Union[str, List[str]],
                              format_type: str,
                              custom_pattern: Optional[str] = None) -> Dict[str, Any]:
        """データフォーマットを検証"""
        try:
            format_patterns = {
                "email": r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                "phone": r'^\+?1?-?\.?\s?\(?(\d{3})\)?[\s.-]?(\d{3})[\s.-]?(\d{4})$',
                "url": r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$',
                "ipv4": r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
                "date_iso": r'^\d{4}-\d{2}-\d{2}$',
                "datetime_iso": r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$',
                "credit_card": r'^\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}$',
                "postal_code": r'^\d{5}(?:-\d{4})?$'
            }

            pattern = custom_pattern or format_patterns.get(format_type)

            if not pattern:
                return {
                    "success": False,
                    "error": f"Unknown format type: {format_type}"
                }

            if isinstance(data, str):
                data = [data]

            validation_results = []
            valid_count = 0

            for i, item in enumerate(data):
                is_valid = bool(re.match(pattern, str(item)))
                if is_valid:
                    valid_count += 1

                validation_results.append({
                    "index": i,
                    "value": item,
                    "valid": is_valid
                })

            return {
                "success": True,
                "format_type": format_type,
                "pattern": pattern,
                "total_items": len(data),
                "valid_items": valid_count,
                "invalid_items": len(data) - valid_count,
                "validity_rate": valid_count / len(data),
                "results": validation_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Format validation failed: {e}"
            }

    async def _check_constraints(self, data: List[Dict[str, Any]],
                                constraints: Dict[str, Any]) -> Dict[str, Any]:
        """データ制約をチェック"""
        try:
            constraint_violations = []

            for constraint_name, constraint_rule in constraints.items():
                constraint_type = constraint_rule.get("type")

                if constraint_type == "unique":
                    # 一意性制約
                    field = constraint_rule["field"]
                    values = [record.get(field) for record in data]
                    duplicates = [v for v in values if values.count(v) > 1]

                    if duplicates:
                        constraint_violations.append({
                            "constraint": constraint_name,
                            "type": "unique",
                            "field": field,
                            "violation": f"Duplicate values found: {set(duplicates)}"
                        })

                elif constraint_type == "foreign_key":
                    # 外部キー制約（簡易版）
                    field = constraint_rule["field"]
                    reference_values = constraint_rule["reference_values"]

                    for i, record in enumerate(data):
                        value = record.get(field)
                        if value is not None and value not in reference_values:
                            constraint_violations.append({
                                "constraint": constraint_name,
                                "type": "foreign_key",
                                "field": field,
                                "record_index": i,
                                "violation": f"Value '{value}' not found in reference"
                            })

                elif constraint_type == "check":
                    # チェック制約
                    condition = constraint_rule["condition"]

                    for i, record in enumerate(data):
                        if not self._evaluate_condition(record, condition):
                            constraint_violations.append({
                                "constraint": constraint_name,
                                "type": "check",
                                "record_index": i,
                                "violation": f"Check constraint failed: {condition}"
                            })

            return {
                "success": True,
                "total_records": len(data),
                "constraint_violations": len(constraint_violations),
                "violations": constraint_violations,
                "constraints_passed": len(constraints) - len(set(v["constraint"] for v in constraint_violations))
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Constraint checking failed: {e}"
            }

    def _evaluate_condition(self, record: Dict[str, Any], condition: str) -> bool:
        """条件式を評価（簡易版）"""
        try:
            # セキュリティ上の理由で制限された評価
            # 実際の実装では、より安全な式評価器を使用すべき

            # 基本的な比較演算子のサポート
            for field, value in record.items():
                condition = condition.replace(f"{{{field}}}", str(value))

            # 簡易的な評価（実際にはより安全な方法を使用）
            if ">" in condition or "<" in condition or "==" in condition:
                return eval(condition)

            return True

        except Exception:
            return False

    async def _validate_relationships(self, data: List[Dict[str, Any]],
                                    relationships: Dict[str, Any]) -> Dict[str, Any]:
        """データ間の関係性を検証"""
        try:
            relationship_violations = []

            for rel_name, rel_config in relationships.items():
                rel_type = rel_config.get("type")

                if rel_type == "one_to_many":
                    # 1対多の関係
                    parent_field = rel_config["parent_field"]
                    child_field = rel_config["child_field"]

                    parent_values = set(record.get(parent_field) for record in data)

                    for record in data:
                        child_value = record.get(child_field)
                        if child_value is not None and child_value not in parent_values:
                            relationship_violations.append({
                                "relationship": rel_name,
                                "type": "one_to_many",
                                "violation": f"Child value '{child_value}' has no parent"
                            })

                elif rel_type == "referential_integrity":
                    # 参照整合性
                    source_field = rel_config["source_field"]
                    target_field = rel_config["target_field"]

                    target_values = set(record.get(target_field) for record in data)

                    for record in data:
                        source_value = record.get(source_field)
                        if source_value is not None and source_value not in target_values:
                            relationship_violations.append({
                                "relationship": rel_name,
                                "type": "referential_integrity",
                                "violation": f"Reference '{source_value}' not found in target"
                            })

            return {
                "success": True,
                "total_relationships": len(relationships),
                "violations": relationship_violations,
                "violations_count": len(relationship_violations)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Relationship validation failed: {e}"
            }

    async def _create_validation_rule(self, rule_name: str,
                                     rule_definition: Dict[str, Any]) -> Dict[str, Any]:
        """カスタム検証ルールを作成"""
        try:
            self.validation_rules[rule_name] = rule_definition

            return {
                "success": True,
                "message": f"Validation rule '{rule_name}' created successfully",
                "rule_name": rule_name,
                "rule_definition": rule_definition
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create validation rule: {e}"
            }

    async def _batch_validate(self, datasets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """複数のデータセットを一括検証"""
        try:
            batch_results = []

            for i, dataset_config in enumerate(datasets):
                dataset_name = dataset_config.get("name", f"dataset_{i}")
                data = dataset_config["data"]
                validation_config = dataset_config.get("validation", {})

                # データセット検証を実行
                if "schema" in validation_config:
                    result = await self._validate_schema(data, validation_config["schema"])
                elif "rules" in validation_config:
                    result = await self._validate_data(data, validation_config["rules"])
                else:
                    result = await self._check_data_quality(data)

                batch_results.append({
                    "dataset_name": dataset_name,
                    "result": result
                })

            # 全体サマリー
            total_datasets = len(datasets)
            successful_validations = sum(1 for r in batch_results if r["result"].get("success", False))

            return {
                "success": True,
                "total_datasets": total_datasets,
                "successful_validations": successful_validations,
                "failed_validations": total_datasets - successful_validations,
                "batch_results": batch_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Batch validation failed: {e}"
            }

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """各コマンドのパラメータ定義を返す"""
        return {
            "validate_data": {
                "data": {"type": "any", "required": True, "description": "検証対象データ"},
                "validation_rules": {"type": "object", "required": True, "description": "検証ルール"},
                "strict_mode": {"type": "boolean", "required": False, "description": "厳密モード"}
            },
            "validate_schema": {
                "data": {"type": "any", "required": True, "description": "検証対象データ"},
                "schema": {"type": "object", "required": True, "description": "JSONスキーマ"}
            },
            "check_data_quality": {
                "data": {"type": "array", "required": True, "description": "データセット"},
                "quality_checks": {"type": "object", "required": False, "description": "品質チェック設定"}
            },
            "detect_anomalies": {
                "data": {"type": "array", "required": True, "description": "異常値検出対象データ"},
                "method": {"type": "string", "required": False, "description": "検出手法"},
                "threshold": {"type": "number", "required": False, "description": "閾値"}
            },
            "validate_format": {
                "data": {"type": "any", "required": True, "description": "フォーマット検証対象"},
                "format_type": {"type": "string", "required": True, "description": "フォーマットタイプ"},
                "custom_pattern": {"type": "string", "required": False, "description": "カスタムパターン"}
            },
            "check_constraints": {
                "data": {"type": "array", "required": True, "description": "制約チェック対象データ"},
                "constraints": {"type": "object", "required": True, "description": "制約定義"}
            },
            "validate_relationships": {
                "data": {"type": "array", "required": True, "description": "関係性検証対象データ"},
                "relationships": {"type": "object", "required": True, "description": "関係性定義"}
            },
            "create_validation_rule": {
                "rule_name": {"type": "string", "required": True, "description": "ルール名"},
                "rule_definition": {"type": "object", "required": True, "description": "ルール定義"}
            },
            "batch_validate": {
                "datasets": {"type": "array", "required": True, "description": "データセットリスト"}
            }
        }
