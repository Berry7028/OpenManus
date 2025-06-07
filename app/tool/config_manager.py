"""
Configuration Manager Tool

This tool provides comprehensive configuration management capabilities including:
- Configuration file parsing and editing (JSON, YAML, INI, TOML, XML)
- Environment variable management
- Configuration validation and schema checking
- Configuration templating and variable substitution
- Configuration versioning and backup
- Multi-environment configuration management
- Configuration merging and inheritance
"""

import asyncio
import os
import json
import yaml
import configparser
import xml.etree.ElementTree as ET
import re
import shutil
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import tempfile
import copy
from pathlib import Path
from .base import BaseTool

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False


class ConfigManager(BaseTool):
    """Tool for configuration file management"""

    def __init__(self):
        super().__init__()
        self.name = "config_manager"
        self.description = "Comprehensive configuration file management tool"

        # Supported configuration formats
        self.supported_formats = {
            'json': {'extensions': ['.json'], 'loader': self._load_json, 'saver': self._save_json},
            'yaml': {'extensions': ['.yaml', '.yml'], 'loader': self._load_yaml, 'saver': self._save_yaml},
            'ini': {'extensions': ['.ini', '.cfg', '.conf'], 'loader': self._load_ini, 'saver': self._save_ini},
            'xml': {'extensions': ['.xml'], 'loader': self._load_xml, 'saver': self._save_xml},
            'env': {'extensions': ['.env'], 'loader': self._load_env, 'saver': self._save_env}
        }

        if TOML_AVAILABLE:
            self.supported_formats['toml'] = {'extensions': ['.toml'], 'loader': self._load_toml, 'saver': self._save_toml}

        # Configuration cache
        self.config_cache = {}

        # Environment variable cache
        self.env_backup = {}

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute configuration manager commands"""
        try:
            if command == "load_config":
                return await self._load_config(**kwargs)
            elif command == "save_config":
                return await self._save_config(**kwargs)
            elif command == "get_value":
                return await self._get_value(**kwargs)
            elif command == "set_value":
                return await self._set_value(**kwargs)
            elif command == "merge_configs":
                return await self._merge_configs(**kwargs)
            elif command == "validate_config":
                return await self._validate_config(**kwargs)
            elif command == "template_config":
                return await self._template_config(**kwargs)
            elif command == "backup_config":
                return await self._backup_config(**kwargs)
            elif command == "restore_config":
                return await self._restore_config(**kwargs)
            elif command == "manage_env":
                return await self._manage_env(**kwargs)
            elif command == "convert_format":
                return await self._convert_format(**kwargs)
            elif command == "list_configs":
                return await self._list_configs(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Configuration manager error: {str(e)}"}

    async def _load_config(self, file_path: str, format_type: Optional[str] = None, cache: bool = True) -> Dict[str, Any]:
        """Load configuration file"""
        if not os.path.exists(file_path):
            return {"error": f"Configuration file not found: {file_path}"}

        # Auto-detect format if not specified
        if format_type is None:
            format_type = self._detect_format(file_path)

        if format_type not in self.supported_formats:
            return {"error": f"Unsupported format: {format_type}"}

        try:
            loader = self.supported_formats[format_type]['loader']
            config_data = loader(file_path)

            if cache:
                self.config_cache[file_path] = {
                    'data': copy.deepcopy(config_data),
                    'format': format_type,
                    'loaded_at': datetime.now().isoformat(),
                    'file_mtime': os.path.getmtime(file_path)
                }

            return {
                "file_path": file_path,
                "format": format_type,
                "config_data": config_data,
                "loaded_at": datetime.now().isoformat(),
                "file_size": os.path.getsize(file_path)
            }

        except Exception as e:
            return {"error": f"Failed to load config: {str(e)}"}

    async def _save_config(self, file_path: str, config_data: Dict[str, Any],
                          format_type: Optional[str] = None, backup: bool = True) -> Dict[str, Any]:
        """Save configuration file"""
        # Auto-detect format if not specified
        if format_type is None:
            format_type = self._detect_format(file_path)

        if format_type not in self.supported_formats:
            return {"error": f"Unsupported format: {format_type}"}

        try:
            # Create backup if requested and file exists
            backup_path = None
            if backup and os.path.exists(file_path):
                backup_path = f"{file_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(file_path, backup_path)

            # Save configuration
            saver = self.supported_formats[format_type]['saver']
            saver(file_path, config_data)

            # Update cache
            self.config_cache[file_path] = {
                'data': copy.deepcopy(config_data),
                'format': format_type,
                'saved_at': datetime.now().isoformat(),
                'file_mtime': os.path.getmtime(file_path)
            }

            return {
                "file_path": file_path,
                "format": format_type,
                "backup_created": backup_path is not None,
                "backup_path": backup_path,
                "saved_at": datetime.now().isoformat(),
                "file_size": os.path.getsize(file_path)
            }

        except Exception as e:
            return {"error": f"Failed to save config: {str(e)}"}

    def _detect_format(self, file_path: str) -> str:
        """Auto-detect configuration file format"""
        file_ext = Path(file_path).suffix.lower()

        for format_type, info in self.supported_formats.items():
            if file_ext in info['extensions']:
                return format_type

        # Try to detect by content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()

            if content.startswith('{') and content.endswith('}'):
                return 'json'
            elif content.startswith('<?xml'):
                return 'xml'
            elif '=' in content and '[' not in content:
                return 'env'
            elif '[' in content and ']' in content:
                return 'ini'
            else:
                return 'yaml'  # Default fallback

        except Exception:
            return 'json'  # Safe fallback

    # Format-specific loaders
    def _load_json(self, file_path: str) -> Dict[str, Any]:
        """Load JSON configuration"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_json(self, file_path: str, data: Dict[str, Any]):
        """Save JSON configuration"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_yaml(self, file_path: str) -> Dict[str, Any]:
        """Load YAML configuration"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}

    def _save_yaml(self, file_path: str, data: Dict[str, Any]):
        """Save YAML configuration"""
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)

    def _load_ini(self, file_path: str) -> Dict[str, Any]:
        """Load INI configuration"""
        config = configparser.ConfigParser()
        config.read(file_path, encoding='utf-8')

        result = {}
        for section_name in config.sections():
            result[section_name] = dict(config[section_name])

        # Handle default section
        if config.defaults():
            result['DEFAULT'] = dict(config.defaults())

        return result

    def _save_ini(self, file_path: str, data: Dict[str, Any]):
        """Save INI configuration"""
        config = configparser.ConfigParser()

        for section_name, section_data in data.items():
            if section_name != 'DEFAULT':
                config.add_section(section_name)
                for key, value in section_data.items():
                    config.set(section_name, key, str(value))
            else:
                # Handle DEFAULT section
                for key, value in section_data.items():
                    config.set('DEFAULT', key, str(value))

        with open(file_path, 'w', encoding='utf-8') as f:
            config.write(f)

    def _load_xml(self, file_path: str) -> Dict[str, Any]:
        """Load XML configuration"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        return self._xml_to_dict(root)

    def _save_xml(self, file_path: str, data: Dict[str, Any]):
        """Save XML configuration"""
        root = self._dict_to_xml('config', data)
        tree = ET.ElementTree(root)
        tree.write(file_path, encoding='utf-8', xml_declaration=True)

    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}

        # Handle attributes
        if element.attrib:
            result['@attributes'] = element.attrib

        # Handle text content
        if element.text and element.text.strip():
            if len(element) == 0:  # No child elements
                return element.text.strip()
            else:
                result['#text'] = element.text.strip()

        # Handle child elements
        for child in element:
            child_data = self._xml_to_dict(child)

            if child.tag in result:
                # Convert to list if multiple elements with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        return result

    def _dict_to_xml(self, tag: str, data: Any) -> ET.Element:
        """Convert dictionary to XML element"""
        element = ET.Element(tag)

        if isinstance(data, dict):
            for key, value in data.items():
                if key == '@attributes':
                    element.attrib.update(value)
                elif key == '#text':
                    element.text = str(value)
                else:
                    if isinstance(value, list):
                        for item in value:
                            child = self._dict_to_xml(key, item)
                            element.append(child)
                    else:
                        child = self._dict_to_xml(key, value)
                        element.append(child)
        else:
            element.text = str(data)

        return element

    def _load_env(self, file_path: str) -> Dict[str, Any]:
        """Load environment file"""
        result = {}

        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue

                # Parse key=value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    # Remove quotes if present
                    if (value.startswith('"') and value.endswith('"')) or \
                       (value.startswith("'") and value.endswith("'")):
                        value = value[1:-1]

                    result[key] = value

        return result

    def _save_env(self, file_path: str, data: Dict[str, Any]):
        """Save environment file"""
        with open(file_path, 'w', encoding='utf-8') as f:
            for key, value in data.items():
                # Quote values that contain spaces or special characters
                if isinstance(value, str) and (' ' in value or any(c in value for c in ';"\'$`')):
                    f.write(f'{key}="{value}"\n')
                else:
                    f.write(f'{key}={value}\n')

    def _load_toml(self, file_path: str) -> Dict[str, Any]:
        """Load TOML configuration"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return toml.load(f)

    def _save_toml(self, file_path: str, data: Dict[str, Any]):
        """Save TOML configuration"""
        with open(file_path, 'w', encoding='utf-8') as f:
            toml.dump(data, f)

    async def _get_value(self, file_path: str, key_path: str, default: Any = None) -> Dict[str, Any]:
        """Get value from configuration using dot notation"""
        # Load config if not cached or outdated
        if file_path not in self.config_cache or self._is_cache_outdated(file_path):
            load_result = await self._load_config(file_path)
            if "error" in load_result:
                return load_result

        config_data = self.config_cache[file_path]['data']

        # Navigate through the key path
        keys = key_path.split('.')
        current = config_data

        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return {
                    "file_path": file_path,
                    "key_path": key_path,
                    "value": default,
                    "found": False,
                    "default_used": True
                }

        return {
            "file_path": file_path,
            "key_path": key_path,
            "value": current,
            "found": True,
            "default_used": False
        }

    async def _set_value(self, file_path: str, key_path: str, value: Any,
                        create_missing: bool = True) -> Dict[str, Any]:
        """Set value in configuration using dot notation"""
        # Load config if not cached or outdated
        if file_path not in self.config_cache or self._is_cache_outdated(file_path):
            load_result = await self._load_config(file_path)
            if "error" in load_result:
                return load_result

        config_data = self.config_cache[file_path]['data']

        # Navigate and set the value
        keys = key_path.split('.')
        current = config_data

        for i, key in enumerate(keys[:-1]):
            if key not in current:
                if create_missing:
                    current[key] = {}
                else:
                    return {"error": f"Key path not found: {'.'.join(keys[:i+1])}"}
            elif not isinstance(current[key], dict):
                return {"error": f"Cannot navigate through non-dict value at: {'.'.join(keys[:i+1])}"}
            current = current[key]

        # Set the final value
        final_key = keys[-1]
        old_value = current.get(final_key)
        current[final_key] = value

        # Save the updated configuration
        save_result = await self._save_config(file_path, config_data)
        if "error" in save_result:
            return save_result

        return {
            "file_path": file_path,
            "key_path": key_path,
            "old_value": old_value,
            "new_value": value,
            "updated_at": datetime.now().isoformat()
        }

    def _is_cache_outdated(self, file_path: str) -> bool:
        """Check if cached config is outdated"""
        if file_path not in self.config_cache:
            return True

        try:
            current_mtime = os.path.getmtime(file_path)
            cached_mtime = self.config_cache[file_path]['file_mtime']
            return current_mtime != cached_mtime
        except OSError:
            return True

    async def _merge_configs(self, primary_file: str, secondary_files: List[str],
                           output_file: Optional[str] = None, merge_strategy: str = "overwrite") -> Dict[str, Any]:
        """Merge multiple configuration files"""
        # Load primary configuration
        primary_result = await self._load_config(primary_file)
        if "error" in primary_result:
            return primary_result

        merged_config = copy.deepcopy(primary_result["config_data"])
        merge_info = {"primary_file": primary_file, "merged_files": []}

        # Merge secondary configurations
        for secondary_file in secondary_files:
            secondary_result = await self._load_config(secondary_file)
            if "error" in secondary_result:
                merge_info["errors"] = merge_info.get("errors", [])
                merge_info["errors"].append(f"Failed to load {secondary_file}: {secondary_result['error']}")
                continue

            secondary_config = secondary_result["config_data"]

            if merge_strategy == "overwrite":
                merged_config = self._deep_merge_overwrite(merged_config, secondary_config)
            elif merge_strategy == "preserve":
                merged_config = self._deep_merge_preserve(merged_config, secondary_config)
            elif merge_strategy == "append":
                merged_config = self._deep_merge_append(merged_config, secondary_config)

            merge_info["merged_files"].append(secondary_file)

        # Save merged configuration
        if output_file:
            save_result = await self._save_config(output_file, merged_config)
            if "error" in save_result:
                return save_result
            merge_info["output_file"] = output_file

        return {
            "merged_config": merged_config,
            "merge_info": merge_info,
            "merge_strategy": merge_strategy,
            "merged_at": datetime.now().isoformat()
        }

    def _deep_merge_overwrite(self, primary: Dict, secondary: Dict) -> Dict:
        """Deep merge with overwrite strategy"""
        result = copy.deepcopy(primary)

        for key, value in secondary.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_overwrite(result[key], value)
            else:
                result[key] = copy.deepcopy(value)

        return result

    def _deep_merge_preserve(self, primary: Dict, secondary: Dict) -> Dict:
        """Deep merge with preserve strategy (don't overwrite existing)"""
        result = copy.deepcopy(primary)

        for key, value in secondary.items():
            if key not in result:
                result[key] = copy.deepcopy(value)
            elif isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge_preserve(result[key], value)

        return result

    def _deep_merge_append(self, primary: Dict, secondary: Dict) -> Dict:
        """Deep merge with append strategy (append to lists)"""
        result = copy.deepcopy(primary)

        for key, value in secondary.items():
            if key in result:
                if isinstance(result[key], list) and isinstance(value, list):
                    result[key].extend(copy.deepcopy(value))
                elif isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge_append(result[key], value)
                else:
                    result[key] = copy.deepcopy(value)
            else:
                result[key] = copy.deepcopy(value)

        return result

    async def _validate_config(self, file_path: str, schema: Optional[Dict] = None,
                             validation_rules: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Validate configuration against schema or rules"""
        # Load configuration
        load_result = await self._load_config(file_path)
        if "error" in load_result:
            return load_result

        config_data = load_result["config_data"]
        validation_errors = []
        validation_warnings = []

        # Schema validation
        if schema:
            errors = self._validate_against_schema(config_data, schema)
            validation_errors.extend(errors)

        # Custom validation rules
        if validation_rules:
            for rule in validation_rules:
                rule_result = self._apply_validation_rule(config_data, rule)
                if rule_result["level"] == "error":
                    validation_errors.append(rule_result)
                elif rule_result["level"] == "warning":
                    validation_warnings.append(rule_result)

        # Built-in validations
        builtin_results = self._builtin_validations(config_data)
        validation_warnings.extend(builtin_results)

        return {
            "file_path": file_path,
            "valid": len(validation_errors) == 0,
            "errors": validation_errors,
            "warnings": validation_warnings,
            "error_count": len(validation_errors),
            "warning_count": len(validation_warnings),
            "validated_at": datetime.now().isoformat()
        }

    def _validate_against_schema(self, data: Dict, schema: Dict, path: str = "") -> List[Dict]:
        """Validate data against a simple schema"""
        errors = []

        # Check required fields
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                errors.append({
                    "type": "missing_required",
                    "message": f"Required field '{field}' is missing",
                    "path": f"{path}.{field}" if path else field
                })

        # Check field types
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in data:
                field_path = f"{path}.{field}" if path else field
                expected_type = field_schema.get("type")

                if expected_type:
                    if not self._check_type(data[field], expected_type):
                        errors.append({
                            "type": "type_mismatch",
                            "message": f"Field '{field}' should be of type {expected_type}",
                            "path": field_path,
                            "actual_type": type(data[field]).__name__
                        })

                # Recursive validation for objects
                if expected_type == "object" and isinstance(data[field], dict):
                    nested_errors = self._validate_against_schema(data[field], field_schema, field_path)
                    errors.extend(nested_errors)

        return errors

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_mapping = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }

        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)

        return True

    def _apply_validation_rule(self, data: Dict, rule: Dict) -> Dict:
        """Apply custom validation rule"""
        rule_type = rule.get("type")
        path = rule.get("path", "")
        level = rule.get("level", "warning")

        # Navigate to the specified path
        current = data
        for key in path.split('.') if path else []:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return {
                    "type": "path_not_found",
                    "message": f"Path '{path}' not found",
                    "level": "warning",
                    "rule": rule
                }

        # Apply rule based on type
        if rule_type == "range":
            min_val = rule.get("min")
            max_val = rule.get("max")
            if isinstance(current, (int, float)):
                if (min_val is not None and current < min_val) or \
                   (max_val is not None and current > max_val):
                    return {
                        "type": "range_violation",
                        "message": f"Value {current} is outside allowed range [{min_val}, {max_val}]",
                        "level": level,
                        "path": path
                    }

        elif rule_type == "pattern":
            pattern = rule.get("pattern")
            if isinstance(current, str) and pattern:
                if not re.match(pattern, current):
                    return {
                        "type": "pattern_mismatch",
                        "message": f"Value '{current}' does not match pattern '{pattern}'",
                        "level": level,
                        "path": path
                    }

        elif rule_type == "enum":
            allowed_values = rule.get("values", [])
            if current not in allowed_values:
                return {
                    "type": "enum_violation",
                    "message": f"Value '{current}' not in allowed values: {allowed_values}",
                    "level": level,
                    "path": path
                }

        return {"type": "rule_passed", "level": "info", "rule": rule}

    def _builtin_validations(self, data: Dict) -> List[Dict]:
        """Apply built-in validation checks"""
        warnings = []

        # Check for common security issues
        def check_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key

                    # Check for hardcoded passwords
                    if 'password' in key.lower() and isinstance(value, str) and value:
                        warnings.append({
                            "type": "security",
                            "message": "Hardcoded password detected",
                            "level": "warning",
                            "path": current_path
                        })

                    # Check for empty critical fields
                    critical_fields = ['host', 'url', 'endpoint', 'database']
                    if any(field in key.lower() for field in critical_fields) and not value:
                        warnings.append({
                            "type": "empty_critical",
                            "message": f"Critical field '{key}' is empty",
                            "level": "warning",
                            "path": current_path
                        })

                    check_recursive(value, current_path)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_recursive(item, f"{path}[{i}]")

        check_recursive(data)
        return warnings

    async def _template_config(self, template_file: str, variables: Dict[str, Any],
                             output_file: str) -> Dict[str, Any]:
        """Generate configuration from template with variable substitution"""
        if not os.path.exists(template_file):
            return {"error": f"Template file not found: {template_file}"}

        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # Simple variable substitution with ${variable} syntax
            substituted_content = template_content
            substitutions_made = {}

            for var_name, var_value in variables.items():
                pattern = f"${{{var_name}}}"
                if pattern in substituted_content:
                    substituted_content = substituted_content.replace(pattern, str(var_value))
                    substitutions_made[var_name] = var_value

            # Check for unresolved variables
            unresolved = re.findall(r'\$\{([^}]+)\}', substituted_content)

            # Write output file
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(substituted_content)

            return {
                "template_file": template_file,
                "output_file": output_file,
                "substitutions_made": substitutions_made,
                "unresolved_variables": unresolved,
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Template processing failed: {str(e)}"}

    async def _backup_config(self, file_path: str, backup_dir: Optional[str] = None,
                           keep_versions: int = 5) -> Dict[str, Any]:
        """Create versioned backup of configuration file"""
        if not os.path.exists(file_path):
            return {"error": f"Configuration file not found: {file_path}"}

        if backup_dir is None:
            backup_dir = os.path.dirname(file_path)

        os.makedirs(backup_dir, exist_ok=True)

        # Generate backup filename with timestamp
        file_name = os.path.basename(file_path)
        name, ext = os.path.splitext(file_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{name}.backup.{timestamp}{ext}"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            # Create backup
            shutil.copy2(file_path, backup_path)

            # Clean up old backups
            cleanup_result = self._cleanup_old_backups(backup_dir, name, ext, keep_versions)

            return {
                "original_file": file_path,
                "backup_file": backup_path,
                "backup_directory": backup_dir,
                "cleanup_result": cleanup_result,
                "backup_created_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Backup failed: {str(e)}"}

    def _cleanup_old_backups(self, backup_dir: str, base_name: str, extension: str, keep_versions: int) -> Dict[str, Any]:
        """Clean up old backup files"""
        pattern = f"{base_name}.backup.*{extension}"
        backup_files = []

        for file in os.listdir(backup_dir):
            if file.startswith(f"{base_name}.backup.") and file.endswith(extension):
                file_path = os.path.join(backup_dir, file)
                backup_files.append((file_path, os.path.getmtime(file_path)))

        # Sort by modification time (newest first)
        backup_files.sort(key=lambda x: x[1], reverse=True)

        # Remove old backups
        removed_files = []
        if len(backup_files) > keep_versions:
            for file_path, _ in backup_files[keep_versions:]:
                try:
                    os.remove(file_path)
                    removed_files.append(file_path)
                except Exception:
                    pass

        return {
            "total_backups": len(backup_files),
            "kept_backups": min(len(backup_files), keep_versions),
            "removed_backups": len(removed_files),
            "removed_files": removed_files
        }

    async def _restore_config(self, backup_file: str, target_file: Optional[str] = None) -> Dict[str, Any]:
        """Restore configuration from backup"""
        if not os.path.exists(backup_file):
            return {"error": f"Backup file not found: {backup_file}"}

        if target_file is None:
            # Try to determine original file name
            backup_name = os.path.basename(backup_file)
            if '.backup.' in backup_name:
                # Extract original name
                parts = backup_name.split('.backup.')
                original_name = parts[0]
                extension = os.path.splitext(backup_name)[1]
                target_file = os.path.join(os.path.dirname(backup_file), f"{original_name}{extension}")
            else:
                return {"error": "Cannot determine target file name"}

        try:
            # Create backup of current file if it exists
            current_backup = None
            if os.path.exists(target_file):
                current_backup = f"{target_file}.pre_restore.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(target_file, current_backup)

            # Restore from backup
            shutil.copy2(backup_file, target_file)

            # Clear cache for the restored file
            if target_file in self.config_cache:
                del self.config_cache[target_file]

            return {
                "backup_file": backup_file,
                "target_file": target_file,
                "current_backup": current_backup,
                "restored_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Restore failed: {str(e)}"}

    async def _manage_env(self, operation: str, key: Optional[str] = None,
                         value: Optional[str] = None, env_file: Optional[str] = None) -> Dict[str, Any]:
        """Manage environment variables"""
        try:
            if operation == "get":
                if key:
                    env_value = os.environ.get(key)
                    return {
                        "operation": "get",
                        "key": key,
                        "value": env_value,
                        "exists": env_value is not None
                    }
                else:
                    return {
                        "operation": "get_all",
                        "environment": dict(os.environ)
                    }

            elif operation == "set":
                if not key:
                    return {"error": "Key is required for set operation"}

                old_value = os.environ.get(key)
                os.environ[key] = str(value) if value is not None else ""

                return {
                    "operation": "set",
                    "key": key,
                    "old_value": old_value,
                    "new_value": value,
                    "set_at": datetime.now().isoformat()
                }

            elif operation == "unset":
                if not key:
                    return {"error": "Key is required for unset operation"}

                old_value = os.environ.pop(key, None)

                return {
                    "operation": "unset",
                    "key": key,
                    "old_value": old_value,
                    "existed": old_value is not None,
                    "unset_at": datetime.now().isoformat()
                }

            elif operation == "load_from_file":
                if not env_file or not os.path.exists(env_file):
                    return {"error": f"Environment file not found: {env_file}"}

                env_data = self._load_env(env_file)
                loaded_vars = []

                for env_key, env_value in env_data.items():
                    old_value = os.environ.get(env_key)
                    os.environ[env_key] = env_value
                    loaded_vars.append({
                        "key": env_key,
                        "old_value": old_value,
                        "new_value": env_value
                    })

                return {
                    "operation": "load_from_file",
                    "env_file": env_file,
                    "loaded_variables": loaded_vars,
                    "loaded_count": len(loaded_vars),
                    "loaded_at": datetime.now().isoformat()
                }

            elif operation == "backup":
                # Backup current environment
                self.env_backup = dict(os.environ)

                return {
                    "operation": "backup",
                    "backed_up_count": len(self.env_backup),
                    "backed_up_at": datetime.now().isoformat()
                }

            elif operation == "restore":
                if not self.env_backup:
                    return {"error": "No environment backup available"}

                # Clear current environment and restore backup
                os.environ.clear()
                os.environ.update(self.env_backup)

                return {
                    "operation": "restore",
                    "restored_count": len(self.env_backup),
                    "restored_at": datetime.now().isoformat()
                }

            else:
                return {"error": f"Unknown environment operation: {operation}"}

        except Exception as e:
            return {"error": f"Environment management error: {str(e)}"}

    async def _convert_format(self, input_file: str, output_file: str,
                            target_format: Optional[str] = None) -> Dict[str, Any]:
        """Convert configuration file between formats"""
        # Load input file
        load_result = await self._load_config(input_file)
        if "error" in load_result:
            return load_result

        # Determine target format
        if target_format is None:
            target_format = self._detect_format(output_file)

        if target_format not in self.supported_formats:
            return {"error": f"Unsupported target format: {target_format}"}

        # Save in target format
        save_result = await self._save_config(output_file, load_result["config_data"], target_format)
        if "error" in save_result:
            return save_result

        return {
            "input_file": input_file,
            "input_format": load_result["format"],
            "output_file": output_file,
            "output_format": target_format,
            "converted_at": datetime.now().isoformat()
        }

    async def _list_configs(self, directory: str, recursive: bool = True) -> Dict[str, Any]:
        """List configuration files in directory"""
        if not os.path.exists(directory):
            return {"error": f"Directory not found: {directory}"}

        config_files = []

        # Get all supported extensions
        all_extensions = []
        for format_info in self.supported_formats.values():
            all_extensions.extend(format_info['extensions'])

        # Scan directory
        if recursive:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if any(file.lower().endswith(ext) for ext in all_extensions):
                        format_type = self._detect_format(file_path)
                        file_stat = os.stat(file_path)

                        config_files.append({
                            "file_path": file_path,
                            "relative_path": os.path.relpath(file_path, directory),
                            "format": format_type,
                            "size": file_stat.st_size,
                            "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                        })
        else:
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in all_extensions):
                    format_type = self._detect_format(file_path)
                    file_stat = os.stat(file_path)

                    config_files.append({
                        "file_path": file_path,
                        "relative_path": file,
                        "format": format_type,
                        "size": file_stat.st_size,
                        "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                    })

        # Group by format
        format_summary = {}
        for config_file in config_files:
            fmt = config_file["format"]
            if fmt not in format_summary:
                format_summary[fmt] = 0
            format_summary[fmt] += 1

        return {
            "directory": directory,
            "recursive": recursive,
            "total_configs": len(config_files),
            "format_summary": format_summary,
            "config_files": sorted(config_files, key=lambda x: x["file_path"]),
            "scanned_at": datetime.now().isoformat()
        }
