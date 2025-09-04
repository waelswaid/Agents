# Providers Module Documentation

## base.py

### Overview
Defines the base provider contract and error handling for LLM interactions.

### Classes

#### `ProviderError`
**Purpose:** Custom exception for provider-specific errors.

**Attributes:**
- `message` (str): Error description
- `status_code` (int): HTTP status code (defaults to 502)

**Example:**
```python
raise ProviderError("Failed to connect to LLM", status_code=503)
```

### Types

#### `GenerateReturn`
**Purpose:** Type alias for provider response formats.
```python
GenerateReturn = Union[str, AsyncIterator[str]]
```
- `str`: Complete response for non-streaming
- `AsyncIterator[str]`: Token stream for streaming

## ollama.py

### Overview
Implements the Ollama API provider with streaming and non-streaming support.

### Functions

#### `_apply_defaults(options: Optional[Dict[str, Any]]) -> Dict[str, Any]`
**Purpose:** Applies default configuration values to Ollama request options.

**Parameters:**
- `options` (Optional[Dict[str, Any]]): Custom options

**Returns:**
- Dictionary with complete Ollama configuration

**Example:**
```python
opts = _apply_defaults({"temperature": 0.7})
# Returns: {"temperature": 0.7, "num_ctx": 4096, "num_predict": 1024}
```

#### `_generate_streaming(payload: Dict[str, Any]) -> AsyncIterator[str]`
**Purpose:** Handles streaming responses from Ollama API.

**Parameters:**
- `payload` (Dict[str, Any]): Request body for Ollama

**Returns:**
- `AsyncIterator[str]`: Stream of text chunks

**Example:**
```python
async for chunk in _generate_streaming({"prompt": "Hello", "model": "qwen:3b"}):
    print(chunk)
```

#### `generate(prompt: str, *, model: str, stream: bool = False, options: Optional[Dict[str, Any]] = None) -> GenerateReturn`
**Purpose:** Main generation function, wraps Ollama's /api/generate endpoint.

**Parameters:**
- `prompt` (str): Input text
- `model` (str): Model identifier
- `stream` (bool): Enable streaming mode
- `options` (Optional[Dict[str, Any]]): Custom configuration

**Returns:**
- `str` or `AsyncIterator[str]` depending on stream mode

**Example:**
```python
# Non-streaming
response = await generate("Hello!", model="qwen:3b")

# Streaming
async for chunk in await generate("Hello!", model="qwen:3b", stream=True):
    print(chunk)
```

### Implementation Notes
- Uses httpx for async HTTP requests
- Implements proper timeout handling
- Supports NDJSON streaming format
- Includes error handling and status