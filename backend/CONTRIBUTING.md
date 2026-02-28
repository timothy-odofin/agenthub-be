# Contributing to AgentHub

Thanks for your interest in contributing! This document will help you get started.

## Ways to Contribute

- 🐛 Report bugs
- 💡 Suggest new features or integrations
- 📝 Improve documentation
- 🔧 Submit bug fixes
- ✨ Add new features or tools
- 🎨 Improve code quality or architecture

## Getting Started

### 1. Fork & Clone
```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/agenthub-be.git
cd agenthub-be/backend
```

### 2. Set Up Development Environment
```bash
# Install dependencies
poetry install

# Or with pip
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Add your API keys
```

### 3. Run the Application
```bash
# Development mode (with auto-reload)
uvicorn src.app.main:app --reload

# Or with Docker
docker-compose up
```

### 4. Run Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_example.py
```

## Making Changes

### 1. Create a Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes
- Follow existing code style
- Add tests for new features
- Update documentation if needed
- Keep commits focused and atomic

### 3. Test Your Changes
```bash
# Run tests
pytest

# Check code style
black src/ tests/
flake8 src/ tests/
```

### 4. Commit Your Changes
```bash
git add .
git commit -m "feat: add new feature description"
# or
git commit -m "fix: resolve bug description"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

### 5. Push & Create Pull Request
```bash
git push origin feature/your-feature-name
```

Then go to GitHub and create a Pull Request.

## Code Guidelines

### Style
- Follow PEP 8
- Use type hints where possible
- Write descriptive variable names
- Add docstrings to classes and functions

### Architecture
- Keep separation of concerns
- Use dependency injection
- Follow existing patterns (Factory, Strategy, Registry)
- Add proper error handling

### Example - Adding a New Tool
```python
# 1. Create tool file in src/app/agent/tools/your_tool/
from app.agent.tools.base import BaseTool

class YourTool(BaseTool):
    name = "your_tool"
    description = "What your tool does"

    def _run(self, query: str) -> str:
        # Implementation
        pass
```

```python
# 2. Register in src/app/agent/tools/registry.py
from app.agent.tools.your_tool import YourTool

registry.register_tool(YourTool)
```

```python
# 3. Add configuration in resources/application-tools.yaml
tools:
  your_tool:
    enabled: true
    # configuration options
```

```python
# 4. Add tests in tests/unit/tools/test_your_tool.py
def test_your_tool():
    tool = YourTool()
    result = tool._run("test query")
    assert result is not None
```

## Adding New Integrations

### 1. Connection Manager
Create in `src/app/infrastructure/connections/`:
```python
class YourServiceConnectionManager(BaseConnectionManager):
    def get_config_category(self) -> str:
        return "external"

    def get_connection_name(self) -> str:
        return "your_service"

    def validate_config(self) -> None:
        # Validate required fields
        pass

    def connect(self):
        # Establish connection
        pass
```

### 2. Configuration
Add to `resources/application-external.yaml`:
```yaml
your_service:
  api_key: "${YOUR_SERVICE_API_KEY}"
  base_url: "https://api.yourservice.com"
  enabled: true
```

### 3. Service Layer
Create in `src/app/services/external/`:
```python
class YourService:
    def __init__(self):
        self._connection_manager = None

    def your_method(self):
        self._ensure_connected()
        # Implementation
```

### 4. Documentation
Update `docs/guides/` with usage examples.

## Pull Request Guidelines

### Before Submitting
- ✅ Tests pass locally
- ✅ Code follows style guidelines
- ✅ Documentation is updated
- ✅ Commit messages are clear
- ✅ Branch is up to date with main

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Code refactoring

## Testing
How has this been tested?

## Screenshots (if applicable)

## Checklist
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code follows style guidelines
```

## Need Help?

- 💬 [GitHub Discussions](https://github.com/timothy-odofin/agenthub-be/discussions)
- 🐛 [Report Issues](https://github.com/timothy-odofin/agenthub-be/issues)
- 📧 Contact maintainers through GitHub

## Recognition

Contributors will be:
- Added to the contributors list
- Mentioned in release notes
- Credited in documentation

Thank you for contributing! 🎉
