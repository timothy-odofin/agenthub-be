# Resources Directory & Configuration System - Summary

## ✨ The Two Key Features

### 1. Flexible Access Pattern: `settings.profile_name`

Every YAML file in `resources/` becomes accessible as a dictionary:

```python
from app.core.config import Settings

settings = Settings.instance()

# Any YAML file → Dictionary
llm_config = settings.llm          # resources/application-llm.yaml
db_config = settings.db            # resources/application-db.yaml
vector_config = settings.vector    # resources/application-vector.yaml
```

**Two Access Methods (Both Work!)**

#### Method 1: Dictionary Access
```python
provider = settings.llm['default_provider']
api_key = settings.llm['providers']['openai']['api_key']
```

#### Method 2: Dot Notation
```python
provider = settings.llm.default_provider
api_key = settings.llm.providers.openai.api_key
```

### 2. Automatic Environment Variable Resolution

**Write this in YAML:**
```yaml
database:
  host: "${POSTGRES_HOST:localhost}"
  port: "${POSTGRES_PORT:5432}"
  password: "${POSTGRES_PASSWORD}"
```

**Get this in Python:**
```python
db_config = settings.db

print(db_config['host'])      # "localhost" or actual value from env
print(db_config['port'])      # 5432 or actual value from env
print(db_config['password'])  # Actual password from POSTGRES_PASSWORD
```

**All ${...} patterns automatically resolved before you access them!** ⚡

---

## Complete Example

### Step 1: Create YAML File

**File**: `resources/application-llm.yaml`

```yaml
llm:
  default_provider: "openai"
  temperature: "${TEMPERATURE:0.7}"
  
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
      model: "${OPENAI_MODEL:gpt-4}"
    
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "${ANTHROPIC_MODEL:claude-2}"
```

### Step 2: Set Environment Variables

```bash
export OPENAI_API_KEY="sk-abc123..."
export ANTHROPIC_API_KEY="sk-ant-xyz..."
# TEMPERATURE and models will use defaults
```

### Step 3: Access in Python

```python
from app.core.config import Settings

settings = Settings.instance()

# Dictionary access
llm_config = settings.llm
print(llm_config['temperature'])  # 0.7 (from default)
print(llm_config['providers']['openai']['api_key'])  # "sk-abc123..."

# Dot notation access
temperature = settings.llm.temperature  # 0.7
api_key = settings.llm.providers.openai.api_key  # "sk-abc123..."

# All environment variables already resolved!
```

---

## Key Benefits

| Feature | Benefit |
|---------|---------|
| **Flexible Access** | Use dictionary `['key']` OR dot notation `.key` |
| **Auto Environment Variables** | `${VAR}` automatically resolved |
| **Default Values** | `${VAR:default}` provides fallback |
| **No Boilerplate** | Just add YAML, access immediately |
| **Type Safe** | Validated at load time |
| **Centralized** | All configs in `resources/` directory |
| **Version Controlled** | Track changes in git |

---

## The Magic Explained

### What AgentHub Does Automatically

```
┌──────────────────────────────────────────────────────┐
│  You Write YAML                                      │
│  ───────────────                                     │
│  api_key: "${OPENAI_API_KEY}"                       │
│  host: "${DB_HOST:localhost}"                       │
└─────────────────────────┬────────────────────────────┘
                          │
                          ↓
┌──────────────────────────────────────────────────────┐
│  AgentHub Processes                                  │
│  ──────────────────                                  │
│  1. Finds ${OPENAI_API_KEY} → Checks environment    │
│  2. Finds ${DB_HOST:localhost} → Checks env or uses │
│     'localhost'                                      │
└─────────────────────────┬────────────────────────────┘
                          │
                          ↓
┌──────────────────────────────────────────────────────┐
│  You Access in Python                                │
│  ─────────────────────                               │
│  settings.config['api_key']  → "sk-abc123..."       │
│  settings.config.host        → "localhost"          │
│                                                       │
│  All values already resolved! ✨                     │
└──────────────────────────────────────────────────────┘
```

---

## Common Patterns

### Pattern 1: Required Variable (No Default)

```yaml
api_key: "${OPENAI_API_KEY}"  # Error if not set
```

### Pattern 2: Optional Variable (With Default)

```yaml
temperature: "${TEMPERATURE:0.7}"  # Uses 0.7 if not set
host: "${DB_HOST:localhost}"       # Uses 'localhost' if not set
```

### Pattern 3: Multiple Variables

```yaml
database:
  host: "${DB_HOST:localhost}"
  port: "${DB_PORT:5432}"
  user: "${DB_USER:postgres}"
  password: "${DB_PASSWORD}"  # Required
```

### Pattern 4: Nested Objects

```yaml
llm:
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"
      model: "${OPENAI_MODEL:gpt-4}"
    anthropic:
      api_key: "${ANTHROPIC_API_KEY}"
      model: "${ANTHROPIC_MODEL:claude-2}"
```

---

## Access Pattern Comparison

| Scenario | Dictionary | Dot Notation |
|----------|-----------|--------------|
| **Simple value** | `settings.llm['temperature']` | `settings.llm.temperature` |
| **Nested value** | `settings.llm['providers']['openai']` | `settings.llm.providers.openai` |
| **Dynamic key** | `settings.llm['providers'][provider_name]` | `settings.llm.providers[provider_name]` |
| **Safe access** | `settings.llm.get('timeout', 30)` | N/A (use dict) |
| **Check existence** | `'key' in settings.llm` | `hasattr(settings.llm, 'key')` |

**Recommendation**: Use whichever style you prefer! Both work perfectly.

---

## File Naming Convention

```
resources/application-{profile}.yaml  →  settings.{profile}

Examples:
application-llm.yaml        →  settings.llm
application-db.yaml         →  settings.db  
application-vector.yaml     →  settings.vector
application-my-custom.yaml  →  settings.my_custom  (hyphens → underscores)
```

---

## Quick Reference

### Adding New Configuration

1. Create YAML file: `resources/application-mycustom.yaml`
2. Add content:
   ```yaml
   mycustom:
     setting1: "value1"
     setting2: "${ENV_VAR:default}"
   ```
3. Access immediately:
   ```python
   config = settings.mycustom
   value = config['setting1']  # or settings.mycustom.setting1
   ```

### Environment Variables

```yaml
# Syntax
${ENV_VAR_NAME}              # Required (error if not set)
${ENV_VAR_NAME:default}      # Optional (uses default if not set)

# Examples
api_key: "${OPENAI_API_KEY}"                    # Required
model: "${OPENAI_MODEL:gpt-4}"                  # Optional
temperature: "${OPENAI_TEMPERATURE:0.7}"        # Optional
host: "${DATABASE_HOST:localhost}"              # Optional
port: "${DATABASE_PORT:5432}"                   # Optional
```

---

## Learn More

- **[Resources Directory Guide](../guides/configuration/resources-directory.md)** - Complete guide with 40+ examples
- **[Configuration System](../architecture/configuration-system.md)** - Architecture deep dive
- **[Quick Start](../getting-started/quick-start.md)** - See it in action

---

**Key Takeaway**: Just add a YAML file in `resources/`, use `${ENV_VAR:default}` for any variables, and access via `settings.profile_name` with either dictionary or dot notation. Everything else is automatic! ✨

**Last Updated**: January 8, 2026
