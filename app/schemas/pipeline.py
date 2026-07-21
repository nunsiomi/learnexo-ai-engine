from typing import Optional, Any, Literal
from pydantic import BaseModel, Field, model_validator
from app.schemas.learning_style import LearningStyleRequest, LearningStyleLiteral
from app.core.topics import SubjectLiteral
from app.core.validators import validate_slug_list

# Phase 3: Literal aliases — same values as individual route files.
# Centralised here rather than imported from routes to keep the schema layer
# independent of the route layer.
ClassLevel = Literal["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"]
TermName = Literal["First", "Second", "Third"]
ContentDepth = Literal["introduction", "core", "advanced", "revision"]


class GenerateLearningRequest(BaseModel):
    student_activity: LearningStyleRequest
    # Phase 3: subject, class_level, term, content_depth were plain str (AUDIT.md §4.3).
    # Now constrained to Literal types — invalid values 422 before any service call.
    subject: SubjectLiteral = Field(..., description="School subject: 'Mathematics' or 'English Language'")
    class_level: ClassLevel = Field(..., description="Student class level, e.g. JSS1, SS3")
    term: TermName = Field(default="First", description="Academic term: First, Second, or Third")
    content_depth: ContentDepth = Field(default="core", description="Content depth: introduction, core, advanced, or revision")
    weak_topics: list[str] = Field(default=[], description="Topic slugs the student struggles with")
    strong_topics: list[str] = Field(default=[], description="Topic slugs the student is comfortable with")
    generate_content_for_first_topic: bool = True

    @model_validator(mode="after")
    def validate_topic_slugs(self) -> "GenerateLearningRequest":
        # Phase 4: delegated to shared validate_slug_list() in app/core/validators.py
        # (previously inlined here — AUDIT.md §1.4 item 6).
        validate_slug_list(self.weak_topics, self.subject, field_name="weak_topics")
        validate_slug_list(self.strong_topics, self.subject, field_name="strong_topics")
        return self


class GenerateLearningResponse(BaseModel):
    learning_style: LearningStyleLiteral
    learning_path: dict[str, Any]
    content: Optional[dict[str, Any]] = None
