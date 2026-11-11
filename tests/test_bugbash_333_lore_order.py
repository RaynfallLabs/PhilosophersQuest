"""3.3.3 play (Brandon): "our monster lore messages and/or powers ... seem to
be messed up ... some things happen too early? overlap? doesn't make enough
sense". The lore audit's fixes, each pinned through a real Game:

  * what a blow set off (its family techniques, the weakness it met) is said
    before "X is slain!" and its loot (Game._say_action_lines);
  * Forewarned once a floor per family; the combined line lists with commas;
  * a ward's line only when the save held; Garlic and Ash's bite line only
    for the bite;
  * no double weakness (Bonebreaker and "super effective" on one blow);
  * Harpe's and the executes' lines only when it happens; a named foe's
    harder blow has its own line; Cold Iron and Silvered only with their metal;
  * Yield! after the blow, said once, and no "his";
  * Perseus' Shield said once; Lay the Ghost's blessing named as holy;
  * the Ring of Invisibility's veil lines;
  * a lurker's reveal before the blow, never for a dead one;
  * the world's turn says its own hits; the queue is emptied on a new floor;
  * the keen-senses check and the family techniques that show lurkers;
  * hints after the strike line, and no "skates off its scales" when they
    were passed;
  * the lower list: the clock's lines before the quiz, Fire and Dawn only
    on regenerators, Opposing Element only for an element, Second Sight not
    when the hero sees invisible, the on-sight fear never on sleepers.

And Brandon's rulings on the open items:
  * an execute that by lore leaves no body leaves no corpse (banish as the
    Banishment spell: no loot either);
  * the popups from play, one at a time, once play is calm (game_popups.PopupMixin);
  * a creature with no blood never bleeds (data/monster_blood.json).
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import affinity  # noqa: E402
import family_edges  # noqa: E402
import family_lore  # noqa: E402
from quiz_engine import QuizResult  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import quiz_engine
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setattr(quiz_engine, '_HISTORY_DIR_OVERRIDE', str(tmp_path))
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(11)
    g = Game(pygame.display.set_mode((1, 1)), player_name='__test_lore_order__')
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    g.ground_items[:] = []
    g.msg_log.clear()
    affinity.drain()
    family_edges.drain(g.player)
    _open_ground(g)
    yield g
    affinity.drain()


def _open_ground(g):
    """The hero on a tile with open floor three tiles east of him."""
    d = g.dungeon
    for y in range(d.height):
        for x in range(d.width):
            if all(d.is_walkable(x + i, y) for i in range(0, 4)):
                g.player.x, g.player.y = x, y
                g._refresh_fov()
                return


def _grant(g, **tiers):
    g.player.family_lore_grants = dict(tiers)
    family_lore.mark_all_told(g.player)


def _mon(g, kind, dx=1, dy=0, hp=None, max_hp=None, still=True):
    from monster import Monster
    m = Monster({**MONS[kind], 'id': kind}, g.player.x + dx, g.player.y + dy)
    if max_hp is not None:
        m.max_hp = max_hp
    if hp is not None:
        m.hp = hp
    if still:
        m.status_effects['paralyzed'] = 50          # its own turn says nothing
    g.monsters.append(m)
    g._refresh_fov()
    return m


def _answer(g, score, seen=None):
    def start_quiz(**kw):
        if seen is not None:
            seen.append([t for t, _ in g.msg_log.entries])
        kw['callback'](QuizResult(success=True, score=score, correct=score, asked=score))
    g.quiz_engine.start_quiz = start_quiz


def _log(g):
    return [str(t) for t, _ in g.msg_log.entries]


def _at(lines, needle):
    """Index of the first line holding `needle` (-1 when none)."""
    return next((i for i, t in enumerate(lines) if needle in t), -1)


def _weapon(template, material):
    from items import instantiate_weapon
    return instantiate_weapon(template, material)


def _affinity_pool(kind):
    data = affinity.lines()
    return data[kind] + data[kind + '_many']


def _is_affinity(line, kind):
    """The line is one of the pool's (with any names and words filled in)."""
    import re
    for s in _affinity_pool(kind):
        pat = re.escape(s)
        for f in ('{name}', '{the}', '{word}', '{word_cap}'):
            pat = pat.replace(re.escape(f), '.+')
        if re.fullmatch(pat, line):
            return True
    return False


