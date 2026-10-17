"""Bug bash 4 rulings (2026-10-17), world rules: calls 25, 26, 27, 28, 29,
30, 31 and 33.

25  a floor-100 altar takes one prayer a visit (no retry-until-right);
26  Sisyphus' trial counts the steps the Boulder is carried, at any load;
27  one Mjolnir: Brokkr's Anvil forges the unique and claims it;
28  every hurt and every new status reaches the trait counters;
29  Cerberus counts each staircase once (no farming one staircase);
30  Leonardo's Codex helper bites by its table's dice;
31  a hero power that found nothing to act on gives its cooldown back;
33  encounter effects print the turns they really last.
These are deep or random content, so logic tests stand in for play.
"""
import json
import os
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()


@pytest.fixture(autouse=True)
def _no_saves(monkeypatch, tmp_path):
    import save_system
    import bones
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, 'save_dir', lambda: str(tmp_path))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    yield


def _game(name='__bb4_rulings_world__', build=None):
    from main import Game
    from game_states import STATE_PLAYER
    import items
    items.bind_unique_registry(set())
    screen = pygame.display.set_mode((1, 1))
    if isinstance(build, str):
        from welcome_screen import SECRET_BUILDS
        name, build = build, SECRET_BUILDS[build]
    g = Game(screen, player_name=name, secret_build=build)
    g.state = STATE_PLAYER
    return g


def _msgs(g):
    return [str(e[0]) for e in g.msg_log.entries]


def _monster(g, mid, x, y):
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    m = Monster({**mons[mid], 'id': mid}, x, y)
    g.monsters.append(m)
    return m


def _open_tile_by(g):
    px, py = g.player.x, g.player.y
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        x, y = px + dx, py + dy
        if g.dungeon.is_walkable(x, y) and not any(
                m.alive and (m.x, m.y) == (x, y) for m in g.monsters):
            return x, y
    raise AssertionError('no open tile beside the hero')


# ---------------------------------------------------------------- call 25
def _on_l100_altar(g):
    from dungeon import ALTAR
    g.dungeon_level = 100
    g.dungeon.tiles[g.player.y][g.player.x] = ALTAR
    g.player.prayer_cooldown = 0
    return (g.player.x, g.player.y)


def test_an_unanswered_prayer_spends_the_altars_try_for_this_visit():
    """A wrong answer at a fresh floor-100 altar left it fresh and ignored
    the cooldown: pray, fail, pray again at once, until it was answered."""
    from game_states import STATE_PRAYER_MENU, STATE_PLAYER
    g = _game()
    pos = _on_l100_altar(g)
    g._start_pray()
    assert g.state == STATE_PRAYER_MENU
    g.state = STATE_PLAYER
    g._resolve_simple_prayer(0, at_altar=True)            # the heavens are silent
    assert pos in g._l100_altars_tried
    g._start_pray()
    assert g.state == STATE_PLAYER                        # refused: the cooldown holds
    assert any('cannot pray yet' in m for m in _msgs(g))
    # Even when the cooldown has run out, this visit's try is spent.
    g.player.prayer_cooldown = 0
    before = g.abaddon_resist_removed_turns
    g._resolve_simple_prayer(3, at_altar=True)
    assert g.abaddon_resist_removed_turns == before
    assert pos not in g._l100_altars_used
    assert any('heard you once already' in m for m in _msgs(g))


def test_a_new_visit_gives_the_altar_a_new_try():
    g = _game()
    pos = _on_l100_altar(g)
    g._resolve_simple_prayer(0, at_altar=True)
    assert pos in g._l100_altars_tried
    g._change_level(2, True)
    assert g._l100_altars_tried == set()


def test_an_answered_prayer_still_strips_the_destroyer():
    g = _game()
    pos = _on_l100_altar(g)
    g._resolve_simple_prayer(2, at_altar=True)
    assert g.abaddon_resist_removed_turns == 4
    assert pos in g._l100_altars_used


