# Azure OpenAI Provider Implementation

## Overview
The Azure OpenAI provider enables the use of OpenAI models deployed on Microsoft Azure's infrastructure. This is particularly useful for organizations that:
- Have enterprise agreements with Microsoft Azure
- Need data residency compliance
- Require Azure's security and compliance features
- Want to use Azure's networking and identity management

## Configuration

### Environment Variables
Add these to your `.env` file:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your-azure-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4  # Your deployment name in Azure
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### YAML Configuration
The provider is configured in `resources/application-llm.yaml`:

```yaml
azure:
  api_key: "${AZURE_OPENAI_API_KEY}"
  endpoint: "${AZURE_OPENAI_ENDPOINT}"
  model: "${AZURE_OPENAI_DEPLOYMENT:gpt-4}"
  api_version: "${AZURE_OPENAI_API_VERSION:2024-02-15-preview}"
  temperature: "${AZURE_OPENAI_TEMPERATURE:0.1}"
  max_tokens: "${AZURE_OPENAI_MAX_TOKENS:4096}"
  timeout: "${AZURE_OPENAI_TIMEOUT:60}"
```

## Key Differences from OpenAI

### 1. Deployment Names vs Model Names
- **OpenAI**: Uses model names like `gpt-4`, `gpt-3.5-turbo`
- **Azure OpenAI**: Uses **deployment names** that you configure in Azure Portal
  - You create a deployment in Azure (e.g., "my-gpt4-deployment")
  - Use that deployment name in configuration

### 2. Endpoint Structure
- **OpenAI**: `https://api.openai.com/v1`
- **Azure OpenAI**: `https://{your-resource-name}.openai.azure.com/`

### 3. Authentication
- **OpenAI**: API key only
- **Azure OpenAI**: API key or Azure Active Directory (AAD) authentication

### 4. API Versioning
- **OpenAI**: Version in URL path
- **Azure OpenAI**: Explicit `api_version` parameter (e.g., "2024-02-15-preview")

## Usage

### Basic Usage
```python
from app.llm.factory.llm_factory import LLMFactory
from app.core.constants import LLMProvider

# Create Azure OpenAI provider
llm = await LLMFactory.create_llm(LLMProvider.AZURE_OPENAI)

# Generate text
response = await llm.generate("Explain quantum computing in simple terms")
print(response.content)
```

### Streaming Usage
```python
# Stream responses
async for chunk in llm.stream_generate("Write a story about AI"):
    print(chunk, end="", flush=True)
```

### With Custom Parameters
```python
response = await llm.generate(
    "Explain machine learning",
    temperature=0.5,
    max_tokens=500
)
```

## Setting Up Azure OpenAI

### Step 1: Create Azure OpenAI Resource
1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new "Azure OpenAI" resource
3. Note your **resource name** (e.g., "my-openai-resource")
4. Your endpoint will be: `https://my-openai-resource.openai.azure.com/`

### Step 2: Create a Deployment
1. Navigate to your Azure OpenAI resource
2. Go to "Model deployments" or "Deployments"
3. Create a new deployment:
   - Select a model (e.g., GPT-4, GPT-3.5-Turbo)
   - Give it a deployment name (e.g., "gpt-4-production")
4. Note the **deployment name** for configuration

### Step 3: Get API Key
1. In your Azure OpenAI resource
2. Go to "Keys and Endpoint"
3. Copy one of the keys (KEY 1 or KEY 2)

### Step 4: Configure Application
```bash
# .env
AZURE_OPENAI_API_KEY=abc123...your-key-here
AZURE_OPENAI_ENDPOINT=https://my-openai-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4-production  # Your deployment name
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

## Supported Models (via Azure Deployments)

Common models available in Azure OpenAI:
- **GPT-4 Turbo**: Most capable, best for complex tasks
- **GPT-4**: Highly capable, good balance
- **GPT-3.5 Turbo**: Fast and cost-effective
- **GPT-4 32K**: Extended context window
- **GPT-4o**: Optimized for speed
- **GPT-4o Mini**: Smaller, faster variant

## Supported Capabilities

The Azure OpenAI provider supports:
- ✅ **Chat**: Conversational AI
- ✅ **Code Generation**: Programming assistance
- ✅ **Function Calling**: Structured outputs
- ✅ **Streaming**: Real-time response streaming

## Cost Considerations

Azure OpenAI pricing is typically based on:
- **Tokens processed** (input + output)
- **Model tier** (GPT-4 vs GPT-3.5)
- **Region** (pricing varies by Azure region)

Check [Azure OpenAI Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/) for details.

## Troubleshooting

### Common Issues

#### 1. "Resource not found" Error
- Check your `AZURE_OPENAI_ENDPOINT` is correct
- Verify the resource exists in Azure Portal
- Ensure no trailing slash in endpoint

#### 2. "Deployment not found" Error
- Verify `AZURE_OPENAI_DEPLOYMENT` matches your deployment name in Azure
- Check deployment is in "Succeeded" state in Azure Portal

#### 3. "Invalid API Key" Error
- Regenerate key in Azure Portal if needed
- Ensure no extra spaces in the key
- Check key hasn't expired (Azure keys don't expire by default)

#### 4. "API Version not supported" Error
- Update `AZURE_OPENAI_API_VERSION` to a supported version
- Check [Azure OpenAI API versions](https://learn.microsoft.com/azure/ai-services/openai/reference)

## Security Best Practices

1. **Use Azure Key Vault**: Store API keys in Azure Key Vault instead of environment files
2. **Enable Azure AD Authentication**: Use managed identities instead of API keys
3. **Network Security**: Configure Virtual Network integration
4. **Monitoring**: Enable Azure Monitor for usage tracking
5. **Rate Limiting**: Configure appropriate rate limits in Azure

## Migration from OpenAI to Azure OpenAI

### Code Changes Required
Minimal! Just change the provider:

```python
# Before (OpenAI)
llm = await LLMFactory.create_llm(LLMProvider.OPENAI)

# After (Azure OpenAI)
llm = await LLMFactory.create_llm(LLMProvider.AZURE_OPENAI)
```

### Configuration Changes
Update environment variables from OpenAI to Azure format:
- Replace `OPENAI_API_KEY` with `AZURE_OPENAI_API_KEY`
- Add `AZURE_OPENAI_ENDPOINT`
- Add `AZURE_OPENAI_DEPLOYMENT`
- Add `AZURE_OPENAI_API_VERSION`

## References

- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [LangChain AzureChatOpenAI](https://python.langchain.com/docs/integrations/chat/azure_chat_openai)
- [Azure OpenAI API Reference](https://learn.microsoft.com/azure/ai-services/openai/reference)
- [Azure OpenAI Quotas](https://learn.microsoft.com/azure/ai-services/openai/quotas-limits)
