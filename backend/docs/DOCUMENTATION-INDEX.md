# Documentation Updates

## Recent Changes

### Latest Updates - April 9, 2026

1. **[MCP-GITHUB-INTEGRATION-2026-04-09.md](./architecture/MCP-GITHUB-INTEGRATION-2026-04-09.md)** ⭐ **NEW - ARCHITECTURE**
   - Full account of all MCP GitHub integration changes on this branch
   - SHA-as-path guardrail (`_sanitize_github_args`) and error-as-string handling
   - Tool list reduced 14 → 10; `search_code` reordered to first position
   - `tool_descriptions` YAML override map — agent-optimised descriptions without code changes
   - Intent classifier extended with codebase/architecture/design-pattern keywords
   - `AgentExecutor` `max_iterations` and `max_execution_time` now wired correctly
   - `early_stopping_method` removed (unsupported in LangChain 0.3.x)
   - WebTools `_run_async()` helper fixing "coroutine never awaited" warning
   - Redis `ensure_connected()` override with real async PING (fixes TCPTransport closed)
   - Frontend `MarkdownRenderer.tsx` inline/block code fix + CSS cleanup

2. **[GitHub Tools Guide](./guides/tools/github-tools.md)** ⭐ **NEW - GUIDE**
   - Full reference for GitHub MCP tools (replaces stub "documentation to be added")
   - Available tools table, configuration, intent classification patterns
   - Usage examples — efficient 3-call flow vs slow directory-crawling anti-pattern
   - Known pitfalls: SHA-as-path, error strings, Redis reconnects
   - Architecture trade-off table: direct API vs MCP
   - File reference and test coverage guide

3. **Updated Existing Docs:**
   - [Tools Guide README](./guides/tools/README.md) — GitHub section replaced stub with full entry; intent classifier table updated; tool comparison table updated
   - [Documentation Index](./DOCUMENTATION-INDEX.md) — This file

---

### Previous Updates - April 7, 2026

1. **[VOICE-NAVIGATION-ARCHITECTURE.md](./architecture/VOICE-NAVIGATION-ARCHITECTURE.md)** ⭐ **NEW - ARCHITECTURE**
   - Voice input and auto-sync route navigation architecture
   - Route Registry, Sync Hook, and Action Executor components
   - Full flow from frontend route sync to LLM-driven navigation
   - NAVIGATE and UI_ACTION action types
   - Testing guide (10 direct + 7 LLM integration tests)

2. **[PROMPT-OPTIMIZATION-2026-04-07.md](./architecture/PROMPT-OPTIMIZATION-2026-04-07.md)** ⭐ **NEW - OPTIMIZATION**
   - System prompt reduced from 984 → 110 lines (89% reduction)
   - Intent classifier reduces 86 tools → category-relevant subset (avg 23)
   - Tool descriptions enhanced so LLM relies on them instead of prompt
   - Category-level provider skip for unused integrations
   - Temperature tuning (0.7 → 0.3) for deterministic tool calls

3. **[Navigation Tools Guide](./guides/tools/navigation-tools.md)** ⭐ **NEW - GUIDE**
   - `navigate_to_route` and `list_available_routes` tool reference
   - Route sync mechanism and file storage
   - Intent classification patterns for navigation
   - Configuration and testing guide

4. **[Route Sync API](./api-reference/routes.md)** ⭐ **NEW - API REFERENCE**
   - GET /routes — list stored routes
   - POST /routes/sync — frontend syncs routes to backend
   - POST /routes/action-completed — frontend confirms action execution

5. **Updated Existing Docs:**
   - [Tools Guide](./guides/tools/README.md) — Added Navigation & Voice section, Intent Classifier config
   - [Agent Frameworks Guide](./guides/agent-frameworks/README.md) — Added navigation tools, prompt optimization
   - [Chat API](./api-reference/chat.md) — Added `action` field in response schema
   - [API Reference](./api-reference/README.md) — Added Route Sync API to endpoint list
   - [Frontend Integration](./tutorials/frontend-integration.md) — Added voice input & action executor sections
   - [Architecture Overview](./architecture/overview.md) — Added navigation & file storage components

---

### Previous Updates - February 25, 2026

1. **[CACHE-ARCHITECTURE-TWO-LAYER-DESIGN.md](./architecture/CACHE-ARCHITECTURE-TWO-LAYER-DESIGN.md)** ⭐ **NEW - ARCHITECTURE**
   - Explains why AgentHub uses two complementary caching layers
   - Redis/BaseCacheProvider for serializable data (sessions, tokens)
   - In-Memory LRU for non-serializable objects (LLM providers, agents)
   - Industry standard approach, used by Django, FastAPI, Spring
   - Why "no code duplication" - different problems need different solutions

2. **[PRODUCTION-GRADE-CACHING.md](./architecture/PRODUCTION-GRADE-CACHING.md)** ⭐ **NEW - IMPLEMENTATION**
   - Enterprise-grade caching patterns (thread safety, LRU, telemetry)
   - Thread-safe LRU cache with RLock implementation
   - Memory profiling and capacity planning
   - Production monitoring and alerting strategies

3. **[OPTIMIZATION-2026-02-25.md](./architecture/OPTIMIZATION-2026-02-25.md)** ⭐ **NEW - CRITICAL**
   - Performance optimization reducing request time from 50-75s to 2-5s (97-98% improvement)
   - Connection Manager caching (60% reduction in overhead)
   - Tool Registry caching (95-98% faster initialization)
   - GitHub Repository discovery caching (10-minute TTL)
   - Cache management API and monitoring guide
   - Production deployment considerations

