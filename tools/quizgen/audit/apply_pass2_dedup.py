"""Apply Pass-2 dedup rewrites from the 3 history shard agents, with FULL
gate validation before each write.

Inputs:
  _dedup_history_shard_A.json  (9 groups × size 4-6 = 35 rewrites)
  _dedup_history_shard_B.json  (19 groups × size 3 = 38 rewrites)
  _dedup_history_shard_C.json  (44 groups × size 2 = 44 rewrites)

For each rewrite:
  1. Match the original by question_prefix.
  2. Build the proposed new 5-field dict at the agent's tier.
  3. If length_budget fails, auto-promote up to T5.
  4. Run the full gate suite (validate_rewrite) — pipeline + history
     scratch + answer_collision.
  5. APPLY only if no hard fails. Soft-warns are logged but applied.
  6. Reject + log failures.

Outputs:
  - data/questions/history.json (mutated in place)
  - _pass2_history_dedup_log.md (per-shard rewrite log)
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.apply_pass1 import (  # noqa: E402
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

SHARD_FILES = [
    REPO / "_dedup_history_shard_A.json",
    REPO / "_dedup_history_shard_B.json",
    REPO / "_dedup_history_shard_C.json",
]
BANK_PATH = REPO / "data" / "questions" / "history.json"
LOG_PATH = REPO / "_pass2_history_dedup_log.md"


def load_all_shards() -> tuple[list[dict], list[dict], list[dict], dict]:
    rewrites: list[dict] = []
    flags: list[dict] = []
    kept_canonicals: list[dict] = []
    summary: dict = {}
    for path in SHARD_FILES:
        if not path.exists():
            print(f"  ! MISSING: {path.name} — skipping")
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


def apply() -> dict:
    print("Loading all 3 dedup shards...")
    rewrites, flags, canonicals, shard_summary = load_all_shards()
    print(f"  Total rewrites proposed: {len(rewrites)}")
    print()

    print("Loading history bank...")
    bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))
    print(f"  Bank size: {len(bank)}")

    # Build initial indices. As we mutate the bank, we'll keep the answer
    # index in sync by rebuilding after EACH apply — answer_collision is
    # the primary thing we're solving, so a stale index would silently
    # accept rewrites that collide with already-applied rewrites in the
    # same batch.
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
                "history",
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
                "original": original,
                "new": _build_new_q(norm, starting_tier),
                "rationale": norm["rationale"],
                "fail_reason": "; ".join(f"{g}: {r}" for g, r in (last_result or {}).get("hard_fails", [])[:3]),
                "hard_fails": (last_result or {}).get("hard_fails", []),
                "soft_warns": (last_result or {}).get("soft_warns", []),
            })
            continue

        bank[i] = best_q
        # Re-build answer index ONLY (dup index is stem-based; rare for
        # this to change) so subsequent rewrites in the same batch see the
        # already-applied changes and don't collide with each other.
        _, answer_index = build_bank_indices(bank)

        applied.append({
            "prefix": match_key,
            "original": original,
            "new": best_q,
            "rationale": norm["rationale"],
            "auto_promoted_from": starting_tier if best_tier != starting_tier else None,
            "soft_warns": last_result.get("soft_warns", []) if last_result else [],
        })

    if applied:
        BANK_PATH.write_text(
            json.dumps(bank, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    write_log(applied, rejected, not_found, flags, canonicals, shard_summary)

    return {
        "rewrites_proposed": len(rewrites),
        "applied": len(applied),
        "rejected": len(rejected),
        "not_found": len(not_found),
        "flags": len(flags),
        "soft_warned_applies": sum(1 for a in applied if a["soft_warns"]),
        "auto_promoted": sum(1 for a in applied if a["auto_promoted_from"]),
    }


def write_log(
    applied: list[dict],
    rejected: list[dict],
    not_found: list[dict],
    flags: list[dict],
    canonicals: list[dict],
    shard_summary: dict,
) -> None:
    out: list[str] = []
    out.append("# Pass-2 history dedup-by-diversification log")
    out.append("")
    out.append("3 parallel opus agents proposed rewrites for the 72 answer-collision")
    out.append("groups in the history bank. Each agent took one shard:")
    out.append("")
    out.append("- Shard A: 9 groups of size 4-6 (the largest collision clusters)")
    out.append("- Shard B: 19 groups of size 3")
    out.append("- Shard C: 44 groups of size 2 (simple pair deduplication)")
    out.append("")
    out.append("Each proposed rewrite was validated against the full gate suite")
    out.append("(pipeline + history_structural_gates + new answer_collision) before")
    out.append("application. The answer_collision index was rebuilt after EVERY apply")
    out.append("so rewrites within the same batch don't collide with each other.")
    out.append("")
    out.append("## Counts")
    out.append("")
    proposed = len(applied) + len(rejected) + len(not_found)
    out.append(f"- Proposed by agents: {proposed}")
    out.append(f"- **Applied**: {len(applied)}")
    out.append(f"  - of which soft-warned: {sum(1 for a in applied if a['soft_warns'])}")
    out.append(f"  - of which auto-promoted to higher tier: {sum(1 for a in applied if a['auto_promoted_from'])}")
    out.append(f"- **Rejected by gates**: {len(rejected)}")
    out.append(f"- Prefix not matched: {len(not_found)}")
    out.append(f"- Flagged for human review: {len(flags)}")
    out.append("")

    out.append("## Per-shard summaries")
    out.append("")
    for fname, s in shard_summary.items():
        out.append(f"### {fname}")
        out.append("")
        if isinstance(s, dict):
            for k, v in s.items():
                if isinstance(v, (int, float, bool)):
                    out.append(f"- {k}: {v}")
                else:
                    out.append(f"- {k}: {str(v)[:300]}")
        out.append("")

    if applied:
        out.append("---")
        out.append("")
        out.append("## Applied rewrites")
        out.append("")
        by_tier = Counter(a["new"].get("tier") for a in applied)
        out.append("| Tier | Applied |")
        out.append("|---|---:|")
        for t in (1, 2, 3, 4, 5):
            out.append(f"| T{t} | {by_tier.get(t, 0)} |")
        out.append("")
        applied_sorted = sorted(applied, key=lambda a: (a["new"].get("tier", 99), a.get("rationale", "")))
        for i, a in enumerate(applied_sorted, 1):
            orig, new = a["original"], a["new"]
            promo = f" (promoted from T{a['auto_promoted_from']})" if a.get("auto_promoted_from") else ""
            out.append(f"### {i}. T{new.get('tier')}{promo} — {a.get('rationale', '(no rationale)')[:160]}")
            out.append("")
            out.append("**ORIGINAL:**")
            out.append("")
            out.append(f"> {orig.get('question', '')}")
            out.append(f"> answer: `{orig.get('answer', '')}`")
            out.append("")
            out.append("**NEW:**")
            out.append("")
            out.append(f"> {new.get('question', '')}")
            out.append(f"> answer: `{new.get('answer', '')}`")
            for c in new.get("choices", []):
                if c != new.get("answer"):
                    out.append(f"> - distractor: `{c}`")
            out.append("")
            if new.get("context"):
                out.append(f"_context: {new['context'][:300]}_")
                out.append("")
            if a["soft_warns"]:
                out.append("**Soft-warn (applied anyway):**")
                for g, r in a["soft_warns"]:
                    out.append(f"- `{g}`: {r}")
                out.append("")
            out.append("---")
            out.append("")

    if rejected:
        out.append("## Rejected by gates")
        out.append("")
        for i, r in enumerate(rejected, 1):
            out.append(f"### Rejection {i} — {r.get('rationale', '(no rationale)')[:140]}")
            out.append(f"- **Prefix:** `{r['prefix']}`")
            out.append(f"- **Failed gates:** {r['fail_reason']}")
            new = r["new"]
            out.append(f"- **Proposed answer:** `{new.get('answer', '')}`")
            out.append(f"- **Proposed stem:** {new.get('question', '')[:140]}")
            out.append("")
            for g, reason in r["hard_fails"]:
                out.append(f"  - `{g}`: {reason}")
            out.append("")

    if not_found:
        out.append("## Could not match prefix in bank")
        out.append("")
        for nf in not_found:
            out.append(f"- `{nf.get('question_prefix') or nf.get('match_key') or ''[:80]}` — {nf.get('_reason', '?')}")
        out.append("")

    if flags:
        out.append("## Flagged for human review")
        out.append("")
        for i, f in enumerate(flags, 1):
            out.append(f"### Flag {i}")
            out.append(f"- **Prefix:** `{f.get('question_prefix', '')}`")
            out.append(f"- **Concern:** {f.get('concern', '')}")
            out.append(f"- **Suggested direction:** {f.get('suggested_direction', '(none)')}")
            out.append("")

    if canonicals:
        out.append("## Kept canonicals (one per group)")
        out.append("")
        out.append(f"_{len(canonicals)} of the 72 groups had a canonical kept as-is._")
        out.append("")

    LOG_PATH.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = apply()
    print()
    print(
        f"Total: proposed={result['rewrites_proposed']} "
        f"applied={result['applied']} (soft={result['soft_warned_applies']}, "
        f"promoted={result['auto_promoted']}) "
        f"rejected={result['rejected']} not_found={result['not_found']} "
        f"flags={result['flags']}"
    )
    print(f"Log: {LOG_PATH}")
