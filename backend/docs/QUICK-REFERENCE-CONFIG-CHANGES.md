# Quick Reference: Configuration Changes

> **TL;DR** - What changed and what you need to do

## 🚀 Quick Migration Checklist

- [ ] Replace `DatabaseConfig`/`VectorConfig`/`ExternalConfig` with direct `settings` access
- [ ] Update imports: `app.services.ingestion.*` → `app.infrastructure.ingestion.*`
- [ ] Add `get_config_category()` to custom connection managers
- [ ] Use `DictConfigProvider` for embedding tests
- [ ] Update data source refs: `settings.data_sources.dataSources` → `settings.data.sources`

---

## Before → After Examples

### 1. Configuration Access

```python
# ❌ OLD - Delete this
from app.core.config.sources.database import DatabaseConfig
db_config = DatabaseConfig(settings.db)
mongo = db_config.mongodb

# ✅ NEW - Use this
from app.core.config.framework.settings import settings
mongo = settings.db.mongodb
```

### 2. Connection Managers

```python
# ❌ OLD
class MyConnectionManager(BaseConnectionManager):
    def __init__(self):
        super().__init__()
        # Config retrieved via hardcoded mappings

# ✅ NEW  
class MyConnectionManager(BaseConnectionManager):
    def get_config_category(self) -> str:
        return "db"  # or "vector" or "external"
    
    def validate_config(self) -> None:
        config_dict = self._get_config_dict()
        # Use config_dict instead of self.config
```

### 3. Embedding Factory

```python
# ❌ OLD - Testing
embedding = EmbeddingFactory.get_embedding_model(
    EmbeddingType.OPENAI,
    embedding_config={'api_key': 'test'}
)

# ✅ NEW - Testing
from app.db.vector.providers import DictConfigProvider
EmbeddingFactory.set_config_provider(
    DictConfigProvider({
        EmbeddingType.OPENAI: {'api_key': 'test'}
    })
)
embedding = EmbeddingFactory.get_embedding_model(EmbeddingType.OPENAI)
```

### 4. Ingestion Imports

```python
# ❌ OLD
from app.services.ingestion.file_ingestion_service import FileIngestionService

# ✅ NEW
from app.infrastructure.ingestion.file_ingestion_service import FileIngestionService
```

### 5. Data Sources

```python
# ❌ OLD
data_sources = settings.data_sources.dataSources

# ✅ NEW
data_sources = settings.data.sources
```

---

## Configuration Categories

| Access | File | Purpose |
|--------|------|---------|
| `settings.db.*` | `application-db.yaml` | Databases |
| `settings.vector.*` | `application-vector.yaml` | Vector stores |
| `settings.external.*` | `application-external.yaml` | External services |
| `settings.embeddings.*` | `application-embeddings.yaml` | Embeddings |
| `settings.data.sources` | `application-data.yaml` | Data sources |

---

## Strategy Pattern for Embeddings

### Production (Default)
```python
# Uses SettingsConfigProvider automatically
embedding = EmbeddingFactory.get_embedding_model(EmbeddingType.OPENAI)
```

### Testing
```python
from app.db.vector.providers import DictConfigProvider

# Inject test config
EmbeddingFactory.set_config_provider(
    DictConfigProvider({
        EmbeddingType.OPENAI: {'api_key': 'test-key'}
    })
)
```

---

## Finding Files to Update

```bash
# Find old ingestion imports
grep -rn "from app.services.ingestion" src/

# Find old config wrappers
grep -rn "DatabaseConfig\|VectorConfig\|ExternalConfig" src/

# Find old data source refs
grep -rn "data_sources.dataSources" src/
```

---

## Test Updates

### Old Test Mocks
```python
@patch('app.core.config.sources.database.DatabaseConfig')
def test_something(mock_db_config):
    pass
```

### New Test Mocks
```python
@patch('app.infrastructure.connections.base.base_connection_manager.settings')
def test_something(mock_settings):
    mock_settings.db.mongodb = Mock(host='test-host')
```

---

## Key Benefits

✅ **Simpler** - Direct access, no wrappers
✅ **Cleaner** - One way to do things  
✅ **Testable** - Easy to mock and inject configs
✅ **Maintainable** - Clear patterns, less code

---

**See full documentation:** [REFACTORING-2026-02-03.md](./REFACTORING-2026-02-03.md)
