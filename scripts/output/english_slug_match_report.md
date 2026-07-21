# English Language Slug ↔ Curriculum Match Report

**Scoring: token-based Jaccard word-set overlap** (intersection over union of stop-word-filtered words), with `difflib.SequenceMatcher` used only as a tiebreaker for equal Jaccard scores — identical to the Mathematics script's method. **Matching covers the full JSS1-SS3 range** (all six class levels in one primary pool) from the start; there is no JSS-only pre-pass. Read-only diagnostic: no source files were modified.

**Thresholds used** (re-tuned for English independently of Math — see script comments for the reasoning)

- `CONFIDENT_THRESHOLD` = 0.3  (Math uses 0.34)
- `AMBIGUOUS_GAP` = 0.1  (same as Math)
- `MATCH_FLOOR` = 0.12  (Math uses 0.15)
- `COVERAGE_FLOOR` = 0.12  (Math uses 0.15)

**Scope of matching:** 23 allowlist slugs vs 72 curriculum topics across the full JSS1-SS3 range (JSS1, JSS2, JSS3, SS1, SS2, SS3 — all in one primary pass).

**Summary:** 2 confident · 17 ambiguous · 4 unmatched · 28 curriculum topics with no slug · 5 shared-entry group(s) · 0 duplicate title(s).

**Version note (v2 — plural normalization):** This version adds basic singular/plural normalization to the token step (a guarded trailing-"s" strip via `_singular`, applied identically to slugs and titles) and **supersedes the prior report**. It was prompted by `articles` scoring 0.000 against curriculum titles that use the singular "Article". The strip did more than fix `articles` alone — every slug/title whose top match or bucket moved is listed here:

- `articles`: **unmatched → ambiguous** (0.000 → 0.250; best is now "Report and Feature Article Writing", SS2 Second). The intended fix.
- `essay_writing`: **top match changed** — from "Summary Writing" (SS1 Second, 0.333) to "Composition Writing: Descriptive and Narrative Essays" (JSS2 First, 0.400), because "Essays" now folds to "essay". Still ambiguous, but a different owning entry.
- Section 4 (coverage): **4 curriculum titles left the no-slug list** — "Composition: Expository and Argumentative Essays" (JSS1 Second, now via `essay_writing`); "Grammar: Complex Sentences and Conditional Clauses" (SS1 First, "Sentences"→"sentence", now via `sentence_structure`); "Report and Feature Article Writing" (SS2 Second, now via `articles`); and "Oral English: Public Speaking and Advanced Sound Work" (SS2 Second, "Sounds"↔"Sound", now via `consonant_sounds`).
- Section 5 (shared-entry): `essay_writing` moved into the "…Descriptive and Narrative Essays" group (now 3 slugs) and the old "Summary Writing" 2-slug group dissolved, so groups went 6 → 5.
- Scope SS-reach evidence: the 5-slug list keeps its count but changes membership — `articles` now lands on an SS title, `essay_writing` no longer does (its best is now a JSS2 entry).
- Net bucket counts: 2 confident (unchanged), 17 ambiguous (+1), 4 unmatched (−1). `concord`, `inference`, `word_formation` and `spelling` stay unmatched — they share no title token in either spelling.

## ENGLISH_TOPICS Intended Scope (Task 2)

**Finding:** NOT scoped by class level anywhere in code, and consistent with the confirmed FULL JSS1-SS3 project scope - it is NOT a JSS-only list. But note the caveat below: unlike Mathematics, no English slug is SS-exclusive, so 'reaches SS' is established from where matches land, not from slug composition.

Evidence from `app/core/topics.py` and this run:

- `ENGLISH_TOPICS` has no docstring or comment stating its scope, and its name carries no `JSS`/`SS` qualifier (it mirrors `MATHS_TOPICS`).
- `get_topics()` / `invalid_topics()` return and validate against the whole flat list; there is no class-level filtering anywhere in topics.py.
- Unlike Mathematics (where `surds`, `logarithms`, `matrices` are intrinsically SS-only and prove SS reach by composition), every English slug is a generic, level-agnostic concept - grammar points (`concord`, `tenses`, `prepositions`), oral-English sounds (`vowel_sounds`, `consonant_sounds`, `stress`, `intonation`) and reading/writing skills (`summary`, `comprehension`, `essay_writing`) that ALL recur across both JSS and SS. So NO slug is SS-exclusive; scope cannot be inferred from composition the way it was for Math.
- This run (full JSS1-SS3 pool): 5 slug(s) have their best match on an SS1-SS3 title (`summary`, `articles`, `vocabulary_in_context`, `reading_skills`, `idioms`) - so the allowlist does reach SS.
- The gap to flag for English is the OPPOSITE of a scope-narrowing one: several SS-distinctive English topics have NO slug at all (e.g. conditional clauses, reported speech, registers, nominalisation, speech/article/report writing) - see 'Curriculum Topics With No Slug'. So while the allowlist is nominally full-range, its SS coverage is thin.

## 1. Confident Matches

_Sorted by score ascending, so the weakest 'confident' calls sit at the top._

| Slug | Best curriculum title | Class | Term | Score | Gap to 2nd |
| --- | --- | --- | --- | --- | --- |
| `summary` | Summary Writing | SS1 | Second | 0.500 | 0.167 |
| `letter_writing` | Formal and Informal Letter Writing | JSS1 | Second | 0.500 | 0.167 |

## 2. Ambiguous

_Sorted by best score descending. Multiple curriculum titles score close together, or the best score sits below the confident threshold._

- `consonant_sounds` — best 0.400, gap 0.067:
    - Oral English: Diphthongs and Consonant Sounds (JSS1 Third) — 0.400
    - Oral English: Consonant Contrasts and Nasal Sounds (JSS3 Second) — 0.333
    - Oral English: Revision of Vowel and Consonant Sounds (JSS2 First) — 0.333
- `essay_writing` — best 0.400, gap 0.067:
    - Composition Writing: Descriptive and Narrative Essays (JSS2 First) — 0.400
    - Summary Writing (SS1 Second) — 0.333
    - Composition: Article Writing, Expository and Argumentative Essays (JSS3 Second) — 0.333
- `narrative_writing` — best 0.400, gap 0.067:
    - Composition Writing: Descriptive and Narrative Essays (JSS2 First) — 0.400
    - Summary Writing (SS1 Second) — 0.333
    - Summary Writing (Advanced) (SS2 Second) — 0.250
- `descriptive_writing` — best 0.400, gap 0.067:
    - Composition Writing: Descriptive and Narrative Essays (JSS2 First) — 0.400
    - Summary Writing (SS1 Second) — 0.333
    - Composition and Dialogue Writing (JSS2 Third) — 0.250
- `vowel_sounds` — best 0.333, gap 0.000:
    - Oral English: Vowel Sounds (Continued) and Tenses (JSS1 Second) — 0.333
    - Oral English: Revision of Vowel and Consonant Sounds (JSS2 First) — 0.333
    - Oral English: Sounds, Stress and Intonation (SS1 First) — 0.167
- `articles` — best 0.250, gap 0.083:
    - Report and Feature Article Writing (SS2 Second) — 0.250
    - Composition: Article Writing, Expository and Argumentative Essays (JSS3 Second) — 0.167
    - Summary Writing (Advanced) (SS2 Second) — 0.000
- `comprehension` — best 0.250, gap 0.000:
    - Summary Writing and Reading Comprehension (JSS1 Third) — 0.250
    - Reading Comprehension and Vocabulary Development (SS1 First) — 0.250
    - Reading Comprehension: Speed Reading and Summarising (JSS2 Second) — 0.250
- `sentence_structure` — best 0.200, gap 0.033:
    - Grammar: Sentence Types and Pronouns (JSS3 Second) — 0.200
    - Grammar: Complex Sentences and Conditional Clauses (SS1 First) — 0.167
    - Advanced Grammar: Nominalisation, Passive and Complex Structures (SS2 First) — 0.143
- `vocabulary_in_context` — best 0.200, gap 0.033:
    - Reading Comprehension and Vocabulary Development (SS1 First) — 0.200
    - Vocabulary: Registers, Idioms and Technical Language (SS2 First) — 0.167
    - BECE Comprehensive Revision: Reading and Vocabulary (JSS3 Third) — 0.167
