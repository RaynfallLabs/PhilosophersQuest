"""Bug bash 2026-10-16 (F5), CQ-25 / CQ-26: stale comments and docs."""
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


# ── CQ-25 / CQ-26 ───────────────────────────────────────────────────────────

_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))


def test_project_docs_name_only_source_files_that_exist():
    """CLAUDE.md and AGENTS.md named src/help_screens.py (gone; the help
    screen is game_render._draw_help_screen)."""
    import re
    for doc in ('CLAUDE.md', 'AGENTS.md'):
        with open(os.path.join(_ROOT, doc), encoding='utf-8') as f:
            text = f.read()
        for rel in set(re.findall(r'src/[\w/]+\.py', text)):
            assert os.path.exists(os.path.join(_ROOT, rel)), (doc, rel)
        assert '32×32' not in text            # map tiles are 40 px, art 64 px
        assert '(e.g., cooking)' not in text  # cooking is one threshold question


def test_stale_chain_and_escalator_comments_are_gone():
    """Lockpick v3 and cook v3 are one question each; these comments still
    described the chain / escalator versions."""
    def read(*parts):
        with open(os.path.join(_ROOT, *parts), encoding='utf-8') as f:
            return f.read()
    assert 'CHAIN is the new dial' not in read('src', 'container_system.py')
    assert 'chain-mode Economics quiz' not in read('src', 'game_states.py')
    assert 'new chests use chain mode' not in read('src', 'items.py')
    assert 'cooking escalator' not in read('src', 'effects', 'chain_aura.py')
    assert 'recipe_class for cook' not in read('src', 'food_system.py')
