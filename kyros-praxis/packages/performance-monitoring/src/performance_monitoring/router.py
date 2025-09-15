import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from enum import Enum

from .types import (
    ModelType, 
    ModelPerformanceMetrics, 
    OptimizationDecision,
    PerformanceThreshold,
    PerformanceMetric
)

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    """Optimization strategies for model selection"""
    LOWEST_LATENCY = "lowest_latency"
    HIGHEST_QUALITY = "highest_quality"
    COST_EFFECTIVE = "cost_effective"
    BALANCED = "balanced"
    ADAPTIVE = "adaptive"
    LOAD_BALANCED = "load_balanced"


@dataclass
class ModelCapabilities:
    """Model capability profiles"""
    model_type: ModelType
    max_tokens: int
    context_length: int
    supports_vision: bool
    supports_code: bool
    creativity_score: float  # 0.0 to 1.0
    reasoning_score: float  # 0.0 to 1.0
    speed_score: float  # 0.0 to 1.0
    cost_per_1k_tokens: float


class ModelRouter:
    """Intelligent model routing based on performance optimization"""
    
    def __init__(self):
        self.model_capabilities = self._initialize_model_capabilities()
        self.strategy_weights = {
            OptimizationStrategy.LOWEST_LATENCY: {"latency": 0.7, "quality": 0.2, "cost": 0.1},
            OptimizationStrategy.HIGHEST_QUALITY: {"latency": 0.1, "quality": 0.8, "cost": 0.1},
            OptimizationStrategy.COST_EFFECTIVE: {"latency": 0.2, "quality": 0.3, "cost": 0.5},
            OptimizationStrategy.BALANCED: {"latency": 0.33, "quality": 0.33, "cost": 0.34},
            OptimizationStrategy.ADAPTIVE: {"latency": 0.4, "quality": 0.4, "cost": 0.2}
        }
        self.performance_cache = {}
        self.cache_ttl = timedelta(minutes=5)
        self.last_cache_update = {}
    
    def _initialize_model_capabilities(self) -> Dict[ModelType, ModelCapabilities]:
        """Initialize model capability profiles"""
        return {
            ModelType.GPT_4: ModelCapabilities(
                model_type=ModelType.GPT_4,
                max_tokens=8192,
                context_length=128000,
                supports_vision=True,
                supports_code=True,
                creativity_score=0.85,
                reasoning_score=0.95,
                speed_score=0.6,
                cost_per_1k_tokens=0.03
            ),
            ModelType.GPT_3_5: ModelCapabilities(
                model_type=ModelType.GPT_3_5,
                max_tokens=4096,
                context_length=16385,
                supports_vision=False,
                supports_code=True,
                creativity_score=0.7,
                reasoning_score=0.75,
                speed_score=0.9,
                cost_per_1k_tokens=0.0015
            ),
            ModelType.CLAUDE: ModelCapabilities(
                model_type=ModelType.CLAUDE,
                max_tokens=4096,
                context_length=100000,
                supports_vision=True,
                supports_code=True,
                creativity_score=0.9,
                reasoning_score=0.9,
                speed_score=0.7,
                cost_per_1k_tokens=0.015
            ),
            ModelType.GEMINI: ModelCapabilities(
                model_type=ModelType.GEMINI,
                max_tokens=8192,
                context_length=32000,
                supports_vision=True,
                supports_code=True,
                creativity_score=0.8,
                reasoning_score=0.85,
                speed_score=0.8,
                cost_per_1k_tokens=0.00125
            ),
            ModelType.LOCAL_LLAMA: ModelCapabilities(
                model_type=ModelType.LOCAL_LLAMA,
                max_tokens=2048,
                context_length=4096,
                supports_vision=False,
                supports_code=False,
                creativity_score=0.5,
                reasoning_score=0.6,
                speed_score=0.4,
                cost_per_1k_tokens=0.0
            )
        }
    
    async def select_model(self,
                          request_features: Dict[str, Any],
                          available_models: List[ModelType],
                          strategy: OptimizationStrategy = OptimizationStrategy.ADAPTIVE,
                          performance_data: Optional[List[ModelPerformanceMetrics]] = None) -> OptimizationDecision:
        """
        Select the optimal model based on request features and optimization strategy
        """
        request_id = request_features.get('request_id', str(hash(str(request_features))))
        
        # Filter available models based on requirements
        eligible_models = self._filter_eligible_models(request_features, available_models)
        
        if not eligible_models:
            logger.warning("No eligible models found for request")
            return OptimizationDecision(
                request_id=request_id,
                selected_model=available_models[0] if available_models else ModelType.GPT_3_5,
                confidence_score=0.1,
                expected_improvement=0.0,
                reasoning="No eligible models found, falling back to default",
                timestamp=datetime.now()
            )
        
        # Calculate scores for each eligible model
        model_scores = []
        for model_type in eligible_models:
            score = await self._calculate_model_score(
                model_type, request_features, strategy, performance_data
            )
            model_scores.append((model_type, score))
        
        # Select best model
        best_model, best_score = max(model_scores, key=lambda x: x[1]['total_score'])
        
        # Calculate confidence and expected improvement
        confidence = self._calculate_confidence(model_scores, best_score)
        expected_improvement = self._calculate_expected_improvement(model_scores, best_score)
        
        reasoning = self._generate_reasoning(best_model, best_score, strategy, request_features)
        
        return OptimizationDecision(
            request_id=request_id,
            selected_model=best_model,
            confidence_score=confidence,
            expected_improvement=expected_improvement,
            reasoning=reasoning,
            timestamp=datetime.now()
        )
    
    def _filter_eligible_models(self, 
                               request_features: Dict[str, Any],
                               available_models: List[ModelType]) -> List[ModelType]:
        """Filter models based on request requirements"""
        eligible = []
        
        for model_type in available_models:
            capabilities = self.model_capabilities.get(model_type)
            if not capabilities:
                continue
            
            # Check token requirements
            estimated_tokens = request_features.get('estimated_tokens', 0)
            if estimated_tokens > capabilities.max_tokens:
                continue
            
            # Check context length requirements
            context_length = request_features.get('context_length', 0)
            if context_length > capabilities.context_length:
                continue
            
            # Check for vision support
            if request_features.get('requires_vision', False) and not capabilities.supports_vision:
                continue
            
            # Check for code support
            if request_features.get('requires_code', False) and not capabilities.supports_code:
                continue
            
            eligible.append(model_type)
        
        return eligible
    
    async def _calculate_model_score(self,
                                   model_type: ModelType,
                                   request_features: Dict[str, Any],
                                   strategy: OptimizationStrategy,
                                   performance_data: Optional[List[ModelPerformanceMetrics]] = None) -> Dict[str, float]:
        """Calculate optimization score for a model"""
        capabilities = self.model_capabilities[model_type]
        
        # Get performance metrics
        performance_score = await self._get_performance_score(model_type, performance_data)
        
        # Calculate capability match score
        capability_score = self._calculate_capability_match(capabilities, request_features)
        
        # Calculate resource utilization score
        resource_score = self._calculate_resource_score(model_type)
        
        # Get strategy weights
        weights = self.strategy_weights.get(strategy, self.strategy_weights[OptimizationStrategy.BALANCED])
        
        # Calculate weighted total score
        total_score = (
            performance_score['latency_score'] * weights['latency'] +
            performance_score['quality_score'] * weights['quality'] +
            performance_score['cost_score'] * weights['cost'] +
            capability_score * 0.2 +  # 20% weight for capability matching
            resource_score * 0.1       # 10% weight for resource utilization
        )
        
        return {
            'total_score': total_score,
            'latency_score': performance_score['latency_score'],
            'quality_score': performance_score['quality_score'],
            'cost_score': performance_score['cost_score'],
            'capability_score': capability_score,
            'resource_score': resource_score,
            'performance_score': performance_score['overall']
        }
    
    async def _get_performance_score(self, 
                                   model_type: ModelType,
                                   performance_data: Optional[List[ModelPerformanceMetrics]] = None) -> Dict[str, float]:
        """Get performance-based scores for a model"""
        cache_key = f"performance_score:{model_type.value}"
        
        # Check cache first
        if cache_key in self.performance_cache:
            last_update = self.last_cache_update.get(cache_key)
            if last_update and datetime.now() - last_update < self.cache_ttl:
                return self.performance_cache[cache_key]
        
        if performance_data:
            model_metrics = [m for m in performance_data if m.model_type == model_type]
        else:
            model_metrics = []  # Will use default scores
        
        if model_metrics:
            # Calculate actual performance scores
            successful_metrics = [m for m in model_metrics if m.success]
            
            if successful_metrics:
                avg_latency = np.mean([m.execution_time for m in successful_metrics])
                avg_quality = np.mean([m.quality_score for m in successful_metrics if m.quality_score])
                avg_cost = np.mean([m.cost for m in successful_metrics if m.cost])
                error_rate = 1 - (len(successful_metrics) / len(model_metrics))
            else:
                avg_latency = 30.0  # Default high latency
                avg_quality = 0.5
                avg_cost = 0.01
                error_rate = 1.0
        else:
            # Use capability-based estimates
            capabilities = self.model_capabilities[model_type]
            avg_latency = 10.0 / capabilities.speed_score  # Inverse of speed
            avg_quality = (capabilities.creativity_score + capabilities.reasoning_score) / 2
            avg_cost = capabilities.cost_per_1k_tokens
            error_rate = 0.05  # Default 5% error rate
        
        # Normalize scores (0.0 to 1.0, where 1.0 is best)
        latency_score = max(0, 1 - (avg_latency / 60.0))  # Normalize to 60 seconds max
        quality_score = avg_quality
        cost_score = max(0, 1 - (avg_cost / 0.1))  # Normalize to $0.10 max
        error_score = max(0, 1 - error_rate)
        
        overall_score = (latency_score + quality_score + cost_score + error_score) / 4
        
        result = {
            'latency_score': latency_score,
            'quality_score': quality_score,
            'cost_score': cost_score,
            'error_score': error_score,
            'overall': overall_score
        }
        
        # Cache the result
        self.performance_cache[cache_key] = result
        self.last_cache_update[cache_key] = datetime.now()
        
        return result
    
    def _calculate_capability_match(self, 
                                  capabilities: ModelCapabilities,
                                  request_features: Dict[str, Any]) -> float:
        """Calculate how well model capabilities match request requirements"""
        match_score = 1.0
        
        # Creativity requirement
        required_creativity = request_features.get('creativity_requirement', 0.5)
        if capabilities.creativity_score < required_creativity:
            match_score *= 0.5
        
        # Reasoning requirement
        required_reasoning = request_features.get('reasoning_requirement', 0.5)
        if capabilities.reasoning_score < required_reasoning:
            match_score *= 0.5
        
        # Token efficiency
        estimated_tokens = request_features.get('estimated_tokens', 0)
        if estimated_tokens > 0:
            token_efficiency = min(1.0, capabilities.max_tokens / estimated_tokens)
            match_score *= token_efficiency
        
        return match_score
    
    def _calculate_resource_score(self, model_type: ModelType) -> float:
        """Calculate resource utilization score"""
        # For now, this is a simple heuristic
        # Local models get higher resource scores since they don't use external APIs
        if model_type == ModelType.LOCAL_LLAMA:
            return 0.8
        else:
            return 0.6  # Cloud models have external resource usage
    
    def _calculate_confidence(self, 
                            model_scores: List[Tuple[ModelType, Dict]],
                            best_score: Dict) -> float:
        """Calculate confidence in the model selection decision"""
        if len(model_scores) <= 1:
            return 1.0
        
        scores = [score[1]['total_score'] for score in model_scores]
        best_total = best_score['total_score']
        second_best = sorted(scores)[-2] if len(scores) > 1 else 0
        
        # Confidence based on how much better the best model is
        if second_best == 0:
            return 1.0
        
        ratio = best_total / second_best
        confidence = min(1.0, (ratio - 1.0) * 2)  # Scale difference
        
        return confidence
    
    def _calculate_expected_improvement(self,
                                     model_scores: List[Tuple[ModelType, Dict]],
                                     best_score: Dict) -> float:
        """Calculate expected improvement over average performance"""
        if not model_scores:
            return 0.0
        
        avg_score = np.mean([score[1]['total_score'] for score in model_scores])
        best_total = best_score['total_score']
        
        improvement = (best_total - avg_score) / avg_score if avg_score > 0 else 0
        return max(0, improvement)
    
    def _generate_reasoning(self, 
                           model_type: ModelType,
                           score: Dict,
                           strategy: OptimizationStrategy,
                           request_features: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for model selection"""
        capabilities = self.model_capabilities[model_type]
        
        reasoning_parts = []
        
        # Strategy-based reasoning
        if strategy == OptimizationStrategy.LOWEST_LATENCY:
            reasoning_parts.append(f"Selected for speed: {score['latency_score']:.2f} latency score")
        elif strategy == OptimizationStrategy.HIGHEST_QUALITY:
            reasoning_parts.append(f"Selected for quality: {score['quality_score']:.2f} quality score")
        elif strategy == OptimizationStrategy.COST_EFFECTIVE:
            reasoning_parts.append(f"Selected for cost efficiency: {score['cost_score']:.2f} cost score")
        
        # Capability-based reasoning
        if request_features.get('requires_vision') and capabilities.supports_vision:
            reasoning_parts.append("Supports vision input")
        if request_features.get('requires_code') and capabilities.supports_code:
            reasoning_parts.append("Strong code generation capabilities")
        
        # Performance-based reasoning
        if score['performance_score'] > 0.8:
            reasoning_parts.append("Excellent historical performance")
        elif score['performance_score'] > 0.6:
            reasoning_parts.append("Good historical performance")
        
        return "; ".join(reasoning_parts) if reasoning_parts else "Default selection based on overall scores"
    
    async def update_model_capabilities(self, 
                                      model_type: ModelType,
                                      performance_metrics: List[ModelPerformanceMetrics]):
        """Update model capability estimates based on recent performance"""
        if not performance_metrics:
            return
        
        successful_metrics = [m for m in performance_metrics if m.success]
        if not successful_metrics:
            return
        
        # Update speed score based on actual performance
        avg_latency = np.mean([m.execution_time for m in successful_metrics])
        capabilities = self.model_capabilities[model_type]
        
        # Adjust speed score based on observed latency
        observed_speed = max(0.1, 1.0 / (avg_latency / 10.0))  # Normalize to 10 seconds baseline
        capabilities.speed_score = (capabilities.speed_score + observed_speed) / 2
        
        logger.info(f"Updated {model_type.value} capabilities: speed_score={capabilities.speed_score:.2f}")
    
    def get_model_recommendations(self, 
                                 request_features: Dict[str, Any],
                                 available_models: List[ModelType],
                                 top_n: int = 3) -> List[OptimizationDecision]:
        """Get top N model recommendations"""
        if not available_models:
            return []
        
        # Calculate scores for all models
        model_scores = []
        for model_type in available_models:
            try:
                score_dict = asyncio.run(self._calculate_model_score(
                    model_type, request_features, OptimizationStrategy.BALANCED
                ))
                model_scores.append((model_type, score_dict))
            except Exception as e:
                logger.warning(f"Error calculating score for {model_type}: {e}")
                continue
        
        # Sort by score and get top N
        model_scores.sort(key=lambda x: x[1]['total_score'], reverse=True)
        top_models = model_scores[:top_n]
        
        recommendations = []
        for i, (model_type, score_dict) in enumerate(top_models):
            request_id = f"rec_{i}_{hash(str(request_features))}"
            confidence = score_dict['total_score']
            expected_improvement = score_dict['total_score'] * 0.1  # Simplified
            
            recommendations.append(OptimizationDecision(
                request_id=request_id,
                selected_model=model_type,
                confidence_score=confidence,
                expected_improvement=expected_improvement,
                reasoning=f"Recommendation #{i+1} with score {score_dict['total_score']:.2f}",
                timestamp=datetime.now()
            ))
        
        return recommendations