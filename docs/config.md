# Configuration Module Documentation

## Overview
The `utils/config.py` module manages environment-based configuration for the agent server, providing defaults and type-safe configuration values.

## Environment Variables

### Provider Settings
- `PROVIDER` (str): LLM provider selection (default: "ollama")
- `OLLAMA_MODEL_GENERAL` (str): Default Ollama model (default: "qwen2.5:3b-instruct")
- `OLLAMA_HOST` (str): Ollama API endpoint (default: "http://127.0.0.1:11434")

### Memory Configuration
- `ENABLE_MEMORY` (bool): Toggle conversation memory (default: true)
- `MEMORY_MAX_TURNS` (int): Messages kept per conversation (default: 8)
- `MEMORY_TTL_MIN` (int): Conversation timeout in minutes (default: 60)
- `MEMORY_MAX_CONVERSATIONS` (int): Maximum concurrent conversations (default: 500)

### Model Parameters
- `CTX_TOKENS` (int): Context window size (default: 4096)
- `MAX_TOKENS` (int): Maximum tokens to generate (default: 1024)
- `TEMPERATURE` (float): Response randomness (default: 0.7)

## Functions

### `load_dotenv()`
**Purpose:** Loads environment variables from `.env` file if present

**Example:**
```python
# .env file
OLLAMA_MODEL_GENERAL=llama2:13b
TEMPERATURE=0.5
```

## Implementation Notes
- Uses `python-dotenv` for .env file support
- Provides sensible defaults for all values
- Type conversion for numeric values
- Boolean parsing supports various formats ("true", "1", "yes", "y")
- Environment variables take precedence over defaults

## Usage Example
```python
from utils.config import OLLAMA_HOST, TEMPERATURE

client = OllamaClient(host=OLLAMA_HOST)
response = await client.generate(
    prompt="Hello",
    temperature=TEMPERATURE