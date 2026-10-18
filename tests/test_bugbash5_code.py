"""Bug bash 5 (2026-10-17): code quality. CODE-08 (dead or duplicated code)
and CODE-09 (swallowed errors)."""
import os
import re
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))


def _src(name):
    with open(os.path.join(ROOT, 'src', name), encoding='utf-8') as f:
        return f.read()


# ---------------------------------------------------------------- CODE-08
def test_the_cow_level_is_defined_once():
    import boss_levels
    import escort_system
    import game_road
    import road
    import setne_tomb
    for mod in (escort_system, game_road, road, setne_tomb):
        assert mod.COW_LEVEL is boss_levels.COW_LEVEL
    defs = [n for n in os.listdir(os.path.join(ROOT, 'src')) if n.endswith('.py')
            and re.search(r'^COW_LEVEL\s*=', _src(n), re.M)]
    assert defs == ['boss_levels.py']


def test_a_road_band_is_a_karma_block():
    import deeds
    import road
    assert road.band_of is deeds.karma_block
    assert [road.band_of(f) for f in (1, 10, 11, 95, 100)] == [1, 1, 2, 10, 10]


def test_dead_names_are_gone_and_where_is_public():
    import deeds
    import karma
    assert not hasattr(karma, 'current_block')
    assert not hasattr(deeds, 'OATH_STATUSES')
    assert 'karma._where' not in _src('game_encounters.py')


# ---------------------------------------------------------------- CODE-09
def _game(**kw):
    g = types.SimpleNamespace(dungeon_level=5, turn_count=7, karma=0,
                              player=types.SimpleNamespace(deepest_floor_reached=5))
    g.__dict__.update(kw)
    return g


def _logged(monkeypatch):
    import game_log
    seen = []
    monkeypatch.setattr(game_log, 'log_error', lambda msg, *a, **k: seen.append(msg))
    return seen


def test_a_bad_deed_id_is_logged_not_silently_dropped(monkeypatch):
    import deeds
    seen = _logged(monkeypatch)
    assert deeds.note(_game(), 'Bad.Id', source='x') is None
    assert any("'Bad.Id'" in m for m in seen)
    # A good id still records and logs nothing.
    seen.clear()
    assert deeds.note(_game(), 'met.wynn', source='x') is not None
    assert seen == []


class _NoWrite:
    """A game whose karma cannot be written."""
    dungeon_level = 5
    turn_count = 7
    player = types.SimpleNamespace(deepest_floor_reached=5)

    @property
    def karma(self):
        return 0

    @karma.setter
    def karma(self, v):
        raise RuntimeError('read-only')


def test_a_failed_karma_write_is_logged_and_not_ledgered_as_applied(monkeypatch):
    import karma
    seen = _logged(monkeypatch)
    g = _NoWrite()
    assert karma.adjust(g, -2, kind='cruelty', source='test') == 0
    entry = g._deeds['karma']['ledger'][-1]
    assert entry['applied'] == 0 and entry['requested'] == -2
    assert any('karma.adjust' in m for m in seen)


def test_a_failed_soul_line_is_logged(monkeypatch):
    import chronicle
    import karma
    seen = _logged(monkeypatch)

    def boom(*a, **k):
        raise RuntimeError('x')
    monkeypatch.setattr(chronicle, 'chron', boom)
    karma._soul_line(_game(), {'id': 'r1', 'chronicle': 'A line.'})
    assert any("'r1'" in m for m in seen)
