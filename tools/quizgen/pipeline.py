"""Resumable orchestrator for the quiz validation pipeline.

This module runs deterministic gates over a set of questions and writes
structured results (JSON) + a human-readable summary (Markdown) to a
run directory under `tools/quizgen/state/runs/<timestamp>/`.

LLM-driven gates (moral_fit, wonder_fun, tier_fit, fact_check, gameplay,
viral_check) are NOT invoked from here. They run via Claude Code
subagents from the chat session. The pipeline emits "needs_llm" queues
that the session can pick up.
"""
from __future__ import annotations

import datetime
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tools.quizgen import specs
from tools.quizgen.deterministic import (
    GateResult,
    GateStatus,
    build_answer_collision_index,
    build_duplicate_index,
    validate_answer_collision,
    validate_anti_rote,
    validate_duplicate,
    validate_length_budget,
    validate_length_parity,
    validate_math_correctness,
    validate_schema,
    validate_trailing_tokens,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DATA_DIR = _REPO_ROOT / "data" / "questions"
_STATE_DIR = _REPO_ROOT / "tools" / "quizgen" / "state"
_RUNS_DIR = _STATE_DIR / "runs"


@dataclass
class QuestionResult:
    idx: int
    tier: int
    question_preview: str
    gates: dict[str, GateResult] = field(default_factory=dict)

    @property
    def fails(self) -> list[str]:
        return [g for g, r in self.gates.items() if r.status == GateStatus.FAIL]

    @property
    def hard_fail(self) -> bool:
        # schema fail is a hard fail; everything else is soft
        return self.gates.get("schema", None) is not None and self.gates["schema"].status == GateStatus.FAIL

    @property
    def verdict(self) -> str:
        """Deterministic-only verdict. LLM gates may downgrade further."""
        if self.hard_fail:
            return "DISCARD"
        if not self.fails:
            return "KEEP"
        return "REPAIR"

    def to_dict(self) -> dict[str, Any]:
        return {
            "idx": self.idx,
            "tier": self.tier,
            "question_preview": self.question_preview,
            "verdict": self.verdict,
            "fails": self.fails,
            "gates": {g: r.to_dict() for g, r in self.gates.items()},
        }


@dataclass
class RunReport:
    subject: str
    started_at: str
    moral_vision_sha: str
    n_questions: int
    n_keep: int = 0
    n_repair: int = 0
    n_discard: int = 0
    gate_fail_counts: dict[str, int] = field(default_factory=dict)
    fail_counts_by_tier: dict[int, dict[str, int]] = field(default_factory=dict)
    results: list[QuestionResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject": self.subject,
            "started_at": self.started_at,
            "moral_vision_sha": self.moral_vision_sha,
            "n_questions": self.n_questions,
            "n_keep": self.n_keep,
            "n_repair": self.n_repair,
            "n_discard": self.n_discard,
            "gate_fail_counts": dict(self.gate_fail_counts),
            "fail_counts_by_tier": {
                int(t): dict(counts) for t, counts in self.fail_counts_by_tier.items()
            },
            "results": [r.to_dict() for r in self.results],
        }


def _load_questions(subject: str) -> list[dict[str, Any]]:
    path = _DATA_DIR / f"{subject}.json"
    if not path.exists():
        raise FileNotFoundError(f"No question file for subject {subject!r}: {path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array; got {type(data).__name__}")
    return data


def _stratified_sample(
    questions: list[dict[str, Any]],
    n_per_tier: int,
    seed: int,
) -> list[tuple[int, dict[str, Any]]]:
    """Return [(original_idx, question), ...] stratified by tier."""
    rng = random.Random(seed)
    by_tier: dict[int, list[tuple[int, dict[str, Any]]]] = {}
    for i, q in enumerate(questions):
        by_tier.setdefault(int(q.get("tier", 0)), []).append((i, q))
    out: list[tuple[int, dict[str, Any]]] = []
    for tier in sorted(by_tier):
        pool = by_tier[tier]
        rng.shuffle(pool)
        out.extend(pool[:n_per_tier])
    return out


def run_deterministic(
    subject: str,
    sample_size: int | None = None,
    seed: int | None = None,
    out_dir: Path | None = None,
) -> RunReport:
    """Run all deterministic gates against a subject's bank.

    If `sample_size` is given, sample (sample_size // 5) per tier with the
    given seed. Otherwise validate the whole bank.

    Writes structured + human-readable output to `out_dir` (default: a
    timestamped subdir under state/runs/).
    """
    all_questions = _load_questions(subject)
    spec_set = specs.load_all(subject=subject)
    mv_sha = spec_set.moral_vision.sha256

    # sampling
    if sample_size:
        n_per_tier = sample_size // 5
        sampled = _stratified_sample(all_questions, n_per_tier, seed or 0)
        targets: list[tuple[int, dict[str, Any]]] = sampled
    else:
        targets = list(enumerate(all_questions))

    # duplicate index built over the sample's questions (so dup-detection
    # is intra-sample for calibration runs, and intra-bank for full runs).
    dup_index = build_duplicate_index([q for _, q in targets])
    # Answer-collision index — separate from stem dedup. Catches same-answer
    # questions even when stems differ. Discovered 2026-05-25 after the
    # history rebuild surfaced 64 cross-tier same-answer collisions.
    answer_index = build_answer_collision_index([q for _, q in targets])

    started_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    report = RunReport(
        subject=subject,
        started_at=started_at,
        moral_vision_sha=mv_sha,
        n_questions=len(targets),
    )

    for local_idx, (orig_idx, q) in enumerate(targets):
        tier = int(q.get("tier", 0)) if isinstance(q.get("tier", 0), int) else 0
        question_text = str(q.get("question", ""))
        preview = (question_text[:80] + "...") if len(question_text) > 80 else question_text
        qr = QuestionResult(
            idx=orig_idx,
            tier=tier,
            question_preview=preview,
        )
        # Math's templated questions ("Is 7 prime?" vs "Is 17 prime?") are
        # pedagogically valuable AS patterned exposure — relax the default
        # 0.85 dup threshold to 0.97 for math so only exact/near-exact
        # paraphrases are flagged.
        dup_threshold = 0.97 if subject == "math" else 0.85
        qr.gates["schema"] = validate_schema(q)
        qr.gates["length_parity"] = validate_length_parity(q, subject=subject)
        qr.gates["length_budget"] = validate_length_budget(q, subject=subject)
        qr.gates["anti_rote"] = validate_anti_rote(q, subject=subject)
        qr.gates["duplicate"] = validate_duplicate(
            q, dup_index, threshold=dup_threshold, self_idx=local_idx
        )
        qr.gates["answer_collision"] = validate_answer_collision(
            q, answer_index, self_idx=local_idx, subject=subject
        )
        qr.gates["math_correctness"] = validate_math_correctness(q, subject=subject)
        qr.gates["trailing_tokens"] = validate_trailing_tokens(q, subject=subject)

        for gate_name, gate_result in qr.gates.items():
            if gate_result.status == GateStatus.FAIL:
                report.gate_fail_counts[gate_name] = report.gate_fail_counts.get(gate_name, 0) + 1
                tier_counts = report.fail_counts_by_tier.setdefault(tier, {})
                tier_counts[gate_name] = tier_counts.get(gate_name, 0) + 1

        v = qr.verdict
        if v == "KEEP":
            report.n_keep += 1
        elif v == "REPAIR":
            report.n_repair += 1
        else:
            report.n_discard += 1
        report.results.append(qr)

    # write outputs
    if out_dir is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
        out_dir = _RUNS_DIR / f"{timestamp}_{subject}_det"
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "report.json"
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")

    md_path = out_dir / "report.md"
    md_path.write_text(_render_markdown(report, spec_set), encoding="utf-8")

    return report


def _render_markdown(report: RunReport, spec_set: specs.Specs) -> str:
    lines: list[str] = []
    lines.append(f"# Deterministic pipeline report — {report.subject}")
    lines.append("")
    lines.append(f"- Run started: `{report.started_at}`")
    lines.append(f"- moral_vision.md SHA: `{report.moral_vision_sha[:12]}`")
    lines.append(f"- Questions evaluated: **{report.n_questions}**")
    lines.append("")
    lines.append("## Verdict distribution (deterministic-only)")
    lines.append("")
    lines.append("| Verdict | Count | % |")
    lines.append("|---|---:|---:|")
    n = max(report.n_questions, 1)
    lines.append(f"| KEEP | {report.n_keep} | {report.n_keep / n * 100:.1f}% |")
    lines.append(f"| REPAIR | {report.n_repair} | {report.n_repair / n * 100:.1f}% |")
    lines.append(f"| DISCARD | {report.n_discard} | {report.n_discard / n * 100:.1f}% |")
    lines.append("")
    lines.append("## Gate-by-gate fail counts")
    lines.append("")
    lines.append("| Gate | Fails | % of n |")
    lines.append("|---|---:|---:|")
    for gate, count in sorted(report.gate_fail_counts.items(), key=lambda t: -t[1]):
        lines.append(f"| {gate} | {count} | {count / n * 100:.1f}% |")
    lines.append("")
    lines.append("## Verdict by tier")
    lines.append("")
    tiers = sorted({r.tier for r in report.results})
    if tiers:
        lines.append("| Tier | n | KEEP | REPAIR | DISCARD |")
        lines.append("|---|---:|---:|---:|---:|")
        for t in tiers:
            results_t = [r for r in report.results if r.tier == t]
            nt = len(results_t)
            kt = sum(1 for r in results_t if r.verdict == "KEEP")
            rt = sum(1 for r in results_t if r.verdict == "REPAIR")
            dt = sum(1 for r in results_t if r.verdict == "DISCARD")
            lines.append(f"| {t} | {nt} | {kt} | {rt} | {dt} |")
        lines.append("")
    lines.append("## Failure modes per tier")
    lines.append("")
    for t in tiers:
        tier_counts = report.fail_counts_by_tier.get(t, {})
        if not tier_counts:
            continue
        lines.append(f"### Tier {t}")
        lines.append("")
        for gate, count in sorted(tier_counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {gate}: {count} fails")
        lines.append("")

    lines.append("## Per-question detail (failed only)")
    lines.append("")
    failed = [r for r in report.results if r.fails or r.hard_fail]
    if not failed:
        lines.append("_No failures._")
    else:
        lines.append(f"_{len(failed)} questions with at least one failed gate._")
        lines.append("")
        lines.append("| Idx | Tier | Verdict | Failed gates | Preview |")
        lines.append("|---|---|---|---|---|")
        for r in failed[:100]:
            failed_list = ", ".join(r.fails)
            preview = r.question_preview.replace("|", "\\|")
            lines.append(f"| {r.idx} | {r.tier} | {r.verdict} | {failed_list} | {preview} |")
        if len(failed) > 100:
            lines.append("")
            lines.append(f"_(showing first 100 of {len(failed)} failures; full data in report.json)_")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    """CLI entry; see `__main__.py` for argparse setup."""
    # left empty; __main__.py invokes the higher-level functions directly
    raise NotImplementedError("Invoke via `py -m tools.quizgen`.")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
