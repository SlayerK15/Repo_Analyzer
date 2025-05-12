"""
AI Provider Management for the Technology Extraction System.

This module provides functionality for managing interactions with
different AI providers, handling API calls, and fallback strategies.
"""
import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import openai
from anthropic import AsyncAnthropic
from anthropic.types import MessageParam

from tech_extraction.config import settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    async def complete(self, prompt: str, max_tokens: int = None, temperature: float = None) -> Dict:
        """
        Generate a completion for the given prompt.
        
        Args:
            prompt: The prompt to generate a completion for
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Response from the AI provider
        """
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = None, temperature: float = None) -> Dict:
        """
        Generate a chat completion for the given messages.
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Response from the AI provider
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text.
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Token count
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, api_key: str, model: str):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model to use for completions
        """
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
    
    async def complete(self, prompt: str, max_tokens: int = None, temperature: float = None) -> Dict:
        """Generate a completion using OpenAI."""
        max_tokens = max_tokens or settings.ai.max_tokens
        temperature = temperature or settings.ai.temperature
        
        try:
            response = await asyncio.to_thread(
                self.client.completions.create,
                model=self.model,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=settings.ai.request_timeout
            )
            
            return {
                "text": response.choices[0].text,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": self.model,
                "provider": "openai"
            }
        
        except Exception as e:
            logger.error(f"Error calling OpenAI completion API: {e}")
            raise
    
    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = None, temperature: float = None) -> Dict:
        """Generate a chat completion using OpenAI."""
        max_tokens = max_tokens or settings.ai.max_tokens
        temperature = temperature or settings.ai.temperature
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=settings.ai.request_timeout
            )
            
            return {
                "text": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": self.model,
                "provider": "openai"
            }
        
        except Exception as e:
            logger.error(f"Error calling OpenAI chat API: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        try:
            import tiktoken
            enc = tiktoken.encoding_for_model(self.model)
            return len(enc.encode(text))
        except ImportError:
            logger.warning("tiktoken not installed; using approximate token counting")
            # Approximate: 4 characters per token
            return int(len(text) / 4)
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Fallback to approximation
            return int(len(text) / 4)


class AnthropicProvider(AIProvider):
    """Anthropic provider implementation."""
    
    def __init__(self, api_key: str, model: str):
        """
        Initialize the Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            model: Model to use for completions
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def complete(self, prompt: str, max_tokens: int = None, temperature: float = None) -> Dict:
        """Generate a completion using Anthropic."""
        max_tokens = max_tokens or settings.ai.max_tokens
        temperature = temperature or settings.ai.temperature
        
        try:
            # Anthropic uses a chat-based API, so we'll wrap the prompt
            message: MessageParam = {
                "role": "user",
                "content": prompt
            }
            
            response = await self.client.messages.create(
                model=self.model,
                messages=[message],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            return {
                "text": response.content[0].text,
                "finish_reason": response.stop_reason,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": self.model,
                "provider": "anthropic"
            }
        
        except Exception as e:
            logger.error(f"Error calling Anthropic completion API: {e}")
            raise
    
    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = None, temperature: float = None) -> Dict:
        """Generate a chat completion using Anthropic."""
        max_tokens = max_tokens or settings.ai.max_tokens
        temperature = temperature or settings.ai.temperature
        
        try:
            # Convert OpenAI-style messages to Anthropic format
            anthropic_messages = []
            for msg in messages:
                role = "user" if msg["role"] == "user" else "assistant"
                anthropic_messages.append({"role": role, "content": msg["content"]})
            
            response = await self.client.messages.create(
                model=self.model,
                messages=anthropic_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            return {
                "text": response.content[0].text,
                "finish_reason": response.stop_reason,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": self.model,
                "provider": "anthropic"
            }
        
        except Exception as e:
            logger.error(f"Error calling Anthropic chat API: {e}")
            raise
    
    def count_tokens(self, text: str) -> int:
        """Count tokens for Anthropic."""
        try:
            from anthropic.tokenizer import count_tokens
            return count_tokens(text)
        except ImportError:
            logger.warning("anthropic tokenizer not installed; using approximate token counting")
            # Anthropic's tokenizer is roughly similar to GPT tokenizers
            # Approximate: 4 characters per token
            return int(len(text) / 4)
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Fallback to approximation
            return int(len(text) / 4)


class AIProviderManager:
    """
    Manager for AI provider interactions.
    
    Handles provider selection, fallbacks, retries, and request optimization.
    """
    
    def __init__(self):
        """Initialize the AI provider manager."""
        self.providers = {}
        self.initialize_providers()
        
        # Track token usage
        self.token_usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "estimated_cost": 0.0
        }
    
    def initialize_providers(self):
        """Initialize configured AI providers."""
        try:
            # Initialize OpenAI provider
            if settings.ai.openai_api_key:
                self.providers["openai"] = OpenAIProvider(
                    api_key=settings.ai.openai_api_key,
                    model=settings.ai.default_model
                )
                logger.info(f"Initialized OpenAI provider with model {settings.ai.default_model}")
                
                # Initialize backup model if different
                if settings.ai.backup_model != settings.ai.default_model:
                    self.providers["openai_backup"] = OpenAIProvider(
                        api_key=settings.ai.openai_api_key,
                        model=settings.ai.backup_model
                    )
                    logger.info(f"Initialized OpenAI backup provider with model {settings.ai.backup_model}")
            
            # Initialize Anthropic provider if available
            if settings.ai.anthropic_api_key:
                self.providers["anthropic"] = AnthropicProvider(
                    api_key=settings.ai.anthropic_api_key,
                    model=settings.ai.claude_model
                )
                logger.info(f"Initialized Anthropic provider with model {settings.ai.claude_model}")
        
        except Exception as e:
            logger.error(f"Error initializing AI providers: {e}")
    
    def get_provider(self, provider_name: str = None) -> AIProvider:
        """
        Get an AI provider by name.
        
        Args:
            provider_name: Name of the provider to get
            
        Returns:
            AI provider instance
            
        Raises:
            ValueError: If the provider is not available
        """
        if not provider_name:
            # Default to first available provider
            if not self.providers:
                raise ValueError("No AI providers configured")
            return next(iter(self.providers.values()))
        
        if provider_name not in self.providers:
            raise ValueError(f"Provider {provider_name} not available")
        
        return self.providers[provider_name]
    
    async def complete_with_fallback(
        self, prompt: str, max_tokens: int = None, temperature: float = None
    ) -> Dict:
        """
        Generate a completion with fallback to backup providers.
        
        Args:
            prompt: The prompt to generate a completion for
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Response from an AI provider
            
        Raises:
            RuntimeError: If all providers fail
        """
        errors = []
        
        # Try primary provider first
        try:
            provider = self.get_provider("openai")
            response = await provider.complete(prompt, max_tokens, temperature)
            self._update_token_usage(response)
            return response
        except Exception as e:
            errors.append(f"Primary provider error: {str(e)}")
        
        # Try backup provider if available
        if "openai_backup" in self.providers:
            try:
                provider = self.get_provider("openai_backup")
                response = await provider.complete(prompt, max_tokens, temperature)
                self._update_token_usage(response)
                return response
            except Exception as e:
                errors.append(f"Backup provider error: {str(e)}")
        
        # Try Anthropic if available
        if "anthropic" in self.providers:
            try:
                provider = self.get_provider("anthropic")
                response = await provider.complete(prompt, max_tokens, temperature)
                self._update_token_usage(response)
                return response
            except Exception as e:
                errors.append(f"Anthropic provider error: {str(e)}")
        
        # If we get here, all providers failed
        raise RuntimeError(f"All AI providers failed: {'; '.join(errors)}")
    
    async def chat_with_fallback(
        self, messages: List[Dict[str, str]], max_tokens: int = None, temperature: float = None
    ) -> Dict:
        """
        Generate a chat completion with fallback to backup providers.
        
        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Response from an AI provider
            
        Raises:
            RuntimeError: If all providers fail
        """
        errors = []
        
        # Try primary provider first
        try:
            provider = self.get_provider("openai")
            response = await provider.chat(messages, max_tokens, temperature)
            self._update_token_usage(response)
            return response
        except Exception as e:
            errors.append(f"Primary provider error: {str(e)}")
        
        # Try backup provider if available
        if "openai_backup" in self.providers:
            try:
                provider = self.get_provider("openai_backup")
                response = await provider.chat(messages, max_tokens, temperature)
                self._update_token_usage(response)
                return response
            except Exception as e:
                errors.append(f"Backup provider error: {str(e)}")
        
        # Try Anthropic if available
        if "anthropic" in self.providers:
            try:
                provider = self.get_provider("anthropic")
                response = await provider.chat(messages, max_tokens, temperature)
                self._update_token_usage(response)
                return response
            except Exception as e:
                errors.append(f"Anthropic provider error: {str(e)}")
        
        # If we get here, all providers failed
        raise RuntimeError(f"All AI providers failed: {'; '.join(errors)}")
    
    async def retry_with_backoff(
        self, func, *args, max_retries: int = None, **kwargs
    ) -> Dict:
        """
        Retry a function with exponential backoff.
        
        Args:
            func: Function to call
            *args: Arguments to pass to the function
            max_retries: Maximum number of retries
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result from the function
            
        Raises:
            Exception: If the function fails after all retries
        """
        max_retries = max_retries or settings.ai.retry_attempts
        retry_delay = settings.ai.retry_delay
        
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    # Calculate backoff delay
                    delay = retry_delay * (2 ** attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        
        # If we get here, all retries failed
        raise last_exception
    
    def count_tokens(self, text: str, provider_name: str = None) -> int:
        """
        Count tokens in text using the specified provider.
        
        Args:
            text: The text to count tokens for
            provider_name: Name of the provider to use
            
        Returns:
            Token count
        """
        provider = self.get_provider(provider_name)
        return provider.count_tokens(text)
    
    def _update_token_usage(self, response: Dict):
        """
        Update token usage statistics.
        
        Args:
            response: Response from an AI provider
        """
        if "usage" in response:
            usage = response["usage"]
            self.token_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
            self.token_usage["completion_tokens"] += usage.get("completion_tokens", 0)
            self.token_usage["total_tokens"] += usage.get("total_tokens", 0)
            
            # Estimate cost based on model
            # This is a simplification; actual costs vary by model and provider
            model = response.get("model", "")
            provider = response.get("provider", "")
            
            cost_per_1k_prompt = 0.01  # Default
            cost_per_1k_completion = 0.03  # Default
            
            if provider == "openai":
                if "gpt-4" in model:
                    cost_per_1k_prompt = 0.03
                    cost_per_1k_completion = 0.06
                elif "gpt-3.5" in model:
                    cost_per_1k_prompt = 0.0015
                    cost_per_1k_completion = 0.002
            elif provider == "anthropic":
                cost_per_1k_prompt = 0.008
                cost_per_1k_completion = 0.024
            
            prompt_cost = (usage.get("prompt_tokens", 0) / 1000) * cost_per_1k_prompt
            completion_cost = (usage.get("completion_tokens", 0) / 1000) * cost_per_1k_completion
            
            self.token_usage["estimated_cost"] += prompt_cost + completion_cost
    
    def get_token_usage(self) -> Dict:
        """
        Get current token usage statistics.
        
        Returns:
            Dictionary with token usage statistics
        """
        return self.token_usage
    
    async def batch_process(
        self, prompts: List[str], max_tokens: int = None, temperature: float = None
    ) -> List[Dict]:
        """
        Process a batch of prompts efficiently.
        
        Args:
            prompts: List of prompts to process
            max_tokens: Maximum tokens to generate for each prompt
            temperature: Temperature for generation
            
        Returns:
            List of responses from AI providers
        """
        batch_size = settings.ai.batch_size
        results = []
        
        # Process in batches
        for i in range(0, len(prompts), batch_size):
            batch = prompts[i:i+batch_size]
            batch_tasks = []
            
            for prompt in batch:
                task = self.retry_with_backoff(
                    self.complete_with_fallback,
                    prompt,
                    max_tokens,
                    temperature
                )
                batch_tasks.append(task)
            
            # Process batch concurrently
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle exceptions
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Error in batch processing: {result}")
                    results.append({"error": str(result)})
                else:
                    results.append(result)
            
            # Avoid rate limits
            if i + batch_size < len(prompts):
                await asyncio.sleep(1)
        
        return results