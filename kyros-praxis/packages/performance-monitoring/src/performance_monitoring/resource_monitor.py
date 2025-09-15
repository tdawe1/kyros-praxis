import asyncio
import psutil
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import json
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
import numpy as np

from .types import SystemResourceMetrics, ModelPerformanceMetrics, ModelType

logger = logging.getLogger(__name__)


class ResourceType(str, Enum):
    """Types of system resources"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"
    CUSTOM = "custom"


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class ResourceAlert:
    """Resource usage alert"""
    resource_type: ResourceType
    current_value: float
    threshold_value: float
    alert_level: AlertLevel
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class ResourceUsagePattern:
    """Identified resource usage pattern"""
    pattern_type: str  # e.g., "spike", "gradual_increase", "cyclical"
    resource_type: ResourceType
    start_time: datetime
    end_time: Optional[datetime]
    severity: float  # 0.0 to 1.0
    description: str
    recommended_actions: List[str]


@dataclass
class ScalingDecision:
    """Decision about resource scaling"""
    action: str  # "scale_up", "scale_down", "no_change"
    resource_type: ResourceType
    current_capacity: float
    recommended_capacity: float
    reasoning: str
    confidence: float  # 0.0 to 1.0
    expected_impact: str


class ResourceMonitor:
    """Real-time system resource monitoring and optimization"""
    
    def __init__(self,
                 monitor_interval_seconds: int = 5,
                 alert_thresholds: Optional[Dict[str, Dict]] = None,
                 enable_gpu_monitoring: bool = False):
        self.monitor_interval = monitor_interval_seconds
        self.enable_gpu = enable_gpu_monitoring
        
        # Alert thresholds (percentage-based)
        self.alert_thresholds = alert_thresholds or {
            'cpu': {'warning': 70, 'critical': 85, 'emergency': 95},
            'memory': {'warning': 75, 'critical': 90, 'emergency': 95},
            'disk': {'warning': 80, 'critical': 90, 'emergency': 95},
            'network': {'warning': 80, 'critical': 90, 'emergency': 95}
        }
        
        self.is_running = False
        self.monitor_thread = None
        self.resource_history = []
        self.alerts = []
        self.patterns = []
        self.callbacks = {
            'on_alert': [],
            'on_pattern_detected': [],
            'on_scaling_decision': []
        }
        
        # Initialize GPU monitoring if available
        self.gpu_available = self._check_gpu_availability()
        
    def _check_gpu_availability(self) -> bool:
        """Check if GPU monitoring is available"""
        try:
            import GPUtil
            return len(GPUtil.getGPUs()) > 0
        except ImportError:
            logger.info("GPUtil not available, GPU monitoring disabled")
            return False
        except Exception as e:
            logger.warning(f"GPU check failed: {e}")
            return False
    
    async def start_monitoring(self) -> None:
        """Start resource monitoring"""
        if self.is_running:
            logger.warning("Resource monitoring is already running")
            return
        
        self.is_running = True
        logger.info(f"Starting resource monitoring with {self.monitor_interval}s interval")
        
        # Start monitoring in a separate thread
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop resource monitoring"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Resource monitoring stopped")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop running in separate thread"""
        while self.is_running:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                
                # Store metrics
                self.resource_history.append(metrics)
                
                # Keep only last 1000 entries to prevent memory issues
                if len(self.resource_history) > 1000:
                    self.resource_history = self.resource_history[-1000:]
                
                # Check for alerts
                alerts = self._check_alerts(metrics)
                for alert in alerts:
                    self.alerts.append(alert)
                    self._trigger_callbacks('on_alert', alert)
                
                # Analyze patterns
                patterns = self._analyze_patterns()
                for pattern in patterns:
                    self.patterns.append(pattern)
                    self._trigger_callbacks('on_pattern_detected', pattern)
                
                # Check scaling decisions
                scaling_decision = self._evaluate_scaling()
                if scaling_decision:
                    self._trigger_callbacks('on_scaling_decision', scaling_decision)
                
                time.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitor_interval)
    
    def _collect_system_metrics(self) -> SystemResourceMetrics:
        """Collect current system resource metrics"""
        timestamp = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # Network metrics
        network = psutil.net_io_counters()
        network_io_sent = network.bytes_sent
        network_io_recv = network.bytes_recv
        
        # Get active connections (simplified)
        try:
            connections = len(psutil.net_connections())
        except:
            connections = 0
        
        # Queue size (simplified - would need actual queue monitoring)
        queue_size = self._estimate_queue_size()
        
        return SystemResourceMetrics(
            timestamp=timestamp,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_usage=disk_usage,
            network_io_sent=network_io_sent,
            network_io_recv=network_io_recv,
            active_connections=connections,
            queue_size=queue_size
        )
    
    def _estimate_queue_size(self) -> int:
        """Estimate current request queue size"""
        # This is a simplified implementation
        # In a real system, this would integrate with the actual request queue
        if self.resource_history:
            recent_metrics = self.resource_history[-10:]  # Last 10 measurements
            if recent_metrics:
                avg_cpu = statistics.mean([m.cpu_percent for m in recent_metrics])
                avg_memory = statistics.mean([m.memory_percent for m in recent_metrics])
                
                # Simple heuristic: higher resource usage suggests more queued work
                load_factor = (avg_cpu + avg_memory) / 200
                return int(load_factor * 100)  # Scale to reasonable queue size
        
        return 0
    
    def _check_alerts(self, metrics: SystemResourceMetrics) -> List[ResourceAlert]:
        """Check for resource usage alerts"""
        alerts = []
        timestamp = datetime.now()
        
        # Check CPU
        if metrics.cpu_percent > self.alert_thresholds['cpu']['emergency']:
            alerts.append(ResourceAlert(
                resource_type=ResourceType.CPU,
                current_value=metrics.cpu_percent,
                threshold_value=self.alert_thresholds['cpu']['emergency'],
                alert_level=AlertLevel.EMERGENCY,
                message=f"Emergency CPU usage: {metrics.cpu_percent:.1f}%",
                timestamp=timestamp
            ))
        elif metrics.cpu_percent > self.alert_thresholds['cpu']['critical']:
            alerts.append(ResourceAlert(
                resource_type=ResourceType.CPU,
                current_value=metrics.cpu_percent,
                threshold_value=self.alert_thresholds['cpu']['critical'],
                alert_level=AlertLevel.CRITICAL,
                message=f"Critical CPU usage: {metrics.cpu_percent:.1f}%",
                timestamp=timestamp
            ))
        elif metrics.cpu_percent > self.alert_thresholds['cpu']['warning']:
            alerts.append(ResourceAlert(
                resource_type=ResourceType.CPU,
                current_value=metrics.cpu_percent,
                threshold_value=self.alert_thresholds['cpu']['warning'],
                alert_level=AlertLevel.WARNING,
                message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                timestamp=timestamp
            ))
        
        # Check Memory
        if metrics.memory_percent > self.alert_thresholds['memory']['emergency']:
            alerts.append(ResourceAlert(
                resource_type=ResourceType.MEMORY,
                current_value=metrics.memory_percent,
                threshold_value=self.alert_thresholds['memory']['emergency'],
                alert_level=AlertLevel.EMERGENCY,
                message=f"Emergency memory usage: {metrics.memory_percent:.1f}%",
                timestamp=timestamp
            ))
        elif metrics.memory_percent > self.alert_thresholds['memory']['critical']:
            alerts.append(ResourceAlert(
                resource_type=ResourceType.MEMORY,
                current_value=metrics.memory_percent,
                threshold_value=self.alert_thresholds['memory']['critical'],
                alert_level=AlertLevel.CRITICAL,
                message=f"Critical memory usage: {metrics.memory_percent:.1f}%",
                timestamp=timestamp
            ))
        elif metrics.memory_percent > self.alert_thresholds['memory']['warning']:
            alerts.append(ResourceAlert(
                resource_type=ResourceType.MEMORY,
                current_value=metrics.memory_percent,
                threshold_value=self.alert_thresholds['memory']['warning'],
                alert_level=AlertLevel.WARNING,
                message=f"High memory usage: {metrics.memory_percent:.1f}%",
                timestamp=timestamp
            ))
        
        # Check Disk
        if metrics.disk_usage > self.alert_thresholds['disk']['emergency']:
            alerts.append(ResourceAlert(
                resource_type=ResourceType.DISK,
                current_value=metrics.disk_usage,
                threshold_value=self.alert_thresholds['disk']['emergency'],
                alert_level=AlertLevel.EMERGENCY,
                message=f"Emergency disk usage: {metrics.disk_usage:.1f}%",
                timestamp=timestamp
            ))
        
        return alerts
    
    def _analyze_patterns(self) -> List[ResourceUsagePattern]:
        """Analyze resource usage patterns"""
        patterns = []
        
        if len(self.resource_history) < 20:  # Need enough data for pattern analysis
            return patterns
        
        # Analyze different patterns
        patterns.extend(self._detect_spikes())
        patterns.extend(self._detect_gradual_increases())
        patterns.extend(self._detect_cyclical_patterns())
        
        return patterns
    
    def _detect_spikes(self) -> List[ResourceUsagePattern]:
        """Detect sudden resource usage spikes"""
        patterns = []
        
        if len(self.resource_history) < 5:
            return patterns
        
        # Check for spikes in the last 5 measurements
        recent = self.resource_history[-5:]
        previous = self.resource_history[-10:-5] if len(self.resource_history) >= 10 else []
        
        if not previous:
            return patterns
        
        # CPU spike detection
        recent_cpu = [m.cpu_percent for m in recent]
        previous_cpu = [m.cpu_percent for m in previous]
        
        if statistics.mean(recent_cpu) > statistics.mean(previous_cpu) * 1.5:
            patterns.append(ResourceUsagePattern(
                pattern_type="cpu_spike",
                resource_type=ResourceType.CPU,
                start_time=recent[0].timestamp,
                end_time=recent[-1].timestamp,
                severity=min(1.0, statistics.mean(recent_cpu) / 100),
                description=f"CPU spike detected: {statistics.mean(recent_cpu):.1f}% average vs {statistics.mean(previous_cpu):.1f}% baseline",
                recommended_actions=["Investigate processes causing high CPU", "Consider scaling up resources"]
            ))
        
        # Memory spike detection
        recent_memory = [m.memory_percent for m in recent]
        previous_memory = [m.memory_percent for m in previous]
        
        if statistics.mean(recent_memory) > statistics.mean(previous_memory) * 1.3:
            patterns.append(ResourceUsagePattern(
                pattern_type="memory_spike",
                resource_type=ResourceType.MEMORY,
                start_time=recent[0].timestamp,
                end_time=recent[-1].timestamp,
                severity=min(1.0, statistics.mean(recent_memory) / 100),
                description=f"Memory spike detected: {statistics.mean(recent_memory):.1f}% average vs {statistics.mean(previous_memory):.1f}% baseline",
                recommended_actions=["Check for memory leaks", "Restart affected services", "Add more memory"]
            ))
        
        return patterns
    
    def _detect_gradual_increases(self) -> List[ResourceUsagePattern]:
        """Detect gradual resource usage increases over time"""
        patterns = []
        
        if len(self.resource_history) < 30:  # Need 30 data points for trend analysis
            return patterns
        
        # Analyze last 30 minutes of data
        recent_data = self.resource_history[-30:]
        
        # CPU trend analysis
        cpu_values = [m.cpu_percent for m in recent_data]
        cpu_trend = self._calculate_trend(cpu_values)
        
        if cpu_trend > 0.1:  # 10% increase over the period
            patterns.append(ResourceUsagePattern(
                pattern_type="gradual_cpu_increase",
                resource_type=ResourceType.CPU,
                start_time=recent_data[0].timestamp,
                end_time=recent_data[-1].timestamp,
                severity=min(1.0, cpu_trend * 2),
                description=f"Gradual CPU increase detected: {cpu_trend:.1%} growth rate",
                recommended_actions=["Monitor for continued growth", "Plan for resource scaling", "Optimize application performance"]
            ))
        
        # Memory trend analysis
        memory_values = [m.memory_percent for m in recent_data]
        memory_trend = self._calculate_trend(memory_values)
        
        if memory_trend > 0.1:
            patterns.append(ResourceUsagePattern(
                pattern_type="gradual_memory_increase",
                resource_type=ResourceType.MEMORY,
                start_time=recent_data[0].timestamp,
                end_time=recent_data[-1].timestamp,
                severity=min(1.0, memory_trend * 2),
                description=f"Gradual memory increase detected: {memory_trend:.1%} growth rate",
                recommended_actions=["Investigate for memory leaks", "Monitor application health", "Plan memory scaling"]
            ))
        
        return patterns
    
    def _detect_cyclical_patterns(self) -> List[ResourceUsagePattern]:
        """Detect cyclical resource usage patterns"""
        patterns = []
        
        if len(self.resource_history) < 100:  # Need more data for cyclical analysis
            return patterns
        
        # Simple cyclical pattern detection
        # This is a basic implementation - more sophisticated methods could use FFT or autocorrelation
        cpu_values = [m.cpu_percent for m in self.resource_history[-100:]]
        
        # Check for periodicity every ~10 data points
        period = 10
        if len(cpu_values) >= period * 2:
            correlation = self._calculate_autocorrelation(cpu_values, period)
            if correlation > 0.6:  # Strong correlation indicates periodicity
                patterns.append(ResourceUsagePattern(
                    pattern_type="cyclical_cpu_usage",
                    resource_type=ResourceType.CPU,
                    start_time=self.resource_history[-100].timestamp,
                    end_time=self.resource_history[-1].timestamp,
                    severity=0.5,
                    description=f"Cyclical CPU pattern detected with period ~{period} measurements (correlation: {correlation:.2f})",
                    recommended_actions=["Schedule resource-intensive tasks during low-usage periods", "Consider auto-scaling based on cyclical patterns"]
                ))
        
        return patterns
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend as percentage change"""
        if len(values) < 2:
            return 0.0
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        if first_avg == 0:
            return 0.0
        
        return (second_avg - first_avg) / first_avg
    
    def _calculate_autocorrelation(self, values: List[float], lag: int) -> float:
        """Calculate autocorrelation at given lag"""
        if len(values) <= lag:
            return 0.0
        
        n = len(values)
        mean = statistics.mean(values)
        
        numerator = sum((values[i] - mean) * (values[i + lag] - mean) for i in range(n - lag))
        denominator = sum((values[i] - mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _evaluate_scaling(self) -> Optional[ScalingDecision]:
        """Evaluate if scaling is needed"""
        if len(self.resource_history) < 10:
            return None
        
        recent_metrics = self.resource_history[-10:]
        
        # Calculate average resource usage
        avg_cpu = statistics.mean([m.cpu_percent for m in recent_metrics])
        avg_memory = statistics.mean([m.memory_percent for m in recent_metrics])
        avg_queue = statistics.mean([m.queue_size for m in recent_metrics])
        
        # Check for scale-up conditions
        scale_up_reasons = []
        
        if avg_cpu > 80:
            scale_up_reasons.append(f"High CPU usage: {avg_cpu:.1f}%")
        
        if avg_memory > 85:
            scale_up_reasons.append(f"High memory usage: {avg_memory:.1f}%")
        
        if avg_queue > 50:
            scale_up_reasons.append(f"Large request queue: {avg_queue:.0f}")
        
        # Check for scale-down conditions
        scale_down_reasons = []
        
        if avg_cpu < 20 and avg_memory < 30 and avg_queue < 10:
            scale_down_reasons.append("Low resource utilization")
        
        # Make scaling decision
        if scale_up_reasons and len(scale_up_reasons) >= 2:
            return ScalingDecision(
                action="scale_up",
                resource_type=ResourceType.CPU,  # Simplified - would target specific resources
                current_capacity=1.0,  # Normalized current capacity
                recommended_capacity=1.5,  # 50% increase
                reasoning="; ".join(scale_up_reasons),
                confidence=0.8,
                expected_impact="Reduce latency and improve responsiveness"
            )
        elif scale_down_reasons:
            return ScalingDecision(
                action="scale_down",
                resource_type=ResourceType.CPU,
                current_capacity=1.0,
                recommended_capacity=0.8,  # 20% decrease
                reasoning="; ".join(scale_down_reasons),
                confidence=0.7,
                expected_impact="Reduce costs while maintaining performance"
            )
        
        return None
    
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """Add callback for specific events"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def _trigger_callbacks(self, event_type: str, *args) -> None:
        """Trigger callbacks for specific events"""
        for callback in self.callbacks.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(*args))
                else:
                    callback(*args)
            except Exception as e:
                logger.error(f"Error in callback for {event_type}: {e}")
    
    async def get_resource_summary(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """Get resource usage summary for the specified time window"""
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        relevant_metrics = [m for m in self.resource_history if m.timestamp >= cutoff_time]
        
        if not relevant_metrics:
            return {"error": "No data available for the specified time window"}
        
        cpu_values = [m.cpu_percent for m in relevant_metrics]
        memory_values = [m.memory_percent for m in relevant_metrics]
        disk_values = [m.disk_usage for m in relevant_metrics]
        queue_values = [m.queue_size for m in relevant_metrics]
        
        return {
            "time_window_minutes": time_window_minutes,
            "data_points": len(relevant_metrics),
            "start_time": relevant_metrics[0].timestamp.isoformat(),
            "end_time": relevant_metrics[-1].timestamp.isoformat(),
            "cpu": {
                "current": cpu_values[-1],
                "average": statistics.mean(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values),
                "p95": np.percentile(cpu_values, 95)
            },
            "memory": {
                "current": memory_values[-1],
                "average": statistics.mean(memory_values),
                "min": min(memory_values),
                "max": max(memory_values),
                "p95": np.percentile(memory_values, 95)
            },
            "disk": {
                "current": disk_values[-1],
                "average": statistics.mean(disk_values),
                "min": min(disk_values),
                "max": max(disk_values)
            },
            "queue": {
                "current": queue_values[-1],
                "average": statistics.mean(queue_values),
                "min": min(queue_values),
                "max": max(queue_values)
            },
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
            "total_alerts": len(self.alerts),
            "detected_patterns": len(self.patterns)
        }
    
    async def get_alerts(self, 
                        resolved: Optional[bool] = None,
                        time_window_minutes: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering"""
        alerts = self.alerts
        
        # Filter by resolution status
        if resolved is not None:
            alerts = [a for a in alerts if a.resolved == resolved]
        
        # Filter by time window
        if time_window_minutes:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            alerts = [a for a in alerts if a.timestamp >= cutoff_time]
        
        return [
            {
                "resource_type": alert.resource_type.value,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "alert_level": alert.alert_level.value,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolution_time": alert.resolution_time.isoformat() if alert.resolution_time else None
            }
            for alert in sorted(alerts, key=lambda x: x.timestamp, reverse=True)
        ]
    
    async def get_patterns(self, time_window_minutes: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get detected patterns"""
        patterns = self.patterns
        
        if time_window_minutes:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            patterns = [p for p in patterns if p.start_time >= cutoff_time]
        
        return [
            {
                "pattern_type": pattern.pattern_type,
                "resource_type": pattern.resource_type.value,
                "start_time": pattern.start_time.isoformat(),
                "end_time": pattern.end_time.isoformat() if pattern.end_time else None,
                "severity": pattern.severity,
                "description": pattern.description,
                "recommended_actions": pattern.recommended_actions
            }
            for pattern in sorted(patterns, key=lambda x: x.start_time, reverse=True)
        ]
    
    def resolve_alert(self, alert_index: int) -> bool:
        """Resolve a specific alert"""
        if 0 <= alert_index < len(self.alerts):
            alert = self.alerts[alert_index]
            if not alert.resolved:
                alert.resolved = True
                alert.resolution_time = datetime.now()
                logger.info(f"Resolved alert: {alert.message}")
                return True
        return False
    
    def update_thresholds(self, 
                          resource_type: str, 
                          warning: Optional[float] = None,
                          critical: Optional[float] = None,
                          emergency: Optional[float] = None) -> None:
        """Update alert thresholds for a resource type"""
        if resource_type in self.alert_thresholds:
            if warning is not None:
                self.alert_thresholds[resource_type]['warning'] = warning
            if critical is not None:
                self.alert_thresholds[resource_type]['critical'] = critical
            if emergency is not None:
                self.alert_thresholds[resource_type]['emergency'] = emergency
            
            logger.info(f"Updated {resource_type} thresholds: {self.alert_thresholds[resource_type]}")
    
    def export_metrics(self, 
                      format_type: str = 'json',
                      time_window_minutes: Optional[int] = None) -> str:
        """Export resource metrics"""
        if time_window_minutes:
            cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
            metrics = [m for m in self.resource_history if m.timestamp >= cutoff_time]
        else:
            metrics = self.resource_history
        
        if format_type == 'json':
            return json.dumps([asdict(metric) for metric in metrics], indent=2)
        elif format_type == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if metrics:
                writer = csv.DictWriter(output, fieldnames=asdict(metrics[0]).keys())
                writer.writeheader()
                for metric in metrics:
                    writer.writerow(asdict(metric))
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get resource optimization recommendations"""
        recommendations = []
        
        if len(self.resource_history) < 20:
            return recommendations
        
        recent_metrics = self.resource_history[-20:]
        
        # CPU optimization recommendations
        cpu_values = [m.cpu_percent for m in recent_metrics]
        avg_cpu = statistics.mean(cpu_values)
        
        if avg_cpu > 70:
            recommendations.append({
                "category": "CPU Optimization",
                "priority": "high",
                "current_value": f"{avg_cpu:.1f}%",
                "recommendation": "Consider CPU optimization or scaling",
                "estimated_impact": "Reduce latency and improve responsiveness"
            })
        
        # Memory optimization recommendations
        memory_values = [m.memory_percent for m in recent_metrics]
        avg_memory = statistics.mean(memory_values)
        
        if avg_memory > 80:
            recommendations.append({
                "category": "Memory Optimization",
                "priority": "high",
                "current_value": f"{avg_memory:.1f}%",
                "recommendation": "Investigate memory usage or add more memory",
                "estimated_impact": "Prevent out-of-memory errors"
            })
        
        # Queue optimization recommendations
        queue_values = [m.queue_size for m in recent_metrics]
        avg_queue = statistics.mean(queue_values)
        
        if avg_queue > 30:
            recommendations.append({
                "category": "Queue Management",
                "priority": "medium",
                "current_value": f"{avg_queue:.0f}",
                "recommendation": "Increase worker count or optimize request processing",
                "estimated_impact": "Reduce request wait times"
            })
        
        return recommendations