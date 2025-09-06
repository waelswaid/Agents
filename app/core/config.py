# centralized configuration loader
# runs load_dotenv() to read .env
# decouples code from environment we can swap models/hosts/limits without code change

import os
from dotenv import load_dotenv

load_dotenv()

# Provider
PROVIDER = os.getenv("PROVIDER", "ollama")
OLLAMA_MODEL_GENERAL = os.getenv("OLLAMA_MODEL_GENERAL", "qwen2.5:3b-instruct")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# Generation caps
CTX_TOKENS = int(os.getenv("CTX_TOKENS", "2048"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "200"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Memory
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() in {"1", "true", "yes", "y"}
MEMORY_MAX_TURNS = int(os.getenv("MEMORY_MAX_TURNS", "8"))
MEMORY_TTL_MIN = int(os.getenv("MEMORY_TTL_MIN", "60"))
MEMORY_MAX_CONVERSATIONS = int(os.getenv("MEMORY_MAX_CONVERSATIONS", "500"))
