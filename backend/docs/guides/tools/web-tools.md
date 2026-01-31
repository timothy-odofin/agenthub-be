# Web Tools

Web tools enable agents to read and search external web content without requiring vector store embedding. This provides flexible access to up-to-date documentation, blogs, and other web resources.

## Overview

The web tools system consists of two types of tools:

1. **Static URL Tools**: Pre-configured tools for frequently accessed documentation sites
2. **Generic URL Reader**: Dynamic tool for accessing any whitelisted URL

## Features

- **Direct Web Access**: Read content without embedding into vector stores
- **Content Caching**: Reduces network overhead with configurable TTL
- **Smart Chunking**: Handles large pages efficiently with LangChain document chunks
- **Domain Whitelisting**: Security through allowed domain configuration
- **Search Capability**: Find specific content within fetched pages

## Configuration

Web tools are configured in `resources/application-tools.yaml`:

```yaml
tools:
  web:
    enabled: true
    cache_ttl: 3600  # Cache content for 1 hour (in seconds)
    
    # Content chunking configuration
    chunking:
      chunk_size: 1000      # Maximum characters per chunk
      chunk_overlap: 200    # Overlap between chunks to maintain context
    
    available_tools:
      # Static URL tools
      documentation:
        read_python_docs:
          enabled: true
          url: "https://docs.python.org/3/"
          description: "Search official Python documentation"
          max_content_length: 50000
        
        read_fastapi_docs:
          enabled: true
          url: "https://fastapi.tiangolo.com/"
          description: "Search FastAPI documentation"
          max_content_length: 50000
      
      # Generic URL reader
      generic:
        read_web_url:
          enabled: true
          description: "Read any whitelisted URL"
          allowed_domains:
            - "docs.python.org"
            - "fastapi.tiangolo.com"
            - "*.company.com"  # Wildcard support
          max_content_length: 50000
```

### Configuration Options

- **`cache_ttl`**: How long to cache web content (seconds, default: 3600)
- **`chunking.chunk_size`**: Maximum characters per chunk (default: 1000)
- **`chunking.chunk_overlap`**: Overlap between chunks for context (default: 200)
- **`max_content_length`**: Maximum content length per URL (bytes, default: 50000)
- **`allowed_domains`**: Whitelist for generic tool (supports wildcards like `*.domain.com`)


## Usage

### Static URL Tools

Static tools are automatically created for each configured URL:

**Agent Example:**
```
User: "What does Python docs say about asyncio?"

Agent: Uses read_python_docs tool
→ Fetches https://docs.python.org/3/
→ Searches for "asyncio"
→ Returns relevant sections
```

**Response Format:**
```json
{
  "status": "success",
  "url": "https://docs.python.org/3/",
  "title": "Python Documentation",
  "query": "asyncio",
  "matching_chunks": 3,
  "sections": [
    {
      "section": 1,
      "content": "asyncio is a library to write concurrent code...",
      "chunk_index": 15,
      "relevance": "high"
    }
  ]
}
```

### Generic URL Reader

For URLs not covered by static tools:

**Agent Example:**
```
User: "Read this article: https://realpython.com/async-io-python/"

Agent: Uses read_web_url tool
→ Checks domain whitelist
→ Fetches content if allowed
→ Returns formatted content
```

**Security:**
- Only whitelisted domains are accessible
- Error returned for blocked domains
- Includes hint for users to contact admin

## Architecture

### Components

1. **WebContentChunker** (`src/app/core/utils/web_content_chunker.py`)
   - Fetches web content asynchronously
   - Cleans HTML and extracts text
   - Chunks content using RecursiveCharacterTextSplitter
   - Handles caching with Redis

2. **WebTools** (`src/app/agent/tools/web/web_tools.py`)
   - Registers with ToolRegistry
   - Creates LangChain StructuredTools
   - Manages domain whitelisting
   - Formats responses for agents

3. **Cache Layer**
   - Uses existing RedisCacheProvider
   - Namespace: `web_content`
   - Configurable TTL (default: 1 hour)
   - Reduces redundant network requests

