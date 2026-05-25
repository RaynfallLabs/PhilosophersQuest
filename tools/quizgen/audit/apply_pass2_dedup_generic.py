"""Generic Pass-2 dedup applier — works for any subject.

Reads dedup shards in one of two patterns:
  Pattern A (single file):     `_dedup_<subject>.json`
  Pattern B (sharded by size): `_dedup_<subject>_shard_A.json`,
                                `_dedup_<subject>_shard_B.json`,
                                `_dedup_<subject>_shard_C.json`

For each rewrite:
  1. Look up bank target by _target_index (preferred) or match_key.
  2. Build proposed new dict at agent's tier; auto-promote on length fail
     up to T5.
  3. Run full gate suite via validate_rewrite.
  4. Apply on PASS / SOFT_WARN. Rebuild answer-collision index after each
     apply so within-batch rewrites don't silently collide.

Outputs (per subject):
  - data/questions/<subject>.json (mutated in place)
  - _pass2_<subject>_dedup_log.md
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.quizgen.scratch._apply_pass1_rewrites import (  # noqa: E402
    TIER_CAPS,
    _build_new_q,
    _find_bank_idx,
    _normalize_rewrite,
    _starting_tier,
)
from tools.quizgen.audit.validate import (  # noqa: E402
    build_bank_indices,
    validate_rewrite,
)


def _load_shards(subject: str) -> tuple[list[dict], list[dict], list[dict], dict]:
    """Load shards for a subject. Supports both single-file and shard-A/B/C patterns."""
    rewrites: list[dict] = []
    flags: list[dict] = []
    kept_canonicals: list[dict] = []
    summary: dict = {}
    paths_to_try = [
        REPO / f"_dedup_{subject}.json",
        REPO / f"_dedup_{subject}_shard_A.json",
        REPO / f"_dedup_{subject}_shard_B.json",
        REPO / f"_dedup_{subject}_shard_C.json",
    ]
    for path in paths_to_try:
        if not path.exists():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        rewrites.extend(data.get("rewrites", []))
        flags.extend(data.get("flags", []))
        kept_canonicals.extend(data.get("kept_canonicals", []))
        summary[path.name] = data.get("summary", {})
        print(
            f"  loaded {path.name}: "
            f"{len(data.get('rewrites', []))} rewrites, "
            f"{len(data.get('flags', []))} flags, "
            f"{len(data.get('kept_canonicals', []))} canonicals"
        )
    return rewrites, flags, kept_canonicals, summary


def apply_subject(subject: str) -> dict:
    print(f"=== Pass-2 dedup apply: {subject} ===")
    rewrites, flags, canonicals, shard_summary = _load_shards(subject)
    if not rewrites and not flags:
        print(f"  ! no dedup files found for {subject} — skipping")
        return {"subject": subject, "missing": True}
    bank_path = REPO / "data" / "questions" / f"{subject}.json"
    bank = json.loads(bank_path.read_text(encoding="utf-8"))
    dup_index, answer_index = build_bank_indices(bank)

    applied: list[dict] = []
    rejected: list[dict] = []
    not_found: list[dict] = []

    for rw in rewrites:
        norm = _normalize_rewrite(rw)
        match_key = norm["match_key"]
        target_idx = rw.get("_target_index")
        if isinstance(target_idx, str):
            try:
                target_idx = int(target_idx)
            except ValueError:
                target_idx = None
        i = _find_bank_idx(bank, match_key, target_index=target_idx)
        if i is None:
            not_found.append({**rw, "_reason": f"match_key not in bank: {match_key[:60]!r}"})
            continue
        original = dict(bank[i])

        if not norm["new_question_text"] or not norm["new_answer"] or not norm["new_choices"]:
            not_found.append({**rw, "_reason": "rewrite missing required fields"})
            continue

        starting_tier = _starting_tier(norm, original)
        best_q: dict | None = None
        best_tier: int = starting_tier
        last_result: dict | None = None
        for trial_tier in range(max(1, starting_tier), 6):
            new_q = _build_new_q(norm, trial_tier)
            total = len(new_q["question"]) + sum(len(c) for c in new_q["choices"])
            if total > TIER_CAPS[5]:
                last_result = {
                    "verdict": "FAIL",
                    "hard_fails": [("length_total", f"{total} > {TIER_CAPS[5]}")],
                    "soft_warns": [],
                }
                break
            result = validate_rewrite(
                subject,
                new_q,
                bank=bank,
                dup_index=dup_index,
                answer_index=answer_index,
                replace_idx=i,
            )
            last_result = result
            if result["verdict"] in ("PASS", "SOFT_WARN"):
                best_q = new_q
                best_tier = trial_tier
                break

        if best_q is None:
            rejected.append({
                "prefix": match_key,
                "_target_index": target_idx,
                "original": original,
                "new": _build_new_q(norm, starting_tier),
                "rationale": norm["rationale"],
                "fail_reason": "; ".join(f"{g}: {r}" for g, r in (last_result or {}).get("hard_fails", [])[:3]),
                "hard_fails": (last_result or {}).get("hard_fails", []),
                "soft_warns": (last_result or {}).get("soft_warns", []),
            })
            continue

        bank[i] = best_q
        _, answer_index = build_bank_indices(bank)
        applied.append({
            "prefix": match_key,
            "_target_index": target_idx,
            "original": original,
            "new": best_q,
            "rationale": norm["rationale"],
            "auto_promoted_from": starting_tier if best_tier != starting_tier else None,
            "soft_warns": last_result.get("soft_warns", []) if last_result else [],
        })

    if applied:
        bank_path.write_text(
            json.dumps(bank, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    _write_log(subject, applied, rejected, not_found, flags, canonicals, shard_summary)

    return {
        "subject": subject,
        "proposed": len(rewrites),
        "applied": len(applied),
        "rejected": len(rejected),
        "not_found": len(not_found),
        "flags": len(flags),
        "auto_promoted": sum(1 for a in applied if a["auto_promoted_from"]),
    }


def _write_log(subject, applied, rejected, not_found, flags, canonicals, shard_summary):
    log_path = REPO / f"_pass2_{subject}_dedup_log.md"
    out: list[str] = []
    out.append(f"# Pass-2 {subject} dedup-by-diversification log")
    out.append("")
    proposed = len(applied) + len(rejected) + len(not_found)
    out.append(f"- Proposed: {proposed}")
    out.append(f"- **Applied**: {len(applied)} (auto-promoted: {sum(1 for a in applied if a['auto_promoted_from'])})")
    out.append(f"- **Rejected by gates**: {len(rejected)}")
    out.append(f"- Prefix not matched: {len(not_found)}")
    out.append(f"- Flags: {len(flags)}")
    out.append("")
    if applied:
        out.append("## Applied tier distribution")
        out.append("")
        out.append("| Tier | Applied |")
        out.append("|---|---:|")
        by_tier = Counter(a["new"].get("tier") for a in applied)
        for t in (1, 2, 3, 4, 5):
            out.append(f"| T{t} | {by_tier.get(t, 0)} |")
        out.append("")
    if rejected:
        out.append("## Rejected by gates (NOT applied — review)")
        out.append("")
        for i, r in enumerate(rejected, 1):
            out.append(f"### Rejection {i} — bank idx {r.get('_target_index', '?')}")
            out.append(f"- Failed gates: {r['fail_reason']}")
            out.append(f"- Proposed answer: `{r['new'].get('answer','')[:120]}`")
            out.append("")
    if not_found:
        out.append("## Could not match")
        out.append("")
        for nf in not_found:
            out.append(f"- `{(nf.get('question_prefix') or nf.get('match_key') or '')[:80]}` — {nf.get('_reason')}")
        out.append("")
    log_path.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: py -m tools.quizgen.audit.apply_pass2_dedup_generic <subject> [<subject> ...]")
        return 1
    summary_rows = []
    for subject in args:
        result = apply_subject(subject)
        if result.get("missing"):
            continue
        summary_rows.append(result)
        print(
            f"  RESULT {subject}: proposed={result['proposed']} "
            f"applied={result['applied']} (promoted={result['auto_promoted']}) "
            f"rejected={result['rejected']} not_found={result['not_found']} "
            f"flags={result['flags']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
