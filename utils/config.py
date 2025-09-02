# centralized configuration loader
# runs load_dotenv() to read .env
# decouples code from environment we can swap models/hosts/limits without code change

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env if present

PROVIDER = os.getenv("PROVIDER", "ollama") # TODO when more providers are added this should be changed to a list
OLLAMA_MODEL_GENERAL = os.getenv("OLLAMA_MODEL_GENERAL", "qwen2.5:3b-instruct")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


                                    # ---- Phase 2 additions -----

# toggle short term memory (in-memory only)
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() in {"1", "true", "yes", "y"}

#how many recent turns to keep per conversation (user/assistant pairs)
MEMORY_MAX_TURNS = int(os.getenv("MEMORY_MAX_TURNS", "8"))

#prune if idle for N minutes (O=no TTL)
MEMORY_TTL_MIN = int(os.getenv("MEMORY_TTL_MIN", "60"))

# bound total conversations to avoid pi RAM creep (LRU eviction)
MEMORY_MAX_CONVERSATIONS = int(os.getenv("MEMORY_MAX_CONVERSATIONS", "500"))




# simple caps; we'll enforce these later
CTX_TOKENS = int(os.getenv("CTX_TOKENS", "2048"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "200"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))