### Flow Diagram

```
User Query
    ↓
Agent selects tool
    ↓
Static URL? ────Yes────→ Use configured URL
    ↓ No                       ↓
Generic tool               Check cache
    ↓                          ↓
Check whitelist         Cache hit? ─Yes→ Return cached
    ↓                          ↓ No
Allowed? ─No→ Error       Fetch URL
    ↓ Yes                      ↓
Check cache               Clean HTML
    ↓                          ↓
Cache hit? ─Yes→ Return   Chunk content
    ↓ No                       ↓
Fetch URL                  Cache result
    ↓                          ↓
Clean & chunk             Search chunks
    ↓                          ↓
Cache result              Format response
    ↓                          ↓
Search & return           Return to agent
```

## Adding New Static URLs

1. **Edit Configuration:**

```yaml
# resources/application-tools.yaml
tools:
  web:
    available_tools:
      documentation:
        read_company_docs:
          enabled: true
          url: "https://docs.company.com/"
          description: "Search company documentation"
          max_content_length: 50000
```

2. **Restart Application:**
   - Tool automatically registered on startup
   - No code changes required

3. **Tool Available:**
   ```
   Agent now has: read_company_docs(query: str)
   ```

## Extending Allowed Domains

**For Generic Tool:**

```yaml
tools:
  web:
    available_tools:
      generic:
        read_web_url:
          allowed_domains:
            - "docs.python.org"
            - "github.com"
            - "*.internal"  # Wildcard for *.internal domains
```

**Wildcard Patterns:**
- `*.example.com` matches `api.example.com`, `docs.example.com`
- `*.internal` matches any subdomain ending in `.internal`

## Caching Strategy

**Cache Key Generation:**
```python
# URL is hashed for safe, fixed-length keys
url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
cache_key = f"web_url_{url_hash}"
```

**Cache Content:**
```json
[
  {
    "page_content": "Chunk text here...",
    "metadata": {
      "url": "https://example.com",
      "title": "Page Title",
      "fetch_time": "2026-01-12T10:30:00",
      "chunk_index": 0,
      "total_chunks": 5
    }
  }
]
```

**TTL Configuration:**
```yaml
tools:
  web:
    cache_ttl: 3600  # 1 hour (in seconds)
```

## Performance Considerations

1. **Chunking:**
   - Default: 1000 characters per chunk
   - Overlap: 200 characters for context
   - Configurable in WebContentChunker

2. **Content Limits:**
   - Default: 50KB per page
   - Prevents excessive memory usage
   - Content truncated if exceeded

3. **Caching:**
   - Reduces network requests
   - Shares cache across agent sessions
   - Automatic expiration via TTL

4. **HTML Cleaning:**
   - Removes scripts, styles, navigation
   - Normalizes whitespace
   - Extracts page title

## Security

### Domain Whitelisting

**Purpose:**
- Prevent access to malicious sites
- Control allowed resources
- Reduce attack surface

**Implementation:**
```python
def _is_domain_allowed(domain: str, allowed: List[str]) -> bool:
    for allowed_domain in allowed:
        if allowed_domain.startswith("*."):
            # Wildcard match
            suffix = allowed_domain[2:]
            if domain.endswith(suffix):
                return True
        elif domain == allowed_domain:
            # Exact match
            return True
    return False
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Domain 'malicious.com' is not whitelisted",
  "allowed_domains": ["docs.python.org", "example.com"],
  "hint": "Contact your administrator to whitelist this domain"
}
```

### Content Validation

- **URL Format**: Validates URL structure
- **Content Length**: Enforces maximum size
- **HTML Sanitization**: Removes potentially harmful content
- **Error Handling**: Graceful degradation on failures

## Testing

### Unit Tests

**WebContentChunker Tests:**
```bash
pytest tests/unit/core/utils/test_web_content_chunker.py -v
```

**WebTools Tests:**
```bash
pytest tests/unit/agent/tools/test_web_tools.py -v
```

