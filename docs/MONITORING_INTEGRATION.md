# Monitoring Integration Guide

This guide provides comprehensive instructions for integrating the Ollama-OpenAI proxy metrics system with external monitoring tools like Prometheus, Grafana, and alerting systems.

## Overview

The proxy provides three main metrics endpoints:

- `/v1/metrics` - Comprehensive JSON metrics
- `/v1/metrics/prometheus` - Prometheus-compatible format
- `/v1/metrics/health` - Essential health indicators

## Available Metrics

### HTTP Request Metrics

| Metric Name | Type | Description |
|-------------|------|-------------|
| `http_requests_total` | Counter | Total number of HTTP requests |
| `http_requests_active` | Gauge | Currently active HTTP requests |
| `http_request_success_rate` | Gauge | Success rate of HTTP requests (0-1) |
| `http_request_error_rate` | Gauge | Error rate of HTTP requests (0-1) |
| `http_request_duration_seconds` | Histogram | Request duration distribution |
| `http_request_duration_p50_seconds` | Gauge | 50th percentile request duration |
| `http_request_duration_p95_seconds` | Gauge | 95th percentile request duration |
| `http_request_duration_p99_seconds` | Gauge | 99th percentile request duration |

### Per-Endpoint Metrics

| Metric Name | Type | Description |
|-------------|------|-------------|
| `http_requests_per_endpoint_total{endpoint}` | Counter | Total requests per endpoint |
| `http_request_duration_per_endpoint_seconds{endpoint}` | Gauge | Average duration per endpoint |
| `http_request_errors_per_endpoint_total{endpoint}` | Counter | Total errors per endpoint |
| `http_streaming_requests_per_endpoint_total{endpoint}` | Counter | Streaming requests per endpoint |

### Streaming Metrics

| Metric Name | Type | Description |
|-------------|------|-------------|
| `http_streaming_requests_total` | Counter | Total streaming requests |
| `http_streaming_first_byte_time_seconds` | Gauge | Average time to first byte |
| `http_streaming_throughput_bytes_per_second` | Gauge | Average streaming throughput |
| `http_streaming_chunks_total` | Counter | Total chunks processed |
| `http_streaming_cancelled_total` | Counter | Total cancelled streams |
| `http_streaming_timeout_total` | Counter | Total timed out streams |
| `http_streaming_avg_chunk_size_bytes` | Gauge | Average chunk size |

### System Metrics

| Metric Name | Type | Description |
|-------------|------|-------------|
| `system_cpu_usage_percent` | Gauge | CPU usage percentage |
| `system_memory_usage_percent` | Gauge | Memory usage percentage |
| `system_memory_usage_bytes` | Gauge | Memory usage in bytes |
| `system_disk_usage_percent` | Gauge | Disk usage percentage |
| `system_uptime_seconds` | Counter | System uptime in seconds |
| `network_bytes_sent_total` | Counter | Total network bytes sent |
| `network_bytes_recv_total` | Counter | Total network bytes received |
| `disk_read_bytes_total` | Counter | Total disk bytes read |
| `disk_write_bytes_total` | Counter | Total disk bytes written |

## Prometheus Integration

### Scraping Configuration

Add the following to your `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ollama-openai-proxy'
    static_configs:
      - targets: ['localhost:11434']
    metrics_path: '/v1/metrics/prometheus'
    scrape_interval: 15s
    scrape_timeout: 10s
    honor_labels: true
    params:
      format: ['prometheus']
```

### Service Discovery

For Kubernetes environments:

```yaml
- job_name: 'ollama-openai-proxy'
  kubernetes_sd_configs:
    - role: pod
      namespaces:
        names:
          - default
  relabel_configs:
    - source_labels: [__meta_kubernetes_pod_label_app]
      action: keep
      regex: ollama-openai-proxy
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
      action: keep
      regex: true
    - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
      action: replace
      target_label: __metrics_path__
      regex: (.+)
      replacement: /v1/metrics/prometheus
```

### Docker Compose Example

```yaml
version: '3.8'
services:
  ollama-openai-proxy:
    image: ollama/openai-proxy:latest
    ports:
      - "11434:11434"
    environment:
      - OPENAI_API_KEY=your_key_here
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=11434"
      - "prometheus.io/path=/v1/metrics/prometheus"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
```

## Grafana Integration

### Dashboard Configuration

Create a new dashboard with the following panels:

#### 1. Request Rate Panel

```json
{
  "title": "Request Rate",
  "type": "graph",
  "targets": [
    {
      "expr": "rate(http_requests_total[5m])",
      "legendFormat": "Requests/sec",
      "refId": "A"
    }
  ],
  "yAxes": [
    {
      "label": "Requests/sec",
      "min": 0
    }
  ]
}
```

