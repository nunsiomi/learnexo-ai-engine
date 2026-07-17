"""
Stage 2 curriculum-grounding evaluation — main runner.

Runs the GROUNDED condition (the real LearningPathService, prompt unchanged) and
the UNGROUNDED baseline (same model/temperature/parser, grounding removed) over
the test profiles, validates every returned topic against both official
vocabularies, and writes:

  evaluation/results/per_topic.csv   — one row per returned topic
  evaluation/results/summary.csv     — aggregated rates per condition

...and prints a summary table to the console.

Usage (from repo root):
  python evaluation/run_evaluation.py            # full run, 5 repeats/profile
  python evaluation/run_evaluation.py --dry-run  # 1 profile x 1 repeat (wiring check)
  python evaluation/run_evaluation.py --repeats 3

Requires GROQ_API_KEY in .env (loaded via app.core.config).
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from pathlib import Path

# Make the repo root importable when run as a plain script.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.learning_path_service import LearningPathService  # noqa: E402
from evaluation.matching import build_references, evaluate_topic  # noqa: E402
from evaluation.profiles import PROFILES, SUBJECT, humanize_slug  # noqa: E402
from evaluation.ungrounded import UngroundedLearningPathChain  # noqa: E402

# Condition order used everywhere (CSV, summary, console table):
#   grounded            — real LearningPathService, slug inputs, full grounding
#   ungrounded          — grounding removed, slug inputs (clean single-variable)
#   ungrounded_readable — grounding removed, human-readable inputs (no slug priming)
CONDITIONS = ["grounded", "ungrounded", "ungrounded_readable"]

RESULTS_DIR = Path(__file__).resolve().parent / "results"
PER_TOPIC_CSV = RESULTS_DIR / "per_topic.csv"
SUMMARY_CSV = RESULTS_DIR / "summary.csv"

DEFAULT_REPEATS = 5
INTER_CALL_DELAY_S = 1.0  # gentle pacing to avoid Groq rate limits
MAX_ATTEMPTS = 4          # 1 try + 3 retries on transient API errors
RETRY_BACKOFF_S = 3.0     # backoff base: 3s, 6s, 12s

PER_TOPIC_FIELDS = [
    "run_id", "condition", "profile_id", "class_level", "term", "learning_style",
    "returned_rank", "returned_topic",
    "slug_match_type", "slug_matched_value", "slug_similarity",
    "curr_match_type", "curr_matched_value", "curr_similarity",
    "is_hallucinated",
]


def _one_call(condition, service, profile, run_id, slug_ref, curriculum_ref):
    """Run a single LLM call and return (rows, failed: bool)."""
    # The ungrounded_readable arm receives human-readable topic names so the
    # baseline isn't primed by slug-formatted inputs.
    if condition == "ungrounded_readable":
        weak_topics = [humanize_slug(t) for t in profile["weak_topics"]]
        strong_topics = [humanize_slug(t) for t in profile["strong_topics"]]
    else:
        weak_topics = profile["weak_topics"]
        strong_topics = profile["strong_topics"]

    # Retry transient connection/timeout errors with exponential backoff so a
    # short Groq/network blip doesn't wipe out the rest of the run.
    last_exc = None
    result = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = service.generate(
                learning_style=profile["learning_style"],
                subject=SUBJECT,
                class_level=profile["class_level"],
                weak_topics=weak_topics,
                strong_topics=strong_topics,
                term=profile["term"],
            )
            break
        except Exception as exc:  # LLM error, JSON parse failure, etc.
            last_exc = exc
            if attempt < MAX_ATTEMPTS:
                backoff = RETRY_BACKOFF_S * (2 ** (attempt - 1))
                print(f"  [retry {attempt}/{MAX_ATTEMPTS - 1}] {run_id}: "
                      f"{type(exc).__name__} — waiting {backoff}s")
                time.sleep(backoff)

    if result is None:
        print(f"  [FAIL] {run_id} ({condition}): "
              f"{type(last_exc).__name__}: {last_exc}")
        return [], True

    rows = []
    for rank, topic in enumerate(result.get("recommended_order", []), start=1):
        topic = str(topic)
        verdict = evaluate_topic(topic, slug_ref, curriculum_ref)
        rows.append({
            "run_id": run_id,
            "condition": condition,
            "profile_id": profile["profile_id"],
            "class_level": profile["class_level"],
            "term": profile["term"],
            "learning_style": profile["learning_style"],
            "returned_rank": rank,
            "returned_topic": topic,
            "slug_match_type": verdict.slug.match_type,
            "slug_matched_value": verdict.slug.matched_value,
            "slug_similarity": verdict.slug.similarity,
            "curr_match_type": verdict.curriculum.match_type,
            "curr_matched_value": verdict.curriculum.matched_value,
            "curr_similarity": verdict.curriculum.similarity,
            "is_hallucinated": verdict.is_hallucinated,
        })
    return rows, False


def run(repeats: int, profiles: list[dict], model: str | None = None) -> list[dict]:
    if model:
        print(f"Using model override: {model}")
    grounded = LearningPathService(model=model)
    ungrounded = UngroundedLearningPathChain(model=model)
    services = {
        "grounded": grounded,
        "ungrounded": ungrounded,
        "ungrounded_readable": ungrounded,  # same chain, readable inputs (see _one_call)
    }
    conditions = [(name, services[name]) for name in CONDITIONS]

    all_rows: list[dict] = []
    failures: dict[str, int] = {c: 0 for c in CONDITIONS}
    calls: dict[str, int] = {c: 0 for c in CONDITIONS}

    total = len(profiles) * repeats * len(conditions)
    done = 0
    for profile in profiles:
        slug_ref, curriculum_ref = build_references(
            SUBJECT, profile["class_level"], profile["term"]
        )
        for rep in range(1, repeats + 1):
            for condition, service in conditions:
                run_id = f"{profile['profile_id']}__r{rep}__{condition}"
                done += 1
                print(f"[{done}/{total}] {run_id}")
                rows, failed = _one_call(
                    condition, service, profile, run_id, slug_ref, curriculum_ref
                )
                calls[condition] += 1
                if failed:
                    failures[condition] += 1
                all_rows.extend(rows)
                time.sleep(INTER_CALL_DELAY_S)

    _write_per_topic(all_rows)
    summary = _summarize(all_rows, calls, failures)
    _write_summary(summary)
    _print_table(summary)
    return summary


def _write_per_topic(rows: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with PER_TOPIC_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PER_TOPIC_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nWrote {len(rows)} topic rows -> {PER_TOPIC_CSV}")


def _pct(n: int, total: int) -> float:
    return round(100.0 * n / total, 1) if total else 0.0


def _summarize(rows, calls, failures) -> list[dict]:
    summary = []
    for condition in CONDITIONS:
        crows = [r for r in rows if r["condition"] == condition]
        total = len(crows)
        slug = {k: sum(1 for r in crows if r["slug_match_type"] == k)
                for k in ("exact", "borderline", "none")}
        curr = {k: sum(1 for r in crows if r["curr_match_type"] == k)
                for k in ("exact", "borderline", "none")}
        halluc = sum(1 for r in crows if r["is_hallucinated"])
        n_calls = calls[condition]
        summary.append({
            "condition": condition,
            "n_calls": n_calls,
            "n_failures": failures[condition],
            "total_topics": total,
            "slug_exact_%": _pct(slug["exact"], total),
            "slug_borderline_%": _pct(slug["borderline"], total),
            "slug_none_%": _pct(slug["none"], total),
            "curr_exact_%": _pct(curr["exact"], total),
            "curr_borderline_%": _pct(curr["borderline"], total),
            "curr_none_%": _pct(curr["none"], total),
            "hallucination_rate": _pct(halluc, total),
            "avg_topics_per_call": round(total / n_calls, 2) if n_calls else 0.0,
        })
    return summary


def _write_summary(summary: list[dict]) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with SUMMARY_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        writer.writeheader()
        writer.writerows(summary)
    print(f"Wrote summary -> {SUMMARY_CSV}")


def _print_table(summary: list[dict]) -> None:
    print("\n" + "=" * 72)
    print("STAGE 2 GROUNDING EVALUATION - SUMMARY")
    print("=" * 72)
    metrics = list(summary[0].keys())[1:]  # everything except "condition"
    label_w = max(len(m) for m in metrics)
    header = f"{'metric':<{label_w}}  " + "  ".join(f"{s['condition']:>12}" for s in summary)
    print(header)
    print("-" * len(header))
    for m in metrics:
        line = f"{m:<{label_w}}  " + "  ".join(f"{str(s[m]):>12}" for s in summary)
        print(line)
    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser(description="Stage 2 grounding evaluation")
    parser.add_argument("--dry-run", action="store_true",
                        help="1 profile x 1 repeat — quick wiring check")
    parser.add_argument("--repeats", type=int, default=DEFAULT_REPEATS,
                        help=f"repeats per profile per condition (default {DEFAULT_REPEATS})")
    parser.add_argument("--model", type=str, default=None,
                        help="Override the Groq model for all arms (e.g. llama-3.1-8b-instant). "
                             "Default: the production model from config (llama-3.3-70b-versatile).")
    args = parser.parse_args()

    if args.dry_run:
        print("DRY RUN: 1 profile x 1 repeat")
        run(repeats=1, profiles=PROFILES[:1], model=args.model)
    else:
        run(repeats=args.repeats, profiles=PROFILES, model=args.model)


if __name__ == "__main__":
    main()
