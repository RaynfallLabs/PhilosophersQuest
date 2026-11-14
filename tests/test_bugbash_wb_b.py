"""Bug bash on the winning build, area B: monsters, knowledge and magic
(slices 2, 3 and 7). Each test names the finding it pins (WB-Bnn in the
hunter's report).

Logic tests on a real headless Game: the knowledge leaks, a rule that did
not follow its own data, and lines that said an effect took hold when the
creature's nature had refused it. How any of it feels in play is a play-test
question (Claude cannot drive Pygame).
"""
import json
import os
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, 'src'), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import affinity  # noqa: E402
import combat  # noqa: E402
import enemy_lore  # noqa: E402
import family_lore  # noqa: E402
import items  # noqa: E402
import tells  # noqa: E402
from family_lore import KNOWN, UNKNOWN  # noqa: E402
from monster import Monster  # noqa: E402
from spells import LEARNABLE_SPELLS  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _m(kind, x=5, y=5, **over):
    m = Monster({**MONS[kind], 'id': kind}, x, y)
    for k, v in over.items():
        setattr(m, k, v)
    return m


@pytest.fixture(autouse=True)
def _clean():
    affinity.drain()
    yield
    affinity.drain()


@pytest.fixture
def game(monkeypatch, tmp_path):
    import bones
    import save_system
    from main import Game
    from game_states import STATE_PLAYER
    monkeypatch.setenv('PQ_NO_BONES', '1')
    monkeypatch.setattr(save_system, '_save_path', lambda n: str(tmp_path / f'save_{n}.pkl'))
    monkeypatch.setattr(bones, 'save_bones', lambda *a, **k: None)
    random.seed(7)
    items.bind_unique_registry(set())
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_bugbash_wb_b__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    log = []
    monkeypatch.setattr(g, 'add_message', lambda text, kind='info', *a, **k: log.append(str(text)))
    g._log = log
    return g


def _in_view(g, kind, dx=1, **over):
    from dungeon import FLOOR
    x = min(max(g.player.x, 5), g.dungeon.width - 6)
    y = min(max(g.player.y, 5), g.dungeon.height - 6)
    for i in range(-4, 5):
        for j in range(-4, 5):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    g.player.x, g.player.y = x, y
    m = _m(kind, x + dx, y, **over)
    m._aware = True
    g.monsters.append(m)
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-4, 5) for j in range(-4, 5)}
    return m


def _wand(wid):
    w = items.make_item_by_id('wand', wid)
    assert w is not None, wid
    return w


def _zap(g, wid, target):
    g._wand_override_target = target
    try:
        g._apply_wand_effect(_wand(wid))
    finally:
        g._wand_override_target = None


def _cast(g, sid, target=None):
    sp = LEARNABLE_SPELLS[sid]
    g._active_spell_tier = int(sp.get('tier', 1))
    g._apply_spell_effect(sp, target)


# ---------------------------------------------------------------------------
# WB-B01: the Wand of Poison named a poison resistance the hero had not learned
# ---------------------------------------------------------------------------
def test_wb_b01_poison_wand_names_no_resistance_of_an_unknown_kind(game):
    cobra = _in_view(game, 'cobra')
    assert 'poison' in cobra.resistances and 'poisoned' not in cobra.status_immune
    assert family_lore.knowledge(game.player, cobra) == UNKNOWN
    _zap(game, 'wand_of_poison_monster', cobra)
    assert cobra.has_effect('poisoned')
    said = ' '.join(game._log).lower()
    assert 'resists' not in said and 'venom' not in said, game._log


def test_wb_b01_poison_wand_still_names_it_for_a_kind_he_knows(game):
    cobra = _in_view(game, 'cobra')
    game._open_kind_page('cobra')
    assert family_lore.knowledge(game.player, cobra) == KNOWN
    _zap(game, 'wand_of_poison_monster', cobra)
    assert cobra.has_effect('poisoned')
    assert any('resists the venom' in t for t in game._log), game._log


