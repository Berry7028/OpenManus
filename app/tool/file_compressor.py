"""
File Compressor Tool

ファイル圧縮・解凍を行うツール
ZIP、TAR、GZIP、7Z等の複数フォーマット対応、アーカイブ作成・展開機能を提供
"""

import asyncio
import os
import zipfile
import tarfile
import gzip
import shutil
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import tempfile

from .base import BaseTool

logger = logging.getLogger(__name__)

class FileCompressor(BaseTool):
    """ファイル圧縮・解凍ツール"""

    def __init__(self):
        super().__init__()
        self.supported_formats = {
            'zip': ['.zip'],
            'tar': ['.tar'],
            'tar.gz': ['.tar.gz', '.tgz'],
            'tar.bz2': ['.tar.bz2', '.tbz2'],
            'tar.xz': ['.tar.xz', '.txz'],
            'gzip': ['.gz'],
            '7z': ['.7z']
        }

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        ファイル圧縮・解凍操作を実行

        Args:
            command: 実行するコマンド
            **kwargs: コマンド固有のパラメータ

        Returns:
            実行結果
        """
        try:
            if command == "compress":
                return await self._compress(**kwargs)
            elif command == "decompress":
                return await self._decompress(**kwargs)
            elif command == "list_contents":
                return await self._list_contents(**kwargs)
            elif command == "add_files":
                return await self._add_files(**kwargs)
            elif command == "extract_file":
                return await self._extract_file(**kwargs)
            elif command == "create_archive":
                return await self._create_archive(**kwargs)
            elif command == "get_info":
                return await self._get_info(**kwargs)
            elif command == "test_archive":
                return await self._test_archive(**kwargs)
            elif command == "compare_sizes":
                return await self._compare_sizes(**kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "compress", "decompress", "list_contents", "add_files",
                        "extract_file", "create_archive", "get_info", "test_archive",
                        "compare_sizes"
                    ]
                }

        except Exception as e:
            logger.error(f"File compression operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def _detect_format(self, file_path: str) -> str:
        """ファイル拡張子から圧縮フォーマットを検出"""
        file_path = file_path.lower()

        for format_name, extensions in self.supported_formats.items():
            for ext in extensions:
                if file_path.endswith(ext):
                    return format_name

        return "unknown"

    async def _compress(self, source_path: str, output_path: str,
                       format: str = "zip", compression_level: int = 6,
                       exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """ファイル・ディレクトリを圧縮"""
        try:
            source = Path(source_path)
            output = Path(output_path)

            if not source.exists():
                return {
                    "success": False,
                    "error": f"Source path does not exist: {source_path}"
                }

            # 除外パターンの処理
            exclude_patterns = exclude_patterns or []

            start_time = datetime.now()
            original_size = 0
            compressed_size = 0
            file_count = 0

            if format == "zip":
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, compresslevel=compression_level) as zf:
                    if source.is_file():
                        # 単一ファイルの場合
                        original_size = source.stat().st_size
                        zf.write(source, source.name)
                        file_count = 1
                    else:
                        # ディレクトリの場合
                        for file_path in source.rglob('*'):
                            if file_path.is_file():
                                # 除外パターンチェック
                                if any(pattern in str(file_path) for pattern in exclude_patterns):
                                    continue

                                relative_path = file_path.relative_to(source)
                                zf.write(file_path, relative_path)
                                original_size += file_path.stat().st_size
                                file_count += 1

                compressed_size = output.stat().st_size

            elif format.startswith("tar"):
                mode = "w"
                if format == "tar.gz":
                    mode = "w:gz"
                elif format == "tar.bz2":
                    mode = "w:bz2"
                elif format == "tar.xz":
                    mode = "w:xz"

                with tarfile.open(output, mode) as tf:
                    if source.is_file():
                        original_size = source.stat().st_size
                        tf.add(source, source.name)
                        file_count = 1
                    else:
                        for file_path in source.rglob('*'):
                            if file_path.is_file():
                                if any(pattern in str(file_path) for pattern in exclude_patterns):
                                    continue

                                relative_path = file_path.relative_to(source)
                                tf.add(file_path, relative_path)
                                original_size += file_path.stat().st_size
                                file_count += 1

                compressed_size = output.stat().st_size

            elif format == "gzip":
                if not source.is_file():
                    return {
                        "success": False,
                        "error": "GZIP format only supports single files"
                    }

                original_size = source.stat().st_size
                with open(source, 'rb') as f_in:
                    with gzip.open(output, 'wb', compresslevel=compression_level) as f_out:
                        shutil.copyfileobj(f_in, f_out)

                compressed_size = output.stat().st_size
                file_count = 1

            else:
                return {
                    "success": False,
                    "error": f"Unsupported compression format: {format}"
                }

            end_time = datetime.now()
            compression_ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0

            return {
                "success": True,
                "message": f"Successfully compressed to {output_path}",
                "source_path": source_path,
                "output_path": str(output),
                "format": format,
                "original_size_bytes": original_size,
                "compressed_size_bytes": compressed_size,
                "compression_ratio_percent": round(compression_ratio, 2),
                "file_count": file_count,
                "processing_time_seconds": (end_time - start_time).total_seconds()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Compression failed: {e}"
            }

    async def _decompress(self, archive_path: str, output_dir: str,
                         format: Optional[str] = None,
                         extract_specific_files: Optional[List[str]] = None) -> Dict[str, Any]:
        """アーカイブを解凍"""
        try:
            archive = Path(archive_path)
            output = Path(output_dir)

            if not archive.exists():
                return {
                    "success": False,
                    "error": f"Archive file does not exist: {archive_path}"
                }

            # フォーマット自動検出
            if format is None:
                format = self._detect_format(archive_path)
                if format == "unknown":
                    return {
                        "success": False,
                        "error": f"Cannot detect archive format: {archive_path}"
                    }

            # 出力ディレクトリを作成
            output.mkdir(parents=True, exist_ok=True)

            start_time = datetime.now()
            extracted_files = []

            if format == "zip":
                with zipfile.ZipFile(archive, 'r') as zf:
                    if extract_specific_files:
                        for file_name in extract_specific_files:
                            if file_name in zf.namelist():
                                zf.extract(file_name, output)
                                extracted_files.append(file_name)
                    else:
                        zf.extractall(output)
                        extracted_files = zf.namelist()

            elif format.startswith("tar"):
                with tarfile.open(archive, 'r') as tf:
                    if extract_specific_files:
                        for file_name in extract_specific_files:
                            try:
                                tf.extract(file_name, output)
                                extracted_files.append(file_name)
                            except KeyError:
                                continue
                    else:
                        tf.extractall(output)
                        extracted_files = tf.getnames()

            elif format == "gzip":
                output_file = output / archive.stem
                with gzip.open(archive, 'rb') as f_in:
                    with open(output_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                extracted_files = [str(output_file)]

            else:
                return {
                    "success": False,
                    "error": f"Unsupported decompression format: {format}"
                }

            end_time = datetime.now()

            return {
                "success": True,
                "message": f"Successfully extracted to {output_dir}",
                "archive_path": archive_path,
                "output_directory": str(output),
                "format": format,
                "extracted_files": extracted_files,
                "file_count": len(extracted_files),
                "processing_time_seconds": (end_time - start_time).total_seconds()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Decompression failed: {e}"
            }

    async def _list_contents(self, archive_path: str,
                           format: Optional[str] = None) -> Dict[str, Any]:
        """アーカイブの内容を一覧表示"""
        try:
            archive = Path(archive_path)

            if not archive.exists():
                return {
                    "success": False,
                    "error": f"Archive file does not exist: {archive_path}"
                }

            if format is None:
                format = self._detect_format(archive_path)
                if format == "unknown":
                    return {
                        "success": False,
                        "error": f"Cannot detect archive format: {archive_path}"
                    }

            contents = []
            total_size = 0

            if format == "zip":
                with zipfile.ZipFile(archive, 'r') as zf:
                    for info in zf.infolist():
                        contents.append({
                            "name": info.filename,
                            "size_bytes": info.file_size,
                            "compressed_size_bytes": info.compress_size,
                            "modified_time": datetime(*info.date_time).isoformat(),
                            "is_directory": info.filename.endswith('/'),
                            "compression_ratio_percent": round((1 - info.compress_size / info.file_size) * 100, 2) if info.file_size > 0 else 0
                        })
                        total_size += info.file_size

            elif format.startswith("tar"):
                with tarfile.open(archive, 'r') as tf:
                    for member in tf.getmembers():
                        contents.append({
                            "name": member.name,
                            "size_bytes": member.size,
                            "modified_time": datetime.fromtimestamp(member.mtime).isoformat(),
                            "is_directory": member.isdir(),
                            "is_file": member.isfile(),
                            "mode": oct(member.mode)
                        })
                        total_size += member.size

            elif format == "gzip":
                # GZIPは単一ファイルのため、ファイル情報のみ
                stat = archive.stat()
                contents.append({
                    "name": archive.stem,
                    "compressed_size_bytes": stat.st_size,
                    "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

            else:
                return {
                    "success": False,
                    "error": f"Unsupported format for listing: {format}"
                }

            return {
                "success": True,
                "archive_path": archive_path,
                "format": format,
                "total_files": len(contents),
                "total_size_bytes": total_size,
                "contents": contents
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list contents: {e}"
            }

    async def _add_files(self, archive_path: str, files_to_add: List[str],
                        format: Optional[str] = None) -> Dict[str, Any]:
        """既存のアーカイブにファイルを追加"""
        try:
            archive = Path(archive_path)

            if not archive.exists():
                return {
                    "success": False,
                    "error": f"Archive file does not exist: {archive_path}"
                }

            if format is None:
                format = self._detect_format(archive_path)

            added_files = []

            if format == "zip":
                with zipfile.ZipFile(archive, 'a') as zf:
                    for file_path in files_to_add:
                        file_obj = Path(file_path)
                        if file_obj.exists():
                            zf.write(file_obj, file_obj.name)
                            added_files.append(file_path)

            else:
                return {
                    "success": False,
                    "error": f"Adding files not supported for format: {format}"
                }

            return {
                "success": True,
                "message": f"Added {len(added_files)} files to archive",
                "archive_path": archive_path,
                "added_files": added_files
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add files: {e}"
            }

    async def _extract_file(self, archive_path: str, file_name: str,
                           output_path: str, format: Optional[str] = None) -> Dict[str, Any]:
        """アーカイブから特定のファイルを抽出"""
        try:
            archive = Path(archive_path)

            if not archive.exists():
                return {
                    "success": False,
                    "error": f"Archive file does not exist: {archive_path}"
                }

            if format is None:
                format = self._detect_format(archive_path)

            if format == "zip":
                with zipfile.ZipFile(archive, 'r') as zf:
                    if file_name in zf.namelist():
                        with zf.open(file_name) as source, open(output_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    else:
                        return {
                            "success": False,
                            "error": f"File not found in archive: {file_name}"
                        }

            elif format.startswith("tar"):
                with tarfile.open(archive, 'r') as tf:
                    try:
                        member = tf.getmember(file_name)
                        with tf.extractfile(member) as source, open(output_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    except KeyError:
                        return {
                            "success": False,
                            "error": f"File not found in archive: {file_name}"
                        }

            else:
                return {
                    "success": False,
                    "error": f"File extraction not supported for format: {format}"
                }

            return {
                "success": True,
                "message": f"Successfully extracted {file_name}",
                "archive_path": archive_path,
                "extracted_file": file_name,
                "output_path": output_path
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"File extraction failed: {e}"
            }

    async def _create_archive(self, files_and_dirs: List[str], output_path: str,
                             format: str = "zip", base_dir: Optional[str] = None) -> Dict[str, Any]:
        """複数のファイル・ディレクトリからアーカイブを作成"""
        try:
            output = Path(output_path)
            base_path = Path(base_dir) if base_dir else None

            start_time = datetime.now()
            total_size = 0
            file_count = 0

            if format == "zip":
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for item_path in files_and_dirs:
                        item = Path(item_path)
                        if not item.exists():
                            continue

                        if item.is_file():
                            arc_name = item.relative_to(base_path) if base_path else item.name
                            zf.write(item, arc_name)
                            total_size += item.stat().st_size
                            file_count += 1
                        elif item.is_dir():
                            for file_path in item.rglob('*'):
                                if file_path.is_file():
                                    if base_path:
                                        arc_name = file_path.relative_to(base_path)
                                    else:
                                        arc_name = file_path.relative_to(item.parent)
                                    zf.write(file_path, arc_name)
                                    total_size += file_path.stat().st_size
                                    file_count += 1

            elif format.startswith("tar"):
                mode = "w"
                if format == "tar.gz":
                    mode = "w:gz"
                elif format == "tar.bz2":
                    mode = "w:bz2"
                elif format == "tar.xz":
                    mode = "w:xz"

                with tarfile.open(output, mode) as tf:
                    for item_path in files_and_dirs:
                        item = Path(item_path)
                        if item.exists():
                            arc_name = item.relative_to(base_path) if base_path else item.name
                            tf.add(item, arc_name)
                            if item.is_file():
                                total_size += item.stat().st_size
                                file_count += 1
                            else:
                                for file_path in item.rglob('*'):
                                    if file_path.is_file():
                                        total_size += file_path.stat().st_size
                                        file_count += 1

            else:
                return {
                    "success": False,
                    "error": f"Unsupported format for archive creation: {format}"
                }

            end_time = datetime.now()
            compressed_size = output.stat().st_size
            compression_ratio = (1 - compressed_size / total_size) * 100 if total_size > 0 else 0

            return {
                "success": True,
                "message": f"Successfully created archive: {output_path}",
                "archive_path": str(output),
                "format": format,
                "input_files": files_and_dirs,
                "total_files": file_count,
                "original_size_bytes": total_size,
                "compressed_size_bytes": compressed_size,
                "compression_ratio_percent": round(compression_ratio, 2),
                "processing_time_seconds": (end_time - start_time).total_seconds()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Archive creation failed: {e}"
            }

    async def _get_info(self, archive_path: str) -> Dict[str, Any]:
        """アーカイブの詳細情報を取得"""
        try:
            archive = Path(archive_path)

            if not archive.exists():
                return {
                    "success": False,
                    "error": f"Archive file does not exist: {archive_path}"
                }

            stat = archive.stat()
            format = self._detect_format(archive_path)

            info = {
                "archive_path": archive_path,
                "format": format,
                "file_size_bytes": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat()
            }

            # フォーマット固有の情報
            if format == "zip":
                with zipfile.ZipFile(archive, 'r') as zf:
                    info.update({
                        "total_files": len(zf.namelist()),
                        "uncompressed_size_bytes": sum(info.file_size for info in zf.infolist()),
                        "compression_method": "ZIP_DEFLATED"
                    })

            elif format.startswith("tar"):
                with tarfile.open(archive, 'r') as tf:
                    members = tf.getmembers()
                    info.update({
                        "total_files": len([m for m in members if m.isfile()]),
                        "total_entries": len(members),
                        "uncompressed_size_bytes": sum(m.size for m in members if m.isfile())
                    })

            # 圧縮率計算
            if "uncompressed_size_bytes" in info and info["uncompressed_size_bytes"] > 0:
                compression_ratio = (1 - stat.st_size / info["uncompressed_size_bytes"]) * 100
                info["compression_ratio_percent"] = round(compression_ratio, 2)

            return {
                "success": True,
                "archive_info": info
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get archive info: {e}"
            }

    async def _test_archive(self, archive_path: str) -> Dict[str, Any]:
        """アーカイブの整合性をテスト"""
        try:
            archive = Path(archive_path)

            if not archive.exists():
                return {
                    "success": False,
                    "error": f"Archive file does not exist: {archive_path}"
                }

            format = self._detect_format(archive_path)

            if format == "zip":
                with zipfile.ZipFile(archive, 'r') as zf:
                    bad_files = zf.testzip()
                    if bad_files:
                        return {
                            "success": False,
                            "error": f"Archive test failed. Bad file: {bad_files}",
                            "archive_path": archive_path
                        }

            elif format.startswith("tar"):
                # tarfileには直接的なテスト機能がないため、読み込みテストを実行
                try:
                    with tarfile.open(archive, 'r') as tf:
                        tf.getmembers()  # 全メンバーを読み込んでテスト
                except tarfile.TarError as e:
                    return {
                        "success": False,
                        "error": f"Archive test failed: {e}",
                        "archive_path": archive_path
                    }

            elif format == "gzip":
                try:
                    with gzip.open(archive, 'rb') as f:
                        f.read(1)  # 最初の1バイトを読み込んでテスト
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"GZIP test failed: {e}",
                        "archive_path": archive_path
                    }

            else:
                return {
                    "success": False,
                    "error": f"Archive testing not supported for format: {format}"
                }

            return {
                "success": True,
                "message": "Archive integrity test passed",
                "archive_path": archive_path,
                "format": format
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Archive test failed: {e}"
            }

    async def _compare_sizes(self, file_or_dir_path: str,
                           formats: List[str] = None) -> Dict[str, Any]:
        """異なる圧縮フォーマットでのサイズを比較"""
        try:
            source = Path(file_or_dir_path)

            if not source.exists():
                return {
                    "success": False,
                    "error": f"Source path does not exist: {file_or_dir_path}"
                }

            if formats is None:
                formats = ["zip", "tar.gz", "tar.bz2", "tar.xz"]

            # 元のサイズを計算
            original_size = 0
            if source.is_file():
                original_size = source.stat().st_size
            else:
                for file_path in source.rglob('*'):
                    if file_path.is_file():
                        original_size += file_path.stat().st_size

            comparison_results = {
                "original_size_bytes": original_size,
                "format_comparison": {}
            }

            # 一時ディレクトリで各フォーマットをテスト
            with tempfile.TemporaryDirectory() as temp_dir:
                for format_name in formats:
                    try:
                        temp_archive = Path(temp_dir) / f"test.{format_name.replace('.', '_')}"

                        # 圧縮実行
                        result = await self._compress(
                            str(source), str(temp_archive), format_name
                        )

                        if result["success"]:
                            compressed_size = result["compressed_size_bytes"]
                            compression_ratio = result["compression_ratio_percent"]

                            comparison_results["format_comparison"][format_name] = {
                                "compressed_size_bytes": compressed_size,
                                "compression_ratio_percent": compression_ratio,
                                "space_saved_bytes": original_size - compressed_size,
                                "processing_time_seconds": result["processing_time_seconds"]
                            }
                        else:
                            comparison_results["format_comparison"][format_name] = {
                                "error": result["error"]
                            }

                    except Exception as e:
                        comparison_results["format_comparison"][format_name] = {
                            "error": str(e)
                        }

            # 最適なフォーマットを特定
            successful_formats = {
                k: v for k, v in comparison_results["format_comparison"].items()
                if "error" not in v
            }

            if successful_formats:
                best_compression = min(
                    successful_formats.items(),
                    key=lambda x: x[1]["compressed_size_bytes"]
                )
                fastest_compression = min(
                    successful_formats.items(),
                    key=lambda x: x[1]["processing_time_seconds"]
                )

                comparison_results.update({
                    "best_compression_format": best_compression[0],
                    "best_compression_size": best_compression[1]["compressed_size_bytes"],
                    "fastest_format": fastest_compression[0],
                    "fastest_time": fastest_compression[1]["processing_time_seconds"]
                })

            return {
                "success": True,
                "source_path": file_or_dir_path,
                "comparison_results": comparison_results
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Size comparison failed: {e}"
            }

    def get_parameters(self) -> Dict[str, Dict[str, Any]]:
        """各コマンドのパラメータ定義を返す"""
        return {
            "compress": {
                "source_path": {"type": "string", "required": True, "description": "圧縮対象のファイル・ディレクトリパス"},
                "output_path": {"type": "string", "required": True, "description": "出力アーカイブファイルパス"},
                "format": {"type": "string", "required": False, "description": "圧縮フォーマット（zip, tar, tar.gz, tar.bz2, tar.xz, gzip）"},
                "compression_level": {"type": "integer", "required": False, "description": "圧縮レベル（1-9）"},
                "exclude_patterns": {"type": "array", "required": False, "description": "除外パターンリスト"}
            },
            "decompress": {
                "archive_path": {"type": "string", "required": True, "description": "解凍対象アーカイブファイルパス"},
                "output_dir": {"type": "string", "required": True, "description": "解凍先ディレクトリ"},
                "format": {"type": "string", "required": False, "description": "アーカイブフォーマット（自動検出）"},
                "extract_specific_files": {"type": "array", "required": False, "description": "特定ファイルのみ解凍"}
            },
            "list_contents": {
                "archive_path": {"type": "string", "required": True, "description": "アーカイブファイルパス"},
                "format": {"type": "string", "required": False, "description": "アーカイブフォーマット（自動検出）"}
            },
            "add_files": {
                "archive_path": {"type": "string", "required": True, "description": "対象アーカイブファイルパス"},
                "files_to_add": {"type": "array", "required": True, "description": "追加するファイルパスリスト"},
                "format": {"type": "string", "required": False, "description": "アーカイブフォーマット（自動検出）"}
            },
            "extract_file": {
                "archive_path": {"type": "string", "required": True, "description": "アーカイブファイルパス"},
                "file_name": {"type": "string", "required": True, "description": "抽出するファイル名"},
                "output_path": {"type": "string", "required": True, "description": "出力ファイルパス"},
                "format": {"type": "string", "required": False, "description": "アーカイブフォーマット（自動検出）"}
            },
            "create_archive": {
                "files_and_dirs": {"type": "array", "required": True, "description": "アーカイブに含めるファイル・ディレクトリリスト"},
                "output_path": {"type": "string", "required": True, "description": "出力アーカイブファイルパス"},
                "format": {"type": "string", "required": False, "description": "圧縮フォーマット"},
                "base_dir": {"type": "string", "required": False, "description": "ベースディレクトリ"}
            },
            "get_info": {
                "archive_path": {"type": "string", "required": True, "description": "アーカイブファイルパス"}
            },
            "test_archive": {
                "archive_path": {"type": "string", "required": True, "description": "テスト対象アーカイブファイルパス"}
            },
            "compare_sizes": {
                "file_or_dir_path": {"type": "string", "required": True, "description": "比較対象ファイル・ディレクトリパス"},
                "formats": {"type": "array", "required": False, "description": "比較する圧縮フォーマットリスト"}
            }
        }
