#!/usr/bin/env python3
"""
Decision Threshold Logic and Automated Escalation System

This module implements sophisticated threshold logic for automatic escalation decisions,
including dynamic thresholds, confidence scoring, and automated escalation workflows.
"""

import json
import logging
import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Callable, Any, Union
from datetime import datetime, timedelta
from pathlib import Path
import statistics

from escalation_criteria import (
    EscalationFramework, DecisionResult, ServiceType
)
from validation_system import ScoringCalibrator

logger = logging.getLogger(__name__)


class ConfidenceLevel(Enum):
    """Confidence levels for decisions"""
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


class EscalationType(Enum):
    """Types of escalation actions"""
    NONE = "none"
    RECOMMENDED = "recommended"
    AUTOMATIC = "automatic"
    OVERRIDE_REQUIRED = "override_required"


@dataclass
class ThresholdConfig:
    """Configuration for escalation thresholds"""
    architect_threshold: float = 0.75
    integrator_threshold: float = 0.80
    architect_auto_escalate_threshold: float = 0.90
    integrator_auto_escalate_threshold: float = 0.95
    confidence_threshold: float = 0.80
    uncertainty_threshold: float = 0.15
    
    # Dynamic adjustment parameters
    enable_dynamic_thresholds: bool = True
    adjustment_rate: float = 0.05
    min_threshold: float = 0.50
    max_threshold: float = 0.99
    
    # Safety parameters
    max_escalations_per_hour: int = 10
    max_escalations_per_day: int = 50
    cost_threshold_per_escalation: float = 0.50  # USD


@dataclass
class EscalationDecision:
    """Complete escalation decision with metadata"""
    should_escalate: bool
    escalation_type: EscalationType
    confidence: ConfidenceLevel
    certainty_score: float
    uncertainty_score: float
    risk_score: float
    cost_estimate: float
    reasoning: List[str]
    alternatives: List[str]
    override_allowed: bool
    override_reason: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "should_escalate": self.should_escalate,
            "escalation_type": self.escalation_type.value,
            "confidence": self.confidence.name,
            "certainty_score": self.certainty_score,
            "uncertainty_score": self.uncertainty_score,
            "risk_score": self.risk_score,
            "cost_estimate": self.cost_estimate,
            "reasoning": self.reasoning,
            "alternatives": self.alternatives,
            "override_allowed": self.override_allowed,
            "override_reason": self.override_reason
        }


@dataclass
class EscalationHistory:
    """History of escalation decisions"""
    timestamp: datetime
    role: str
    task_id: str
    decision: EscalationDecision
    context_hash: str
    execution_time: float
    user_feedback: Optional[str] = None
    actual_cost: Optional[float] = None


