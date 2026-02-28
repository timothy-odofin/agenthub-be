# CHANGELOG

## [2.0.0] - 2026-02-03

### 🚀 Major Refactoring: Configuration & Connection System

#### Breaking Changes
- ⚠️ Removed configuration wrapper classes (`DatabaseConfig`, `VectorConfig`, `ExternalConfig`)
- ⚠️ Migrated ingestion services from `services/` to `infrastructure/` package
- ⚠️ Changed embedding factory API to use Strategy Pattern
- ⚠️ Renamed `application-data-sources.yaml` to `application-data.yaml`
- ⚠️ Changed data source config key from `dataSources` to `sources`

#### Added
- ✅ Strategy Pattern for embedding configuration management
- ✅ `EmbeddingConfigProvider` interface with multiple implementations
- ✅ `SettingsConfigProvider` for production (default)
- ✅ `DictConfigProvider` for testing
- ✅ `get_config_category()` method in all connection managers
- ✅ Direct settings access pattern throughout codebase
- ✅ `_get_config_dict()` helper for converting DynamicConfig to dict
- ✅ Comprehensive refactoring documentation

#### Changed
- 🔄 Connection managers now use `get_config_category()` pattern
- 🔄 Configuration access simplified: `settings.db.mongodb` instead of wrappers
- 🔄 Vector stores get config as dictionary via `_get_config_dict()`
- 🔄 Embedding factory delegates config retrieval to providers
- 🔄 All async methods in vector stores follow base class contract
- 🔄 Ingestion base class adapted to new YAML structure

#### Removed
- 🗑️ `src/app/core/config/sources/database.py`
- 🗑️ `src/app/core/config/sources/vector.py`
- 🗑️ `src/app/core/config/sources/external.py`
- 🗑️ `validate_config_dict` export from config utils
- 🗑️ Hardcoded connection type mappings in base connection manager
- 🗑️ ConfigSourceRegistry pattern (no longer needed)

#### Fixed
- 🐛 Vector store configuration access (DynamicConfig → dict conversion)
- 🐛 Embedding provider config retrieval (`settings.embeddings` instead of `settings.vector.embedding_config`)
- 🐛 Async/await consistency in Qdrant vector store
- 🐛 Ingestion service configuration loading after YAML restructure

#### Documentation
- 📚 Added `docs/architecture/REFACTORING-2026-02-03.md` - Comprehensive refactoring guide
- 📚 Added `docs/QUICK-REFERENCE-CONFIG-CHANGES.md` - Quick migration reference
- 📚 Added `docs/DOCUMENTATION-INDEX.md` - Documentation update tracker
- 📚 Updated embedding system documentation with Strategy Pattern
- 📚 Updated connection manager documentation with new pattern

#### Migration Required
Developers must update:
1. All configuration wrapper imports → direct settings access
2. Ingestion service imports → new `infrastructure` location
3. Custom connection managers → add `get_config_category()` method
4. Embedding tests → use `DictConfigProvider` pattern
5. Data source config references → use `settings.data.sources`

**Migration Guide:** See [docs/architecture/REFACTORING-2026-02-03.md](docs/architecture/REFACTORING-2026-02-03.md)

---

## [1.x.x] - Previous Versions

### Infrastructure Improvements
- Added factory and registry patterns for infrastructure components
- Implemented Redis and in-memory cache services
- Created comprehensive connection management system
- Added LLM provider abstraction layer

### Features
- REST API for chat, authentication, and document ingestion
- RAG (Retrieval-Augmented Generation) pipeline
- Multi-LLM support (OpenAI, Anthropic, Groq, Azure)
- Vector database integration (Qdrant, PgVector, ChromaDB)
- Document processing from multiple sources
- Conversational authentication flow
- Session management with Redis
- Health check endpoints

### Documentation
- Comprehensive architecture documentation
- API reference guides
- Integration tutorials
- Configuration guides

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 2.0.0 | 2026-02-03 | Configuration & connection system refactoring (Strategy Pattern) |
| 1.x.x | Previous | Initial production release with core features |

---

## Upgrade Notes

### Upgrading to 2.0.0

**Step 1:** Review breaking changes
```bash
# Check if your code uses old patterns
grep -rn "DatabaseConfig\|VectorConfig\|ExternalConfig" src/
grep -rn "from app.services.ingestion" src/
grep -rn "data_sources.dataSources" src/
```

**Step 2:** Update imports and configuration access
- See [QUICK-REFERENCE-CONFIG-CHANGES.md](docs/QUICK-REFERENCE-CONFIG-CHANGES.md)

**Step 3:** Test your application
```bash
# Run unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Check application startup
python src/app/main.py
```

**Step 4:** Update custom components
- Add `get_config_category()` to custom connection managers
- Update embedding tests to use `DictConfigProvider`
- Verify data source configuration references

---

## Contributors

- Development Team @ AgentHub

---

**For detailed changes:** See individual commit messages and PR descriptions
**For migration help:** See [REFACTORING-2026-02-03.md](docs/architecture/REFACTORING-2026-02-03.md)
