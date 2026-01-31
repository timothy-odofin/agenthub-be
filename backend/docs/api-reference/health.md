# Health API

> **System health checks and monitoring** for production readiness

## Overview

The Health API provides endpoints to monitor system status, check component health, and verify worker processes.

**Base Path**: `/api/v1/health/` 
**Authentication**: Not required (public endpoints)

---

## Endpoints

### GET /test-celery

Test Celery worker connectivity and background task processing.

**Authentication**: Not required

**Request**:
```bash
curl http://localhost:8000/api/v1/health/test-celery
```

**Success Response** (200 OK):
```json
{
"task_id": "a4f3c2e1-5d6a-4b8c-9e2f-1a3b5c7d9e1f",
"message": "Task sent to Celery"
}
```

**What It Tests**:
- Celery worker is running
- Redis broker is accessible
- Task can be queued
- Background processing is operational

**Example Usage**:

```python
import requests

response = requests.get("http://localhost:8000/api/v1/health/test-celery")

if response.status_code == 200:
data = response.json()
print(f"Celery is working! Task ID: {data['task_id']}")
else:
print(" Celery is down!")
```

---

### GET / (Main Health Check)

**Status**: Coming soon

**Planned Response**:
```json
{
"status": "healthy",
"timestamp": "2026-01-10T14:30:00Z",
"version": "1.0.0",
"components": {
"api": {
"status": "up",
"response_time_ms": 5.2
},
"database": {
"status": "up",
"response_time_ms": 12.8,
"connections": {
"active": 5,
"idle": 15,
"max": 20
}
},
"redis": {
"status": "up",
"response_time_ms": 2.1,
"memory_used_mb": 45.3
},
"celery": {
"status": "up",
"workers": 4,
"active_tasks": 2,
"pending_tasks": 0
},
"vector_db": {
"status": "up",
"response_time_ms": 25.4,
"collections": 3
},
"llm": {
"status": "up",
"provider": "openai",
"model": "gpt-4",
"response_time_ms": 450.2
}
},
"uptime_seconds": 3600,
"environment": "production"
}
```

---

## Health Check Patterns

### Basic Health Check

```python
import requests

def check_health():
"""Simple health check."""
try:
response = requests.get(
"http://localhost:8000/api/v1/health/test-celery",
timeout=5
)
return response.status_code == 200
except:
return False

if check_health():
print("System is healthy")
else:
print(" System is down")
```

---

### Detailed Component Check

```python
def check_components():
"""Check individual components."""
checks = {
"celery": check_celery(),
"database": check_database(),
"redis": check_redis(),
}

all_healthy = all(checks.values())

for component, status in checks.items():
icon = "" if status else ""
print(f"{icon} {component}: {'UP' if status else 'DOWN'}")

return all_healthy

def check_celery():
"""Check Celery workers."""
try:
response = requests.get(
"http://localhost:8000/api/v1/health/test-celery",
timeout=5
)
return response.status_code == 200
except:
return False

def check_database():
"""Check database connection."""
# Your database check logic
pass

def check_redis():
"""Check Redis connection."""
# Your Redis check logic
pass
```

---

### Monitoring Loop

```python
import time
from datetime import datetime

def monitor_health(interval=60):
"""Continuously monitor health."""
while True:
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
healthy = check_health()

status = "HEALTHY" if healthy else " UNHEALTHY"
print(f"[{timestamp}] {status}")

if not healthy:
# Alert logic here
send_alert("System health check failed!")

time.sleep(interval)

# Run monitoring
monitor_health(interval=60) # Check every minute
```

---

## Kubernetes Probes

### Liveness Probe

Check if application is running:

```yaml
livenessProbe:
httpGet:
path: /api/v1/health/test-celery
port: 8000
initialDelaySeconds: 30
periodSeconds: 10
timeoutSeconds: 5
failureThreshold: 3
```

### Readiness Probe

Check if application is ready to serve traffic:

```yaml
readinessProbe:
httpGet:
path: /api/v1/health/test-celery
port: 8000
initialDelaySeconds: 10
periodSeconds: 5
timeoutSeconds: 3
failureThreshold: 3
```

---

## Docker Health Check

```dockerfile
FROM python:3.11

# ... your Dockerfile content ...

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
CMD curl -f http://localhost:8000/api/v1/health/test-celery || exit 1
```

