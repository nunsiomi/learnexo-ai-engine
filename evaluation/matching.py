"""
Topic-matching layer for the Stage 2 grounding experiment.

Validates each topic returned by the LLM against the two official vocabularies,
reported separately (per the experiment design):

  1. SLUG reference   — subject-wide slugs from app/core/topics.py (MATHS_TOPICS).
                        This is what the grounded prompt forces the model to emit.
  2. CURRICULUM ref   — the official per-class/term topic names from
                        mathematics.json, loaded via _load_curriculum().

The two vocabularies use different strings, and the two experiment conditions
emit different styles (grounded -> slugs, ungrounded -> free text), so every
topic is normalised (lowercase, underscores -> spaces) before comparison.

Matching is intentionally conservative: an EXACT normalised match is trusted,
a fuzzy match is flagged "borderline" for manual review (never silently treated
as a hit), and anything else is "none". Uses only stdlib difflib.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import NamedTuple

from app.core.topics import get_topics
from app.services.learning_path_service import _load_curriculum

FUZZY_THRESHOLD = 0.85


def normalize(s: str) -> str:
    """Lowercase, turn separators into spaces, collapse whitespace, strip."""
    s = (s or "").lower().replace("_", " ").replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


class MatchResult(NamedTuple):
    match_type: str          # "exact" | "borderline" | "none"
    matched_value: str       # the reference entry that matched (or "")
    similarity: float        # best ratio found, rounded to 3 dp


def _classify(topic: str, references: list[str]) -> MatchResult:
    """Classify a single topic against one reference vocabulary."""
    norm_topic = normalize(topic)
    if not norm_topic or not references:
        return MatchResult("none", "", 0.0)

    best_value = ""
    best_ratio = 0.0
    for ref in references:
        norm_ref = normalize(ref)

        # 1) exact normalised equality -> trusted hit
        if norm_topic == norm_ref:
            return MatchResult("exact", ref, 1.0)

        # 2) track the best fuzzy candidate (ratio or substring containment)
        ratio = SequenceMatcher(None, norm_topic, norm_ref).ratio()
        is_substring = norm_topic in norm_ref or norm_ref in norm_topic
        effective = max(ratio, 0.9 if is_substring else 0.0)
        if effective > best_ratio:
            best_ratio = effective
            best_value = ref

    if best_ratio >= FUZZY_THRESHOLD:
        return MatchResult("borderline", best_value, round(best_ratio, 3))
    return MatchResult("none", best_value, round(best_ratio, 3))


class TopicVerdict(NamedTuple):
    slug: MatchResult
    curriculum: MatchResult
    is_hallucinated: bool     # matched NEITHER reference


def build_references(subject: str, class_level: str, term: str) -> tuple[list[str], list[str]]:
    """Return (slug_reference, curriculum_name_reference) for a curriculum slice."""
    slug_ref = get_topics(subject)
    curriculum_topics = _load_curriculum(subject, class_level, term)
    curriculum_ref = [t.get("topic", "") for t in curriculum_topics if t.get("topic")]
    return slug_ref, curriculum_ref


def evaluate_topic(
    topic: str,
    slug_ref: list[str],
    curriculum_ref: list[str],
) -> TopicVerdict:
    """Classify one returned topic against both vocabularies."""
    slug = _classify(topic, slug_ref)
    curriculum = _classify(topic, curriculum_ref)
    is_hallucinated = slug.match_type == "none" and curriculum.match_type == "none"
    return TopicVerdict(slug=slug, curriculum=curriculum, is_hallucinated=is_hallucinated)