class DynamicThresholdManager:
    """Manages dynamic threshold adjustments based on feedback"""
    
    def __init__(self, config: ThresholdConfig):
        self.config = config
        self.adjustment_history: List[Dict] = []
        self.performance_metrics: Dict[str, List[float]] = {
            "accuracy": [],
            "false_positive_rate": [],
            "false_negative_rate": [],
            "user_satisfaction": []
        }
        
    def calculate_dynamic_threshold(
        self, 
        role: str, 
        recent_performance: Dict[str, float]
    ) -> float:
        """Calculate dynamically adjusted threshold"""
        if not self.config.enable_dynamic_thresholds:
            return getattr(self.config, f"{role}_threshold")
        
        base_threshold = getattr(self.config, f"{role}_threshold")
        
        # Adjust based on accuracy
        accuracy = recent_performance.get("accuracy", 0.8)
        if accuracy < 0.7:
            # Poor accuracy - adjust threshold
            adjustment = (0.7 - accuracy) * self.config.adjustment_rate
            new_threshold = max(
                self.config.min_threshold,
                base_threshold - adjustment
            )
        elif accuracy > 0.95:
            # Excellent accuracy - can be more conservative
            adjustment = (accuracy - 0.95) * self.config.adjustment_rate
            new_threshold = min(
                self.config.max_threshold,
                base_threshold + adjustment
            )
        else:
            new_threshold = base_threshold
        
        # Consider false positive/negative rates
        fp_rate = recent_performance.get("false_positive_rate", 0.1)
        fn_rate = recent_performance.get("false_negative_rate", 0.1)
        
        if fp_rate > 0.2:
            # Too many false positives - raise threshold
            new_threshold = min(
                self.config.max_threshold,
                new_threshold + (fp_rate - 0.2) * self.config.adjustment_rate
            )
        
        if fn_rate > 0.2:
            # Too many false negatives - lower threshold
            new_threshold = max(
                self.config.min_threshold,
                new_threshold - (fn_rate - 0.2) * self.config.adjustment_rate
            )
        
        # Record adjustment
        self.adjustment_history.append({
            "timestamp": datetime.utcnow(),
            "role": role,
            "old_threshold": base_threshold,
            "new_threshold": new_threshold,
            "performance_metrics": recent_performance
        })
        
        logger.info(f"Dynamic threshold adjustment for {role}: "
                   f"{base_threshold:.3f} → {new_threshold:.3f}")
        
        return new_threshold
    
    def update_performance_metrics(self, metrics: Dict[str, float]) -> None:
        """Update performance metrics for threshold calculation"""
        for key, value in metrics.items():
            if key in self.performance_metrics:
                self.performance_metrics[key].append(value)
                # Keep only recent history (last 100 measurements)
                if len(self.performance_metrics[key]) > 100:
                    self.performance_metrics[key] = self.performance_metrics[key][-100:]
    
    def get_recent_performance(self, window_hours: int = 24) -> Dict[str, float]:
        """Get recent performance metrics"""
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        recent_history = [
            adj for adj in self.adjustment_history
            if adj["timestamp"] > cutoff
        ]
        
        if not recent_history:
            return {"accuracy": 0.8, "false_positive_rate": 0.1, "false_negative_rate": 0.1}
        
        # Aggregate recent metrics
        return {
            "accuracy": statistics.mean([
                adj["performance_metrics"].get("accuracy", 0.8)
                for adj in recent_history
            ]),
            "false_positive_rate": statistics.mean([
                adj["performance_metrics"].get("false_positive_rate", 0.1)
                for adj in recent_history
            ]),
            "false_negative_rate": statistics.mean([
                adj["performance_metrics"].get("false_negative_rate", 0.1)
                for adj in recent_history
            ])
        }


