"""
Environment Manager Tool

This tool provides comprehensive environment management capabilities including:
- Environment variable management and validation
- Development environment setup and configuration
- Dependency management and version control
- Virtual environment creation and management
- Project configuration and settings management
- Environment synchronization and deployment
- Environment health checks and monitoring
"""

import asyncio
import os
import sys
import subprocess
import json
import shutil
import venv
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import platform
from pathlib import Path
import configparser
import re
from .base import BaseTool


class EnvironmentManager(BaseTool):
    """Tool for environment and project management"""

    def __init__(self):
        super().__init__()
        self.name = "environment_manager"
        self.description = "Comprehensive environment and project management tool"

        # Environment configurations
        self.env_configs = {}

        # Supported package managers
        self.package_managers = {
            'pip': {
                'install_cmd': 'pip install',
                'uninstall_cmd': 'pip uninstall -y',
                'list_cmd': 'pip list --format=json',
                'freeze_cmd': 'pip freeze',
                'requirements_file': 'requirements.txt'
            },
            'npm': {
                'install_cmd': 'npm install',
                'uninstall_cmd': 'npm uninstall',
                'list_cmd': 'npm list --json',
                'init_cmd': 'npm init -y',
                'requirements_file': 'package.json'
            },
            'yarn': {
                'install_cmd': 'yarn add',
                'uninstall_cmd': 'yarn remove',
                'list_cmd': 'yarn list --json',
                'init_cmd': 'yarn init -y',
                'requirements_file': 'package.json'
            },
            'conda': {
                'install_cmd': 'conda install -y',
                'uninstall_cmd': 'conda remove -y',
                'list_cmd': 'conda list --json',
                'requirements_file': 'environment.yml'
            }
        }

        # Environment templates
        self.env_templates = {
            'python': {
                'files': {
                    '.env': 'PYTHONPATH=.\nDEBUG=True\n',
                    'requirements.txt': '# Add your dependencies here\n',
                    '.gitignore': '__pycache__/\n*.pyc\n.env\nvenv/\n.venv/\n',
                    'README.md': '# Project Title\n\nDescription of your project.\n'
                },
                'directories': ['src', 'tests', 'docs']
            },
            'node': {
                'files': {
                    '.env': 'NODE_ENV=development\nPORT=3000\n',
                    '.gitignore': 'node_modules/\n.env\nnpm-debug.log*\n.npm\n',
                    'README.md': '# Project Title\n\nDescription of your project.\n'
                },
                'directories': ['src', 'tests', 'docs']
            },
            'web': {
                'files': {
                    '.env': 'ENVIRONMENT=development\nAPI_URL=http://localhost:3000\n',
                    '.gitignore': 'node_modules/\ndist/\n.env\n*.log\n',
                    'README.md': '# Web Project\n\nDescription of your web project.\n'
                },
                'directories': ['src', 'public', 'assets', 'docs']
            }
        }

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute environment manager commands"""
        try:
            if command == "create_env":
                return await self._create_env(**kwargs)
            elif command == "activate_env":
                return await self._activate_env(**kwargs)
            elif command == "install_packages":
                return await self._install_packages(**kwargs)
            elif command == "manage_dependencies":
                return await self._manage_dependencies(**kwargs)
            elif command == "setup_project":
                return await self._setup_project(**kwargs)
            elif command == "check_env":
                return await self._check_env(**kwargs)
            elif command == "sync_env":
                return await self._sync_env(**kwargs)
            elif command == "manage_env_vars":
                return await self._manage_env_vars(**kwargs)
            elif command == "generate_config":
                return await self._generate_config(**kwargs)
            elif command == "health_check":
                return await self._health_check(**kwargs)
            elif command == "export_env":
                return await self._export_env(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Environment manager error: {str(e)}"}

    async def _create_env(self, env_name: str, env_type: str = "python",
                         python_version: Optional[str] = None, project_dir: Optional[str] = None) -> Dict[str, Any]:
        """Create a new development environment"""
        if project_dir is None:
            project_dir = os.getcwd()

        project_dir = os.path.abspath(project_dir)

        try:
            if env_type == "python":
                # Create Python virtual environment
                env_path = os.path.join(project_dir, f"venv_{env_name}")

                # Determine Python executable
                if python_version:
                    python_exe = f"python{python_version}"
                else:
                    python_exe = sys.executable

                # Create virtual environment
                venv.create(env_path, with_pip=True)

                # Get activation script path
                if platform.system() == "Windows":
                    activate_script = os.path.join(env_path, "Scripts", "activate.bat")
                    python_exe_path = os.path.join(env_path, "Scripts", "python.exe")
                else:
                    activate_script = os.path.join(env_path, "bin", "activate")
                    python_exe_path = os.path.join(env_path, "bin", "python")

                env_info = {
                    "env_name": env_name,
                    "env_type": env_type,
                    "env_path": env_path,
                    "activate_script": activate_script,
                    "python_executable": python_exe_path,
                    "project_directory": project_dir
                }

            elif env_type == "conda":
                # Create Conda environment
                if python_version:
                    cmd = f"conda create -n {env_name} python={python_version} -y"
                else:
                    cmd = f"conda create -n {env_name} -y"

                result = await self._run_command(cmd)
                if result["return_code"] != 0:
                    return {"error": f"Failed to create conda environment: {result['stderr']}"}

                env_info = {
                    "env_name": env_name,
                    "env_type": env_type,
                    "conda_env": env_name,
                    "project_directory": project_dir
                }

            else:
                return {"error": f"Unsupported environment type: {env_type}"}

            # Store environment configuration
            self.env_configs[env_name] = env_info

            # Create project structure if template available
            template = self.env_templates.get(env_type)
            if template:
                await self._create_project_structure(project_dir, template)

            env_info.update({
                "created_at": datetime.now().isoformat(),
                "status": "created"
            })

            return env_info

        except Exception as e:
            return {"error": f"Environment creation failed: {str(e)}"}

    async def _create_project_structure(self, project_dir: str, template: Dict[str, Any]):
        """Create project structure from template"""
        # Create directories
        for directory in template.get("directories", []):
            dir_path = os.path.join(project_dir, directory)
            os.makedirs(dir_path, exist_ok=True)

        # Create files
        for filename, content in template.get("files", {}).items():
            file_path = os.path.join(project_dir, filename)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    f.write(content)

    async def _activate_env(self, env_name: str) -> Dict[str, Any]:
        """Activate an environment"""
        if env_name not in self.env_configs:
            return {"error": f"Environment not found: {env_name}"}

        env_config = self.env_configs[env_name]
        env_type = env_config["env_type"]

        try:
            if env_type == "python":
                env_path = env_config["env_path"]

                if platform.system() == "Windows":
                    activate_cmd = os.path.join(env_path, "Scripts", "activate.bat")
                else:
                    activate_cmd = f"source {os.path.join(env_path, 'bin', 'activate')}"

                return {
                    "env_name": env_name,
                    "activation_command": activate_cmd,
                    "env_path": env_path,
                    "python_executable": env_config["python_executable"],
                    "instructions": f"Run: {activate_cmd}"
                }

            elif env_type == "conda":
                conda_env = env_config["conda_env"]
                activate_cmd = f"conda activate {conda_env}"

                return {
                    "env_name": env_name,
                    "activation_command": activate_cmd,
                    "conda_env": conda_env,
                    "instructions": f"Run: {activate_cmd}"
                }

            else:
                return {"error": f"Unsupported environment type: {env_type}"}

        except Exception as e:
            return {"error": f"Environment activation failed: {str(e)}"}

    async def _install_packages(self, packages: List[str], package_manager: str = "pip",
                              env_name: Optional[str] = None, save_to_requirements: bool = True) -> Dict[str, Any]:
        """Install packages in environment"""
        if package_manager not in self.package_managers:
            return {"error": f"Unsupported package manager: {package_manager}"}

        pm_config = self.package_managers[package_manager]
        install_cmd = pm_config["install_cmd"]

        # Prepare environment-specific command
        if env_name and env_name in self.env_configs:
            env_config = self.env_configs[env_name]

            if env_config["env_type"] == "python" and package_manager == "pip":
                python_exe = env_config["python_executable"]
                install_cmd = f"{python_exe} -m pip install"
            elif env_config["env_type"] == "conda":
                install_cmd = f"conda install -n {env_config['conda_env']} -y"

        installed_packages = []
        failed_packages = []

        for package in packages:
            cmd = f"{install_cmd} {package}"
            result = await self._run_command(cmd)

            if result["return_code"] == 0:
                installed_packages.append({
                    "package": package,
                    "status": "installed",
                    "output": result["stdout"]
                })
            else:
                failed_packages.append({
                    "package": package,
                    "status": "failed",
                    "error": result["stderr"]
                })

        # Update requirements file if requested
        requirements_updated = False
        if save_to_requirements and package_manager in ["pip", "npm", "yarn"]:
            try:
                await self._update_requirements_file(package_manager, env_name)
                requirements_updated = True
            except Exception as e:
                pass  # Continue even if requirements update fails

        return {
            "package_manager": package_manager,
            "env_name": env_name,
            "installed_packages": installed_packages,
            "failed_packages": failed_packages,
            "success_count": len(installed_packages),
            "failure_count": len(failed_packages),
            "requirements_updated": requirements_updated,
            "installed_at": datetime.now().isoformat()
        }

    async def _update_requirements_file(self, package_manager: str, env_name: Optional[str] = None):
        """Update requirements file with current packages"""
        pm_config = self.package_managers[package_manager]

        if package_manager == "pip":
            # Generate pip freeze output
            if env_name and env_name in self.env_configs:
                env_config = self.env_configs[env_name]
                python_exe = env_config["python_executable"]
                freeze_cmd = f"{python_exe} -m pip freeze"
                project_dir = env_config["project_directory"]
            else:
                freeze_cmd = "pip freeze"
                project_dir = os.getcwd()

            result = await self._run_command(freeze_cmd)
            if result["return_code"] == 0:
                requirements_path = os.path.join(project_dir, "requirements.txt")
                with open(requirements_path, 'w') as f:
                    f.write(result["stdout"])

    async def _manage_dependencies(self, action: str, dependency_file: Optional[str] = None,
                                 package_manager: str = "pip", env_name: Optional[str] = None) -> Dict[str, Any]:
        """Manage project dependencies"""
        if action == "install_from_file":
            if not dependency_file:
                # Auto-detect dependency file
                for pm, config in self.package_managers.items():
                    req_file = config["requirements_file"]
                    if os.path.exists(req_file):
                        dependency_file = req_file
                        package_manager = pm
                        break

                if not dependency_file:
                    return {"error": "No dependency file found"}

            if not os.path.exists(dependency_file):
                return {"error": f"Dependency file not found: {dependency_file}"}

            # Install dependencies
            if package_manager == "pip":
                if env_name and env_name in self.env_configs:
                    env_config = self.env_configs[env_name]
                    python_exe = env_config["python_executable"]
                    cmd = f"{python_exe} -m pip install -r {dependency_file}"
                else:
                    cmd = f"pip install -r {dependency_file}"

            elif package_manager in ["npm", "yarn"]:
                cmd = f"{package_manager} install"

            elif package_manager == "conda":
                cmd = f"conda env update -f {dependency_file}"

            else:
                return {"error": f"Unsupported package manager: {package_manager}"}

            result = await self._run_command(cmd)

            return {
                "action": action,
                "dependency_file": dependency_file,
                "package_manager": package_manager,
                "success": result["return_code"] == 0,
                "output": result["stdout"],
                "error": result["stderr"] if result["return_code"] != 0 else None,
                "completed_at": datetime.now().isoformat()
            }

        elif action == "list_installed":
            # List currently installed packages
            pm_config = self.package_managers.get(package_manager)
            if not pm_config:
                return {"error": f"Unsupported package manager: {package_manager}"}

            list_cmd = pm_config["list_cmd"]

            if env_name and env_name in self.env_configs:
                env_config = self.env_configs[env_name]
                if env_config["env_type"] == "python" and package_manager == "pip":
                    python_exe = env_config["python_executable"]
                    list_cmd = f"{python_exe} -m pip list --format=json"

            result = await self._run_command(list_cmd)

            if result["return_code"] == 0:
                try:
                    if package_manager == "pip":
                        packages = json.loads(result["stdout"])
                    else:
                        packages = json.loads(result["stdout"])
                except json.JSONDecodeError:
                    packages = result["stdout"].split('\n')

                return {
                    "action": action,
                    "package_manager": package_manager,
                    "env_name": env_name,
                    "packages": packages,
                    "package_count": len(packages) if isinstance(packages, list) else 0,
                    "listed_at": datetime.now().isoformat()
                }
            else:
                return {"error": f"Failed to list packages: {result['stderr']}"}

        elif action == "check_outdated":
            # Check for outdated packages
            if package_manager == "pip":
                if env_name and env_name in self.env_configs:
                    env_config = self.env_configs[env_name]
                    python_exe = env_config["python_executable"]
                    cmd = f"{python_exe} -m pip list --outdated --format=json"
                else:
                    cmd = "pip list --outdated --format=json"

            elif package_manager == "npm":
                cmd = "npm outdated --json"

            elif package_manager == "yarn":
                cmd = "yarn outdated --json"

            else:
                return {"error": f"Outdated check not supported for: {package_manager}"}

            result = await self._run_command(cmd)

            try:
                if result["return_code"] == 0:
                    outdated = json.loads(result["stdout"]) if result["stdout"] else []
                else:
                    outdated = []
            except json.JSONDecodeError:
                outdated = []

            return {
                "action": action,
                "package_manager": package_manager,
                "env_name": env_name,
                "outdated_packages": outdated,
                "outdated_count": len(outdated) if isinstance(outdated, list) else 0,
                "checked_at": datetime.now().isoformat()
            }

        else:
            return {"error": f"Unknown dependency action: {action}"}

    async def _setup_project(self, project_name: str, project_type: str = "python",
                           project_dir: Optional[str] = None, initialize_git: bool = True,
                           create_venv: bool = True) -> Dict[str, Any]:
        """Setup a new project with environment and structure"""
        if project_dir is None:
            project_dir = os.path.join(os.getcwd(), project_name)

        try:
            # Create project directory
            os.makedirs(project_dir, exist_ok=True)

            setup_results = {
                "project_name": project_name,
                "project_type": project_type,
                "project_directory": project_dir,
                "steps_completed": []
            }

            # Create project structure
            template = self.env_templates.get(project_type)
            if template:
                await self._create_project_structure(project_dir, template)
                setup_results["steps_completed"].append("project_structure")

            # Initialize Git repository
            if initialize_git:
                git_result = await self._run_command("git init", cwd=project_dir)
                if git_result["return_code"] == 0:
                    setup_results["steps_completed"].append("git_init")
                    setup_results["git_initialized"] = True
                else:
                    setup_results["git_error"] = git_result["stderr"]

            # Create virtual environment
            if create_venv and project_type == "python":
                env_result = await self._create_env(f"{project_name}_env", project_type, project_dir=project_dir)
                if "error" not in env_result:
                    setup_results["steps_completed"].append("virtual_environment")
                    setup_results["environment"] = env_result
                else:
                    setup_results["env_error"] = env_result["error"]

            # Initialize package manager
            if project_type == "node":
                npm_result = await self._run_command("npm init -y", cwd=project_dir)
                if npm_result["return_code"] == 0:
                    setup_results["steps_completed"].append("npm_init")
                    setup_results["package_json_created"] = True

            setup_results.update({
                "setup_completed": True,
                "completed_at": datetime.now().isoformat()
            })

            return setup_results

        except Exception as e:
            return {"error": f"Project setup failed: {str(e)}"}

    async def _check_env(self, env_name: Optional[str] = None, check_type: str = "basic") -> Dict[str, Any]:
        """Check environment status and health"""
        if env_name and env_name not in self.env_configs:
            return {"error": f"Environment not found: {env_name}"}

        check_results = {
            "check_type": check_type,
            "checked_at": datetime.now().isoformat()
        }

        if check_type == "basic":
            # Basic environment information
            system_info = {
                "platform": platform.platform(),
                "python_version": sys.version,
                "python_executable": sys.executable,
                "current_directory": os.getcwd(),
                "environment_variables": len(os.environ),
                "path_entries": len(os.environ.get("PATH", "").split(os.pathsep))
            }

            check_results["system_info"] = system_info

            # Check specific environment if provided
            if env_name:
                env_config = self.env_configs[env_name]
                env_status = {
                    "env_name": env_name,
                    "env_type": env_config["env_type"],
                    "env_exists": True
                }

                if env_config["env_type"] == "python":
                    env_path = env_config["env_path"]
                    env_status.update({
                        "env_path": env_path,
                        "env_directory_exists": os.path.exists(env_path),
                        "python_executable_exists": os.path.exists(env_config["python_executable"])
                    })

                check_results["environment_status"] = env_status

        elif check_type == "dependencies":
            # Check installed packages and dependencies
            dependency_info = {}

            for pm_name in ["pip", "npm", "yarn"]:
                if shutil.which(pm_name):
                    pm_result = await self._run_command(f"{pm_name} --version")
                    dependency_info[pm_name] = {
                        "available": True,
                        "version": pm_result["stdout"].strip() if pm_result["return_code"] == 0 else "unknown"
                    }
                else:
                    dependency_info[pm_name] = {"available": False}

            check_results["package_managers"] = dependency_info

            # Check for common requirement files
            requirement_files = {}
            for filename in ["requirements.txt", "package.json", "environment.yml", "Pipfile"]:
                requirement_files[filename] = os.path.exists(filename)

            check_results["requirement_files"] = requirement_files

        elif check_type == "tools":
            # Check development tools
            tools_to_check = ["git", "docker", "node", "python", "pip", "npm", "yarn", "conda"]
            tool_status = {}

            for tool in tools_to_check:
                if shutil.which(tool):
                    version_result = await self._run_command(f"{tool} --version")
                    tool_status[tool] = {
                        "available": True,
                        "version": version_result["stdout"].strip()[:100] if version_result["return_code"] == 0 else "unknown"
                    }
                else:
                    tool_status[tool] = {"available": False}

            check_results["development_tools"] = tool_status

        return check_results

    async def _sync_env(self, source_env: str, target_env: str, sync_type: str = "packages") -> Dict[str, Any]:
        """Synchronize environments"""
        if source_env not in self.env_configs:
            return {"error": f"Source environment not found: {source_env}"}

        if target_env not in self.env_configs:
            return {"error": f"Target environment not found: {target_env}"}

        source_config = self.env_configs[source_env]
        target_config = self.env_configs[target_env]

        try:
            if sync_type == "packages":
                # Sync installed packages
                if source_config["env_type"] == "python" and target_config["env_type"] == "python":
                    # Get packages from source environment
                    source_python = source_config["python_executable"]
                    freeze_result = await self._run_command(f"{source_python} -m pip freeze")

                    if freeze_result["return_code"] == 0:
                        # Create temporary requirements file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                            f.write(freeze_result["stdout"])
                            temp_requirements = f.name

                        try:
                            # Install packages in target environment
                            target_python = target_config["python_executable"]
                            install_result = await self._run_command(f"{target_python} -m pip install -r {temp_requirements}")

                            return {
                                "source_env": source_env,
                                "target_env": target_env,
                                "sync_type": sync_type,
                                "success": install_result["return_code"] == 0,
                                "output": install_result["stdout"],
                                "error": install_result["stderr"] if install_result["return_code"] != 0 else None,
                                "synced_at": datetime.now().isoformat()
                            }

                        finally:
                            os.unlink(temp_requirements)

                    else:
                        return {"error": f"Failed to get packages from source environment: {freeze_result['stderr']}"}

                else:
                    return {"error": "Package sync only supported between Python environments"}

            else:
                return {"error": f"Unsupported sync type: {sync_type}"}

        except Exception as e:
            return {"error": f"Environment sync failed: {str(e)}"}

    async def _manage_env_vars(self, action: str, key: Optional[str] = None,
                             value: Optional[str] = None, env_file: Optional[str] = None) -> Dict[str, Any]:
        """Manage environment variables"""
        try:
            if action == "get":
                if key:
                    env_value = os.environ.get(key)
                    return {
                        "action": action,
                        "key": key,
                        "value": env_value,
                        "exists": env_value is not None
                    }
                else:
                    return {
                        "action": action,
                        "environment_variables": dict(os.environ),
                        "total_variables": len(os.environ)
                    }

            elif action == "set":
                if not key:
                    return {"error": "Key is required for set action"}

                old_value = os.environ.get(key)
                os.environ[key] = str(value) if value is not None else ""

                return {
                    "action": action,
                    "key": key,
                    "old_value": old_value,
                    "new_value": value,
                    "set_at": datetime.now().isoformat()
                }

            elif action == "unset":
                if not key:
                    return {"error": "Key is required for unset action"}

                old_value = os.environ.pop(key, None)

                return {
                    "action": action,
                    "key": key,
                    "old_value": old_value,
                    "existed": old_value is not None,
                    "unset_at": datetime.now().isoformat()
                }

            elif action == "load_from_file":
                if not env_file:
                    env_file = ".env"

                if not os.path.exists(env_file):
                    return {"error": f"Environment file not found: {env_file}"}

                loaded_vars = []

                with open(env_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()

                        # Skip empty lines and comments
                        if not line or line.startswith('#'):
                            continue

                        # Parse key=value
                        if '=' in line:
                            env_key, env_value = line.split('=', 1)
                            env_key = env_key.strip()
                            env_value = env_value.strip()

                            # Remove quotes if present
                            if (env_value.startswith('"') and env_value.endswith('"')) or \
                               (env_value.startswith("'") and env_value.endswith("'")):
                                env_value = env_value[1:-1]

                            old_value = os.environ.get(env_key)
                            os.environ[env_key] = env_value

                            loaded_vars.append({
                                "key": env_key,
                                "value": env_value,
                                "old_value": old_value,
                                "line_number": line_num
                            })

                return {
                    "action": action,
                    "env_file": env_file,
                    "loaded_variables": loaded_vars,
                    "loaded_count": len(loaded_vars),
                    "loaded_at": datetime.now().isoformat()
                }

            elif action == "save_to_file":
                if not env_file:
                    env_file = ".env"

                # Get current environment variables
                env_vars = dict(os.environ)

                # Filter out system variables if requested
                filtered_vars = {}
                for k, v in env_vars.items():
                    # Skip common system variables
                    if not k.startswith(('SYSTEM', 'WINDOWS', 'PROGRAMFILES', 'USERPROFILE', 'TEMP', 'TMP')):
                        filtered_vars[k] = v

                with open(env_file, 'w') as f:
                    f.write(f"# Environment variables exported on {datetime.now().isoformat()}\n")
                    for key, value in sorted(filtered_vars.items()):
                        # Quote values that contain spaces or special characters
                        if ' ' in value or any(c in value for c in ';"\'$`'):
                            f.write(f'{key}="{value}"\n')
                        else:
                            f.write(f'{key}={value}\n')

                return {
                    "action": action,
                    "env_file": env_file,
                    "exported_count": len(filtered_vars),
                    "saved_at": datetime.now().isoformat()
                }

            else:
                return {"error": f"Unknown environment variable action: {action}"}

        except Exception as e:
            return {"error": f"Environment variable management failed: {str(e)}"}

    async def _generate_config(self, config_type: str, project_dir: Optional[str] = None,
                             template_vars: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate configuration files"""
        if project_dir is None:
            project_dir = os.getcwd()

        if template_vars is None:
            template_vars = {}

        try:
            generated_files = []

            if config_type == "docker":
                # Generate Dockerfile
                dockerfile_content = f"""FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {template_vars.get('port', 8000)}

CMD ["python", "app.py"]
"""

                dockerfile_path = os.path.join(project_dir, "Dockerfile")
                with open(dockerfile_path, 'w') as f:
                    f.write(dockerfile_content)
                generated_files.append(dockerfile_path)

                # Generate docker-compose.yml
                compose_content = f"""version: '3.8'

services:
  app:
    build: .
    ports:
      - "{template_vars.get('port', 8000)}:8000"
    environment:
      - DEBUG={template_vars.get('debug', 'False')}
    volumes:
      - .:/app
"""

                compose_path = os.path.join(project_dir, "docker-compose.yml")
                with open(compose_path, 'w') as f:
                    f.write(compose_content)
                generated_files.append(compose_path)

            elif config_type == "ci_cd":
                # Generate GitHub Actions workflow
                workflow_dir = os.path.join(project_dir, ".github", "workflows")
                os.makedirs(workflow_dir, exist_ok=True)

                workflow_content = f"""name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: {template_vars.get('python_version', '3.9')}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run tests
      run: |
        python -m pytest
"""

                workflow_path = os.path.join(workflow_dir, "ci.yml")
                with open(workflow_path, 'w') as f:
                    f.write(workflow_content)
                generated_files.append(workflow_path)

            elif config_type == "vscode":
                # Generate VS Code settings
                vscode_dir = os.path.join(project_dir, ".vscode")
                os.makedirs(vscode_dir, exist_ok=True)

                settings_content = {
                    "python.defaultInterpreterPath": template_vars.get('python_path', './venv/bin/python'),
                    "python.formatting.provider": "black",
                    "python.linting.enabled": True,
                    "python.linting.pylintEnabled": True,
                    "files.exclude": {
                        "**/__pycache__": True,
                        "**/*.pyc": True
                    }
                }

                settings_path = os.path.join(vscode_dir, "settings.json")
                with open(settings_path, 'w') as f:
                    json.dump(settings_content, f, indent=2)
                generated_files.append(settings_path)

            else:
                return {"error": f"Unsupported config type: {config_type}"}

            return {
                "config_type": config_type,
                "project_directory": project_dir,
                "generated_files": generated_files,
                "file_count": len(generated_files),
                "template_vars": template_vars,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Config generation failed: {str(e)}"}

    async def _health_check(self) -> Dict[str, Any]:
        """Perform comprehensive environment health check"""
        health_status = {
            "overall_status": "healthy",
            "checked_at": datetime.now().isoformat(),
            "issues": []
        }

        try:
            # Check Python environment
            python_check = {
                "python_version": sys.version,
                "python_executable": sys.executable,
                "pip_available": shutil.which("pip") is not None
            }

            # Check disk space
            import shutil as disk_util
            total, used, free = disk_util.disk_usage(os.getcwd())
            disk_check = {
                "total_gb": round(total / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "free_gb": round(free / (1024**3), 2),
                "usage_percent": round((used / total) * 100, 2)
            }

            if disk_check["usage_percent"] > 90:
                health_status["issues"].append("Low disk space (>90% used)")
                health_status["overall_status"] = "warning"

            # Check environment variables
            critical_env_vars = ["PATH", "HOME", "USER"]
            missing_env_vars = [var for var in critical_env_vars if var not in os.environ]

            if missing_env_vars:
                health_status["issues"].append(f"Missing environment variables: {missing_env_vars}")
                health_status["overall_status"] = "warning"

            # Check virtual environments
            env_check = {}
            for env_name, env_config in self.env_configs.items():
                if env_config["env_type"] == "python":
                    env_path = env_config["env_path"]
                    python_exe = env_config["python_executable"]

                    env_check[env_name] = {
                        "env_exists": os.path.exists(env_path),
                        "python_exists": os.path.exists(python_exe),
                        "accessible": os.access(python_exe, os.X_OK) if os.path.exists(python_exe) else False
                    }

                    if not env_check[env_name]["env_exists"]:
                        health_status["issues"].append(f"Environment directory missing: {env_name}")
                        health_status["overall_status"] = "error"

            health_status.update({
                "python_environment": python_check,
                "disk_usage": disk_check,
                "virtual_environments": env_check,
                "environment_variable_count": len(os.environ),
                "current_directory": os.getcwd(),
                "platform_info": {
                    "system": platform.system(),
                    "release": platform.release(),
                    "machine": platform.machine()
                }
            })

            if health_status["issues"]:
                health_status["issue_count"] = len(health_status["issues"])

            return health_status

        except Exception as e:
            return {
                "overall_status": "error",
                "error": f"Health check failed: {str(e)}",
                "checked_at": datetime.now().isoformat()
            }

    async def _export_env(self, env_name: str, export_format: str = "json",
                         output_file: Optional[str] = None) -> Dict[str, Any]:
        """Export environment configuration"""
        if env_name not in self.env_configs:
            return {"error": f"Environment not found: {env_name}"}

        env_config = self.env_configs[env_name]

        try:
            # Gather environment information
            export_data = {
                "environment_name": env_name,
                "environment_config": env_config,
                "export_timestamp": datetime.now().isoformat(),
                "system_info": {
                    "platform": platform.platform(),
                    "python_version": sys.version
                }
            }

            # Get installed packages if Python environment
            if env_config["env_type"] == "python":
                python_exe = env_config["python_executable"]
                packages_result = await self._run_command(f"{python_exe} -m pip list --format=json")

                if packages_result["return_code"] == 0:
                    try:
                        export_data["installed_packages"] = json.loads(packages_result["stdout"])
                    except json.JSONDecodeError:
                        export_data["installed_packages"] = []

            # Generate output file name if not provided
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"{env_name}_export_{timestamp}.{export_format}"

            # Save export data
            if export_format == "json":
                with open(output_file, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)

            elif export_format == "yaml":
                import yaml
                with open(output_file, 'w') as f:
                    yaml.dump(export_data, f, default_flow_style=False)

            else:
                return {"error": f"Unsupported export format: {export_format}"}

            return {
                "env_name": env_name,
                "export_format": export_format,
                "output_file": output_file,
                "file_size": os.path.getsize(output_file),
                "exported_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Environment export failed: {str(e)}"}

    async def _run_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
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
