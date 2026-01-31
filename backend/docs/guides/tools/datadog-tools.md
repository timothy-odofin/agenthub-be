# Datadog Tools Integration

Connect your AI agents to Datadog for real-time monitoring and observability.

## Overview

This integration enables AI agents to interact with your Datadog account to:
- Search and analyze application logs
- Query system and application metrics
- Check monitor status and alerts

## Features

- **Log Search** - Find errors, traces, and application behavior patterns
- **Metrics Query** - Monitor CPU, memory, and custom application metrics
- **Monitor Status** - Check alerts and monitor configurations
- **Rate Limiting** - Built-in controls to manage API usage
- **Flexible Configuration** - YAML-based settings for easy customization

## Setup

### Getting Your Datadog API Credentials

You'll need two keys from your Datadog account:

1. Log in to your Datadog account
2. Go to **Organization Settings** → **API Keys**
3. Create or copy your **API Key**
4. Go to **Organization Settings** → **Application Keys**
5. Create or copy your **Application Key**

### Configuration

Add these environment variables to your `.env` file:

```bash
# Required
DATADOG_API_KEY=your_api_key_here
DATADOG_APP_KEY=your_app_key_here

# Optional (defaults shown)
DATADOG_SITE=datadoghq.com        # Use datadoghq.eu for EU region
DATADOG_DEFAULT_LIMIT=50          # Default number of results per query
DATADOG_MAX_LIMIT=200             # Maximum allowed results
DATADOG_TIMEOUT=30                # API request timeout in seconds
```

Update `resources/application-external.yaml`:

```yaml
external_services:
  datadog:
    enabled: true
    api_key: "${DATADOG_API_KEY}"
    app_key: "${DATADOG_APP_KEY}"
    site: "${DATADOG_SITE:datadoghq.com}"
    timeout: ${DATADOG_TIMEOUT:30}
    guardrails:
      default_limit: ${DATADOG_DEFAULT_LIMIT:50}
      max_limit: ${DATADOG_MAX_LIMIT:200}
```

Enable the tools in `resources/application-tools.yaml`:

```yaml
tools:
  datadog:
    enabled: true
```

## Available Tools

### Search Logs

Search through your Datadog logs using flexible query syntax.

**Parameters:**
- `query` - Search query using Datadog's log search syntax
- `limit` - Maximum number of logs to return (optional, default: 50)
- `time_from` - Start time in ISO format (optional)
- `time_to` - End time in ISO format (optional)

**Example Queries:**

```python
# Find errors in your API service
"service:api status:error"

# Search by hostname
"host:web-server-1"

# Combine multiple filters
"env:production service:api status:error"

# Use wildcards for pattern matching
"service:api message:*timeout*"
```

**Common Uses:**
- Debug production errors
- Trace request flows through your application
- Monitor application health
- Investigate user-reported issues
- Analyze application behavior patterns

### Query Metrics

Retrieve system and application metrics from Datadog.

**Parameters:**
- `query` - Metric query using Datadog's query syntax
- `from_ts` - Start time as UNIX timestamp in seconds
- `to_ts` - End time as UNIX timestamp in seconds

**Example Queries:**

```python
# Average CPU usage across all hosts
"avg:system.cpu.user{*}"

# Memory usage for a specific service
"avg:system.mem.used{service:api}"

# Custom application metrics
"avg:custom.app.requests{env:production}"

# HTTP request rate with aggregation
"sum:http.requests{*}.as_rate()"
```

**Common Uses:**
- Monitor CPU, memory, and disk usage
- Track application performance metrics
- Analyze traffic patterns
- Plan capacity needs
- Identify performance bottlenecks

### List Monitors

Check the status of your Datadog monitors and alerts.

**Parameters:**
- `name_query` - Filter monitors by name (optional)

**Examples:**

```python
# List all monitors
datadog_list_monitors()

# Find CPU-related monitors
datadog_list_monitors("CPU")

# Find production environment monitors
datadog_list_monitors("prod")
```

**Common Uses:**
- Check current alert status
- Investigate active incidents
- Review system health
- Audit monitoring coverage
- Troubleshoot alerting configuration

## Usage Examples

### Investigating Production Errors

**User:** "Are there any errors in the production API service in the last hour?"

**Agent Actions:**
1. Uses `datadog_search_logs` with query: `"service:api env:production status:error"`
2. Sets `time_from` to 1 hour ago
3. Analyzes log patterns
4. Reports error summary to user

**Agent Response:**
```
Found 15 error logs in the production API service:

[2024-01-01T10:30:45] api @ web-1 | ERROR | Database connection timeout after 30s
[2024-01-01T10:31:12] api @ web-2 | ERROR | Database connection timeout after 30s
[2024-01-01T10:35:22] api @ web-1 | ERROR | Redis cache unavailable: connection refused

Most common error: Database connection timeout (12 occurrences)
Affected hosts: web-1, web-2
```

