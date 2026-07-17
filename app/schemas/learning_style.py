from typing import Dict, List, Literal

from pydantic import BaseModel, Field

LearningStyleLiteral = Literal["visual", "auditory", "kinesthetic"]


class StudentActivity(BaseModel):
    activity: List[str] = Field(..., min_length=1)


class LearningStyleRequest(BaseModel):
    learning_style_scores: Dict[str, int]
    cognitive_score: int
    student_profile: dict


class LearningStyleEvaluation(BaseModel):
    learning_style: LearningStyleLiteral
    friendly_label: str = Field(
        ...,
        description="Human-readable label, e.g. 'Visual Learner'",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    what_it_means: str = Field(
        ...,
        description="Plain-language explanation of this learning style for the student or parent",
    )
    how_platform_adapts: List[str] = Field(
        ...,
        description="Concrete list of how LearNEXO will personalise content for this student",
    )
    recommended_formats: List[str] = Field(
        ...,
        description="2–3 content format keywords (e.g. 'videos', 'diagrams')",
    )
    study_tips: List[str] = Field(
        ...,
        description="3 practical study tips tailored to this learning style",
    )
    explanation: str = Field(
        ...,
        description="Internal note on why this style was chosen based on the scores",
    )
    risk_of_misclassification: Literal["low", "medium", "high"]


class LearningStyleResponse(BaseModel):
    learning_style: LearningStyleLiteral
