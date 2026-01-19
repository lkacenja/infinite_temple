"""
User configuration management.

Handles API key storage in memory (not persisted).
Supports multiple LLM providers (OpenAI, Anthropic).
"""

# Supported providers
PROVIDERS = ["openai", "anthropic"]

# In-memory storage for API keys
_api_keys = {}


def get_api_key(provider: str = "openai") -> str | None:
    """
    Get API key for a provider from memory.

    Args:
        provider: Provider name ("openai" or "anthropic")

    Returns:
        API key string or None if not configured
    """
    return _api_keys.get(provider)


def set_api_key(key: str, provider: str = "openai"):
    """
    Store API key for a provider in memory.

    Args:
        key: The API key to save
        provider: Provider name ("openai" or "anthropic")
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider: {provider}")
    _api_keys[provider] = key


def has_api_key(provider: str = None) -> bool:
    """
    Check if an API key is configured.

    Args:
        provider: Specific provider to check, or None to check any provider

    Returns:
        True if at least one API key is configured
    """
    if provider:
        return bool(get_api_key(provider))

    return len(_api_keys) > 0


def get_configured_providers() -> list[str]:
    """Return list of providers that have API keys configured."""
    return [p for p in PROVIDERS if p in _api_keys]
