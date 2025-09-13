#!/usr/bin/env python3
"""
Continuous Quality Monitoring and Alerting System
Implements real-time monitoring, anomaly detection, and automated alerting
"""

import asyncio
import json
import logging
import statistics
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import aiofiles
import asyncpg
import httpx
import redis.asyncio as redis
from concurrent.futures import ThreadPoolExecutor
import yaml
import numpy as np
from dataclasses import asdict

from .quality_metrics import (
    QualityAssessment, QualityMetricResult, 
    Role, QualityLevel, QualityMetric
)
from .automated_testing import QualityValidationEngine, TestResult, TestStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertType(Enum):
    """Types of quality alerts"""
    THRESHOLD_BREACH = "threshold_breach"
    ANOMALY_DETECTED = "anomaly_detected"
    TREND_DEGRADATION = "trend_degradation"
    SYSTEM_FAILURE = "system_failure"
    SECURITY_BREACH = "security_breach"
    PERFORMANCE_DEGRADATION = "performance_degradation"


@dataclass
class QualityMetric:
    """Quality metric with monitoring configuration"""
    name: str
    value: float
    timestamp: datetime
    role: Role
    metric_type: QualityMetric
    thresholds: Dict[str, float] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)


@dataclass
class Alert:
    """Quality alert"""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    metric_name: str
    current_value: float
    threshold_value: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)


@dataclass
class AlertRule:
    """Alert rule configuration"""
    name: str
    description: str
    metric_pattern: str
    condition: str  # e.g., "value > threshold", "value < threshold"
    threshold: float
    severity: AlertSeverity
    cooldown_period: int = 300  # seconds
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)


class AnomalyDetector(ABC):
    """Abstract base class for anomaly detection algorithms"""
    
    @abstractmethod
    async def detect_anomaly(self, metric: QualityMetric, history: List[QualityMetric]) -> bool:
        """Detect if current metric value is anomalous"""
        pass
    
    @abstractmethod
    def get_confidence(self) -> float:
        """Get confidence level in the detection"""
        pass


class StatisticalAnomalyDetector(AnomalyDetector):
    """Statistical anomaly detection using z-score"""
    
    def __init__(self, z_threshold: float = 3.0, min_samples: int = 10):
        self.z_threshold = z_threshold
        self.min_samples = min_samples
        self.confidence = 0.0
    
    async def detect_anomaly(self, metric: QualityMetric, history: List[QualityMetric]) -> bool:
        """Detect anomaly using z-score"""
        if len(history) < self.min_samples:
            return False
        
        # Extract historical values
        values = [m.value for m in history[-min_samples:]]
        
        # Calculate statistics
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        if std_dev == 0:
            return False
        
        # Calculate z-score
        z_score = abs((metric.value - mean) / std_dev)
        
        # Calculate confidence based on how far from threshold
        self.confidence = min(1.0, z_score / self.z_threshold)
        
        return z_score > self.z_threshold
    
    def get_confidence(self) -> float:
        return self.confidence


class MovingAverageAnomalyDetector(AnomalyDetector):
    """Moving average based anomaly detection"""
    
    def __init__(self, window_size: int = 10, deviation_threshold: float = 0.3):
        self.window_size = window_size
        self.deviation_threshold = deviation_threshold
        self.confidence = 0.0
    
    async def detect_anomaly(self, metric: QualityMetric, history: List[QualityMetric]) -> bool:
        """Detect anomaly using moving average deviation"""
        if len(history) < self.window_size:
            return False
        
        # Calculate moving average
        recent_values = [m.value for m in history[-self.window_size:]]
        moving_avg = statistics.mean(recent_values)
        
        # Calculate percentage deviation
        if moving_avg != 0:
            deviation = abs((metric.value - moving_avg) / moving_avg)
        else:
            deviation = 0.0
        
        # Calculate confidence
        self.confidence = min(1.0, deviation / self.deviation_threshold)
        
        return deviation > self.deviation_threshold
    
    def get_confidence(self) -> float:
        return self.confidence


