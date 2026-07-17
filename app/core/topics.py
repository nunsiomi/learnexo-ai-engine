from __future__ import annotations

ENGLISH_TOPICS: list[str] = [
    "concord",
    "tenses",
    "articles",
    "prepositions",
    "sentence_structure",
    "comprehension",
    "inference",
    "vocabulary_in_context",
    "summary",
    "reading_skills",
    "synonyms",
    "antonyms",
    "idioms",
    "word_formation",
    "spelling",
    "vowel_sounds",
    "consonant_sounds",
    "stress",
    "intonation",
    "essay_writing",
    "letter_writing",
    "narrative_writing",
    "descriptive_writing",
]

MATHS_TOPICS: list[str] = [
    "numbers_and_numeration",
    "basic_operations",
    "fractions",
    "decimals",
    "percentages",
    "ratio_and_proportion",
    "indices",
    "logarithms",
    "surds",
    "algebraic_expressions",
    "linear_equations",
    "simultaneous_equations",
    "quadratic_equations",
    "inequalities",
    "polynomials",
    "sets",
    "logic",
    "plane_geometry",
    "angles",
    "triangles",
    "circles",
    "mensuration",
    "coordinate_geometry",
    "vectors",
    "statistics",
    "probability",
    "sequence_and_series",
    "commercial_arithmetic",
    "matrices",
    "trigonometry",
]

SUBJECT_TOPICS: dict[str, list[str]] = {
    "English Language": ENGLISH_TOPICS,
    "Mathematics": MATHS_TOPICS,
}


def get_topics(subject: str) -> list[str]:
    """Return the valid topic slugs for a subject, or [] for unknown subjects."""
    return SUBJECT_TOPICS.get(subject, [])


def invalid_topics(topics: list[str], subject: str) -> list[str]:
    """Return any topic slugs not in the subject's allowlist."""
    valid = set(get_topics(subject))
    if not valid:
        return []
    return [t for t in topics if t not in valid]