# ---------------------------------------------------------------------------
# WB-B02: the galla's fearlessness: named to a hero who never studied it,
# and a flask or a mass spell said it was Feared when it shakes fear off
# ---------------------------------------------------------------------------
def test_wb_b02_fearless_refuses_fear_by_nature():
    galla = _m('galla_demon')
    assert galla.fearless
    assert galla.resists_control('feared')
    galla.add_effect('feared', 10)
    assert not galla.has_effect('feared')


def test_wb_b02_fear_wand_on_an_unknown_galla_names_nothing(game, monkeypatch):
    import game_magic
    monkeypatch.setattr(game_magic, '_is_big_foe', lambda m: False)
    galla = _in_view(game, 'galla_demon')
    for wid in ('wand_of_fear', 'wand_of_terror'):
        game._log.clear()
        _zap(game, wid, galla)
        said = ' '.join(game._log).lower()
        assert 'fear' not in said and 'flees' not in said, (wid, game._log)


def test_wb_b02_fear_spell_on_an_unknown_galla_names_nothing(game, monkeypatch):
    import game_magic
    monkeypatch.setattr(game_magic, '_is_big_foe', lambda m: False)
    galla = _in_view(game, 'galla_demon')
    sid = next(k for k, v in LEARNABLE_SPELLS.items() if v.get('effect') == 'fear_monster_spell')
    _cast(game, sid, galla)
    said = ' '.join(game._log).lower()
    assert 'fear' not in said and 'flees' not in said, game._log


def test_wb_b02_a_thrown_fear_flask_does_not_say_the_galla_is_feared(game):
    galla = _in_view(game, 'galla_demon')

    class _P:
        effect, duration, power = 'fear', 10, ''
    game._apply_thrown_potion(_P(), galla, 'potion')
    assert not any('It is Feared' in t for t in game._log), game._log
    assert not galla.has_effect('feared')


def test_wb_b02_the_bestiary_keeps_fearless_for_a_kind_he_knows():
    from game_render import monster_trait_lines
    d = {**MONS['galla_demon'], 'id': 'galla_demon'}
    assert any('Fearless' in t for t in monster_trait_lines(d))
    assert not any('Fearless' in t for t in monster_trait_lines(d, known=False))


# ---------------------------------------------------------------------------
# WB-B03: fire never routs a named foe, yet five carried fear_of_fire
# ---------------------------------------------------------------------------
def test_wb_b03_no_named_foe_falls_to_fear_of_fire():
    for kind, d in MONS.items():
        if d.get('is_boss') or d.get('is_mini_boss') or d.get('is_seal_demon'):
            assert affinity.FEAR_OF_FIRE not in (d.get('status_weak') or ()), kind


def test_wb_b03_a_named_foe_with_the_old_token_is_not_routed_and_not_told_so():
    fen = _m('fenrir_wolf', status_weak=['fear_of_fire'])
    fen.take_damage(50, 'fire')
    assert not fen.has_effect('feared')           # the rule: named foes stand
    assert 'flight' not in ' '.join(tells.lore_lines(_m('fenrir_wolf'))).lower()


def test_wb_b03_fenrirs_quest_line_claims_only_what_is_true():
    e = enemy_lore.quest_entry('fenrir_wolf')
    assert 'status_weak' not in e['claims'] or not e['claims']['status_weak']
    text = ' '.join(e['lines']).lower()
    assert 'fears fire' not in text


# ---------------------------------------------------------------------------
# WB-B04: a fire or acid weapon did not stop a troll's mending or frighten
# what fears fire, though a fire coating, flask or spell does
# ---------------------------------------------------------------------------
class _Res:
    def __init__(self, score):
        self.score = score
        self.struck_early = False
        self.success = True


class _Quiz:
    forgive_was_used = False

    def __init__(self, score):
        self.score = score

    def start_quiz(self, *a, callback=None, **k):
        callback(_Res(self.score))


def _fire_weapon():
    w = items.make_item_by_id('weapon', 'prometheus_torch')
    assert w is not None
    w.damage_types = list(w.damage_types)
    assert 'fire' in w.damage_types
    return w


