from langchain.tools import  tool

from app.core.constants import VectorDBType
from app.core.utils.single_ton import SingletonMeta
from app.db.vector import VectorStoreFactory
import json
from app.services.external.jira_service import  jira

from abc import ABC, abstractmethod
from typing import List
from langchain.tools import Tool


class BaseToolProvider(ABC):
    """Base class for all tool providers"""
    
    @abstractmethod
    def get_tools(self) -> List[Tool]:
        """Return list of tools provided by this class"""
        pass

class VectorStoreTools(BaseToolProvider):
    """Tools for vector store operations"""
    
    def __init__(self):
        self.vector_store = VectorStoreFactory.get_vector_store(VectorDBType.QDRANT)
    
    def get_tools(self) -> List[Tool]:
        return [
            Tool(
                name="retrieve_information",
                description="Retrieve information from vector store",
                func=self._retrieve_information
            )
        ]
    

    def _retrieve_information(query: str) :
        """
        Retrieve information from the vector store based on the provided query.
        This information includes relevant confluence docs, knowledge base articles, and other related data.

        Args:
            query (str): The query string to search in the vector store.

        Returns:
            str: The retrieved information as a string.
        """
        vector_store_class = VectorStoreFactory.get_vector_store(VectorDBType.QDRANT)
        vector_db = vector_store_class.as_retriever(earch_kwargs={"k": 4})
        docs = vector_db.get_relevant_documents(query)
        formatted = []
        for d in docs:
            formatted.append(
                f"CONTENT:\n{d.page_content}\n\nMETADATA:\n{json.dumps(d.metadata)}"
            )

        return "\n\n---\n\n".join(formatted)

class JiraTools(BaseToolProvider):
    """Tools for Jira operations"""
    
    def __init__(self):
        self.jira_service = jira
    
    def get_tools(self) -> List[Tool]:
        return [
            Tool(name="jira_search", description="Search Jira issues", func=self._search_issues),
            Tool(name="jira_create", description="Create Jira issue", func=self._create_issue),
            Tool(name="jira_get", description="Get Jira issue", func=self._get_issue)
        ]
    

    def _search_issues(jql: str):
        """Search Jira issues using JQL."""
        return jira.search_issues(jql)


    def _create_issue(data: dict):
        """
        Create a Jira issue.
        Expected keys: project, summary, description, issue_type.
        """
        return jira.create_issue(
            project=data["project"],
            summary=data["summary"],
            description=data["description"],
            issue_type=data.get("issue_type", "Task")
        )

    def _get_issue(issue_key: str):
        """Get a Jira issue by key."""
        return jira.get_issue(issue_key)

class ToolRegistry(metaclass=SingletonMeta):
    """Central registry for all tools"""
    
    def __init__(self):
        self._providers = [
            VectorStoreTools(),
            JiraTools(),
            # Add more tool providers here
        ]
    
    def get_all_tools(self) -> List[Tool]:
        """Get all available tools from all providers"""
        tools = []
        for provider in self._providers:
            tools.extend(provider.get_tools())
        return tools

tool_registry = ToolRegistry()