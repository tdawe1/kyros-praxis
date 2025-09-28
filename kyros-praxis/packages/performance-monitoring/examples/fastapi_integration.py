"""
FastAPI Integration for Performance Monitoring

This module demonstrates how to integrate the performance monitoring system
with a FastAPI application for real-time monitoring and optimization.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import logging

from performance_monitoring import (
    RedisPerformanceMonitor,
    ModelRouter,
    AutomatedTuner,
    ResourceMonitor,
    ModelType,
    OptimizationStrategy,
    ModelPerformanceMetrics
)

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class ModelRequest(BaseModel):
    prompt: str
    model_type: Optional[str] = None
    optimization_strategy: str = "adaptive"
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class ModelResponse(BaseModel):
    model_type: str
    response: str
    execution_time: float
    input_tokens: int
    output_tokens: int
    quality_score: float
    cost: float
    optimization_decision: Optional[Dict[str, Any]] = None

class BenchmarkRequest(BaseModel):
    model_types: List[str]
    test_prompts: List[str]
    iterations_per_model: int = 5
    concurrency_levels: List[int] = [1, 2]

class PerformanceMetrics(BaseModel):
    timestamp: datetime
    model_type: str
    execution_time: float
    success: bool
    quality_score: Optional[float] = None
    cost: Optional[float] = None

class ResourceMetrics(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    active_connections: int
    queue_size: int

# Initialize FastAPI app
app = FastAPI(
    title="Performance Monitoring API",
    description="API for monitoring and optimizing hybrid model performance",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for monitoring components
monitor: Optional[RedisPerformanceMonitor] = None
router: Optional[ModelRouter] = None
tuner: Optional[AutomatedTuner] = None
resource_monitor: Optional[ResourceMonitor] = None


async def get_monitor() -> RedisPerformanceMonitor:
    """Dependency to get performance monitor"""
    if monitor is None:
        raise HTTPException(status_code=503, detail="Performance monitor not initialized")
    return monitor


@app.on_event("startup")
async def startup_event():
    """Initialize monitoring components on startup"""
    global monitor, router, tuner, resource_monitor
    
    logger.info("Initializing performance monitoring components...")
    
    try:
        # Initialize performance monitor
        monitor = RedisPerformanceMonitor(redis_url="redis://localhost:6379")
        await monitor.initialize()
        
        # Initialize model router
        router = ModelRouter()
        
        # Initialize automated tuner
        tuner = AutomatedTuner(monitor=monitor)
        
        # Initialize resource monitor
        resource_monitor = ResourceMonitor(monitor_interval_seconds=5)
        await resource_monitor.start_monitoring()
        
        logger.info("Performance monitoring components initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize monitoring components: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    global monitor, resource_monitor
    
    logger.info("Shutting down monitoring components...")
    
    if resource_monitor:
        resource_monitor.stop_monitoring()
    
    if monitor:
        await monitor.close()
    
    logger.info("Monitoring components shutdown completed")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Performance Monitoring API is running", "timestamp": datetime.now()}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    status = {
        "status": "healthy",
        "timestamp": datetime.now(),
        "components": {
            "monitor": monitor is not None,
            "router": router is not None,
            "tuner": tuner is not None,
            "resource_monitor": resource_monitor is not None
        }
    }
    return status


@app.post("/v1/models/generate", response_model=ModelResponse)
async def generate_response(
    request: ModelRequest,
    background_tasks: BackgroundTasks,
    monitor: RedisPerformanceMonitor = Depends(get_monitor)
):
    """Generate response using optimal model selection"""
    try:
        start_time = datetime.now()
        
        # Get available models
        available_models = list(ModelType)
        
        # Parse optimization strategy
        try:
            strategy = OptimizationStrategy(request.optimization_strategy.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid optimization strategy")
        
        # Create request features for routing
        request_features = {
            "estimated_tokens": len(request.prompt.split()),
            "creativity_requirement": 0.5,  # Default values
            "reasoning_requirement": 0.7,
            "requires_code": "code" in request.prompt.lower(),
            "requires_vision": "image" in request.prompt.lower(),
            "request_id": f"req_{start_time.timestamp()}",
            "user_id": request.user_id,
            "session_id": request.session_id
        }
        
        # Get model routing decision
        optimization_decision = await router.select_model(
            request_features=request_features,
            available_models=available_models,
            strategy=strategy
        )
        
        # Use selected model or user-specified model
        selected_model = (
            ModelType(request.model_type) if request.model_type 
            else optimization_decision.selected_model
        )
        
        # Simulate model generation (replace with actual model client)
        execution_time = 1.5 + (0.5 if selected_model == ModelType.GPT_4 else 0.2)
        await asyncio.sleep(execution_time)  # Simulate processing time
        
        # Calculate metrics
        input_tokens = len(request.prompt.split())
        output_tokens = int(input_tokens * (1.5 + 0.5 * random.random()))
        quality_score = 0.8 + 0.1 * random.random()
        cost = 0.01 + 0.02 * random.random()
        
        # Create performance metrics
        metrics = ModelPerformanceMetrics(
            model_id=f"api_{selected_model.value}",
            model_type=selected_model,
            timestamp=start_time,
            execution_time=execution_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            success=True,
            cost=cost,
            quality_score=quality_score,
            user_id=request.user_id,
            session_id=request.session_id,
            request_id=request_features["request_id"]
        )
        
        # Record metrics in background
        background_tasks.add_task(monitor.record_model_performance, metrics)
        
        # Return response
        return ModelResponse(
            model_type=selected_model.value,
            response=f"Generated response for: {request.prompt[:50]}...",
            execution_time=execution_time,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            quality_score=quality_score,
            cost=cost,
            optimization_decision={
                "selected_model": optimization_decision.selected_model.value,
                "confidence": optimization_decision.confidence_score,
                "expected_improvement": optimization_decision.expected_improvement,
                "reasoning": optimization_decision.reasoning
            }
        )
        
    except Exception as e:
        logger.error(f"Error in generate_response: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/v1/performance/models/{model_type}")
async def get_model_performance(
    model_type: str,
    time_window_hours: int = 24,
    monitor: RedisPerformanceMonitor = Depends(get_monitor)
):
    """Get performance metrics for a specific model"""
    try:
        # Validate model type
        try:
            model = ModelType(model_type.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid model type")
        
        # Get performance summary
        time_window = timedelta(hours=time_window_hours)
        summary = await monitor.get_performance_summary(model, time_window)
        
        return {
            "model_type": model_type,
            "time_window_hours": time_window_hours,
            "summary": summary,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/v1/performance/summary")
async def get_performance_summary(
    time_window_hours: int = 1,
    monitor: RedisPerformanceMonitor = Depends(get_monitor)
):
    """Get performance summary for all models"""
    try:
        time_window = timedelta(hours=time_window_hours)
        summary = {}
        
        for model_type in ModelType:
            model_summary = await monitor.get_performance_summary(model_type, time_window)
            if model_summary:
                summary[model_type.value] = model_summary
        
        return {
            "time_window_hours": time_window_hours,
            "model_summaries": summary,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/v1/benchmark/run")
async def run_benchmark(
    request: BenchmarkRequest,
    monitor: RedisPerformanceMonitor = Depends(get_monitor)
):
    """Run performance benchmark"""
    try:
        # Import benchmark components
        from performance_monitoring import PerformanceBenchmark, BenchmarkConfig
        
        # Mock model client for benchmarking
        class MockBenchmarkClient:
            async def generate(self, model_type, prompt):
                await asyncio.sleep(0.1)  # Simulate processing
                return type('Response', (), {
                    'input_tokens': len(prompt.split()),
                    'output_tokens': len(prompt.split()) * 2,
                    'execution_time': 0.1,
                    'cost': 0.001,
                    'quality_score': 0.8
                })()
        
        # Create benchmark config
        model_types = [ModelType(mt) for mt in request.model_types]
        config = BenchmarkConfig(
            model_types=model_types,
            test_prompts=request.test_prompts,
            iterations_per_model=request.iterations_per_model,
            concurrency_levels=request.concurrency_levels
        )
        
        # Run benchmark
        benchmark = PerformanceBenchmark(
            model_client=MockBenchmarkClient(),
            monitor=monitor
        )
        
        result = await benchmark.run_comparative_benchmark(config)
        
        return {
            "benchmark_id": result.benchmark_id,
            "config": {
                "model_types": request.model_types,
                "iterations_per_model": request.iterations_per_model,
                "concurrency_levels": request.concurrency_levels
            },
            "summary": result.summary,
            "recommendations": result.recommendations,
            "duration": (result.end_time - result.start_time).total_seconds(),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error running benchmark: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/v1/tuning/status")
async def get_tuning_status():
    """Get automated tuning status"""
    try:
        if tuner is None:
            raise HTTPException(status_code=503, detail="Tuner not available")
        
        status = await tuner.get_tuning_status()
        return {
            "tuning_status": status,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting tuning status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/v1/tuning/run")
async def run_tuning_cycle():
    """Run automated tuning cycle"""
    try:
        if tuner is None:
            raise HTTPException(status_code=503, detail="Tuner not available")
        
        recommendations = await tuner.run_tuning_cycle()
        
        return {
            "recommendations": [
                {
                    "action": rec.action.value,
                    "target": rec.target,
                    "current_value": rec.current_value,
                    "recommended_value": rec.recommended_value,
                    "confidence": rec.confidence,
                    "reasoning": rec.reasoning,
                    "priority": rec.priority
                }
                for rec in recommendations
            ],
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error running tuning cycle: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/v1/resources/summary")
async def get_resource_summary(time_window_minutes: int = 60):
    """Get resource usage summary"""
    try:
        if resource_monitor is None:
            raise HTTPException(status_code=503, detail="Resource monitor not available")
        
        summary = await resource_monitor.get_resource_summary(time_window_minutes)
        return {
            "resource_summary": summary,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting resource summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/v1/resources/alerts")
async def get_resource_alerts(
    resolved: Optional[bool] = None,
    time_window_minutes: Optional[int] = None
):
    """Get resource usage alerts"""
    try:
        if resource_monitor is None:
            raise HTTPException(status_code=503, detail="Resource monitor not available")
        
        alerts = await resource_monitor.get_alerts(resolved, time_window_minutes)
        return {
            "alerts": alerts,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting resource alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/v1/models/recommendations")
async def get_model_recommendations(
    prompt: str,
    strategy: str = "adaptive",
    top_n: int = 3
):
    """Get model recommendations for a given prompt"""
    try:
        if router is None:
            raise HTTPException(status_code=503, detail="Model router not available")
        
        # Parse strategy
        try:
            optimization_strategy = OptimizationStrategy(strategy.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid optimization strategy")
        
        # Create request features
        request_features = {
            "estimated_tokens": len(prompt.split()),
            "creativity_requirement": 0.5,
            "reasoning_requirement": 0.7,
            "requires_code": "code" in prompt.lower(),
            "requires_vision": "image" in prompt.lower()
        }
        
        # Get recommendations
        available_models = list(ModelType)
        recommendations = router.get_model_recommendations(
            request_features=request_features,
            available_models=available_models,
            top_n=top_n
        )
        
        return {
            "prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
            "strategy": strategy,
            "recommendations": [
                {
                    "rank": i + 1,
                    "model": rec.selected_model.value,
                    "confidence": rec.confidence_score,
                    "expected_improvement": rec.expected_improvement,
                    "reasoning": rec.reasoning
                }
                for i, rec in enumerate(recommendations)
            ],
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Error getting model recommendations: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/v1/metrics/export")
async def export_metrics(
    format_type: str = "json",
    time_window_minutes: Optional[int] = None,
    monitor: RedisPerformanceMonitor = Depends(get_monitor)
):
    """Export performance metrics"""
    try:
        if format_type not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        # Note: This is a simplified implementation
        # In a real system, you'd integrate with the actual metrics storage
        return {
            "message": f"Metrics export in {format_type} format",
            "time_window_minutes": time_window_minutes,
            "timestamp": datetime.now(),
            "note": "Full export functionality would be implemented with actual metrics storage"
        }
        
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    import random
    
    uvicorn.run(app, host="0.0.0.0", port=8000)