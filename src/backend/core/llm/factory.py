"""
Factory for creating LLM provider instances.

Manages provider instantiation and configuration.
"""

from enum import Enum
from typing import Dict, Type, Optional

from src.backend.core.llm.base import LLMProvider
from src.backend.core.llm.anthropic import AnthropicProvider
from src.backend.core.config import settings
from src.backend.config.logging_config import get_logger

logger = get_logger(__name__)


class ProviderType(str, Enum):
    """Available LLM provider types."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"  # To be implemented
    GOOGLE = "google"  # To be implemented


class LLMFactory:
    """Factory for creating LLM provider instances."""
    
    # Registry of available providers
    _providers: Dict[ProviderType, Type[LLMProvider]] = {
        ProviderType.ANTHROPIC: AnthropicProvider,
        # Add more providers here as they are implemented
    }
    
    # Cached provider instances
    _instances: Dict[ProviderType, LLMProvider] = {}
    
    @classmethod
    def create_provider(
        cls,
        provider_type: ProviderType,
        api_key: Optional[str] = None,
        **kwargs
    ) -> LLMProvider:
        """
        Create or retrieve an LLM provider instance.
        
        Args:
            provider_type: Type of provider to create
            api_key: API key for the provider (uses env var if not provided)
            **kwargs: Additional provider-specific configuration
            
        Returns:
            LLMProvider instance
            
        Raises:
            ValueError: If provider type is not supported
            KeyError: If API key is not provided and not in environment
        """
        if provider_type not in cls._providers:
            raise ValueError(
                f"Provider '{provider_type}' not supported. "
                f"Available providers: {', '.join(cls._providers.keys())}"
            )
        
        # Get API key from environment if not provided
        if api_key is None:
            env_var_map = {
                ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
                ProviderType.OPENAI: "OPENAI_API_KEY",
                ProviderType.GOOGLE: "GOOGLE_API_KEY",
            }
            
            env_var = env_var_map.get(provider_type)
            if env_var:
                api_key = getattr(settings, env_var.lower(), None)
                
            if not api_key:
                raise KeyError(
                    f"API key not provided and {env_var} not found in environment"
                )
        
        # Create cache key
        cache_key = f"{provider_type}:{api_key[:8]}..."  # Use first 8 chars of key
        
        # Check cache
        if cache_key in cls._instances:
            logger.debug("Using cached provider instance", provider=provider_type)
            return cls._instances[cache_key]
        
        # Create new instance
        provider_class = cls._providers[provider_type]
        provider = provider_class(api_key, **kwargs)
        
        # Cache instance
        cls._instances[cache_key] = provider
        
        logger.info(
            "Created new LLM provider instance",
            provider=provider_type,
            cached=True,
        )
        
        return provider
    
    @classmethod
    def register_provider(
        cls,
        provider_type: ProviderType,
        provider_class: Type[LLMProvider]
    ) -> None:
        """
        Register a new provider type.
        
        Args:
            provider_type: Type identifier for the provider
            provider_class: Provider class that implements LLMProvider
        """
        cls._providers[provider_type] = provider_class
        logger.info(
            "Registered new LLM provider",
            provider=provider_type,
            class_name=provider_class.__name__,
        )
    
    @classmethod
    def get_default_provider(cls) -> LLMProvider:
        """
        Get the default LLM provider based on configuration.
        
        Returns:
            Default LLMProvider instance
        """
        # Default to Anthropic Claude
        default_provider = getattr(settings, "default_llm_provider", ProviderType.ANTHROPIC)
        return cls.create_provider(default_provider)
    
    @classmethod
    def clear_cache(cls) -> None:
        """Clear all cached provider instances."""
        cls._instances.clear()
        logger.info("Cleared LLM provider cache")


# Convenience function
def get_llm_provider(
    provider_type: Optional[ProviderType] = None,
    **kwargs
) -> LLMProvider:
    """
    Get an LLM provider instance.
    
    Args:
        provider_type: Type of provider (uses default if not specified)
        **kwargs: Additional provider configuration
        
    Returns:
        LLMProvider instance
    """
    if provider_type is None:
        return LLMFactory.get_default_provider()
    
    return LLMFactory.create_provider(provider_type, **kwargs) 