"""
Security Scanner Tool

This tool provides comprehensive security scanning and analysis capabilities including:
- Vulnerability scanning
- Password strength analysis
- File and directory permission checks
- Network security assessment
- Code security analysis
- Encryption/decryption utilities
- Security compliance checks
"""

import asyncio
import hashlib
import secrets
import string
import os
import stat
import socket
import ssl
import subprocess
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import ipaddress
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from .base import BaseTool


class SecurityScanner(BaseTool):
    """Tool for security scanning and analysis"""

    def __init__(self):
        super().__init__()
        self.name = "security_scanner"
        self.description = "Comprehensive security scanning and analysis tool"

        # Common vulnerable patterns
        self.vulnerable_patterns = {
            'sql_injection': [
                r'SELECT.*FROM.*WHERE.*=.*[\'"].*[\'"]',
                r'INSERT.*INTO.*VALUES.*[\'"].*[\'"]',
                r'UPDATE.*SET.*=.*[\'"].*[\'"]',
                r'DELETE.*FROM.*WHERE.*=.*[\'"].*[\'"]'
            ],
            'xss': [
                r'<script.*?>.*?</script>',
                r'javascript:',
                r'on\w+\s*=\s*[\'"].*[\'"]'
            ],
            'command_injection': [
                r'exec\s*\(',
                r'eval\s*\(',
                r'system\s*\(',
                r'shell_exec\s*\(',
                r'passthru\s*\('
            ],
            'path_traversal': [
                r'\.\./.*',
                r'\.\.\\.*',
                r'/etc/passwd',
                r'/etc/shadow'
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*[\'"][^\'"]+[\'"]',
                r'api_key\s*=\s*[\'"][^\'"]+[\'"]',
                r'secret\s*=\s*[\'"][^\'"]+[\'"]',
                r'token\s*=\s*[\'"][^\'"]+[\'"]'
            ]
        }

        # Port vulnerability database
        self.vulnerable_services = {
            21: "FTP - Often misconfigured",
            22: "SSH - Check for weak keys",
            23: "Telnet - Unencrypted protocol",
            25: "SMTP - Mail relay risks",
            53: "DNS - Cache poisoning risks",
            80: "HTTP - Unencrypted web traffic",
            110: "POP3 - Unencrypted email",
            139: "NetBIOS - Information disclosure",
            143: "IMAP - Unencrypted email",
            443: "HTTPS - Check SSL/TLS config",
            445: "SMB - Remote code execution risks",
            993: "IMAPS - Check certificate",
            995: "POP3S - Check certificate",
            1433: "MSSQL - Database security",
            3306: "MySQL - Database security",
            3389: "RDP - Remote access risks",
            5432: "PostgreSQL - Database security",
            6379: "Redis - Often unsecured",
            27017: "MongoDB - Often unsecured"
        }

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute security scanner commands"""
        try:
            if command == "scan_file":
                return await self._scan_file(**kwargs)
            elif command == "scan_directory":
                return await self._scan_directory(**kwargs)
            elif command == "check_password":
                return await self._check_password(**kwargs)
            elif command == "scan_network":
                return await self._scan_network(**kwargs)
            elif command == "check_permissions":
                return await self._check_permissions(**kwargs)
            elif command == "ssl_check":
                return await self._ssl_check(**kwargs)
            elif command == "encrypt_file":
                return await self._encrypt_file(**kwargs)
            elif command == "decrypt_file":
                return await self._decrypt_file(**kwargs)
            elif command == "generate_hash":
                return await self._generate_hash(**kwargs)
            elif command == "vulnerability_report":
                return await self._vulnerability_report(**kwargs)
            elif command == "security_audit":
                return await self._security_audit(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Security scanner error: {str(e)}"}

    async def _scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a single file for security vulnerabilities"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        vulnerabilities = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Check for vulnerable patterns
            for vuln_type, patterns in self.vulnerable_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                    for match in matches:
                        line_num = content[:match.start()].count('\n') + 1
                        vulnerabilities.append({
                            "type": vuln_type,
                            "line": line_num,
                            "match": match.group(),
                            "severity": self._get_severity(vuln_type),
                            "description": self._get_vulnerability_description(vuln_type)
                        })

            # Check file permissions
            file_stat = os.stat(file_path)
            permissions = stat.filemode(file_stat.st_mode)

            # Check for overly permissive files
            if file_stat.st_mode & 0o002:  # World writable
                vulnerabilities.append({
                    "type": "file_permissions",
                    "line": 0,
                    "match": permissions,
                    "severity": "medium",
                    "description": "File is world-writable"
                })

            if file_stat.st_mode & 0o004 and file_path.endswith(('.key', '.pem', '.p12')):  # World readable key file
                vulnerabilities.append({
                    "type": "file_permissions",
                    "line": 0,
                    "match": permissions,
                    "severity": "high",
                    "description": "Sensitive file is world-readable"
                })

            return {
                "file_path": file_path,
                "vulnerabilities_found": len(vulnerabilities),
                "vulnerabilities": vulnerabilities,
                "file_size": file_stat.st_size,
                "permissions": permissions,
                "scan_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Failed to scan file: {str(e)}"}

    async def _scan_directory(self, directory_path: str, recursive: bool = True, file_extensions: List[str] = None) -> Dict[str, Any]:
        """Scan directory for security vulnerabilities"""
        if not os.path.exists(directory_path):
            return {"error": f"Directory not found: {directory_path}"}

        if file_extensions is None:
            file_extensions = ['.py', '.js', '.php', '.java', '.cpp', '.c', '.sql', '.sh', '.bat']

        scanned_files = []
        total_vulnerabilities = 0
        vulnerability_summary = {}

        # Walk through directory
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)

                # Check if file extension matches
                if any(file_path.lower().endswith(ext) for ext in file_extensions):
                    scan_result = await self._scan_file(file_path)

                    if "vulnerabilities" in scan_result:
                        scanned_files.append(scan_result)
                        total_vulnerabilities += scan_result["vulnerabilities_found"]

                        # Update summary
                        for vuln in scan_result["vulnerabilities"]:
                            vuln_type = vuln["type"]
                            if vuln_type not in vulnerability_summary:
                                vulnerability_summary[vuln_type] = 0
                            vulnerability_summary[vuln_type] += 1

            if not recursive:
                break

        return {
            "directory_path": directory_path,
            "scanned_files": len(scanned_files),
            "total_vulnerabilities": total_vulnerabilities,
            "vulnerability_summary": vulnerability_summary,
            "detailed_results": scanned_files,
            "scan_timestamp": datetime.now().isoformat()
        }

    async def _check_password(self, password: str) -> Dict[str, Any]:
        """Analyze password strength and security"""
        score = 0
        feedback = []

        # Length check
        length = len(password)
        if length >= 12:
            score += 2
        elif length >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters long")

        # Character variety
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))

        char_types = sum([has_upper, has_lower, has_digit, has_special])
        score += char_types

        if not has_upper:
            feedback.append("Add uppercase letters")
        if not has_lower:
            feedback.append("Add lowercase letters")
        if not has_digit:
            feedback.append("Add numbers")
        if not has_special:
            feedback.append("Add special characters")

        # Pattern checks
        if re.search(r'(.)\1{2,}', password):  # Repeated characters
            score -= 1
            feedback.append("Avoid repeated characters")

        if re.search(r'(012|123|234|345|456|567|678|789|890)', password):  # Sequential numbers
            score -= 1
            feedback.append("Avoid sequential numbers")

        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
            score -= 1
            feedback.append("Avoid sequential letters")

        # Common password check
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]

        if password.lower() in common_passwords:
            score = 0
            feedback.append("This is a commonly used password")

        # Calculate entropy
        charset_size = 0
        if has_lower:
            charset_size += 26
        if has_upper:
            charset_size += 26
        if has_digit:
            charset_size += 10
        if has_special:
            charset_size += 32

        entropy = length * (charset_size.bit_length() - 1) if charset_size > 0 else 0

        # Determine strength
        if score >= 8:
            strength = "Very Strong"
        elif score >= 6:
            strength = "Strong"
        elif score >= 4:
            strength = "Medium"
        elif score >= 2:
            strength = "Weak"
        else:
            strength = "Very Weak"

        return {
            "password_length": length,
            "strength": strength,
            "score": max(0, score),
            "entropy_bits": entropy,
            "has_uppercase": has_upper,
            "has_lowercase": has_lower,
            "has_digits": has_digit,
            "has_special_chars": has_special,
            "feedback": feedback,
            "estimated_crack_time": self._estimate_crack_time(entropy)
        }

    def _estimate_crack_time(self, entropy_bits: int) -> str:
        """Estimate time to crack password based on entropy"""
        if entropy_bits < 28:
            return "Instantly"
        elif entropy_bits < 35:
            return "Minutes"
        elif entropy_bits < 45:
            return "Hours"
        elif entropy_bits < 55:
            return "Days"
        elif entropy_bits < 65:
            return "Years"
        else:
            return "Centuries"

    async def _scan_network(self, target: str, port_range: str = "1-1000") -> Dict[str, Any]:
        """Scan network target for security issues"""
        try:
            # Parse port range
            if '-' in port_range:
                start_port, end_port = map(int, port_range.split('-'))
            else:
                start_port = end_port = int(port_range)

            # Validate target
            try:
                target_ip = ipaddress.ip_address(target)
            except ValueError:
                # Try to resolve hostname
                try:
                    target_ip = socket.gethostbyname(target)
                except socket.gaierror:
                    return {"error": f"Cannot resolve target: {target}"}

            open_ports = []
            vulnerable_services = []

            # Port scan
            for port in range(start_port, end_port + 1):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)

                try:
                    result = sock.connect_ex((str(target_ip), port))
                    if result == 0:
                        open_ports.append(port)

                        # Check for known vulnerabilities
                        if port in self.vulnerable_services:
                            vulnerable_services.append({
                                "port": port,
                                "service": self.vulnerable_services[port],
                                "risk_level": self._get_port_risk_level(port)
                            })

                        # Try to grab banner
                        try:
                            sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
                            banner = sock.recv(1024).decode('utf-8', errors='ignore')
                            if banner:
                                vulnerable_services.append({
                                    "port": port,
                                    "banner": banner[:200],
                                    "risk_level": "info"
                                })
                        except:
                            pass
                except:
                    pass
                finally:
                    sock.close()

            return {
                "target": target,
                "target_ip": str(target_ip),
                "port_range": port_range,
                "open_ports": open_ports,
                "total_open_ports": len(open_ports),
                "vulnerable_services": vulnerable_services,
                "scan_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Network scan failed: {str(e)}"}

    def _get_port_risk_level(self, port: int) -> str:
        """Get risk level for specific port"""
        high_risk_ports = [21, 23, 25, 139, 445, 3389]
        medium_risk_ports = [22, 80, 110, 143, 993, 995]

        if port in high_risk_ports:
            return "high"
        elif port in medium_risk_ports:
            return "medium"
        else:
            return "low"

    async def _check_permissions(self, path: str) -> Dict[str, Any]:
        """Check file and directory permissions for security issues"""
        if not os.path.exists(path):
            return {"error": f"Path not found: {path}"}

        permission_issues = []

        def check_path_permissions(file_path: str) -> Dict[str, Any]:
            try:
                file_stat = os.stat(file_path)
                mode = file_stat.st_mode
                permissions = stat.filemode(mode)

                issues = []

                # Check for world-writable files
                if mode & 0o002:
                    issues.append({
                        "issue": "world_writable",
                        "severity": "high",
                        "description": "File/directory is writable by everyone"
                    })

                # Check for world-readable sensitive files
                if mode & 0o004:
                    if any(file_path.endswith(ext) for ext in ['.key', '.pem', '.p12', '.ppk', 'id_rsa', 'id_dsa']):
                        issues.append({
                            "issue": "sensitive_readable",
                            "severity": "high",
                            "description": "Sensitive file is readable by everyone"
                        })

                # Check for setuid/setgid files
                if mode & 0o4000:  # setuid
                    issues.append({
                        "issue": "setuid",
                        "severity": "medium",
                        "description": "File has setuid bit set"
                    })

                if mode & 0o2000:  # setgid
                    issues.append({
                        "issue": "setgid",
                        "severity": "medium",
                        "description": "File has setgid bit set"
                    })

                return {
                    "path": file_path,
                    "permissions": permissions,
                    "owner_uid": file_stat.st_uid,
                    "group_gid": file_stat.st_gid,
                    "issues": issues
                }

            except Exception as e:
                return {"path": file_path, "error": str(e)}

        if os.path.isfile(path):
            return check_path_permissions(path)
        else:
            # Directory scan
            results = []
            for root, dirs, files in os.walk(path):
                # Check directory permissions
                results.append(check_path_permissions(root))

                # Check file permissions
                for file in files:
                    file_path = os.path.join(root, file)
                    results.append(check_path_permissions(file_path))

            # Summarize issues
            total_issues = 0
            severity_count = {"high": 0, "medium": 0, "low": 0}

            for result in results:
                if "issues" in result:
                    total_issues += len(result["issues"])
                    for issue in result["issues"]:
                        severity_count[issue["severity"]] += 1

            return {
                "path": path,
                "total_items_checked": len(results),
                "total_issues": total_issues,
                "severity_breakdown": severity_count,
                "detailed_results": results,
                "scan_timestamp": datetime.now().isoformat()
            }

    async def _ssl_check(self, hostname: str, port: int = 443) -> Dict[str, Any]:
        """Check SSL/TLS configuration for security issues"""
        try:
            # Create SSL context
            context = ssl.create_default_context()

            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    version = ssock.version()

            # Analyze certificate
            cert_issues = []

            # Check expiration
            not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            days_until_expiry = (not_after - datetime.now()).days

            if days_until_expiry < 30:
                cert_issues.append({
                    "issue": "certificate_expiring",
                    "severity": "high" if days_until_expiry < 7 else "medium",
                    "description": f"Certificate expires in {days_until_expiry} days"
                })

            # Check for self-signed certificate
            if cert.get('issuer') == cert.get('subject'):
                cert_issues.append({
                    "issue": "self_signed",
                    "severity": "medium",
                    "description": "Certificate is self-signed"
                })

            # Check SSL/TLS version
            version_issues = []
            if version in ['SSLv2', 'SSLv3', 'TLSv1', 'TLSv1.1']:
                version_issues.append({
                    "issue": "weak_tls_version",
                    "severity": "high",
                    "description": f"Using weak TLS version: {version}"
                })

            # Check cipher suite
            cipher_issues = []
            if cipher and len(cipher) >= 3:
                cipher_name = cipher[0]
                if 'RC4' in cipher_name or 'DES' in cipher_name:
                    cipher_issues.append({
                        "issue": "weak_cipher",
                        "severity": "high",
                        "description": f"Using weak cipher: {cipher_name}"
                    })

            return {
                "hostname": hostname,
                "port": port,
                "certificate": {
                    "subject": dict(x[0] for x in cert['subject']),
                    "issuer": dict(x[0] for x in cert['issuer']),
                    "not_before": cert['notBefore'],
                    "not_after": cert['notAfter'],
                    "days_until_expiry": days_until_expiry,
                    "serial_number": cert['serialNumber'],
                    "version": cert['version']
                },
                "tls_version": version,
                "cipher_suite": cipher,
                "certificate_issues": cert_issues,
                "version_issues": version_issues,
                "cipher_issues": cipher_issues,
                "total_issues": len(cert_issues) + len(version_issues) + len(cipher_issues),
                "scan_timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"SSL check failed: {str(e)}"}

    async def _encrypt_file(self, file_path: str, password: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Encrypt file using password-based encryption"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}

            if output_path is None:
                output_path = file_path + ".encrypted"

            # Generate key from password
            password_bytes = password.encode()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))

            # Encrypt file
            fernet = Fernet(key)

            with open(file_path, 'rb') as f:
                file_data = f.read()

            encrypted_data = fernet.encrypt(file_data)

            # Save encrypted file with salt
            with open(output_path, 'wb') as f:
                f.write(salt + encrypted_data)

            return {
                "original_file": file_path,
                "encrypted_file": output_path,
                "original_size": len(file_data),
                "encrypted_size": len(salt + encrypted_data),
                "encryption_method": "AES-256 with PBKDF2",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Encryption failed: {str(e)}"}

    async def _decrypt_file(self, file_path: str, password: str, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Decrypt file using password-based decryption"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}

            if output_path is None:
                output_path = file_path.replace(".encrypted", "")
                if output_path == file_path:
                    output_path = file_path + ".decrypted"

            # Read encrypted file
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()

            # Extract salt and encrypted content
            salt = encrypted_data[:16]
            encrypted_content = encrypted_data[16:]

            # Generate key from password
            password_bytes = password.encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))

            # Decrypt file
            fernet = Fernet(key)
            decrypted_data = fernet.decrypt(encrypted_content)

            # Save decrypted file
            with open(output_path, 'wb') as f:
                f.write(decrypted_data)

            return {
                "encrypted_file": file_path,
                "decrypted_file": output_path,
                "encrypted_size": len(encrypted_data),
                "decrypted_size": len(decrypted_data),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Decryption failed: {str(e)}"}

    async def _generate_hash(self, text: str, algorithm: str = "sha256") -> Dict[str, Any]:
        """Generate cryptographic hash of text"""
        try:
            algorithms = {
                'md5': hashlib.md5,
                'sha1': hashlib.sha1,
                'sha256': hashlib.sha256,
                'sha512': hashlib.sha512
            }

            if algorithm not in algorithms:
                return {"error": f"Unsupported algorithm: {algorithm}"}

            hash_func = algorithms[algorithm]()
            hash_func.update(text.encode('utf-8'))
            hash_value = hash_func.hexdigest()

            # Security assessment of algorithm
            security_level = {
                'md5': 'weak',
                'sha1': 'weak',
                'sha256': 'strong',
                'sha512': 'strong'
            }

            return {
                "input_text": text,
                "algorithm": algorithm,
                "hash_value": hash_value,
                "security_level": security_level[algorithm],
                "hash_length": len(hash_value),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Hash generation failed: {str(e)}"}

    def _get_severity(self, vuln_type: str) -> str:
        """Get severity level for vulnerability type"""
        severity_map = {
            'sql_injection': 'critical',
            'xss': 'high',
            'command_injection': 'critical',
            'path_traversal': 'high',
            'hardcoded_secrets': 'high',
            'file_permissions': 'medium'
        }
        return severity_map.get(vuln_type, 'medium')

    def _get_vulnerability_description(self, vuln_type: str) -> str:
        """Get description for vulnerability type"""
        descriptions = {
            'sql_injection': 'Potential SQL injection vulnerability detected',
            'xss': 'Potential Cross-Site Scripting (XSS) vulnerability detected',
            'command_injection': 'Potential command injection vulnerability detected',
            'path_traversal': 'Potential path traversal vulnerability detected',
            'hardcoded_secrets': 'Hardcoded secret or credential detected',
            'file_permissions': 'Insecure file permissions detected'
        }
        return descriptions.get(vuln_type, 'Security issue detected')

    async def _vulnerability_report(self, scan_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive vulnerability report"""
        if not scan_results:
            return {"error": "No scan results provided"}

        total_vulnerabilities = 0
        severity_count = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        vulnerability_types = {}

        for result in scan_results:
            if "vulnerabilities" in result:
                total_vulnerabilities += len(result["vulnerabilities"])

                for vuln in result["vulnerabilities"]:
                    severity = vuln.get("severity", "medium")
                    vuln_type = vuln.get("type", "unknown")

                    severity_count[severity] += 1

                    if vuln_type not in vulnerability_types:
                        vulnerability_types[vuln_type] = 0
                    vulnerability_types[vuln_type] += 1

        # Calculate risk score
        risk_score = (
            severity_count["critical"] * 10 +
            severity_count["high"] * 7 +
            severity_count["medium"] * 4 +
            severity_count["low"] * 1
        )

        # Determine overall risk level
        if risk_score >= 50:
            risk_level = "Critical"
        elif risk_score >= 30:
            risk_level = "High"
        elif risk_score >= 15:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        return {
            "total_vulnerabilities": total_vulnerabilities,
            "severity_breakdown": severity_count,
            "vulnerability_types": vulnerability_types,
            "risk_score": risk_score,
            "overall_risk_level": risk_level,
            "scan_results": scan_results,
            "report_timestamp": datetime.now().isoformat(),
            "recommendations": self._get_security_recommendations(severity_count, vulnerability_types)
        }

    def _get_security_recommendations(self, severity_count: Dict[str, int], vulnerability_types: Dict[str, int]) -> List[str]:
        """Generate security recommendations based on findings"""
        recommendations = []

        if severity_count["critical"] > 0:
            recommendations.append("Immediately address critical vulnerabilities - system may be compromised")

        if severity_count["high"] > 0:
            recommendations.append("Prioritize fixing high-severity vulnerabilities within 24-48 hours")

        if "sql_injection" in vulnerability_types:
            recommendations.append("Implement parameterized queries and input validation to prevent SQL injection")

        if "xss" in vulnerability_types:
            recommendations.append("Implement proper output encoding and Content Security Policy (CSP)")

        if "command_injection" in vulnerability_types:
            recommendations.append("Avoid executing user input as system commands; use safer alternatives")

        if "hardcoded_secrets" in vulnerability_types:
            recommendations.append("Move secrets to environment variables or secure key management systems")

        if "file_permissions" in vulnerability_types:
            recommendations.append("Review and restrict file permissions following principle of least privilege")

        recommendations.append("Implement regular security scanning as part of development workflow")
        recommendations.append("Conduct security code reviews before deploying changes")

        return recommendations

    async def _security_audit(self, target_path: str) -> Dict[str, Any]:
        """Perform comprehensive security audit"""
        audit_results = {
            "audit_timestamp": datetime.now().isoformat(),
            "target_path": target_path,
            "checks_performed": []
        }

        # File/directory scan
        if os.path.exists(target_path):
            file_scan = await self._scan_directory(target_path)
            audit_results["file_vulnerabilities"] = file_scan
            audit_results["checks_performed"].append("file_vulnerability_scan")

            # Permission check
            perm_check = await self._check_permissions(target_path)
            audit_results["permission_issues"] = perm_check
            audit_results["checks_performed"].append("permission_check")

        # Network scan (if target looks like IP/hostname)
        try:
            socket.inet_aton(target_path)  # Check if it's an IP
            network_scan = await self._scan_network(target_path)
            audit_results["network_vulnerabilities"] = network_scan
            audit_results["checks_performed"].append("network_scan")
        except socket.error:
            pass

        # Generate summary
        total_issues = 0
        if "file_vulnerabilities" in audit_results:
            total_issues += audit_results["file_vulnerabilities"].get("total_vulnerabilities", 0)
        if "permission_issues" in audit_results:
            total_issues += audit_results["permission_issues"].get("total_issues", 0)
        if "network_vulnerabilities" in audit_results:
            total_issues += len(audit_results["network_vulnerabilities"].get("vulnerable_services", []))

        audit_results["summary"] = {
            "total_security_issues": total_issues,
            "checks_completed": len(audit_results["checks_performed"]),
            "audit_status": "completed"
        }

        return audit_results
