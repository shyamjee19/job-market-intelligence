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


class ResumeAnalysisRequest(BaseModel):
    resume_text: str = Field(..., min_length=50, max_length=20000)


class CareerAdviceRequest(BaseModel):
    current_skills: str = Field(..., min_length=1, max_length=1000)
    goal: str = Field(..., min_length=1, max_length=500)


class SkillGapRequest(BaseModel):
    current_skills: str = Field(..., min_length=1, max_length=1000)
    target_role: str = Field(..., min_length=1, max_length=200)


class SalaryInsightsRequest(BaseModel):
    role: str | None = Field(None, max_length=200)
    location: str | None = Field(None, max_length=200)


class InterviewPrepRequest(BaseModel):
    role: str = Field(..., min_length=1, max_length=200)
    company: str | None = Field(None, max_length=200)


class AIToolResponse(BaseModel):
    summary: str
    data: dict | None = None