def test_the_altars_try_survives_a_save():
    from save_system import save_game, load_game
    g = _game('bb4altar')
    pos = _on_l100_altar(g)
    g._resolve_simple_prayer(0, at_altar=True)
    assert save_game(g)
    assert pos in load_game('bb4altar')['_l100_altars_tried']


# ---------------------------------------------------------------- call 26
def _boulder():
    from mystery_system import MysteryKeyItem, MYSTERIES
    k = MYSTERIES['sisyphus']['key_item']
    return MysteryKeyItem('sisyphus', k['name'], k['symbol'], k['color'], k['weight'])


def _walk(g, steps):
    """Walk back and forth on two open tiles; returns steps actually taken."""
    from game_states import STATE_PLAYER
    a = (g.player.x, g.player.y)
    b = _open_tile_by(g)
    taken = 0
    for i in range(steps):
        tx, ty = b if (g.player.x, g.player.y) == a else a
        g.state = STATE_PLAYER
        before = (g.player.x, g.player.y)
        g._do_move(tx - g.player.x, ty - g.player.y)
        if (g.player.x, g.player.y) != before:
            taken += 1
    return taken


def test_sisyphus_counts_every_step_the_boulder_is_carried():
    """The Boulder weighs 20: an ordinary hero carried it under the limit and
    the trial counted nothing ("The slope is waiting.", then silence)."""
    g = _game()
    g.monsters = []
    g.player.add_to_inventory(_boulder())
    assert not g.player.is_overloaded()
    g.player.quirk_progress['sisyphus_boulder_active'] = True
    g.player.quirk_progress['sisyphus_boulder_tiles'] = 0
    str_before = g.player.STR
    taken = _walk(g, 6)
    assert taken == 6
    assert g.player.quirk_progress['sisyphus_boulder_tiles'] == 6
    _walk(g, 9)                                            # 15 in all: the hill is climbed
    assert g.player.STR == str_before + 2
    assert not g.player.quirk_progress['sisyphus_boulder_active']
    assert all(getattr(i, 'mystery_id', None) != 'sisyphus' for i in g.player.inventory)


