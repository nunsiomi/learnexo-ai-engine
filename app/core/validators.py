"""
app/core/validators.py — Phase 4: shared topic-slug validator.

Previously the topic-slug validation block was copy-pasted three times with
identical structure (AUDIT.md §1.4, item 6):
  - app/routes/content.py (validate_topic_slugs model_validator)
  - app/routes/learning_path.py (validate_topic_slugs model_validator)
  - app/schemas/pipeline.py (validate_topic_slugs model_validator)

This module provides a single shared function that each of those validators
delegates to. Behavior is unchanged — it raises ValueError with a consistent
message listing the bad slugs and the full valid list for that subject.
"""

from __future__ import annotations

from app.core.topics import get_topics, invalid_topics


def validate_slug_list(
    slugs: list[str],
    subject: str,
    field_name: str,
) -> None:
    """Validate that every slug in *slugs* is a known topic for *subject*.

    Raises:
        ValueError: if any slug is not in the allowlist for the given subject,
            with a message naming the bad slugs and listing all valid ones.
            The ValueError is raised by Pydantic model_validators and maps to
            a 422 Unprocessable Entity response.

    Args:
        slugs: The list of topic slug strings to validate (may be empty).
        subject: The subject name (e.g. "Mathematics", "English Language").
        field_name: The request-field being validated — used in the error
            message so the client knows which field caused the rejection.
    """
    if not slugs:
        return  # Empty list is always valid — no slugs to check.

    bad = invalid_topics(slugs, subject)
    if bad:
        valid = get_topics(subject)
        raise ValueError(
            f"Invalid {field_name} for '{subject}': {bad}. "
            f"Valid topics: {valid}"
        )
