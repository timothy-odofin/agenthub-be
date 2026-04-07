# Prompt & Performance Optimization — April 7, 2026

> **90% prompt reduction + intent-based tool filtering**

**Branch:** `feature/voice-integration`
**Status:** ✅ Implemented & Tested (81/81 tests passing)

---

## Table of Contents

- [Executive Summary](#executive-summary)
- [Problem Analysis](#problem-analysis)
- [Changes Made](#changes-made)
  - [1. System Prompt Rewrite](#1-system-prompt-rewrite)
  - [2. Intent Classifier](#2-intent-classifier)
  - [3. Tool Description Enhancement](#3-tool-description-enhancement)
  - [4. Category-Level Provider Skip](#4-category-level-provider-skip)
  - [5. LLM Temperature Tuning](#5-llm-temperature-tuning)
- [Results](#results)
- [Modified Files](#modified-files)
- [Testing](#testing)

---

## Executive Summary

Reduced system prompt tokens by **90%** (12,000 → 1,139 tokens), eliminated triple tool-description redundancy, and added an intent classifier that cuts loaded tools from **86 → 23** for general queries.

Combined with earlier caching optimizations, chat response time dropped from **22.7s → 2-4s**.

---

## Problem Analysis

Three root causes were identified for slow response times:

### 1. All 86 Tools Loaded on Every Request

The intent classifier's general fallback returned **all 7 categories** including GitHub (63 tools, 7+ seconds to connect). For general queries like "hello", this was unnecessary.

### 2. Bloated System Prompt (~12,000 tokens)

The system prompt (`application-prompt.yaml`) had grown to **984 lines** with:
- Tool category descriptions (~200 lines) — duplicated what `bind_tools()` already provides
- Jira mention/comment workflows (~100 lines) — belonged in tool descriptions
- Confluence vs Vector decision trees (~50 lines) — belonged in tool descriptions
- 9 verbose examples (~100 lines) — not needed with good tool descriptions
- Markdown formatting tutorials (~80 lines) — LLMs already know Markdown
- `{available_tools}` text injection — redundant with `bind_tools()` API

### 3. Triple Redundancy

Tool descriptions appeared in three places:
1. **Prompt YAML** — "Tool Categories" section listing every tool
2. **`{available_tools}` placeholder** — Text-injected list of tool names + descriptions
3. **`bind_tools()`** — OpenAI function-calling API (the idiomatic approach)

Only #3 is needed. The LLM reads tool schemas from `bind_tools()` automatically.

---

## Changes Made

### 1. System Prompt Rewrite

**File:** `resources/application-prompt.yaml`

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Lines | 984 | 110 | 89% |
| Characters | ~45,000 | 4,558 | 90% |
| Estimated tokens | ~12,000 | ~1,139 | 90% |

**Sections kept** (concise):
- Identity (3 lines)
- Core Principles (4 items)
- Knowledge Source Priority (4 tiers)
- When to Use Tools (2 lines)
- Terminology Mapping (9 compact mappings)
- Response Formatting (10 lines)
- Confirmation Protocol (~30 lines)
- General Guidelines (6 lines)

**Sections removed:**
- Tool Categories listing (~200 lines)
- `{available_tools}` placeholder
- Jira mention/comment workflows (~100 lines) → moved to tool descriptions
- Confluence vs Vector decision tree (~50 lines) → moved to tool descriptions
- Structured response templates (~100 lines)
- 9 verbose examples (~100 lines)
- Markdown formatting tutorial (~80 lines)
- Full terminology synonyms (~50 lines)

### 2. Intent Classifier

**File:** `src/app/services/intent_classifier.py`

A zero-latency (~0ms) keyword/pattern-based classifier that runs **before** the LLM call:

```python
from app.services.intent_classifier import classify_intent, ToolCategory

categories = classify_intent("search for bugs in jira")
# → {ToolCategory.JIRA, ToolCategory.NAVIGATION}

categories = classify_intent("hello, how are you?")
# → _GENERAL_CATEGORIES (excludes GitHub)
```

**7 categories:** NAVIGATION, GITHUB, JIRA, CONFLUENCE, DATADOG, VECTOR, WEB

**Key design:** The `_GENERAL_CATEGORIES` fallback set **excludes GitHub** (63 tools, 7+s connection time). GitHub tools are only loaded when the user explicitly mentions GitHub/repos/PRs.

| Input | Categories | Tools loaded |
|-------|-----------|-------------|
| "search jira bugs" | JIRA, NAVIGATION | ~15 |
| "show me PRs" | GITHUB, NAVIGATION | ~65 |
| "hello" | General (no GitHub) | ~23 |
| "go to dashboard" | NAVIGATION | ~2 |

### 3. Tool Description Enhancement

**Why:** With the system prompt no longer containing tool-specific guidance, that guidance was moved into the tool `description` fields — where it travels WITH the tool and only appears when that tool is loaded.

**Files modified:**

| File | Tools Enhanced | What Was Added |
|------|---------------|----------------|
| `jira.py` | `search_jira_issues` | JQL operators, status mappings, example queries |
| `jira.py` | `create_jira_issue` | Confirmation note, common issue types |
| `jira.py` | `add_jira_comment` | Full mention workflow, privacy rules |
| `jira.py` | `search_jira_users` | "Use BEFORE add_jira_comment" guidance |
| `confluence.py` | `search_confluence_pages` | "PREFERRED for real-time Confluence content" |
| `confluence.py` | `get_confluence_page` | "Returns the latest version" |
| `vector_store.py` | `retrieve_information` | "For real-time Confluence, prefer Confluence tools" |

### 4. Category-Level Provider Skip

**File:** `src/app/agent/tools/base/registry.py`

Added `is_category_enabled()` function and a category-level check **before** `tool_class(...)` instantiation. This prevents expensive provider initialization (e.g., GitHub's 7+s API connection) when a category is disabled.

```python
from app.agent.tools.base.registry import is_category_enabled

if not is_category_enabled("github"):
    # Skip — don't even import the GitHub provider
    pass
```

### 5. LLM Temperature Tuning

**File:** `resources/application-llm.yaml`

Changed default temperature from `1.0` → `0.2` for more deterministic, focused responses.

---

## Results

| Metric | Before | After |
|--------|--------|-------|
| System prompt tokens | ~12,000 | ~1,139 |
| Tools loaded (general query) | 86 | 23 |
| Tools loaded (GitHub query) | 86 | 65 |
| Tool description redundancy | 3× | 1× |
| Disabled category provider init | Still ran | Skipped |
| LLM temperature | 1.0 | 0.2 |

---

## Modified Files

| # | File | Change |
|---|------|--------|
| 1 | `resources/application-prompt.yaml` | Rewritten 984→110 lines |
| 2 | `src/app/agent/implementations/langchain_react_agent.py` | Removed `{available_tools}` formatting |
| 3 | `src/app/agent/tools/base/registry.py` | Added `is_category_enabled()` + provider skip |
| 4 | `src/app/agent/tools/atlassian/jira.py` | Enhanced 4 tool descriptions |
| 5 | `src/app/agent/tools/atlassian/confluence.py` | Enhanced 2 tool descriptions |
| 6 | `src/app/agent/tools/database/vector_store.py` | Enhanced 1 tool description |
| 7 | `src/app/services/intent_classifier.py` | **NEW** — keyword-based classifier |

---

## Testing

### Intent Classifier — 35 tests

```bash
cd backend
pytest tests/unit/services/test_intent_classifier.py -v
```

Covers: all 7 categories, multi-intent messages, general fallback, navigation-always-included, category-to-registry mapping.

### Tool Registry — 29 tests (7 new)

```bash
cd backend
pytest tests/unit/agent/tools/test_tool_registry.py -v
```

New tests cover: `is_category_enabled()` (enabled, disabled, nonexistent, missing config, exception), provider skip on disabled category (verifies `__init__` count=0).

### YAML Validation

```bash
cd backend && source .venv/bin/activate
python -c "
import yaml
with open('resources/application-prompt.yaml') as f:
    data = yaml.safe_load(f)
prompt = data['system']['agent']['react_agent']
print(f'Valid: ✅  |  {len(prompt)} chars  |  ~{len(prompt)//4} tokens')
assert '{available_tools}' not in prompt, 'Stale placeholder!'
"
```

---

## Related Documentation

- [Voice & Navigation Architecture](./VOICE-NAVIGATION-ARCHITECTURE.md)
- [Optimization Summary (Feb 2026)](./OPTIMIZATION-SUMMARY.md) — Earlier caching optimizations
- [Tools Guide](../guides/tools/README.md) — Tool integration patterns
- [TODO Tracking](../TODO_PROMPT_OPTIMIZATION.md) — Implementation checklist
