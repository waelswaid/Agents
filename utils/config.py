# centralized configuration loader
# runs load_dotenv() to read .env
# decouples code from environment we can swap models/hosts/limits without code change

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env if present

PROVIDER = os.getenv("PROVIDER", "ollama") # TODO when more providers are added this should be changed to a list
OLLAMA_MODEL_GENERAL = os.getenv("OLLAMA_MODEL_GENERAL", "qwen2.5:3b-instruct")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

# simple caps; we'll enforce these later
CTX_TOKENS = int(os.getenv("CTX_TOKENS", "2048"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "200"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))