from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator
from ..constants import DataSourceType

class DataSourceConfig(BaseModel):
    """Configuration for a single data sources."""
    name: str = Field(..., min_length=1, description="Alias for the data sources")
    type: DataSourceType = Field(..., description="Type of data sources")
    sources: List[str] = Field(..., min_items=1, description="List of sources identifiers (paths, URLs, IDs)")
    location: Optional[HttpUrl] = Field(None, description="Base location for the sources (e.g. Confluence URL)")

    @field_validator('sources')
    @classmethod
    def validate_sources(cls, v: List[str]) -> List[str]:
        """Validate that sources strings are not empty"""
        if any(not source.strip() for source in v):
            raise ValueError("Source identifiers cannot be empty strings")
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is not just whitespace"""
        if not v.strip():
            raise ValueError("Name cannot be just whitespace")
        return v.strip()
    
class IngestionConfig(BaseModel):
    """Root configuration for data ingestion."""
    data_sources: List[DataSourceConfig] = Field(..., 
                                               alias="dataSources",
                                               description="List of data sources to ingest")
