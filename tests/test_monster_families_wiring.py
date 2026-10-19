"""Monster family knowledge: the wiring audit's regressions (2026-10-19).

Each test here pins a seam the independent wiring audit found open:
  * one study knows every corpse of the kind, wherever it lay (a corpse left
    on a floor before the study, or kept in a sack, used to ask again);
  * a corpse carried in the pack can be studied from the identify menu (it
    was listed nowhere);
  * the Philosopher's Stone leaves corpses to their own study (it marked
    them known without the study counting, and then they could never be
    studied);
  * calm-on-arrival never touches, or announces, a concealed creature;
  * the Black Knight never yields, and is never turned, calmed, charmed or
    executed (he never leaves his bridge);
  * a kind with no family still follows the one-study rule for its corpses;
  * several unlocks in one popup each stand under their own heading;
  * a circle's "from anything" save boon counts against an effect with no
    monster behind it (a bad meal's confusion or fear);
  * an Omnisight read that raises a tier popup still costs its turn;
  * the QA key never names a concealed creature's family;
  * text: the tier-one Journal line never says one study is enough, the
    Bones ghost has a real name on the Families page, and a maxed family
    reads cleanly on an unstudied corpse;
  * a whole Game saved and loaded through save_system keeps the studied
    kinds, the tiers told, the grants and the circles, and an old save
    (no family fields) loads with nothing to announce.

Late-game content: logic tests, not play-tests (CLAUDE.md).
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import family_edges  # noqa: E402
import family_lore  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _game(name='__test_family_wiring__'):
    from main import Game
    from game_states import STATE_PLAYER
    random.seed(7)
    g = Game(_screen(), player_name=name)
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _plain(fid, n=None):
    out = [k for k in family_lore.members(fid) if k in MONS and not family_lore.is_keystone(k)]
    return out if n is None else out[:n]


def _corpse(kind, x, y):
    from items import Corpse
    return Corpse(MONS[kind]['name'], kind, x, y, harvest_tier=1,
                  monster_def={'tags': MONS[kind]['tags']})


class _Right:
    success = True


def _answer_right(g):
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](_Right())


def _mon(kind, x=5, y=5):
    from monster import Monster
    return Monster({**MONS[kind], 'id': kind}, x, y)


# ---------------------------------------------------------------------------
# Every path that identifies a corpse or a kind
# ---------------------------------------------------------------------------
def test_one_study_knows_every_corpse_of_the_kind_wherever_it_lay():
    from game_states import STATE_LORE
    from items import corpse_is_known
    g = _game()
    px, py = g.player.x, g.player.y
    first = _corpse('skeleton', px, py)
    g.ground_items.append(first)
    _answer_right(g)
    g._start_corpse_identify(first, after_advance_turn=False)
    assert 'skeleton' in g.player.studied_monster_ids
    # A skeleton corpse that missed the study's sweep: left on another floor,
    # in a sack, or dropped by a thief. Its own id_level still says 0.
    stale = _corpse('skeleton', px, py)
    assert stale.id_level == 0 and corpse_is_known(g.player, stale)
    g.ground_items.append(stale)
    g.state = 'player'
    g._open_identify_menu()
    listed = [i for i, _g, _c in (getattr(g, 'identify_menu_items', None) or [])]
    assert stale not in listed                       # nothing left to learn
    asked = []
    g.quiz_engine.start_quiz = lambda **kw: asked.append(kw)
    g._start_corpse_identify(stale, after_advance_turn=False)
    assert not asked                                 # never asks again
    assert g.state == STATE_LORE and stale.id_level == 5
    assert g._lore_direct_id_level(_corpse('skeleton', 0, 0)) == 5   # its page shows all


def test_a_kind_thoth_only_opened_still_asks_and_still_counts():
    from items import corpse_is_known
    g = _game()
    g.player.lore_known_monster_ids.add('zombie')
    c = _corpse('zombie', g.player.x, g.player.y)
    assert not corpse_is_known(g.player, c)
    g.ground_items.append(c)
    _answer_right(g)
    g._start_corpse_identify(c, after_advance_turn=False)
    assert 'zombie' in g.player.studied_monster_ids


def test_a_kind_with_no_family_is_still_known_after_one_study():
    """The unicorn, the secret cow and encounter NPCs have no family, so a
    study never records them as studied (record_study); their corpses still
    follow the one-study rule through the page it opened, as before."""
    from items import Corpse, corpse_is_known
    g = _game()
    first = Corpse('Ethereal Unicorn', 'ethereal_unicorn', g.player.x, g.player.y)
    g.ground_items.append(first)
    _answer_right(g)
    g._start_corpse_identify(first, after_advance_turn=False)
    assert 'ethereal_unicorn' not in g.player.studied_monster_ids
    later = Corpse('Ethereal Unicorn', 'ethereal_unicorn', 0, 0)
    assert corpse_is_known(g.player, later)
    # ...but a family kind only opened by the Book of Thoth still asks.
    g.player.lore_known_monster_ids.add('ghoul')
    assert not corpse_is_known(g.player, Corpse('Ghoul', 'ghoul', 0, 0))


def test_a_carried_corpse_is_studied_from_the_identify_menu():
    import pygame as pg
    g = _game()
    carried = _corpse('ghoul', g.player.x, g.player.y)
    g.player.inventory.append(carried)
    g._open_identify_menu()
    entries = getattr(g, 'identify_menu_items', None) or []
    row = next((e for e in entries if e[0] is carried), None)
    assert row is not None, entries                  # it used to be listed nowhere
    assert row[1] is False and row[2] is True        # in the pack, a corpse
    g._identify_sel = entries.index(row)
    _answer_right(g)
    g._identify_menu_input(pg.K_RETURN)
    assert 'ghoul' in g.player.studied_monster_ids
    assert carried.id_level == 5


def test_the_philosophers_stone_leaves_corpses_to_their_own_study():
    from items import corpse_is_known
    g = _game()
    on_floor = _corpse('ghoul', g.player.x, g.player.y)
    carried = _corpse('zombie', g.player.x, g.player.y)
    g.ground_items.append(on_floor)
    g.player.inventory.append(carried)
    g._auto_identify_all()
    assert not corpse_is_known(g.player, on_floor)
    assert not corpse_is_known(g.player, carried)
    assert 'corpse_ghoul' not in g.player.known_item_ids


def test_an_omnisight_read_that_raises_a_tier_popup_still_costs_its_turn():
    from game_states import STATE_STORY_POPUP
    from items import make_item_by_id
    g = _game()
    fid = 'oozes'
    kinds = _plain(fid)
    need = family_lore.thresholds(fid)[2]
    g.player.studied_monster_ids.update(kinds[:need - 1])
    family_lore.mark_all_told(g.player)
    g.player.inventory.append(_corpse(kinds[need - 1], g.player.x, g.player.y))
    scroll = make_item_by_id('scroll', 'scroll_of_omnisight')
    assert scroll is not None
    scroll.buc = 'uncursed'
    g.player.inventory.append(scroll)
    _answer_right(g)
    t0 = g.turn_count
    g._read_scroll(scroll)
    assert family_lore.tier(g.player, fid) == 3
    assert g.state == STATE_STORY_POPUP and g.popup_data.get('_family')
    assert g.turn_count == t0 + 1                    # the read was free before


# ---------------------------------------------------------------------------
# Hidden things never leak
# ---------------------------------------------------------------------------
def test_calm_on_arrival_never_touches_a_concealed_creature():
    import unseen
    from player import Player
    p = Player()
    p.x, p.y = 10, 10
    p.studied_monster_ids.update(_plain('great_beasts'))
    assert family_edges.calm_chance(p, 'great_beasts')[0] > 0
    lurker = _mon(_plain('great_beasts')[0], 12, 12)
    lurker.ai_pattern, lurker._aware = 'ambush', False
    assert unseen.concealed(lurker, p)

    class _Always:
        @staticmethod
        def random():
            return 0.0
    assert family_edges.calm_arrivals(p, [lurker], rng=_Always()) == []
    assert not lurker.status_effects.get('charmed')
    lurker._aware = True                             # sprung: now it can be calmed
    assert family_edges.calm_arrivals(p, [lurker], rng=_Always())
    assert lurker.status_effects.get('charmed')


def test_the_qa_key_never_names_a_concealed_creatures_family():
    g = _game()
    g.player.qa_tools = True
    hidden = _mon('gilded_mimic', g.player.x + 1, g.player.y)    # a disguised mimic
    hidden._aware = False
    g.monsters = [hidden]
    g.visible = {(hidden.x, hidden.y), (g.player.x, g.player.y)}
    g._qa_family_tier()
    texts = [str(e[0]) for e in g.msg_log.entries]
    assert not any('[QA]' in t and 'Aberrations' in t and '...' not in t for t in texts)
    assert len(family_lore.tiers(g.player)) == 22    # no creature in sight: every family


# ---------------------------------------------------------------------------
# The named-foe rail
# ---------------------------------------------------------------------------
def test_the_black_knight_never_yields_and_is_never_turned_or_calmed():
    """He is a Mortal Foe but no charm, fear or instant kill moves him off
    his bridge (game_magic._is_big_foe), and he never yields. Yield! used to
    fire on him at chain 8 below half health: "throws down his purse and
    runs" while he stood there, his gold dropped early."""
    from black_knight import BlackKnight, monster_defn
    from player import Player
    p = Player()
    p.x, p.y = 10, 10
    p.studied_monster_ids.update(_plain('mortals'))
    assert family_lore.tier(p, 'mortals') == 5
    k = BlackKnight(monster_defn(), 11, 10)
    assert family_lore.family_of(k) == 'mortals'
    k.__dict__['_bk_hp'] = max(1, k.max_hp // 3)            # below half health
    assert family_edges.surrender(p, k, 30) is None
    out = family_edges.after_blow(p, k, 30, 5, monsters=[k], visible={(11, 10)})
    assert out['surrendered'] is None and not k.status_effects.get('feared')
    params = {'trigger': 'on_hit', 'turns': 5}
    assert family_edges.turn_members(p, 'mortals', params, [k], {(11, 10)}) == 0
    assert family_edges.charm_on_hit(p, k, 30) is None
    assert family_edges.execute(p, k, 30) is None
    # An ordinary Mortal Foe still yields.
    bandit = _mon('bandit_thug', 11, 11)
    bandit.hp = max(1, bandit.max_hp // 3)
    assert family_edges.surrender(p, bandit, 30) is not None


# ---------------------------------------------------------------------------
# Circles
# ---------------------------------------------------------------------------
def test_unbent_mind_counts_against_an_effect_with_no_monster_behind_it():
    import status_effects
    from player import Player
    p = Player()
    for fid in ('demons', 'fair_folk', 'aberrations'):
        p.studied_monster_ids.update(_plain(fid, family_lore.thresholds(fid)[2]))
    assert family_lore.circle_complete(p, 'hellward_gate')
    amount = family_lore.circles()['hellward_gate']['boon']['params']['amount']
    # A bad meal's confusion or fear has no source (food_system): the boon
    # says "from anything", so it counts there too.
    assert status_effects._family_ward(p, None, 'confused', False)[0] == amount
    assert status_effects._family_ward(p, None, 'feared', False)[0] == amount
    assert status_effects._family_ward(p, None, 'paralyzed', False)[0] == 0
    fresh = Player()
    assert status_effects._family_ward(fresh, None, 'confused', False) == (0, 1.0)


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------
def test_the_tier_one_journal_line_never_says_one_study_is_enough():
    first = family_lore.data()['tier_chronicle'][0]
    assert min(family_lore.thresholds(f)[0] for f in family_lore.families()) >= 2
    assert 'one of {kin}' not in first


def test_the_bones_ghost_has_a_real_name_on_the_families_page():
    g = _game()
    assert g._monster_display_name('player_ghost') == 'Ghost of a Fallen Hero'
    g.player.known_monster_ids.add('player_ghost')
    texts = [str(t) for t, *_ in g._family_page_lines('ghosts')]
    assert not any('Player Ghost' in t or 'player ghost' in t for t in texts)


def test_an_unstudied_corpse_of_a_maxed_family_reads_cleanly():
    g = _game()
    kinds = _plain('oozes')
    g.player.studied_monster_ids.update(kinds[:family_lore.thresholds('oozes')[-1]])
    assert family_lore.progress(g.player, 'oozes')['next'] is None
    unstudied = next(k for k in kinds if k not in g.player.studied_monster_ids)
    identity, _mech, _lore = g._lore_corpse_lines(_corpse(unstudied, 0, 0), 0)
    texts = [str(t) for t, *_ in identity]
    assert any(t.startswith('Not yet studied.') and 'every tier learned' in t for t in texts)
    assert not any('Every tier learned' in t and t.startswith('Not yet studied:') for t in texts)


# ---------------------------------------------------------------------------
# The UI: several unlocks at once
# ---------------------------------------------------------------------------
def test_several_unlocks_in_one_popup_each_stand_under_their_own_heading():
    """One study of Medusa (a legend: two kinds) crosses two gorgon tiers and
    completes the Hero's Road. The popup joins touching lines into one
    paragraph, so every heading after the first needs a blank line on both
    sides; it used to read "HUNTER OF THE GORGONS AND BASILISKS You have
    learned how..." and "CIRCLE COMPLETE The Hero's Road"."""
    from game_states import STATE_LORE, STATE_STORY_POPUP
    g = _game()
    for fid, t in (('legend', 3), ('giants', 3), ('gorgons', 2)):
        g.player.studied_monster_ids.update(_plain(fid, family_lore.thresholds(fid)[t - 1]))
    family_lore.mark_all_told(g.player)
    g.state = STATE_LORE
    g._family_study('medusa_gorgon')
    assert g.state == STATE_STORY_POPUP and g.popup_next_state == STATE_LORE
    lines = g.popup_data['lines']
    for head in ('Hunter of the Gorgons and Basilisks', "Circle Complete: The Hero's Road"):
        assert head in lines, lines
        i = lines.index(head)
        assert lines[i - 1] == '' and lines[i + 1] == '', (head, lines[i - 1:i + 2])
    assert not any(ln.isupper() for ln in lines if len(ln) > 3)     # no shouting headings


# ---------------------------------------------------------------------------
# Saves, through the real save system
# ---------------------------------------------------------------------------
def _roundtrip(g, name, tmp_path, monkeypatch):
    import save_system
    from main import Game
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    save_system.settle_unfinished_actions(g)
    assert save_system.save_game(g)
    g2 = Game(_screen(), player_name=name)
    g2.load_state(save_system.load_game(name))
    return g2


def test_a_saved_and_loaded_game_keeps_its_family_knowledge(tmp_path, monkeypatch):
    from game_states import STATE_PLAYER
    name = '__test_family_save__'
    g = _game(name)
    for fid in ('restless_dead', 'ghosts', 'vampires_liches'):
        g.player.studied_monster_ids.update(_plain(fid, family_lore.thresholds(fid)[2]))
    g.player.family_lore_grants['legend'] = 2
    g._family_news()
    g.state = STATE_PLAYER
    before = (set(g.player.studied_monster_ids), dict(g.player.family_tiers_told),
              dict(g.player.family_lore_grants), family_lore.complete_circles(g.player),
              family_lore.tiers(g.player))
    assert 'grave_watch' in before[3]
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    after = (set(g2.player.studied_monster_ids), dict(g2.player.family_tiers_told),
             dict(g2.player.family_lore_grants), family_lore.complete_circles(g2.player),
             family_lore.tiers(g2.player))
    assert after == before
    assert family_lore.news(g2.player) == []          # nothing announced twice


def test_an_old_save_catches_up_with_nothing_to_announce(tmp_path, monkeypatch):
    name = '__test_family_old_save__'
    g = _game(name)
    kinds = _plain('vermin', family_lore.thresholds('vermin')[3])
    g.player.lore_known_monster_ids.update(kinds)
    for k in ('studied_monster_ids', 'family_tiers_told', 'family_lore_grants'):
        g.player.__dict__.pop(k, None)               # a save from before families
    g2 = _roundtrip(g, name, tmp_path, monkeypatch)
    assert g2.player.studied_monster_ids == set(kinds)
    assert family_lore.tier(g2.player, 'vermin') == 4
    assert family_lore.news(g2.player) == []
    assert not (getattr(g2, 'popup_data', None) or {}).get('_family')