def test_wb_b04_a_fire_weapon_blow_stops_a_trolls_mending(game):
    troll = _in_view(game, 'troll')
    troll.max_hp = troll.hp = 100000                 # it lives through the blow
    game.player.weapon = _fire_weapon()
    combat.player_attack(game.player, troll, _Quiz(2), lambda *a, **k: None)
    assert int(troll.__dict__.get('_regen_blocked', 0) or 0) > 0
    hp = troll.hp
    troll.tick_effects()
    assert troll.hp <= hp                           # the wound does not close


def test_wb_b04_a_fire_weapon_blow_frightens_what_fears_fire(game):
    wolf = _in_view(game, 'troll')
    wolf.max_hp = wolf.hp = 100000
    assert affinity.FEAR_OF_FIRE in wolf.status_weak
    game.player.weapon = _fire_weapon()
    combat.player_attack(game.player, wolf, _Quiz(2), lambda *a, **k: None)
    assert wolf.has_effect('feared')


def test_wb_b04_a_plain_weapon_blow_does_neither(game):
    troll = _in_view(game, 'troll')
    troll.max_hp = troll.hp = 100000
    game.player.weapon = items.instantiate_weapon('mace', 'iron')
    combat.player_attack(game.player, troll, _Quiz(2), lambda *a, **k: None)
    assert not troll.__dict__.get('_regen_blocked')
    assert not troll.has_effect('feared')


def test_wb_b04_a_thrown_fire_weapon_counts_too(game):
    troll = _in_view(game, 'troll')
    troll.max_hp = troll.hp = 100000
    w = _fire_weapon()
    game.player.inventory.append(w)
    game._throw_weapon(w, troll, troll.x, troll.y)
    assert int(troll.__dict__.get('_regen_blocked', 0) or 0) > 0


# ---------------------------------------------------------------------------
# WB-B05: Mistilteinn's preview told an unstudied kind's resistances
# ---------------------------------------------------------------------------
def test_wb_b05_mistilteinn_preview_tells_no_resistance_of_an_unknown_kind():
    from player import Player
    p = Player()
    w = items.make_item_by_id('weapon', 'mistilteinn')
    assert w is not None and getattr(w, 'damage_double_vs_resistant_at_max', False)
    p.weapon = w
    top = int(w.max_chain_length or len(w.chain_multipliers))
    plain = _m('goblin', resistances=[], weaknesses=[], shrugs_off=[])
    hard = _m('goblin', resistances=['poison'], weaknesses=[], shrugs_off=[])
    for m in (plain, hard):
        m.max_hp = m.hp = 10 ** 7
    assert (combat.strike_preview(p, plain, top, known=False)
            == combat.strike_preview(p, hard, top, known=False))
    # the blow itself still doubles, and so does the preview of a known kind
    assert (combat.strike_preview(p, hard, top, known=True)
            > combat.strike_preview(p, plain, top, known=True))


# ---------------------------------------------------------------------------
# WB-B06: lines that said an effect took hold when the creature's nature
# (status_immune) or a named foe's cap had refused it
# ---------------------------------------------------------------------------
def test_wb_b06_imprisonment_on_a_swarm_does_not_say_it_is_sealed(game):
    swarm = _in_view(game, 'scarab_swarm', dx=2)
    assert 'paralyzed' in swarm.status_immune
    random.seed(3)
    _cast(game, 'imprisonment_spell', swarm)
    assert not swarm.has_effect('paralyzed')
    assert not any('sealed in arcane stone' in t for t in game._log), game._log


def test_wb_b06_imprisonment_on_a_named_foe_says_the_turns_it_really_holds(game, monkeypatch):
    import game_magic
    monkeypatch.setattr(game_magic, '_is_big_foe', lambda m: False)
    boss = _in_view(game, 'asterion_minotaur', dx=2)
    _cast(game, 'imprisonment_spell', boss)
    held = int(boss.status_effects.get('paralyzed', 0))
    assert held <= 2
    for t in game._log:
        if 'sealed in arcane stone' in t:
            assert f"for {held} turns" in t, game._log


