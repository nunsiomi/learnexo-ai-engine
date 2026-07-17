from fastapi import APIRouter, Depends
from app.schemas.learning_style import (
    LearningStyleRequest,
    LearningStyleEvaluation,
)
from app.services.learning_style_service import LearningStyleService
from app.core.dependencies import get_learning_style_service

router = APIRouter(prefix="/api/learning-style", tags=["Learning Style"])

@router.post("/detailed", response_model=LearningStyleEvaluation)
def detect_learning_style_detailed(
    payload: LearningStyleRequest,
    service: LearningStyleService = Depends(get_learning_style_service),
):
    return service.evaluate(payload)