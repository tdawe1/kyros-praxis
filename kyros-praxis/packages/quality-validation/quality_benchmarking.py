#!/usr/bin/env python3
"""
Quality Benchmarking and Comparison Tools
Implements benchmarking, baselines, and comparative analysis across roles and time periods
"""

import json
import logging
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import asyncpg

from .quality_metrics import (
    QualityAssessment, Role, QualityMetric
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkType(Enum):
    """Types of quality benchmarks"""
    BASELINE = "baseline"
    INDUSTRY_STANDARD = "industry_standard"
    HISTORICAL_AVERAGE = "historical_average"
    PEAK_PERFORMANCE = "peak_performance"
    CUSTOM = "custom"


class ComparisonMetric(Enum):
    """Metrics for comparison analysis"""
    ABSOLUTE_DIFFERENCE = "absolute_difference"
    PERCENTAGE_CHANGE = "percentage_change"
    Z_SCORE = "z_score"
    PERCENTILE_RANK = "percentile_rank"
    TREND_COEFFICIENT = "trend_coefficient"


@dataclass
class Benchmark:
    """Quality benchmark definition"""
    id: str
    name: str
    description: str
    type: BenchmarkType
    role: Role
    metric: QualityMetric
    target_value: float
    acceptable_range: Tuple[float, float]
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Result of benchmark comparison"""
    benchmark_id: str
    actual_value: float
    target_value: float
    difference: float
    percentage_change: float
    z_score: float
    percentile_rank: float
    is_within_range: bool
    assessment: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ComparisonReport:
    """Comprehensive comparison report"""
    id: str
    title: str
    description: str
    comparison_type: str
    baseline_period: Tuple[datetime, datetime]
    comparison_period: Tuple[datetime, datetime]
    results: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


class QualityBenchmarkEngine:
    """Quality benchmarking and comparison engine"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.database_pool: Optional[asyncpg.Pool] = None
        self.logger = logging.getLogger(__name__)
        self.benchmarks: Dict[str, Benchmark] = {}
        self.historical_data: Dict[str, List[Dict[str, Any]]] = {}
    
    async def initialize(self, database_url: str = None):
        """Initialize external connections"""
        if database_url:
            self.database_pool = await asyncpg.create_pool(database_url)
        
        # Load benchmarks
        await self._load_benchmarks()
        
        # Load historical data
        await self._load_historical_data()
    
    async def _load_benchmarks(self):
        """Load benchmarks from configuration and database"""
        # Load default benchmarks
        default_benchmarks = [
            Benchmark(
                id="architect_code_quality_baseline",
                name="Architect Code Quality Baseline",
                description="Industry standard for architecture quality",
                type=BenchmarkType.INDUSTRY_STANDARD,
                role=Role.ARCHITECT,
                metric=QualityMetric.ARCHITECTURE_ADHERENCE,
                target_value=85.0,
                acceptable_range=(80.0, 95.0),
                metadata={"source": "industry_survey_2024", "confidence": 0.9}
            ),
            Benchmark(
                id="implementer_test_coverage_baseline",
                name="Implementer Test Coverage Baseline",
                description="Minimum acceptable test coverage",
                type=BenchmarkType.BASELINE,
                role=Role.IMPLEMENTER,
                metric=QualityMetric.TEST_COVERAGE,
                target_value=80.0,
                acceptable_range=(75.0, 100.0),
                metadata={"source": "company_policy", "version": "1.0"}
            ),
            Benchmark(
                id="orchestrator_performance_baseline",
                name="Orchestrator Performance Baseline",
                description="Target response time and throughput",
                type=BenchmarkType.BASELINE,
                role=Role.ORCHESTRATOR,
                metric=QualityMetric.PERFORMANCE,
                target_value=90.0,
                acceptable_range=(85.0, 100.0),
                metadata={"source": "sla_requirements", "sla_target": "99.9%"}
            ),
            Benchmark(
                id="critic_security_baseline",
                name="Critic Security Baseline",
                description="Security compliance requirements",
                type=BenchmarkType.INDUSTRY_STANDARD,
                role=Role.CRITIC,
                metric=QualityMetric.SECURITY,
                target_value=95.0,
                acceptable_range=(90.0, 100.0),
                metadata={"source": "security_standard", "standard": "ISO_27001"}
            ),
            Benchmark(
                id="integrator_reliability_baseline",
                name="Integrator Reliability Baseline",
                description="Integration reliability targets",
                type=BenchmarkType.BASELINE,
                role=Role.INTEGRATOR,
                metric=QualityMetric.RELIABILITY,
                target_value=98.0,
                acceptable_range=(95.0, 100.0),
                metadata={"source": "reliability_target", "uptime_target": "99.9%"}
            ),
        ]
        
        for benchmark in default_benchmarks:
            self.benchmarks[benchmark.id] = benchmark
        
        # Load custom benchmarks from database
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT id, name, description, type, role, metric, target_value,
                               acceptable_min, acceptable_max, created_at, metadata
                        FROM quality_benchmarks
                        WHERE is_active = true
                    """)
                    
                    for row in rows:
                        benchmark = Benchmark(
                            id=row["id"],
                            name=row["name"],
                            description=row["description"],
                            type=BenchmarkType(row["type"]),
                            role=Role(row["role"]),
                            metric=QualityMetric(row["metric"]),
                            target_value=row["target_value"],
                            acceptable_range=(row["acceptable_min"], row["acceptable_max"]),
                            created_at=row["created_at"],
                            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                        )
                        self.benchmarks[benchmark.id] = benchmark
                
                self.logger.info(f"Loaded {len(self.benchmarks)} benchmarks")
            except Exception as e:
                self.logger.error(f"Failed to load benchmarks from database: {e}")
    
    async def _load_historical_data(self):
        """Load historical quality data for comparison"""
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    # Load quality assessment history
                    rows = await conn.fetch("""
                        SELECT timestamp, role, overall_score, overall_level, metric_results_json
                        FROM quality_assessments
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    """)
                    
                    for row in rows:
                        assessment_data = {
                            "timestamp": row["timestamp"],
                            "role": row["role"],
                            "overall_score": row["overall_score"],
                            "overall_level": row["overall_level"],
                            "metric_results": json.loads(row["metric_results_json"]) if row["metric_results_json"] else []
                        }
                        
                        role_key = row["role"]
                        if role_key not in self.historical_data:
                            self.historical_data[role_key] = []
                        
                        self.historical_data[role_key].append(assessment_data)
                
                self.logger.info(f"Loaded historical data for {len(self.historical_data)} roles")
            except Exception as e:
                self.logger.error(f"Failed to load historical data: {e}")
    
    async def compare_against_benchmark(
        self, 
        assessment: QualityAssessment, 
        benchmark_ids: List[str] = None
    ) -> List[BenchmarkResult]:
        """Compare quality assessment against benchmarks"""
        results = []
        
        # Get relevant benchmarks for this role
        relevant_benchmarks = [
            b for b in self.benchmarks.values() 
            if b.role == assessment.role and (benchmark_ids is None or b.id in benchmark_ids)
        ]
        
        # Get metric values from assessment
        metric_values = {}
        for metric_result in assessment.metric_results:
            metric_values[metric_result.metric] = metric_result.score
        
        # Compare each benchmark
        for benchmark in relevant_benchmarks:
            if benchmark.metric in metric_values:
                actual_value = metric_values[benchmark.metric]
                result = await self._calculate_benchmark_result(benchmark, actual_value)
                results.append(result)
        
        return results
    
    async def _calculate_benchmark_result(self, benchmark: Benchmark, actual_value: float) -> BenchmarkResult:
        """Calculate benchmark comparison result"""
        target_value = benchmark.target_value
        min_acceptable, max_acceptable = benchmark.acceptable_range
        
        # Calculate metrics
        difference = actual_value - target_value
        percentage_change = (difference / target_value) * 100 if target_value != 0 else 0
        
        # Calculate Z-score using historical data
        z_score = await self._calculate_z_score(benchmark.role, benchmark.metric, actual_value)
        
        # Calculate percentile rank
        percentile_rank = await self._calculate_percentile_rank(benchmark.role, benchmark.metric, actual_value)
        
        # Check if within acceptable range
        is_within_range = min_acceptable <= actual_value <= max_acceptable
        
        # Generate assessment
        if is_within_range:
            assessment = "MEETS_STANDARD"
        elif actual_value > max_acceptable:
            assessment = "EXCEEDS_STANDARD"
        else:
            assessment = "BELOW_STANDARD"
        
        return BenchmarkResult(
            benchmark_id=benchmark.id,
            actual_value=actual_value,
            target_value=target_value,
            difference=difference,
            percentage_change=percentage_change,
            z_score=z_score,
            percentile_rank=percentile_rank,
            is_within_range=is_within_range,
            assessment=assessment
        )
    
    async def _calculate_z_score(self, role: Role, metric: QualityMetric, value: float) -> float:
        """Calculate Z-score for a metric value"""
        historical_values = await self._get_historical_values(role, metric)
        
        if len(historical_values) < 2:
            return 0.0
        
        mean = statistics.mean(historical_values)
        std_dev = statistics.stdev(historical_values)
        
        if std_dev == 0:
            return 0.0
        
        return (value - mean) / std_dev
    
    async def _calculate_percentile_rank(self, role: Role, metric: QualityMetric, value: float) -> float:
        """Calculate percentile rank for a metric value"""
        historical_values = await self._get_historical_values(role, metric)
        
        if not historical_values:
            return 50.0  # Default to median
        
        # Count values less than or equal to current value
        values_less_or_equal = sum(1 for v in historical_values if v <= value)
        
        # Calculate percentile rank
        percentile = (values_less_or_equal / len(historical_values)) * 100
        
        return min(100.0, max(0.0, percentile))
    
    async def _get_historical_values(self, role: Role, metric: QualityMetric) -> List[float]:
        """Get historical values for a specific role and metric"""
        values = []
        
        role_key = role.value
        if role_key in self.historical_data:
            for assessment in self.historical_data[role_key]:
                for metric_result in assessment.get("metric_results", []):
                    if metric_result.get("metric") == metric.value:
                        values.append(metric_result.get("score", 0))
        
        return values
    
    async def create_comparison_report(
        self,
        title: str,
        description: str,
        baseline_start: datetime,
        baseline_end: datetime,
        comparison_start: datetime,
        comparison_end: datetime,
        roles: List[Role] = None
    ) -> ComparisonReport:
        """Create comprehensive comparison report"""
        roles = roles or list(Role)
        
        report = ComparisonReport(
            id=f"comparison_{int(time.time())}",
            title=title,
            description=description,
            comparison_type="period_comparison",
            baseline_period=(baseline_start, baseline_end),
            comparison_period=(comparison_start, comparison_end)
        )
        
        # Get data for both periods
        baseline_data = await self._get_period_data(baseline_start, baseline_end, roles)
        comparison_data = await self._get_period_data(comparison_start, comparison_end, roles)
        
        # Analyze comparison
        report.results = await self._analyze_comparison(baseline_data, comparison_data)
        
        # Generate summary
        report.summary = await self._generate_comparison_summary(baseline_data, comparison_data)
        
        # Generate recommendations
        report.recommendations = await self._generate_comparison_recommendations(report.results)
        
        return report
    
    async def _get_period_data(
        self, 
        start: datetime, 
        end: datetime, 
        roles: List[Role]
    ) -> Dict[str, Dict[str, Any]]:
        """Get quality data for a specific time period"""
        period_data = {}
        
        for role in roles:
            role_key = role.value
            if role_key in self.historical_data:
                # Filter data by time period
                role_data = [
                    assessment for assessment in self.historical_data[role_key]
                    if start <= assessment["timestamp"] <= end
                ]
                
                if role_data:
                    # Calculate statistics
                    scores = [assessment["overall_score"] for assessment in role_data]
                    
                    # Extract metric data
                    metric_data = {}
                    for assessment in role_data:
                        for metric_result in assessment.get("metric_results", []):
                            metric_name = metric_result.get("metric")
                            if metric_name not in metric_data:
                                metric_data[metric_name] = []
                            metric_data[metric_name].append(metric_result.get("score", 0))
                    
                    period_data[role_key] = {
                        "count": len(role_data),
                        "overall_scores": scores,
                        "avg_score": statistics.mean(scores) if scores else 0,
                        "min_score": min(scores) if scores else 0,
                        "max_score": max(scores) if scores else 0,
                        "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
                        "metric_data": metric_data
                    }
        
        return period_data
    
    async def _analyze_comparison(
        self, 
        baseline_data: Dict[str, Dict[str, Any]], 
        comparison_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze comparison between two periods"""
        results = {}
        
        # Compare each role
        all_roles = set(baseline_data.keys()) | set(comparison_data.keys())
        
        for role_key in all_roles:
            baseline = baseline_data.get(role_key, {})
            comparison = comparison_data.get(role_key, {})
            
            role_results = {
                "overall_change": await self._calculate_metric_change(
                    baseline.get("avg_score", 0),
                    comparison.get("avg_score", 0)
                ),
                "sample_size_change": {
                    "baseline": baseline.get("count", 0),
                    "comparison": comparison.get("count", 0),
                    "change": comparison.get("count", 0) - baseline.get("count", 0)
                },
                "metric_changes": {}
            }
            
            # Compare each metric
            baseline_metrics = baseline.get("metric_data", {})
            comparison_metrics = comparison.get("metric_data", {})
            
            all_metrics = set(baseline_metrics.keys()) | set(comparison_metrics.keys())
            
            for metric_name in all_metrics:
                baseline_values = baseline_metrics.get(metric_name, [])
                comparison_values = comparison_metrics.get(metric_name, [])
                
                baseline_avg = statistics.mean(baseline_values) if baseline_values else 0
                comparison_avg = statistics.mean(comparison_values) if comparison_values else 0
                
                role_results["metric_changes"][metric_name] = await self._calculate_metric_change(
                    baseline_avg, comparison_avg
                )
            
            results[role_key] = role_results
        
        return results
    
    async def _calculate_metric_change(self, baseline: float, comparison: float) -> Dict[str, Any]:
        """Calculate change between two metric values"""
        if baseline == 0:
            percentage_change = 0 if comparison == 0 else 100
        else:
            percentage_change = ((comparison - baseline) / baseline) * 100
        
        return {
            "baseline": baseline,
            "comparison": comparison,
            "absolute_change": comparison - baseline,
            "percentage_change": percentage_change,
            "direction": "improved" if comparison > baseline else "degraded" if comparison < baseline else "stable"
        }
    
    async def _generate_comparison_summary(
        self, 
        baseline_data: Dict[str, Dict[str, Any]], 
        comparison_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate summary of comparison results"""
        summary = {
            "overall_improvement": 0,
            "overall_degradation": 0,
            "role_counts": {
                "improved": 0,
                "degraded": 0,
                "stable": 0
            },
            "significant_changes": [],
            "key_insights": []
        }
        
        # Analyze role-level changes
        all_roles = set(baseline_data.keys()) | set(comparison_data.keys())
        
        for role_key in all_roles:
            baseline_avg = baseline_data.get(role_key, {}).get("avg_score", 0)
            comparison_avg = comparison_data.get(role_key, {}).get("avg_score", 0)
            
            if comparison_avg > baseline_avg + 5:  # Significant improvement
                summary["role_counts"]["improved"] += 1
                summary["overall_improvement"] += 1
                summary["significant_changes"].append({
                    "role": role_key,
                    "type": "improvement",
                    "magnitude": comparison_avg - baseline_avg
                })
            elif comparison_avg < baseline_avg - 5:  # Significant degradation
                summary["role_counts"]["degraded"] += 1
                summary["overall_degradation"] += 1
                summary["significant_changes"].append({
                    "role": role_key,
                    "type": "degradation",
                    "magnitude": baseline_avg - comparison_avg
                })
            else:
                summary["role_counts"]["stable"] += 1
        
        # Generate key insights
        if summary["overall_improvement"] > summary["overall_degradation"]:
            summary["key_insights"].append("Overall quality has improved between periods")
        elif summary["overall_degradation"] > summary["overall_improvement"]:
            summary["key_insights"].append("Overall quality has degraded between periods")
        else:
            summary["key_insights"].append("Quality remains relatively stable between periods")
        
        if summary["significant_changes"]:
            summary["key_insights"].append(f"Found {len(summary['significant_changes'])} significant changes")
        
        return summary
    
    async def _generate_comparison_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on comparison results"""
        recommendations = []
        
        # Analyze role-specific changes
        for role_key, role_results in results.items():
            overall_change = role_results.get("overall_change", {})
            
            if overall_change.get("direction") == "degraded":
                recommendations.append(
                    f"Investigate quality degradation in {role_key} role "
                    f"({overall_change.get('percentage_change', 0):.1f}% decrease)"
                )
            
            # Check metric-specific issues
            metric_changes = role_results.get("metric_changes", {})
            for metric_name, change in metric_changes.items():
                if change.get("direction") == "degraded" and abs(change.get("percentage_change", 0)) > 10:
                    recommendations.append(
                        f"Address significant degradation in {role_key} {metric_name} "
                        f"({change.get('percentage_change', 0):.1f}% decrease)"
                    )
        
        # Add general recommendations
        if not recommendations:
            recommendations.append("Quality trends are stable. Continue current practices.")
        else:
            recommendations.append("Review detailed metrics and implement improvement plans.")
        
        return recommendations
    
    async def generate_benchmark_report(self) -> Dict[str, Any]:
        """Generate comprehensive benchmark report"""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "benchmarks": {},
            "summary": {
                "total_benchmarks": len(self.benchmarks),
                "by_role": {},
                "by_type": {}
            },
            "recommendations": []
        }
        
        # Analyze benchmarks by role and type
        for benchmark in self.benchmarks.values():
            role_key = benchmark.role.value
            type_key = benchmark.type.value
            
            if role_key not in report["summary"]["by_role"]:
                report["summary"]["by_role"][role_key] = 0
            report["summary"]["by_role"][role_key] += 1
            
            if type_key not in report["summary"]["by_type"]:
                report["summary"]["by_type"][type_key] = 0
            report["summary"]["by_type"][type_key] += 1
            
            # Add benchmark details
            report["benchmarks"][benchmark.id] = {
                "name": benchmark.name,
                "role": role_key,
                "metric": benchmark.metric.value,
                "target_value": benchmark.target_value,
                "acceptable_range": benchmark.acceptable_range,
                "type": type_key,
                "created_at": benchmark.created_at.isoformat(),
                "metadata": benchmark.metadata
            }
        
        # Generate recommendations
        report["recommendations"] = [
            "Review and update benchmarks quarterly",
            "Consider adding custom benchmarks for project-specific metrics",
            "Monitor benchmark compliance regularly",
            "Use benchmark data to set quality improvement targets"
        ]
        
        return report
    
    async def get_trend_analysis(
        self, 
        role: Role, 
        metric: QualityMetric, 
        days: int = 30
    ) -> Dict[str, Any]:
        """Get trend analysis for a specific role and metric"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Get historical data for the period
        historical_values = []
        timestamps = []
        
        role_key = role.value
        if role_key in self.historical_data:
            for assessment in self.historical_data[role_key]:
                if start_time <= assessment["timestamp"] <= end_time:
                    for metric_result in assessment.get("metric_results", []):
                        if metric_result.get("metric") == metric.value:
                            historical_values.append(metric_result.get("score", 0))
                            timestamps.append(assessment["timestamp"])
        
        if len(historical_values) < 2:
            return {"error": "Insufficient data for trend analysis"}
        
        # Calculate trend metrics
        # Simple linear regression
        n = len(historical_values)
        x = list(range(n))  # Time indices
        y = historical_values
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Calculate correlation coefficient
        y_mean = sum_y / n
        ss_tot = sum((yi - y_mean) ** 2 for yi in y)
        ss_res = sum((yi - (slope * xi + (sum_y - slope * sum_x) / n)) ** 2 for xi, yi in zip(x, y))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Determine trend direction
        if abs(slope) < 0.1:
            trend_direction = "stable"
        elif slope > 0:
            trend_direction = "improving"
        else:
            trend_direction = "degrading"
        
        # Calculate volatility
        volatility = statistics.stdev(historical_values) if len(historical_values) > 1 else 0
        
        return {
            "role": role.value,
            "metric": metric.value,
            "period_days": days,
            "data_points": len(historical_values),
            "current_value": historical_values[-1] if historical_values else 0,
            "average_value": statistics.mean(historical_values),
            "min_value": min(historical_values),
            "max_value": max(historical_values),
            "trend_direction": trend_direction,
            "trend_slope": slope,
            "correlation_coefficient": r_squared ** 0.5,  # Pearson correlation
            "volatility": volatility,
            "recommendations": self._generate_trend_recommendations(trend_direction, volatility, r_squared)
        }
    
    def _generate_trend_recommendations(self, trend_direction: str, volatility: float, correlation: float) -> List[str]:
        """Generate recommendations based on trend analysis"""
        recommendations = []
        
        if trend_direction == "improving":
            if correlation > 0.7:
                recommendations.append("Strong positive trend detected. Continue current practices.")
            else:
                recommendations.append("Improving trend but correlation is weak. Monitor for consistency.")
        elif trend_direction == "degrading":
            recommendations.append("Quality is trending downward. Investigate causes and implement improvements.")
        else:
            recommendations.append("Quality is stable. Consider optimization opportunities.")
        
        if volatility > 15:
            recommendations.append("High volatility detected. Investigate causes of variation.")
        
        if correlation < 0.5:
            recommendations.append("Weak correlation suggests inconsistent patterns. Review measurement methodology.")
        
        return recommendations
    
    async def export_benchmarks(self, format: str = "json") -> str:
        """Export benchmarks in specified format"""
        benchmarks_data = []
        
        for benchmark in self.benchmarks.values():
            benchmark_data = {
                "id": benchmark.id,
                "name": benchmark.name,
                "description": benchmark.description,
                "type": benchmark.type.value,
                "role": benchmark.role.value,
                "metric": benchmark.metric.value,
                "target_value": benchmark.target_value,
                "acceptable_range": {
                    "min": benchmark.acceptable_range[0],
                    "max": benchmark.acceptable_range[1]
                },
                "created_at": benchmark.created_at.isoformat(),
                "metadata": benchmark.metadata
            }
            benchmarks_data.append(benchmark_data)
        
        if format.lower() == "json":
            return json.dumps(benchmarks_data, indent=2)
        elif format.lower() == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if benchmarks_data:
                writer = csv.DictWriter(output, fieldnames=benchmarks_data[0].keys())
                writer.writeheader()
                writer.writerows(benchmarks_data)
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def import_benchmarks(self, data: str, format: str = "json"):
        """Import benchmarks from data"""
        if format.lower() == "json":
            benchmarks_data = json.loads(data)
        elif format.lower() == "csv":
            import csv
            import io
            
            benchmarks_data = []
            reader = csv.DictReader(io.StringIO(data))
            for row in reader:
                # Convert string values back to appropriate types
                row["target_value"] = float(row["target_value"])
                row["acceptable_range"] = {
                    "min": float(row["acceptable_range"]["min"]),
                    "max": float(row["acceptable_range"]["max"])
                }
                benchmarks_data.append(row)
        else:
            raise ValueError(f"Unsupported import format: {format}")
        
        # Create benchmark objects
        for benchmark_data in benchmarks_data:
            benchmark = Benchmark(
                id=benchmark_data["id"],
                name=benchmark_data["name"],
                description=benchmark_data["description"],
                type=BenchmarkType(benchmark_data["type"]),
                role=Role(benchmark_data["role"]),
                metric=QualityMetric(benchmark_data["metric"]),
                target_value=benchmark_data["target_value"],
                acceptable_range=(
                    benchmark_data["acceptable_range"]["min"],
                    benchmark_data["acceptable_range"]["max"]
                ),
                metadata=benchmark_data.get("metadata", {})
            )
            
            self.benchmarks[benchmark.id] = benchmark
        
        # Store in database if available
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    for benchmark in self.benchmarks.values():
                        await conn.execute("""
                            INSERT INTO quality_benchmarks 
                            (id, name, description, type, role, metric, target_value,
                             acceptable_min, acceptable_max, created_at, metadata, is_active)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, true)
                            ON CONFLICT (id) DO UPDATE SET
                                name = EXCLUDED.name,
                                description = EXCLUDED.description,
                                type = EXCLUDED.type,
                                role = EXCLUDED.role,
                                metric = EXCLUDED.metric,
                                target_value = EXCLUDED.target_value,
                                acceptable_min = EXCLUDED.acceptable_min,
                                acceptable_max = EXCLUDED.acceptable_max,
                                metadata = EXCLUDED.metadata,
                                is_active = true
                        """, 
                        benchmark.id, benchmark.name, benchmark.description, benchmark.type.value,
                        benchmark.role.value, benchmark.metric.value, benchmark.target_value,
                        benchmark.acceptable_range[0], benchmark.acceptable_range[1],
                        benchmark.created_at, json.dumps(benchmark.metadata)
                        )
                
                self.logger.info(f"Imported {len(benchmarks_data)} benchmarks")
            except Exception as e:
                self.logger.error(f"Failed to store imported benchmarks in database: {e}")