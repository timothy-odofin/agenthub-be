"""
Schemas for LLM provider management endpoints.
"""

from pydantic import BaseModel
from typing import List


class ProviderInfo(BaseModel):
    """LLM provider information for frontend."""
    name: str
    display_name: str
    model_versions: List[str]
    default_model: str
    is_default: bool


class ProviderDetailInfo(ProviderInfo):
    """Extended provider information with additional details."""
    base_url: str
    timeout: int
    max_tokens: int


class ProvidersResponse(BaseModel):
    """Response containing list of available providers."""
    success: bool
    providers: List[ProviderInfo]
    total: int
