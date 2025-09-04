# Memory Module Documentation

## Overview
The `utils/memory.py` module implements a lightweight, thread-safe, in-memory conversation store designed for Raspberry Pi constraints. It provides TTL-based expiration and LRU eviction.

## Classes

### `Turn`
**Purpose:** TypedDict for conversation turn structure

**Fields:**
- `role` (str): Message source ("user" or "assistant")
- `content` (str): Message text
- `ts` (float): Unix timestamp of message

**Example:**
```python
turn: Turn = {
    "role": "user",
    "content": "Hello!",
    "ts": 1693743200.0
}
```

### `MemoryStore`
**Purpose:** Thread-safe conversation manager with size and time limits

**Constructor Parameters:**
- `max_turns` (int): Messages per conversation (default: 8)
- `ttl_seconds` (int): Conversation timeout (default: 3600)
- `max_conversations` (int): Total conversations (default: 500)

#### Methods

##### `async def get(convo_id: str) -> List[Turn]`
**Purpose:** Retrieve conversation history

**Parameters:**
- `convo_id` (str): Unique conversation identifier

**Returns:**
- List of Turn objects or empty list if not found

**Example:**
```python
turns = await memory.get("abc-123")
```

##### `async def append(convo_id: str, role: str, content: str) -> None`
**Purpose:** Add message to conversation

**Parameters:**
- `convo_id` (str): Conversation identifier
- `role` (str): Message source
- `content` (str): Message text

**Example:**
```python
await memory.append("abc-123", "user", "Hello!")
```

##### `async def _maybe_prune(convo_id: str) -> None`
**Purpose:** Internal method to handle TTL expiration

**Parameters:**
- `convo_id` (str): Conversation to check

## Implementation Notes

### Memory Management
- Uses `collections.deque` with maxlen for automatic turn pruning
- Thread-safe operations via `asyncio.Lock()`
- TTL expiration checked on access
- LRU eviction when max conversations reached

### Storage Structure
```python
self._store: Dict[str, Deque[Turn]]  # Conversations
self._last: Dict[str, float]         # Access timestamps
```

### Example Usage
```python
memory = MemoryStore(
    max_turns=8,
    ttl_seconds=3600,
    max_conversations=500
)

# Add messages
await memory.append("conv1", "user", "Hello")
await memory.append("conv1", "assistant", "Hi!")

# Get history
turns = await memory.get("conv1")
```