- `reading_skills` — best 0.200, gap 0.000:
    - Reading Comprehension and Vocabulary Development (SS1 First) — 0.200
    - Summary Writing and Reading Comprehension (JSS1 Third) — 0.200
    - Introduction to Speech and Language Skills (JSS1 First) — 0.200
- `idioms` — best 0.200, gap 0.200:
    - Vocabulary: Registers, Idioms and Technical Language (SS2 First) — 0.200
    - Grammar Revision and Modal Forms (JSS3 First) — 0.000
    - Summary Writing and Reading Comprehension (JSS1 Third) — 0.000
- `stress` — best 0.200, gap 0.000:
    - Oral English: Intonation, Stress and Rhythm (JSS2 Second) — 0.200
    - Oral English: Sounds, Stress and Intonation (SS1 First) — 0.200
    - Oral English: Schwa, Stress, Intonation and Consonant Contrasts (JSS3 First) — 0.143
- `intonation` — best 0.200, gap 0.000:
    - Oral English: Intonation, Stress and Rhythm (JSS2 Second) — 0.200
    - Oral English: Sounds, Stress and Intonation (SS1 First) — 0.200
    - Oral English: Schwa, Stress, Intonation and Consonant Contrasts (JSS3 First) — 0.143
- `tenses` — best 0.167, gap 0.000:
    - Oral English: Vowel Sounds (Continued) and Tenses (JSS1 Second) — 0.167
    - Grammar: Voice, Tenses and Direct/Indirect Speech (JSS2 First) — 0.167
    - Parts of Speech (1): Nouns, Pronouns and Verbs (JSS1 First) — 0.000
- `synonyms` — best 0.167, gap 0.167:
    - Grammar: Conjunctions, Synonyms, Antonyms and Causative Verbs (JSS2 Third) — 0.167
    - Grammar: Sentence Types and Pronouns (JSS3 Second) — 0.000
    - Summary Writing (SS1 Second) — 0.000
- `antonyms` — best 0.167, gap 0.167:
    - Grammar: Conjunctions, Synonyms, Antonyms and Causative Verbs (JSS2 Third) — 0.167
    - Oral English: Intonation, Stress and Rhythm (JSS2 Second) — 0.000
    - Grammar Revision and Modal Forms (JSS3 First) — 0.000
- `prepositions` — best 0.143, gap 0.143:
    - Parts of Speech (2): Adjectives, Adverbs, Prepositions and Conjunctions (JSS1 First) — 0.143
    - Summary Writing (SS1 Second) — 0.000
    - Composition Writing: Introduction (JSS1 First) — 0.000

## 3. Unmatched

_Sorted by best score descending, so near-misses (just under `MATCH_FLOOR`) are easiest to scan first. With the full JSS1-SS3 range in the pool, a slug here shares essentially no word with any curriculum title — for English that usually means the concept lives only inside subtopics (e.g. `concord`, `spelling`), never in a topic title._

| Slug | Closest curriculum title | Class | Term | Score |
| --- | --- | --- | --- | --- |
| `concord` | Oral English: Consonant Contrasts and Review | JSS2 | Third | 0.000 |
| `inference` | Literature: Drama and Poetry | SS1 | Second | 0.000 |
| `word_formation` | Report and Feature Article Writing | SS2 | Second | 0.000 |
| `spelling` | Summary Writing | SS1 | Second | 0.000 |

## 4. Curriculum Topics With No Allowlist Slug

_JSS1-SS3 curriculum titles whose best-matching slug scores below `COVERAGE_FLOOR`. Sorted by score descending — the allowlist may be missing these topics. Closest near-misses appear first._

