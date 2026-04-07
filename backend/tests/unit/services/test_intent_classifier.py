"""
Tests for the intent classifier — ensures messages are correctly categorized
into tool categories for performance filtering.
"""

import pytest

from app.services.intent_classifier import (
    _GENERAL_CATEGORIES,
    CATEGORY_TO_REGISTRY,
    ToolCategory,
    classify_intent,
)


class TestIntentClassifier:
    """Tests for classify_intent function."""

    # ── Navigation intents ────────────────────────────────────────────

    def test_navigate_to_dashboard(self):
        result = classify_intent("take me to the dashboard")
        assert ToolCategory.NAVIGATION in result

    def test_go_to_login(self):
        result = classify_intent("go to login page")
        assert ToolCategory.NAVIGATION in result

    def test_logout(self):
        result = classify_intent("log me out")
        assert ToolCategory.NAVIGATION in result

    def test_sign_out(self):
        result = classify_intent("sign out please")
        assert ToolCategory.NAVIGATION in result

    def test_open_page(self):
        result = classify_intent("open the signup page")
        assert ToolCategory.NAVIGATION in result

    def test_navigation_only_has_few_categories(self):
        """Navigation-only queries should NOT include github, jira, etc."""
        result = classify_intent("take me to the dashboard")
        assert ToolCategory.GITHUB not in result
        assert ToolCategory.JIRA not in result
        assert ToolCategory.DATADOG not in result

    # ── GitHub intents ────────────────────────────────────────────────

    def test_github_repo(self):
        result = classify_intent("show me the repositories on github")
        assert ToolCategory.GITHUB in result

    def test_github_pr(self):
        result = classify_intent("list open pull requests")
        assert ToolCategory.GITHUB in result

    def test_github_branch(self):
        result = classify_intent("create a new branch called feature-x")
        assert ToolCategory.GITHUB in result

    def test_github_code_search(self):
        result = classify_intent("search code for authentication")
        # 'code search' triggers github
        assert ToolCategory.GITHUB in result

    def test_known_repo_name(self):
        result = classify_intent("show issues in accountmgt")
        assert ToolCategory.GITHUB in result

    # ── Jira intents ──────────────────────────────────────────────────

    def test_jira_search(self):
        result = classify_intent("search for open bugs in Jira")
        assert ToolCategory.JIRA in result

    def test_create_ticket(self):
        result = classify_intent("create a new task for implementing login")
        assert ToolCategory.JIRA in result

    def test_sprint_backlog(self):
        result = classify_intent("what's in the current sprint backlog?")
        assert ToolCategory.JIRA in result

    def test_jira_issue(self):
        result = classify_intent("find issues assigned to me in the project")
        assert ToolCategory.JIRA in result

    # ── Confluence intents ────────────────────────────────────────────

    def test_confluence_wiki(self):
        result = classify_intent("search the wiki for deployment procedures")
        assert ToolCategory.CONFLUENCE in result

    def test_confluence_docs(self):
        result = classify_intent("find documentation about API authentication")
        assert ToolCategory.CONFLUENCE in result

    def test_confluence_space(self):
        result = classify_intent("search the confluence knowledge base")
        assert ToolCategory.CONFLUENCE in result

    # ── Datadog intents ───────────────────────────────────────────────

    def test_datadog_logs(self):
        result = classify_intent("search datadog logs for errors")
        assert ToolCategory.DATADOG in result

    def test_cpu_metrics(self):
        result = classify_intent("what's the CPU usage for the API service?")
        assert ToolCategory.DATADOG in result

    def test_monitoring_alerts(self):
        result = classify_intent("show me active monitoring alerts")
        assert ToolCategory.DATADOG in result

    def test_response_time(self):
        result = classify_intent("what's the response time for the payment endpoint?")
        assert ToolCategory.DATADOG in result

    # ── Vector / Knowledge base ───────────────────────────────────────

    def test_vector_knowledge_base(self):
        result = classify_intent("search the knowledge base for user auth")
        assert ToolCategory.VECTOR in result

    def test_semantic_search(self):
        result = classify_intent("do a semantic search for payment processing")
        assert ToolCategory.VECTOR in result

    # ── Web intents ───────────────────────────────────────────────────

    def test_web_python_docs(self):
        result = classify_intent("check the python docs for asyncio")
        assert ToolCategory.WEB in result

    def test_web_url(self):
        result = classify_intent("read this url https://example.com")
        assert ToolCategory.WEB in result

    # ── General / fallback ────────────────────────────────────────────

    def test_general_greeting(self):
        """Greetings should return the general set (excludes github)."""
        result = classify_intent("hello, how are you?")
        assert result == _GENERAL_CATEGORIES
        assert ToolCategory.GITHUB not in result

    def test_general_question(self):
        """General knowledge questions should return the general set."""
        result = classify_intent("explain how neural networks work")
        assert result == _GENERAL_CATEGORIES
        assert ToolCategory.GITHUB not in result

    def test_ambiguous_returns_general(self):
        """If no patterns match, the general set should be returned (no github)."""
        result = classify_intent("xyz abc 123")
        assert result == _GENERAL_CATEGORIES
        assert ToolCategory.GITHUB not in result

    def test_general_includes_core_tools(self):
        """General set should include navigation, jira, confluence, etc."""
        result = classify_intent("hello")
        assert ToolCategory.NAVIGATION in result
        assert ToolCategory.JIRA in result
        assert ToolCategory.CONFLUENCE in result
        assert ToolCategory.DATADOG in result
        assert ToolCategory.VECTOR in result
        assert ToolCategory.WEB in result

    # ── Navigation always included ────────────────────────────────────

    def test_navigation_always_included_with_jira(self):
        """Navigation should always be included alongside specific intents."""
        result = classify_intent("search for bugs in jira")
        assert ToolCategory.NAVIGATION in result
        assert ToolCategory.JIRA in result

    def test_navigation_always_included_with_github(self):
        result = classify_intent("show me the pull requests")
        assert ToolCategory.NAVIGATION in result
        assert ToolCategory.GITHUB in result

    # ── Multi-intent messages ─────────────────────────────────────────

    def test_multi_intent_jira_and_github(self):
        result = classify_intent("find jira tickets related to the github PR")
        assert ToolCategory.JIRA in result
        assert ToolCategory.GITHUB in result

    # ── Category to registry mapping ──────────────────────────────────

    def test_all_categories_have_registry_mapping(self):
        """Every ToolCategory must have a corresponding registry category name."""
        for cat in ToolCategory:
            assert (
                cat in CATEGORY_TO_REGISTRY
            ), f"ToolCategory.{cat.value} has no entry in CATEGORY_TO_REGISTRY"

    def test_registry_names_match_tool_registry(self):
        """Registry names must match @ToolRegistry.register() categories."""
        expected = {
            "navigation",
            "github",
            "jira",
            "confluence",
            "datadog",
            "vector",
            "web",
        }
        actual = set(CATEGORY_TO_REGISTRY.values())
        assert actual == expected
