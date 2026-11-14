"""Round 3, agent M (2026-11-14): monster pronouns, fire that is fire, and
the grammar of the lines that name a monster.

Brandon: pronouns "it unless clearly humanoid, then use appropriate: most
will be he, but some, clearly feminine (see Give Me Some Sugar power for
Ash) probably should be she"; fire "Fix fire.. it's fire, make it so";
wording "a game about knowledge and grammar should use it".

Logic and data tests. Whether the lines read well in play is Brandon's
play-test; the Stray Kids journey is tests/test_stray_kids_journey.py.
"""
import json
import os
import random
import re
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pytest  # noqa: E402

import affinity  # noqa: E402
import monster as monster_mod  # noqa: E402
from monster import Monster, a_name, attack_line, pronouns, the_name  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)


def _m(kind, **kw):
    m = Monster(dict(MONS[kind], id=kind), 5, 5)
    for k, v in kw.items():
        setattr(m, k, v)
    return m


@pytest.fixture(autouse=True)
def _clean():
    affinity.drain()
    yield
    affinity.drain()


# ---------------------------------------------------------------------------
# 1. Every monster has a pronoun
# ---------------------------------------------------------------------------
def test_every_monster_has_a_pronoun_and_the_attractive_are_she():
    assert len(MONS) >= 583
    bad = [k for k, d in MONS.items() if d.get('pronoun') not in ('it', 'he', 'she')]
    assert not bad, bad
    fem = [k for k, d in MONS.items() if 'female_attractive' in (d.get('tags') or ())]
    assert fem and all(MONS[k]['pronoun'] == 'she' for k in fem), fem


@pytest.mark.parametrize('kind,word', [
    # named individuals take their myth's
    ('fenrir_wolf', 'he'), ('medusa_gorgon', 'she'), ('scylla', 'she'), ('tiamat', 'she'),
    ('cerberus', 'he'), ('asterion_minotaur', 'he'), ('the_sphinx', 'she'), ('baba_yaga', 'she'),
    ('arachne', 'she'), ('anansi', 'he'), ('old_nickel', 'he'), ('mere_wife', 'she'),
    # people and the humanoid dead
    ('goblin', 'he'), ('orc_warrior', 'he'), ('frost_giant', 'he'), ('zombie', 'he'),
    ('vampire', 'he'), ('lich', 'he'), ('mummy', 'he'), ('minotaur', 'he'),
    ('sk_zombie_lee_know', 'he'), ('black_knight', 'he'),
    # the feminine kinds
    ('green_hag', 'she'), ('harrow_witch', 'she'), ('valkyrie_shade', 'she'), ('banshee', 'she'),
    ('lamia', 'she'), ('harpy', 'she'), ('erinyes_lesser', 'she'), ('hels_handmaid', 'she'),
    # beasts, the mindless and the made
    ('giant_rat', 'it'), ('skeleton', 'it'), ('wraith', 'it'), ('gelatinous_cube', 'it'),
    ('iron_golem', 'it'), ('fire_elemental', 'it'), ('young_red_dragon', 'it'), ('cockatrice', 'it'),
])
def test_the_calls(kind, word):
    assert MONS[kind]['pronoun'] == word
    assert pronouns(_m(kind, _aware=True))[0] == word       # (an ambusher, once sprung)


def test_an_old_pickled_monster_takes_its_kinds_pronoun():
    m = _m('goblin')
    del m.__dict__['pronoun']                    # saved before the field
    assert m.pronoun == 'he' and pronouns(m) == ('he', 'him', 'his')


def test_an_unseen_or_lurking_creature_is_it():
    gob = _m('goblin')
    gob._unseen = True
    assert pronouns(gob)[0] == 'it'
    mere = _m('mere_wife')                      # she, but lurking in the water
    assert mere.ai_pattern in ('ambush', 'mimic') and not mere._aware
    assert pronouns(mere)[0] == 'it'
    mere._aware = True
    assert pronouns(mere)[0] == 'she'


def test_a_polymorphed_monster_takes_the_new_kinds_pronoun():
    import game_magic

    class _G:
        def __init__(self, ms):
            self.monsters = ms
            self.player = Player()

        def _a_or_an(self, n):
            return monster_mod.an_article(n) + ' ' + n
    medusa = _m('medusa')
    g = _G([medusa])
    rat = _m('giant_rat')
    game_magic._polymorph_swap(g, medusa, rat)
    assert g.monsters[0] is rat and pronouns(rat)[0] == 'it'


