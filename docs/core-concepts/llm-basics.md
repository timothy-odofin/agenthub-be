# LLM Basics: Understanding Large Language Models

> **Beginner-Friendly Guide**: This document explains LLMs in simple terms. No prior AI/ML knowledge required!

## Table of Contents
- [What is an LLM?](#what-is-an-llm)
- [How Do LLMs Work?](#how-do-llms-work)
- [Key Concepts](#key-concepts)
- [Understanding Parameters](#understanding-parameters)
- [LLM Providers](#llm-providers)
- [Cost Considerations](#cost-considerations)
- [Best Practices](#best-practices)

---

## What is an LLM?

**Large Language Model (LLM)** = A computer program trained on massive amounts of text that can:
- Understand and generate human-like text
- Answer questions
- Write code
- Summarize documents
- Translate languages
- And much more!

### Real-World Analogy

Think of an LLM like a **very well-read assistant**:
- It has "read" billions of documents, books, and websites
- It can use this knowledge to help you with tasks
- It responds based on patterns it learned during training
- It doesn't "know" things perfectly—it predicts what would be a good response

### Popular LLMs You May Know

| LLM | Provider | Best For |
|-----|----------|----------|
| **GPT-4** | OpenAI | General tasks, reasoning |
| **Claude** | Anthropic | Long documents, coding |
| **Gemini** | Google | Multimodal (text + images) |
| **Llama** | Meta | Open-source, local deployment |

---

## How Do LLMs Work?

### The Simple Explanation

```
Your Input → LLM Processing → Response

"What is Python?" → [LLM thinks] → "Python is a programming language..."
```

### The Technical Process (Simplified)

1. **Tokenization**: Your text is broken into small pieces called "tokens"
   ```python
   "Hello, world!" → ["Hello", ",", " world", "!"]
   ```

2. **Encoding**: Tokens are converted to numbers the model understands
   ```python
   ["Hello", ",", " world", "!"] → [15496, 11, 995, 0]
   ```

3. **Processing**: The model uses billions of parameters to predict the best response

4. **Decoding**: Numbers are converted back to readable text
   ```python
   [1212, 318, 257] → "This is a"
   ```

5. **Generation**: The model continues predicting the next best token until complete

---

## Key Concepts

### 1. Tokens

**Tokens** are the basic units LLMs work with. They're like "words" but not exactly.

```python
# English text: ~4 characters = 1 token
"Hello, how are you doing today?" 
# Approximately 8 tokens: ["Hello", ",", " how", " are", " you", " doing", " today", "?"]

# Code: varies by complexity
"def hello_world():"
# Approximately 6 tokens: ["def", " hello", "_", "world", "(", "):"]
```

**Why Tokens Matter:**
- LLMs have a **token limit** (context window)
- You're charged by tokens (input + output)
- More tokens = longer wait time

**Token Estimator (Rule of Thumb):**
- English: 100 tokens ≈ 75 words ≈ 400 characters
- Code: Varies, but usually more tokens per line than prose

### 2. Context Window

The **context window** is the maximum amount of text the LLM can "remember" at once.

```python
Context Window = Input Tokens + Output Tokens

# Example: GPT-4 (8K context window)
Input:  5,000 tokens (your question + conversation history)
Output: 3,000 tokens (maximum response length)
Total:  8,000 tokens (fits within limit )

# If you exceed the limit:
Input:  7,500 tokens
Output: 2,000 tokens
Total:  9,500 tokens (exceeds 8K limit )
```

**Common Context Windows:**
| Model | Context Window | Equivalent Pages |
|-------|----------------|------------------|
| GPT-3.5 | 4,096 tokens | ~3 pages |
| GPT-4 | 8,192 tokens | ~6 pages |
| GPT-4-32K | 32,768 tokens | ~24 pages |
| Claude 2 | 100,000 tokens | ~75 pages |
| Gemini Pro | 32,768 tokens | ~24 pages |

**AgentHub Implementation:**
```python
# From: src/app/llm/providers/openai_provider.py
def get_available_models(self) -> List[str]:
    return [
        "gpt-4",           # 8K context
        "gpt-4-32k",       # 32K context
        "gpt-3.5-turbo",   # 4K context
        "gpt-3.5-turbo-16k" # 16K context
    ]
```

### 3. Temperature

**Temperature** controls how "creative" or "random" the LLM's responses are.

```python
Temperature Range: 0.0 to 2.0

Lower (0.0 - 0.3)     →  More deterministic, focused, consistent
Medium (0.4 - 0.9)    →  Balanced creativity and coherence
Higher (1.0 - 2.0)    →  More creative, diverse, unpredictable
```

**Visual Guide:**

```
Temperature = 0.0                    Temperature = 1.0
┌─────────────────┐                  ┌─────────────────┐
│ "The capital    │                  │ "The capital    │
│  of France is   │                  │  of France is   │
│  Paris."        │                  │  Paris, the     │
│                 │                  │  City of Light, │
│ (Always same)   │                  │  known for..."  │
│                 │                  │ (Varies each    │
│                 │                  │  time)          │
└─────────────────┘                  └─────────────────┘
```

**When to Use Each:**

| Temperature | Use Case | Example |
|-------------|----------|---------|
| **0.0 - 0.3** | Factual answers, data extraction, consistency | "Extract email from: 'Contact john@example.com'" |
| **0.5 - 0.7** | General conversation, balanced tasks | "Write a product description" |
| **0.8 - 1.0** | Creative writing, brainstorming | "Write a poem about AI" |
| **1.1 - 2.0** | Experimental, highly creative | "Generate unusual marketing ideas" |

**AgentHub Configuration:**
```yaml
# From: resources/application-llm.yaml
llm:
  default_provider: "openai"
  temperature: 0.1                     # Conservative for consistency
  
providers:
  openai:
    temperature: 0.1                   # Factual responses
  
  groq:
    temperature: 0.7                   # More creative
```

**Code Example:**
```python
# Using different temperatures for different tasks
from app.llm.factory.llm_factory import LLMFactory

# Factual extraction (low temperature)
llm_factual = LLMFactory.get_llm("openai")
result = await llm_factual.generate(
    messages=["Extract the email from: Contact sales@example.com"],
    temperature=0.1  # Very consistent
)
# Output: "sales@example.com"

# Creative writing (high temperature)
llm_creative = LLMFactory.get_llm("openai")
result = await llm_creative.generate(
    messages=["Write a tagline for a space tourism company"],
    temperature=0.9  # More varied/creative
)
# Output: "Journey Beyond Stars, Discover Your Universe" (varies each run)
```

### 4. Max Tokens (Output Length)

**Max Tokens** limits how long the response can be.

```python
# Control response length
max_tokens = 100   # Short answer (~75 words)
max_tokens = 500   # Medium answer (~375 words)
max_tokens = 2000  # Long answer (~1500 words)
```

**Important Notes:**
- Setting `max_tokens` too low may cut off responses mid-sentence
- Setting it too high wastes tokens (costs money) if LLM finishes early
- The LLM will stop naturally if it completes its thought before hitting the limit

**AgentHub Example:**
```python
# From: src/app/llm/providers/openai_provider.py
async def generate(
    self,
    messages: List[str],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    custom_model: Optional[str] = None,
    **kwargs
) -> LLMResponse:
    """
    Generate a response using OpenAI.
    
    Args:
        messages: Input messages
        temperature: Controls randomness (0.0-2.0)
        max_tokens: Maximum tokens in response
        custom_model: Override default model
    """
    # Implementation uses these parameters
```

### 5. Top-P (Nucleus Sampling)

**Top-P** is an alternative to temperature for controlling randomness.

```python
# Top-P: Only consider tokens that make up the top P% probability
top_p = 0.1   # Very focused (top 10% most likely tokens)
top_p = 0.5   # Balanced
top_p = 1.0   # Consider all tokens (default)
```

**Temperature vs Top-P:**
- Use **temperature** OR **top-p**, not both
- Temperature: Flattens/sharpens entire probability distribution
- Top-P: Cuts off low-probability tokens

**When to Use:**
| Parameter | Best For |
|-----------|----------|
| **Temperature** | General use, intuitive control |
| **Top-P** | Fine-tuned control, specific tasks |

### 6. Streaming vs Batch

**Batch Mode**: Wait for the entire response before showing anything

```python
User: "Explain quantum computing"
[5 seconds later...]
LLM: "Quantum computing is a revolutionary technology..." [complete response]
```

**Streaming Mode**: Show response as it's generated (word by word)

```python
User: "Explain quantum computing"
LLM: "Quantum" [0.1s]
     "computing" [0.2s]
     "is" [0.3s]
     "a revolutionary" [0.4s]
     ... [continues]
```

**AgentHub Implementation:**
```python
# From: src/app/llm/base/base_llm_provider.py
async def stream(
    self,
    messages: List[str],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **kwargs
) -> AsyncGenerator[str, None]:
    """Stream LLM responses token by token."""
    # Returns chunks as they're generated
    async for chunk in self._stream_implementation(messages, **kwargs):
        yield chunk
```

**When to Use Streaming:**
- Better user experience (feels faster)
- Long responses (articles, code)
- Interactive applications
- Need complete response before processing
- Parsing structured data

---

## Understanding Parameters

### Parameter Summary Table

| Parameter | Type | Range | Default | Purpose |
|-----------|------|-------|---------|---------|
| **temperature** | float | 0.0-2.0 | 0.7 | Controls randomness |
| **max_tokens** | int | 1-∞ | Model limit | Maximum output length |
| **top_p** | float | 0.0-1.0 | 1.0 | Nucleus sampling |
| **frequency_penalty** | float | -2.0-2.0 | 0.0 | Reduce repetition |
| **presence_penalty** | float | -2.0-2.0 | 0.0 | Encourage new topics |

### AgentHub Configuration Examples

**Example 1: Factual Question Answering**
```yaml
# Conservative settings for consistent, accurate answers
temperature: 0.1
max_tokens: 500
top_p: 0.95
```

**Example 2: Creative Content Generation**
```yaml
# Higher temperature for diverse, creative output
temperature: 0.9
max_tokens: 2000
frequency_penalty: 0.5  # Reduce word repetition
```

**Example 3: Code Generation**
```yaml
# Balanced for correct but readable code
temperature: 0.3
max_tokens: 1500
top_p: 0.95
```

---

## LLM Providers

AgentHub supports **7 major LLM providers**, each with unique strengths:

### Provider Comparison

| Provider | Models | Strengths | Best For |
|----------|--------|-----------|----------|
| **OpenAI** | GPT-4, GPT-3.5 | Most capable, best reasoning | General tasks, complex problems |
| **Anthropic** | Claude 2, Claude Instant | Long context (100K), safe | Document analysis, research |
| **Google** | Gemini Pro | Multimodal, fast | Vision + text, real-time |
| **Groq** | Llama 2, Mixtral | Ultra-fast inference | Real-time, high throughput |
| **Ollama** | Local models | Privacy, offline | Sensitive data, local dev |
| **HuggingFace** | Thousands of models | Open-source, customizable | Research, experimentation |
| **Azure OpenAI** | GPT-4, GPT-3.5 | Enterprise, compliance | Corporate, regulated industries |

### Switching Providers in AgentHub

**Method 1: Configuration File**
```yaml
# resources/application-llm.yaml
llm:
  default_provider: "openai"  # Change to: anthropic, google, groq, etc.
```

**Method 2: Environment Variable**
```bash
export DEFAULT_LLM_PROVIDER=anthropic
```

**Method 3: Programmatically**
```python
from app.llm.factory.llm_factory import LLMFactory
from app.core.constants import LLMProvider

# Use specific provider
openai_llm = LLMFactory.get_llm(LLMProvider.OPENAI)
claude_llm = LLMFactory.get_llm(LLMProvider.ANTHROPIC)

# Use default provider
default_llm = LLMFactory.get_default_llm()
```

---

## Cost Considerations

### Understanding Pricing

LLM providers charge based on **tokens processed**:

```
Total Cost = (Input Tokens × Input Price) + (Output Tokens × Output Price)
```

### Example Pricing (OpenAI GPT-4, as of 2024)

| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| GPT-4 | $0.03 | $0.06 |
| GPT-4-32K | $0.06 | $0.12 |
| GPT-3.5-Turbo | $0.001 | $0.002 |

**Real Cost Example:**
```python
# User asks: "Explain machine learning" (5 tokens)
# Response: 500 tokens explanation

Input cost:  5 tokens × $0.03/1000 = $0.00015
Output cost: 500 tokens × $0.06/1000 = $0.03
Total cost:  $0.03015 per request

# 1,000 similar requests = ~$30
# 10,000 similar requests = ~$300
```

### Cost Optimization Strategies

**1. Choose the Right Model**
```python
# Use GPT-3.5 for simple tasks (20x cheaper!)
simple_tasks = ["summarize", "extract", "classify"]

# Use GPT-4 only for complex tasks
complex_tasks = ["reasoning", "coding", "analysis"]
```

**2. Limit Context Window**
```python
# Don't send entire conversation history if not needed
messages = recent_messages[-5:]  # Only last 5 messages
```

**3. Optimize Prompts**
```python
# Inefficient (uses many tokens)
prompt = "Please take your time and explain in great detail..."

# Efficient (fewer tokens, same result)
prompt = "Explain concisely:"
```

**4. Set Reasonable max_tokens**
```python
# Don't use:
max_tokens = 4000  # If you only need a short answer

# Use:
max_tokens = 200   # For short answers
```

**5. Cache Frequent Responses**
```python
# Cache common questions to avoid re-computing
cache = {"What is AI?": "AI is...", ...}
if question in cache:
    return cache[question]  # Free!
else:
    response = await llm.generate(question)  # Costs money
```

**AgentHub Cost Tracking:**
```python
# From: src/app/llm/base/base_llm_provider.py
class LLMResponse:
    def __init__(self, content: str, usage: Dict[str, Any]):
        self.content = content
        self.usage = usage  # Contains token counts!
        
# Usage tracking
response = await llm.generate(messages)
print(f"Tokens used: {response.usage}")
# Output: {'prompt_tokens': 10, 'completion_tokens': 50, 'total_tokens': 60}
```

---

## Best Practices

### 1. Start with Lower-Cost Models

```python
# Development/Testing
test_llm = LLMFactory.get_llm(LLMProvider.GROQ)  # Free tier available

# Production (after testing)
prod_llm = LLMFactory.get_llm(LLMProvider.OPENAI)
```

### 2. Use Appropriate Temperature

```python
# Factual tasks
temperature = 0.1  # Consistent, accurate

# Creative tasks
temperature = 0.8  # Varied, interesting
```

### 3. Implement Error Handling

```python
# AgentHub has built-in resilience
from app.llm.factory.llm_factory import LLMFactory

try:
    llm = LLMFactory.get_llm(LLMProvider.OPENAI)
    response = await llm.generate(messages)
except Exception as e:
    # Automatic retry, circuit breaker, fallback
    logger.error(f"LLM error: {e}")
```

### 4. Monitor Token Usage

```python
# Track costs in production
response = await llm.generate(messages)

logger.info(f"Tokens: {response.usage['total_tokens']}")
logger.info(f"Cost: ${calculate_cost(response.usage)}")
```

### 5. Validate Responses

```python
# Always validate LLM output
response = await llm.generate("Extract email from text")

if not is_valid_email(response.content):
    # Handle invalid response
    logger.warning("LLM returned invalid email")
```

---

## Quick Reference

### Common Tasks & Recommended Settings

| Task | Temperature | Max Tokens | Example |
|------|-------------|------------|---------|
| **Data Extraction** | 0.0-0.2 | 100-500 | Extract phone number |
| **Summarization** | 0.3-0.5 | 200-1000 | Summarize article |
| **Q&A** | 0.3-0.7 | 200-1000 | Answer questions |
| **Code Generation** | 0.2-0.4 | 500-2000 | Write function |
| **Creative Writing** | 0.7-1.0 | 1000-3000 | Write story |
| **Brainstorming** | 0.8-1.2 | 500-2000 | Generate ideas |

### AgentHub Quick Start

```python
from app.llm.factory.llm_factory import LLMFactory

# 1. Get LLM instance
llm = LLMFactory.get_default_llm()

# 2. Generate response
response = await llm.generate(
    messages=["What is Python?"],
    temperature=0.3,
    max_tokens=200
)

# 3. Use response
print(response.content)
print(f"Tokens used: {response.usage['total_tokens']}")
```

---

## Next Steps

Now that you understand LLM basics, explore:

1. **[RAG Pipeline](./rag-pipeline.md)** - Learn how to give LLMs access to your own data
2. **[Configuration Guide](../guides/configuration/README.md)** - Configure LLM providers
3. **[Architecture Overview](../architecture/overview.md)** - See how LLMs fit into AgentHub

---

## Glossary

| Term | Definition |
|------|------------|
| **Context Window** | Maximum tokens (input + output) an LLM can process |
| **Embedding** | Numerical representation of text for similarity search |
| **Fine-tuning** | Training an LLM on specific data for specialized tasks |
| **Inference** | Using a trained model to generate responses |
| **Parameter** | Internal weights in the model (e.g., "7B parameters") |
| **Prompt** | The input text you give to an LLM |
| **Token** | Basic unit of text (roughly 0.75 words in English) |
| **Temperature** | Controls randomness in responses (0.0-2.0) |

---

**Additional Resources:**
- [OpenAI Documentation](https://platform.openai.com/docs)
- [Anthropic Claude Guide](https://docs.anthropic.com)
- [LangChain Concepts](https://python.langchain.com/docs/get_started/introduction)

**Need Help?**
- Check our [Tutorials](../tutorials/README.md)
- See [Architecture Docs](../architecture/overview.md) for more code examples
- Ask in [Discussions](https://github.com/timothy-odofin/agenthub-be/discussions)
