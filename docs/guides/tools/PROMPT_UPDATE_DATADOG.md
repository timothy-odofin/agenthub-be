# Prompt Configuration Update - Datadog Tools Integration

## Summary

Updated `application-prompt.yaml` to include comprehensive guidance for Datadog monitoring and observability tools.

---

## Changes Made

### 1. Added Datadog to "When to Use Tools" Section

**Before:**
```yaml
**DO use tools for:**
- Retrieving current/live data (issues, files, database records)
- Searching specific systems (GitHub, Jira, vector stores)
```

**After:**
```yaml
**DO use tools for:**
- Retrieving current/live data (issues, files, database records, logs, metrics)
- Searching specific systems (GitHub, Jira, Datadog, vector stores)
- Investigating incidents or performance issues (logs, metrics, monitors)
- Checking system health and monitoring status
```

### 2. Added Datadog Tool Category Description

**New Section:**
```yaml
### Datadog Tools
Monitor and observe application and system performance:
- **Logs**: Search and analyze application logs for errors, traces, and behavior patterns
- **Metrics**: Query system and application metrics (CPU, memory, custom metrics)
- **Monitors**: Check alert status and monitor configurations

**Use Datadog tools for**:
- Investigating production errors or incidents
- Checking system performance and resource usage
- Analyzing application behavior and patterns
- Monitoring alert status and health checks
- Troubleshooting performance issues
```

### 3. Added Two New Examples

**Example 5 - Datadog Incident Investigation:**
```yaml
User: "Are there any errors in the production API service?"

Thought: I need to search Datadog logs for errors in the production API service.
Action: Use `datadog_search_logs` with query "service:api env:production status:error"
Observation: [Tool returns error logs with timestamps, messages, and affected hosts]
Response: "Yes, I found 15 errors in the production API service in the last hour. 
The most common issue is database connection timeouts (10 occurrences) affecting 
hosts web-1 and web-2. Here are the details: [formatted log summary with 
timestamps and error patterns]"
```

**Example 6 - System Performance Check:**
```yaml
User: "What's the current CPU usage on our production servers?"

Thought: I need to query Datadog metrics for CPU usage on production servers.
Action: Use `datadog_query_metrics` with query "avg:system.cpu.user{env:production}"
Observation: [Tool returns metric data for production hosts]
Response: "CPU usage on production servers is currently healthy. web-1 is at 45% 
(avg: 42%) and web-2 is at 53% (avg: 49%). Both are within normal operating range."
```

---

## Impact

### For the Agent:
✅ **Clear guidance** on when to use Datadog tools  
✅ **Specific examples** of log searches and metrics queries  
✅ **Context awareness** for incident investigation and performance monitoring  
✅ **Better decision-making** about tool selection  

### For Users:
✅ **More intelligent responses** to production issues  
✅ **Proactive monitoring** insights  
✅ **Faster incident resolution** through automated log analysis  
✅ **Performance optimization** recommendations based on real metrics  

---

## Example Use Cases Now Supported

### 1. Error Investigation
**User:** "Why is the API slow?"  
**Agent:** Uses `datadog_search_logs` + `datadog_query_metrics` to analyze errors and performance

### 2. Performance Monitoring
**User:** "How is our production system performing?"  
**Agent:** Uses `datadog_query_metrics` for CPU, memory, response times

### 3. Alert Status Check
**User:** "Are there any active alerts?"  
**Agent:** Uses `datadog_list_monitors` to check monitor status

### 4. Incident Analysis
**User:** "What caused the outage at 3pm?"  
**Agent:** Uses `datadog_search_logs` with time filters to investigate

### 5. Capacity Planning
**User:** "Do we need to scale up?"  
**Agent:** Uses `datadog_query_metrics` to analyze resource trends

---

## ReAct Process with Datadog

The agent now understands to:

1. **Thought**: "User is asking about production errors - I need to check Datadog logs"
2. **Action**: Use `datadog_search_logs` with appropriate query
3. **Observation**: Analyze log patterns, frequencies, affected hosts
4. **Action** (if needed): Use `datadog_query_metrics` for additional context
5. **Response**: Provide comprehensive analysis with actionable insights

---

## Integration with Existing Tools

The prompt now guides the agent to:

- **Combine tools**: Use Datadog + GitHub (e.g., find errors, then check related code)
- **Cross-reference**: Use Datadog + Jira (e.g., find errors, then check related tickets)
- **Validate**: Use Datadog + Vector Store (e.g., find issues, then check documentation)

---

## Best Practices Included

✅ Use specific Datadog query syntax (service:, env:, status:)  
✅ Include time ranges for relevant queries  
✅ Analyze patterns, not just individual logs  
✅ Provide actionable insights, not just raw data  
✅ Cite specific sources (hosts, services, timestamps)  

---

## Files Modified

- `resources/application-prompt.yaml` (171 lines)
  - Added Datadog tool category (11 lines)
  - Updated "When to Use Tools" section (2 lines)
  - Added 2 new examples (22 lines)

---

## Validation

The prompt structure follows the same pattern as:
- ✅ GitHub Tools (repository-scoped operations)
- ✅ Vector Store Tools (knowledge retrieval)
- ✅ Jira Tools (issue management)

Ensuring consistency in:
- Tool category descriptions
- Usage guidance
- Example formats
- ReAct process demonstration

---

## Next Steps

With this prompt update, the agent will now:

1. **Recognize** when to use Datadog tools for monitoring queries
2. **Construct** proper Datadog queries with appropriate syntax
3. **Analyze** logs and metrics to provide insights
4. **Combine** Datadog with other tools for comprehensive analysis
5. **Respond** with actionable recommendations based on monitoring data

---

**Status**: ✅ Complete  
**Date**: December 29, 2025  
**Impact**: High - Enables intelligent monitoring and incident response capabilities
