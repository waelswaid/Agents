# load the system prompt text for the general agent from the prompts/ folder
from pathlib import Path

def load_system_prompt() -> str:
    p = Path("prompts/general_system.txt") # TODO: currently uses a relative path, harden it later to a using a path relative to __file__
    return p.read_text(encoding="utf-8").strip()