# ---------------------------------------------------------------------------
# 1, 4: a kill's lines come after what the blow set off
# ---------------------------------------------------------------------------
def test_the_weakness_line_comes_before_the_slain_line_and_the_loot(game):
    game.player.weapon = None                       # a fist crushes: a skeleton's weakness
    m = _mon(game, 'skeleton', hp=1)
    m.treasure = {'gold': [6, 6]}
    _answer(game, 2)
    game._start_combat(m)
    log = _log(game)
    weak = next(i for i, t in enumerate(log) if _is_affinity(t, 'weak'))
    assert _at(log, 'Chain x2!') < weak < _at(log, 'is slain!')


def test_a_technique_on_a_killing_blow_comes_before_the_slain_line(game):
    _grant(game, vampires_liches=5)
    game.player.weapon = _weapon('longsword', 'steel')
    m = _mon(game, 'vampire_spawn', max_hp=10000, hp=600)
    m.treasure = {'gold': [30, 30]}
    _answer(game, 18)
    game._start_combat(m)
    log = _log(game)
    stake = _at(log, 'Stake Through the Heart!')
    assert stake >= 0 and not m.alive
    assert _at(log, 'Chain x18!') < stake < _at(log, 'is slain!')


# ---------------------------------------------------------------------------
# 2, 15: Forewarned
# ---------------------------------------------------------------------------
def test_forewarned_is_said_once_a_floor_and_a_family_that_comes_later_once(game):
    _grant(game, goblinkin=2, vermin=2)
    _mon(game, 'goblin', dx=3)
    for _ in range(3):
        game._family_arrival(first_visit=False)
    log = _log(game)
    assert sum('goblin warband' in t for t in log) == 1
    _mon(game, 'giant_rat', dx=2)                   # vermin wander in
    game._family_arrival(first_visit=False)
    game._family_arrival(first_visit=False)
    log = _log(game)
    assert sum('goblin warband' in t for t in log) == 1
    assert sum('vermin and spiders creep' in t for t in log) == 1
    # Another floor is told again.
    game.dungeon_level += 1
    game._family_arrival(first_visit=True)
    assert sum('goblin warband' in t for t in _log(game)) == 2


def test_the_combined_forewarned_line_lists_with_commas_only():
    from monster import Monster
    from player import Player
    p = Player()
    for f in ('goblinkin', 'vermin', 'giants', 'restless_dead', 'ghosts'):
        p.family_lore_grants[f] = 2
    ms = [Monster({**MONS[k], 'id': k}, 1, 1) for k in ('goblin', 'giant_rat', 'troll', 'skeleton', 'wraith')]
    lines = family_lore.arrival_lines(p, ms, concealed=lambda m: False, is_ally=lambda m: False)
    assert lines[-1] == 'You sense more on this floor: Giants and Trolls, Restless Dead, Ghosts.'


# ---------------------------------------------------------------------------
# 3: a ward's line only when the save held
# ---------------------------------------------------------------------------
def test_a_ward_line_only_when_the_save_held(game):
    from status_effects import apply_debuff_with_save
    _grant(game, restless_dead=3)
    ghoul = _mon(game, 'ghoul')
    applied, msg = apply_debuff_with_save(game.player, 'paralyzed', 3, 99, source=ghoul)
    assert applied and msg == 'The paralysis takes hold!'
    assert family_edges.drain(game.player) == []          # no "keeps the grave's grip off you"
    game.player.status_effects.pop('paralyzed', None)
    other = _mon(game, 'ghoul', dx=2)
    applied, _msg = apply_debuff_with_save(game.player, 'paralyzed', 3, -99, source=other)
    assert not applied
    assert any(t.startswith('Grave-Salt:') for t in family_edges.drain(game.player))


