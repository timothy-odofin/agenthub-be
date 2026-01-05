# Datadog Tools Integration

Comprehensive monitoring and observability tools for Datadog integration with AgentHub.

## Overview

The Datadog tools integration provides AI agents with the ability to:
- Search and analyze application logs
- Query system and application metrics
- Monitor alert status and configurations

## Features

✅ **Log Search**: Search Datadog logs with flexible query syntax  
✅ **Metrics Querying**: Query system and custom application metrics  
✅ **Monitor Management**: List and check status of Datadog monitors  
✅ **Guardrails**: Built-in rate limiting and result size controls  
✅ **Configuration-Driven**: All settings managed via YAML files  

## Configuration

### 1. Environment Variables

Add to your `.env` file:

```bash
# Datadog API Credentials
DATADOG_API_KEY=your_api_key_here
DATADOG_APP_KEY=your_app_key_here

# Datadog Site (optional, defaults to datadoghq.com)
DATADOG_SITE=datadoghq.com  # or datadoghq.eu for EU region

# Request Limits (optional)
DATADOG_DEFAULT_LIMIT=50    # Default number of results
DATADOG_MAX_LIMIT=200       # Maximum allowed results (guardrail)
DATADOG_TIMEOUT=30          # API timeout in seconds
```

### 2. Enable in Configuration

The Datadog tools are already configured in `resources/application-tools.yaml`:

```yaml
tools:
  datadog:
    enabled: true
    available_tools:
      logs:
        datadog_search_logs:
          enabled: true
          description: "Search Datadog logs for errors, traces, and application behavior"
          category: "observability"
      metrics:
        datadog_query_metrics:
          enabled: true
          description: "Query Datadog metrics for system and application performance"
          category: "observability"
      monitors:
        datadog_list_monitors:
          enabled: true
          description: "List and check status of Datadog monitors"
          category: "observability"
```

## Available Tools

### 1. **datadog_search_logs**

Search Datadog logs with flexible query syntax.

**Parameters:**
- `query` (str): Datadog log search query
- `limit` (int, optional): Maximum logs to return (default: 50, max: 200)
- `time_from` (str, optional): Start time in ISO format
- `time_to` (str, optional): End time in ISO format

**Example Queries:**
```python
# Search for errors in API service
"service:api status:error"

# Search by host
"host:web-server-1"

# Search with multiple tags
"env:production service:api status:error"

# Search with wildcards
"service:api message:*timeout*"
```

**Use Cases:**
- Investigate application errors
- Trace request flows
- Analyze user behavior
- Debug production issues
- Monitor application health

### 2. **datadog_query_metrics**

Query Datadog metrics for system and application performance.

**Parameters:**
- `query` (str): Datadog metric query
- `from_ts` (int): Start timestamp in UNIX seconds
- `to_ts` (int): End timestamp in UNIX seconds

**Example Queries:**
```python
# CPU usage across all hosts
"avg:system.cpu.user{*}"

# Memory usage for specific service
"avg:system.mem.used{service:api}"

# Custom application metric
"avg:custom.app.requests{env:production}"

# Request rate with aggregation
"sum:http.requests{*}.as_rate()"
```

**Use Cases:**
- Monitor system resource usage
- Track application performance
- Analyze traffic patterns
- Capacity planning
- Performance optimization

### 3. **datadog_list_monitors**

List and check status of Datadog monitors.

**Parameters:**
- `name_query` (str, optional): Filter by monitor name substring

**Example Usage:**
```python
# List all monitors
datadog_list_monitors()

# Find CPU-related monitors
datadog_list_monitors("CPU")

# Find production monitors
datadog_list_monitors("prod")
```

**Use Cases:**
- Check alert status
- Investigate incidents
- Monitor system health
- Audit monitoring coverage
- Troubleshoot alerting issues

## Agent Interaction Examples

### Example 1: Investigating Production Errors

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

### Example 2: Checking System Performance

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

### Example 3: Monitor Status Check

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

⚠️ Attention needed: 2 monitors in Alert state
```

## Architecture

```
DatadogToolsProvider
├── DatadogAPIWrapper
│   ├── Configuration from settings
│   ├── API client management
│   └── Request guardrails
└── Tools
    ├── datadog_search_logs
    ├── datadog_query_metrics
    └── datadog_list_monitors
```

## Best Practices

### 1. **Query Optimization**
- Use specific service/host tags to narrow results
- Apply time ranges to limit data volume
- Use appropriate aggregation functions

### 2. **Guardrails**
- Default limit: 50 results
- Maximum limit: 200 results (configurable)
- Results are automatically truncated to prevent context overflow

### 3. **Error Handling**
- All API errors are logged
- Failed requests return empty results
- Agent receives user-friendly error messages

### 4. **Security**
- API keys stored in environment variables
- No credentials in code or logs
- Read-only operations by default

## Testing

Run unit tests:

```bash
pytest tests/unit/agent/tools/test_datadog_tools.py -v
```

## Troubleshooting

### Issue: "Missing Datadog API key or App key"

**Solution:** Ensure environment variables are set:
```bash
export DATADOG_API_KEY=your_key
export DATADOG_APP_KEY=your_app_key
```

### Issue: No logs returned

**Possible causes:**
1. Query syntax incorrect
2. Time range doesn't include matching logs
3. Service/host tags don't exist

**Solution:** Test query in Datadog UI first, then use exact same syntax in agent

### Issue: Tools not available

**Solution:** Check `application-tools.yaml`:
```yaml
tools:
  datadog:
    enabled: true  # Must be true
```

## Getting Datadog Credentials

1. Log in to your Datadog account
2. Navigate to **Organization Settings** → **API Keys**
3. Create or copy your **API Key**
4. Navigate to **Organization Settings** → **Application Keys**
5. Create or copy your **Application Key**
6. Add both to your `.env` file

## Extending

To add new Datadog tools:

1. Add tool method to `DatadogAPIWrapper`
2. Add `@tool` decorated function to `DatadogToolsProvider.get_tools()`
3. Update `application-tools.yaml` configuration
4. Add unit tests

Example:

```python
@tool
def datadog_create_event(title: str, text: str, tags: List[str] = None) -> str:
    """Create a Datadog event."""
    # Implementation
```

## Resources

- [Datadog API Documentation](https://docs.datadoghq.com/api/)
- [Log Search Syntax](https://docs.datadoghq.com/logs/search_syntax/)
- [Metrics Query Language](https://docs.datadoghq.com/dashboards/functions/)
- [Monitor API](https://docs.datadoghq.com/api/latest/monitors/)

## License

Part of AgentHub - MIT License
