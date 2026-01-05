"""
Datadog Tools Provider - Main entry point for Datadog integration.
"""

from typing import List, Dict, Any, Optional
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.agent.tools.base.registry import ToolRegistry
from app.core.utils.logger import get_logger
from .datadog_wrapper import DatadogAPIWrapper

logger = get_logger(__name__)


# Input schemas for tools
class SearchLogsInput(BaseModel):
    """Input schema for searching Datadog logs."""
    query: str = Field(description="Datadog log search query (e.g., 'service:api status:error')")
    limit: int = Field(default=50, description="Maximum number of logs to return (default: 50, max: 200)")
    time_from: Optional[str] = Field(default=None, description="Start time in ISO format (optional)")
    time_to: Optional[str] = Field(default=None, description="End time in ISO format (optional)")


class QueryMetricsInput(BaseModel):
    """Input schema for querying Datadog metrics."""
    query: str = Field(description="Datadog metric query (e.g., 'avg:system.cpu.user{*}')")
    from_ts: int = Field(description="Start timestamp in UNIX seconds")
    to_ts: int = Field(description="End timestamp in UNIX seconds")


class ListMonitorsInput(BaseModel):
    """Input schema for listing Datadog monitors."""
    name_query: Optional[str] = Field(default="", description="Optional substring to filter monitor names")


