"""
match_math_slugs.py — READ-ONLY diagnostic.

Fuzzy-matches the Mathematics topic allowlist (app/core/topics.py) against the
FULL JSS1-SS3 range of the Mathematics curriculum (app/data/curriculum/
mathematics.json) and writes a markdown report to
scripts/output/math_slug_match_report.md.

This script only READS those two files. It never modifies topics.py, the
curriculum JSON, or anything under git. The only thing it writes is its own
markdown report inside scripts/output/.

Scoring method: TOKEN-BASED Jaccard similarity (word-set overlap), NOT character
ratio. Both slug and title are lowercased, stripped of punctuation, split on
whitespace/underscore, and reduced to a set of words with common stop words
("and", "of", "the", "in", ...) removed. Score = |A ∩ B| / |A ∪ B|.
difflib.SequenceMatcher (stdlib) survives ONLY as a tiebreaker: when two
candidates have an identical Jaccard score, the one with the higher character
ratio wins. This replaces the previous character-ratio-primary approach, which
let short titles with accidental letter overlap (e.g. "Simple Equations") beat
long titles containing the literal topic word (e.g. "Revision: Mensuration and
Geometry" for slug `mensuration`).

Scope note: earlier versions matched only JSS1-JSS3 and checked SS1-SS3 as a
secondary diagnostic. Project scope is now the full JSS1-SS3 range, so SS1-SS3
titles are part of the SINGLE primary matching pool here. Every slug is scored
against all six class levels at once, and the SS-only diagnostic section has
been repurposed into a class-level breakdown (see Section 5).

No new dependency is introduced (rapidfuzz is not in requirements.txt).

Run from the repo root:
    python scripts/match_math_slugs.py
"""

from __future__ import annotations

import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path

# --------------------------------------------------------------------------- #
# Tunable thresholds — change these to re-bucket without touching the logic.
#
# NOTE: these were re-tuned DOWN from the old character-ratio version. Jaccard
# word-overlap runs on a lower numeric scale than SequenceMatcher's char ratio:
# a slug like `trigonometry` (one word) matching a descriptive title like
# "Trigonometry (1): Tangent of an Angle" (four words) shares 1 of 4 union
# tokens = 0.25, even though the match is genuine. A perfect single-word match
# (`probability` -> "Probability") is 1.0, and a solid two-word overlap
# (`commercial_arithmetic` -> "Household and Commercial Arithmetic") is ~0.67.
# The old defaults (0.72 / 0.08 / 0.45 / 0.45) were calibrated for the char
# scale and would classify almost everything as unmatched here.
# --------------------------------------------------------------------------- #
# A slug's best curriculum match must score at least this to be a CONFIDENT match.
# 0.34 ≈ "shares at least a third of the combined word set" — on the Jaccard
# scale that means a strong, mostly-overlapping match rather than one stray word.
CONFIDENT_THRESHOLD = 0.34
# The best match must beat the second-best by at least this much; otherwise the
# slug is AMBIGUOUS (two or more titles are too close to call). One extra shared
# token typically shifts Jaccard by ~0.1, so 0.10 is roughly "one clear token
# of separation".
AMBIGUOUS_GAP = 0.10
# Below this similarity, a slug is UNMATCHED (essentially no shared meaningful
# word). 0.15 ≈ one shared token against a ~6-word title; a slug that shares
# zero tokens scores 0.0 and is cleanly unmatched.
MATCH_FLOOR = 0.15
# Reverse pass: a curriculum title whose best-matching slug scores below this is
# flagged as having no allowlist slug at all. Kept equal to MATCH_FLOOR.
COVERAGE_FLOOR = 0.15
# How many close runner-up candidates to display for AMBIGUOUS slugs.
AMBIGUOUS_SHOW = 3

# All class levels now form the SINGLE primary matching pool (full JSS1-SS3
# project scope). SS_LEVELS is retained only to label which matches are
# senior-secondary in the class-level breakdown / scope evidence.
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
CURRICULUM_PATH = REPO_ROOT / "app" / "data" / "curriculum" / "mathematics.json"
OUTPUT_DIR = REPO_ROOT / "scripts" / "output"
REPORT_PATH = OUTPUT_DIR / "math_slug_match_report.md"


