"""
used to load system prompt (general_system.txt) to the agent
"""
from pathlib import Path

def load_system_prompt() -> str:
    p = Path(__file__).resolve().parents[1] / "prompts" / "general_system.txt"
    return p.read_text(encoding="utf-8").strip()

"""
- __file__ is a special python variable that holds the absolute path of the python file
- .resolve() turns the relative path into an absolute, canonical path.
    example:
    Path("./../project/src/utils/helpers.py").resolve()
    might return: /home/user/project/src/utils/helpers.py
- .parents gives a list of all parent directories, starting from the closest folder to the root.
    .parents[0] → immediate parent (directory containing the current file)
    .parents[1] → grandparent directory
    .parents[2] → great-grandparent, and so on.
- .strip() removes leading and trailing whitespace, including:
    Spaces
    Tabs
    Newlines (\n)
"""