def test_a_drain_ward_line_only_when_the_drain_was_kept_off(game, monkeypatch):
    import monster as monster_mod
    _grant(game, restless_dead=3)
    game.player.CON = 16
    w = _mon(game, 'wight')
    monkeypatch.setattr(monster_mod.random, 'randint', lambda a, b: a)      # a 1: it takes hold
    assert w._drain_takes_hold(game.player)
    assert family_edges.drain(game.player) == []
    monkeypatch.setattr(monster_mod.random, 'randint', lambda a, b: b)      # a 20: held
    w2 = _mon(game, 'wight', dx=2)
    assert not w2._drain_takes_hold(game.player)
    assert any(t.startswith('Grave-Salt:') for t in family_edges.drain(game.player))


def test_garlic_and_ash_never_talks_about_a_bite_on_a_paralysis_save(game):
    from status_effects import apply_debuff_with_save
    _grant(game, vampires_liches=3)
    lich = _mon(game, 'lich')
    apply_debuff_with_save(game.player, 'paralyzed', 3, -99, source=lich)
    said = family_edges.drain(game.player)
    assert said and all('bite' not in t for t in said), said
    spawn = _mon(game, 'vampire_spawn', dx=2)
    assert family_edges.drain_heal_blocked(game.player, spawn)
    assert family_edges.drain(game.player) == ['Garlic and Ash: the bite takes nothing back to heal it.']


# ---------------------------------------------------------------------------
# 5: no double weakness
# ---------------------------------------------------------------------------
def test_bonebreaker_and_super_effective_are_not_both_said_on_one_blow(game):
    _grant(game, restless_dead=4)
    game.player.weapon = None
    m = _mon(game, 'skeleton', max_hp=999, hp=999)
    _answer(game, 2)
    game._start_combat(m)
    log = _log(game)
    assert _at(log, 'Bonebreaker!') >= 0
    assert not any(_is_affinity(t, 'weak') for t in log)
    game.msg_log.clear()
    game._start_combat(m)                            # the technique's line is once a creature
    log = _log(game)
    assert _at(log, 'Bonebreaker!') < 0 and any(_is_affinity(t, 'weak') for t in log)


# ---------------------------------------------------------------------------
# 6, 7: lines that said what did not happen
# ---------------------------------------------------------------------------
def test_harpes_stone_line_is_never_said_on_a_blow_that_does_not_stone(game):
    _grant(game, gorgons=5)
    m = _mon(game, 'cockatrice', max_hp=999, hp=999)
    _answer(game, 1)
    game._start_combat(m)
    assert m.alive
    assert _at(_log(game), 'turns to stone') < 0


def test_a_named_foes_harder_blow_has_its_own_line(game):
    _grant(game, demons=5)
    game.player.weapon = _weapon('longsword', 'steel')
    m = _mon(game, 'camazotz', max_hp=100000, hp=9000)
    _answer(game, 18)
    game._start_combat(m)
    log = _log(game)
    assert m.alive
    assert _at(log, 'Banishment! It reels, but it does not fall.') >= 0
    assert _at(log, 'cast back into the Pit') < 0


@pytest.mark.parametrize('fid,kind,line,metal,says', [
    ('fair_folk', 'satyr_warrior', 'Cold Iron!', None, False),
    ('fair_folk', 'satyr_warrior', 'Cold Iron!', 'steel', False),
    ('fair_folk', 'satyr_warrior', 'Cold Iron!', 'silver', False),
    ('fair_folk', 'satyr_warrior', 'Cold Iron!', 'cold_iron', True),
    ('shapeshifters', 'wererat', 'Silvered!', 'steel', False),
    ('shapeshifters', 'wererat', 'Silvered!', 'silver', True),
])
def test_cold_iron_and_silvered_only_with_their_metal(game, fid, kind, line, metal, says):
    _grant(game, **{fid: 4})
    game.player.weapon = _weapon('longsword', metal) if metal else None
    m = _mon(game, kind, max_hp=999, hp=999)
    _answer(game, 1)
    game._start_combat(m)
    assert (_at(_log(game), line) >= 0) == says


