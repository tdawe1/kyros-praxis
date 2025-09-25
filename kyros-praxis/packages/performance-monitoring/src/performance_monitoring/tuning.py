import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import statistics

from .types import (
    PerformanceThreshold, 
    ModelType, 
    ModelPerformanceMetrics,
    PerformanceMetric
)
from .monitor import PerformanceMonitor

logger = logging.getLogger(__name__)


class TuningAction(str, Enum):
    """Types of tuning actions"""
    ADJUST_THRESHOLD = "adjust_threshold"
    SCALE_RESOURCES = "scale_resources"
    CHANGE_MODEL_ROUTING = "change_model_routing"
    OPTIMIZE_CONFIG = "optimize_config"
    ALERT_ADMIN = "alert_admin"


@dataclass
class TuningRecommendation:
    """Recommendation for performance tuning"""
    action: TuningAction
    target: str  # What to tune (e.g., model type, threshold name)
    current_value: Any
    recommended_value: Any
    confidence: float  # 0.0 to 1.0
    reasoning: str
    impact: str  # Expected impact
    priority: int  # 1-10, higher is more urgent


@dataclass
class TuningConfiguration:
    """Configuration for automated tuning"""
    enabled: bool = True
    tuning_interval_minutes: int = 30
    confidence_threshold: float = 0.7
    impact_threshold: float = 0.1  # Minimum expected improvement
    max_concurrent_tunings: int = 3
    learning_rate: float = 0.1  # For gradual adjustments
    safety_margin: float = 0.2  # Conservative adjustment margin


