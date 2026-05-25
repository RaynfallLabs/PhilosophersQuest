"""Apply Pass-1 rewrites from per-subject audit-agent outputs, with FULL
gate validation before each write.

Inputs:
  _audit_<subject>_rewrites.json  (one per subject, agent-produced)

For each rewrite:
  1. Match the original question by question_prefix.
  2. Construct the proposed new 5-field dict.
  3. Auto-promote tier upward if the rewrite exceeds the current tier's
     character budget (existing behavior, preserved from
     _apply_audit_rewrites.py).
  4. Run the full gate suite (validate_rewrite) — pipeline + scratch + the
     new answer_collision gate.
  5. APPLY only if hard_fails is empty. Soft-warns are logged but applied.
  6. Otherwise REJECT and add to the failure log with the failing gates.

Outputs:
  - data/questions/<subject>.json  (mutated in place)
  - _pass1_<subject>_log.md        (per-subject morning-review log)

Usage:
  py tools/quizgen/scratch/_apply_pass1_rewrites.py <subject> [<subject> ...]
  py tools/quizgen/scratch/_apply_pass1_rewrites.py all
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import (  # noqa: E402
    build_bank_indices,
    validate_rewrite,
)

# Per-tier hard caps with 5% grace, matching history convention. We
# auto-promote upward if a richer rewrite exceeds the current tier cap.
TIER_CAPS = {1: 525, 2: 651, 3: 808, 4: 945, 5: 1155}

SUBJECTS = ("philosophy", "cooking", "animal", "geography")


def _audit_file(subject: str) -> Path:
    return REPO / f"_audit_{subject}_rewrites.json"


def _bank_file(subject: str) -> Path:
    return REPO / "data" / "questions" / f"{subject}.json"


def _log_file(subject: str) -> Path:
    return REPO / f"_pass1_{subject}_log.md"


def _coerce_int(v: Any, default: int | None = None) -> int | None:
    if v is None:
        return default
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        try:
            return int(v.strip())
        except (TypeError, ValueError):
            return default
    return default


def _normalize_rewrite(rw: dict) -> dict:
    """Normalize the schemas agents have produced into a canonical flat shape.

    Schema A (history-style):
      question_prefix, tier, promote_to_tier, new_question (str),
      new_answer, new_choices, new_context, rationale

    Schema B (animal-style):
      match_key, tier, issue, new_question (dict with 5 fields)

    Schema C (geography-style):
      match_key, tier (str), reason, rewrite (dict with 5 fields)
    """
    # Find the nested 5-field dict, if any
    nested = None
    for key in ("rewrite", "new_question", "new"):
        v = rw.get(key)
        if isinstance(v, dict) and "question" in v and "answer" in v:
            nested = v
            break

    match_key = rw.get("match_key") or rw.get("question_prefix") or ""
    rationale = (
        rw.get("rationale")
        or rw.get("reason")
        or rw.get("issue")
        or rw.get("rewrite_rationale")
        or ""
    )
    tier_in = _coerce_int(rw.get("tier"))
    promote_in = _coerce_int(rw.get("promote_to_tier"))

    if nested is not None:
        return {
            "match_key": match_key,
            "tier": tier_in or _coerce_int(nested.get("tier")),
            "promote_to_tier": promote_in or _coerce_int(nested.get("tier")),
            "new_question_text": nested.get("question", "") or "",
            "new_answer": nested.get("answer", "") or "",
            "new_choices": nested.get("choices", []) or [],
            "new_context": nested.get("context", "") or "",
            "rationale": rationale,
        }
    # Flat schema A
    return {
        "match_key": match_key,
        "tier": tier_in,
        "promote_to_tier": promote_in,
        "new_question_text": rw.get("new_question", "") or "",
        "new_answer": rw.get("new_answer", "") or "",
        "new_choices": rw.get("new_choices", []) or [],
        "new_context": rw.get("new_context", "") or "",
        "rationale": rationale,
    }


def _find_bank_idx(bank: list[dict], match_key: str, target_index: int | None = None) -> int | None:
    """Locate the bank index for a rewrite. Resolution order:
      1. `target_index` if provided and in-range (unambiguous lookup; the
         Shard-A dedup agent supplies this when 60-char prefixes collide).
      2. Bank question startswith(match_key).
      3. Bank question contains match_key as substring.
    """
    if target_index is not None and 0 <= target_index < len(bank):
        return target_index
    if not match_key:
        return None
    mk = match_key.strip()
    for i, q in enumerate(bank):
        if q.get("question", "").startswith(mk):
            return i
    for i, q in enumerate(bank):
        if mk in q.get("question", ""):
            return i
    return None


def _build_new_q(norm: dict, tier: int) -> dict:
    return {
        "tier": int(tier),
        "question": norm["new_question_text"],
        "answer": norm["new_answer"],
        "choices": norm["new_choices"],
        "context": norm["new_context"],
    }


def _starting_tier(norm: dict, original: dict) -> int:
    t = norm.get("promote_to_tier") or norm.get("tier") or original.get("tier") or 1
    try:
        return int(t)
    except (TypeError, ValueError):
        return 1


def apply_for_subject(subject: str) -> dict:
    """Returns summary dict: counts + per-rewrite results."""
    audit = _audit_file(subject)
    bank_path = _bank_file(subject)
    if not audit.exists():
        return {"subject": subject, "missing_audit": True}
    if not bank_path.exists():
        return {"subject": subject, "missing_bank": True}

    audit_data = json.loads(audit.read_text(encoding="utf-8"))
    rewrites = audit_data.get("rewrites", []) or []
    flags = audit_data.get("flags", []) or []
    summary_notes = audit_data.get("summary", {})

    bank = json.loads(bank_path.read_text(encoding="utf-8"))

    # Build indices ONCE per subject — reused across all proposed rewrites
    # for that subject. Bank doesn't shrink during the pass (we replace, not
    # delete), so indices stay valid even as we mutate bank entries.
    dup_index, answer_index = build_bank_indices(bank)

    applied: list[dict] = []
    rejected: list[dict] = []
    not_found: list[dict] = []

    for rw in rewrites:
        norm = _normalize_rewrite(rw)
        match_key = norm["match_key"]
        # Honor agent-provided target index if present (Shard A's disambiguator)
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

        # Try the rewrite at the proposed tier first; if any pipeline/structural
        # gate fails (most often length_budget), bump tier up and retry. Land
        # at the LOWEST tier that fully passes. Reject only if every tier
        # T_proposed..T5 fails the gate suite.
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
            # Either every tier failed gates, or total exceeded T5 cap
            failed_q = _build_new_q(norm, starting_tier)
            rejected.append({
                "prefix": match_key,
                "original": original,
                "new": failed_q,
                "rationale": norm["rationale"],
                "fail_reason": "; ".join(f"{g}: {r}" for g, r in (last_result or {}).get("hard_fails", [])[:3]),
                "hard_fails": (last_result or {}).get("hard_fails", []),
                "soft_warns": (last_result or {}).get("soft_warns", []),
            })
            continue

        # PASS or SOFT_WARN — apply at best_tier
        bank[i] = best_q
        applied.append({
            "prefix": match_key,
            "original": original,
            "new": best_q,
            "rationale": norm["rationale"],
            "auto_promoted_from": starting_tier if best_tier != starting_tier else None,
            "soft_warns": last_result.get("soft_warns", []) if last_result else [],
        })

    # Persist mutated bank
    if applied:
        bank_path.write_text(
            json.dumps(bank, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    _write_log(
        subject=subject,
        applied=applied,
        rejected=rejected,
        not_found=not_found,
        flags=flags,
        summary_notes=summary_notes,
    )

    return {
        "subject": subject,
        "rewrites_proposed": len(rewrites),
        "applied": len(applied),
        "rejected": len(rejected),
        "not_found": len(not_found),
        "flags": len(flags),
        "soft_warned_applies": sum(1 for a in applied if a["soft_warns"]),
        "auto_promoted": sum(1 for a in applied if a["auto_promoted_from"]),
    }


def _write_log(
    *,
    subject: str,
    applied: list[dict],
    rejected: list[dict],
    not_found: list[dict],
    flags: list[dict],
    summary_notes: Any,
) -> None:
    log = _log_file(subject)
    out: list[str] = []
    out.append(f"# Pass-1 rewrite log — {subject}")
    out.append("")
    out.append("Generated by `_apply_pass1_rewrites.py`. Each proposed rewrite was")
    out.append("validated against the full gate suite (pipeline deterministic +")
    out.append("subject structural + answer_collision) before being applied.")
    out.append("")
    out.append("## Counts")
    out.append("")
    out.append(f"- Proposed by agent: {len(applied) + len(rejected) + len(not_found)}")
    out.append(f"- **Applied**: {len(applied)}")
    out.append(f"  - of which soft-warned: {sum(1 for a in applied if a['soft_warns'])}")
    out.append(f"  - of which auto-promoted to higher tier: {sum(1 for a in applied if a['auto_promoted_from'])}")
    out.append(f"- **Rejected by gates**: {len(rejected)}")
    out.append(f"- Prefix not matched: {len(not_found)}")
    out.append(f"- Flagged for human review: {len(flags)}")
    out.append("")

    if isinstance(summary_notes, dict) and summary_notes.get("notes"):
        out.append("## Agent notes")
        out.append("")
        out.append(f"> {summary_notes['notes']}")
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
            out.append(f"### {i}. T{new.get('tier')}{promo} — {a.get('rationale', '(no rationale)')}")
            out.append("")
            out.append("**ORIGINAL:**")
            out.append("")
            out.append(f"> {orig.get('question', '')}")
            out.append(f"> answer: `{orig.get('answer', '')}`")
            for c in orig.get("choices", []):
                if c != orig.get("answer"):
                    out.append(f"> - distractor: `{c}`")
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
                out.append(f"_context: {new['context']}_")
                out.append("")
            if a["soft_warns"]:
                out.append("**Soft-warn flags (applied anyway):**")
                for g, r in a["soft_warns"]:
                    out.append(f"- `{g}`: {r}")
                out.append("")
            out.append("---")
            out.append("")

    if rejected:
        out.append("")
        out.append("## Rejected by gates (NOT applied — review and re-attempt)")
        out.append("")
        for i, r in enumerate(rejected, 1):
            out.append(f"### Rejection {i} — {r.get('rationale', '(no rationale)')}")
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
        out.append("")
        out.append("## Could not match prefix in bank")
        out.append("")
        for nf in not_found:
            out.append(f"- `{nf.get('question_prefix', '')[:80]}` — {nf.get('_reason', '?')}")
        out.append("")

    if flags:
        out.append("")
        out.append("## Flagged for human review (no rewrite proposed)")
        out.append("")
        for i, f in enumerate(flags, 1):
            out.append(f"### Flag {i}")
            out.append(f"- **Prefix:** `{f.get('question_prefix', '')}`")
            out.append(f"- **Original answer:** `{f.get('original_answer', '')}`")
            out.append(f"- **Concern:** {f.get('concern', '')}")
            out.append(f"- **Suggested direction:** {f.get('suggested_direction', '(none)')}")
            out.append("")

    log.write_text("\n".join(out) + "\n", encoding="utf-8")


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("Usage: py _apply_pass1_rewrites.py <subject>|all")
        return 1
    targets = list(SUBJECTS) if args[0] == "all" else args
    for subject in targets:
        result = apply_for_subject(subject)
        if result.get("missing_audit"):
            print(f"  {subject}: NO AUDIT FILE")
            continue
        if result.get("missing_bank"):
            print(f"  {subject}: NO BANK FILE")
            continue
        print(
            f"  {subject}: proposed={result['rewrites_proposed']} "
            f"applied={result['applied']} (soft={result['soft_warned_applies']}, "
            f"promoted={result['auto_promoted']}) "
            f"rejected={result['rejected']} not_found={result['not_found']} "
            f"flags={result['flags']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