| Curriculum title | Class | Term | Closest slug | Score |
| --- | --- | --- | --- | --- |
| Parts of Speech (1): Nouns, Pronouns and Verbs | JSS1 | First | `vowel_sounds` | 0.000 |
| Introduction to Literature in English | JSS1 | First | `narrative_writing` | 0.000 |
| Literature: Poetry, Myths and Legends | JSS1 | Second | `letter_writing` | 0.000 |
| Grammar: Active and Passive Voice, and Tag Questions | JSS1 | Third | `narrative_writing` | 0.000 |
| Composition Revision and Oral Composition | JSS1 | Third | `comprehension` | 0.000 |
| Literature Revision: Prose, Drama, Poetry and Figures of Speech | JSS1 | Third | `letter_writing` | 0.000 |
| Literature: Prose Features, Folktales and Figures of Speech | JSS2 | First | `reading_skills` | 0.000 |
| Grammar: Reported Speech (Commands and Requests) and Punctuation | JSS2 | Second | `word_formation` | 0.000 |
| Literature: Drama, Figures of Speech and Recommended Texts | JSS2 | Second | `vocabulary_in_context` | 0.000 |
| Literature Revision: Myths, Drama and Recommended Texts | JSS2 | Third | `vocabulary_in_context` | 0.000 |
| Grammar Revision and Modal Forms | JSS3 | First | `prepositions` | 0.000 |
| Literature: Fiction, Poetry and Rhyme Schemes | JSS3 | First | `letter_writing` | 0.000 |
| Literature: Poetry, Drama and Prose Revision | JSS3 | Second | `comprehension` | 0.000 |
| BECE Comprehensive Revision: Grammar and Oral English | JSS3 | Third | `comprehension` | 0.000 |
| BECE Comprehensive Revision: Literature | JSS3 | Third | `comprehension` | 0.000 |
| Literature: Introduction to Prose and the Novel | SS1 | First | `vocabulary_in_context` | 0.000 |
| Literature: Drama and Poetry | SS1 | Second | `letter_writing` | 0.000 |
| WAEC/NECO Comprehensive English Revision | SS1 | Third | `comprehension` | 0.000 |
| Literature: African Prose and Social Themes | SS2 | First | `reading_skills` | 0.000 |
| Literature: Poetry and Drama (Advanced) | SS2 | Second | `word_formation` | 0.000 |
| WAEC/NECO Revision: Language Paper | SS2 | Third | `comprehension` | 0.000 |
| WAEC/NECO Revision: Composition and Literature | SS2 | Third | `prepositions` | 0.000 |
| Oral English: Comprehensive WAEC/NECO Preparation | SS3 | First | `comprehension` | 0.000 |
| Grammar: Comprehensive WAEC/NECO Revision | SS3 | First | `comprehension` | 0.000 |
| Literature: WAEC/NECO Set Texts and Exam Technique | SS3 | First | `vocabulary_in_context` | 0.000 |
| WAEC/NECO/JAMB Full Revision: Language Papers | SS3 | Second | `vocabulary_in_context` | 0.000 |
| JAMB Use of English: Specific Preparation | SS3 | Second | `sentence_structure` | 0.000 |
| Final Examinations: Mock Papers and Guided Revision | SS3 | Third | `letter_writing` | 0.000 |

## 5. Shared-Entry Candidates

_Curriculum entries that are the single best match for MORE THAN ONE slug. Decide per group whether the entry legitimately owns several slugs or whether it's a false collision from a shared framing word (e.g. 'Writing'). Sorted by number of contending slugs descending._

- **Composition Writing: Descriptive and Narrative Essays** (JSS2 First) — 3 slugs: `essay_writing` (0.400), `narrative_writing` (0.400), `descriptive_writing` (0.400)
- **Grammar: Conjunctions, Synonyms, Antonyms and Causative Verbs** (JSS2 Third) — 2 slugs: `synonyms` (0.167), `antonyms` (0.167)
- **Oral English: Intonation, Stress and Rhythm** (JSS2 Second) — 2 slugs: `stress` (0.200), `intonation` (0.200)
- **Oral English: Vowel Sounds (Continued) and Tenses** (JSS1 Second) — 2 slugs: `vowel_sounds` (0.333), `tenses` (0.167)
- **Reading Comprehension and Vocabulary Development** (SS1 First) — 2 slugs: `vocabulary_in_context` (0.200), `reading_skills` (0.200)

## 6. Duplicate-Title Candidates

_Curriculum title strings that appear at more than one class-level/term position. A slug matching one of these is inherently ambiguous about which class level it grounds to. Detected from the curriculum alone, independent of the allowlist. Sorted by number of positions descending._

_None — every curriculum title string is unique to a single class-level/term position._