#### 2. Response Time Panel

```json
{
  "title": "Response Time Percentiles",
  "type": "graph",
  "targets": [
    {
      "expr": "http_request_duration_p50_seconds * 1000",
      "legendFormat": "P50",
      "refId": "A"
    },
    {
      "expr": "http_request_duration_p95_seconds * 1000",
      "legendFormat": "P95",
      "refId": "B"
    },
    {
      "expr": "http_request_duration_p99_seconds * 1000",
      "legendFormat": "P99",
      "refId": "C"
    }
  ],
  "yAxes": [
    {
      "label": "Milliseconds",
      "min": 0
    }
  ]
}
```

#### 3. Error Rate Panel

```json
{
  "title": "Error Rate",
  "type": "graph",
  "targets": [
    {
      "expr": "http_request_error_rate * 100",
      "legendFormat": "Error %",
      "refId": "A"
    }
  ],
  "yAxes": [
    {
      "label": "Percentage",
      "min": 0,
      "max": 100
    }
  ]
}
```

#### 4. System Resources Panel

```json
{
  "title": "System Resources",
  "type": "graph",
  "targets": [
    {
      "expr": "system_cpu_usage_percent",
      "legendFormat": "CPU %",
      "refId": "A"
    },
    {
      "expr": "system_memory_usage_percent",
      "legendFormat": "Memory %",
      "refId": "B"
    },
    {
      "expr": "system_disk_usage_percent",
      "legendFormat": "Disk %",
      "refId": "C"
    }
  ],
  "yAxes": [
    {
      "label": "Percentage",
      "min": 0,
      "max": 100
    }
  ]
}
```

#### 5. Streaming Metrics Panel

```json
{
  "title": "Streaming Performance",
  "type": "graph",
  "targets": [
    {
      "expr": "http_streaming_throughput_bytes_per_second",
      "legendFormat": "Throughput (bytes/sec)",
      "refId": "A"
    },
    {
      "expr": "http_streaming_first_byte_time_seconds * 1000",
      "legendFormat": "First Byte Time (ms)",
      "refId": "B"
    }
  ]
}
```

### Complete Dashboard JSON

```json
{
  "dashboard": {
    "title": "Ollama-OpenAI Proxy Metrics",
    "tags": ["ollama", "openai", "proxy"],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "10s",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "Requests/sec"
          }
        ]
      },
      {
        "title": "Active Requests",
        "type": "stat",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "http_requests_active",
            "legendFormat": "Active"
          }
        ]
      },
      {
        "title": "Response Time Percentiles",
        "type": "graph",
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "http_request_duration_p50_seconds * 1000",
            "legendFormat": "P50"
          },
          {
            "expr": "http_request_duration_p95_seconds * 1000",
            "legendFormat": "P95"
          },
          {
            "expr": "http_request_duration_p99_seconds * 1000",
            "legendFormat": "P99"
          }
        ]
      }
    ]
  }
}
```

## Alerting Rules

### Prometheus Alerting Rules

Create `alerts.yml`:

```yaml
groups:
  - name: ollama-openai-proxy
    rules:
      - alert: HighErrorRate
        expr: http_request_error_rate > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} for 5 minutes"

      - alert: HighResponseTime
        expr: http_request_duration_p95_seconds > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: ServiceDown
        expr: up{job="ollama-openai-proxy"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service is down"
          description: "Ollama-OpenAI proxy service is not responding"

      - alert: HighCPUUsage
        expr: system_cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}% for 10 minutes"

      - alert: HighMemoryUsage
        expr: system_memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}% for 5 minutes"

      - alert: StreamingPerformanceDegraded
        expr: http_streaming_throughput_bytes_per_second < 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Streaming performance degraded"
          description: "Streaming throughput is {{ $value }} bytes/sec"

      - alert: HighStreamCancellationRate
        expr: rate(http_streaming_cancelled_total[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High stream cancellation rate"
          description: "Stream cancellation rate is {{ $value }}/sec"
```

### Alertmanager Configuration

Configure `alertmanager.yml`:

```yaml
global:
  smtp_smarthost: 'localhost:587'
  smtp_from: 'alertmanager@example.org'

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'web.hook'

receivers:
  - name: 'web.hook'
    webhook_configs:
      - url: 'http://127.0.0.1:5001/'
        send_resolved: true
```

## Health Check Integration

### Kubernetes Health Checks

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ollama-openai-proxy
spec:
  containers:
  - name: proxy
    image: ollama/openai-proxy:latest
    ports:
    - containerPort: 11434
    livenessProbe:
      httpGet:
        path: /health
        port: 11434
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /ready
        port: 11434
      initialDelaySeconds: 5
      periodSeconds: 5
