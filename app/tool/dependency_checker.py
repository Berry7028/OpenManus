"""
Dependency Checker Tool

This tool provides comprehensive dependency management and analysis capabilities including:
- Package dependency analysis and visualization
- Version compatibility checking
- Security vulnerability scanning
- License compliance checking
- Dependency graph generation
- Outdated package detection
- Dependency conflict resolution
"""

import asyncio
import json
import subprocess
import re
import os
import sys
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime
import requests
from packaging import version
from .base import BaseTool


class DependencyChecker(BaseTool):
    """Tool for dependency analysis and management"""

    def __init__(self):
        super().__init__()
        self.name = "dependency_checker"
        self.description = "Comprehensive dependency analysis and management tool"

        # Package managers and their configurations
        self.package_managers = {
            'pip': {
                'list_cmd': 'pip list --format=json',
                'show_cmd': 'pip show',
                'outdated_cmd': 'pip list --outdated --format=json',
                'requirements_files': ['requirements.txt', 'requirements-dev.txt', 'setup.py'],
                'lock_files': ['pip.lock', 'requirements.lock']
            },
            'npm': {
                'list_cmd': 'npm list --json --depth=0',
                'show_cmd': 'npm show',
                'outdated_cmd': 'npm outdated --json',
                'requirements_files': ['package.json'],
                'lock_files': ['package-lock.json', 'yarn.lock']
            },
            'yarn': {
                'list_cmd': 'yarn list --json --depth=0',
                'show_cmd': 'yarn info',
                'outdated_cmd': 'yarn outdated --json',
                'requirements_files': ['package.json'],
                'lock_files': ['yarn.lock']
            },
            'conda': {
                'list_cmd': 'conda list --json',
                'show_cmd': 'conda info',
                'outdated_cmd': 'conda search --outdated --json',
                'requirements_files': ['environment.yml', 'conda.yml'],
                'lock_files': ['conda-lock.yml']
            }
        }

        # Known vulnerability databases
        self.vuln_databases = {
            'python': 'https://pyup.io/api/v1/safety/',
            'npm': 'https://registry.npmjs.org/-/npm/v1/security/audits',
            'github': 'https://api.github.com/advisories'
        }

        # Cache for package information
        self.package_cache = {}
        self.vulnerability_cache = {}

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute dependency checker commands"""
        try:
            if command == "analyze_dependencies":
                return await self._analyze_dependencies(**kwargs)
            elif command == "check_vulnerabilities":
                return await self._check_vulnerabilities(**kwargs)
            elif command == "check_outdated":
                return await self._check_outdated(**kwargs)
            elif command == "dependency_graph":
                return await self._dependency_graph(**kwargs)
            elif command == "license_check":
                return await self._license_check(**kwargs)
            elif command == "conflict_resolution":
                return await self._conflict_resolution(**kwargs)
            elif command == "compatibility_check":
                return await self._compatibility_check(**kwargs)
            elif command == "security_audit":
                return await self._security_audit(**kwargs)
            elif command == "update_recommendations":
                return await self._update_recommendations(**kwargs)
            elif command == "dependency_report":
                return await self._dependency_report(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Dependency checker error: {str(e)}"}

    async def _analyze_dependencies(self, package_manager: str = "auto",
                                  project_path: str = ".", depth: int = 1) -> Dict[str, Any]:
        """Analyze project dependencies"""
        if package_manager == "auto":
            package_manager = self._detect_package_manager(project_path)

        if package_manager not in self.package_managers:
            return {"error": f"Unsupported package manager: {package_manager}"}

        pm_config = self.package_managers[package_manager]

        try:
            # Get installed packages
            result = await self._run_command(pm_config['list_cmd'], cwd=project_path)
            if result['return_code'] != 0:
                return {"error": f"Failed to list packages: {result['stderr']}"}

            # Parse package list
            packages = self._parse_package_list(result['stdout'], package_manager)

            # Analyze each package
            analysis_results = {
                "package_manager": package_manager,
                "project_path": project_path,
                "total_packages": len(packages),
                "packages": [],
                "summary": {
                    "direct_dependencies": 0,
                    "transitive_dependencies": 0,
                    "development_dependencies": 0,
                    "production_dependencies": 0
                },
                "analyzed_at": datetime.now().isoformat()
            }

            for package in packages:
                package_info = await self._get_package_info(
                    package['name'], package['version'], package_manager
                )

                package_analysis = {
                    "name": package['name'],
                    "version": package['version'],
                    "type": package.get('type', 'production'),
                    "dependencies": package_info.get('dependencies', []),
                    "license": package_info.get('license'),
                    "homepage": package_info.get('homepage'),
                    "description": package_info.get('description', '')[:200],
                    "last_update": package_info.get('last_update'),
                    "size": package_info.get('size', 0)
                }

                analysis_results["packages"].append(package_analysis)

                # Update summary
                if package.get('type') == 'development':
                    analysis_results["summary"]["development_dependencies"] += 1
                else:
                    analysis_results["summary"]["production_dependencies"] += 1

                if package.get('is_direct', True):
                    analysis_results["summary"]["direct_dependencies"] += 1
                else:
                    analysis_results["summary"]["transitive_dependencies"] += 1

            return analysis_results

        except Exception as e:
            return {"error": f"Dependency analysis failed: {str(e)}"}

    def _detect_package_manager(self, project_path: str) -> str:
        """Auto-detect package manager based on project files"""
        for pm, config in self.package_managers.items():
            for req_file in config['requirements_files']:
                if os.path.exists(os.path.join(project_path, req_file)):
                    return pm

        # Default fallback
        return "pip"

    def _parse_package_list(self, output: str, package_manager: str) -> List[Dict[str, Any]]:
        """Parse package list output for different package managers"""
        packages = []

        try:
            if package_manager == "pip":
                data = json.loads(output)
                for item in data:
                    packages.append({
                        "name": item["name"],
                        "version": item["version"],
                        "type": "production",
                        "is_direct": True  # pip doesn't distinguish easily
                    })

            elif package_manager in ["npm", "yarn"]:
                data = json.loads(output)
                dependencies = data.get("dependencies", {})

                for name, info in dependencies.items():
                    packages.append({
                        "name": name,
                        "version": info.get("version", "unknown"),
                        "type": "production",
                        "is_direct": True
                    })

            elif package_manager == "conda":
                data = json.loads(output)
                for item in data:
                    packages.append({
                        "name": item["name"],
                        "version": item["version"],
                        "type": "production",
                        "is_direct": True,
                        "channel": item.get("channel", "unknown")
                    })

        except json.JSONDecodeError:
            # Fallback to text parsing
            lines = output.strip().split('\n')
            for line in lines:
                if line and not line.startswith('#'):
                    parts = line.split()
                    if len(parts) >= 2:
                        packages.append({
                            "name": parts[0],
                            "version": parts[1],
                            "type": "production",
                            "is_direct": True
                        })

        return packages

    async def _get_package_info(self, package_name: str, version: str,
                              package_manager: str) -> Dict[str, Any]:
        """Get detailed package information"""
        cache_key = f"{package_manager}:{package_name}:{version}"

        if cache_key in self.package_cache:
            return self.package_cache[cache_key]

        try:
            pm_config = self.package_managers[package_manager]
            result = await self._run_command(f"{pm_config['show_cmd']} {package_name}")

            if result['return_code'] == 0:
                package_info = self._parse_package_info(result['stdout'], package_manager)
            else:
                package_info = {"name": package_name, "version": version}

            self.package_cache[cache_key] = package_info
            return package_info

        except Exception:
            return {"name": package_name, "version": version}

    def _parse_package_info(self, output: str, package_manager: str) -> Dict[str, Any]:
        """Parse package information from show command output"""
        info = {}

        if package_manager == "pip":
            lines = output.split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace('-', '_')
                    value = value.strip()

                    if key == "requires":
                        info["dependencies"] = [dep.strip() for dep in value.split(',') if dep.strip()]
                    elif key in ["license", "home_page", "summary", "version"]:
                        info[key.replace('home_page', 'homepage').replace('summary', 'description')] = value

        elif package_manager in ["npm", "yarn"]:
            try:
                data = json.loads(output)
                info = {
                    "license": data.get("license"),
                    "homepage": data.get("homepage"),
                    "description": data.get("description"),
                    "dependencies": list(data.get("dependencies", {}).keys()),
                    "version": data.get("version")
                }
            except json.JSONDecodeError:
                pass

        return info

    async def _check_vulnerabilities(self, package_manager: str = "auto",
                                   project_path: str = ".") -> Dict[str, Any]:
        """Check for known security vulnerabilities"""
        if package_manager == "auto":
            package_manager = self._detect_package_manager(project_path)

        # Get package list
        analysis = await self._analyze_dependencies(package_manager, project_path)
        if "error" in analysis:
            return analysis

        vulnerabilities = []
        checked_packages = []

        for package in analysis["packages"]:
            package_name = package["name"]
            package_version = package["version"]

            # Check against vulnerability databases
            vulns = await self._check_package_vulnerabilities(
                package_name, package_version, package_manager
            )

            if vulns:
                vulnerabilities.extend(vulns)

            checked_packages.append({
                "name": package_name,
                "version": package_version,
                "vulnerabilities": len(vulns),
                "severity_levels": [v.get("severity", "unknown") for v in vulns]
            })

        # Categorize vulnerabilities by severity
        severity_count = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
        for vuln in vulnerabilities:
            severity = vuln.get("severity", "unknown").lower()
            if severity in severity_count:
                severity_count[severity] += 1
            else:
                severity_count["unknown"] += 1

        return {
            "package_manager": package_manager,
            "project_path": project_path,
            "total_packages_checked": len(checked_packages),
            "total_vulnerabilities": len(vulnerabilities),
            "severity_breakdown": severity_count,
            "vulnerabilities": vulnerabilities,
            "checked_packages": checked_packages,
            "scan_completed_at": datetime.now().isoformat()
        }

    async def _check_package_vulnerabilities(self, package_name: str, package_version: str,
                                           package_manager: str) -> List[Dict[str, Any]]:
        """Check specific package for vulnerabilities"""
        cache_key = f"vuln:{package_manager}:{package_name}:{package_version}"

        if cache_key in self.vulnerability_cache:
            return self.vulnerability_cache[cache_key]

        vulnerabilities = []

        try:
            # For Python packages, use safety database
            if package_manager == "pip":
                # Simplified vulnerability check (in real implementation, use safety API)
                known_vulns = {
                    "django": ["1.11.0", "2.0.0", "2.1.0"],
                    "flask": ["0.12.0", "1.0.0"],
                    "requests": ["2.19.0", "2.20.0"]
                }

                if package_name.lower() in known_vulns:
                    for vuln_version in known_vulns[package_name.lower()]:
                        if version.parse(package_version) <= version.parse(vuln_version):
                            vulnerabilities.append({
                                "package": package_name,
                                "version": package_version,
                                "vulnerability_id": f"VULN-{package_name}-{vuln_version}",
                                "severity": "high",
                                "description": f"Known vulnerability in {package_name} {vuln_version}",
                                "fixed_in": "latest",
                                "source": "example_database"
                            })

            # For Node packages, check npm audit (simplified)
            elif package_manager in ["npm", "yarn"]:
                # Run npm audit for real vulnerability checking
                audit_result = await self._run_command("npm audit --json")
                if audit_result['return_code'] == 0:
                    try:
                        audit_data = json.loads(audit_result['stdout'])
                        advisories = audit_data.get("advisories", {})

                        for advisory_id, advisory in advisories.items():
                            if package_name in advisory.get("module_name", ""):
                                vulnerabilities.append({
                                    "package": package_name,
                                    "version": package_version,
                                    "vulnerability_id": advisory_id,
                                    "severity": advisory.get("severity", "unknown"),
                                    "description": advisory.get("title", ""),
                                    "fixed_in": advisory.get("patched_versions", "unknown"),
                                    "source": "npm_audit"
                                })
                    except json.JSONDecodeError:
                        pass

        except Exception:
            pass  # Continue on error

        self.vulnerability_cache[cache_key] = vulnerabilities
        return vulnerabilities

    async def _check_outdated(self, package_manager: str = "auto",
                            project_path: str = ".") -> Dict[str, Any]:
        """Check for outdated packages"""
        if package_manager == "auto":
            package_manager = self._detect_package_manager(project_path)

        if package_manager not in self.package_managers:
            return {"error": f"Unsupported package manager: {package_manager}"}

        pm_config = self.package_managers[package_manager]

        try:
            result = await self._run_command(pm_config['outdated_cmd'], cwd=project_path)

            # Parse outdated packages
            outdated_packages = []

            if package_manager == "pip":
                if result['return_code'] == 0:
                    try:
                        data = json.loads(result['stdout'])
                        for item in data:
                            outdated_packages.append({
                                "name": item["name"],
                                "current_version": item["version"],
                                "latest_version": item.get("latest_version", "unknown"),
                                "type": item.get("latest_filetype", "wheel")
                            })
                    except json.JSONDecodeError:
                        pass

            elif package_manager in ["npm", "yarn"]:
                if result['return_code'] == 0:
                    try:
                        data = json.loads(result['stdout'])
                        for name, info in data.items():
                            outdated_packages.append({
                                "name": name,
                                "current_version": info.get("current", "unknown"),
                                "latest_version": info.get("latest", "unknown"),
                                "wanted_version": info.get("wanted", "unknown")
                            })
                    except json.JSONDecodeError:
                        pass

            # Calculate update recommendations
            update_recommendations = []
            for pkg in outdated_packages:
                try:
                    current = version.parse(pkg["current_version"])
                    latest = version.parse(pkg["latest_version"])

                    if latest > current:
                        update_type = "patch"
                        if latest.major > current.major:
                            update_type = "major"
                        elif latest.minor > current.minor:
                            update_type = "minor"

                        update_recommendations.append({
                            "package": pkg["name"],
                            "current": pkg["current_version"],
                            "latest": pkg["latest_version"],
                            "update_type": update_type,
                            "priority": "high" if update_type == "patch" else "medium"
                        })

                except Exception:
                    continue

            return {
                "package_manager": package_manager,
                "project_path": project_path,
                "outdated_packages": outdated_packages,
                "update_recommendations": update_recommendations,
                "total_outdated": len(outdated_packages),
                "checked_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Outdated check failed: {str(e)}"}

    async def _dependency_graph(self, package_manager: str = "auto",
                              project_path: str = ".", output_format: str = "json") -> Dict[str, Any]:
        """Generate dependency graph"""
        if package_manager == "auto":
            package_manager = self._detect_package_manager(project_path)

        # Get dependency analysis
        analysis = await self._analyze_dependencies(package_manager, project_path, depth=2)
        if "error" in analysis:
            return analysis

        # Build dependency graph
        graph = {
            "nodes": [],
            "edges": [],
            "metadata": {
                "package_manager": package_manager,
                "total_packages": analysis["total_packages"],
                "generated_at": datetime.now().isoformat()
            }
        }

        # Add nodes (packages)
        for package in analysis["packages"]:
            graph["nodes"].append({
                "id": package["name"],
                "label": f"{package['name']} ({package['version']})",
                "version": package["version"],
                "type": package.get("type", "production"),
                "license": package.get("license", "unknown"),
                "size": package.get("size", 0)
            })

            # Add edges (dependencies)
            for dep in package.get("dependencies", []):
                # Clean dependency name (remove version specifiers)
                dep_name = re.split(r'[<>=!]', dep)[0].strip()

                graph["edges"].append({
                    "source": package["name"],
                    "target": dep_name,
                    "type": "depends_on"
                })

        # Calculate graph statistics
        stats = self._calculate_graph_stats(graph)
        graph["metadata"]["statistics"] = stats

        if output_format == "dot":
            # Generate Graphviz DOT format
            dot_content = self._generate_dot_graph(graph)
            return {
                "format": "dot",
                "content": dot_content,
                "metadata": graph["metadata"]
            }

        return {
            "format": "json",
            "graph": graph
        }

    def _calculate_graph_stats(self, graph: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate graph statistics"""
        nodes = graph["nodes"]
        edges = graph["edges"]

        # Count node types
        node_types = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1

        # Calculate degree statistics
        in_degrees = {}
        out_degrees = {}

        for edge in edges:
            source = edge["source"]
            target = edge["target"]

            out_degrees[source] = out_degrees.get(source, 0) + 1
            in_degrees[target] = in_degrees.get(target, 0) + 1

        # Find packages with highest dependencies
        most_dependencies = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        most_dependents = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": node_types,
            "average_dependencies": sum(out_degrees.values()) / len(nodes) if nodes else 0,
            "packages_with_most_dependencies": most_dependencies,
            "packages_with_most_dependents": most_dependents
        }

    def _generate_dot_graph(self, graph: Dict[str, Any]) -> str:
        """Generate Graphviz DOT format"""
        dot_lines = ["digraph Dependencies {"]
        dot_lines.append("  rankdir=TB;")
        dot_lines.append("  node [shape=box];")

        # Add nodes
        for node in graph["nodes"]:
            node_id = node["id"].replace("-", "_").replace(".", "_")
            label = node["label"].replace('"', '\\"')
            color = "lightblue" if node.get("type") == "development" else "lightgreen"

            dot_lines.append(f'  "{node_id}" [label="{label}" fillcolor="{color}" style=filled];')

        # Add edges
        for edge in graph["edges"]:
            source = edge["source"].replace("-", "_").replace(".", "_")
            target = edge["target"].replace("-", "_").replace(".", "_")
            dot_lines.append(f'  "{source}" -> "{target}";')

        dot_lines.append("}")
        return "\n".join(dot_lines)

    async def _license_check(self, package_manager: str = "auto",
                           project_path: str = ".") -> Dict[str, Any]:
        """Check package licenses for compliance"""
        if package_manager == "auto":
            package_manager = self._detect_package_manager(project_path)

        # Get dependency analysis
        analysis = await self._analyze_dependencies(package_manager, project_path)
        if "error" in analysis:
            return analysis

        # License categories
        license_categories = {
            "permissive": ["MIT", "BSD", "Apache", "ISC", "WTFPL"],
            "copyleft": ["GPL", "AGPL", "LGPL"],
            "proprietary": ["Commercial", "Proprietary"],
            "unknown": ["UNKNOWN", ""]
        }

        license_analysis = {
            "package_manager": package_manager,
            "project_path": project_path,
            "total_packages": len(analysis["packages"]),
            "license_summary": {cat: 0 for cat in license_categories.keys()},
            "license_details": {},
            "compliance_issues": [],
            "analyzed_at": datetime.now().isoformat()
        }

        for package in analysis["packages"]:
            package_license = package.get("license", "UNKNOWN")

            # Categorize license
            category = "unknown"
            for cat, licenses in license_categories.items():
                if any(lic.lower() in package_license.lower() for lic in licenses):
                    category = cat
                    break

            license_analysis["license_summary"][category] += 1

            if package_license not in license_analysis["license_details"]:
                license_analysis["license_details"][package_license] = []

            license_analysis["license_details"][package_license].append({
                "name": package["name"],
                "version": package["version"]
            })

            # Check for compliance issues
            if category == "copyleft" and package.get("type") == "production":
                license_analysis["compliance_issues"].append({
                    "package": package["name"],
                    "version": package["version"],
                    "license": package_license,
                    "issue": "Copyleft license in production dependency",
                    "severity": "medium"
                })

            elif category == "unknown":
                license_analysis["compliance_issues"].append({
                    "package": package["name"],
                    "version": package["version"],
                    "license": package_license,
                    "issue": "Unknown or missing license",
                    "severity": "low"
                })

        return license_analysis

    async def _conflict_resolution(self, package_manager: str = "auto",
                                 project_path: str = ".") -> Dict[str, Any]:
        """Detect and suggest resolution for dependency conflicts"""
        if package_manager == "auto":
            package_manager = self._detect_package_manager(project_path)

        # Get dependency analysis
        analysis = await self._analyze_dependencies(package_manager, project_path)
        if "error" in analysis:
            return analysis

        conflicts = []
        version_conflicts = {}

        # Check for version conflicts
        package_versions = {}
        for package in analysis["packages"]:
            name = package["name"]
            version_str = package["version"]

            if name not in package_versions:
                package_versions[name] = []
            package_versions[name].append(version_str)

        # Find packages with multiple versions
        for package_name, versions in package_versions.items():
            if len(set(versions)) > 1:
                conflicts.append({
                    "type": "version_conflict",
                    "package": package_name,
                    "versions": list(set(versions)),
                    "description": f"Multiple versions of {package_name} detected",
                    "severity": "high",
                    "resolution": f"Consolidate to single version of {package_name}"
                })

        # Check for dependency cycles (simplified)
        dependency_map = {}
        for package in analysis["packages"]:
            dependency_map[package["name"]] = package.get("dependencies", [])

        cycles = self._detect_cycles(dependency_map)
        for cycle in cycles:
            conflicts.append({
                "type": "circular_dependency",
                "packages": cycle,
                "description": f"Circular dependency detected: {' -> '.join(cycle)}",
                "severity": "medium",
                "resolution": "Review and break circular dependency"
            })

        # Generate resolution recommendations
        recommendations = []
        for conflict in conflicts:
            if conflict["type"] == "version_conflict":
                latest_version = max(conflict["versions"], key=lambda v: version.parse(v))
                recommendations.append({
                    "conflict": conflict["package"],
                    "action": "update_all_to_latest",
                    "target_version": latest_version,
                    "command": f"Update all dependencies of {conflict['package']} to {latest_version}"
                })

        return {
            "package_manager": package_manager,
            "project_path": project_path,
            "conflicts_detected": len(conflicts),
            "conflicts": conflicts,
            "recommendations": recommendations,
            "analyzed_at": datetime.now().isoformat()
        }

    def _detect_cycles(self, dependency_map: Dict[str, List[str]]) -> List[List[str]]:
        """Detect circular dependencies"""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True

            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            dependencies = dependency_map.get(node, [])
            for dep in dependencies:
                # Clean dependency name
                dep_name = re.split(r'[<>=!]', dep)[0].strip()
                if dep_name in dependency_map:
                    dfs(dep_name, path + [node])

            rec_stack.remove(node)
            return False

        for package in dependency_map:
            if package not in visited:
                dfs(package, [])

        return cycles

    async def _compatibility_check(self, package_manager: str = "auto",
                                 project_path: str = ".", python_version: str = None) -> Dict[str, Any]:
        """Check package compatibility with target environment"""
        if package_manager == "auto":
            package_manager = self._detect_package_manager(project_path)

        if python_version is None:
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"

        # Get dependency analysis
        analysis = await self._analyze_dependencies(package_manager, project_path)
        if "error" in analysis:
            return analysis

        compatibility_results = {
            "package_manager": package_manager,
            "target_python_version": python_version,
            "compatible_packages": [],
            "incompatible_packages": [],
            "unknown_compatibility": [],
            "checked_at": datetime.now().isoformat()
        }

        for package in analysis["packages"]:
            package_name = package["name"]
            package_version = package["version"]

            # Check Python version compatibility (simplified)
            compatibility = await self._check_python_compatibility(
                package_name, package_version, python_version
            )

            if compatibility["status"] == "compatible":
                compatibility_results["compatible_packages"].append({
                    "name": package_name,
                    "version": package_version,
                    "supported_versions": compatibility.get("supported_versions", [])
                })
            elif compatibility["status"] == "incompatible":
                compatibility_results["incompatible_packages"].append({
                    "name": package_name,
                    "version": package_version,
                    "issue": compatibility.get("issue", "Unknown compatibility issue"),
                    "required_python": compatibility.get("required_python", "unknown")
                })
            else:
                compatibility_results["unknown_compatibility"].append({
                    "name": package_name,
                    "version": package_version,
                    "reason": "Compatibility information not available"
                })

        return compatibility_results

    async def _check_python_compatibility(self, package_name: str, package_version: str,
                                        target_python: str) -> Dict[str, Any]:
        """Check if package is compatible with target Python version"""
        try:
            # This is a simplified check - in real implementation,
            # would query PyPI API for requires_python information

            # Some known compatibility issues
            known_issues = {
                "asyncio": {"min_python": "3.7", "max_python": None},
                "typing": {"min_python": "3.5", "max_python": "3.9"},
                "dataclasses": {"min_python": "3.7", "max_python": None}
            }

            if package_name in known_issues:
                info = known_issues[package_name]
                target_version = version.parse(target_python)

                if info["min_python"]:
                    min_version = version.parse(info["min_python"])
                    if target_version < min_version:
                        return {
                            "status": "incompatible",
                            "issue": f"Requires Python >= {info['min_python']}",
                            "required_python": f">= {info['min_python']}"
                        }

                if info["max_python"]:
                    max_version = version.parse(info["max_python"])
                    if target_version > max_version:
                        return {
                            "status": "incompatible",
                            "issue": f"Not compatible with Python > {info['max_python']}",
                            "required_python": f"<= {info['max_python']}"
                        }

                return {"status": "compatible"}

            # Default to unknown for packages not in our database
            return {"status": "unknown"}

        except Exception:
            return {"status": "unknown"}

    async def _security_audit(self, package_manager: str = "auto",
                            project_path: str = ".") -> Dict[str, Any]:
        """Comprehensive security audit of dependencies"""
        # Combine vulnerability check with additional security analysis
        vuln_results = await self._check_vulnerabilities(package_manager, project_path)
        if "error" in vuln_results:
            return vuln_results

        license_results = await self._license_check(package_manager, project_path)
        outdated_results = await self._check_outdated(package_manager, project_path)

        # Calculate security score
        total_packages = vuln_results["total_packages_checked"]
        vuln_count = vuln_results["total_vulnerabilities"]
        critical_vulns = vuln_results["severity_breakdown"]["critical"]
        high_vulns = vuln_results["severity_breakdown"]["high"]
        outdated_count = len(outdated_results.get("outdated_packages", []))

        # Security score calculation (0-100)
        security_score = 100
        security_score -= min(50, critical_vulns * 20)  # Critical vulns heavily penalized
        security_score -= min(30, high_vulns * 10)     # High vulns moderately penalized
        security_score -= min(20, (outdated_count / total_packages) * 20)  # Outdated packages

        security_score = max(0, security_score)

        # Generate security recommendations
        recommendations = []

        if critical_vulns > 0:
            recommendations.append({
                "priority": "critical",
                "action": "update_vulnerable_packages",
                "description": f"Immediately update {critical_vulns} packages with critical vulnerabilities"
            })

        if outdated_count > total_packages * 0.3:
            recommendations.append({
                "priority": "medium",
                "action": "update_outdated_packages",
                "description": f"Update {outdated_count} outdated packages to latest versions"
            })

        if license_results.get("compliance_issues"):
            recommendations.append({
                "priority": "low",
                "action": "review_licenses",
                "description": "Review license compliance issues"
            })

        return {
            "security_score": round(security_score, 1),
            "audit_summary": {
                "total_packages": total_packages,
                "vulnerable_packages": vuln_count,
                "outdated_packages": outdated_count,
                "license_issues": len(license_results.get("compliance_issues", []))
            },
            "vulnerability_details": vuln_results,
            "outdated_details": outdated_results,
            "license_details": license_results,
            "security_recommendations": recommendations,
            "audit_completed_at": datetime.now().isoformat()
        }

    async def _update_recommendations(self, package_manager: str = "auto",
                                    project_path: str = ".") -> Dict[str, Any]:
        """Generate package update recommendations"""
        outdated_results = await self._check_outdated(package_manager, project_path)
        if "error" in outdated_results:
            return outdated_results

        vuln_results = await self._check_vulnerabilities(package_manager, project_path)

        recommendations = []

        # Priority 1: Security updates
        for vuln in vuln_results.get("vulnerabilities", []):
            if vuln.get("severity") in ["critical", "high"]:
                recommendations.append({
                    "package": vuln["package"],
                    "current_version": vuln["version"],
                    "recommended_action": "security_update",
                    "target_version": vuln.get("fixed_in", "latest"),
                    "priority": "critical" if vuln["severity"] == "critical" else "high",
                    "reason": f"Security vulnerability: {vuln['description']}"
                })

        # Priority 2: Major version updates with breaking changes
        for update in outdated_results.get("update_recommendations", []):
            if update["update_type"] == "major":
                recommendations.append({
                    "package": update["package"],
                    "current_version": update["current"],
                    "recommended_action": "major_update",
                    "target_version": update["latest"],
                    "priority": "low",
                    "reason": "Major version update available (may have breaking changes)"
                })

        # Priority 3: Minor and patch updates
        for update in outdated_results.get("update_recommendations", []):
            if update["update_type"] in ["minor", "patch"]:
                recommendations.append({
                    "package": update["package"],
                    "current_version": update["current"],
                    "recommended_action": "safe_update",
                    "target_version": update["latest"],
                    "priority": "medium",
                    "reason": f"{update['update_type'].title()} update available"
                })

        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 4))

        return {
            "package_manager": package_manager,
            "project_path": project_path,
            "total_recommendations": len(recommendations),
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }

    async def _dependency_report(self, package_manager: str = "auto",
                               project_path: str = ".", output_format: str = "json") -> Dict[str, Any]:
        """Generate comprehensive dependency report"""
        # Gather all analyses
        dependency_analysis = await self._analyze_dependencies(package_manager, project_path)
        vulnerability_analysis = await self._check_vulnerabilities(package_manager, project_path)
        license_analysis = await self._license_check(package_manager, project_path)
        outdated_analysis = await self._check_outdated(package_manager, project_path)
        security_audit = await self._security_audit(package_manager, project_path)

        report = {
            "report_metadata": {
                "package_manager": package_manager,
                "project_path": project_path,
                "generated_at": datetime.now().isoformat(),
                "report_version": "1.0"
            },
            "executive_summary": {
                "total_packages": dependency_analysis.get("total_packages", 0),
                "security_score": security_audit.get("security_score", 0),
                "vulnerabilities": vulnerability_analysis.get("total_vulnerabilities", 0),
                "outdated_packages": len(outdated_analysis.get("outdated_packages", [])),
                "license_issues": len(license_analysis.get("compliance_issues", []))
            },
            "detailed_analysis": {
                "dependencies": dependency_analysis,
                "vulnerabilities": vulnerability_analysis,
                "licenses": license_analysis,
                "outdated": outdated_analysis,
                "security_audit": security_audit
            }
        }

        if output_format == "markdown":
            # Generate markdown report
            markdown_content = self._generate_markdown_report(report)
            return {
                "format": "markdown",
                "content": markdown_content
            }

        return {
            "format": "json",
            "report": report
        }

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown format report"""
        metadata = report["report_metadata"]
        summary = report["executive_summary"]

        markdown_lines = [
            f"# Dependency Analysis Report",
            f"",
            f"**Project:** {metadata['project_path']}",
            f"**Package Manager:** {metadata['package_manager']}",
            f"**Generated:** {metadata['generated_at']}",
            f"",
            f"## Executive Summary",
            f"",
            f"- **Total Packages:** {summary['total_packages']}",
            f"- **Security Score:** {summary['security_score']}/100",
            f"- **Vulnerabilities:** {summary['vulnerabilities']}",
            f"- **Outdated Packages:** {summary['outdated_packages']}",
            f"- **License Issues:** {summary['license_issues']}",
            f"",
            f"## Security Analysis",
            f"",
        ]

        # Add vulnerability details
        vulns = report["detailed_analysis"]["vulnerabilities"]
        if vulns.get("vulnerabilities"):
            markdown_lines.append("### Critical Vulnerabilities")
            for vuln in vulns["vulnerabilities"][:5]:  # Top 5
                markdown_lines.append(f"- **{vuln['package']}** ({vuln['version']}): {vuln['description']}")
            markdown_lines.append("")

        # Add license summary
        licenses = report["detailed_analysis"]["licenses"]
        markdown_lines.extend([
            "## License Summary",
            "",
            f"- **Permissive:** {licenses['license_summary']['permissive']}",
            f"- **Copyleft:** {licenses['license_summary']['copyleft']}",
            f"- **Unknown:** {licenses['license_summary']['unknown']}",
            ""
        ])

        return "\n".join(markdown_lines)

    async def _run_command(self, command: str, cwd: str = None) -> Dict[str, Any]:
        """Run shell command and return result"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            stdout, stderr = await process.communicate()

            return {
                "command": command,
                "return_code": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore')
            }

        except Exception as e:
            return {
                "command": command,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
