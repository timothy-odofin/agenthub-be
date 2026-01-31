"""
Confluence integration tools for knowledge base access and content retrieval.
"""

import json
from typing import List, Dict, Any, Optional
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from app.agent.tools.base.registry import ToolRegistry


# Pydantic models for structured input
class GetPageInput(BaseModel):
    """Input schema for getting a Confluence page."""
    page_id: str = Field(description="The Confluence page ID (e.g., '123456789')")


class SearchPagesInput(BaseModel):
    """Input schema for searching Confluence pages."""
    query: str = Field(description="Search query text to find in page titles and content")
    space_key: Optional[str] = Field(default=None, description="Optional space key to limit search (e.g., 'MYSPACE')")
    max_results: Optional[int] = Field(default=10, description="Maximum number of results to return")


class ListSpacesInput(BaseModel):
    """Input schema for listing Confluence spaces."""
    space_keys: Optional[List[str]] = Field(
        default=None,
        description="Optional list of specific space keys to retrieve. Use ['*'] for all spaces."
    )


class GetSpaceInput(BaseModel):
    """Input schema for getting a specific Confluence space."""
    space_key: str = Field(description="The Confluence space key (e.g., 'MYSPACE')")


class ListPagesInSpaceInput(BaseModel):
    """Input schema for listing all pages in a space."""
    space_key: str = Field(description="The Confluence space key (e.g., 'MYSPACE')")
    max_results: Optional[int] = Field(default=50, description="Maximum number of pages to return")


