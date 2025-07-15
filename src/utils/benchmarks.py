"""
Performance benchmarking suite for metrics collection system.

This module provides benchmarks to measure the overhead of metrics collection
and ensure minimal impact on application performance.
"""

import asyncio
import gc
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

import psutil

from src.utils.metrics import (
    get_metrics_collector,
    reset_metrics,
    track_request,
    track_streaming_request,
)


@dataclass
class BenchmarkResult:
    """Result of a benchmark test."""

    test_name: str
    iterations: int
    total_time_seconds: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    p50_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    overhead_percent: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MetricsBenchmark:
    """
    Benchmark suite for metrics collection system.
    """

    def __init__(self):
        self.results: List[BenchmarkResult] = []
        self.baseline_result: Optional[BenchmarkResult] = None

    async def run_all_benchmarks(
        self, iterations: int = 1000
    ) -> Dict[str, BenchmarkResult]:
        """
        Run all benchmarks and return results.

        Args:
            iterations: Number of iterations per benchmark

        Returns:
            Dictionary of benchmark results
        """
        print(f"Running comprehensive benchmarks ({iterations} iterations each)...")

        # Reset metrics before benchmarking
        await reset_metrics()

        # Run benchmarks
        results = {}

        # 1. Baseline (no metrics)
        results["baseline"] = await self._benchmark_baseline(iterations)
        self.baseline_result = results["baseline"]

        # 2. Simple request tracking
        results["simple_tracking"] = await self._benchmark_simple_tracking(iterations)

        # 3. Streaming request tracking
        results["streaming_tracking"] = await self._benchmark_streaming_tracking(
            iterations
        )

        # 4. Concurrent tracking
        results["concurrent_tracking"] = await self._benchmark_concurrent_tracking(
            iterations
        )

        # 5. Memory stress test
        results["memory_stress"] = await self._benchmark_memory_stress(iterations * 10)

        # 6. System metrics overhead
        results["system_metrics"] = await self._benchmark_system_metrics(iterations)

        # Calculate overhead percentages
        for name, result in results.items():
            if name != "baseline" and self.baseline_result:
                result.overhead_percent = (
                    (result.avg_time_ms - self.baseline_result.avg_time_ms)
                    / self.baseline_result.avg_time_ms
                    * 100
                )

        self.results = list(results.values())
        return results

    async def _benchmark_baseline(self, iterations: int) -> BenchmarkResult:
        """Benchmark baseline performance without metrics."""
        print("  Running baseline benchmark...")

        async def baseline_operation():
            """Simulate basic operation without metrics."""
            await asyncio.sleep(0.001)  # Simulate minimal work
            return "response"

        return await self._run_benchmark("baseline", baseline_operation, iterations)

    async def _benchmark_simple_tracking(self, iterations: int) -> BenchmarkResult:
        """Benchmark simple request tracking."""
        print("  Running simple tracking benchmark...")

        async def tracked_operation():
            """Simulate operation with metrics tracking."""
            async with track_request("/test/endpoint", "GET", "test-model") as metric:
                await asyncio.sleep(0.001)  # Simulate work
                metric.status_code = 200
                metric.request_size = 100
                metric.response_size = 200
                return "response"

        return await self._run_benchmark(
            "simple_tracking", tracked_operation, iterations
        )

    async def _benchmark_streaming_tracking(self, iterations: int) -> BenchmarkResult:
        """Benchmark streaming request tracking."""
        print("  Running streaming tracking benchmark...")

        async def mock_stream():
            """Mock streaming response."""
            for i in range(10):
                await asyncio.sleep(0.0001)
                yield f"chunk_{i}".encode()

        async def streaming_operation():
            """Simulate streaming operation with metrics."""
            async with track_streaming_request(
                "/test/stream", "POST", "stream-model"
            ) as (metric, wrapper_factory):
                metric.status_code = 200
                metric.request_size = 500

                stream = wrapper_factory(mock_stream())
                chunks = []
                async for chunk in stream:
                    chunks.append(chunk)

                return chunks

        return await self._run_benchmark(
            "streaming_tracking", streaming_operation, iterations
        )

    async def _benchmark_concurrent_tracking(self, iterations: int) -> BenchmarkResult:
        """Benchmark concurrent request tracking."""
        print("  Running concurrent tracking benchmark...")

        async def concurrent_operation():
            """Simulate concurrent operations."""

            async def single_request(i):
                async with track_request(
                    f"/test/concurrent_{i}", "POST", "concurrent-model"
                ) as metric:
                    await asyncio.sleep(0.001)
                    metric.status_code = 200
                    metric.request_size = 150
                    metric.response_size = 300
                    return f"response_{i}"

            # Run 10 concurrent requests
            tasks = [single_request(i) for i in range(10)]
            results = await asyncio.gather(*tasks)
            return results

        return await self._run_benchmark(
            "concurrent_tracking",
            concurrent_operation,
            iterations // 10,  # Adjust for 10 concurrent requests per iteration
        )

    async def _benchmark_memory_stress(self, iterations: int) -> BenchmarkResult:
        """Benchmark memory usage under stress."""
        print("  Running memory stress benchmark...")

        async def memory_stress_operation():
            """Operation that stresses memory usage."""
            async with track_request("/test/memory", "PUT", "memory-model") as metric:
                await asyncio.sleep(0.0005)
                metric.status_code = 200
                metric.request_size = 1000
                metric.response_size = 2000
                # Simulate some memory allocation
                data = [f"data_{i}" for i in range(100)]
                return len(data)

        return await self._run_benchmark(
            "memory_stress", memory_stress_operation, iterations
        )

    async def _benchmark_system_metrics(self, iterations: int) -> BenchmarkResult:
        """Benchmark system metrics collection overhead."""
        print("  Running system metrics benchmark...")

        async def system_metrics_operation():
            """Operation while system metrics are being collected."""
            collector = get_metrics_collector()

            # Force system metrics collection
            current_metrics = collector._get_current_system_metrics()

            async with track_request("/test/system", "GET", "system-model") as metric:
                await asyncio.sleep(0.001)
                metric.status_code = 200
                metric.request_size = 80
                metric.response_size = 160
                return current_metrics

        return await self._run_benchmark(
            "system_metrics", system_metrics_operation, iterations
        )

    async def _run_benchmark(
        self, name: str, operation: Callable, iterations: int
    ) -> BenchmarkResult:
        """Run a single benchmark."""
        # Force garbage collection before benchmark
        gc.collect()

        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Warm up
        for _ in range(min(10, iterations // 10)):
            await operation()

        # Run benchmark
        times = []
        start_time = time.time()

        for i in range(iterations):
            op_start = time.time()
            await operation()
            op_end = time.time()
            times.append((op_end - op_start) * 1000)  # Convert to ms

            # Yield control periodically
            if i % 100 == 0:
                await asyncio.sleep(0)

        end_time = time.time()

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = final_memory - initial_memory

        # Calculate CPU usage (approximate)
        cpu_usage = process.cpu_percent()

        # Calculate statistics
        total_time = end_time - start_time
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        p50_time = statistics.median(times)

        # Handle cases with insufficient data points for quantiles
        if len(times) >= 2:
            try:
                p95_time = statistics.quantiles(times, n=20)[18]  # 95th percentile
            except statistics.StatisticsError:
                p95_time = statistics.median(times)

            try:
                p99_time = statistics.quantiles(times, n=100)[98]  # 99th percentile
            except statistics.StatisticsError:
                p99_time = max_time
        else:
            p95_time = max_time
            p99_time = max_time

        return BenchmarkResult(
            test_name=name,
            iterations=iterations,
            total_time_seconds=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            p50_time_ms=p50_time,
            p95_time_ms=p95_time,
            p99_time_ms=p99_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
        )

    def print_results(self, results: Dict[str, BenchmarkResult]) -> None:
        """Print benchmark results in a readable format."""
        print("\n" + "=" * 80)
        print("PERFORMANCE BENCHMARK RESULTS")
        print("=" * 80)

        # Print summary table
        print(
            f"{'Test Name':<20} {'Avg Time (ms)':<15} {'Overhead %':<12} {'Memory (MB)':<12}"
        )
        print("-" * 80)

        for name, result in results.items():
            overhead_str = (
                f"{result.overhead_percent:.2f}%"
                if result.overhead_percent > 0
                else "baseline"
            )
            print(
                f"{name:<20} {result.avg_time_ms:<15.3f} {overhead_str:<12} {result.memory_usage_mb:<12.2f}"
            )

        print("\nDetailed Results:")
        print("-" * 80)

        for name, result in results.items():
            print(f"\n{name.upper()}:")
            print(f"  Iterations: {result.iterations}")
            print(f"  Total Time: {result.total_time_seconds:.3f}s")
            print(f"  Average: {result.avg_time_ms:.3f}ms")
            print(f"  Min: {result.min_time_ms:.3f}ms")
            print(f"  Max: {result.max_time_ms:.3f}ms")
            print(f"  P50: {result.p50_time_ms:.3f}ms")
            print(f"  P95: {result.p95_time_ms:.3f}ms")
            print(f"  P99: {result.p99_time_ms:.3f}ms")
            print(f"  Memory Usage: {result.memory_usage_mb:.2f}MB")
            print(f"  CPU Usage: {result.cpu_usage_percent:.2f}%")
            if result.overhead_percent > 0:
                print(f"  Overhead: {result.overhead_percent:.2f}%")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        if not self.results:
            return {"error": "No benchmark results available"}

        # Find max overhead
        max_overhead = max(
            r.overhead_percent for r in self.results if r.overhead_percent > 0
        )

        # Calculate memory usage
        total_memory = sum(r.memory_usage_mb for r in self.results)

        return {
            "total_tests": len(self.results),
            "max_overhead_percent": max_overhead,
            "total_memory_usage_mb": total_memory,
            "baseline_avg_time_ms": (
                self.baseline_result.avg_time_ms if self.baseline_result else 0
            ),
            "performance_acceptable": max_overhead < 10.0,  # Less than 10% overhead
            "memory_efficient": total_memory < 50.0,  # Less than 50MB total
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


async def run_performance_benchmarks(iterations: int = 1000) -> Dict[str, Any]:
    """
    Run performance benchmarks for the metrics system.

    Args:
        iterations: Number of iterations per benchmark

    Returns:
        Dictionary with benchmark results and summary
    """
    benchmark = MetricsBenchmark()
    results = await benchmark.run_all_benchmarks(iterations)

    benchmark.print_results(results)
    summary = benchmark.get_performance_summary()

    return {
        "results": {name: result.__dict__ for name, result in results.items()},
        "summary": summary,
    }
