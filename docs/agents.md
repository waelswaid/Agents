# Agents Module Documentation

## agents/agents_base.py

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



#### `build_prompt(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str`
**Purpose:** Assembles a complete prompt combining system instructions, chat history, and current user message.

**Parameters:**
- `system` (str): System instructions/rules for the model (generated in agents/general.py)
- `user` (str): Current user message
- `history` (List[Dict[str, str]] | None): Optional conversation history

**Returns:**
- `str`: Complete formatted prompt with XML-style tags

## Full Code

- agents/agents_base.py

```python
"""
provides the generic function that assembles a chat prompt from:

* a system block (behaviour/rules)
* a user block (the user's message)
* a placeholder for future chat history

"""

from typing import List, Dict, Iterable

def _render_history(history: Iterable[Dict[str, str]]) -> str:
    parts: List[str] = []
    for turn in history:
        role = turn.get("role", "").strip().lower()
        content = turn.get("content", "")
        if not content:
            continue
        if role == "assistant": # response from the model
            parts.append(f"<assistant>\n{content}\n</assistant>")
        else:
            parts.append(f"<user>\n{content}\n</user>")
    return "\n".join(parts)

def build_prompt(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str:
    """
    Prompt composer with optional short history:
    <system>...</system>
    <user/assistant history...>
    <user>...</user>
    """
    hist = _render_history(history or [])
    # contains the formatted conversation history that provides context for the model's next response
    if hist:
        return (
            f"<system>\n{system}\n</system>\n\n"
            f"{hist}\n\n"
            f"<user>\n{user}\n</user>"
        )
    else:
        return (
            f"<system>\n{system}\n</system>\n\n"
            f"<user>\n{user}\n</user>"
        )
```


## agents/agents_general.py

### Overview
- loads prompts/general_system.txt for the general agent from the prompts/ folder

## Full Code

- agents/agents_general.py

```python
# load the system prompt text for the general agent from the prompts/ folder
from pathlib import Path

def load_system_prompt() -> str:
    p = Path(__file__).resolve().parents[1] / "prompts" / "general_system.txt"
    return p.read_text(encoding="utf-8").strip()

```