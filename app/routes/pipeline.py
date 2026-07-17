from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.pipeline import GenerateLearningRequest, GenerateLearningResponse
from app.schemas.learning_style import LearningStyleEvaluation
from app.services.learning_style_service import LearningStyleService
from app.services.learning_path_service import LearningPathService
from app.services.content_service import ContentService, TopicInput
from app.core.dependencies import get_learning_style_service

router = APIRouter(prefix="/api", tags=["Pipeline"])


def get_learning_path_service() -> LearningPathService:
    return LearningPathService()


def get_content_service() -> ContentService:
    return ContentService()


@router.post(
    "/generate-learning/",
    response_model=GenerateLearningResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Stages 1 + 2 + 3 together",
    description=(
        "Detects the student's learning style, generates a personalised learning path, "
        "and optionally generates lesson content for the first recommended topic."
    ),
)
def generate_learning(
    payload: GenerateLearningRequest,
    stage1: LearningStyleService = Depends(get_learning_style_service),
    stage2: LearningPathService = Depends(get_learning_path_service),
    stage3: ContentService = Depends(get_content_service),
) -> GenerateLearningResponse:
    try:
        # Stage 1: Detect learning style
        stage1_result: LearningStyleEvaluation = stage1.evaluate(payload.student_activity)

        # Stage 2: Generate learning path
        learning_path = stage2.generate(
            learning_style=stage1_result.learning_style,
            subject=payload.subject,
            class_level=payload.class_level,
            weak_topics=payload.weak_topics,
            strong_topics=payload.strong_topics,
            student_id=payload.student_id,
            term=payload.term,
        )

        # Stage 3: Optionally generate content for the first recommended topic
        content = None
        if payload.generate_content_for_first_topic:
            recommended_order = learning_path.get("recommended_order", [])
            if recommended_order:
                first_topic = recommended_order[0]
                content = stage3.generate(
                    topics=[TopicInput(topic=first_topic, mastery=0.3, learning_stage="foundation")],
                    subject=payload.subject,
                    class_level=payload.class_level,
                    learning_style=stage1_result.learning_style,
                    content_depth=payload.content_depth,
                    focus_reason="pipeline_first_topic",
                    student_id=payload.student_id,
                )

        return GenerateLearningResponse(
            learning_style=stage1_result.learning_style,
            learning_path=learning_path,
            content=content,
        )

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run full learning pipeline",
        ) from exc