# ---------------------------------------------------------------------------
# 8: Yield!
# ---------------------------------------------------------------------------
def test_yield_comes_after_the_blow_and_the_purse_is_said_once(game):
    _grant(game, mortals=5)
    m = _mon(game, 'bandit_thug', max_hp=400, hp=210)
    m.treasure = {'gold': [40, 40]}
    _answer(game, 8)
    game._start_combat(m)
    log = _log(game)
    blow = _at(log, 'Chain x8!')
    yld = _at(log, 'Yield! Your foe breaks and runs.')
    gold = _at(log, 'throws down 40 gold.')
    assert 0 <= blow < yld < gold, log
    assert sum('purse' in t for t in log) == 0
    assert not any(' his ' in f' {t} ' for t in log)


def test_no_his_in_the_mortal_foes_lines():
    for t in family_lore.family('mortals')['tiers']:
        for a in t['abilities']:
            for text in (a.get('text', ''), a.get('trigger_msg', '')):
                assert ' his ' not in f' {text} ', (a['id'], text)


# ---------------------------------------------------------------------------
# 9, 11: Perseus' Shield once; Lay the Ghost names holy
# ---------------------------------------------------------------------------
def test_perseus_shield_is_said_once(game):
    from items import load_items
    _grant(game, gorgons=4)
    game.player.shield = load_items('shield')[0]
    m = _mon(game, 'basilisk')
    gaze = next(a for a in m.attacks if 'gaze' in a.get('name', '').lower())
    _dmg, msg = m._resolve_blow(gaze, game.player)
    assert 'bright metal of your shield' in msg
    assert family_edges.drain(game.player) == []


def test_lay_the_ghost_names_the_holy_it_lent(game):
    import combat
    _grant(game, ghosts=5)
    p = game.player
    p.weapon = _weapon('longsword', 'steel')
    m = _mon(game, 'wraith', max_hp=999, hp=999)
    affinity.drain()
    combat.strike_damage(p, m, 8, consume=True)
    notes = affinity.drain()
    assert notes and notes[0][1] == 'weak' and notes[0][2] == 'holy', notes


# ---------------------------------------------------------------------------
# 12: the Ring of Invisibility's veil
# ---------------------------------------------------------------------------
def _ring_on(g, level=10):
    import rings
    from items import load_items
    ring = next(i for i in load_items('accessory') if getattr(i, 'kind', '') == 'invisibility')
    rings.relevel(ring, level)
    ring.ench_level = getattr(ring, 'ench_level', 0) or level
    g.player.accessory_slots[0] = ring
    assert rings.veil_turns(g.player) == 2
    return ring


def test_the_veil_lines(game):
    _ring_on(game)
    for _ in range(2):
        game._advance_turn()
    log = _log(game)
    assert 'You fade from sight.' in log and 'You fade from sight again.' not in log
    game.msg_log.clear()
    game.player.weapon = _weapon('longsword', 'steel')
    m = _mon(game, 'goblin', max_hp=999, hp=999)
    seen = []
    _answer(game, 2, seen)
    game._start_combat(m)
    assert not any('veil slips' in t for t in seen[0])      # not before the quiz
    log = _log(game)
    assert _at(log, 'Chain x2!') < _at(log, 'Your veil slips as you strike.')
    # The striking turn is not quiet: two more quiet turns, as the ring says.
    game._advance_turn()
    assert 'You fade from sight again.' not in _log(game)
    game._advance_turn()
    assert 'You fade from sight again.' in _log(game)


