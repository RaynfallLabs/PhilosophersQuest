"""The old monster-rewriting tools may not write any more (2026-11-19).

Brandon, 2026-11-19, the third time: "Your fix SUCKS AGAIN, because you
started using smoothing multipliers to hit a target ... NEVER DO THIS ...
Fix the data at the source." The monster lore pass of that day gave every
ordinary monster its own numbers from its lore (tools/balance/
apply_lore_pass.py, docs/design/MONSTER_LORE_PASS_2026_11_19.md). These older tools
rewrite monsters by a formula of the floor or of HP (re-seat by HP, scale by
a depth schedule, stats from a curve): run with their write flag they would
iron the monsters flat again. Each calls refuse() first: it lets a dry run
through and stops a write.
"""
from __future__ import annotations

import sys

WRITE_FLAGS = ('--write', '--i-know', '--apply')


def refuse(tool: str, argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if any(f in argv for f in WRITE_FLAGS):
        sys.stderr.write(
            f"{tool}: will not write. It rewrites monsters by a formula of floor or HP, and the "
            "2026-11-19 lore pass gave each monster its own numbers from its lore (Brandon: no "
            "smoothing multipliers; fix the data at the source). Edit monsters one by one, by lore, "
            "and check them with tools/balance/apply_lore_pass.py and monster_bands.py.\n")
        raise SystemExit(2)
