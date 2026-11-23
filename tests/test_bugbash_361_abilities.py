"""Bug bash 3.6.1 (2026-11-22, Brandon to bed: "make sure it all works the way
it's supposed to work"): the hero's abilities. Each test pins one finding; the
findings list is in the bug bash report. Staged on a real headless Game where
the bug lives in Game code. What these cannot prove (how a cue reads in play)
is a play-test question: Claude cannot drive Pygame.
"""
import copy
import json
import os
import random
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402

pygame.init()

import items  # noqa: E402
from items import load_items  # noqa: E402

MONS = json.loads(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8').read())
_SCREEN = None


def _game(name='__test_bb361_abilities__'):
    global _SCREEN
    from main import Game
    from game_states import STATE_PLAYER
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    random.seed(3)
    items.bind_unique_registry(set())
    g = Game(_SCREEN, player_name=name)
    g._autosave = lambda *a, **k: None
    g.monsters, g.pets = [], []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    return g


def _item(cls, iid):
    return copy.copy(next(a for a in load_items(cls) if a.id == iid))


def _mon(kind, x=0, y=0):
    from monster import Monster
    return Monster({**MONS[kind], 'id': kind}, x, y)


def _beside(g, kind, dist=1):
    m = _mon(kind)
    px, py = g.player.x, g.player.y
    for dx in range(-dist, dist + 1):
        for dy in range(-dist, dist + 1):
            if max(abs(dx), abs(dy)) != dist:
                continue
            if g.dungeon.is_walkable(px + dx, py + dy) and not any(
                    (o.x, o.y) == (px + dx, py + dy) for o in g.monsters):
                m.x, m.y = px + dx, py + dy
                g.monsters.append(m)
                return m
    raise AssertionError('no room beside the hero')


def _texts(g, n=10):
    return [str(e[0]) for e in g.msg_log.entries[-n:]]


# ---------------------------------------------------------------- charges

def test_excalibur_keeps_its_second_life_while_the_first_is_held():
    """Excalibur's once-a-run second Life Save (cast_me_away) was spent, with
    an enchantment point, while its first was still held: refused, wasted."""
    from player import Player
    p = Player()
    p.weapon = _item('weapon', 'excalibur')
    p.weapon.enchant_bonus = 3
    p.add_effect('life_save', -1)                    # the blade's own first ward
    p.max_hp, p.hp = 100, 100
    p.take_damage(80, 'physical')
    assert 0 < p.hp <= 25
    assert not getattr(p, '_cast_me_away_used', False)
    assert p.weapon.enchant_bonus == 3
    # The first is spent (a killing blow took it): the next bad blow gives the second.
    del p.status_effects['life_save']
    p.hp = 60
    p.take_damage(40, 'physical')
    assert p._cast_me_away_used and p.weapon.enchant_bonus == 2
    assert p.status_effects.get('life_save') == -1


def test_eluned_veil_is_not_spent_on_a_hero_already_invisible():
    """The Ring of Eluned's own Invisible is permanent: its low-health veil
    was refused, yet 'Luned's ring veils you' was said and the floor's use
    spent. The use is spent only when the veil takes."""
    g = _game()
    ring = _item('accessory', 'ring_of_eluned')
    g.player._apply_equip(ring)
    assert g.player.status_effects.get('invisible') == -1
    g.player.hp = max(1, g.player.max_hp // 10)
    g._advance_turn()
    assert not g.player._eluned_auto_invis_used
    assert not any('veils you' in t for t in _texts(g, 30))
    # With the ring's own veil gone (dispelled), the low-health veil comes.
    del g.player.status_effects['invisible']
    g.player.hp = max(1, g.player.max_hp // 10)
    g._advance_turn()
    assert g.player._eluned_auto_invis_used
    assert g.player.status_effects.get('invisible', 0) > 0


def test_a_stair_up_and_down_gives_no_fresh_daimonion():
    """The Ring of Mastery's daimonion stops a floor; a stair up and back
    down to floors already walked gave them all again (the other once-a-floor
    charges are held across a revisit: _once_a_floor_state)."""
    g = _game()
    g._change_level(2, True)
    g._change_level(3, True)
    g.player._daimonion_used = 2
    g._change_level(2, False)
    g._change_level(3, True)
    assert g.player._daimonion_used == 2
    g._change_level(4, True)                         # a new floor: given back
    assert g.player._daimonion_used == 0


# ------------------------------------------------------- what by nature refuses

def test_greater_aegis_turns_a_gaze_back_though_it_is_stoneproof():
    """The Greater Aegis is stoneproof from its first tier, and that check,
    asked first, kept its mirror from ever freezing a gazer."""
    from player import Player
    p = Player()
    p.shield = _item('shield', 'greater_aegis_of_athena')
    p.add_effect('petrify_immune', -1)
    eye = _mon('medusa_gorgon', 1, 0)
    p.x, p.y = 0, 0
    eye.x, eye.y = 4, 0
    eye.status_effects.pop('paralyzed', None)
    random.seed(1)
    for _ in range(40):
        eye._gaze_cooldown = 0
        eye.__dict__.pop('_gaze_cd', None)
        _, line = eye.attack(p)
        if eye.status_effects.get('paralyzed', 0) >= 2:
            break
    assert eye.status_effects.get('paralyzed', 0) >= 2, line
    assert not p.has_effect('paralyzed')


def test_the_blindfold_leaves_raphaels_gall_in_the_pack():
    """Tying on the Blindfold (a worn, permanent Blinded) used up Raphael's
    Gall, and the blindfold still left the hero in the dark."""
    from player import Player
    p = Player()
    gall = _item('artifact', 'raphaels_gall') if any(
        a.id == 'raphaels_gall' for a in load_items('artifact')) else None
    if gall is None:
        gall = types.SimpleNamespace(id='raphaels_gall', cures_blindness_once=True, weight=0)
    p.inventory.append(gall)
    p.add_effect('blinded', -1)                      # what the Blindfold's on_equip_status does
    assert gall in p.inventory
    # A blinding that comes on him is still answered by the gall.
    p.status_effects.pop('blinded', None)
    assert p.add_effect('blinded', 5) is False
    assert gall not in p.inventory


def test_curtana_never_spares_a_named_foe():
    """Curtana could leave a gate boss, seal demon or mini-boss at 1 HP
    (up to five times a floor) instead of letting the killing blow land."""
    import inspect
    import combat
    src = inspect.getsource(combat)
    i = src.index("spare_kill_chance', 0.0)")
    assert 'not monster._is_named_foe()' in src[i:i + 700]


def test_seal_of_solomon_does_not_hold_what_cannot_be_held(monkeypatch):
    """The Seal of Solomon wrote Paralyzed straight onto anything within two
    tiles; a swarm that by nature is never held was held."""
    g = _game()
    g.player._apply_equip(_item('accessory', 'seal_of_solomon'))
    swarm = _beside(g, 'scarab_swarm')
    rat = _beside(g, 'giant_rat')
    monkeypatch.setattr(random, 'random', lambda: 0.0)
    g._advance_turn()
    assert not swarm.status_effects.get('paralyzed', 0)
    assert rat.status_effects.get('paralyzed', 0) >= 1


def test_hero_specials_lay_their_holds_through_monster_hold():
    """The build specials wrote their statuses straight in: a mindless
    humanoid was confused, the dead charmed, a swarm paralysed."""
    import hero_specials as hs
    g = _game()
    sentinel = _beside(g, 'throne_sentinel')          # humanoid, mindless
    monkeypatch_sees = lambda m: True                  # noqa: E731
    g._sees_monster = monkeypatch_sees
    r = hs._eff_confuse_visible(g, {}, {'count': 3, 'duration': 5, 'slow_too': False}, 3)
    assert r is hs.NOTHING and not sentinel.status_effects.get('confused', 0)
    g.monsters = []
    zombie = _beside(g, 'zombie')
    r = hs._eff_charm_visible(g, {}, {'count': 3, 'duration': 9}, 3)
    assert r is hs.NOTHING and not zombie.status_effects.get('charmed', 0)
    g.monsters = []
    swarm = _beside(g, 'scarab_swarm')
    rat = _beside(g, 'giant_rat')
    hs._eff_paralyze_target(g, {}, {'paralyze': 3, 'slow_too': 0}, 3)
    assert not swarm.status_effects.get('paralyzed', 0)
    assert rat.status_effects.get('paralyzed', 0) == 3
    # A charm said as what it is: the creature holds its blow.
    g.monsters = []
    rat = _beside(g, 'giant_rat')
    hs._eff_charm_visible(g, {}, {'count': 1, 'duration': 9}, 3)
    assert rat.status_effects.get('charmed', 0) == 9
    assert not any('to your side' in t for t in _texts(g))


def test_paths_of_the_dead_spends_its_run_on_one_who_takes_the_charm():
    """The Helm of Aragorn's Paths of the Dead charmed the strongest foe in
    sight, often one that refuses a charm (the dead, the mindless, a named
    foe): the run's one use was spent with nothing done."""
    g = _game()
    zombie = _beside(g, 'zombie')
    zombie.max_hp = zombie.hp = 9999                   # the strongest in sight
    rat = _beside(g, 'giant_rat')
    g.player._paths_armed = True
    import chain_passives
    orig = chain_passives.player_has_passive
    chain_passives.player_has_passive = lambda p, f: f == 'paths_of_the_dead' or orig(p, f)
    try:
        g._sees_monster = lambda m: True
        g._refresh_fov()
    finally:
        chain_passives.player_has_passive = orig
    assert not zombie.status_effects.get('charmed', 0)
    assert rat.status_effects.get('charmed', 0) > 0
    assert any('lowers' in t for t in _texts(g, 20))


def test_fire_thrown_back_is_fire_the_striker_may_shrug_off():
    """Svalinn's, Philip's Aspis's and Beowulf's Lendings' fire, and the fire
    and cold shields' lash, came straight off the health bar: a fire
    elemental was burned by its own flame."""
    import inspect
    import game_combat
    src = inspect.getsource(game_combat.CombatMixin)
    i = src.index("Svalinn: reflect fire damage back")
    assert "take_damage(max(1, int(_roll * _shld.fire_reflect)), 'fire')" in src[i:i + 1200]
    for kind in ("'fire')", "'cold')"):
        assert f"SHIELD_LASH_SHARE, m.max_hp, m._is_named_foe()), {kind}" in src
    assert 'm.hp -= reflect_dmg' not in src and 'm.hp -= _fire_ref' not in src
    # And the rule it relies on: a fire elemental shrugs most fire off.
    elem = _mon('fire_elemental')
    hp = elem.hp
    assert elem.take_damage(50, 'fire') < 25 and elem.hp > hp - 25


# ---------------------------------------------------------- marks nothing read

def test_the_sling_of_david_knocks_back_with_a_shot():
    """A shot's knockback was resolved by combat and dropped by the ranged
    callback: the Sling of David never pushed anything back."""
    g = _game()
    rat = _beside(g, 'giant_rat', dist=1)
    was = (rat.x, rat.y)
    line = g._knock_back(rat, True, False)
    moved = (rat.x, rat.y) != was
    assert (moved and 'knocked back' in line) or (not moved and line == '')
    import inspect
    import game_combat
    src = inspect.getsource(game_combat.CombatMixin._fire_ranged)
    assert 'self._knock_back(monster, knocked, killed)' in src


def test_meleagers_marked_beasts_are_shown():
    """Meleager's Boar-Spear marked the floor's beasts on a top-of-the-chain
    kill, and nothing read the marks."""
    g = _game()
    rat = _beside(g, 'giant_rat', dist=1)
    rat.x, rat.y = g.player.x + 30, g.player.y            # far out of sight
    g.player._revealed_tag_ids = {id(rat)}
    g.player._revealed_tag_turns_left = 3
    g._refresh_fov()
    assert (rat.x, rat.y) in g.visible
    g.player._revealed_tag_turns_left = 0
    g._refresh_fov()
    assert (rat.x, rat.y) not in g.visible


def test_a_demon_bound_by_the_seventy_two_seals_leaves_an_item(monkeypatch):
    """The Seventy-Two Seals marked the demon for a sure item and nothing read
    the mark."""
    g = _game()
    imp = _beside(g, 'giant_rat')
    imp.treasure = {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1}
    dropped = []
    monkeypatch.setattr(g, '_spawn_treasure_item', lambda x, y, t: dropped.append(t))
    g._drop_treasure(imp)
    assert dropped == []
    imp._seal_marked = True
    g._drop_treasure(imp)
    assert dropped == [1]


def test_beautiful_ruin_stirs_the_strongest_it_sees_against_him():
    """Beautiful Ruin only set _aware: a lurker unseen in its tile was
    unmasked without springing, and nothing was sent after him."""
    g = _game()
    ogre = _beside(g, 'giant_rat')
    ogre.max_hp = 999
    import chain_passives
    orig = chain_passives.player_has_passive
    chain_passives.player_has_passive = lambda p, f: f == 'beautiful_ruin' or orig(p, f)
    try:
        g._refresh_fov()
    finally:
        chain_passives.player_has_passive = orig
    assert ogre._aware and ogre._alerted and ogre._goal == (g.player.x, g.player.y)


def test_death_omen_counts_only_while_the_cloak_is_worn():
    """The Morrigan's mark kept its +25% after the cloak came off."""
    import inspect
    import combat
    src = inspect.getsource(combat)
    i = src.index("_death_omen_target', None) is monster")
    assert "player_has_passive" in src[i:i + 300] and "'death_omen_mark'" in src[i:i + 300]


def test_the_master_lockpick_picked_up_again_is_kept():
    """Dropped and picked up again, the Master Lockpick was sold for scrap."""
    g = _game()
    pick = next((i for i in g.player.inventory if getattr(i, 'id', '') == 'master_lockpick'), None)
    assert pick is not None
    g.player.inventory.remove(pick)
    pick.x, pick.y = g.player.x, g.player.y
    g.ground_items.append(pick)
    g._pickup(pick)
    assert pick in g.player.inventory


# ------------------------------------------------------- the Ring of Sustenance

def test_the_ring_of_sustenance_is_its_ladder_not_sustained():
    """Its data lent Sustained for good on top of its kind's hunger ladder,
    undoing the hunger rebuild (Sustained only from big dishes)."""
    ring = _item('accessory', 'ring_of_sustenance')
    from items import worn_statuses
    assert 'sustained' not in worn_statuses(ring.effects)


def test_an_old_save_ring_of_sustenance_stops_lending_sustained():
    """A ring found before the fix carries the old effects in the save: the
    load takes a kind ring's effects from today's data (gear_saves)."""
    import gear_saves
    import rings
    from player import Player
    p = Player()
    ring = _item('accessory', 'ring_of_sustenance')
    rings.relevel(ring, 3)
    ring.effects = {'status': 'sustained', 'duration': -1}      # as pickled in 3.6.0
    p.accessory_slots[0] = ring
    p.status_effects['sustained'] = -1
    gear_saves.migrate(p, [ring])
    assert 'status' not in ring.effects
    assert not p.has_effect('sustained')
    # A stat kind keeps its amount by its level.
    amu = _item('accessory', 'amulet_of_wisdom')
    rings.relevel(amu, 6)
    assert gear_saves.refresh_kind(amu)
    assert amu.effects.get('stat') == 'WIS' and amu.effects.get('amount') == 3


# ------------------------------------------------------------------- spells

def _cast(g, sid):
    from game_states import STATE_TARGET
    g.player.mp = g.player.max_mp = 999
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](
        types.SimpleNamespace(success=True, score=5))
    g._refresh_fov()
    g._invoke_spell(sid)
    if g.state == STATE_TARGET:
        g._confirm_power_target()


def test_the_invisibility_spell_breaks_on_a_strike_and_greater_does_not():
    """"Vanish from sight for 15 turns; breaks on attack": it never broke, so
    Greater Invisibility ("attacking does NOT break it") was only longer."""
    g = _game()
    _cast(g, 'invisibility_spell')
    assert g.player.status_effects.get('invisible', 0) > 0
    g._ring_veil_slips()                               # a blow, a shot, a spell at a foe
    assert not g.player.status_effects.get('invisible', 0)
    _cast(g, 'greater_invisibility_spell')
    left = g.player.status_effects.get('invisible', 0)
    assert left > 0
    g._ring_veil_slips()
    assert g.player.status_effects.get('invisible', 0) == left


def test_power_word_kill_says_its_real_rule():
    """Its desc said "HP at or below INT x 20"; it kills a share of the
    foe's own health (game_magic.DEATH_WORD_*)."""
    from spells import LEARNABLE_SPELLS
    import game_magic
    d = LEARNABLE_SPELLS['power_word_kill_spell']['desc']
    assert 'INT x' not in d
    assert 'quarter' in d and f"{round(game_magic.DEATH_WORD_CAP * 100)}%" in d
    assert game_magic.DEATH_WORD_BASE == 0.25 and game_magic.DEATH_WORD_PER_INT == 0.01


def test_the_robe_of_the_magus_does_not_weave_at_a_corpse():
    """The second weave of a tier-5 spell was cast at the foe the first had
    killed: "Holy fire smites the Goblin for 2067 damage!" of a corpse."""
    import chain_passives
    g = _game()
    gob = _beside(g, 'goblin')
    orig = chain_passives.player_has_passive
    chain_passives.player_has_passive = lambda p, f: f == 'double_cast_at_peak_tier' or orig(p, f)
    try:
        _cast(g, 'judgment_spell')
    finally:
        chain_passives.player_has_passive = orig
    assert not gob.alive
    assert not any('a second time' in t for t in _texts(g, 12))


# --------------------------------------------------------------- the V menu

def test_a_quirk_power_with_nothing_to_do_keeps_its_use():
    """Mind Fortress, Reality Anchor, Phoenix Rising, Life Drain, Metabolic
    and the Iron Ration spent one of their few uses doing nothing."""
    g = _game()
    p = g.player
    p.status_effects = {k: v for k, v in p.status_effects.items() if v == -1}
    p.hp = p.max_hp
    p.sp = p.max_sp
    for pid in ('mind_fortress', 'reality_anchor', 'phoenix_rising', 'life_drain',
                'metabolic', 'iron_ration'):
        p.power_uses[pid] = 2
        assert g._activate_power(pid) is True, pid        # no turn passes
        assert p.power_uses[pid] == 2, pid
    # With something to do, the use goes.
    p.status_effects['confused'] = 5
    assert g._activate_power('mind_fortress') is False
    assert p.power_uses['mind_fortress'] == 1 and not p.status_effects.get('confused')


def test_a_cure_power_leaves_what_the_gear_holds():
    """Reality Anchor and Mind Fortress popped every debuff, a worn -1 one
    (the Blindfold's dark) and the crossbow's crank among them."""
    g = _game()
    p = g.player
    p.status_effects['blinded'] = -1
    p.status_effects['reloading'] = 2
    p.status_effects['poisoned'] = 4
    p.power_uses['reality_anchor'] = 1
    g._activate_power('reality_anchor')
    assert p.status_effects.get('blinded') == -1
    assert p.status_effects.get('reloading') == 2
    assert not p.status_effects.get('poisoned')


def test_the_lyre_holds_the_nearest_foe_that_can_be_held():
    """The Lyre of Orpheus and the Hand of Glory spent a charge on the
    nearest creature even when it could not be held and another could."""
    g = _game()
    lyre = _item('accessory', 'lyre_of_orpheus')
    g.player._apply_equip(lyre)
    g._sees_monster = lambda m: True
    swarm = _beside(g, 'scarab_swarm', dist=1)
    rat = _beside(g, 'giant_rat', dist=2)
    before = lyre.charges
    g._activate_accessory_charge('lyre_of_orpheus')
    assert not swarm.status_effects.get('paralyzed', 0)
    assert rat.status_effects.get('paralyzed', 0) > 0
    assert lyre.charges == before - 1
    # Only a creature that cannot be held: the charge is kept, no turn.
    g.monsters = [swarm]
    assert g._activate_accessory_charge('lyre_of_orpheus') is True
    assert lyre.charges == before - 1


def test_gleipnir_with_no_wolf_spends_no_turn():
    g = _game()
    assert g._activate_power('bind_odinkiller') is True


def test_the_stuffies_fire_breath_is_fire():
    import inspect
    import game_combat
    src = inspect.getsource(game_combat.CombatMixin._confirm_power_target)
    i = src.index('cone = get_cone_tiles')
    assert "m._is_named_foe()),\n" in src[i:i + 800] and "'fire')" in src[i:i + 800]


def test_gilgameshs_bribe_with_no_taker_spends_no_turn():
    """No one in sight to take gold, or too little gold: it spent a turn."""
    g = _game()
    assert g._activate_gold_offering() is True         # nothing in sight to take gold


def test_a_family_stun_is_not_said_of_one_that_cannot_be_stunned(monkeypatch):
    """stun_on_hit held the stun through Monster.hold (refused by its nature)
    and said the technique's line all the same."""
    import family_edges
    from player import Player
    p = Player()
    m = _mon('giant_rat')
    m.status_immune = ['stunned']
    told = []
    monkeypatch.setattr(family_edges, 'stun_on_hit', lambda pl, t, c: ({'name': 'X'}, {'turns': 2}))
    monkeypatch.setattr(family_edges, 'tell', lambda pl, t, a, **k: told.append(a) or True)
    for name in ('execute', 'turn_on_hit', 'charm_on_hit', 'surrender'):
        monkeypatch.setattr(family_edges, name, lambda *a, **k: None)
    monkeypatch.setattr(family_edges, 'block_regen_turns', lambda pl, t: 0)
    family_edges.after_blow(p, m, 5, 10)
    assert told == [] and not m.status_effects.get('stunned', 0)
    m.status_immune = []
    family_edges.after_blow(p, m, 5, 10)
    assert told and m.status_effects.get('stunned', 0) == 2


def test_atalantas_choice_is_said_only_when_it_holds_something():
    import inspect
    import main
    src = inspect.getsource(main.Game._change_level)
    i = src.index("Atalanta's choice! Time itself pauses")
    assert 'if _held:' in src[i - 300:i]


def test_orpheus_slows_through_monster_hold():
    import inspect
    import main
    src = inspect.getsource(main.Game._change_level)
    i = src.index("orpheus_active")
    assert "m.hold('slowed', 5)" in src[i:i + 400]


def test_a_hero_specials_cleanse_lifts_what_a_cure_lifts():
    """Harmony of Spheres and Viriditas popped debuffs at random, a worn -1
    one (the Blindfold's dark) and the crossbow's crank among them."""
    import hero_specials as hs
    g = _game()
    p = g.player
    p.hp = 1
    for build in ('pythagoras of samos', 'saint hildegard von bingen'):
        sp = hs.HERO_SPECIALS[build]
        p.status_effects['blinded'] = -1
        p.status_effects['reloading'] = 2
        p.status_effects['poisoned'] = 4
        hs.resolve_active_special(g, sp, 5)
        assert p.status_effects.get('blinded') == -1, build
        assert p.status_effects.get('reloading') == 2, build
        assert not p.status_effects.get('poisoned'), build