@ToolRegistry.register("datadog", "monitoring")
class DatadogToolsProvider:
    """
    Datadog Tools Provider for monitoring and observability.
    
    Provides tools for:
    - Log searching and analysis
    - Metrics querying
    - Monitor management
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Datadog tools provider."""
        self.config = config or {}
        self._wrapper = None
        
    @property
    def wrapper(self) -> DatadogAPIWrapper:
        """Lazy initialization of API wrapper."""
        if self._wrapper is None:
            self._wrapper = DatadogAPIWrapper()
        return self._wrapper
    
    def get_tools(self) -> List[StructuredTool]:
        """
        Get all Datadog tools.
        
        This is the main entry point called by the ToolRegistry.
        
        Returns:
            List of Datadog monitoring tools
        """
        try:
            dd = self.wrapper
            
            def search_logs_func(
                query: str,
                limit: int = 50,
                time_from: Optional[str] = None,
                time_to: Optional[str] = None,
            ) -> str:
                """Search Datadog logs with a query string and optional time bounds."""
                logs = dd.search_logs(
                    query=query,
                    limit=limit,
                    time_from=time_from,
                    time_to=time_to,
                )
                
                if not logs:
                    return "No logs found matching the query."

                lines = [f"Found {len(logs)} log entries:\n"]
                for log in logs[:min(limit, 50)]:
                    ts = log.get("timestamp", "N/A")
                    svc = log.get("service", "unknown")
                    status = log.get("status", "N/A")
                    msg = (log.get("message") or "").replace("\n", " ")[:300]
                    host = log.get("host", "N/A")
                    
                    lines.append(f"[{ts}] {svc} @ {host} | {status} | {msg}")
                
                if len(logs) > 50:
                    lines.append(f"\n... and {len(logs) - 50} more log entries")
                
                return "\n".join(lines)
            
            datadog_search_logs = StructuredTool.from_function(
                func=search_logs_func,
                name="datadog_search_logs",
                description=(
                    "Search Datadog logs. Provide a Datadog query string, optionally with time bounds. "
                    "Use this to investigate errors, trace requests, or analyze application behavior. "
                    "Examples: 'service:api status:error', 'host:web-server-1', 'env:production service:api'"
                ),
                args_schema=SearchLogsInput,
            )

            def query_metrics_func(query: str, from_ts: int, to_ts: int) -> str:
                """Query Datadog metrics with a Datadog metric query."""
                result = dd.query_metrics(query=query, from_ts=from_ts, to_ts=to_ts)
                
                if "error" in result:
                    return f"Error querying metrics: {result['error']}"
                
                # Format the response for the agent
                series = result.get("series", [])
                if not series:
                    return "No metric data found for the query."
                
                lines = [f"Metric Query: {query}\n"]
                for s in series[:5]:  # Limit to 5 series
                    # Handle both dict and object responses
                    if isinstance(s, dict):
                        scope = s.get("scope", "N/A")
                        expression = s.get("expression", "N/A")
                        points = s.get("pointlist", [])
                    else:
                        scope = getattr(s, "scope", "N/A")
                        expression = getattr(s, "expression", "N/A")
                        points = getattr(s, "pointlist", [])
                    
                    if points:
                        # Get latest value
                        latest = points[-1]
                        latest_value = latest[1] if len(latest) > 1 else "N/A"
                        
                        # Calculate average
                        values = [p[1] for p in points if len(p) > 1]
                        avg_value = sum(values) / len(values) if values else 0
                        
                        lines.append(f"Scope: {scope}")
                        lines.append(f"  Expression: {expression}")
                        lines.append(f"  Latest: {latest_value:.2f}")
                        lines.append(f"  Average: {avg_value:.2f}")
                        lines.append(f"  Data points: {len(points)}\n")
                
                if len(series) > 5:
                    lines.append(f"... and {len(series) - 5} more series")
                
                return "\n".join(lines)
            
            datadog_query_metrics = StructuredTool.from_function(
                func=query_metrics_func,
                name="datadog_query_metrics",
                description=(
                    "Query Datadog metrics with a Datadog metric query. "
                    "Use this to check system performance, resource usage, or custom application metrics. "
                    "Examples: 'avg:system.cpu.user{{*}}', 'avg:system.mem.used{{*}}', 'avg:custom.app.requests{{service:api}}'"
                ),
                args_schema=QueryMetricsInput,
            )

            def list_monitors_func(name_query: Optional[str] = None) -> str:
                """List Datadog monitors, optionally filtering by name substring."""
                monitors = dd.list_monitors(name_query=name_query)
                
                if not monitors:
                    filter_msg = f" matching '{name_query}'" if name_query else ""
                    return f"No monitors found{filter_msg}."
                
                lines = [f"Found {len(monitors)} monitors:\n"]
                
                # Group by state
                by_state = {}
                for m in monitors:
                    state = m.get("overall_state", "Unknown")
                    if state not in by_state:
                        by_state[state] = []
                    by_state[state].append(m)
                
                # Show summary
                lines.append("Summary:")
                for state, mons in sorted(by_state.items()):
                    lines.append(f"  {state}: {len(mons)} monitors")
                lines.append("")
                
                # Show details for first 20 monitors
                for i, m in enumerate(monitors[:20]):
                    name = m.get("name", "Unnamed")
                    state = m.get("overall_state", "Unknown")
                    mon_type = m.get("type", "N/A")
                    mon_id = m.get("id", "N/A")
                    
                    lines.append(f"{i+1}. [{state}] {name}")
                    lines.append(f"   ID: {mon_id} | Type: {mon_type}")
                    
                    query = m.get("query")
                    if query:
                        # Truncate long queries
                        query_short = query[:100] + "..." if len(query) > 100 else query
                        lines.append(f"   Query: {query_short}")
                    lines.append("")
                
                if len(monitors) > 20:
                    lines.append(f"... and {len(monitors) - 20} more monitors")
                
                return "\n".join(lines)
            
            datadog_list_monitors = StructuredTool.from_function(
                func=list_monitors_func,
                name="datadog_list_monitors",
                description=(
                    "List Datadog monitors, optionally filtering by name substring. "
                    "Use this to check monitor status, find alerting conditions, or investigate incidents. "
                    "Examples: List all monitors, filter by name like 'CPU', find production monitors with 'prod'"
                ),
                args_schema=ListMonitorsInput,
            )

            tools = [datadog_search_logs, datadog_query_metrics, datadog_list_monitors]
            
            logger.info(f"Datadog tools initialized: {len(tools)} tools available")
            return tools
            
        except Exception as e:
            logger.error(f"Failed to initialize Datadog tools: {e}", exc_info=True)
            return []
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get Datadog connection information for debugging."""
        try:
            return self.wrapper.get_connection_info()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
