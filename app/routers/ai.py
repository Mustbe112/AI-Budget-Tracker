"""AI endpoints. All routes require a valid JWT."""
from fastapi import APIRouter, Depends

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.ai import (AIResponse, AIStatus, ChatRequest,
                            RecommendationRequest)
from app.services.ai_service import (AIService, build_financial_context,
                                     get_ai_service)

router = APIRouter(prefix="/ai", tags=["AI"])


@router.get("/status", response_model=AIStatus)
def ai_status(user: CurrentUser, ai: AIService = Depends(get_ai_service)):
    return AIStatus(provider=ai.provider_name, enabled=ai.enabled)


@router.post("/recommendations", response_model=AIResponse)
def recommendations(payload: RecommendationRequest,
                    user: CurrentUser,
                    db: DbSession,
                    ai: AIService = Depends(get_ai_service)):
    ctx = build_financial_context(db, user.id, payload.days)  # only this user's data
    return ai.recommendations(ctx, payload.focus_category)


@router.post("/chat", response_model=AIResponse)
def chat(payload: ChatRequest,
         user: CurrentUser,
         db: DbSession,
         ai: AIService = Depends(get_ai_service)):
    ctx = build_financial_context(db, user.id, payload.days)
    return ai.chat(ctx, payload.question)