"""
Test module for the OpenAI Agent SDK integration.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.openai_agent import OpenAIAgent


def test_openai_agent_initialization():
    """Test that the OpenAI agent initializes correctly with valid configuration."""
    with patch('app.core.config.settings.OPENAI_API_KEY', 'test-key'), \
         patch('app.core.config.settings.OPENAI_BASE_URL', 'https://api.openai.com/v1'), \
         patch('app.core.config.settings.OPENAI_MODEL', 'gpt-4o-mini'):
        
        agent = OpenAIAgent()
        assert agent.api_key == 'test-key'
        assert agent.base_url == 'https://api.openai.com/v1'
        assert agent.model == 'gpt-4o-mini'
        assert agent.async_client == False


def test_openai_agent_initialization_async():
    """Test that the OpenAI agent initializes correctly with async client."""
    with patch('app.core.config.settings.OPENAI_API_KEY', 'test-key'), \
         patch('app.core.config.settings.OPENAI_BASE_URL', 'https://api.openai.com/v1'), \
         patch('app.core.config.settings.OPENAI_MODEL', 'gpt-4o-mini'):
        
        agent = OpenAIAgent(async_client=True)
        assert agent.api_key == 'test-key'
        assert agent.base_url == 'https://api.openai.com/v1'
        assert agent.model == 'gpt-4o-mini'
        assert agent.async_client == True


def test_openai_agent_missing_api_key():
    """Test that the OpenAI agent raises an error when API key is missing."""
    with patch('app.core.config.settings.OPENAI_API_KEY', ''):
        with pytest.raises(ValueError, match="OPENAI_API_KEY is not set in configuration"):
            OpenAIAgent()


@patch('app.core.openai_agent.OpenAI')
def test_send_prompt(mock_openai):
    """Test sending a prompt to the OpenAI model."""
    # Mock the OpenAI client and response
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    mock_message.content = "Test response"
    mock_message.role = "assistant"
    mock_choice.message = mock_message
    mock_choice.finish_reason = "stop"
    mock_response.choices = [mock_choice]
    mock_response.model = "gpt-4o-mini"
    mock_response.created = 1234567890
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 20
    mock_usage.total_tokens = 30
    mock_response.usage = mock_usage
    
    mock_client.chat.completions.create.return_value = mock_response
    mock_openai.return_value = mock_client
    
    # Initialize agent with mocked client
    with patch('app.core.config.settings.OPENAI_API_KEY', 'test-key'):
        agent = OpenAIAgent()
        agent.client = mock_client
        
        # Send a test prompt
        result = agent.send_prompt("Hello, world!")
        
        # Verify the result
        assert result["content"] == "Test response"
        assert result["role"] == "assistant"
        assert result["finish_reason"] == "stop"
        assert result["model"] == "gpt-4o-mini"
        assert result["usage"]["prompt_tokens"] == 10
        assert result["usage"]["completion_tokens"] == 20
        assert result["usage"]["total_tokens"] == 30


if __name__ == "__main__":
    pytest.main([__file__])