def test_the_family_pets_have_their_own_pronouns():
    from pet_system import Pet
    assert Pet('sherlock').pronouns()[0] == 'he'
    assert Pet('irene').pronouns()[0] == 'she'
    assert Pet('shep').pronouns()[0] == 'he'
    assert Pet('fire').pronouns()[0] == 'it'


# ---------------------------------------------------------------------------
# The hit and miss lines, one each of it, he and she, on the real path
# ---------------------------------------------------------------------------
def _land(m, atk, monkeypatch):
    """One blow that lands (a natural 20, no dodge, no rider)."""
    monkeypatch.setattr(monster_mod.random, 'randint', lambda a, b: b)
    monkeypatch.setattr(monster_mod.random, 'random', lambda: 0.999)
    p = Player()
    p.hp = p.max_hp = 10 ** 6
    return m._resolve_blow(atk, p)


def _miss(m, atk, monkeypatch):
    monkeypatch.setattr(monster_mod.random, 'randint', lambda a, b: a)    # a natural 1
    p = Player()
    return m._resolve_blow(atk, p)


@pytest.mark.parametrize('kind,atk_name,line', [
    ('goblin', 'Rusty Knife', 'The Goblin hits you with his rusty knife for'),
    ('harpy', None, 'The Harpy hits you with her '),
    ('giant_rat', 'Bite', 'The Giant Rat hits you with its bite for'),
    ('gelatinous_cube', 'Engulf', 'The Gelatinous Cube engulfs you for'),
    ('arachne', None, 'Arachne '),
])
def test_the_hit_line_says_whose_weapon_it_is(kind, atk_name, line, monkeypatch):
    m = _m(kind)
    atk = next(a for a in m.attacks if atk_name is None or a['name'] == atk_name)
    if kind == 'harpy':
        atk = next(a for a in m.attacks if not monster_mod._attack_verb(a))
    dmg, msg = _land(m, atk, monkeypatch)
    assert dmg > 0 and msg.startswith(line), msg
    assert 'hits you with claw' not in msg and ' with its ' not in msg or pronouns(m)[0] == 'it'


def test_the_miss_lines_name_the_creature_and_his_own(monkeypatch):
    sk = _m('skeletal_archer')
    bow = next(a for a in sk.attacks if a.get('ranged') or 'arrow' in a['name'].lower())
    _d, msg = _miss(sk, bow, monkeypatch)
    assert msg.startswith("The Skeletal Archer's ") and msg.endswith('misses you!'), msg
    gob = _m('goblin')
    _d, msg = _miss(gob, gob.attacks[0], monkeypatch)
    assert msg == 'The Goblin swings at you and misses!'
    gob.status_effects['confused'] = 5
    arc = _m('orc_archer')
    shot = next(a for a in arc.attacks if a.get('ranged') or 'arrow' in a['name'].lower()
                or 'bow' in a['name'].lower())
    assert 'in his confusion' in arc._miss_text(shot, confused=True)


def test_a_proper_word_in_an_attack_keeps_its_capital():
    eur = _m('euryale_gorgon')
    wail = next(a for a in eur.attacks if "Euryale" in a['name'])
    assert attack_line(eur, wail, 4) == "Euryale the Gorgon hits you with Euryale's wail for 4 damage!"


# ---------------------------------------------------------------------------
# 3. "You see a Skeleton": the article is the kind's, a named foe has none
# ---------------------------------------------------------------------------
@pytest.mark.parametrize('kind,seen', [
    ('skeleton', 'a Skeleton'), ('orc_scout', 'an Orc Scout'), ('ushabti_worker', 'an Ushabti Worker'),
    ('autolycus_heir', 'an Heir of Autolycus'), ('arachne', 'Arachne'), ('the_sphinx', 'the Sphinx'),
    ('black_knight', 'the Black Knight'), ('seal_demon_wrath', 'Amon, Demon of Wrath'),
])
def test_first_sight_names_a_kind_with_its_article(kind, seen):
    assert a_name(_m(kind)) == seen


