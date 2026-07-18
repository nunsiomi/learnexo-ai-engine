"""
match_english_slugs.py — READ-ONLY diagnostic.

Fuzzy-matches the English Language topic allowlist (app/core/topics.py) against
the FULL JSS1-SS3 range of the English curriculum (app/data/curriculum/
english_language.json) and writes a markdown report to
scripts/output/english_slug_match_report.md.

This is the English counterpart of scripts/match_math_slugs.py and deliberately
mirrors its structure, scoring and style — the ONLY intentional differences are:
  * the subject/paths/variable name (ENGLISH_TOPICS via get_topics),
  * the four thresholds, re-tuned for English's data (see the block below),
  * an English-specific scope finding, and
  * two extra proactively-computed sections (Shared-Entry Candidates and
    Duplicate-Title Candidates) that Math only added after manual review.

This script only READS those two files. It never modifies topics.py, the
curriculum JSON, or anything under git. The only thing it writes is its own
markdown report inside scripts/output/.

Scoring method: TOKEN-BASED Jaccard similarity (word-set overlap), NOT character
ratio — identical to the Math script's v3. Both slug and title are lowercased,
stripped of punctuation, split on whitespace/underscore, and reduced to a set of
words with common stop words ("and", "of", "the", ...) removed. Score =
|A ∩ B| / |A ∪ B|. difflib.SequenceMatcher (stdlib) survives ONLY as a
tiebreaker: when two candidates have an identical Jaccard score, the one with the
higher character ratio wins.

Scope note: the full JSS1-SS3 range is in the SINGLE primary matching pool from
the start. We do NOT do a JSS-only pass first — the Math exercise showed that
narrowing scope up front only creates rework once SS is confirmed in scope, and
project scope is confirmed JSS1-SS3 (Fix_Roadmap.md).

No new dependency is introduced (rapidfuzz is not in requirements.txt).

Run from the repo root:
    python scripts/match_english_slugs.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

# --------------------------------------------------------------------------- #
# Tunable thresholds — change these to re-bucket without touching the logic.
#
# These are re-tuned for ENGLISH independently of Math; the Math values do NOT
# transfer, because the two data sets have very different shapes:
#
#   * Math slugs are mostly the literal topic word ("trigonometry", "matrices")
#     and Math titles are fairly short, so a genuine match often shares a large
#     fraction of the combined token set.
#   * English slugs are terse grammatical/skill labels ("prepositions",
#     "vowel_sounds", "letter_writing") while English curriculum titles are long
#     and descriptive ("Parts of Speech (2): Adjectives, Adverbs, Prepositions
#     and Conjunctions", ~7 content tokens). A CORRECT single-concept match
#     therefore shares just 1 token out of 6-8 union tokens ≈ 0.12-0.17, and even
#     a strong two-token match ("letter_writing" -> "Formal and Informal Letter
#     Writing") only reaches ~0.40. English Jaccard scores run structurally lower
#     than Math's for equally-good matches, so every threshold is pulled DOWN.
#
# A further English-specific effect: the curriculum reuses a small vocabulary of
# framing words ("Oral English", "Composition", "Writing", "Sounds",
# "Comprehension") across many terms and levels. That makes near-ties between
# curriculum entries the NORM, not the exception, so the AMBIGUOUS_GAP test —
# not the confident threshold — is what places most English slugs in Ambiguous.
# That abundance of ambiguity is a real signal and is exactly what the
# Shared-Entry / Duplicate-Title sections below exist to explain.
# --------------------------------------------------------------------------- #
# A slug's best curriculum match must score at least this to be a CONFIDENT match.
# 0.30 ≈ "a strong, mostly two-token overlap on the English scale" (e.g. both
# words of a 2-word slug land in the title). Lower than Math's 0.34 because
# English's long titles dilute the union and depress Jaccard for equally-good
# matches.
CONFIDENT_THRESHOLD = 0.30
# The best match must beat the second-best by at least this much; otherwise the
# slug is AMBIGUOUS. Kept at Math's 0.10 (~one clear extra shared token). Note:
# because English recycles framing words, genuine ties are common, so this test
# intentionally routes many slugs to Ambiguous even when their top score is
# respectable.
AMBIGUOUS_GAP = 0.10
# Below this similarity a slug is UNMATCHED. 0.12 (below Math's 0.15) so that a
# correct-but-weak single-concept hit against a ~7-word English title (≈0.12-0.14)
# still registers as a faint match, while slugs that share literally NO title
# token (e.g. `concord`, `spelling`, which live only inside subtopics) score 0.0
# and are cleanly unmatched. For English, "shares zero title tokens" is the
# meaningful unmatched line.
MATCH_FLOOR = 0.12
# Reverse pass: a curriculum title whose best-matching slug scores below this is
# flagged as having no allowlist slug at all. Kept equal to MATCH_FLOOR.
COVERAGE_FLOOR = 0.12
# How many close runner-up candidates to display for AMBIGUOUS slugs.
AMBIGUOUS_SHOW = 3

# All class levels form the SINGLE primary matching pool (full JSS1-SS3 project
# scope). SS_LEVELS is retained only to label which matches are senior-secondary
# in the scope evidence.
ALL_LEVELS = ("JSS1", "JSS2", "JSS3", "SS1", "SS2", "SS3")
SS_LEVELS = ("SS1", "SS2", "SS3")

# Stop words dropped from every word set before scoring. Kept deliberately small
# so only true connectives are removed, not content words.
STOP_WORDS = {
    "and", "of", "the", "in", "a", "an", "to", "for", "with", "on", "or",
}

# --------------------------------------------------------------------------- #
# Paths (all derived from this file's location — no hard-coded absolutes).
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[1]
TOPICS_PATH = REPO_ROOT / "app" / "core" / "topics.py"
CURRICULUM_PATH = REPO_ROOT / "app" / "data" / "curriculum" / "english_language.json"
OUTPUT_DIR = REPO_ROOT / "scripts" / "output"
REPORT_PATH = OUTPUT_DIR / "english_slug_match_report.md"


# --------------------------------------------------------------------------- #
# Input loading
# --------------------------------------------------------------------------- #
def load_allowlist_slugs() -> list[str]:
    """Read the English Language slug allowlist from app/core/topics.py.

    Prefers importing get_topics(); falls back to regex-parsing ENGLISH_TOPICS so
    the script still works even if the package can't be imported.
    """
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from app.core.topics import get_topics  # type: ignore

        slugs = get_topics("English Language")
        if slugs:
            return list(slugs)
    except Exception as exc:  # pragma: no cover - defensive fallback
        print(f"[warn] import of app.core.topics failed ({exc}); parsing file instead")

    # Fallback: parse the ENGLISH_TOPICS = [...] literal directly.
    topics_src = TOPICS_PATH.read_text(encoding="utf-8")
    match = re.search(r"ENGLISH_TOPICS\s*[:=].*?\[(.*?)\]", topics_src, re.DOTALL)
    if not match:
        raise RuntimeError("Could not locate ENGLISH_TOPICS in app/core/topics.py")
    return re.findall(r'"([^"]+)"', match.group(1))


def load_titles(levels: tuple[str, ...]) -> list[tuple[str, str, str]]:
    """Return (class_level, term, topic_title) for every topic in the given levels."""
    data = json.loads(CURRICULUM_PATH.read_text(encoding="utf-8"))
    class_levels = data.get("class_levels", {})
    entries: list[tuple[str, str, str]] = []
    for level in levels:
        terms = class_levels.get(level, {})
        for term, topic_list in terms.items():
            for topic in topic_list:
                title = topic.get("topic")
                if title:
                    entries.append((level, term, title))
    return entries


# --------------------------------------------------------------------------- #
# Scoring — token-based Jaccard, with SequenceMatcher only as a tiebreaker.
# --------------------------------------------------------------------------- #
def _singular(tok: str) -> str:
    """Crudely fold a plural token to its singular form via a trailing-"s" strip.

    Deliberately NOT a real stemmer (no library, no dependency): just enough to
    stop "articles"/"article", "essays"/"essay", "sounds"/"sound" scoring as
    different words. Two guards keep it from mangling genuine singulars:
      * skip tokens ending in "ss" ("stress", "class") — that "s" is not a plural,
      * skip tokens of 3 chars or fewer, so short words aren't hollowed out.
    Applied inside tokenize(), so BOTH slugs and titles are folded identically.
    """
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def tokenize(text: str) -> set[str]:
    """Lowercase, underscores/punctuation -> spaces, split to a stop-word-free set.

    Tokens are singularized (basic trailing-"s" strip, see _singular) so plural /
    singular spellings of the same word match — e.g. the slug `articles` now
    aligns with curriculum titles that say "Article Writing".
    """
    text = text.lower().replace("_", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)  # drop punctuation / symbols
    return {_singular(tok) for tok in text.split() if tok and tok not in STOP_WORDS}


def normalize(text: str) -> str:
    """Full normalized string used only for the SequenceMatcher tiebreaker."""
    text = text.lower().replace("_", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def jaccard(a: str, b: str) -> float:
    """Primary score: token-set intersection over union, in [0, 1]."""
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def char_ratio(a: str, b: str) -> float:
    """Tiebreaker only: normalized SequenceMatcher character ratio in [0, 1]."""
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


# --------------------------------------------------------------------------- #
# Forward pass: slug -> curriculum
# --------------------------------------------------------------------------- #
def score_slug(slug: str, titles: list[tuple[str, str, str]]) -> list[dict]:
    """All candidate matches for a slug, sorted by Jaccard (char ratio breaks ties)."""
    candidates = [
        {
            "level": level,
            "term": term,
            "title": title,
            "score": jaccard(slug, title),
            "tie": char_ratio(slug, title),
        }
        for (level, term, title) in titles
    ]
    # Sort by Jaccard desc; identical Jaccard scores fall back to char ratio desc.
    candidates.sort(key=lambda c: (c["score"], c["tie"]), reverse=True)
    return candidates


def bucket_slug(candidates: list[dict]) -> tuple[str, float, float]:
    """Return (bucket, best_score, gap) for a slug given its ranked candidates."""
    best = candidates[0]["score"] if candidates else 0.0
    second = candidates[1]["score"] if len(candidates) > 1 else 0.0
    gap = best - second

    if best < MATCH_FLOOR:
        return "unmatched", best, gap
    if best >= CONFIDENT_THRESHOLD and gap >= AMBIGUOUS_GAP:
        return "confident", best, gap
    return "ambiguous", best, gap


# --------------------------------------------------------------------------- #
# Reverse pass: curriculum -> slug
# --------------------------------------------------------------------------- #
def uncovered_titles(
    titles: list[tuple[str, str, str]], slugs: list[str]
) -> list[dict]:
    """Curriculum titles whose best-matching slug scores below COVERAGE_FLOOR."""
    rows: list[dict] = []
    for (level, term, title) in titles:
        best_slug, best_score, best_tie = None, 0.0, 0.0
        for slug in slugs:
            s = jaccard(slug, title)
            t = char_ratio(slug, title)
            if (s, t) > (best_score, best_tie):
                best_slug, best_score, best_tie = slug, s, t
        if best_score < COVERAGE_FLOOR:
            rows.append(
                {"level": level, "term": term, "title": title,
                 "best_slug": best_slug, "score": best_score}
            )
    return rows


# --------------------------------------------------------------------------- #
# Task 7a: shared-entry candidates.
#
# Multiple slugs whose SINGLE best-matching curriculum entry (identified by
# level+term+title) is the same one. These are the cases where two allowlist
# concepts would ground to the same lesson — worth a human deciding whether one
# entry should legitimately own several slugs (as Math's "Indices and Logarithms"
# did) or whether it's a false collision from a shared framing word ("Writing").
# Only slugs whose best score clears MATCH_FLOOR are considered — a shared "best"
# at 0.0 is meaningless.
# --------------------------------------------------------------------------- #
def shared_entry_candidates(matched_rows: list[dict]) -> list[dict]:
    """Group matched slugs by the identity of their single best candidate entry."""
    groups: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in matched_rows:
        best = row["candidates"][0]
        if best["score"] < MATCH_FLOOR:
            continue
        key = (best["level"], best["term"], best["title"])
        groups[key].append({"slug": row["slug"], "score": best["score"]})
    shared = [
        {"level": lvl, "term": term, "title": title,
         "slugs": sorted(members, key=lambda m: m["score"], reverse=True)}
        for (lvl, term, title), members in groups.items()
        if len(members) > 1
    ]
    # Most-contested entries first, then alphabetical by title for stability.
    shared.sort(key=lambda g: (-len(g["slugs"]), g["title"]))
    return shared


# --------------------------------------------------------------------------- #
# Task 7b: duplicate-title candidates.
#
# One curriculum title string appearing at more than one class-level/term slot.
# A duplicate title means a slug matching it is inherently ambiguous about WHICH
# class level it grounds to (Math hit this with "Probability" at JSS2 and SS3).
# Detected purely from the curriculum, independent of the allowlist.
# --------------------------------------------------------------------------- #
def duplicate_titles(titles: list[tuple[str, str, str]]) -> list[dict]:
    """Curriculum titles that occur at 2+ distinct (level, term) positions."""
    positions: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for (level, term, title) in titles:
        positions[title].append((level, term))
    dupes = [
        {"title": title, "positions": pos}
        for title, pos in positions.items()
        if len(pos) > 1
    ]
    dupes.sort(key=lambda d: (-len(d["positions"]), d["title"]))
    return dupes


# --------------------------------------------------------------------------- #
# Task 2: describe the intended scope of ENGLISH_TOPICS from the file's contents.
# --------------------------------------------------------------------------- #
def analyze_scope(matched_rows: list[dict]) -> tuple[str, list[str]]:
    """Return (verdict, evidence_lines) about ENGLISH_TOPICS's intended scope.

    Unlike Math, English has no intrinsically-SS slug (every concept recurs at
    JSS and SS), so the scope call rests on (a) the absence of any scoping code
    and (b) how many slugs' best match actually lands on an SS-level title.
    """
    ss_matched = [
        r["slug"] for r in matched_rows
        if r["candidates"][0]["score"] >= MATCH_FLOOR
        and r["candidates"][0]["level"] in SS_LEVELS
    ]
    reaches_ss = len(ss_matched) > 0

    if reaches_ss:
        verdict = (
            "NOT scoped by class level anywhere in code, and consistent with the "
            "confirmed FULL JSS1-SS3 project scope - it is NOT a JSS-only list. "
            "But note the caveat below: unlike Mathematics, no English slug is "
            "SS-exclusive, so 'reaches SS' is established from where matches land, "
            "not from slug composition."
        )
    else:
        verdict = (
            "NOT scoped in code, but NONE of the slugs' best matches land on an "
            "SS-level title - so although the project scope is confirmed JSS1-SS3, "
            "this allowlist may not actually reach SS content. FLAG as a possible "
            "coverage gap, not assumed fine."
        )

    evidence = [
        "`ENGLISH_TOPICS` has no docstring or comment stating its scope, and its "
        "name carries no `JSS`/`SS` qualifier (it mirrors `MATHS_TOPICS`).",
        "`get_topics()` / `invalid_topics()` return and validate against the whole "
        "flat list; there is no class-level filtering anywhere in topics.py.",
        "Unlike Mathematics (where `surds`, `logarithms`, `matrices` are "
        "intrinsically SS-only and prove SS reach by composition), every English "
        "slug is a generic, level-agnostic concept - grammar points (`concord`, "
        "`tenses`, `prepositions`), oral-English sounds (`vowel_sounds`, "
        "`consonant_sounds`, `stress`, `intonation`) and reading/writing skills "
        "(`summary`, `comprehension`, `essay_writing`) that ALL recur across both "
        "JSS and SS. So NO slug is SS-exclusive; scope cannot be inferred from "
        "composition the way it was for Math.",
        f"This run (full JSS1-SS3 pool): {len(ss_matched)} slug(s) have their best "
        f"match on an SS1-SS3 title "
        f"({', '.join('`' + s + '`' for s in ss_matched) if ss_matched else 'none'})"
        f"{' - so the allowlist does reach SS.' if reaches_ss else ' - so the allowlist may not reach SS at all.'}",
        "The gap to flag for English is the OPPOSITE of a scope-narrowing one: "
        "several SS-distinctive English topics have NO slug at all (e.g. "
        "conditional clauses, reported speech, registers, nominalisation, "
        "speech/article/report writing) - see 'Curriculum Topics With No Slug'. "
        "So while the allowlist is nominally full-range, its SS coverage is thin.",
    ]
    return verdict, evidence


# --------------------------------------------------------------------------- #
# Report rendering
# --------------------------------------------------------------------------- #
def fmt_candidate(c: dict) -> str:
    return f"{c['title']} ({c['level']} {c['term']}) — {c['score']:.3f}"


def build_report(
    confident: list[dict], ambiguous: list[dict], unmatched: list[dict],
    uncovered: list[dict], shared: list[dict], dupes: list[dict],
    scope_verdict: str, scope_evidence: list[str],
    n_slugs: int, n_titles: int,
) -> str:
    lines: list[str] = []
    lines.append("# English Language Slug ↔ Curriculum Match Report")
    lines.append("")
    lines.append(
        "**Scoring: token-based Jaccard word-set overlap** (intersection over "
        "union of stop-word-filtered words), with `difflib.SequenceMatcher` used "
        "only as a tiebreaker for equal Jaccard scores — identical to the "
        "Mathematics script's method. **Matching covers the full JSS1-SS3 range** "
        "(all six class levels in one primary pool) from the start; there is no "
        "JSS-only pre-pass. Read-only diagnostic: no source files were modified."
    )
    lines.append("")
    lines.append(
        "**Thresholds used** (re-tuned for English independently of Math — see "
        "script comments for the reasoning)"
    )
    lines.append("")
    lines.append(f"- `CONFIDENT_THRESHOLD` = {CONFIDENT_THRESHOLD}  (Math uses 0.34)")
    lines.append(f"- `AMBIGUOUS_GAP` = {AMBIGUOUS_GAP}  (same as Math)")
    lines.append(f"- `MATCH_FLOOR` = {MATCH_FLOOR}  (Math uses 0.15)")
    lines.append(f"- `COVERAGE_FLOOR` = {COVERAGE_FLOOR}  (Math uses 0.15)")
    lines.append("")
    lines.append(
        f"**Scope of matching:** {n_slugs} allowlist slugs vs {n_titles} "
        "curriculum topics across the full JSS1-SS3 range (JSS1, JSS2, JSS3, "
        "SS1, SS2, SS3 — all in one primary pass)."
    )
    lines.append("")
    lines.append(
        f"**Summary:** {len(confident)} confident · {len(ambiguous)} ambiguous · "
        f"{len(unmatched)} unmatched · {len(uncovered)} curriculum topics with no "
        f"slug · {len(shared)} shared-entry group(s) · {len(dupes)} duplicate title(s)."
    )
    lines.append("")

    # --- Version note: what the plural-normalization fix changed ---------- #
    # Hand-authored from a direct before/after diff of the prior (no-plural)
    # report against this run, so the reader can see the fix was NOT a one-off.
    lines.append(
        "**Version note (v2 — plural normalization):** This version adds basic "
        "singular/plural normalization to the token step (a guarded trailing-\"s\" "
        "strip via `_singular`, applied identically to slugs and titles) and "
        "**supersedes the prior report**. It was prompted by `articles` scoring "
        "0.000 against curriculum titles that use the singular \"Article\". The "
        "strip did more than fix `articles` alone — every slug/title whose top "
        "match or bucket moved is listed here:"
    )
    lines.append("")
    lines.append(
        "- `articles`: **unmatched → ambiguous** (0.000 → 0.250; best is now "
        "\"Report and Feature Article Writing\", SS2 Second). The intended fix."
    )
    lines.append(
        "- `essay_writing`: **top match changed** — from \"Summary Writing\" (SS1 "
        "Second, 0.333) to \"Composition Writing: Descriptive and Narrative Essays\" "
        "(JSS2 First, 0.400), because \"Essays\" now folds to \"essay\". Still "
        "ambiguous, but a different owning entry."
    )
    lines.append(
        "- Section 4 (coverage): **4 curriculum titles left the no-slug list** — "
        "\"Composition: Expository and Argumentative Essays\" (JSS1 Second, now via "
        "`essay_writing`); \"Grammar: Complex Sentences and Conditional Clauses\" "
        "(SS1 First, \"Sentences\"→\"sentence\", now via `sentence_structure`); "
        "\"Report and Feature Article Writing\" (SS2 Second, now via `articles`); "
        "and \"Oral English: Public Speaking and Advanced Sound Work\" (SS2 Second, "
        "\"Sounds\"↔\"Sound\", now via `consonant_sounds`)."
    )
    lines.append(
        "- Section 5 (shared-entry): `essay_writing` moved into the \"…Descriptive "
        "and Narrative Essays\" group (now 3 slugs) and the old \"Summary Writing\" "
        "2-slug group dissolved, so groups went 6 → 5."
    )
    lines.append(
        "- Scope SS-reach evidence: the 5-slug list keeps its count but changes "
        "membership — `articles` now lands on an SS title, `essay_writing` no "
        "longer does (its best is now a JSS2 entry)."
    )
    lines.append(
        "- Net bucket counts: 2 confident (unchanged), 17 ambiguous (+1), "
        "4 unmatched (−1). `concord`, `inference`, `word_formation` and `spelling` "
        "stay unmatched — they share no title token in either spelling."
    )
    lines.append("")

    # --- Task 2: scope finding -------------------------------------------- #
    lines.append("## ENGLISH_TOPICS Intended Scope (Task 2)")
    lines.append("")
    lines.append(f"**Finding:** {scope_verdict}")
    lines.append("")
    lines.append("Evidence from `app/core/topics.py` and this run:")
    lines.append("")
    for e in scope_evidence:
        lines.append(f"- {e}")
    lines.append("")

    # --- Section 1: Confident (ascending score → most borderline at top) -- #
    lines.append("## 1. Confident Matches")
    lines.append("")
    lines.append("_Sorted by score ascending, so the weakest 'confident' calls sit at the top._")
    lines.append("")
    if confident:
        lines.append("| Slug | Best curriculum title | Class | Term | Score | Gap to 2nd |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for r in sorted(confident, key=lambda r: r["score"]):
            best = r["candidates"][0]
            lines.append(
                f"| `{r['slug']}` | {best['title']} | {best['level']} | "
                f"{best['term']} | {r['score']:.3f} | {r['gap']:.3f} |"
            )
    else:
        lines.append("_None._")
    lines.append("")

    # --- Section 2: Ambiguous (descending score → nearest-to-confident top) #
    lines.append("## 2. Ambiguous")
    lines.append("")
    lines.append(
        "_Sorted by best score descending. Multiple curriculum titles score "
        "close together, or the best score sits below the confident threshold._"
    )
    lines.append("")
    if ambiguous:
        for r in sorted(ambiguous, key=lambda r: r["score"], reverse=True):
            lines.append(
                f"- `{r['slug']}` — best {r['score']:.3f}, gap {r['gap']:.3f}:"
            )
            for c in r["candidates"][:AMBIGUOUS_SHOW]:
                lines.append(f"    - {fmt_candidate(c)}")
    else:
        lines.append("_None._")
    lines.append("")

    # --- Section 3: Unmatched (descending score → closest-to-floor at top) - #
    lines.append("## 3. Unmatched")
    lines.append("")
    lines.append(
        "_Sorted by best score descending, so near-misses (just under "
        "`MATCH_FLOOR`) are easiest to scan first. With the full JSS1-SS3 range in "
        "the pool, a slug here shares essentially no word with any curriculum "
        "title — for English that usually means the concept lives only inside "
        "subtopics (e.g. `concord`, `spelling`), never in a topic title._"
    )
    lines.append("")
    if unmatched:
        lines.append("| Slug | Closest curriculum title | Class | Term | Score |")
        lines.append("| --- | --- | --- | --- | --- |")
        for r in sorted(unmatched, key=lambda r: r["score"], reverse=True):
            best = r["candidates"][0]
            lines.append(
                f"| `{r['slug']}` | {best['title']} | {best['level']} | "
                f"{best['term']} | {r['score']:.3f} |"
            )
    else:
        lines.append("_None._")
    lines.append("")

    # --- Section 4: Curriculum topics with no allowlist slug -------------- #
    lines.append("## 4. Curriculum Topics With No Allowlist Slug")
    lines.append("")
    lines.append(
        "_JSS1-SS3 curriculum titles whose best-matching slug scores below "
        "`COVERAGE_FLOOR`. Sorted by score descending — the allowlist may be "
        "missing these topics. Closest near-misses appear first._"
    )
    lines.append("")
    if uncovered:
        lines.append("| Curriculum title | Class | Term | Closest slug | Score |")
        lines.append("| --- | --- | --- | --- | --- |")
        for r in sorted(uncovered, key=lambda r: r["score"], reverse=True):
            lines.append(
                f"| {r['title']} | {r['level']} | {r['term']} | "
                f"`{r['best_slug']}` | {r['score']:.3f} |"
            )
    else:
        lines.append("_None — every curriculum topic has at least one nearby slug._")
    lines.append("")

    # --- Section 5: Shared-entry candidates (Task 7a) --------------------- #
    lines.append("## 5. Shared-Entry Candidates")
    lines.append("")
    lines.append(
        "_Curriculum entries that are the single best match for MORE THAN ONE "
        "slug. Decide per group whether the entry legitimately owns several slugs "
        "or whether it's a false collision from a shared framing word (e.g. "
        "'Writing'). Sorted by number of contending slugs descending._"
    )
    lines.append("")
    if shared:
        for g in shared:
            slug_list = ", ".join(
                f"`{m['slug']}` ({m['score']:.3f})" for m in g["slugs"]
            )
            lines.append(
                f"- **{g['title']}** ({g['level']} {g['term']}) — "
                f"{len(g['slugs'])} slugs: {slug_list}"
            )
    else:
        lines.append("_None — no curriculum entry is the top match for two or more slugs._")
    lines.append("")

    # --- Section 6: Duplicate-title candidates (Task 7b) ------------------ #
    lines.append("## 6. Duplicate-Title Candidates")
    lines.append("")
    lines.append(
        "_Curriculum title strings that appear at more than one class-level/term "
        "position. A slug matching one of these is inherently ambiguous about "
        "which class level it grounds to. Detected from the curriculum alone, "
        "independent of the allowlist. Sorted by number of positions descending._"
    )
    lines.append("")
    if dupes:
        for d in dupes:
            pos = ", ".join(f"{lvl} {term}" for (lvl, term) in d["positions"])
            lines.append(f"- **{d['title']}** — {len(d['positions'])} positions: {pos}")
    else:
        lines.append(
            "_None — every curriculum title string is unique to a single "
            "class-level/term position._"
        )
    lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    slugs = load_allowlist_slugs()
    # Full JSS1-SS3 pool from the start — no JSS-only pre-pass.
    titles = load_titles(ALL_LEVELS)

    confident: list[dict] = []
    ambiguous: list[dict] = []
    unmatched: list[dict] = []

    for slug in slugs:
        candidates = score_slug(slug, titles)
        bucket, best, gap = bucket_slug(candidates)
        row = {"slug": slug, "candidates": candidates, "score": best, "gap": gap}
        if bucket == "confident":
            confident.append(row)
        elif bucket == "ambiguous":
            ambiguous.append(row)
        else:
            unmatched.append(row)

    matched_rows = confident + ambiguous  # everything that cleared MATCH_FLOOR
    uncovered = uncovered_titles(titles, slugs)
    shared = shared_entry_candidates(matched_rows)
    dupes = duplicate_titles(titles)
    scope_verdict, scope_evidence = analyze_scope(matched_rows)

    report = build_report(
        confident, ambiguous, unmatched, uncovered, shared, dupes,
        scope_verdict, scope_evidence, len(slugs), len(titles),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(
        f"{len(confident)} confident, {len(ambiguous)} ambiguous, "
        f"{len(unmatched)} unmatched, {len(uncovered)} curriculum topics with no slug, "
        f"{len(shared)} shared-entry group(s), {len(dupes)} duplicate title(s) "
        f"-> {REPORT_PATH.relative_to(REPO_ROOT)}"
    )


if __name__ == "__main__":
    main()
