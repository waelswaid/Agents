from typing import List, Dict

def build_prompt(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str:
    """
    Very simple prompt composer:
    <system>...</system>
    <user>...</user>
    (history left for later)
    """
    _ = history  # unused in Phase 1
    return f"<system>\n{system}\n</system>\n\n<user>\n{user}\n</user>"
