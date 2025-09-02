"""
provides the generic function that assembles a chat prompt from:

* a system block (behaviour/rules)
* a user block (the user's message)
* a placeholder for future chat history

"""

from typing import List, Dict

#def build_prompt(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str:
    
    #Very simple prompt composer:
    #<system>...</system>
    #<user>...</user>
    #(history left for later)
    
#    _ = history  # unused in Phase 1
#    return f"<system>\n{system}\n</system>\n\n<user>\n{user}\n</user>"



from typing import List, Dict, Iterable

def _render_history(history: Iterable[Dict[str, str]]) -> str:
    parts: List[str] = []
    for turn in history:
        role = turn.get("role", "").strip().lower()
        content = turn.get("content", "")
        if not content:
            continue
        if role == "assistant":
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