# tests/test_agents_prompt.py
from agents.agents_base import build_prompt
import re

def test_build_prompt_formatting():
    # Tests that build_prompt formats the system message, history,
    # and new user message correctly with <system>, <user>, <assistant> tags.
    # Uses whitespace normalization so formatting changes won't break the test.
    system = "You are helpful."
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello!"},
        {"role": "user", "content": "How are you?"},
    ]
    new_msg = "Tell me a joke."
    text = build_prompt(system, new_msg, history)

    def cw(s: str) -> str:
        return re.sub(r"\s+", " ", s.strip())

    T = cw(text)
    assert cw("<system>You are helpful.</system>") in T
    assert cw("<user>Hi</user>") in T
    assert cw("<assistant>Hello!</assistant>") in T
    assert cw("<user>How are you?</user>") in T
    assert T.endswith(cw("<user>Tell me a joke.</user>"))
    
