"""CLI entry for the quiz pipeline.

Usage:
    py -m tools.quizgen validate --subject philosophy
    py -m tools.quizgen calibrate --subject philosophy --sample 100 --seed 20260511
    py -m tools.quizgen specs                 # print spec hashes
    py -m tools.quizgen patterns              # print anti-rote regex list
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.quizgen import specs
from tools.quizgen.curate import assemble_pilot_bank
from tools.quizgen.deterministic.anti_rote import ANTI_ROTE_PATTERN_SOURCES
from tools.quizgen.pipeline import run_deterministic


def _cmd_validate(args: argparse.Namespace) -> int:
    out_dir = Path(args.out) if args.out else None
    report = run_deterministic(subject=args.subject, out_dir=out_dir)
    print(
        f"\nValidated {report.n_questions} {args.subject} questions: "
        f"{report.n_keep} KEEP, {report.n_repair} REPAIR, {report.n_discard} DISCARD"
    )
    print("Top failure modes:")
    for gate, count in sorted(
        report.gate_fail_counts.items(), key=lambda t: -t[1]
    )[:5]:
        pct = count / max(report.n_questions, 1) * 100
        print(f"  {gate}: {count} ({pct:.1f}%)")
    return 0


def _cmd_calibrate(args: argparse.Namespace) -> int:
    out_dir = Path(args.out) if args.out else None
    report = run_deterministic(
        subject=args.subject,
        sample_size=args.sample,
        seed=args.seed,
        out_dir=out_dir,
    )
    print(
        f"\nCalibrated {report.n_questions} {args.subject} questions "
        f"(stratified random, seed {args.seed}):"
    )
    print(
        f"  {report.n_keep} KEEP ({report.n_keep / max(report.n_questions,1) * 100:.0f}%), "
        f"{report.n_repair} REPAIR ({report.n_repair / max(report.n_questions,1) * 100:.0f}%), "
        f"{report.n_discard} DISCARD ({report.n_discard / max(report.n_questions,1) * 100:.0f}%)"
    )
    return 0


def _cmd_specs(args: argparse.Namespace) -> int:
    mv = specs.load_moral_vision()
    print(f"moral_vision.md:     v{mv.version}  {mv.date}  sha={mv.sha256[:12]}")
    for subj in specs.available_subjects():
        s = specs.load_subject_spec(subj)
        print(f"  subjects/{subj}.md: v{s.version}  style={s.style_verdict}  sha={s.sha256[:12]}")
    taxonomy = specs.load_taxonomy()
    print()
    for subj, tax in taxonomy.items():
        print(
            f"taxonomy[{subj}]: target={tax.total_target}, actual={tax.actual_total}, "
            f"cells={len(tax.cells)}, by_tier={tax.by_tier}"
        )
    return 0


def _cmd_patterns(args: argparse.Namespace) -> int:
    print("Anti-rote regex patterns (from moral_vision.md §6):")
    print()
    for i, src in enumerate(ANTI_ROTE_PATTERN_SOURCES, 1):
        print(f"  {i:2d}. {src}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tools.quizgen", description="Philosopher's Quest quiz pipeline.")
    sub = p.add_subparsers(dest="cmd", required=True)

    pv = sub.add_parser("validate", help="Run deterministic gates over a subject's full bank")
    pv.add_argument("--subject", required=True, help="Subject name (e.g. philosophy)")
    pv.add_argument("--out", default=None, help="Output directory (default: timestamped)")
    pv.set_defaults(func=_cmd_validate)

    pc = sub.add_parser("calibrate", help="Run deterministic gates over a stratified random sample")
    pc.add_argument("--subject", required=True)
    pc.add_argument("--sample", type=int, default=100, help="Total sample size (split evenly across tiers)")
    pc.add_argument("--seed", type=int, default=20260511, help="Random seed (for reproducibility)")
    pc.add_argument("--out", default=None)
    pc.set_defaults(func=_cmd_calibrate)

    ps = sub.add_parser("specs", help="Print spec doc summary (versions, hashes, taxonomy totals)")
    ps.set_defaults(func=_cmd_specs)

    pp = sub.add_parser("patterns", help="Print the canonical anti-rote regex list")
    pp.set_defaults(func=_cmd_patterns)

    pcur = sub.add_parser("curate", help="Assemble approved pilot bank from queue manifests")
    pcur.set_defaults(func=_cmd_curate)

    return p


def _cmd_curate(args: argparse.Namespace) -> int:
    summary = assemble_pilot_bank()
    print(f"\nWrote pilot bank: {summary['out_path']}")
    print(f"  count: {summary['count']}")
    print(f"  by tier:   {summary['by_tier']}")
    print(f"  by origin: {summary['by_origin']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
