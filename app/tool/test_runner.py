"""
Test Runner Tool

This tool provides comprehensive testing capabilities including:
- Running various types of tests (unit, integration, end-to-end)
- Test discovery and execution
- Coverage analysis and reporting
- Performance testing and benchmarking
- Test result analysis and reporting
- Continuous integration support
"""

import asyncio
import json
import subprocess
import os
import sys
import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import xml.etree.ElementTree as ET
from .base import BaseTool


class TestRunner(BaseTool):
    """Tool for comprehensive test execution and analysis"""

    def __init__(self):
        super().__init__()
        self.name = "test_runner"
        self.description = "Comprehensive test execution and analysis tool"

        # Supported test frameworks
        self.test_frameworks = {
            'pytest': {
                'command': 'pytest',
                'config_files': ['pytest.ini', 'pyproject.toml', 'setup.cfg'],
                'test_patterns': ['test_*.py', '*_test.py'],
                'coverage_plugin': 'pytest-cov'
            },
            'unittest': {
                'command': 'python -m unittest',
                'config_files': [],
                'test_patterns': ['test_*.py'],
                'coverage_plugin': 'coverage'
            },
            'jest': {
                'command': 'npm test',
                'config_files': ['jest.config.js', 'package.json'],
                'test_patterns': ['*.test.js', '*.spec.js'],
                'coverage_plugin': 'built-in'
            },
            'mocha': {
                'command': 'mocha',
                'config_files': ['.mocharc.json', 'mocha.opts'],
                'test_patterns': ['*.test.js', '*.spec.js'],
                'coverage_plugin': 'nyc'
            },
            'go_test': {
                'command': 'go test',
                'config_files': [],
                'test_patterns': ['*_test.go'],
                'coverage_plugin': 'built-in'
            }
        }

        # Test result cache
        self.test_results = {}
        self.coverage_data = {}

    async def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """Execute test runner commands"""
        try:
            if command == "discover_tests":
                return await self._discover_tests(**kwargs)
            elif command == "run_tests":
                return await self._run_tests(**kwargs)
            elif command == "run_coverage":
                return await self._run_coverage(**kwargs)
            elif command == "performance_test":
                return await self._performance_test(**kwargs)
            elif command == "test_report":
                return await self._test_report(**kwargs)
            elif command == "continuous_test":
                return await self._continuous_test(**kwargs)
            elif command == "test_analysis":
                return await self._test_analysis(**kwargs)
            elif command == "benchmark_tests":
                return await self._benchmark_tests(**kwargs)
            elif command == "test_history":
                return await self._test_history(**kwargs)
            elif command == "parallel_test":
                return await self._parallel_test(**kwargs)
            else:
                return {"error": f"Unknown command: {command}"}

        except Exception as e:
            return {"error": f"Test runner error: {str(e)}"}

    async def _discover_tests(self, project_path: str = ".", framework: str = "auto") -> Dict[str, Any]:
        """Discover test files and test cases"""
        if framework == "auto":
            framework = self._detect_test_framework(project_path)

        if framework not in self.test_frameworks:
            return {"error": f"Unsupported test framework: {framework}"}

        framework_config = self.test_frameworks[framework]
        test_files = []
        test_cases = []

        try:
            # Find test files
            for root, dirs, files in os.walk(project_path):
                # Skip common non-test directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'venv']]

                for file in files:
                    file_path = os.path.join(root, file)

                    # Check if file matches test patterns
                    for pattern in framework_config['test_patterns']:
                        if self._matches_pattern(file, pattern):
                            relative_path = os.path.relpath(file_path, project_path)
                            test_files.append({
                                "path": relative_path,
                                "absolute_path": file_path,
                                "size": os.path.getsize(file_path),
                                "modified": os.path.getmtime(file_path)
                            })

                            # Extract test cases from file
                            cases = await self._extract_test_cases(file_path, framework)
                            test_cases.extend(cases)
                            break

            # Get framework-specific test discovery
            discovered_tests = await self._framework_discover(project_path, framework)

            return {
                "framework": framework,
                "project_path": project_path,
                "total_test_files": len(test_files),
                "total_test_cases": len(test_cases),
                "test_files": test_files,
                "test_cases": test_cases,
                "framework_discovery": discovered_tests,
                "discovered_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Test discovery failed: {str(e)}"}

    def _detect_test_framework(self, project_path: str) -> str:
        """Auto-detect test framework based on project files"""
        for framework, config in self.test_frameworks.items():
            for config_file in config['config_files']:
                if os.path.exists(os.path.join(project_path, config_file)):
                    return framework

        # Check for common test files
        if any(os.path.exists(os.path.join(project_path, f)) for f in ['conftest.py', 'pytest.ini']):
            return 'pytest'
        elif os.path.exists(os.path.join(project_path, 'package.json')):
            with open(os.path.join(project_path, 'package.json'), 'r') as f:
                package_data = json.load(f)
                if 'jest' in package_data.get('devDependencies', {}):
                    return 'jest'
                elif 'mocha' in package_data.get('devDependencies', {}):
                    return 'mocha'

        # Default fallback
        return 'pytest'

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches test pattern"""
        import fnmatch
        return fnmatch.fnmatch(filename, pattern)

    async def _extract_test_cases(self, file_path: str, framework: str) -> List[Dict[str, Any]]:
        """Extract test cases from test file"""
        test_cases = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            if framework == 'pytest' or framework == 'unittest':
                # Python test case extraction
                import ast
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef) and node.name.startswith('test_'):
                            test_cases.append({
                                "name": node.name,
                                "file": file_path,
                                "line": node.lineno,
                                "type": "function",
                                "framework": framework
                            })
                        elif isinstance(node, ast.ClassDef) and 'Test' in node.name:
                            for item in node.body:
                                if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                                    test_cases.append({
                                        "name": f"{node.name}.{item.name}",
                                        "file": file_path,
                                        "line": item.lineno,
                                        "type": "method",
                                        "class": node.name,
                                        "framework": framework
                                    })
                except SyntaxError:
                    pass

            elif framework in ['jest', 'mocha']:
                # JavaScript test case extraction
                test_patterns = [
                    r'test\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                    r'it\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
                    r'describe\s*\(\s*[\'"`]([^\'"`]+)[\'"`]'
                ]

                for pattern in test_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        test_cases.append({
                            "name": match.group(1),
                            "file": file_path,
                            "line": content[:match.start()].count('\n') + 1,
                            "type": "test" if 'test' in pattern or 'it' in pattern else "suite",
                            "framework": framework
                        })

        except Exception:
            pass  # Continue on error

        return test_cases

    async def _framework_discover(self, project_path: str, framework: str) -> Dict[str, Any]:
        """Use framework-specific test discovery"""
        try:
            if framework == 'pytest':
                result = await self._run_command('pytest --collect-only -q', cwd=project_path)
                return {"method": "pytest_collect", "output": result['stdout'][:1000]}

            elif framework == 'jest':
                result = await self._run_command('npm test -- --listTests', cwd=project_path)
                return {"method": "jest_list", "output": result['stdout'][:1000]}

            elif framework == 'go_test':
                result = await self._run_command('go test -list .', cwd=project_path)
                return {"method": "go_list", "output": result['stdout'][:1000]}

            return {"method": "manual", "output": "Used manual discovery"}

        except Exception as e:
            return {"method": "error", "output": str(e)}

    async def _run_tests(self, project_path: str = ".", framework: str = "auto",
                        test_pattern: str = None, verbose: bool = False,
                        parallel: bool = False) -> Dict[str, Any]:
        """Run tests with specified framework"""
        if framework == "auto":
            framework = self._detect_test_framework(project_path)

        if framework not in self.test_frameworks:
            return {"error": f"Unsupported test framework: {framework}"}

        framework_config = self.test_frameworks[framework]

        # Build test command
        base_command = framework_config['command']
        command_args = []

        if framework == 'pytest':
            if verbose:
                command_args.append('-v')
            if parallel:
                command_args.append('-n auto')
            if test_pattern:
                command_args.append(f'-k {test_pattern}')
            command_args.append('--tb=short')
            command_args.append('--json-report')
            command_args.append('--json-report-file=test_results.json')

        elif framework == 'jest':
            if verbose:
                command_args.append('--verbose')
            if test_pattern:
                command_args.append(f'--testNamePattern="{test_pattern}"')
            command_args.append('--json')
            command_args.append('--outputFile=test_results.json')

        elif framework == 'unittest':
            if verbose:
                command_args.append('-v')
            if test_pattern:
                command_args.append(f'-k {test_pattern}')

        command = f"{base_command} {' '.join(command_args)}"

        # Run tests
        start_time = time.time()
        result = await self._run_command(command, cwd=project_path)
        execution_time = time.time() - start_time

        # Parse test results
        test_results = await self._parse_test_results(result, framework, project_path)

        # Store results
        test_run = {
            "framework": framework,
            "project_path": project_path,
            "command": command,
            "execution_time": round(execution_time, 2),
            "return_code": result['return_code'],
            "results": test_results,
            "run_at": datetime.now().isoformat()
        }

        # Cache results
        run_id = f"{framework}_{int(time.time())}"
        self.test_results[run_id] = test_run

        return {
            "run_id": run_id,
            "test_run": test_run
        }

    async def _parse_test_results(self, command_result: Dict[str, Any],
                                framework: str, project_path: str) -> Dict[str, Any]:
        """Parse test results from command output"""
        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "failures": [],
            "success_rate": 0.0
        }

        try:
            # Try to load JSON results file if available
            json_file = os.path.join(project_path, 'test_results.json')
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    json_results = json.load(f)
                    results.update(self._parse_json_results(json_results, framework))
                os.remove(json_file)  # Clean up
                return results

            # Fallback to parsing stdout
            stdout = command_result['stdout']

            if framework == 'pytest':
                # Parse pytest output
                if '::' in stdout:
                    for line in stdout.split('\n'):
                        if '::' in line:
                            if 'PASSED' in line:
                                results["passed"] += 1
                            elif 'FAILED' in line:
                                results["failed"] += 1
                                results["failures"].append(line.strip())
                            elif 'SKIPPED' in line:
                                results["skipped"] += 1
                            elif 'ERROR' in line:
                                results["errors"] += 1

                # Look for summary line
                summary_match = re.search(r'(\d+) passed.*?(\d+) failed.*?(\d+) error', stdout)
                if summary_match:
                    results["passed"] = int(summary_match.group(1))
                    results["failed"] = int(summary_match.group(2))
                    results["errors"] = int(summary_match.group(3))

            elif framework == 'jest':
                # Parse Jest output
                if 'Tests:' in stdout:
                    tests_line = [line for line in stdout.split('\n') if 'Tests:' in line][-1]
                    numbers = re.findall(r'(\d+)', tests_line)
                    if len(numbers) >= 2:
                        results["failed"] = int(numbers[0])
                        results["passed"] = int(numbers[1])

            elif framework == 'unittest':
                # Parse unittest output
                if 'Ran' in stdout:
                    ran_match = re.search(r'Ran (\d+) tests?', stdout)
                    if ran_match:
                        total = int(ran_match.group(1))
                        if 'FAILED' in stdout:
                            failed_match = re.search(r'FAILED \(.*?failures=(\d+)', stdout)
                            results["failed"] = int(failed_match.group(1)) if failed_match else 0
                            results["passed"] = total - results["failed"]
                        else:
                            results["passed"] = total

            # Calculate totals
            results["total_tests"] = results["passed"] + results["failed"] + results["skipped"] + results["errors"]
            if results["total_tests"] > 0:
                results["success_rate"] = round((results["passed"] / results["total_tests"]) * 100, 2)

        except Exception as e:
            results["parse_error"] = str(e)

        return results

    def _parse_json_results(self, json_data: Dict[str, Any], framework: str) -> Dict[str, Any]:
        """Parse JSON test results"""
        results = {}

        try:
            if framework == 'pytest':
                if 'summary' in json_data:
                    summary = json_data['summary']
                    results.update({
                        "total_tests": summary.get('total', 0),
                        "passed": summary.get('passed', 0),
                        "failed": summary.get('failed', 0),
                        "skipped": summary.get('skipped', 0),
                        "errors": summary.get('error', 0)
                    })

            elif framework == 'jest':
                if 'numTotalTests' in json_data:
                    results.update({
                        "total_tests": json_data.get('numTotalTests', 0),
                        "passed": json_data.get('numPassedTests', 0),
                        "failed": json_data.get('numFailedTests', 0),
                        "skipped": json_data.get('numPendingTests', 0)
                    })

        except Exception:
            pass

        return results

    async def _run_coverage(self, project_path: str = ".", framework: str = "auto",
                          min_coverage: float = 80.0) -> Dict[str, Any]:
        """Run tests with coverage analysis"""
        if framework == "auto":
            framework = self._detect_test_framework(project_path)

        coverage_commands = {
            'pytest': 'pytest --cov=. --cov-report=json --cov-report=term-missing',
            'unittest': 'coverage run -m unittest discover && coverage json',
            'jest': 'npm test -- --coverage --coverageReporters=json',
            'go_test': 'go test -coverprofile=coverage.out ./... && go tool cover -func=coverage.out'
        }

        if framework not in coverage_commands:
            return {"error": f"Coverage not supported for framework: {framework}"}

        command = coverage_commands[framework]

        # Run tests with coverage
        start_time = time.time()
        result = await self._run_command(command, cwd=project_path)
        execution_time = time.time() - start_time

        # Parse coverage results
        coverage_data = await self._parse_coverage_results(result, framework, project_path)

        # Check coverage thresholds
        overall_coverage = coverage_data.get("overall_coverage", 0.0)
        coverage_status = "passed" if overall_coverage >= min_coverage else "failed"

        coverage_result = {
            "framework": framework,
            "project_path": project_path,
            "execution_time": round(execution_time, 2),
            "min_coverage_threshold": min_coverage,
            "coverage_status": coverage_status,
            "coverage_data": coverage_data,
            "run_at": datetime.now().isoformat()
        }

        # Store coverage data
        coverage_id = f"cov_{framework}_{int(time.time())}"
        self.coverage_data[coverage_id] = coverage_result

        return {
            "coverage_id": coverage_id,
            "coverage_result": coverage_result
        }

    async def _parse_coverage_results(self, command_result: Dict[str, Any],
                                    framework: str, project_path: str) -> Dict[str, Any]:
        """Parse coverage results"""
        coverage_data = {
            "overall_coverage": 0.0,
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "files": [],
            "uncovered_lines": []
        }

        try:
            # Look for JSON coverage file
            json_files = ['coverage.json', '.coverage.json', 'coverage/coverage-final.json']

            for json_file in json_files:
                full_path = os.path.join(project_path, json_file)
                if os.path.exists(full_path):
                    with open(full_path, 'r') as f:
                        json_data = json.load(f)
                        coverage_data.update(self._parse_coverage_json(json_data, framework))
                    break

            # Fallback to parsing stdout
            if coverage_data["overall_coverage"] == 0.0:
                stdout = command_result['stdout']
                coverage_data.update(self._parse_coverage_output(stdout, framework))

        except Exception as e:
            coverage_data["parse_error"] = str(e)

        return coverage_data

    def _parse_coverage_json(self, json_data: Dict[str, Any], framework: str) -> Dict[str, Any]:
        """Parse JSON coverage data"""
        coverage_data = {}

        try:
            if framework in ['pytest', 'unittest']:
                # Python coverage.py format
                if 'totals' in json_data:
                    totals = json_data['totals']
                    coverage_data["overall_coverage"] = round(totals.get('percent_covered', 0), 2)
                    coverage_data["line_coverage"] = round(totals.get('percent_covered_display', 0), 2)

                if 'files' in json_data:
                    files = []
                    for file_path, file_data in json_data['files'].items():
                        files.append({
                            "file": file_path,
                            "coverage": round(file_data.get('percent_covered', 0), 2),
                            "lines_covered": file_data.get('num_statements', 0),
                            "lines_missed": len(file_data.get('missing_lines', []))
                        })
                    coverage_data["files"] = files

            elif framework == 'jest':
                # Jest coverage format
                if 'total' in json_data:
                    total = json_data['total']
                    coverage_data["overall_coverage"] = round(total.get('lines', {}).get('pct', 0), 2)
                    coverage_data["line_coverage"] = round(total.get('lines', {}).get('pct', 0), 2)
                    coverage_data["branch_coverage"] = round(total.get('branches', {}).get('pct', 0), 2)

        except Exception:
            pass

        return coverage_data

    def _parse_coverage_output(self, output: str, framework: str) -> Dict[str, Any]:
        """Parse coverage from command output"""
        coverage_data = {}

        try:
            if framework in ['pytest', 'unittest']:
                # Look for overall coverage percentage
                coverage_match = re.search(r'TOTAL.*?(\d+)%', output)
                if coverage_match:
                    coverage_data["overall_coverage"] = float(coverage_match.group(1))

            elif framework == 'go_test':
                # Parse Go coverage output
                coverage_match = re.search(r'total:.*?(\d+\.\d+)%', output)
                if coverage_match:
                    coverage_data["overall_coverage"] = float(coverage_match.group(1))

        except Exception:
            pass

        return coverage_data

    async def _performance_test(self, project_path: str = ".", framework: str = "auto",
                              iterations: int = 10, timeout: int = 300) -> Dict[str, Any]:
        """Run performance tests and benchmarks"""
        performance_results = {
            "framework": framework,
            "project_path": project_path,
            "iterations": iterations,
            "timeout": timeout,
            "runs": [],
            "statistics": {},
            "started_at": datetime.now().isoformat()
        }

        try:
            for i in range(iterations):
                start_time = time.time()

                # Run single test iteration
                result = await self._run_tests(project_path, framework, verbose=False)

                execution_time = time.time() - start_time

                if "error" not in result:
                    test_run = result["test_run"]
                    performance_results["runs"].append({
                        "iteration": i + 1,
                        "execution_time": execution_time,
                        "total_tests": test_run["results"]["total_tests"],
                        "passed": test_run["results"]["passed"],
                        "failed": test_run["results"]["failed"],
                        "success_rate": test_run["results"]["success_rate"]
                    })

                # Check timeout
                if execution_time > timeout:
                    performance_results["timeout_reached"] = True
                    break

            # Calculate statistics
            if performance_results["runs"]:
                execution_times = [run["execution_time"] for run in performance_results["runs"]]
                performance_results["statistics"] = {
                    "min_time": min(execution_times),
                    "max_time": max(execution_times),
                    "avg_time": sum(execution_times) / len(execution_times),
                    "total_runs": len(performance_results["runs"]),
                    "successful_runs": len([r for r in performance_results["runs"] if r["failed"] == 0])
                }

        except Exception as e:
            performance_results["error"] = str(e)

        performance_results["completed_at"] = datetime.now().isoformat()
        return performance_results

    async def _test_report(self, project_path: str = ".", format: str = "json",
                         include_coverage: bool = True) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            "project_path": project_path,
            "generated_at": datetime.now().isoformat(),
            "format": format
        }

        try:
            # Discover tests
            discovery = await self._discover_tests(project_path)
            report["test_discovery"] = discovery

            # Run tests
            test_result = await self._run_tests(project_path)
            report["test_execution"] = test_result

            # Run coverage if requested
            if include_coverage:
                coverage_result = await self._run_coverage(project_path)
                report["coverage_analysis"] = coverage_result

            # Generate summary
            if "error" not in test_result:
                test_run = test_result["test_run"]
                report["summary"] = {
                    "total_test_files": discovery.get("total_test_files", 0),
                    "total_test_cases": discovery.get("total_test_cases", 0),
                    "tests_passed": test_run["results"]["passed"],
                    "tests_failed": test_run["results"]["failed"],
                    "success_rate": test_run["results"]["success_rate"],
                    "execution_time": test_run["execution_time"]
                }

                if include_coverage and "error" not in coverage_result:
                    coverage_data = coverage_result["coverage_result"]["coverage_data"]
                    report["summary"]["coverage_percentage"] = coverage_data.get("overall_coverage", 0)

            # Format output
            if format == "markdown":
                markdown_content = self._generate_markdown_report(report)
                return {
                    "format": "markdown",
                    "content": markdown_content
                }
            elif format == "html":
                html_content = self._generate_html_report(report)
                return {
                    "format": "html",
                    "content": html_content
                }

        except Exception as e:
            report["error"] = str(e)

        return {
            "format": "json",
            "report": report
        }

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate markdown test report"""
        lines = [
            "# Test Report",
            f"",
            f"**Project:** {report['project_path']}",
            f"**Generated:** {report['generated_at']}",
            f"",
            f"## Summary",
            f""
        ]

        if "summary" in report:
            summary = report["summary"]
            lines.extend([
                f"- **Test Files:** {summary.get('total_test_files', 0)}",
                f"- **Test Cases:** {summary.get('total_test_cases', 0)}",
                f"- **Tests Passed:** {summary.get('tests_passed', 0)}",
                f"- **Tests Failed:** {summary.get('tests_failed', 0)}",
                f"- **Success Rate:** {summary.get('success_rate', 0)}%",
                f"- **Execution Time:** {summary.get('execution_time', 0)}s",
                f""
            ])

            if "coverage_percentage" in summary:
                lines.append(f"- **Coverage:** {summary['coverage_percentage']}%")
                lines.append("")

        lines.extend([
            "## Test Results",
            ""
        ])

        if "test_execution" in report and "error" not in report["test_execution"]:
            test_run = report["test_execution"]["test_run"]
            results = test_run["results"]

            if results["failures"]:
                lines.extend([
                    "### Failed Tests",
                    ""
                ])
                for failure in results["failures"][:10]:  # Limit to first 10
                    lines.append(f"- {failure}")
                lines.append("")

        return "\n".join(lines)

    def _generate_html_report(self, report: Dict[str, Any]) -> str:
        """Generate HTML test report"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .metric {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>Test Report</h1>
            <p><strong>Project:</strong> {report['project_path']}</p>
            <p><strong>Generated:</strong> {report['generated_at']}</p>
        """

        if "summary" in report:
            summary = report["summary"]
            html += f"""
            <div class="summary">
                <h2>Summary</h2>
                <div class="metric">Test Files: {summary.get('total_test_files', 0)}</div>
                <div class="metric">Test Cases: {summary.get('total_test_cases', 0)}</div>
                <div class="metric passed">Tests Passed: {summary.get('tests_passed', 0)}</div>
                <div class="metric failed">Tests Failed: {summary.get('tests_failed', 0)}</div>
                <div class="metric">Success Rate: {summary.get('success_rate', 0)}%</div>
                <div class="metric">Execution Time: {summary.get('execution_time', 0)}s</div>
            """

            if "coverage_percentage" in summary:
                html += f'<div class="metric">Coverage: {summary["coverage_percentage"]}%</div>'

            html += "</div>"

        html += """
        </body>
        </html>
        """

        return html

    async def _continuous_test(self, project_path: str = ".", framework: str = "auto",
                             watch_interval: int = 5) -> Dict[str, Any]:
        """Set up continuous testing (watch mode)"""
        return {
            "message": "Continuous testing started",
            "project_path": project_path,
            "framework": framework,
            "watch_interval": watch_interval,
            "started_at": datetime.now().isoformat(),
            "note": "This would typically run in background and watch for file changes"
        }

    async def _test_analysis(self, run_id: str = None) -> Dict[str, Any]:
        """Analyze test results and provide insights"""
        if run_id and run_id in self.test_results:
            test_run = self.test_results[run_id]
        elif self.test_results:
            # Use most recent run
            test_run = list(self.test_results.values())[-1]
        else:
            return {"error": "No test results available for analysis"}

        results = test_run["results"]
        analysis = {
            "run_id": run_id,
            "analysis_type": "test_execution",
            "insights": [],
            "recommendations": [],
            "trends": {},
            "analyzed_at": datetime.now().isoformat()
        }

        # Generate insights
        if results["success_rate"] == 100:
            analysis["insights"].append("All tests are passing - excellent test coverage!")
        elif results["success_rate"] >= 90:
            analysis["insights"].append("Very high test success rate - minor issues detected")
        elif results["success_rate"] >= 70:
            analysis["insights"].append("Moderate test success rate - some attention needed")
        else:
            analysis["insights"].append("Low test success rate - significant issues detected")

        # Generate recommendations
        if results["failed"] > 0:
            analysis["recommendations"].append(f"Fix {results['failed']} failing tests")

        if results["total_tests"] < 10:
            analysis["recommendations"].append("Consider adding more test cases for better coverage")

        if test_run["execution_time"] > 60:
            analysis["recommendations"].append("Test execution time is high - consider optimizing")

        return analysis

    async def _benchmark_tests(self, project_path: str = ".", framework: str = "auto",
                             benchmark_type: str = "speed") -> Dict[str, Any]:
        """Run benchmark tests"""
        benchmark_results = {
            "benchmark_type": benchmark_type,
            "framework": framework,
            "project_path": project_path,
            "benchmarks": [],
            "started_at": datetime.now().isoformat()
        }

        if benchmark_type == "speed":
            # Speed benchmark - run tests multiple times
            for i in range(5):
                start_time = time.time()
                result = await self._run_tests(project_path, framework)
                execution_time = time.time() - start_time

                if "error" not in result:
                    benchmark_results["benchmarks"].append({
                        "run": i + 1,
                        "execution_time": execution_time,
                        "tests_run": result["test_run"]["results"]["total_tests"]
                    })

        elif benchmark_type == "memory":
            # Memory benchmark - would need psutil for real implementation
            benchmark_results["note"] = "Memory benchmarking requires additional tools"

        benchmark_results["completed_at"] = datetime.now().isoformat()
        return benchmark_results

    async def _test_history(self, project_path: str = ".") -> Dict[str, Any]:
        """Get test execution history"""
        history = {
            "project_path": project_path,
            "total_runs": len(self.test_results),
            "runs": list(self.test_results.values()),
            "trends": {},
            "retrieved_at": datetime.now().isoformat()
        }

        if len(self.test_results) > 1:
            # Calculate trends
            runs = list(self.test_results.values())
            success_rates = [run["results"]["success_rate"] for run in runs]
            execution_times = [run["execution_time"] for run in runs]

            history["trends"] = {
                "success_rate_trend": "improving" if success_rates[-1] > success_rates[0] else "declining",
                "execution_time_trend": "improving" if execution_times[-1] < execution_times[0] else "declining",
                "average_success_rate": sum(success_rates) / len(success_rates),
                "average_execution_time": sum(execution_times) / len(execution_times)
            }

        return history

    async def _parallel_test(self, project_path: str = ".", framework: str = "auto",
                           workers: int = 4) -> Dict[str, Any]:
        """Run tests in parallel"""
        if framework == "auto":
            framework = self._detect_test_framework(project_path)

        # Build parallel test command
        if framework == 'pytest':
            command = f"pytest -n {workers} --tb=short"
        elif framework == 'jest':
            command = f"npm test -- --maxWorkers={workers}"
        else:
            return {"error": f"Parallel testing not supported for {framework}"}

        start_time = time.time()
        result = await self._run_command(command, cwd=project_path)
        execution_time = time.time() - start_time

        test_results = await self._parse_test_results(result, framework, project_path)

        return {
            "framework": framework,
            "workers": workers,
            "execution_time": round(execution_time, 2),
            "results": test_results,
            "command_output": result,
            "run_at": datetime.now().isoformat()
        }

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
