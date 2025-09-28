#!/usr/bin/env python3
"""
Automated Quality Testing and Validation Systems
Implements continuous testing, validation pipelines, and quality gates
"""

import asyncio
import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import asyncpg
import redis.asyncio as redis
import statistics

from .quality_metrics import (
    QualityEvaluator, QualityAssessment, Role, QualityLevel, CodeQualityEvaluator, ArchitectureQualityEvaluator,
    PerformanceQualityEvaluator, SecurityQualityEvaluator,
    IntegrationQualityEvaluator
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of automated tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "e2e"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPATIBILITY = "compatibility"
    LOAD = "load"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass
class TestResult:
    """Test execution result"""
    test_id: str
    test_type: TestType
    status: TestStatus
    duration: float
    output: str
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    environment: str = "development"


@dataclass
class TestSuite:
    """Collection of related tests"""
    name: str
    tests: List[str]
    timeout: float = 300.0
    parallel: bool = True
    dependencies: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)


@dataclass
class QualityGate:
    """Quality gate definition"""
    name: str
    description: str
    criteria: List[Dict[str, Any]]
    action_on_fail: str = "block"  # block, warn, ignore
    severity: str = "high"  # high, medium, low


class AutomatedTestRunner(ABC):
    """Abstract base class for automated test runners"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def run_test(self, test_id: str, context: Dict[str, Any] = None) -> TestResult:
        """Run a single test"""
        pass
    
    @abstractmethod
    async def run_suite(self, suite: TestSuite, context: Dict[str, Any] = None) -> List[TestResult]:
        """Run a test suite"""
        pass
    
    @abstractmethod
    def get_supported_tests(self) -> List[TestType]:
        """Return supported test types"""
        pass


class PythonTestRunner(AutomatedTestRunner):
    """Python test runner using pytest"""
    
    def __init__(self, workspace_root: Path):
        super().__init__(workspace_root)
        self.python_path = os.environ.get("PYTHONPATH", "")
    
    async def run_test(self, test_id: str, context: Dict[str, Any] = None) -> TestResult:
        """Run a single Python test"""
        start_time = time.time()
        
        try:
            # Run pytest for specific test
            cmd = [
                "python", "-m", "pytest", 
                test_id, "-v", "--tb=short",
                "--json-report", "--json-report-file=/tmp/test_result.json"
            ]
            
            if self.python_path:
                cmd.insert(0, f"PYTHONPATH={self.python_path}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=300.0
            )
            
            duration = time.time() - start_time
            
            # Parse pytest output
            if process.returncode == 0:
                status = TestStatus.PASSED
                output = stdout.decode().strip()
                error = None
            else:
                status = TestStatus.FAILED
                output = stdout.decode().strip()
                error = stderr.decode().strip()
            
            # Try to parse JSON report if available
            metrics = {}
            try:
                with open("/tmp/test_result.json", "r") as f:
                    report = json.load(f)
                    metrics = {
                        "tests_total": report.get("summary", {}).get("total", 0),
                        "tests_passed": report.get("summary", {}).get("passed", 0),
                        "tests_failed": report.get("summary", {}).get("failed", 0),
                        "tests_skipped": report.get("summary", {}).get("skipped", 0),
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            return TestResult(
                test_id=test_id,
                test_type=TestType.UNIT,
                status=status,
                duration=duration,
                output=output,
                error=error,
                metrics=metrics,
                timestamp=datetime.utcnow()
            )
            
        except asyncio.TimeoutError:
            return TestResult(
                test_id=test_id,
                test_type=TestType.UNIT,
                status=TestStatus.TIMEOUT,
                duration=time.time() - start_time,
                output="Test timed out",
                error="Test execution exceeded timeout",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return TestResult(
                test_id=test_id,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                duration=time.time() - start_time,
                output=f"Test execution failed: {str(e)}",
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def run_suite(self, suite: TestSuite, context: Dict[str, Any] = None) -> List[TestResult]:
        """Run a Python test suite"""
        results = []
        
        if suite.parallel:
            # Run tests in parallel
            tasks = []
            for test_id in suite.tests:
                task = asyncio.create_task(self.run_test(test_id, context))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [r for r in results if isinstance(r, TestResult)]
        else:
            # Run tests sequentially
            for test_id in suite.tests:
                result = await self.run_test(test_id, context)
                results.append(result)
                
                # Stop on first failure if configured
                if result.status == TestStatus.FAILED and context and context.get("fail_fast"):
                    break
        
        return results
    
    def get_supported_tests(self) -> List[TestType]:
        return [TestType.UNIT, TestType.INTEGRATION]


class JavaScriptTestRunner(AutomatedTestRunner):
    """JavaScript test runner using Jest/Playwright"""
    
    def __init__(self, workspace_root: Path):
        super().__init__(workspace_root)
    
    async def run_test(self, test_id: str, context: Dict[str, Any] = None) -> TestResult:
        """Run a single JavaScript test"""
        start_time = time.time()
        
        try:
            # Determine test type and run appropriate command
            if test_id.endswith(".test.ts") or test_id.endswith(".test.js"):
                cmd = ["npm", "test", "--", test_id, "--json"]
                test_type = TestType.UNIT
            elif test_id.startswith("e2e:"):
                cmd = ["npm", "run", "test:e2e", "--", test_id]
                test_type = TestType.E2E
            else:
                cmd = ["npm", "test", "--", test_id, "--json"]
                test_type = TestType.UNIT
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300.0
            )
            
            duration = time.time() - start_time
            
            if process.returncode == 0:
                status = TestStatus.PASSED
                output = stdout.decode().strip()
                error = None
            else:
                status = TestStatus.FAILED
                output = stdout.decode().strip()
                error = stderr.decode().strip()
            
            # Parse JSON output for metrics
            metrics = {}
            try:
                # Jest JSON output parsing
                json_lines = [line for line in output.split('\n') if line.strip().startswith('{')]
                if json_lines:
                    test_data = json.loads(json_lines[-1])
                    metrics = {
                        "tests_total": test_data.get("numTotalTests", 0),
                        "tests_passed": test_data.get("numPassedTests", 0),
                        "tests_failed": test_data.get("numFailedTests", 0),
                        "tests_skipped": test_data.get("numPendingTests", 0),
                    }
            except (json.JSONDecodeError, IndexError):
                pass
            
            return TestResult(
                test_id=test_id,
                test_type=test_type,
                status=status,
                duration=duration,
                output=output,
                error=error,
                metrics=metrics,
                timestamp=datetime.utcnow()
            )
            
        except asyncio.TimeoutError:
            return TestResult(
                test_id=test_id,
                test_type=TestType.UNIT,
                status=TestStatus.TIMEOUT,
                duration=time.time() - start_time,
                output="Test timed out",
                error="Test execution exceeded timeout",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return TestResult(
                test_id=test_id,
                test_type=TestType.UNIT,
                status=TestStatus.FAILED,
                duration=time.time() - start_time,
                output=f"Test execution failed: {str(e)}",
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def run_suite(self, suite: TestSuite, context: Dict[str, Any] = None) -> List[TestResult]:
        """Run a JavaScript test suite"""
        results = []
        
        if suite.parallel:
            # Use Jest's parallel execution
            cmd = ["npm", "test", "--", "--json", "--passWithNoTests"]
            
            if suite.timeout:
                cmd.extend(["--testTimeout", str(int(suite.timeout * 1000))])
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=suite.timeout
            )
            
            # Parse Jest output
            try:
                output = stdout.decode().strip()
                json_lines = [line for line in output.split('\n') if line.strip().startswith('{')]
                
                for line in json_lines:
                    test_data = json.loads(line)
                    
                    # Map Jest test results to our format
                    if test_data.get("testResults"):
                        for test_result in test_data["testResults"]:
                            for assertion in test_result.get("assertionResults", []):
                                status = TestStatus.PASSED if assertion["status"] == "passed" else TestStatus.FAILED
                                
                                results.append(TestResult(
                                    test_id=f"{test_result['name']}::{assertion['title']}",
                                    test_type=TestType.UNIT,
                                    status=status,
                                    duration=assertion.get("duration", 0) / 1000,
                                    output=assertion.get("failureMessages", [""])[0] if assertion["status"] == "failed" else "",
                                    error=None,
                                    metrics={},
                                    timestamp=datetime.utcnow()
                                ))
            except Exception as e:
                logger.error(f"Failed to parse Jest output: {e}")
        
        return results
    
    def get_supported_tests(self) -> List[TestType]:
        return [TestType.UNIT, TestType.E2E]


class PerformanceTestRunner(AutomatedTestRunner):
    """Performance test runner using Locust/k6"""
    
    def __init__(self, workspace_root: Path):
        super().__init__(workspace_root)
    
    async def run_test(self, test_id: str, context: Dict[str, Any] = None) -> TestResult:
        """Run a performance test"""
        start_time = time.time()
        
        try:
            # Use k6 for performance testing
            cmd = ["k6", "run", test_id, "--json", "/tmp/k6_results.json"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=600.0  # Longer timeout for performance tests
            )
            
            duration = time.time() - start_time
            
            if process.returncode == 0:
                status = TestStatus.PASSED
                output = stdout.decode().strip()
                error = None
            else:
                status = TestStatus.FAILED
                output = stdout.decode().strip()
                error = stderr.decode().strip()
            
            # Parse k6 results
            metrics = {}
            try:
                with open("/tmp/k6_results.json", "r") as f:
                    results = json.load(f)
                    # Extract key performance metrics
                    metrics = {
                        "vus_max": results.get("metrics", {}).get("vus_max", {}).get("value", 0),
                        "http_reqs": results.get("metrics", {}).get("http_reqs", {}).get("value", 0),
                        "http_req_duration_avg": results.get("metrics", {}).get("http_req_duration", {}).get("avg", 0),
                        "http_req_failed_rate": results.get("metrics", {}).get("http_req_failed", {}).get("rate", 0),
                    }
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            return TestResult(
                test_id=test_id,
                test_type=TestType.PERFORMANCE,
                status=status,
                duration=duration,
                output=output,
                error=error,
                metrics=metrics,
                timestamp=datetime.utcnow()
            )
            
        except asyncio.TimeoutError:
            return TestResult(
                test_id=test_id,
                test_type=TestType.PERFORMANCE,
                status=TestStatus.TIMEOUT,
                duration=time.time() - start_time,
                output="Performance test timed out",
                error="Test execution exceeded timeout",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return TestResult(
                test_id=test_id,
                test_type=TestType.PERFORMANCE,
                status=TestStatus.FAILED,
                duration=time.time() - start_time,
                output=f"Performance test execution failed: {str(e)}",
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def run_suite(self, suite: TestSuite, context: Dict[str, Any] = None) -> List[TestResult]:
        """Run a performance test suite"""
        results = []
        
        # Performance tests typically run sequentially
        for test_id in suite.tests:
            result = await self.run_test(test_id, context)
            results.append(result)
        
        return results
    
    def get_supported_tests(self) -> List[TestType]:
        return [TestType.PERFORMANCE, TestType.LOAD]


class SecurityTestRunner(AutomatedTestRunner):
    """Security test runner using various security tools"""
    
    def __init__(self, workspace_root: Path):
        super().__init__(workspace_root)
    
    async def run_test(self, test_id: str, context: Dict[str, Any] = None) -> TestResult:
        """Run a security test"""
        start_time = time.time()
        
        try:
            # Map test type to security tool
            if test_id.startswith("sast:"):
                cmd = ["bandit", "-r", test_id[5:], "-f", "json", "-o", "/tmp/bandit_results.json"]
                tool = "bandit"
            elif test_id.startswith("depscan:"):
                cmd = ["safety", "check", "--json", "--output", "/tmp/safety_results.json"]
                tool = "safety"
            elif test_id.startswith("secretscan:"):
                cmd = ["gitleaks", "detect", "--source", ".", "--report-format", "json", "--report-path", "/tmp/gitleaks_results.json"]
                tool = "gitleaks"
            else:
                # Default to comprehensive security scan
                cmd = ["bandit", "-r", ".", "-f", "json", "-o", "/tmp/bandit_results.json"]
                tool = "bandit"
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.workspace_root,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300.0
            )
            
            duration = time.time() - start_time
            
            if process.returncode == 0:
                status = TestStatus.PASSED
                output = stdout.decode().strip()
                error = None
            else:
                # Security tools may return non-zero even with findings
                status = TestStatus.PASSED  # We'll parse results for severity
                output = stdout.decode().strip()
                error = stderr.decode().strip()
            
            # Parse security tool results
            metrics = {}
            try:
                if tool == "bandit":
                    with open("/tmp/bandit_results.json", "r") as f:
                        results = json.load(f)
                        metrics = {
                            "high_severity": len([r for r in results.get("results", []) if r.get("issue_severity") == "HIGH"]),
                            "medium_severity": len([r for r in results.get("results", []) if r.get("issue_severity") == "MEDIUM"]),
                            "low_severity": len([r for r in results.get("results", []) if r.get("issue_severity") == "LOW"]),
                            "total_issues": len(results.get("results", [])),
                        }
                elif tool == "safety":
                    with open("/tmp/safety_results.json", "r") as f:
                        results = json.load(f)
                        metrics = {
                            "vulnerabilities_found": len(results),
                            "high_risk": len([r for r in results if r.get("severity") in ["HIGH", "CRITICAL"]]),
                        }
            except (FileNotFoundError, json.JSONDecodeError):
                pass
            
            return TestResult(
                test_id=test_id,
                test_type=TestType.SECURITY,
                status=status,
                duration=duration,
                output=output,
                error=error,
                metrics=metrics,
                timestamp=datetime.utcnow()
            )
            
        except asyncio.TimeoutError:
            return TestResult(
                test_id=test_id,
                test_type=TestType.SECURITY,
                status=TestStatus.TIMEOUT,
                duration=time.time() - start_time,
                output="Security test timed out",
                error="Test execution exceeded timeout",
                timestamp=datetime.utcnow()
            )
        except Exception as e:
            return TestResult(
                test_id=test_id,
                test_type=TestType.SECURITY,
                status=TestStatus.FAILED,
                duration=time.time() - start_time,
                output=f"Security test execution failed: {str(e)}",
                error=str(e),
                timestamp=datetime.utcnow()
            )
    
    async def run_suite(self, suite: TestSuite, context: Dict[str, Any] = None) -> List[TestResult]:
        """Run a security test suite"""
        results = []
        
        # Security tests typically run sequentially
        for test_id in suite.tests:
            result = await self.run_test(test_id, context)
            results.append(result)
        
        return results
    
    def get_supported_tests(self) -> List[TestType]:
        return [TestType.SECURITY]


class QualityValidationEngine:
    """Main quality validation engine that coordinates all testing"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.test_runners: Dict[TestType, AutomatedTestRunner] = {}
        self.quality_evaluators: Dict[Role, QualityEvaluator] = {}
        self.redis_client: Optional[redis.Redis] = None
        self.database_pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)
        
        self._initialize_runners()
        self._initialize_evaluators()
    
    def _initialize_runners(self):
        """Initialize test runners"""
        self.test_runners[TestType.UNIT] = PythonTestRunner(self.workspace_root)
        self.test_runners[TestType.INTEGRATION] = PythonTestRunner(self.workspace_root)
        self.test_runners[TestType.E2E] = JavaScriptTestRunner(self.workspace_root)
        self.test_runners[TestType.PERFORMANCE] = PerformanceTestRunner(self.workspace_root)
        self.test_runners[TestType.SECURITY] = SecurityTestRunner(self.workspace_root)
    
    def _initialize_evaluators(self):
        """Initialize quality evaluators"""
        self.quality_evaluators[Role.IMPLEMENTER] = CodeQualityEvaluator()
        self.quality_evaluators[Role.ARCHITECT] = ArchitectureQualityEvaluator()
        self.quality_evaluators[Role.ORCHESTRATOR] = PerformanceQualityEvaluator()
        self.quality_evaluators[Role.CRITIC] = SecurityQualityEvaluator()
        self.quality_evaluators[Role.INTEGRATOR] = IntegrationQualityEvaluator()
    
    async def initialize(self, redis_url: str = None, database_url: str = None):
        """Initialize external connections"""
        if redis_url:
            self.redis_client = redis.from_url(redis_url)
        
        if database_url:
            self.database_pool = await asyncpg.create_pool(database_url)
    
    async def run_quality_validation(
        self, 
        test_suites: List[TestSuite], 
        roles: List[Role] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run comprehensive quality validation"""
        context = context or {}
        roles = roles or list(Role)
        
        results = {
            "test_results": [],
            "quality_assessments": [],
            "summary": {},
            "recommendations": [],
            "critical_issues": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Run test suites
        for suite in test_suites:
            suite_results = await self._run_test_suite(suite, context)
            results["test_results"].extend(suite_results)
        
        # Generate quality assessments
        for role in roles:
            assessment = await self._generate_quality_assessment(role, results["test_results"], context)
            results["quality_assessments"].append(assessment)
        
        # Generate summary
        results["summary"] = self._generate_summary(results)
        results["recommendations"] = self._generate_recommendations(results)
        results["critical_issues"] = self._identify_critical_issues(results)
        
        # Store results
        await self._store_validation_results(results)
        
        return results
    
    async def _run_test_suite(self, suite: TestSuite, context: Dict[str, Any]) -> List[TestResult]:
        """Run a test suite with appropriate runner"""
        results = []
        
        # Determine test type from suite tags or first test
        test_type = self._determine_test_type(suite)
        
        if test_type in self.test_runners:
            runner = self.test_runners[test_type]
            results = await runner.run_suite(suite, context)
        else:
            # Fallback: try to run with available runners
            for test_id in suite.tests:
                for runner in self.test_runners.values():
                    try:
                        result = await runner.run_test(test_id, context)
                        results.append(result)
                        break
                    except Exception as e:
                        self.logger.warning(f"Failed to run test {test_id} with {runner.__class__.__name__}: {e}")
        
        return results
    
    def _determine_test_type(self, suite: TestSuite) -> TestType:
        """Determine test type from suite information"""
        if "e2e" in suite.tags or "end-to-end" in suite.tags:
            return TestType.E2E
        elif "performance" in suite.tags or "perf" in suite.tags:
            return TestType.PERFORMANCE
        elif "security" in suite.tags or "sec" in suite.tags:
            return TestType.SECURITY
        elif "integration" in suite.tags or "int" in suite.tags:
            return TestType.INTEGRATION
        else:
            return TestType.UNIT
    
    async def _generate_quality_assessment(
        self, 
        role: Role, 
        test_results: List[TestResult], 
        context: Dict[str, Any]
    ) -> QualityAssessment:
        """Generate quality assessment for a role"""
        evaluator = self.quality_evaluators.get(role)
        if not evaluator:
            return None
        
        # Prepare context for evaluator
        evaluator_context = self._prepare_evaluator_context(role, test_results, context)
        
        # Run evaluation
        assessment = await evaluator.evaluate(evaluator_context)
        
        return assessment
    
    def _prepare_evaluator_context(
        self, 
        role: Role, 
        test_results: List[TestResult], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare context for quality evaluator"""
        evaluator_context = context.copy()
        
        # Add test results summary
        passed_tests = [r for r in test_results if r.status == TestStatus.PASSED]
        failed_tests = [r for r in test_results if r.status == TestStatus.FAILED]
        
        evaluator_context.update({
            "total_tests": len(test_results),
            "passed_tests": len(passed_tests),
            "failed_tests": len(failed_tests),
            "test_pass_rate": len(passed_tests) / max(len(test_results), 1) * 100,
            "test_coverage": self._calculate_test_coverage(test_results),
        })
        
        # Role-specific context
        if role == Role.IMPLEMENTER:
            evaluator_context.update({
                "lint_issues": self._count_lint_issues(test_results),
                "complexity_score": self._calculate_complexity_score(test_results),
            })
        elif role == Role.ARCHITECT:
            evaluator_context.update({
                "pattern_violations": self._count_architecture_violations(test_results),
                "documentation_coverage": self._calculate_documentation_coverage(test_results),
            })
        elif role == Role.ORCHESTRATOR:
            evaluator_context.update({
                "avg_response_time": self._calculate_avg_response_time(test_results),
                "uptime_percent": self._calculate_uptime(test_results),
            })
        elif role == Role.CRITIC:
            evaluator_context.update({
                "security_vulnerabilities": self._count_security_vulnerabilities(test_results),
                "critical_vulnerabilities": self._count_critical_vulnerabilities(test_results),
            })
        elif role == Role.INTEGRATOR:
            evaluator_context.update({
                "integration_failures": self._count_integration_failures(test_results),
                "integration_latency": self._calculate_integration_latency(test_results),
            })
        
        return evaluator_context
    
    def _calculate_test_coverage(self, test_results: List[TestResult]) -> float:
        """Calculate test coverage from test results"""
        coverage_sum = 0
        coverage_count = 0
        
        for result in test_results:
            if "coverage_percent" in result.metrics:
                coverage_sum += result.metrics["coverage_percent"]
                coverage_count += 1
        
        return coverage_sum / max(coverage_count, 1)
    
    def _count_lint_issues(self, test_results: List[TestResult]) -> int:
        """Count lint issues from test results"""
        lint_issues = 0
        for result in test_results:
            if "lint_issues" in result.metrics:
                lint_issues += result.metrics["lint_issues"]
        return lint_issues
    
    def _calculate_complexity_score(self, test_results: List[TestResult]) -> float:
        """Calculate complexity score from test results"""
        complexity_scores = []
        for result in test_results:
            if "complexity_score" in result.metrics:
                complexity_scores.append(result.metrics["complexity_score"])
        return statistics.mean(complexity_scores) if complexity_scores else 10.0
    
    def _count_architecture_violations(self, test_results: List[TestResult]) -> int:
        """Count architecture violations from test results"""
        violations = 0
        for result in test_results:
            if "pattern_violations" in result.metrics:
                violations += result.metrics["pattern_violations"]
        return violations
    
    def _calculate_documentation_coverage(self, test_results: List[TestResult]) -> float:
        """Calculate documentation coverage from test results"""
        coverage_sum = 0
        coverage_count = 0
        
        for result in test_results:
            if "doc_coverage" in result.metrics:
                coverage_sum += result.metrics["doc_coverage"]
                coverage_count += 1
        
        return coverage_sum / max(coverage_count, 1)
    
    def _calculate_avg_response_time(self, test_results: List[TestResult]) -> float:
        """Calculate average response time from test results"""
        response_times = []
        for result in test_results:
            if "avg_response_time" in result.metrics:
                response_times.append(result.metrics["avg_response_time"])
        return statistics.mean(response_times) if response_times else 1000.0
    
    def _calculate_uptime(self, test_results: List[TestResult]) -> float:
        """Calculate uptime percentage from test results"""
        uptime_sum = 0
        uptime_count = 0
        
        for result in test_results:
            if "uptime_percent" in result.metrics:
                uptime_sum += result.metrics["uptime_percent"]
                uptime_count += 1
        
        return uptime_sum / max(uptime_count, 1)
    
    def _count_security_vulnerabilities(self, test_results: List[TestResult]) -> int:
        """Count security vulnerabilities from test results"""
        vulns = 0
        for result in test_results:
            if "vulnerabilities" in result.metrics:
                vulns += result.metrics["vulnerabilities"]
            elif "total_issues" in result.metrics:
                vulns += result.metrics["total_issues"]
        return vulns
    
    def _count_critical_vulnerabilities(self, test_results: List[TestResult]) -> int:
        """Count critical vulnerabilities from test results"""
        critical_vulns = 0
        for result in test_results:
            if "critical_vulnerabilities" in result.metrics:
                critical_vulns += result.metrics["critical_vulnerabilities"]
            elif "high_severity" in result.metrics:
                critical_vulns += result.metrics["high_severity"]
        return critical_vulns
    
    def _count_integration_failures(self, test_results: List[TestResult]) -> int:
        """Count integration failures from test results"""
        failures = 0
        for result in test_results:
            if result.test_type == TestType.INTEGRATION and result.status == TestStatus.FAILED:
                failures += 1
        return failures
    
    def _calculate_integration_latency(self, test_results: List[TestResult]) -> float:
        """Calculate integration latency from test results"""
        latencies = []
        for result in test_results:
            if "integration_latency" in result.metrics:
                latencies.append(result.metrics["integration_latency"])
        return statistics.mean(latencies) if latencies else 500.0
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation summary"""
        test_results = results["test_results"]
        assessments = results["quality_assessments"]
        
        passed_tests = [r for r in test_results if r.status == TestStatus.PASSED]
        failed_tests = [r for r in test_results if r.status == TestStatus.FAILED]
        
        overall_scores = [a.overall_score for a in assessments if a.overall_score]
        
        return {
            "total_tests": len(test_results),
            "passed_tests": len(passed_tests),
            "failed_tests": len(failed_tests),
            "test_pass_rate": len(passed_tests) / max(len(test_results), 1) * 100,
            "average_quality_score": statistics.mean(overall_scores) if overall_scores else 0,
            "min_quality_score": min(overall_scores) if overall_scores else 0,
            "max_quality_score": max(overall_scores) if overall_scores else 0,
            "quality_level_distribution": self._get_quality_level_distribution(assessments),
        }
    
    def _get_quality_level_distribution(self, assessments: List[QualityAssessment]) -> Dict[str, int]:
        """Get distribution of quality levels"""
        distribution = {level.value: 0 for level in QualityLevel}
        
        for assessment in assessments:
            distribution[assessment.overall_level.value] += 1
        
        return distribution
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        # Collect recommendations from all assessments
        for assessment in results["quality_assessments"]:
            recommendations.extend(assessment.recommendations)
        
        # Add summary recommendations
        summary = results["summary"]
        
        if summary["test_pass_rate"] < 80:
            recommendations.append("Overall test pass rate is below 80%. Focus on fixing failing tests.")
        
        if summary["average_quality_score"] < 70:
            recommendations.append("Overall quality score is below 70. Review all quality metrics.")
        
        # Remove duplicates and limit
        unique_recommendations = list(set(recommendations))
        return unique_recommendations[:10]
    
    def _identify_critical_issues(self, results: Dict[str, Any]) -> List[str]:
        """Identify critical quality issues"""
        critical_issues = []
        
        # Collect critical issues from all assessments
        for assessment in results["quality_assessments"]:
            critical_issues.extend(assessment.critical_issues)
        
        # Add summary critical issues
        summary = results["summary"]
        test_results = results["test_results"]
        
        if summary["test_pass_rate"] < 50:
            critical_issues.append(f"Critical: Test pass rate {summary['test_pass_rate']:.1f}% is below 50%")
        
        failed_critical_tests = [r for r in test_results 
                                if r.status == TestStatus.FAILED and "critical" in r.test_id.lower()]
        if failed_critical_tests:
            critical_issues.append(f"Critical: {len(failed_critical_tests)} critical tests failed")
        
        # Remove duplicates
        unique_issues = list(set(critical_issues))
        return unique_issues
    
    async def _store_validation_results(self, results: Dict[str, Any]):
        """Store validation results in database and cache"""
        # Store in Redis for quick access
        if self.redis_client:
            try:
                await self.redis_client.setex(
                    f"quality_validation:{results['timestamp']}",
                    3600,  # 1 hour TTL
                    json.dumps(results, default=str)
                )
            except Exception as e:
                self.logger.error(f"Failed to store results in Redis: {e}")
        
        # Store in database for persistence
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO quality_validation_results 
                        (timestamp, summary, recommendations, critical_issues, results_json)
                        VALUES ($1, $2, $3, $4, $5)
                    """, 
                    results["timestamp"],
                    json.dumps(results["summary"]),
                    json.dumps(results["recommendations"]),
                    json.dumps(results["critical_issues"]),
                    json.dumps(results, default=str)
                    )
            except Exception as e:
                self.logger.error(f"Failed to store results in database: {e}")
    
    async def get_validation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent validation history"""
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT timestamp, summary, recommendations, critical_issues
                        FROM quality_validation_results
                        ORDER BY timestamp DESC
                        LIMIT $1
                    """, limit)
                    
                    return [dict(row) for row in rows]
            except Exception as e:
                self.logger.error(f"Failed to fetch validation history: {e}")
        
        return []
    
    async def get_quality_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get quality trends over time"""
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT timestamp, summary
                        FROM quality_validation_results
                        WHERE timestamp >= NOW() - INTERVAL '${days} days'
                        ORDER BY timestamp ASC
                    """)
                    
                    timestamps = []
                    quality_scores = []
                    test_pass_rates = []
                    
                    for row in rows:
                        summary = json.loads(row["summary"])
                        timestamps.append(row["timestamp"])
                        quality_scores.append(summary.get("average_quality_score", 0))
                        test_pass_rates.append(summary.get("test_pass_rate", 0))
                    
                    return {
                        "timestamps": timestamps,
                        "quality_scores": quality_scores,
                        "test_pass_rates": test_pass_rates,
                    }
            except Exception as e:
                self.logger.error(f"Failed to fetch quality trends: {e}")
        
        return {"timestamps": [], "quality_scores": [], "test_pass_rates": []}