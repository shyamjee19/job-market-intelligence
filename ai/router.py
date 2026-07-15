from fastapi import APIRouter, Depends, HTTPException, Request

from ai.models.schemas import (
    AIToolResponse,
    CareerAdviceRequest,
    ChatRequest,
    ChatResponse,
    InterviewPrepRequest,
    ResumeAnalysisRequest,
    SalaryInsightsRequest,
    SkillGapRequest,
)
from ai.services import ai_tools_service
from ai.services.rag_chatbot_service import answer_question
from ai.services.rate_limiter import check_rate_limit
from auth.dependencies import get_current_user
from config.settings import settings
from database.users_queries import get_profile
from utils.exceptions import DataValidationError
from utils.logger import logger
from utils.rate_limiter import check_rate_limit as check_rate_limit_generic

router = APIRouter()

_TOOLS_NAMESPACE = "ai-tools"


@router.post("/chat", response_model=ChatResponse)
def chat(request: Request, body: ChatRequest):
    client_id = request.client.host if request.client else "unknown"

    if not check_rate_limit(client_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded - try again in a minute.")

    try:
        result = answer_question(body.message, body.conversation_id)
    except DataValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception:
        logger.exception("AI chat request failed")
        raise HTTPException(status_code=503, detail="AI assistant is temporarily unavailable") from None

    return result


def _enforce_tool_rate_limit(user: dict) -> None:
    if not check_rate_limit_generic(_TOOLS_NAMESPACE, str(user["user_id"]), settings.AI_RATE_LIMIT_PER_MINUTE):
        raise HTTPException(status_code=429, detail="Rate limit exceeded - try again in a minute.")


def _run_tool(tool_name: str, fn, *args) -> dict:
    try:
        return fn(*args)
    except Exception:
        logger.exception("AI tool '%s' failed", tool_name)
        raise HTTPException(status_code=503, detail="AI assistant is temporarily unavailable") from None


@router.post("/tools/resume-analyzer", response_model=AIToolResponse)
def resume_analyzer(body: ResumeAnalysisRequest, user: dict = Depends(get_current_user)):
    _enforce_tool_rate_limit(user)
    return _run_tool("resume-analyzer", ai_tools_service.analyze_resume, body.resume_text)


@router.post("/tools/career-advisor", response_model=AIToolResponse)
def career_advisor(body: CareerAdviceRequest, user: dict = Depends(get_current_user)):
    _enforce_tool_rate_limit(user)
    return _run_tool("career-advisor", ai_tools_service.career_advice, body.current_skills, body.goal)


@router.post("/tools/skill-gap", response_model=AIToolResponse)
def skill_gap_tool(body: SkillGapRequest, user: dict = Depends(get_current_user)):
    _enforce_tool_rate_limit(user)
    return _run_tool("skill-gap", ai_tools_service.skill_gap, body.current_skills, body.target_role)


@router.post("/tools/salary-insights", response_model=AIToolResponse)
def salary_insights_tool(body: SalaryInsightsRequest, user: dict = Depends(get_current_user)):
    _enforce_tool_rate_limit(user)
    return _run_tool("salary-insights", ai_tools_service.salary_insights, body.role, body.location)


@router.get("/tools/job-recommendations", response_model=AIToolResponse)
def job_recommendations_tool(user: dict = Depends(get_current_user)):
    _enforce_tool_rate_limit(user)
    profile = get_profile(user["user_id"])
    skills = profile["skills"] if profile else []
    return _run_tool("job-recommendations", ai_tools_service.job_recommendations, skills)


@router.post("/tools/interview-prep", response_model=AIToolResponse)
def interview_prep_tool(body: InterviewPrepRequest, user: dict = Depends(get_current_user)):
    _enforce_tool_rate_limit(user)
    return _run_tool("interview-prep", ai_tools_service.interview_prep, body.role, body.company)