class AutomatedTuner:
    """Automated performance tuning and threshold adjustment system"""
    
    def __init__(self,
                 monitor: PerformanceMonitor,
                 config: TuningConfiguration = None):
        self.monitor = monitor
        self.config = config or TuningConfiguration()
        self.active_tunings = []
        self.tuning_history = []
        self.threshold_configs = self._initialize_threshold_configs()
        self.model_routing_weights = self._initialize_routing_weights()
        self.last_tuning_time = datetime.now()
        
    def _initialize_threshold_configs(self) -> Dict[str, PerformanceThreshold]:
        """Initialize default threshold configurations"""
        return {
            'gpt_4_latency': PerformanceThreshold(
                metric=PerformanceMetric.LATENCY,
                max_value=45.0,
                warning_level=30.0,
                critical_level=40.0,
                model_type=ModelType.GPT_4
            ),
            'gpt_3_5_latency': PerformanceThreshold(
                metric=PerformanceMetric.LATENCY,
                max_value=25.0,
                warning_level=15.0,
                critical_level=20.0,
                model_type=ModelType.GPT_3_5
            ),
            'claude_latency': PerformanceThreshold(
                metric=PerformanceMetric.LATENCY,
                max_value=35.0,
                warning_level=25.0,
                critical_level=30.0,
                model_type=ModelType.CLAUDE
            ),
            'gemini_latency': PerformanceThreshold(
                metric=PerformanceMetric.LATENCY,
                max_value=30.0,
                warning_level=20.0,
                critical_level=25.0,
                model_type=ModelType.GEMINI
            ),
            'global_error_rate': PerformanceThreshold(
                metric=PerformanceMetric.ERROR_RATE,
                max_value=0.05,  # 5%
                warning_level=0.03,
                critical_level=0.04
            ),
            'global_quality': PerformanceThreshold(
                metric=PerformanceMetric.QUALITY,
                min_value=0.7,  # 70%
                warning_level=0.75,
                critical_level=0.72
            )
        }
    
    def _initialize_routing_weights(self) -> Dict[ModelType, Dict[str, float]]:
        """Initialize model routing weights"""
        return {
            ModelType.GPT_4: {'latency': 0.3, 'quality': 0.5, 'cost': 0.2},
            ModelType.GPT_3_5: {'latency': 0.5, 'quality': 0.3, 'cost': 0.2},
            ModelType.CLAUDE: {'latency': 0.4, 'quality': 0.4, 'cost': 0.2},
            ModelType.GEMINI: {'latency': 0.4, 'quality': 0.4, 'cost': 0.2},
            ModelType.LOCAL_LLAMA: {'latency': 0.2, 'quality': 0.3, 'cost': 0.5}
        }
    
    async def run_tuning_cycle(self) -> List[TuningRecommendation]:
        """Run a complete tuning cycle"""
        if not self.config.enabled:
            logger.info("Automated tuning is disabled")
            return []
        
        # Check if it's time for tuning
        if datetime.now() - self.last_tuning_time < timedelta(minutes=self.config.tuning_interval_minutes):
            return []
        
        logger.info("Starting automated tuning cycle")
        recommendations = []
        
        # Check each model type for tuning opportunities
        for model_type in ModelType:
            model_recommendations = await self._tune_model_performance(model_type)
            recommendations.extend(model_recommendations)
        
        # Check global thresholds
        global_recommendations = await self._tune_global_thresholds()
        recommendations.extend(global_recommendations)
        
        # Check routing optimization
        routing_recommendations = await self._optimize_model_routing()
        recommendations.extend(routing_recommendations)
        
        # Filter and prioritize recommendations
        filtered_recommendations = self._filter_recommendations(recommendations)
        
        # Apply automatic adjustments if confidence is high enough
        await self._apply_automatic_adjustments(filtered_recommendations)
        
        self.last_tuning_time = datetime.now()
        logger.info(f"Tuning cycle completed with {len(filtered_recommendations)} recommendations")
        
        return filtered_recommendations
    
    async def _tune_model_performance(self, model_type: ModelType) -> List[TuningRecommendation]:
        """Tune performance thresholds for a specific model"""
        recommendations = []
        
        # Get recent performance data
        performance_data = await self.monitor.get_recent_performance(
            model_type, timedelta(hours=24)
        )
        
        if not performance_data:
            return recommendations
        
        # Analyze latency patterns
        latency_recommendations = await self._analyze_latency_patterns(model_type, performance_data)
        recommendations.extend(latency_recommendations)
        
        # Analyze error rates
        error_recommendations = await self._analyze_error_patterns(model_type, performance_data)
        recommendations.extend(error_recommendations)
        
        # Analyze quality scores
        quality_recommendations = await self._analyze_quality_patterns(model_type, performance_data)
        recommendations.extend(quality_recommendations)
        
        return recommendations
    
    async def _analyze_latency_patterns(self, 
                                      model_type: ModelType,
                                      performance_data: List[ModelPerformanceMetrics]) -> List[TuningRecommendation]:
        """Analyze latency patterns and generate threshold recommendations"""
        recommendations = []
        
        successful_data = [p for p in performance_data if p.success]
        if not successful_data:
            return recommendations
        
        latencies = [p.execution_time for p in successful_data]
        avg_latency = statistics.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        
        # Find current threshold for this model
        threshold_key = f"{model_type.value}_latency"
        current_threshold = self.threshold_configs.get(threshold_key)
        
        if current_threshold:
            # Check if current threshold is too tight or too loose
            violations = sum(1 for latency in latencies if latency > current_threshold.max_value)
            violation_rate = violations / len(latencies)
            
            if violation_rate > 0.1:  # More than 10% violations
                # Threshold is too tight, recommend relaxing it
                recommended_max = p95_latency * 1.2  # Add 20% safety margin
                
                recommendation = TuningRecommendation(
                    action=TuningAction.ADJUST_THRESHOLD,
                    target=threshold_key,
                    current_value=current_threshold.max_value,
                    recommended_value=recommended_max,
                    confidence=min(1.0, violation_rate * 5),
                    reasoning=f"High violation rate ({violation_rate:.1%}) indicates threshold is too tight",
                    impact="Reduce false alarms, allow more requests to succeed",
                    priority=8
                )
                recommendations.append(recommendation)
            
            elif violation_rate < 0.01 and avg_latency < current_threshold.max_value * 0.5:
                # Threshold is too loose, recommend tightening it
                recommended_max = p95_latency * 1.1  # Tighten but keep safety margin
                
                recommendation = TuningRecommendation(
                    action=TuningAction.ADJUST_THRESHOLD,
                    target=threshold_key,
                    current_value=current_threshold.max_value,
                    recommended_value=recommended_max,
                    confidence=min(1.0, (1.0 - violation_rate) * 3),
                    reasoning=f"Very low violation rate ({violation_rate:.1%}) indicates threshold is too loose",
                    impact="Earlier detection of performance issues",
                    priority=5
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    async def _analyze_error_patterns(self,
                                    model_type: ModelType,
                                    performance_data: List[ModelPerformanceMetrics]) -> List[TuningRecommendation]:
        """Analyze error patterns and generate recommendations"""
        recommendations = []
        
        total_requests = len(performance_data)
        if total_requests == 0:
            return recommendations
        
        error_count = sum(1 for p in performance_data if not p.success)
        error_rate = error_count / total_requests
        
        # Check against global error rate threshold
        error_threshold = self.threshold_configs.get('global_error_rate')
        if error_threshold and error_rate > error_threshold.max_value:
            # Analyze error types
            error_messages = [p.error_message for p in performance_data if p.error_message]
            common_errors = self._get_most_common_errors(error_messages)
            
            recommendation = TuningRecommendation(
                action=TuningAction.ALERT_ADMIN,
                target=f"{model_type.value}_error_rate",
                current_value=error_rate,
                recommended_value=error_threshold.max_value,
                confidence=min(1.0, error_rate * 2),
                reasoning=f"High error rate ({error_rate:.1%}). Common errors: {', '.join(common_errors[:3])}",
                impact="Improve system reliability and user experience",
                priority=9
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _analyze_quality_patterns(self,
                                      model_type: ModelType,
                                      performance_data: List[ModelPerformanceMetrics]) -> List[TuningRecommendation]:
        """Analyze quality score patterns and generate recommendations"""
        recommendations = []
        
        quality_data = [p for p in performance_data if p.quality_score is not None]
        if not quality_data:
            return recommendations
        
        quality_scores = [p.quality_score for p in quality_data]
        avg_quality = statistics.mean(quality_scores)
        
        # Check against global quality threshold
        quality_threshold = self.threshold_configs.get('global_quality')
        if quality_threshold and avg_quality < quality_threshold.min_value:
            recommendation = TuningRecommendation(
                action=TuningAction.CHANGE_MODEL_ROUTING,
                target=f"{model_type.value}_quality",
                current_value=avg_quality,
                recommended_value=quality_threshold.min_value,
                confidence=min(1.0, (quality_threshold.min_value - avg_quality) * 2),
                reasoning=f"Low average quality score ({avg_quality:.3f}) below threshold",
                impact="Improve response quality by routing to higher-quality models",
                priority=7
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _tune_global_thresholds(self) -> List[TuningRecommendation]:
        """Tune global system thresholds"""
        recommendations = []
        
        # Analyze system-wide error rate
        all_models_data = []
        for model_type in ModelType:
            model_data = await self.monitor.get_recent_performance(model_type, timedelta(hours=24))
            all_models_data.extend(model_data)
        
        if all_models_data:
            total_requests = len(all_models_data)
            error_count = sum(1 for p in all_models_data if not p.success)
            global_error_rate = error_count / total_requests
            
            error_threshold = self.threshold_configs.get('global_error_rate')
            if error_threshold:
                if global_error_rate > error_threshold.warning_level:
                    recommendation = TuningRecommendation(
                        action=TuningAction.ADJUST_THRESHOLD,
                        target='global_error_rate',
                        current_value=error_threshold.max_value,
                        recommended_value=global_error_rate * 1.5,  # Increase threshold
                        confidence=0.8,
                        reasoning=f"Global error rate ({global_error_rate:.1%}) exceeds warning level",
                        impact="Reduce false alarms while maintaining monitoring effectiveness",
                        priority=6
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    async def _optimize_model_routing(self) -> List[TuningRecommendation]:
        """Optimize model routing weights based on performance"""
        recommendations = []
        
        # Get performance data for all models
        model_performances = {}
        for model_type in ModelType:
            performance_summary = await self.monitor.get_performance_summary(
                model_type, timedelta(hours=24)
            )
            if performance_summary:
                model_performances[model_type] = performance_summary
        
        if len(model_performances) < 2:
            return recommendations  # Need at least 2 models for comparison
        
        # Find best performing model for each metric
        best_latency_model = min(model_performances.items(), 
                                key=lambda x: x[1].get('avg_latency', float('inf')))[0]
        
        best_quality_model = max(model_performances.items(), 
                               key=lambda x: x[1].get('avg_quality_score', 0))[0]
        
        best_cost_model = min(model_performances.items(), 
                              key=lambda x: x[1].get('avg_cost', float('inf')))[0]
        
        # Recommend weight adjustments
        for model_type, weights in self.model_routing_weights.items():
            adjustments = {}
            
            if model_type == best_latency_model and weights['latency'] < 0.6:
                adjustments['latency'] = min(0.8, weights['latency'] + 0.2)
            
            if model_type == best_quality_model and weights['quality'] < 0.6:
                adjustments['quality'] = min(0.8, weights['quality'] + 0.2)
            
            if model_type == best_cost_model and weights['cost'] < 0.6:
                adjustments['cost'] = min(0.8, weights['cost'] + 0.2)
            
            if adjustments:
                recommendation = TuningRecommendation(
                    action=TuningAction.OPTIMIZE_CONFIG,
                    target=f"{model_type.value}_routing_weights",
                    current_value=weights,
                    recommended_value={**weights, **adjustments},
                    confidence=0.7,
                    reasoning=f"Model excels in {', '.join(adjustments.keys())}",
                    impact="Better model selection for improved overall performance",
                    priority=4
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _filter_recommendations(self, 
                             recommendations: List[TuningRecommendation]) -> List[TuningRecommendation]:
        """Filter recommendations based on confidence and impact"""
        filtered = []
        
        for rec in recommendations:
            # Apply confidence threshold
            if rec.confidence < self.config.confidence_threshold:
                continue
            
            # Check if similar recommendation is already active
            is_duplicate = any(
                self.active_tunings and
                active.action == rec.action and 
                active.target == rec.target
                for active in self.active_tunings
            )
            
            if not is_duplicate:
                filtered.append(rec)
        
        # Sort by priority
        filtered.sort(key=lambda x: x.priority, reverse=True)
        
        # Limit number of concurrent tunings
        return filtered[:self.config.max_concurrent_tunings]
    
    async def _apply_automatic_adjustments(self, 
                                        recommendations: List[TuningRecommendation]) -> None:
        """Apply automatic adjustments for high-confidence recommendations"""
        for rec in recommendations:
            if rec.confidence >= 0.9:  # Very high confidence
                try:
                    if rec.action == TuningAction.ADJUST_THRESHOLD:
                        await self._apply_threshold_adjustment(rec)
                    elif rec.action == TuningAction.OPTIMIZE_CONFIG:
                        await self._apply_routing_optimization(rec)
                    
                    self.active_tunings.append(rec)
                    logger.info(f"Applied automatic tuning: {rec.action} for {rec.target}")
                    
                except Exception as e:
                    logger.error(f"Failed to apply automatic tuning {rec.action} for {rec.target}: {e}")
    
    async def _apply_threshold_adjustment(self, rec: TuningRecommendation) -> None:
        """Apply threshold adjustment"""
        if rec.target in self.threshold_configs:
            threshold = self.threshold_configs[rec.target]
            
            if isinstance(rec.recommended_value, (int, float)):
                # Apply gradual adjustment with safety margin
                current = getattr(threshold, 'max_value', None) or getattr(threshold, 'min_value', 0)
                adjustment = (rec.recommended_value - current) * self.config.learning_rate
                new_value = current + adjustment
                
                if hasattr(threshold, 'max_value'):
                    threshold.max_value = new_value
                elif hasattr(threshold, 'min_value'):
                    threshold.min_value = new_value
                
                logger.info(f"Adjusted {rec.target} from {current} to {new_value}")
    
    async def _apply_routing_optimization(self, rec: TuningRecommendation) -> None:
        """Apply routing weight optimization"""
        if rec.target in self.model_routing_weights:
            current_weights = self.model_routing_weights[rec.target]
            recommended_weights = rec.recommended_value
            
            # Apply gradual adjustment
            for key, new_value in recommended_weights.items():
                if key in current_weights:
                    current = current_weights[key]
                    adjustment = (new_value - current) * self.config.learning_rate
                    current_weights[key] = current + adjustment
            
            logger.info(f"Optimized routing weights for {rec.target}")
    
    def _get_most_common_errors(self, error_messages: List[str], top_n: int = 5) -> List[str]:
        """Get most common error messages"""
        from collections import Counter
        
        if not error_messages:
            return []
        
        error_counter = Counter(error_messages)
        return [error for error, count in error_counter.most_common(top_n)]
    
    async def get_tuning_status(self) -> Dict[str, Any]:
        """Get current tuning status and statistics"""
        return {
            'enabled': self.config.enabled,
            'last_tuning_time': self.last_tuning_time.isoformat(),
            'active_tunings': len(self.active_tunings),
            'total_tunings_applied': len(self.tuning_history),
            'current_thresholds': {
                name: {
                    'metric': threshold.metric.value,
                    'max_value': getattr(threshold, 'max_value', None),
                    'min_value': getattr(threshold, 'min_value', None),
                    'warning_level': threshold.warning_level,
                    'critical_level': threshold.critical_level
                }
                for name, threshold in self.threshold_configs.items()
            },
            'routing_weights': {
                model.value: weights for model, weights in self.model_routing_weights.items()
            }
        }
    
    async def reset_to_defaults(self) -> None:
        """Reset all tuning configurations to defaults"""
        self.threshold_configs = self._initialize_threshold_configs()
        self.model_routing_weights = self._initialize_routing_weights()
        self.active_tunings = []
        self.tuning_history = []
        logger.info("Reset all tuning configurations to defaults")
    
    async def export_configuration(self) -> Dict[str, Any]:
        """Export current tuning configuration"""
        return {
            'thresholds': {
                name: asdict(threshold) for name, threshold in self.threshold_configs.items()
            },
            'routing_weights': {
                model.value: weights for model, weights in self.model_routing_weights.items()
            },
            'tuning_config': asdict(self.config),
            'export_time': datetime.now().isoformat()
        }
    
    async def import_configuration(self, config_data: Dict[str, Any]) -> None:
        """Import tuning configuration"""
        try:
            # Import thresholds
            if 'thresholds' in config_data:
                for name, threshold_data in config_data['thresholds'].items():
                    self.threshold_configs[name] = PerformanceThreshold(**threshold_data)
            
            # Import routing weights
            if 'routing_weights' in config_data:
                for model_name, weights in config_data['routing_weights'].items():
                    model_type = ModelType(model_name)
                    self.model_routing_weights[model_type] = weights
            
            # Import tuning config
            if 'tuning_config' in config_data:
                self.config = TuningConfiguration(**config_data['tuning_config'])
            
            logger.info("Successfully imported tuning configuration")
            
        except Exception as e:
            logger.error(f"Failed to import tuning configuration: {e}")
            raise