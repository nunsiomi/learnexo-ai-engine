from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from typing import Literal, Optional, Any

from app.services.content_service import ContentService, TopicInput
from app.core.topics import get_topics, invalid_topics

router = APIRouter(
    prefix="/content",
    tags=["Stage 3 — Content Generation"],
)

LearningStyle = Literal["visual", "auditory", "kinesthetic"]
ClassLevel = Literal["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"]


class ContentRequest(BaseModel):
    mode: str = Field(default="multi_topic", description="Generation mode — currently only 'multi_topic' is supported")
    topics: list[TopicInput] = Field(
        ...,
        min_length=1,
        description="List of topics with mastery score and learning stage",
    )
    subject: str = Field(..., min_length=2, description="School subject")
    class_level: ClassLevel = Field(..., description="Student class level")
    learning_style: LearningStyle = Field(..., description="Student learning style")
    student_id: Optional[str] = Field(default=None, description="Optional student identifier")
    focus_reason: Optional[str] = Field(
        default="general_assessment",
        description="Why these topics were selected, e.g. 'general_assessment', 'exam_prep'",
    )
    content_depth: str = Field(
        default="core",
        description="Depth: introduction, core, advanced, or revision",
    )

    @model_validator(mode="after")
    def validate_topic_slugs(self) -> "ContentRequest":
        slugs = [t.topic for t in self.topics]
        bad = invalid_topics(slugs, self.subject)
        if bad:
            valid = get_topics(self.subject)
            raise ValueError(
                f"Invalid topic slugs for '{self.subject}': {bad}. "
                f"Valid topics: {valid}"
            )
        return self


class ContentResponse(BaseModel):
    generated_content: list[dict[str, Any]]
    recommended_start: str


def get_content_service() -> ContentService:
    return ContentService()


@router.post(
    "",
    response_model=ContentResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate learning content for one or more topics",
    description=(
        "Accepts a list of topics with mastery scores and returns prioritised study content. "
        "Topics with lower mastery are assigned higher priority. Each topic receives an "
        "explanation, key points, resource links, and a recommended first action."
    ),
)
@router.post(
    "/",
    response_model=ContentResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def content_endpoint(
    request: ContentRequest,
    service: ContentService = Depends(get_content_service),
) -> ContentResponse:
    try:
        result = service.generate(
            topics=request.topics,
            subject=request.subject,
            class_level=request.class_level,
            learning_style=request.learning_style,
            content_depth=request.content_depth,
            focus_reason=request.focus_reason,
            student_id=request.student_id,
        )

        return ContentResponse(
            generated_content=result["generated_content"],
            recommended_start=result["recommended_start"],
        )

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate content",
        ) from exc
