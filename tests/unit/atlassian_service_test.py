import pytest

from app.core.utils.logger import get_logger
from src.app.services.external.atlassian_service import AtlassianService
logger =  get_logger(__name__)
@pytest.fixture
def atlassian_service() -> AtlassianService:
        return AtlassianService()

# @pytest.mark.asyncio
def test_list_confluence_spaces(atlassian_service: AtlassianService) -> None:
    space_details =  atlassian_service.list_confluence_spaces(['SD',"FI","GT"])
    assert space_details is not None
    assert isinstance(space_details, list)

