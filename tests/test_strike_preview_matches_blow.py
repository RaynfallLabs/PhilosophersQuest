"""Call 13 (bug bash 4): the combat strip's "Strike Now N Damage" is the
blow's own number.

Before, the strip did its own sum ((base + enchant) x chain x form x
substance) and left out Strength, blessings, ammo, the ranged stat bonus,
weakened, shields, dragon scales, Abaddon's ward and the gear bonuses, so the
number a child was shown was not the number dealt (14 shown, 20 dealt at STR
18; 21 shown, 4 dealt against Fafnir). Now the real blow and the preview both
call combat.effective_chain + combat.strike_damage.

These drive the REAL combat.player_attack (a stub quiz engine hands its
callback the score) and compare what it deals with what the preview says
just before, across every common weapon template, a spread of materials,
targets with resistances / weaknesses / scales / ward / shield, player
states and chains up to 20. Dice-based bonuses are random and excluded.
"""
import json
import os
import sys
import types

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import combat  # noqa: E402
import items  # noqa: E402
from monster import Monster  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    _DEFS = json.load(_f)

TEMPLATES = sorted(items.load_templates('weapons'))
MATERIALS = ('iron', 'oak', 'silver', 'cold_iron', 'mithril', 'adamantine', 'yew',
             'void_touched')
TARGETS = ('giant_rat', 'zombie', 'wraith', 'gelatinous_cube', 'fafnir_dragon',
           'abaddon_destroyer', 'goblin', 'cave_spider')


class _Quiz:
    """Stands in for QuizEngine: the attack's callback gets ``score``."""
    def __init__(self, score):
        self.score = score

    def start_quiz(self, callback=None, **_kw):
        callback(types.SimpleNamespace(score=self.score, success=True))


def _target(kind):
    m = Monster(dict(_DEFS[kind], id=kind), 6, 5)
    m.hp = m.max_hp = 10 ** 8          # never dies, never revives
    return m


def _make(template, material, *, buc='uncursed', enchant=0):
    try:
        return items.instantiate_weapon(template, material, buc=buc, enchant=enchant)
    except Exception:
        return None


def _player(weapon, *, STR=10, PER=10, ranged=False):
    p = Player()
    p.x, p.y = 5, 5
    p.STR, p.PER = STR, PER
    p.hp = p.max_hp = 10 ** 6
    if ranged:
        p.ranged_weapon = weapon
    else:
        p.weapon = weapon
    return p


def _blow(p, m, score, *, ranged=False, ammo=None):
    """(preview, dealt) for one attack at quiz score ``score``."""
    preview = combat.strike_preview(p, m, score, ranged=ranged, ammo=ammo)
    got = []
    combat.player_attack(p, m, _Quiz(score), lambda dmg, *a, **k: got.append(dmg),
                         ammo=ammo, ranged=ranged)
    return preview, got[0]


def _is_ranged(template):
    return bool(items.load_templates('weapons')[template].get('requires_ammo')) \
        or template == 'sling'


def test_preview_equals_dealt_across_weapons_targets_and_chains():
    checked = 0
    mismatches = []
    for template in TEMPLATES:
        ranged = _is_ranged(template)
        for material in MATERIALS:
            w = _make(template, material)
            if w is None:
                continue
            for kind in TARGETS:
                for score in (1, 3, 5, 10, 15, 20):
                    p = _player(w, ranged=ranged, STR=14, PER=16)
                    m = _target(kind)
                    ammo = None
                    if ranged and w.requires_ammo == 'arrow':
                        ammo = items.make_item_by_id('ammo', 'steel_arrow')
                    pv, dealt = _blow(p, m, score, ranged=ranged, ammo=ammo)
                    checked += 1
                    if pv != dealt:
                        mismatches.append((template, material, kind, score, pv, dealt))
    assert checked > 3000
    assert not mismatches, mismatches[:10]


