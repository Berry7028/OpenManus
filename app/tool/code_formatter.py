"""
Code Formatter Tool

コード整形・リファクタリングを行うツール
複数言語対応、コード品質チェック、自動修正、スタイルガイド適用などの機能を提供
"""

import asyncio
import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import tempfile
import subprocess

from .base import BaseTool

logger = logging.getLogger(__name__)

class CodeFormatter(BaseTool):
    """コード整形・リファクタリングツール"""

    def __init__(self):
        super().__init__()
        self.supported_languages = {
            'python': {
                'extensions': ['.py'],
                'formatters': ['black', 'autopep8', 'yapf'],
                'linters': ['flake8', 'pylint', 'mypy']
            },
            'javascript': {
                'extensions': ['.js', '.jsx'],
                'formatters': ['prettier', 'eslint'],
                'linters': ['eslint', 'jshint']
            },
            'typescript': {
                'extensions': ['.ts', '.tsx'],
                'formatters': ['prettier', 'tslint'],
                'linters': ['tslint', 'eslint']
            },
            'java': {
                'extensions': ['.java'],
                'formatters': ['google-java-format'],
                'linters': ['checkstyle', 'spotbugs']
            },
            'cpp': {
                'extensions': ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.h'],
                'formatters': ['clang-format'],
                'linters': ['cppcheck', 'clang-tidy']
            },
            'go': {
                'extensions': ['.go'],
                'formatters': ['gofmt', 'goimports'],
                'linters': ['golint', 'go vet']
            },
            'rust': {
                'extensions': ['.rs'],
                'formatters': ['rustfmt'],
                'linters': ['clippy']
            },
            'json': {
                'extensions': ['.json'],
                'formatters': ['jq', 'prettier'],
                'linters': ['jsonlint']
            },
            'yaml': {
                'extensions': ['.yml', '.yaml'],
                'formatters': ['prettier'],
                'linters': ['yamllint']
            },
            'xml': {
                'extensions': ['.xml'],
                'formatters': ['xmllint'],
                'linters': ['xmllint']
            }
        }

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        コード整形・リファクタリング操作を実行

        Args:
            command: 実行するコマンド
            **kwargs: コマンド固有のパラメータ

        Returns:
            実行結果
        """
        try:
            if command == "format_code":
                return await self._format_code(**kwargs)
            elif command == "lint_code":
                return await self._lint_code(**kwargs)
            elif command == "format_file":
                return await self._format_file(**kwargs)
            elif command == "format_directory":
                return await self._format_directory(**kwargs)
            elif command == "check_style":
                return await self._check_style(**kwargs)
            elif command == "fix_issues":
                return await self._fix_issues(**kwargs)
            elif command == "detect_language":
                return await self._detect_language(**kwargs)
            elif command == "validate_syntax":
                return await self._validate_syntax(**kwargs)
            elif command == "optimize_imports":
                return await self._optimize_imports(**kwargs)
            elif command == "remove_unused":
                return await self._remove_unused(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "format_code", "lint_code", "format_file", "format_directory",
                        "check_style", "fix_issues", "detect_language", "validate_syntax",
                        "optimize_imports", "remove_unused"
                    ]
                }

        except Exception as e:
            logger.error(f"Code formatting operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def _detect_language_from_content(self, content: str, file_path: Optional[str] = None) -> str:
        """コンテンツから言語を検出"""
        if file_path:
            ext = Path(file_path).suffix.lower()
            for lang, info in self.supported_languages.items():
                if ext in info['extensions']:
                    return lang

        # コンテンツベースの検出
        content_lower = content.lower().strip()

        # Python
        if any(keyword in content_lower for keyword in ['def ', 'import ', 'from ', 'class ', 'if __name__']):
            return 'python'

        # JavaScript/TypeScript
        if any(keyword in content_lower for keyword in ['function', 'var ', 'let ', 'const ', 'console.log']):
            if 'interface ' in content_lower or ': string' in content_lower:
                return 'typescript'
            return 'javascript'

        # Java
        if any(keyword in content_lower for keyword in ['public class', 'public static void main', 'import java']):
            return 'java'

        # C++
        if any(keyword in content_lower for keyword in ['#include', 'using namespace', 'int main()']):
            return 'cpp'

        # Go
        if any(keyword in content_lower for keyword in ['package main', 'func main()', 'import (']):
            return 'go'

        # Rust
        if any(keyword in content_lower for keyword in ['fn main()', 'use std::', 'let mut']):
            return 'rust'

        # JSON
        if content_lower.startswith('{') and content_lower.endswith('}'):
            try:
                json.loads(content)
                return 'json'
            except:
                pass

        # XML
        if content_lower.startswith('<?xml') or (content_lower.startswith('<') and content_lower.endswith('>')):
            return 'xml'

        # YAML
        if ':' in content and not content_lower.startswith('{'):
            return 'yaml'

        return 'unknown'

    async def _format_code(self, code: str, language: Optional[str] = None,
                          formatter: Optional[str] = None,
                          options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """コードを整形"""
        try:
            if language is None:
                language = self._detect_language_from_content(code)

            if language not in self.supported_languages:
                return {
                    "success": False,
                    "error": f"Unsupported language: {language}"
                }

            lang_info = self.supported_languages[language]

            # フォーマッターを選択
            if formatter is None:
                formatter = lang_info['formatters'][0] if lang_info['formatters'] else None

            if formatter is None:
                return {
                    "success": False,
                    "error": f"No formatter available for {language}"
                }

            # 一時ファイルに書き込み
            with tempfile.NamedTemporaryFile(mode='w', suffix=lang_info['extensions'][0], delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            try:
                formatted_code = await self._run_formatter(temp_file_path, language, formatter, options)

                # 変更の統計
                original_lines = code.split('\n')
                formatted_lines = formatted_code.split('\n')

                changes = {
                    "original_lines": len(original_lines),
                    "formatted_lines": len(formatted_lines),
                    "lines_changed": sum(1 for i, (orig, fmt) in enumerate(zip(original_lines, formatted_lines)) if orig != fmt),
                    "characters_original": len(code),
                    "characters_formatted": len(formatted_code)
                }

                return {
                    "success": True,
                    "original_code": code,
                    "formatted_code": formatted_code,
                    "language": language,
                    "formatter": formatter,
                    "changes": changes
                }

            finally:
                # 一時ファイルを削除
                os.unlink(temp_file_path)

        except Exception as e:
            return {
                "success": False,
                "error": f"Code formatting failed: {e}"
            }

    async def _run_formatter(self, file_path: str, language: str, formatter: str,
                           options: Optional[Dict[str, Any]] = None) -> str:
        """指定されたフォーマッターを実行"""
        options = options or {}

        if language == 'python':
            if formatter == 'black':
                cmd = ['black', '--quiet', '--code', open(file_path).read()]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode == 0:
                    return stdout.decode('utf-8')
                else:
                    # Fallback: 基本的なPython整形
                    return self._basic_python_format(open(file_path).read())

            elif formatter == 'autopep8':
                cmd = ['autopep8', '--aggressive', '--aggressive', file_path]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode == 0:
                    return stdout.decode('utf-8')

        elif language == 'javascript' or language == 'typescript':
            if formatter == 'prettier':
                cmd = ['prettier', '--parser', 'typescript' if language == 'typescript' else 'babel', file_path]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode == 0:
                    return stdout.decode('utf-8')

        elif language == 'json':
            # JSON整形（内蔵）
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return json.dumps(data, indent=2, ensure_ascii=False)
            except:
                pass

        elif language == 'go':
            if formatter == 'gofmt':
                cmd = ['gofmt', file_path]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                if process.returncode == 0:
                    return stdout.decode('utf-8')

        # フォーマッターが利用できない場合は基本的な整形を実行
        return self._basic_format(open(file_path).read(), language)

    def _basic_python_format(self, code: str) -> str:
        """基本的なPython整形"""
        lines = code.split('\n')
        formatted_lines = []
        indent_level = 0

        for line in lines:
            stripped = line.strip()

            if not stripped:
                formatted_lines.append('')
                continue

            # インデントレベルを調整
            if stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ')):
                formatted_lines.append('    ' * indent_level + stripped)
                if stripped.endswith(':'):
                    indent_level += 1
            elif stripped in ['else:', 'elif', 'except:', 'finally:']:
                indent_level = max(0, indent_level - 1)
                formatted_lines.append('    ' * indent_level + stripped)
                indent_level += 1
            elif stripped.startswith(('return', 'break', 'continue', 'pass', 'raise')):
                formatted_lines.append('    ' * indent_level + stripped)
            else:
                # 通常の行
                if line.startswith(' ') or line.startswith('\t'):
                    formatted_lines.append('    ' * indent_level + stripped)
                else:
                    indent_level = 0
                    formatted_lines.append(stripped)

        return '\n'.join(formatted_lines)

    def _basic_format(self, code: str, language: str) -> str:
        """基本的なコード整形"""
        lines = code.split('\n')
        formatted_lines = []

        for line in lines:
            stripped = line.strip()
            if stripped:
                formatted_lines.append(stripped)
            else:
                formatted_lines.append('')

        return '\n'.join(formatted_lines)

    async def _lint_code(self, code: str, language: Optional[str] = None,
                        linter: Optional[str] = None) -> Dict[str, Any]:
        """コードをリント"""
        try:
            if language is None:
                language = self._detect_language_from_content(code)

            if language not in self.supported_languages:
                return {
                    "success": False,
                    "error": f"Unsupported language: {language}"
                }

            lang_info = self.supported_languages[language]

            if linter is None:
                linter = lang_info['linters'][0] if lang_info['linters'] else None

            if linter is None:
                return {
                    "success": False,
                    "error": f"No linter available for {language}"
                }

            # 一時ファイルに書き込み
            with tempfile.NamedTemporaryFile(mode='w', suffix=lang_info['extensions'][0], delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name

            try:
                lint_results = await self._run_linter(temp_file_path, language, linter)

                return {
                    "success": True,
                    "language": language,
                    "linter": linter,
                    "lint_results": lint_results
                }

            finally:
                os.unlink(temp_file_path)

        except Exception as e:
            return {
                "success": False,
                "error": f"Code linting failed: {e}"
            }

    async def _run_linter(self, file_path: str, language: str, linter: str) -> Dict[str, Any]:
        """指定されたリンターを実行"""
        lint_results = {
            "issues": [],
            "warnings": 0,
            "errors": 0,
            "info": 0
        }

        try:
            if language == 'python' and linter == 'flake8':
                cmd = ['flake8', '--format=json', file_path]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if stdout:
                    try:
                        issues = json.loads(stdout.decode('utf-8'))
                        for issue in issues:
                            lint_results["issues"].append({
                                "line": issue.get("line_number"),
                                "column": issue.get("column_number"),
                                "message": issue.get("text"),
                                "rule": issue.get("code"),
                                "severity": "warning"
                            })
                            lint_results["warnings"] += 1
                    except:
                        pass

            elif language == 'javascript' and linter == 'eslint':
                cmd = ['eslint', '--format=json', file_path]
                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()

                if stdout:
                    try:
                        results = json.loads(stdout.decode('utf-8'))
                        for file_result in results:
                            for message in file_result.get("messages", []):
                                severity = "error" if message.get("severity") == 2 else "warning"
                                lint_results["issues"].append({
                                    "line": message.get("line"),
                                    "column": message.get("column"),
                                    "message": message.get("message"),
                                    "rule": message.get("ruleId"),
                                    "severity": severity
                                })
                                if severity == "error":
                                    lint_results["errors"] += 1
                                else:
                                    lint_results["warnings"] += 1
                    except:
                        pass

            else:
                # 基本的な構文チェック
                lint_results = self._basic_syntax_check(open(file_path).read(), language)

        except Exception as e:
            lint_results["issues"].append({
                "line": 0,
                "column": 0,
                "message": f"Linter execution failed: {e}",
                "rule": "linter_error",
                "severity": "error"
            })
            lint_results["errors"] += 1

        return lint_results

    def _basic_syntax_check(self, code: str, language: str) -> Dict[str, Any]:
        """基本的な構文チェック"""
        issues = []
        warnings = 0
        errors = 0

        lines = code.split('\n')

        if language == 'python':
            # Python基本チェック
            for i, line in enumerate(lines, 1):
                stripped = line.strip()

                # インデントチェック
                if line.startswith('\t') and '    ' in line:
                    issues.append({
                        "line": i,
                        "column": 1,
                        "message": "Mixed tabs and spaces",
                        "rule": "mixed_indentation",
                        "severity": "warning"
                    })
                    warnings += 1

                # 長い行チェック
                if len(line) > 120:
                    issues.append({
                        "line": i,
                        "column": 120,
                        "message": "Line too long",
                        "rule": "line_length",
                        "severity": "warning"
                    })
                    warnings += 1

                # 未使用import（簡易）
                if stripped.startswith('import ') or stripped.startswith('from '):
                    module_name = stripped.split()[1].split('.')[0]
                    if module_name not in code[lines[i-1:]:]:
                        issues.append({
                            "line": i,
                            "column": 1,
                            "message": f"Unused import: {module_name}",
                            "rule": "unused_import",
                            "severity": "info"
                        })

        elif language == 'javascript' or language == 'typescript':
            # JavaScript/TypeScript基本チェック
            for i, line in enumerate(lines, 1):
                stripped = line.strip()

                # セミコロンチェック
                if stripped and not stripped.endswith((';', '{', '}', ')', ']')) and not stripped.startswith(('if', 'for', 'while', 'function', 'class')):
                    if any(keyword in stripped for keyword in ['var ', 'let ', 'const ', 'return']):
                        issues.append({
                            "line": i,
                            "column": len(line),
                            "message": "Missing semicolon",
                            "rule": "missing_semicolon",
                            "severity": "warning"
                        })
                        warnings += 1

        return {
            "issues": issues,
            "warnings": warnings,
            "errors": errors,
            "info": len([i for i in issues if i["severity"] == "info"])
        }

    async def _format_file(self, file_path: str, formatter: Optional[str] = None,
                          backup: bool = True) -> Dict[str, Any]:
        """ファイルを整形"""
        try:
            file_obj = Path(file_path)

            if not file_obj.exists():
                return {
                    "success": False,
                    "error": f"File does not exist: {file_path}"
                }

            # 言語を検出
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            language = self._detect_language_from_content(content, file_path)

            # バックアップ作成
            if backup:
                backup_path = f"{file_path}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(content)

            # コードを整形
            format_result = await self._format_code(content, language, formatter)

            if format_result["success"]:
                # 整形されたコードをファイルに書き込み
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(format_result["formatted_code"])

                return {
                    "success": True,
                    "file_path": file_path,
                    "language": language,
                    "formatter": format_result["formatter"],
                    "changes": format_result["changes"],
                    "backup_created": backup,
                    "backup_path": backup_path if backup else None
                }
            else:
                return format_result

        except Exception as e:
            return {
                "success": False,
                "error": f"File formatting failed: {e}"
            }

    async def _format_directory(self, directory_path: str,
                               file_patterns: Optional[List[str]] = None,
                               recursive: bool = True,
                               formatter: Optional[str] = None) -> Dict[str, Any]:
        """ディレクトリ内のファイルを一括整形"""
        try:
            dir_obj = Path(directory_path)

            if not dir_obj.exists() or not dir_obj.is_dir():
                return {
                    "success": False,
                    "error": f"Directory does not exist: {directory_path}"
                }

            if file_patterns is None:
                file_patterns = ['*.py', '*.js', '*.ts', '*.java', '*.cpp', '*.go', '*.rs']

            # ファイルを収集
            files_to_format = []

            if recursive:
                for pattern in file_patterns:
                    files_to_format.extend(dir_obj.rglob(pattern))
            else:
                for pattern in file_patterns:
                    files_to_format.extend(dir_obj.glob(pattern))

            # 重複を除去
            files_to_format = list(set(files_to_format))

            format_results = {
                "directory": directory_path,
                "total_files": len(files_to_format),
                "successful_files": 0,
                "failed_files": 0,
                "file_results": []
            }

            # 各ファイルを整形
            for file_path in files_to_format:
                try:
                    result = await self._format_file(str(file_path), formatter, backup=True)

                    if result["success"]:
                        format_results["successful_files"] += 1
                    else:
                        format_results["failed_files"] += 1

                    format_results["file_results"].append({
                        "file": str(file_path),
                        "success": result["success"],
                        "error": result.get("error"),
                        "changes": result.get("changes")
                    })

                except Exception as e:
                    format_results["failed_files"] += 1
                    format_results["file_results"].append({
                        "file": str(file_path),
                        "success": False,
                        "error": str(e)
                    })

            return {
                "success": True,
                "directory_format_results": format_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Directory formatting failed: {e}"
            }

    async def _check_style(self, code: str, language: Optional[str] = None,
                          style_guide: str = "default") -> Dict[str, Any]:
        """コードスタイルをチェック"""
        try:
            if language is None:
                language = self._detect_language_from_content(code)

            style_issues = []

            lines = code.split('\n')

            # 共通スタイルチェック
            for i, line in enumerate(lines, 1):
                # 行末の空白
                if line.endswith(' ') or line.endswith('\t'):
                    style_issues.append({
                        "line": i,
                        "column": len(line),
                        "message": "Trailing whitespace",
                        "rule": "trailing_whitespace",
                        "severity": "warning"
                    })

                # 長い行
                max_length = 120 if language == 'python' else 100
                if len(line) > max_length:
                    style_issues.append({
                        "line": i,
                        "column": max_length,
                        "message": f"Line too long ({len(line)} > {max_length})",
                        "rule": "line_length",
                        "severity": "warning"
                    })

            # 言語固有のスタイルチェック
            if language == 'python':
                style_issues.extend(self._check_python_style(lines))
            elif language in ['javascript', 'typescript']:
                style_issues.extend(self._check_js_style(lines))

            return {
                "success": True,
                "language": language,
                "style_guide": style_guide,
                "total_issues": len(style_issues),
                "issues": style_issues
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Style check failed: {e}"
            }

    def _check_python_style(self, lines: List[str]) -> List[Dict[str, Any]]:
        """Pythonスタイルチェック"""
        issues = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # PEP 8チェック
            if '==' in line and ('True' in line or 'False' in line):
                issues.append({
                    "line": i,
                    "column": line.find('=='),
                    "message": "Use 'is' for boolean comparison",
                    "rule": "boolean_comparison",
                    "severity": "warning"
                })

            # インポートスタイル
            if stripped.startswith('from ') and ' import *' in stripped:
                issues.append({
                    "line": i,
                    "column": 1,
                    "message": "Avoid wildcard imports",
                    "rule": "wildcard_import",
                    "severity": "warning"
                })

        return issues

    def _check_js_style(self, lines: List[str]) -> List[Dict[str, Any]]:
        """JavaScript/TypeScriptスタイルチェック"""
        issues = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            # var使用チェック
            if 'var ' in stripped:
                issues.append({
                    "line": i,
                    "column": line.find('var'),
                    "message": "Use 'let' or 'const' instead of 'var'",
                    "rule": "no_var",
                    "severity": "warning"
                })

            # == vs ===
            if '==' in stripped and '===' not in stripped:
                issues.append({
                    "line": i,
                    "column": line.find('=='),
                    "message": "Use '===' instead of '=='",
                    "rule": "strict_equality",
                    "severity": "warning"
                })

        return issues

    async def _fix_issues(self, code: str, language: Optional[str] = None,
                         fix_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """コードの問題を自動修正"""
        try:
            if language is None:
                language = self._detect_language_from_content(code)

            if fix_types is None:
                fix_types = ["trailing_whitespace", "line_endings", "indentation"]

            fixed_code = code
            fixes_applied = []

            # 行末空白の除去
            if "trailing_whitespace" in fix_types:
                lines = fixed_code.split('\n')
                new_lines = [line.rstrip() for line in lines]
                if new_lines != lines:
                    fixed_code = '\n'.join(new_lines)
                    fixes_applied.append("trailing_whitespace")

            # 行末の統一
            if "line_endings" in fix_types:
                if '\r\n' in fixed_code:
                    fixed_code = fixed_code.replace('\r\n', '\n')
                    fixes_applied.append("line_endings")

            # インデントの統一（言語固有）
            if "indentation" in fix_types:
                if language == 'python':
                    fixed_code = self._fix_python_indentation(fixed_code)
                    fixes_applied.append("indentation")

            return {
                "success": True,
                "original_code": code,
                "fixed_code": fixed_code,
                "language": language,
                "fixes_applied": fixes_applied,
                "changes_made": len(fixes_applied) > 0
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Issue fixing failed: {e}"
            }

    def _fix_python_indentation(self, code: str) -> str:
        """Pythonのインデントを修正"""
        lines = code.split('\n')
        fixed_lines = []

        for line in lines:
            if line.strip():
                # タブをスペースに変換
                fixed_line = line.expandtabs(4)
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append('')

        return '\n'.join(fixed_lines)

    async def _detect_language(self, file_path: str) -> Dict[str, Any]:
        """ファイルの言語を検出"""
        try:
            file_obj = Path(file_path)

            if not file_obj.exists():
                return {
                    "success": False,
                    "error": f"File does not exist: {file_path}"
                }

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            language = self._detect_language_from_content(content, file_path)

            return {
                "success": True,
                "file_path": file_path,
                "detected_language": language,
                "confidence": "high" if language != "unknown" else "low",
                "supported": language in self.supported_languages
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Language detection failed: {e}"
            }

    async def _validate_syntax(self, code: str, language: Optional[str] = None) -> Dict[str, Any]:
        """構文の妥当性を検証"""
        try:
            if language is None:
                language = self._detect_language_from_content(code)

            validation_result = {
                "language": language,
                "valid": True,
                "errors": [],
                "warnings": []
            }

            if language == 'python':
                try:
                    compile(code, '<string>', 'exec')
                except SyntaxError as e:
                    validation_result["valid"] = False
                    validation_result["errors"].append({
                        "line": e.lineno,
                        "column": e.offset,
                        "message": e.msg,
                        "type": "SyntaxError"
                    })

            elif language == 'json':
                try:
                    json.loads(code)
                except json.JSONDecodeError as e:
                    validation_result["valid"] = False
                    validation_result["errors"].append({
                        "line": e.lineno,
                        "column": e.colno,
                        "message": e.msg,
                        "type": "JSONDecodeError"
                    })

            return {
                "success": True,
                "syntax_validation": validation_result
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Syntax validation failed: {e}"
            }

    async def _optimize_imports(self, code: str, language: Optional[str] = None) -> Dict[str, Any]:
        """インポート文を最適化"""
        try:
            if language is None:
                language = self._detect_language_from_content(code)

            if language != 'python':
                return {
                    "success": False,
                    "error": f"Import optimization not supported for {language}"
                }

            lines = code.split('\n')
            import_lines = []
            other_lines = []

            # インポート文を分離
            for line in lines:
                stripped = line.strip()
                if stripped.startswith(('import ', 'from ')):
                    import_lines.append(line)
                else:
                    other_lines.append(line)

            # インポートをソート
            import_lines.sort()

            # 重複を除去
            unique_imports = []
            seen = set()
            for imp in import_lines:
                if imp.strip() not in seen:
                    unique_imports.append(imp)
                    seen.add(imp.strip())

            # 再構築
            optimized_code = '\n'.join(unique_imports + [''] + other_lines)

            return {
                "success": True,
                "original_code": code,
                "optimized_code": optimized_code,
                "language": language,
                "imports_removed": len(import_lines) - len(unique_imports),
                "imports_sorted": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Import optimization failed: {e}"
            }

    async def _remove_unused(self, code: str, language: Optional[str] = None,
                           remove_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """未使用要素を除去"""
        try:
            if language is None:
                language = self._detect_language_from_content(code)

            if remove_types is None:
                remove_types = ["imports", "variables", "functions"]

            cleaned_code = code
            removed_items = []

            if language == 'python' and "imports" in remove_types:
                # 未使用インポートの除去（簡易版）
                lines = cleaned_code.split('\n')
                new_lines = []

                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith(('import ', 'from ')):
                        # インポートされたモジュール名を抽出
                        if stripped.startswith('import '):
                            module = stripped.split()[1].split('.')[0]
                        else:  # from ... import ...
                            parts = stripped.split()
                            if len(parts) >= 4:
                                module = parts[3]
                            else:
                                module = parts[1] if len(parts) > 1 else ""

                        # コード内で使用されているかチェック
                        if module and module in cleaned_code.replace(line, ''):
                            new_lines.append(line)
                        else:
                            removed_items.append(f"unused import: {stripped}")
                    else:
                        new_lines.append(line)

                cleaned_code = '\n'.join(new_lines)

            return {
                "success": True,
                "original_code": code,
                "cleaned_code": cleaned_code,
                "language": language,
                "removed_items": removed_items,
                "items_removed": len(removed_items)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Unused removal failed: {e}"
            }

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """各コマンドのパラメータ定義を返す"""
        return {
            "format_code": {
                "code": {"type": "string", "required": True, "description": "整形対象のコード"},
                "language": {"type": "string", "required": False, "description": "プログラミング言語（自動検出）"},
                "formatter": {"type": "string", "required": False, "description": "使用するフォーマッター"},
                "options": {"type": "object", "required": False, "description": "フォーマッターオプション"}
            },
            "lint_code": {
                "code": {"type": "string", "required": True, "description": "リント対象のコード"},
                "language": {"type": "string", "required": False, "description": "プログラミング言語（自動検出）"},
                "linter": {"type": "string", "required": False, "description": "使用するリンター"}
            },
            "format_file": {
                "file_path": {"type": "string", "required": True, "description": "整形対象ファイルパス"},
                "formatter": {"type": "string", "required": False, "description": "使用するフォーマッター"},
                "backup": {"type": "boolean", "required": False, "description": "バックアップ作成"}
            },
            "format_directory": {
                "directory_path": {"type": "string", "required": True, "description": "整形対象ディレクトリパス"},
                "file_patterns": {"type": "array", "required": False, "description": "対象ファイルパターン"},
                "recursive": {"type": "boolean", "required": False, "description": "再帰的処理"},
                "formatter": {"type": "string", "required": False, "description": "使用するフォーマッター"}
            },
            "check_style": {
                "code": {"type": "string", "required": True, "description": "スタイルチェック対象コード"},
                "language": {"type": "string", "required": False, "description": "プログラミング言語"},
                "style_guide": {"type": "string", "required": False, "description": "スタイルガイド"}
            },
            "fix_issues": {
                "code": {"type": "string", "required": True, "description": "修正対象コード"},
                "language": {"type": "string", "required": False, "description": "プログラミング言語"},
                "fix_types": {"type": "array", "required": False, "description": "修正タイプリスト"}
            },
            "detect_language": {
                "file_path": {"type": "string", "required": True, "description": "言語検出対象ファイルパス"}
            },
            "validate_syntax": {
                "code": {"type": "string", "required": True, "description": "構文検証対象コード"},
                "language": {"type": "string", "required": False, "description": "プログラミング言語"}
            },
            "optimize_imports": {
                "code": {"type": "string", "required": True, "description": "インポート最適化対象コード"},
                "language": {"type": "string", "required": False, "description": "プログラミング言語"}
            },
            "remove_unused": {
                "code": {"type": "string", "required": True, "description": "未使用要素除去対象コード"},
                "language": {"type": "string", "required": False, "description": "プログラミング言語"},
                "remove_types": {"type": "array", "required": False, "description": "除去対象タイプリスト"}
            }
        }
