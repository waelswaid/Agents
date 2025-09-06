from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    agent: str = Field(default="general")
    stream: bool = Field(default=False)
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    conversation_id: Optional[str] = None
    model: Optional[str] = None
    provider: Optional[str] = None
