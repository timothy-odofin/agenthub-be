# Documentation Updates - February 3, 2026

## Recent Changes

### New Documentation Added

1. **[REFACTORING-2026-02-03.md](./architecture/REFACTORING-2026-02-03.md)** ⭐ **NEW**
   - Comprehensive guide to configuration and connection system refactoring
   - Migration guide for developers
   - Before/after code examples
   - Architecture diagrams
   - Breaking changes list

2. **[QUICK-REFERENCE-CONFIG-CHANGES.md](./QUICK-REFERENCE-CONFIG-CHANGES.md)** ⭐ **NEW**
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

**Last Updated:** February 3, 2026
**Maintainer:** Development Team