class ConfidenceCalculator:
    """Calculates confidence scores for escalation decisions"""
    
    def __init__(self):
        self.confidence_factors = {
            "score_clarity": 0.25,
            "consistency": 0.20,
            "context_completeness": 0.20,
            "historical_accuracy": 0.15,
            "risk_certainty": 0.10,
            "cost_certainty": 0.10
        }
    
    def calculate_confidence(
        self, 
        decision_result: DecisionResult,
        context: Dict,
        historical_data: List[EscalationHistory]
    ) -> Tuple[ConfidenceLevel, float]:
        """Calculate overall confidence in the decision"""
        
        factors = {}
        
        # Score clarity (how far from threshold)
        score_distance = abs(decision_result.total_score - decision_result.threshold)
        max_distance = max(decision_result.threshold, 1.0 - decision_result.threshold)
        factors["score_clarity"] = min(1.0, score_distance / max_distance)
        
        # Consistency with historical decisions
        factors["consistency"] = self._calculate_consistency(
            decision_result, context, historical_data
        )
        
        # Context completeness
        factors["context_completeness"] = self._assess_context_completeness(context)
        
        # Historical accuracy
        factors["historical_accuracy"] = self._calculate_historical_accuracy(historical_data)
        
        # Risk certainty
        factors["risk_certainty"] = self._assess_risk_certainty(decision_result)
        
        # Cost certainty
        factors["cost_certainty"] = self._assess_cost_certainty(decision_result)
        
        # Calculate weighted confidence score
        confidence_score = sum(
            factors[factor] * weight 
            for factor, weight in self.confidence_factors.items()
        )
        
        # Map to confidence level
        if confidence_score >= 0.9:
            confidence_level = ConfidenceLevel.VERY_HIGH
        elif confidence_score >= 0.75:
            confidence_level = ConfidenceLevel.HIGH
        elif confidence_score >= 0.6:
            confidence_level = ConfidenceLevel.MEDIUM
        elif confidence_score >= 0.4:
            confidence_level = ConfidenceLevel.LOW
        else:
            confidence_level = ConfidenceLevel.VERY_LOW
        
        return confidence_level, confidence_score
    
    def _calculate_consistency(
        self, 
        decision_result: DecisionResult,
        context: Dict,
        historical_data: List[EscalationHistory]
    ) -> float:
        """Calculate consistency with historical decisions"""
        if not historical_data:
            return 0.5  # Neutral for no history
        
        # Find similar historical decisions
        similar_decisions = [
            hist for hist in historical_data
            if hist.context_hash == self._hash_context(context)
        ]
        
        if not similar_decisions:
            return 0.7  # Slightly positive for unique contexts
        
        # Check consistency
        consistent = sum(
            1 for hist in similar_decisions
            if hist.decision.should_escalate == decision_result.should_escalate
        )
        
        return consistent / len(similar_decisions)
    
    def _assess_context_completeness(self, context: Dict) -> float:
        """Assess how complete the context information is"""
        required_keys = {
            "architect": ["affected_services", "security_factors", "performance_factors", "complexity_factors"],
            "integrator": ["conflict_factors", "boundary_factors", "integration_factors", "risk_factors"]
        }
        
        # Determine role from context
        if "affected_services" in context:
            role = "architect"
            required = required_keys["architect"]
        elif "conflict_factors" in context:
            role = "integrator"
            required = required_keys["integrator"]
        else:
            return 0.3  # Low for unclear role
        
        # Check required keys
        present_keys = sum(1 for key in required if key in context and context[key])
        completeness = present_keys / len(required)
        
        # Additional check for non-empty values
        non_empty_values = 0
        for key in required:
            if key in context and context[key]:
                if isinstance(context[key], dict):
                    if any(context[key].values()):
                        non_empty_values += 1
                elif isinstance(context[key], (set, list)):
                    if len(context[key]) > 0:
                        non_empty_values += 1
        
        value_completeness = non_empty_values / len(required) if required else 0
        
        return (completeness + value_completeness) / 2
    
    def _calculate_historical_accuracy(self, historical_data: List[EscalationHistory]) -> float:
        """Calculate historical accuracy of decisions"""
        if not historical_data:
            return 0.8  # Default positive assumption
        
        recent_data = historical_data[-20:]  # Last 20 decisions
        
        feedback_based_accuracy = 0.8  # Default
        if recent_data:
            positive_feedback = sum(
                1 for hist in recent_data
                if hist.user_feedback and hist.user_feedback.lower() in ["good", "correct", "accurate"]
            )
            total_feedback = sum(
                1 for hist in recent_data
                if hist.user_feedback
            )
            
            if total_feedback > 0:
                feedback_based_accuracy = positive_feedback / total_feedback
        
        return feedback_based_accuracy
    
    def _assess_risk_certainty(self, decision_result: DecisionResult) -> float:
        """Assess certainty in risk assessment"""
        # Higher scores near thresholds are less certain
        threshold_distance = abs(decision_result.total_score - decision_result.threshold)
        
        if threshold_distance < 0.1:
            return 0.3  # Low certainty near threshold
        elif threshold_distance < 0.2:
            return 0.6  # Medium certainty
        else:
            return 0.9  # High certainty when clearly above/below
    
    def _assess_cost_certainty(self, decision_result: DecisionResult) -> float:
        """Assess certainty in cost estimation"""
        # Cost is more certain when factors are clear
        clear_factors = sum(
            1 for cs in decision_result.criteria_scores
            if cs.score > 0.7 or cs.score < 0.3
        )
        total_factors = len(decision_result.criteria_scores)
        
        return clear_factors / total_factors if total_factors > 0 else 0.5
    
    def _hash_context(self, context: Dict) -> str:
        """Create hash of context for comparison"""
        import hashlib
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()


class CostEstimator:
    """Estimates costs for escalation decisions"""
    
    def __init__(self):
        self.cost_model = {
            "claude_opus_input_cost": 0.015,  # $0.015 per 1K tokens
            "claude_opus_output_cost": 0.075,  # $0.075 per 1K tokens
            "average_tokens_per_decision": 5000,
            "average_output_tokens": 1000,
            "operational_overhead": 0.05  # 5% overhead
        }
    
    def estimate_cost(self, decision_result: DecisionResult) -> float:
        """Estimate cost for this escalation decision"""
        
        # Base calculation
        input_cost = (self.cost_model["average_tokens_per_decision"] / 1000) * self.cost_model["claude_opus_input_cost"]
        output_cost = (self.cost_model["average_output_tokens"] / 1000) * self.cost_model["claude_opus_output_cost"]
        
        # Adjust based on complexity
        complexity_multiplier = 1.0 + (decision_result.total_score - 0.5) * 0.5
        complexity_multiplier = max(0.5, min(2.0, complexity_multiplier))
        
        total_cost = (input_cost + output_cost) * complexity_multiplier
        
        # Add overhead
        total_cost *= (1 + self.cost_model["operational_overhead"])
        
        return round(total_cost, 4)
    
    def is_cost_justified(self, cost: float, risk_score: float, context: Dict) -> bool:
        """Determine if escalation cost is justified"""
        
        # High-risk scenarios always justify cost
        if risk_score > 0.8:
            return True
        
        # Security-critical scenarios justify cost
        security_factors = context.get("security_factors", {})
        if any(security_factors.values()):
            return True
        
        # Multi-service scenarios justify moderate cost
        affected_services = context.get("affected_services", set())
        if len(affected_services) >= 3:
            return True
        
        # Cost threshold check
        return cost <= 1.0  # $1.00 threshold for non-critical scenarios


