# Ingestion API

> **Document and data ingestion** for RAG (Retrieval-Augmented Generation) systems

## Overview

The Ingestion API allows you to upload and process documents, files, and data sources for use in AI-powered retrieval and question-answering.

**Base Path**: `/api/v1/ingest/` 
**Authentication**: Required (JWT Bearer token)

---

## Endpoint

### POST /load/{data_source}

Ingest data from a specific source type.

**Authentication**: Required

**Path Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `data_source` | enum | Type of data source to ingest |

**Supported Data Sources**:

| Source Type | Value | Description |
|-------------|-------|-------------|
| **FILE** | `file` | Local files (PDF, TXT, MD, DOC) |
| **JIRA** | `jira` | Jira tickets and issues |
| **CONFLUENCE** | `confluence` | Confluence pages and spaces |
| **WEB** | `web` | Web pages and URLs |
| **DATABASE** | `database` | Database tables and queries |
| **API** | `api` | External API data |

**Request Headers**:
```
Authorization: Bearer eyJhbGci...
Content-Type: application/json
```

**Success Response** (200 OK):
```json
{
"message": "Data loaded successfully"
}
```

**Error Response**:
```json
{
"message": "Data loading failed"
}
```

---

## Data Source Examples

### 1. File Ingestion

Ingest local files (PDF, TXT, Markdown, Word documents):

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/ingest/load/file \
-H "Authorization: Bearer eyJhbGci..." \
-H "Content-Type: application/json"
```

**Supported File Types**:
- PDF (`.pdf`)
- Text (`.txt`)
- Markdown (`.md`)
- Word (`.doc`, `.docx`)
- CSV (`.csv`)
- JSON (`.json`)

**Configuration**:
```yaml
# resources/application-data.yaml
data_sources:
file:
type: FILE
sources:
- "/path/to/documents/*.pdf"
- "/path/to/docs/*.md"
chunk_size: 1000
chunk_overlap: 200
```

---

### 2. Jira Ingestion

Ingest Jira tickets and issues:

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/ingest/load/jira \
-H "Authorization: Bearer eyJhbGci..." \
-H "Content-Type: application/json"
```

**What Gets Ingested**:
- Issue titles and descriptions
- Comments and attachments
- Custom fields
- Issue history and status changes

**Configuration**:
```yaml
# resources/application-external.yaml
external:
jira:
base_url: "https://your-domain.atlassian.net"
email: "your-email@example.com"
api_token: "${JIRA_API_TOKEN}"
project_keys:
- "PROJ"
- "DEV"
```

---

### 3. Confluence Ingestion

Ingest Confluence pages and spaces:

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/ingest/load/confluence \
-H "Authorization: Bearer eyJhbGci..." \
-H "Content-Type: application/json"
```

**What Gets Ingested**:
- Page content (body)
- Page titles and metadata
- Attachments
- Comments

**Configuration**:
```yaml
# resources/application-external.yaml
external:
confluence:
base_url: "https://your-domain.atlassian.net/wiki"
email: "your-email@example.com"
api_token: "${CONFLUENCE_API_TOKEN}"
spaces:
- "ENG"
- "DOCS"
```

---

### 4. Web Scraping

Ingest content from web pages:

**Request**:
```bash
curl -X POST http://localhost:8000/api/v1/ingest/load/web \
-H "Authorization: Bearer eyJhbGci..." \
-H "Content-Type: application/json"
```

**What Gets Ingested**:
- Page text content
- Headings and structure
- Metadata (title, description)
- Links (optional)

**Configuration**:
```yaml
# resources/application-data.yaml
data_sources:
web:
type: WEB
sources:
- "https://docs.example.com/*"
- "https://blog.example.com/posts/*"
max_depth: 2
follow_links: true
```

---

## Complete Ingestion Flow

### Python Example

```python
import requests
import time

class IngestionClient:
def __init__(self, access_token):
self.base_url = "http://localhost:8000"
self.access_token = access_token

def ingest(self, data_source: str):
"""Trigger data ingestion."""
response = requests.post(
f"{self.base_url}/api/v1/ingest/load/{data_source}",
headers={
"Authorization": f"Bearer {self.access_token}",
"Content-Type": "application/json"
}
)

if response.status_code == 200:
return response.json()
else:
raise Exception(f"Ingestion failed: {response.json()}")

def ingest_all_sources(self):
"""Ingest all configured data sources."""
sources = ["file", "jira", "confluence"]
results = {}

for source in sources:
print(f"Ingesting {source}...")
try:
result = self.ingest(source)
results[source] = result
print(f"{source}: {result['message']}")
except Exception as e:
results[source] = {"error": str(e)}
print(f" {source}: {e}")

# Wait between sources
time.sleep(1)

return results

# Usage
client = IngestionClient(access_token="your_token_here")

# Ingest single source
result = client.ingest("file")
print(result)

# Ingest all sources
results = client.ingest_all_sources()
```

---

## Background Processing

Ingestion runs as a **background task** using Celery:

```python
# Behind the scenes
@shared_task
def task_file_ingestion(file_paths: List[str], source_name: str = "documents"):
"""Background task for file ingestion."""
config = DataSourceConfig(
name=source_name,
type=DataSourceType.FILE,
sources=file_paths
)
service = FileIngestionService(config)
return await service.ingest()
```

**Benefits**:
- Non-blocking API responses
- Can process large datasets
- Automatic retry on failure
- Progress tracking (coming soon)

---

## Document Processing Pipeline

### Step-by-Step

```
1. Load Documents
↓
2. Extract Text
(PDF, DOCX, etc. → plain text)
↓
3. Chunk Content
(Split into manageable pieces)
↓
4. Generate Embeddings
(Convert text → vectors)
↓
5. Store in Vector DB
(Qdrant, PgVector, or ChromaDB)
↓
6. Index for Retrieval
(Ready for RAG queries)
```

### Configuration

```yaml
# resources/application-embeddings.yaml
embeddings:
provider: "openai"
model: "text-embedding-ada-002"
dimensions: 1536
batch_size: 100

