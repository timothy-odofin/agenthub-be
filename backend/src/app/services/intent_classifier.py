"""
Lightweight intent classifier for tool filtering.

Classifies user messages into tool categories BEFORE the full agent call,
allowing us to only load the tools the LLM actually needs.

This dramatically reduces the number of tools sent to the LLM
(from 86 → 1-22), which cuts inference time from ~15s to ~2-4s.

The classification is done via simple keyword/pattern matching —
no LLM call is needed, keeping it under 1ms.
"""

import re
from enum import Enum
from typing import List, Set

from app.core.utils.logger import get_logger

logger = get_logger(__name__)


class ToolCategory(str, Enum):
    """Categories of tools available in the system."""

    NAVIGATION = "navigation"
    GITHUB = "github"
    JIRA = "jira"
    CONFLUENCE = "confluence"
    DATADOG = "datadog"
    VECTOR = "vector"
    WEB = "web"


# ─────────────────────────────────────────────────────────────────────
# Keyword patterns for each category
# ─────────────────────────────────────────────────────────────────────
# Each pattern list is matched case-insensitively against the user message.
# If ANY pattern matches, that category is included.
# The patterns are intentionally broad — false positives are cheap (just
# includes a few extra tools), but false negatives mean missing tools.
# ─────────────────────────────────────────────────────────────────────

_CATEGORY_PATTERNS: dict[ToolCategory, List[re.Pattern]] = {
    ToolCategory.NAVIGATION: [
        re.compile(r"\b(navigate|go\s+to|take\s+me|open|redirect|switch\s+to)\b", re.I),
        re.compile(
            r"\b(dashboard|login|sign\s*up|sign\s*out|log\s*out|log\s*me\s*out|home\s*page)\b",
            re.I,
        ),
        re.compile(r"\b(page|screen|route|view)\b", re.I),
    ],
    ToolCategory.GITHUB: [
        re.compile(r"\b(github|git|repo|repository|repositories)\b", re.I),
        re.compile(r"\b(pull\s*requests?|PRs?|merge|branch|commit)\b", re.I),
        re.compile(
            r"\b(code\s*search|search\s*code|source\s*code|file\s*in\s*repo)\b", re.I
        ),
        re.compile(r"\b(issue|bug)\b.*\b(repo|github|create|open|close)\b", re.I),
        re.compile(r"\b(accountmgt|oze|car-mgt)\b", re.I),  # Known repo names
        # Codebase exploration / architecture queries — route to GitHub MCP tools,
        # NOT the generic web URL reader which crawls HTML one page at a time.
        re.compile(
            r"\b(codebase|code\s*base|application\s*code|source\s*files?)\b", re.I
        ),
        re.compile(
            r"\b(design\s*patterns?|architecture|architectural|software\s*design)\b",
            re.I,
        ),
        re.compile(
            r"\b(how\s+is\s+.*(structured|organized|built|implemented|designed))\b",
            re.I,
        ),
        re.compile(
            r"\b(folder\s*structure|directory\s*structure|project\s*structure|file\s*structure)\b",
            re.I,
        ),
        re.compile(
            r"\b(class\s*diagram|module|package|layer|dependency\s*injection|factory|singleton|observer|strategy|decorator)\b",
            re.I,
        ),
        re.compile(
            r"\b(what\s+.*(pattern|patterns|approach|approaches|technique|techniques)\s+.*(use|used|applied|implemented))\b",
            re.I,
        ),
        re.compile(
            r"\b(implementation|implemented|how\s+does|how\s+do)\b.*\b(work|work\?|implemented)\b",
            re.I,
        ),
    ],
    ToolCategory.JIRA: [
        re.compile(r"\b(jira|jql|sprint|epic|story|backlog)\b", re.I),
        re.compile(
            r"\b(ticket|issue|task|bug)\b.*\b(create|assign|update|search|find|list|status)\b",
            re.I,
        ),
        re.compile(
            r"\b(create|assign|update|search|find|list)\b.*\b(ticket|issue|task)\b",
            re.I,
        ),
        re.compile(r"\b(project\s*management|kanban|scrum)\b", re.I),
    ],
    ToolCategory.CONFLUENCE: [
        re.compile(r"\b(confluence|wiki|knowledge\s*base)\b", re.I),
        re.compile(
            r"\b(documentation|docs|page|space)\b.*\b(search|find|read|get)\b", re.I
        ),
        re.compile(
            r"\b(search|find|read|get)\b.*\b(documentation|docs|page|space)\b", re.I
        ),
    ],
    ToolCategory.DATADOG: [
        re.compile(r"\b(datadog|monitoring|observability)\b", re.I),
        re.compile(
            r"\b(metrics?|logs?|alerts?|monitors?)\b.*\b(search|query|check|show|list)\b",
            re.I,
        ),
        re.compile(
            r"\b(cpu|memory|latency|error\s*rate|response\s*time|uptime)\b", re.I
        ),
    ],
    ToolCategory.VECTOR: [
        re.compile(r"\b(knowledge\s*base|semantic\s*search|vector|embedding)\b", re.I),
        re.compile(r"\b(what\s+do\s+we\s+know|find\s+information)\b", re.I),
    ],
    ToolCategory.WEB: [
        re.compile(r"\b(web\s*page|website|url|http|browse)\b", re.I),
        re.compile(r"\b(python\s*docs|fastapi\s*docs|langchain\s*docs)\b", re.I),
        re.compile(r"\b(read|fetch|scrape)\b.*\b(web|url|site|page)\b", re.I),
    ],
}

