# AgentHub 🤖

> **A production-ready, modular LLM application framework for RAG, tool orchestration, and intelligent agents**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 🎯 What is AgentHub?

AgentHub is a **full-featured LLM application framework** designed to be a reference implementation for production-grade AI applications. Unlike tutorials and toy examples, AgentHub provides:

- 🏗️ **Production-Ready Architecture** - SOLID principles, design patterns, resilience
- 🔌 **Fully Modular** - Swap LLMs, vector stores, agents, tools without breaking changes
- ⚙️ **Type-Safe Configuration** - YAML-based with Pydantic validation
- 🛡️ **Built-In Resilience** - Retry, circuit breakers, timeout patterns
- 📊 **Observable** - Structured logging, monitoring endpoints, health checks
- 🚀 **Deploy Anywhere** - Docker, Kubernetes, cloud platforms

### Who is AgentHub For?

| You are... | AgentHub helps you... |
|------------|----------------------|
| 🎓 **New to LLMs** | Learn how production LLM apps work with real code |
| 👨‍💻 **Python Developer** | Bootstrap AI features with proven patterns |
| 🏗️ **Learning Architecture** | Study design patterns in a real codebase |
| 🏢 **Organization** | Deploy internal RAG/MCP servers quickly |
| 🚀 **Building Startup** | Start with production-grade foundation |

---

## ✨ Key Features

### 🤖 **Intelligent Agent System**
- Multi-framework support (LangChain, LangGraph)
- ReAct agent pattern
- Tool orchestration with registry
- Conversation memory management

### 🔍 **RAG (Retrieval-Augmented Generation)**
- Multiple vector stores (Qdrant, ChromaDB, PgVector)
- Document chunking and embedding
- Semantic search with metadata filtering
- Hybrid search capabilities

### 🔌 **Tool Integrations**
- **Atlassian**: Jira, Confluence
- **DevOps**: GitHub (App auth), Datadog
- **Databases**: PostgreSQL, MongoDB, Redis
- **Extensible**: Add custom tools easily

### 🎛️ **LLM Provider Flexibility**
- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI
- Anthropic (Claude)
- Groq (Llama, Mixtral)
- **Easy to add new providers**

### ⚙️ **Configuration System** ⭐ (Star Feature!)
```yaml
# resources/application-llm.yaml
providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    model: gpt-4
    temperature: 0.7
```
- Type-safe YAML configuration
- Profile-based configs (dev/staging/prod)
- Environment variable substitution
- Dynamic config loading

**[Learn more →](docs/architecture/configuration-system.md)**

### 🛡️ **Resilience Patterns**
```python
@retry(max_attempts=3, backoff=RetryStrategy.EXPONENTIAL)
@circuit_breaker(name="jira_api", failure_threshold=5)
def search_issues(jql: str):
    return jira.search_issues(jql)
```
- Automatic retry with backoff
- Circuit breakers prevent cascade failures
- Timeout enforcement
- Real-time monitoring API

**[Learn more →](docs/guides/resilience/overview.md)**

---

## 🚀 Quick Start

Get AgentHub running in **< 5 minutes**:

```bash
# 1. Clone and setup
git clone https://github.com/timothy-odofin/agenthub-be.git
cd agenthub-be
chmod +x agenthub_setup.sh
./agenthub_setup.sh

# 2. Start services (PostgreSQL, Redis, MongoDB)
docker-compose up -d

# 3. Activate environment
source .venv/bin/activate

# 4. Run migrations (optional - auto-creates tables)
alembic upgrade head

# 5. Start the API
make run-api
```

**Visit**: 
- 🌐 API: http://localhost:8000
- 📚 Docs: http://localhost:8000/docs
- 🔍 ReDoc: http://localhost:8000/redoc

### Environment Setup

Create `.env` file in project root:

```bash
# LLM Provider (choose one or multiple)
OPENAI_API_KEY=sk-...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...

# Database (provided by docker-compose)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=polyagent
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123

# Redis (provided by docker-compose)
REDIS_HOST=localhost
REDIS_PORT=6379

# MongoDB (provided by docker-compose)
MONGODB_URI=mongodb://admin:admin123@localhost:27017

# App Configuration
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO
```

**[Full installation guide →](docs/getting-started/installation.md)**

---

## 📚 Documentation

### For Different Audiences

<table>
<tr>
<td width="50%">

#### 🎓 **New to LLMs?**
Start with the basics:
1. [What are LLMs?](docs/core-concepts/llm-basics.md)
2. [Understanding RAG](docs/core-concepts/rag-pipeline.md)
3. [Build Your First Agent](docs/tutorials/build-rag-chatbot.md)

</td>
<td width="50%">

#### 👨‍💻 **Python Developer?**
Jump right in:
1. [Quick Start Guide](docs/getting-started/quick-start.md)
2. [Architecture Overview](docs/architecture/overview.md)
3. [Add a Custom Tool](docs/guides/tools/custom-tool.md)

</td>
</tr>
<tr>
<td width="50%">

