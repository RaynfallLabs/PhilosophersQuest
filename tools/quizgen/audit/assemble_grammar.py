"""Assemble the grammar bank from `_gen_grammar_t*.json` outputs.

Reads every `_gen_grammar_*.json` at repo root, validates each question
against the full grammar gate suite, dedups within the new bank,
strips agent metadata, archives the legacy bank, and writes the new
bank to `data/questions/grammar.json`.

Aggregator priority (when multiple sources have the same tier/pillar):
  1. Tier-complete files first (`_gen_grammar_t1.json` through `t5.json`)
  2. Topic-supplement files for gaps (`_gen_grammar_t<N>_p<P>.json`)
  3. Drop questions whose normalized stem or answer matches one already
     accepted (intra-bank dedup)

Usage:
  py -m tools.quizgen.audit.assemble_grammar [--dry-run]
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402
from tools.quizgen.deterministic.answer_collision import _normalize_answer  # noqa: E402


def _normalize_stem(stem: str) -> str:
    """Same normalization the duplicate gate uses."""
    return _normalize_answer(stem)


# Phrasings the user has explicitly rejected during exemplar review.
# Drop any question containing these in stem/answer/choices/context.
USER_REJECTED_PHRASES = [
    "raced past the barn",       # garden-path that feels ungrammatical to native speakers;
                                  # user prefers "racing past the barn fell" with participle.
    "hungry pat",                 # broken vocative-comma example — "hungry" isn't transitive,
                                  # so the cannibalism reading doesn't actually parse.
]


def _contains_rejected_phrase(q: dict) -> str | None:
    """Returns the offending phrase if found, else None."""
    text = (
        q.get("question", "") + " " +
        q.get("answer", "") + " " +
        " ".join(q.get("choices", []) or []) + " " +
        q.get("context", "")
    ).lower()
    for phrase in USER_REJECTED_PHRASES:
        if phrase.lower() in text:
            return phrase
    return None


def load_sources() -> dict[str, list[dict]]:
    """Returns {filename: [questions]} for every _gen_grammar_*.json."""
    sources: dict[str, list[dict]] = {}
    # Tier-complete files first, then topic-supplement files (alphabetical
    # within each group preserves insertion order during dedup).
    tier_files = sorted(REPO.glob("_gen_grammar_t?.json"))
    topic_files = sorted(REPO.glob("_gen_grammar_t?_p*.json"))
    for path in tier_files + topic_files:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  !! {path.name}: JSON parse error: {e}")
            continue
        qs = data.get("questions", [])
        if not qs:
            print(f"  -- {path.name}: empty")
            continue
        sources[path.name] = qs
        print(f"  loaded {path.name}: {len(qs)} questions")
    return sources


def assemble(dry_run: bool = False) -> dict:
    print("=== Grammar bank assembly ===")
    sources = load_sources()
    print()

    # Pool all questions in priority order, drop _pillar/_strategy metadata.
    all_questions: list[tuple[str, dict]] = []
    for name, qs in sources.items():
        for q in qs:
            stripped = {k: v for k, v in q.items() if not k.startswith("_")}
            all_questions.append((name, stripped))
    print(f"Pool: {len(all_questions)} questions across {len(sources)} files")

    # First pass: drop user-rejected phrasings (specific examples the user
    # called out as ungrammatical / not-actually-parsing during review).
    after_rejected = []
    rejected_drops: list[dict] = []
    for name, q in all_questions:
        rej = _contains_rejected_phrase(q)
        if rej:
            rejected_drops.append({
                "source": name,
                "phrase": rej,
                "stem": q.get("question", "")[:80],
            })
            continue
        after_rejected.append((name, q))
    if rejected_drops:
        print(f"User-rejected phrasing drops: {len(rejected_drops)}")
        for d in rejected_drops:
            print(f"  - [{d['source']}] phrase={d['phrase']!r}: {d['stem']!r}")

    # Intra-bank dedup: drop later-seen duplicates by normalized stem.
    seen_stems: set[str] = set()
    accepted: list[dict] = []
    dedup_drops: list[dict] = []
    for name, q in after_rejected:
        stem_norm = _normalize_stem(q.get("question", ""))
        if not stem_norm:
            dedup_drops.append({"source": name, "reason": "empty stem", "q": q})
            continue
        if stem_norm in seen_stems:
            dedup_drops.append({"source": name, "reason": "duplicate stem", "stem": stem_norm[:80]})
            continue
        seen_stems.add(stem_norm)
        accepted.append(q)
    print(f"After intra-bank dedup: {len(accepted)} accepted, {len(dedup_drops)} dropped")

    # Validate every accepted question against the full grammar gate suite.
    print()
    print("Validating against gates...")
    dup, ans = build_bank_indices(accepted)
    pass_count = 0
    fail_count = 0
    fail_records: list[dict] = []
    fail_by_gate: Counter = Counter()
    for i, q in enumerate(accepted):
        r = validate_rewrite("grammar", q, bank=accepted, dup_index=dup, answer_index=ans, replace_idx=i)
        if r["verdict"] == "FAIL":
            fail_count += 1
            for g, reason in r["hard_fails"]:
                fail_by_gate[g] += 1
            fail_records.append({
                "index_in_accepted": i,
                "stem": q.get("question", "")[:100],
                "answer": q.get("answer", "")[:80],
                "tier": q.get("tier"),
                "hard_fails": r["hard_fails"][:3],
            })
        else:
            pass_count += 1

    print(f"  Pass: {pass_count}")
    print(f"  Fail: {fail_count}")
    if fail_by_gate:
        print(f"  By gate: {dict(fail_by_gate)}")

    # Build the new bank from PASS-only questions.
    pass_indices = {fr["index_in_accepted"] for fr in fail_records}
    new_bank = [q for i, q in enumerate(accepted) if i not in pass_indices]

    # Tier distribution
    by_tier = Counter(q.get("tier") for q in new_bank)
    print()
    print("Final bank tier distribution:")
    for t in (1, 2, 3, 4, 5):
        print(f"  T{t}: {by_tier.get(t, 0)}")
    print(f"  Total: {len(new_bank)}")

    if dry_run:
        print()
        print("(dry-run — no files written)")
        return {
            "pool": len(all_questions),
            "after_dedup": len(accepted),
            "validated_pass": pass_count,
            "validated_fail": fail_count,
            "final": len(new_bank),
            "by_tier": dict(by_tier),
            "fail_by_gate": dict(fail_by_gate),
            "dedup_drops": dedup_drops,
            "fail_records": fail_records,
        }

    # Archive existing legacy bank
    bank_path = REPO / "data" / "questions" / "grammar.json"
    dropped_path = REPO / "data" / "questions" / "dropped" / "grammar.json"
    if bank_path.exists():
        legacy = json.loads(bank_path.read_text(encoding="utf-8"))
        existing_dropped = []
        if dropped_path.exists():
            try:
                existing_dropped = json.loads(dropped_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing_dropped = []
        # Annotate each legacy entry with drop reason
        annotated = []
        for q in legacy:
            qcopy = dict(q)
            qcopy["_drop_reason"] = "v2_rebuild_2026_05_25_grammar_from_scratch"
            annotated.append(qcopy)
        merged_dropped = list(existing_dropped) + annotated
        dropped_path.write_text(
            json.dumps(merged_dropped, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Archived {len(legacy)} legacy questions to dropped/grammar.json "
              f"(now {len(merged_dropped)} dropped total)")

    # Write new bank
    bank_path.write_text(
        json.dumps(new_bank, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote new bank: {bank_path} ({len(new_bank)} questions)")

    # Write assembly log
    log_path = REPO / "_grammar_assembly_log.md"
    out: list[str] = []
    out.append("# Grammar bank assembly log")
    out.append("")
    out.append(f"- Pool: {len(all_questions)} questions across {len(sources)} source files")
    out.append(f"- After intra-bank dedup: {len(accepted)}")
    out.append(f"- After gate validation: {pass_count} pass, {fail_count} fail")
    out.append(f"- Final bank size: **{len(new_bank)}**")
    out.append("")
    out.append("## Sources")
    out.append("")
    for name, qs in sources.items():
        out.append(f"- `{name}` — {len(qs)} questions")
    out.append("")
    out.append("## Tier distribution")
    out.append("")
    for t in (1, 2, 3, 4, 5):
        out.append(f"- T{t}: {by_tier.get(t, 0)}")
    out.append("")
    if fail_by_gate:
        out.append("## Gate failures (dropped)")
        out.append("")
        for gate, count in sorted(fail_by_gate.items(), key=lambda kv: -kv[1]):
            out.append(f"- `{gate}`: {count}")
        out.append("")
    if dedup_drops:
        out.append(f"## Dedup drops ({len(dedup_drops)})")
        out.append("")
        out.append("Questions dropped because their normalized stem matched an")
        out.append("earlier-accepted question. Tier-complete files take priority.")
        out.append("")
    log_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote log: {log_path}")

    return {
        "pool": len(all_questions),
        "after_dedup": len(accepted),
        "validated_pass": pass_count,
        "validated_fail": fail_count,
        "final": len(new_bank),
        "by_tier": dict(by_tier),
        "fail_by_gate": dict(fail_by_gate),
    }


def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    result = assemble(dry_run=dry)
    return 0 if result["validated_fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