def test_a_thrown_weapon_slips_the_veil(game):
    import rings
    _ring_on(game)
    game._advance_turn()
    game._advance_turn()
    assert game.player.has_effect('invisible')
    m = _mon(game, 'goblin', max_hp=999, hp=999)
    dagger = _weapon('dagger', 'iron')
    game.player.inventory.append(dagger)
    game._throw_weapon(dagger, m, m.x, m.y)
    assert not game.player.has_effect('invisible') and not game.player._veil_on
    game._advance_turn()
    assert 'Your veil slips as you strike.' in _log(game)
    assert rings.veil_turns(game.player) == 2


# ---------------------------------------------------------------------------
# 13: a lurker's reveal
# ---------------------------------------------------------------------------
def test_a_lurker_killed_by_the_blow_never_springs(game):
    game.player.weapon = _weapon('mace', 'iron')
    m = _mon(game, 'piercer', hp=1, still=False)
    _answer(game, 2)
    game._start_combat(m)
    log = _log(game)
    assert _at(log, 'is slain!') >= 0
    assert _at(log, 'springs') < 0


def test_a_lurker_that_lives_springs_before_the_blow(game):
    game.player.weapon = _weapon('mace', 'iron')
    m = _mon(game, 'piercer', max_hp=999, hp=999, still=False)
    _answer(game, 2)
    game._start_combat(m)
    log = _log(game)
    assert 0 <= _at(log, 'springs from hiding') < _at(log, 'Chain x2!')


# ---------------------------------------------------------------------------
# 14: the world's turn says its own hits; a new floor starts clean
# ---------------------------------------------------------------------------
def test_a_hit_in_the_worlds_turn_is_said_in_that_turn(game, monkeypatch):
    m = _mon(game, 'skeleton', dx=2, max_hp=999, hp=999)

    def world(self):
        m.take_damage(5, 'holy')                # Boots of Thor, a pet's special ...
    monkeypatch.setattr(type(game), '_do_monster_turns', world)
    game._advance_turn()
    assert any(_is_affinity(t, 'weak') for t in _log(game))
    assert affinity.drain() == []


def test_a_new_floor_starts_with_no_hits_to_tell(game):
    m = _mon(game, 'skeleton', dx=2)
    affinity.note(m, affinity.WEAK, 'holy')
    game._change_level(2, enter_from_top=True)
    assert affinity.drain() == []


# ---------------------------------------------------------------------------
# 16: the keen-senses check and the family techniques
# ---------------------------------------------------------------------------
def test_a_sure_detection_names_the_technique(game):
    _grant(game, goblinkin=4)
    _mon(game, 'kobold_trapsetter', dx=2, still=False)
    game._do_passive_ambush_detection()
    log = _log(game)
    assert any(t.startswith('Trap-Wise: you spot') for t in log), log
    assert not any('keen senses' in t for t in log)


def test_a_lurker_a_technique_shows_is_not_announced_twice(game, monkeypatch):
    _grant(game, vermin=4)
    m = _mon(game, 'giant_spider', dx=2, still=False)
    game.player.PER = 99                               # the keen-senses roll would succeed
    game._do_passive_ambush_detection()
    assert not m._aware and not _log(game)
    game._family_turn()
    assert sum(t.startswith('Tremor-Sense:') for t in _log(game)) == 1
    # Out of the technique's reach (it no longer shows it), a later
    # keen-senses spot is silent: the technique named it already.
    import main as main_mod
    monkeypatch.setattr(main_mod.family_edges, 'senses', lambda p, mm: False)
    game._do_passive_ambush_detection()
    assert m._aware
    assert not any('keen senses' in t for t in _log(game))


# ---------------------------------------------------------------------------
# 17: hints after the strike line; scales passed say nothing
# ---------------------------------------------------------------------------
def test_a_ward_hint_comes_after_the_strike_line(game):
    game.player.weapon = _weapon('longsword', 'steel')
    m = _mon(game, 'goblin', max_hp=999, hp=999)
    m.damage_ward = 0.5
    _answer(game, 2)
    game._start_combat(m)
    log = _log(game)
    assert 0 <= _at(log, 'Chain x2!') < _at(log, 'half of it is lost there')


