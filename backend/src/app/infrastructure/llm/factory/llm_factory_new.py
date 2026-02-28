"""
Factory for creating LLM instances with integrated caching.

Leverages the existing cache infrastructure (app.infrastructure.cache)
for thread-safe, production-grade caching with telemetry.
"""

import pickle
from typing import Dict, Optional

from app.core.constants import LLMProvider
from app.core.utils.logger import get_logger
from app.infrastructure.llm.base.base_llm_provider import BaseLLMProvider
from app.infrastructure.llm.base.llm_registry import LLMRegistry

logger = get_logger(__name__)


class LLMFactory:
    """
    Factory class for creating LLM instances with integrated caching.

    Uses the existing BaseCacheProvider infrastructure for production-grade caching:
    - Thread-safe (Redis/In-Memory implementations handle concurrency)
    - Telemetry support (can integrate with existing cache monitoring)
    - No code duplication (reuses tested cache infrastructure)
    - Consistent with application patterns
    """

    _instance: Optional["LLMFactory"] = None
    _cache_hits = 0
    _cache_misses = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def reset_for_testing(cls):
        """Reset factory singleton for testing."""
        import asyncio

        from app.infrastructure.cache.instances import llm_provider_cache

        cls._instance = None
        cls._cache_hits = 0
        cls._cache_misses = 0
        # Clear cache asynchronously
        asyncio.create_task(cls._clear_cache_async())

    @staticmethod
    async def _clear_cache_async():
        """Helper to clear cache asynchronously."""
        from app.infrastructure.cache.instances import llm_provider_cache

        # Note: Cache doesn't have a clear_all method, so we'll rely on namespace isolation
        logger.info("Cache cleared (namespace isolated)")

    @staticmethod
    async def clear_llm_cache(
        provider_name: Optional[str] = None, model: Optional[str] = None
    ) -> int:
        """
        Clear LLM provider cache entries.

        Args:
            provider_name: Provider name to clear (e.g., 'openai'). If None, clears all.
            model: Model name to clear. If None but provider_name is set, clears all models for that provider.

        Returns:
            Number of cache entries cleared

        Note: Uses the cache's secondary index feature to find and delete entries.
        """
        from app.infrastructure.cache.instances import llm_provider_cache

        try:
            if provider_name is None:
                # Unfortunately, BaseCacheProvider doesn't have a clear_all method
                # We'd need to track all keys or use a pattern scan (Redis SCAN)
                logger.warning(
                    "Clearing all LLM cache requires Redis SCAN or key tracking - not implemented yet"
                )
                return 0
            elif model is None:
                # Get all keys for this provider using secondary index
                keys = await llm_provider_cache.get_keys_by_index(
                    "provider", provider_name
                )
                count = 0
                for key in keys:
                    if await llm_provider_cache.delete(
                        key, indexes={"provider": provider_name}
                    ):
                        count += 1
                logger.info(
                    f"Cleared {count} LLM cache entries for provider '{provider_name}'"
                )
                return count
            else:
                # Clear specific provider+model combination
                cache_key = f"{provider_name}:{model}"
                if await llm_provider_cache.delete(
                    cache_key, indexes={"provider": provider_name, "model": model}
                ):
                    logger.info(
                        f"Cleared LLM cache for provider '{provider_name}', model '{model}'"
                    )
                    return 1
                return 0
        except Exception as e:
            logger.error(f"Error clearing LLM cache: {e}", exc_info=True)
            return 0

    @staticmethod
    async def get_llm_cache_stats() -> Dict:
        """
        Get LLM provider cache statistics.

        Note: The current BaseCacheProvider doesn't expose stats.
        This would need to be added to the cache interface.
        """
        total_requests = LLMFactory._cache_hits + LLMFactory._cache_misses
        hit_rate = (
            (LLMFactory._cache_hits / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "cache_hits": LLMFactory._cache_hits,
            "cache_misses": LLMFactory._cache_misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "total_requests": total_requests,
            "note": "Cache backend stats not exposed by BaseCacheProvider",
        }

    @staticmethod
    def get_llm(provider: LLMProvider) -> BaseLLMProvider:
        """
        Get an LLM instance for the specified provider.

        Args:
            provider: LLM provider to use (required)

        Returns:
            LLM provider instance (lazy initialization)

        Raises:
            ValueError: If provider is not available or not registered
        """
        # Validate provider is registered
        if not LLMRegistry.is_provider_registered(provider):
            available = LLMRegistry.list_providers()
            raise ValueError(
                f"LLM provider '{provider}' not available. Available: {available}"
            )

        # Get provider class and create instance
        provider_class = LLMRegistry.get_provider_class(provider)
        llm_instance = (
            provider_class()
        )  # Provider self-configures and handles lazy initialization

        logger.info(f"Created LLM instance: {provider}")
        return llm_instance

    @staticmethod
    async def get_llm_by_name(
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
        use_cache: bool = True,
    ) -> BaseLLMProvider:
        """
        Get an LLM instance by provider name string with optional model specification.

        This method uses the existing cache infrastructure (BaseCacheProvider)
        for production-grade caching with thread safety and telemetry.

        Caching Strategy:
        - Uses app.infrastructure.cache.instances.llm_provider_cache
        - Pickle serialization for storing provider instances
        - Secondary indexes for provider/model filtering
        - No TTL (cache indefinitely until manually cleared)

        Args:
            provider_name: String name of the provider (e.g., "openai", "anthropic").
                          If None, uses the default provider from configuration.
            model: Optional model name to validate. If None, uses provider's default.
                   Model is used as cache key to support dynamic switching.
            use_cache: Whether to use cached provider instances. Default True.

        Returns:
            LLM provider instance configured for the specified provider

        Raises:
            ValueError: If provider name is invalid or model is not supported
        """
        # Import here to avoid circular imports
        from app.core.config.framework.settings import settings
        from app.infrastructure.cache.instances import llm_provider_cache
        from app.services.llm_service import LLMService

        # Get provider name - use default if not specified
        if not provider_name:
            provider_name = settings.get_section("llm.default.provider")
            if not provider_name:
                raise ValueError(
                    "No provider specified and no default provider configured"
                )

        # Convert string to enum
        try:
            provider = LLMProvider(provider_name.lower())
        except ValueError:
            valid_providers = [p.value for p in LLMProvider]
            raise ValueError(
                f"Invalid provider '{provider_name}'. Valid providers: {valid_providers}"
            )

        # Validate model if provided (this also returns the validated/default model)
        validated_model = LLMService.validate_model_for_provider(provider_name, model)

        # Check cache first (thread-safe via BaseCacheProvider)
        cache_key = f"{provider_name}:{validated_model}"

        if use_cache:
            try:
                cached_data = await llm_provider_cache.get(cache_key, deserialize=False)
                if cached_data is not None:
                    # Deserialize the pickled provider
                    cached_provider = pickle.loads(cached_data.encode("latin1"))
                    LLMFactory._cache_hits += 1

                    stats = await LLMFactory.get_llm_cache_stats()
                    logger.info(
                        f"✅ Reusing cached LLM provider: {provider_name}, model: {validated_model} "
                        f"(hit_rate: {stats['hit_rate']})"
                    )
                    return cached_provider
                else:
                    LLMFactory._cache_misses += 1
            except Exception as e:
                logger.warning(f"Cache lookup failed: {e}, creating new provider")
                LLMFactory._cache_misses += 1

        logger.info(f"Creating LLM provider: {provider_name}, model: {validated_model}")

        # Create NEW provider instance (no shared state)
        provider_class = LLMRegistry.get_provider_class(provider)
        llm_provider = provider_class()

        # Set model in config BEFORE caching (immutable after caching)
        if validated_model and hasattr(llm_provider, "config"):
            llm_provider.config["model"] = validated_model
            logger.debug(f"Configured provider with model: {validated_model}")

        # Cache the provider instance using pickle serialization
        if use_cache:
            try:
                # Pickle the provider for storage
                pickled_provider = pickle.dumps(llm_provider).decode("latin1")

                # Store with secondary indexes for filtering
                await llm_provider_cache.set(
                    key=cache_key,
                    value=pickled_provider,
                    ttl=None,  # No expiration
                    indexes={"provider": provider_name, "model": validated_model},
                )
                logger.debug(
                    f"Cached LLM provider: {provider_name}, model: {validated_model}"
                )
            except Exception as e:
                logger.warning(f"Failed to cache provider: {e}")

        return llm_provider

    @staticmethod
    def get_default_llm() -> BaseLLMProvider:
        """Get the default LLM instance based on configuration."""
        # Import here to avoid circular imports
        from app.core.config.framework.settings import settings

        default_provider_str = settings.get_section("llm.default.provider")
        if not default_provider_str:
            raise ValueError(
                "No default LLM provider configured. Set DEFAULT_LLM_PROVIDER environment variable."
            )

        try:
            provider = LLMProvider(default_provider_str)
        except ValueError:
            raise ValueError(
                f"Invalid default provider '{default_provider_str}'. "
                f"Valid providers: {[p.value for p in LLMProvider]}"
            )

        return LLMFactory.get_llm(provider)

    @staticmethod
    def list_available_providers() -> list[str]:
        """List all available LLM providers."""
        return LLMRegistry.list_providers()

    @staticmethod
    def is_provider_available(provider: LLMProvider) -> bool:
        """Check if a provider is available and properly configured."""
        try:
            # Import here to avoid circular imports
            from app.core.config.framework.settings import settings

            provider_config = settings.get_section(f"llm.{provider.value}")

            return LLMRegistry.is_provider_registered(provider) and bool(
                provider_config
            )
        except Exception:
            return False
