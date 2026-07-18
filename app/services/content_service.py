from __future__ import annotations

import logging
import os
from typing import Any, Literal, Optional

from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from app.core.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

LearningStyle = Literal["visual", "auditory", "kinesthetic"]
ClassLevel = Literal["JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3"]
ContentDepth = Literal["introduction", "core", "advanced", "revision"]


class ContentGenerationError(Exception):
    """Raised when content generation fails due to a server-side condition
    (e.g. the LLM returned an unexpected response shape). This is NOT a
    client input error — it maps to HTTP 500 in the route layer, not 400.

    Introduced in Phase 4 (AUDIT.md §2.2): previously these failures were
    raised as ValueError, which the route mis-mapped to 400 Bad Request.
    """


class TopicInput(BaseModel):
    topic: str
    mastery: float = Field(default=0.5, ge=0.0, le=1.0)
    learning_stage: str = Field(default="foundation")


class VideoItem(BaseModel):
    title: str
    url: str
    # Ranking hint, not gating: True surfaces this video prominently (currently
    # set for visual learners). Optional so LLM-generated videos default to False.
    featured: bool = False


class MaterialItem(BaseModel):
    title: str
    # Materials deliberately carry NO url: the LLM hallucinates reading links, so
    # it is only asked for a title + short description it can be trusted to write.
    description: str = Field(
        ..., description="One-line description of the reading/reference material"
    )


class TopicResources(BaseModel):
    videos: list[VideoItem] = Field(
        ..., description="2–3 video recommendations (YouTube or other)"
    )
    materials: list[MaterialItem] = Field(
        ..., description="2–3 reading or reference suggestions (title + description, no links)"
    )


class TopicExplanation(BaseModel):
    summary: str = Field(..., description="One or two sentence plain-English summary")
    key_points: list[str] = Field(..., description="3–5 key learning points")


class SingleTopicOutput(BaseModel):
    topic: str
    priority: int = Field(..., description="1 = highest priority")
    resources: TopicResources
    explanation: TopicExplanation
    recommended_action: str = Field(
        ..., description="One sentence telling the student what to do first"
    )


CONTENT_TEMPLATE = """
You are an expert Nigerian secondary-school lesson designer.

Generate focused study content for one topic.

INPUT
- Topic slug: {topic}
- Subject: {subject}
- Class level: {class_level}
- Learning style: {learning_style}
- Student mastery level: {mastery} (0.0 = no knowledge, 1.0 = mastered)
- Learning stage: {learning_stage}
- Content depth: {content_depth}
- Focus reason: {focus_reason}

REQUIREMENTS
1. explanation.summary: one or two plain sentences explaining the topic slug above simply.
2. explanation.key_points: 3 to 5 bullet-point facts or rules the student must know.
3. resources.videos: suggest 2 to 3 relevant YouTube video titles with real or plausible URLs that a Nigerian student could search for.
4. resources.materials: suggest 2 to 3 reading or reference materials relevant to this topic and level. Each material must have a title and a one-line description ONLY — do NOT include any URL, link, or web address for materials.
5. recommended_action: one sentence telling the student exactly what to do first (e.g. watch, read, practise).
6. Use Nigerian context throughout — Naira, Lagos, local schools, WAEC/NECO/JAMB where relevant.
7. Adjust depth to the mastery level: low mastery → foundational explanation; high mastery → revision and extension.
8. The "topic" field in your response must be the exact slug string from the INPUT above, unchanged.
9. Return valid JSON only — follow the schema exactly.

{format_instructions}
""".strip()


