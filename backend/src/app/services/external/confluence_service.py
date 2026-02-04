import re
from typing import Any, Tuple

import requests
from atlassian import Confluence
from bs4 import BeautifulSoup

from app.core.utils.exception.http_exception_handler import handle_atlassian_errors
from app.core.utils.logger import get_logger
from app.core.utils.single_ton import SingletonMeta

logger = get_logger(__name__)
RESULT_KEY = "results"
SIZE_KEY = "size"

class ConfluenceService(metaclass=SingletonMeta):
    """Abstract base class for Atlassian services."""
    def __init__(self):
        self._confluence = None
        self.__init_client()

    def __extract_keys_from_data(self, data: list[Any], key: str) -> list[str]:
        return [item[key] for item in data]

    @handle_atlassian_errors(default_return=[])
    def list_confluence_spaces(self, space_keys: list[str]) -> list[Any]:
        """Fetch all spaces from atlassian Confluence."""
        space_details = []
        page_size =0
        limit = 100
        if "*" in space_keys:
            while True:
                spaces =  self._confluence.get_all_spaces(start=page_size, limit=limit, expand='description.plain,homepage')
                logger.info(f"Fetched spaces page starting at {page_size} from Confluence First Item, total Record {spaces['size']}")
                result = spaces.get(RESULT_KEY, [])
                if result:
                    space_details.extend(spaces.get(RESULT_KEY, []))
                    page_size += limit
                if spaces[SIZE_KEY] < limit:
                    break
        else:
            for space_key in space_keys:
                space_data =   self._confluence.get_space(space_key, expand='description.plain,homepage')
                if space_data:
                    logger.info(f"Fetched space  with key {space_key} from Confluence First Item")
                    space_details.append(space_data)
                else:
                    logger.warning(f"Could not find space {space_key} in Confluence First Item")
        return self.__extract_keys_from_data(space_details, 'key')

    @handle_atlassian_errors(default_return=[])
    def retrieve_confluence_page(self, page_id:str) -> Tuple[str,dict]:
        page  =self._confluence.get_page_by_id(page_id, expand='body.storage,version,ancestors,space')
        return self.extract_content_from_a_page(page)

    #@handle_atlassian_errors(default_return=[])
    def list_confluence_pages_in_space(self, space_key: str) -> list[Any]:
        page_size = 0
        limit = 100
        page_details = []
        while True:
                result = self._confluence.get_all_pages_from_space_raw(space_key, start=page_size, limit=limit,  expand='body.storage,version,ancestors')
                if result:
                    pages = result.get(RESULT_KEY, []) if isinstance(result, dict) else result
                    page_details.extend(pages)
                page_size += limit
                if result[SIZE_KEY] < limit:
                    break
        return page_details

    def __get_page_meta(self, page:dict)-> dict:
       page_id = page['id']
       title = page['title']
       # Build metadata
       metadata = {
           'source': 'confluence',
           'page_id': page_id,
           'title': title,
           'url': page.get('_links', {}).get('webui', ''),
           'space': page.get('space', {}).get('key', ''),
           'space_name': page.get('space', {}).get('name', ''),
           'last_modified': page.get('version', {}).get('when', ''),
           'version': page.get('version', {}).get('number', 1),
           'type': 'confluence_page'
       }

       # Add ancestor information (breadcrumb)
       if 'ancestors' in page:
           ancestors = [ancestor['title'] for ancestor in page['ancestors']]
           metadata['breadcrumb'] = ' > '.join(ancestors + [title])
       return metadata

    @handle_atlassian_errors(default_return=['',{}])
    def extract_content_from_a_page(self, page: dict)-> Tuple[str,dict]:
        """Extract and clean content from Confluence page."""
        body = page.get('body', {})
        storage = body.get('storage', {})
        content = storage.get('value', '')

        if not content:
            return page.get('title', ''), {}

        # Use BeautifulSoup for better HTML cleaning
        soup = BeautifulSoup(content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text).strip()
        title = page.get('title', '')
        full_content = f"{title}\n\n{text}" if title else text

        return full_content, self.__get_page_meta(page)


    def __init_client(self):
        """
        Initialize Confluence client with configuration.
        
        Note: Uses lazy import to avoid circular dependency:
        app.services.external → app.core.config → app.services
        Config is only loaded when client is first initialized.
        """
        if self._confluence is None:
            from app.core.config.framework.settings import settings
            from app.core.utils.config_converter import dynamic_config_to_dict
            
            atlassian_config = dynamic_config_to_dict(settings.external.atlassian)
            logger.info(f"Initializing Confluence client... with config: {atlassian_config.keys()}")
            self._confluence = Confluence(
                url=atlassian_config['confluence_base_url'],
                username=atlassian_config['email'],
                password=atlassian_config['api_key'],
                cloud=True , # Set to True for Confluence Cloud
                session=requests.Session()
            )
        return self._confluence