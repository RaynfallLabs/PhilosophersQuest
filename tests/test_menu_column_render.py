"""Guard: any column-based table render in src/game_render.py must call
truncate_label on every cell before rendering. The Kit-items / Kit-spells
bug pattern of 2026-05-28 was the second time we shipped this regression
(spells did it right, items did it wrong, identical code shape). This
test source-scans game_render.py for the antipattern so the lesson
doesn't have to be relearned.

Pattern matched:
  - A function uses `fit_columns(...)` (signal: this is a tabular layout)
  - Within that function, every `.render(text, True, ...)` call that
    blits a per-cell text surface must be preceded by a `truncate_label`
    call (or the literal name `truncated`/`clipped`/`label_text` derived
    from one) in the same function body.

This is a heuristic scan, not a perfect AST analysis. It exists to catch
the specific failure mode of forgetting the truncate seam in a future
table-style render.
"""
import os
import re

import pytest

SRC = os.path.join(os.path.dirname(__file__), '..', 'src', 'game_render.py')


def _split_top_level_methods(text: str):
    """Yield (method_name, body_text) for every `    def NAME(self, ...)`
    block in a class. Brittle — assumes 4-space indented methods in one
    class — but game_render.py is exactly that shape today."""
    lines = text.splitlines()
    cur_name = None
    cur_lines: list[str] = []
    for line in lines:
        m = re.match(r'^    def (_?\w+)\s*\(', line)
        if m:
            if cur_name is not None:
                yield cur_name, '\n'.join(cur_lines)
            cur_name = m.group(1)
            cur_lines = [line]
        elif cur_name is not None:
            cur_lines.append(line)
    if cur_name is not None:
        yield cur_name, '\n'.join(cur_lines)


def test_every_tabular_render_uses_truncate_label():
    """If a method calls fit_columns(), every text render inside it must
    be preceded somewhere in the method body by truncate_label."""
    with open(SRC, encoding='utf-8') as f:
        src = f.read()

    offenders = []
    for name, body in _split_top_level_methods(src):
        if 'fit_columns' not in body:
            continue
        # Pure layout helpers that only RETURN widths (no per-cell text
        # rendering) are fine — they delegate the render seam to their caller.
        if '.render(' not in body:
            continue
        if 'truncate_label' not in body:
            offenders.append(name)

    assert not offenders, (
        f"Methods in game_render.py that build column layouts via "
        f"fit_columns(...) but never call truncate_label(...) — text will "
        f"bleed into adjacent columns. Offenders: {offenders}. "
        f"Fix: every per-cell .render(...) needs a "
        f"`text = truncate_label(text, cell_w, font)` before it. See "
        f"_kit_draw_spells for the canonical pattern."
    )
