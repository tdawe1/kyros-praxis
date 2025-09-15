#!/usr/bin/env python3
"""
Quality Validation System Main Integration
Brings together all quality validation components for the hybrid model system
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import aiofiles
import asyncpg
import redis.asyncio as redis

from .quality_metrics import (
    QualityAssessment, QualityMetricResult, 
    Role, QualityLevel, QualityMetric,
    CodeQualityEvaluator, ArchitectureQualityEvaluator,
    PerformanceQualityEvaluator, SecurityQualityEvaluator,
    IntegrationQualityEvaluator
)
from .automated_testing import QualityValidationEngine, TestResult, TestStatus, TestSuite
from .quality_monitoring import QualityMonitoringEngine, Alert, AlertSeverity
from .quality_benchmarking import QualityBenchmarkEngine, Benchmark, BenchmarkResult
from .role_protocols import QualityAssuranceManager, ProtocolExecution, ProtocolStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QualityValidationSystem:
    """Main quality validation system for hybrid model system"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.logger = logging.getLogger(__name__)
        
        # Initialize core components
        self.validation_engine = QualityValidationEngine(workspace_root)
        self.monitoring_engine = QualityMonitoringEngine(workspace_root)
        self.benchmark_engine = QualityBenchmarkEngine(workspace_root)
        self.assurance_manager = QualityAssuranceManager(workspace_root, self.validation_engine)
        
        # Configuration
        self.config: Dict[str, Any] = {}
        self.is_initialized = False
        
        # Database connections
        self.redis_client: Optional[redis.Redis] = None
        self.database_pool: Optional[asyncpg.Pool] = None
    
    async def initialize(self, config_path: Path = None):
        """Initialize the quality validation system"""
        if config_path:
            await self._load_config(config_path)
        
        # Initialize database connections
        redis_url = self.config.get("redis_url")
        database_url = self.config.get("database_url")
        
        await self.validation_engine.initialize(redis_url, database_url)
        await self.monitoring_engine.initialize(redis_url, database_url)
        await self.benchmark_engine.initialize(database_url)
        
        # Store connections for system use
        if redis_url:
            self.redis_client = redis.from_url(redis_url)
        
        if database_url:
            self.database_pool = await asyncpg.create_pool(database_url)
        
        # Initialize assurance protocols
        await self.assurance_manager.initialize_protocols()
        
        # Create database schema if needed
        await self._create_database_schema()
        
        self.is_initialized = True
        self.logger.info("Quality Validation System initialized successfully")
    
    async def _load_config(self, config_path: Path):
        """Load system configuration"""
        try:
            async with aiofiles.open(config_path) as f:
                content = await f.read()
                self.config = json.loads(content)
            
            self.logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            # Use default configuration
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default system configuration"""
        return {
            "redis_url": "redis://localhost:6379",
            "database_url": "postgresql://postgres:password@localhost:5432/quality_validation",
            "monitoring": {
                "check_interval": 300,
                "alert_cooldown": 600,
                "anomaly_threshold": 3.0
            },
            "validation": {
                "max_concurrent_tests": 10,
                "test_timeout": 300,
                "fail_fast": False
            },
            "benchmarking": {
                "historical_data_days": 90,
                "trend_analysis_window": 30,
                "percentile_calculation_samples": 100
            },
            "protocols": {
                "auto_start": True,
                "approval_required": True,
                "cleanup_days": 30
            }
        }
    
    async def _create_database_schema(self):
        """Create database schema if it doesn't exist"""
        if not self.database_pool:
            return
        
        try:
            async with self.database_pool.acquire() as conn:
                # Create tables
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS quality_assessments (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        role VARCHAR(50) NOT NULL,
                        overall_score FLOAT NOT NULL,
                        overall_level VARCHAR(20) NOT NULL,
                        metric_results_json JSONB,
                        recommendations JSONB,
                        critical_issues JSONB,
                        assessment_id VARCHAR(64) UNIQUE
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS quality_alerts (
                        id VARCHAR(128) PRIMARY KEY,
                        type VARCHAR(50) NOT NULL,
                        severity VARCHAR(20) NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        metric_name VARCHAR(100),
                        current_value FLOAT,
                        threshold_value FLOAT,
                        timestamp TIMESTAMP NOT NULL,
                        acknowledged BOOLEAN DEFAULT FALSE,
                        resolved BOOLEAN DEFAULT FALSE,
                        acknowledged_at TIMESTAMP,
                        resolved_at TIMESTAMP,
                        acknowledged_by VARCHAR(100),
                        resolved_by VARCHAR(100),
                        metadata JSONB,
                        tags JSONB
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS quality_benchmarks (
                        id VARCHAR(128) PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        type VARCHAR(50) NOT NULL,
                        role VARCHAR(50) NOT NULL,
                        metric VARCHAR(50) NOT NULL,
                        target_value FLOAT NOT NULL,
                        acceptable_min FLOAT NOT NULL,
                        acceptable_max FLOAT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        metadata JSONB,
                        is_active BOOLEAN DEFAULT TRUE
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS quality_validation_results (
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP NOT NULL,
                        summary JSONB NOT NULL,
                        recommendations JSONB,
                        critical_issues JSONB,
                        results_json JSONB NOT NULL
                    );
                """)
                
                await conn.execute("""
                    CREATE TABLE IF NOT EXISTS protocol_executions (
                        id VARCHAR(128) PRIMARY KEY,
                        protocol_id VARCHAR(128) NOT NULL,
                        role VARCHAR(50) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        current_phase VARCHAR(50) NOT NULL,
                        start_time TIMESTAMP NOT NULL,
                        end_time TIMESTAMP,
                        results_json JSONB,
                        gate_results_json JSONB,
                        artifacts JSONB,
                        approvers JSONB,
                        notes JSONB
                    );
                """)
                
                # Create indexes
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_assessments_timestamp ON quality_assessments(timestamp);")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_assessments_role ON quality_assessments(role);")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON quality_alerts(timestamp);")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_alerts_severity ON quality_alerts(severity);")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_validation_results_timestamp ON quality_validation_results(timestamp);")
                
                self.logger.info("Database schema created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create database schema: {e}")
    
    async def run_comprehensive_validation(
        self,
        roles: List[Role] = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Run comprehensive quality validation across all roles"""
        if not self.is_initialized:
            raise RuntimeError("Quality Validation System not initialized")
        
        roles = roles or list(Role)
        context = context or {}
        
        self.logger.info(f"Starting comprehensive quality validation for roles: {[r.value for r in roles]}")
        
        results = {
            "validation_id": f"validation_{int(time.time())}",
            "timestamp": datetime.utcnow().isoformat(),
            "roles_validated": [role.value for role in roles],
            "role_results": {},
            "system_summary": {},
            "recommendations": [],
            "critical_issues": [],
            "benchmarks": {},
            "alerts": []
        }
        
        # Run validation for each role
        for role in roles:
            try:
                role_result = await self._validate_role(role, context)
                results["role_results"][role.value] = role_result
                
                # Process results through monitoring engine
                if "assessment" in role_result:
                    await self.monitoring_engine.process_quality_assessment(role_result["assessment"])
                
            except Exception as e:
                self.logger.error(f"Failed to validate role {role.value}: {e}")
                results["role_results"][role.value] = {"error": str(e)}
        
        # Generate system summary
        results["system_summary"] = await self._generate_system_summary(results)
        
        # Collect recommendations and critical issues
        for role_result in results["role_results"].values():
            if "assessment" in role_result:
                assessment = role_result["assessment"]
                results["recommendations"].extend(assessment.recommendations)
                results["critical_issues"].extend(assessment.critical_issues)
        
        # Remove duplicates
        results["recommendations"] = list(set(results["recommendations"]))
        results["critical_issues"] = list(set(results["critical_issues"]))
        
        # Compare against benchmarks
        for role in roles:
            if role.value in results["role_results"] and "assessment" in results["role_results"][role.value]:
                assessment = results["role_results"][role.value]["assessment"]
                benchmark_results = await self.benchmark_engine.compare_against_benchmark(assessment)
                results["benchmarks"][role.value] = [
                    {
                        "benchmark_id": result.benchmark_id,
                        "assessment": result.assessment,
                        "difference": result.difference,
                        "percentage_change": result.percentage_change
                    }
                    for result in benchmark_results
                ]
        
        # Get current alerts
        results["alerts"] = await self.monitoring_engine.get_active_alerts()
        
        self.logger.info(f"Comprehensive validation completed with ID: {results['validation_id']}")
        
        return results
    
    async def _validate_role(self, role: Role, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate quality for a specific role"""
        # Create test suites for the role
        test_suites = await self._create_role_test_suites(role, context)
        
        # Run quality validation
        validation_results = await self.validation_engine.run_quality_validation(
            test_suites, [role], context
        )
        
        # Generate role assessment
        assessment = await self._generate_role_assessment(role, validation_results, context)
        
        # Start quality assurance protocol if configured
        protocol_execution = None
        if self.config.get("protocols", {}).get("auto_start", True):
            try:
                protocol_execution = await self.assurance_manager.start_protocol_execution(
                    role, context
                )
                
                # Execute protocol phases
                for phase in protocol_execution.current_phase, ProtocolPhase.VALIDATION:
                    phase_context = {**context, "validation_results": validation_results}
                    await self.assurance_manager.execute_phase(
                        protocol_execution.execution_id, phase, phase_context
                    )
                
                # Complete protocol execution
                await self.assurance_manager.complete_protocol_execution(
                    protocol_execution.execution_id, assessment
                )
            except Exception as e:
                self.logger.error(f"Failed to execute protocol for {role.value}: {e}")
        
        return {
            "role": role.value,
            "validation_results": validation_results,
            "assessment": assessment,
            "protocol_execution": protocol_execution.execution_id if protocol_execution else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _create_role_test_suites(self, role: Role, context: Dict[str, Any]) -> List[TestSuite]:
        """Create test suites for a specific role"""
        test_suites = []
        
        if role == Role.IMPLEMENTER:
            test_suites = [
                TestSuite(
                    name="unit_tests",
                    tests=["tests/unit/"],
                    timeout=300,
                    parallel=True,
                    tags={"unit", role.value}
                ),
                TestSuite(
                    name="code_quality",
                    tests=["lint", "static_analysis", "security_scan"],
                    timeout=180,
                    parallel=False,
                    tags={"quality", role.value}
                )
            ]
        elif role == Role.ARCHITECT:
            test_suites = [
                TestSuite(
                    name="architecture_validation",
                    tests=["tests/architecture/", "design_review"],
                    timeout=600,
                    parallel=False,
                    tags={"architecture", role.value}
                )
            ]
        elif role == Role.ORCHESTRATOR:
            test_suites = [
                TestSuite(
                    name="performance_tests",
                    tests=["tests/performance/", "load_tests"],
                    timeout=900,
                    parallel=False,
                    tags={"performance", role.value}
                )
            ]
        elif role == Role.CRITIC:
            test_suites = [
                TestSuite(
                    name="security_tests",
                    tests=["tests/security/", "vulnerability_scan"],
                    timeout=600,
                    parallel=False,
                    tags={"security", role.value}
                )
            ]
        elif role == Role.INTEGRATOR:
            test_suites = [
                TestSuite(
                    name="integration_tests",
                    tests=["tests/integration/", "e2e_tests"],
                    timeout=1200,
                    parallel=False,
                    tags={"integration", role.value}
                )
            ]
        
        return test_suites
    
    async def _generate_role_assessment(
        self, 
        role: Role, 
        validation_results: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> QualityAssessment:
        """Generate quality assessment for a role"""
        # Get appropriate evaluator
        evaluators = {
            Role.IMPLEMENTER: CodeQualityEvaluator(),
            Role.ARCHITECT: ArchitectureQualityEvaluator(),
            Role.ORCHESTRATOR: PerformanceQualityEvaluator(),
            Role.CRITIC: SecurityQualityEvaluator(),
            Role.INTEGRATOR: IntegrationQualityEvaluator()
        }
        
        evaluator = evaluators.get(role)
        if not evaluator:
            raise ValueError(f"No evaluator for role: {role.value}")
        
        # Prepare evaluation context
        evaluator_context = self._prepare_evaluator_context(role, validation_results, context)
        
        # Generate assessment
        assessment = await evaluator.evaluate(evaluator_context)
        
        # Store assessment in database
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO quality_assessments 
                        (timestamp, role, overall_score, overall_level, 
                         metric_results_json, recommendations, critical_issues, assessment_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """, 
                    assessment.timestamp,
                    assessment.role.value,
                    assessment.overall_score,
                    assessment.overall_level.value,
                    json.dumps([asdict(r) for r in assessment.metric_results]),
                    json.dumps(assessment.recommendations),
                    json.dumps(assessment.critical_issues),
                    assessment.assessment_id
                    )
            except Exception as e:
                self.logger.error(f"Failed to store assessment: {e}")
        
        return assessment
    
    def _prepare_evaluator_context(
        self, 
        role: Role, 
        validation_results: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare context for quality evaluator"""
        evaluator_context = context.copy()
        
        # Add validation results
        evaluator_context["validation_results"] = validation_results
        
        # Add test results summary
        test_results = validation_results.get("test_results", [])
        passed_tests = [r for r in test_results if r.status == TestStatus.PASSED]
        failed_tests = [r for r in test_results if r.status == TestStatus.FAILED]
        
        evaluator_context.update({
            "total_tests": len(test_results),
            "passed_tests": len(passed_tests),
            "failed_tests": len(failed_tests),
            "test_pass_rate": len(passed_tests) / max(len(test_results), 1) * 100
        })
        
        return evaluator_context
    
    async def _generate_system_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate system-wide summary"""
        role_results = results["role_results"]
        
        # Calculate overall metrics
        total_assessments = 0
        passing_assessments = 0
        total_score = 0
        quality_levels = {level.value: 0 for level in QualityLevel}
        
        for role_result in role_results.values():
            if "assessment" in role_result:
                assessment = role_result["assessment"]
                total_assessments += 1
                total_score += assessment.overall_score
                quality_levels[assessment.overall_level.value] += 1
                
                if assessment.overall_level in [QualityLevel.GOOD, QualityLevel.EXCELLENT]:
                    passing_assessments += 1
        
        # Generate summary
        summary = {
            "total_roles_validated": len(role_results),
            "total_assessments": total_assessments,
            "passing_assessments": passing_assessments,
            "pass_rate": (passing_assessments / max(total_assessments, 1)) * 100,
            "average_quality_score": total_score / max(total_assessments, 1),
            "quality_level_distribution": quality_levels,
            "critical_issues_count": len(results["critical_issues"]),
            "active_alerts_count": len(results["alerts"])
        }
        
        return summary
    
    async def start_monitoring(self):
        """Start continuous quality monitoring"""
        if not self.is_initialized:
            raise RuntimeError("Quality Validation System not initialized")
        
        self.logger.info("Starting continuous quality monitoring")
        
        # Get monitoring configuration
        monitoring_config = self.config.get("monitoring", {})
        check_interval = monitoring_config.get("check_interval", 300)
        
        # Start monitoring loop
        asyncio.create_task(
            self.monitoring_engine.start_monitoring(
                self.validation_engine, 
                check_interval
            )
        )
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for quality dashboard"""
        if not self.is_initialized:
            raise RuntimeError("Quality Validation System not initialized")
        
        # Get monitoring dashboard data
        monitoring_data = await self.monitoring_engine.get_monitoring_dashboard_data()
        
        # Get protocol summary
        protocol_summary = await self.assurance_manager.get_protocol_summary()
        
        # Get recent validation history
        recent_history = await self.validation_engine.get_validation_history(limit=10)
        
        # Get benchmark report
        benchmark_report = await self.benchmark_engine.generate_benchmark_report()
        
        # Get active protocol executions
        active_executions = await self.assurance_manager.get_active_executions()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "monitoring": monitoring_data,
            "protocols": protocol_summary,
            "recent_validations": recent_history,
            "benchmarks": benchmark_report,
            "active_executions": [
                {
                    "execution_id": exec.execution_id,
                    "role": exec.protocol_id.split('_')[0],
                    "status": exec.status.value,
                    "current_phase": exec.current_phase.value,
                    "start_time": exec.start_time.isoformat()
                }
                for exec in active_executions
            ],
            "system_status": {
                "initialized": self.is_initialized,
                "redis_connected": self.redis_client is not None,
                "database_connected": self.database_pool is not None
            }
        }
    
    async def generate_quality_report(
        self, 
        start_date: datetime = None, 
        end_date: datetime = None,
        roles: List[Role] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        if not self.is_initialized:
            raise RuntimeError("Quality Validation System not initialized")
        
        end_date = end_date or datetime.utcnow()
        start_date = start_date or (end_date - timedelta(days=30))
        roles = roles or list(Role)
        
        report = {
            "report_id": f"quality_report_{int(time.time())}",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "roles": [role.value for role in roles],
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": {},
            "role_reports": {},
            "trend_analysis": {},
            "benchmark_comparison": {},
            "recommendations": [],
            "appendix": {}
        }
        
        # Generate role-specific reports
        for role in roles:
            role_report = await self._generate_role_report(role, start_date, end_date)
            report["role_reports"][role.value] = role_report
        
        # Generate executive summary
        report["executive_summary"] = await self._generate_executive_summary(report)
        
        # Generate trend analysis
        for role in roles:
            if role.value in report["role_reports"]:
                for metric in QualityMetric:
                    trend_analysis = await self.benchmark_engine.get_trend_analysis(
                        role, metric, days=30
                    )
                    if "error" not in trend_analysis:
                        if role.value not in report["trend_analysis"]:
                            report["trend_analysis"][role.value] = {}
                        report["trend_analysis"][role.value][metric.value] = trend_analysis
        
        # Generate benchmark comparison
        for role in roles:
            if role.value in report["role_reports"] and "current_assessment" in report["role_reports"][role.value]:
                current_assessment = report["role_reports"][role.value]["current_assessment"]
                benchmark_results = await self.benchmark_engine.compare_against_benchmark(current_assessment)
                report["benchmark_comparison"][role.value] = [
                    {
                        "benchmark_id": result.benchmark_id,
                        "target": result.target_value,
                        "actual": result.actual_value,
                        "difference": result.difference,
                        "assessment": result.assessment
                    }
                    for result in benchmark_results
                ]
        
        # Collect recommendations
        for role_report in report["role_reports"].values():
            report["recommendations"].extend(role_report.get("recommendations", []))
        
        # Remove duplicates
        report["recommendations"] = list(set(report["recommendations"]))
        
        return report
    
    async def _generate_role_report(
        self, 
        role: Role, 
        start_date: datetime, 
        end_date: DateTime
    ) -> Dict[str, Any]:
        """Generate role-specific quality report"""
        # Get historical data for the period
        historical_data = []
        
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT timestamp, overall_score, overall_level, recommendations, critical_issues
                        FROM quality_assessments
                        WHERE role = $1 AND timestamp BETWEEN $2 AND $3
                        ORDER BY timestamp ASC
                    """, role.value, start_date, end_date)
                    
                    for row in rows:
                        historical_data.append({
                            "timestamp": row["timestamp"],
                            "overall_score": row["overall_score"],
                            "overall_level": row["overall_level"],
                            "recommendations": json.loads(row["recommendations"]) if row["recommendations"] else [],
                            "critical_issues": json.loads(row["critical_issues"]) if row["critical_issues"] else []
                        })
            except Exception as e:
                self.logger.error(f"Failed to get historical data for {role.value}: {e}")
        
        # Calculate statistics
        scores = [data["overall_score"] for data in historical_data]
        level_distribution = {level.value: 0 for level in QualityLevel}
        
        for data in historical_data:
            level_distribution[data["overall_level"]] += 1
        
        # Get current assessment (most recent)
        current_assessment = None
        if historical_data:
            latest_data = historical_data[-1]
            
            # Reconstruct assessment (simplified)
            current_assessment = QualityAssessment(
                role=role,
                overall_score=latest_data["overall_score"],
                overall_level=QualityLevel(latest_data["overall_level"]),
                metric_results=[],  # Simplified for report
                recommendations=latest_data["recommendations"],
                critical_issues=latest_data["critical_issues"],
                timestamp=latest_data["timestamp"],
                assessment_id=f"report_{role.value}_{int(time.time())}"
            )
        
        return {
            "role": role.value,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "data_points": len(historical_data),
            "statistics": {
                "average_score": statistics.mean(scores) if scores else 0,
                "min_score": min(scores) if scores else 0,
                "max_score": max(scores) if scores else 0,
                "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0
            },
            "level_distribution": level_distribution,
            "current_assessment": current_assessment,
            "trend": "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable",
            "recommendations": []
        }
    
    async def _generate_executive_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary for quality report"""
        role_reports = report["role_reports"]
        
        # Calculate overall metrics
        total_score = 0
        total_assessments = 0
        passing_roles = 0
        
        for role_report in role_reports.values():
            if role_report.get("statistics"):
                stats = role_report["statistics"]
                total_score += stats["average_score"]
                total_assessments += 1
                
                if stats["average_score"] >= 80:
                    passing_roles += 1
        
        return {
            "overall_quality_score": total_score / max(total_assessments, 1),
            "roles_evaluated": len(role_reports),
            "roles_meeting_standards": passing_roles,
            "key_insights": [
                f"Overall quality score: {total_score / max(total_assessments, 1):.1f}%",
                f"{passing_roles} out of {len(role_reports)} roles meeting quality standards"
            ],
            "critical_findings": len([issue for role_report in role_reports.values() 
                                   for issue in role_report.get("current_assessment", {}).get("critical_issues", [])]),
            "recommendations_count": len(report["recommendations"])
        }
    
    async def cleanup_old_data(self, days: int = 90):
        """Clean up old quality data"""
        if not self.is_initialized:
            return
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    # Clean up old assessments
                    result = await conn.execute("""
                        DELETE FROM quality_assessments
                        WHERE timestamp < $1
                    """, cutoff_date)
                    
                    # Clean up old alerts
                    await conn.execute("""
                        DELETE FROM quality_alerts
                        WHERE timestamp < $1 AND resolved = true
                    """, cutoff_date)
                    
                    # Clean up old validation results
                    await conn.execute("""
                        DELETE FROM quality_validation_results
                        WHERE timestamp < $1
                    """, cutoff_date)
                    
                    # Clean up old protocol executions
                    await conn.execute("""
                        DELETE FROM protocol_executions
                        WHERE end_time < $1
                    """, cutoff_date)
                
                self.logger.info(f"Cleaned up data older than {days} days")
            except Exception as e:
                self.logger.error(f"Failed to clean up old data: {e}")
        
        # Clean up protocol executions
        cleaned_count = self.assurance_manager.cleanup_completed_executions(days)
        if cleaned_count > 0:
            self.logger.info(f"Cleaned up {cleaned_count} old protocol executions")
    
    async def shutdown(self):
        """Shutdown the quality validation system"""
        self.logger.info("Shutting down Quality Validation System")
        
        # Close database connections
        if self.database_pool:
            await self.database_pool.close()
        
        if self.redis_client:
            await self.redis_client.close()
        
        self.logger.info("Quality Validation System shutdown complete")