class AutomatedEscalationSystem:
    """Main system for automated escalation decisions"""
    
    def __init__(self, config: Optional[ThresholdConfig] = None):
        self.config = config or ThresholdConfig()
        self.framework = EscalationFramework()
        self.threshold_manager = DynamicThresholdManager(self.config)
        self.confidence_calculator = ConfidenceCalculator()
        self.cost_estimator = CostEstimator()
        self.calibrator = ScoringCalibrator(self.framework)
        
        # Decision history
        self.decision_history: List[EscalationHistory] = []
        
        # Rate limiting
        self.recent_escalations: List[datetime] = []
        
    def make_escalation_decision(
        self,
        role: str,
        task_id: str,
        context: Dict,
        force_escalation: bool = False,
        prevent_escalation: bool = False
    ) -> EscalationDecision:
        """Make automated escalation decision"""
        
        logger.info(f"Making escalation decision for {role} task {task_id}")
        
        start_time = datetime.utcnow()
        
        # Apply overrides if specified
        if prevent_escalation:
            return EscalationDecision(
                should_escalate=False,
                escalation_type=EscalationType.NONE,
                confidence=ConfidenceLevel.VERY_HIGH,
                certainty_score=1.0,
                uncertainty_score=0.0,
                risk_score=0.0,
                cost_estimate=0.0,
                reasoning=["Manual override: escalation prevented"],
                alternatives=["Proceed with GLM-4.5"],
                override_allowed=False,
                override_reason="Manual override applied"
            )
        
        if force_escalation:
            return EscalationDecision(
                should_escalate=True,
                escalation_type=EscalationType.AUTOMATIC,
                confidence=ConfidenceLevel.VERY_HIGH,
                certainty_score=1.0,
                uncertainty_score=0.0,
                risk_score=1.0,
                cost_estimate=self.cost_estimator.estimate_cost(None),
                reasoning=["Manual override: escalation forced"],
                alternatives=["Escalate to Claude 4.1 Opus"],
                override_allowed=False,
                override_reason="Manual override applied"
            )
        
        # Check rate limits
        if not self._check_rate_limits():
            return EscalationDecision(
                should_escalate=False,
                escalation_type=EscalationType.NONE,
                confidence=ConfidenceLevel.HIGH,
                certainty_score=0.9,
                uncertainty_score=0.1,
                risk_score=0.5,
                cost_estimate=0.0,
                reasoning=["Rate limit exceeded for escalations"],
                alternatives=["Wait and retry", "Proceed with GLM-4.5"],
                override_allowed=True
            )
        
        # Get dynamic threshold
        recent_performance = self.threshold_manager.get_recent_performance()
        dynamic_threshold = self.threshold_manager.calculate_dynamic_threshold(role, recent_performance)
        
        # Get base decision from framework
        if role == "architect":
            decision_result = self.framework.evaluate_architect_task(context)
        elif role == "integrator":
            decision_result = self.framework.evaluate_integrator_task(context)
        else:
            raise ValueError(f"Unknown role: {role}")
        
        # Calculate confidence
        confidence_level, confidence_score = self.confidence_calculator.calculate_confidence(
            decision_result, context, self.decision_history
        )
        
        # Calculate uncertainty
        uncertainty_score = 1.0 - confidence_score
        
        # Estimate cost
        cost_estimate = self.cost_estimator.estimate_cost(decision_result)
        
        # Calculate risk score
        risk_score = decision_result.total_score
        
        # Determine escalation type
        auto_threshold = getattr(self.config, f"{role}_auto_escalate_threshold")
        
        if decision_result.should_escalate and decision_result.total_score >= auto_threshold:
            escalation_type = EscalationType.AUTOMATIC
        elif decision_result.should_escalate:
            escalation_type = EscalationType.RECOMMENDED
        else:
            escalation_type = EscalationType.NONE
        
        # Check cost justification
        cost_justified = self.cost_estimator.is_cost_justified(cost_estimate, risk_score, context)
        
        # Final decision logic
        should_escalate = (
            decision_result.should_escalate and
            cost_justified and
            confidence_score >= self.config.confidence_threshold and
            uncertainty_score <= self.config.uncertainty_threshold
        )
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            decision_result, confidence_level, cost_justified, dynamic_threshold
        )
        
        # Generate alternatives
        alternatives = self._generate_alternatives(
            decision_result, cost_estimate, uncertainty_score
        )
        
        # Create decision
        decision = EscalationDecision(
            should_escalate=should_escalate,
            escalation_type=escalation_type,
            confidence=confidence_level,
            certainty_score=confidence_score,
            uncertainty_score=uncertainty_score,
            risk_score=risk_score,
            cost_estimate=cost_estimate,
            reasoning=reasoning,
            alternatives=alternatives,
            override_allowed=True
        )
        
        # Record decision
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        context_hash = self.confidence_calculator._hash_context(context)
        
        history_entry = EscalationHistory(
            timestamp=datetime.utcnow(),
            role=role,
            task_id=task_id,
            decision=decision,
            context_hash=context_hash,
            execution_time=execution_time
        )
        
        self.decision_history.append(history_entry)
        self.recent_escalations.append(datetime.utcnow())
        
        # Update calibration data
        self.calibrator.add_calibration_data(context, decision.should_escalate, "")
        
        logger.info(f"Escalation decision: {decision.should_escalate} "
                   f"(type: {decision.escalation_type.value}, "
                   f"confidence: {decision.confidence.name}, "
                   f"cost: ${decision.cost_estimate:.4f})")
        
        return decision
    
    def _check_rate_limits(self) -> bool:
        """Check if escalation is allowed under rate limits"""
        now = datetime.utcnow()
        
        # Clean old escalations
        self.recent_escalations = [
            ts for ts in self.recent_escalations
            if now - ts < timedelta(days=1)
        ]
        
        # Check hourly limit
        recent_hour = [
            ts for ts in self.recent_escalations
            if now - ts < timedelta(hours=1)
        ]
        
        if len(recent_hour) >= self.config.max_escalations_per_hour:
            logger.warning("Hourly escalation limit reached")
            return False
        
        # Check daily limit
        if len(self.recent_escalations) >= self.config.max_escalations_per_day:
            logger.warning("Daily escalation limit reached")
            return False
        
        return True
    
    def _generate_reasoning(
        self,
        decision_result: DecisionResult,
        confidence_level: ConfidenceLevel,
        cost_justified: bool,
        dynamic_threshold: float
    ) -> List[str]:
        """Generate reasoning for the decision"""
        reasoning = []
        
        # Score-based reasoning
        if decision_result.should_escalate:
            reasoning.append(f"Score {decision_result.total_score:.3f} exceeds threshold {dynamic_threshold:.3f}")
        else:
            reasoning.append(f"Score {decision_result.total_score:.3f} below threshold {dynamic_threshold:.3f}")
        
        # Confidence reasoning
        reasoning.append(f"Confidence level: {confidence_level.name}")
        
        # Cost reasoning
        if not cost_justified:
            reasoning.append("Cost not justified for escalation")
        
        # Primary factors
        if decision_result.primary_reasons:
            reasoning.append(f"Primary factors: {', '.join(decision_result.primary_reasons)}")
        
        return reasoning
    
    def _generate_alternatives(
        self,
        decision_result: DecisionResult,
        cost_estimate: float,
        uncertainty_score: float
    ) -> List[str]:
        """Generate alternative approaches"""
        alternatives = []
        
        if decision_result.should_escalate:
            alternatives.append("Escalate to Claude 4.1 Opus")
            
            if uncertainty_score > 0.3:
                alternatives.append("Seek human review before escalation")
            
            if cost_estimate > self.config.cost_threshold_per_escalation:
                alternatives.append("Break down task to reduce cost")
        else:
            alternatives.append("Proceed with GLM-4.5")
            
            if uncertainty_score > 0.3:
                alternatives.append("Request additional context")
            
            if decision_result.total_score > decision_result.threshold * 0.9:
                alternatives.append("Consider manual escalation review")
        
        return alternatives
    
    def record_feedback(self, decision_id: str, feedback: str, actual_cost: Optional[float] = None) -> None:
        """Record user feedback on a decision"""
        # Find decision in history
        for history in self.decision_history:
            if history.task_id == decision_id:
                history.user_feedback = feedback
                if actual_cost is not None:
                    history.actual_cost = actual_cost
                
                # Update performance metrics
                metrics = {"accuracy": 1.0 if feedback.lower() in ["good", "correct"] else 0.0}
                self.threshold_manager.update_performance_metrics(metrics)
                
                logger.info(f"Recorded feedback for decision {decision_id}: {feedback}")
                break
    
    def get_decision_analytics(self) -> Dict:
        """Get analytics on escalation decisions"""
        if not self.decision_history:
            return {"message": "No decisions recorded"}
        
        total_decisions = len(self.decision_history)
        escalations = sum(1 for d in self.decision_history if d.decision.should_escalate)
        automatic_escalations = sum(
            1 for d in self.decision_history
            if d.decision.escalation_type == EscalationType.AUTOMATIC
        )
        
        # Calculate accuracy from feedback
        decisions_with_feedback = [
            d for d in self.decision_history
            if d.user_feedback
        ]
        
        if decisions_with_feedback:
            positive_feedback = sum(
                1 for d in decisions_with_feedback
                if d.user_feedback.lower() in ["good", "correct", "accurate"]
            )
            feedback_accuracy = positive_feedback / len(decisions_with_feedback)
        else:
            feedback_accuracy = None
        
        # Cost analysis
        total_estimated_cost = sum(d.decision.cost_estimate for d in self.decision_history)
        actual_costs = [d.actual_cost for d in self.decision_history if d.actual_cost]
        total_actual_cost = sum(actual_costs) if actual_costs else 0
        
        return {
            "summary": {
                "total_decisions": total_decisions,
                "escalations": escalations,
                "escalation_rate": escalations / total_decisions,
                "automatic_escalations": automatic_escalations,
                "automatic_escalation_rate": automatic_escalations / total_decisions
            },
            "accuracy": {
                "feedback_accuracy": feedback_accuracy,
                "decisions_with_feedback": len(decisions_with_feedback)
            },
            "costs": {
                "total_estimated_cost": total_estimated_cost,
                "total_actual_cost": total_actual_cost,
                "cost_variance": total_actual_cost - total_estimated_cost if actual_costs else 0
            },
            "confidence_distribution": {
                level.name: sum(1 for d in self.decision_history if d.decision.confidence == level)
                for level in ConfidenceLevel
            }
        }
    
    def export_decision_log(self, file_path: str) -> None:
        """Export decision history to file"""
        data = {
            "decisions": [
                {
                    "timestamp": hist.timestamp.isoformat(),
                    "role": hist.role,
                    "task_id": hist.task_id,
                    "decision": hist.decision.to_dict(),
                    "context_hash": hist.context_hash,
                    "execution_time": hist.execution_time,
                    "user_feedback": hist.user_feedback,
                    "actual_cost": hist.actual_cost
                }
                for hist in self.decision_history
            ],
            "analytics": self.get_decision_analytics(),
            "threshold_adjustments": self.threshold_manager.adjustment_history
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Decision log exported to {file_path}")


# Factory function for easy instantiation
def create_escalation_system(config: Optional[ThresholdConfig] = None) -> AutomatedEscalationSystem:
    """Create an automated escalation system"""
    return AutomatedEscalationSystem(config)


# Command-line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Automated escalation decision system")
    parser.add_argument("--role", choices=["architect", "integrator"], required=True,
                       help="Role for escalation decision")
    parser.add_argument("--task-id", required=True, help="Task identifier")
    parser.add_argument("--context-file", help="JSON file with task context")
    parser.add_argument("--force", action="store_true", help="Force escalation")
    parser.add_argument("--prevent", action="store_true", help="Prevent escalation")
    parser.add_argument("--output", help="Output file for decision")
    
    args = parser.parse_args()
    
    # Load context
    if args.context_file:
        with open(args.context_file, 'r') as f:
            context = json.load(f)
    else:
        context = {}
    
    # Create system and make decision
    system = create_escalation_system()
    decision = system.make_escalation_decision(
        role=args.role,
        task_id=args.task_id,
        context=context,
        force_escalation=args.force,
        prevent_escalation=args.prevent
    )
    
    # Output decision
    result = {
        "task_id": args.task_id,
        "role": args.role,
        "decision": decision.to_dict(),
        "analytics": system.get_decision_analytics()
    }
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"Decision saved to {args.output}")
    else:
        print(json.dumps(result, indent=2))