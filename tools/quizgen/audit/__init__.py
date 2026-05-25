"""Reusable rewrite-audit infrastructure (Pass 1 / Pass 2 / Pass 3).

See ``tools/quizgen/RUNBOOK.md`` for the documented process.

Public modules:
    validate              — universal gate-validation harness
    apply_pass1           — Pass-1 (audit) applier with per-tier retry
    apply_pass2_dedup     — Pass-2 (dedup-by-diversification) applier
    apply_pass3_residuals — Pass-3 (formal cleanup) applier
    build_audit_candidates    — scan for Wonder-Pattern audit candidates
    build_collision_groups    — find same-answer collision groups
    build_residuals_report    — catalog every gate-failing question
    slice_collisions      — shard collision groups by size for parallel agents
"""