def test_preview_counts_strength_blessing_weakness_shield_and_scales():
    """The five cases the bug bash measured, each now equal (D10)."""
    def case(setup, kind='giant_rat'):
        w = items.instantiate_weapon('longsword', 'iron')
        p = _player(w)
        m = _target(kind)
        setup(p, m)
        return _blow(p, m, 3)

    for setup, kind in (
            (lambda p, m: setattr(p, 'STR', 18), 'giant_rat'),
            (lambda p, m: setattr(p.weapon, 'buc', 'blessed'), 'giant_rat'),
            (lambda p, m: setattr(p.weapon, 'buc', 'cursed'), 'giant_rat'),
            (lambda p, m: p.status_effects.__setitem__('weakened', 9), 'giant_rat'),
            (lambda p, m: m.status_effects.__setitem__('shielded', 9), 'giant_rat'),
            (lambda p, m: None, 'fafnir_dragon'),
            (lambda p, m: p.status_effects.__setitem__('in_pit', 9), 'fafnir_dragon'),
            (lambda p, m: None, 'abaddon_destroyer'),
            (lambda p, m: p.status_effects.__setitem__('berserk', 9), 'giant_rat'),
            (lambda p, m: m.status_effects.__setitem__('armor_crack', 9), 'giant_rat')):
        preview, dealt = case(setup, kind)
        assert preview == dealt, (kind, preview, dealt)


def test_preview_spends_nothing_and_the_blow_spends_one_shots():
    """Empower, blade flow and the Amazon charge are one-shot: the preview
    counts them and leaves them; the blow counts them and uses them."""
    w = items.instantiate_weapon('longsword', 'iron')
    p = _player(w)
    m = _target('fafnir_dragon')
    p.status_effects['empowered'] = 5
    p.status_effects['blade_flow'] = 2
    p._amazon_charge_armed = True
    preview_a = combat.strike_damage(p, m, 4)
    preview_b = combat.strike_damage(p, m, 4)
    assert preview_a == preview_b
    assert p.has_effect('empowered') and p.status_effects['blade_flow'] == 2
    assert p._amazon_charge_armed
    pv, dealt = _blow(p, m, 4)
    assert pv == dealt == preview_a
    assert not p.has_effect('empowered')
    assert p.status_effects.get('blade_flow', 0) == 1
    assert not p._amazon_charge_armed


def test_combat_strip_shows_the_blow_number():
    """The strip's own method (game_render) returns what the blow deals,
    including the ammo the shot was loaded with."""
    import game_render

    class _G(game_render.RenderMixin):
        pass

    bow = items.instantiate_weapon('longbow', 'yew')
    p = _player(bow, ranged=True, PER=18, STR=16)
    arrow = items.make_item_by_id('ammo', 'steel_arrow')
    g = _G()
    g.player = p
    g.combat_target = _target('goblin')
    g._combat_is_ranged = True
    g._combat_ammo = arrow
    g.quiz_engine = types.SimpleNamespace(chain=6)
    shown = g._strike_preview_damage()
    _pv, dealt = _blow(p, g.combat_target, 6, ranged=True, ammo=arrow)
    assert shown == dealt > 0

    g.quiz_engine = types.SimpleNamespace(chain=0)
    assert g._strike_preview_damage() == 0          # a miss is a miss


def test_backstab_doubles_on_a_sleeping_target_and_the_preview_says_so():
    """The dagger's Backstab (x2 at max chain on an unaware target) moved
    into strike_damage. It used to be a second hit after the first, and the
    first had already woken a sleeper, so sleepers never took it."""
    dagger = items.instantiate_weapon('dagger', 'iron')
    top = dagger.max_chain_length or len(dagger.chain_multipliers)
    awake_p = _player(dagger)
    awake = _target('giant_rat')
    _pv, awake_dealt = _blow(awake_p, awake, top)
    p = _player(dagger)
    sleeper = _target('giant_rat')
    sleeper.status_effects['sleeping'] = 10
    pv, dealt = _blow(p, sleeper, top)
    assert pv == dealt == 2 * awake_dealt