#### 🏗️ **Learning Architecture?**
Study the patterns:
1. [Design Patterns Used](docs/architecture/design-patterns.md)
2. [Configuration System](docs/architecture/configuration-system.md) ⭐
3. [Modular Design](docs/architecture/modular-design.md)

</td>
<td width="50%">

#### 🚀 **Deploying to Production?**
Get production-ready:
1. [Deployment Guide](docs/deployment/overview.md)
2. [Production Checklist](docs/deployment/production-checklist.md)
3. [Monitoring Setup](docs/deployment/monitoring-setup.md)

</td>
</tr>
</table>

### Documentation Index

| Section | Description |
|---------|-------------|
| 🏁 [**Getting Started**](docs/getting-started/) | Installation, quick start, first agent |
| 🏗️ [**Architecture**](docs/architecture/) | System design, patterns, configuration system ⭐ |
| 📖 [**Core Concepts**](docs/core-concepts/) | LLMs, RAG, agents, tools, sessions |
| 📘 [**Guides**](docs/guides/) | How to use and extend components |
| 📝 [**Tutorials**](docs/tutorials/) | End-to-end examples and use cases |
| 🚀 [**Deployment**](docs/deployment/) | Docker, K8s, cloud platforms |
| 📚 [**API Reference**](docs/api-reference/) | REST endpoints, WebSockets |
| 🔬 [**Advanced**](docs/advanced/) | Performance, security, cost optimization |

---

## 🏗️ Architecture Highlights

### **Modular by Design**

```
┌─────────────────────────────────────────────┐
│              FastAPI API Layer              │
│  /chat  /health  /tools  /resilience        │
└────────────────┬────────────────────────────┘
                 │
┌────────────────┴────────────────────────────┐
│          Agent Orchestration                │
│  LangChain | LangGraph | Custom Agents      │
└────────┬──────────────────┬─────────────────┘
         │                  │
    ┌────┴─────┐      ┌────┴──────────┐
    │  Tools   │      │  RAG Pipeline │
    │  Registry│      │  + Vector DB  │
    └──────────┘      └───────────────┘
         │                  │
    ┌────┴──────────────────┴─────────────────┐
    │     Connection Manager Layer            │
    │  Jira | GitHub | Confluence | Datadog   │
    │  PostgreSQL | MongoDB | Redis | Qdrant  │
    └─────────────────────────────────────────┘
```

**[Detailed architecture →](docs/architecture/overview.md)**

### **Design Patterns Showcase**

AgentHub implements industry-standard patterns:

- **Registry Pattern** - Dynamic tool/agent/config discovery
- **Factory Pattern** - LLM provider and vector store creation
- **Singleton Pattern** - Settings and connection management
- **Strategy Pattern** - Retry strategies, embedding providers
- **Decorator Pattern** - Resilience (retry, circuit breaker, timeout)
- **Template Method** - Base connection manager
- **Dependency Injection** - FastAPI dependencies

**[Learn all patterns →](docs/architecture/design-patterns.md)**

---

## 🎓 Learning Resources

### Tutorials

- 📚 [**Build a RAG Chatbot**](docs/tutorials/build-rag-chatbot.md) - End-to-end tutorial
- 🎨 [**Conversational Auth**](docs/tutorials/conversational-auth.md) - LLM-powered flows (demo)
- 🔧 [**Custom Tool Integration**](docs/tutorials/custom-tool-integration.md) - Add Slack/Discord
- 🌐 [**Frontend Integration**](docs/tutorials/frontend-integration.md) - Connect to React/Vue

### Guides by Component

<details>
<summary><b>🔌 Connections</b></summary>

- [Connection Manager Overview](docs/guides/connections/overview.md)
- [Database Connections](docs/guides/connections/database.md)
- [Vector Store Connections](docs/guides/connections/vector-stores.md)
- [External Services](docs/guides/connections/external-services.md)
- [Create Custom Connection](docs/guides/connections/custom-connection.md)

</details>

<details>
<summary><b>🤖 LLM Providers</b></summary>

- [LLM Provider System](docs/guides/llm-providers/overview.md)
- [OpenAI](docs/guides/llm-providers/openai.md)
- [Azure OpenAI](docs/guides/llm-providers/azure-openai.md)
- [Groq](docs/guides/llm-providers/groq.md)
- [Anthropic](docs/guides/llm-providers/anthropic.md)
- [Add Custom Provider](docs/guides/llm-providers/custom-provider.md)

</details>

<details>
<summary><b>🛠️ Tools</b></summary>

- [Tool System Overview](docs/guides/tools/overview.md)
- [Jira Tools](docs/guides/tools/jira.md)
- [GitHub Tools](docs/guides/tools/github.md)
- [Confluence Tools](docs/guides/tools/confluence.md)
- [Datadog Tools](docs/guides/tools/DATADOG_COMPLETE_SUMMARY.md)
- [Create Custom Tool](docs/guides/tools/custom-tool.md)

</details>

<details>
<summary><b>🛡️ Resilience</b></summary>

- [Resilience Overview](docs/guides/resilience/overview.md)
- [Retry Patterns](docs/guides/resilience/retry-patterns.md)
- [Circuit Breakers](docs/guides/resilience/circuit-breakers.md)
- [Monitoring API](docs/guides/resilience/monitoring.md)

