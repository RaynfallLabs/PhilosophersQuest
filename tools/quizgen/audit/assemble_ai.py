"""Assemble the AI bank from `_gen_ai_*.json` outputs.

Reads every `_gen_ai_*.json` at repo root, validates each question against
the full AI gate suite, dedups within the new bank, strips agent metadata,
archives the legacy bank, and writes the new bank to
`data/questions/ai.json`.

Aggregator priority (when multiple sources have the same tier/pillar):
  1. Tier-complete files first (`_gen_ai_t1.json` through `t5.json`)
  2. Topic-supplement files for gaps (`_gen_ai_t<N>_p<P>.json`)
  3. Drop questions whose normalized stem matches one already accepted
     (intra-bank dedup).

Supports both wrapped (`{"questions": [...]}`) and raw-list source files —
the bulk-gen agents emitted both shapes.

Usage:
  py -m tools.quizgen.audit.assemble_ai [--dry-run]
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import build_bank_indices, validate_rewrite  # noqa: E402
from tools.quizgen.deterministic.answer_collision import _normalize_answer  # noqa: E402


def _normalize_stem(stem: str) -> str:
    """Same normalization the duplicate gate uses."""
    return _normalize_answer(stem)


def _extract_questions(data) -> list[dict]:
    """Accept either {"questions": [...]} or a raw [...] list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        qs = data.get("questions", [])
        if isinstance(qs, list):
            return qs
    return []


def load_sources() -> dict[str, list[dict]]:
    """Returns {filename: [questions]} for every _gen_ai_*.json."""
    sources: dict[str, list[dict]] = {}
    # Tier-complete files first, then topic-supplement files. Alphabetical
    # order within each group ensures stable priority during dedup.
    tier_files = sorted(REPO.glob("_gen_ai_t?.json"))
    topic_files = sorted(REPO.glob("_gen_ai_t?_p*.json"))
    # Exclude any `*_failures.json` debug dumps from the bulk-gen process.
    topic_files = [p for p in topic_files if "_failures" not in p.name]
    for path in tier_files + topic_files:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"  !! {path.name}: JSON parse error: {e}")
            continue
        qs = _extract_questions(data)
        if not qs:
            print(f"  -- {path.name}: empty")
            continue
        sources[path.name] = qs
        print(f"  loaded {path.name}: {len(qs)} questions")
    return sources


def assemble(dry_run: bool = False) -> dict:
    print("=== AI bank assembly ===")
    sources = load_sources()
    print()

    # Pool all questions in priority order, strip underscore-prefixed
    # agent metadata (_pillar, _strategy, _meta, etc.).
    all_questions: list[tuple[str, dict]] = []
    for name, qs in sources.items():
        for q in qs:
            if not isinstance(q, dict):
                continue
            stripped = {k: v for k, v in q.items() if not k.startswith("_")}
            all_questions.append((name, stripped))
    print(f"Pool: {len(all_questions)} questions across {len(sources)} files")

    # Intra-bank dedup: drop later-seen duplicates by normalized stem.
    seen_stems: set[str] = set()
    accepted: list[dict] = []
    dedup_drops: list[dict] = []
    for name, q in all_questions:
        stem_norm = _normalize_stem(q.get("question", ""))
        if not stem_norm:
            dedup_drops.append({"source": name, "reason": "empty stem", "q": q})
            continue
        if stem_norm in seen_stems:
            dedup_drops.append({
                "source": name,
                "reason": "duplicate stem",
                "stem": stem_norm[:80],
            })
            continue
        seen_stems.add(stem_norm)
        accepted.append(q)
    print(f"After intra-bank dedup: {len(accepted)} accepted, {len(dedup_drops)} dropped")

    # Validate every accepted question against the full AI gate suite.
    print()
    print("Validating against gates...")
    dup, ans = build_bank_indices(accepted)
    pass_count = 0
    fail_count = 0
    soft_warn_count = 0
    fail_records: list[dict] = []
    fail_by_gate: Counter = Counter()
    for i, q in enumerate(accepted):
        r = validate_rewrite(
            "ai", q, bank=accepted, dup_index=dup, answer_index=ans, replace_idx=i
        )
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
            if r["verdict"] == "SOFT_WARN":
                soft_warn_count += 1

    print(f"  Pass: {pass_count} (incl. {soft_warn_count} soft-warn)")
    print(f"  Fail: {fail_count}")
    if fail_by_gate:
        print("  By gate:")
        for gate, count in sorted(fail_by_gate.items(), key=lambda kv: -kv[1]):
            print(f"    {gate}: {count}")

    # Build the new bank from PASS-only questions.
    fail_indices = {fr["index_in_accepted"] for fr in fail_records}
    new_bank = [q for i, q in enumerate(accepted) if i not in fail_indices]

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
            "soft_warn": soft_warn_count,
            "final": len(new_bank),
            "by_tier": dict(by_tier),
            "fail_by_gate": dict(fail_by_gate),
            "dedup_drops": dedup_drops,
            "fail_records": fail_records,
        }

    # Archive existing legacy bank
    bank_path = REPO / "data" / "questions" / "ai.json"
    dropped_path = REPO / "data" / "questions" / "dropped" / "ai.json"
    if bank_path.exists():
        legacy = json.loads(bank_path.read_text(encoding="utf-8"))
        existing_dropped = []
        if dropped_path.exists():
            try:
                existing_dropped = json.loads(dropped_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing_dropped = []
        annotated = []
        for q in legacy:
            qcopy = dict(q)
            qcopy["_drop_reason"] = "v2_rebuild_2026_05_25_ai_from_scratch"
            annotated.append(qcopy)
        merged_dropped = list(existing_dropped) + annotated
        dropped_path.parent.mkdir(parents=True, exist_ok=True)
        dropped_path.write_text(
            json.dumps(merged_dropped, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Archived {len(legacy)} legacy questions to dropped/ai.json "
              f"(now {len(merged_dropped)} dropped total)")

    # Write new bank
    bank_path.write_text(
        json.dumps(new_bank, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote new bank: {bank_path} ({len(new_bank)} questions)")

    # Write assembly log
    log_path = REPO / "_ai_assembly_log.md"
    out: list[str] = []
    out.append("# AI bank assembly log")
    out.append("")
    out.append(f"- Pool: {len(all_questions)} questions across {len(sources)} source files")
    out.append(f"- After intra-bank dedup: {len(accepted)}")
    out.append(f"- After gate validation: {pass_count} pass ({soft_warn_count} soft-warn), {fail_count} fail")
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
        "soft_warn": soft_warn_count,
        "final": len(new_bank),
        "by_tier": dict(by_tier),
        "fail_by_gate": dict(fail_by_gate),
    }


def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    result = assemble(dry_run=dry)
    # Always exit 0 — partial failures are expected; the log shows what dropped.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
