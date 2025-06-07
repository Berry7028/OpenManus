"""
Document Generator Tool

ドキュメント自動生成を行うツール
テンプレート処理、複数フォーマット出力、API仕様書生成、README生成などの機能を提供
"""

import asyncio
import os
import json
import yaml
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import tempfile
import re

from .base import BaseTool

logger = logging.getLogger(__name__)

class DocumentGenerator(BaseTool):
    """ドキュメント自動生成ツール"""

    def __init__(self):
        super().__init__()
        self.supported_formats = ['markdown', 'html', 'pdf', 'docx', 'txt', 'rst']
        self.template_variables = {}

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        ドキュメント生成操作を実行

        Args:
            command: 実行するコマンド
            **kwargs: コマンド固有のパラメータ

        Returns:
            実行結果
        """
        try:
            if command == "generate_readme":
                return await self._generate_readme(**kwargs)
            elif command == "generate_api_docs":
                return await self._generate_api_docs(**kwargs)
            elif command == "create_template":
                return await self._create_template(**kwargs)
            elif command == "render_template":
                return await self._render_template(**kwargs)
            elif command == "convert_format":
                return await self._convert_format(**kwargs)
            elif command == "generate_changelog":
                return await self._generate_changelog(**kwargs)
            elif command == "create_user_manual":
                return await self._create_user_manual(**kwargs)
            elif command == "generate_code_docs":
                return await self._generate_code_docs(**kwargs)
            elif command == "create_presentation":
                return await self._create_presentation(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "generate_readme", "generate_api_docs", "create_template",
                        "render_template", "convert_format", "generate_changelog",
                        "create_user_manual", "generate_code_docs", "create_presentation"
                    ]
                }

        except Exception as e:
            logger.error(f"Document generation operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    async def _generate_readme(self, project_name: str, description: str,
                              features: Optional[List[str]] = None,
                              installation_steps: Optional[List[str]] = None,
                              usage_examples: Optional[List[str]] = None,
                              output_path: str = "README.md") -> Dict[str, Any]:
        """README.mdを生成"""
        try:
            features = features or []
            installation_steps = installation_steps or []
            usage_examples = usage_examples or []

            readme_content = f"""# {project_name}

{description}

## Features

"""

            if features:
                for feature in features:
                    readme_content += f"- {feature}\n"
            else:
                readme_content += "- Feature 1\n- Feature 2\n- Feature 3\n"

            readme_content += """
## Installation

"""

            if installation_steps:
                for i, step in enumerate(installation_steps, 1):
                    readme_content += f"{i}. {step}\n"
            else:
                readme_content += """1. Clone the repository
2. Install dependencies
3. Run the application
"""

            readme_content += """
## Usage

"""

            if usage_examples:
                for example in usage_examples:
                    readme_content += f"```\n{example}\n```\n\n"
            else:
                readme_content += """```bash
# Basic usage example
python main.py
```

## Configuration

Describe configuration options here.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
"""

            # ファイルに書き込み
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)

            return {
                "success": True,
                "message": f"README generated successfully: {output_path}",
                "output_path": output_path,
                "content_length": len(readme_content),
                "sections": ["Features", "Installation", "Usage", "Configuration", "Contributing", "License"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"README generation failed: {e}"
            }

    async def _generate_api_docs(self, api_spec: Dict[str, Any],
                                output_format: str = "markdown",
                                output_path: str = "api_docs.md") -> Dict[str, Any]:
        """API仕様書を生成"""
        try:
            if output_format not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"Unsupported output format: {output_format}"
                }

            # API仕様から文書を生成
            if output_format == "markdown":
                content = await self._generate_markdown_api_docs(api_spec)
            elif output_format == "html":
                content = await self._generate_html_api_docs(api_spec)
            else:
                content = await self._generate_text_api_docs(api_spec)

            # ファイルに書き込み
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "message": f"API documentation generated: {output_path}",
                "output_path": output_path,
                "format": output_format,
                "content_length": len(content),
                "endpoints_documented": len(api_spec.get("endpoints", []))
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"API documentation generation failed: {e}"
            }

    async def _generate_markdown_api_docs(self, api_spec: Dict[str, Any]) -> str:
        """Markdown形式のAPI文書を生成"""
        content = f"""# {api_spec.get('title', 'API Documentation')}