```

### Docker Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:11434/health || exit 1
```

## Custom Metrics Integration

### Adding Custom Metrics

```python
from src.utils.metrics import get_metrics_collector, RequestMetrics

# Custom metric collection
collector = get_metrics_collector()

# Record custom metric
custom_metric = RequestMetrics(
    endpoint="/custom/endpoint",
    method="POST",
    status_code=200,
    duration_ms=150.5,
    model="custom-model"
)

await collector.record_request(custom_metric)
```

### Filtering Metrics

```python
from src.utils.metrics import get_filtered_metrics_summary

# Get metrics for specific endpoints
chat_metrics = await get_filtered_metrics_summary(
    endpoint_filter="chat",
    time_range_minutes=60
)

# Get metrics without system data
api_metrics = await get_filtered_metrics_summary(
    include_system_metrics=False
)
```

## Troubleshooting

### Common Issues

#### 1. Metrics Not Appearing

**Problem**: Prometheus not scraping metrics

**Solution**:
```bash
# Check endpoint accessibility
curl http://localhost:11434/v1/metrics/prometheus

# Verify Prometheus configuration
promtool check config prometheus.yml

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets
```

#### 2. High Memory Usage

**Problem**: Metrics collection consuming too much memory

**Solution**:
```python
# Reduce buffer size
from src.utils.metrics import MetricsCollector

collector = MetricsCollector(max_metrics=500)  # Reduce from default 1000
```

#### 3. Slow Response Times

**Problem**: Metrics collection adding latency

**Solution**:
```python
# Disable system metrics collection
collector = get_metrics_collector()
collector.stop()

# Use minimal tracking
async with track_request("/api/endpoint", "GET") as metric:
    # Only set essential fields
    metric.status_code = 200
```

#### 4. Missing Streaming Metrics

**Problem**: Streaming metrics not collected

**Solution**:
```python
# Use streaming context manager
async with track_streaming_request("/api/stream", "POST") as (metric, wrapper):
    metric.status_code = 200
    
    # Wrap the stream
    stream = wrapper(response_stream)
    async for chunk in stream:
        # Process chunk
        pass
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('src.utils.metrics').setLevel(logging.DEBUG)
```

### Performance Monitoring

Check metrics system performance:

```python
from src.utils.benchmarks import run_performance_benchmarks

# Run benchmarks
results = await run_performance_benchmarks(iterations=100)
summary = results["summary"]

if not summary["performance_acceptable"]:
    print(f"Performance issue detected: {summary['max_overhead_percent']}% overhead")
```

## Best Practices

### 1. Monitoring Strategy

- **Start Small**: Begin with basic metrics (requests, response times, errors)
- **Add Gradually**: Introduce system and streaming metrics as needed
- **Monitor Performance**: Use benchmarks to ensure minimal overhead
- **Set Alerts**: Configure meaningful alerts for critical metrics

### 2. Retention Policies

- **Short-term**: High-resolution metrics for recent data (1-7 days)
- **Long-term**: Aggregated metrics for historical analysis (weeks/months)
- **Cleanup**: Regular cleanup of old metrics to prevent storage issues

### 3. Dashboard Design

- **Focus on SLOs**: Track Service Level Objectives
- **User-Centric**: Show metrics that matter to users
- **Actionable**: Include metrics that can drive decisions
- **Contextualized**: Group related metrics together

### 4. Alerting Guidelines

- **Meaningful Thresholds**: Set thresholds based on SLAs
- **Reduce Noise**: Avoid alerts for temporary issues
- **Escalation**: Define escalation paths for critical alerts
- **Documentation**: Include runbooks for alert responses

## Integration Examples

### DataDog Integration

```python
import datadog
from src.utils.metrics import get_metrics_summary

# Configure DataDog
datadog.initialize(api_key='your_api_key', app_key='your_app_key')

# Send metrics to DataDog
async def send_to_datadog():
    summary = await get_metrics_summary()
    
    datadog.api.Metric.send(
        metric='ollama.proxy.requests.total',
        points=summary['total_requests'],
        tags=['service:ollama-proxy']
    )
```

### New Relic Integration

```python
import newrelic.agent
from src.utils.metrics import track_request

# Instrument with New Relic
@newrelic.agent.function_trace()
async def process_request():
    async with track_request("/api/endpoint", "POST") as metric:
        # Your code here
        metric.status_code = 200
```

This comprehensive guide covers all aspects of monitoring integration, from basic setup to advanced troubleshooting. Use it as a reference for implementing robust monitoring for your Ollama-OpenAI proxy deployment.