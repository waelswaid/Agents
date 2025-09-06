from typing import List, Dict, Iterable

def _render_history(history: Iterable[Dict[str, str]]) -> str:
    parts: List[str] = []
    for turn in history:
        role = (turn.get("role") or "").strip().lower()
        content = turn.get("content") or ""
        if not content:
            continue
        if role == "assistant":
            parts.append(f"<assistant>\n{content}\n</assistant>")
        else:
            parts.append(f"<user>\n{content}\n</user>")
    return "\n".join(parts)

def build_prompt(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str:
    hist = _render_history(history or [])
    if hist:
        return (
            f"<system>\n{system}\n</system>\n\n"
            f"{hist}\n\n"
            f"<user>\n{user}\n</user>"
        )
    return (
        f"<system>\n{system}\n</system>\n\n"
        f"<user>\n{user}\n</user>"
    )
