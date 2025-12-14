"""
Multi-Cloud LLM Provider Support

Provides a unified interface for configuring and using LLMs from:
- OpenRouter (default)
- OpenAI
- Google Vertex AI
- Amazon Bedrock
- Microsoft Azure OpenAI

This module uses litellm under the hood for provider abstraction.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

from .core.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENROUTER = "openrouter"
    OPENAI = "openai"
    VERTEX = "vertex"
    BEDROCK = "bedrock"
    AZURE = "azure"


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    extra_params: Optional[Dict[str, Any]] = None


# Default model mappings for each provider
DEFAULT_MODELS = {
    LLMProvider.OPENROUTER: "openrouter/openai/gpt-4o-mini",
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.VERTEX: "gemini-1.5-pro",
    LLMProvider.BEDROCK: "anthropic.claude-3-sonnet-20240229-v1:0",
    LLMProvider.AZURE: "gpt-4o",
}


def get_provider_config(
    provider: Optional[str] = None,
    model_name: Optional[str] = None
) -> ProviderConfig:
    """
    Get configuration for the specified provider.
    
    Args:
        provider: Provider name (defaults to MODEL_PROVIDER setting)
        model_name: Model name (defaults to MODEL_NAME setting or provider default)
        
    Returns:
        ProviderConfig with all necessary settings
    """
    provider_str = (provider or settings.MODEL_PROVIDER or "openrouter").lower()
    
    try:
        llm_provider = LLMProvider(provider_str)
    except ValueError:
        logger.warning(f"Unknown provider '{provider_str}', falling back to openrouter")
        llm_provider = LLMProvider.OPENROUTER
    
    # Get model name with fallbacks
    final_model = model_name or settings.MODEL_NAME or DEFAULT_MODELS.get(llm_provider)
    
    # Build provider-specific config
    if llm_provider == LLMProvider.OPENROUTER:
        return ProviderConfig(
            provider=llm_provider,
            model_name=final_model,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
        )
    
    elif llm_provider == LLMProvider.OPENAI:
        return ProviderConfig(
            provider=llm_provider,
            model_name=final_model,
            api_key=settings.OPENAI_API_KEY,
        )
    
    elif llm_provider == LLMProvider.VERTEX:
        return ProviderConfig(
            provider=llm_provider,
            model_name=f"vertex_ai/{final_model}",  # litellm format
            extra_params={
                "vertex_project": settings.GOOGLE_PROJECT_ID,
                "vertex_location": settings.GOOGLE_LOCATION,
            }
        )
    
    elif llm_provider == LLMProvider.BEDROCK:
        return ProviderConfig(
            provider=llm_provider,
            model_name=f"bedrock/{final_model}",  # litellm format
            extra_params={
                "aws_region_name": settings.AWS_REGION,
            }
        )
    
    elif llm_provider == LLMProvider.AZURE:
        # Azure uses deployment name in the model field
        deployment = settings.AZURE_OPENAI_DEPLOYMENT or final_model
        return ProviderConfig(
            provider=llm_provider,
            model_name=f"azure/{deployment}",  # litellm format
            api_key=settings.AZURE_OPENAI_API_KEY,
            base_url=settings.AZURE_OPENAI_ENDPOINT,
            extra_params={
                "api_version": settings.AZURE_OPENAI_API_VERSION,
            }
        )
    
    # Fallback
    return ProviderConfig(
        provider=LLMProvider.OPENROUTER,
        model_name=final_model,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
    )


def configure_environment(config: ProviderConfig) -> None:
    """
    Configure environment variables for the specified provider.
    
    This sets up the environment so that litellm and CrewAI can
    automatically pick up the correct credentials.
    
    Args:
        config: Provider configuration to apply
    """
    provider = config.provider
    
    if provider == LLMProvider.OPENROUTER:
        if config.api_key:
            os.environ["OPENROUTER_API_KEY"] = config.api_key
            # OpenRouter is OpenAI-compatible
            os.environ["OPENAI_API_KEY"] = config.api_key
        if config.base_url:
            os.environ["OPENAI_BASE_URL"] = config.base_url
            os.environ["OPENAI_API_BASE"] = config.base_url
        os.environ.setdefault("LITELLM_PROVIDER", "openrouter")
        
    elif provider == LLMProvider.OPENAI:
        if config.api_key:
            os.environ["OPENAI_API_KEY"] = config.api_key
            
    elif provider == LLMProvider.VERTEX:
        if settings.GOOGLE_PROJECT_ID:
            os.environ["GOOGLE_PROJECT_ID"] = settings.GOOGLE_PROJECT_ID
            os.environ["VERTEXAI_PROJECT"] = settings.GOOGLE_PROJECT_ID
        if settings.GOOGLE_LOCATION:
            os.environ["GOOGLE_LOCATION"] = settings.GOOGLE_LOCATION
            os.environ["VERTEXAI_LOCATION"] = settings.GOOGLE_LOCATION
        if settings.GOOGLE_APPLICATION_CREDENTIALS:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS
            
    elif provider == LLMProvider.BEDROCK:
        os.environ["AWS_REGION_NAME"] = settings.AWS_REGION
        os.environ["AWS_DEFAULT_REGION"] = settings.AWS_REGION
        if settings.AWS_ACCESS_KEY_ID:
            os.environ["AWS_ACCESS_KEY_ID"] = settings.AWS_ACCESS_KEY_ID
        if settings.AWS_SECRET_ACCESS_KEY:
            os.environ["AWS_SECRET_ACCESS_KEY"] = settings.AWS_SECRET_ACCESS_KEY
        if settings.AWS_BEDROCK_RUNTIME_ENDPOINT:
            os.environ["AWS_BEDROCK_RUNTIME_ENDPOINT"] = settings.AWS_BEDROCK_RUNTIME_ENDPOINT
            
    elif provider == LLMProvider.AZURE:
        if config.api_key:
            os.environ["AZURE_API_KEY"] = config.api_key
            os.environ["AZURE_OPENAI_API_KEY"] = config.api_key
        if config.base_url:
            os.environ["AZURE_API_BASE"] = config.base_url
            os.environ["AZURE_OPENAI_ENDPOINT"] = config.base_url
        if config.extra_params:
            api_version = config.extra_params.get("api_version")
            if api_version:
                os.environ["AZURE_API_VERSION"] = api_version
    
    # Set model name for litellm
    os.environ["OPENAI_MODEL_NAME"] = config.model_name
    
    logger.info(f"Configured environment for provider: {provider.value}, model: {config.model_name}")


def get_litellm_model_string(
    provider: Optional[str] = None,
    model_name: Optional[str] = None
) -> str:
    """
    Get the litellm-compatible model string for the given provider/model.
    
    Args:
        provider: Provider name
        model_name: Model name
        
    Returns:
        Model string in litellm format (e.g., "vertex_ai/gemini-1.5-pro")
    """
    config = get_provider_config(provider, model_name)
    configure_environment(config)
    return config.model_name


def validate_provider_config(provider: str) -> Dict[str, Any]:
    """
    Validate that the required configuration is present for a provider.
    
    Args:
        provider: Provider name to validate
        
    Returns:
        Dict with 'valid' bool and 'missing' list of missing config keys
    """
    provider_str = provider.lower()
    missing = []
    
    if provider_str == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            missing.append("OPENROUTER_API_KEY")
            
    elif provider_str == "openai":
        if not settings.OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
            
    elif provider_str == "vertex":
        if not settings.GOOGLE_PROJECT_ID:
            missing.append("GOOGLE_PROJECT_ID")
        # GOOGLE_APPLICATION_CREDENTIALS is optional if running on GCP
            
    elif provider_str == "bedrock":
        # AWS credentials can come from IAM role, so nothing strictly required
        pass
        
    elif provider_str == "azure":
        if not settings.AZURE_OPENAI_API_KEY:
            missing.append("AZURE_OPENAI_API_KEY")
        if not settings.AZURE_OPENAI_ENDPOINT:
            missing.append("AZURE_OPENAI_ENDPOINT")
    
    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "provider": provider_str
    }


def list_available_providers() -> Dict[str, Dict[str, Any]]:
    """
    List all providers and their configuration status.
    
    Returns:
        Dict mapping provider names to their validation status
    """
    providers = {}
    for p in LLMProvider:
        validation = validate_provider_config(p.value)
        providers[p.value] = {
            "configured": validation["valid"],
            "missing_config": validation["missing"],
            "default_model": DEFAULT_MODELS.get(p),
        }
    return providers
