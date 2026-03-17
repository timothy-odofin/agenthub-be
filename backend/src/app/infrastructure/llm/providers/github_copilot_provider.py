"""
GitHub Copilot LLM provider implementation.

Uses the GitHub Models inference endpoint, which is OpenAI-compatible:
  Base URL : https://models.inference.ai.azure.com
  Auth     : GitHub Personal Access Token (PAT) or GitHub App installation token
             passed as the Bearer token / api_key.

Because the endpoint speaks the OpenAI Chat Completions API, this provider
wraps `langchain_openai.ChatOpenAI` (identical to OpenAILLMProvider) but
targets the GitHub-hosted endpoint instead of api.openai.com.

This means:
  - The `self.client` is a standard LangChain ChatOpenAI instance.
  - LangGraphAgent / LangChainAgent receive it unchanged via llm_provider.client.
  - Tool-calling / function-calling work exactly as with OpenAI — fully
    compatible with create_react_agent, AgentExecutor, bind_tools, etc.
  - Streaming (astream) is supported.

Supported models (as of March 2026) with tool-calling:
  gpt-4o, gpt-4o-mini              — OpenAI (full tool-calling ✅)
  claude-3-5-sonnet, claude-3-7-sonnet — Anthropic (tool-calling ✅)
  Llama-3.3-70B-Instruct            — Meta (function-calling ✅)

How to obtain a GITHUB_TOKEN
-----------------------------
Option 1 — Classic PAT (simplest for local dev):
  1. github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
  2. "Generate new token (classic)"
  3. Enable scope: "models:read"  (under "GitHub Models")
  4. Copy the token → add to your .env:
        GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

Option 2 — Fine-grained PAT (recommended, minimal permissions):
  1. github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens
  2. "Generate new token"
  3. Account permissions → "GitHub Models" → "Read-only"
  4. Copy the token → add to your .env:
        GITHUB_TOKEN=github_pat_xxxxxxxxxxxxxxxxxxxx

Option 3 — GitHub Actions (zero setup):
  The runner injects GITHUB_TOKEN automatically. No .env changes needed.

Option 4 — GitHub App installation token:
  Generate via  POST /app/installations/{id}/access_tokens  (GitHub Apps API)
  and pass the returned token as GITHUB_TOKEN.

Rate limits
-----------
Free tier   : ~15 req/min, 150 req/day per model (varies by model tier).
Copilot Pro/Biz subscribers get higher limits.
See: https://docs.github.com/en/github-models/prototyping-with-ai-models
"""

from typing import AsyncGenerator, List

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from app.core.constants import LLMCapability, LLMProvider
from app.core.utils.logger import get_logger
from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider, LLMResponse
from app.infrastructure.llm.base.llm_registry import LLMRegistry

logger = get_logger(__name__)

# The single endpoint GitHub exposes for all hosted models
_GITHUB_MODELS_BASE_URL = "https://models.inference.ai.azure.com"


