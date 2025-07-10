"""
Metrics endpoint for exposing performance and system metrics.

Provides endpoints for retrieving metrics in various formats including
JSON summary and Prometheus format.
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Response

from src.utils.metrics import (
    get_filtered_metrics_summary,
    get_metrics_summary,
    get_prometheus_metrics,
)

router = APIRouter()


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics(
    endpoint_filter: Optional[str] = Query(
        None, description="Filter metrics by endpoint path"
    ),
    time_range_minutes: Optional[int] = Query(
        None, description="Only include metrics from last N minutes"
    ),
    include_system: bool = Query(
        True, description="Include system metrics (CPU, memory, disk)"
    ),
) -> Dict[str, Any]:
    """
    Get comprehensive metrics summary in JSON format.

    Parameters:
        endpoint_filter: Optional filter to only include metrics for endpoints containing this string
        time_range_minutes: Optional filter to only include metrics from the last N minutes
        include_system: Whether to include system metrics (default: True)

    Returns:
        Detailed metrics including request statistics, performance data,
        endpoint breakdowns, and system information.
    """
    if endpoint_filter or time_range_minutes or not include_system:
        return await get_filtered_metrics_summary(
            endpoint_filter=endpoint_filter,
            time_range_minutes=time_range_minutes,
            include_system_metrics=include_system,
        )
    else:
        return await get_metrics_summary()


@router.get("/metrics/prometheus")
async def get_prometheus_format() -> Response:
    """
    Get metrics in Prometheus format for monitoring integrations.

    Returns:
        Plain text response with metrics in Prometheus exposition format.
    """
    metrics_text = await get_prometheus_metrics()
    return Response(
        content=metrics_text,
        media_type="text/plain",
        headers={"Content-Type": "text/plain; version=0.0.4"},
    )


@router.get("/metrics/health")
async def get_health_metrics() -> Dict[str, Any]:
    """
    Get essential health metrics for monitoring systems.

    Returns:
        Simplified metrics focused on service health indicators.
    """
    summary = await get_metrics_summary()

    # Extract key health indicators
    return {
        "status": "healthy" if summary.get("error_rate", 0) < 0.1 else "degraded",
        "active_requests": summary.get("active_requests", 0),
        "total_requests": summary.get("total_requests", 0),
        "success_rate": summary.get("success_rate", 0),
        "error_rate": summary.get("error_rate", 0),
        "avg_response_time_ms": summary.get("performance", {}).get(
            "avg_duration_ms", 0
        ),
        "p95_response_time_ms": summary.get("performance", {}).get(
            "p95_duration_ms", 0
        ),
        "uptime_seconds": summary.get("system", {}).get("uptime_seconds", 0),
        "buffer_utilization": (
            (
                summary.get("system", {}).get("buffer_size", 0)
                / summary.get("system", {}).get("max_buffer_size", 1)
            )
            if summary.get("system", {}).get("max_buffer_size", 0) > 0
            else 0
        ),
    }
