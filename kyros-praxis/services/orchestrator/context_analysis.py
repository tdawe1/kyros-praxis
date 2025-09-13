"""
Context Analysis for Critical Decisions

This module provides deep analysis of task context, files, and requirements
to make intelligent escalation decisions. It analyzes code complexity,
dependencies, business impact, and risk factors.

ANALYSIS DIMENSIONS:
1. Code Complexity Metrics - Cyclomatic complexity, coupling, cohesion
2. Business Impact Analysis - Revenue, compliance, customer impact
3. Risk Assessment - Security, performance, reliability risks
4. Dependency Analysis - Cross-module, cross-service dependencies
5. Quality Requirements - Testing, documentation, maintainability
"""

import ast
import logging
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class ComplexityLevel(Enum):
    """Complexity levels for code analysis"""
    
    SIMPLE = "simple"          # Straightforward, single responsibility
    MODERATE = "moderate"      # Some complexity, multiple components
    COMPLEX = "complex"        # Highly complex, many interactions
    CRITICAL = "critical"      # Extremely complex, high risk


class BusinessImpact(Enum):
    """Business impact levels"""
    
    LOW = "low"               # Minimal business impact
    MEDIUM = "medium"         # Noticeable impact on operations
    HIGH = "high"             # Significant business impact
    CRITICAL = "critical"     # Mission-critical impact


class RiskLevel(Enum):
    """Risk levels for different factors"""
    
    LOW = "low"               # Low risk, minimal consequences
    MEDIUM = "medium"         # Moderate risk, manageable consequences
    HIGH = "high"             # High risk, significant consequences
    CRITICAL = "critical"     # Critical risk, severe consequences


@dataclass
class ComplexityMetrics:
    """Code complexity metrics"""
    
    cyclomatic_complexity: int
    coupling_score: float
    cohesion_score: float
    lines_of_code: int
    function_count: int
    class_count: int
    dependency_count: int
    complexity_level: ComplexityLevel


@dataclass
class BusinessImpactMetrics:
    """Business impact assessment"""
    
    revenue_impact: BusinessImpact
    customer_impact: BusinessImpact
    compliance_impact: BusinessImpact
    operational_impact: BusinessImpact
    strategic_importance: BusinessImpact
    overall_impact: BusinessImpact


@dataclass
class RiskMetrics:
    """Risk assessment metrics"""
    
    security_risk: RiskLevel
    performance_risk: RiskLevel
    reliability_risk: RiskLevel
    maintainability_risk: RiskLevel
    compliance_risk: RiskLevel
    overall_risk: RiskLevel


@dataclass
class DependencyAnalysis:
    """Dependency analysis results"""
    
    internal_dependencies: List[str]
    external_dependencies: List[str]
    cross_service_dependencies: List[str]
    circular_dependencies: List[Tuple[str, str]]
    critical_dependencies: List[str]
    dependency_depth: int
    fan_out: int
    fan_in: int


@dataclass
class QualityRequirements:
    """Quality and maintainability requirements"""
    
    testing_complexity: ComplexityLevel
    documentation_needs: BusinessImpact
    maintainability_score: float
    code_coverage_requirement: float
    review_complexity: ComplexityLevel


@dataclass
class ContextAnalysisResult:
    """Complete context analysis result"""
    
    overall_complexity: ComplexityLevel
    business_impact: BusinessImpactMetrics
    risk_assessment: RiskMetrics
    dependencies: DependencyAnalysis
    quality_requirements: QualityRequirements
    escalation_recommendation: str
    confidence_score: float
    key_factors: List[str]


