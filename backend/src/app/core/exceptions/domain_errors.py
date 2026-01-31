"""
Domain-Specific Error Exceptions

These exceptions represent business logic errors specific to AgentHub domains
(agents, sessions, workflows, LLM operations, etc.).
"""

from typing import Any, Dict, Optional
from .base import ServerError, ClientError


class AgentError(ServerError):
    """
    Raised when agent operations fail (agent creation, execution, state management, etc.).
    HTTP Status: 500 Internal Server Error
    """
    
    status_code: int = 500
    error_code: str = "AGENT_ERROR"
    error_type: str = "agent_error"
    
    def __init__(
        self,
        message: str = "Agent operation failed",
        agent_id: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if agent_id:
            internal_details["agent_id"] = agent_id
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(message, **kwargs)


class SessionError(ServerError):
    """
    Raised when session operations fail (creation, retrieval, update, etc.).
    HTTP Status: 500 Internal Server Error
    """
    
    status_code: int = 500
    error_code: str = "SESSION_ERROR"
    error_type: str = "session_error"
    
    def __init__(
        self,
        message: str = "Session operation failed",
        session_id: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if session_id:
            internal_details["session_id"] = session_id
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(message, **kwargs)


class WorkflowError(ServerError):
    """
    Raised when workflow operations fail (validation, execution, state transitions, etc.).
    HTTP Status: 500 Internal Server Error
    """
    
    status_code: int = 500
    error_code: str = "WORKFLOW_ERROR"
    error_type: str = "workflow_error"
    
    def __init__(
        self,
        message: str = "Workflow operation failed",
        workflow_name: Optional[str] = None,
        step: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if workflow_name:
            internal_details["workflow_name"] = workflow_name
        if step:
            internal_details["step"] = step
        
        kwargs["internal_details"] = internal_details
        super().__init__(message, **kwargs)


class LLMError(ServerError):
    """
    Raised when LLM operations fail (API errors, context overflow, generation failures, etc.).
    HTTP Status: 500 Internal Server Error or 503 if it's a temporary LLM provider issue
    """
    
    status_code: int = 500
    error_code: str = "LLM_ERROR"
    error_type: str = "llm_error"
    
    def __init__(
        self,
        message: str = "LLM operation failed",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if provider:
            internal_details["provider"] = provider
        if model:
            internal_details["model"] = model
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(message, **kwargs)


class FileOperationError(ServerError):
    """
    Raised when file operations fail (read, write, parse, etc.).
    HTTP Status: 500 Internal Server Error
    
    Note: This replaces the existing FileReadError from file_utils.py
    """
    
    status_code: int = 500
    error_code: str = "FILE_OPERATION_ERROR"
    error_type: str = "file_operation_error"
    
    def __init__(
        self,
        message: str = "File operation failed",
        file_path: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        # Never expose full file paths to client
        if file_path:
            internal_details["file_path"] = file_path
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(message, **kwargs)


class PromptError(ServerError):
    """
    Raised when prompt operations fail (loading, formatting, validation, etc.).
    HTTP Status: 500 Internal Server Error
    
    Note: This replaces the existing PromptConfigError from prompt.py
    """
    
    status_code: int = 500
    error_code: str = "PROMPT_ERROR"
    error_type: str = "prompt_error"
    
    def __init__(
        self,
        message: str = "Prompt operation failed",
        prompt_name: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if prompt_name:
            internal_details["prompt_name"] = prompt_name
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(message, **kwargs)


class EmbeddingError(ServerError):
    """
    Raised when embedding operations fail (generation, storage, retrieval, etc.).
    HTTP Status: 500 Internal Server Error
    """
    
    status_code: int = 500
    error_code: str = "EMBEDDING_ERROR"
    error_type: str = "embedding_error"
    
    def __init__(
        self,
        message: str = "Embedding operation failed",
        model: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        internal_details = kwargs.get("internal_details", {})
        if model:
            internal_details["model"] = model
        if operation:
            internal_details["operation"] = operation
        
        kwargs["internal_details"] = internal_details
        super().__init__(message, **kwargs)