def test_wb_b06_banishment_consolation_on_a_swarm_is_not_said_to_hold(game):
    swarm = _in_view(game, 'scarab_swarm', dx=2)
    _cast(game, 'banishment_spell', swarm)
    assert not swarm.has_effect('paralyzed')
    assert not any('frozen in dread' in t for t in game._log), game._log


def test_wb_b06_a_sleep_scroll_counts_only_what_fell_asleep(game):
    for dx in (1, 2):
        _in_view(game, 'skeleton', dx=dx)
    assert all('sleeping' in m.status_immune for m in game.monsters)
    s = items.make_item_by_id('scroll', 'scroll_of_sleep')
    game._apply_scroll_effect(s)
    assert not any(m.has_effect('sleeping') for m in game.monsters)
    assert not any('fall asleep' in t and '2 creature' in t for t in game._log), game._log


def test_wb_b06_a_confusion_scroll_counts_only_what_reeled(game):
    for dx in (1, 2):
        _in_view(game, 'iron_golem', dx=dx)
    assert all(m.resists_control('confused') for m in game.monsters)
    s = items.make_item_by_id('scroll', 'scroll_of_confusion')
    game._apply_scroll_effect(s)
    assert not any('2 monster(s) reel' in t for t in game._log), game._log


def test_wb_b06_time_freeze_counts_only_what_it_held(game):
    _in_view(game, 'scarab_swarm', dx=2)
    _in_view(game, 'goblin', dx=1)
    _cast(game, 'time_freeze_spell')
    assert any('1 creatures locked' in t or '1 creature locked' in t for t in game._log), game._log


def test_wb_b06_turn_undead_says_only_the_ones_that_flee_flee(game):
    import game_magic
    z = next((k for k, v in MONS.items() if 'undead' in (v.get('tags') or [])
              and 'feared' in (v.get('status_immune') or []) and not v.get('is_boss')
              and not v.get('is_mini_boss')), None)
    if z is None:
        pytest.skip('no fear-immune undead kind')
    m = _in_view(game, z, dx=2)
    m.max_hp = m.hp = 10 ** 6
    assert game_magic._is_undead(m)
    _cast(game, 'turn_undead_spell')
    assert not m.has_effect('feared')
    assert not any('flee' in t for t in game._log), game._log


@pytest.mark.parametrize('aid, said', [('hand_of_glory', 'freezes'),
                                       ('lyre_of_orpheus', 'is enchanted')])
def test_wb_b06_a_hold_charge_on_a_swarm_is_not_said_to_hold(game, aid, said):
    swarm = _in_view(game, 'scarab_swarm')
    acc = items.make_item_by_id('accessory', aid)
    assert acc is not None
    acc.charges = 3
    game.player.accessory_slots[0] = acc
    game._activate_accessory_charge(aid)
    assert not swarm.has_effect('paralyzed')
    assert not any(said in t for t in game._log), game._log


# ---------------------------------------------------------------------------
# WB-B07: a named foe's will called a mind it has
# ---------------------------------------------------------------------------
def test_wb_b07_a_named_foe_refusing_fear_is_not_called_mindless():
    boss = _m('medusa_gorgon')
    assert boss.resists_control('feared') and 'feared' not in boss.status_immune
    for seed in range(30):
        t = affinity.status_line('immune', 'feared', boss, rng=random.Random(seed), level=KNOWN)
        assert 'no mind' not in t.lower(), t
    galla = _m('galla_demon')
    for seed in range(30):
        t = affinity.status_line('immune', 'feared', galla, rng=random.Random(seed), level=KNOWN)
        assert 'no mind' not in t.lower(), t
    golem = _m('iron_golem')
    assert 'feared' in golem.status_immune
    lines = {affinity.status_line('immune', 'feared', golem, rng=random.Random(s), level=KNOWN)
             for s in range(30)}
    assert any('no mind' in t for t in lines)        # the mindless keep their line


