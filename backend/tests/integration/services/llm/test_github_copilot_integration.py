"""
Integration tests for the GitHub Copilot LLM provider.

These tests make REAL HTTP requests to the GitHub Models inference endpoint
(https://models.inference.ai.azure.com).

Authentication is handled entirely by the settings system — the same path used
by the provider at runtime:
    .env -> app.core.config -> settings.llm.github_copilot.api_key

No manual env-var loading or skip guards are needed here. If the token is
missing/unresolved the provider's validate_config() will raise at fixture
setup time, which pytest will report as an ERROR (not a false PASS).

Run:
    cd backend
    pytest tests/integration/services/llm/test_github_copilot_integration.py -v -s --no-cov
"""

import pytest
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.core.constants import LLMCapability, LLMProvider
from app.infrastructure.llm.base.base_llm_provider import LLMResponse
from app.infrastructure.llm.base.llm_registry import LLMRegistry
from app.infrastructure.llm.factory.llm_factory import LLMFactory
from app.infrastructure.llm.providers.github_copilot_provider import GitHubCopilotLLM
from app.services.llm_service import LLMService

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
async def provider() -> GitHubCopilotLLM:
    """
    Resolve GitHubCopilotLLM through LLMFactory — the same code path used by
    ChatService at runtime.  The factory reads the provider name from the
    LLMProvider enum, looks it up in LLMRegistry, and returns the cached
    instance, so config/settings resolution is identical to production.
    """

    LLMFactory.reset_for_testing()  # start with a clean cache for this test run
    instance = await LLMFactory.get_llm(LLMProvider.GITHUB_COPILOT)
    assert isinstance(
        instance, GitHubCopilotLLM
    ), f"Factory returned unexpected type: {type(instance)}"
    return instance


@pytest.fixture(scope="module")
async def initialised_provider(provider: GitHubCopilotLLM) -> GitHubCopilotLLM:
    """Ensure the LangChain ChatOpenAI client is ready before any test runs."""
    await provider._ensure_initialized()
    return provider


# ---------------------------------------------------------------------------
# 1. Provider configuration & registry
# ---------------------------------------------------------------------------


