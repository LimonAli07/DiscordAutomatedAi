import os
import json
import logging
import asyncio
from enum import Enum
from typing import Dict, Any, List, Optional, Union
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel
import httpx

logger = logging.getLogger(__name__)

class ApiProvider(Enum):
    """Enum for different API providers."""
    OPENROUTER = "openrouter"
    GOOGLE_AI = "google_ai"
    CEREBRAS = "cerebras"

class ApiConfig(BaseModel):
    """Configuration for an API provider."""
    enabled: bool = False
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "default"
    retry_attempts: int = 3
    timeout: int = 60
    
    @property
    def is_configured(self) -> bool:
        """Check if the API is properly configured."""
        return self.enabled and self.api_key is not None

class APIManager:
    """Manager class for handling multiple AI API providers with failover."""
    
    def __init__(self):
        self.configs: Dict[ApiProvider, ApiConfig] = {}
        self._clients: Dict[ApiProvider, Any] = {}
        self._current_provider: Optional[ApiProvider] = None
        self._last_error: Dict[ApiProvider, str] = {}
        
        self._setup_providers()
    
    def _setup_providers(self) -> None:
        """Set up all API providers from environment variables."""
        # OpenRouter configuration
        openrouter_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        self.configs[ApiProvider.OPENROUTER] = ApiConfig(
            enabled=bool(openrouter_key),
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            model="deepseek/deepseek-chat-v3-0324:free",
            retry_attempts=2
        )
        
        # Google AI Studio configuration
        google_key = os.getenv("GOOGLE_AI_KEY")
        self.configs[ApiProvider.GOOGLE_AI] = ApiConfig(
            enabled=bool(google_key),
            api_key=google_key,
            base_url="https://generativelanguage.googleapis.com/v1beta",
            model="gemini-1.5-flash",
            retry_attempts=2
        )
        
        # Cerebras configuration
        cerebras_key = os.getenv("CEREBRAS_API_KEY")
        self.configs[ApiProvider.CEREBRAS] = ApiConfig(
            enabled=bool(cerebras_key),
            api_key=cerebras_key,
            base_url="https://cerebras.cloud/api/v1",
            model="llama-3.3-70b",
            retry_attempts=2
        )
        
        # Set the initial provider preference order
        self._set_current_provider()
        logger.info(f"API providers initialized. Active provider: {self._current_provider}")
    
    def _set_current_provider(self) -> None:
        """Set the current provider based on availability."""
        # Priority order: OpenRouter -> Google AI -> Cerebras
        for provider in [ApiProvider.OPENROUTER, ApiProvider.GOOGLE_AI, ApiProvider.CEREBRAS]:
            if self.configs[provider].is_configured:
                self._current_provider = provider
                return
        
        # If no providers are configured, default to OpenRouter but log a warning
        self._current_provider = ApiProvider.OPENROUTER
        logger.warning("No API providers are properly configured. Default to OpenRouter but it may not work.")
    
    def _get_client(self, provider: ApiProvider) -> Any:
        """Get or create an API client for the specified provider."""
        if provider not in self._clients:
            config = self.configs[provider]
            
            if provider == ApiProvider.OPENROUTER:
                self._clients[provider] = OpenAI(
                    base_url=config.base_url,
                    api_key=config.api_key
                )
            elif provider == ApiProvider.GOOGLE_AI:
                # Google AI doesn't use OpenAI client, but we'll handle API calls directly
                self._clients[provider] = httpx.AsyncClient(timeout=config.timeout)
            elif provider == ApiProvider.CEREBRAS:
                # For Cerebras, we'll use the OpenAI client with their API endpoint
                self._clients[provider] = OpenAI(
                    base_url=config.base_url,
                    api_key=config.api_key
                )
        
        return self._clients[provider]
    
    async def call_api_with_fallback(self, system_prompt: str, user_prompt: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Call an AI API with automatic fallback to other providers if one fails.
        
        Args:
            system_prompt: The system instructions
            user_prompt: The user's prompt
            tools: Optional function tools for function calling
            
        Returns:
            Dict with response data containing:
                - content: The text response
                - tool_calls: Any tool/function calls (if applicable)
                - provider: Which API provider was used
        """
        # Start with the current preferred provider
        providers_to_try = list(ApiProvider)
        
        # Reorder to start with the current provider
        if self._current_provider in providers_to_try:
            providers_to_try.remove(self._current_provider)
            providers_to_try.insert(0, self._current_provider)
        
        last_error = None
        
        # Try each provider in order until one succeeds
        for provider in providers_to_try:
            config = self.configs[provider]
            if not config.is_configured:
                continue
            
            for attempt in range(config.retry_attempts):
                try:
                    logger.info(f"Trying provider: {provider.value}, attempt {attempt+1}/{config.retry_attempts}")
                    response = await self._make_api_call(provider, system_prompt, user_prompt, tools)
                    
                    # If successful, update the current provider preference
                    self._current_provider = provider
                    logger.info(f"Successfully used provider: {provider.value}")
                    
                    return {
                        **response,
                        "provider": provider.value
                    }
                
                except Exception as e:
                    last_error = str(e)
                    self._last_error[provider] = last_error
                    logger.warning(f"Error with provider {provider.value}: {str(e)}")
                    # Small delay before retry or next provider
                    await asyncio.sleep(1)
        
        # If all providers failed, raise an exception
        raise Exception(f"All API providers failed. Last error: {last_error}")
    
    async def _make_api_call(self, provider: ApiProvider, system_prompt: str, user_prompt: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make an API call to the specified provider."""
        config = self.configs[provider]
        client = self._get_client(provider)
        
        if provider == ApiProvider.OPENROUTER:
            return await self._call_openrouter(client, config, system_prompt, user_prompt, tools)
        elif provider == ApiProvider.GOOGLE_AI:
            return await self._call_google_ai(client, config, system_prompt, user_prompt, tools)
        elif provider == ApiProvider.CEREBRAS:
            return await self._call_cerebras(client, config, system_prompt, user_prompt, tools)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _call_openrouter(self, client, config: ApiConfig, system_prompt: str, user_prompt: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call the OpenRouter API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        kwargs = {
            "model": config.model,
            "messages": messages
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        result = {
            "content": message.content or "",
            "tool_calls": []
        }
        
        # Check for tool calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = []
            for tool_call in message.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments)
                except:
                    args = {}
                    
                tool_calls.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "args": args
                })
            result["tool_calls"] = tool_calls
        
        return result
    
    async def _call_google_ai(self, client, config: ApiConfig, system_prompt: str, user_prompt: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call the Google AI API."""
        # Convert OpenAI-style tools to Google AI format if provided
        google_tools = None
        if tools:
            google_tools = []
            for tool in tools:
                if tool.get("type") == "function":
                    function_details = tool.get("function", {})
                    google_tools.append({
                        "functionDeclarations": [{
                            "name": function_details.get("name"),
                            "description": function_details.get("description", ""),
                            "parameters": function_details.get("parameters", {})
                        }]
                    })
        
        # Format the prompt for Google AI
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Construct the API request
        api_url = f"{config.base_url}/models/{config.model}:generateContent"
        params = {"key": config.api_key}
        
        request_data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"System: {system_prompt}\n\nUser: {user_prompt}"}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 4096
            }
        }
        
        if google_tools:
            request_data["tools"] = google_tools
        
        # Make the API call
        async with client as session:
            response = await session.post(api_url, params=params, json=request_data)
            response.raise_for_status()
            data = response.json()
        
        # Process the response
        result = {"content": "", "tool_calls": []}
        
        # Extract the content
        try:
            candidate = data["candidates"][0]
            result["content"] = candidate["content"]["parts"][0]["text"]
            
            # Extract function calls if present
            if "functionCalls" in candidate:
                for function_call in candidate["functionCalls"]:
                    args = {}
                    try:
                        for arg in function_call.get("args", []):
                            args[arg["name"]] = arg["value"]
                    except:
                        pass
                    
                    result["tool_calls"].append({
                        "id": f"gemini-call-{len(result['tool_calls'])}",
                        "name": function_call["name"],
                        "args": args
                    })
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Google AI response: {e}")
            raise ValueError(f"Invalid response format from Google AI: {str(e)}")
        
        return result
    
    async def _call_cerebras(self, client, config: ApiConfig, system_prompt: str, user_prompt: str, tools: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Call the Cerebras API."""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        kwargs = {
            "model": config.model,
            "messages": messages
        }
        
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        
        response = client.chat.completions.create(**kwargs)
        message = response.choices[0].message
        
        result = {
            "content": message.content or "",
            "tool_calls": []
        }
        
        # Check for tool calls
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tool_calls = []
            for tool_call in message.tool_calls:
                try:
                    args = json.loads(tool_call.function.arguments)
                except:
                    args = {}
                    
                tool_calls.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "args": args
                })
            result["tool_calls"] = tool_calls
        
        return result
    
    def get_last_errors(self) -> Dict[str, str]:
        """Get the most recent errors from each provider."""
        return {provider.value: error for provider, error in self._last_error.items()}
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get the status of all providers."""
        return {
            provider.value: {
                "enabled": config.enabled,
                "configured": config.is_configured,
                "model": config.model,
                "is_current": provider == self._current_provider,
                "last_error": self._last_error.get(provider, None)
            }
            for provider, config in self.configs.items()
        }