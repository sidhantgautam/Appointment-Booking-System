"""
Performance Monitoring Service
Tracks and logs latency for all AI pipeline components
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import json
import os
from contextlib import contextmanager

# Set up performance logging
performance_logger = logging.getLogger('performance')
performance_handler = logging.FileHandler('logs/performance.log')
performance_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
performance_handler.setFormatter(performance_formatter)
performance_logger.addHandler(performance_handler)
performance_logger.setLevel(logging.INFO)

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
        self.duration = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = (self.end_time - self.start_time) * 1000  # Convert to milliseconds
    
    def get_duration_ms(self) -> float:
        """Get duration in milliseconds"""
        return self.duration if self.duration is not None else 0.0


class LatencyTracker:
    """Tracks latency for different components of the AI pipeline"""
    
    def __init__(self, request_id: str = None):
        self.request_id = request_id or f"req_{int(time.time() * 1000)}"
        self.timings = {}
        self.metadata = {}
        self.start_time = time.perf_counter()
    
    def time_operation(self, operation_name: str):
        """Get a timer for a specific operation"""
        return PerformanceTimer(operation_name)
    
    def record_timing(self, operation_name: str, duration_ms: float, metadata: Dict = None):
        """Record timing for an operation"""
        self.timings[operation_name] = {
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata to the request"""
        self.metadata[key] = value
    
    def get_total_duration(self) -> float:
        """Get total request duration"""
        return (time.perf_counter() - self.start_time) * 1000
    
    def get_summary(self) -> Dict:
        """Get performance summary"""
        total_duration = self.get_total_duration()
        
        summary = {
            "request_id": self.request_id,
            "total_duration_ms": round(total_duration, 2),
            "timestamp": datetime.now().isoformat(),
            "timings": self.timings,
            "metadata": self.metadata
        }
        
        # Calculate breakdown percentages
        if self.timings:
            for operation, timing in self.timings.items():
                percentage = (timing["duration_ms"] / total_duration) * 100
                timing["percentage"] = round(percentage, 1)
        
        return summary
    
    def log_performance(self, log_level: str = "INFO"):
        """Log performance data"""
        summary = self.get_summary()
        
        # Log to performance logger
        performance_logger.info(json.dumps(summary))
        
        if summary["total_duration_ms"] > 1000:  # Log if > 1 second
            logging.warning(f"High latency detected: {summary['total_duration_ms']}ms for request {self.request_id}")
        
        return summary


# Global performance tracking
class PerformanceMonitor:
    """Global performance monitoring"""
    
    @staticmethod
    def create_tracker(request_id: str = None) -> LatencyTracker:
        """Create a new latency tracker"""
        return LatencyTracker(request_id)
    
    @staticmethod
    def log_voice_pipeline_performance(
        request_id: str,
        stt_duration: float,
        translation_duration: float,
        llm_duration: float,
        total_duration: float,
        metadata: Dict = None
    ):
        """Log voice pipeline performance"""
        
        performance_data = {
            "request_id": request_id,
            "pipeline": "voice",
            "total_duration_ms": round(total_duration, 2),
            "components": {
                "stt_processing": round(stt_duration, 2),
                "translation": round(translation_duration, 2),
                "llm_reasoning": round(llm_duration, 2)
            },
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate percentages
        components_copy = dict(performance_data["components"])
        for component, duration in components_copy.items():
            percentage = (duration / total_duration) * 100
            performance_data["components"][f"{component}_percentage"] = round(percentage, 1)
        
        # Log performance
        performance_logger.info(json.dumps(performance_data))
        
        target_latency = 450
        if total_duration > target_latency:
            logging.warning(
                f"Voice pipeline exceeded target latency: {total_duration:.2f}ms > {target_latency}ms "
                f"(Request: {request_id})"
            )
        
        return performance_data
    
    @staticmethod
    def log_text_pipeline_performance(
        request_id: str,
        translation_duration: float,
        llm_duration: float,
        total_duration: float,
        metadata: Dict = None
    ):
        """Log text pipeline performance"""
        
        performance_data = {
            "request_id": request_id,
            "pipeline": "text",
            "total_duration_ms": round(total_duration, 2),
            "components": {
                "translation": round(translation_duration, 2),
                "llm_reasoning": round(llm_duration, 2)
            },
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate percentages
        components_copy = dict(performance_data["components"])
        for component, duration in components_copy.items():
            percentage = (duration / total_duration) * 100
            performance_data["components"][f"{component}_percentage"] = round(percentage, 1)
        
        # Log performance
        performance_logger.info(json.dumps(performance_data))
        
        return performance_data
    
    @staticmethod
    def get_performance_stats(hours: int = 24) -> Dict:
        """Get performance statistics for the last N hours"""
        
        # For now, we'll return a placeholder
        
        return {
            "period_hours": hours,
            "total_requests": 0,
            "average_latency_ms": 0,
            "p95_latency_ms": 0,
            "p99_latency_ms": 0,
            "target_latency_ms": 450,
            "requests_within_target": 0,
            "requests_over_target": 0,
            "component_breakdown": {
                "stt_avg_ms": 0,
                "translation_avg_ms": 0,
                "llm_avg_ms": 0
            }
        }


def track_performance(operation_name: str):
    """Decorator to track performance of a function"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceTimer(operation_name) as timer:
                result = func(*args, **kwargs)
            
            # Log the timing
            logging.info(f"{operation_name} completed in {timer.get_duration_ms():.2f}ms")
            
            return result
        return wrapper
    return decorator


@contextmanager
def performance_context(operation_name: str, tracker: LatencyTracker = None):
    """Context manager for tracking performance"""
    with PerformanceTimer(operation_name) as timer:
        yield timer
    
    if tracker:
        tracker.record_timing(operation_name, timer.get_duration_ms())