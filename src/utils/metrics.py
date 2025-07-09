"""
Performance monitoring and metrics collection system.

This module provides lightweight, non-blocking metrics collection for tracking
request performance, system health, and application statistics.
"""

import time
import asyncio
from typing import Dict, Any, List, Optional, Union
from contextlib import asynccontextmanager
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class RequestMetrics:
    """Metrics for individual HTTP requests."""
    endpoint: str
    method: str
    status_code: int = 0
    duration_ms: float = 0
    request_size: int = 0
    response_size: int = 0
    model: str = ""
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SystemMetrics:
    """System-level metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    active_requests: int = 0
    total_requests: int = 0
    error_rate: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class CircularBuffer:
    """Memory-efficient circular buffer for metrics storage."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.buffer: List[RequestMetrics] = []
        self._index = 0
        self._full = False
    
    def append(self, item: RequestMetrics) -> None:
        """Add item to buffer, overwriting oldest if full."""
        if len(self.buffer) < self.max_size:
            self.buffer.append(item)
        else:
            self.buffer[self._index] = item
            self._index = (self._index + 1) % self.max_size
            self._full = True
    
    def get_all(self) -> List[RequestMetrics]:
        """Get all items in chronological order."""
        if not self._full:
            return self.buffer.copy()
        
        # Return items in chronological order
        return self.buffer[self._index:] + self.buffer[:self._index]
    
    def size(self) -> int:
        """Get current buffer size."""
        return len(self.buffer)
    
    def is_full(self) -> bool:
        """Check if buffer is at capacity."""
        return self._full


