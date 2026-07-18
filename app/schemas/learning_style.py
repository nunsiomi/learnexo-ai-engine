from typing import Dict, List, Literal

from pydantic import BaseModel, Field, model_validator
from app.core.security import check_profile_dict

LearningStyleLiteral = Literal["visual", "auditory", "kinesthetic"]

# The three score keys the learning-style service expects. Defined here
# (not in the service) so the validation lives at the schema layer and the
# LLM is never reached with an incomplete or fabricated score map.
_REQUIRED_SCORE_KEYS: frozenset[str] = frozenset({"visual", "auditory", "kinesthetic"})


class StudentActivity(BaseModel):
    activity: List[str] = Field(..., min_length=1)


class LearningStyleRequest(BaseModel):
    # Phase 3 — bug #22: Dict[str, int] with no key constraints let an empty {}
    # through Pydantic and reach the LLM, which fabricated a confident-sounding
    # result ("cognitive score suggests kinesthetic tendency") with invented
    # reasoning. A model_validator now rejects any request missing one or more
    # of the three required score keys before the request is processed further.
    learning_style_scores: Dict[str, int] = Field(
        ...,
        description=(
            "Score for each learning style. Must include all three keys: "
            "'visual', 'auditory', 'kinesthetic'. Values are integers (0–100)."
        ),
    )
    cognitive_score: int = Field(..., ge=0, le=100, description="Cognitive score (0–100)")
    student_profile: dict

    @model_validator(mode="after")
    def require_all_score_keys(self) -> "LearningStyleRequest":
        """Bug #22 fix: reject requests where any required score key is missing.
        Without this, an empty {} produces a hallucinated learning-style result.
        Also guards student_profile against prompt injection (Phase 3, Task 4)."""
        # --- scores: required keys ---
        present = set(self.learning_style_scores.keys())
        missing = _REQUIRED_SCORE_KEYS - present
        if missing:
            raise ValueError(
                f"learning_style_scores is missing required keys: {sorted(missing)}. "
                f"All three keys must be present: {sorted(_REQUIRED_SCORE_KEYS)}."
            )
        # --- scores: range check ---
        out_of_range = {
            k: v for k, v in self.learning_style_scores.items()
            if not (0 <= v <= 100)
        }
        if out_of_range:
            raise ValueError(
                f"learning_style_scores values must be integers between 0 and 100. "
                f"Out-of-range keys: {out_of_range}"
            )
        # --- student_profile: injection guard (Task 4) ---
        # This is a first-layer check, not a complete defence — see app/core/security.py.
        if self.student_profile:
            check_profile_dict(self.student_profile, field_name="student_profile")
        return self



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