4. **[QUICK-REFERENCE-CACHE-API.md](./QUICK-REFERENCE-CACHE-API.md)** ⭐ **NEW**
   - Quick reference for cache management API
   - Testing utilities for cache clearing
   - Performance monitoring guide
   - Troubleshooting common cache issues
   - Production considerations

5. **[REFACTORING-2026-02-25.md](./architecture/REFACTORING-2026-02-25.md)**
   - Template Method Pattern implementation across all LLM providers
   - Service code optimization (removed redundant initialization calls)
   - Agent framework cleanup (simplified client access)
   - Tool Registry import optimization
   - Comprehensive migration guide
   - Design pattern documentation

### Previous Updates - February 3, 2026

1. **[REFACTORING-2026-02-03.md](./architecture/REFACTORING-2026-02-03.md)**
   - Comprehensive guide to configuration and connection system refactoring
   - Migration guide for developers
   - Before/after code examples
   - Architecture diagrams
   - Breaking changes list

2. **[QUICK-REFERENCE-CONFIG-CHANGES.md](./QUICK-REFERENCE-CONFIG-CHANGES.md)**
   - Quick TL;DR reference
   - Migration checklist
   - Common code patterns
   - Find and replace commands

### Documentation That Needs Updates

The following documentation files reference old patterns and should be reviewed/updated:

#### High Priority
- [ ] `guides/connections/README.md` - Update connection manager examples to show `get_config_category()`
- [ ] `architecture/configuration-system.md` - Remove references to wrapper classes
- [ ] `guides/configuration/` - Update to reflect direct settings access

#### Medium Priority
- [ ] `api-reference/ingestion.md` - Update import paths for ingestion services
- [ ] `guides/llm-providers/` - May reference old config patterns
- [ ] `architecture/design-patterns.md` - Add Strategy Pattern for embeddings

#### Low Priority
- [ ] Test documentation - Update test patterns to use new mocking approach
- [ ] Tutorial files - Check for old configuration examples

---

## What Changed - Summary for Docs

### 1. Configuration Access
**Old:** Wrapper classes (`DatabaseConfig`, `VectorConfig`)
**New:** Direct settings access (`settings.db.mongodb`)

**Docs to update:**
- Any file showing `from app.core.config.sources import ...`
- Configuration examples

### 2. Connection Managers
**Old:** Hardcoded type mappings in base class
**New:** `get_config_category()` method in each manager

**Docs to update:**
- Connection manager creation guides
- Custom connection manager tutorials

### 3. Embedding System
**Old:** Factory manages config retrieval with optional parameter
**New:** Strategy Pattern with pluggable config providers

**Docs to update:**
- Embedding usage examples
- Testing guides for embeddings

### 4. Ingestion Services
**Old:** Located in `services/ingestion/`
**New:** Located in `infrastructure/ingestion/`

**Docs to update:**
- Any import examples
- Ingestion service guides

### 5. Data Source Configuration
**Old:** `application-data-sources.yaml` with `dataSources` key
**New:** `application-data.yaml` with `sources` key

**Docs to update:**
- Data source configuration guides
- Ingestion configuration examples

---

## Documentation Standards Going Forward

When documenting code, please:

1. **Show imports explicitly**
   ```python
   from app.core.config.framework.settings import settings
   ```

2. **Use direct settings access**
   ```python
   config = settings.db.mongodb  # Good
   config = DatabaseConfig(settings.db).mongodb  # Old, don't use
   ```

3. **Reference new locations**
   ```python
   from app.infrastructure.ingestion import FileIngestionService  # Correct
   from app.services.ingestion import FileIngestionService  # Old
   ```

4. **Show Strategy Pattern for tests**
   ```python
   # For testing embeddings
   from app.db.vector.providers import DictConfigProvider
   EmbeddingFactory.set_config_provider(DictConfigProvider({...}))
   ```

---

## Files Created/Modified

### Created
- ✅ `docs/architecture/REFACTORING-2026-02-03.md` - Full refactoring guide
- ✅ `docs/QUICK-REFERENCE-CONFIG-CHANGES.md` - Quick reference
- ✅ `docs/DOCUMENTATION-INDEX.md` - This file

### Need Updates
See "Documentation That Needs Updates" section above.

---

## How to Update Documentation

### Step 1: Find Old Patterns
```bash
cd docs/

# Find old config wrapper references
grep -rn "DatabaseConfig\|VectorConfig\|ExternalConfig" .

# Find old ingestion imports
grep -rn "from app.services.ingestion" .

# Find old data source refs
grep -rn "data_sources.dataSources" .
```

### Step 2: Replace with New Patterns
Use the examples in QUICK-REFERENCE-CONFIG-CHANGES.md

### Step 3: Test Examples
Ensure code examples in docs actually work:
```bash
# Extract code blocks and test them
python scripts/test_doc_examples.py
```

---

## Questions?

- See detailed migration guide: [REFACTORING-2026-02-03.md](./architecture/REFACTORING-2026-02-03.md)
- See quick reference: [QUICK-REFERENCE-CONFIG-CHANGES.md](./QUICK-REFERENCE-CONFIG-CHANGES.md)
- Check original docs for patterns: `guides/connections/README.md`

---

**Last Updated:** April 7, 2026
**Maintainer:** Development Team
