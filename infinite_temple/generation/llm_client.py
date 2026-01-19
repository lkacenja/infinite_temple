"""
Provider-agnostic LLM client using native SDKs.

Supports OpenAI and Anthropic models with a unified interface.
Uses native SDKs for proper structured output support.
"""
import json
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

from openai import OpenAI
import anthropic

from infinite_temple.utility.config import get_api_key


# Type variable for Pydantic models
T = TypeVar('T', bound=BaseModel)

# Provider configurations
PROVIDERS = {
    "anthropic": {
        "name": "Anthropic",
        "default_model": "claude-sonnet-4-5-20250514",
        "key_name": "anthropic",
    },
    "openai": {
        "name": "OpenAI",
        "default_model": "gpt-4o",
        "key_name": "openai",
    },
}

DEFAULT_PROVIDER = "openai"


def get_available_providers() -> list[str]:
    """Return list of providers that have API keys configured."""
    available = []
    for provider_id, config in PROVIDERS.items():
        key = get_api_key(config["key_name"])
        if key:
            available.append(provider_id)
    return available


def get_provider_display_name(provider_id: str) -> str:
    """Get display name for a provider."""
    return PROVIDERS.get(provider_id, {}).get("name", provider_id)


def get_model_for_provider(provider_id: str) -> str:
    """Get the default model for a provider."""
    return PROVIDERS.get(provider_id, {}).get("default_model", "gpt-4o")


class LLMClient:
    """
    Provider-agnostic LLM client using native SDKs.

    Uses OpenAI's responses.parse() for OpenAI models and
    Anthropic's native SDK for Claude models.
    """

    def __init__(self, provider: str = DEFAULT_PROVIDER, model: Optional[str] = None):
        """
        Initialize the LLM client.

        Args:
            provider: Provider ID ("anthropic" or "openai")
            model: Specific model to use (defaults to provider's default)
        """
        if provider not in PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}. Choose from: {list(PROVIDERS.keys())}")

        self.provider = provider
        self.provider_config = PROVIDERS[provider]
        self.model_id = model or self.provider_config["default_model"]

        # Get API key
        key_name = self.provider_config["key_name"]
        self.api_key = get_api_key(key_name)
        if not self.api_key:
            raise ValueError(f"{self.provider_config['name']} API key not configured")

        # Initialize the appropriate client
        if provider == "openai":
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)

    def generate_with_schema(
        self,
        prompt: str,
        schema: Type[T],
        system: Optional[str] = None,
    ) -> T:
        """
        Generate structured output matching a Pydantic schema.

        Args:
            prompt: The user prompt
            schema: Pydantic model class for the response
            system: Optional system message

        Returns:
            Instance of the schema class
        """
        if self.provider == "openai":
            return self._generate_openai(prompt, schema, system)
        else:
            return self._generate_anthropic(prompt, schema, system)

    def _generate_openai(
        self,
        prompt: str,
        schema: Type[T],
        system: Optional[str] = None,
    ) -> T:
        """Generate using OpenAI's responses.parse() API."""
        input_messages = []
        if system:
            input_messages.append({"role": "system", "content": system})
        input_messages.append({"role": "user", "content": prompt})

        response = self.client.responses.parse(
            model=self.model_id,
            input=input_messages,
            text_format=schema,
        )

        return response.output_parsed

    def _generate_anthropic(
        self,
        prompt: str,
        schema: Type[T],
        system: Optional[str] = None,
    ) -> T:
        """Generate using Anthropic's native SDK with tool use for structured output."""
        # Use tool use pattern for structured output with Anthropic
        tool_name = "structured_output"
        tools = [{
            "name": tool_name,
            "description": "Output structured data matching the schema",
            "input_schema": schema.model_json_schema(),
        }]

        messages = [{"role": "user", "content": prompt}]

        response = self.client.messages.create(
            model=self.model_id,
            max_tokens=4096,
            system=system or "",
            messages=messages,
            tools=tools,
            tool_choice={"type": "tool", "name": tool_name},
        )

        # Extract tool use result
        for block in response.content:
            if block.type == "tool_use" and block.name == tool_name:
                return schema.model_validate(block.input)

        raise ValueError("No structured output received from Anthropic")
