# Dependency Management Strategy

This project uses a **hybrid approach** for dependency management to handle the complexity of LLM and ML dependencies:

## 📁 File Structure

```
├── pyproject.toml      # Pure Python dependencies (Poetry managed)
├── requirements.txt    # ML/AI dependencies (pip managed)  
├── requirements-dev.txt # Development dependencies
└── Makefile           # Installation commands
```

## 🔧 Installation

### Production Environment
```bash
make install-system-deps  # Install system dependencies (macOS)
make install-prod        # Install production dependencies
```

### Development Environment  
```bash
make install-system-deps  # Install system dependencies (macOS)
make install-dev         # Install development dependencies
```

## 📋 Dependency Categories

### Poetry Managed (pyproject.toml)
- ✅ Web framework dependencies (FastAPI, Uvicorn)
- ✅ Database libraries (SQLAlchemy, PostgreSQL drivers)
- ✅ Pure Python packages (configuration, utilities)
- ✅ Development tools (pytest, black, mypy)

### Pip Managed (requirements.txt)
- 🔥 LangChain ecosystem
- 🔥 OpenAI and tokenization libraries
- 🔥 Document processing (unstructured, PDF libraries)
- 🔥 Computer vision (OpenCV, Pillow)
- 🔥 Scientific computing (NumPy, Pandas)
- 🔥 Vector databases (Qdrant)

## 🚀 Running the Application

```bash
make run-infra    # Start PostgreSQL, Redis, pgAdmin
make run-api      # Start FastAPI application  
make run-worker   # Start Celery worker
```

## 🔧 Troubleshooting

### If you encounter dependency conflicts:
1. Try `make clean-install` for a fresh installation
2. Check system dependencies with `make install-system-deps`
3. For ML packages, prefer pinned versions in requirements.txt

### Why this approach?
- **Poetry**: Great for pure Python dependencies and development workflow
- **pip**: More reliable for complex ML/AI packages with binary dependencies
- **Hybrid**: Gets the best of both worlds while avoiding common pitfalls

## 📦 Adding New Dependencies

### Pure Python packages → pyproject.toml
```bash
poetry add package-name
```

### ML/AI packages → requirements.txt
```bash
# Add to requirements.txt manually with pinned version
package-name==1.2.3
# Then run: pip install -r requirements.txt
```
