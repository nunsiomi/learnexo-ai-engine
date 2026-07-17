"""
Test student profiles for the Stage 2 curriculum-grounding evaluation.

Mathematics only (pilot scope for this experiment). Profiles are deliberately
varied across class level, term, learning style, and weak/strong topic sets so
the experiment exercises many different curriculum slices.

Note: Stage 2 (LearningPathService) takes weak_topics / strong_topics slug lists
rather than per-topic mastery scores, so "mastery distribution" is represented
here by how many / which slugs land in weak vs strong.

All weak/strong slugs are valid entries of MATHS_TOPICS in app/core/topics.py.
"""

from __future__ import annotations

# Each profile is a plain dict so the runner can splat it into
# LearningPathService.generate(...) and the ungrounded chain identically.
PROFILES: list[dict] = [
    {
        "profile_id": "P1_jss1_visual",
        "class_level": "JSS1",
        "term": "First",
        "learning_style": "visual",
        "weak_topics": ["fractions", "numbers_and_numeration"],
        "strong_topics": ["basic_operations"],
    },
    {
        "profile_id": "P2_jss2_auditory",
        "class_level": "JSS2",
        "term": "Second",
        "learning_style": "auditory",
        "weak_topics": ["algebraic_expressions", "ratio_and_proportion", "percentages"],
        "strong_topics": ["fractions", "decimals"],
    },
    {
        "profile_id": "P3_jss3_kinesthetic",
        "class_level": "JSS3",
        "term": "Third",
        "learning_style": "kinesthetic",
        "weak_topics": ["simultaneous_equations"],
        "strong_topics": ["linear_equations", "indices"],
    },
    {
        "profile_id": "P4_ss1_visual",
        "class_level": "SS1",
        "term": "First",
        "learning_style": "visual",
        "weak_topics": ["quadratic_equations", "logarithms", "sets"],
        "strong_topics": ["indices"],
    },
    {
        "profile_id": "P5_ss1_auditory",
        "class_level": "SS1",
        "term": "Second",
        "learning_style": "auditory",
        "weak_topics": ["coordinate_geometry", "inequalities"],
        "strong_topics": [],
    },
    {
        "profile_id": "P6_ss2_kinesthetic",
        "class_level": "SS2",
        "term": "First",
        "learning_style": "kinesthetic",
        "weak_topics": ["trigonometry", "mensuration", "circles"],
        "strong_topics": ["plane_geometry", "angles"],
    },
    {
        "profile_id": "P7_ss3_visual",
        "class_level": "SS3",
        "term": "First",
        "learning_style": "visual",
        "weak_topics": ["matrices", "vectors", "probability"],
        "strong_topics": ["statistics"],
    },
    {
        "profile_id": "P8_ss3_auditory",
        "class_level": "SS3",
        "term": "Second",
        "learning_style": "auditory",
        "weak_topics": ["sequence_and_series"],
        "strong_topics": ["surds", "logarithms", "polynomials"],
    },
]

SUBJECT = "Mathematics"


def humanize_slug(slug: str) -> str:
    """Render a topic slug as a human-readable name (quadratic_equations -> Quadratic Equations).

    Used by the 'ungrounded_readable' arm so the baseline isn't primed by
    slug-formatted inputs.
    """
    return slug.replace("_", " ").title()

