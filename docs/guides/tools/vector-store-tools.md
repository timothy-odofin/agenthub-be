# Vector Store Tools

Semantic search across your embedded knowledge base using vector similarity.

## Overview

Vector store tools enable AI agents to search through your indexed content using semantic similarity. Unlike keyword-based search, vector search understands the meaning and context of queries to find relevant information even when exact words don't match.

## What Gets Indexed

Your vector store can include:
- **Confluence pages** - Documentation and knowledge base articles
- **Uploaded files** - PDFs, markdown files, text documents
- **Code documentation** - README files, API docs
- **External content** - Web pages, articles, and other sources

Content is embedded (converted to vector representations) and stored for fast semantic retrieval.

## Features

- **Semantic Search** - Find relevant content based on meaning, not just keywords
- **Cross-Source Search** - Search across Confluence, files, and other document types simultaneously
- **Contextual Retrieval** - Get the most relevant passages with metadata
- **Fast Performance** - Optimized vector similarity search
- **Automatic Indexing** - Content is automatically embedded and ready to search

## How It Works

1. **Indexing** - Documents are split into chunks and converted to vector embeddings
2. **Storage** - Embeddings are stored in a vector database (Qdrant by default)
3. **Query** - When you search, your query is also converted to a vector
4. **Matching** - The system finds the most similar vectors using cosine similarity
5. **Results** - Relevant document chunks are returned with metadata

## Configuration

Vector store settings are in `resources/application-vector.yaml`:

```yaml
vector:
  provider: qdrant  # or pgvector
  embedding:
    model: text-embedding-ada-002
    dimension: 1536
  search:
    top_k: 4  # Number of results to return
    similarity_threshold: 0.7
```

Enable the tools in `resources/application-tools.yaml`:

```yaml
tools:
  vector:
    enabled: true
```

## Available Tool

### Retrieve Information

Search the vector store using semantic similarity.

**Parameters:**
- `query` - Natural language search query

**Examples:**

```python
# General search
retrieve_information("How do we handle authentication?")

# Technical search
retrieve_information("API rate limiting implementation")

# Troubleshooting
retrieve_information("Database connection errors")

# Concept search
retrieve_information("microservices architecture patterns")
```

**Response Format:**

The tool returns relevant document chunks with their content and metadata:

```
CONTENT:
OAuth2 authentication is implemented using the authorization code flow.
The client exchanges an authorization code for an access token...

METADATA:
{"source": "confluence", "page_id": "123456", "title": "Authentication Guide", "space": "DEV", "url": "/wiki/spaces/DEV/pages/123456"}

---

CONTENT:
For API authentication, we support three methods:
1. API keys for service-to-service communication
2. OAuth2 for user-facing applications
3. JWT tokens for mobile apps...

METADATA:
{"source": "file", "filename": "api-documentation.md", "path": "/docs/api-documentation.md"}
```

**Common Uses:**
- Search across all documentation
- Find similar content to a query
- Look up technical information
- Discover related documents
- Answer questions using indexed knowledge

---

## Usage Examples

### Searching for Documentation

**User:** "How do we deploy to production?"

**Agent Actions:**
1. Uses `retrieve_information` with query: "deployment production process"
2. Gets relevant chunks from deployment docs
3. Synthesizes answer from retrieved content

**Agent Response:**
```
Based on the documentation, here's our production deployment process:

1. **Build**: Create a Docker image with `docker build -t app:version .`
2. **Test**: Run integration tests in staging environment
3. **Push**: Upload image to container registry
4. **Deploy**: Use `kubectl apply -f k8s/production/` to deploy

The deployment guide also mentions:
- Always deploy during off-peak hours
- Run database migrations before deploying code
- Monitor logs for the first 30 minutes after deployment

Source: Deployment Guide (Confluence - PROD space)
```

---

### Finding Similar Content

**User:** "What documentation do we have about microservices?"

**Agent Actions:**
1. Uses `retrieve_information` with query: "microservices architecture design patterns"
2. Finds multiple relevant documents
3. Lists sources for user

**Agent Response:**
```
I found several documents about microservices in the knowledge base:

**Architecture Documents:**
1. "Microservices Design Patterns" (Confluence - SD space)
   - Covers service discovery, API gateway patterns, circuit breakers

2. "Service Mesh Implementation" (Confluence - DEV space)
   - Details on Istio setup and configuration

**Code Documentation:**
3. "Microservices Best Practices" (docs/architecture/microservices.md)
   - Guidelines for service boundaries, communication, and data management

4. "Breaking the Monolith" (uploaded PDF)
   - Migration strategy from monolithic to microservices architecture

Would you like me to get more details from any of these documents?
```

---

### Troubleshooting Support

**User:** "We're seeing database timeout errors. What should we check?"

**Agent Actions:**
1. Uses `retrieve_information` with query: "database timeout errors troubleshooting"
2. Finds relevant troubleshooting guides
3. Provides actionable steps

