# LLM Providers

Configure and use multiple Large Language Model providers in your AI agent application.

## Table of Contents

- [Overview](#overview)
- [Supported Providers](#supported-providers)
- [Configuration](#configuration)
- [Basic Usage](#basic-usage)
- [Provider Details](#provider-details)
  - [OpenAI](#openai)
  - [Azure OpenAI](#azure-openai)
  - [Anthropic (Claude)](#anthropic-claude)
  - [Google (Gemini)](#google-gemini)
  - [Groq](#groq)
  - [Ollama](#ollama)
  - [HuggingFace](#huggingface)
- [Choosing a Provider](#choosing-a-provider)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [Additional Resources](#additional-resources)

## Overview

This project supports multiple LLM providers, allowing you to choose the best model for your needs based on cost, performance, capabilities, and compliance requirements. You can easily switch between providers or use multiple providers simultaneously.

## Supported Providers

| Provider | Models | Key Features | Best For |
|----------|--------|--------------|----------|
| **OpenAI** | GPT-4, GPT-3.5 | Function calling, streaming, vision | General purpose, production |
| **Azure OpenAI** | GPT-4, GPT-3.5 | Enterprise security, compliance | Enterprise, data residency |
| **Anthropic** | Claude 3, Claude 2 | Long context, safety | Complex reasoning, safety-critical |
| **Google** | Gemini Pro, Gemini Flash | Multimodal, fast | Multimodal tasks, cost-effective |
| **Groq** | Llama, Mixtral | Ultra-fast inference | High-throughput, low latency |
| **Ollama** | Local models | Privacy, no API costs | Development, privacy |
| **HuggingFace** | 100K+ models | Open-source, customizable | Research, custom models |

## Configuration

### Global Settings

All LLM providers are configured in `resources/application-llm.yaml`:

```yaml
llm:
  default_provider: openai  # Default provider to use
  
  openai:
    api_key: "${OPENAI_API_KEY}"
    default_model: "gpt-4"
    temperature: 0.1
    max_tokens: 4096
    timeout: 60
  
  azure:
    api_key: "${AZURE_OPENAI_API_KEY}"
    endpoint: "${AZURE_OPENAI_ENDPOINT}"
    model: "${AZURE_OPENAI_DEPLOYMENT}"
    api_version: "2024-02-15-preview"
    temperature: 0.1
    max_tokens: 4096
  
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    default_model: "claude-3-opus-20240229"
    temperature: 0.1
    max_tokens: 4096
  
  google:
    api_key: "${GOOGLE_API_KEY}"
    default_model: "gemini-pro"
    temperature: 0.1
    max_tokens: 2048
  
  groq:
    api_key: "${GROQ_API_KEY}"
    default_model: "mixtral-8x7b-32768"
    temperature: 0.1
    max_tokens: 4096
  
  ollama:
    base_url: "${OLLAMA_BASE_URL:http://localhost:11434}"
    default_model: "llama2"
    temperature: 0.1
  
  huggingface:
    api_key: "${HUGGINGFACE_API_KEY}"
    default_model: "meta-llama/Llama-2-7b-chat-hf"
    temperature: 0.1
```

### Environment Variables

Create a `.env` file with your API keys:

```bash
# OpenAI
OPENAI_API_KEY=sk-...your-key-here

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...your-key-here

# Google
GOOGLE_API_KEY=AIza...your-key-here

# Groq
GROQ_API_KEY=gsk_...your-key-here

# Ollama (for local deployment)
OLLAMA_BASE_URL=http://localhost:11434

# HuggingFace
HUGGINGFACE_API_KEY=hf_...your-key-here
```

## Basic Usage

### Using the Default Provider

```python
from app.llm.factory.llm_factory import LLMFactory

# Uses the default provider from config
llm = await LLMFactory.create_llm()

# Generate a response
response = await llm.generate("Explain machine learning")
print(response.content)
```

### Specifying a Provider

```python
from app.llm.factory.llm_factory import LLMFactory
from app.core.constants import LLMProvider

# Use a specific provider
llm = await LLMFactory.create_llm(LLMProvider.ANTHROPIC)
response = await llm.generate("Explain quantum computing")
```

### Streaming Responses

```python
# Stream for real-time output
async for chunk in llm.stream_generate("Write a story about AI"):
    print(chunk, end="", flush=True)
```

### Custom Parameters

```python
response = await llm.generate(
    "Explain deep learning",
    temperature=0.7,
    max_tokens=1000
)
```

---

## Provider Details

### OpenAI

The most popular LLM provider with powerful models like GPT-4.

**Setup:**

1. Get an API key from https://platform.openai.com/api-keys
2. Add to `.env`:
   ```bash
   OPENAI_API_KEY=sk-...your-key-here
   ```

**Available Models:**
- `gpt-4-turbo` - Most capable, best for complex tasks
- `gpt-4` - Highly capable general purpose model
- `gpt-3.5-turbo` - Fast and cost-effective

**Capabilities:**
- Chat and conversation
- Function calling
- Streaming responses
- Vision (GPT-4 Vision models)

**Best For:**
- Production applications
- Complex reasoning tasks
- Function calling / tool use
- General purpose AI

**Pricing:** Pay per token (input + output)

---

### Azure OpenAI

OpenAI models deployed on Microsoft Azure infrastructure.

**Setup:**

1. Create Azure OpenAI resource in [Azure Portal](https://portal.azure.com)
2. Create a model deployment (e.g., "gpt-4-production")
3. Get API key from "Keys and Endpoint"
4. Configure:
   ```bash
   AZURE_OPENAI_API_KEY=your-azure-key
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4-production
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   ```

**Key Differences from OpenAI:**
- Uses **deployment names** instead of model names
- Enterprise security and compliance features
- Data residency options
- Azure AD authentication support
- Private network connectivity

**Available Models:**
Same models as OpenAI (GPT-4, GPT-3.5) but deployed in Azure

**Best For:**
- Enterprise customers with Azure agreements
- Data residency requirements
- Compliance and security needs
- Integration with Azure services

**Pricing:** Azure-specific pricing, varies by region

---

### Anthropic (Claude)

Known for longer context windows and strong safety features.

**Setup:**

1. Get an API key from https://console.anthropic.com/
2. Add to `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...your-key-here
   ```

**Available Models:**
- `claude-3-opus-20240229` - Most capable model
- `claude-3-sonnet-20240229` - Balanced performance
- `claude-3-haiku-20240307` - Fast and cost-effective
- `claude-2.1` - Previous generation

**Capabilities:**
- 200K token context window (Claude 2.1)
- Strong performance on reasoning tasks
- Built-in safety features
- Streaming responses

**Best For:**
- Long-context tasks (analyzing large documents)
- Complex reasoning and analysis
- Safety-critical applications
- Research and education

**Pricing:** Pay per token, varies by model tier

---

### Google (Gemini)

Google's multimodal AI models with competitive pricing.

**Setup:**

1. Get an API key from https://makersuite.google.com/app/apikey
2. Add to `.env`:
   ```bash
   GOOGLE_API_KEY=AIza...your-key-here
   ```

**Available Models:**
- `gemini-pro` - Text generation and chat
- `gemini-pro-vision` - Multimodal (text + images)
- `gemini-1.5-pro` - Extended context window
- `gemini-1.5-flash` - Fast and cost-effective

**Capabilities:**
- Multimodal (text and images)
- Up to 1M token context (Gemini 1.5)
- Fast inference
- Streaming responses

**Best For:**
- Multimodal tasks (text + images)
- Cost-effective production use
- Large context requirements
- High-throughput applications

**Pricing:** Competitive pricing, free tier available

---

### Groq

Ultra-fast inference using custom LPU (Language Processing Unit) hardware.

**Setup:**

1. Get an API key from https://console.groq.com/
2. Add to `.env`:
   ```bash
   GROQ_API_KEY=gsk_...your-key-here
   ```

**Available Models:**
- `mixtral-8x7b-32768` - Mixture of experts model
- `llama2-70b-4096` - Large Llama 2 model
- `llama2-7b-4096` - Smaller, faster Llama 2
- `gemma-7b-it` - Google's Gemma model

**Capabilities:**
- Extremely fast inference (500+ tokens/sec)
- Open-source model support
- Streaming responses
- Cost-effective

**Best For:**
- High-throughput applications
- Low-latency requirements
- Real-time chat applications
- Cost-sensitive workloads

**Pricing:** Very competitive, pay per token

---

### Ollama

Run LLMs locally on your own hardware.

**Setup:**

1. Install Ollama from https://ollama.ai/
2. Pull a model:
   ```bash
   ollama pull llama2
   ```
3. Start Ollama server:
   ```bash
   ollama serve
   ```
4. Configure:
   ```bash
   OLLAMA_BASE_URL=http://localhost:11434
   ```

**Available Models:**
- `llama2` - Meta's Llama 2 (7B, 13B, 70B)
- `mistral` - Mistral 7B
- `codellama` - Code-specialized Llama
- `mixtral` - Mixture of experts
- `phi` - Microsoft's Phi models

**Capabilities:**
- Runs entirely on your hardware
- No API costs
- Full data privacy
- Offline operation

**Best For:**
- Development and testing
- Privacy-sensitive applications
- Offline deployments
- Cost-free experimentation

**Pricing:** Free (hardware costs only)

---

### HuggingFace

Access to 100,000+ open-source models.

**Setup:**

1. Create account at https://huggingface.co/
2. Get API token from Settings → Access Tokens
3. Add to `.env`:
   ```bash
   HUGGINGFACE_API_KEY=hf_...your-key-here
   ```

**Available Models:**
- Any model on HuggingFace Hub
- Examples:
  - `meta-llama/Llama-2-7b-chat-hf`
  - `mistralai/Mistral-7B-Instruct-v0.2`
  - `google/flan-t5-xxl`
  - `bigscience/bloom`

**Capabilities:**
- Vast model selection
- Open-source models
- Fine-tuned variants
- Research models

**Best For:**
- Research and experimentation
- Custom fine-tuned models
- Specialized domain models
- Open-source projects

**Pricing:** Inference API pricing, many models free

---

## Choosing a Provider

### Decision Matrix

| Priority | Recommended Provider | Why |
|----------|---------------------|-----|
| **Best Quality** | OpenAI GPT-4, Anthropic Claude 3 Opus | Most capable models |
| **Cost-Effective** | Groq, Google Gemini, GPT-3.5 | Lower pricing |
| **Fastest** | Groq, Google Gemini Flash | Ultra-low latency |
| **Enterprise** | Azure OpenAI | Compliance, security |
| **Privacy** | Ollama | Fully local, no external calls |
| **Long Context** | Anthropic Claude, Gemini 1.5 Pro | 200K+ tokens |
| **Multimodal** | Google Gemini, GPT-4 Vision | Text + images |
| **Open Source** | Ollama, HuggingFace | Full control, customization |

### Cost Comparison (Approximate)

Per 1M tokens:

| Provider | Model | Input | Output |
|----------|-------|-------|--------|
| OpenAI | GPT-4 Turbo | $10 | $30 |
| OpenAI | GPT-3.5 Turbo | $0.50 | $1.50 |
| Anthropic | Claude 3 Opus | $15 | $75 |
| Anthropic | Claude 3 Sonnet | $3 | $15 |
| Google | Gemini Pro | $0.50 | $1.50 |
| Groq | Mixtral 8x7B | $0.24 | $0.24 |
| Ollama | Any | $0 | $0 |

*Prices are approximate and subject to change*

## Advanced Usage

### Using Multiple Providers

```python
# Use different providers for different tasks
fast_llm = await LLMFactory.create_llm(LLMProvider.GROQ)
smart_llm = await LLMFactory.create_llm(LLMProvider.OPENAI)

# Fast response for simple queries
quick_answer = await fast_llm.generate("What is 2+2?")

# Smart model for complex reasoning
detailed_answer = await smart_llm.generate(
    "Explain the implications of quantum computing on cryptography"
)
```

### Provider Fallback

```python
from app.core.constants import LLMProvider

async def generate_with_fallback(prompt: str):
    """Try multiple providers if one fails."""
    providers = [
        LLMProvider.OPENAI,
        LLMProvider.ANTHROPIC,
        LLMProvider.GOOGLE
    ]
    
    for provider in providers:
        try:
            llm = await LLMFactory.create_llm(provider)
            return await llm.generate(prompt)
        except Exception as e:
            print(f"{provider} failed: {e}")
            continue
    
    raise Exception("All providers failed")
```

### Cost Optimization

```python
async def generate_smartly(prompt: str, complexity: str = "simple"):
    """Choose provider based on task complexity."""
    if complexity == "simple":
        # Use cheaper, faster model
        llm = await LLMFactory.create_llm(LLMProvider.GROQ)
    elif complexity == "complex":
        # Use most capable model
        llm = await LLMFactory.create_llm(LLMProvider.OPENAI)
    else:
        # Balanced option
        llm = await LLMFactory.create_llm(LLMProvider.GOOGLE)
    
    return await llm.generate(prompt)
```

## Troubleshooting

### API Key Issues

**Problem:** "Invalid API key" or authentication errors

**Solutions:**
1. Verify the API key is correct (no extra spaces)
2. Check environment variable is loaded: `echo $OPENAI_API_KEY`
3. Regenerate key if expired
4. Ensure key has proper permissions

### Model Not Found

**Problem:** "Model not available" errors

**Solutions:**
1. Check model name spelling
2. Verify model is available for your account
3. For Azure: ensure deployment name matches configuration
4. Check model access/permissions

### Rate Limiting

**Problem:** "Rate limit exceeded" errors

**Solutions:**
1. Implement exponential backoff
2. Use rate limiting libraries
3. Upgrade to higher tier plan
4. Switch to provider with higher limits

### Slow Responses

**Problem:** Responses take too long

**Solutions:**
1. Switch to faster provider (Groq, Gemini Flash)
2. Use streaming for perceived speed
3. Reduce max_tokens limit
4. Implement timeout handling

## Best Practices

### Security

- **Never commit API keys** - Use environment variables
- **Rotate keys regularly** - Especially for production
- **Use separate keys** - Different keys for dev/staging/prod
- **Monitor usage** - Set up billing alerts
- **Restrict permissions** - Use read-only keys when possible

### Performance

- **Cache responses** - For identical prompts
- **Use streaming** - For better user experience
- **Batch requests** - When possible
- **Choose appropriate model** - Balance cost vs capability
- **Set timeouts** - Prevent hanging requests

### Cost Management

- **Monitor usage** - Track costs per provider
- **Set budgets** - Configure spending limits
- **Optimize prompts** - Reduce token usage
- **Use cheaper models** - When appropriate
- **Implement caching** - Avoid redundant calls

## Additional Resources

**Provider Documentation:**
- [OpenAI API](https://platform.openai.com/docs/)
- [Azure OpenAI](https://learn.microsoft.com/azure/ai-services/openai/)
- [Anthropic Claude](https://docs.anthropic.com/)
- [Google Gemini](https://ai.google.dev/)
- [Groq](https://console.groq.com/docs/)
- [Ollama](https://ollama.ai/docs/)
- [HuggingFace](https://huggingface.co/docs/)

**Related Documentation:**
- [Configuration Guide](../configuration/resources-directory.md)
- [LangChain Integration](https://python.langchain.com/docs/integrations/llms/)

---

With support for 7 different LLM providers, you have the flexibility to choose the best model for each use case while maintaining a consistent API across your application.
