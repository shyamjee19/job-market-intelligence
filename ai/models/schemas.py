from pydantic import BaseModel, Field

from config.settings import settings


class ChatSource(BaseModel):
    job_id: str
    position: str | None
    company: str | None
    score: float


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=settings.AI_MAX_MESSAGE_LENGTH)
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]
    conversation_id: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
