# 03. Data Models (Pydantic)

## ChatRequest
```python
from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    agent: str = "general"
    stream: bool = False
    conversation_id: Optional[str] = None
```

- `message`: required, keep it bounded to protect resources.
- `agent`: currently only `"general"`; validate later if you add more.
- `stream`: choose between JSON reply or chunked text stream.
- `conversation_id`: continue a thread; server generates one if absent.

## ChatResponse
```python
class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
```

- Optional `model` & `provider` keep the app tolerant when providers omit these fields.
- Only used for non-stream path (stream returns plain text).
