import sqlite3
from datetime import datetime, timedelta
from typing import List
import logging

from .types import ModelPerformanceMetrics, SystemResourceMetrics, ModelType

logger = logging.getLogger(__name__)


class MetricsStorage:
    """Persistent storage for performance metrics"""
    
    def __init__(self, db_path: str = "performance_metrics.db"):
        self.db_path = db_path
        self._initialized = False
    
    async def initialize(self):
        """Initialize database tables"""
        if not self._initialized:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create model performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS model_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    model_id TEXT NOT NULL,
                    model_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    execution_time REAL NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    cost REAL,
                    quality_score REAL,
                    cpu_usage REAL,
                    memory_usage REAL,
                    user_id TEXT,
                    session_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create system metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    disk_usage REAL NOT NULL,
                    network_io_sent INTEGER NOT NULL,
                    network_io_recv INTEGER NOT NULL,
                    active_connections INTEGER NOT NULL,
                    queue_size INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_performance_timestamp ON model_performance(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_performance_model_type ON model_performance(model_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp ON system_metrics(timestamp)')
            
            conn.commit()
            conn.close()
            self._initialized = True
            logger.info("Metrics storage initialized")
    
    async def store_metrics(self, metrics: ModelPerformanceMetrics) -> None:
        """Store model performance metrics"""
        if not self._initialized:
            await self.initialize()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO model_performance (
                request_id, model_id, model_type, timestamp, execution_time,
                input_tokens, output_tokens, success, error_message, cost,
                quality_score, cpu_usage, memory_usage, user_id, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.request_id,
            metrics.model_id,
            metrics.model_type.value,
            metrics.timestamp,
            metrics.execution_time,
            metrics.input_tokens,
            metrics.output_tokens,
            metrics.success,
            metrics.error_message,
            metrics.cost,
            metrics.quality_score,
            metrics.cpu_usage,
            metrics.memory_usage,
            metrics.user_id,
            metrics.session_id
        ))
        
        conn.commit()
        conn.close()
        logger.debug(f"Stored metrics for request {metrics.request_id}")
    
    async def store_system_metrics(self, metrics: SystemResourceMetrics) -> None:
        """Store system metrics"""
        if not self._initialized:
            await self.initialize()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_metrics (
                timestamp, cpu_percent, memory_percent, disk_usage,
                network_io_sent, network_io_recv, active_connections, queue_size
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp,
            metrics.cpu_percent,
            metrics.memory_percent,
            metrics.disk_usage,
            metrics.network_io_sent,
            metrics.network_io_recv,
            metrics.active_connections,
            metrics.queue_size
        ))
        
        conn.commit()
        conn.close()
    
    async def get_model_metrics(self, 
                               model_type: ModelType,
                               start_time: datetime,
                               end_time: datetime) -> List[ModelPerformanceMetrics]:
        """Retrieve model performance metrics for a time range"""
        if not self._initialized:
            await self.initialize()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT request_id, model_id, model_type, timestamp, execution_time,
                   input_tokens, output_tokens, success, error_message, cost,
                   quality_score, cpu_usage, memory_usage, user_id, session_id
            FROM model_performance
            WHERE model_type = ? AND timestamp BETWEEN ? AND ?
            ORDER BY timestamp DESC
        ''', (model_type.value, start_time, end_time))
        
        rows = cursor.fetchall()
        conn.close()
        
        metrics = []
        for row in rows:
            metrics.append(ModelPerformanceMetrics(
                request_id=row[0],
                model_id=row[1],
                model_type=ModelType(row[2]),
                timestamp=datetime.fromisoformat(row[3]),
                execution_time=row[4],
                input_tokens=row[5],
                output_tokens=row[6],
                success=bool(row[7]),
                error_message=row[8],
                cost=row[9],
                quality_score=row[10],
                cpu_usage=row[11],
                memory_usage=row[12],
                user_id=row[13],
                session_id=row[14]
            ))
        
        return metrics
    
    async def get_performance_aggregates(self,
                                       model_type: ModelType,
                                       start_time: datetime,
                                       end_time: datetime) -> dict:
        """Get aggregated performance statistics"""
        if not self._initialized:
            await self.initialize()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_requests,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
                AVG(execution_time) as avg_latency,
                MIN(execution_time) as min_latency,
                MAX(execution_time) as max_latency,
                AVG(cost) as avg_cost,
                AVG(quality_score) as avg_quality_score
            FROM model_performance
            WHERE model_type = ? AND timestamp BETWEEN ? AND ?
        ''', (model_type.value, start_time, end_time))
        
        row = cursor.fetchone()
        conn.close()
        
        if row and row[0] > 0:
            return {
                'total_requests': row[0],
                'successful_requests': row[1],
                'success_rate': row[1] / row[0] if row[0] > 0 else 0,
                'avg_latency': row[2] or 0,
                'min_latency': row[3] or 0,
                'max_latency': row[4] or 0,
                'avg_cost': row[5] or 0,
                'avg_quality_score': row[6] or 0
            }
        
        return {}
    
    async def cleanup_old_metrics(self, days_to_keep: int = 90) -> int:
        """Clean up old metrics data"""
        if not self._initialized:
            await self.initialize()
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clean up old model performance metrics
        cursor.execute('''
            DELETE FROM model_performance 
            WHERE timestamp < ?
        ''', (cutoff_date,))
        model_deleted = cursor.rowcount
        
        # Clean up old system metrics
        cursor.execute('''
            DELETE FROM system_metrics 
            WHERE timestamp < ?
        ''', (cutoff_date,))
        system_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up {model_deleted} model metrics and {system_deleted} system metrics")
        return model_deleted + system_deleted