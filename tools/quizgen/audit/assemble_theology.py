"""Assemble the theology bank from `_theology_gen/A*.json` outputs.

Reads every `A*.json` file from `_theology_gen/`, validates each question
against the full theology gate suite, dedups within the new bank, strips
agent metadata, archives the legacy bank, and writes the new bank to
`data/questions/theology.json`.

**EXPLICIT bank-path constants** (hand-written, NOT sed-copied — the
AI-bank-overwrite bug from the 2026-05-26 science rebuild taught us
this lesson; verify these constants before every run).

Supports both wrapped (`{"questions": [...]}`) and raw-list source files.

Usage:
  py -m tools.quizgen.audit.assemble_theology [--dry-run]
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


# === EXPLICIT theology constants — verify before run ===
SUBJECT_NAME = "theology"
BANK_PATH = REPO / "data" / "questions" / "theology.json"
DROPPED_PATH = REPO / "data" / "questions" / "dropped" / "theology.json"
ASSEMBLY_LOG_PATH = REPO / "_theology_assembly_log.md"
SOURCE_DIR = REPO / "_theology_gen"
# Match both A*.json (original batches) and R*.json (respawn batches)
# Excludes anything starting with underscore (build scripts, helpers)
SOURCE_GLOB_PATTERNS = ["A*.json", "R*.json"]
DROP_REASON = "v2_rebuild_2026_05_26_theology_from_scratch_story_led"


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
    """Returns {filename: [questions]} for every _theology_gen/A*.json."""
    sources: dict[str, list[dict]] = {}
    if not SOURCE_DIR.is_dir():
        print(f"  !! Source dir not found: {SOURCE_DIR}")
        return sources
    seen_paths: set = set()
    all_paths: list = []
    for pattern in SOURCE_GLOB_PATTERNS:
        for path in SOURCE_DIR.glob(pattern):
            if path in seen_paths:
                continue
            seen_paths.add(path)
            all_paths.append(path)
    for path in sorted(all_paths):
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
    # Sanity-check the explicit constants — print and bail if anything is wrong
    print(f"=== {SUBJECT_NAME} bank assembly ===")
    print(f"  bank path: {BANK_PATH}")
    print(f"  dropped path: {DROPPED_PATH}")
    print(f"  source dir: {SOURCE_DIR} / {SOURCE_GLOB_PATTERNS}")
    assert SUBJECT_NAME == "theology", "SUBJECT_NAME mismatch — refuse to run"
    assert BANK_PATH.name == "theology.json", f"BANK_PATH wrong: {BANK_PATH.name}"
    assert DROPPED_PATH.name == "theology.json", f"DROPPED_PATH wrong: {DROPPED_PATH.name}"

    sources = load_sources()
    print()

    all_questions: list[tuple[str, dict]] = []
    for name, qs in sources.items():
        for q in qs:
            if not isinstance(q, dict):
                continue
            stripped = {k: v for k, v in q.items() if not k.startswith("_")}
            all_questions.append((name, stripped))
    print(f"Pool: {len(all_questions)} questions across {len(sources)} files")

    seen_stems: set[str] = set()
    accepted: list[dict] = []
    dedup_drops: list[dict] = []
    for name, q in all_questions:
        stem_norm = _normalize_stem(q.get("question", ""))
        if not stem_norm:
            dedup_drops.append({"source": name, "reason": "empty stem"})
            continue
        if stem_norm in seen_stems:
            dedup_drops.append({"source": name, "reason": "duplicate stem", "stem": stem_norm[:80]})
            continue
        seen_stems.add(stem_norm)
        accepted.append(q)
    print(f"After intra-bank dedup: {len(accepted)} accepted, {len(dedup_drops)} dropped")

    print()
    print("Validating against gates...")
    dup, ans = build_bank_indices(accepted)
    pass_count = 0
    fail_count = 0
    soft_warn_count = 0
    fail_records: list[dict] = []
    fail_by_gate: Counter = Counter()
    for i, q in enumerate(accepted):
        r = validate_rewrite(SUBJECT_NAME, q, bank=accepted, dup_index=dup, answer_index=ans, replace_idx=i)
        if r["verdict"] == "FAIL":
            fail_count += 1
            for g, _reason in r["hard_fails"]:
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

    fail_indices = {fr["index_in_accepted"] for fr in fail_records}
    new_bank = [q for i, q in enumerate(accepted) if i not in fail_indices]

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
            "fail_records": fail_records,
        }

    # Archive existing legacy bank — use explicit constants
    if BANK_PATH.exists():
        legacy = json.loads(BANK_PATH.read_text(encoding="utf-8"))
        existing_dropped = []
        if DROPPED_PATH.exists():
            try:
                existing_dropped = json.loads(DROPPED_PATH.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing_dropped = []
        annotated = []
        for q in legacy:
            qcopy = dict(q)
            qcopy["_drop_reason"] = DROP_REASON
            annotated.append(qcopy)
        merged_dropped = list(existing_dropped) + annotated
        DROPPED_PATH.parent.mkdir(parents=True, exist_ok=True)
        DROPPED_PATH.write_text(
            json.dumps(merged_dropped, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"Archived {len(legacy)} legacy questions to {DROPPED_PATH.name} "
              f"(now {len(merged_dropped)} dropped total)")

    BANK_PATH.write_text(
        json.dumps(new_bank, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote new bank: {BANK_PATH} ({len(new_bank)} questions)")

    # Assembly log
    out: list[str] = []
    out.append(f"# {SUBJECT_NAME} bank assembly log")
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
    if fail_records:
        out.append(f"## Fail samples (first 20)")
        out.append("")
        for fr in fail_records[:20]:
            out.append(f"### #{fr['index_in_accepted']} T{fr['tier']}")
            out.append(f"- Stem: {fr['stem']}...")
            out.append(f"- Answer: {fr['answer']}")
            for g, r in fr['hard_fails']:
                out.append(f"  - HARD `{g}`: {r[:200]}")
            out.append("")
    if dedup_drops:
        out.append(f"## Dedup drops ({len(dedup_drops)})")
        out.append("")
    ASSEMBLY_LOG_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"Wrote log: {ASSEMBLY_LOG_PATH}")

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
    assemble(dry_run=dry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