</details>

---

## 🛠️ Development

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Make (optional, but recommended)

### Development Setup

```bash
# Install dependencies
make install-dev

# Run tests
make test

# Run tests with coverage
make test-cov

# Format code
make format

# Lint code
make lint

# Type check
make typecheck

# Run all checks
make check-all
```

### Project Structure

```
src/
├── app/
│   ├── api/              # FastAPI endpoints
│   │   └── v1/           # API version 1
│   ├── agent/            # Agent implementations
│   │   ├── frameworks/   # LangChain, LangGraph
│   │   ├── implementations/
│   │   └── tools/        # Tool integrations
│   ├── connections/      # Connection managers
│   │   ├── database/     # PostgreSQL, MongoDB, Redis
│   │   ├── vector/       # Qdrant, ChromaDB, PgVector
│   │   └── external/     # Jira, GitHub, Confluence
│   ├── core/             # Core functionality
│   │   ├── config/       # Configuration system ⭐
│   │   ├── exceptions/   # Exception hierarchy
│   │   ├── handlers/     # Exception handlers
│   │   ├── resilience/   # Retry, circuit breaker
│   │   └── utils/        # Utilities, logging
│   ├── llm/              # LLM providers
│   │   ├── providers/    # OpenAI, Groq, Anthropic
│   │   └── factory/      # LLM factory
│   ├── services/         # Business logic
│   ├── sessions/         # Session management
│   └── db/               # Database models, repos
│
└── tests/
    ├── unit/             # Unit tests
    ├── integration/      # Integration tests
    └── e2e/              # End-to-end tests
```

**[Complete code structure →](docs/contributing/code-structure.md)**

---

## 🧪 Testing

AgentHub has comprehensive test coverage:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests
pytest tests/e2e/              # End-to-end tests

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_resilience_patterns.py -v
```

**Current Test Stats**:
- ✅ 88 tests passing
- 🎯 85%+ coverage
- 🚀 Fast unit tests (< 1s each)

**[Testing guide →](docs/contributing/testing.md)**

---

## 🚢 Deployment

### Docker (Recommended)

```bash
# Build and run everything
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Kubernetes

```bash
# Apply configurations
kubectl apply -f k8s/

# Check status
kubectl get pods

# View logs
kubectl logs -f deployment/agenthub-api
```

**[Full deployment guides →](docs/deployment/)**

### Cloud Platforms

- ☁️ [Render](docs/deployment/render-setup.md)
- ☁️ [AWS ECS](docs/deployment/aws.md)
- ☁️ [Google Cloud Run](docs/deployment/gcp.md)
- ☁️ [Azure Container Apps](docs/deployment/azure.md)

---

## 📊 Tech Stack

| Layer | Technologies |
|-------|-------------|
| **API** | FastAPI, Pydantic, Uvicorn |
| **Agents** | LangChain, LangGraph |
| **LLMs** | OpenAI, Anthropic, Groq, Azure OpenAI |
| **Vector Stores** | Qdrant, ChromaDB, PgVector |
| **Databases** | PostgreSQL, MongoDB, Redis |
| **Tools** | Jira, GitHub, Confluence, Datadog |
| **Testing** | pytest, pytest-asyncio, pytest-mock |
| **Code Quality** | black, isort, mypy, flake8 |
| **Deployment** | Docker, Kubernetes, GitHub Actions |

---

## 🤝 Contributing

We welcome contributions! AgentHub is designed to be a community resource for learning and building LLM applications.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Format code (`make format`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

**[Contributing guide →](CONTRIBUTING.md)**

### Areas We'd Love Help With

- 📝 Documentation improvements
- 🧪 Additional test coverage
- 🔧 New tool integrations
- 🤖 New LLM providers
- 🌐 Frontend examples
- 🐛 Bug fixes
- 💡 Feature suggestions

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🌟 Acknowledgments

Built with ❤️ using these amazing open source projects:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [LangChain](https://python.langchain.com/) - LLM application framework
- [Qdrant](https://qdrant.tech/) - Vector database
- [PostgreSQL](https://www.postgresql.org/) - Relational database
- [Redis](https://redis.io/) - In-memory data store
- And many more in [requirements.txt](requirements.txt)

---

## 📞 Support & Community

- 📖 **Documentation**: [docs/](docs/)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/timothy-odofin/agenthub-be/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/timothy-odofin/agenthub-be/discussions)
- 📧 **Email**: [Your email or team email]

---

## 🗺️ Roadmap

- [ ] Web Component / Plugin version
- [ ] GraphQL API support
- [ ] Distributed tracing (OpenTelemetry)
- [ ] Multi-tenant support
- [ ] Analytics dashboard
- [ ] More LLM providers (Cohere, Together AI)
- [ ] More vector stores (Pinecone, Weaviate)
- [ ] Streaming improvements
- [ ] Cost tracking and budgets

**[Full roadmap →](docs/ROADMAP.md)**

---

<div align="center">

**⭐ If AgentHub helps you, please star this repo! ⭐**

Made with 🤖 and ❤️ for the LLM community

</div>


