from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator, AnyUrl
from ..constants import DataSourceType

class DataSourceConfig(BaseModel):
    """Configuration for a single data sources."""
    type: DataSourceType = Field(..., description="Type of data sources")
    sources: List[str] = Field(..., min_items=1, description="List of sources identifiers (paths, URLs, IDs)")
    location: Optional[AnyUrl] = Field(None, description="Base location for the sources (e.g. Confluence URL)")

    @field_validator('sources')
    @classmethod
    def validate_sources(cls, v: List[str]) -> List[str]:
        """Validate that sources strings are not empty"""
        if any(not source.strip() for source in v):
            raise ValueError("Source identifiers cannot be empty strings")
        return v

    @field_validator('type')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate that name is not just whitespace"""
        if not v.strip():
            raise ValueError("Type cannot be just whitespace")
        return v.strip()
    
class IngestionConfig(BaseModel):
    """Root configuration for data ingestion."""
    data_sources: Dict[str, DataSourceConfig] = Field(...,
                                               alias="dataSources",
                                               description="Dictionary of data sources indexed by type")

    @field_validator('data_sources', mode='before')
    @classmethod
    def normalize_data_sources(cls, v: Any) -> Dict[str, DataSourceConfig]:
        """
        Normalize data_sources from list format (YAML) to dict indexed by type.

        If YAML provides: [{"type": "file", ...}, {"type": "confluence", ...}]
        Convert to: {"file": DataSourceConfig(...), "confluence": DataSourceConfig(...)}
        """
        if isinstance(v, list):
            result = {}
            for item in v:
                if isinstance(item, dict):
                    source_type = item.get('type')
                    if not source_type:
                        raise ValueError("Each data source must have a 'type' field")
                    # Use lowercase type as key
                    key = source_type.lower() if isinstance(source_type, str) else str(source_type).lower()
                    # If duplicate types exist, keep the last one (or raise error)
                    if key in result:
                        raise ValueError(f"Duplicate data source type found: {source_type}")
                    result[key] = item
                else:
                    raise ValueError(f"Expected dict for data source, got {type(item)}")
            return result
        elif isinstance(v, dict):
            # Already in dict format, pass through
            return v
        else:
            raise ValueError(f"data_sources must be a list or dict, got {type(v)}")
