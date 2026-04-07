# Prompt & Tool Description Optimization - Implementation TODO

**Created:** 2026-04-07
**Branch:** feature/voice-integration
**Goal:** Reduce system prompt from ~984 lines (~12,000 tokens) to ~110 lines (~1,139 tokens)
**Status:** ✅ ALL IMPLEMENTED AND TESTED

---

## P0 — Critical (Highest Impact, Lowest Risk)

### P0-A: Remove `{available_tools}` from System Prompt ✅
- **File:** `src/app/agent/implementations/langchain_react_agent.py`
- **What:** Removed `available_tools` formatting and `{available_tools}` placeholder. `bind_tools()` handles tool schemas natively.
- [x] Removed `available_tools` list comprehension from `_create_prompt_template()`
- [x] Removed `{available_tools}` placeholder from `application-prompt.yaml`
- [x] Removed `.format(available_tools=...)` call — now uses `str(system_prompt_obj)`

### P0-B: Remove "Tool Categories" Section from `prompt.yaml` ✅
- **File:** `resources/application-prompt.yaml`
- [x] Deleted "Tool Categories" section (GitHub, Vector, Confluence, Jira, Datadog — ~200 lines)
- [x] Deleted "Confluence vs Vector Store" decision tree (~50 lines)
- [x] Deleted Jira tool listing and JQL examples

### P0-C: Remove Structured List Response Templates ✅
- [x] Deleted Jira/GitHub/Confluence/Datadog format templates (~100 lines)
- [x] Deleted "Key Formatting Rules for Lists" section
- [x] Deleted "Query Interpretation Examples" section
- [x] Deleted "Confluence Resources - ALWAYS Include Full Links" section
- [x] Deleted "Datadog Log Analysis - Structured Error Investigation" section

### P0-D: Remove Verbose Examples Section ✅
- [x] Deleted all 9 example sections (Example 1–9, ~100 lines)

---

## P1 — High Priority (Move Guidance to Tool Descriptions)

### P1-A: Move Jira Mentions/Comments Logic into Tool Description ✅
- **File:** `src/app/agent/tools/atlassian/jira.py`
- [x] Enhanced `add_jira_comment` description with mention workflow and privacy rules
- [x] Enhanced `search_jira_users` description to clarify role in mention workflow
- [x] Enhanced `create_jira_issue` description with confirmation note
- [x] Enhanced `search_jira_issues` description with JQL examples and status mappings

### P1-B: Move Confluence vs Vector Decision Logic into Tool Descriptions ✅
- **Files:** `confluence.py` + `vector_store.py`
- [x] Enhanced `search_confluence_pages` — "PREFERRED for real-time Confluence content"
- [x] Enhanced `retrieve_information` — "For real-time Confluence, prefer Confluence tools"
- [x] Enhanced `get_confluence_page` — "Returns the latest version of the page content"

### P1-C: Skip Provider Instantiation When Category Is Disabled ✅
- **File:** `src/app/agent/tools/base/registry.py`
- [x] Added `is_category_enabled()` helper function
- [x] Added category-level check before `tool_class(...)` instantiation
- [x] Added unit tests (7 new tests, all passing)

---

## P2 — Medium Priority (Shorten Remaining Sections)

### P2-A: Shorten Response Formatting Guidelines ✅
- [x] Condensed ~80 lines to ~10 lines in the optimized prompt

### P2-B: Shorten Terminology/Synonyms Section ✅
- [x] Condensed ~50 lines to ~10 lines (compact mapping format)

### P2-C: Enhance All Tool Descriptions ✅
- [x] `jira.py` — 4 tools enhanced with richer descriptions
- [x] `confluence.py` — 2 tools enhanced with decision guidance
- [x] `vector_store.py` — 1 tool enhanced with Confluence preference note
- [x] `datadog_tools.py` — Already had excellent self-documenting descriptions (no change needed)
- [x] `navigation_tools.py` — Already self-documenting (no change needed)

---

## Verification ✅

- [x] YAML valid — `yaml.safe_load()` succeeds
- [x] No `{available_tools}` placeholder in prompt
- [x] All key sections present (Identity, Core Principles, Knowledge Priority, Confirmation Protocol, Terminology)
- [x] Tool registry tests: 29/29 passed
- [x] Intent classifier tests: 35/35 passed
- [x] Navigation tests: 10/10 passed
- [x] Integration tests: 7/7 passed
- [x] No lint/type errors in any modified file

---

## Results

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| System prompt lines | 984 | 110 | **89%** |
| System prompt chars | ~45,000 | 4,558 | **90%** |
| Estimated prompt tokens | ~12,000 | ~1,139 | **90%** |
| Tool description redundancy | 3× (prompt + available_tools + bind_tools) | 1× (bind_tools only) | **Eliminated** |
| Disabled category provider init | Still instantiated | Skipped entirely | **Eliminated** |

### Files Modified
1. `resources/application-prompt.yaml` — Rewritten (984→110 lines)
2. `src/app/agent/implementations/langchain_react_agent.py` — Removed available_tools formatting
3. `src/app/agent/tools/base/registry.py` — Added `is_category_enabled()` + provider skip
4. `src/app/agent/tools/atlassian/jira.py` — Enhanced 4 tool descriptions
5. `src/app/agent/tools/atlassian/confluence.py` — Enhanced 2 tool descriptions
6. `src/app/agent/tools/database/vector_store.py` — Enhanced 1 tool description
7. `tests/unit/agent/tools/test_tool_registry.py` — Added 7 new tests
