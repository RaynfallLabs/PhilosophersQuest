"""Monster family knowledge, the logic (src/family_lore.py, src/family_edges.py,
src/game_families.py; MONSTER_FAMILIES_DESIGN.md, the v2 design and the
2026-10-18 rulings).

Progress is DISTINCT kinds studied (a known kind's corpse never asks again;
a keystone counts two kinds); the Book of Thoth opens pages and teaches no
tiers; old saves catch up without a popup flood; each technique primitive does
what its data says against its own family only; named foes are never
executed, turned, calmed, charmed, stunned or made to yield; hidden things stay
hidden except to the one technique that senses them, inside its radius.

Late-game content: logic tests, not play-tests (CLAUDE.md).
"""
import os
import pickle
import random
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))

import json  # noqa: E402

import pygame  # noqa: E402

pygame.init()

import family_edges  # noqa: E402
import family_lore  # noqa: E402
from player import Player  # noqa: E402

MONS = json.load(open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8'))
_SCREEN = None


def _screen():
    global _SCREEN
    if _SCREEN is None:
        _SCREEN = pygame.display.set_mode((1280, 720))
    return _SCREEN


def _mon(kind, x=5, y=5):
    from monster import Monster
    return Monster({**MONS[kind], 'id': kind}, x, y)


def _plain(fid, n, exclude=()):
    """n ordinary (non-keystone) kinds of a family."""
    out = [k for k in family_lore.members(fid)
           if k in MONS and not family_lore.is_keystone(k) and k not in exclude]
    assert len(out) >= n, fid
    return out[:n]


def _to_tier(p, fid, t, exclude=()):
    need = family_lore.thresholds(fid)[t - 1]
    p.studied_monster_ids.update(_plain(fid, need, exclude))
    assert family_lore.tier(p, fid) == t, (fid, family_lore.tier(p, fid))


def _param(aid, effect, key):
    """A technique's number, read from the data (the balance pass tunes it)."""
    for f in family_lore.families().values():
        for t in f['tiers']:
            for a in t['abilities']:
                if a['id'] == aid:
                    for part in [a] + list(a.get('also', ())):
                        if part['effect'] == effect:
                            return part['params'][key]
    raise KeyError(aid)


def _circle_param(cid, key):
    return family_lore.circles()[cid]['boon']['params'][key]


def _player_at(x=10, y=10):
    p = Player()
    p.x, p.y = x, y
    return p


# ---------------------------------------------------------------------------
# Progress: distinct kinds, keystones, both rules of a tier
# ---------------------------------------------------------------------------
def test_progress_counts_distinct_kinds_only():
    p = Player()
    kinds = _plain('restless_dead', 3)
    for k in kinds:
        assert family_lore.record_study(p, k) is True
    assert family_lore.score(p, 'restless_dead') == 3
    assert family_lore.tier(p, 'restless_dead') == 0          # T1 needs 4
    family_lore.record_study(p, _plain('restless_dead', 4)[3])
    assert family_lore.tier(p, 'restless_dead') == 1


def test_the_same_kind_twice_adds_nothing():
    p = Player()
    assert family_lore.record_study(p, 'skeleton') is True
    assert family_lore.record_study(p, 'skeleton') is False
    assert family_lore.score(p, 'restless_dead') == 1
    assert family_lore.studied_count(p, 'restless_dead') == 1


def test_a_keystone_counts_two_kinds():
    p = Player()
    family_lore.record_study(p, 'arachne')                    # a mini-boss
    assert family_lore.score(p, 'vermin') == 2
    assert family_lore.studied_count(p, 'vermin') == 1
    assert family_lore.tier(p, 'vermin') == 1                  # vermin T1 needs 2
    q = Player()
    family_lore.record_study(q, 'spider_queen')                # listed in the family's keystones
    assert family_lore.score(q, 'vermin') == 2


def test_no_family_kinds_are_never_studied():
    p = Player()
    for kind in ('death', 'secret_cow', 'ethereal_unicorn'):
        assert family_lore.record_study(p, kind) is False
    assert not p.studied_monster_ids


def test_every_tier_needs_its_own_threshold():
    p = Player()
    th = family_lore.thresholds('oozes')
    kinds = _plain('oozes', th[-1])
    for n, k in enumerate(kinds, start=1):
        family_lore.record_study(p, k)
        assert family_lore.tier(p, 'oozes') == sum(1 for need in th if n >= need)
    assert family_lore.progress(p, 'oozes')['line'] == 'Every tier learned'


def test_the_book_of_thoth_gives_no_tiers():
    p = Player()
    p.lore_known_monster_ids.update(family_lore.members('restless_dead'))
    assert family_lore.tiers(p) == {}
    assert family_lore.has_page(p, 'skeleton')                 # its page is open
    assert not p.studied_monster_ids


def test_old_saves_catch_up_without_a_popup_flood():
    p = Player()
    kinds = _plain('restless_dead', 9)
    p.lore_known_monster_ids = set(kinds)
    state = p.__dict__.copy()
    for k in ('studied_monster_ids', 'family_tiers_told', 'family_lore_grants'):
        state.pop(k, None)
    old = Player.__new__(Player)
    old.__setstate__(state)
    assert old.studied_monster_ids == set(kinds)
    assert family_lore.tier(old, 'restless_dead') == 2
    assert family_lore.news(old) == []                         # all told already
    # The retired mastery names are still deleted on load.
    state2 = dict(state, family_masteries={'undead': 5}, family_mastery_blessings={'x': 1})
    old2 = Player.__new__(Player)
    old2.__setstate__(state2)
    assert not hasattr(old2, 'family_masteries')
    assert not hasattr(old2, 'family_mastery_blessings')


def test_a_new_player_pickles_and_reloads_its_knowledge():
    p = Player()
    family_lore.record_study(p, 'skeleton')
    p.__dict__['_edge_msgs'] = ['x']
    family_lore.tiers(p)
    q = pickle.loads(pickle.dumps(p))
    assert q.studied_monster_ids == {'skeleton'}
    assert '_edge_msgs' not in q.__dict__ and '_family_tier_cache' not in q.__dict__


def test_news_comes_once_and_in_order():
    p = Player()
    _to_tier(p, 'vermin', 3)
    news = family_lore.news(p)
    assert news == [('tier', 'vermin', 1), ('tier', 'vermin', 2), ('tier', 'vermin', 3)]
    assert family_lore.news(p) == []


# ---------------------------------------------------------------------------
# Circles and the Loremaster title
# ---------------------------------------------------------------------------
def test_a_circle_is_worked_out_from_the_tiers_and_told_once():
    p = Player()
    for fid in ('restless_dead', 'ghosts'):
        _to_tier(p, fid, 3)
    assert not family_lore.circle_complete(p, 'grave_watch')
    _to_tier(p, 'vampires_liches', 3)
    assert family_lore.circle_complete(p, 'grave_watch')
    news = family_lore.news(p)
    assert ('circle', 'grave_watch', None) in news
    assert ('circle', 'grave_watch', None) not in family_lore.news(p)
    # Vigil: necrotic and drain hurt 20% less, whoever deals them.
    assert family_edges.any_damage_mult(p, 'necrotic') == _circle_param('grave_watch', 'mult') < 1
    assert family_edges.any_damage_mult(p, 'fire') == 1.0


def test_the_wild_road_takes_any_three_and_gives_sight():
    p = Player()
    base = p.get_sight_radius()
    for fid in ('birds', 'plants', 'oozes'):
        _to_tier(p, fid, 3)
    assert not family_lore.circle_complete(p, 'wild_road')    # oozes are not on the road
    _to_tier(p, 'serpents', 3)
    assert family_lore.circle_complete(p, 'wild_road')
    assert p.get_sight_radius() == base + 1


def test_loremaster_needs_bane_in_five_families():
    p = Player()
    for fid in ('oozes', 'plants', 'birds', 'gorgons'):
        _to_tier(p, fid, 5)
    assert not family_lore.is_loremaster(p)
    _to_tier(p, 'celestials', 5)
    assert family_lore.is_loremaster(p)
    assert ('loremaster', None, None) in family_lore.news(p)


# ---------------------------------------------------------------------------
# Defence primitives
# ---------------------------------------------------------------------------
def test_save_bonus_is_four_against_its_family_only(monkeypatch):
    import status_effects
    p = _player_at()
    _to_tier(p, 'restless_dead', 3)
    ghoul, imp = _mon('ghoul'), _mon('imp')
    ward = _param('restless_dead_grave_salt', 'save_bonus', 'amount')
    assert ward > 0
    assert family_edges.save_bonus(p, ghoul, 'paralyzed') == ward
    assert family_edges.save_bonus(p, ghoul, 'confused') == 0
    assert family_edges.save_bonus(p, imp, 'paralyzed') == 0
    # Seeded: a roll that fails by two passes with the ward.
    dc = 15
    mod = (p.CON - 10) // 2
    roll_needed = dc - mod - p.save_bonus_for('CON') - ward
    monkeypatch.setattr(random, 'randint', lambda a, b: roll_needed)
    p.status_effects.clear()
    applied, _ = status_effects.apply_debuff_with_save(p, 'paralyzed', 3, dc, source=imp)
    assert applied
    p.status_effects.clear()
    applied, msg = status_effects.apply_debuff_with_save(p, 'paralyzed', 3, dc, source=ghoul)
    assert not applied and 'throws off' in msg


def test_the_ward_sits_outside_the_save_cap():
    p = _player_at()
    p._save_bonus = {'all': 9}
    assert p.save_bonus_for('CON') == 5
    _to_tier(p, 'restless_dead', 3)
    assert family_edges.save_bonus(p, _mon('ghoul'), 'paralyzed') == \
        _param('restless_dead_grave_salt', 'save_bonus', 'amount')       # on top of the 5


def test_no_save_effects_wear_off_faster():
    import status_effects
    p = _player_at()
    rat = _mon('giant_rat')
    status_effects.apply_debuff_with_save(p, 'poisoned', 10, 12, source=rat)
    plain = p.status_effects.get('poisoned')
    p.status_effects.clear()
    _to_tier(p, 'vermin', 3)
    status_effects.apply_debuff_with_save(p, 'poisoned', 10, 12, source=rat)
    warded = p.status_effects.get('poisoned')
    share = _param('vermin_web_and_plague', 'duration_mult', 'mult')
    ward = _param('vermin_web_and_plague', 'save_bonus', 'amount')
    assert 0 < share < 1
    assert warded == max(1, max(1, round(10 * share)) - p.save_bonus_for('CON') - ward)
    assert warded < plain


def test_duration_zero_means_it_never_takes_hold():
    import status_effects
    p = _player_at()
    _to_tier(p, 'elementals', 5)                        # Solomon's Seal
    fire = _mon('fire_elemental')
    applied, msg = status_effects.apply_debuff_with_save(p, 'burning', 6, 12, source=fire)
    assert not applied and 'cannot take hold' in msg
    assert 'burning' not in p.status_effects


def test_the_drain_save_counts_the_ward(monkeypatch):
    p = _player_at()
    p.CON = 14
    wraith = _mon('wraith')
    dc = min(18, 12 + wraith.min_level // 7)
    mod = (p.CON - 10) // 2
    monkeypatch.setattr(random, 'randint', lambda a, b: dc - mod - 1)
    assert wraith._drain_takes_hold(p) is True
    _to_tier(p, 'ghosts', 3)
    assert wraith._drain_takes_hold(p) is False


def test_resist_damage_the_strongest_one_wins():
    p = _player_at()
    drake = _mon('drake_fire')
    assert family_edges.incoming_damage_mult(p, drake, 'fire') == 1.0
    _to_tier(p, 'dragons', 3)
    assert family_edges.incoming_damage_mult(p, drake, 'fire') == \
        _param('dragons_dragon_ward', 'resist_damage', 'mult') < 1
    assert family_edges.incoming_damage_mult(p, drake, 'slash') == 1.0
    q = _player_at()
    _to_tier(q, 'elementals', 5)
    seal = _param('elementals_solomons_seal', 'resist_damage', 'mult')
    assert seal < _param('elementals_ward_of_elements', 'resist_damage', 'mult')
    assert family_edges.incoming_damage_mult(q, _mon('fire_elemental'), 'fire') == seal


def test_drain_heal_block_stops_a_vampire_feeding(monkeypatch):
    p = _player_at()
    v = _mon('vampire_lord')
    v.drain_heals_self = 1.0
    assert not family_edges.drain_heal_blocked(p, v)
    _to_tier(p, 'vampires_liches', 3)
    assert family_edges.drain_heal_blocked(p, v)


def test_perseus_shield_needs_a_shield():
    from items import instantiate_shield
    p = _player_at()
    medusa = _mon('medusa')
    _to_tier(p, 'gorgons', 4)
    p.shield = None
    assert not family_edges.gaze_immune(p, medusa)
    p.shield = instantiate_shield('buckler', 'iron') if True else None
    assert p.shield is not None
    assert family_edges.gaze_immune(p, medusa)
    assert not family_edges.gaze_immune(p, _mon('floating_eye'))      # an aberration


def test_theft_immune_keeps_the_purse(monkeypatch):
    import theft

    class G:
        player = _player_at()
        player_gold = 500
    g = G()
    thief = _mon('bandit_thief')
    thief._aware = True                     # it has sprung: the hero can see who it is
    _to_tier(g.player, 'mortals', 3)
    assert theft.steal(g, thief, 'gold') == ''
    assert g.player_gold == 500


# ---------------------------------------------------------------------------
# Offence primitives
# ---------------------------------------------------------------------------
def _sword_player():
    from items import instantiate_weapon
    p = _player_at()
    p.weapon = instantiate_weapon('longsword', 'iron')
    return p


def test_damage_mult_shows_in_the_strike_preview():
    import combat
    p = _sword_player()
    imp = _mon('imp')
    imp.hp = imp.max_hp = 10 ** 6
    before = combat.strike_preview(p, imp, 6)
    _to_tier(p, 'demons', 4)                                    # True Names
    after = combat.strike_preview(p, imp, 6)
    want = _param('demons_true_names', 'damage_mult', 'mult')
    assert abs(after / before - want) <= 0.04
    goblin = _mon('goblin')
    goblin.hp = goblin.max_hp = 10 ** 6
    assert family_edges.damage_mult(p, goblin, 6, p.weapon) == 1.0  # another family


def test_damage_mult_needs_its_chain_and_counts_big_targets():
    p = _sword_player()
    _to_tier(p, 'giants', 5)
    ogre = _mon('ogre')
    aid = 'giants_bigger_they_are'
    assert family_edges.damage_mult(p, ogre, _param(aid, 'damage_mult', 'chain_min') - 1,
                                    p.weapon) == 1.0
    assert family_edges.damage_mult(p, ogre, 5, p.weapon) == _param(aid, 'damage_mult', 'mult')
    ogre.footprint = (2, 2)
    assert family_edges.damage_mult(p, ogre, 5, p.weapon) == _param(aid, 'damage_mult', 'big_mult')


def test_damage_mult_weapon_conditions():
    from items import instantiate_weapon
    p = _player_at()
    _to_tier(p, 'shapeshifters', 4)                             # Silvered
    wolf = _mon('werewolf')
    aid = 'shapeshifters_silvered'
    assert family_edges.damage_mult(p, wolf, 3, instantiate_weapon('longsword', 'iron')) == \
        _param(aid, 'damage_mult', 'mult')
    assert family_edges.damage_mult(p, wolf, 3, instantiate_weapon('longsword', 'silver')) == \
        _param(aid, 'damage_mult', 'weapon_mult')
    q = _player_at()
    _to_tier(q, 'birds', 4)                                     # Falconer's Eye
    harpy = _mon('harpy')
    eye = _param('birds_falconers_eye', 'damage_mult', 'mult')
    assert family_edges.damage_mult(q, harpy, 3, None) == 1.0
    assert family_edges.damage_mult(q, harpy, 3, None, ranged=True) == eye > 1.0
    assert family_edges.damage_mult(q, harpy, 3, None, thrown=True) == eye


def test_damage_mult_never_on_an_unseen_target():
    p = _sword_player()
    _to_tier(p, 'ghosts', 6 - 1)
    wraith = _mon('dread_wraith')                               # invisible
    p.x, p.y = wraith.x + 8, wraith.y                            # outside Second Sight's 3
    assert family_edges.damage_mult(p, wraith, 6, p.weapon) == 1.0


def test_weakness_amp_only_on_a_weakness():
    p = _player_at()
    _to_tier(p, 'restless_dead', 4)                             # Bonebreaker
    sk = _mon('skeleton')
    assert family_edges.weakness_amp(p, sk, True) == _param('restless_dead_bonebreaker',
                                                            'weakness_amp', 'mult') > 1.0
    assert family_edges.weakness_amp(p, sk, False) == 1.0


def test_extra_seconds_reach_the_combat_clock():
    import combat
    p = _sword_player()
    ogre = _mon('ogre')
    got = {}

    class Q:
        def start_quiz(self, **kw):
            got.update(kw)
    combat.player_attack(p, ogre, Q(), lambda *a, **k: None)
    plain = got['extra_seconds']
    _to_tier(p, 'giants', 3)                                    # Steady Hand
    combat.player_attack(p, ogre, Q(), lambda *a, **k: None)
    assert got['extra_seconds'] == plain + _param('giants_steady_hand', 'extra_seconds', 'seconds')


def test_opening_chain_on_the_first_blow_only():
    import combat
    p = _sword_player()
    snake = _mon('cobra')
    assert combat.effective_chain(p, snake, p.weapon, 3, consume=False) == 3
    _to_tier(p, 'serpents', 4)                                  # Mongoose
    assert combat.effective_chain(p, snake, p.weapon, 3, consume=False) == 4
    assert combat.effective_chain(p, snake, p.weapon, 3, consume=True) == 4
    assert combat.effective_chain(p, snake, p.weapon, 3, consume=True) == 3
    assert combat.effective_chain(p, snake, p.weapon, 0, consume=False) == 0   # a miss stays a miss


def test_chain_forgive_once_per_fight():
    from quiz_engine import QuizEngine, QuizState
    p = _player_at()
    hydra = _mon('hydra')
    _to_tier(p, 'legend', 5)                                    # Know the Story
    assert family_edges.chain_forgive_ready(p, hydra)
    q = QuizEngine()
    q._forgive_flag = True
    q.start_quiz(mode='chain', subject='math', tier=1, callback=lambda r: None, timed=False)
    q.answer('definitely not the answer')
    q._advance()
    assert q.state == QuizState.ASKING and q.forgive_was_used
    q.answer('still not the answer')
    q._advance()
    assert q.state != QuizState.ASKING
    family_edges.spend_chain_forgive(p, hydra)
    assert not family_edges.chain_forgive_ready(p, hydra)
    assert family_edges.chain_forgive_ready(p, _mon('chimera'))   # a new fight


def test_pierce_resist_undoes_a_resistance():
    import combat
    from items import instantiate_weapon
    p = _player_at()
    p.weapon = instantiate_weapon('longsword', 'iron')
    golem = _mon('iron_golem')
    golem._aware = True
    golem.resistances = list(p.weapon.damage_types)             # every form it has
    golem.weaknesses = []
    golem.hp = golem.max_hp = 10 ** 6
    plain = combat.strike_preview(p, golem, 6)
    _to_tier(p, 'constructs', 4)                                # Find the Seam, chain 5
    assert combat.strike_preview(p, golem, 4) <= plain * 4 / 6 + 2
    assert combat.strike_preview(p, golem, 6) >= plain * 1.8


def test_block_regen_and_prevent_split():
    import splitting
    p = _player_at()
    troll = _mon('troll')
    troll.regeneration = 10
    _to_tier(p, 'giants', 4)
    family_edges.after_blow(p, troll, 3, 5)
    troll.hp = troll.max_hp - 50
    before = troll.hp
    troll.tick_effects()
    assert troll.hp == before                                   # the wound stays open
    pud = _mon('black_pudding')
    q = _player_at()
    _to_tier(q, 'oozes', 4)
    assert family_edges.prevents_split(q, pud)
    pud.__dict__['_no_split_blow'] = True
    assert splitting.blow_splits(pud, 1, 'slash') is False


def test_execute_ends_a_lesser_foe_and_hits_a_named_one_harder():
    p = _player_at()
    _to_tier(p, 'vampires_liches', 5)                           # Stake Through the Heart
    v = _mon('vampire')
    need = _param('vampires_liches_stake', 'execute', 'chain_min')
    v.hp = int(v.max_hp * _param('vampires_liches_stake', 'execute', 'hp_below') * 0.8)
    assert family_edges.after_blow(p, v, need - 1, 1)['executed'] is None   # chain too short
    out = family_edges.after_blow(p, v, need, 1)
    assert out['executed'] is not None and not v.alive
    neb = _mon('neferkaptah_risen')                             # proper_noun, not a named FOE
    lord = _mon('vampire_lord')
    lord.is_mini_boss = True
    lord.hp = int(lord.max_hp * _param('vampires_liches_stake', 'execute', 'hp_below') * 0.8)
    assert family_edges.execute(p, lord, need) is None
    assert family_edges.execute_named_mult(p, lord, need) == 1.25
    assert family_edges.execute_named_mult(p, lord, need - 1) == 1.0
    assert neb.alive


def test_turn_sends_lesser_members_in_sight_fleeing_never_a_named_foe():
    p = _player_at()
    _to_tier(p, 'restless_dead', 5)                             # Turn the Dead
    a, b, c = _mon('skeleton', 3, 3), _mon('zombie', 4, 4), _mon('ghoul', 30, 30)
    boss = _mon('skeleton_champion', 5, 3)
    boss.is_mini_boss = True
    imp = _mon('imp', 6, 6)
    vis = {(3, 3), (4, 4), (5, 3), (6, 6)}
    need = _param('restless_dead_turn_the_dead', 'turn', 'chain_min')
    family_edges.after_blow(p, a, need - 1, 5, monsters=[a, b, c, boss, imp], visible=vis)
    assert not b.has_effect('feared')                           # chain too short
    family_edges.after_blow(p, a, need, 5, monsters=[a, b, c, boss, imp], visible=vis)
    assert a.has_effect('feared') and b.has_effect('feared')
    assert not c.has_effect('feared')                           # out of sight
    assert not boss.has_effect('feared')                        # named foes stand
    assert not imp.has_effect('feared')                         # another family


def test_calm_on_arrival_and_its_rail():
    p = _player_at()
    _to_tier(p, 'celestials', 5)                                # Entertaining Angels
    peg = _mon('pegasus')
    angel = _mon('corrupted_angel')
    angel.is_boss = True

    class AlwaysCalm:
        def random(self):
            return 0.0                                          # every roll succeeds
    family_edges.calm_arrivals(p, [peg, angel], rng=AlwaysCalm())
    assert peg.has_effect('charmed') and peg.__dict__.get('_bribed')
    assert not angel.has_effect('charmed')
    peg.take_damage(1)                                          # a blow breaks the calm
    assert not peg.has_effect('charmed')


def test_charm_stun_and_surrender_on_hit():
    p = _player_at()
    _to_tier(p, 'serpents', 5)
    snake = _mon('rock_python')
    family_edges.after_blow(p, snake, 8, 3)
    assert snake.has_effect('charmed')
    q = _player_at()
    _to_tier(q, 'shapeshifters', 5)
    wolf = _mon('werewolf')
    family_edges.after_blow(q, wolf, 8, 3)
    assert wolf.has_effect('stunned')
    r = _player_at()
    _to_tier(r, 'mortals', 5)
    bandit = _mon('bandit_thug')
    bandit.hp = int(bandit.max_hp * 0.4)
    out = family_edges.after_blow(r, bandit, 8, 1)
    assert out['surrendered'] and bandit.has_effect('feared')
    assert family_edges.after_blow(r, bandit, 8, 1)['surrendered'] is None   # once


def test_harvest_bonus_gives_one_more_portion():
    import food_system
    from items import Corpse
    p = _player_at()
    corpse = Corpse('cave bear', 'cave_bear', 0, 0, harvest_tier=1)
    got = {}

    class Q:
        def start_quiz(self, **kw):
            class R:
                success = True
            kw['callback'](R())
    food_system.harvest_corpse(p, corpse, Q(), lambda ings, msg: got.update(n=len(ings)))
    plain = got['n']
    _to_tier(p, 'great_beasts', 3)
    food_system.harvest_corpse(p, corpse, Q(), lambda ings, msg: got.update(n=len(ings), msg=msg))
    assert got['n'] == plain + 1 and "Hunter's Harvest" in got['msg']


# ---------------------------------------------------------------------------
# Seeing the hidden: family only, radius limited
# ---------------------------------------------------------------------------
def test_sense_hidden_is_family_only_and_radius_limited():
    import unseen
    p = _player_at(10, 10)
    wraith = _mon('dread_wraith', 12, 10)                       # invisible ghost, 2 away
    assert unseen.concealed(wraith, p)
    _to_tier(p, 'ghosts', 4)                                    # Second Sight, radius 3
    assert not unseen.concealed(wraith, p)
    wraith.x = 14                                               # 4 away
    assert unseen.concealed(wraith, p)
    hulder = _mon('huldufolk_raider', 11, 10)                   # invisible, Fair Folk
    assert unseen.concealed(hulder, p)                          # Second Sight is for ghosts


def test_a_disguised_mimic_stays_hidden_except_to_mimic_sense():
    import unseen
    for kind in ('gilded_mimic', 'lurking_horror'):
        m = _mon(kind, 12, 10)
        assert m.ai_pattern == 'mimic' and unseen.disguise(m)
        p = _player_at(10, 10)
        for fid in family_lore.families():
            if fid != 'aberrations':
                _to_tier(p, fid, 5)
        assert unseen.concealed(m, p), kind                     # nothing else sees it
        _to_tier(p, 'aberrations', 3)
        assert unseen.concealed(m, p), kind                     # tier 3 is not enough
        _to_tier(p, 'aberrations', 4)
        assert not unseen.concealed(m, p), kind                 # Mimic-Sense, 2 tiles
        m.x = 13
        assert unseen.concealed(m, p), kind                     # 3 tiles: hidden again


def test_tremor_sense_shows_a_lurking_spider_and_o_works_on_it():
    import unseen
    p = _player_at(10, 10)
    sp = _mon('phase_spider_lesser', 12, 12)
    sp.ai_pattern, sp._aware = 'ambush', False
    assert unseen.concealed(sp, p)
    _to_tier(p, 'vermin', 4)
    assert not unseen.concealed(sp, p)
    assert unseen.seen_monster_at([sp], 12, 12, p) is sp


# ---------------------------------------------------------------------------
# The Game: studying, news, arrival lines, head starts
# ---------------------------------------------------------------------------
def _game(name='__test_families__'):
    from main import Game
    from game_states import STATE_PLAYER
    from welcome_screen import SECRET_BUILDS
    random.seed(7)
    g = Game(_screen(), player_name=name, secret_build=SECRET_BUILDS.get(name))
    g.monsters = []
    g.pets = []
    g.state = STATE_PLAYER
    return g


def _study(g, kind, success=True):
    from items import Corpse

    class R:
        pass
    R.success = success
    corpse = Corpse(MONS[kind]['name'], kind, g.player.x, g.player.y, harvest_tier=1,
                    monster_def={'tags': MONS[kind]['tags']})
    g.ground_items.append(corpse)
    g.quiz_engine.start_quiz = lambda **kw: kw['callback'](R())
    g._start_corpse_identify(corpse, after_advance_turn=False)
    return corpse


def test_a_right_answer_studies_the_kind_and_a_wrong_one_stuns():
    g = _game()
    _study(g, 'skeleton', success=False)
    assert 'skeleton' not in g.player.studied_monster_ids
    assert g.player.status_effects.get('stunned', 0) >= 10
    g.player.status_effects.clear()
    _study(g, 'skeleton', success=True)
    assert 'skeleton' in g.player.studied_monster_ids


def test_tier_news_messages_popups_and_journal():
    import chronicle
    from game_states import STATE_LORE, STATE_STORY_POPUP
    g = _game()
    kinds = _plain('vermin', 5)
    for k in kinds[:2]:
        _study(g, k)
    texts = [str(e[0]) for e in g.msg_log.entries]
    assert any('You know the vermin and spiders now' in t for t in texts)
    for k in kinds[2:]:
        g.state = STATE_LORE
        _study(g, k)
    assert g.state == STATE_STORY_POPUP and g.popup_data['title'] == 'LORE OF THE VERMIN AND SPIDERS'
    assert any(line.startswith('Web and Plague: ') for line in g.popup_data['lines'])
    assert g.popup_next_state == STATE_LORE                     # back to the lore page
    lines = [e.get('text') for e in chronicle.entries_of(g)]
    assert any('the vermin and spiders apart' in (t or '') for t in lines)
    keys = [e.get('once') for e in chronicle.entries_of(g)]
    assert 'family:vermin:1' in keys and 'family:vermin:3' in keys


def test_arrival_lines_skip_disguised_mimics_and_invisible_monsters():
    g = _game()
    _to_tier(g.player, 'aberrations', 2)
    _to_tier(g.player, 'ghosts', 2)
    g.monsters = [_mon('gilded_mimic'), _mon('dread_wraith')]
    g.msg_log.entries.clear() if hasattr(g.msg_log.entries, 'clear') else None
    g._family_arrival(first_visit=False)
    texts = [str(e[0]) for e in g.msg_log.entries]
    assert not any('aberrations lurk' in t or 'ghosts drift' in t for t in texts)
    g.monsters = [_mon('beholder'), _mon('wraith')]
    g._family_arrival(first_visit=False)
    texts = [str(e[0]) for e in g.msg_log.entries]
    assert any('aberrations lurk' in t for t in texts) and any('ghosts drift' in t for t in texts)


def test_arrival_lines_stop_at_three_then_combine():
    p = Player()
    fams = ['restless_dead', 'ghosts', 'demons', 'dragons', 'goblinkin']
    picks = {'restless_dead': 'skeleton', 'ghosts': 'wraith', 'demons': 'imp',
             'dragons': 'wyvern', 'goblinkin': 'goblin'}
    for fid in fams:
        p.family_lore_grants[fid] = 2
    lines = family_lore.arrival_lines(p, [_mon(picks[f]) for f in fams],
                                      concealed=lambda m: False, is_ally=lambda m: False)
    assert len(lines) == 3
    assert lines[-1].startswith('You sense more on this floor:')


def test_secret_build_head_starts_are_silent_and_never_edges():
    g = _game('geralt of rivia')
    t = family_lore.tiers(g.player)
    for fid in ('restless_dead', 'ghosts', 'vampires_liches', 'shapeshifters'):
        assert t.get(fid) == 2, fid
    assert family_lore.news(g.player) == []                     # nothing announced
    assert family_edges.save_bonus(g.player, _mon('ghoul'), 'paralyzed') == 0
    a = _game('aristotle of stagira')
    assert {f: v for f, v in family_lore.tiers(a.player).items()} == {
        'great_beasts': 1, 'birds': 1, 'serpents': 1, 'vermin': 1}
    s = _game('socrates of athens')
    assert family_lore.tiers(s.player) == {}                   # he knows that he knows nothing
    from welcome_screen import SECRET_BUILDS
    for key, b in SECRET_BUILDS.items():
        for fid, tier in (b.get('_start_family_lore') or {}).items():
            assert fid in family_lore.families() and tier in (1, 2), (key, fid)


def test_yield_drops_the_purse_as_a_gold_pile():
    from items import GoldPile
    g = _game()
    m = _mon('bandit_thug', g.player.x + 1, g.player.y)
    m.treasure = {'gold': [40, 40]}
    g._family_surrender(m)
    piles = [i for i in g.ground_items if isinstance(i, GoldPile) and (i.x, i.y) == (m.x, m.y)]
    assert piles and sum(getattr(pl, 'amount', 0) for pl in piles) >= 40
    assert m.treasure['gold'] == [0, 0]


def test_the_qa_key_raises_a_tier_only_for_the_qa_build():
    g = _game()
    g._qa_family_tier()
    assert family_lore.tiers(g.player) == {}
    g.player.qa_tools = True
    g._qa_family_tier()
    assert all(v == 1 for v in family_lore.tiers(g.player).values())
    assert len(family_lore.tiers(g.player)) == 22


def test_old_saved_monsters_and_corpses_find_their_family_by_kind():
    from items import Corpse
    m = _mon('ghoul')
    del m.__dict__['family']                    # a monster pickled before families
    assert m.family == 'restless_dead'
    c = Corpse('ghoul', 'ghoul', 0, 0)
    assert 'family' not in c.__dict__
    assert family_lore.family_of(c) == 'restless_dead'
    from bones import spawn_ghost  # noqa: F401  (the Bones ghost is a Ghost)
    assert family_lore.family_of('player_ghost') == 'ghosts'
