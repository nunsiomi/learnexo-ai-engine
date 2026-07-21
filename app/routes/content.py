from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal, Optional, Any

from app.services.content_service import ContentService, TopicInput, ContentGenerationError
from app.core.topics import SubjectLiteral
from app.core.validators import validate_slug_list
from app.core.security import check_free_text
from app.core.dependencies import get_content_service

router = APIRouter(
    prefix="/content",
    tags=["Stage 3 — Content Generation"],
)

LearningStyle = Literal["visual", "auditory", "kinesthetic"]
ClassLevel = Literal["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"]
# Phase 3: content_depth constrained to the four values already declared in
# content_service.py. Invalid value → 422 before reaching the LLM.
ContentDepthLiteral = Literal["introduction", "core", "advanced", "revision"]


class ContentRequest(BaseModel):
    mode: str = Field(default="multi_topic", description="Generation mode — currently only 'multi_topic' is supported")
    topics: list[TopicInput] = Field(
        ...,
        min_length=1,
        description="List of topics with mastery score and learning stage",
    )
    # Phase 3: subject constrained to pilot subjects (Literal type → 422 on unknown values).
    subject: SubjectLiteral = Field(..., description="School subject: 'Mathematics' or 'English Language'")
    class_level: ClassLevel = Field(..., description="Student class level")
    learning_style: LearningStyle = Field(..., description="Student learning style")
    focus_reason: Optional[str] = Field(
        default="general_assessment",
        max_length=200,
        description="Why these topics were selected, e.g. 'general_assessment', 'exam_prep'",
    )
    # Phase 3: content_depth constrained to its four valid values.
    content_depth: ContentDepthLiteral = Field(
        default="core",
        description="Depth: introduction, core, advanced, or revision",
    )

    @field_validator("focus_reason", mode="before")
    @classmethod
    def guard_focus_reason(cls, v: Optional[str]) -> Optional[str]:
        """Phase 3: basic prompt-injection guard on focus_reason.
        This is a first-layer check, not a complete defence — see app/core/security.py."""
        if v is not None:
            check_free_text(v, field_name="focus_reason")
        return v

    @model_validator(mode="after")
    def validate_topic_slugs(self) -> "ContentRequest":
        # Phase 4: delegated to shared validate_slug_list() in app/core/validators.py
        # (previously inlined here — AUDIT.md §1.4 item 6).
        slugs = [t.topic for t in self.topics]
        validate_slug_list(slugs, self.subject, field_name="topics")
        return self


class ContentResponse(BaseModel):
    generated_content: list[dict[str, Any]]
    recommended_start: str


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
        )

        return ContentResponse(
            generated_content=result["generated_content"],
            recommended_start=result["recommended_start"],
        )

    except ContentGenerationError:
        # Phase 4 (AUDIT.md §2.2): server-side failure (e.g. LLM returned
        # unexpected format). Report as 500, not 400 — this is NOT the
        # client's fault. No internal detail is included in the response.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while generating content. Please try again.",
        )
    except ValueError as exc:
        # Only genuine client-input errors reach here (empty subject / empty
        # topics list checked in ContentService.generate). These are 400.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while generating content. Please try again.",
        )
