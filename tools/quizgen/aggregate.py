"""Aggregation: read validator outputs for a batch, produce unified verdicts.

For each candidate, decides one of:
  - CLEAN_KEEP    : all validators pass cleanly; under 600 char target
  - GRACE_KEEP    : passes structurally but in 601-630 char grace zone with no other issues
  - RECLASSIFY    : only issue is tier_fit says actual tier differs; metadata change only
  - REPAIR        : has wonder / A6 / ambiguity / structural-budget issues that need rewrite
  - DISCARD       : critical failure (fact error, viral test bomb, unrepairable)

Produces:
  - A markdown summary report
  - A JSON dict mapping candidate_idx → verdict + reasons
  - A list of repair task records (for feeding to the repair agent)

Validator JSON schemas vary; this module knows each.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_QUEUE_DIR = _REPO_ROOT / "tools" / "quizgen" / "state" / "queue"


@dataclass
class CandidateVerdict:
    idx: int
    thinker: str
    tier: int
    verdict: str  # CLEAN_KEEP / GRACE_KEEP / RECLASSIFY / REPAIR / DISCARD
    reasons: list[str] = field(default_factory=list)
    tier_override: int | None = None
    failed_gates: list[dict[str, Any]] = field(default_factory=list)
    chars: int = 0


def _load_validator(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _result_for_idx(validator_out: dict | None, idx: int) -> dict | None:
    if not validator_out:
        return None
    for r in validator_out.get("results", []):
        if r.get("candidate_idx") == idx:
            return r
    return None


def aggregate_batch(batch_filename: str) -> dict[str, Any]:
    """Aggregate validator outputs for one batch.

    `batch_filename` is the JSON filename (e.g. "classical_socratic_t2_batch001.json")
    used both in `state/queue/generated/` and in each validator subdir.
    """
    gen_path = _QUEUE_DIR / "generated" / batch_filename
    candidates = json.loads(gen_path.read_text(encoding="utf-8"))

    moral = _load_validator(_QUEUE_DIR / "moral_fit" / batch_filename)
    wonder = _load_validator(_QUEUE_DIR / "wonder_fun" / batch_filename)
    tier_fit = _load_validator(_QUEUE_DIR / "tier_fit" / batch_filename)
    gameplay = _load_validator(_QUEUE_DIR / "gameplay" / batch_filename)

    verdicts: list[CandidateVerdict] = []

    for idx, q in enumerate(candidates):
        chars = len(q.get("question", "")) + sum(len(c) for c in q.get("choices", []))
        tier = int(q.get("tier", 0))
        thinker = (q.get("_meta") or {}).get("thinker", "?")

        mr = _result_for_idx(moral, idx)
        wr = _result_for_idx(wonder, idx)
        tr = _result_for_idx(tier_fit, idx)
        gr = _result_for_idx(gameplay, idx)

        reasons: list[str] = []
        failed_gates: list[dict[str, Any]] = []
        tier_override: int | None = None

        # ---- moral_fit ----
        moral_verdict = (mr or {}).get("verdict", "pass" if mr is None else "pass")
        if moral_verdict == "discard":
            reasons.append("moral_fit DISCARD")
            failed_gates.append({"gate": "moral_fit", "detail": "see moral_fit output for specific A-gate", "suggested_fix": "see validator notes"})
        elif moral_verdict == "repair":
            reasons.append("moral_fit REPAIR")
            failed_gates.append({"gate": "moral_fit", "detail": (mr or {}).get("verdict_rationale", ""), "suggested_fix": ""})

        # ---- wonder_fun ----
        wonder_verdict = (wr or {}).get("verdict", "pass")
        if wonder_verdict == "discard_recommended":
            reasons.append("wonder_fun DISCARD")
            failed_gates.append({"gate": "wonder_fun", "detail": "fundamental wonder absence", "suggested_fix": "regenerate"})
        elif wonder_verdict == "repair":
            reasons.append("wonder_fun REPAIR")
            note = (wr or {}).get("rationale", "")
            failed_gates.append({"gate": "wonder_fun.B2_or_other", "detail": note, "suggested_fix": "lead with scene/image"})

        # ---- tier_fit ----
        tr_score = (tr or {}).get("fit_score") or (tr or {}).get("fit_status")
        claimed = (tr or {}).get("claimed_tier", tier)
        estimated = (tr or {}).get("estimated_tier")
        if tr_score in ("fail", "partial") and estimated and int(estimated) != int(claimed):
            tier_override = int(estimated)
            reasons.append(f"tier_fit suggests T{estimated} (claimed T{claimed})")
            # "partial" is a pure reclassification, not a rewrite
            # "fail" off-by-2+ might warrant rewrite
            if tr_score == "fail":
                failed_gates.append({"gate": "tier_fit", "detail": (tr or {}).get("rationale", ""), "suggested_fix": (tr or {}).get("suggested_action", "")})

        # ---- gameplay ----
        gp_verdict = (gr or {}).get("overall_verdict", "pass")
        char_status = (gr or {}).get("char_budget_status", "pass")
        ambig_status = (gr or {}).get("ambiguity_status", "pass")
        if gp_verdict == "discard":
            reasons.append("gameplay DISCARD")
            failed_gates.append({"gate": "gameplay", "detail": (gr or {}).get("rationale", ""), "suggested_fix": "see gameplay validator"})
        elif gp_verdict == "repair":
            # char in grace zone alone is not a repair-need; ambiguity is
            if ambig_status in ("fail", "partial"):
                reasons.append(f"gameplay ambiguity {ambig_status}")
                failed_gates.append({
                    "gate": "gameplay.ambiguity",
                    "detail": (gr or {}).get("ambiguity_note", "") or "answer/distractor surface collision",
                    "suggested_fix": "sharpen distractor or prompt to disambiguate"
                })
            elif char_status == "fail":  # over hard cap
                reasons.append(f"gameplay char hard-fail ({chars} chars)")
                failed_gates.append({
                    "gate": "gameplay.char_hard_cap",
                    "detail": f"Total {chars} chars exceeds hard cap.",
                    "suggested_fix": "trim to ≤ tier cap (600 T1-T3 / 800 T4-T5)"
                })
            # if only char_status PARTIAL (601-630 grace) and no ambiguity, treat as keep with grace flag

        # ---- final verdict assignment ----
        if any("DISCARD" in r for r in reasons):
            verdict = "DISCARD"
        elif any("REPAIR" in r for r in reasons) or any("ambiguity" in r for r in reasons) or any("hard-fail" in r for r in reasons):
            # genuine repair issue (wonder/moral/ambiguity/hard-cap)
            verdict = "REPAIR"
        elif tier_override is not None and not reasons[1:] if False else (tier_override is not None and all("tier_fit" in r for r in reasons)):
            # only issue is tier_fit; pure reclassification
            verdict = "RECLASSIFY"
        elif tier_override is not None:
            # mixed: tier shift + other repair
            verdict = "REPAIR"
        elif char_status == "partial":
            # only issue is char grace zone (601-630): accept
            verdict = "GRACE_KEEP"
        else:
            verdict = "CLEAN_KEEP"

        verdicts.append(CandidateVerdict(
            idx=idx,
            thinker=thinker,
            tier=tier,
            verdict=verdict,
            reasons=reasons,
            tier_override=tier_override,
            failed_gates=failed_gates,
            chars=chars,
        ))

    return {
        "batch": batch_filename,
        "verdicts": verdicts,
        "summary": {
            "total": len(candidates),
            "clean_keep": sum(1 for v in verdicts if v.verdict == "CLEAN_KEEP"),
            "grace_keep": sum(1 for v in verdicts if v.verdict == "GRACE_KEEP"),
            "reclassify": sum(1 for v in verdicts if v.verdict == "RECLASSIFY"),
            "repair": sum(1 for v in verdicts if v.verdict == "REPAIR"),
            "discard": sum(1 for v in verdicts if v.verdict == "DISCARD"),
        },
    }


def aggregate_many(batch_filenames: list[str], out_path: Path) -> dict[str, Any]:
    """Aggregate multiple batches; write a unified report."""
    all_results = {}
    grand_summary = {"clean_keep": 0, "grace_keep": 0, "reclassify": 0, "repair": 0, "discard": 0, "total": 0}
    for fn in batch_filenames:
        r = aggregate_batch(fn)
        all_results[fn] = r
        for k, v in r["summary"].items():
            grand_summary[k] += v

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "batches": {fn: {"summary": r["summary"], "verdicts": [v.__dict__ for v in r["verdicts"]]} for fn, r in all_results.items()},
        "grand_summary": grand_summary,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build_repair_task_records(aggregated: dict[str, Any]) -> list[dict[str, Any]]:
    """From an aggregated report, build the list of RepairTask records that the
    repair agent can consume (matching the schema in llm_jobs/repair.md).
    """
    tasks = []
    for batch_filename, br in aggregated["batches"].items():
        gen_path = _QUEUE_DIR / "generated" / batch_filename
        candidates = json.loads(gen_path.read_text(encoding="utf-8"))
        for v in br["verdicts"]:
            if v["verdict"] != "REPAIR":
                continue
            original = candidates[v["idx"]]
            task = {
                "task_id": f"B1_{batch_filename.replace('.json','')}_idx{v['idx']}_{v['thinker'].replace(' ','_')[:30]}",
                "source_batch": batch_filename,
                "source_idx": v["idx"],
                "original": original,
                "failed_gates": v["failed_gates"],
                "tier_override": v.get("tier_override"),
                "attempt_number": 1,
            }
            tasks.append(task)
    return tasks
