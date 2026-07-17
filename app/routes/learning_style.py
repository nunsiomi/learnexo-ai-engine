from fastapi import APIRouter, Depends, HTTPException, status
from langchain_core.exceptions import OutputParserException
from pydantic import ValidationError

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
    try:
        return service.evaluate(payload)
    except (OutputParserException, ValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The learning-style model returned output that did not match the expected schema.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The learning-style service is temporarily unavailable.",
        ) from exc