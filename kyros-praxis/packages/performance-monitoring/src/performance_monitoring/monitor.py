import json
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from .types import (
    PerformanceMonitor, 
    ModelPerformanceMetrics, 
    SystemResourceMetrics,
    PerformanceThreshold,
    ModelType,
    PerformanceMetric
)
from .storage import MetricsStorage


logger = logging.getLogger(__name__)


class RedisPerformanceMonitor(PerformanceMonitor):
    """Redis-based performance monitoring system"""
    
    def __init__(self, 
                 redis_url: str = "redis://localhost:6379",
                 storage: Optional[MetricsStorage] = None):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.storage = storage
        self._initialized = False
        
    async def initialize(self):
        """Initialize Redis connection"""
        if not self._initialized:
            self.redis = redis.from_url(self.redis_url)
            self._initialized = True
            logger.info("Performance monitor initialized")
    
    async def record_model_performance(self, metrics: ModelPerformanceMetrics) -> None:
        """Record model performance metrics"""
        if not self.redis:
            await self.initialize()
        
        # Store in Redis with TTL (30 days)
        key = f"model_performance:{metrics.model_type.value}:{metrics.timestamp.isoformat()}"
        value = json.dumps({
            'model_id': metrics.model_id,
            'execution_time': metrics.execution_time,
            'input_tokens': metrics.input_tokens,
            'output_tokens': metrics.output_tokens,
            'success': metrics.success,
            'error_message': metrics.error_message,
            'cost': metrics.cost,
            'quality_score': metrics.quality_score,
            'cpu_usage': metrics.cpu_usage,
            'memory_usage': metrics.memory_usage,
            'user_id': metrics.user_id,
            'session_id': metrics.session_id,
            'request_id': metrics.request_id
        })
        
        await self.redis.setex(key, 2592000, value)  # 30 days TTL
        
        # Add to sorted set for time-based queries
        score = metrics.timestamp.timestamp()
        await self.redis.zadd(f"model_metrics:{metrics.model_type.value}", {key: score})
        
        # Store in persistent storage if available
        if self.storage:
            await self.storage.store_metrics(metrics)
        
        logger.debug(f"Recorded performance metrics for {metrics.model_type.value}")
    
    async def record_system_metrics(self, metrics: SystemResourceMetrics) -> None:
        """Record system resource metrics"""
        if not self.redis:
            await self.initialize()
        
        key = f"system_metrics:{metrics.timestamp.isoformat()}"
        value = json.dumps({
            'cpu_percent': metrics.cpu_percent,
            'memory_percent': metrics.memory_percent,
            'disk_usage': metrics.disk_usage,
            'network_io_sent': metrics.network_io_sent,
            'network_io_recv': metrics.network_io_recv,
            'active_connections': metrics.active_connections,
            'queue_size': metrics.queue_size
        })
        
        await self.redis.setex(key, 86400, value)  # 1 day TTL
        
        # Add to sorted set for time-based queries
        score = metrics.timestamp.timestamp()
        await self.redis.zadd("system_metrics", {key: score})
        
        logger.debug("Recorded system metrics")
    
    async def get_recent_performance(self, 
                                   model_type: ModelType,
                                   time_window: timedelta) -> List[ModelPerformanceMetrics]:
        """Get recent performance data for a model"""
        if not self.redis:
            await self.initialize()
        
        now = datetime.now()
        min_score = (now - time_window).timestamp()
        max_score = now.timestamp()
        
        keys = await self.redis.zrangebyscore(
            f"model_metrics:{model_type.value}", 
            min_score, 
            max_score
        )
        
        metrics = []
        for key in keys:
            value = await self.redis.get(key)
            if value:
                data = json.loads(value)
                timestamp = datetime.fromisoformat(key.split(":")[2])
                metric = ModelPerformanceMetrics(
                    model_id=data['model_id'],
                    model_type=model_type,
                    timestamp=timestamp,
                    execution_time=data['execution_time'],
                    input_tokens=data['input_tokens'],
                    output_tokens=data['output_tokens'],
                    success=data['success'],
                    error_message=data.get('error_message'),
                    cost=data.get('cost'),
                    quality_score=data.get('quality_score'),
                    cpu_usage=data.get('cpu_usage'),
                    memory_usage=data.get('memory_usage'),
                    user_id=data.get('user_id'),
                    session_id=data.get('session_id'),
                    request_id=data['request_id']
                )
                metrics.append(metric)
        
        return metrics
    
    async def get_performance_summary(self, 
                                     model_type: ModelType,
                                     time_window: timedelta) -> Dict[str, float]:
        """Get performance summary statistics"""
        metrics = await self.get_recent_performance(model_type, time_window)
        
        if not metrics:
            return {}
        
        successful_metrics = [m for m in metrics if m.success]
        
        if not successful_metrics:
            return {
                'total_requests': len(metrics),
                'success_rate': 0.0,
                'avg_latency': 0.0,
                'error_rate': 1.0
            }
        
        execution_times = [m.execution_time for m in successful_metrics]
        costs = [m.cost for m in successful_metrics if m.cost is not None]
        quality_scores = [m.quality_score for m in successful_metrics if m.quality_score is not None]
        
        return {
            'total_requests': len(metrics),
            'successful_requests': len(successful_metrics),
            'success_rate': len(successful_metrics) / len(metrics),
            'avg_latency': sum(execution_times) / len(execution_times),
            'min_latency': min(execution_times),
            'max_latency': max(execution_times),
            'avg_cost': sum(costs) / len(costs) if costs else 0.0,
            'avg_quality_score': sum(quality_scores) / len(quality_scores) if quality_scores else 0.0,
            'p95_latency': sorted(execution_times)[int(0.95 * len(execution_times))],
            'p99_latency': sorted(execution_times)[int(0.99 * len(execution_times))],
            'error_rate': 1.0 - (len(successful_metrics) / len(metrics))
        }
    
    async def check_thresholds(self, metrics: ModelPerformanceMetrics) -> List[PerformanceThreshold]:
        """Check if metrics exceed any thresholds"""
        # This would typically load thresholds from configuration
        # For now, we'll use default thresholds
        thresholds = [
            PerformanceThreshold(
                metric=PerformanceMetric.LATENCY,
                max_value=30.0,  # 30 seconds
                warning_level=15.0,
                critical_level=25.0
            ),
            PerformanceThreshold(
                metric=PerformanceMetric.ERROR_RATE,
                max_value=0.1,  # 10%
                warning_level=0.05,
                critical_level=0.08
            ),
            PerformanceThreshold(
                metric=PerformanceMetric.QUALITY,
                min_value=0.7,  # 70% quality
                warning_level=0.8,
                critical_level=0.75
            )
        ]
        
        violated_thresholds = []
        performance_summary = await self.get_performance_summary(
            metrics.model_type, 
            timedelta(hours=1)
        )
        
        for threshold in thresholds:
            if threshold.metric == PerformanceMetric.LATENCY:
                if performance_summary.get('avg_latency', 0) > threshold.max_value:
                    violated_thresholds.append(threshold)
            elif threshold.metric == PerformanceMetric.ERROR_RATE:
                if performance_summary.get('error_rate', 0) > threshold.max_value:
                    violated_thresholds.append(threshold)
            elif threshold.metric == PerformanceMetric.QUALITY:
                if performance_summary.get('avg_quality_score', 1.0) < threshold.min_value:
                    violated_thresholds.append(threshold)
        
        return violated_thresholds
    
    async def get_real_time_metrics(self, model_type: ModelType) -> Dict[str, Any]:
        """Get real-time performance metrics for dashboard"""
        summary_1h = await self.get_performance_summary(model_type, timedelta(hours=1))
        summary_24h = await self.get_performance_summary(model_type, timedelta(days=1))
        
        return {
            'model_type': model_type.value,
            'last_hour': summary_1h,
            'last_24_hours': summary_24h,
            'timestamp': datetime.now().isoformat()
        }
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            self._initialized = False