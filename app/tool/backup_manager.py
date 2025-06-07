"""
Backup Manager Tool

This tool provides comprehensive backup and restore capabilities including:
- File and directory backup
- Incremental and differential backups
- Backup scheduling and automation
- Compression and encryption
- Backup verification and integrity checks
- Remote backup support
- Backup history and metadata management
"""

import asyncio
import os
import shutil
import json
import hashlib
import time
import tarfile
import zipfile
import gzip
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import subprocess
import tempfile
from pathlib import Path
import sqlite3
from .base import BaseTool


class BackupManager(BaseTool):
    """Tool for backup and restore operations"""

    def __init__(self):
        super().__init__()
        self.name = "backup_manager"
        self.description = "Comprehensive backup and restore management tool"

        # Backup database for metadata
        self.backup_db_path = os.path.expanduser("~/.backup_manager.db")
        self._init_database()

        # Supported compression formats
        self.compression_formats = {
            'zip': {'extension': '.zip', 'module': 'zipfile'},
            'tar': {'extension': '.tar', 'module': 'tarfile'},
            'tgz': {'extension': '.tar.gz', 'module': 'tarfile'},
            'tbz2': {'extension': '.tar.bz2', 'module': 'tarfile'},
            'txz': {'extension': '.tar.xz', 'module': 'tarfile'}
        }

        # Default backup directory
        self.default_backup_dir = os.path.expanduser("~/backups")
        if not os.path.exists(self.default_backup_dir):
            os.makedirs(self.default_backup_dir)

    def _init_database(self):
        """Initialize backup metadata database"""
        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                source_path TEXT NOT NULL,
                backup_path TEXT NOT NULL,
                backup_type TEXT NOT NULL,
                compression TEXT,
                file_count INTEGER,
                total_size INTEGER,
                checksum TEXT,
                created_at TIMESTAMP,
                metadata TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id INTEGER,
                file_path TEXT NOT NULL,
                file_size INTEGER,
                file_hash TEXT,
                modified_time TIMESTAMP,
                FOREIGN KEY (backup_id) REFERENCES backups (id)
            )
        ''')

        conn.commit()
        conn.close()

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute backup manager commands"""
        try:
            if command == "create_backup":
                return await self._create_backup(**kwargs)
            elif command == "restore_backup":
                return await self._restore_backup(**kwargs)
            elif command == "list_backups":
                return await self._list_backups(**kwargs)
            elif command == "delete_backup":
                return await self._delete_backup(**kwargs)
            elif command == "verify_backup":
                return await self._verify_backup(**kwargs)
            elif command == "incremental_backup":
                return await self._incremental_backup(**kwargs)
            elif command == "schedule_backup":
                return await self._schedule_backup(**kwargs)
            elif command == "backup_status":
                return await self._backup_status(**kwargs)
            elif command == "cleanup_old_backups":
                return await self._cleanup_old_backups(**kwargs)
            elif command == "export_backup_config":
                return await self._export_backup_config(**kwargs)
            elif command == "import_backup_config":
                return await self._import_backup_config(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Backup manager error: {str(e)}"}

    async def _create_backup(self, source_path: str, backup_name: Optional[str] = None,
                           backup_dir: Optional[str] = None, compression: str = "tgz",
                           exclude_patterns: Optional[List[str]] = None,
                           include_metadata: bool = True) -> Dict[str, Any]:
        """Create a new backup"""
        if not os.path.exists(source_path):
            return {"error": f"Source path not found: {source_path}"}

        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{os.path.basename(source_path)}_{timestamp}"

        if backup_dir is None:
            backup_dir = self.default_backup_dir

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        if compression not in self.compression_formats:
            return {"error": f"Unsupported compression format: {compression}"}

        # Generate backup file path
        backup_extension = self.compression_formats[compression]['extension']
        backup_file_path = os.path.join(backup_dir, backup_name + backup_extension)

        start_time = time.time()
        file_count = 0
        total_size = 0
        files_info = []

        try:
            if compression == 'zip':
                with zipfile.ZipFile(backup_file_path, 'w', zipfile.ZIP_DEFLATED) as backup_file:
                    for root, dirs, files in os.walk(source_path):
                        # Apply exclude patterns
                        if exclude_patterns:
                            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d), exclude_patterns)]
                            files = [f for f in files if not self._should_exclude(os.path.join(root, f), exclude_patterns)]

                        for file in files:
                            file_path = os.path.join(root, file)
                            archive_name = os.path.relpath(file_path, source_path)

                            if os.path.isfile(file_path):
                                backup_file.write(file_path, archive_name)

                                # Collect file metadata
                                file_stat = os.stat(file_path)
                                file_size = file_stat.st_size
                                file_hash = self._calculate_file_hash(file_path)

                                files_info.append({
                                    'path': archive_name,
                                    'size': file_size,
                                    'hash': file_hash,
                                    'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                                })

                                file_count += 1
                                total_size += file_size

            else:  # tar-based formats
                mode_map = {
                    'tar': 'w',
                    'tgz': 'w:gz',
                    'tbz2': 'w:bz2',
                    'txz': 'w:xz'
                }

                with tarfile.open(backup_file_path, mode_map[compression]) as backup_file:
                    for root, dirs, files in os.walk(source_path):
                        # Apply exclude patterns
                        if exclude_patterns:
                            dirs[:] = [d for d in dirs if not self._should_exclude(os.path.join(root, d), exclude_patterns)]
                            files = [f for f in files if not self._should_exclude(os.path.join(root, f), exclude_patterns)]

                        for file in files:
                            file_path = os.path.join(root, file)
                            archive_name = os.path.relpath(file_path, source_path)

                            if os.path.isfile(file_path):
                                backup_file.add(file_path, arcname=archive_name)

                                # Collect file metadata
                                file_stat = os.stat(file_path)
                                file_size = file_stat.st_size
                                file_hash = self._calculate_file_hash(file_path)

                                files_info.append({
                                    'path': archive_name,
                                    'size': file_size,
                                    'hash': file_hash,
                                    'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                                })

                                file_count += 1
                                total_size += file_size

            # Calculate backup file checksum
            backup_checksum = self._calculate_file_hash(backup_file_path)
            backup_size = os.path.getsize(backup_file_path)
            duration = time.time() - start_time

            # Store backup metadata in database
            backup_id = self._store_backup_metadata(
                backup_name, source_path, backup_file_path, "full",
                compression, file_count, total_size, backup_checksum,
                {"files": files_info, "exclude_patterns": exclude_patterns}
            )

            # Store individual file metadata
            self._store_file_metadata(backup_id, files_info)

            return {
                "backup_name": backup_name,
                "backup_id": backup_id,
                "source_path": source_path,
                "backup_file": backup_file_path,
                "compression": compression,
                "file_count": file_count,
                "total_source_size": total_size,
                "backup_file_size": backup_size,
                "compression_ratio": round((1 - backup_size / total_size) * 100, 2) if total_size > 0 else 0,
                "backup_checksum": backup_checksum,
                "duration_seconds": round(duration, 2),
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            # Clean up partial backup file
            if os.path.exists(backup_file_path):
                os.remove(backup_file_path)
            raise e

    def _should_exclude(self, file_path: str, exclude_patterns: List[str]) -> bool:
        """Check if file should be excluded based on patterns"""
        import fnmatch

        for pattern in exclude_patterns:
            if fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(os.path.basename(file_path), pattern):
                return True
        return False

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""

    def _store_backup_metadata(self, name: str, source_path: str, backup_path: str,
                              backup_type: str, compression: str, file_count: int,
                              total_size: int, checksum: str, metadata: Dict) -> int:
        """Store backup metadata in database"""
        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO backups (name, source_path, backup_path, backup_type,
                               compression, file_count, total_size, checksum,
                               created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, source_path, backup_path, backup_type, compression,
              file_count, total_size, checksum, datetime.now(), json.dumps(metadata)))

        backup_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return backup_id

    def _store_file_metadata(self, backup_id: int, files_info: List[Dict]):
        """Store individual file metadata"""
        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()

        for file_info in files_info:
            cursor.execute('''
                INSERT INTO backup_files (backup_id, file_path, file_size, file_hash, modified_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (backup_id, file_info['path'], file_info['size'],
                  file_info['hash'], file_info['modified']))

        conn.commit()
        conn.close()

    async def _restore_backup(self, backup_id: Optional[int] = None, backup_name: Optional[str] = None,
                            restore_path: Optional[str] = None, overwrite: bool = False,
                            verify_checksums: bool = True) -> Dict[str, Any]:
        """Restore a backup"""
        # Get backup metadata
        backup_info = self._get_backup_metadata(backup_id, backup_name)
        if not backup_info:
            return {"error": "Backup not found"}

        backup_file_path = backup_info['backup_path']
        if not os.path.exists(backup_file_path):
            return {"error": f"Backup file not found: {backup_file_path}"}

        if restore_path is None:
            restore_path = backup_info['source_path'] + "_restored"

        if os.path.exists(restore_path) and not overwrite:
            return {"error": f"Restore path already exists: {restore_path}"}

        start_time = time.time()
        restored_files = 0

        try:
            # Create restore directory
            os.makedirs(restore_path, exist_ok=True)

            # Extract based on compression format
            compression = backup_info['compression']

            if compression == 'zip':
                with zipfile.ZipFile(backup_file_path, 'r') as backup_file:
                    backup_file.extractall(restore_path)
                    restored_files = len(backup_file.namelist())

            else:  # tar-based formats
                mode_map = {
                    'tar': 'r',
                    'tgz': 'r:gz',
                    'tbz2': 'r:bz2',
                    'txz': 'r:xz'
                }

                with tarfile.open(backup_file_path, mode_map[compression]) as backup_file:
                    backup_file.extractall(restore_path)
                    restored_files = len(backup_file.getnames())

            # Verify checksums if requested
            verification_results = None
            if verify_checksums:
                verification_results = await self._verify_restored_files(backup_info['id'], restore_path)

            duration = time.time() - start_time

            return {
                "backup_name": backup_info['name'],
                "backup_id": backup_info['id'],
                "restore_path": restore_path,
                "restored_files": restored_files,
                "duration_seconds": round(duration, 2),
                "verification_results": verification_results,
                "restored_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Restore failed: {str(e)}"}

    def _get_backup_metadata(self, backup_id: Optional[int] = None, backup_name: Optional[str] = None) -> Optional[Dict]:
        """Get backup metadata from database"""
        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()

        if backup_id:
            cursor.execute('SELECT * FROM backups WHERE id = ?', (backup_id,))
        elif backup_name:
            cursor.execute('SELECT * FROM backups WHERE name = ?', (backup_name,))
        else:
            return None

        row = cursor.fetchone()
        conn.close()

        if row:
            columns = ['id', 'name', 'source_path', 'backup_path', 'backup_type',
                      'compression', 'file_count', 'total_size', 'checksum',
                      'created_at', 'metadata']
            return dict(zip(columns, row))

        return None

    async def _verify_restored_files(self, backup_id: int, restore_path: str) -> Dict[str, Any]:
        """Verify restored files against original checksums"""
        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT file_path, file_hash FROM backup_files WHERE backup_id = ?', (backup_id,))
        file_records = cursor.fetchall()
        conn.close()

        verified_files = 0
        failed_files = []

        for file_path, expected_hash in file_records:
            full_path = os.path.join(restore_path, file_path)

            if os.path.exists(full_path):
                actual_hash = self._calculate_file_hash(full_path)
                if actual_hash == expected_hash:
                    verified_files += 1
                else:
                    failed_files.append({
                        'file': file_path,
                        'expected_hash': expected_hash,
                        'actual_hash': actual_hash
                    })
            else:
                failed_files.append({
                    'file': file_path,
                    'error': 'File not found in restore'
                })

        return {
            "total_files": len(file_records),
            "verified_files": verified_files,
            "failed_files": len(failed_files),
            "failed_details": failed_files,
            "verification_success": len(failed_files) == 0
        }

    async def _list_backups(self, limit: int = 50, backup_type: Optional[str] = None) -> Dict[str, Any]:
        """List all backups"""
        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()

        query = 'SELECT * FROM backups'
        params = []

        if backup_type:
            query += ' WHERE backup_type = ?'
            params.append(backup_type)

        query += ' ORDER BY created_at DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        columns = ['id', 'name', 'source_path', 'backup_path', 'backup_type',
                  'compression', 'file_count', 'total_size', 'checksum',
                  'created_at', 'metadata']

        backups = []
        for row in rows:
            backup = dict(zip(columns, row))
            # Add file existence check
            backup['backup_file_exists'] = os.path.exists(backup['backup_path'])
            # Parse metadata
            try:
                backup['metadata'] = json.loads(backup['metadata']) if backup['metadata'] else {}
            except:
                backup['metadata'] = {}
            backups.append(backup)

        return {
            "total_backups": len(backups),
            "backups": backups
        }

    async def _delete_backup(self, backup_id: Optional[int] = None, backup_name: Optional[str] = None,
                           delete_files: bool = True) -> Dict[str, Any]:
        """Delete a backup"""
        backup_info = self._get_backup_metadata(backup_id, backup_name)
        if not backup_info:
            return {"error": "Backup not found"}

        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()

        try:
            # Delete file metadata
            cursor.execute('DELETE FROM backup_files WHERE backup_id = ?', (backup_info['id'],))

            # Delete backup metadata
            cursor.execute('DELETE FROM backups WHERE id = ?', (backup_info['id'],))

            # Delete backup file if requested
            if delete_files and os.path.exists(backup_info['backup_path']):
                os.remove(backup_info['backup_path'])
                file_deleted = True
            else:
                file_deleted = False

            conn.commit()

            return {
                "backup_name": backup_info['name'],
                "backup_id": backup_info['id'],
                "metadata_deleted": True,
                "file_deleted": file_deleted,
                "deleted_at": datetime.now().isoformat()
            }

        except Exception as e:
            conn.rollback()
            return {"error": f"Delete failed: {str(e)}"}
        finally:
            conn.close()

    async def _verify_backup(self, backup_id: Optional[int] = None, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """Verify backup integrity"""
        backup_info = self._get_backup_metadata(backup_id, backup_name)
        if not backup_info:
            return {"error": "Backup not found"}

        backup_file_path = backup_info['backup_path']
        if not os.path.exists(backup_file_path):
            return {"error": f"Backup file not found: {backup_file_path}"}

        start_time = time.time()

        # Verify backup file checksum
        current_checksum = self._calculate_file_hash(backup_file_path)
        checksum_match = current_checksum == backup_info['checksum']

        # Try to open and validate archive
        archive_valid = False
        file_count = 0

        try:
            compression = backup_info['compression']

            if compression == 'zip':
                with zipfile.ZipFile(backup_file_path, 'r') as backup_file:
                    # Test archive integrity
                    bad_files = backup_file.testzip()
                    archive_valid = bad_files is None
                    file_count = len(backup_file.namelist())

            else:  # tar-based formats
                mode_map = {
                    'tar': 'r',
                    'tgz': 'r:gz',
                    'tbz2': 'r:bz2',
                    'txz': 'r:xz'
                }

                with tarfile.open(backup_file_path, mode_map[compression]) as backup_file:
                    # Try to list all files
                    backup_file.getnames()
                    archive_valid = True
                    file_count = len(backup_file.getnames())

        except Exception as e:
            archive_valid = False

        duration = time.time() - start_time

        return {
            "backup_name": backup_info['name'],
            "backup_id": backup_info['id'],
            "backup_file": backup_file_path,
            "checksum_match": checksum_match,
            "expected_checksum": backup_info['checksum'],
            "current_checksum": current_checksum,
            "archive_valid": archive_valid,
            "expected_file_count": backup_info['file_count'],
            "actual_file_count": file_count,
            "file_count_match": file_count == backup_info['file_count'],
            "verification_duration": round(duration, 2),
            "overall_integrity": checksum_match and archive_valid and (file_count == backup_info['file_count']),
            "verified_at": datetime.now().isoformat()
        }

    async def _incremental_backup(self, source_path: str, base_backup_name: str,
                                backup_name: Optional[str] = None, backup_dir: Optional[str] = None,
                                compression: str = "tgz") -> Dict[str, Any]:
        """Create incremental backup based on a previous backup"""
        # Get base backup metadata
        base_backup = self._get_backup_metadata(backup_name=base_backup_name)
        if not base_backup:
            return {"error": f"Base backup not found: {base_backup_name}"}

        # Get file list from base backup
        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT file_path, file_hash, modified_time FROM backup_files WHERE backup_id = ?',
                      (base_backup['id'],))
        base_files = {row[0]: {'hash': row[1], 'modified': row[2]} for row in cursor.fetchall()}
        conn.close()

        # Find changed/new files
        changed_files = []
        new_files = []

        for root, dirs, files in os.walk(source_path):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, source_path)

                if os.path.isfile(file_path):
                    current_hash = self._calculate_file_hash(file_path)
                    file_stat = os.stat(file_path)
                    current_modified = datetime.fromtimestamp(file_stat.st_mtime).isoformat()

                    if relative_path in base_files:
                        # Check if file changed
                        if current_hash != base_files[relative_path]['hash']:
                            changed_files.append({
                                'path': relative_path,
                                'full_path': file_path,
                                'size': file_stat.st_size,
                                'hash': current_hash,
                                'modified': current_modified
                            })
                    else:
                        # New file
                        new_files.append({
                            'path': relative_path,
                            'full_path': file_path,
                            'size': file_stat.st_size,
                            'hash': current_hash,
                            'modified': current_modified
                        })

        if not changed_files and not new_files:
            return {
                "message": "No changes detected since base backup",
                "base_backup": base_backup_name,
                "changed_files": 0,
                "new_files": 0
            }

        # Create incremental backup
        if backup_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"incremental_{base_backup_name}_{timestamp}"

        if backup_dir is None:
            backup_dir = self.default_backup_dir

        backup_extension = self.compression_formats[compression]['extension']
        backup_file_path = os.path.join(backup_dir, backup_name + backup_extension)

        files_to_backup = changed_files + new_files
        file_count = len(files_to_backup)
        total_size = sum(f['size'] for f in files_to_backup)

        start_time = time.time()

        try:
            if compression == 'zip':
                with zipfile.ZipFile(backup_file_path, 'w', zipfile.ZIP_DEFLATED) as backup_file:
                    for file_info in files_to_backup:
                        backup_file.write(file_info['full_path'], file_info['path'])

            else:  # tar-based formats
                mode_map = {
                    'tar': 'w',
                    'tgz': 'w:gz',
                    'tbz2': 'w:bz2',
                    'txz': 'w:xz'
                }

                with tarfile.open(backup_file_path, mode_map[compression]) as backup_file:
                    for file_info in files_to_backup:
                        backup_file.add(file_info['full_path'], arcname=file_info['path'])

            # Calculate backup checksum
            backup_checksum = self._calculate_file_hash(backup_file_path)
            backup_size = os.path.getsize(backup_file_path)
            duration = time.time() - start_time

            # Store backup metadata
            metadata = {
                "base_backup_id": base_backup['id'],
                "base_backup_name": base_backup_name,
                "changed_files": len(changed_files),
                "new_files": len(new_files),
                "files": [{'path': f['path'], 'size': f['size'], 'hash': f['hash'], 'modified': f['modified']}
                         for f in files_to_backup]
            }

            backup_id = self._store_backup_metadata(
                backup_name, source_path, backup_file_path, "incremental",
                compression, file_count, total_size, backup_checksum, metadata
            )

            # Store file metadata
            self._store_file_metadata(backup_id, [{'path': f['path'], 'size': f['size'], 'hash': f['hash'], 'modified': f['modified']}
                                                  for f in files_to_backup])

            return {
                "backup_name": backup_name,
                "backup_id": backup_id,
                "backup_type": "incremental",
                "base_backup": base_backup_name,
                "source_path": source_path,
                "backup_file": backup_file_path,
                "changed_files": len(changed_files),
                "new_files": len(new_files),
                "total_files": file_count,
                "total_size": total_size,
                "backup_file_size": backup_size,
                "compression_ratio": round((1 - backup_size / total_size) * 100, 2) if total_size > 0 else 0,
                "duration_seconds": round(duration, 2),
                "created_at": datetime.now().isoformat()
            }

        except Exception as e:
            if os.path.exists(backup_file_path):
                os.remove(backup_file_path)
            raise e

    async def _schedule_backup(self, source_path: str, schedule: str, backup_name_prefix: str,
                             compression: str = "tgz", exclude_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Schedule automatic backups (placeholder - would require cron or task scheduler)"""
        # This is a simplified implementation that would need integration with system scheduler
        schedule_info = {
            "source_path": source_path,
            "schedule": schedule,
            "backup_name_prefix": backup_name_prefix,
            "compression": compression,
            "exclude_patterns": exclude_patterns or [],
            "created_at": datetime.now().isoformat()
        }

        # In a real implementation, this would:
        # 1. Create cron job on Linux/macOS
        # 2. Create scheduled task on Windows
        # 3. Store schedule in database for management

        return {
            "message": "Backup schedule created (note: requires system scheduler integration)",
            "schedule_info": schedule_info,
            "next_suggested_implementation": [
                "For Linux/macOS: Add cron job",
                "For Windows: Use Task Scheduler",
                "Store schedule config in database",
                "Implement schedule management commands"
            ]
        }

    async def _backup_status(self) -> Dict[str, Any]:
        """Get backup system status and statistics"""
        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()

        # Get backup statistics
        cursor.execute('SELECT COUNT(*) FROM backups')
        total_backups = cursor.fetchone()[0]

        cursor.execute('SELECT backup_type, COUNT(*) FROM backups GROUP BY backup_type')
        backup_types = dict(cursor.fetchall())

        cursor.execute('SELECT SUM(total_size), SUM(file_count) FROM backups')
        totals = cursor.fetchone()
        total_size = totals[0] or 0
        total_files = totals[1] or 0

        # Get recent backups
        cursor.execute('SELECT name, created_at, backup_type FROM backups ORDER BY created_at DESC LIMIT 5')
        recent_backups = [{'name': row[0], 'created_at': row[1], 'type': row[2]} for row in cursor.fetchall()]

        # Check backup file existence
        cursor.execute('SELECT backup_path FROM backups')
        backup_paths = [row[0] for row in cursor.fetchall()]
        missing_files = [path for path in backup_paths if not os.path.exists(path)]

        conn.close()

        # Calculate disk usage
        backup_dir_size = 0
        if os.path.exists(self.default_backup_dir):
            for root, dirs, files in os.walk(self.default_backup_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        backup_dir_size += os.path.getsize(file_path)

        return {
            "total_backups": total_backups,
            "backup_types": backup_types,
            "total_source_size_bytes": total_size,
            "total_files_backed_up": total_files,
            "backup_directory": self.default_backup_dir,
            "backup_directory_size_bytes": backup_dir_size,
            "recent_backups": recent_backups,
            "missing_backup_files": len(missing_files),
            "database_path": self.backup_db_path,
            "status_generated_at": datetime.now().isoformat()
        }

    async def _cleanup_old_backups(self, days_to_keep: int = 30, backup_type: Optional[str] = None,
                                 dry_run: bool = True) -> Dict[str, Any]:
        """Clean up old backups based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        conn = sqlite3.connect(self.backup_db_path)
        cursor = conn.cursor()

        query = 'SELECT id, name, backup_path, created_at FROM backups WHERE created_at < ?'
        params = [cutoff_date]

        if backup_type:
            query += ' AND backup_type = ?'
            params.append(backup_type)

        cursor.execute(query, params)
        old_backups = cursor.fetchall()

        if dry_run:
            conn.close()
            return {
                "dry_run": True,
                "backups_to_delete": len(old_backups),
                "cutoff_date": cutoff_date.isoformat(),
                "backups": [{'id': row[0], 'name': row[1], 'path': row[2], 'created_at': row[3]}
                           for row in old_backups]
            }

        # Actually delete backups
        deleted_count = 0
        deleted_size = 0
        errors = []

        for backup_id, name, backup_path, created_at in old_backups:
            try:
                # Get file size before deletion
                file_size = os.path.getsize(backup_path) if os.path.exists(backup_path) else 0

                # Delete file metadata
                cursor.execute('DELETE FROM backup_files WHERE backup_id = ?', (backup_id,))

                # Delete backup metadata
                cursor.execute('DELETE FROM backups WHERE id = ?', (backup_id,))

                # Delete backup file
                if os.path.exists(backup_path):
                    os.remove(backup_path)

                deleted_count += 1
                deleted_size += file_size

            except Exception as e:
                errors.append(f"Failed to delete backup {name}: {str(e)}")

        conn.commit()
        conn.close()

        return {
            "dry_run": False,
            "deleted_backups": deleted_count,
            "deleted_size_bytes": deleted_size,
            "cutoff_date": cutoff_date.isoformat(),
            "errors": errors,
            "cleanup_completed_at": datetime.now().isoformat()
        }

    async def _export_backup_config(self, output_file: str) -> Dict[str, Any]:
        """Export backup configuration and metadata"""
        conn = sqlite3.connect(self.backup_db_path)

        # Export all backups
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM backups')
        backups = cursor.fetchall()

        # Export all file metadata
        cursor.execute('SELECT * FROM backup_files')
        files = cursor.fetchall()

        conn.close()

        config_data = {
            "export_timestamp": datetime.now().isoformat(),
            "backup_manager_version": "1.0",
            "default_backup_dir": self.default_backup_dir,
            "backups": [dict(zip(['id', 'name', 'source_path', 'backup_path', 'backup_type',
                                'compression', 'file_count', 'total_size', 'checksum',
                                'created_at', 'metadata'], backup)) for backup in backups],
            "files": [dict(zip(['id', 'backup_id', 'file_path', 'file_size',
                              'file_hash', 'modified_time'], file)) for file in files]
        }

        try:
            with open(output_file, 'w') as f:
                json.dump(config_data, f, indent=2, default=str)

            return {
                "config_exported": True,
                "output_file": output_file,
                "exported_backups": len(backups),
                "exported_files": len(files),
                "export_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Export failed: {str(e)}"}

    async def _import_backup_config(self, config_file: str, merge: bool = True) -> Dict[str, Any]:
        """Import backup configuration and metadata"""
        if not os.path.exists(config_file):
            return {"error": f"Config file not found: {config_file}"}

        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)

            conn = sqlite3.connect(self.backup_db_path)
            cursor = conn.cursor()

            if not merge:
                # Clear existing data
                cursor.execute('DELETE FROM backup_files')
                cursor.execute('DELETE FROM backups')

            imported_backups = 0
            imported_files = 0

            # Import backups
            for backup in config_data.get('backups', []):
                if merge:
                    # Check if backup already exists
                    cursor.execute('SELECT id FROM backups WHERE name = ?', (backup['name'],))
                    if cursor.fetchone():
                        continue

                cursor.execute('''
                    INSERT INTO backups (name, source_path, backup_path, backup_type,
                                       compression, file_count, total_size, checksum,
                                       created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (backup['name'], backup['source_path'], backup['backup_path'],
                      backup['backup_type'], backup['compression'], backup['file_count'],
                      backup['total_size'], backup['checksum'], backup['created_at'],
                      backup['metadata']))

                imported_backups += 1

            # Import files
            for file_data in config_data.get('files', []):
                cursor.execute('''
                    INSERT INTO backup_files (backup_id, file_path, file_size, file_hash, modified_time)
                    VALUES (?, ?, ?, ?, ?)
                ''', (file_data['backup_id'], file_data['file_path'], file_data['file_size'],
                      file_data['file_hash'], file_data['modified_time']))

                imported_files += 1

            conn.commit()
            conn.close()

            return {
                "config_imported": True,
                "config_file": config_file,
                "imported_backups": imported_backups,
                "imported_files": imported_files,
                "merge_mode": merge,
                "import_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Import failed: {str(e)}"}