**Agent Response:**
```
Here's what to check for database timeout errors:

**Common Causes:**
1. Connection pool exhaustion - Check if max_connections is reached
2. Long-running queries - Look for queries exceeding 30 seconds
3. Network issues - Verify database server connectivity
4. Resource constraints - Check CPU/memory on database server

**Debugging Steps:**
1. Check Datadog for database metrics and slow queries
2. Review application logs for connection pool stats
3. Run EXPLAIN ANALYZE on suspected slow queries
4. Verify connection timeout settings in config

**Quick Fixes:**
- Increase connection pool size if constantly hitting max
- Add indexes to frequently queried columns
- Consider query optimization or caching

Sources:
- Database Troubleshooting Guide (Confluence)
- Performance Optimization Runbook (Confluence)
```

---

## When to Use Vector Store

### Best For:

**Cross-Source Semantic Search**
- Searching across Confluence, files, and other sources simultaneously
- "What do we have about testing?" (broad, multi-source query)
- Finding similar or related content

**Knowledge Discovery**
- Exploring what documentation exists
- Finding information when you don't know exact keywords
- Discovering related topics and connections

**Embedded Content**
- When real-time APIs aren't available
- For fast local searches without API calls
- When semantic similarity is more important than freshness

### Not Ideal For:

**Real-Time Data**
- Latest Confluence pages (use Confluence tools instead)
- Current Jira issue status (use Jira tools instead)
- Live system metrics (use Datadog tools instead)

**Specific System Queries**
- "List Jira projects" → Use Jira tools
- "Show me the latest page in DEV space" → Use Confluence tools
- "Check current CPU usage" → Use Datadog tools

## Vector Store vs Real-Time Tools

| Aspect | Vector Store | Real-Time Tools |
|--------|-------------|-----------------|
| **Data Freshness** | Slightly stale (requires re-indexing) | Always current |
| **Search Type** | Semantic similarity | Keyword/exact match |
| **Sources** | Multiple (Confluence + files + web) | Single source |
| **Speed** | Very fast (~100ms) | Depends on API (~500ms) |
| **Cost** | Embedding costs | API call costs |
| **Best For** | Broad discovery, similar content | Specific, current information |

**Use Both Together:**
- Vector store for discovery: "What docs exist about authentication?"
- Real-time tools for specifics: "Get the latest authentication guide from Confluence"

## Best Practices

### Query Formulation
- Use natural language questions
- Be specific but not overly narrow
- Include context: "production deployment process" vs just "deployment"
- Try multiple phrasings if first query doesn't yield results

### Result Interpretation
- Check metadata to understand source and context
- Note the similarity scores (if available)
- Cross-reference with real-time tools for current information
- Verify information date if recency matters

### Performance
- Start with default k=4 results
- Increase k if you need more context
- Consider similarity thresholds to filter weak matches
- Re-index content regularly to keep vector store current

## Maintaining the Vector Store

### Adding Content

Content can be added through data ingestion:

```python
# Confluence pages are automatically indexed
# Files can be uploaded and indexed
# External URLs can be scraped and indexed
```

### Updating Content

To update the vector store with fresh content:

1. Re-run the ingestion process for changed sources
2. Old embeddings are updated or replaced
3. New content is automatically indexed

### Monitoring

Check vector store health:
- Number of indexed documents
- Embedding model performance
- Search response times
- Storage usage

## Troubleshooting

### No Results Found

If searches return no relevant results:

1. **Check if content is indexed** - Verify documents exist in vector store
2. **Rephrase query** - Try different words or more context
3. **Broaden search** - Use more general terms
4. **Check embeddings** - Ensure embedding model is working

### Poor Result Quality

If results aren't relevant:

1. **Improve query specificity** - Add more context to your question
2. **Check similarity threshold** - May be too low
3. **Review indexed content** - Ensure quality sources are indexed
4. **Re-index content** - Embeddings may be outdated

### Slow Performance

If vector search is slow:

1. **Reduce k value** - Return fewer results
2. **Check database** - Verify vector DB performance
3. **Optimize indexes** - Ensure proper vector indexing
4. **Consider scaling** - May need more resources

### Tools Not Available

Make sure vector tools are enabled in `resources/application-tools.yaml`:

```yaml
tools:
  vector:
    enabled: true
```

## Combining with Other Tools

The AI agent intelligently combines vector store with other tools:

- **Vector + Confluence** - Discover docs in vector store, get latest from Confluence
- **Vector + Jira** - Find related docs, then check related Jira issues
- **Vector + Datadog** - Search troubleshooting guides, then check live metrics
- **Vector + GitHub** - Find documentation, then check related code

## Additional Resources

**Vector Database Documentation:**
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [PgVector Documentation](https://github.com/pgvector/pgvector)

**Embedding Models:**
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [Sentence Transformers](https://www.sbert.net/)

**Related Documentation:**
- [Confluence Tools](./confluence-tools.md) - Real-time Confluence access
- [All Available Tools](./README.md) - Complete tools overview
- [Configuration Guide](../configuration/resources-directory.md)

---

The vector store provides powerful semantic search capabilities across all your indexed content, helping AI agents discover information and answer questions using your organization's knowledge base.