class ContextAnalyzer:
    """
    Analyzes task context to determine complexity and business impact
    
    This class provides deep analysis capabilities for making informed
    escalation decisions.
    """
    
    def __init__(self):
        # Complexity thresholds
        self.complexity_thresholds = {
            "cyclomatic": {
                ComplexityLevel.SIMPLE: 10,
                ComplexityLevel.MODERATE: 20,
                ComplexityLevel.COMPLEX: 40,
                ComplexityLevel.CRITICAL: float('inf')
            },
            "coupling": {
                ComplexityLevel.SIMPLE: 0.2,
                ComplexityLevel.MODERATE: 0.4,
                ComplexityLevel.COMPLEX: 0.6,
                ComplexityLevel.CRITICAL: float('inf')
            },
            "functions": {
                ComplexityLevel.SIMPLE: 5,
                ComplexityLevel.MODERATE: 15,
                ComplexityLevel.COMPLEX: 30,
                ComplexityLevel.CRITICAL: float('inf')
            }
        }
        
        # Business impact patterns
        self.business_impact_patterns = {
            BusinessImpact.CRITICAL: [
                "revenue", "billing", "payment", "transaction", "checkout",
                "authentication", "authorization", "security", "compliance",
                "gdpr", "hipaa", "pci", "audit", "legal", "contract"
            ],
            BusinessImpact.HIGH: [
                "api", "integration", "migration", "database", "schema",
                "performance", "scalability", "availability", "reliability"
            ],
            BusinessImpact.MEDIUM: [
                "ui", "ux", "feature", "enhancement", "improvement",
                "refactor", "cleanup", "documentation"
            ]
        }
        
        # Risk patterns
        self.risk_patterns = {
            RiskLevel.CRITICAL: [
                "security", "vulnerability", "exploit", "breach", "attack",
                "data_loss", "corruption", "downtime", "outage", "critical"
            ],
            RiskLevel.HIGH: [
                "performance", "latency", "throughput", "memory", "cpu",
                "race_condition", "deadlock", "timeout", "failure"
            ],
            RiskLevel.MEDIUM: [
                "bug", "error", "exception", "warning", "deprecation",
                "maintainability", "readability", "technical_debt"
            ]
        }
    
    def analyze_task_context(
        self,
        task_description: str,
        files_to_modify: List[str],
        file_contents: Optional[Dict[str, str]] = None,
        task_type: str = "implementation"
    ) -> ContextAnalysisResult:
        """
        Perform comprehensive context analysis
        
        Args:
            task_description: Description of the task
            files_to_modify: List of files to be modified
            file_contents: Optional mapping of file paths to contents
            task_type: Type of task being performed
            
        Returns:
            ContextAnalysisResult with comprehensive analysis
        """
        # Analyze code complexity
        complexity_metrics = self._analyze_code_complexity(files_to_modify, file_contents)
        
        # Analyze business impact
        business_impact = self._analyze_business_impact(task_description, files_to_modify)
        
        # Assess risks
        risk_metrics = self._assess_risks(task_description, files_to_modify, file_contents)
        
        # Analyze dependencies
        dependencies = self._analyze_dependencies(files_to_modify, file_contents)
        
        # Determine quality requirements
        quality_requirements = self._determine_quality_requirements(task_description, complexity_metrics)
        
        # Make escalation recommendation
        escalation_recommendation, confidence_score = self._make_recommendation(
            complexity_metrics, business_impact, risk_metrics, dependencies, quality_requirements
        )
        
        # Identify key factors
        key_factors = self._identify_key_factors(
            complexity_metrics, business_impact, risk_metrics, dependencies
        )
        
        return ContextAnalysisResult(
            overall_complexity=complexity_metrics.complexity_level,
            business_impact=business_impact,
            risk_assessment=risk_metrics,
            dependencies=dependencies,
            quality_requirements=quality_requirements,
            escalation_recommendation=escalation_recommendation,
            confidence_score=confidence_score,
            key_factors=key_factors
        )
    
    def _analyze_code_complexity(
        self,
        files_to_modify: List[str],
        file_contents: Optional[Dict[str, str]] = None
    ) -> ComplexityMetrics:
        """Analyze code complexity metrics"""
        
        total_cyclomatic = 0
        total_lines = 0
        total_functions = 0
        total_classes = 0
        all_dependencies = set()
        
        file_contents = file_contents or {}
        
        for file_path in files_to_modify:
            if file_path.endswith('.py'):
                content = file_contents.get(file_path, "")
                if content:
                    try:
                        # Parse Python code
                        tree = ast.parse(content)
                        
                        # Count functions and classes
                        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
                        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
                        
                        total_functions += len(functions)
                        total_classes += len(classes)
                        total_lines += len(content.splitlines())
                        
                        # Estimate cyclomatic complexity
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                                total_cyclomatic += 1
                        
                        # Extract dependencies
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    all_dependencies.add(alias.name)
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    all_dependencies.add(node.module)
                    
                    except SyntaxError:
                        logger.warning(f"Could not parse {file_path}")
                        continue
        
        # Calculate coupling and cohesion (simplified estimates)
        coupling_score = min(len(all_dependencies) / max(len(files_to_modify), 1), 1.0)
        cohesion_score = 1.0 - coupling_score  # Inverse relationship as simplification
        
        # Determine complexity level
        complexity_level = self._determine_complexity_level(
            cyclomatic_complexity=total_cyclomatic,
            coupling_score=coupling_score,
            function_count=total_functions
        )
        
        return ComplexityMetrics(
            cyclomatic_complexity=total_cyclomatic,
            coupling_score=coupling_score,
            cohesion_score=cohesion_score,
            lines_of_code=total_lines,
            function_count=total_functions,
            class_count=total_classes,
            dependency_count=len(all_dependencies),
            complexity_level=complexity_level
        )
    
    def _determine_complexity_level(
        self,
        cyclomatic_complexity: int,
        coupling_score: float,
        function_count: int
    ) -> ComplexityLevel:
        """Determine overall complexity level"""
        
        # Score each metric
        cyclomatic_score = 0
        for level, threshold in self.complexity_thresholds["cyclomatic"].items():
            if cyclomatic_complexity <= threshold:
                cyclomatic_score = list(ComplexityLevel).index(level)
                break
        
        coupling_score_level = ComplexityLevel.SIMPLE
        for level, threshold in self.complexity_thresholds["coupling"].items():
            if coupling_score <= threshold:
                coupling_score_level = level
                break
        
        function_score = 0
        for level, threshold in self.complexity_thresholds["functions"].items():
            if function_count <= threshold:
                function_score = list(ComplexityLevel).index(level)
                break
        
        # Average the scores
        avg_score = (cyclomatic_score + list(ComplexityLevel).index(coupling_score_level) + function_score) / 3
        
        # Convert back to ComplexityLevel
        if avg_score <= 1:
            return ComplexityLevel.SIMPLE
        elif avg_score <= 2:
            return ComplexityLevel.MODERATE
        elif avg_score <= 3:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.CRITICAL
    
    def _analyze_business_impact(
        self,
        task_description: str,
        files_to_modify: List[str]
    ) -> BusinessImpactMetrics:
        """Analyze business impact of the task"""
        
        desc_lower = task_description.lower()
        
        # Analyze each impact dimension
        revenue_impact = self._assess_business_dimension(desc_lower, files_to_modify, BusinessImpact.CRITICAL)
        customer_impact = self._assess_business_dimension(desc_lower, files_to_modify, BusinessImpact.HIGH)
        compliance_impact = self._assess_business_dimension(desc_lower, files_to_modify, BusinessImpact.CRITICAL)
        operational_impact = self._assess_business_dimension(desc_lower, files_to_modify, BusinessImpact.MEDIUM)
        strategic_importance = self._assess_business_dimension(desc_lower, files_to_modify, BusinessImpact.MEDIUM)
        
        # Calculate overall impact
        impact_scores = [
            list(BusinessImpact).index(revenue_impact),
            list(BusinessImpact).index(customer_impact),
            list(BusinessImpact).index(compliance_impact),
            list(BusinessImpact).index(operational_impact),
            list(BusinessImpact).index(strategic_importance)
        ]
        
        avg_score = sum(impact_scores) / len(impact_scores)
        overall_impact = list(BusinessImpact)[min(int(avg_score), len(BusinessImpact) - 1)]
        
        return BusinessImpactMetrics(
            revenue_impact=revenue_impact,
            customer_impact=customer_impact,
            compliance_impact=compliance_impact,
            operational_impact=operational_impact,
            strategic_importance=strategic_importance,
            overall_impact=overall_impact
        )
    
    def _assess_business_dimension(
        self,
        task_description: str,
        files_to_modify: List[str],
        default_level: BusinessImpact
    ) -> BusinessImpact:
        """Assess a specific business impact dimension"""
        
        # Check for critical impact patterns first
        for impact_level in [BusinessImpact.CRITICAL, BusinessImpact.HIGH, BusinessImpact.MEDIUM]:
            patterns = self.business_impact_patterns.get(impact_level, [])
            matches = [pattern for pattern in patterns if pattern in task_description]
            
            if matches:
                return impact_level
        
        # Check file paths for impact indicators
        for file_path in files_to_modify:
            file_lower = file_path.lower()
            for impact_level, patterns in self.business_impact_patterns.items():
                if any(pattern in file_lower for pattern in patterns):
                    return impact_level
        
        return default_level
    
    def _assess_risks(
        self,
        task_description: str,
        files_to_modify: List[str],
        file_contents: Optional[Dict[str, str]] = None
    ) -> RiskMetrics:
        """Assess various risk factors"""
        
        desc_lower = task_description.lower()
        
        # Assess each risk dimension
        security_risk = self._assess_risk_dimension(desc_lower, files_to_modify, RiskLevel.LOW)
        performance_risk = self._assess_risk_dimension(desc_lower, files_to_modify, RiskLevel.LOW)
        reliability_risk = self._assess_risk_dimension(desc_lower, files_to_modify, RiskLevel.LOW)
        maintainability_risk = self._assess_risk_dimension(desc_lower, files_to_modify, RiskLevel.MEDIUM)
        compliance_risk = self._assess_risk_dimension(desc_lower, files_to_modify, RiskLevel.LOW)
        
        # Calculate overall risk
        risk_scores = [
            list(RiskLevel).index(security_risk),
            list(RiskLevel).index(performance_risk),
            list(RiskLevel).index(reliability_risk),
            list(RiskLevel).index(maintainability_risk),
            list(RiskLevel).index(compliance_risk)
        ]
        
        avg_score = sum(risk_scores) / len(risk_scores)
        overall_risk = list(RiskLevel)[min(int(avg_score), len(RiskLevel) - 1)]
        
        return RiskMetrics(
            security_risk=security_risk,
            performance_risk=performance_risk,
            reliability_risk=reliability_risk,
            maintainability_risk=maintainability_risk,
            compliance_risk=compliance_risk,
            overall_risk=overall_risk
        )
    
    def _assess_risk_dimension(
        self,
        task_description: str,
        files_to_modify: List[str],
        default_level: RiskLevel
    ) -> RiskLevel:
        """Assess a specific risk dimension"""
        
        # Check for critical risk patterns first
        for risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH, RiskLevel.MEDIUM]:
            patterns = self.risk_patterns.get(risk_level, [])
            matches = [pattern for pattern in patterns if pattern in task_description]
            
            if matches:
                return risk_level
        
        # Check file paths for risk indicators
        for file_path in files_to_modify:
            file_lower = file_path.lower()
            for risk_level, patterns in self.risk_patterns.items():
                if any(pattern in file_lower for pattern in patterns):
                    return risk_level
        
        return default_level
    
    def _analyze_dependencies(
        self,
        files_to_modify: List[str],
        file_contents: Optional[Dict[str, str]] = None
    ) -> DependencyAnalysis:
        """Analyze code dependencies"""
        
        internal_deps = set()
        external_deps = set()
        cross_service_deps = set()
        
        file_contents = file_contents or {}
        
        for file_path in files_to_modify:
            if file_path.endswith('.py'):
                content = file_contents.get(file_path, "")
                if content:
                    try:
                        tree = ast.parse(content)
                        
                        # Extract imports
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    if alias.name.startswith(('.', '..')):
                                        # Relative import - internal dependency
                                        internal_deps.add(alias.name)
                                    else:
                                        # Check if it's a known external package
                                        if self._is_external_package(alias.name):
                                            external_deps.add(alias.name)
                                        else:
                                            internal_deps.add(alias.name)
                            
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    if node.module.startswith(('.', '..')):
                                        internal_deps.add(node.module)
                                    else:
                                        if self._is_external_package(node.module):
                                            external_deps.add(node.module)
                                        else:
                                            internal_deps.add(node.module)
                    
                    except SyntaxError:
                        logger.warning(f"Could not parse {file_path}")
                        continue
        
        # Check for cross-service dependencies
        for file_path in files_to_modify:
            if "services/" in file_path:
                for dep in internal_deps:
                    if "services/" in dep:
                        cross_service_deps.add(dep)
        
        # Simplified dependency analysis (in real implementation, would need full project graph)
        return DependencyAnalysis(
            internal_dependencies=list(internal_deps),
            external_dependencies=list(external_deps),
            cross_service_dependencies=list(cross_service_deps),
            circular_dependencies=[],  # Would need full analysis
            critical_dependencies=list(cross_service_deps),  # Cross-service deps are critical
            dependency_depth=1,  # Simplified
            fan_out=len(internal_deps) + len(external_deps),
            fan_in=0  # Would need reverse dependency analysis
        )
    
    def _is_external_package(self, module_name: str) -> bool:
        """Check if a module is an external package"""
        # Simplified check - in real implementation would use package registry
        external_indicators = [
            'os', 'sys', 'json', 'requests', 'numpy', 'pandas', 'django', 'flask',
            'fastapi', 'sqlalchemy', 'pytest', 'uvicorn', 'pydantic', 'asyncio',
            'aiohttp', 'httpx', 'redis', 'psycopg2', 'boto3', 'tensorflow', 'torch'
        ]
        return any(indicator in module_name.lower() for indicator in external_indicators)
    
    def _determine_quality_requirements(
        self,
        task_description: str,
        complexity_metrics: ComplexityMetrics
    ) -> QualityRequirements:
        """Determine quality and testing requirements"""
        
        desc_lower = task_description.lower()
        
        # Testing complexity based on task description and complexity
        if any(keyword in desc_lower for keyword in ["test", "spec", "mock", "integration", "e2e"]):
            testing_complexity = ComplexityLevel.COMPLEX
        elif complexity_metrics.complexity_level in [ComplexityLevel.COMPLEX, ComplexityLevel.CRITICAL]:
            testing_complexity = ComplexityLevel.COMPLEX
        elif complexity_metrics.complexity_level == ComplexityLevel.MODERATE:
            testing_complexity = ComplexityLevel.MODERATE
        else:
            testing_complexity = ComplexityLevel.SIMPLE
        
        # Documentation needs
        if any(keyword in desc_lower for keyword in ["document", "docstring", "readme", "guide"]):
            documentation_needs = BusinessImpact.HIGH
        else:
            documentation_needs = BusinessImpact.MEDIUM
        
        # Maintainability score (inverse of complexity)
        maintainability_score = 1.0 - (list(ComplexityLevel).index(complexity_metrics.complexity_level) / 3)
        
        # Code coverage requirement
        if complexity_metrics.complexity_level == ComplexityLevel.CRITICAL:
            coverage_requirement = 0.9
        elif complexity_metrics.complexity_level == ComplexityLevel.COMPLEX:
            coverage_requirement = 0.8
        else:
            coverage_requirement = 0.7
        
        # Review complexity
        review_complexity = complexity_metrics.complexity_level
        
        return QualityRequirements(
            testing_complexity=testing_complexity,
            documentation_needs=documentation_needs,
            maintainability_score=maintainability_score,
            code_coverage_requirement=coverage_requirement,
            review_complexity=review_complexity
        )
    
    def _make_recommendation(
        self,
        complexity_metrics: ComplexityMetrics,
        business_impact: BusinessImpactMetrics,
        risk_metrics: RiskMetrics,
        dependencies: DependencyAnalysis,
        quality_requirements: QualityRequirements
    ) -> Tuple[str, float]:
        """Make escalation recommendation based on analysis"""
        
        escalation_factors = []
        confidence_score = 0.5
        
        # Critical complexity
        if complexity_metrics.complexity_level == ComplexityLevel.CRITICAL:
            escalation_factors.append("Critical code complexity detected")
            confidence_score += 0.3
        
        # High business impact
        if business_impact.overall_impact in [BusinessImpact.HIGH, BusinessImpact.CRITICAL]:
            escalation_factors.append("High business impact")
            confidence_score += 0.2
        
        # Critical or high risk
        if risk_metrics.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            escalation_factors.append("Significant risk factors")
            confidence_score += 0.25
        
        # Cross-service dependencies
        if dependencies.cross_service_dependencies:
            escalation_factors.append("Cross-service dependencies")
            confidence_score += 0.15
        
        # High testing requirements
        if quality_requirements.testing_complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.CRITICAL]:
            escalation_factors.append("Complex testing requirements")
            confidence_score += 0.1
        
        # Cap confidence at 1.0
        confidence_score = min(confidence_score, 1.0)
        
        # Make recommendation
        if confidence_score >= 0.8:
            recommendation = "ESCALATE to Claude 4.1 Opus - High confidence recommendation"
        elif confidence_score >= 0.6:
            recommendation = "RECOMMEND escalation to Claude 4.1 Opus"
        elif confidence_score >= 0.4:
            recommendation = "Consider escalation to Claude 4.1 Opus"
        else:
            recommendation = "GLM-4.5 should be sufficient"
        
        return recommendation, confidence_score
    
    def _identify_key_factors(
        self,
        complexity_metrics: ComplexityMetrics,
        business_impact: BusinessImpactMetrics,
        risk_metrics: RiskMetrics,
        dependencies: DependencyAnalysis
    ) -> List[str]:
        """Identify key factors influencing the decision"""
        
        key_factors = []
        
        # Complexity factors
        if complexity_metrics.complexity_level != ComplexityLevel.SIMPLE:
            key_factors.append(f"Code complexity: {complexity_metrics.complexity_level.value}")
        
        # Business impact factors
        if business_impact.overall_impact != BusinessImpact.LOW:
            key_factors.append(f"Business impact: {business_impact.overall_impact.value}")
        
        # Risk factors
        if risk_metrics.overall_risk != RiskLevel.LOW:
            key_factors.append(f"Risk level: {risk_metrics.overall_risk.value}")
        
        # Dependency factors
        if dependencies.cross_service_dependencies:
            key_factors.append(f"Cross-service dependencies: {len(dependencies.cross_service_dependencies)}")
        
        if dependencies.critical_dependencies:
            key_factors.append(f"Critical dependencies: {len(dependencies.critical_dependencies)}")
        
        return key_factors


# Convenience function for quick context analysis
def analyze_task_context(
    task_description: str,
    files_to_modify: List[str],
    file_contents: Optional[Dict[str, str]] = None,
    task_type: str = "implementation"
) -> ContextAnalysisResult:
    """
    Quick context analysis for escalation decisions
    
    Args:
        task_description: Description of the task
        files_to_modify: Files to be modified
        file_contents: Optional file contents
        task_type: Type of task
        
    Returns:
        ContextAnalysisResult with analysis
    """
    analyzer = ContextAnalyzer()
    return analyzer.analyze_task_context(
        task_description=task_description,
        files_to_modify=files_to_modify,
        file_contents=file_contents,
        task_type=task_type
    )