"""
LLM validation decorator for FastAPI endpoints.

Validates LLM provider and model parameters in request body before processing.
Automatically falls back to defaults when not provided.
"""

from functools import wraps
from typing import Callable, Any, Optional
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.services.llm_service import LLMService
from app.core.utils.logger import get_logger
from app.core.config import settings

logger = get_logger(__name__)


def validate_llm_params(func: Callable) -> Callable:
    """
    Decorator to validate LLM provider and model parameters.
    
    Validates and normalizes provider/model parameters from the request body:
    - If provider not provided: uses system default (settings.llm.default.provider)
    - If model not provided: uses provider's default model
    - If provider provided: validates it's configured and available
    - If model provided: validates it's supported by the provider
    
    The decorator modifies the request body to ensure it contains validated
    provider and model values before passing to the endpoint handler.
    
    Usage:
        @router.post("/chat")
        @validate_llm_params
        async def chat(request: ChatRequest):
            # request.provider and request.model are guaranteed to be valid
            ...
    
    Raises:
        HTTPException 400: If provider/model validation fails
        HTTPException 500: If default provider/model not configured
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request body from kwargs (FastAPI passes it as keyword arg)
        request_body = None
        for key, value in kwargs.items():
            if isinstance(value, BaseModel):
                request_body = value
                break
        
        if not request_body:
            # No Pydantic model in args, proceed without validation
            return await func(*args, **kwargs)
        
        try:
            # Get provider from request or use system default
            provider = getattr(request_body, 'provider', None)
            if not provider:
                provider = settings.llm.default.provider
                logger.debug(f"No provider specified, using default: {provider}")
            
            # Get model from request (can be None - will use provider's default)
            model = getattr(request_body, 'model', None)
            
            # Validate provider and model using LLMService
            validated_model = LLMService.validate_model_for_provider(provider, model)
            
            # Update request body with validated values
            if hasattr(request_body, 'provider'):
                request_body.provider = provider
            if hasattr(request_body, 'model'):
                request_body.model = validated_model
            
            logger.info(f"Validated LLM params - provider: {provider}, model: {validated_model}")
            
            # Call the original endpoint handler
            return await func(*args, **kwargs)
            
        except ValueError as e:
            # Provider not found, not configured, or model not supported
            logger.warning(f"LLM validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            # Unexpected error during validation
            logger.error(f"Unexpected error in LLM validation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate LLM parameters"
            )
    
    return wrapper


def validate_llm_params_sync(func: Callable) -> Callable:
    """
    Synchronous version of validate_llm_params decorator.
    
    Use this for synchronous endpoint handlers (non-async functions).
    
    Usage:
        @router.post("/sync-endpoint")
        @validate_llm_params_sync
        def sync_handler(request: ChatRequest):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract request body from kwargs
        request_body = None
        for key, value in kwargs.items():
            if isinstance(value, BaseModel):
                request_body = value
                break
        
        if not request_body:
            return func(*args, **kwargs)
        
        try:
            # Get provider from request or use system default
            provider = getattr(request_body, 'provider', None)
            if not provider:
                provider = settings.llm.default.provider
                logger.debug(f"No provider specified, using default: {provider}")
            
            # Get model from request (can be None - will use provider's default)
            model = getattr(request_body, 'model', None)
            
            # Validate provider and model
            validated_model = LLMService.validate_model_for_provider(provider, model)
            
            # Update request body with validated values
            if hasattr(request_body, 'provider'):
                request_body.provider = provider
            if hasattr(request_body, 'model'):
                request_body.model = validated_model
            
            logger.info(f"Validated LLM params - provider: {provider}, model: {validated_model}")
            
            return func(*args, **kwargs)
            
        except ValueError as e:
            logger.warning(f"LLM validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error in LLM validation: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to validate LLM parameters"
            )
    
    return wrapper