class TrendAnalyzer:
    """Analyzes quality trends over time"""
    
    def __init__(self, window_size: int = 20):
        self.window_size = window_size
    
    async def analyze_trend(self, metrics: List[QualityMetric]) -> Dict[str, Any]:
        """Analyze trend in metrics"""
        if len(metrics) < self.window_size:
            return {"trend": "insufficient_data", "slope": 0.0, "confidence": 0.0}
        
        # Extract values and timestamps
        values = [m.value for m in metrics[-self.window_size:]]
        timestamps = [(m.timestamp - metrics[0].timestamp).total_seconds() for m in metrics[-self.window_size:]]
        
        # Simple linear regression
        if len(values) < 2:
            return {"trend": "stable", "slope": 0.0, "confidence": 0.0}
        
        # Calculate slope (trend)
        n = len(values)
        sum_x = sum(timestamps)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(timestamps, values))
        sum_x2 = sum(x * x for x in timestamps)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return {"trend": "stable", "slope": 0.0, "confidence": 0.0}
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        
        # Determine trend direction and strength
        if abs(slope) < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "improving"
        else:
            trend = "degrading"
        
        # Calculate confidence based on correlation
        y_mean = sum_y / n
        ss_tot = sum((y - y_mean) ** 2 for y in values)
        ss_res = sum((y - (slope * x + (sum_y - slope * sum_x) / n)) ** 2 for x, y in zip(timestamps, values))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        confidence = min(1.0, abs(r_squared))
        
        return {
            "trend": trend,
            "slope": slope,
            "confidence": confidence,
            "r_squared": r_squared
        }


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""
    
    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert notification"""
        pass


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        # Implementation would use SMTP library
        logger.info(f"Sending email alert: {alert.title}")
        return True


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""
    
    def __init__(self, webhook_url: str, channel: str):
        self.webhook_url = webhook_url
        self.channel = channel
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "channel": self.channel,
                    "text": f"🚨 {alert.title}",
                    "attachments": [
                        {
                            "color": self._get_color_for_severity(alert.severity),
                            "fields": [
                                {"title": "Severity", "value": alert.severity.value, "short": True},
                                {"title": "Metric", "value": alert.metric_name, "short": True},
                                {"title": "Value", "value": str(alert.current_value), "short": True},
                                {"title": "Description", "value": alert.description, "short": False},
                            ]
                        }
                    ]
                }
                
                response = await client.post(self.webhook_url, json=payload)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def _get_color_for_severity(self, severity: AlertSeverity) -> str:
        """Get Slack color for severity level"""
        colors = {
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.HIGH: "warning",
            AlertSeverity.MEDIUM: "#ffcc00",
            AlertSeverity.LOW: "#36a64f",
            AlertSeverity.INFO: "#439fe0"
        }
        return colors.get(severity, "#439fe0")


class WebhookNotificationChannel(NotificationChannel):
    """Generic webhook notification channel"""
    
    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {}
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send webhook alert"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "alert_id": alert.id,
                    "type": alert.type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "description": alert.description,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "timestamp": alert.timestamp.isoformat(),
                    "metadata": alert.metadata,
                    "tags": list(alert.tags)
                }
                
                response = await client.post(
                    self.webhook_url, 
                    json=payload,
                    headers=self.headers
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False


class QualityMonitoringEngine:
    """Main quality monitoring engine"""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.redis_client: Optional[redis.Redis] = None
        self.database_pool: Optional[asyncpg.Pool] = None
        self.alert_rules: List[AlertRule] = []
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.anomaly_detectors: List[AnomalyDetector] = []
        self.trend_analyzer = TrendAnalyzer()
        self.logger = logging.getLogger(__name__)
        self.active_alerts: Dict[str, Alert] = {}
        self.metric_history: Dict[str, List[QualityMetric]] = {}
        
        self._initialize_detectors()
    
    def _initialize_detectors(self):
        """Initialize anomaly detectors"""
        self.anomaly_detectors = [
            StatisticalAnomalyDetector(z_threshold=3.0, min_samples=10),
            MovingAverageAnomalyDetector(window_size=10, deviation_threshold=0.3)
        ]
    
    async def initialize(self, redis_url: str = None, database_url: str = None):
        """Initialize external connections"""
        if redis_url:
            self.redis_client = redis.from_url(redis_url)
        
        if database_url:
            self.database_pool = await asyncpg.create_pool(database_url)
        
        # Load alert rules
        await self._load_alert_rules()
        
        # Load notification channels
        await self._load_notification_channels()
    
    async def _load_alert_rules(self):
        """Load alert rules from configuration"""
        config_path = self.workspace_root / "config" / "alert_rules.yaml"
        if config_path.exists():
            try:
                async with aiofiles.open(config_path) as f:
                    content = await f.read()
                    config = yaml.safe_load(content)
                    
                for rule_config in config.get("rules", []):
                    rule = AlertRule(
                        name=rule_config["name"],
                        description=rule_config["description"],
                        metric_pattern=rule_config["metric_pattern"],
                        condition=rule_config["condition"],
                        threshold=rule_config["threshold"],
                        severity=AlertSeverity(rule_config["severity"]),
                        cooldown_period=rule_config.get("cooldown_period", 300),
                        enabled=rule_config.get("enabled", True),
                        notification_channels=rule_config.get("notification_channels", [])
                    )
                    self.alert_rules.append(rule)
                    
                self.logger.info(f"Loaded {len(self.alert_rules)} alert rules")
            except Exception as e:
                self.logger.error(f"Failed to load alert rules: {e}")
    
    async def _load_notification_channels(self):
        """Load notification channel configurations"""
        config_path = self.workspace_root / "config" / "notification_channels.yaml"
        if config_path.exists():
            try:
                async with aiofiles.open(config_path) as f:
                    content = await f.read()
                    config = yaml.safe_load(content)
                
                for channel_config in config.get("channels", []):
                    channel_type = channel_config["type"]
                    channel_name = channel_config["name"]
                    
                    if channel_type == "email":
                        channel = EmailNotificationChannel(channel_config["smtp_config"])
                    elif channel_type == "slack":
                        channel = SlackNotificationChannel(
                            channel_config["webhook_url"],
                            channel_config["channel"]
                        )
                    elif channel_type == "webhook":
                        channel = WebhookNotificationChannel(
                            channel_config["webhook_url"],
                            channel_config.get("headers", {})
                        )
                    else:
                        continue
                    
                    self.notification_channels[channel_name] = channel
                
                self.logger.info(f"Loaded {len(self.notification_channels)} notification channels")
            except Exception as e:
                self.logger.error(f"Failed to load notification channels: {e}")
    
    async def process_quality_assessment(self, assessment: QualityAssessment):
        """Process quality assessment and trigger monitoring"""
        # Process each metric result
        for metric_result in assessment.metric_results:
            await self._process_metric_result(metric_result, assessment)
        
        # Check overall assessment quality
        await self._check_overall_quality(assessment)
    
    async def _process_metric_result(self, metric_result: QualityMetricResult, assessment: QualityAssessment):
        """Process individual metric result"""
        # Create quality metric
        metric = QualityMetric(
            name=f"{assessment.role.value}_{metric_result.metric.value}",
            value=metric_result.score,
            timestamp=metric_result.timestamp,
            role=assessment.role,
            metric_type=metric_result.metric,
            thresholds=metric_result.details,
            tags={assessment.role.value, metric_result.metric.value}
        )
        
        # Store metric in history
        metric_key = metric.name
        if metric_key not in self.metric_history:
            self.metric_history[metric_key] = []
        
        self.metric_history[metric_key].append(metric)
        
        # Keep only recent history (last 100 metrics)
        if len(self.metric_history[metric_key]) > 100:
            self.metric_history[metric_key] = self.metric_history[metric_key][-100:]
        
        # Check for threshold breaches
        await self._check_threshold_breaches(metric)
        
        # Check for anomalies
        await self._check_anomalies(metric)
        
        # Check trends
        await self._check_trends(metric)
        
        # Store in Redis for real-time monitoring
        if self.redis_client:
            await self._store_metric_in_redis(metric)
    
    async def _check_threshold_breaches(self, metric: QualityMetric):
        """Check if metric breaches any thresholds"""
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            # Check if rule applies to this metric
            if not self._rule_applies_to_metric(rule, metric):
                continue
            
            # Check cooldown period
            alert_key = f"{rule.name}_{metric.name}"
            if alert_key in self.active_alerts:
                last_alert = self.active_alerts[alert_key]
                if (datetime.utcnow() - last_alert.timestamp).total_seconds() < rule.cooldown_period:
                    continue
            
            # Evaluate condition
            if self._evaluate_condition(rule.condition, metric.value, rule.threshold):
                # Create alert
                alert = Alert(
                    id=f"{alert_key}_{int(time.time())}",
                    type=AlertType.THRESHOLD_BREACH,
                    severity=rule.severity,
                    title=f"{rule.name}: {metric.name} threshold breached",
                    description=f"{metric.name} value {metric.value} {rule.condition} {rule.threshold}",
                    metric_name=metric.name,
                    current_value=metric.value,
                    threshold_value=rule.threshold,
                    tags=metric.tags.union({rule.name})
                )
                
                await self._trigger_alert(alert, rule.notification_channels)
                self.active_alerts[alert_key] = alert
    
    async def _check_anomalies(self, metric: QualityMetric):
        """Check for anomalies in metric values"""
        metric_key = metric.name
        history = self.metric_history.get(metric_key, [])
        
        if len(history) < 5:  # Need some history for anomaly detection
            return
        
        # Check with each anomaly detector
        for detector in self.anomaly_detectors:
            is_anomaly = await detector.detect_anomaly(metric, history)
            
            if is_anomaly:
                confidence = detector.get_confidence()
                
                # Create anomaly alert
                alert = Alert(
                    id=f"anomaly_{metric.name}_{int(time.time())}",
                    type=AlertType.ANOMALY_DETECTED,
                    severity=AlertSeverity.MEDIUM if confidence > 0.8 else AlertSeverity.LOW,
                    title=f"Anomaly detected in {metric.name}",
                    description=f"Statistical anomaly detected in {metric.name} with confidence {confidence:.2f}",
                    metric_name=metric.name,
                    current_value=metric.value,
                    metadata={"detector": detector.__class__.__name__, "confidence": confidence},
                    tags=metric.tags.union({"anomaly"})
                )
                
                await self._trigger_alert(alert)
                break  # Stop after first anomaly detected
    
    async def _check_trends(self, metric: QualityMetric):
        """Check for degrading trends"""
        metric_key = metric.name
        history = self.metric_history.get(metric_key, [])
        
        if len(history) < 10:  # Need enough history for trend analysis
            return
        
        # Analyze trend
        trend_analysis = await self.trend_analyzer.analyze_trend(history)
        
        if trend_analysis["trend"] == "degrading" and trend_analysis["confidence"] > 0.7:
            # Create trend alert
            alert = Alert(
                id=f"trend_{metric.name}_{int(time.time())}",
                type=AlertType.TREND_DEGRADATION,
                severity=AlertSeverity.HIGH if trend_analysis["confidence"] > 0.9 else AlertSeverity.MEDIUM,
                title=f"Degrading trend detected in {metric.name}",
                description=f"{metric.name} shows degrading trend with slope {trend_analysis['slope']:.4f} and confidence {trend_analysis['confidence']:.2f}",
                metric_name=metric.name,
                current_value=metric.value,
                metadata={
                    "trend": trend_analysis["trend"],
                    "slope": trend_analysis["slope"],
                    "confidence": trend_analysis["confidence"],
                    "r_squared": trend_analysis["r_squared"]
                },
                tags=metric.tags.union({"trend"})
            )
            
            await self._trigger_alert(alert)
    
    async def _check_overall_quality(self, assessment: QualityAssessment):
        """Check overall quality assessment for issues"""
        # Check for poor overall quality
        if assessment.overall_level in [QualityLevel.POOR, QualityLevel.FAIL]:
            alert = Alert(
                id=f"overall_quality_{assessment.role.value}_{int(time.time())}",
                type=AlertType.THRESHOLD_BREACH,
                severity=AlertSeverity.HIGH if assessment.overall_level == QualityLevel.FAIL else AlertSeverity.MEDIUM,
                title=f"Poor overall quality for {assessment.role.value}",
                description=f"Overall quality score {assessment.overall_score} is {assessment.overall_level.value}",
                metric_name=f"{assessment.role.value}_overall_quality",
                current_value=assessment.overall_score,
                threshold_value=70.0,  # Minimum acceptable score
                tags={assessment.role.value, "overall_quality"}
            )
            
            await self._trigger_alert(alert)
        
        # Check for critical issues
        if assessment.critical_issues:
            alert = Alert(
                id=f"critical_issues_{assessment.role.value}_{int(time.time())}",
                type=AlertType.SYSTEM_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title=f"Critical quality issues detected for {assessment.role.value}",
                description=f"Found {len(assessment.critical_issues)} critical issues: {'; '.join(assessment.critical_issues)}",
                metric_name=f"{assessment.role.value}_critical_issues",
                current_value=len(assessment.critical_issues),
                threshold_value=0.0,
                tags={assessment.role.value, "critical_issues"}
            )
            
            await self._trigger_alert(alert)
    
    def _rule_applies_to_metric(self, rule: AlertRule, metric: QualityMetric) -> bool:
        """Check if alert rule applies to metric"""
        # Simple pattern matching - can be enhanced with regex
        return rule.metric_pattern in metric.name or metric.name.endswith(rule.metric_pattern)
    
    def _evaluate_condition(self, condition: str, value: float, threshold: float) -> bool:
        """Evaluate alert condition"""
        try:
            # Simple condition evaluation
            if condition == "value > threshold":
                return value > threshold
            elif condition == "value < threshold":
                return value < threshold
            elif condition == "value >= threshold":
                return value >= threshold
            elif condition == "value <= threshold":
                return value <= threshold
            elif condition == "value == threshold":
                return abs(value - threshold) < 0.001
            else:
                return False
        except Exception:
            return False
    
    async def _trigger_alert(self, alert: Alert, channel_names: List[str] = None):
        """Trigger alert through notification channels"""
        self.logger.warning(f"Triggering alert: {alert.title}")
        
        # Store alert
        await self._store_alert(alert)
        
        # Send notifications
        channels_to_notify = channel_names or list(self.notification_channels.keys())
        
        for channel_name in channels_to_notify:
            if channel_name in self.notification_channels:
                channel = self.notification_channels[channel_name]
                success = await channel.send_alert(alert)
                
                if not success:
                    self.logger.error(f"Failed to send alert via {channel_name}")
            else:
                self.logger.warning(f"Notification channel {channel_name} not found")
    
    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    await conn.execute("""
                        INSERT INTO quality_alerts 
                        (id, type, severity, title, description, metric_name, 
                         current_value, threshold_value, timestamp, acknowledged, 
                         resolved, metadata, tags)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                    """, 
                    alert.id, alert.type.value, alert.severity.value, alert.title,
                    alert.description, alert.metric_name, alert.current_value,
                    alert.threshold_value, alert.timestamp, alert.acknowledged,
                    alert.resolved, json.dumps(alert.metadata), 
                    json.dumps(list(alert.tags))
                    )
            except Exception as e:
                self.logger.error(f"Failed to store alert in database: {e}")
    
    async def _store_metric_in_redis(self, metric: QualityMetric):
        """Store metric in Redis for real-time monitoring"""
        if self.redis_client:
            try:
                # Store current value
                await self.redis_client.setex(
                    f"metric:{metric.name}",
                    3600,  # 1 hour TTL
                    json.dumps({
                        "value": metric.value,
                        "timestamp": metric.timestamp.isoformat(),
                        "role": metric.role.value,
                        "metric_type": metric.metric_type.value
                    })
                )
                
                # Store in time series
                await self.redis_client.zadd(
                    f"timeseries:{metric.name}",
                    {json.dumps({
                        "value": metric.value,
                        "timestamp": metric.timestamp.isoformat()
                    }): metric.timestamp.timestamp()}
                )
                
                # Keep only recent data (last 24 hours)
                cutoff = time.time() - 86400
                await self.redis_client.zremrangebyscore(f"timeseries:{metric.name}", 0, cutoff)
                
            except Exception as e:
                self.logger.error(f"Failed to store metric in Redis: {e}")
    
    async def get_current_metrics(self) -> Dict[str, Any]:
        """Get current quality metrics"""
        metrics = {}
        
        if self.redis_client:
            try:
                # Get all metric keys
                keys = await self.redis_client.keys("metric:*")
                
                for key in keys:
                    metric_name = key.decode().replace("metric:", "")
                    data = await self.redis_client.get(key)
                    if data:
                        metrics[metric_name] = json.loads(data.decode())
            except Exception as e:
                self.logger.error(f"Failed to get current metrics from Redis: {e}")
        
        return metrics
    
    async def get_metric_history(self, metric_name: str, hours: int = 24) -> List[Dict[str, Any]]:
        """Get metric history for specified time period"""
        history = []
        
        if self.redis_client:
            try:
                # Get time series data
                data = await self.redis_client.zrangebyscore(
                    f"timeseries:{metric_name}",
                    time.time() - (hours * 3600),
                    time.time()
                )
                
                for item in data:
                    history.append(json.loads(item.decode()))
            except Exception as e:
                self.logger.error(f"Failed to get metric history from Redis: {e}")
        
        return history
    
    async def get_active_alerts(self) -> List[Alert]:
        """Get active (unresolved) alerts"""
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    rows = await conn.fetch("""
                        SELECT id, type, severity, title, description, metric_name,
                               current_value, threshold_value, timestamp, acknowledged,
                               resolved, metadata, tags
                        FROM quality_alerts
                        WHERE resolved = false
                        ORDER BY timestamp DESC
                    """)
                    
                    alerts = []
                    for row in rows:
                        alert = Alert(
                            id=row["id"],
                            type=AlertType(row["type"]),
                            severity=AlertSeverity(row["severity"]),
                            title=row["title"],
                            description=row["description"],
                            metric_name=row["metric_name"],
                            current_value=row["current_value"],
                            threshold_value=row["threshold_value"],
                            timestamp=row["timestamp"],
                            acknowledged=row["acknowledged"],
                            resolved=row["resolved"],
                            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
                            tags=set(json.loads(row["tags"])) if row["tags"] else set()
                        )
                        alerts.append(alert)
                    
                    return alerts
            except Exception as e:
                self.logger.error(f"Failed to get active alerts from database: {e}")
        
        return list(self.active_alerts.values())
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an alert"""
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    result = await conn.execute("""
                        UPDATE quality_alerts
                        SET acknowledged = true, acknowledged_at = NOW(), acknowledged_by = $1
                        WHERE id = $2
                    """, acknowledged_by, alert_id)
                    
                    # Update in-memory alerts
                    for alert in self.active_alerts.values():
                        if alert.id == alert_id:
                            alert.acknowledged = True
                            break
                    
                    return "UPDATE 1" in result
            except Exception as e:
                self.logger.error(f"Failed to acknowledge alert: {e}")
        
        return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str = "system") -> bool:
        """Resolve an alert"""
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    result = await conn.execute("""
                        UPDATE quality_alerts
                        SET resolved = true, resolved_at = NOW(), resolved_by = $1
                        WHERE id = $2
                    """, resolved_by, alert_id)
                    
                    # Remove from active alerts
                    if alert_id in self.active_alerts:
                        del self.active_alerts[alert_id]
                    
                    return "UPDATE 1" in result
            except Exception as e:
                self.logger.error(f"Failed to resolve alert: {e}")
        
        return False
    
    async def start_monitoring(self, validation_engine: QualityValidationEngine, interval: int = 300):
        """Start continuous monitoring"""
        self.logger.info(f"Starting quality monitoring with {interval}s interval")
        
        while True:
            try:
                # Get latest quality metrics
                current_metrics = await self.get_current_metrics()
                
                # Process any new quality assessments
                # This would typically be triggered by validation results
                # For now, we'll simulate periodic checks
                
                # Check for system health
                await self._check_system_health()
                
                # Sleep until next check
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval)
    
    async def _check_system_health(self):
        """Check overall system health"""
        # Check active alerts count
        active_alerts = await self.get_active_alerts()
        critical_alerts = [a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]
        
        if len(critical_alerts) > 5:
            alert = Alert(
                id=f"system_health_{int(time.time())}",
                type=AlertType.SYSTEM_FAILURE,
                severity=AlertSeverity.CRITICAL,
                title="System health degraded",
                description=f"Too many critical alerts active: {len(critical_alerts)}",
                metric_name="system_health",
                current_value=len(critical_alerts),
                threshold_value=5.0,
                tags={"system_health", "critical"}
            )
            
            await self._trigger_alert(alert)
        
        # Check Redis connectivity
        if self.redis_client:
            try:
                await self.redis_client.ping()
            except Exception:
                alert = Alert(
                    id=f"redis_down_{int(time.time())}",
                    type=AlertType.SYSTEM_FAILURE,
                    severity=AlertSeverity.HIGH,
                    title="Redis connectivity lost",
                    description="Unable to connect to Redis monitoring backend",
                    metric_name="redis_connectivity",
                    current_value=0.0,
                    threshold_value=1.0,
                    tags={"system_health", "redis"}
                )
                
                await self._trigger_alert(alert)
        
        # Check database connectivity
        if self.database_pool:
            try:
                async with self.database_pool.acquire() as conn:
                    await conn.execute("SELECT 1")
            except Exception:
                alert = Alert(
                    id=f"database_down_{int(time.time())}",
                    type=AlertType.SYSTEM_FAILURE,
                    severity=AlertSeverity.HIGH,
                    title="Database connectivity lost",
                    description="Unable to connect to monitoring database",
                    metric_name="database_connectivity",
                    current_value=0.0,
                    threshold_value=1.0,
                    tags={"system_health", "database"}
                )
                
                await self._trigger_alert(alert)
    
    async def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard"""
        current_metrics = await self.get_current_metrics()
        active_alerts = await self.get_active_alerts()
        
        # Calculate summary statistics
        total_alerts = len(active_alerts)
        critical_alerts = len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL])
        high_alerts = len([a for a in active_alerts if a.severity == AlertSeverity.HIGH])
        
        # Get quality scores by role
        role_scores = {}
        for metric_name, metric_data in current_metrics.items():
            role = metric_data.get("role")
            if role and "score" in metric_name.lower():
                if role not in role_scores:
                    role_scores[role] = []
                role_scores[role].append(metric_data["value"])
        
        # Calculate average scores by role
        avg_scores = {}
        for role, scores in role_scores.items():
            if scores:
                avg_scores[role] = statistics.mean(scores)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "current_metrics": current_metrics,
            "active_alerts": [
                {
                    "id": alert.id,
                    "type": alert.type.value,
                    "severity": alert.severity.value,
                    "title": alert.title,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "timestamp": alert.timestamp.isoformat()
                }
                for alert in active_alerts
            ],
            "summary": {
                "total_alerts": total_alerts,
                "critical_alerts": critical_alerts,
                "high_alerts": high_alerts,
                "alert_severity_distribution": {
                    severity.value: len([a for a in active_alerts if a.severity == severity])
                    for severity in AlertSeverity
                },
                "average_role_scores": avg_scores
            },
            "system_health": {
                "redis_connected": self.redis_client is not None,
                "database_connected": self.database_pool is not None,
                "alert_rules_loaded": len(self.alert_rules),
                "notification_channels": len(self.notification_channels)
            }
        }