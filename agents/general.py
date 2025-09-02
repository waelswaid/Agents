# load the system prompt text for the general agent from the prompts/ folder
from pathlib import Path

def load_system_prompt() -> str:
    p = Path(__file__).resolve().parents[1] / "prompts" / "general_system.txt"
    return p.read_text(encoding="utf-8").strip()
