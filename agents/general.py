from pathlib import Path

def load_system_prompt() -> str:
    p = Path("prompts/general_system.txt")
    return p.read_text(encoding="utf-8").strip()
