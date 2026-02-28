---
title: AgentHub Backend API
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 7860
---

# AgentHub

> **Learn, Build, and Deploy Production LLM Applications**
> *A complete framework for developers who want to understand how real-world AI systems work*

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downlo---

## Documentation

**[Complete Documentation Hub](docs/)** - Everything you need to learn, build, and deploy

### Learning Path

**New to LLMs?** Follow this path:

1. **[LLM Basics](docs/core-concepts/llm-basics.md)** - Understand how LLMs work
2. **[RAG Pipeline](docs/core-concepts/rag-pipeline.md)** - Learn retrieval-augmented generation
3. **[Agent Frameworks](docs/guides/agent-frameworks/README.md)** - How agents make decisions
4. **[Quickstart Tutorial](docs/getting-started/quick-start.md)** - Build your first LLM app

### For Python Developers

Want to adopt these patterns? Start here:

1. **[Configuration System](docs/guides/configuration/README.md)** - Type-safe YAML configs
2. **[Resilience Patterns](src/app/core/resilience/)** - Retry, circuit breakers (see code implementation)
3. **[Testing Patterns](tests/)** - Unit, integration, E2E test examples
4. **[Connection Management](docs/guides/connections/README.md)** - Database connection patterns

### Documentation by Topic

- **[Getting Started](docs/getting-started/quick-start.md)** - 5-minute setup
- **[API Reference](docs/api-reference/README.md)** - Complete REST API docs
- **[Architecture](docs/architecture/overview.md)** - System design & patterns
- **[Feature Guides](docs/guides/)** - LLM, RAG, tools, resilience, configuration
- **[Tutorials](docs/tutorials/)** - Step-by-step examples
- **[Deployment](docs/deployment/overview.md)** - AWS, GCP, Azure, Kubernetes

**Looking for specific roles?** See [docs/README.md](docs/) for paths tailored to developers, DevOps, data scientists, and product managers.https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## What is AgentHub?

AgentHub is **your LLM learning laboratory and production framework**. Whether you're building your first AI app or scaling to production, AgentHub shows you the complete picture with real, working code.

### Built for Learning & Innovation

Unlike tutorials that show toy examples, AgentHub is a **complete, production-grade LLM application** you can learn from, fork, and build upon:

- � **Learn by Example** - See how real LLM systems work, not just "hello world" demos
- **Proven Design Patterns** - Configuration system, resilience patterns, agent workflows
- **Working Implementations** - Conversational signup, RAG pipeline, tool orchestration
- **Educational First** - Every feature is documented with "why" not just "how"
- **Open Innovation** - Propose any LLM problem, we'll build the solution together

### � Why AgentHub Exists

**The Problem**: Most LLM tutorials teach isolated concepts. Real apps need **configuration management**, **error handling**, **observability**, **testing**, and **deployment** - but few resources show how it all fits together.

**Our Solution**: AgentHub is a **living textbook** - a complete LLM application with patterns you can adopt in **any Python framework** (FastAPI, Django, Flask, etc.).

### Who Should Use AgentHub?

| You are... | AgentHub helps you... |
|------------|----------------------|
| **New to LLMs** | Learn how production AI apps work with complete, working code |
| **Python Developer** | See reusable patterns: settings, retry logic, agent workflows |
| **FastAPI/Django Dev** | Adopt design patterns: type-safe config, resilience, modularity |
| **Learning AI** | Study real implementations: RAG, agents, conversational flows |
| **Building Products** | Fork and customize a production-ready foundation |
| **Teams** | Reference architecture for internal AI platforms |

### Featured Learning Examples

These aren't just features - they're **learning modules** demonstrating real LLM patterns:

- **Configuration System** - Type-safe YAML configs you can use in any Python project
- **Conversational Signup** - See how agent workflows work with a practical example
- **� RAG Pipeline** - Complete implementation: chunking, embedding, retrieval, generation
- **Resilience Patterns** - Retry, circuit breakers, timeouts for production reliability
- **Tool Orchestration** - How agents decide which tools to use and when
- **Session Management** - Multi-turn conversations with context management

