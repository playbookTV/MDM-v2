# Modomo Monitoring Stack

This directory contains the complete monitoring setup for the Modomo Dataset Management system using Grafana, Prometheus, and supporting services.

## Quick Start

1. **Start the monitoring stack:**
   ```bash
   cd monitoring
   docker-compose up -d
   ```

2. **Access the services:**
   - **Grafana**: http://localhost:3000 (admin/modomo2024)
   - **Prometheus**: http://localhost:9090
   - **AlertManager**: http://localhost:9093

3. **Configure your backend to expose metrics:**
   ```bash
   # Add to your .env file
   ENABLE_METRICS=true
   SENTRY_DSN=your-sentry-dsn-here
   ```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Modomo API    │    │   React App     │    │   Redis Queue   │
│   (port 8000)   │    │   (port 5173)   │    │   (port 6379)   │
│                 │    │                 │    │                 │
│ /metrics        │    │ Sentry SDK      │    │ Redis Exporter  │
└─────────┬───────┘    └─────────────────┘    └─────────┬───────┘
          │                                               │
          └─────────────────┐               ┌─────────────┘
                            │               │
                    ┌───────▼───────────────▼───────┐
                    │       Prometheus              │
                    │       (port 9090)             │
                    └───────────────┬───────────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │       Grafana                 │
                    │       (port 3000)             │
                    │                               │
                    │ • Overview Dashboard          │
                    │ • API Performance Dashboard   │
                    │ • System Metrics Dashboard    │
                    └───────────────────────────────┘
```

## Dashboards

### 1. Modomo Overview Dashboard
- **URL**: http://localhost:3000/d/modomo-overview
- **Metrics**:
  - API request rate and response times
  - Active jobs and dataset imports
  - Scene review statistics
  - System resource usage
  - Redis performance

### 2. API Performance Dashboard
- **URL**: http://localhost:3000/d/modomo-api-performance
- **Metrics**:
  - Response time percentiles (50th, 95th, 99th)
  - Request rate by endpoint
  - Error rates (4xx, 5xx)
  - Job processing times by type

## Metrics Collection

### Backend API Metrics (FastAPI + Prometheus)
```python
# Automatic metrics via prometheus-fastapi-instrumentator
- http_requests_total
- http_request_duration_seconds
- http_requests_inprogress

# Custom Modomo metrics
- modomo_dataset_imports_total{source}
- modomo_job_processing_seconds{job_type}
- modomo_active_jobs
- modomo_scene_reviews_total{verdict}
```

### System Metrics
- **Node Exporter**: CPU, memory, disk, network
- **cAdvisor**: Container metrics
- **Redis Exporter**: Redis performance and queue stats

## Sentry Integration

### Backend (FastAPI)
```python
# Automatic error tracking and performance monitoring
- Exception tracking with stack traces
- Transaction performance monitoring
- Custom breadcrumbs for job processing
- User context and custom tags
```

### Frontend (React)
```typescript
// Complete error boundary and performance tracking
- React component error boundaries
- Route change tracking
- API call monitoring
- Session replay (10% sample rate)
```

## Alert Configuration

The AlertManager is configured but requires setup of notification channels:

1. **Edit alertmanager.yml** to add your notification preferences:
   - Slack webhooks
   - Email SMTP
   - PagerDuty integration

2. **Add alerting rules** in `prometheus/rules/` directory

## Environment Variables

### Backend (.env)
```bash
# Monitoring
ENABLE_METRICS=true
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
SENTRY_TRACES_SAMPLE_RATE=0.1
ENVIRONMENT=production

# Redis (for metrics)
REDIS_URL=redis://localhost:6379
```

### Frontend (.env)
```bash
# Sentry
VITE_SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
VITE_SENTRY_TRACES_SAMPLE_RATE=0.1
VITE_ENVIRONMENT=production
VITE_APP_VERSION=1.0.0
```

## Troubleshooting

### Common Issues

1. **Metrics not appearing in Grafana**
   - Check if Prometheus can reach your API: http://localhost:9090/targets
   - Verify ENABLE_METRICS=true in backend environment
   - Check API is running on expected port (8000)

2. **Sentry not receiving errors**
   - Verify SENTRY_DSN is set correctly
   - Check network connectivity to sentry.io
   - Test with a manual error in development

3. **Redis metrics missing**
   - Ensure Redis is running on localhost:6379
   - Check redis-exporter container logs
   - Verify Redis allows connections from Docker network

### Viewing Logs
```bash
# View all monitoring services
docker-compose logs -f

# View specific service
docker-compose logs -f grafana
docker-compose logs -f prometheus
```

## Scaling and Production

For production deployment:

1. **External Prometheus**: Use managed Prometheus (AWS CloudWatch, GCP Cloud Monitoring)
2. **External Grafana**: Use Grafana Cloud or managed service
3. **Persistent Storage**: Configure external volumes for data persistence
4. **Load Balancing**: Add multiple API instances with Prometheus scraping all
5. **Alerting**: Set up proper notification channels and escalation policies

## Custom Metrics

To add new metrics to your application:

```python
# In your FastAPI route
from prometheus_client import Counter, Histogram

custom_counter = Counter('modomo_custom_total', 'Description', ['label'])
custom_histogram = Histogram('modomo_custom_duration_seconds', 'Description')

@app.post("/api/endpoint")
async def endpoint():
    with custom_histogram.time():
        # Your logic here
        custom_counter.labels(label="value").inc()
        return {"status": "success"}
```

The metric will automatically appear in Prometheus and can be added to Grafana dashboards.