def test_no_skates_off_the_scales_when_the_blow_passed_them(game):
    game.player.weapon = _weapon('longsword', 'steel')
    m = _mon(game, 'goblin', max_hp=999, hp=999)
    m.dragon_scales = 0.8
    game.player.status_effects['blade_flow'] = 3          # the blow goes past
    _answer(game, 2)
    game._start_combat(m)
    assert _at(_log(game), 'skates off') < 0
    game.msg_log.clear()
    game.player.status_effects.pop('blade_flow', None)
    m2 = _mon(game, 'goblin', dx=2, max_hp=999, hp=999)
    m2.dragon_scales = 0.8
    game._start_combat(m2)
    assert _at(_log(game), 'skates off') >= 0


# ---------------------------------------------------------------------------
# The lower list
# ---------------------------------------------------------------------------
def test_the_clocks_line_is_said_as_the_quiz_opens(game):
    _grant(game, giants=3)
    m = _mon(game, 'ogre', max_hp=999, hp=999)
    seen = []
    _answer(game, 1, seen)
    game._start_combat(m)
    assert any(t.startswith('Steady Hand:') for t in seen[0])
    log = _log(game)
    assert _at(log, 'Steady Hand:') < _at(log, 'Chain x1!')


def test_fire_and_dawn_only_on_a_creature_that_regenerates(game):
    _grant(game, giants=4)
    game.player.weapon = _weapon('longsword', 'steel')
    ogre = _mon(game, 'ogre', max_hp=999, hp=999)
    _answer(game, 1)
    game._start_combat(ogre)
    assert _at(_log(game), 'Fire and Dawn') < 0
    troll = _mon(game, 'troll', dx=2, max_hp=999, hp=999)
    game._start_combat(troll)
    assert _at(_log(game), 'Fire and Dawn') >= 0


def test_opposing_element_is_said_only_for_an_element(game):
    _grant(game, elementals=4)
    m = _mon(game, 'void_elemental')
    family_edges.weakness_amp(game.player, m, True, consume=True, word='holy')
    assert family_edges.drain(game.player) == []
    assert family_edges.weakness_amp(game.player, m, True, consume=True, word='fire') > 1.0
    assert [t for t in family_edges.drain(game.player) if t.startswith('Opposing Element!')]


def test_second_sight_says_nothing_when_the_hero_sees_invisible(game):
    _grant(game, ghosts=4)
    _mon(game, 'poltergeist', dx=2)
    game.player.status_effects['see_invisible'] = 50
    game._family_turn()
    assert _at(_log(game), 'Second Sight') < 0
    game.player.status_effects.pop('see_invisible', None)
    _mon(game, 'poltergeist', dx=1)
    game._family_turn()
    assert _at(_log(game), 'Second Sight') >= 0


def test_the_on_sight_fear_never_touches_a_sleeper(game):
    _grant(game, goblinkin=5)
    m = _mon(game, 'goblin', dx=2, still=False)
    m.status_effects['sleeping'] = 50
    game._family_turn()
    assert not m.has_effect('feared')
    assert _at(_log(game), 'Your Name Is Known') < 0


# ---------------------------------------------------------------------------
# Brandon's ruling 1: what an execute leaves
# ---------------------------------------------------------------------------
def _corpse_of(g, m):
    return [i for i in g.ground_items if getattr(i, 'monster_id', None) == m.kind]


def _gold_at(g, x, y):
    from items import GoldPile
    return sum(int(getattr(i, 'amount', 0) or 0) for i in g.ground_items
               if isinstance(i, GoldPile) and (i.x, i.y) == (x, y))


