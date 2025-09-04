# Agents Module Documentation

## base.py

### Overview
The `base.py` module provides functionality for assembling chat prompts by combining system instructions, conversation history, and user messages using XML-style formatting.

### Functions

#### `_render_history(history: Iterable[Dict[str, str]]) -> str`
**Purpose:** Formats conversation history into XML-style blocks.

**Parameters:**
- `history` (Iterable[Dict[str, str]]): Collection of conversation turns, each containing:
  - `role`: Either "user" or "assistant"
  - `content`: The message content

**Returns:**
- `str`: Formatted history as string with XML-style tags

**Example:**
```python
history = [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
]
rendered = _render_history(history)
# Output:
# <user>
# Hello
# </user>
# <assistant>
# Hi there!
# </assistant>
```

#### `build_prompt(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str`
**Purpose:** Assembles a complete prompt combining system instructions, chat history, and current user message.

**Parameters:**
- `system` (str): System instructions/rules for the model (generated in agents/general.py)
- `user` (str): Current user message
- `history` (List[Dict[str, str]] | None): Optional conversation history

**Returns:**
- `str`: Complete formatted prompt with XML-style tags

**Example:**
```python
prompt = build_prompt(
    system="You are a helpful assistant.",
    user="What's the weather?",
    history=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
)
# Output:
# <system>
# You are a helpful assistant.
# </system>
# 
# <user>
# Hello
# </user>
# <assistant>
# Hi there!
# </assistant>
# 
# <user>
# What's the weather?
# </user>
```

## Implementation Notes
- Uses XML-style tags for clear role separation
- Handles empty/invalid messages gracefully
- Supports optional history for stateless operation
- Maintains consistent formatting for model input