# --------------------------------------------------------------------------- #
# Input loading
# --------------------------------------------------------------------------- #
def load_allowlist_slugs() -> list[str]:
    """Read the Mathematics slug allowlist from app/core/topics.py.

    Prefers importing get_topics(); falls back to regex-parsing MATHS_TOPICS so
    the script still works even if the package can't be imported.
    """
    sys.path.insert(0, str(REPO_ROOT))
    try:
        from app.core.topics import get_topics  # type: ignore

        slugs = get_topics("Mathematics")
        if slugs:
            return list(slugs)
    except Exception as exc:  # pragma: no cover - defensive fallback
        print(f"[warn] import of app.core.topics failed ({exc}); parsing file instead")

    # Fallback: parse the MATHS_TOPICS = [...] literal directly.
    topics_src = TOPICS_PATH.read_text(encoding="utf-8")
    match = re.search(r"MATHS_TOPICS\s*[:=].*?\[(.*?)\]", topics_src, re.DOTALL)
    if not match:
        raise RuntimeError("Could not locate MATHS_TOPICS in app/core/topics.py")
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
def tokenize(text: str) -> set[str]:
    """Lowercase, underscores/punctuation -> spaces, split to a stop-word-free set."""
    text = text.lower().replace("_", " ")
    text = re.sub(r"[^a-z0-9\s]", " ", text)  # drop punctuation / symbols
    return {tok for tok in text.split() if tok and tok not in STOP_WORDS}


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
# Task 3: class-level breakdown (repurposed from the old SS-only diagnostic).
#
# I REPURPOSED the former "Unmatched vs JSS, Checked Against SS" section rather
# than deleting it. Now that SS1-SS3 is in the main pool, that JSS-vs-SS check
# is structurally redundant (the SS title just competes directly for best
# match). I chose an AGGREGATE class-level distribution (counts per level)
# rather than a per-match level list, because Sections 1 & 2 already show each
# match's Class column — a distribution summary adds genuinely new information
# (how matched coverage spreads across JSS1-SS3) instead of duplicating them.
# --------------------------------------------------------------------------- #
def class_level_breakdown(confident: list[dict], ambiguous: list[dict]) -> list[dict]:
    """Count confident/ambiguous matches by the class level of their best candidate."""
    counts = {lvl: {"confident": 0, "ambiguous": 0} for lvl in ALL_LEVELS}
    for r in confident:
        counts[r["candidates"][0]["level"]]["confident"] += 1
    for r in ambiguous:
        counts[r["candidates"][0]["level"]]["ambiguous"] += 1
    return [
        {"level": lvl,
         "confident": counts[lvl]["confident"],
         "ambiguous": counts[lvl]["ambiguous"],
         "total": counts[lvl]["confident"] + counts[lvl]["ambiguous"]}
        for lvl in ALL_LEVELS
    ]


# --------------------------------------------------------------------------- #
# Task 2: describe the intended scope of MATHS_TOPICS from the file's contents.
# --------------------------------------------------------------------------- #
def analyze_scope(confident: list[dict], ambiguous: list[dict]) -> tuple[str, list[str]]:
    """Return (verdict, evidence_lines) about MATHS_TOPICS's intended scope.

    Verdict is derived from the file's actual contents (inspected separately)
    plus this run's data: how many slugs' best match lands at an SS level.
    """
    ss_matched = [
        r["slug"] for r in (confident + ambiguous)
        if r["candidates"][0]["level"] in SS_LEVELS
    ]
    verdict = (
        "FULL JSS1-SS3 (secondary-wide) list that is NOT scoped by class level "
        "anywhere in code - NOT a JSS-only list."
    )
    evidence = [
        "`MATHS_TOPICS` has no docstring or comment stating its scope, and its "
        "name carries no `JSS`/`SS` qualifier (it mirrors `ENGLISH_TOPICS`).",
        "`get_topics()` / `invalid_topics()` return and validate against the "
        "whole flat list; there is no class-level filtering anywhere in topics.py.",
        "The list contains topics that are unambiguously SS-level in the "
        "curriculum (e.g. `surds`, `logarithms`, `matrices`, `coordinate_geometry`, "
        "`sets`), plus `vectors` and `logic`, which appear in neither JSS nor SS.",
        f"This run (full JSS1-SS3 pool): {len(ss_matched)} slug(s) have their best "
        f"match at an SS1-SS3 level "
        f"({', '.join('`' + s + '`' for s in ss_matched) if ss_matched else 'none'}), "
        "confirming the allowlist reaches beyond JSS content.",
        "No docstring explicitly *declares* the intended scope, so this is "
        "inferred from composition + absence of scoping code, not a stated "
        "contract. It is not, however, genuinely ambiguous: a JSS-only list "
        "would not include strictly-SS topics.",
    ]
    return verdict, evidence


