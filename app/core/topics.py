from __future__ import annotations

# KNOWN SCOPE GAP — Literature is not covered by this allowlist. The active
# ENGLISH_TOPICS below has NO slugs for Literature content (poetry, drama, prose,
# folktales, oral literature), even though english_language.json carries
# substantial Literature topics at EVERY class level (e.g. "Introduction to
# Literature in English", "Literature: Drama and Poetry", "Literature: African
# Prose and Social Themes"). This is a documented, deliberate gap for the current
# pilot — NOT an oversight and NOT something to fix in this task. Flagged here so
# a future contributor sees it immediately rather than assuming Literature is
# already covered.
#
# Active English allowlist — every slug here maps to a real curriculum entry in
# app/data/curriculum/english_language.json via that entry's "slug" field.
# stress and intonation were each split into class-specific variants
# (_jss2/_ss1) because the curriculum carries them at two levels as distinct
# oral-English entries.
ENGLISH_TOPICS: list[str] = [
    "prepositions",
    "tenses",
    "sentence_structure",
    "synonyms",
    "antonyms",
    "idioms",
    "vocabulary_in_context",
    "comprehension",
    "reading_skills",
    "summary",
    "essay_writing",
    "letter_writing",
    "narrative_writing",
    "descriptive_writing",
    "articles",
    "vowel_sounds",
    "consonant_sounds",
    "stress_jss2",
    "stress_ss1",
    "intonation_jss2",
    "intonation_ss1",
]

# Reserved (NOT active) — English counterpart of MATHS_TOPICS_RESERVED. Slugs
# pulled from the active allowlist because they have no standalone curriculum
# entry to ground against. Intentionally NOT referenced by
# get_topics()/invalid_topics(); requests using these slugs are rejected as
# invalid, by design. Kept here (rather than deleted) so the reasoning survives
# and re-adding is a deliberate, documented act.
ENGLISH_TOPICS_RESERVED: list[str] = [
    # concord: taught as part of a larger grammar lesson (subject-verb agreement
    #   surfaces inside broader grammar/revision entries), never as its own
    #   lesson with its own curriculum entry.
    "concord",
    # inference: taught as a skill inside vocabulary/reading lessons — it appears
    #   in multiple lessons' objectives but never as a lesson title.
    "inference",
    # spelling: taught as part of vocabulary/proofreading lessons, not its own
    #   lesson.
    "spelling",
    # word_formation: does not appear to be covered anywhere in the current
    #   curriculum data — a genuine content gap, not a matching failure.
    "word_formation",
]

# Active Math allowlist — every slug here maps to a real curriculum entry in
# app/data/curriculum/mathematics.json via that entry's "slug" field.
# sequence_and_series, probability and coordinate_geometry were each split into
# class-specific variants because the curriculum carries them at two levels.
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
    "sets",
    "plane_geometry",
    "angles",
    "circles",
    "mensuration",
    "coordinate_geometry_ss1",
    "coordinate_geometry_ss2",
    "statistics",
    "probability_jss2",
    "probability_ss3",
    "sequence_arithmetic",
    "sequence_geometric",
    "commercial_arithmetic",
    "matrices",
    "trigonometry",
]

# Reserved (NOT active) — documented parking lot for slugs pulled from the active
# allowlist because they have no standalone curriculum entry to ground against.
# Intentionally NOT referenced by get_topics()/invalid_topics(); requests using
# these slugs are rejected as invalid, by design. Kept here (rather than deleted)
# so the reasoning survives and re-adding is a deliberate, documented act.
MATHS_TOPICS_RESERVED: list[str] = [
    # logic: appears only as a nested learning objective under the Binary Number
    #   System topic, not as a standalone curriculum entry.
    "logic",
    # polynomials: appears only as a nested learning objective under the
    #   Differentiation / Integration topics, not as a standalone entry.
    "polynomials",
    # triangles: a cross-cutting concept spread across 5+ curriculum topics
    #   (Pythagoras, similarity, trigonometry, construction, ...), with no single
    #   owning entry to ground against.
    "triangles",
    # vectors: confirmed absent from the curriculum entirely — a genuine content
    #   gap. Reinstating it would require authoring new curriculum content first,
    #   not merely re-adding the slug.
    "vectors",
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
