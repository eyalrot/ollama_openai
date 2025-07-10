"""
Performance regression tests for metrics system.
"""

import asyncio
import pytest
from src.utils.benchmarks import MetricsBenchmark


class TestMetricsPerformance:
    """Performance regression tests."""
    
    @pytest.mark.asyncio
    async def test_simple_tracking_overhead(self):
        """Test that simple tracking has minimal overhead."""
        benchmark = MetricsBenchmark()
        
        # Run with fewer iterations for CI
        baseline = await benchmark._benchmark_baseline(50)
        tracking = await benchmark._benchmark_simple_tracking(50)
        
        # Calculate overhead
        overhead = (tracking.avg_time_ms - baseline.avg_time_ms) / baseline.avg_time_ms * 100
        
        # Should be less than 50% overhead
        assert overhead < 50.0, f"Simple tracking overhead too high: {overhead:.2f}%"
    
    @pytest.mark.asyncio
    async def test_memory_usage_bounded(self):
        """Test that memory usage remains bounded."""
        benchmark = MetricsBenchmark()
        
        # Run memory stress test
        result = await benchmark._benchmark_memory_stress(100)
        
        # Memory usage should be minimal (less than 10MB)
        assert result.memory_usage_mb < 10.0, f"Memory usage too high: {result.memory_usage_mb:.2f}MB"
    
    @pytest.mark.asyncio
    async def test_concurrent_tracking_scales(self):
        """Test that concurrent tracking scales reasonably."""
        benchmark = MetricsBenchmark()
        
        # Run concurrent benchmark
        result = await benchmark._benchmark_concurrent_tracking(10)
        
        # Should complete in reasonable time (less than 100ms average)
        assert result.avg_time_ms < 100.0, f"Concurrent tracking too slow: {result.avg_time_ms:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_system_metrics_overhead(self):
        """Test that system metrics collection has reasonable overhead."""
        benchmark = MetricsBenchmark()
        
        baseline = await benchmark._benchmark_baseline(50)
        system_metrics = await benchmark._benchmark_system_metrics(50)
        
        # Calculate overhead
        overhead = (system_metrics.avg_time_ms - baseline.avg_time_ms) / baseline.avg_time_ms * 100
        
        # Should be less than 100% overhead
        assert overhead < 100.0, f"System metrics overhead too high: {overhead:.2f}%"