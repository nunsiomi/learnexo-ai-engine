"""
Ungrounded baseline for the Stage 2 curriculum-grounding experiment.

This mirrors app/services/learning_path_service.py exactly EXCEPT that the
grounding is removed:
  - no curriculum topic list / valid-slug list is injected, and
  - the "use only these slugs / do not invent new names" instructions are gone.

Everything else is held constant so curriculum-grounding is the only variable:
  - same LLM (ChatGroq, same model, temperature=0.2),
  - same output parser (JsonOutputParser(LearningPathOutput)),
  - same profile inputs, learning-style guidance, ordering rules, and JSON schema.

The model is therefore free to emit any topic names it likes (typically
free-text like "Quadratic Equations" rather than slugs) — which is exactly what
the matching layer measures against the official vocabularies.
"""

from __future__ import annotations

import json
from typing import Any

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq

from app.core.config import GROQ_API_KEY, GROQ_MODEL
from app.services.learning_path_service import LearningPathOutput

# Same structure as LEARNING_PATH_TEMPLATE but with all grounding removed.
# (No {curriculum_context}; rules 2 and 6 no longer reference a slug list.)
UNGROUNDED_TEMPLATE = """
You are an expert Nigerian curriculum planner for secondary school students.

Generate a personalised learning path for the student below.

Student details:
- Learning style: {learning_style}
- Subject: {subject}
- Class level: {class_level}
- Term: {term}
- Weak topics (needs help): {weak_topics}
- Strong topics (already comfortable): {strong_topics}

Learning style guidance:
- visual: prioritise diagram-based and chart-heavy topics first so they can build a visual mental map
- auditory: order topics so each builds on discussion and verbal explanation from the previous
- kinesthetic: sequence hands-on or application-heavy topics early to keep engagement high

Requirements:
1. Return recommended_order as an ordered JSON array — weakest/most needed first.
2. Choose topics that are appropriate for the student's subject, class level and term.
3. Topics in weak_topics must appear early in recommended_order.
4. Topics in strong_topics may appear later or be omitted if not needed for progression.
5. strategy must be one or two plain-English sentences explaining the study approach.
6. focus_areas must be a subset of weak_topics that need the most immediate attention.
7. Return valid JSON only — follow the schema exactly.

{format_instructions}
""".strip()


class UngroundedLearningPathChain:
    """Drop-in baseline whose generate() signature matches LearningPathService."""

    def __init__(
        self,
        groq_api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.parser = JsonOutputParser(pydantic_object=LearningPathOutput)
        self.prompt = PromptTemplate(
            template=UNGROUNDED_TEMPLATE,
            input_variables=[
                "learning_style",
                "subject",
                "class_level",
                "term",
                "weak_topics",
                "strong_topics",
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
        learning_style: str,
        subject: str,
        class_level: str,
        weak_topics: list[str] | None = None,
        strong_topics: list[str] | None = None,
        term: str = "First",
        **_ignored: Any,
    ) -> dict[str, Any]:
        result = self.chain.invoke(
            {
                "learning_style": learning_style,
                "subject": subject,
                "class_level": class_level,
                "term": term,
                "weak_topics": json.dumps(weak_topics or []),
                "strong_topics": json.dumps(strong_topics or []),
            }
        )

        if not isinstance(result, dict):
            raise ValueError("Invalid ungrounded learning path response format")

        result.setdefault("recommended_order", [])
        result.setdefault("strategy", "")
        result.setdefault("focus_areas", [])
        return result
