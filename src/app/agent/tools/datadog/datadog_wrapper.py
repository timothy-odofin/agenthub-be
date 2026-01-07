"""
Datadog API Wrapper - Handles authentication and API client configuration.
"""

from typing import List, Dict, Any, Optional

from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.logs_api import LogsApi
from datadog_api_client.v2.models import LogsSort, LogsListRequest, LogsListRequestPage
from datadog_api_client.v1.api.metrics_api import MetricsApi
from datadog_api_client.v1.api.monitors_api import MonitorsApi

from app.core.config.framework.settings import settings
from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class DatadogAPIWrapper:
    """
    Thin wrapper over Datadog APIs with guardrails and proper configuration.
    
    Handles:
    - API client configuration
    - Authentication
    - Request limiting (guardrails)
    - Error handling
    """

    def __init__(self):
        """Initialize Datadog API wrapper from configuration."""
        # Get config from settings
        dd_config = settings.external.datadog
        
        if not dd_config.api_key or not dd_config.app_key:
            raise ValueError("Missing Datadog API key or App key in configuration")
        
        self.config = dd_config
        
        # Configure Datadog API client directly (no environment variables)
        self._configuration = Configuration()
        self._configuration.api_key["apiKeyAuth"] = dd_config.api_key
        self._configuration.api_key["appKeyAuth"] = dd_config.app_key
        self._configuration.server_variables["site"] = dd_config.site
        
        # Set timeout if configured
        if hasattr(dd_config, 'timeout') and dd_config.timeout:
            self._configuration.connection_pool_maxsize = dd_config.timeout
        
        logger.info(f"Datadog API wrapper initialized for site: {dd_config.site}")

    def _client(self) -> ApiClient:
        """Create API client instance."""
        return ApiClient(self._configuration)

    def search_logs(
        self,
        query: str,
        limit: Optional[int] = None,
        sort_desc: bool = True,
        time_from: Optional[str] = None,
        time_to: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search Datadog logs with guardrails.
        
        Args:
            query: Datadog log search query (e.g., "service:api status:error")
            limit: Maximum number of logs to return
            sort_desc: Sort by timestamp descending (newest first)
            time_from: Start time in ISO format
            time_to: End time in ISO format
            
        Returns:
            List of log entries with relevant fields
        """
        # Apply limits from config with guardrails
        default_limit = getattr(self.config, 'default_limit', 50)
        max_limit = getattr(self.config, 'max_limit', 200)
        lim = limit or default_limit
        lim = max(1, min(lim, max_limit))

        try:
            with self._client() as api_client:
                api = LogsApi(api_client)
                
                # Build request body
                filter_dict = {"query": query}
                if time_from:
                    filter_dict["from"] = time_from
                if time_to:
                    filter_dict["to"] = time_to
                
                body = LogsListRequest(
                    filter=filter_dict,
                    page=LogsListRequestPage(limit=lim),
                    sort=LogsSort.TIMESTAMP_DESCENDING if sort_desc else LogsSort.TIMESTAMP_ASCENDING,
                )
                
                resp = api.list_logs(body=body)
                
                # Extract relevant fields from response
                out = []
                for item in (resp.data or []):
                    attrs = getattr(item, "attributes", None)
                    if attrs:
                        out.append({
                            "id": getattr(item, "id", None),
                            "timestamp": getattr(attrs, "timestamp", None),
                            "message": getattr(attrs, "message", None),
                            "service": getattr(attrs, "service", None),
                            "status": getattr(attrs, "status", None),
                            "host": getattr(attrs, "host", None),
                            "tags": getattr(attrs, "tags", None),
                        })
                
                logger.info(f"Datadog logs search returned {len(out)} results for query: {query}")
                return out
                
        except Exception as e:
            logger.error(f"Datadog logs search failed: {e}", exc_info=True)
            return []

    def query_metrics(
        self, 
        query: str, 
        from_ts: int, 
        to_ts: int
    ) -> Dict[str, Any]:
        """
        Query Datadog metrics.
        
        Args:
            query: Datadog metric query (e.g., "avg:system.cpu.user{*}")
            from_ts: Start timestamp in UNIX seconds
            to_ts: End timestamp in UNIX seconds
            
        Returns:
            Metric data with series information
        """
        try:
            with self._client() as api_client:
                api = MetricsApi(api_client)
                result = api.query_metrics(_from=from_ts, to=to_ts, query=query)
                
                logger.info(f"Datadog metrics query executed: {query}")
                return result
                
        except Exception as e:
            logger.error(f"Datadog metrics query failed: {e}", exc_info=True)
            return {"error": str(e), "series": []}

    def list_monitors(
        self, 
        name_query: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List Datadog monitors.
        
        Args:
            name_query: Optional substring to filter monitor names
            tags: Optional list of tags to filter monitors
            
        Returns:
            List of monitors with relevant fields
        """
        try:
            with self._client() as api_client:
                api = MonitorsApi(api_client)
                
                # Get monitors with optional tag filtering
                kwargs = {}
                if tags:
                    kwargs['tags'] = ','.join(tags)
                
                monitors = api.list_monitors(**kwargs) or []
                
                # Filter by name if provided
                out = []
                nq = (name_query or "").lower().strip()
                
                for m in monitors:
                    # Monitors can be dict or object depending on API version
                    if isinstance(m, dict):
                        name = (m.get("name") or "")
                        if nq and nq not in name.lower():
                            continue
                        out.append({
                            "id": m.get("id"),
                            "name": name,
                            "type": m.get("type"),
                            "overall_state": m.get("overall_state"),
                            "query": m.get("query"),
                            "message": m.get("message"),
                            "tags": m.get("tags", []),
                        })
                    else:
                        # Handle object response
                        name = getattr(m, 'name', '')
                        if nq and nq not in name.lower():
                            continue
                        out.append({
                            "id": getattr(m, 'id', None),
                            "name": name,
                            "type": getattr(m, 'type', None),
                            "overall_state": getattr(m, 'overall_state', None),
                            "query": getattr(m, 'query', None),
                            "message": getattr(m, 'message', None),
                            "tags": getattr(m, 'tags', []),
                        })
                
                logger.info(f"Datadog monitors list returned {len(out)} results")
                return out
                
        except Exception as e:
            logger.error(f"Datadog monitors list failed: {e}", exc_info=True)
            return []

    def get_connection_info(self) -> Dict[str, Any]:
        """Get Datadog connection information for debugging."""
        return {
            "site": self.config.site,
            "api_key_set": bool(self.config.api_key),
            "app_key_set": bool(self.config.app_key),
            "default_limit": getattr(self.config, 'default_limit', 50),
            "max_limit": getattr(self.config, 'max_limit', 200),
        }
