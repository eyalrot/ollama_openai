# Performance Benchmarks for Metrics System

This document describes the performance benchmarking suite for the metrics collection system and provides guidelines for performance regression testing.

## Overview

The metrics system is designed to have minimal performance impact on the main application. The benchmarking suite measures:

- Request processing overhead
- Memory usage
- Concurrent request handling
- System metrics collection overhead
- Streaming response monitoring performance

## Running Benchmarks

### Command Line Usage

```python
from src.utils.benchmarks import run_performance_benchmarks

# Run full benchmark suite
results = await run_performance_benchmarks(iterations=1000)

# Run with fewer iterations for quick testing
results = await run_performance_benchmarks(iterations=100)
```

### Available Benchmarks

1. **Baseline** - Measures performance without any metrics collection
2. **Simple Tracking** - Basic request metrics collection
3. **Streaming Tracking** - Streaming response monitoring
4. **Concurrent Tracking** - Multiple concurrent requests
5. **Memory Stress** - High-volume metric collection
6. **System Metrics** - System resource monitoring overhead

## Performance Expectations

### Acceptable Overhead Thresholds

- **Simple Tracking**: < 10% overhead
- **Concurrent Tracking**: < 50% overhead
- **Memory Stress**: < 20% overhead
- **System Metrics**: < 30% overhead

### Memory Usage Limits

- **Total Memory**: < 50MB for full benchmark suite
- **Individual Tests**: < 10MB per test
- **Streaming**: Bounded by chunk sampling (max 100 chunks)

### Response Time Targets

- **Simple Operations**: < 5ms average
- **Concurrent Operations**: < 50ms average
- **Streaming Setup**: < 100ms average (excluding stream duration)

## Benchmark Results Interpretation

### Overhead Calculation

```
Overhead % = (Test Time - Baseline Time) / Baseline Time × 100
```

### Performance Metrics

- **Average Time**: Mean request processing time
- **P50/P95/P99**: Percentile response times
- **Memory Usage**: Additional memory consumption
- **CPU Usage**: Processor utilization during test

### Performance Indicators

- ✅ **Good**: < 10% overhead, < 5MB memory
- ⚠️ **Acceptable**: 10-50% overhead, 5-20MB memory
- ❌ **Poor**: > 50% overhead, > 20MB memory

## Running Performance Tests

### Automated Testing

```bash
# Run performance regression tests
python -m pytest tests/performance/test_metrics_performance.py -v

# Run with coverage
python -m pytest tests/performance/test_metrics_performance.py --cov=src.utils.metrics
```

### Manual Benchmarking

```python
import asyncio
from src.utils.benchmarks import MetricsBenchmark

async def run_custom_benchmark():
    benchmark = MetricsBenchmark()
    
    # Run specific benchmarks
    baseline = await benchmark._benchmark_baseline(1000)
    tracking = await benchmark._benchmark_simple_tracking(1000)
    
    # Calculate overhead
    overhead = (tracking.avg_time_ms - baseline.avg_time_ms) / baseline.avg_time_ms * 100
    print(f"Overhead: {overhead:.2f}%")

asyncio.run(run_custom_benchmark())
```

## Performance Optimization Guidelines

### Best Practices

1. **Minimal Synchronization**: Use locks only when necessary
2. **Async Operations**: Prefer async/await over blocking operations
3. **Memory Efficiency**: Use circular buffers and sampling
4. **Batch Operations**: Group metric updates when possible
5. **Lazy Evaluation**: Calculate expensive metrics only when needed

### Common Performance Issues

1. **Excessive Locking**: Over-synchronization can cause contention
2. **Memory Leaks**: Unbounded metric storage
3. **Blocking Operations**: Synchronous I/O in async context
4. **Large Payloads**: Storing full request/response bodies

### Monitoring in Production

```python
# Check metrics overhead in production
from src.utils.benchmarks import MetricsBenchmark

benchmark = MetricsBenchmark()
results = await benchmark.run_all_benchmarks(iterations=100)
summary = benchmark.get_performance_summary()

if not summary['performance_acceptable']:
    logger.warning(f"Metrics overhead too high: {summary['max_overhead_percent']:.2f}%")
```

## Continuous Integration

### CI Performance Tests

The performance tests are designed to run in CI environments:

- **Reduced Iterations**: Tests use fewer iterations for speed
- **Relaxed Thresholds**: CI thresholds are more permissive
- **Timeout Protection**: Tests have reasonable time limits
- **Resource Monitoring**: Memory and CPU usage tracking

### Performance Regression Detection

```python
# Example CI performance check
@pytest.mark.asyncio
async def test_performance_regression():
    benchmark = MetricsBenchmark()
    
    # Current performance
    current = await benchmark._benchmark_simple_tracking(100)
    
    # Historical baseline (stored in CI)
    baseline_time = 2.0  # ms
    
    # Check for regression
    regression = (current.avg_time_ms - baseline_time) / baseline_time * 100
    assert regression < 50.0, f"Performance regression detected: {regression:.2f}%"
```

## Troubleshooting Performance Issues

### Common Causes

1. **High System Load**: Other processes consuming resources
2. **Memory Pressure**: Insufficient available memory
3. **Disk I/O**: Slow filesystem operations
4. **Network Latency**: Remote dependencies

### Debugging Steps

1. **Isolate the Issue**: Run individual benchmarks
2. **Check Resources**: Monitor CPU, memory, and disk usage
3. **Profile Code**: Use Python profilers for detailed analysis
4. **Compare Baselines**: Run with/without metrics collection

### Performance Profiling

```python
import cProfile
import pstats
from src.utils.benchmarks import run_performance_benchmarks

# Profile the benchmarks
profiler = cProfile.Profile()
profiler.enable()

results = await run_performance_benchmarks(iterations=100)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

## Conclusion

The metrics system is designed for production use with minimal performance impact. Regular benchmarking ensures that performance remains acceptable as the system evolves. The benchmarking suite provides comprehensive coverage of different usage patterns and helps identify performance regressions early in the development process.