def test_observe_says_you_see_a_skeleton():
    from game_combat import CombatMixin
    import inspect
    src = inspect.getsource(CombatMixin)
    assert 'f"You see {monster.name} (' not in src
    assert 'f"You see {a_name(monster)} (' in src


# ---------------------------------------------------------------------------
# The grammar sweep: the templated lines across a spread of monsters
# ---------------------------------------------------------------------------
SPREAD = ('arachne', 'medusa_gorgon', 'fenrir_wolf',            # proper names, she and he
          'orc_scout', 'ushabti_worker', 'autolycus_heir', 'ochre_jelly',   # vowel-initial
          'scarab_swarm', 'erinyes_greater', 'lizardfolk', 'skeleton_horde',  # plural-looking
          'goblin', 'harpy', 'giant_rat', 'zombie', 'skeleton', 'troll', 'gelatinous_cube',
          'ghoul', 'vampire_spawn', 'green_hag', 'fire_elemental', 'sk_zombie_han')

_A_AN = re.compile(r"(?<![\w'])(a [aeiouAEIOU](?!ni|se|su|ti)\w*|an [b-df-hj-np-tv-zB-DF-HJ-NP-TV-Z](?!eir|our|on)\w*)")
_DOUBLE = re.compile(r"\b(\w+) \1\b", re.I)


def _slips(text, m):
    out = []
    if '{' in text or '}' in text:
        out.append('unfilled slot')
    if '  ' in text or ' ,' in text or ' .' in text or re.search(r'(?<!\.)\.\.(?!\.)', text):
        out.append('doubled space or punctuation')
    if _A_AN.search(text):
        out.append('a/an: ' + _A_AN.search(text).group(0))
    d = _DOUBLE.search(text)
    if d:
        out.append('doubled word: ' + d.group(0))
    if text[:1].islower():
        out.append('lower-case start')
    if re.search(r'\b[Tt]he The\b|\b[Tt]he [Aa]n? ', text):
        out.append('doubled article')
    low = (m.name or '').lower()
    proper = monster_mod._is_proper(m, low)
    if proper and low and low in text and m.name not in text and low != m.name:
        out.append('lower-case name')
    if re.search(r'\b1 (turns|creatures|monsters|items|charges|tiles|pieces)\b', text):
        out.append('number agreement')
    sub, obj, pos = pronouns(m)
    if sub != 'it' and re.search(r'\b(its|It is|it is)\b', text) and 'It is only water' not in text \
            and "It's super" not in text and "It's not" not in text and 'it lasts' not in text:
        # (an 'it' that is not the creature: a gaze, the effect, the blow)
        if re.search(r'\bits (bane|hold|name|eyes|own|face|wounds|feet|claws|bite|head|disguise)\b', text):
            out.append(f'"its" said of a {sub}')
    # "they" in a sentence that names this one creature
    name = the_name(m)
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        if name in sentence and re.search(r'\b(they|them|their)\b', sentence):
            out.append('singular they')
    return out


def _lines_of(m):
    import senses
    import tells
    import enemy_lore
    rng = random.Random(3)
    out = [f"You see {a_name(m)} (uninjured).", f"{the_name(m)} is slain!",
           senses.status_line(m)]
    for atk in m.attacks:
        out.append(attack_line(m, atk, 7))
        out.append(m._miss_text(atk))
        out.append(m._miss_text(atk, confused=True))
    for kind in ('weak', 'resisted', 'shrugs_off', 'fire_fright'):
        for level in (affinity.UNKNOWN, affinity.KIN, affinity.KNOWN):
            for seed in range(4):
                out += [t for t, _k in affinity.say([(m, kind, 'fire')], random.Random(seed),
                                                    level_of=lambda _m, lv=level: lv)]
    for eff in ('feared', 'stunned', 'immobilized', 'burning', 'poisoned', 'paralyzed'):
        out.append(affinity.status_line('immune', eff, m, rng, level=affinity.KNOWN))
        out.append(affinity.status_line('immune', eff, m, rng, level=affinity.UNKNOWN))
        out.append(affinity.status_line('weak', eff, m, rng))
    out += tells.lines(m, tells.KNOWN, limit=4) + tells.lore_lines(m)
    # Recall Lore no longer speaks of a creature (round 3 R); the probe does.
    out += enemy_lore.probe_lines(m) + [enemy_lore.probe_learn_line(m)]
    return [t for t in out if t]