def test_sisyphus_hint_no_longer_says_too_heavy():
    hints = json.load(open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8'))
    lines = [h for pool in hints.values() for h in pool if 'Sisyphus' in str(h)]
    assert lines and not any('too heavy' in str(h) for h in lines)


# ---------------------------------------------------------------- call 27
def test_the_anvil_forges_the_one_mjolnir_and_claims_it():
    """The forge built a second hammer in code under the unique's id: a run
    could hold two Mjolnirs."""
    import items
    from mystery_system import apply_mystery_reward
    g = _game()
    apply_mystery_reward('mjolnir', g.player, g, True)
    forged = [i for i in g.player.inventory + g.ground_items if getattr(i, 'id', '') == 'mjolnir']
    assert len(forged) == 1
    hammer = forged[0]
    unique = items.make_item_by_id('weapon', 'mjolnir')
    assert hammer.base_damage == unique.base_damage
    assert hammer.quiz_tier == unique.quiz_tier
    assert not items.unique_available(unique)             # claimed: never spawns again
    assert getattr(hammer, 'identified', False) and getattr(hammer, 'id_level', 0) == 5


def test_the_anvil_makes_no_second_mjolnir_when_it_is_already_found():
    import items
    from mystery_system import apply_mystery_reward
    g = _game()
    items.claim_unique(items.make_item_by_id('weapon', 'mjolnir'))
    apply_mystery_reward('mjolnir', g.player, g, True)
    assert not [i for i in g.player.inventory + g.ground_items
                if getattr(i, 'id', '') == 'mjolnir']
    assert any('already out in the world' in m for m in _msgs(g))


def test_no_mjolnir_is_built_in_code():
    src = open(os.path.join(ROOT, 'src', 'mystery_system.py'), encoding='utf-8').read()
    assert "'id': 'mjolnir'" not in src


# ---------------------------------------------------------------- call 28
def test_a_trap_and_a_poison_tick_reach_the_trait_counters():
    """Only a monster's melee blow reached on_take_damage: Eye of the Storm's
    "without taking ANY damage" ignored traps and poison."""
    g = _game()
    qp = g.player.quirk_progress
    qp['eye_storm_no_damage_prev'] = True
    hits = qp.get('temporal_shield_hits', 0)
    g.player.max_hp = g.player.hp = 500
    g.player.take_damage(5, 'physical')                    # a trap's blow
    assert qp['eye_storm_no_damage_prev'] is False
    assert qp['temporal_shield_hits'] == hits + 1
    g.player.add_effect('poisoned', 5)
    g.player.tick_effects()                                # one poison tick
    assert qp['temporal_shield_hits'] == hits + 2


def test_a_status_from_anywhere_reaches_the_trait_counters():
    """A blinding from a potion, wand or trap never started a Medusa episode."""
    g = _game()
    qp = g.player.quirk_progress
    qp['medusa_episode_answered'] = True
    g.player.add_effect('blinded', 5)
    assert qp['medusa_episode_answered'] is False
    assert 'blinded' in qp.get('darwin_debuff_types', set())


def test_a_monster_blow_is_counted_once():
    g = _game()
    g.player.max_hp = g.player.hp = 5000
    x, y = _open_tile_by(g)
    m = _monster(g, 'goblin', x, y)
    m.attack = lambda pl: (pl.take_damage(7, 'physical'), 'The goblin hits you.')
    qp = g.player.quirk_progress
    hits = qp.get('temporal_shield_hits', 0)
    g._do_monster_turns()
    assert qp.get('temporal_shield_hits', 0) - hits == 1


def test_damage_outside_a_game_needs_no_game():
    from player import Player
    p = Player()
    assert p.take_damage(3, 'physical') >= 1
    assert p.add_effect('blinded', 3)


# ---------------------------------------------------------------- call 29
def test_cerberus_counts_each_staircase_once():
    """120 stair uses gave permanent warning: bounce on one staircase."""
    g = _game()
    qs = g.quirk_system
    for _ in range(200):
        qs.on_stair_use(2, 1)
        qs.on_stair_use(1, 2)
    assert not qs.is_unlocked('cerberus')
    assert len(g.player.quirk_progress['cerberus_stairs']) == 2
    for lvl in range(2, 70):
        qs.on_stair_use(lvl + 1, lvl)                      # down, one floor at a time
        qs.on_stair_use(lvl, lvl + 1)                      # and back up that staircase
    assert qs.is_unlocked('cerberus')


def test_change_level_passes_the_staircase():
    g = _game()
    g._change_level(2, True)
    assert (1, 2) in g.player.quirk_progress['cerberus_stairs']


# ---------------------------------------------------------------- call 30
def _summon_helper(chain):
    import hero_specials
    from hero_specials import HERO_SPECIALS, resolve_active_special
    g = _game(build='leonardo di ser piero da vinci')
    sp = HERO_SPECIALS['leonardo di ser piero da vinci']
    resolve_active_special(g, sp, chain)
    helper = next(p for p in g.pets if getattr(p, 'is_sketch', False))
    return g, helper, sp['tier_effects'][chain]['damage'], hero_specials


def test_the_codex_helper_bites_by_its_tables_dice():
    """A chain-5 helper bit a floor-1 Goblin for 254: the table's 3d8+6 was
    never read."""
    _g, helper, dice, _ = _summon_helper(5)
    assert dice == '3d8+6'
    bites = [helper.get_attack_damage() for _ in range(400)]
    assert min(bites) >= 9 and max(bites) <= 30
    _g, helper1, dice1, _ = _summon_helper(1)
    bites1 = [helper1.get_attack_damage() for _ in range(400)]
    assert dice1 == '1d8+2' and min(bites1) >= 3 and max(bites1) <= 10


def test_a_sketchbook_drawing_still_bites_like_its_subject():
    from pet_system import SketchedPet, growth
    from monster import Monster
    with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as f:
        mons = json.load(f)
    m = Monster({**mons['goblin'], 'id': 'goblin'}, 1, 1)
    pet = SketchedPet(m, 1, 1, 10)
    assert pet.base_damage == growth('bite', pet.level)


# ---------------------------------------------------------------- call 31
def _use_power(g, pid, chain):
    """Run the hero power through its real menu path; answer with `chain`."""
    from game_states import STATE_QUIZ
    assert g._activate_hero_special(pid) is True
    assert g.state == STATE_QUIZ
    cb = g.quiz_engine.callback
    g.quiz_engine.callback = None
    cb(type('R', (), {'score': chain, 'success': chain > 0})())


def test_a_power_with_nothing_to_act_on_gives_its_cooldown_back():
    """Ash Ketchum's "I Choose You!" with no pet spent 250 turns."""
    g = _game(build='ash ketchum')
    g.pets = []
    pid = g.player.hero_specials[0]['id']
    _use_power(g, pid, 3)
    assert g.player.hero_special_cooldowns.get(pid, 0) == 0
    assert any('not spent' in m for m in _msgs(g))


def test_aristotle_catalogue_with_nothing_unknown_is_not_spent():
    g = _game(build='aristotle of stagira')
    for i in g.player.inventory:
        if hasattr(i, 'identified'):
            i.identified = True
    pid = g.player.hero_specials[0]['id']
    _use_power(g, pid, 4)
    assert g.player.hero_special_cooldowns.get(pid, 0) == 0


def test_a_failed_quiz_still_spends_the_power():
    g = _game(build='ash ketchum')
    pid = g.player.hero_specials[0]['id']
    import pet_system
    species = next(iter(pet_system._SPECIES))
    x, y = _open_tile_by(g)
    g.pets = [pet_system.Pet(species, x, y)]
    _use_power(g, pid, 0)                     # wrong answer: the power is spent
    assert g.player.hero_special_cooldowns.get(pid, 0) > 0


def test_a_power_that_acts_keeps_its_cooldown():
    g = _game(build='ada augusta byron lovelace')
    x, y = _open_tile_by(g)
    m = _monster(g, 'goblin', x, y)
    g._refresh_fov()
    assert (m.x, m.y) in g.visible
    pid = g.player.hero_specials[0]['id']
    _use_power(g, pid, 3)
    assert g.player.hero_special_cooldowns.get(pid, 0) > 0
    assert m.status_effects.get('paralyzed', 0) > 0


# ---------------------------------------------------------------- call 33
def test_encounter_effects_print_the_turns_they_really_last():
    """'Blessed for 150 turns!' gave 60 (statuses are capped)."""
    from status_effects import MAX_EFFECT_DURATION
    g = _game()
    g._apply_npc_reward({'type': 'effect', 'effect': 'blessed', 'duration': 150})
    assert g.player.status_effects['blessed'] == MAX_EFFECT_DURATION
    assert f"Blessed for {MAX_EFFECT_DURATION} turns!" in _msgs(g)
    assert not any('150 turns' in m for m in _msgs(g))


# ---------------------------------------------------------------- call 35
def test_ci_runs_the_slow_tests_and_a_plain_run_leaves_them_out():
    import subprocess
    wf = open(os.path.join(ROOT, '.github', 'workflows', 'release.yml'), encoding='utf-8').read()
    assert 'python -m pytest tests/' in wf and '--run-slow' in wf
    env = dict(os.environ, PQ_RUN_SLOW='')
    plain = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/test_ui_gates.py', '--collect-only', '-q',
         '-p', 'no:cacheprovider'], cwd=ROOT, capture_output=True, text=True, env=env)
    assert 'deselected' in plain.stdout and '::test_' not in plain.stdout
    slow = subprocess.run(
        [sys.executable, '-m', 'pytest', 'tests/test_ui_gates.py', '--collect-only', '-q',
         '-p', 'no:cacheprovider', '--run-slow'], cwd=ROOT, capture_output=True, text=True, env=env)
    assert 'test_every_screen_renders_within_the_frame_budget' in slow.stdout