{api_spec.get('description', 'API documentation for this service.')}

## Base URL

```
{api_spec.get('base_url', 'https://api.example.com')}
```

## Authentication

{api_spec.get('authentication', 'Authentication details not provided.')}

## Endpoints

"""

        for endpoint in api_spec.get('endpoints', []):
            content += f"""### {endpoint.get('method', 'GET').upper()} {endpoint.get('path', '/')}

{endpoint.get('description', 'No description provided.')}

#### Parameters

"""

            parameters = endpoint.get('parameters', [])
            if parameters:
                content += "| Name | Type | Required | Description |\n"
                content += "|------|------|----------|-------------|\n"
                for param in parameters:
                    required = "Yes" if param.get('required', False) else "No"
                    content += f"| {param.get('name', '')} | {param.get('type', '')} | {required} | {param.get('description', '')} |\n"
            else:
                content += "No parameters required.\n"

            content += "\n#### Response\n\n"

            response = endpoint.get('response', {})
            if response:
                content += f"**Status Code:** {response.get('status_code', 200)}\n\n"
                content += "```json\n"
                content += json.dumps(response.get('example', {}), indent=2)
                content += "\n```\n\n"
            else:
                content += "Response format not documented.\n\n"

            content += "---\n\n"

        return content

    async def _generate_html_api_docs(self, api_spec: Dict[str, Any]) -> str:
        """HTML形式のAPI文書を生成"""
        content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{api_spec.get('title', 'API Documentation')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 4px; }}
        .endpoint {{ margin: 30px 0; padding: 20px; border: 1px solid #eee; border-radius: 8px; }}
    </style>
</head>
<body>
    <h1>{api_spec.get('title', 'API Documentation')}</h1>
    <p>{api_spec.get('description', 'API documentation for this service.')}</p>

    <h2>Base URL</h2>
    <pre>{api_spec.get('base_url', 'https://api.example.com')}</pre>

    <h2>Authentication</h2>
    <p>{api_spec.get('authentication', 'Authentication details not provided.')}</p>

    <h2>Endpoints</h2>
"""

        for endpoint in api_spec.get('endpoints', []):
            content += f"""
    <div class="endpoint">
        <h3>{endpoint.get('method', 'GET').upper()} {endpoint.get('path', '/')}</h3>
        <p>{endpoint.get('description', 'No description provided.')}</p>

        <h4>Parameters</h4>
"""

            parameters = endpoint.get('parameters', [])
            if parameters:
                content += """
        <table>
            <tr><th>Name</th><th>Type</th><th>Required</th><th>Description</th></tr>
"""
                for param in parameters:
                    required = "Yes" if param.get('required', False) else "No"
                    content += f"""
            <tr>
                <td>{param.get('name', '')}</td>
                <td>{param.get('type', '')}</td>
                <td>{required}</td>
                <td>{param.get('description', '')}</td>
            </tr>
"""
                content += "        </table>\n"
            else:
                content += "        <p>No parameters required.</p>\n"

            response = endpoint.get('response', {})
            if response:
                content += f"""
        <h4>Response</h4>
        <p><strong>Status Code:</strong> {response.get('status_code', 200)}</p>
        <pre>{json.dumps(response.get('example', {}), indent=2)}</pre>
"""

            content += "    </div>\n"

        content += """
</body>
</html>
"""

        return content

    async def _generate_text_api_docs(self, api_spec: Dict[str, Any]) -> str:
        """テキスト形式のAPI文書を生成"""
        content = f"""{api_spec.get('title', 'API Documentation')}
{'=' * len(api_spec.get('title', 'API Documentation'))}

{api_spec.get('description', 'API documentation for this service.')}

Base URL: {api_spec.get('base_url', 'https://api.example.com')}

Authentication: {api_spec.get('authentication', 'Authentication details not provided.')}

Endpoints:
----------

"""

        for endpoint in api_spec.get('endpoints', []):
            content += f"""{endpoint.get('method', 'GET').upper()} {endpoint.get('path', '/')}
{'-' * (len(endpoint.get('method', 'GET')) + len(endpoint.get('path', '/')) + 1)}

Description: {endpoint.get('description', 'No description provided.')}

Parameters:
"""

            parameters = endpoint.get('parameters', [])
            if parameters:
                for param in parameters:
                    required = "Required" if param.get('required', False) else "Optional"
                    content += f"  - {param.get('name', '')} ({param.get('type', '')}, {required}): {param.get('description', '')}\n"
            else:
                content += "  No parameters required.\n"

            response = endpoint.get('response', {})
            if response:
                content += f"\nResponse (Status {response.get('status_code', 200)}):\n"
                content += json.dumps(response.get('example', {}), indent=2)
                content += "\n"

            content += "\n" + "="*50 + "\n\n"

        return content

    async def _create_template(self, template_name: str, template_content: str,
                              variables: Optional[Dict[str, str]] = None,
                              output_path: Optional[str] = None) -> Dict[str, Any]:
        """ドキュメントテンプレートを作成"""
        try:
            variables = variables or {}

            if output_path is None:
                output_path = f"{template_name}.template"

            # テンプレート情報を含むメタデータ
            template_data = {
                "name": template_name,
                "created_at": datetime.now().isoformat(),
                "variables": variables,
                "content": template_content
            }

            # テンプレートファイルに保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("---\n")
                yaml.dump({k: v for k, v in template_data.items() if k != 'content'}, f)
                f.write("---\n")
                f.write(template_content)

            return {
                "success": True,
                "message": f"Template created: {output_path}",
                "template_name": template_name,
                "output_path": output_path,
                "variables": list(variables.keys()),
                "content_length": len(template_content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Template creation failed: {e}"
            }

    async def _render_template(self, template_path: str, variables: Dict[str, Any],
                              output_path: Optional[str] = None) -> Dict[str, Any]:
        """テンプレートを変数で置換してレンダリング"""
        try:
            # テンプレートファイルを読み込み
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # メタデータとコンテンツを分離
            if content.startswith('---\n'):
                parts = content.split('---\n', 2)
                if len(parts) >= 3:
                    template_content = parts[2]
                else:
                    template_content = content
            else:
                template_content = content

            # 変数を置換
            rendered_content = template_content
            for key, value in variables.items():
                # {{variable}} 形式の置換
                rendered_content = rendered_content.replace(f"{{{{{key}}}}}", str(value))
                # ${variable} 形式の置換
                rendered_content = rendered_content.replace(f"${{{key}}}", str(value))

            # 出力パスが指定されていない場合は生成
            if output_path is None:
                template_name = Path(template_path).stem
                output_path = f"{template_name}_rendered.md"

            # レンダリング結果を保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rendered_content)

            return {
                "success": True,
                "message": f"Template rendered: {output_path}",
                "template_path": template_path,
                "output_path": output_path,
                "variables_used": list(variables.keys()),
                "content_length": len(rendered_content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Template rendering failed: {e}"
            }

    async def _convert_format(self, input_path: str, output_format: str,
                             output_path: Optional[str] = None) -> Dict[str, Any]:
        """ドキュメントフォーマットを変換"""
        try:
            if output_format not in self.supported_formats:
                return {
                    "success": False,
                    "error": f"Unsupported output format: {output_format}"
                }

            # 入力ファイルを読み込み
            with open(input_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 入力フォーマットを検出
            input_format = self._detect_format(input_path, content)

            if output_path is None:
                base_name = Path(input_path).stem
                output_path = f"{base_name}.{output_format}"

            # フォーマット変換
            converted_content = await self._perform_format_conversion(
                content, input_format, output_format
            )

            # 変換結果を保存
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)

            return {
                "success": True,
                "message": f"Format converted: {input_path} -> {output_path}",
                "input_path": input_path,
                "output_path": output_path,
                "input_format": input_format,
                "output_format": output_format,
                "content_length": len(converted_content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Format conversion failed: {e}"
            }

    def _detect_format(self, file_path: str, content: str) -> str:
        """ファイルフォーマットを検出"""
        ext = Path(file_path).suffix.lower()

        format_map = {
            '.md': 'markdown',
            '.markdown': 'markdown',
            '.html': 'html',
            '.htm': 'html',
            '.txt': 'txt',
            '.rst': 'rst',
            '.pdf': 'pdf',
            '.docx': 'docx'
        }

        return format_map.get(ext, 'txt')

    async def _perform_format_conversion(self, content: str, input_format: str, output_format: str) -> str:
        """実際のフォーマット変換を実行"""
        if input_format == output_format:
            return content

        # Markdown to HTML
        if input_format == 'markdown' and output_format == 'html':
            return self._markdown_to_html(content)

        # HTML to Markdown (簡易版)
        elif input_format == 'html' and output_format == 'markdown':
            return self._html_to_markdown(content)

        # Markdown to Text
        elif input_format == 'markdown' and output_format == 'txt':
            return self._markdown_to_text(content)

        # Text to Markdown
        elif input_format == 'txt' and output_format == 'markdown':
            return self._text_to_markdown(content)

        # その他の変換は基本的にそのまま返す
        else:
            return content

    def _markdown_to_html(self, markdown_content: str) -> str:
        """MarkdownをHTMLに変換（簡易版）"""
        html = markdown_content

        # ヘッダー変換
        html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)

        # 太字・斜体
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

        # リンク
        html = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', html)

        # コードブロック
        html = re.sub(r'```(.+?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
        html = re.sub(r'`(.+?)`', r'<code>\1</code>', html)

        # 改行をHTMLに変換
        html = html.replace('\n\n', '</p><p>')
        html = f'<p>{html}</p>'

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Converted Document</title>
</head>
<body>
{html}
</body>
</html>"""

    def _html_to_markdown(self, html_content: str) -> str:
        """HTMLをMarkdownに変換（簡易版）"""
        markdown = html_content

        # HTMLタグを除去してMarkdownに変換
        markdown = re.sub(r'<h1.*?>(.*?)</h1>', r'# \1', markdown, flags=re.DOTALL)
        markdown = re.sub(r'<h2.*?>(.*?)</h2>', r'## \1', markdown, flags=re.DOTALL)
        markdown = re.sub(r'<h3.*?>(.*?)</h3>', r'### \1', markdown, flags=re.DOTALL)

        markdown = re.sub(r'<strong.*?>(.*?)</strong>', r'**\1**', markdown, flags=re.DOTALL)
        markdown = re.sub(r'<em.*?>(.*?)</em>', r'*\1*', markdown, flags=re.DOTALL)

        markdown = re.sub(r'<a.*?href="(.*?)".*?>(.*?)</a>', r'[\2](\1)', markdown, flags=re.DOTALL)

        markdown = re.sub(r'<code.*?>(.*?)</code>', r'`\1`', markdown, flags=re.DOTALL)
        markdown = re.sub(r'<pre.*?><code.*?>(.*?)</code></pre>', r'```\n\1\n```', markdown, flags=re.DOTALL)

        # その他のHTMLタグを除去
        markdown = re.sub(r'<[^>]+>', '', markdown)

        return markdown.strip()

    def _markdown_to_text(self, markdown_content: str) -> str:
        """Markdownをプレーンテキストに変換"""
        text = markdown_content

        # Markdownマークアップを除去
        text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # ヘッダー
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)  # 太字
        text = re.sub(r'\*(.+?)\*', r'\1', text)  # 斜体
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)  # リンク
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # コードブロック
        text = re.sub(r'`(.+?)`', r'\1', text)  # インラインコード
        text = re.sub(r'^[-*+]\s+', '', text, flags=re.MULTILINE)  # リスト

        return text.strip()

    def _text_to_markdown(self, text_content: str) -> str:
        """プレーンテキストをMarkdownに変換"""
        lines = text_content.split('\n')
        markdown_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                markdown_lines.append('')
                continue

            # 大文字のみの行をヘッダーとして扱う
            if stripped.isupper() and len(stripped) > 3:
                markdown_lines.append(f"# {stripped}")
            # 数字で始まる行をリストとして扱う
            elif re.match(r'^\d+\.', stripped):
                markdown_lines.append(stripped)
            # ハイフンで始まる行をリストとして扱う
            elif stripped.startswith('-'):
                markdown_lines.append(stripped)
            else:
                markdown_lines.append(stripped)

        return '\n'.join(markdown_lines)

    async def _generate_changelog(self, version_history: List[Dict[str, Any]],
                                 output_path: str = "CHANGELOG.md") -> Dict[str, Any]:
        """変更履歴を生成"""
        try:
            changelog_content = "# Changelog\n\n"
            changelog_content += "All notable changes to this project will be documented in this file.\n\n"

            for version_info in version_history:
                version = version_info.get('version', 'Unknown')
                date = version_info.get('date', datetime.now().strftime('%Y-%m-%d'))
                changes = version_info.get('changes', {})

                changelog_content += f"## [{version}] - {date}\n\n"

                for change_type, change_list in changes.items():
                    if change_list:
                        changelog_content += f"### {change_type.title()}\n\n"
                        for change in change_list:
                            changelog_content += f"- {change}\n"
                        changelog_content += "\n"

            # ファイルに書き込み
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(changelog_content)

            return {
                "success": True,
                "message": f"Changelog generated: {output_path}",
                "output_path": output_path,
                "versions_documented": len(version_history),
                "content_length": len(changelog_content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Changelog generation failed: {e}"
            }

    async def _create_user_manual(self, sections: List[Dict[str, Any]],
                                 title: str = "User Manual",
                                 output_path: str = "user_manual.md") -> Dict[str, Any]:
        """ユーザーマニュアルを作成"""
        try:
            manual_content = f"# {title}\n\n"
            manual_content += "## Table of Contents\n\n"

            # 目次を生成
            for i, section in enumerate(sections, 1):
                section_title = section.get('title', f'Section {i}')
                manual_content += f"{i}. [{section_title}](#{section_title.lower().replace(' ', '-')})\n"

            manual_content += "\n---\n\n"

            # セクション内容を生成
            for i, section in enumerate(sections, 1):
                section_title = section.get('title', f'Section {i}')
                section_content = section.get('content', 'Content not provided.')
                steps = section.get('steps', [])
                images = section.get('images', [])

                manual_content += f"## {i}. {section_title}\n\n"
                manual_content += f"{section_content}\n\n"

                if steps:
                    manual_content += "### Steps:\n\n"
                    for j, step in enumerate(steps, 1):
                        manual_content += f"{j}. {step}\n"
                    manual_content += "\n"

                if images:
                    manual_content += "### Screenshots:\n\n"
                    for image in images:
                        manual_content += f"![{image.get('alt', 'Screenshot')}]({image.get('url', '')})\n\n"

                manual_content += "---\n\n"

            # ファイルに書き込み
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(manual_content)

            return {
                "success": True,
                "message": f"User manual created: {output_path}",
                "output_path": output_path,
                "sections_count": len(sections),
                "content_length": len(manual_content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"User manual creation failed: {e}"
            }

    async def _generate_code_docs(self, source_directory: str,
                                 output_path: str = "code_documentation.md",
                                 include_private: bool = False) -> Dict[str, Any]:
        """ソースコードからドキュメントを生成"""
        try:
            source_dir = Path(source_directory)

            if not source_dir.exists() or not source_dir.is_dir():
                return {
                    "success": False,
                    "error": f"Source directory does not exist: {source_directory}"
                }

            docs_content = "# Code Documentation\n\n"
            docs_content += f"Generated from: {source_directory}\n\n"
            docs_content += "## Overview\n\n"

            documented_files = 0

            # Python ファイルを処理
            for py_file in source_dir.rglob('*.py'):
                if py_file.name.startswith('__') and not include_private:
                    continue

                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # ファイル情報を抽出
                    file_docs = self._extract_python_docs(content, py_file)
                    if file_docs:
                        docs_content += file_docs
                        documented_files += 1

                except Exception as e:
                    logger.warning(f"Failed to process {py_file}: {e}")

            # ファイルに書き込み
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(docs_content)

            return {
                "success": True,
                "message": f"Code documentation generated: {output_path}",
                "output_path": output_path,
                "source_directory": source_directory,
                "files_documented": documented_files,
                "content_length": len(docs_content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Code documentation generation failed: {e}"
            }

    def _extract_python_docs(self, content: str, file_path: Path) -> str:
        """Pythonファイルからドキュメントを抽出"""
        docs = f"## {file_path.name}\n\n"
        docs += f"**Path:** `{file_path}`\n\n"

        lines = content.split('\n')

        # モジュールdocstring
        if len(lines) > 0 and lines[0].strip().startswith('"""'):
            docstring_lines = []
            in_docstring = True
            for line in lines[1:]:
                if line.strip().endswith('"""'):
                    break
                docstring_lines.append(line)

            if docstring_lines:
                docs += "### Description\n\n"
                docs += '\n'.join(docstring_lines).strip() + "\n\n"

        # クラスと関数を抽出
        classes = re.findall(r'^class\s+(\w+).*?:', content, re.MULTILINE)
        functions = re.findall(r'^def\s+(\w+)\(.*?\):', content, re.MULTILINE)

        if classes:
            docs += "### Classes\n\n"
            for class_name in classes:
                docs += f"- `{class_name}`\n"
            docs += "\n"

        if functions:
            docs += "### Functions\n\n"
            for func_name in functions:
                if not func_name.startswith('_'):  # パブリック関数のみ
                    docs += f"- `{func_name}()`\n"
            docs += "\n"

        docs += "---\n\n"

        return docs

    async def _create_presentation(self, slides: List[Dict[str, Any]],
                                  title: str = "Presentation",
                                  output_format: str = "markdown",
                                  output_path: Optional[str] = None) -> Dict[str, Any]:
        """プレゼンテーション資料を作成"""
        try:
            if output_path is None:
                ext = "md" if output_format == "markdown" else "html"
                output_path = f"{title.lower().replace(' ', '_')}.{ext}"

            if output_format == "markdown":
                content = await self._create_markdown_presentation(title, slides)
            elif output_format == "html":
                content = await self._create_html_presentation(title, slides)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported presentation format: {output_format}"
                }

            # ファイルに書き込み
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return {
                "success": True,
                "message": f"Presentation created: {output_path}",
                "output_path": output_path,
                "format": output_format,
                "slides_count": len(slides),
                "content_length": len(content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Presentation creation failed: {e}"
            }

    async def _create_markdown_presentation(self, title: str, slides: List[Dict[str, Any]]) -> str:
        """Markdownプレゼンテーションを作成"""
        content = f"# {title}\n\n"
        content += "---\n\n"

        for i, slide in enumerate(slides, 1):
            slide_title = slide.get('title', f'Slide {i}')
            slide_content = slide.get('content', '')
            bullet_points = slide.get('bullets', [])
            image = slide.get('image')

            content += f"## {slide_title}\n\n"

            if slide_content:
                content += f"{slide_content}\n\n"

            if bullet_points:
                for bullet in bullet_points:
                    content += f"- {bullet}\n"
                content += "\n"

            if image:
                content += f"![{image.get('alt', 'Image')}]({image.get('url', '')})\n\n"

            content += "---\n\n"

        return content

    async def _create_html_presentation(self, title: str, slides: List[Dict[str, Any]]) -> str:
        """HTMLプレゼンテーションを作成"""
        content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; }}
        .slide {{ width: 100vw; height: 100vh; padding: 60px; box-sizing: border-box;
                 display: none; flex-direction: column; justify-content: center; }}
        .slide.active {{ display: flex; }}
        .slide h1, .slide h2 {{ color: #333; margin-bottom: 30px; }}
        .slide ul {{ font-size: 1.2em; line-height: 1.6; }}
        .slide img {{ max-width: 80%; height: auto; margin: 20px 0; }}
        .navigation {{ position: fixed; bottom: 20px; right: 20px; }}
        .nav-btn {{ padding: 10px 20px; margin: 0 5px; background: #007bff;
                   color: white; border: none; border-radius: 5px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="slide active">
        <h1>{title}</h1>
        <p>Use the navigation buttons to move between slides.</p>
    </div>
"""

        for i, slide in enumerate(slides, 1):
            slide_title = slide.get('title', f'Slide {i}')
            slide_content = slide.get('content', '')
            bullet_points = slide.get('bullets', [])
            image = slide.get('image')

            content += f"""
    <div class="slide">
        <h2>{slide_title}</h2>
"""

            if slide_content:
                content += f"        <p>{slide_content}</p>\n"

            if bullet_points:
                content += "        <ul>\n"
                for bullet in bullet_points:
                    content += f"            <li>{bullet}</li>\n"
                content += "        </ul>\n"

            if image:
                content += f"        <img src=\"{image.get('url', '')}\" alt=\"{image.get('alt', 'Image')}\">\n"

            content += "    </div>\n"

        content += f"""
    <div class="navigation">
        <button class="nav-btn" onclick="previousSlide()">Previous</button>
        <button class="nav-btn" onclick="nextSlide()">Next</button>
    </div>

    <script>
        let currentSlide = 0;
        const slides = document.querySelectorAll('.slide');

        function showSlide(n) {{
            slides[currentSlide].classList.remove('active');
            currentSlide = (n + slides.length) % slides.length;
            slides[currentSlide].classList.add('active');
        }}

        function nextSlide() {{ showSlide(currentSlide + 1); }}
        function previousSlide() {{ showSlide(currentSlide - 1); }}

        document.addEventListener('keydown', function(e) {{
            if (e.key === 'ArrowRight') nextSlide();
            if (e.key === 'ArrowLeft') previousSlide();
        }});
    </script>
</body>
</html>
"""

        return content

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """各コマンドのパラメータ定義を返す"""
        return {
            "generate_readme": {
                "project_name": {"type": "string", "required": True, "description": "プロジェクト名"},
                "description": {"type": "string", "required": True, "description": "プロジェクトの説明"},
                "features": {"type": "array", "required": False, "description": "機能リスト"},
                "installation_steps": {"type": "array", "required": False, "description": "インストール手順"},
                "usage_examples": {"type": "array", "required": False, "description": "使用例"},
                "output_path": {"type": "string", "required": False, "description": "出力ファイルパス"}
            },
            "generate_api_docs": {
                "api_spec": {"type": "object", "required": True, "description": "API仕様"},
                "output_format": {"type": "string", "required": False, "description": "出力フォーマット"},
                "output_path": {"type": "string", "required": False, "description": "出力ファイルパス"}
            },
            "create_template": {
                "template_name": {"type": "string", "required": True, "description": "テンプレート名"},
                "template_content": {"type": "string", "required": True, "description": "テンプレート内容"},
                "variables": {"type": "object", "required": False, "description": "変数定義"},
                "output_path": {"type": "string", "required": False, "description": "出力ファイルパス"}
            },
            "render_template": {
                "template_path": {"type": "string", "required": True, "description": "テンプレートファイルパス"},
                "variables": {"type": "object", "required": True, "description": "置換変数"},
                "output_path": {"type": "string", "required": False, "description": "出力ファイルパス"}
            },
            "convert_format": {
                "input_path": {"type": "string", "required": True, "description": "入力ファイルパス"},
                "output_format": {"type": "string", "required": True, "description": "出力フォーマット"},
                "output_path": {"type": "string", "required": False, "description": "出力ファイルパス"}
            },
            "generate_changelog": {
                "version_history": {"type": "array", "required": True, "description": "バージョン履歴"},
                "output_path": {"type": "string", "required": False, "description": "出力ファイルパス"}
            },
            "create_user_manual": {
                "sections": {"type": "array", "required": True, "description": "マニュアルセクション"},
                "title": {"type": "string", "required": False, "description": "マニュアルタイトル"},
                "output_path": {"type": "string", "required": False, "description": "出力ファイルパス"}
            },
            "generate_code_docs": {
                "source_directory": {"type": "string", "required": True, "description": "ソースディレクトリパス"},
                "output_path": {"type": "string", "required": False, "description": "出力ファイルパス"},
                "include_private": {"type": "boolean", "required": False, "description": "プライベート要素を含める"}
            },
            "create_presentation": {
                "slides": {"type": "array", "required": True, "description": "スライド内容"},
                "title": {"type": "string", "required": False, "description": "プレゼンテーションタイトル"},
                "output_format": {"type": "string", "required": False, "description": "出力フォーマット"},
                "output_path": {"type": "string", "required": False, "description": "出力ファイルパス"}
            }
        }