def test_a_stake_leaves_no_corpse_but_drops_the_loot(game):
    _grant(game, vampires_liches=5)
    game.player.weapon = _weapon('longsword', 'steel')
    m = _mon(game, 'vampire_spawn', max_hp=10000, hp=600)
    m.treasure = {'gold': [30, 30]}
    kills = game.level_mgr.monsters_killed
    _answer(game, 18)
    game._start_combat(m)
    assert not m.alive and game.level_mgr.monsters_killed == kills + 1
    assert not _corpse_of(game, m)
    assert _gold_at(game, m.x, m.y) >= 30
    assert _at(_log(game), 'is slain!') >= 0


def test_erase_the_letter_leaves_no_corpse(game):
    _grant(game, constructs=5)
    game.player.weapon = _weapon('mace', 'steel')
    m = _mon(game, 'iron_golem', max_hp=10000, hp=600)
    _answer(game, 18)
    game._start_combat(m)
    assert not m.alive and not _corpse_of(game, m)


def test_family_banishment_is_the_banishment_spells_rule(game):
    _grant(game, demons=5)
    game.player.weapon = _weapon('longsword', 'steel')
    m = _mon(game, 'imp', max_hp=10000, hp=600)
    m.treasure = {'gold': [30, 30]}
    m.stolen_gold = 12
    kills = game.level_mgr.monsters_killed
    _answer(game, 18)
    game._start_combat(m)
    assert not m.alive and game.level_mgr.monsters_killed == kills + 1     # the credit
    assert not _corpse_of(game, m)                                         # no body
    assert _gold_at(game, m.x, m.y) == 12                                  # only the hero's own back
    log = _log(game)
    assert _at(log, 'is slain!') < 0 and _at(log, 'Banishment!') >= 0


# ---------------------------------------------------------------------------
# Brandon's ruling 3: the popups from play, one at a time
# ---------------------------------------------------------------------------
def _popup(title, line='x'):
    return {'title': title, 'accent': (200, 200, 200), 'lines': [line], 'code': None}


def test_two_popups_raised_in_one_action_show_one_after_the_other(game):
    from game_states import STATE_PLAYER, STATE_STORY_POPUP
    game._queue_popup(_popup('ONE'), 'family')
    game._queue_popup(_popup('TWO'), 'trait')
    game._popup_tick(1.0)
    assert game.state == STATE_STORY_POPUP and game.popup_data['title'] == 'ONE'
    game._close_story_popup()
    assert game.state == STATE_STORY_POPUP and game.popup_data['title'] == 'TWO'
    game._close_story_popup()
    assert game.state == STATE_PLAYER and not game._popups_waiting()


def test_an_identical_popup_is_not_queued_twice(game):
    from game_states import STATE_STORY_POPUP
    assert game._queue_popup(_popup('SAME'), 'trait')
    assert not game._queue_popup(_popup('SAME'), 'trait')
    assert game._queue_popup(_popup('SAME'), 'family')             # another kind is another popup
    game._popup_tick(1.0)
    assert game.state == STATE_STORY_POPUP
    assert not game._queue_popup(_popup('SAME'), 'trait')          # it is showing
    assert len(game._popup_queue) == 1


def test_no_popup_opens_during_a_quiz_or_before_play_is_calm(game):
    from game_states import STATE_PLAYER, STATE_QUIZ, STATE_STORY_POPUP
    game._queue_popup(_popup('WAIT'), 'trait')
    game.state = STATE_QUIZ
    game._popup_tick(5.0)
    assert game.state == STATE_QUIZ
    game.state = STATE_PLAYER
    game._popup_tick(0.5)
    assert game.state == STATE_PLAYER                        # the quiz's result first
    game._popup_tick(0.3)
    assert game.state == STATE_STORY_POPUP


def test_no_popup_while_the_strike_flourish_is_on_screen(game):
    from game_states import STATE_PLAYER, STATE_STORY_POPUP
    game._queue_popup(_popup('AFTER'), 'trait')
    game._fire_strike_finisher(None, 5, 30, True)
    game._popup_tick(1.0)
    assert game.state == STATE_PLAYER
    game.effects_runtime.update(10.0)                        # the flourish is over
    game._popup_tick(1.0)
    assert game.state == STATE_STORY_POPUP