# Categories to always include (lightweight, always useful)
_ALWAYS_INCLUDE: Set[ToolCategory] = {ToolCategory.NAVIGATION}

# "General" fallback set — used when no specific intent is matched.
# This EXCLUDES heavy categories like GitHub (MCP server connection overhead,
# and tool schemas that bloat every LLM request).
# GitHub tools are only loaded when the user explicitly mentions GitHub/repos/PRs.
_GENERAL_CATEGORIES: Set[ToolCategory] = {
    ToolCategory.NAVIGATION,
    ToolCategory.JIRA,
    ToolCategory.CONFLUENCE,
    ToolCategory.DATADOG,
    ToolCategory.VECTOR,
    ToolCategory.WEB,
}


def classify_intent(message: str) -> Set[ToolCategory]:
    """
    Classify a user message into relevant tool categories.

    Uses keyword/pattern matching (~0ms) instead of an LLM call.
    Returns the set of tool categories that should be loaded for this message.

    If no specific category matches, returns the "general" set — a curated
    subset that excludes heavy categories like GitHub (63 tools).
    GitHub is only loaded when explicitly mentioned.

    Args:
        message: The user's message text

    Returns:
        Set of ToolCategory values indicating which tools to load
    """
    matched_categories: Set[ToolCategory] = set()

    for category, patterns in _CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(message):
                matched_categories.add(category)
                break  # One match per category is enough

    # If nothing matched, use the "general" set (excludes heavy tools like GitHub)
    if not matched_categories:
        logger.info(
            f"No specific intent matched — using general set "
            f"({len(_GENERAL_CATEGORIES)} categories, excludes github) "
            f"for message: '{message[:60]}...'"
        )
        return _GENERAL_CATEGORIES.copy()

    # Always include lightweight categories
    matched_categories |= _ALWAYS_INCLUDE

    logger.info(
        f"Intent classified: {[c.value for c in matched_categories]} "
        f"for message: '{message[:60]}...'"
    )

    return matched_categories


# ─────────────────────────────────────────────────────────────────────
# Map ToolCategory → ToolRegistry category names
# ─────────────────────────────────────────────────────────────────────
# These must match the strings used in @ToolRegistry.register("category")

CATEGORY_TO_REGISTRY: dict[ToolCategory, str] = {
    ToolCategory.NAVIGATION: "navigation",
    ToolCategory.GITHUB: "github",
    ToolCategory.JIRA: "jira",
    ToolCategory.CONFLUENCE: "confluence",
    ToolCategory.DATADOG: "datadog",
    ToolCategory.VECTOR: "vector",
    ToolCategory.WEB: "web",
}
