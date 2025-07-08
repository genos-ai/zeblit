"""
Base interface and models for LLM providers.

Defines the contract that all LLM implementations must follow.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, AsyncIterator
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.backend.config.logging_config import get_logger

logger = get_logger(__name__)


class LLMRole(str, Enum):
    """Role of the message sender in a conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    """Represents a single message in a conversation."""
    role: LLMRole
    content: str
    name: Optional[str] = None  # For multi-agent conversations
    metadata: Dict[str, Any] = Field(default_factory=dict)


@dataclass
class TokenUsage:
    """Token usage statistics for a request."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    @property
    def cost_usd(self) -> float:
        """Calculate cost in USD (to be overridden by specific providers)."""
        return 0.0


class LLMResponse(BaseModel):
    """Response from an LLM provider."""
    id: UUID = Field(default_factory=uuid4)
    model: str
    content: str
    finish_reason: Optional[str] = None
    usage: Optional[TokenUsage] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True


class LLMConfig(BaseModel):
    """Configuration for LLM requests."""
    model: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=2000, gt=0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    stop_sequences: List[str] = Field(default_factory=list)
    stream: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    def __init__(self, message: str, provider: str, details: Optional[Dict[str, Any]] = None):
        self.provider = provider
        self.details = details or {}
        super().__init__(message)


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, **kwargs):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
        logger.info(
            "Initializing LLM provider",
            provider=self.__class__.__name__,
            config_keys=list(kwargs.keys())
        )
    
    @abstractmethod
    async def complete(
        self,
        messages: List[LLMMessage],
        config: LLMConfig
    ) -> LLMResponse:
        """
        Generate a completion for the given messages.
        
        Args:
            messages: List of messages in the conversation
            config: Configuration for the completion request
            
        Returns:
            LLMResponse with the generated completion
            
        Raises:
            LLMError: If the request fails
        """
        pass
    
    @abstractmethod
    async def stream_complete(
        self,
        messages: List[LLMMessage],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """
        Stream a completion for the given messages.
        
        Args:
            messages: List of messages in the conversation
            config: Configuration for the completion request
            
        Yields:
            Chunks of the generated completion
            
        Raises:
            LLMError: If the request fails
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Count the number of tokens in the given text.
        
        Args:
            text: Text to count tokens for
            model: Model to use for tokenization
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    def calculate_cost(self, usage: TokenUsage, model: str) -> float:
        """
        Calculate the cost for the given token usage.
        
        Args:
            usage: Token usage statistics
            model: Model used for the request
            
        Returns:
            Cost in USD
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """
        Get list of supported models for this provider.
        
        Returns:
            List of model names
        """
        pass
    
    def validate_config(self, config: LLMConfig) -> None:
        """
        Validate the configuration for this provider.
        
        Args:
            config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        supported_models = self.get_supported_models()
        if config.model not in supported_models:
            raise ValueError(
                f"Model '{config.model}' not supported. "
                f"Supported models: {', '.join(supported_models)}"
            )
    
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try a minimal request
            test_messages = [
                LLMMessage(role=LLMRole.USER, content="Hi")
            ]
            test_config = LLMConfig(
                model=self.get_supported_models()[0],
                max_tokens=10,
                temperature=0
            )
            
            response = await self.complete(test_messages, test_config)
            return bool(response.content)
            
        except Exception as e:
            logger.error(
                "Health check failed",
                provider=self.__class__.__name__,
                error=str(e)
            )
            return False 