# --------------------------------------------------------------------------- #
# Report rendering
# --------------------------------------------------------------------------- #
def fmt_candidate(c: dict) -> str:
    return f"{c['title']} ({c['level']} {c['term']}) — {c['score']:.3f}"


def build_report(
    confident: list[dict], ambiguous: list[dict], unmatched: list[dict],
    uncovered: list[dict], breakdown: list[dict],
    scope_verdict: str, scope_evidence: list[str],
    n_slugs: int, n_titles: int,
) -> str:
    lines: list[str] = []
    lines.append("# Mathematics Slug ↔ Curriculum Match Report")
    lines.append("")
    lines.append(
        "**Scoring: token-based Jaccard word-set overlap** (intersection over "
        "union of stop-word-filtered words), with `difflib.SequenceMatcher` used "
        "only as a tiebreaker for equal Jaccard scores. **Matching now covers the "
        "full JSS1-SS3 range** (all six class levels are in one primary pool), "
        "not JSS1-JSS3. This **supersedes both prior versions** of this report — "
        "the original character-ratio version and the JSS1-JSS3-only token "
        "version; this full-scope token-based one is authoritative. Read-only "
        "diagnostic: no source files were modified."
    )
    lines.append("")
    lines.append("**Thresholds used** (re-tuned for the Jaccard scale — see script comments)")
    lines.append("")
    lines.append(f"- `CONFIDENT_THRESHOLD` = {CONFIDENT_THRESHOLD}")
    lines.append(f"- `AMBIGUOUS_GAP` = {AMBIGUOUS_GAP}")
    lines.append(f"- `MATCH_FLOOR` = {MATCH_FLOOR}")
    lines.append(f"- `COVERAGE_FLOOR` = {COVERAGE_FLOOR}")
    lines.append("")
    lines.append(
        f"**Scope of matching:** {n_slugs} allowlist slugs vs {n_titles} "
        "curriculum topics across the full JSS1-SS3 range (JSS1, JSS2, JSS3, "
        "SS1, SS2, SS3 — all in one primary pass)."
    )
    lines.append("")
    lines.append(
        f"**Summary:** {len(confident)} confident · {len(ambiguous)} ambiguous · "
        f"{len(unmatched)} unmatched · {len(uncovered)} curriculum topics with no slug."
    )
    lines.append("")

    # --- Task 2: scope finding -------------------------------------------- #
    lines.append("## MATHS_TOPICS Intended Scope (Task 2)")
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
        "`MATCH_FLOOR`) are easiest to scan first. With SS1-SS3 now in the main "
        "pool, a slug here is genuinely absent from the curriculum titles, not "
        "merely out of scope._"
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

    # --- Section 5: Class-level breakdown (repurposed) -------------------- #
    lines.append("## 5. Class-Level Breakdown of Matches")
    lines.append("")
    lines.append(
        "_Where the confident and ambiguous matches land across the full "
        "JSS1-SS3 range. (Replaces the old 'Unmatched vs JSS, Checked Against "
        "SS' diagnostic, which is redundant now that SS is in the main pool.) "
        "Level = the class level of each slug's single best-matching title._"
    )
    lines.append("")
    lines.append("| Class level | Confident | Ambiguous | Total matched |")
    lines.append("| --- | --- | --- | --- |")
    for row in breakdown:
        lines.append(
            f"| {row['level']} | {row['confident']} | {row['ambiguous']} | "
            f"{row['total']} |"
        )
    total_conf = sum(r["confident"] for r in breakdown)
    total_amb = sum(r["ambiguous"] for r in breakdown)
    lines.append(
        f"| **All levels** | **{total_conf}** | **{total_amb}** | "
        f"**{total_conf + total_amb}** |"
    )
    lines.append("")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    slugs = load_allowlist_slugs()
    # Task 1: single primary pass over the FULL JSS1-SS3 pool.
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

    uncovered = uncovered_titles(titles, slugs)
    breakdown = class_level_breakdown(confident, ambiguous)
    scope_verdict, scope_evidence = analyze_scope(confident, ambiguous)

    report = build_report(
        confident, ambiguous, unmatched, uncovered, breakdown,
        scope_verdict, scope_evidence, len(slugs), len(titles),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(
        f"{len(confident)} confident, {len(ambiguous)} ambiguous, "
        f"{len(unmatched)} unmatched, {len(uncovered)} curriculum topics with no slug "
        f"-> {REPORT_PATH.relative_to(REPO_ROOT)}"
    )
    print(f"[Task 2] MATHS_TOPICS scope: {scope_verdict}")


if __name__ == "__main__":
    main()
