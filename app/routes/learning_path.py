from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional

from app.services.learning_path_service import LearningPathService
from app.core.topics import SubjectLiteral
from app.core.validators import validate_slug_list

router = APIRouter(prefix="/learning-path", tags=["Learning Path"])

LearningStyle = Literal["visual", "auditory", "kinesthetic"]
ClassLevel = Literal["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"]
TermName = Literal["First", "Second", "Third"]


class LearningPathRequest(BaseModel):
    learning_style: LearningStyle = Field(
        ...,
        description="Student learning style: visual, auditory, or kinesthetic",
    )
    # Phase 3: subject constrained to pilot subjects (Literal type → 422 on unknown values).
    subject: SubjectLiteral = Field(..., description="School subject: 'Mathematics' or 'English Language'")
    class_level: ClassLevel = Field(..., description="Student class level")
    weak_topics: list[str] = Field(
        default=[],
        description="Topic slugs the student struggles with — placed first in the recommended order",
    )
    strong_topics: list[str] = Field(
        default=[],
        description="Topic slugs the student is comfortable with — deprioritised in the recommended order",
    )
    term: TermName = Field(
        default="First",
        description="Academic term — used to select the correct curriculum reference",
    )
    student_id: Optional[str] = Field(default=None, description="Optional student identifier")

    @model_validator(mode="after")
    def validate_topic_slugs(self) -> "LearningPathRequest":
        # Phase 4: delegated to shared validate_slug_list() in app/core/validators.py
        # (previously inlined here — AUDIT.md §1.4 item 6).
        validate_slug_list(self.weak_topics, self.subject, field_name="weak_topics")
        validate_slug_list(self.strong_topics, self.subject, field_name="strong_topics")
        return self


class LearningPathResponse(BaseModel):
    recommended_order: list[str]
    strategy: str
    focus_areas: list[str]


def get_learning_path_service() -> LearningPathService:
    return LearningPathService()


@router.post(
    "",
    response_model=LearningPathResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate personalized learning path",
)
@router.post(
    "/",
    response_model=LearningPathResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def generate_learning_path(
    payload: LearningPathRequest,
    service: LearningPathService = Depends(get_learning_path_service),
) -> LearningPathResponse:
    try:
        result = service.generate(
            learning_style=payload.learning_style,
            subject=payload.subject,
            class_level=payload.class_level,
            weak_topics=payload.weak_topics,
            strong_topics=payload.strong_topics,
            student_id=payload.student_id,
            term=payload.term,
        )

        return LearningPathResponse(
            recommended_order=result.get("recommended_order", []),
            strategy=result.get("strategy", ""),
            focus_areas=result.get("focus_areas", []),
        )

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate learning path",
        ) from exc
