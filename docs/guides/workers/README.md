# Background Workers System

> ⚙️ **Async task processing** with Celery for long-running operations, file ingestion, and background jobs

## Table of Contents

### Overview
- [What is the Workers System?](#what-is-the-workers-system)
- [Architecture Overview](#architecture-overview)
- [Key Features](#key-features)

### Core Components
- [Celery Application](#celery-application)
  - [Configuration](#celery-configuration)
  - [Broker & Backend](#broker--backend)
- [Task Definitions](#task-definitions)
  - [Example Task](#example-task)
  - [File Ingestion Task](#file-ingestion-task)

### Usage Patterns
- [Running Tasks](#running-tasks)
  - [Immediate Execution](#immediate-execution)
  - [Delayed Execution](#delayed-execution)
  - [Getting Results](#getting-results)
- [Task Monitoring](#task-monitoring)
- [Integration with API](#integration-with-api)

### Extending Workers
- [Creating Custom Tasks](#creating-custom-tasks)
- [Async Tasks](#async-tasks)
- [Task Chains](#task-chains)
- [Periodic Tasks](#periodic-tasks)

### Reference
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

---

## What is the Workers System?

The workers system (`src/app/workers/`) provides **background task processing** using Celery, enabling:

- **Async Operations** - Long-running tasks don't block API requests
- **Distributed Processing** - Tasks can run on multiple worker processes
- **Task Queuing** - Fair scheduling with Redis broker
- **Retry Logic** - Automatic retry on failure
- **Result Tracking** - Store and retrieve task results

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│              (HTTP Requests from Clients)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ 1. Submit task
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Celery Application                        │
│              (celery_app - Task Registry)                    │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ 2. Queue task
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Redis Broker                            │
│           (Message Queue: localhost:6379/0)                  │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ 3. Pick task
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Celery Workers                            │
│              (Multiple processes executing tasks)            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ 4. Store result
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Redis Backend                             │
│          (Result Storage: localhost:6379/0)                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ 5. Retrieve result
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 Application Code                             │
│           (Check status, get results)                        │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Redis Broker** | Fast, reliable message queue |
| **Redis Backend** | Persistent result storage |
| **JSON Serialization** | Type-safe task parameters |
| **UTC Timezone** | Consistent time handling |
| **Task Discovery** | Auto-import from tasks.py |
| **Async Support** | Bridge async/sync operations |
| **Error Handling** | Automatic retry and logging |

---

## Celery Application

**Location**: `src/app/workers/celery_app.py`

### Celery Configuration

```python
from celery import Celery

# Initialize Celery app
celery_app = Celery(
    'app.workers',                          # App name
    broker='redis://localhost:6379/0',      # Message broker
    backend='redis://localhost:6379/0',     # Result backend
    include=['app.workers.tasks']           # Auto-discover tasks
)

# Configuration
celery_app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',                 # Use JSON for serialization
    accept_content=['json'],                # Only accept JSON
    result_serializer='json',               # Results in JSON format
    enable_utc=True,                        # Use UTC timezone
)
```

### Broker & Backend

#### Redis as Broker

**Purpose**: Message queue for task distribution

**Configuration**:
```python
broker='redis://localhost:6379/0'
```

**Features**:
- ✅ Fast in-memory queue
- ✅ Message persistence
- ✅ Multiple worker support
- ✅ Task priority support

#### Redis as Backend

**Purpose**: Store task results for retrieval

**Configuration**:
```python
backend='redis://localhost:6379/0'
```

**Features**:
- ✅ Result persistence
- ✅ TTL support for auto-cleanup
- ✅ Query task status
- ✅ Retrieve task results

---

## Task Definitions

**Location**: `src/app/workers/tasks.py`

Tasks are defined using the `@shared_task` decorator.

### Example Task

Simple arithmetic task for testing:

```python
from celery import shared_task

@shared_task
def example_task(x, y):
    """Example task that adds two numbers."""
    return x + y
```

**Usage**:
```python
from app.workers.tasks import example_task

# Execute asynchronously
result = example_task.delay(4, 5)

# Wait for result
answer = result.get()  # Returns: 9
```

### File Ingestion Task

Background file ingestion for RAG systems:

```python
import asyncio
from celery import shared_task
from typing import List

from app.core.schemas.ingestion_config import DataSourceConfig, DataSourceType
from app.services.ingestion.file_ingestion_service import FileIngestionService

async def create_ingestion_service(
    file_paths: List[str], 
    source_name: str = "documents"
):
    """
    Create a file ingestion service with the given configuration.
    
    Args:
        file_paths: List of file paths to ingest
        source_name: Name of the data source
    """
    config = DataSourceConfig(
        name=source_name,
        type=DataSourceType.FILE,
        sources=file_paths
    )
    return await FileIngestionService(config).ingest()

@shared_task
def task_file_ingestion(
    file_paths: List[str], 
    source_name: str = "documents"
):
    """
    Task to perform file ingestion.
    
    Args:
        file_paths: List of file paths to process
        source_name: Name of the data source
    
    Returns:
        bool: True if ingestion was successful, False otherwise
    """
    asyncio.run(create_ingestion_service(file_paths, source_name))
    return True
```

**Key Features**:
- ✅ **Async Bridge**: Uses `asyncio.run()` to call async ingestion service
- ✅ **Batch Processing**: Handles multiple files
- ✅ **Configuration**: Uses DataSourceConfig for settings
- ✅ **Error Handling**: Returns success/failure status

**Usage**:
```python
from app.workers.tasks import task_file_ingestion

# Submit ingestion task
result = task_file_ingestion.delay(
    file_paths=[
        "/data/docs/api_guide.pdf",
        "/data/docs/user_manual.pdf"
    ],
    source_name="product_documentation"
)

# Check status
print(f"Task ID: {result.id}")
print(f"Status: {result.status}")

# Wait for completion
success = result.get(timeout=300)  # 5 minute timeout
print(f"Ingestion successful: {success}")
```

---

## Running Tasks

### Immediate Execution

**Synchronous (blocks until complete)**:
```python
from app.workers.tasks import example_task

# Call directly (not recommended in production)
result = example_task(4, 5)
print(result)  # Prints: 9
```

### Delayed Execution

**Asynchronous (returns immediately)**:
```python
from app.workers.tasks import example_task

# Submit to Celery
async_result = example_task.delay(4, 5)

# Returns AsyncResult object immediately
print(f"Task ID: {async_result.id}")
```

### Getting Results

**Check status and retrieve result**:
```python
# Get async result
async_result = example_task.delay(10, 20)

# Check if task is ready
if async_result.ready():
    print("Task completed!")

# Check status
print(async_result.status)  # PENDING, STARTED, SUCCESS, FAILURE, RETRY

# Wait for result (blocking)
result = async_result.get(timeout=10)
print(f"Result: {result}")

# Check if task failed
if async_result.failed():
    print(f"Task failed: {async_result.info}")

# Get result without raising exception on failure
result = async_result.get(propagate=False)
```

---

## Task Monitoring

### Check Task Status

```python
from celery.result import AsyncResult

# Get task by ID
task_id = "a4f3c2e1-5d6a-4b8c-9e2f-1a3b5c7d9e1f"
result = AsyncResult(task_id, app=celery_app)

# Get status
print(f"Status: {result.status}")
print(f"Ready: {result.ready()}")
print(f"Successful: {result.successful()}")
print(f"Failed: {result.failed()}")

# Get metadata
print(f"Result: {result.result}")
print(f"Info: {result.info}")
```

### Task States

| State | Description |
|-------|-------------|
| `PENDING` | Task is waiting for execution |
| `STARTED` | Task has been started |
| `SUCCESS` | Task executed successfully |
| `FAILURE` | Task execution failed |
| `RETRY` | Task is being retried |
| `REVOKED` | Task was cancelled/revoked |

---

## Integration with API

**Location**: `src/app/api/v1/health.py`

### Test Endpoint

```python
from fastapi import APIRouter
from app.workers.tasks import example_task

router = APIRouter()

@router.get("/test-celery")
async def test_celery():
    """Test endpoint to verify Celery is working."""
    result = example_task.delay(4, 4)
    return {
        "task_id": result.id, 
        "message": "Task sent to Celery"
    }
```

**Usage**:
```bash
# Test Celery integration
curl http://localhost:8000/api/v1/health/test-celery

# Response:
{
  "task_id": "a4f3c2e1-5d6a-4b8c-9e2f-1a3b5c7d9e1f",
  "message": "Task sent to Celery"
}
```

### Ingestion Endpoint Example

```python
from fastapi import APIRouter, BackgroundTasks
from app.workers.tasks import task_file_ingestion

router = APIRouter()

@router.post("/ingest")
async def ingest_files(file_paths: List[str]):
    """Submit file ingestion task."""
    result = task_file_ingestion.delay(file_paths)
    
    return {
        "task_id": result.id,
        "status": "submitted",
        "message": f"Processing {len(file_paths)} files"
    }

@router.get("/ingest/status/{task_id}")
async def check_ingestion_status(task_id: str):
    """Check ingestion task status."""
    from celery.result import AsyncResult
    from app.workers.celery_app import celery_app
    
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "result": result.result if result.ready() else None
    }
```

---

## Creating Custom Tasks

### Step-by-Step Guide

#### 1. Define Task

```python
# In src/app/workers/tasks.py
from celery import shared_task
import time

@shared_task
def send_email_task(recipient: str, subject: str, body: str):
    """
    Send email in background.
    
    Args:
        recipient: Email recipient
        subject: Email subject
        body: Email body
        
    Returns:
        dict: Status and message
    """
    # Simulate email sending
    time.sleep(2)
    
    return {
        "success": True,
        "recipient": recipient,
        "sent_at": datetime.utcnow().isoformat()
    }
```

#### 2. Use Task

```python
from app.workers.tasks import send_email_task

# Submit task
result = send_email_task.delay(
    recipient="user@example.com",
    subject="Welcome!",
    body="Thank you for signing up."
)

# Check result
status = result.get(timeout=10)
print(status)
```

---

## Async Tasks

### Async Task Pattern

For async operations, use `asyncio.run()`:

```python
@shared_task
def async_operation_task(data: dict):
    """
    Execute async operation in Celery task.
    """
    async def do_async_work():
        # Your async code here
        await some_async_function()
        return result
    
    # Run async function
    return asyncio.run(do_async_work())
```

### Example: Database Operation

```python
@shared_task
def cleanup_old_sessions_task(days: int = 30):
    """Clean up sessions older than N days."""
    async def cleanup():
        from app.sessions.repositories.session_repository_factory import (
            SessionRepositoryFactory
        )
        
        repo = SessionRepositoryFactory.get_default_repository()
        await repo._ensure_connection()
        
        # Cleanup logic here
        return {"cleaned": 50}
    
    return asyncio.run(cleanup())
```

---

## Task Chains

Execute tasks sequentially:

```python
from celery import chain
from app.workers.tasks import example_task

# Chain tasks together
workflow = chain(
    example_task.s(2, 2),      # 2 + 2 = 4
    example_task.s(3),         # 4 + 3 = 7
    example_task.s(5)          # 7 + 5 = 12
)

# Execute chain
result = workflow.apply_async()
final_result = result.get()  # Returns: 12
```

---

## Periodic Tasks

### Using Celery Beat

Install celery-beat and configure periodic tasks:

```python
# In celery_app.py
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-old-sessions-daily': {
        'task': 'app.workers.tasks.cleanup_old_sessions_task',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
        'args': (30,)  # 30 days
    },
    'health-check-every-5-minutes': {
        'task': 'app.workers.tasks.system_health_check_task',
        'schedule': 300.0,  # 5 minutes in seconds
    },
}
```

### Run Beat Scheduler

```bash
# Start beat scheduler
celery -A app.workers.celery_app beat --loglevel=info
```

---

## Configuration

### Environment Variables

```bash
# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Worker Configuration
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_TASK_TIME_LIMIT=3600  # 1 hour
CELERY_TASK_SOFT_TIME_LIMIT=3300  # 55 minutes
```

### Production Configuration

```python
# In celery_app.py
celery_app.conf.update(
    broker_url=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
    
    # Task execution
    task_time_limit=3600,        # Hard limit: 1 hour
    task_soft_time_limit=3300,   # Soft limit: 55 minutes
    task_acks_late=True,         # Acknowledge after execution
    worker_prefetch_multiplier=1, # One task at a time
    
    # Result backend
    result_expires=3600,         # Results expire after 1 hour
    result_persistent=True,      # Persist results
    
    # Retry
    task_publish_retry=True,
    task_publish_retry_policy={
        'max_retries': 3,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.2,
    },
)
```

---

## Best Practices

### 1. Use Async for I/O Operations

```python
# ✅ GOOD - Async I/O operations
@shared_task
def process_files_task(file_paths: List[str]):
    async def process():
        async with aiohttp.ClientSession() as session:
            for file_path in file_paths:
                await upload_file(session, file_path)
    
    return asyncio.run(process())

# ❌ BAD - Blocking I/O in task
@shared_task
def process_files_task(file_paths: List[str]):
    for file_path in file_paths:
        # Blocking upload
        requests.post(url, files={'file': open(file_path, 'rb')})
```

### 2. Set Task Timeouts

```python
# ✅ GOOD - Set timeout
@shared_task(time_limit=300, soft_time_limit=270)
def long_running_task():
    # Will be killed after 300 seconds
    pass

# ❌ BAD - No timeout (can hang forever)
@shared_task
def long_running_task():
    while True:
        time.sleep(1)
```

### 3. Use Retry Logic

```python
# ✅ GOOD - Automatic retry
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def unstable_task(self, data):
    try:
        # Potentially failing operation
        result = api_call(data)
        return result
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

# ❌ BAD - No retry on failure
@shared_task
def unstable_task(data):
    return api_call(data)  # Fails permanently on error
```

### 4. Log Task Progress

```python
# ✅ GOOD - Log progress
@shared_task(bind=True)
def batch_process_task(self, items):
    total = len(items)
    for i, item in enumerate(items):
        process_item(item)
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': i + 1, 'total': total}
        )
    
    return {'processed': total}
```

### 5. Handle Task Failures Gracefully

```python
# ✅ GOOD - Graceful error handling
@shared_task
def critical_task(data):
    try:
        result = process_data(data)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Task failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

# ❌ BAD - Unhandled exceptions
@shared_task
def critical_task(data):
    result = process_data(data)  # Can crash task
    return result
```

---

## Troubleshooting

### Issue 1: Task Not Executing

**Symptoms**: Task stays in PENDING state

**Causes**:
- Worker not running
- Redis not accessible
- Task not registered

**Solutions**:
```bash
# Check if workers are running
celery -A app.workers.celery_app inspect active

# Check Redis connection
redis-cli -h localhost -p 6379 ping

# Start worker
celery -A app.workers.celery_app worker --loglevel=info
```

### Issue 2: Redis Connection Failed

**Error**: `ConnectionError: Error connecting to Redis`

**Solutions**:
```bash
# Check if Redis is running
redis-cli ping

# Start Redis (macOS)
brew services start redis

# Start Redis (Linux)
sudo systemctl start redis

# Check Redis logs
tail -f /var/log/redis/redis-server.log
```

### Issue 3: Task Timeout

**Error**: `SoftTimeLimitExceeded` or `TimeLimitExceeded`

**Solutions**:
```python
# Increase timeout
@shared_task(time_limit=600, soft_time_limit=570)
def long_task():
    pass

# Or in config
celery_app.conf.update(
    task_time_limit=600,
    task_soft_time_limit=570
)
```

### Issue 4: Task Serialization Error

**Error**: `EncodeError: Object of type X is not JSON serializable`

**Solutions**:
```python
# ✅ GOOD - Use JSON-serializable types
@shared_task
def my_task(data: dict, items: list):
    pass

# ❌ BAD - Custom objects not serializable
@shared_task
def my_task(obj: MyCustomClass):
    pass

# Solution: Serialize manually
@shared_task
def my_task(obj_dict: dict):
    obj = MyCustomClass.from_dict(obj_dict)
    pass
```

### Issue 5: Worker Memory Issues

**Symptoms**: Worker processes growing in memory

**Solutions**:
```bash
# Restart workers after N tasks
celery -A app.workers.celery_app worker --max-tasks-per-child=100

# Or in config
celery_app.conf.update(
    worker_max_tasks_per_child=100
)
```

---

## Running Workers

### Development

```bash
# Start single worker with INFO logging
celery -A app.workers.celery_app worker --loglevel=info

# Start with autoreload (development)
celery -A app.workers.celery_app worker --loglevel=info --autoreload
```

### Production

```bash
# Start multiple workers
celery -A app.workers.celery_app worker --concurrency=4 --loglevel=warning

# Start with systemd (Linux)
sudo systemctl start celery

# Start with supervisor
supervisorctl start celery
```

### Docker

```yaml
# docker-compose.yml
services:
  celery_worker:
    build: .
    command: celery -A app.workers.celery_app worker --loglevel=info
    depends_on:
      - redis
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
```

---

## Future Improvements

### 1. Task Priority

```python
# High priority task
@shared_task(priority=9)
def urgent_task():
    pass
```

### 2. Task Routing

```python
# Route to specific queue
@shared_task(queue='high_priority')
def critical_task():
    pass
```

### 3. Task Result Callbacks

```python
@shared_task
def on_success_callback(result):
    logger.info(f"Task succeeded: {result}")

@shared_task(link=on_success_callback.s())
def main_task():
    return "done"
```

### 4. Task Groups

```python
from celery import group

# Execute tasks in parallel
job = group(
    example_task.s(2, 2),
    example_task.s(3, 3),
    example_task.s(4, 4)
)
result = job.apply_async()
```

---

## Related Documentation

- **[Configuration Guide](../configuration/README.md)** - Redis configuration
- **[API Documentation](../../api/README.md)** - API integration
- **[Schemas Documentation](../schemas/README.md)** - Task input/output schemas

---

**Last Updated**: January 10, 2026  
**Version**: 1.0  
**Related**: Background Processing, Celery, Redis, Async Tasks

---

Thank you for using AgentHub's background workers system! ⚙️