@pytest.mark.parametrize('kind', SPREAD)
def test_the_templated_lines_read_right(kind):
    m = _m(kind)
    bad = []
    for text in _lines_of(m):
        for s in _slips(text, m):
            bad.append((s, text))
    assert not bad, bad[:6]


def test_no_monster_hit_or_sight_line_has_a_slip():
    """Every kind in the game, every attack: the sight, hit, miss and kill
    lines."""
    bad = []
    for kind in MONS:
        m = _m(kind)
        lines = [f"You see {a_name(m)} (uninjured).", f"{the_name(m)} is slain!"]
        for atk in m.attacks:
            lines += [attack_line(m, atk, 7), m._miss_text(atk)]
        for text in lines:
            for s in _slips(text, m):
                bad.append((kind, s, text))
    assert not bad, bad[:8]


def test_the_family_habits_are_true_of_every_damage_kind_they_are_said_for():
    habits = affinity.lines()['habits']['families']
    assert 'cannot be cut' not in json.dumps(habits['vermin'])
    for fid in ('mortals', 'goblinkin', 'vermin', 'serpents', 'gorgons', 'birds', 'dragons'):
        for meet in ('resisted', 'shrugs_off'):
            for line in habits[fid][meet]:
                assert 'armour' not in line and 'Scale' not in line.split()[:1], (fid, meet, line)


def test_a_plural_kind_name_is_singular():
    assert MONS['erinyes_lesser']['name'] == 'Lesser Erinys'
    assert MONS['erinyes_greater']['name'] == 'Greater Erinys'


def test_a_count_agrees_with_its_noun():
    from naming import quantity
    assert quantity(1, 'turn') == '1 turn' and quantity(3, 'turn') == '3 turns'
    assert quantity(1, 'enemy', 'enemies') == '1 enemy' and quantity(0, 'enemy', 'enemies') == '0 enemies'


# ---------------------------------------------------------------------------
# 2. Fire is fire
# ---------------------------------------------------------------------------
def _resister():
    """A creature that resists fire but is not made of it."""
    kind = next(k for k, d in MONS.items() if 'fire' in d['resistances']
                and 'fire' not in d['shrugs_off'] and 'fire' not in d['weaknesses']
                and not d.get('is_boss') and not d.get('is_mini_boss') and not d.get('is_seal_demon')
                and not d.get('regeneration'))
    return _m(kind, max_hp=2000, hp=2000)


def _plain():
    kind = next(k for k, d in MONS.items() if 'fire' not in d['resistances']
                and 'fire' not in d['shrugs_off'] and 'fire' not in d['weaknesses']
                and 'burning' not in d['status_immune'] and not d.get('is_boss')
                and not d.get('is_mini_boss') and not d.get('is_seal_demon')
                and not d.get('regeneration') and 'fear_of_fire' not in d['status_weak'])
    return _m(kind, max_hp=2000, hp=2000)


def _tick_burn(m):
    m.status_effects['burning'] = 5
    before = m.hp
    m.tick_effects()
    return before - m.hp


def test_a_burn_ticks_as_fire():
    plain, res = _plain(), _resister()
    full = _tick_burn(plain)
    half = _tick_burn(res)
    assert full == 2000 // monster_mod.BURN_DIVISOR
    assert half == int(full * affinity.resisted_step())
    weak_kind = next(k for k, d in MONS.items() if 'fire' in d['weaknesses'] and not d.get('regeneration')
                     and not d.get('is_boss') and not d.get('is_mini_boss') and 'fire' not in d['resistances'])
    weak = _m(weak_kind, max_hp=2000, hp=2000)
    assert _tick_burn(weak) == int(full * affinity.weak_step())


def test_a_creature_made_of_fire_never_catches_fire():
    fe = _m('fire_elemental', max_hp=2000, hp=2000)
    assert fe.resists_control('burning')
    assert fe.add_effect('burning', 5) == 0
    fe.hold('burning', 5)
    assert not fe.has_effect('burning')
    fe.status_effects['burning'] = 5            # written straight in (an old save)
    hp = fe.hp
    fe.tick_effects()
    assert fe.hp == hp and 'burning' not in fe.status_effects
    assert affinity.status_line('immune', 'burning', fe, random.Random(1)) == 'The Fire Elemental will not burn.'