---

## Nagios/Prometheus Integration

### Nagios Check Script

```bash
#!/bin/bash
# check_agenthub_health.sh

URL="http://localhost:8000/api/v1/health/test-celery"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ "$RESPONSE" -eq 200 ]; then
echo "OK - AgentHub is healthy"
exit 0
else
echo "CRITICAL - AgentHub is down (HTTP $RESPONSE)"
exit 2
fi
```

### Prometheus Metrics

**Coming soon**:

```
GET /metrics

# HELP agenthub_health_status System health status (1=healthy, 0=unhealthy)
# TYPE agenthub_health_status gauge
agenthub_health_status 1

# HELP agenthub_api_requests_total Total API requests
# TYPE agenthub_api_requests_total counter
agenthub_api_requests_total{method="POST",endpoint="/chat/message"} 1234

# HELP agenthub_response_time_seconds API response time
# TYPE agenthub_response_time_seconds histogram
agenthub_response_time_seconds_bucket{le="0.1"} 500
agenthub_response_time_seconds_bucket{le="0.5"} 1200
```

---

## Status Codes

| Code | Status | Meaning |
|------|--------|---------|
| **200** | OK | All systems operational |
| **503** | Service Unavailable | One or more components down |
| **500** | Internal Error | Unexpected error occurred |

---

## Component Health Indicators

### Healthy System

```json
{
"status": "healthy",
"components": {
"api": "up",
"database": "up",
"redis": "up",
"celery": "up",
"vector_db": "up",
"llm": "up"
}
}
```

### Degraded System

```json
{
"status": "degraded",
"components": {
"api": "up",
"database": "up",
"redis": "up",
"celery": "up",
"vector_db": "degraded", // Slow responses
"llm": "up"
},
"warnings": [
"Vector DB response time > 1s"
]
}
```

### Unhealthy System

```json
{
"status": "unhealthy",
"components": {
"api": "up",
"database": "down", // Critical failure
"redis": "up",
"celery": "down", // Workers offline
"vector_db": "up",
"llm": "up"
},
"errors": [
"MongoDB connection refused",
"No Celery workers available"
]
}
```

---

## Best Practices

### 1. Regular Health Checks

```python
# GOOD - Check health regularly
import schedule

def job():
if not check_health():
alert_ops_team()

schedule.every(1).minutes.do(job)

while True:
schedule.run_pending()
time.sleep(1)
```

### 2. Timeout Configuration

```python
# GOOD - Set reasonable timeouts
response = requests.get(
health_url,
timeout=5 # Don't wait forever
)

# BAD - No timeout
response = requests.get(health_url)
```

### 3. Graceful Degradation

```python
# GOOD - Continue with degraded service
if not celery_healthy():
# Use synchronous processing
process_sync(data)
else:
# Use async background processing
process_async.delay(data)
```

---

## Troubleshooting

### Celery Health Check Fails

**Symptoms**: `/test-celery` returns error or times out

**Possible Causes**:
1. Celery workers not running
2. Redis broker not accessible
3. Network connectivity issues

**Solutions**:

```bash
# Check if workers are running
celery -A app.workers.celery_app inspect active

# Check Redis connection
redis-cli -h localhost -p 6379 ping

# Start workers
celery -A app.workers.celery_app worker --loglevel=info

# Check network
curl http://localhost:6379
```

---

### Database Connection Issues

**Symptoms**: Slow responses or connection errors

**Solutions**:

```bash
# Check MongoDB
mongosh --eval "db.adminCommand('ping')"

# Check PostgreSQL
pg_isready -h localhost -p 5432

# Check connection pool
# Look for "too many connections" errors
```

---

## Alerting

### Alert Conditions

| Condition | Severity | Action |
|-----------|----------|--------|
| Health check fails | Critical | Page on-call engineer |
| Response time > 5s | Warning | Monitor closely |
| Component degraded | Warning | Investigate |
| Uptime < 99.9% | Warning | Review logs |

---

## Related Documentation

- **[Workers Guide](../guides/workers/README.md)** - Celery worker setup
- **[Database Guide](../guides/database/README.md)** - Database health
- **[Deployment Guide](../deployment/overview.md)** - Production setup

---

**Last Updated**: January 10, 2026 
**Status**: Production Ready

---
