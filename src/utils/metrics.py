"""
Performance monitoring and metrics collection system.

This module provides lightweight, non-blocking metrics collection for tracking
request performance, system health, and application statistics.
"""

import asyncio
import logging
import threading
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics that can be collected."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class StreamingMetrics:
    """Metrics specific to streaming responses."""

    is_streaming: bool = False
    first_byte_time_ms: float = 0
    last_byte_time_ms: float = 0
    total_chunks: int = 0
    chunk_sizes: List[int] = field(default_factory=list)
    throughput_bytes_per_second: float = 0
    stream_cancelled: bool = False
    stream_timeout: bool = False
    avg_chunk_size: float = 0
    max_chunk_size: int = 0
    min_chunk_size: int = 0


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
    streaming: Optional[StreamingMetrics] = None


@dataclass
class SystemMetrics:
    """System-level metrics."""

    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    memory_usage_bytes: int = 0
    disk_usage: float = 0.0
    active_requests: int = 0
    total_requests: int = 0
    error_rate: float = 0.0
    network_io: Dict[str, int] = field(default_factory=dict)
    disk_io: Dict[str, int] = field(default_factory=dict)
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
        return self.buffer[self._index :] + self.buffer[: self._index]

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

        # System metrics tracking
        self._system_metrics = SystemMetrics()
        self._system_metrics_lock = threading.Lock()
        self._system_metrics_thread = None
        self._stop_system_metrics = threading.Event()
        self._start_system_metrics_collection()

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

    def _start_system_metrics_collection(self) -> None:
        """Start background system metrics collection."""
        if (
            self._system_metrics_thread is None
            or not self._system_metrics_thread.is_alive()
        ):
            self._system_metrics_thread = threading.Thread(
                target=self._collect_system_metrics, daemon=True
            )
            self._system_metrics_thread.start()

    def _collect_system_metrics(self) -> None:
        """Background thread to collect system metrics."""
        while not self._stop_system_metrics.is_set():
            try:
                # Collect CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)

                # Collect memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_bytes = memory.used

                # Collect disk usage
                disk = psutil.disk_usage("/")
                disk_percent = (disk.used / disk.total) * 100

                # Collect network I/O
                net_io = psutil.net_io_counters()
                network_io = {
                    "bytes_sent": net_io.bytes_sent,
                    "bytes_recv": net_io.bytes_recv,
                    "packets_sent": net_io.packets_sent,
                    "packets_recv": net_io.packets_recv,
                }

                # Collect disk I/O
                disk_io_counters = psutil.disk_io_counters()
                disk_io = (
                    {
                        "read_bytes": disk_io_counters.read_bytes,
                        "write_bytes": disk_io_counters.write_bytes,
                        "read_count": disk_io_counters.read_count,
                        "write_count": disk_io_counters.write_count,
                    }
                    if disk_io_counters
                    else {}
                )

                # Update system metrics
                with self._system_metrics_lock:
                    self._system_metrics.cpu_usage = cpu_percent
                    self._system_metrics.memory_usage = memory_percent
                    self._system_metrics.memory_usage_bytes = memory_bytes
                    self._system_metrics.disk_usage = disk_percent
                    self._system_metrics.network_io = network_io
                    self._system_metrics.disk_io = disk_io
                    self._system_metrics.active_requests = self._active_requests
                    self._system_metrics.total_requests = self._total_requests
                    self._system_metrics.timestamp = datetime.now(timezone.utc)

                # Sleep for 5 seconds between collections
                self._stop_system_metrics.wait(5)

            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                self._stop_system_metrics.wait(5)

    def _get_current_system_metrics(self) -> SystemMetrics:
        """Get the current system metrics snapshot."""
        with self._system_metrics_lock:
            return SystemMetrics(
                cpu_usage=self._system_metrics.cpu_usage,
                memory_usage=self._system_metrics.memory_usage,
                memory_usage_bytes=self._system_metrics.memory_usage_bytes,
                disk_usage=self._system_metrics.disk_usage,
                active_requests=self._active_requests,
                total_requests=self._total_requests,
                error_rate=self._calculate_error_rate(),
                network_io=self._system_metrics.network_io.copy(),
                disk_io=self._system_metrics.disk_io.copy(),
                timestamp=datetime.now(timezone.utc),
            )

    def _calculate_error_rate(self) -> float:
        """Calculate current error rate from recent metrics."""
        metrics = self._metrics_buffer.get_all()
        if not metrics:
            return 0.0

        # Calculate error rate from recent metrics (last 5 minutes)
        recent_time = datetime.now(timezone.utc)
        five_minutes_ago = recent_time.replace(minute=recent_time.minute - 5)

        recent_metrics = [m for m in metrics if m.timestamp >= five_minutes_ago]
        if not recent_metrics:
            return 0.0

        error_count = sum(1 for m in recent_metrics if m.error or m.status_code >= 400)
        return error_count / len(recent_metrics)

    def _get_system_metrics_dict(self) -> Dict[str, Any]:
        """Get system metrics as a dictionary."""
        sys_metrics = self._get_current_system_metrics()
        return {
            "cpu_usage_percent": sys_metrics.cpu_usage,
            "memory_usage_percent": sys_metrics.memory_usage,
            "memory_usage_bytes": sys_metrics.memory_usage_bytes,
            "disk_usage_percent": sys_metrics.disk_usage,
            "network_io": sys_metrics.network_io,
            "disk_io": sys_metrics.disk_io,
            "system_timestamp": sys_metrics.timestamp.isoformat(),
        }

    async def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        async with self._lock:
            metrics = self._metrics_buffer.get_all()

            if not metrics:
                return {
                    "message": "No metrics available",
                    "active_requests": self._active_requests,
                    "total_requests": self._total_requests,
                    "uptime_seconds": (
                        datetime.now(timezone.utc) - self._start_time
                    ).total_seconds(),
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

            # Group by endpoint and collect streaming stats
            endpoints = {}
            streaming_stats = {
                "total_streaming_requests": 0,
                "avg_first_byte_time_ms": 0,
                "avg_throughput_bytes_per_second": 0,
                "total_chunks": 0,
                "cancelled_streams": 0,
                "timeout_streams": 0,
                "avg_chunk_size": 0,
            }

            streaming_metrics = []
            for metric in metrics:
                key = f"{metric.method} {metric.endpoint}"
                if key not in endpoints:
                    endpoints[key] = {
                        "count": 0,
                        "avg_duration_ms": 0,
                        "errors": 0,
                        "models": set(),
                        "streaming_requests": 0,
                    }

                endpoints[key]["count"] += 1
                endpoints[key]["avg_duration_ms"] += metric.duration_ms
                if metric.error:
                    endpoints[key]["errors"] += 1
                if metric.model:
                    endpoints[key]["models"].add(metric.model)

                # Collect streaming statistics
                if metric.streaming and metric.streaming.is_streaming:
                    endpoints[key]["streaming_requests"] += 1
                    streaming_stats["total_streaming_requests"] += 1
                    streaming_metrics.append(metric.streaming)

                    if metric.streaming.stream_cancelled:
                        streaming_stats["cancelled_streams"] += 1
                    if metric.streaming.stream_timeout:
                        streaming_stats["timeout_streams"] += 1

                    streaming_stats["total_chunks"] += metric.streaming.total_chunks

            # Calculate streaming averages
            if streaming_metrics:
                first_byte_times = [
                    s.first_byte_time_ms
                    for s in streaming_metrics
                    if s.first_byte_time_ms > 0
                ]
                throughputs = [
                    s.throughput_bytes_per_second
                    for s in streaming_metrics
                    if s.throughput_bytes_per_second > 0
                ]
                chunk_sizes = [
                    s.avg_chunk_size for s in streaming_metrics if s.avg_chunk_size > 0
                ]

                if first_byte_times:
                    streaming_stats["avg_first_byte_time_ms"] = sum(
                        first_byte_times
                    ) / len(first_byte_times)
                if throughputs:
                    streaming_stats["avg_throughput_bytes_per_second"] = sum(
                        throughputs
                    ) / len(throughputs)
                if chunk_sizes:
                    streaming_stats["avg_chunk_size"] = sum(chunk_sizes) / len(
                        chunk_sizes
                    )

            # Calculate averages and convert sets to lists
            for endpoint_data in endpoints.values():
                if endpoint_data["count"] > 0:
                    endpoint_data["avg_duration_ms"] /= endpoint_data["count"]
                    endpoint_data["error_rate"] = (
                        endpoint_data["errors"] / endpoint_data["count"]
                    )
                endpoint_data["models"] = list(endpoint_data["models"])

            return {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (
                    successful_requests / total_requests if total_requests > 0 else 0
                ),
                "error_rate": (
                    failed_requests / total_requests if total_requests > 0 else 0
                ),
                "active_requests": self._active_requests,
                "global_total_requests": self._total_requests,
                "performance": {
                    "avg_duration_ms": avg_duration,
                    "p50_duration_ms": p50,
                    "p95_duration_ms": p95,
                    "p99_duration_ms": p99,
                    "min_duration_ms": min(durations) if durations else 0,
                    "max_duration_ms": max(durations) if durations else 0,
                },
                "streaming": streaming_stats,
                "endpoints": endpoints,
                "period": {
                    "start": metrics[0].timestamp.isoformat() if metrics else None,
                    "end": metrics[-1].timestamp.isoformat() if metrics else None,
                    "duration_seconds": (
                        (metrics[-1].timestamp - metrics[0].timestamp).total_seconds()
                        if len(metrics) > 1
                        else 0
                    ),
                },
                "system": {
                    "buffer_size": self._metrics_buffer.size(),
                    "buffer_full": self._metrics_buffer.is_full(),
                    "max_buffer_size": self.max_metrics,
                    "uptime_seconds": (
                        datetime.now(timezone.utc) - self._start_time
                    ).total_seconds(),
                    **self._get_system_metrics_dict(),
                },
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
            "",
            "# HELP http_request_error_rate Error rate of HTTP requests",
            "# TYPE http_request_error_rate gauge",
            f"http_request_error_rate {summary['error_rate']}",
            "",
            "# HELP http_request_duration_p50_seconds 50th percentile request duration",
            "# TYPE http_request_duration_p50_seconds gauge",
            f"http_request_duration_p50_seconds {summary['performance']['p50_duration_ms'] / 1000}",
            "",
            "# HELP http_request_duration_p95_seconds 95th percentile request duration",
            "# TYPE http_request_duration_p95_seconds gauge",
            f"http_request_duration_p95_seconds {summary['performance']['p95_duration_ms'] / 1000}",
            "",
            "# HELP http_request_duration_p99_seconds 99th percentile request duration",
            "# TYPE http_request_duration_p99_seconds gauge",
            f"http_request_duration_p99_seconds {summary['performance']['p99_duration_ms'] / 1000}",
            "",
            "# HELP system_cpu_usage_percent CPU usage percentage",
            "# TYPE system_cpu_usage_percent gauge",
            f"system_cpu_usage_percent {summary['system']['cpu_usage_percent']}",
            "",
            "# HELP system_memory_usage_percent Memory usage percentage",
            "# TYPE system_memory_usage_percent gauge",
            f"system_memory_usage_percent {summary['system']['memory_usage_percent']}",
            "",
            "# HELP system_memory_usage_bytes Memory usage in bytes",
            "# TYPE system_memory_usage_bytes gauge",
            f"system_memory_usage_bytes {summary['system']['memory_usage_bytes']}",
            "",
            "# HELP system_disk_usage_percent Disk usage percentage",
            "# TYPE system_disk_usage_percent gauge",
            f"system_disk_usage_percent {summary['system']['disk_usage_percent']}",
            "",
            "# HELP system_uptime_seconds System uptime in seconds",
            "# TYPE system_uptime_seconds counter",
            f"system_uptime_seconds {summary['system']['uptime_seconds']}",
        ]

        # Add network I/O metrics
        network_io = summary["system"].get("network_io", {})
        if network_io:
            lines.extend(
                [
                    "",
                    "# HELP network_bytes_sent_total Total network bytes sent",
                    "# TYPE network_bytes_sent_total counter",
                    f"network_bytes_sent_total {network_io.get('bytes_sent', 0)}",
                    "",
                    "# HELP network_bytes_recv_total Total network bytes received",
                    "# TYPE network_bytes_recv_total counter",
                    f"network_bytes_recv_total {network_io.get('bytes_recv', 0)}",
                ]
            )

        # Add disk I/O metrics
        disk_io = summary["system"].get("disk_io", {})
        if disk_io:
            lines.extend(
                [
                    "",
                    "# HELP disk_read_bytes_total Total disk bytes read",
                    "# TYPE disk_read_bytes_total counter",
                    f"disk_read_bytes_total {disk_io.get('read_bytes', 0)}",
                    "",
                    "# HELP disk_write_bytes_total Total disk bytes written",
                    "# TYPE disk_write_bytes_total counter",
                    f"disk_write_bytes_total {disk_io.get('write_bytes', 0)}",
                ]
            )

        # Add streaming metrics
        streaming = summary.get("streaming", {})
        if streaming.get("total_streaming_requests", 0) > 0:
            lines.extend(
                [
                    "",
                    "# HELP http_streaming_requests_total Total streaming requests",
                    "# TYPE http_streaming_requests_total counter",
                    f"http_streaming_requests_total {streaming['total_streaming_requests']}",
                    "",
                    "# HELP http_streaming_first_byte_time_seconds Average first byte time for streaming requests",
                    "# TYPE http_streaming_first_byte_time_seconds gauge",
                    f"http_streaming_first_byte_time_seconds {streaming['avg_first_byte_time_ms'] / 1000}",
                    "",
                    "# HELP http_streaming_throughput_bytes_per_second Average throughput for streaming requests",
                    "# TYPE http_streaming_throughput_bytes_per_second gauge",
                    f"http_streaming_throughput_bytes_per_second {streaming['avg_throughput_bytes_per_second']}",
                    "",
                    "# HELP http_streaming_chunks_total Total chunks processed in streaming requests",
                    "# TYPE http_streaming_chunks_total counter",
                    f"http_streaming_chunks_total {streaming['total_chunks']}",
                    "",
                    "# HELP http_streaming_cancelled_total Total cancelled streaming requests",
                    "# TYPE http_streaming_cancelled_total counter",
                    f"http_streaming_cancelled_total {streaming['cancelled_streams']}",
                    "",
                    "# HELP http_streaming_timeout_total Total timed out streaming requests",
                    "# TYPE http_streaming_timeout_total counter",
                    f"http_streaming_timeout_total {streaming['timeout_streams']}",
                    "",
                    "# HELP http_streaming_avg_chunk_size_bytes Average chunk size for streaming requests",
                    "# TYPE http_streaming_avg_chunk_size_bytes gauge",
                    f"http_streaming_avg_chunk_size_bytes {streaming['avg_chunk_size']}",
                ]
            )

        # Add per-endpoint metrics
        for endpoint, stats in summary["endpoints"].items():
            lines.extend(
                [
                    "",
                    f"# HELP http_requests_per_endpoint_total Total requests for {endpoint}",
                    "# TYPE http_requests_per_endpoint_total counter",
                    f"http_requests_per_endpoint_total{{endpoint=\"{endpoint}\"}} {stats['count']}",
                    "",
                    f"# HELP http_request_duration_per_endpoint_seconds Average duration for {endpoint}",
                    "# TYPE http_request_duration_per_endpoint_seconds gauge",
                    f"http_request_duration_per_endpoint_seconds{{endpoint=\"{endpoint}\"}} {stats['avg_duration_ms'] / 1000}",
                    "",
                    f"# HELP http_request_errors_per_endpoint_total Total errors for {endpoint}",
                    "# TYPE http_request_errors_per_endpoint_total counter",
                    f"http_request_errors_per_endpoint_total{{endpoint=\"{endpoint}\"}} {stats['errors']}",
                ]
            )

            # Add streaming metrics per endpoint
            if stats.get("streaming_requests", 0) > 0:
                lines.extend(
                    [
                        "",
                        f"# HELP http_streaming_requests_per_endpoint_total Streaming requests for {endpoint}",
                        "# TYPE http_streaming_requests_per_endpoint_total counter",
                        f"http_streaming_requests_per_endpoint_total{{endpoint=\"{endpoint}\"}} {stats['streaming_requests']}",
                    ]
                )

        return "\n".join(lines)

    async def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        async with self._lock:
            self._metrics_buffer = CircularBuffer(self.max_metrics)
            self._active_requests = 0
            self._total_requests = 0
            self._start_time = datetime.now(timezone.utc)

    def stop(self) -> None:
        """Stop system metrics collection."""
        self._stop_system_metrics.set()
        if self._system_metrics_thread and self._system_metrics_thread.is_alive():
            self._system_metrics_thread.join(timeout=5)

    async def get_filtered_summary(
        self,
        endpoint_filter: Optional[str] = None,
        time_range_minutes: Optional[int] = None,
        include_system_metrics: bool = True,
    ) -> Dict[str, Any]:
        """Get filtered metrics summary with optional filtering."""
        async with self._lock:
            metrics = self._metrics_buffer.get_all()

            # Apply time range filter
            if time_range_minutes:
                cutoff_time = datetime.now(timezone.utc).replace(
                    minute=datetime.now(timezone.utc).minute - time_range_minutes
                )
                metrics = [m for m in metrics if m.timestamp >= cutoff_time]

            # Apply endpoint filter
            if endpoint_filter:
                metrics = [
                    m for m in metrics if endpoint_filter.lower() in m.endpoint.lower()
                ]

            if not metrics:
                base_summary = {
                    "message": "No metrics available for specified filters",
                    "filters": {
                        "endpoint_filter": endpoint_filter,
                        "time_range_minutes": time_range_minutes,
                    },
                    "active_requests": self._active_requests,
                    "total_requests": self._total_requests,
                    "uptime_seconds": (
                        datetime.now(timezone.utc) - self._start_time
                    ).total_seconds(),
                }

                if include_system_metrics:
                    base_summary["system"] = self._get_system_metrics_dict()

                return base_summary

            # Calculate filtered statistics
            total_requests = len(metrics)
            successful_requests = sum(1 for m in metrics if 200 <= m.status_code < 300)
            failed_requests = total_requests - successful_requests

            durations = [m.duration_ms for m in metrics]
            avg_duration = sum(durations) / len(durations) if durations else 0

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
                        "models": set(),
                    }

                endpoints[key]["count"] += 1
                endpoints[key]["avg_duration_ms"] += metric.duration_ms
                if metric.error:
                    endpoints[key]["errors"] += 1
                if metric.model:
                    endpoints[key]["models"].add(metric.model)

            # Calculate averages
            for endpoint_data in endpoints.values():
                if endpoint_data["count"] > 0:
                    endpoint_data["avg_duration_ms"] /= endpoint_data["count"]
                    endpoint_data["error_rate"] = (
                        endpoint_data["errors"] / endpoint_data["count"]
                    )
                endpoint_data["models"] = list(endpoint_data["models"])

            summary = {
                "filters": {
                    "endpoint_filter": endpoint_filter,
                    "time_range_minutes": time_range_minutes,
                    "include_system_metrics": include_system_metrics,
                },
                "filtered_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate": (
                    successful_requests / total_requests if total_requests > 0 else 0
                ),
                "error_rate": (
                    failed_requests / total_requests if total_requests > 0 else 0
                ),
                "global_active_requests": self._active_requests,
                "global_total_requests": self._total_requests,
                "performance": {
                    "avg_duration_ms": avg_duration,
                    "p50_duration_ms": p50,
                    "p95_duration_ms": p95,
                    "p99_duration_ms": p99,
                    "min_duration_ms": min(durations) if durations else 0,
                    "max_duration_ms": max(durations) if durations else 0,
                },
                "endpoints": endpoints,
                "period": {
                    "start": metrics[0].timestamp.isoformat() if metrics else None,
                    "end": metrics[-1].timestamp.isoformat() if metrics else None,
                    "duration_seconds": (
                        (metrics[-1].timestamp - metrics[0].timestamp).total_seconds()
                        if len(metrics) > 1
                        else 0
                    ),
                },
            }

            if include_system_metrics:
                summary["system"] = {
                    "buffer_size": self._metrics_buffer.size(),
                    "buffer_full": self._metrics_buffer.is_full(),
                    "max_buffer_size": self.max_metrics,
                    "uptime_seconds": (
                        datetime.now(timezone.utc) - self._start_time
                    ).total_seconds(),
                    **self._get_system_metrics_dict(),
                }

            return summary


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


