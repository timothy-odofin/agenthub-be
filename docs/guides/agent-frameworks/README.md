# Agent Frameworks Guide

This guide covers the different agent frameworks used in AgentHub and how to implement custom agents.

## Overview

AgentHub supports multiple agent frameworks to give you flexibility in building LLM-powered agents:

- **LangChain Agents** - Full-featured agent framework with extensive tooling
- **LangGraph Agents** - Graph-based agent workflows for complex orchestration
- **Custom Agents** - Build your own agent implementations

## Available Agent Implementations

### 1. LangChain ReAct Agent

**Location:** `src/app/agent/implementations/langchain_react_agent.py`

ReAct (Reasoning + Acting) agents alternate between thinking and taking actions to solve tasks.

**When to use:**
- Simple, straightforward task execution
- Single-step or few-step problems
- Clear reasoning needed for decisions

**Example:**
```python
from app.agent.implementations.langchain_react_agent import LangchainReactAgent

agent = LangchainReactAgent()
response = await agent.run("Search for the latest Python trends")
```

### 2. LangGraph Agents

**Location:** 
- `src/app/agent/frameworks/langgraph_agent.py`
- `src/app/agent/implementations/langgraph_react_agent.py`

LangGraph enables graph-based agent workflows with complex state management and branching logic.

**When to use:**
- Multi-step workflows with conditional logic
- Complex state management across steps
- Parallel tool execution
- Cyclic workflows (agents that iterate)

**Example:**
```python
from app.agent.implementations.langgraph_react_agent import LanggraphReactAgent

agent = LanggraphReactAgent()
response = await agent.run("Complex multi-step task")
```

## Agent Components

### Tools Registry

Agents can access tools registered in the system:

**Location:** `src/app/agent/tools/`

Available tool categories:
- **Jira Tools** - Issue tracking and project management
- **GitHub Tools** - Repository operations
- **Confluence Tools** - Documentation management
- **Datadog Tools** - Monitoring and observability
- **Web Tools** - Web scraping and content extraction

### Tool Configuration

Tools are configured via YAML:

```yaml
# resources/application-tools.yaml
tools:
  jira:
    enabled: true
    server: "https://your-domain.atlassian.net"
  github:
    enabled: true
    token: ${GITHUB_TOKEN}
```

## Creating Custom Agents

### Base Agent Interface

All agents should implement the base agent interface:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAgent(ABC):
    """Base interface for all agent implementations."""
    
    @abstractmethod
    async def run(
        self,
        message: str,
        context: Dict[str, Any] = None,
        tools: List[str] = None
    ) -> str:
        """Execute agent with given message and context."""
        pass
    
    @abstractmethod
    async def stream(
        self,
        message: str,
        context: Dict[str, Any] = None
    ):
        """Stream agent responses."""
        pass
```

### Example Custom Agent

```python
from app.agent.base import BaseAgent
from app.core.utils.logger import get_logger

logger = get_logger(__name__)

class CustomAgent(BaseAgent):
    """Your custom agent implementation."""
    
    def __init__(self):
        self.llm = get_llm()  # Get configured LLM
        self.tools = get_tools()  # Get available tools
    
    async def run(
        self,
        message: str,
        context: Dict[str, Any] = None,
        tools: List[str] = None
    ) -> str:
        """Custom agent logic here."""
        
        # 1. Analyze the message
        intent = await self._analyze_intent(message)
        
        # 2. Select appropriate tools
        selected_tools = self._select_tools(intent, tools)
        
        # 3. Execute with LLM
        response = await self.llm.generate(
            prompt=message,
            context=context,
            tools=selected_tools
        )
        
        return response
    
    async def stream(self, message: str, context: Dict[str, Any] = None):
        """Implement streaming if needed."""
        async for chunk in self.llm.stream(message, context):
            yield chunk
```

## Agent Selection Strategy

AgentHub automatically selects the best agent for your use case:

1. **Simple queries** → LangChain ReAct Agent
2. **Complex workflows** → LangGraph Agent
3. **Custom requirements** → Your custom agent

You can also explicitly specify the agent:

```python
# In your API request
POST /api/v1/chat/message
{
  "message": "Your query",
  "agent_type": "langgraph",  # or "langchain", "custom"
  "session_id": "abc123"
}
```

## Advanced Topics

### Agent Memory

Agents maintain conversation history through sessions:

```python
from app.sessions import get_session_manager

session_manager = get_session_manager()
history = await session_manager.get_history(session_id)
```

See [Session Management Guide](../sessions/README.md) for details.

### Agent Resilience

Agents inherit resilience patterns from the system:

- **Retry Logic** - Automatic retry on LLM failures
- **Circuit Breakers** - Prevent cascade failures
- **Timeouts** - Prevent hanging operations

See [Resilience Patterns](../../core/resilience/) for implementation details.

### Tool Orchestration

Agents can orchestrate multiple tools in sequence or parallel:

```python
# Sequential execution
result1 = await agent.use_tool("jira", action="search")
result2 = await agent.use_tool("github", action="create_issue", data=result1)

