"""
OpenAI Agent SDK Integration Module

This module provides a wrapper class for the OpenAI SDK to enable AI-driven 
decision-making within the orchestrator service. It handles initialization of 
the OpenAI client, sending prompts, and receiving responses with proper 
error handling and logging.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion

from app.core.config import settings

# Setup logger
logger = logging.getLogger(__name__)


class OpenAIAgent:
    """
    A wrapper class for the OpenAI SDK that provides a simplified interface
    for interacting with OpenAI's models.
    """

    def __init__(self, async_client: bool = False):
        """
        Initialize the OpenAI agent with configuration from settings.

        Args:
            async_client (bool): Whether to initialize an async client or not
        """
        self.api_key = settings.OPENAI_API_KEY
        self.base_url = settings.OPENAI_BASE_URL
        self.model = settings.OPENAI_MODEL
        self.async_client = async_client

        # Validate that API key is provided for client construction
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set in configuration. "
                "Please set it in your .env file or environment variables."
            )

        # Initialize the appropriate client
        if self.async_client:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info("Initialized OpenAI async client")
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info("Initialized OpenAI client")

    def send_prompt(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a prompt to the OpenAI model and return the response.

        Args:
            prompt (str): The user prompt to send to the model
            system_message (Optional[str]): System message to set context
            temperature (float): Sampling temperature (0.0 to 1.0)
            max_tokens (Optional[int]): Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the API

        Returns:
            Dict[str, Any]: The response from the model, including content and metadata

        Raises:
            Exception: If there's an error communicating with the OpenAI API
        """
        try:
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            # Prepare parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            # Send request
            logger.info(f"Sending prompt to OpenAI model {self.model}")
            response: ChatCompletion = self.client.chat.completions.create(**params)

            # Extract relevant information
            result = {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    "total_tokens": response.usage.total_tokens if response.usage else None,
                },
                "model": response.model,
                "created": response.created,
            }

            logger.info(f"Received response from OpenAI model {self.model}")
            return result

        except Exception as e:
            logger.error(f"Error communicating with OpenAI API: {str(e)}")
            raise

    async def send_prompt_async(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a prompt to the OpenAI model asynchronously and return the response.

        Args:
            prompt (str): The user prompt to send to the model
            system_message (Optional[str]): System message to set context
            temperature (float): Sampling temperature (0.0 to 1.0)
            max_tokens (Optional[int]): Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the API

        Returns:
            Dict[str, Any]: The response from the model, including content and metadata

        Raises:
            Exception: If there's an error communicating with the OpenAI API
        """
        if not self.async_client:
            raise ValueError("This method requires an async client. Initialize with async_client=True")

        try:
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})

            # Prepare parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            # Send request
            logger.info(f"Sending async prompt to OpenAI model {self.model}")
            response: ChatCompletion = await self.client.chat.completions.create(**params)

            # Extract relevant information
            result = {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    "total_tokens": response.usage.total_tokens if response.usage else None,
                },
                "model": response.model,
                "created": response.created,
            }

            logger.info(f"Received async response from OpenAI model {self.model}")
            return result

        except Exception as e:
            logger.error(f"Error communicating with OpenAI API: {str(e)}")
            raise

    def send_structured_prompt(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a structured prompt (list of message dicts) to the OpenAI model.

        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            temperature (float): Sampling temperature (0.0 to 1.0)
            max_tokens (Optional[int]): Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the API

        Returns:
            Dict[str, Any]: The response from the model, including content and metadata

        Raises:
            Exception: If there's an error communicating with the OpenAI API
        """
        try:
            # Prepare parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            # Send request
            logger.info(f"Sending structured prompt to OpenAI model {self.model}")
            response: ChatCompletion = self.client.chat.completions.create(**params)

            # Extract relevant information
            result = {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    "total_tokens": response.usage.total_tokens if response.usage else None,
                },
                "model": response.model,
                "created": response.created,
            }

            logger.info(f"Received response from OpenAI model {self.model}")
            return result

        except Exception as e:
            logger.error(f"Error communicating with OpenAI API: {str(e)}")
            raise

    async def send_structured_prompt_async(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a structured prompt (list of message dicts) to the OpenAI model asynchronously.

        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'
            temperature (float): Sampling temperature (0.0 to 1.0)
            max_tokens (Optional[int]): Maximum number of tokens to generate
            **kwargs: Additional arguments to pass to the API

        Returns:
            Dict[str, Any]: The response from the model, including content and metadata

        Raises:
            Exception: If there's an error communicating with the OpenAI API
        """
        if not self.async_client:
            raise ValueError("This method requires an async client. Initialize with async_client=True")

        try:
            # Prepare parameters
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                **kwargs
            }
            
            if max_tokens is not None:
                params["max_tokens"] = max_tokens

            # Send request
            logger.info(f"Sending async structured prompt to OpenAI model {self.model}")
            response: ChatCompletion = await self.client.chat.completions.create(**params)

            # Extract relevant information
            result = {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                    "completion_tokens": response.usage.completion_tokens if response.usage else None,
                    "total_tokens": response.usage.total_tokens if response.usage else None,
                },
                "model": response.model,
                "created": response.created,
            }

            logger.info(f"Received async response from OpenAI model {self.model}")
            return result

        except Exception as e:
            logger.error(f"Error communicating with OpenAI API: {str(e)}")
            raise


# Avoid instantiating global clients at import time to prevent failures when
# OPENAI_API_KEY isn't configured (e.g., in test environments). Provide
# optional factory helpers for consumers that still want a shortcut.

def get_sync_agent() -> OpenAIAgent:
    return OpenAIAgent(async_client=False)


def get_async_agent() -> OpenAIAgent:
    return OpenAIAgent(async_client=True)


# Backwards compatibility alias
OpenAIWrapper = OpenAIAgent
