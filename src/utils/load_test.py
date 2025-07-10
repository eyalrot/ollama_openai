"""
Load testing framework with monitoring validation.

This module provides load testing capabilities to verify that the metrics
system maintains accuracy and performance under high load conditions.
"""

import asyncio
import gc
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import psutil

from src.utils.metrics import (
    get_metrics_summary,
    reset_metrics,
    track_request,
    track_streaming_request,
)


@dataclass
class LoadTestConfig:
    """Configuration for load tests."""

    name: str
    total_requests: int
    concurrent_requests: int
    duration_seconds: Optional[int] = None
    endpoint: str = "/test/load"
    method: str = "POST"
    model: str = "load-test-model"
    request_size: int = 1000
    response_size: int = 2000
    simulate_work_ms: float = 1.0
    use_streaming: bool = False
    verify_accuracy: bool = True


@dataclass
class LoadTestResult:
    """Result of a load test."""

    config: LoadTestConfig
    actual_requests: int
    duration_seconds: float
    requests_per_second: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    errors: int
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    metrics_accuracy: Dict[str, float]
    metrics_lost: int
    performance_degradation: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class LoadTestRunner:
    """
    Load testing framework with monitoring validation.
    """

    def __init__(self):
        self.results: List[LoadTestResult] = []
        self.baseline_performance: Optional[float] = None

    async def run_load_test(self, config: LoadTestConfig) -> LoadTestResult:
        """
        Run a single load test.

        Args:
            config: Load test configuration

        Returns:
            Load test result with metrics validation
        """
        print(f"Running load test: {config.name}")
        print(f"  Requests: {config.total_requests}")
        print(f"  Concurrency: {config.concurrent_requests}")
        print(f"  Duration: {config.duration_seconds or 'unlimited'}s")

        # Reset metrics before test
        await reset_metrics()

        # Force garbage collection
        gc.collect()

        # Get initial system state
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run the load test
        start_time = time.time()

        if config.duration_seconds:
            result = await self._run_duration_based_test(config)
        else:
            result = await self._run_request_based_test(config)

        end_time = time.time()
        duration = end_time - start_time

        # Get final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_usage = final_memory - initial_memory

        # Get CPU usage
        cpu_usage = process.cpu_percent()

        # Calculate performance metrics
        response_times = result["response_times"]
        avg_response_time = statistics.mean(response_times) if response_times else 0
        p95_response_time = (
            statistics.quantiles(response_times, n=20)[18]
            if len(response_times) >= 20
            else 0
        )
        p99_response_time = (
            statistics.quantiles(response_times, n=100)[98]
            if len(response_times) >= 100
            else 0
        )

        # Verify metrics accuracy
        metrics_accuracy = {}
        metrics_lost = 0

        if config.verify_accuracy:
            metrics_accuracy, metrics_lost = await self._verify_metrics_accuracy(
                result["actual_requests"], result["errors"], config
            )

        # Calculate performance degradation
        performance_degradation = 0.0
        if self.baseline_performance:
            performance_degradation = (
                (avg_response_time - self.baseline_performance)
                / self.baseline_performance
                * 100
            )

        # Create result
        test_result = LoadTestResult(
            config=config,
            actual_requests=result["actual_requests"],
            duration_seconds=duration,
            requests_per_second=result["actual_requests"] / duration,
            avg_response_time_ms=avg_response_time,
            p95_response_time_ms=p95_response_time,
            p99_response_time_ms=p99_response_time,
            errors=result["errors"],
            error_rate=(
                result["errors"] / result["actual_requests"]
                if result["actual_requests"] > 0
                else 0
            ),
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            metrics_accuracy=metrics_accuracy,
            metrics_lost=metrics_lost,
            performance_degradation=performance_degradation,
        )

        self.results.append(test_result)
        return test_result

    async def _run_request_based_test(self, config: LoadTestConfig) -> Dict[str, Any]:
        """Run a test based on total number of requests."""
        semaphore = asyncio.Semaphore(config.concurrent_requests)
        response_times = []
        actual_requests = 0
        errors = 0

        async def single_request():
            nonlocal actual_requests, errors
            async with semaphore:
                try:
                    start_time = time.time()

                    if config.use_streaming:
                        await self._simulate_streaming_request(config)
                    else:
                        await self._simulate_request(config)

                    end_time = time.time()
                    response_times.append((end_time - start_time) * 1000)
                    actual_requests += 1

                except Exception as e:
                    errors += 1
                    print(f"Request error: {e}")

        # Create tasks for all requests
        tasks = [single_request() for _ in range(config.total_requests)]

        # Run all requests
        await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "actual_requests": actual_requests,
            "errors": errors,
            "response_times": response_times,
        }

    async def _run_duration_based_test(self, config: LoadTestConfig) -> Dict[str, Any]:
        """Run a test based on duration."""
        semaphore = asyncio.Semaphore(config.concurrent_requests)
        response_times = []
        actual_requests = 0
        errors = 0
        stop_event = asyncio.Event()

        async def single_request():
            nonlocal actual_requests, errors
            async with semaphore:
                try:
                    start_time = time.time()

                    if config.use_streaming:
                        await self._simulate_streaming_request(config)
                    else:
                        await self._simulate_request(config)

                    end_time = time.time()
                    response_times.append((end_time - start_time) * 1000)
                    actual_requests += 1

                except Exception as e:
                    errors += 1
                    print(f"Request error: {e}")

        async def request_generator():
            """Generate requests continuously."""
            while not stop_event.is_set():
                asyncio.create_task(single_request())
                await asyncio.sleep(0.001)  # Small delay to prevent overwhelming

        # Start request generation
        generator_task = asyncio.create_task(request_generator())

        # Wait for duration
        await asyncio.sleep(config.duration_seconds)

        # Stop generation
        stop_event.set()
        generator_task.cancel()

        # Wait for remaining requests to complete
        await asyncio.sleep(1)

        return {
            "actual_requests": actual_requests,
            "errors": errors,
            "response_times": response_times,
        }

    async def _simulate_request(self, config: LoadTestConfig):
        """Simulate a single request with metrics tracking."""
        async with track_request(
            config.endpoint, config.method, config.model
        ) as metric:
            # Simulate processing time
            await asyncio.sleep(config.simulate_work_ms / 1000)

            # Set metric values
            metric.status_code = 200
            metric.request_size = config.request_size
            metric.response_size = config.response_size

    async def _simulate_streaming_request(self, config: LoadTestConfig):
        """Simulate a streaming request with metrics tracking."""

        async def mock_stream():
            """Mock streaming response."""
            for i in range(10):
                await asyncio.sleep(0.001)
                yield f"chunk_{i}".encode()

        async with track_streaming_request(
            config.endpoint, config.method, config.model
        ) as (metric, wrapper_factory):
            # Simulate processing time
            await asyncio.sleep(config.simulate_work_ms / 1000)

            # Set metric values
            metric.status_code = 200
            metric.request_size = config.request_size

            # Process stream
            stream = wrapper_factory(mock_stream())
            chunks = []
            async for chunk in stream:
                chunks.append(chunk)

    async def _verify_metrics_accuracy(
        self, expected_requests: int, expected_errors: int, config: LoadTestConfig
    ) -> Tuple[Dict[str, float], int]:
        """Verify metrics accuracy after load test."""
        # Wait for metrics to be processed
        await asyncio.sleep(0.1)

        # Get metrics summary
        summary = await get_metrics_summary()

        # Calculate accuracy
        accuracy = {}
        metrics_lost = 0

        # Request count accuracy
        actual_requests = summary.get("total_requests", 0)
        if expected_requests > 0:
            accuracy["request_count"] = min(actual_requests / expected_requests, 1.0)
            metrics_lost = max(0, expected_requests - actual_requests)

        # Error rate accuracy
        actual_errors = summary.get("failed_requests", 0)
        if expected_errors > 0:
            accuracy["error_count"] = min(actual_errors / expected_errors, 1.0)

        # Response time accuracy (check if reasonable)
        avg_response_time = summary.get("performance", {}).get("avg_duration_ms", 0)
        expected_response_time = config.simulate_work_ms
        if expected_response_time > 0:
            accuracy["response_time"] = min(
                expected_response_time / max(avg_response_time, 0.1), 1.0
            )

        # Streaming accuracy (if applicable)
        if config.use_streaming:
            streaming_requests = summary.get("streaming", {}).get(
                "total_streaming_requests", 0
            )
            if expected_requests > 0:
                accuracy["streaming_count"] = min(
                    streaming_requests / expected_requests, 1.0
                )

        return accuracy, metrics_lost

    async def run_comprehensive_load_tests(self) -> Dict[str, LoadTestResult]:
        """Run comprehensive load tests with various scenarios."""
        print("Running comprehensive load tests...")

        # Test configurations
        configs = [
            LoadTestConfig(
                name="Light Load",
                total_requests=100,
                concurrent_requests=10,
                simulate_work_ms=1.0,
            ),
            LoadTestConfig(
                name="Medium Load",
                total_requests=1000,
                concurrent_requests=50,
                simulate_work_ms=2.0,
            ),
            LoadTestConfig(
                name="Heavy Load",
                total_requests=5000,
                concurrent_requests=100,
                simulate_work_ms=1.0,
            ),
            LoadTestConfig(
                name="Streaming Load",
                total_requests=500,
                concurrent_requests=25,
                simulate_work_ms=2.0,
                use_streaming=True,
            ),
            LoadTestConfig(
                name="Duration Test",
                total_requests=0,  # Unlimited
                concurrent_requests=50,
                duration_seconds=30,
                simulate_work_ms=1.0,
            ),
            LoadTestConfig(
                name="Memory Stress",
                total_requests=10000,
                concurrent_requests=200,
                simulate_work_ms=0.5,
                request_size=5000,
                response_size=10000,
            ),
        ]

        # Run baseline test first
        baseline_config = LoadTestConfig(
            name="Baseline",
            total_requests=100,
            concurrent_requests=10,
            simulate_work_ms=1.0,
            verify_accuracy=False,
        )

        baseline_result = await self.run_load_test(baseline_config)
        self.baseline_performance = baseline_result.avg_response_time_ms

        # Run all tests
        results = {"baseline": baseline_result}

        for config in configs:
            result = await self.run_load_test(config)
            results[config.name] = result

        return results

    def print_results(self, results: Dict[str, LoadTestResult]):
        """Print load test results."""
        print("\n" + "=" * 100)
        print("LOAD TEST RESULTS")
        print("=" * 100)

        # Summary table
        print(
            f"{'Test Name':<20} {'Requests':<10} {'RPS':<10} {'Avg RT(ms)':<12} {'P95 RT(ms)':<12} {'Errors':<8} {'Memory(MB)':<12}"
        )
        print("-" * 100)

        for name, result in results.items():
            print(
                f"{name:<20} {result.actual_requests:<10} {result.requests_per_second:<10.1f} "
                f"{result.avg_response_time_ms:<12.2f} {result.p95_response_time_ms:<12.2f} "
                f"{result.errors:<8} {result.memory_usage_mb:<12.2f}"
            )

        print("\nDetailed Results:")
        print("-" * 100)

        for name, result in results.items():
            print(f"\n{name.upper()}:")
            print(
                f"  Requests: {result.actual_requests} (target: {result.config.total_requests})"
            )
            print(f"  Duration: {result.duration_seconds:.2f}s")
            print(f"  RPS: {result.requests_per_second:.1f}")
            print(f"  Avg Response Time: {result.avg_response_time_ms:.2f}ms")
            print(f"  P95 Response Time: {result.p95_response_time_ms:.2f}ms")
            print(f"  P99 Response Time: {result.p99_response_time_ms:.2f}ms")
            print(f"  Errors: {result.errors} ({result.error_rate:.2%})")
            print(f"  Memory Usage: {result.memory_usage_mb:.2f}MB")
            print(f"  CPU Usage: {result.cpu_usage_percent:.1f}%")
            print(f"  Performance Degradation: {result.performance_degradation:.2f}%")
            print(f"  Metrics Lost: {result.metrics_lost}")

            if result.metrics_accuracy:
                print("  Metrics Accuracy:")
                for metric_name, accuracy in result.metrics_accuracy.items():
                    print(f"    {metric_name}: {accuracy:.2%}")

    def get_load_test_summary(self) -> Dict[str, Any]:
        """Get summary of load test results."""
        if not self.results:
            return {"error": "No load test results available"}

        # Calculate overall statistics
        total_requests = sum(r.actual_requests for r in self.results)
        total_errors = sum(r.errors for r in self.results)
        avg_performance_degradation = statistics.mean(
            r.performance_degradation
            for r in self.results
            if r.performance_degradation > 0
        )
        max_memory_usage = max(r.memory_usage_mb for r in self.results)
        total_metrics_lost = sum(r.metrics_lost for r in self.results)

        # Calculate average accuracy
        accuracy_scores = []
        for result in self.results:
            if result.metrics_accuracy:
                accuracy_scores.extend(result.metrics_accuracy.values())

        avg_accuracy = statistics.mean(accuracy_scores) if accuracy_scores else 0

        return {
            "total_tests": len(self.results),
            "total_requests": total_requests,
            "total_errors": total_errors,
            "overall_error_rate": (
                total_errors / total_requests if total_requests > 0 else 0
            ),
            "avg_performance_degradation": avg_performance_degradation,
            "max_memory_usage_mb": max_memory_usage,
            "total_metrics_lost": total_metrics_lost,
            "metrics_accuracy": avg_accuracy,
            "performance_acceptable": avg_performance_degradation < 50.0,
            "memory_stable": max_memory_usage < 100.0,
            "metrics_reliable": total_metrics_lost
            < total_requests * 0.01,  # Less than 1% loss
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


async def run_load_tests() -> Dict[str, Any]:
    """
    Run comprehensive load tests for the metrics system.

    Returns:
        Dictionary with load test results and summary
    """
    runner = LoadTestRunner()
    results = await runner.run_comprehensive_load_tests()

    runner.print_results(results)
    summary = runner.get_load_test_summary()

    return {
        "results": {name: result.__dict__ for name, result in results.items()},
        "summary": summary,
    }
