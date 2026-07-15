from fastapi import APIRouter, HTTPException, Request

from ai.models.schemas import ChatRequest, ChatResponse
from ai.services.rag_chatbot_service import answer_question
from ai.services.rate_limiter import check_rate_limit
from utils.exceptions import DataValidationError
from utils.logger import logger

router = APIRouter()


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
