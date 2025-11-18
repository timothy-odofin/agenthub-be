class RagDataProvider:
    _registry = {}

    @classmethod
    def register(cls, name):
        """Decorator to register a data provider class under a given name."""
        def decorator(provider_cls):
            cls._registry[name] = provider_cls
            return provider_cls
        return decorator

    @classmethod
    def get_class(cls, name):
        """Get a registered data provider class by name."""
        if name not in cls._registry:
            raise ValueError(f"Data provider '{name}' not found in registry. Available: {list(cls._registry.keys())}")
        return cls._registry[name]