from typing import Optional, Any
from pydantic import BaseModel, Field, model_validator
from app.schemas.learning_style import LearningStyleRequest, LearningStyleLiteral
from app.core.topics import get_topics, invalid_topics


class GenerateLearningRequest(BaseModel):
    student_activity: LearningStyleRequest
    subject: str = Field(..., min_length=2)
    class_level: str = Field(..., min_length=2)
    term: str = "First"
    student_id: Optional[str] = None
    content_depth: str = "core"
    weak_topics: list[str] = Field(default=[], description="Topic slugs the student struggles with")
    strong_topics: list[str] = Field(default=[], description="Topic slugs the student is comfortable with")
    generate_content_for_first_topic: bool = True

    @model_validator(mode="after")
    def validate_topic_slugs(self) -> "GenerateLearningRequest":
        bad = invalid_topics(self.weak_topics, self.subject)
        if bad:
            valid = get_topics(self.subject)
            raise ValueError(
                f"Invalid weak_topics for '{self.subject}': {bad}. "
                f"Valid topics: {valid}"
            )
        bad = invalid_topics(self.strong_topics, self.subject)
        if bad:
            valid = get_topics(self.subject)
            raise ValueError(
                f"Invalid strong_topics for '{self.subject}': {bad}. "
                f"Valid topics: {valid}"
            )
        return self


class GenerateLearningResponse(BaseModel):
    learning_style: LearningStyleLiteral
    learning_path: dict[str, Any]
    content: Optional[dict[str, Any]] = None