# resources/application-vector.yaml
vector_db:
provider: "qdrant"
collection: "documents"
host: "localhost"
port: 6333
```

---

## Advanced Usage

### Custom File Paths

Configure specific files to ingest:

```yaml
# resources/application-data.yaml
data_sources:
technical_docs:
type: FILE
sources:
- "/docs/api/*.pdf"
- "/docs/guides/*.md"
metadata:
category: "technical"
version: "2.0"

user_guides:
type: FILE
sources:
- "/docs/user/*.pdf"
metadata:
category: "user_guide"
audience: "end_user"
```

---

### Filtering Jira Issues

Filter by project, status, or custom fields:

```yaml
# resources/application-external.yaml
external:
jira:
base_url: "https://your-domain.atlassian.net"
email: "your-email@example.com"
api_token: "${JIRA_API_TOKEN}"
filters:
projects: ["PROJ", "DEV"]
status: ["Open", "In Progress"]
created_after: "2025-01-01"
```

---

### Chunking Strategy

Control how documents are split:

```yaml
# resources/application-data.yaml
chunking:
strategy: "semantic" # or "fixed", "recursive"
chunk_size: 1000 # characters per chunk
chunk_overlap: 200 # overlap between chunks
separators:
- "\n\n"
- "\n"
- " "
```

**Strategies**:

| Strategy | Description | Best For |
|----------|-------------|----------|
| **fixed** | Fixed character count | Simple documents |
| **recursive** | Split by separators recursively | Most documents |
| **semantic** | Split at meaningful boundaries | Technical docs |

---

## Error Handling

### Common Errors

```json
// Authentication Error (401)
{
"detail": "Not authenticated"
}

// Invalid Data Source (400)
{
"message": "Data loading failed",
"error": "Invalid data source type: 'invalid_source'"
}

// Configuration Error (500)
{
"message": "Data loading failed",
"error": "No file sources configured"
}

// External Service Error (503)
{
"message": "Data loading failed",
"error": "Jira API connection failed: Invalid credentials"
}

// Vector DB Error (503)
{
"message": "Data loading failed",
"error": "Qdrant connection failed: Connection refused"
}
```

---

## Monitoring Ingestion

### Check Ingestion Status

Currently, ingestion runs synchronously. Status monitoring is planned:

**Planned Endpoint** (coming soon):
```bash
GET /api/v1/ingest/status/{task_id}
```

**Planned Response**:
```json
{
"task_id": "abc-123-def",
"status": "processing",
"progress": {
"total_documents": 100,
"processed": 45,
"percentage": 45
},
"started_at": "2026-01-10T14:00:00Z",
"estimated_completion": "2026-01-10T14:10:00Z"
}
```

---

## Best Practices

### 1. Incremental Ingestion

```python
# GOOD - Ingest new documents only
# Track last ingestion timestamp
last_ingestion = get_last_ingestion_time()
ingest_since(last_ingestion)

# BAD - Re-ingest everything every time
ingest_all_documents()
```

### 2. Error Handling

```python
# GOOD - Retry on failure
def ingest_with_retry(source, max_retries=3):
for attempt in range(max_retries):
try:
return client.ingest(source)
except Exception as e:
if attempt == max_retries - 1:
raise
time.sleep(2 ** attempt) # Exponential backoff

# BAD - No error handling
result = client.ingest(source)
```

### 3. Batch Processing

```python
# GOOD - Process in batches
sources = ["file", "jira", "confluence", "web"]
for source in sources:
ingest(source)
time.sleep(5) # Rate limiting

# BAD - All at once
for source in sources:
ingest(source) # May overwhelm system
```

---

## Configuration Reference

### Supported File Types

| Extension | Type | Parser |
|-----------|------|--------|
| `.pdf` | PDF Document | PyPDF |
| `.txt` | Plain Text | Built-in |
| `.md` | Markdown | markdown-it |
| `.doc`, `.docx` | Word Document | python-docx |
| `.csv` | CSV Data | pandas |
| `.json` | JSON Data | Built-in |
| `.html` | HTML | BeautifulSoup |

### Environment Variables

```bash
# External Services
export JIRA_API_TOKEN="your_jira_token"
export CONFLUENCE_API_TOKEN="your_confluence_token"

# Vector Database
export QDRANT_URL="http://localhost:6333"
export QDRANT_API_KEY="your_api_key"

# OpenAI (for embeddings)
export OPENAI_API_KEY="your_openai_key"
```

---

## Performance Optimization

### Parallel Processing

```python
# Process multiple sources in parallel
from concurrent.futures import ThreadPoolExecutor

def ingest_parallel(sources):
with ThreadPoolExecutor(max_workers=3) as executor:
futures = [executor.submit(client.ingest, source) for source in sources]
results = [f.result() for f in futures]
return results
```

### Caching

```python
# Cache embeddings to avoid recomputation
# Coming soon: Automatic deduplication
```

---

## Related Documentation

- **[Workers Guide](../guides/workers/README.md)** - Background task processing
- **[Database Guide](../guides/database/README.md)** - Vector database setup
- **[Configuration Guide](../guides/configuration/README.md)** - Data source configuration

---

**Last Updated**: January 10, 2026 
**Status**: Beta (Production-ready for file ingestion)

---