**More patterns coming soon - [suggest what you want to learn!](https://github.com/timothy-odofin/agenthub-be/issues)**

---

## What You'll Learn & Build With

### ️ **Reusable Design Patterns** ⭐

AgentHub demonstrates patterns you can adopt in **any Python project** (FastAPI, Django, Flask):

#### Type-Safe Configuration System
```yaml
# resources/application-llm.yaml
providers:
openai:
api_key: ${OPENAI_API_KEY} # Environment variable substitution
model: gpt-4
temperature: 0.7
retry:
max_attempts: 3
strategy: exponential
```

```python
# Use in your code - no manual parsing!
from app.core.config import get_settings

settings = get_settings()
api_key = settings.llm.providers.openai.api_key # Type-safe!
```

**Why this matters**: Configuration is hard. This pattern gives you:
- Type safety (catch errors at startup, not runtime)
- Environment-specific configs (dev/staging/prod)
- Hot reload without restarts
- Works with Django, Flask, FastAPI, or any Python app

**[Adopt this pattern in your project →](docs/guides/configuration/README.md)**

---

#### �️ Production Resilience Patterns
```python
from app.core.resilience import retry, circuit_breaker, timeout

@retry(max_attempts=3, backoff=RetryStrategy.EXPONENTIAL)
@circuit_breaker(name="external_api", failure_threshold=5)
@timeout(seconds=30)
async def call_external_api(data: dict):
"""
Automatically retries on failure, stops calling if system is down,
and prevents hanging requests. Copy this pattern to any service!
"""
return await external_api.post("/endpoint", json=data)
```

**Why this matters**: Production systems fail. This pattern handles:
- Automatic retry with exponential backoff
- Circuit breaker prevents cascade failures
- ⏱️ Timeout prevents resource exhaustion
- Built-in monitoring and metrics

**Works with**: Any async Python framework (FastAPI, Sanic, Quart)

**[Learn resilience patterns →](src/app/core/resilience/)**

---

### **Real-World LLM Implementations**

These aren't just features - they're **educational examples** showing how to solve real LLM problems:

#### Conversational Signup (Agent Workflow Example)
```python
# See how agents maintain context and make decisions
POST /api/v1/conversational-auth/message
{
"message": "I want to sign up. My email is user@example.com and name is John",
"session_id": "abc123"
}

# Agent extracts multiple fields, validates, and guides user through 7 steps
# → Study how it works: parsing, validation, state management
```

**What you'll learn**:
- How agents extract structured data from natural language
- Multi-turn conversation state management
- Validation and error recovery
- Real-time progress tracking

**[See the complete implementation →](docs/api-reference/conversational-auth.md)**

---

#### � RAG Pipeline (Complete End-to-End)
```python
# Learn the complete RAG flow: ingest → chunk → embed → store → retrieve → generate

# 1. Ingest documents
POST /api/v1/data-ingestion/load/FILE
{
"files": ["document.pdf"],
"chunk_size": 1000,
"chunk_overlap": 200
}

# 2. Query with context
POST /api/v1/chat/message
{
"message": "What does the document say about pricing?",
"use_rag": true
}

# → See how documents flow through: chunking → embeddings → vector search → context injection
```

**What you'll learn**:
- Document processing and chunking strategies
- Embedding generation and storage
- Semantic search with metadata filtering
- Context injection and generation

**[Understand the complete RAG pipeline →](docs/core-concepts/rag-pipeline.md)**

---

### **LLM Features (Production-Ready)**

Not learning? Just want to build? Everything's production-ready:

- **Multi-Provider Support** - OpenAI, Anthropic, Groq, Azure (swap with config change)
- **RAG System** - Qdrant, ChromaDB, PgVector vector stores
- **Tool Integration** - Jira, GitHub, Confluence, Datadog (extensible)
- **Agent Frameworks** - LangChain, LangGraph with custom agents
- **Session Management** - PostgreSQL + Redis for chat history
- **Background Jobs** - Celery for async document processing
- **Monitoring** - Health checks, structured logging, metrics endpoints

### **Framework-Agnostic Patterns**

Many patterns work in **any Python framework**:

| Pattern | Works With | Location |
|---------|-----------|----------|
| **YAML Configuration** | Django, Flask, FastAPI | `src/app/core/config/` |
| **Resilience (Retry/Circuit Breaker)** | Any async Python | `src/app/core/resilience/` |
| **Connection Manager** | Any database app | `src/app/connections/` |
| **Structured Logging** | Any Python app | `src/app/core/utils/logger.py` |
| **Testing Patterns** | pytest anywhere | `tests/` |

**Copy what you need - it's MIT licensed!**

---

## Quick Start

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
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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

### Multi-Environment Support

AgentHub supports different environment configurations for dev/staging/production:

```bash
# Development (hot reload)
make run-api-dev # Uses .env.dev

# Staging
make run-api-staging # Uses .env.staging

# Production
make run-api-prod # Uses .env.production

# Custom environment file
uvicorn src.app.main:app --env /path/to/.env.custom
```

**Example environment files provided:**
- `.env.dev` - Development with debug enabled
- `.env.staging` - Staging with production-like settings
- `.env.production` - Production with security hardened

**[Multi-Environment Guide →](docs/guides/multi-environment.md)**

**[Full installation guide →](docs/getting-started/quick-start.md)**

---

## Documentation

**[Complete Documentation](docs/)** - Full documentation hub with guides, tutorials, and API reference

### Quick Links by Topic:

- **[Getting Started](docs/getting-started/quick-start.md)** - 5-minute setup
- **[API Reference](docs/api-reference/README.md)** - REST API endpoints
- **[Architecture](docs/architecture/overview.md)** - System design & patterns
- **[Guides](docs/guides/)** - Feature guides (LLM, RAG, Tools, Databases)
- **[Tutorials](docs/tutorials/)** - Step-by-step examples
- **[Deployment](docs/deployment/overview.md)** - Production deployment (AWS, GCP, Azure, K8s)

**New to LLMs?** Start with [LLM Basics](docs/core-concepts/llm-basics.md) and [RAG Pipeline](docs/core-concepts/rag-pipeline.md)

**� Looking for role-based navigation?** See [docs/README.md](docs/) for guides tailored to developers, DevOps, data scientists, and PMs.

---

## Architecture Highlights

### **Modular by Design**

```
┌─────────────────────────────────────────────┐
│ FastAPI API Layer │
│ /chat /health /tools /resilience │
└────────────────┬────────────────────────────┘
│
┌────────────────┴────────────────────────────┐
│ Agent Orchestration │
│ LangChain | LangGraph | Custom Agents │
└────────┬──────────────────┬─────────────────┘
│ │
┌────┴─────┐ ┌────┴──────────┐
│ Tools │ │ RAG Pipeline │
│ Registry│ │ + Vector DB │
└──────────┘ └───────────────┘
│ │
┌────┴──────────────────┴─────────────────┐
│ Connection Manager Layer │
│ Jira | GitHub | Confluence | Datadog │
│ PostgreSQL | MongoDB | Redis | Qdrant │
└─────────────────────────────────────────┘
```

**[Detailed architecture & design patterns →](docs/architecture/overview.md)**

### **Visual Architecture Diagrams**

Explore detailed system diagrams to understand AgentHub's architecture:

- **[System Architecture](docs/architecture/diagrams/AgentHub%20System%20Architecture.svg)** - Complete component view
- **[Request Flow](docs/architecture/diagrams/AgentHub%20Request%20Flow%20with%20Tool%20Orchestration.svg)** - End-to-end request lifecycle
- **[Error Handling](docs/architecture/diagrams/Error%20Handling%20and%20Validation%20Flow.svg)** - Resilience & recovery patterns

**[View all diagrams with explanations →](docs/architecture/overview.md#architecture-diagrams)**

---

## Key Guides

Deep-dive into specific topics:

- **[Configuration System](docs/guides/configuration/README.md)** ⭐ - Type-safe YAML configs (use in any Python project!)
- **[Resilience Patterns](src/app/core/resilience/)** ⭐ - Retry, circuit breakers (production-ready patterns)
- ** [Connections](docs/guides/connections/README.md)** - Database & vector store management
- **[LLM Providers](docs/guides/llm-providers/README.md)** - OpenAI, Anthropic, Groq, Azure
- **[Tools](docs/guides/tools/README.md)** - Jira, GitHub, Confluence integrations
- **[Sessions](docs/guides/sessions/README.md)** - Multi-turn conversation management
- **[Testing Examples](tests/)** - See comprehensive test implementations

**[See all 15+ guides →](docs/guides/)**

---

## Development

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
│ ├── api/ # FastAPI endpoints
│ │ └── v1/ # API version 1
│ ├── agent/ # Agent implementations
│ │ ├── frameworks/ # LangChain, LangGraph
│ │ ├── implementations/
│ │ └── tools/ # Tool integrations
│ ├── connections/ # Connection managers
│ │ ├── database/ # PostgreSQL, MongoDB, Redis
│ │ ├── vector/ # Qdrant, ChromaDB, PgVector
│ │ └── external/ # Jira, GitHub, Confluence
│ ├── core/ # Core functionality
│ │ ├── config/ # Configuration system ⭐
│ │ ├── exceptions/ # Exception hierarchy
│ │ ├── handlers/ # Exception handlers
│ │ ├── resilience/ # Retry, circuit breaker
│ │ └── utils/ # Utilities, logging
│ ├── llm/ # LLM providers
│ │ ├── providers/ # OpenAI, Groq, Anthropic
│ │ └── factory/ # LLM factory
│ ├── services/ # Business logic
│ ├── sessions/ # Session management
│ └── db/ # Database models, repos
│
└── tests/
├── unit/ # Unit tests
├── integration/ # Integration tests
└── e2e/ # End-to-end tests
```

**See project structure in the codebase**

---

## Testing

AgentHub has comprehensive test coverage:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/ # Unit tests only
pytest tests/integration/ # Integration tests
pytest tests/e2e/ # End-to-end tests

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_resilience_patterns.py -v
```

**Current Test Stats**:
- 88 tests passing
- 85%+ coverage
- Fast unit tests (< 1s each)

**[See test examples in tests/ directory →](tests/)**

---

## Deployment

### Quick Start with Docker

```bash
# Build and run everything
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f api
```

### Production Deployment

Deploy to your preferred platform:

- ** [Render](docs/deployment/render-setup.md)** - Zero DevOps, free tier (recommended for MVPs)
- **️ [AWS](docs/deployment/overview.md#aws-amazon-web-services)** - ECS Fargate, Elastic Beanstalk, Lambda
- ** [Google Cloud](docs/deployment/overview.md#google-cloud-platform)** - Cloud Run, GKE
- ** [Azure](docs/deployment/overview.md#microsoft-azure)** - App Service, Container Apps
- **️ [Kubernetes](docs/deployment/overview.md#kubernetes-self-managed)** - Self-managed K8s clusters
- ** [Docker Compose](docs/deployment/overview.md#docker-compose-localdevelopment)** - Local/small deployments

**[Complete deployment guide with costs & CLI commands →](docs/deployment/overview.md)**

---

## Tech Stack

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

## Contributing & Open Innovation

### We Build What You Need

**Have an LLM problem?** We want to solve it!

AgentHub is an **open innovation platform**. If there's an LLM use case you want to learn or a pattern you need, we'll build it together:

- **Need a specific RAG strategy?** (e.g., hybrid search, re-ranking)
- **Want to see a new agent pattern?** (e.g., multi-agent collaboration)
- **Missing a tool integration?** (e.g., Slack, Linear, Notion)
- **Need observability patterns?** (e.g., tracing, cost tracking)
- ️ **Want streaming implementations?** (e.g., SSE, WebSockets)

**[Open an issue](https://github.com/timothy-odofin/agenthub-be/issues/new?template=feature-request.md)** with your use case - we'll prioritize it!

### How to Contribute

We welcome all contributions - code, documentation, ideas:

1. **Code Contributions**
- Fork the repo
- Create feature branch: `git checkout -b feature/amazing-pattern`
- Add tests: `make test`
- Format: `make format`
- Submit PR with clear description

2. **Documentation Contributions**
- Found something unclear? Open a PR
- Want to add examples? We'd love it
- Tutorial ideas? [Propose them here](https://github.com/timothy-odofin/agenthub-be/discussions)

3. **Suggest Problems to Solve**
- What LLM challenges do you face?
- What patterns do you wish existed?
- What would help you learn faster?

**[Open an issue to contribute →](https://github.com/timothy-odofin/agenthub-be/issues)**

### Current Priority Areas

Vote on what you want next! ️

- [ ] � **Multi-Agent Collaboration** - Agents working together on complex tasks
- [ ] **Cost Tracking & Budgets** - Monitor and limit LLM spend
- [ ] **Advanced RAG Patterns** - Hybrid search, re-ranking, query rewriting
- [ ] � **More Tool Integrations** - Slack, Linear, Notion, Discord
- [ ] **Prompt Management** - Version control, A/B testing, optimization
- [ ] **Observability** - OpenTelemetry, distributed tracing, dashboards
- [ ] � **Streaming Improvements** - SSE, WebSockets, real-time updates
- [ ] **Plugin System** - Community-contributed agents and tools

**[Vote on features →](https://github.com/timothy-odofin/agenthub-be/discussions/categories/feature-requests)**

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Why Developers Choose AgentHub

> "Finally, a complete LLM app I can actually learn from. Not just snippets - the whole thing."
> — **Python Developer learning AI**

> "The configuration system alone is worth forking. I copied it to my Django project."
> — **Senior Backend Engineer**

> "Conversational signup showed me how agents actually work. Changed how I think about LLM apps."
> — **ML Engineer**

> "Best part: it's not just 'how to call GPT-4'. It shows resilience, testing, deployment - the whole picture."
> — **Startup CTO**

### What Makes AgentHub Different

| Other Resources | AgentHub |
|-----------------|----------|
| Tutorial snippets | Complete, production-ready app |
| "Hello World" demos | Real features you can fork and use |
| "Figure out production yourself" | Deployment guides for 6+ platforms |
| Closed-source examples | MIT licensed - copy anything |
| Isolated concepts | See how everything fits together |
| Just documentation | Working code + "why" not just "how" |

---

## About the Project

### Why AgentHub Exists

AgentHub was created to solve a critical gap in the AI development ecosystem: **most resources show isolated concepts, but it's rare to find well-structured, production-ready AI/ML systems that teams can actually learn from and deploy.**

The mission is simple: **make enterprise-grade AI accessible to everyone** by providing:

- **For Developers**: A complete, real-world LLM application to study, learn from, and adopt patterns
- **For Organizations**: A production-ready RAG system you can deploy with just configuration changes - no coding required
- **For Startups**: Enterprise-grade AI foundation you can launch in hours, not months
- **For Teams**: Battle-tested architecture and patterns you can trust in production
- **For Learners**: Educational platform to understand how real AI systems work end-to-end

### What Makes AgentHub Different

**Zero-Code Deployment for Non-Technical Teams:**
- Clone the repo, update configuration files (YAML), and deploy
- Add your API keys, configure your data sources, customize tools
- Production-ready AI agent without writing a single line of code

**Full-Stack Learning for Developers:**
- See how configuration, resilience, testing, and deployment work together
- Adopt proven patterns into your existing projects (FastAPI, Django, Flask, etc.)
- Learn by exploring working, production-quality code

**Enterprise-Ready for Organizations:**
- Multi-LLM support with easy provider switching
- Advanced RAG with multiple vector databases
- Built-in resilience patterns, caching, monitoring
- Security, scalability, and observability built-in

### Project Philosophy

AgentHub isn't just about code - it's about **making AI accessible to everyone**:

- **Deploy Without Coding**: Organizations can launch AI agents with configuration-only changes
- **Learn by Doing**: Developers can study complete, production-ready implementations
- **Production-First**: Real patterns you can trust in production, not just demos
- **Open & Collaborative**: Community-driven development with transparent roadmap
- **Barrier-Free Access**: No one should struggle to deploy AI or find quality learning resources

### Community-Driven Development

This project grows based on what the community needs:

- 💡 **Request Features**: Tell us what integrations or capabilities you need
- 🔧 **Contribute Code**: PRs welcome - from typos to major features
- 📚 **Share Knowledge**: Help others deploy and learn through discussions
- 🎯 **Adopt Patterns**: Use our design patterns in your own projects
- 🚀 **Deploy & Share**: Tell us about your use cases and success stories

### Use Cases Across Industries

**Organizations & Enterprises:**
- Customer support automation with knowledge base integration
- Internal knowledge management (Confluence, Jira, GitHub)
- DevOps automation and monitoring
- Document Q&A and analysis

**Startups:**
- Launch AI-powered products without AI expertise
- Rapid prototyping with production-quality foundation
- Cost-effective multi-LLM support
- Scale from MVP to enterprise

**Developers & Teams:**
- Learn production AI patterns and architectures
- Adopt configuration systems, resilience patterns, caching strategies
- Build custom AI tools and integrations
- Reference architecture for internal platforms

### Project Origins

AgentHub started from a clear observation: after years of training engineers and working with organizations worldwide, it became evident that **accessible, production-quality AI resources are rare**. Most tutorials teach concepts, but few show how to actually deploy and scale AI systems.

The project embodies the belief that **barriers to AI adoption shouldn't exist** - whether you're a developer learning, a startup launching, or an enterprise deploying at scale.

## Contributors

AgentHub is built and maintained by developers who believe in open-source education.

### Core Team

- **[Timothy Oyejide Odofin](https://github.com/timothy-odofin)** - Project Creator & Lead Maintainer
  - 16+ years software engineering across Finance, Healthcare, Education, Telecom, Agriculture, Banking
  - Full-stack expertise: Python, Java, React, Angular, Cloud Architecture
  - Passionate about making AI development accessible

### How to Become a Contributor

We welcome contributions of all sizes! Check out our [CONTRIBUTING.md](CONTRIBUTING.md) guide to get started.

**Notable Contributors:**
- Your name could be here! [Make your first contribution →](CONTRIBUTING.md)

**All Contributors:**
- See the full list on our [Contributors page](https://github.com/timothy-odofin/agenthub-be/graphs/contributors)

### Recognition

Contributors are recognized through:
- Credits in release notes
- Mentions in documentation
- GitHub contributor badge
- Community appreciation 🙏

**[Become a contributor today! →](CONTRIBUTING.md)**

---

## Acknowledgments

Built with ❤️ using these amazing open source projects:

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [LangChain](https://python.langchain.com/) - LLM application framework
- [Qdrant](https://qdrant.tech/) - Vector database
- [PostgreSQL](https://www.postgresql.org/) - Relational database
- [Redis](https://redis.io/) - In-memory data store
- And many more in [requirements.txt](requirements.txt)

**Special thanks** to every developer who asked "how does this *really* work in production?" Your questions drive this project forward.

---

## Support & Community

- 📖 **Documentation**: [docs/](docs/)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/timothy-odofin/agenthub-be/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/timothy-odofin/agenthub-be/discussions)
- 💡 **Feature Requests**: [Propose new patterns](https://github.com/timothy-odofin/agenthub-be/issues/new?template=feature-request.md)
- ❓ **Questions**: [Ask anything](https://github.com/timothy-odofin/agenthub-be/discussions/categories/q-a)
- 🤝 **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)

**No question is too basic.** We're here to help you learn and build.

**Want to connect with the maintainers?**
- Reach out via [GitHub Discussions](https://github.com/timothy-odofin/agenthub-be/discussions)
- Follow project updates on the repository

---

<div align="center">

### ⭐ If AgentHub helps you learn or build, please star this repo! ⭐

**Your stars help others discover these patterns**

---

**Made with ❤️ and ☕ by developers, for developers**

*Building the LLM applications the community needs, one pattern at a time*

---

**[Get Started](docs/getting-started/quick-start.md)** | **[Read the Docs](docs/)** | **[Suggest a Feature](https://github.com/timothy-odofin/agenthub-be/issues/new)** | **[Open an Issue](https://github.com/timothy-odofin/agenthub-be/issues)**

</div>
