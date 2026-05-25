"""Apply Pass-3 residuals fixes from the residuals-fix agent.

Unlike Pass 1 / Pass 2, this applier keys fixes by EXPLICIT bank index
(not prefix or match_key) because:
  - The residuals catalog used `_build_residuals_report.py` which already
    captures exact indices
  - Many choice_shape_parity residuals share opening text (e.g. multiple
    "He said" stems) — prefix-only lookup is ambiguous

Input: `_pass3_residuals_fixes.json` from the residuals-fix agent.

For each fix:
  1. Locate `bank[index]` (no prefix matching — index is authoritative)
  2. Run full gate validation on the proposed new question
  3. Apply only if PASS or SOFT_WARN
  4. Reject + log everything else

Output:
  - data/questions/<subject>.json (mutated in place, one per subject in fixes)
  - _pass3_residuals_log.md (per-fix outcome)
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO))

from tools.quizgen.audit.validate import (  # noqa: E402
    build_bank_indices,
    validate_rewrite,
)

FIXES_FILE = REPO / "_pass3_residuals_fixes.json"
LOG_FILE = REPO / "_pass3_residuals_log.md"


def apply() -> dict:
    if not FIXES_FILE.exists():
        print(f"  ! missing: {FIXES_FILE.name}")
        return {"missing": True}
    data = json.loads(FIXES_FILE.read_text(encoding="utf-8"))
    fixes = data.get("fixes", [])
    flags = data.get("flags", [])
    summary = data.get("summary", {})

    print(f"Loaded {len(fixes)} fixes + {len(flags)} flags from {FIXES_FILE.name}")

    # Group fixes by subject so we load each bank only once
    by_subject: dict[str, list[dict]] = defaultdict(list)
    for fix in fixes:
        by_subject[fix["subject"]].append(fix)

    applied: list[dict] = []
    rejected: list[dict] = []
    not_found: list[dict] = []

    for subject, subject_fixes in by_subject.items():
        bank_path = REPO / "data" / "questions" / f"{subject}.json"
        if not bank_path.exists():
            for fix in subject_fixes:
                not_found.append({**fix, "_reason": f"no bank for {subject}"})
            continue
        bank = json.loads(bank_path.read_text(encoding="utf-8"))
        dup_index, answer_index = build_bank_indices(bank)
        modified = False

        for fix in subject_fixes:
            i = fix.get("index")
            if not isinstance(i, int) or not (0 <= i < len(bank)):
                not_found.append({**fix, "_reason": f"index {i!r} out of range"})
                continue
            new_q = fix.get("new_q")
            if not isinstance(new_q, dict) or not all(k in new_q for k in ("tier", "question", "answer", "choices", "context")):
                not_found.append({**fix, "_reason": "new_q missing required fields"})
                continue

            result = validate_rewrite(
                subject,
                new_q,
                bank=bank,
                dup_index=dup_index,
                answer_index=answer_index,
                replace_idx=i,
            )
            if result["verdict"] == "FAIL":
                rejected.append({
                    "subject": subject,
                    "index": i,
                    "fix_strategy": fix.get("fix_strategy", ""),
                    "original_failed_gates": fix.get("failed_gates", []),
                    "new_failed_gates": result["hard_fails"],
                    "original_q": bank[i],
                    "new_q": new_q,
                })
                continue

            original = dict(bank[i])
            bank[i] = new_q
            modified = True
            # Rebuild collision/dup indices: subsequent fixes in the same
            # subject see the just-applied change, so we don't accidentally
            # re-introduce collisions among the residuals themselves.
            dup_index, answer_index = build_bank_indices(bank)
            applied.append({
                "subject": subject,
                "index": i,
                "fix_strategy": fix.get("fix_strategy", ""),
                "original_failed_gates": fix.get("failed_gates", []),
                "original_q": original,
                "new_q": new_q,
                "soft_warns": result["soft_warns"],
                "verdict": result["verdict"],
            })

        if modified:
            bank_path.write_text(
                json.dumps(bank, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

    write_log(applied, rejected, not_found, flags, summary)

    return {
        "fixes_proposed": len(fixes),
        "applied": len(applied),
        "rejected": len(rejected),
        "not_found": len(not_found),
        "flags": len(flags),
        "soft_warned_applies": sum(1 for a in applied if a["soft_warns"]),
    }


def write_log(applied, rejected, not_found, flags, summary):
    out: list[str] = []
    out.append("# Pass-3 residuals fixes — log")
    out.append("")
    out.append("Pass-3 cleanup of pre-existing gate failures across 4 banks")
    out.append("(history, philosophy, cooking, animal). One opus agent proposed")
    out.append("fixes against `_residuals_catalog.json`; each was independently")
    out.append("re-validated against the full gate suite before applying.")
    out.append("")

    out.append("## Counts")
    out.append("")
    out.append(f"- Proposed: {len(applied) + len(rejected) + len(not_found)}")
    out.append(f"- **Applied**: {len(applied)} "
               f"(soft-warned: {sum(1 for a in applied if a['soft_warns'])})")
    out.append(f"- **Rejected by gates**: {len(rejected)}")
    out.append(f"- Index not in bank / malformed: {len(not_found)}")
    out.append(f"- Flagged for human review (no fix proposed): {len(flags)}")
    out.append("")

    if isinstance(summary, dict) and summary.get("notes"):
        out.append("## Agent notes")
        out.append("")
        out.append(f"> {summary['notes']}")
        out.append("")

    # Per-subject summary
    if applied:
        out.append("## Applied fixes by subject + original failure gate")
        out.append("")
        sg = Counter()
        for a in applied:
            sub = a["subject"]
            for g in a["original_failed_gates"]:
                gate_name = g["gate"] if isinstance(g, dict) else str(g)
                sg[(sub, gate_name)] += 1
        out.append("| Subject | Gate fixed | Count |")
        out.append("|---|---|---:|")
        for (sub, gate), count in sorted(sg.items()):
            out.append(f"| {sub} | {gate} | {count} |")
        out.append("")

    # Detailed apply log (every fix)
    if applied:
        out.append("---")
        out.append("")
        out.append("## Applied fixes (detail)")
        out.append("")
        for i, a in enumerate(applied, 1):
            orig, new = a["original_q"], a["new_q"]
            gates = ", ".join(
                g["gate"] if isinstance(g, dict) else str(g)
                for g in a["original_failed_gates"]
            )
            out.append(f"### {i}. {a['subject']} [{a['index']}] — fixed: {gates}")
            out.append("")
            out.append(f"**Strategy:** {a['fix_strategy']}")
            out.append("")
            out.append(f"**Original** (T{orig.get('tier')}, ans `{orig.get('answer','')[:80]}`):")
            out.append("")
            out.append(f"> {orig.get('question', '')[:200]}")
            out.append("")
            out.append(f"**New** (T{new.get('tier')}, ans `{new.get('answer','')[:80]}`):")
            out.append("")
            out.append(f"> {new.get('question', '')[:200]}")
            for c in new.get("choices", []):
                if c != new.get("answer"):
                    out.append(f"> - distractor: `{c[:120]}`")
            if a["soft_warns"]:
                out.append("")
                out.append("**Soft-warns (applied anyway):**")
                for g, r in a["soft_warns"]:
                    out.append(f"- `{g}`: {r}")
            out.append("")
            out.append("---")
            out.append("")

    if rejected:
        out.append("## Rejected by gates (NOT applied)")
        out.append("")
        for i, r in enumerate(rejected, 1):
            new = r["new_q"]
            out.append(f"### Rejection {i} — {r['subject']} [{r['index']}]")
            out.append(f"- **Original failed gates:** {r['original_failed_gates']}")
            out.append(f"- **New failed gates:** {r['new_failed_gates']}")
            out.append(f"- **Strategy:** {r['fix_strategy']}")
            out.append(f"- **Proposed answer:** `{new.get('answer','')[:120]}`")
            out.append("")

    if not_found:
        out.append("## Could not locate bank target")
        out.append("")
        for nf in not_found:
            out.append(f"- {nf.get('subject')}[{nf.get('index')}] — {nf.get('_reason')}")
        out.append("")

    if flags:
        out.append("## Flagged for human review")
        out.append("")
        for f in flags:
            out.append(f"- {f.get('subject','?')}[{f.get('index','?')}]: {f.get('concern','')}")
            out.append(f"    suggested: {f.get('suggested_direction','(none)')}")
        out.append("")

    LOG_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = apply()
    if result.get("missing"):
        sys.exit(1)
    print()
    print(
        f"Total: proposed={result['fixes_proposed']} "
        f"applied={result['applied']} (soft={result['soft_warned_applies']}) "
        f"rejected={result['rejected']} not_found={result['not_found']} "
        f"flags={result['flags']}"
    )
    print(f"Log: {LOG_FILE.name}")