class _TrapGame:
    """Just what Game._fire_trap_on_monster reads."""

    def __init__(self, dungeon):
        self.dungeon = dungeon
        self.visible = set()
        self.monsters = []
        self.log = []

    def add_message(self, text, kind='info'):
        self.log.append(text)

    def _on_monster_killed(self, m):
        pass


def _fire_trap(m, monkeypatch):
    import main
    import dungeon as dungeon_mod

    class _D:
        traps = {}
    trap = dict(next(t for t in dungeon_mod.TRAP_TYPES if t['type'] == 'fire'))
    pos = (m.x, m.y)
    _D.traps = {pos: trap}
    g = _TrapGame(_D())
    monkeypatch.setattr(main._snd, 'play', lambda *a, **k: None)
    rolls = iter([10] * 10)
    import dice
    monkeypatch.setattr(dice, 'roll', lambda s: next(rolls))
    before = m.hp
    main.Game._fire_trap_on_monster(g, m, trap, pos)
    return before - m.hp


def test_the_fire_trap_burns_as_fire(monkeypatch):
    plain, res = _plain(), _resister()
    full = _fire_trap(plain, monkeypatch)
    half = _fire_trap(res, monkeypatch)
    assert full > 0 and half == int(full * affinity.resisted_step())
    assert plain.has_effect('burning') and res.has_effect('burning')
    fe = _m('fire_elemental', max_hp=2000, hp=2000)
    _fire_trap(fe, monkeypatch)
    assert not fe.has_effect('burning')                   # it does not catch
    hp = fe.hp
    fe.tick_effects()
    assert fe.hp == hp


def test_the_stolen_flame_is_fire(monkeypatch):
    import hero_specials

    class _G:
        def __init__(self, ms):
            self.monsters = ms
            self.player = Player()
            self.log = []

        def add_message(self, t, k='info'):
            self.log.append(t)

        def _on_monster_killed(self, m):
            pass
    plain = _m(next(k for k in ('goblin', 'kobold', 'orc_scout')
                    if 'fire' not in MONS[k]['resistances']))
    fe = _m('fire_elemental')
    for m in (plain, fe):
        m.x, m.y = 6, 5
    g = _G([plain, fe])
    g.player.x, g.player.y = 5, 5
    hero_specials._eff_self_aoe_fire(g, {}, {'radius': 1, 'dice': '6d6', 'burn_turns': 3}, 5)
    assert plain.has_effect('burning') and not fe.has_effect('burning')
    # It shrugs off fire: a smaller share than a plain creature loses.
    assert (not plain.alive
            or (fe.max_hp - fe.hp) / fe.max_hp < (plain.max_hp - plain.hp) / plain.max_hp)


def test_a_fire_vent_on_the_hero_is_halved_once_by_fire_resistance(monkeypatch):
    import game_hazards
    import hazards

    class _G(game_hazards.HazardsMixin):
        def __init__(self):
            self.player = Player()
            self.state = 'player'
            self.log = []

        def add_message(self, t, k='info'):
            self.log.append(t)
    g = _G()
    g.player.hp = g.player.max_hp = 600
    vent = dict(hazards.hazard_def('fire_vent'), status=None)
    import dice
    monkeypatch.setattr(dice, 'roll', lambda s: 12)
    g._hazard_hit_hero(vent)
    plain = 600 - g.player.hp
    g.player.hp = 600
    g.player.status_effects['fire_resist'] = 50
    g._hazard_hit_hero(vent)
    resisted = 600 - g.player.hp
    assert plain > 2 and abs(resisted - plain / 2) <= 1, (plain, resisted)     # halved once, not twice


def test_dragonscale_never_lets_the_hero_burn():
    import gear
    from status_effects import apply_effect
    p = Player()

    class _Scale:
        slot = 'body'
        wards = ['flame']
        name = 'Dragonscale Mail'
    p.armor_slots = [_Scale()]
    assert gear.ward_against(p, None, 'burning') is not None
    assert not apply_effect(p, 'burning', 5) and not p.has_effect('burning')
