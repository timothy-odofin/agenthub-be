# Architecture Overview

## Table of Contents
- [System Architecture](#system-architecture)
- [Architecture Diagrams](#architecture-diagrams)
- [Core Components](#core-components)
- [Technology Stack](#technology-stack)
- [Design Philosophy](#design-philosophy)
- [Component Interaction](#component-interaction)
- [Data Flow](#data-flow)

---

## System Architecture

AgentHub follows a **modular, layered architecture** designed for flexibility, maintainability, and scalability. The system is built around the principle of **separation of concerns** with clear boundaries between layers.

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │   REST APIs  │  │  WebSockets  │  │  Health Endpoints  │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                        Service Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │ Agent Service│  │ Session Mgmt │  │  External Services │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                     Core Components Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  LLM Factory │  │  Tool System │  │  Agent Framework   │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────┐    │
│  │  PostgreSQL  │  │   MongoDB    │  │      Redis         │    │
│  └──────────────┘  └──────────────┘  └────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Diagrams

AgentHub provides detailed visual diagrams to help you understand the system architecture and request flows. All diagrams are available in the `diagrams/` directory in both PlantUML source format (`.puml`) and rendered SVG format.

### 📊 Available Diagrams

#### 1. [System Architecture](diagrams/AgentHub%20System%20Architecture.svg)

**High-level component view** showing all major system components and their relationships.

**What it shows:**
- Client applications (React/Angular, Swagger, Mobile)
- API Gateway layer (FastAPI, middlewares)
- Service layer (Chat, Agent, Ingestion, Session)
- Agent framework (Factory, Registry, Agents)
- LLM providers (OpenAI, Groq, Anthropic, Azure)
- Tool orchestration (Registry, Executor, Tools)
- Core infrastructure (Config, Context Manager, Resilience)
- Data storage (PostgreSQL, MongoDB, Redis)
- Background workers (Celery)
- External services (Atlassian, Datadog, GitHub)

**Use this diagram to:**
- Understand the overall system structure
- See how components interact
- Identify integration points
- Plan new features

**Source:** [`diagrams/system-architecture.puml`](diagrams/system-architecture.puml)

---

#### 2. [Request Flow Sequence](diagrams/AgentHub%20Request%20Flow%20with%20Tool%20Orchestration.svg)

**Detailed sequence diagram** showing the complete flow of a user request with LLM tool orchestration.

**What it shows - 8 Phases:**
1. **Request Reception & Validation** - Client → API → Validation → Auth
2. **Session Management** - Load conversation context from MongoDB
3. **Agent Initialization** - Factory creates agent with tools
4. **Agent Reasoning** - First LLM call (tool selection)
5. **Tool Execution** - Execute Jira tool, get results
6. **Response Generation** - Second LLM call (format response)
7. **Response Processing** - Save to MongoDB, cache in Redis
8. **Response Delivery** - Return to client

**Key concepts illustrated:**
- **Two LLM Calls**: First to decide tools, second to generate response
- **LLM Decides Tools**: Not hardcoded, based on context and reasoning
- **Tool Results → LLM**: Tools provide structured data, LLM formats it for users
- **Graceful Failures**: Retry logic, fallback responses if tools fail
- **Session Continuity**: Full conversation context maintained

**Real example flow:**
```
User: "Show me open bugs in PROJ-123"
  ↓
1. Validate request, authenticate user
2. Load session history
3. Create ReAct agent with [Jira, Datadog, Vector] tools
4. LLM analyzes request → decides to use jira_search_issues
5. Execute Jira tool → returns 3 bugs
6. LLM formats response → numbered list with details
7. Save to MongoDB, cache in Redis
8. Return to user with follow-up suggestions
```

**Use this diagram to:**
- Understand the complete request lifecycle
- See how LLMs decide tool usage
- Debug flow issues
- Optimize performance bottlenecks

**Source:** [`diagrams/request-flow-sequence.puml`](diagrams/request-flow-sequence.puml)

---

#### 3. [Error Handling and Validation Flow](diagrams/Error%20Handling%20and%20Validation%20Flow.svg)

**Error scenarios and recovery strategies** showing how AgentHub handles different types of failures.

**What it shows - 6 Scenarios:**

1. **Request Validation Error (422)**
   - Invalid request format
   - Missing required fields
   - Early rejection at API layer
   - Detailed field-level errors

2. **Authentication Error (401)**
   - Invalid JWT token
   - Expired token
   - User not found
   - Clear user guidance

3. **LLM Provider Error with Retry**
   - Rate limit exceeded
   - Retry with exponential backoff (2s, 4s, 8s)
   - Circuit breaker monitoring
   - Transparent to user

4. **Tool Execution Error**
   - Jira API unavailable
   - LLM-generated fallback response
   - Graceful degradation
   - User informed clearly

5. **Circuit Breaker Protection**
   - Provider blocked after 5 failures
   - Automatic failover to backup provider
   - User doesn't experience failure
   - Groq → OpenAI fallback example

6. **Unhandled Exception (500)**
   - Programming bugs
   - Sanitized error responses (no stack traces)
   - Unique error IDs for tracking
   - Full logging for debugging
   - Monitoring alerts

**Use this diagram to:**
- Understand error handling strategy
- Design resilience patterns
- Debug production issues
- Plan for failure scenarios

**Source:** [`diagrams/error-handling-flow.puml`](diagrams/error-handling-flow.puml)

---

### 🖼️ Viewing the Diagrams

#### Option 1: VS Code Extension (Recommended)

1. Install [PlantUML extension](https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml)
2. Install Java (required for PlantUML)
3. Open any `.puml` file in the `diagrams/` directory
4. Press `Alt+D` to preview

#### Option 2: View Pre-rendered SVG Files

Simply open the SVG files in the `diagrams/` directory:
- `AgentHub System Architecture.svg`
- `AgentHub Request Flow with Tool Orchestration.svg`
- `Error Handling and Validation Flow.svg`

#### Option 3: PlantUML Online

1. Copy the content from any `.puml` file
2. Go to [PlantUML Online](http://www.plantuml.com/plantuml/uml/)
3. Paste and view

#### Option 4: Command Line

```bash
# Install PlantUML
brew install plantuml  # macOS

# Generate PNG
plantuml docs/architecture/diagrams/system-architecture.puml

# Generate SVG (better quality)
plantuml -tsvg docs/architecture/diagrams/system-architecture.puml

# Generate all diagrams
plantuml docs/architecture/diagrams/*.puml
```

#### Option 5: Docker

```bash
# Generate all diagrams as PNG
docker run --rm -v $(pwd):/data plantuml/plantuml:latest \
  docs/architecture/diagrams/*.puml

# Generate as SVG
docker run --rm -v $(pwd):/data plantuml/plantuml:latest \
  -tsvg docs/architecture/diagrams/*.puml
```

---

### 📝 When to Update Diagrams

Update these diagrams when:
- Adding new components (services, agents, tools)
- Changing request flow
- Adding/modifying error handling
- Making significant architectural changes
- Adding new integration points

---

### 💡 Tips for Using Diagrams

**System Architecture:**
- Start from top (User) and follow arrows down
- Colors represent different layers
- Dotted lines = configuration/dependency
- Solid lines = data flow

**Request Flow Sequence:**
- Read top to bottom, left to right
- Colored boxes = phases of execution
- Activation bars = component active
- Return arrows = responses
- Alt boxes = alternative scenarios

**Error Handling:**
- Each group = one error scenario
- Red/pink = failure paths
- Green/blue = recovery paths
- Notes explain the "why"

---

### 🔍 Real-World Scenario Examples

**Scenario 1: Adding a New Tool** (e.g., GitHub tool)
1. Update **System Architecture**: Add new tool component to "Tools" section
2. Update **Request Flow**: Add tool execution example
3. Update **Error Handling**: Add tool-specific error scenario

**Scenario 2: Adding New LLM Provider** (e.g., Google Gemini)
1. Update **System Architecture**: Add to "LLM Providers" section
2. Update **Request Flow**: Update LLM call examples
3. Update **Error Handling**: Add provider-specific error handling

**Scenario 3: New Authentication Method** (e.g., OAuth)
1. Update **System Architecture**: Modify "API Gateway Layer"
2. Update **Request Flow**: Update authentication phase
3. Update **Error Handling**: Add OAuth-specific error scenarios

---

## Core Components

### 1. **Configuration System** ⭐

The heart of AgentHub's flexibility is its **YAML-based configuration system** with type safety and profile management.

**Key Features:**
- **Type-Safe**: Pydantic models ensure configuration validity
- **Profile-Based**: Support for dev, test, prod environments
- **Hot Reloadable**: Changes can be applied without restart
- **Validation**: Comprehensive validation before startup
- **Modular**: Split across multiple YAML files by concern

**Configuration Files:**
```
resources/
├── application-app.yaml           # Application settings
├── application-context.yaml       # Context window configuration
├── application-data-sources.yaml  # Database connections
├── application-db.yaml            # Database settings
├── application-embeddings.yaml    # Embedding configuration
├── application-external.yaml      # External services (Jira, Confluence)
├── application-llm.yaml           # LLM provider configuration
├── application-prompt.yaml        # Prompt templates
└── application-vector.yaml        # Vector store settings
```

**Example:**
```python
from src.app.core.config import get_settings

settings = get_settings()
print(settings.llm.openai.api_key)  # Type-safe access
```

### 2. **LLM Factory Pattern**

Unified interface for multiple LLM providers with runtime provider switching.

**Supported Providers:**
- OpenAI (GPT-4, GPT-3.5)
- Azure OpenAI
- Anthropic (Claude)
- Google (Gemini)
- Open-source models (via LiteLLM)

**Features:**
- **Provider Agnostic**: Same interface for all LLMs
- **Runtime Switching**: Change providers without code changes
- **Fallback Support**: Automatic failover to backup providers
- **Cost Tracking**: Built-in token usage monitoring
- **Rate Limiting**: Respects provider limits

**Example:**
```python
from src.app.llm.factory import LLMFactory

# Get LLM instance for any provider
llm = LLMFactory.create_llm(
    provider="openai",
    model="gpt-4",
    temperature=0.7
)

response = await llm.generate("Explain RAG")
```

### 3. **Agent Framework**

Flexible agent system supporting multiple frameworks and execution patterns.

**Supported Frameworks:**
- LangChain
- LlamaIndex
- Custom implementations

**Agent Types:**
- Conversational agents
- Tool-using agents
- RAG agents
- Multi-agent systems

**Features:**
- **Tool Integration**: Easy tool registration and discovery
- **Memory Management**: Short-term and long-term memory
- **State Management**: Persistent conversation state
- **Error Recovery**: Graceful handling of failures

### 4. **Tool System**

Extensible tool system for agent capabilities with dynamic registration.

**Built-in Tools:**
- **Jira Integration**: Create/update issues, search, transitions
- **Confluence Integration**: Search, create/update pages
- **Datadog Integration**: Metrics, logs, monitors, dashboards
- **Database Tools**: Query execution, schema inspection
- **File Operations**: Read, write, search files
- **Web Search**: Internet search capabilities

**Tool Registration:**
```python
from src.app.agent.tools import tool_registry

@tool_registry.register("custom_tool")
async def my_custom_tool(param: str) -> str:
    """Tool description for LLM."""
    return f"Result: {param}"
```

### 5. **Session Management**

Robust session management with multiple storage backends.

**Features:**
- **Multiple Backends**: MongoDB, Redis, in-memory
- **Session Persistence**: Conversation history and state
- **Context Window Management**: Automatic token management
- **Session Recovery**: Resume interrupted conversations
- **Expiration Policies**: Configurable TTL

**Storage Options:**
```python
# MongoDB for persistent sessions
session_manager = MongoDBSessionManager()

# Redis for high-performance caching
session_manager = RedisSessionManager()
```

### 6. **External Service Connectors**

Pre-built connectors for popular enterprise tools.

**Supported Services:**
- **Atlassian**: Jira, Confluence
- **Monitoring**: Datadog, Prometheus
- **Databases**: PostgreSQL, MongoDB
- **Vector Stores**: Pinecone, Weaviate, Qdrant

**Connection Pool Management:**
- Automatic connection pooling
- Health checks
- Retry with exponential backoff
- Circuit breaker pattern

---

## Technology Stack

### **API Layer**
| Technology | Purpose | Why? |
|------------|---------|------|
| FastAPI | Web framework | Modern, async, automatic OpenAPI docs |
| Pydantic | Data validation | Type safety, serialization |
| WebSockets | Real-time communication | Streaming responses |

### **LLM Layer**
| Technology | Purpose | Why? |
|------------|---------|------|
| OpenAI SDK | GPT models | Industry standard |
| LangChain | Agent framework | Rich ecosystem |
| LlamaIndex | RAG framework | Specialized for retrieval |
| LiteLLM | Unified interface | Multi-provider support |

### **Data Layer**
| Technology | Purpose | Why? |
|------------|---------|------|
| PostgreSQL | Relational data | ACID compliance |
| MongoDB | Document store | Flexible schema for sessions |
| Redis | Caching | High-performance, pub/sub |

### **Infrastructure**
| Technology | Purpose | Why? |
|------------|---------|------|
| Docker | Containerization | Consistent environments |
| Docker Compose | Orchestration | Local development |
| Kubernetes | Production orchestration | Scalability |

---

## Design Philosophy

### 1. **Configuration Over Code**

Instead of hardcoding values, AgentHub uses configuration files for all settings. This enables:
- **Environment-specific configs**: Dev, test, prod
- **Runtime changes**: Update without redeployment
- **A/B testing**: Easy experimentation
- **Security**: Secrets in environment variables

### 2. **Modularity**

Every component is designed to be:
- **Replaceable**: Swap implementations easily
- **Testable**: Unit test in isolation
- **Reusable**: Use components independently
- **Extensible**: Add features without modifications

### 3. **Fail-Safe Design**

Built with production resilience in mind:
- **Circuit breakers**: Prevent cascade failures
- **Retry logic**: Automatic recovery from transient errors
- **Graceful degradation**: Partial functionality on failures
- **Comprehensive logging**: Debug issues quickly

### 4. **Developer Experience**

Code is written for humans:
- **Type hints**: Full type coverage
- **Documentation**: Inline comments and docstrings
- **Examples**: Working code in `/examples`
- **Error messages**: Clear, actionable feedback

---

## Component Interaction

### Example: Chat Request Flow

```
1. Client Request
   ↓
2. API Layer (FastAPI endpoint)
   ↓
3. Request Validation (Pydantic)
   ↓
4. Service Layer (AgentService)
   ↓
5. Session Manager (load conversation history)
   ↓
6. LLM Factory (get configured LLM)
   ↓
7. Agent Framework (process with tools)
   ↓
8. Tool Execution (if needed - Jira, Datadog, etc.)
   ↓
9. LLM Generation (call provider API)
   ↓
10. Response Processing (format, validate)
    ↓
11. Session Update (save history)
    ↓
12. Client Response (WebSocket or REST)
```

### Example: RAG Query Flow

```
1. User Query
   ↓
2. Query Analysis (intent detection)
   ↓
3. Embedding Generation (text → vector)
   ↓
4. Vector Search (find relevant docs)
   ↓
5. Context Retrieval (fetch document chunks)
   ↓
6. Context Window Management (fit within token limit)
   ↓
7. Prompt Construction (query + context)
   ↓
8. LLM Generation (answer synthesis)
   ↓
9. Citation Addition (link to sources)
   ↓
10. Response Delivery
```

---

## Data Flow

### Session Data Flow

```
┌──────────────┐
│   Client     │
└──────┬───────┘
       │
       ↓
┌──────────────────────────────────────┐
│  FastAPI Endpoint                    │
│  - Authenticate                      │
│  - Validate request                  │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Session Manager                     │
│  - Load session                      │
│  - Check context window              │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│  MongoDB/Redis                       │
│  - Retrieve conversation history     │
│  - Get user preferences              │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Agent Service                       │
│  - Process with context              │
│  - Execute tools if needed           │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│  LLM Provider                        │
│  - Generate response                 │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│  Session Manager                     │
│  - Update conversation history       │
│  - Save to storage                   │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────┐
│   Client     │
└──────────────┘
```

---

## Key Design Patterns

AgentHub leverages multiple design patterns for maintainability and extensibility. Each pattern is documented in detail in [Design Patterns](./design-patterns.md).

**Patterns Used:**
- **Registry Pattern**: Dynamic tool and provider registration
- **Factory Pattern**: LLM and service instantiation
- **Singleton Pattern**: Configuration and connection management
- **Strategy Pattern**: Pluggable algorithms (embeddings, chunking)
- **Decorator Pattern**: Middleware, caching, monitoring
- **Template Method**: Agent execution flow
- **Observer Pattern**: Event-driven notifications

---

## Scalability Considerations

### Horizontal Scaling

**Stateless API Layer:**
- API endpoints are stateless
- Session state in external storage (MongoDB/Redis)
- Load balance across multiple instances
- No sticky sessions required

**Worker Separation:**
- Long-running tasks in separate workers
- Queue-based job processing
- Independent scaling of workers

### Vertical Scaling

**Resource Management:**
- Connection pooling for databases
- Token bucket rate limiting
- Memory-efficient streaming
- Async I/O throughout

### Caching Strategy

**Multi-Layer Caching:**
```
Redis (hot cache)
    ↓
MongoDB (warm cache)
    ↓
PostgreSQL (cold storage)
```

---

## Monitoring & Observability

### Built-in Monitoring

**Metrics Collected:**
- Request latency (p50, p95, p99)
- Error rates
- Token usage
- Cache hit rates
- Database query times

**Logging Levels:**
- **DEBUG**: Development troubleshooting
- **INFO**: Normal operations
- **WARNING**: Recoverable issues
- **ERROR**: Application errors
- **CRITICAL**: System failures

**Integration Points:**
- Datadog for metrics and traces
- Structured JSON logging
- Health check endpoints
- OpenTelemetry support

---

## Security Architecture

### Authentication & Authorization

**Supported Methods:**
- API key authentication
- JWT tokens
- OAuth 2.0 integration
- Conversational signup (demo feature)

### Data Protection

**In Transit:**
- TLS/HTTPS for all endpoints
- Encrypted WebSocket connections

**At Rest:**
- Encrypted database connections
- Secret management via environment variables
- Sensitive data hashing

### Rate Limiting

**Protection Against Abuse:**
- Per-user rate limits
- Per-IP rate limits
- Token bucket algorithm
- Configurable limits per environment

---

## Configuration Management

### Environment Profiles

```yaml
# application-app.yaml
app:
  name: "agenthub"
  version: "1.0.0"
  environment: "${APP_ENV:dev}"  # dev, test, prod
  
  profiles:
    dev:
      debug: true
      reload: true
    prod:
      debug: false
      workers: 4
```

### Secret Management

**Best Practices:**
- Secrets in environment variables only
- Never commit secrets to git
- Use `.env.example` for documentation
- Rotate secrets regularly

**Example:**
```bash
# .env
OPENAI_API_KEY=sk-xxx
DATABASE_URL=postgresql://user:pass@localhost/db
```

---

## Testing Strategy

### Test Pyramid

```
           ┌────────────┐
          /    E2E       \      (10%)
         ├────────────────┤
        /   Integration    \    (30%)
       ├────────────────────┤
      /      Unit Tests      \  (60%)
     └────────────────────────┘
```

**Test Coverage:**
- Unit tests: 88+ tests for core logic
- Integration tests: Database, external services
- E2E tests: Full workflow validation

**Test Organization:**
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Database, API tests
└── e2e/           # Full system tests
```

---

## Deployment Architecture

### Development Environment

```
Docker Compose
├── FastAPI (port 8000)
├── PostgreSQL (port 5432)
├── MongoDB (port 27017)
├── Redis (port 6379)
└── pgAdmin (port 5050)
```

### Production Environment

```
Kubernetes Cluster
├── API Pods (3+ replicas)
├── Worker Pods (autoscaling)
├── PostgreSQL (managed service)
├── MongoDB (managed service)
├── Redis (managed service)
└── Load Balancer
```

---

## Performance Characteristics

### Typical Response Times

| Operation | Latency | Notes |
|-----------|---------|-------|
| Simple chat | 500-1000ms | Without tools |
| RAG query | 1-2s | Includes vector search |
| Tool execution | 2-5s | Depends on external API |
| Session load | 50-100ms | From Redis |

### Throughput

| Metric | Value | Notes |
|--------|-------|-------|
| Requests/sec | 100-500 | Single instance |
| Concurrent users | 1000+ | With horizontal scaling |
| WebSocket connections | 10,000+ | With proper tuning |

---

## Future Architecture Considerations

### Planned Enhancements

1. **Event Sourcing**: Full audit trail of all operations
2. **CQRS**: Separate read/write models for scalability
3. **Microservices**: Split into smaller, independent services
4. **GraphQL**: Alternative API layer for complex queries
5. **gRPC**: High-performance internal communication

### Extensibility Points

**Current Extension Mechanisms:**
- Tool registration system
- Custom LLM providers
- Agent framework plugins
- Middleware system
- Custom storage backends

---

## Related Documentation

- **[Design Patterns](./design-patterns.md)**: Detailed pattern implementations
- **[Configuration System](./configuration-system.md)**: In-depth configuration guide
- **[LLM Basics](../core-concepts/llm-basics.md)**: Understanding language models
- **[Deployment Guide](../deployment/overview.md)**: Production deployment

---

## Questions?

- **Architecture decisions**: See [ADR documentation](../reference/adr/)
- **Code examples**: Check [Design Patterns](./design-patterns.md) for working implementations
- **API reference**: See [API Documentation](../api-reference/)
- **Contributing**: Read [Contributing Guide](../contributing/README.md)

---

**Last Updated**: January 8, 2026  
**Maintainer**: AgentHub Team  
**Status**: ✅ Production-ready
