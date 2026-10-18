"""Bug bash 5 (2026-10-17): docs. CODE-05, CODE-06."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------- CODE-05
def test_claude_md_lists_every_src_module():
    text = _read('CLAUDE.md')
    section = text.split('## Project Structure', 1)[1].split('\n## ', 1)[0]
    missing = []
    for name in sorted(os.listdir(os.path.join(ROOT, 'src'))):
        if name.endswith('.py') and name != '__init__.py':
            if not re.search(r'\b' + re.escape(name[:-3]) + r'\b', section):
                missing.append(name)
    assert missing == []


# ---------------------------------------------------------------- CODE-06
def test_monster_keys_and_new_modules_are_documented():
    doc = _read('docs', 'systems', 'monsters.md') + _read('docs', 'systems', 'data_schemas.md')
    for key in ('after_theft', 'disguise', 'fearless', 'kill_chronicle', 'pack_size',
                'proper_noun', 'quarrelsome', 'quarrels_when_struck_by_thrown', 'splits',
                'stationary', 'weighs_heart', 'bonus_vs', 'steal_chance'):
        assert f'`{key}`' in doc, key
    for module in ('theft.py', 'splitting.py', 'false_stairs.py', 'black_knight.py'):
        assert module in doc, module
