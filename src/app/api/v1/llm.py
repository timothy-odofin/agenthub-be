"""
LLM Provider API endpoints.

Provides endpoints to:
- List available LLM providers
- Get detailed information about specific providers
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.llm import ProvidersResponse, ProviderDetailInfo
from app.services.llm_service import llm_service
from app.core.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/providers", response_model=ProvidersResponse)
async def list_providers():
    """
    Get list of available LLM providers.
    
    Returns only providers that are properly configured (have API keys, etc.).
    Each provider includes:
    - name: Provider identifier (e.g., "openai", "anthropic")
    - display_name: Human-readable name for UI
    - model_versions: Available models for this provider
    - default_model: The default model for this provider
    - is_default: Whether this is the system's default provider
    
    Frontend can use this to populate provider selection dropdown.
    
    **Example Response:**
    ```json
    {
      "success": true,
      "total": 3,
      "providers": [
        {
          "name": "openai",
          "display_name": "OpenAI",
          "model_versions": ["gpt-4", "gpt-5-mini", "gpt-3.5-turbo"],
          "default_model": "gpt-5-mini",
          "is_default": true
        },
        {
          "name": "anthropic",
          "display_name": "Anthropic (Claude)",
          "model_versions": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
          "default_model": "claude-3-sonnet-20240229",
          "is_default": false
        }
      ]
    }
    ```
    """
    try:
        providers = llm_service.get_available_providers()
        
        return ProvidersResponse(
            success=True,
            providers=providers,
            total=len(providers)
        )
    
    except Exception as e:
        logger.error(f"Error fetching providers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch providers: {str(e)}"
        )


@router.get("/providers/{provider_name}", response_model=ProviderDetailInfo)
async def get_provider(provider_name: str):
    """
    Get detailed information about a specific provider.
    
    Returns extended provider information including base_url, timeout, and max_tokens.
    
    **Path Parameters:**
    - provider_name: The provider identifier (e.g., "openai", "anthropic", "groq")
        
    **Returns:**
    Detailed provider configuration including:
    - All fields from list endpoint
    - base_url: API endpoint URL
    - timeout: Request timeout in seconds
    - max_tokens: Maximum token limit
    
    **Errors:**
    - 404: If provider not found or not configured (missing API key)
    - 500: Internal server error
    
    **Example Response:**
    ```json
    {
      "name": "openai",
      "display_name": "OpenAI",
      "model_versions": ["gpt-4", "gpt-5-mini"],
      "default_model": "gpt-5-mini",
      "is_default": true,
      "base_url": "https://api.openai.com/v1",
      "timeout": 60,
      "max_tokens": 4096
    }
    ```
    """
    try:
        provider_info = llm_service.get_provider_info(provider_name)
        return ProviderDetailInfo(**provider_info)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error fetching provider {provider_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch provider: {str(e)}"
        )