### Checking System Performance

**User:** "What's the current CPU usage on our production servers?"

**Agent Actions:**
1. Calculates timestamps (last 1 hour)
2. Uses `datadog_query_metrics` with query: `"avg:system.cpu.user{env:production}"`
3. Analyzes metric trends
4. Reports findings

**Agent Response:**
```
CPU Usage (Production Servers - Last Hour):

Scope: env:production, host:web-1
  Expression: avg:system.cpu.user
  Latest: 45.23%
  Average: 42.15%
  Data points: 60

Scope: env:production, host:web-2
  Expression: avg:system.cpu.user
  Latest: 52.67%
  Average: 48.92%
  Data points: 60

Overall: CPU usage is within normal range, with web-2 slightly higher than web-1.
```

### Monitor Status Check

**User:** "Are all our production monitors in a healthy state?"

**Agent Actions:**
1. Uses `datadog_list_monitors` with filter: `"production"`
2. Groups monitors by state
3. Identifies any alerts
4. Reports summary

**Agent Response:**
```
Production Monitors Status:

Summary:
  OK: 45 monitors
  Alert: 2 monitors
  Warn: 3 monitors

ALERTS:
1. [Alert] Production Database Connection Pool
   ID: 12345 | Type: metric alert
   Query: avg(last_5m):avg:postgres.connections{env:production} > 80

2. [Alert] Production API Response Time
   ID: 12346 | Type: metric alert
   Query: avg(last_15m):avg:http.response.time{service:api} > 2000

Attention needed: 2 monitors in Alert state
```

## Best Practices

### Query Optimization
- Use specific service or host tags to narrow your search results
- Apply time ranges to avoid querying excessive data
- Choose appropriate aggregation functions for metrics (avg, sum, max, etc.)

### Rate Limiting
The integration includes built-in limits to manage API usage:
- Default: 50 results per query
- Maximum: 200 results (configurable via `DATADOG_MAX_LIMIT`)
- Results exceeding the limit are automatically truncated

### Security
- Store API keys in environment variables, never in code
- Credentials are never logged or exposed
- All operations are read-only by default

## Troubleshooting

### Missing API Credentials Error

If you see errors about missing API keys:

```bash
export DATADOG_API_KEY=your_key
export DATADOG_APP_KEY=your_app_key
```

Make sure these variables are set in your environment or `.env` file.

### No Results Returned

If your queries return no results, check:

1. **Query syntax** - Test your query in the Datadog UI first to verify it works
2. **Time range** - Make sure your time range includes the data you're looking for
3. **Tags** - Verify the service/host tags exist in your Datadog account

### Tools Not Available

If the Datadog tools aren't showing up, verify that they're enabled in `resources/application-tools.yaml`:

```yaml
tools:
  datadog:
    enabled: true
```

## Extending the Integration

You can add additional Datadog capabilities by:

1. Adding new methods to the API wrapper (`src/app/agent/tools/datadog/datadog_wrapper.py`)
2. Creating new tool functions in the provider (`src/app/agent/tools/datadog/datadog_tools.py`)
3. Enabling the new tools in your configuration
4. Writing tests for the new functionality

For example, to add event creation:

```python
@tool
def datadog_create_event(title: str, text: str, tags: List[str] = None) -> str:
    """Create a Datadog event for tracking deployments or incidents."""
    # Your implementation here
```

### Running Tests

The integration includes comprehensive unit tests:

```bash
pytest tests/unit/agent/tools/test_datadog_tools.py -v
```

## Combining with Other Tools

Your AI agent can use Datadog alongside other integrations for more powerful workflows:

- **Datadog + GitHub** - Find errors in logs, then check recent code changes
- **Datadog + Jira** - Detect issues in monitoring, then create or check related tickets
- **Datadog + Confluence** - Analyze errors, then search documentation for solutions
- **Datadog + Vector Store** - Identify patterns in logs, then search your knowledge base

## Additional Resources

**Datadog Documentation:**
- [API Documentation](https://docs.datadoghq.com/api/)
- [Log Search Syntax](https://docs.datadoghq.com/logs/search_syntax/)
- [Metrics Query Language](https://docs.datadoghq.com/dashboards/functions/)
- [Monitor API](https://docs.datadoghq.com/api/latest/monitors/)

**AgentHub Documentation:**
- [Confluence Tools](./confluence-tools.md)
- [All Available Tools](./README.md)
- [Configuration Guide](../configuration/resources-directory.md)

---

This integration brings Datadog's monitoring and observability capabilities directly to your AI agents, enabling them to investigate incidents, analyze performance, and monitor system health in real-time.
