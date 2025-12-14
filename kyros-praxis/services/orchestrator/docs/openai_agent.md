# OpenAI Agent SDK Integration

This document explains how to use the OpenAI Agent SDK integration in the Kyros Orchestrator service.

## Configuration

The OpenAI integration is configured through environment variables in the `.env` file:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

These values can also be configured in the `app/core/config.py` file through the Settings class.

## Usage

### Synchronous Usage

```python
from app.core.openai_agent import sync_agent

# Send a simple prompt
response = sync_agent.send_prompt("Hello, how are you?")
print(response["content"])

# Send a prompt with a system message
response = sync_agent.send_prompt(
    prompt="What is the weather like today?",
    system_message="You are a helpful weather assistant.",
    temperature=0.7
)
print(response["content"])
```

### Asynchronous Usage

```python
from app.core.openai_agent import async_agent

async def get_response():
    response = await async_agent.send_prompt_async("Hello, how are you?")
    return response["content"]

# Or with structured messages
async def get_structured_response():
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    response = await async_agent.send_structured_prompt_async(messages)
    return response["content"]
```

### Advanced Usage

```python
from app.core.openai_agent import OpenAIAgent

# Create a custom agent instance
agent = OpenAIAgent(async_client=False)

# Send a prompt with custom parameters
response = agent.send_prompt(
    prompt="Write a short poem about programming.",
    temperature=0.9,
    max_tokens=150
)
print(response["content"])
```

## Error Handling

The OpenAI agent includes comprehensive error handling and logging. All API errors are logged and re-raised for the calling code to handle appropriately.

```python
from app.core.openai_agent import sync_agent

try:
    response = sync_agent.send_prompt("Hello, world!")
    print(response["content"])
except Exception as e:
    print(f"Error communicating with OpenAI: {e}")
```

## Testing

Unit tests for the OpenAI agent can be found in `tests/test_openai_agent.py`. Run them with:

```bash
pytest tests/test_openai_agent.py
```