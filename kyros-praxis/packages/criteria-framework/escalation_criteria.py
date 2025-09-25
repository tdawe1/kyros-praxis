#!/usr/bin/env python3
"""
Claude 4.1 Opus Escalation Criteria Framework

This module implements a comprehensive decision system for determining when GLM-4.5 
should escalate to Claude 4.1 Opus based on task complexity, security implications, 
and system impact.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classifications"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ServiceType(Enum):
    """Service type classifications"""
    ORCHESTRATOR = "orchestrator"
    CONSOLE = "console"
    TERMINAL_DAEMON = "terminal-daemon"
    DATABASE = "database"
    CACHE = "cache"
    AUTH = "auth"
    EXTERNAL_API = "external_api"
    INFRASTRUCTURE = "infrastructure"


@dataclass
class CriteriaScore:
    """Represents the score for a specific criteria"""
    name: str
    score: float
    max_score: float
    weight: float
    justification: str = ""
    
    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


@dataclass
class DecisionResult:
    """Result of escalation decision"""
    should_escalate: bool
    total_score: float
    threshold: float
    criteria_scores: List[CriteriaScore] = field(default_factory=list)
    primary_reasons: List[str] = field(default_factory=list)
    recommendation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "should_escalate": self.should_escalate,
            "total_score": self.total_score,
            "threshold": self.threshold,
            "criteria_scores": [
                {
                    "name": cs.name,
                    "score": cs.score,
                    "max_score": cs.max_score,
                    "weight": cs.weight,
                    "weighted_score": cs.weighted_score,
                    "justification": cs.justification
                }
                for cs in self.criteria_scores
            ],
            "primary_reasons": self.primary_reasons,
            "recommendation": self.recommendation
        }


class ArchitectCriteria:
    """Criteria for architect role escalation decisions"""
    
    def __init__(self):
        self.min_escalation_threshold = 0.75  # 75% score threshold
        self.critical_factors_threshold = 0.90  # 90% for auto-escalate
        
    def evaluate_service_impact(self, affected_services: Set[ServiceType]) -> CriteriaScore:
        """Evaluate impact across multiple services"""
        service_count = len(affected_services)
        score = 0.0
        justification = ""
        
        if service_count >= 3:
            score = 1.0
            justification = f"Affects {service_count} services, meets minimum threshold for escalation"
        elif service_count == 2:
            score = 0.6
            justification = f"Affects {service_count} services, moderate impact"
        else:
            score = 0.2
            justification = f"Affects {service_count} service(s), low impact"
        
        return CriteriaScore(
            name="service_impact",
            score=score,
            max_score=1.0,
            weight=0.25,
            justification=justification
        )
    
    def evaluate_security_implications(self, security_factors: Dict[str, bool]) -> CriteriaScore:
        """Evaluate security-related factors"""
        factors = [
            ("authentication", 0.3),
            ("authorization", 0.3),
            ("data_encryption", 0.2),
            ("input_validation", 0.15),
            ("csrf_protection", 0.05)
        ]
        
        total_score = 0.0
        max_score = sum(weight for _, weight in factors)
        active_factors = []
        
        for factor, weight in factors:
            if security_factors.get(factor, False):
                total_score += weight
                active_factors.append(factor)
        
        score = total_score / max_score if max_score > 0 else 0.0
        
        justification = ""
        if score >= 0.7:
            justification = f"Critical security implications: {', '.join(active_factors)}"
        elif score >= 0.4:
            justification = f"Moderate security concerns: {', '.join(active_factors)}"
        else:
            justification = f"Minor security considerations: {', '.join(active_factors)}"
        
        return CriteriaScore(
            name="security_implications",
            score=score,
            max_score=1.0,
            weight=0.30,
            justification=justification
        )
    
    def evaluate_performance_criticality(self, perf_factors: Dict[str, bool]) -> CriteriaScore:
        """Evaluate performance-critical factors"""
        factors = [
            ("high_throughput", 0.25),
            ("low_latency_required", 0.25),
            ("scalability_constraints", 0.20),
            ("resource_intensive", 0.15),
            ("real_time_requirements", 0.15)
        ]
        
        total_score = 0.0
        max_score = sum(weight for _, weight in factors)
        active_factors = []
        
        for factor, weight in factors:
            if perf_factors.get(factor, False):
                total_score += weight
                active_factors.append(factor)
        
        score = total_score / max_score if max_score > 0 else 0.0
        
        justification = ""
        if score >= 0.7:
            justification = f"High-performance requirements: {', '.join(active_factors)}"
        elif score >= 0.4:
            justification = f"Moderate performance considerations: {', '.join(active_factors)}"
        else:
            justification = f"Standard performance profile: {', '.join(active_factors)}"
        
        return CriteriaScore(
            name="performance_criticality",
            score=score,
            max_score=1.0,
            weight=0.25,
            justification=justification
        )
    
    def evaluate_architectural_complexity(self, complexity_factors: Dict[str, bool]) -> CriteriaScore:
        """Evaluate architectural complexity factors"""
        factors = [
            ("microservices_coordination", 0.20),
            ("event_driven_design", 0.15),
            ("distributed_transactions", 0.25),
            ("circuit_breakers", 0.10),
            ("service_discovery", 0.10),
            ("load_balancing", 0.10),
            ("failure_domain_isolation", 0.10)
        ]
        
        total_score = 0.0
        max_score = sum(weight for _, weight in factors)
        active_factors = []
        
        for factor, weight in factors:
            if complexity_factors.get(factor, False):
                total_score += weight
                active_factors.append(factor)
        
        score = total_score / max_score if max_score > 0 else 0.0
        
        justification = ""
        if score >= 0.6:
            justification = f"Complex architectural patterns: {', '.join(active_factors)}"
        elif score >= 0.3:
            justification = f"Moderate architectural complexity: {', '.join(active_factors)}"
        else:
            justification = f"Straightforward architecture: {', '.join(active_factors)}"
        
        return CriteriaScore(
            name="architectural_complexity",
            score=score,
            max_score=1.0,
            weight=0.20,
            justification=justification
        )
    
    def make_decision(self, context: Dict) -> DecisionResult:
        """Make escalation decision for architect role"""
        affected_services = context.get("affected_services", set())
        security_factors = context.get("security_factors", {})
        perf_factors = context.get("performance_factors", {})
        complexity_factors = context.get("complexity_factors", {})
        
        # Evaluate all criteria
        scores = [
            self.evaluate_service_impact(affected_services),
            self.evaluate_security_implications(security_factors),
            self.evaluate_performance_criticality(perf_factors),
            self.evaluate_architectural_complexity(complexity_factors)
        ]
        
        # Calculate total weighted score
        total_score = sum(cs.weighted_score for cs in scores)
        
        # Determine if escalation is needed
        should_escalate = total_score >= self.min_escalation_threshold
        
        # Generate primary reasons and recommendation
        primary_reasons = []
        if len(affected_services) >= 3:
            primary_reasons.append("Affects 3+ services")
        
        high_security_score = any(
            cs.name == "security_implications" and cs.score >= 0.7 for cs in scores
        )
        if high_security_score:
            primary_reasons.append("Critical security implications")
        
        high_perf_score = any(
            cs.name == "performance_criticality" and cs.score >= 0.7 for cs in scores
        )
        if high_perf_score:
            primary_reasons.append("High-performance requirements")
        
        if not primary_reasons and should_escalate:
            primary_reasons.append("Complexity threshold met")
        
        # Generate recommendation
        if total_score >= self.critical_factors_threshold:
            recommendation = "AUTO-ESCALATE: Critical factors detected requiring Claude 4.1 Opus expertise"
        elif should_escalate:
            recommendation = "RECOMMEND ESCALATION: Consider Claude 4.1 Opus for complex architectural decisions"
        else:
            recommendation = "PROCEED WITH GLM-4.5: Task complexity within acceptable limits"
        
        return DecisionResult(
            should_escalate=should_escalate,
            total_score=total_score,
            threshold=self.min_escalation_threshold,
            criteria_scores=scores,
            primary_reasons=primary_reasons,
            recommendation=recommendation
        )


class IntegratorCriteria:
    """Criteria for integrator role escalation decisions"""
    
    def __init__(self):
        self.min_escalation_threshold = 0.80  # Higher threshold for integrator
        self.critical_conflict_threshold = 0.95  # Near-certain escalation for major conflicts
        
    def evaluate_conflict_severity(self, conflict_factors: Dict[str, bool]) -> CriteriaScore:
        """Evaluate merge conflict severity"""
        factors = [
            ("multiple_service_conflicts", 0.30),
            ("api_contract_breaks", 0.25),
            ("data_model_conflicts", 0.20),
            ("dependency_chain_breaks", 0.15),
            ("migration_conflicts", 0.10)
        ]
        
        total_score = 0.0
        max_score = sum(weight for _, weight in factors)
        active_factors = []
        
        for factor, weight in factors:
            if conflict_factors.get(factor, False):
                total_score += weight
                active_factors.append(factor)
        
        score = total_score / max_score if max_score > 0 else 0.0
        
        justification = ""
        if score >= 0.7:
            justification = f"Severe conflicts requiring expert resolution: {', '.join(active_factors)}"
        elif score >= 0.4:
            justification = f"Moderate conflicts: {', '.join(active_factors)}"
        else:
            justification = f"Minor conflicts: {', '.join(active_factors)}"
        
        return CriteriaScore(
            name="conflict_severity",
            score=score,
            max_score=1.0,
            weight=0.35,
            justification=justification
        )
    
    def evaluate_system_boundary_impact(self, boundary_factors: Dict[str, bool]) -> CriteriaScore:
        """Evaluate impact on system boundaries"""
        factors = [
            ("authentication_boundary", 0.25),
            ("data_boundary", 0.20),
            ("service_boundary", 0.20),
            ("api_boundary", 0.20),
            ("infrastructure_boundary", 0.15)
        ]
        
        total_score = 0.0
        max_score = sum(weight for _, weight in factors)
        active_factors = []
        
        for factor, weight in factors:
            if boundary_factors.get(factor, False):
                total_score += weight
                active_factors.append(factor)
        
        score = total_score / max_score if max_score > 0 else 0.0
        
        justification = ""
        if score >= 0.6:
            justification = f"Multiple system boundaries affected: {', '.join(active_factors)}"
        elif score >= 0.3:
            justification = f"Some boundary considerations: {', '.join(active_factors)}"
        else:
            justification = f"Minimal boundary impact: {', '.join(active_factors)}"
        
        return CriteriaScore(
            name="system_boundary_impact",
            score=score,
            max_score=1.0,
            weight=0.30,
            justification=justification
        )
    
    def evaluate_integration_complexity(self, integration_factors: Dict[str, bool]) -> CriteriaScore:
        """Evaluate integration complexity"""
        factors = [
            ("cross_service_dependencies", 0.25),
            ("version_conflicts", 0.20),
            ("schema_migrations", 0.20),
            ("configuration_drift", 0.15),
            ("test_integration", 0.10),
            ("deployment_coordination", 0.10)
        ]
        
        total_score = 0.0
        max_score = sum(weight for _, weight in factors)
        active_factors = []
        
        for factor, weight in factors:
            if integration_factors.get(factor, False):
                total_score += weight
                active_factors.append(factor)
        
        score = total_score / max_score if max_score > 0 else 0.0
        
        justification = ""
        if score >= 0.6:
            justification = f"High integration complexity: {', '.join(active_factors)}"
        elif score >= 0.3:
            justification = f"Moderate integration challenges: {', '.join(active_factors)}"
        else:
            justification = f"Standard integration: {', '.join(active_factors)}"
        
        return CriteriaScore(
            name="integration_complexity",
            score=score,
            max_score=1.0,
            weight=0.20,
            justification=justification
        )
    
    def evaluate_risk_factors(self, risk_factors: Dict[str, bool]) -> CriteriaScore:
        """Evaluate risk factors for integration"""
        factors = [
            ("data_loss_risk", 0.30),
            ("service_disruption_risk", 0.25),
            ("rollback_complexity", 0.20),
            ("deployment_failure_risk", 0.15),
            ("performance_regression_risk", 0.10)
        ]
        
        total_score = 0.0
        max_score = sum(weight for _, weight in factors)
        active_factors = []
        
        for factor, weight in factors:
            if risk_factors.get(factor, False):
                total_score += weight
                active_factors.append(factor)
        
        score = total_score / max_score if max_score > 0 else 0.0
        
        justification = ""
        if score >= 0.6:
            justification = f"High-risk integration: {', '.join(active_factors)}"
        elif score >= 0.3:
            justification = f"Moderate risk factors: {', '.join(active_factors)}"
        else:
            justification = f"Low-risk integration: {', '.join(active_factors)}"
        
        return CriteriaScore(
            name="risk_factors",
            score=score,
            max_score=1.0,
            weight=0.15,
            justification=justification
        )
    
    def make_decision(self, context: Dict) -> DecisionResult:
        """Make escalation decision for integrator role"""
        conflict_factors = context.get("conflict_factors", {})
        boundary_factors = context.get("boundary_factors", {})
        integration_factors = context.get("integration_factors", {})
        risk_factors = context.get("risk_factors", {})
        
        # Evaluate all criteria
        scores = [
            self.evaluate_conflict_severity(conflict_factors),
            self.evaluate_system_boundary_impact(boundary_factors),
            self.evaluate_integration_complexity(integration_factors),
            self.evaluate_risk_factors(risk_factors)
        ]
        
        # Calculate total weighted score
        total_score = sum(cs.weighted_score for cs in scores)
        
        # Determine if escalation is needed
        should_escalate = total_score >= self.min_escalation_threshold
        
        # Generate primary reasons and recommendation
        primary_reasons = []
        
        high_conflict_score = any(
            cs.name == "conflict_severity" and cs.score >= 0.7 for cs in scores
        )
        if high_conflict_score:
            primary_reasons.append("Severe merge conflicts detected")
        
        high_boundary_score = any(
            cs.name == "system_boundary_impact" and cs.score >= 0.6 for cs in scores
        )
        if high_boundary_score:
            primary_reasons.append("Multiple system boundaries affected")
        
        high_risk_score = any(
            cs.name == "risk_factors" and cs.score >= 0.6 for cs in scores
        )
        if high_risk_score:
            primary_reasons.append("High-risk integration factors")
        
        if not primary_reasons and should_escalate:
            primary_reasons.append("Integration complexity threshold met")
        
        # Generate recommendation
        if total_score >= self.critical_conflict_threshold:
            recommendation = "AUTO-ESCALATE: Critical conflicts requiring Claude 4.1 Opus expertise"
        elif should_escalate:
            recommendation = "RECOMMEND ESCALATION: Complex integration may benefit from Claude 4.1 Opus"
        else:
            recommendation = "PROCEED WITH GLM-4.5: Integration within standard complexity limits"
        
        return DecisionResult(
            should_escalate=should_escalate,
            total_score=total_score,
            threshold=self.min_escalation_threshold,
            criteria_scores=scores,
            primary_reasons=primary_reasons,
            recommendation=recommendation
        )


class EscalationFramework:
    """Main escalation framework that coordinates all role criteria"""
    
    def __init__(self):
        self.architect_criteria = ArchitectCriteria()
        self.integrator_criteria = IntegratorCriteria()
        self.decision_history: List[Dict] = []
        
    def evaluate_architect_task(self, task_context: Dict) -> DecisionResult:
        """Evaluate whether architect task should escalate to Opus"""
        logger.info(f"Evaluating architect task for escalation: {task_context.get('task_id', 'unknown')}")
        
        result = self.architect_criteria.make_decision(task_context)
        
        # Log decision
        self.decision_history.append({
            "timestamp": self._get_timestamp(),
            "role": "architect",
            "task_id": task_context.get("task_id"),
            "decision": result.to_dict()
        })
        
        logger.info(f"Architect escalation decision: {result.should_escalate} (score: {result.total_score:.2f})")
        return result
    
    def evaluate_integrator_task(self, task_context: Dict) -> DecisionResult:
        """Evaluate whether integrator task should escalate to Opus"""
        logger.info(f"Evaluating integrator task for escalation: {task_context.get('task_id', 'unknown')}")
        
        result = self.integrator_criteria.make_decision(task_context)
        
        # Log decision
        self.decision_history.append({
            "timestamp": self._get_timestamp(),
            "role": "integrator",
            "task_id": task_context.get("task_id"),
            "decision": result.to_dict()
        })
        
        logger.info(f"Integrator escalation decision: {result.should_escalate} (score: {result.total_score:.2f})")
        return result
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
    
    def get_decision_history(self, role: Optional[str] = None) -> List[Dict]:
        """Get decision history, optionally filtered by role"""
        if role:
            return [d for d in self.decision_history if d["role"] == role]
        return self.decision_history.copy()
    
    def analyze_patterns(self) -> Dict:
        """Analyze escalation patterns"""
        if not self.decision_history:
            return {"message": "No decisions recorded yet"}
        
        total_decisions = len(self.decision_history)
        escalations = sum(1 for d in self.decision_history if d["decision"]["should_escalate"])
        
        role_breakdown = {}
        for role in ["architect", "integrator"]:
            role_decisions = [d for d in self.decision_history if d["role"] == role]
            if role_decisions:
                role_escalations = sum(1 for d in role_decisions if d["decision"]["should_escalate"])
                role_breakdown[role] = {
                    "total": len(role_decisions),
                    "escalations": role_escalations,
                    "escalation_rate": role_escalations / len(role_decisions)
                }
        
        return {
            "total_decisions": total_decisions,
            "total_escalations": escalations,
            "overall_escalation_rate": escalations / total_decisions,
            "role_breakdown": role_breakdown
        }


# Utility functions for context extraction
def extract_service_context(files_changed: List[str]) -> Set[ServiceType]:
    """Extract service types from file paths"""
    services = set()
    
    for file_path in files_changed:
        if "orchestrator" in file_path:
            services.add(ServiceType.ORCHESTRATOR)
        elif "console" in file_path:
            services.add(ServiceType.CONSOLE)
        elif "terminal-daemon" in file_path:
            services.add(ServiceType.TERMINAL_DAEMON)
        elif any(db_term in file_path for db_term in ["models.py", "database", "migrations"]):
            services.add(ServiceType.DATABASE)
        elif "auth" in file_path:
            services.add(ServiceType.AUTH)
        # Check for database in the path more specifically
        elif "database" in file_path.lower():
            services.add(ServiceType.DATABASE)
    
    return services


def extract_security_factors(files_changed: List[str], commit_messages: List[str]) -> Dict[str, bool]:
    """Extract security-related factors from files and messages"""
    factors = {
        "authentication": False,
        "authorization": False,
        "csrf_protection": False,
        "input_validation": False,
        "data_encryption": False
    }
    
    # Check files and messages for security keywords
    all_text = " ".join(files_changed + commit_messages).lower()
    
    if any(term in all_text for term in ["auth", "authentication", "jwt", "token", "login"]):
        factors["authentication"] = True
    
    if any(term in all_text for term in ["authorization", "permission", "access", "oauth", "oauth2"]):
        factors["authorization"] = True
    
    if any(term in all_text for term in ["csrf", "cross-site", "token"]):
        factors["csrf_protection"] = True
    
    if any(term in all_text for term in ["validation", "sanitize", "input", "form"]):
        factors["input_validation"] = True
    
    if any(term in all_text for term in ["encrypt", "decrypt", "cipher", "password", "salt", "hash"]):
        factors["data_encryption"] = True
    
    return factors


def extract_performance_factors(files_changed: List[str], commit_messages: List[str]) -> Dict[str, bool]:
    """Extract performance-related factors"""
    factors = {
        "high_throughput": False,
        "low_latency_required": False,
        "scalability_constraints": False,
        "resource_intensive": False,
        "real_time_requirements": False
    }
    
    all_text = " ".join(files_changed + commit_messages).lower()
    
    if any(term in all_text for term in ["throughput", "tps", "requests", "scale"]):
        factors["high_throughput"] = True
    
    if any(term in all_text for term in ["latency", "response", "speed", "fast"]):
        factors["low_latency_required"] = True
    
    if any(term in all_text for term in ["scalability", "scale", "load", "concurrent"]):
        factors["scalability_constraints"] = True
    
    if any(term in all_text for term in ["resource", "memory", "cpu", "heavy"]):
        factors["resource_intensive"] = True
    
    if any(term in all_text for term in ["real-time", "stream", "live", "immediate"]):
        factors["real_time_requirements"] = True
    
    return factors


# Singleton instance for global use
framework = EscalationFramework()