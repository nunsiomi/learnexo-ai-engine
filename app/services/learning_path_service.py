from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.core.config import GROQ_API_KEY, GROQ_MODEL
from app.core.topics import get_topics, PILOT_SUBJECTS

LearningStyle = Literal["visual", "auditory", "kinesthetic"]
ClassLevel = Literal["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"]
TermName = Literal["First", "Second", "Third"]

# PILOT_SUBJECTS is imported from app.core.topics (single source of truth).
# Previously defined here as a local set — moved to topics.py in Phase 3
# so the schema layer and the service layer share the same definition.

_CURRICULUM_DIR = Path(__file__).parent.parent / "data" / "curriculum"
_SUBJECT_FILE_MAP = {
    "Mathematics": "mathematics.json",
    "English Language": "english_language.json",
}


def _load_curriculum(subject: str, class_level: str, term: str) -> list[dict]:
    filename = _SUBJECT_FILE_MAP.get(subject)
    if not filename:
        return []
    filepath = _CURRICULUM_DIR / filename
    if not filepath.exists():
        return []
    try:
        data = json.loads(filepath.read_text(encoding="utf-8"))
        return data["class_levels"].get(class_level, {}).get(term, [])
    except Exception:
        return []


class LearningPathOutput(BaseModel):
    recommended_order: list[str] = Field(
        ...,
        description="Ordered list of topic names the student should study, weakest/most needed first",
    )
    strategy: str = Field(
        ...,
        description="One or two sentence study strategy tailored to the learning style and weak areas",
    )
    focus_areas: list[str] = Field(
        ...,
        description="Topic names the student should focus most effort on (subset of weak_topics)",
    )


LEARNING_PATH_TEMPLATE = """
You are an expert Nigerian curriculum planner for secondary school students.

Generate a personalised learning path for the student below.

Student details:
- Learning style: {learning_style}
- Subject: {subject}
- Class level: {class_level}
- Term: {term}
- Weak topics (needs help): {weak_topics}
- Strong topics (already comfortable): {strong_topics}

{curriculum_context}

Learning style guidance:
- visual: prioritise diagram-based and chart-heavy topics first so they can build a visual mental map
- auditory: order topics so each builds on discussion and verbal explanation from the previous
- kinesthetic: sequence hands-on or application-heavy topics early to keep engagement high

Requirements:
1. Return recommended_order as an ordered JSON array — weakest/most needed first.
2. Every string in recommended_order MUST be one of the valid topic slugs listed in the topic list above. Do not invent new names.
3. Topics in weak_topics must appear early in recommended_order.
4. Topics in strong_topics may appear later or be omitted if not needed for progression.
5. strategy must be one or two plain-English sentences explaining the study approach.
6. focus_areas must be a subset of weak_topics (use the same slug strings) that need the most immediate attention.
7. Return valid JSON only — follow the schema exactly.

{format_instructions}
""".strip()


class LearningPathService:
    def __init__(
        self,
        groq_api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.parser = JsonOutputParser(pydantic_object=LearningPathOutput)
        self.prompt = PromptTemplate(
            template=LEARNING_PATH_TEMPLATE,
            input_variables=[
                "learning_style",
                "subject",
                "class_level",
                "term",
                "weak_topics",
                "strong_topics",
                "curriculum_context",
            ],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            },
        )
        self.llm = ChatGroq(
            api_key=groq_api_key or GROQ_API_KEY,
            model=model or GROQ_MODEL,
            temperature=0.2,
        )
        self.chain = self.prompt | self.llm | self.parser

    def generate(
        self,
        learning_style: LearningStyle,
        subject: str,
        class_level: ClassLevel,
        weak_topics: list[str] | None = None,
        strong_topics: list[str] | None = None,
        student_id: str | None = None,
        term: TermName = "First",
    ) -> dict[str, Any]:
        subject = subject.strip()
        if not subject:
            raise ValueError("subject cannot be empty")

        if subject not in PILOT_SUBJECTS:
            raise ValueError(
                f"'{subject}' is not available in the pilot. "
                f"Supported subjects: {', '.join(sorted(PILOT_SUBJECTS))}"
            )

        valid_slugs = get_topics(subject)
        slug_context = (
            f"Valid topic slugs for {subject} — you MUST use only these exact strings:\n"
            + json.dumps(valid_slugs, indent=2)
            + "\n"
        ) if valid_slugs else ""

        curriculum_topics = _load_curriculum(subject, class_level, term)
        curriculum_context = slug_context
        if curriculum_topics:
            topics_text = json.dumps([t["topic"] for t in curriculum_topics], indent=2)
            curriculum_context += (
                f"\nCurriculum reference — {subject}, {class_level}, {term} Term "
                f"(use to inform depth and ordering, but use slug names above in output):\n"
                f"{topics_text}\n"
            )

        result = self.chain.invoke(
            {
                "learning_style": learning_style,
                "subject": subject,
                "class_level": class_level,
                "term": term,
                "weak_topics": json.dumps(weak_topics or []),
                "strong_topics": json.dumps(strong_topics or []),
                "curriculum_context": curriculum_context,
            }
        )

        if not isinstance(result, dict):
            raise ValueError("Invalid learning path response format")

        result.setdefault("recommended_order", [])
        result.setdefault("strategy", "")
        result.setdefault("focus_areas", [])

        return result