class ContentService:
    def __init__(
        self,
        groq_api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.groq_api_key = groq_api_key or GROQ_API_KEY
        self.model = model or GROQ_MODEL

        self.parser = JsonOutputParser(pydantic_object=SingleTopicOutput)
        self.prompt = PromptTemplate(
            template=CONTENT_TEMPLATE,
            input_variables=[
                "topic",
                "subject",
                "class_level",
                "learning_style",
                "mastery",
                "learning_stage",
                "content_depth",
                "focus_reason",
            ],
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            },
        )
        self.llm = ChatGroq(
            api_key=self.groq_api_key,
            model=self.model,
            temperature=0.2,
        )
        self.chain = self.prompt | self.llm | self.parser

    def _fetch_youtube_videos(
        self,
        topic: str,
        subject: str,
        class_level: ClassLevel,
    ) -> list[dict[str, str]] | None:
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        if not youtube_api_key:
            # Task 5 / AUDIT.md §2.3: silent-skip is deliberate here.
            # Videos are supplementary — a missing key must not block content
            # generation. Logged at DEBUG (not WARNING) because content_service
            # is not the primary caller; youtube_recommender._fetch_videos
            # already emits the WARNING when it runs.
            logger.debug(
                "YOUTUBE_API_KEY not set; skipping real-video fetch for topic=%r", topic
            )
            return None
        try:
            from youtube_recommender import recommend_videos

            recommendation = recommend_videos(
                topic=topic,
                subject=subject,
                class_level=class_level,
                max_results=3,
            )
            return [
                {"title": v.title, "url": v.url}
                for v in recommendation.videos
            ]
        except Exception as exc:
            # YouTube call failed but this is a supplementary enrichment step;
            # log and degrade gracefully rather than failing the whole request.
            logger.warning(
                "YouTube video fetch failed for topic=%r, degrading to LLM-only videos: %s",
                topic, exc,
            )
            return None

    def _generate_single(
        self,
        topic_input: TopicInput,
        priority: int,
        subject: str,
        class_level: ClassLevel,
        learning_style: LearningStyle,
        content_depth: ContentDepth,
        focus_reason: str,
    ) -> dict[str, Any]:
        result = self.chain.invoke(
            {
                "topic": topic_input.topic,
                "subject": subject,
                "class_level": class_level,
                "learning_style": learning_style,
                "mastery": topic_input.mastery,
                "learning_stage": topic_input.learning_stage,
                "content_depth": content_depth,
                "focus_reason": focus_reason or "general_assessment",
            }
        )

        if not isinstance(result, dict):
            raise ContentGenerationError(
                f"Content service received an unexpected response for topic '{topic_input.topic}'. "
                f"The upstream model did not return the expected format."
            )

        result["topic"] = topic_input.topic
        result["priority"] = priority

        # Fetch real videos for EVERY learning style, not just visual learners.
        # learning_style now affects ranking, not whether videos appear: visual
        # learners get their videos flagged "featured" and surfaced first.
        real_videos = self._fetch_youtube_videos(topic_input.topic, subject, class_level)
        if real_videos:
            is_visual = learning_style == "visual"
            for video in real_videos:
                video["featured"] = is_visual
            if is_visual:
                real_videos.sort(key=lambda v: not v.get("featured", False))
            result.setdefault("resources", {})
            result["resources"]["videos"] = real_videos

        result.setdefault("resources", {"videos": [], "materials": []})
        result.setdefault("explanation", {"summary": "", "key_points": []})
        result.setdefault("recommended_action", "")

        return result

    def generate(
        self,
        topics: list[TopicInput],
        subject: str,
        class_level: ClassLevel,
        learning_style: LearningStyle,
        content_depth: ContentDepth = "core",
        focus_reason: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> dict[str, Any]:
        subject = subject.strip()
        if not subject:
            raise ValueError("subject cannot be empty")
        if not topics:
            raise ValueError("topics list cannot be empty")

        sorted_topics = sorted(topics, key=lambda t: t.mastery)

        generated_content = []
        for priority, topic_input in enumerate(sorted_topics, start=1):
            item = self._generate_single(
                topic_input=topic_input,
                priority=priority,
                subject=subject,
                class_level=class_level,
                learning_style=learning_style,
                content_depth=content_depth,
                focus_reason=focus_reason or "general_assessment",
            )
            generated_content.append(item)

        return {
            "generated_content": generated_content,
            "recommended_start": sorted_topics[0].topic if sorted_topics else "",
        }
