"""Curation: assemble approved candidates from generation + repair queues into
a single bank file.

This is the step that turns "queue of validated candidates" into "ready-to-ship
question bank." It does NOT touch `data/questions/*.json` directly — it writes
to a staging file under `state/approved/`. Promotion to the live game data is
a separate manual step the user invokes.

Approval records list each candidate's source (which generation/repair batch
+ idx or task_id), any tier overrides (for pure reclassifications), and an
origin tag for provenance.

The output file matches the live game schema (`tier`, `question`, `answer`,
`choices`, `context`) plus an embedded `_meta` for provenance. The game's
quiz engine ignores unknown fields, so `_meta` is safe.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_QUEUE_DIR = _REPO_ROOT / "tools" / "quizgen" / "state" / "queue"
_GEN_DIR = _QUEUE_DIR / "generated"
_REPAIR_OUT_DIR = _QUEUE_DIR / "repair_out"
_APPROVED_DIR = _REPO_ROOT / "tools" / "quizgen" / "state" / "approved"


@dataclass(frozen=True)
class Approval:
    """One row of the curation manifest.

    Sources:
      - If `task_id` is set, pull from `repair_out/<repair_batch>.json` and use
        the `repaired` field of the matching task.
      - Otherwise pull from `generated/<src>.json` at `idx`.

    `tier_override` lets a pure reclassification (no rewrite) ship at a tier
    different from the original generation tier.

    `origin` is a short tag for provenance (e.g. "pilot1_keep",
    "pilot2_repair", "pilot1_reclass_t2_to_t3").
    """

    src: str  # filename in generated/ OR repair_out/
    origin: str
    idx: int | None = None  # for generation-source rows
    task_id: str | None = None  # for repair-source rows
    tier_override: int | None = None
    validators_passed: tuple[str, ...] = ()


def _load_generated(src: str, idx: int) -> dict[str, Any]:
    path = _GEN_DIR / src
    data = json.loads(path.read_text(encoding="utf-8"))
    if idx < 0 or idx >= len(data):
        raise IndexError(f"idx {idx} out of range for {src} (len {len(data)})")
    return dict(data[idx])  # copy so caller mutations don't affect cache


def _load_repaired(src: str, task_id: str) -> dict[str, Any]:
    path = _REPAIR_OUT_DIR / src
    wrapper = json.loads(path.read_text(encoding="utf-8"))
    for r in wrapper.get("results", []):
        if r.get("task_id") == task_id:
            return dict(r["repaired"])
    raise KeyError(f"task_id {task_id!r} not found in {src}")


def _strip_to_game_schema(c: dict[str, Any], origin: str, source_ref: str) -> dict[str, Any]:
    """Reduce a candidate to the live-game schema + a slim _meta sidecar.

    Live game reads: tier, question, answer, choices, context.
    We add _meta with provenance — game ignores it.
    """
    out = {
        "tier": int(c["tier"]),
        "question": c["question"],
        "answer": c["answer"],
        "choices": list(c["choices"]),
        "context": c.get("context", ""),
    }
    # provenance — keep slim
    meta = c.get("_meta", {}) or {}
    out["_meta"] = {
        "origin": origin,
        "source_ref": source_ref,
        "thinker": meta.get("thinker"),
        "topic_cell": c.get("topic_cell") or meta.get("topic_cell"),
    }
    return out


def assemble_bank(approvals: list[Approval], out_path: Path) -> dict[str, Any]:
    """Pull each approved candidate, apply tier overrides, write to out_path.

    Returns a small summary dict with counts.
    """
    bank: list[dict[str, Any]] = []
    by_tier: dict[int, int] = {}
    by_origin: dict[str, int] = {}

    for a in approvals:
        if a.task_id is not None:
            cand = _load_repaired(a.src, a.task_id)
            source_ref = f"repair_out/{a.src}#{a.task_id}"
        elif a.idx is not None:
            cand = _load_generated(a.src, a.idx)
            source_ref = f"generated/{a.src}#{a.idx}"
        else:
            raise ValueError(f"Approval {a} has neither idx nor task_id")

        if a.tier_override is not None:
            cand["tier"] = a.tier_override

        record = _strip_to_game_schema(cand, a.origin, source_ref)
        bank.append(record)

        by_tier[record["tier"]] = by_tier.get(record["tier"], 0) + 1
        by_origin[a.origin] = by_origin.get(a.origin, 0) + 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bank, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "out_path": str(out_path),
        "count": len(bank),
        "by_tier": dict(sorted(by_tier.items())),
        "by_origin": dict(sorted(by_origin.items())),
    }
    return summary


# ----------------------------------------------------------------------
# The pilot manifest — current as of 2026-05-11
# ----------------------------------------------------------------------
PILOT_MANIFEST: list[Approval] = [
    # ----- Pilot 1 (presocratics T2) immediate keepers -----
    Approval(src="presocratics_t2_batch001.json", idx=0, origin="pilot1_keep"),  # Heraclitus fire
    Approval(src="presocratics_t2_batch001.json", idx=1, origin="pilot1_keep"),  # Heraclitus road
    Approval(src="presocratics_t2_batch001.json", idx=2, origin="pilot1_keep"),  # Parmenides nothing
    Approval(src="presocratics_t2_batch001.json", idx=4, origin="pilot1_keep"),  # Zeno arrow
    Approval(src="presocratics_t2_batch001.json", idx=5, origin="pilot1_keep"),  # Pythagoras hammers
    Approval(src="presocratics_t2_batch001.json", idx=6, origin="pilot1_keep"),  # Pythagoras beans
    Approval(src="presocratics_t2_batch001.json", idx=11, origin="pilot1_keep"),  # Xenophanes gods
    # ----- Pilot 1 pure reclassifications T2 -> T3 -----
    Approval(src="presocratics_t2_batch001.json", idx=7,  origin="pilot1_reclass_t2_to_t3", tier_override=3),  # Anaximander apeiron
    Approval(src="presocratics_t2_batch001.json", idx=8,  origin="pilot1_reclass_t2_to_t3", tier_override=3),  # Anaximenes condensation
    # ----- Pilot 1 repaired -----
    Approval(src="repair_batch001.json", task_id="P1C9_empedocles_wonder+length", origin="pilot1_repair"),  # Empedocles Love/Strife
    # ----- Pilot 2 (classical_liberal T3) immediate keepers -----
    Approval(src="classical_liberal_t3_batch001.json", idx=0,  origin="pilot2_keep"),  # Burke prudence
    Approval(src="classical_liberal_t3_batch001.json", idx=1,  origin="pilot2_keep"),  # Tocqueville township
    Approval(src="classical_liberal_t3_batch001.json", idx=2,  origin="pilot2_keep"),  # Bastiat candle-makers
    Approval(src="classical_liberal_t3_batch001.json", idx=3,  origin="pilot2_keep"),  # Mises subjectivism
    Approval(src="classical_liberal_t3_batch001.json", idx=4,  origin="pilot2_keep"),  # Hayek social justice
    Approval(src="classical_liberal_t3_batch001.json", idx=7,  origin="pilot2_keep"),  # Oakeshott
    Approval(src="classical_liberal_t3_batch001.json", idx=8,  origin="pilot2_keep"),  # Scruton oikophilia
    Approval(src="classical_liberal_t3_batch001.json", idx=10, origin="pilot2_keep"),  # Tocqueville equality
    # ----- Pilot 2 repaired -----
    Approval(src="repair_batch001.json", task_id="P2C5_friedman_gameplay_ambiguity", origin="pilot2_repair"),
    Approval(src="repair_batch001.json", task_id="P2C6_nozick_wonder", origin="pilot2_repair"),
    # ----- Pilot 3 (philosophy_of_mind T5) immediate keepers -----
    Approval(src="philosophy_of_mind_t5_batch001.json", idx=0, origin="pilot3_keep"),  # Searle systems reply
    Approval(src="philosophy_of_mind_t5_batch001.json", idx=1, origin="pilot3_keep"),  # Mary ability hypothesis
    Approval(src="philosophy_of_mind_t5_batch001.json", idx=2, origin="pilot3_keep"),  # Block access/phenomenal
    Approval(src="philosophy_of_mind_t5_batch001.json", idx=5, origin="pilot3_keep"),  # Strawson panpsychism
    # ----- Pilot 3 pure reclassification T5 -> T4 -----
    Approval(src="philosophy_of_mind_t5_batch001.json", idx=3, origin="pilot3_reclass_t5_to_t4", tier_override=4),  # Putnam multiple realizability
    # ----- Pilot 3 repaired (also reclassified T5 -> T4 in the repair) -----
    Approval(src="repair_batch001.json", task_id="P3C4_dennett_wonder+tier_shift", origin="pilot3_repair"),
]


def _load_json_manifests() -> list[Approval]:
    """Load all batch manifests under state/approved/manifests/*.json.

    Each is a JSON array of dicts with keys: src, origin, and either idx
    or task_id. Optional: tier_override.
    """
    manifests_dir = _APPROVED_DIR / "manifests"
    if not manifests_dir.exists():
        return []
    out = []
    for path in sorted(manifests_dir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for d in data:
            out.append(Approval(
                src=d["src"],
                origin=d["origin"],
                idx=d.get("idx"),
                task_id=d.get("task_id"),
                tier_override=d.get("tier_override"),
            ))
    return out


def assemble_pilot_bank() -> dict[str, Any]:
    """Assemble the current pilot bank: pilot manifest + all batch manifests."""
    out = _APPROVED_DIR / "philosophy_pilot_bank.json"
    full_manifest = list(PILOT_MANIFEST) + _load_json_manifests()
    return assemble_bank(full_manifest, out)


if __name__ == "__main__":
    summary = assemble_pilot_bank()
    print(f"Wrote pilot bank to: {summary['out_path']}")
    print(f"Total questions: {summary['count']}")
    print(f"By tier:   {summary['by_tier']}")
    print(f"By origin: {summary['by_origin']}")