@LLMRegistry.register(LLMProvider.GITHUB_COPILOT)
class GitHubCopilotLLM(BaseLLMProvider):
    """
    GitHub Copilot LLM provider.

    Wraps the GitHub Models inference endpoint using langchain_openai.ChatOpenAI.
    The endpoint is fully OpenAI-compatible so no custom HTTP logic is needed.
    """

    def __init__(self):
        super().__init__()
        self._supported_capabilities = {
            LLMCapability.CHAT,
            LLMCapability.CODE_GENERATION,
            LLMCapability.FUNCTION_CALLING,  # gpt-4o, gpt-4o-mini, claude-3-x-sonnet
            LLMCapability.STREAMING,
        }

    # ------------------------------------------------------------------
    # BaseLLMProvider contract
    # ------------------------------------------------------------------

    def get_config_name(self) -> str:
        """Return the YAML config key: llm.github_copilot."""
        return LLMProvider.GITHUB_COPILOT.value  # "github_copilot"

    @property
    def provider_name(self) -> str:
        return "github_copilot"

    def validate_config(self) -> None:
        """
        Validate GitHub Copilot provider configuration.

        Requires:
          - api_key (GITHUB_TOKEN) — must be set and not an unresolved env var
        """
        api_key = self.config.get("api_key")
        if not api_key or api_key.startswith("${"):
            raise ValueError(
                "GitHub Copilot provider requires a GITHUB_TOKEN.\n"
                "Set GITHUB_TOKEN in your .env file.\n"
                "See provider docstring for instructions on obtaining a token."
            )

        model = self.config.get("model") or self.config.get("default_model")
        if model and model not in self.get_available_models():
            logger.warning(
                f"Model '{model}' may not be available on the GitHub Models endpoint. "
                f"Known models: {self.get_available_models()}"
            )

        temperature = self.config.get("temperature")
        if temperature is not None:
            try:
                temp_float = float(temperature)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "GitHub Copilot temperature must be a numeric value"
                ) from exc
            if temp_float < 0 or temp_float > 2:
                raise ValueError(
                    "GitHub Copilot temperature must be between 0 and 2"
                )

        max_tokens = self.config.get("max_tokens")
        if max_tokens is not None:
            try:
                max_tokens_int = int(max_tokens)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "GitHub Copilot max_tokens must be a positive integer"
                ) from exc
            if max_tokens_int <= 0:
                raise ValueError(
                    "GitHub Copilot max_tokens must be a positive integer"
                )

        logger.info("GitHub Copilot provider configuration validated successfully")

    async def initialize(self) -> None:
        """
        Initialize the LangChain ChatOpenAI client pointed at the GitHub Models endpoint.

        Uses ChatOpenAI because the endpoint is OpenAI-API-compatible.
        Passing `base_url` redirects every request to GitHub's infrastructure.
        The GITHUB_TOKEN is passed as the Bearer token via `api_key`.
        """
        try:
            model = (
                self.config.get("model") or self.config.get("default_model") or "gpt-4o"
            )
            base_url = self.config.get("base_url") or _GITHUB_MODELS_BASE_URL

            self.client = ChatOpenAI(
                api_key=self.config.get("api_key"),  # GITHUB_TOKEN
                base_url=base_url,  # GitHub Models endpoint
                model=model,
                temperature=float(self.config.get("temperature", 0.7)),
                max_tokens=self.config.get("max_tokens", None),
                streaming=True,
            )
            self._initialized = True
            logger.info(
                f"GitHub Copilot LLM provider initialized | "
                f"model={model} | endpoint={base_url}"
            )
        except Exception as exc:
            logger.error(f"Failed to initialize GitHub Copilot provider: {exc}")
            raise

    async def _generate_impl(self, prompt: str, **kwargs) -> LLMResponse:
        """
        Generate a response via the GitHub Models endpoint.

        Args:
            prompt      : User prompt string.
            **kwargs    : Optional overrides — model, temperature, max_tokens.

        Returns:
            LLMResponse with content and usage metadata.
        """
        try:
            message = HumanMessage(content=prompt)

            # Support per-request model override (same pattern as OpenAI provider)
            model_override = kwargs.pop("model", None)
            if model_override:
                logger.info(
                    f"GitHub Copilot — model override: {model_override} "
                    f"(default: {self.client.model_name})"
                )
                kwargs["model"] = model_override

            response = await self.client.ainvoke([message], **kwargs)
            usage_metadata = getattr(response, "usage_metadata", {}) or {}

            return LLMResponse(content=response.content, usage=usage_metadata)
        except Exception as exc:
            logger.error(f"GitHub Copilot generation failed: {exc}")
            raise

    async def stream_generate(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream tokens from the GitHub Models endpoint.

        Args:
            prompt  : User prompt string.
            **kwargs: Optional overrides — model, temperature, max_tokens.

        Yields:
            Text chunks as they arrive.
        """
        try:
            message = HumanMessage(content=prompt)

            model_override = kwargs.pop("model", None)
            if model_override:
                logger.info(
                    f"GitHub Copilot streaming — model override: {model_override} "
                    f"(default: {self.client.model_name})"
                )
                kwargs["model"] = model_override

            async for chunk in self.client.astream([message], **kwargs):
                if chunk.content:
                    yield chunk.content
        except Exception as exc:
            logger.error(f"GitHub Copilot streaming failed: {exc}")
            raise

    def get_available_models(self) -> List[str]:
        """
        Models available on the GitHub Models inference endpoint.

        Models marked ✅ support tool/function calling and work with
        LangGraph ReAct / LangChain AgentExecutor out of the box.
        """
        return [
            # OpenAI — full tool-calling ✅
            "gpt-4o",
            "gpt-4o-mini",
            # Anthropic — tool-calling on sonnet variants ✅
            "claude-3-5-sonnet",
            "claude-3-7-sonnet",
            # Meta Llama — function-calling ✅
            "Llama-3.3-70B-Instruct",
            "Llama-3.2-90B-Vision-Instruct",
            "Llama-3.2-11B-Vision-Instruct",
            # Mistral
            "Mistral-Large-2411",
            "Mistral-small",
            # Microsoft Phi
            "Phi-4",
            "Phi-3.5-MoE-instruct",
            # DeepSeek
            "DeepSeek-R1",
            "DeepSeek-V3",
            # Cohere
            "command-r-plus",
            "command-r",
        ]

    def supports_capability(self, capability: LLMCapability) -> bool:
        """Check if this provider supports a specific capability."""
        return capability in self._supported_capabilities