class MetricsCollector:
    """
    Lightweight, thread-safe metrics collection system.
    
    Features:
    - Non-blocking async operations
    - Memory-bounded storage with circular buffer
    - Configurable retention policies
    - Automatic metric aggregation
    """
    
    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self._metrics_buffer = CircularBuffer(max_metrics)
        self._lock = asyncio.Lock()
        self._active_requests = 0
        self._total_requests = 0
        self._start_time = datetime.now(timezone.utc)
        
    async def record_request(self, metric: RequestMetrics) -> None:
        """Record a request metric asynchronously."""
        async with self._lock:
            self._metrics_buffer.append(metric)
            self._total_requests += 1
            
            # Log significant events
            if metric.error:
                logger.warning(f"Request error: {metric.error}")
            elif metric.duration_ms > 5000:  # Log slow requests
                logger.warning(
                    f"Slow request: {metric.method} {metric.endpoint} "
                    f"took {metric.duration_ms:.2f}ms"
                )
    
    async def increment_active_requests(self) -> None:
        """Increment active request counter."""
        async with self._lock:
            self._active_requests += 1
    
    async def decrement_active_requests(self) -> None:
        """Decrement active request counter."""
        async with self._lock:
            self._active_requests = max(0, self._active_requests - 1)
    
    async def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        async with self._lock:
            metrics = self._metrics_buffer.get_all()
            
            if not metrics:
                return {
                    "message": "No metrics available",
                    "active_requests": self._active_requests,
                    "total_requests": self._total_requests,
                    "uptime_seconds": (datetime.now(timezone.utc) - self._start_time).total_seconds()
                }
            
            # Calculate basic statistics
            total_requests = len(metrics)
            successful_requests = sum(1 for m in metrics if 200 <= m.status_code < 300)
            failed_requests = total_requests - successful_requests
            
            # Calculate duration statistics
            durations = [m.duration_ms for m in metrics]
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # Calculate percentiles
            sorted_durations = sorted(durations)
            p50 = self._percentile(sorted_durations, 50)
            p95 = self._percentile(sorted_durations, 95)
            p99 = self._percentile(sorted_durations, 99)
            
            # Group by endpoint
            endpoints = {}
            for metric in metrics:
                key = f"{metric.method} {metric.endpoint}"
                if key not in endpoints:
                    endpoints[key] = {
                        "count": 0,
                        "avg_duration_ms": 0,
                        "errors": 0,
                        "models": set()
                    }
                
                endpoints[key]["count"] += 1
                endpoints[key]["avg_duration_ms"] += metric.duration_ms
                if metric.error:
                    endpoints[key]["errors"] += 1
                if metric.model:
                    endpoints[key]["models"].add(metric.model)
            
            # Calculate averages and convert sets to lists
            for endpoint_data in endpoints.values():
                if endpoint_data["count"] > 0:
                    endpoint_data["avg_duration_ms"] /= endpoint_data["count"]
                    endpoint_data["error_rate"] = endpoint_data["errors"] / endpoint_data["count"]
                endpoint_data["models"] = list(endpoint_data["models"])
            
            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": successful_requests / total_requests if total_requests > 0 else 0,
                "error_rate": failed_requests / total_requests if total_requests > 0 else 0,
                "active_requests": self._active_requests,
                "global_total_requests": self._total_requests,
                "performance": {
                    "avg_duration_ms": avg_duration,
                    "p50_duration_ms": p50,
                    "p95_duration_ms": p95,
                    "p99_duration_ms": p99,
                    "min_duration_ms": min(durations) if durations else 0,
                    "max_duration_ms": max(durations) if durations else 0
                },
                "endpoints": endpoints,
                "period": {
                    "start": metrics[0].timestamp.isoformat() if metrics else None,
                    "end": metrics[-1].timestamp.isoformat() if metrics else None,
                    "duration_seconds": (metrics[-1].timestamp - metrics[0].timestamp).total_seconds() if len(metrics) > 1 else 0
                },
                "system": {
                    "buffer_size": self._metrics_buffer.size(),
                    "buffer_full": self._metrics_buffer.is_full(),
                    "max_buffer_size": self.max_metrics,
                    "uptime_seconds": (datetime.now(timezone.utc) - self._start_time).total_seconds()
                }
            }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a sorted list."""
        if not data:
            return 0.0
        
        index = (percentile / 100) * (len(data) - 1)
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(data) - 1)
        
        if lower_index == upper_index:
            return data[lower_index]
        
        # Linear interpolation
        weight = index - lower_index
        return data[lower_index] * (1 - weight) + data[upper_index] * weight
    
    async def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        summary = await self.get_summary()
        
        lines = [
            "# HELP http_requests_total Total number of HTTP requests",
            "# TYPE http_requests_total counter",
            f"http_requests_total {summary['total_requests']}",
            "",
            "# HELP http_request_duration_seconds Request duration in seconds",
            "# TYPE http_request_duration_seconds histogram",
            f"http_request_duration_seconds_sum {summary['performance']['avg_duration_ms'] * summary['total_requests'] / 1000}",
            f"http_request_duration_seconds_count {summary['total_requests']}",
            "",
            "# HELP http_requests_active Currently active HTTP requests",
            "# TYPE http_requests_active gauge",
            f"http_requests_active {summary['active_requests']}",
            "",
            "# HELP http_request_success_rate Success rate of HTTP requests",
            "# TYPE http_request_success_rate gauge",
            f"http_request_success_rate {summary['success_rate']}",
        ]
        
        return "\n".join(lines)
    
    async def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        async with self._lock:
            self._metrics_buffer = CircularBuffer(self.max_metrics)
            self._active_requests = 0
            self._total_requests = 0
            self._start_time = datetime.now(timezone.utc)


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


@asynccontextmanager
async def track_request(endpoint: str, method: str, model: str = ""):
    """
    Context manager to track request metrics.
    
    Usage:
        async with track_request("/api/chat", "POST", "gpt-4") as metric:
            # ... perform request ...
            metric.status_code = 200
            metric.request_size = len(request_data)
            metric.response_size = len(response_data)
    """
    collector = get_metrics_collector()
    await collector.increment_active_requests()
    
    start_time = time.time()
    metric = RequestMetrics(endpoint=endpoint, method=method, model=model)
    
    try:
        yield metric
    except Exception as e:
        metric.error = str(e)
        raise
    finally:
        metric.duration_ms = (time.time() - start_time) * 1000
        await collector.record_request(metric)
        await collector.decrement_active_requests()


async def get_metrics_summary() -> Dict[str, Any]:
    """Get current metrics summary."""
    collector = get_metrics_collector()
    return await collector.get_summary()


async def get_prometheus_metrics() -> str:
    """Get metrics in Prometheus format."""
    collector = get_metrics_collector()
    return await collector.get_prometheus_metrics()


async def reset_metrics() -> None:
    """Reset all metrics (useful for testing)."""
    collector = get_metrics_collector()
    await collector.reset()