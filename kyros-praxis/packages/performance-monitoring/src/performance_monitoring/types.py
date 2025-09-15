from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json
import time
import psutil
import threading
import uuid


class ModelType(str, Enum):
    GPT_4 = "gpt-4"
    GPT_3_5 = "gpt-3.5-turbo"
    CLAUDE = "claude-3-sonnet"
    GEMINI = "gemini-pro"
    LOCAL_LLAMA = "local-llama"


class PerformanceMetric(str, Enum):
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    ERROR_RATE = "error_rate"
    COST = "cost"
    QUALITY = "quality"
    RESOURCE_USAGE = "resource_usage"


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a model execution"""
    model_id: str
    model_type: ModelType
    timestamp: datetime
    execution_time: float  # seconds
    input_tokens: int
    output_tokens: int
    success: bool
    error_message: Optional[str] = None
    cost: Optional[float] = None
    quality_score: Optional[float] = None  # 0.0 to 1.0
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: str


@dataclass
class SystemResourceMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io_sent: int
    network_io_recv: int
    active_connections: int
    queue_size: int


@dataclass
class PerformanceThreshold:
    """Performance threshold configuration"""
    metric: PerformanceMetric
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    warning_level: Optional[float] = None
    critical_level: Optional[float] = None
    model_type: Optional[ModelType] = None
    enabled: bool = True


@dataclass
class OptimizationDecision:
    """Decision made by the optimization algorithm"""
    request_id: str
    selected_model: ModelType
    confidence_score: float  # 0.0 to 1.0
    expected_improvement: float
    reasoning: str
    timestamp: datetime


class PerformanceMonitor(ABC):
    """Abstract base class for performance monitoring"""
    
    @abstractmethod
    async def record_model_performance(self, metrics: ModelPerformanceMetrics) -> None:
        """Record model performance metrics"""
        pass
    
    @abstractmethod
    async def record_system_metrics(self, metrics: SystemResourceMetrics) -> None:
        """Record system resource metrics"""
        pass
    
    @abstractmethod
    async def get_recent_performance(self, 
                                   model_type: ModelType,
                                   time_window: timedelta) -> List[ModelPerformanceMetrics]:
        """Get recent performance data for a model"""
        pass
    
    @abstractmethod
    async def get_performance_summary(self, 
                                     model_type: ModelType,
                                     time_window: timedelta) -> Dict[str, float]:
        """Get performance summary statistics"""
        pass
    
    @abstractmethod
    async def check_thresholds(self, metrics: ModelPerformanceMetrics) -> List[PerformanceThreshold]:
        """Check if metrics exceed any thresholds"""
        pass