# Parallel execution (LangGraph)
results = await agent.use_tools_parallel([
    ("jira", {"action": "search"}),
    ("github", {"action": "search"})
])
```

## Testing Agents

### Unit Testing

```python
import pytest
from app.agent.implementations.langchain_react_agent import LangchainReactAgent

@pytest.mark.asyncio
async def test_agent_simple_query():
    agent = LangchainReactAgent()
    response = await agent.run("What is 2+2?")
    assert "4" in response
```

### Integration Testing

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_with_tools():
    agent = LangchainReactAgent()
    response = await agent.run(
        "Search Jira for open bugs",
        tools=["jira"]
    )
    assert response is not None
```

See [test examples](../../../tests/unit/test_agents.py) for more patterns.

## Configuration

### Agent Configuration

Configure agents via `resources/application-app.yaml`:

```yaml
agent:
  default_type: "langchain"  # Default agent to use
  timeout: 60  # Agent execution timeout
  max_iterations: 5  # Max reasoning steps
  
  langchain:
    verbose: true
    max_tokens: 2000
  
  langgraph:
    max_nodes: 10
    parallel_execution: true
```

### LLM Configuration

Agents use the system-wide LLM configuration:

```yaml
# resources/application-llm.yaml
llm:
  default_provider: "openai"
  providers:
    openai:
      model: "gpt-4"
      temperature: 0.7
```

See [LLM Providers Guide](../llm-providers/README.md) for details.

## Performance Considerations

### Response Time

- **LangChain ReAct**: ~2-5 seconds
- **LangGraph**: ~3-10 seconds (depends on workflow complexity)
- **Custom agents**: Varies

### Token Usage

Monitor token usage to control costs:

```python
from app.core.monitoring import track_tokens

@track_tokens
async def run_agent(message: str):
    response = await agent.run(message)
    return response
```

### Caching

Enable caching for repeated queries:

```yaml
cache:
  enabled: true
  ttl: 3600  # 1 hour
  strategy: "semantic"  # Cache similar questions
```

See [Cache Service Guide](../redis-cache-service.md) for details.

## Common Patterns

### 1. Multi-Tool Workflows

```python
async def complex_workflow(query: str):
    # Step 1: Search for information
    search_result = await agent.use_tool("web_search", {"query": query})
    
    # Step 2: Create Jira issue with findings
    issue = await agent.use_tool("jira", {
        "action": "create",
        "data": search_result
    })
    
    # Step 3: Notify team
    await agent.use_tool("slack", {
        "action": "notify",
        "message": f"Created issue: {issue['key']}"
    })
```

### 2. Conditional Logic

```python
response = await agent.run(
    "Analyze this data and take action if needed",
    context={"data": data}
)

if "ERROR" in response:
    # Handle error case
    await agent.run("Create an incident report")
else:
    # Handle success case
    await agent.run("Send summary to stakeholders")
```

### 3. Iterative Refinement

```python
result = await agent.run("Research topic X")

# Agent can iterate to improve response
for _ in range(max_iterations):
    if is_satisfactory(result):
        break
    result = await agent.run(
        f"Improve this response: {result}",
        context={"previous": result}
    )
```

## Troubleshooting

### Agent Not Responding

1. Check LLM provider availability
2. Verify tool configurations
3. Check timeout settings
4. Review logs: `logs/*.log`

### Tools Not Working

1. Verify tool credentials in `.env`
2. Check tool configuration in YAML
3. Test tool connection independently
4. Review circuit breaker status: `/api/v1/resilience/circuit-breakers`

### Slow Performance

1. Reduce `max_iterations`
2. Use simpler agent (LangChain vs LangGraph)
3. Enable caching
4. Use streaming for better UX
5. Reduce tool count in single call

## Resources

- **[LangChain Documentation](https://python.langchain.com/)**
- **[LangGraph Documentation](https://langchain-ai.github.io/langgraph/)**
- **[Agent Code Examples](../../../src/app/agent/)**
- **[Test Examples](../../../tests/unit/test_agents.py)**
- **[API Reference](../../api-reference/chat.md)**

## Next Steps

1. **[Try the Quick Start](../../getting-started/quick-start.md)** - Get agents running
2. **[Explore Tools](../tools/README.md)** - See available tool integrations
3. **[Configure LLMs](../llm-providers/README.md)** - Set up your preferred provider
4. **[Test Your Agents](../../../tests/)** - Learn testing patterns

---

**Questions or suggestions?** [Open an issue](https://github.com/timothy-odofin/agenthub-be/issues) or check the [main documentation](../../README.md).