class StreamingResponseWrapper:
    """
    Wrapper for streaming responses to collect metrics without buffering.
    """

    def __init__(
        self, response_stream, metric: RequestMetrics, collector: MetricsCollector
    ):
        self.response_stream = response_stream
        self.metric = metric
        self.collector = collector
        self.start_time = time.time()
        self.first_byte_time = None
        self.last_byte_time = None
        self.chunk_count = 0
        self.total_bytes = 0
        self.chunk_sizes = []
        self.cancelled = False
        self.timeout = False
        self.max_chunks_to_track = 100  # Limit memory usage

        # Initialize streaming metrics
        self.metric.streaming = StreamingMetrics(is_streaming=True)

    async def __aiter__(self):
        """Async iterator for streaming response."""
        try:
            async for chunk in self.response_stream:
                if self.first_byte_time is None:
                    self.first_byte_time = time.time()
                    self.metric.streaming.first_byte_time_ms = (
                        self.first_byte_time - self.start_time
                    ) * 1000

                self.last_byte_time = time.time()
                chunk_size = len(chunk) if isinstance(chunk, (bytes, str)) else 0
                self.chunk_count += 1
                self.total_bytes += chunk_size

                # Sample chunk sizes to avoid memory issues
                if len(self.chunk_sizes) < self.max_chunks_to_track:
                    self.chunk_sizes.append(chunk_size)

                yield chunk

        except asyncio.CancelledError:
            self.cancelled = True
            raise
        except asyncio.TimeoutError:
            self.timeout = True
            raise
        except Exception as e:
            self.metric.error = str(e)
            raise
        finally:
            await self._finalize_metrics()

    async def _finalize_metrics(self):
        """Finalize streaming metrics."""
        if self.last_byte_time and self.first_byte_time:
            stream_duration = self.last_byte_time - self.first_byte_time
            self.metric.streaming.last_byte_time_ms = (
                self.last_byte_time - self.start_time
            ) * 1000

            # Calculate throughput
            if stream_duration > 0:
                self.metric.streaming.throughput_bytes_per_second = (
                    self.total_bytes / stream_duration
                )

        # Update streaming metrics
        self.metric.streaming.total_chunks = self.chunk_count
        self.metric.streaming.chunk_sizes = self.chunk_sizes
        self.metric.streaming.stream_cancelled = self.cancelled
        self.metric.streaming.stream_timeout = self.timeout
        self.metric.response_size = self.total_bytes

        # Calculate chunk statistics
        if self.chunk_sizes:
            self.metric.streaming.avg_chunk_size = sum(self.chunk_sizes) / len(
                self.chunk_sizes
            )
            self.metric.streaming.max_chunk_size = max(self.chunk_sizes)
            self.metric.streaming.min_chunk_size = min(self.chunk_sizes)


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