@ToolRegistry.register("confluence", "atlassian")
class ConfluenceTools:
    """Confluence knowledge base access and content retrieval tools."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with optional configuration."""
        self.config = config or {}
        self._confluence_service = None
        
    @property
    def confluence_service(self):
        """Lazy load confluence service to avoid circular imports."""
        if self._confluence_service is None:
            try:
                from app.services.external.confluence_service import ConfluenceService
                self._confluence_service = ConfluenceService()
            except ImportError as e:
                print(f"Warning: Could not import confluence service: {e}")
                self._confluence_service = None
        return self._confluence_service
        
    def get_tools(self) -> List[StructuredTool]:
        """Return list of Confluence tools."""
        return [
            StructuredTool(
                name="list_confluence_spaces",
                description="Get a list of accessible Confluence spaces with their keys, names, and details. Use ['*'] to get all spaces.",
                func=self._list_spaces,
                args_schema=ListSpacesInput
            ),
            StructuredTool(
                name="get_confluence_page",
                description="Get the full content and metadata of a specific Confluence page by its ID.",
                func=self._get_page,
                args_schema=GetPageInput
            ),
            StructuredTool(
                name="list_pages_in_space",
                description="List all pages in a specific Confluence space with their titles, IDs, and metadata.",
                func=self._list_pages_in_space,
                args_schema=ListPagesInSpaceInput
            ),
            StructuredTool(
                name="search_confluence_pages",
                description="Search for Confluence pages by text query across titles and content. Optionally filter by space.",
                func=self._search_pages,
                args_schema=SearchPagesInput
            ),
            StructuredTool(
                name="get_confluence_space",
                description="Get detailed information about a specific Confluence space including description and homepage.",
                func=self._get_space,
                args_schema=GetSpaceInput
            )
        ]
    
    def _list_spaces(self, space_keys: Optional[List[str]] = None) -> str:
        """List all accessible Confluence spaces."""
        try:
            # Check if service is available before using it
            service = self.confluence_service
            if not service:
                return json.dumps({
                    "status": "error",
                    "message": "Confluence service not available"
                })
            # Check if service is available before using it
            service = self.confluence_service
            if not service:
                return json.dumps({
                    "status": "error",
                    "message": "Confluence service not available"
                })
            
            # Default to all spaces if none specified
            keys_to_fetch = space_keys or ["*"]
            
            space_keys_list = service.list_confluence_spaces(keys_to_fetch)
            
            if not space_keys_list:
                return json.dumps({
                    "status": "success",
                    "message": "No accessible Confluence spaces found.",
                    "total_spaces": 0,
                    "spaces": []
                })
            
            result = {
                "status": "success",
                "total_spaces": len(space_keys_list),
                "space_keys": space_keys_list
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error listing Confluence spaces: {str(e)}"
            })

    def _get_page(self, page_id: str) -> str:
        """Get a specific Confluence page by its ID."""
        try:
            # Check if service is available before using it
            service = self.confluence_service
            if not service:
                return json.dumps({
                    "status": "error",
                    "message": "Confluence service not available"
                })
                
            if not page_id or not page_id.strip():
                return json.dumps({
                    "status": "error",
                    "message": "Page ID is required"
                })
                
            content, metadata = service.retrieve_confluence_page(page_id.strip())
            
            if not content:
                return json.dumps({
                    "status": "error",
                    "message": f"Could not retrieve page {page_id}"
                })
            
            result = {
                "status": "success",
                "page_id": page_id,
                "content": content,
                "metadata": metadata
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error getting Confluence page: {str(e)}"
            })

    def _list_pages_in_space(self, space_key: str, max_results: int = 50) -> str:
        """List all pages in a specific Confluence space."""
        try:
            # Check if service is available before using it
            service = self.confluence_service
            if not service:
                return json.dumps({
                    "status": "error",
                    "message": "Confluence service not available"
                })
            
            if not space_key or not space_key.strip():
                return json.dumps({
                    "status": "error",
                    "message": "Space key is required"
                })
                
            pages = service.list_confluence_pages_in_space(space_key.strip())
            
            if not pages:
                return json.dumps({
                    "status": "success",
                    "message": f"No pages found in space {space_key}",
                    "space_key": space_key,
                    "total_pages": 0,
                    "pages": []
                })
            
            # Limit results
            limited_pages = pages[:max_results]
            
            # Extract key information
            page_summaries = []
            for page in limited_pages:
                page_summary = {
                    "id": page.get("id", ""),
                    "title": page.get("title", ""),
                    "type": page.get("type", ""),
                    "status": page.get("status", ""),
                    "url": page.get("_links", {}).get("webui", ""),
                    "version": page.get("version", {}).get("number", 1),
                    "last_modified": page.get("version", {}).get("when", "")
                }
                page_summaries.append(page_summary)
            
            result = {
                "status": "success",
                "space_key": space_key,
                "total_pages": len(pages),
                "returned_pages": len(limited_pages),
                "pages": page_summaries
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error listing pages in space: {str(e)}"
            })

    def _search_pages(self, query: str, space_key: Optional[str] = None, max_results: int = 10) -> str:
        """Search for Confluence pages by text query."""
        try:
            # Check if service is available before using it
            service = self.confluence_service
            if not service:
                return json.dumps({
                    "status": "error",
                    "message": "Confluence service not available"
                })
            
            if not query or not query.strip():
                return json.dumps({
                    "status": "error",
                    "message": "Search query is required"
                })
            
            # Build CQL query
            cql_query = f'text ~ "{query.strip()}"'
            if space_key:
                cql_query += f' AND space = "{space_key.strip()}"'
            
            # Use the underlying Confluence API client
            confluence_client = service._confluence
            search_results = confluence_client.cql(cql_query, limit=max_results)
            
            if not search_results or not search_results.get("results"):
                return json.dumps({
                    "status": "success",
                    "message": "No pages found matching the query",
                    "query": query,
                    "space_key": space_key,
                    "total_results": 0,
                    "results": []
                })
            
            # Extract key information from search results
            page_results = []
            for result in search_results.get("results", []):
                content = result.get("content", {})
                page_result = {
                    "id": content.get("id", ""),
                    "title": content.get("title", ""),
                    "type": content.get("type", ""),
                    "space": content.get("space", {}).get("key", ""),
                    "url": content.get("_links", {}).get("webui", ""),
                    "excerpt": result.get("excerpt", "")
                }
                page_results.append(page_result)
            
            result = {
                "status": "success",
                "query": query,
                "space_key": space_key,
                "total_results": search_results.get("totalSize", 0),
                "returned_results": len(page_results),
                "results": page_results
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error searching Confluence pages: {str(e)}"
            })

    def _get_space(self, space_key: str) -> str:
        """Get detailed information about a specific Confluence space."""
        try:
            # Check if service is available before using it
            service = self.confluence_service
            if not service:
                return json.dumps({
                    "status": "error",
                    "message": "Confluence service not available"
                })
                
            if not space_key or not space_key.strip():
                return json.dumps({
                    "status": "error",
                    "message": "Space key is required"
                })
            
            # Use the underlying Confluence API client
            confluence_client = service._confluence
            space_data = confluence_client.get_space(space_key.strip(), expand='description.plain,homepage')
            
            if not space_data:
                return json.dumps({
                    "status": "error",
                    "message": f"Could not find space {space_key}"
                })
            
            space_info = {
                "key": space_data.get("key", ""),
                "name": space_data.get("name", ""),
                "id": space_data.get("id", ""),
                "type": space_data.get("type", ""),
                "description": space_data.get("description", {}).get("plain", {}).get("value", ""),
                "homepage": {
                    "id": space_data.get("homepage", {}).get("id", ""),
                    "title": space_data.get("homepage", {}).get("title", "")
                },
                "url": space_data.get("_links", {}).get("webui", "")
            }
            
            result = {
                "status": "success",
                "space": space_info
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error getting Confluence space: {str(e)}"
            })