# ---------------------------------------------------------------------------
# WB-B08: the Kit's Spells tab showed the untaxed cost in metal armour
# ---------------------------------------------------------------------------
def test_wb_b08_the_kit_spells_tab_shows_what_a_cast_costs(game):
    p = game.player
    p.known_spells['fire_bolt_spell'] = LEARNABLE_SPELLS['fire_bolt_spell']['mp_cost']
    p._apply_equip(items.instantiate_armor('plate', 'chain_steel'))
    base = LEARNABLE_SPELLS['fire_bolt_spell']['mp_cost']
    assert p.spell_mp_cost(base) > base                   # steel plate taxes it
    row = next(r for r in game._kit_collect_spells() if r['spell_id'] == 'fire_bolt_spell')
    assert row['mp_cost'] == p.spell_mp_cost(base)


def test_wb_b06_the_dread_aura_counts_only_what_it_frightens(monkeypatch):
    import chain_passives
    from player import Player
    monkeypatch.setattr(chain_passives, 'player_has_passive',
                        lambda p, name: name == 'fafnirs_glare')
    golem = _m('iron_golem')
    boss = _m('asterion_minotaur', x=6)
    assert golem.resists_control('feared') and boss.resists_control('feared')
    p = Player()
    random.seed(0)
    n = sum(chain_passives.apply_fear_auras(p, [golem, boss], {(5, 5), (6, 5)})
            for _ in range(40))
    assert n == 0
    assert not golem.has_effect('feared') and not boss.has_effect('feared')


def test_wb_b06_achilles_helm_counts_only_what_flinches(game, monkeypatch):
    import armor_procs
    import main as _main
    golem = _in_view(game, 'iron_golem', dx=2)
    monkeypatch.setattr(armor_procs, 'player_has_armor_proc',
                        lambda p, proc: proc == 'ringing_intimidation')
    monkeypatch.setattr(_main, 'RING_FEAR_CHANCE', 1.0)
    golem.__dict__.pop('_heard_the_ring', None)
    game._log.clear()
    game._refresh_fov()
    assert golem.__dict__.get('_heard_the_ring')         # the helm rang for it
    assert not any('flinch' in t for t in game._log), game._log


# ---------------------------------------------------------------------------
# WB-B09: Cold Bolt shares Frost Touch's handler and was announced as it
# ---------------------------------------------------------------------------
def test_wb_b09_cold_bolt_is_named_as_itself(game):
    gob = _in_view(game, 'goblin', dx=3)
    gob.max_hp = gob.hp = 10 ** 6
    _cast(game, 'cold_bolt_spell', gob)
    assert any(t.startswith('Cold Bolt chills') for t in game._log), game._log
    assert not any('Frost touch' in t for t in game._log)
    game._log.clear()
    _cast(game, 'frost_touch_spell', gob)
    assert any(t.startswith('Frost Touch chills') for t in game._log), game._log


# ---------------------------------------------------------------------------
# WB-B10: a family's plain habit line named a cause that had not met it
# ---------------------------------------------------------------------------
def test_wb_b10_a_familys_plain_weak_line_names_no_cause_its_kinds_lack():
    """The plain 'weak' habit is said at KIN whenever no keyed habit fits
    (data/affinity_lines.json: 'which names nothing'). A damage word in it
    must be true of every kind of the family that has a weakness, or a
    blessed blade on a corrupted angel says the shadow hurt it."""
    words = dict(affinity.lines()['words'])
    words.update({'shadow': 'the shadow', 'necrotic': 'death-magic'})
    fams, _groups = affinity._habit_tables()
    for fid, (_keyed, plain) in fams.items():
        kinds = [d for d in MONS.values() if d.get('family') == fid and d.get('weaknesses')]
        for line in plain.get('weak') or []:
            low = line.lower()
            for key, word in words.items():
                if len(word) > 4 and word in low:
                    assert all(key in (d.get('weaknesses') or []) for d in kinds), (fid, line, key)


def test_wb_b10_a_corrupted_angel_struck_by_holy_hears_no_shadow():
    angel = _m('corrupted_angel')
    assert 'holy' in angel.weaknesses
    for seed in range(20):
        t = affinity.habit(angel, affinity.WEAK, 'holy', rng=random.Random(seed))
        assert 'shadow' not in t.lower() and 'death' not in t.lower(), t
