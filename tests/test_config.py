# tests/test_config.py
import os
from importlib import reload
import utils.config as cfg_mod

def test_defaults_present():
    # Tests that default configuration values (like TEMPERATURE, CTX_TOKENS, etc.)
    # are present and valid when no environment variables are set.
    reload(cfg_mod)
    assert cfg_mod.TEMPERATURE is not None
    assert cfg_mod.CTX_TOKENS > 0
    assert cfg_mod.MAX_TOKENS > 0

def test_bool_parsing(monkeypatch):
    # Tests that ENABLE_MEMORY environment variable is correctly parsed
    # into a boolean value, handling different capitalizations and words like
    # "yes", "no", "true", "false".
    monkeypatch.setenv("ENABLE_MEMORY", "Yes")
    reload(cfg_mod)
    assert cfg_mod.ENABLE_MEMORY is True
    monkeypatch.setenv("ENABLE_MEMORY", "no")
    reload(cfg_mod)
    assert cfg_mod.ENABLE_MEMORY is False
