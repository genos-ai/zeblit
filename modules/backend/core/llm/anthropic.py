"""
Anthropic Claude LLM provider implementation.

Supports Claude 3 Opus, Sonnet, and Haiku models.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, AsyncIterator

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from modules.backend.core.llm.base import (
    LLMProvider,
    LLMResponse,
    LLMMessage,
    LLMRole,
    LLMConfig,
    LLMError,
    TokenUsage,
)
from modules.backend.config.logging_config import get_logger, log_llm_request, log_llm_response

logger = get_logger(__name__)


class AnthropicError(LLMError):
    """Anthropic-specific error."""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "anthropic", details)
        self.status_code = status_code


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""
    
    API_URL = "https://api.anthropic.com/v1/messages"
    API_VERSION = "2023-06-01"
    
    # Model configurations with pricing (per 1M tokens)
    MODEL_CONFIG = {
        # Claude 4 Family
        "claude-opus-4-1-20250805": {
            "max_tokens": 8192,
            "input_price": 20.00,   # Estimated pricing for Claude 4
            "output_price": 100.00,
        },
        "claude-opus-4-20250514": {
            "max_tokens": 8192,
            "input_price": 18.00,   # Estimated pricing for Claude 4
            "output_price": 90.00,
        },
        "claude-sonnet-4-20250514": {
            "max_tokens": 8192,
            "input_price": 5.00,    # Estimated pricing for Claude 4
            "output_price": 25.00,
        },
        # Claude 3.7
        "claude-3-7-sonnet-20250219": {
            "max_tokens": 8192,
            "input_price": 4.00,
            "output_price": 20.00,
        },
        # Claude 3.5
        "claude-3-5-sonnet-20241022": {
            "max_tokens": 8192,
            "input_price": 3.00,
            "output_price": 15.00,
        },
        "claude-3-5-haiku-20241022": {
            "max_tokens": 8192,
            "input_price": 1.00,
            "output_price": 5.00,
        },
        "claude-3-5-sonnet-20240620": {
            "max_tokens": 8192,
            "input_price": 3.00,
            "output_price": 15.00,
        },
        # Claude 3 Legacy
        "claude-3-opus-20240229": {
            "max_tokens": 4096,
            "input_price": 15.00,
            "output_price": 75.00,
        },
        "claude-3-haiku-20240307": {
            "max_tokens": 4096,
            "input_price": 0.25,
            "output_price": 1.25,
        },
        # Aliases for convenience (point to latest Claude 4)
        "claude-4-opus": "claude-opus-4-1-20250805",
        "claude-4-sonnet": "claude-sonnet-4-20250514",
        "claude-3-opus": "claude-3-opus-20240229",
        "claude-3-haiku": "claude-3-haiku-20240307",
    }
    
    def __init__(self, api_key: str, timeout: float = 30.0, max_retries: int = 3):
        """
        Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key)
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={
                "x-api-key": api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json",
            },
        )
    
    def get_supported_models(self) -> List[str]:
        """Get list of supported Claude models."""
        return list(self.MODEL_CONFIG.keys())
    
    def _resolve_model(self, model: str) -> str:
        """Resolve model aliases to full model names."""
        if model in self.MODEL_CONFIG:
            return model
        return model
    
    def _convert_messages(self, messages: List[LLMMessage]) -> tuple[Optional[str], List[Dict[str, str]]]:
        """
        Convert messages to Anthropic format.
        
        Returns:
            Tuple of (system_prompt, messages)
        """
        system_prompt = None
        anthropic_messages = []
        
        for msg in messages:
            if msg.role == LLMRole.SYSTEM:
                # Anthropic uses a separate system parameter
                system_prompt = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role.value,
                    "content": msg.content,
                })
        
        return system_prompt, anthropic_messages
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.TimeoutException),
    )
    async def complete(
        self,
        messages: List[LLMMessage],
        config: LLMConfig
    ) -> LLMResponse:
        """Generate a completion using Claude."""
        self.validate_config(config)
        
        # Resolve model name
        model = self._resolve_model(config.model)
        
        # Convert messages
        system_prompt, anthropic_messages = self._convert_messages(messages)
        
        # Build request
        request_data = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": config.max_tokens or self.MODEL_CONFIG[model]["max_tokens"],
            "temperature": config.temperature,
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        # Anthropic API doesn't allow both temperature and top_p
        # Use temperature if provided, otherwise use top_p
        if config.temperature != 0.7:  # If temperature is explicitly set
            # Already added temperature above, don't add top_p
            pass
        elif config.top_p is not None and config.top_p != 1.0:
            # Only use top_p if temperature is default and top_p is explicitly set
            del request_data["temperature"]
            request_data["top_p"] = config.top_p
        
        if config.stop_sequences:
            request_data["stop_sequences"] = config.stop_sequences
        
        # Log request
        start_time = time.time()
        req_logger = log_llm_request(
            model=model,
            prompt_tokens=0,  # Will update after response
            max_tokens=request_data["max_tokens"],
            temperature=config.temperature,
            provider="anthropic",
        )
        
        try:
            # Make request
            response = await self.client.post(
                self.API_URL,
                json=request_data,
            )
            
            # Check for errors
            if response.status_code != 200:
                error_data = response.json()
                raise AnthropicError(
                    f"API request failed: {error_data.get('error', {}).get('message', 'Unknown error')}",
                    status_code=response.status_code,
                    details=error_data,
                )
            
            # Parse response
            data = response.json()
            
            # Extract content
            content = data["content"][0]["text"]
            
            # Create token usage
            usage = TokenUsage(
                prompt_tokens=data["usage"]["input_tokens"],
                completion_tokens=data["usage"]["output_tokens"],
                total_tokens=data["usage"]["input_tokens"] + data["usage"]["output_tokens"],
            )
            
            # Calculate cost
            cost = self.calculate_cost(usage, model)
            
            # Log response
            duration_ms = (time.time() - start_time) * 1000
            log_llm_response(
                req_logger,
                response_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                cost_usd=cost,
                duration_ms=duration_ms,
                model_version=model,
            )
            
            # Create response
            return LLMResponse(
                model=model,
                content=content,
                finish_reason=data.get("stop_reason"),
                usage=usage,
                metadata={
                    "id": data["id"],
                    "model": data["model"],
                    "stop_reason": data.get("stop_reason"),
                    "cost_usd": cost,
                },
            )
            
        except httpx.TimeoutException:
            logger.error("Anthropic API request timed out", model=model, timeout=self.timeout)
            raise AnthropicError(f"Request timed out after {self.timeout}s")
            
        except httpx.HTTPError as e:
            logger.error("HTTP error during Anthropic API request", error=str(e))
            raise AnthropicError(f"HTTP error: {str(e)}")
            
        except Exception as e:
            logger.error("Unexpected error during Anthropic API request", error=str(e), exc_info=True)
            raise AnthropicError(f"Unexpected error: {str(e)}")
    
    async def stream_complete(
        self,
        messages: List[LLMMessage],
        config: LLMConfig
    ) -> AsyncIterator[str]:
        """Stream a completion using Claude."""
        self.validate_config(config)
        
        # Resolve model name
        model = self._resolve_model(config.model)
        
        # Convert messages
        system_prompt, anthropic_messages = self._convert_messages(messages)
        
        # Build request
        request_data = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": config.max_tokens or self.MODEL_CONFIG[model]["max_tokens"],
            "temperature": config.temperature,
            "stream": True,
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        # Anthropic API doesn't allow both temperature and top_p
        # Use temperature if provided, otherwise use top_p
        if config.temperature != 0.7:  # If temperature is explicitly set
            # Already added temperature above, don't add top_p
            pass
        elif config.top_p is not None and config.top_p != 1.0:
            # Only use top_p if temperature is default and top_p is explicitly set
            del request_data["temperature"]
            request_data["top_p"] = config.top_p
        
        if config.stop_sequences:
            request_data["stop_sequences"] = config.stop_sequences
        
        try:
            # Make streaming request
            async with self.client.stream(
                "POST",
                self.API_URL,
                json=request_data,
            ) as response:
                if response.status_code != 200:
                    error_text = await response.aread()
                    raise AnthropicError(
                        f"API request failed: {error_text.decode()}",
                        status_code=response.status_code,
                    )
                
                # Process stream
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        
                        if data == "[DONE]":
                            break
                        
                        try:
                            import json
                            event = json.loads(data)
                            
                            if event["type"] == "content_block_delta":
                                yield event["delta"]["text"]
                                
                        except json.JSONDecodeError:
                            logger.warning("Failed to parse streaming response", data=data)
                            
        except httpx.TimeoutException:
            logger.error("Anthropic API streaming request timed out", model=model)
            raise AnthropicError(f"Streaming request timed out")
            
        except Exception as e:
            logger.error("Error during streaming", error=str(e), exc_info=True)
            raise AnthropicError(f"Streaming error: {str(e)}")
    
    async def count_tokens(self, text: str, model: str) -> int:
        """
        Estimate token count for text.
        
        Note: This is an approximation. For exact counts, use Anthropic's tokenizer.
        """
        # Rough approximation: ~4 characters per token
        # This is a simplified approach; in production, use tiktoken or Anthropic's tokenizer
        return len(text) // 4
    
    def calculate_cost(self, usage: TokenUsage, model: str) -> float:
        """Calculate cost for the given token usage."""
        model = self._resolve_model(model)
        
        if model not in self.MODEL_CONFIG:
            logger.warning(f"Unknown model for cost calculation: {model}")
            return 0.0
        
        config = self.MODEL_CONFIG[model]
        
        # Calculate cost (prices are per 1M tokens)
        input_cost = (usage.prompt_tokens / 1_000_000) * config["input_price"]
        output_cost = (usage.completion_tokens / 1_000_000) * config["output_price"]
        
        return round(input_cost + output_cost, 6)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close HTTP client."""
        await self.client.aclose() 