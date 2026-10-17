"""P2 and P13 (DEEDS_KARMA_DESIGN 1, 8.1): karma changes only through
karma.adjust, and the renderer never reads an encounter's stakes."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'src')

# `(?!=)` so `self.karma == -10` is not a write.
_WRITE = re.compile(r'\.karma\s*[+\-]?=(?!=)')
_SETATTR = re.compile(r"setattr\([^,]+,\s*['\"]karma['\"]")


def test_single_karma_entry_point():
    hits = []
    for name in sorted(os.listdir(SRC)):
        if not name.endswith('.py') or name == 'karma.py':
            continue
        with open(os.path.join(SRC, name), encoding='utf-8') as f:
            for n, line in enumerate(f, 1):
                code = line.split('#', 1)[0]
                if _WRITE.search(code) or _SETATTR.search(code):
                    # The one exemption: restoring the saved value on load.
                    if name == 'main.py' and "self.karma = state.get('karma', 0)" in code:
                        continue
                    hits.append(f'{name}:{n}: {line.strip()}')
    assert not hits, 'karma written outside karma.adjust:\n' + '\n'.join(hits)


def test_the_grep_itself_works():
    assert _WRITE.search('self.karma = 3')
    assert _WRITE.search('_g.karma += 1')
    assert not _WRITE.search('if self.karma == -10:')
    assert not _WRITE.search('self.karma >= 8')


def test_renderer_never_reads_stakes():
    for name in ('game_render.py', 'fantasy_ui.py'):
        with open(os.path.join(SRC, name), encoding='utf-8') as f:
            text = f.read()
        assert not re.search(r"""['"]stakes['"]""", text), name