class TestGitHubCopilotProviderSetup:
    """Verify the provider registers correctly and reads config via settings."""

    def test_provider_registered_in_registry(self):
        """GitHubCopilotLLM must appear in LLMRegistry after the providers package loads."""
        assert LLMRegistry.is_provider_registered(LLMProvider.GITHUB_COPILOT), (
            "LLMProvider.GITHUB_COPILOT not registered — "
            "check github_copilot_provider.py is listed in providers/__init__.py"
        )

    def test_provider_config_name(self, provider: GitHubCopilotLLM):
        """get_config_name() must return 'github_copilot' to match the YAML key."""
        assert provider.get_config_name() == "github_copilot"

    def test_provider_config_has_resolved_api_key(self, provider: GitHubCopilotLLM):
        """api_key must be a resolved string (not None, not '${…}')."""
        api_key = provider.config.get("api_key", "")
        assert api_key and not api_key.startswith(
            "${"
        ), f"api_key was not resolved by settings: {api_key!r}"

    def test_provider_config_has_resolved_base_url(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """
        base_url config, if set, must be resolved, and the effective client base
        URL must point to the GitHub Models endpoint.
        """
        # Config-level base_url may legitimately be None if the env var is unset
        # and the provider falls back internally during initialization.
        base_url = initialised_provider.config.get("base_url")
        if base_url is not None:
            assert base_url and not base_url.startswith(
                "${"
            ), f"base_url was not resolved by settings: {base_url!r}"
            assert "models.inference.ai.azure.com" in base_url

        # Regardless of the config value, the initialized client must have the
        # correct effective base URL.
        client_base_url = getattr(
            getattr(initialised_provider, "client", None), "openai_api_base", None
        )
        assert client_base_url, "GitHubCopilotLLM client has no base URL configured"
        assert "models.inference.ai.azure.com" in client_base_url

    def test_provider_default_model_is_set(self, provider: GitHubCopilotLLM):
        """A default model must be present in config."""
        model = provider.config.get("model") or provider.config.get("default_model")
        assert model, "No default model found in github_copilot config"

    def test_available_models_list(self, provider: GitHubCopilotLLM):
        """get_available_models() must return a non-empty list containing gpt-4o."""
        models = provider.get_available_models()
        assert isinstance(models, list) and len(models) > 0
        assert "gpt-4o" in models

    def test_supports_expected_capabilities(self, provider: GitHubCopilotLLM):
        """Provider must declare CHAT, STREAMING, and FUNCTION_CALLING."""
        assert provider.supports_capability(LLMCapability.CHAT)
        assert provider.supports_capability(LLMCapability.STREAMING)
        assert provider.supports_capability(LLMCapability.FUNCTION_CALLING)

    def test_validate_config_passes_with_resolved_token(
        self, provider: GitHubCopilotLLM
    ):
        """validate_config() must not raise when settings has a real token."""
        provider.validate_config()  # must not raise


# ---------------------------------------------------------------------------
# 2. Initialisation
# ---------------------------------------------------------------------------


class TestGitHubCopilotInitialisation:
    """Verify the ChatOpenAI client initialises correctly against the endpoint."""

    @pytest.mark.asyncio
    async def test_initialise_sets_client(self, provider: GitHubCopilotLLM):
        """After _ensure_initialized(), provider.client must not be None."""
        await provider._ensure_initialized()
        assert provider.client is not None

    @pytest.mark.asyncio
    async def test_initialise_sets_initialized_flag(self, provider: GitHubCopilotLLM):
        """is_initialized must be True after initialisation."""
        await provider._ensure_initialized()
        assert provider.is_initialized is True

    @pytest.mark.asyncio
    async def test_client_is_chat_openai_instance(self, provider: GitHubCopilotLLM):
        """The underlying client must be a LangChain ChatOpenAI instance."""
        await provider._ensure_initialized()
        assert isinstance(provider.client, ChatOpenAI)

    @pytest.mark.asyncio
    async def test_client_base_url_points_to_github_endpoint(
        self, provider: GitHubCopilotLLM
    ):
        """The LangChain client must target the GitHub Models endpoint."""
        await provider._ensure_initialized()
        client_base = str(provider.client.openai_api_base or "")
        assert (
            "models.inference.ai.azure.com" in client_base
        ), f"ChatOpenAI base_url is not the GitHub endpoint: {client_base!r}"


# ---------------------------------------------------------------------------
# 3. Live generate() — single-turn text completion
# ---------------------------------------------------------------------------


class TestGitHubCopilotGenerate:
    """End-to-end tests that send real prompts to the GitHub Models endpoint."""

    @pytest.mark.asyncio
    async def test_generate_returns_non_empty_response(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """generate() must return an LLMResponse with non-empty content."""
        response = await initialised_provider.generate(
            "Reply with exactly three words: integration test passed"
        )
        assert isinstance(response, LLMResponse)
        assert isinstance(response.content, str)
        assert len(response.content.strip()) > 0, "Response content is empty"

    @pytest.mark.asyncio
    async def test_generate_simple_arithmetic(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """Model must answer a simple arithmetic question correctly."""
        response = await initialised_provider.generate(
            "What is 7 multiplied by 6? Answer with only the number."
        )
        assert (
            "42" in response.content
        ), f"Expected '42' in response, got: {response.content!r}"

    @pytest.mark.asyncio
    async def test_generate_returns_usage_metadata(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """Response usage field must be a dict (may be empty for some models)."""
        response = await initialised_provider.generate("Say 'hello' and nothing else.")
        assert isinstance(response.usage, dict)

    @pytest.mark.asyncio
    async def test_generate_addition_answer(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """Model must correctly answer what 2 + 4 equals."""
        response = await initialised_provider.generate(
            "What does 2 + 4 equal? Answer with only the number."
        )
        assert (
            "6" in response.content
        ), f"Expected '6' in response, got: {response.content!r}"

    @pytest.mark.asyncio
    async def test_generate_with_model_override(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """Per-request model override (gpt-4o-mini) must return content."""
        response = await initialised_provider.generate(
            "Reply with the single word: confirmed",
            model="gpt-4o-mini",
        )
        assert len(response.content.strip()) > 0

    def test_llm_service_validates_github_copilot_provider(self):
        """LLMService.validate_model_for_provider must accept 'github_copilot'."""
        model = LLMService.validate_model_for_provider("github_copilot")
        assert model, "validate_model_for_provider returned empty string"

    def test_llm_service_lists_github_copilot_as_available(self):
        """get_available_providers() must include github_copilot when token is set."""
        providers = LLMService.get_available_providers()
        names = [p["name"] for p in providers]
        assert (
            "github_copilot" in names
        ), f"github_copilot not in available providers list: {names}"


# ---------------------------------------------------------------------------
# 4. Live stream_generate() — streaming tokens
# ---------------------------------------------------------------------------


class TestGitHubCopilotStreaming:
    """Verify token-by-token streaming works against the live endpoint."""

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self, initialised_provider: GitHubCopilotLLM):
        """stream_generate() must yield at least one non-empty string chunk."""
        chunks = []
        async for chunk in initialised_provider.stream_generate(
            "Count from 1 to 5, one number per line."
        ):
            assert isinstance(chunk, str)
            chunks.append(chunk)

        assert len(chunks) > 0, "No chunks received from streaming"
        assert len("".join(chunks).strip()) > 0

    @pytest.mark.asyncio
    async def test_stream_reassembled_contains_expected_content(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """Reassembled stream must contain the numbers 1–5."""
        chunks = []
        async for chunk in initialised_provider.stream_generate(
            "List the numbers 1, 2, 3, 4, 5 separated by commas. Nothing else."
        ):
            chunks.append(chunk)

        full = "".join(chunks)
        for num in ["1", "2", "3", "4", "5"]:
            assert num in full, f"Expected '{num}' in streamed response: {full!r}"

    @pytest.mark.asyncio
    async def test_stream_with_model_override(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """Streaming with a per-request model override must still yield content."""
        chunks = []
        async for chunk in initialised_provider.stream_generate(
            "Say 'streaming works' and stop.",
            model="gpt-4o-mini",
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert len("".join(chunks).strip()) > 0


# ---------------------------------------------------------------------------
# 5. LangChain / LangGraph compatibility
# ---------------------------------------------------------------------------


class TestGitHubCopilotLangChainCompatibility:
    """
    Verify provider.client is a drop-in LangChain ChatModel compatible with
    LangChainReactAgent (bind_tools / AgentExecutor) and LangGraphReactAgent
    (create_react_agent).
    """

    @pytest.mark.asyncio
    async def test_client_ainvoke_directly(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """
        client.ainvoke() must work — this is the exact call made by
        LangChainAgent and LangGraphAgent internals.
        """
        messages = [HumanMessage(content="What is the capital of France? One word.")]
        result = await initialised_provider.client.ainvoke(messages)
        assert result.content
        assert "Paris" in result.content

    @pytest.mark.asyncio
    async def test_client_bind_tools_returns_runnable(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """
        client.bind_tools() must succeed — called by LangChainReactAgent
        when wiring tools to the model.
        """

        @tool
        def dummy_tool(query: str) -> str:
            """A dummy tool for testing bind_tools compatibility."""
            return f"dummy: {query}"

        bound = initialised_provider.client.bind_tools([dummy_tool])
        assert hasattr(
            bound, "ainvoke"
        ), "bind_tools() did not return a Runnable with ainvoke"

    @pytest.mark.asyncio
    async def test_create_react_agent_compatible(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """
        create_react_agent(model=provider.client, tools=[...]) must not raise —
        mirrors exactly what LangGraphReactAgent._create_graph() does.
        """

        @tool
        def get_weather(city: str) -> str:
            """Returns the weather for a given city."""
            return f"Sunny in {city}"

        agent = create_react_agent(
            model=initialised_provider.client,
            tools=[get_weather],
        )
        assert agent is not None

    @pytest.mark.asyncio
    async def test_react_agent_invoke_with_tool(
        self, initialised_provider: GitHubCopilotLLM
    ):
        """
        Full end-to-end: LangGraph ReAct agent backed by GitHub Copilot must
        call the tool and surface the result in the final message.
        """

        @tool
        def get_current_date() -> str:
            """Returns today's date."""
            return "2026-03-16"

        agent = create_react_agent(
            model=initialised_provider.client,
            tools=[get_current_date],
        )

        result = await agent.ainvoke(
            {"messages": [HumanMessage(content="What is today's date? Use the tool.")]}
        )

        final_message = result["messages"][-1]
        assert (
            "2026" in final_message.content or "March" in final_message.content
        ), f"Agent did not surface the tool result. Final message: {final_message.content!r}"
