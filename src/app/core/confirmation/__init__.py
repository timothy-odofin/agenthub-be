"""
Universal action confirmation system.

Provides a generic, extensible framework for requiring user confirmation
before executing mutating operations across any integration (Jira, Email,
GitHub, etc.).

This module follows open-source standards and enterprise best practices:
- DRY: Reusable components across all integrations
- KISS: Simple, clear interfaces
- YAGNI: Only implements what's needed now
"""

from .pending_actions_store import PendingActionsStore
from .action_preview_formatter import ActionPreviewFormatter, get_default_formatter
from .confirmation_service import ConfirmationService

__all__ = [
    "PendingActionsStore",
    "ActionPreviewFormatter",
    "ConfirmationService",
    "get_default_formatter",
]
