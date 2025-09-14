"""
LLM client with multi-provider support and fallback
"""

import os
import logging
from typing import List, Dict, Optional, Any
from openai import OpenAI
from anthropic import Anthropic

from src.config import (
    OPENAI_API_KEY, 
    ANTHROPIC_API_KEY, 
    PRIMARY_LLM_PROVIDER,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS
)

logger = logging.getLogger(__name__)

class LLMClient:
    """Multi-provider LLM client with automatic fallback"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.primary_provider = PRIMARY_LLM_PROVIDER
        
        # Initialize OpenAI client
        if OPENAI_API_KEY:
            try:
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
        
        # Initialize Anthropic client
        if ANTHROPIC_API_KEY:
            try:
                self.anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
        
        # Validate configuration
        if not self.openai_client and not self.anthropic_client:
            logger.error("No LLM clients available. Please configure API keys.")
    
    def chat(self, messages: List[Dict[str, str]], 
             temperature: float = LLM_TEMPERATURE,
             max_tokens: int = LLM_MAX_TOKENS,
             model: Optional[str] = None) -> str:
        """Send chat request with automatic fallback"""
        
        # Try primary provider first
        try:
            if self.primary_provider == "openai" and self.openai_client:
                return self._openai_chat(messages, temperature, max_tokens, model)
            elif self.primary_provider == "anthropic" and self.anthropic_client:
                return self._anthropic_chat(messages, temperature, max_tokens, model)
        except Exception as e:
            logger.warning(f"Primary LLM provider ({self.primary_provider}) failed: {e}")
        
        # Try fallback provider
        try:
            if self.primary_provider == "openai" and self.anthropic_client:
                logger.info("Falling back to Anthropic")
                return self._anthropic_chat(messages, temperature, max_tokens, model)
            elif self.primary_provider == "anthropic" and self.openai_client:
                logger.info("Falling back to OpenAI")
                return self._openai_chat(messages, temperature, max_tokens, model)
        except Exception as e:
            logger.error(f"Fallback LLM provider also failed: {e}")
        
        # If both fail, return error message
        return "I'm having trouble connecting to the AI service right now. Please try again in a moment."
    
    def _openai_chat(self, messages: List[Dict[str, str]], 
                    temperature: float, max_tokens: int, 
                    model: Optional[str] = None) -> str:
        """OpenAI API call"""
        if not self.openai_client:
            raise Exception("OpenAI client not available")
        
        # Default to GPT-4o mini for cost efficiency
        if not model:
            model = "gpt-4o-mini"
        
        response = self.openai_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content or ""
    
    def _anthropic_chat(self, messages: List[Dict[str, str]], 
                       temperature: float, max_tokens: int,
                       model: Optional[str] = None) -> str:
        """Anthropic API call"""
        if not self.anthropic_client:
            raise Exception("Anthropic client not available")
        
        # Default to Claude 3.5 Haiku for cost efficiency
        if not model:
            model = "claude-3-5-haiku-20241022"
        
        # Convert OpenAI format to Anthropic format
        system_message = ""
        anthropic_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Create the request
        kwargs = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if system_message:
            kwargs["system"] = system_message
        
        response = self.anthropic_client.messages.create(**kwargs)
        
        return response.content[0].text if response.content else ""
    
    def is_available(self) -> bool:
        """Check if at least one LLM provider is available"""
        return self.openai_client is not None or self.anthropic_client is not None
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        providers = []
        if self.openai_client:
            providers.append("openai")
        if self.anthropic_client:
            providers.append("anthropic")
        return providers