def test_after_a_study_the_lore_page_comes_first(game):
    from game_states import STATE_LORE, STATE_PLAYER, STATE_STORY_POPUP
    from items import Corpse
    fid = 'vermin'
    kinds = [k for k in family_lore.members(fid) if k in MONS and not family_lore.is_keystone(k)]
    need = family_lore.thresholds(fid)[2]
    game.player.studied_monster_ids.update(kinds[:need - 1])
    family_lore.mark_all_told(game.player)
    kind = kinds[need - 1]
    corpse = Corpse(MONS[kind]['name'], kind, game.player.x, game.player.y, harvest_tier=1,
                    monster_def={'tags': MONS[kind]['tags']})
    game.ground_items.append(corpse)
    game.quiz_engine.start_quiz = lambda **kw: kw['callback'](QuizResult(True, 1, 1, 1))
    game._start_corpse_identify(corpse, after_advance_turn=True)
    assert family_lore.tier(game.player, fid) == 3
    assert game.state == STATE_LORE                          # the lore page, not the popup
    game._popup_tick(5.0)
    assert game.state == STATE_LORE
    game.state = STATE_PLAYER                                # the page is closed
    game._popup_tick(1.0)
    assert game.state == STATE_STORY_POPUP and game.popup_data.get('_family')


def test_a_trait_earned_mid_quiz_waits_for_calm_play(game):
    from game_states import STATE_PLAYER, STATE_QUIZ, STATE_STORY_POPUP
    game.state = STATE_QUIZ
    game._show_quirk_unlock_popup('Test Trait', 'It does a thing.', '', '')
    game._popup_tick(1.0)
    assert game.state == STATE_QUIZ
    game.state = STATE_PLAYER
    game._popup_tick(1.0)
    assert game.state == STATE_STORY_POPUP and game.popup_data['title'] == 'TRAIT UNLOCKED'


# ---------------------------------------------------------------------------
# Brandon's ruling 4: no blood, no bleeding
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('kind', ['skeleton', 'wraith', 'iron_golem', 'fire_elemental',
                                  'green_slime', 'shambling_mound', 'lich', 'mummy'])
def test_a_creature_with_no_blood_never_bleeds(game, kind):
    m = _mon(game, kind, max_hp=500, hp=500)
    assert not m.can_bleed()
    m.add_effect('bleeding', 5)
    m.hold('bleeding', 5)
    assert not m.has_effect('bleeding')
    m.status_effects['bleeding'] = 5             # an old save, a proc written straight in
    hp = m.hp
    m.tick_effects()
    assert m.hp == hp and 'bleeding' not in m.status_effects


@pytest.mark.parametrize('kind', ['vampire_spawn', 'ghoul', 'zombie', 'goblin', 'troll'])
def test_a_creature_with_blood_bleeds(game, kind):
    m = _mon(game, kind, max_hp=500, hp=500)
    assert m.can_bleed()
    m.add_effect('bleeding', 5)
    assert m.has_effect('bleeding')


def test_a_wraith_is_never_called_bleeding(game):
    _grant(game, ghosts=5)
    game.player.weapon = _weapon('longsword', 'steel')
    m = _mon(game, 'wraith', max_hp=999, hp=999)
    _answer(game, 8)
    game._start_combat(m)
    assert _at(_log(game), 'is bleeding') < 0


def test_the_blood_lists_name_real_kinds():
    data = json.load(open(os.path.join(ROOT, 'data', 'monster_blood.json'), encoding='utf-8'))
    for key in ('bleeds', 'bloodless'):
        for k in data[key]:
            assert k in MONS, (key, k)
    fams = set(family_lore.families())
    for key in ('bloodless_families', 'bleeding_families'):
        assert set(data[key]) <= fams, key