**Test Coverage:**
- Fetching and chunking
- Caching behavior
- Domain whitelisting
- Error handling
- Response formatting

### Integration Testing

**Manual Test:**
```python
from app.agent.tools.web import WebTools

# Initialize tools
web_tools = WebTools()
tools = web_tools.get_tools()

# Find static tool
python_docs_tool = next(t for t in tools if t.name == "read_python_docs")

# Test tool
result = await python_docs_tool.func(query="asyncio")
print(result)
```

## Troubleshooting

### Issue: Tool Not Appearing

**Check:**
1. Configuration enabled: `web.enabled: true`
2. Tool enabled: `read_python_docs.enabled: true`
3. Import in `__init__.py`: `from . import web`

### Issue: Domain Blocked

**Error:**
```json
{
  "status": "error",
  "message": "Domain 'example.com' is not whitelisted"
}
```

**Solution:**
Add domain to `allowed_domains` list in configuration.

### Issue: Cache Not Working

**Check:**
1. Redis connection available
2. Cache namespace: `web_content`
3. TTL configuration: `cache_ttl: 3600`

**Debug:**
```python
from app.services.cache.cache_factory import CacheFactory

cache = CacheFactory.create_cache(namespace="web_content")
# Check cache connectivity
```

### Issue: Content Truncated

**Cause:**
Content exceeds `max_content_length`

**Solution:**
Increase limit in configuration:
```yaml
read_python_docs:
  max_content_length: 100000  # 100KB
```

## Comparison: Web Tools vs Embedding

| Aspect | Web Tools | Embedding |
|--------|-----------|-----------|
| **Freshness** | Always current | Can be stale |
| **Latency** | Higher (network) | Lower (local) |
| **Setup** | Minimal config | Requires ingestion |
| **Storage** | Cache only | Vector DB |
| **Search** | Keyword-based | Semantic |
| **Best For** | External docs, blogs | Large document sets |

## Best Practices

1. **Use Static Tools for Frequent Docs:**
   - Better LLM tool selection
   - Descriptive names help agent
   - Faster than generic tool

2. **Whitelist Carefully:**
   - Only trusted domains
   - Use wildcards for internal domains
   - Regular security reviews

3. **Configure Appropriate TTL:**
   - Frequent updates: Lower TTL (1 hour)
   - Stable docs: Higher TTL (24 hours)
   - Balance freshness vs performance

4. **Limit Content Size:**
   - Prevents memory issues
   - Faster processing
   - Better agent responses

5. **Monitor Cache Usage:**
   - Track cache hit rates
   - Adjust TTL based on patterns
   - Clear cache if needed

## Future Enhancements

Potential improvements:

1. **JavaScript Rendering**: Support for dynamic content
2. **PDF Support**: Read PDF documentation directly
3. **Authentication**: Access private documentation
4. **Rate Limiting**: Prevent excessive requests
5. **Content Summarization**: AI-powered page summaries
6. **Link Following**: Crawl related pages

## API Reference

### WebContentChunker

```python
class WebContentChunker:
    """Fetch and chunk web content."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        cache_provider: Optional[BaseCacheProvider] = None,
        cache_ttl: int = 3600
    )
    
    async def fetch_and_chunk(
        self,
        url: str,
        use_cache: bool = True,
        max_content_length: Optional[int] = None
    ) -> List[Document]
```

### WebTools

```python
@ToolRegistry.register("web", "web")
class WebTools:
    """Web content reading tools."""
    
    def get_tools(self) -> List[StructuredTool]
    
    async def _read_static_url(
        self,
        url: str,
        query: str,
        max_content_length: Optional[int] = None
    ) -> str
    
    async def _read_dynamic_url(
        self,
        url: str,
        query: str = ""
    ) -> str
```

## Contributing

When adding new features:

1. Follow existing patterns (Confluence, GitHub tools)
2. Add comprehensive unit tests
3. Update this documentation
4. Test with real URLs
5. Consider security implications

## License

This component is part of AgentHub and follows the same license.