@asynccontextmanager
async def track_streaming_request(endpoint: str, method: str, model: str = ""):
    """
    Context manager for tracking streaming request metrics.

    Usage:
        async with track_streaming_request("/api/chat", "POST", "gpt-4") as (metric, wrapper_factory):
            # ... perform request setup ...
            metric.status_code = 200
            metric.request_size = len(request_data)

            # Wrap the streaming response
            streaming_response = wrapper_factory(response_stream)
            async for chunk in streaming_response:
                # ... process chunk ...
                pass
    """
    collector = get_metrics_collector()
    await collector.increment_active_requests()

    start_time = time.time()
    metric = RequestMetrics(endpoint=endpoint, method=method, model=model)

    def create_wrapper(response_stream):
        return StreamingResponseWrapper(response_stream, metric, collector)

    try:
        yield metric, create_wrapper
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


async def get_filtered_metrics_summary(
    endpoint_filter: Optional[str] = None,
    time_range_minutes: Optional[int] = None,
    include_system_metrics: bool = True,
) -> Dict[str, Any]:
    """Get filtered metrics summary."""
    collector = get_metrics_collector()
    return await collector.get_filtered_summary(
        endpoint_filter=endpoint_filter,
        time_range_minutes=time_range_minutes,
        include_system_metrics=include_system_metrics,
    )


async def get_prometheus_metrics() -> str:
    """Get metrics in Prometheus format."""
    collector = get_metrics_collector()
    return await collector.get_prometheus_metrics()


async def reset_metrics() -> None:
    """Reset all metrics (useful for testing)."""
    collector = get_metrics_collector()
    await collector.reset()


def stop_metrics_collection() -> None:
    """Stop metrics collection (useful for cleanup)."""
    global _metrics_collector
    if _metrics_collector:
        _metrics_collector.stop()
        _metrics_collector = None
