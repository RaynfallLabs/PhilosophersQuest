"""Know your enemy: knowledge decides what the hero is told (winning-build
plan 2026-11-13, section 3.1; slice 3).

Brandon, 2026-11-12: "no omniscient monsters". The hero always FEELS a hit;
knowing the creature tells him WHY, and tells him BEFORE he swings:

  * the hit lines (src/affinity.py): felt only for a kind he does not know,
    felt plus the family's habit for one he knows by its family, the cause
    named for one he knows;
  * the Strike Now preview and the combat strip's tag (combat.py): the
    weakness or resistance only for a kind he knows;
  * first sight and Observe at KNOWN: what it is made of (tells.lore_lines,
    pinned in tests/test_monster_notes.py);
  * Kit Sense at the family's Hunter tier (src/kit_sense.py);
  * Recall Lore is NOT about the creature in view (Brandon, 2026-11-14): it
    is the trivia quiz that gives a random hint of the chain's tier, and it
    leaves what the hero knows of every creature as it was;
  * the Wand of Probing reads the real affinity and status lists (and
    teaches the kind as a corpse study does: tests/test_probing_teaches.py);
  * a gate boss's quest step opens his page, the quest-giver naming his
    weakness;
  * the Bestiary page at KNOWN shows what it shrugs off and its nature.

Logic tests; the feel of it in play is a play-test question (Claude cannot
drive Pygame).
"""
import collections
import json
import os
import random
import string
import sys

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

import pygame  # noqa: E402
import pytest  # noqa: E402

pygame.init()

import affinity  # noqa: E402
import combat  # noqa: E402
import enemy_lore  # noqa: E402
import family_lore  # noqa: E402
import items  # noqa: E402
import kit_sense  # noqa: E402
from family_lore import KIN, KNOWN, UNKNOWN  # noqa: E402
from monster import Monster, the_name  # noqa: E402
from player import Player  # noqa: E402

with open(os.path.join(ROOT, 'data', 'monsters.json'), encoding='utf-8') as _f:
    MONS = json.load(_f)
with open(os.path.join(ROOT, 'data', 'family_affinity.json'), encoding='utf-8') as _f:
    PROF = json.load(_f)


def _m(kind, x=5, y=5, **over):
    m = Monster({**MONS[kind], 'id': kind}, x, y)
    for k, v in over.items():
        setattr(m, k, v)
    return m


def _known(weapon):
    weapon.id_level = 5
    return weapon


@pytest.fixture(autouse=True)
def _clean():
    affinity.drain()
    yield
    affinity.drain()


def _fill(s, m, word=''):
    from monster import pronoun_fill
    w = affinity.word_for(word) if word else ''
    return s.format(name=the_name(m), the=the_name(m, lower=True), word=w, word_cap=w[:1].upper() + w[1:],
                    **pronoun_fill(m))


# ---------------------------------------------------------------------------
# 1. The hit lines, by knowledge
# ---------------------------------------------------------------------------
def test_the_felt_pools_never_name_the_cause():
    felt = affinity.lines()['felt']
    for pool in ('weak', 'resisted', 'shrugs_off', 'weak_many', 'resisted_many', 'shrugs_off_many'):
        assert len(felt[pool]) >= 2, pool
        for s in felt[pool]:
            used = {f for _, f, _, _ in string.Formatter().parse(s) if f}
            # (the creature's own pronouns: data/monsters.json pronoun, round 3)
            assert used <= {'name', 'the', 'he', 'He', 'him', 'his', 'His'}, (pool, s)
    for pool in ('weak', 'resisted', 'shrugs_off'):
        assert len(felt[pool]) >= 5, pool
    assert '{He} reels!' in felt['weak']
    # every KNOWN line names what met it
    for pool in ('weak', 'resisted', 'shrugs_off'):
        for s in affinity.lines()[pool]:
            assert '{word' in s, (pool, s)


def test_an_unstudied_kinds_hit_line_names_no_cause():
    sk = _m('skeleton')
    for seed in range(20):
        out = affinity.say([(sk, 'resisted', 'slash'), (sk, 'weak', 'blunt')], random.Random(seed),
                           level_of=lambda m: UNKNOWN)
        assert [k for _t, k in out] == ['weak', 'resisted']
        for text, kind in out:
            assert text in [_fill(s, sk) for s in affinity.lines()['felt'][kind]], text
            low = text.lower()
            assert 'cutting' not in low and 'crushing' not in low and 'blade' not in low


def test_a_studied_kinds_hit_line_names_the_cause():
    sk = _m('skeleton')
    out = affinity.say([(sk, 'weak', 'blunt')], random.Random(1), level_of=lambda m: KNOWN)
    assert out[0][0] in [_fill(s, sk, 'blunt') for s in affinity.lines()['weak']]
    assert 'crushing blow' in out[0][0].lower()


def test_kin_adds_the_familys_habit_to_the_felt_line():
    z = _m('zombie')
    out = affinity.say([(z, 'resisted', 'pierce')], random.Random(2), level_of=lambda m: KIN)
    text = out[0][0]
    habits = affinity.lines()['habits']['families']['restless_dead']['resisted:pierce']
    assert any(text.endswith(' ' + h) for h in habits), text
    felt = [_fill(s, z) for s in affinity.lines()['felt']['resisted']]
    assert any(text.startswith(f) for f in felt), text
    # the creature's group speaks first: a skeleton's bones
    sk = _m('skeleton')
    text = affinity.say([(sk, 'weak', 'blunt')], random.Random(3), level_of=lambda m: KIN)[0][0]
    assert text.endswith('Bones snap under crushing force.'), text
    # a meeting the family's profile does not explain gets its plain line
    gob = _m('goblin')
    text = affinity.say([(gob, 'weak', 'fire')], random.Random(4), level_of=lambda m: KIN)[0][0]
    plain = affinity.lines()['habits']['families']['goblinkin']['weak']
    assert any(text.endswith(' ' + h) for h in plain), text


def test_the_game_says_each_creature_as_far_as_the_hero_knows_it():
    """CombatMixin._say_affinity_lines asks family_lore.knowledge."""
    from game_combat import CombatMixin

    class _G:
        _say_affinity_lines = CombatMixin._say_affinity_lines

        def __init__(self):
            self.player = Player()
            self.log = []

        def add_message(self, text, kind='info'):
            self.log.append(text)

    g = _G()
    sk = _m('skeleton')
    affinity.note(sk, 'weak', 'blunt')
    g._say_affinity_lines()
    assert g.log and 'crushing' not in g.log[0].lower()
    g.player.family_lore_grants = {'restless_dead': 1}            # KIN
    affinity.note(sk, 'weak', 'blunt')
    g._say_affinity_lines()
    assert g.log[1].endswith('Bones snap under crushing force.')
    g.player.studied_monster_ids.add('skeleton')                  # KNOWN
    affinity.note(sk, 'weak', 'blunt')
    g._say_affinity_lines()
    assert 'crushing blow' in g.log[2].lower()


def test_a_refusal_says_why_only_to_a_hero_who_knows():
    golem = _m('clay_golem')
    felt = affinity.status_line('immune', 'feared', golem, level=UNKNOWN)
    assert 'fear' not in felt.lower() and 'mind' not in felt.lower()
    assert felt in [_fill(s, golem) for s in affinity.lines()['status_immune_felt']]
    for level in (KIN, KNOWN):
        why = affinity.status_line('immune', 'feared', golem, level=level)
        assert 'fear' in why or 'frighten' in why
    from game_magic import MagicMixin

    class _G:
        player = Player()

        def _boss_resist_cc(self, target, duration):
            return duration, False
    got, why = MagicMixin._inflict(_G(), golem, 'feared', 6)
    assert got == 0 and why and 'fear' not in why.lower()


# -- the habits are true ----------------------------------------------------
def _facts(kinds) -> collections.Counter:
    combat._load_material_tags()
    eff = combat._MATERIAL_EFFECTIVE_AGAINST
    c = collections.Counter()
    for k in kinds:
        d = MONS[k]
        tags = set(d.get('tags') or ())
        for meet, lst in (('weak', 'weaknesses'), ('resisted', 'resistances'), ('shrugs_off', 'shrugs_off')):
            for t in d.get(lst) or ():
                c[f'{meet}:{t}'] += 1
        for mat, et in eff.items():
            if et & tags and mat not in (d.get('weaknesses') or ()):
                c[f'weak:{mat}'] += 1
    return c


def test_every_keyed_habit_is_true_of_most_of_its_kinds():
    """A habit names a cause only where the family's (or group's) lore and
    its kinds agree: true of at least half of the kinds it speaks for (a
    family's: its kinds outside a group of their own, where there are
    enough of them)."""
    habits = affinity.lines()['habits']
    grouped = affinity.group_of_kind()
    by_family = collections.defaultdict(list)
    for k, d in MONS.items():
        if d.get('family'):
            by_family[d['family']].append(k)
    bad = []
    for fid, table in habits['families'].items():
        assert fid in by_family, fid
        loose = [k for k in by_family[fid] if k not in grouped]
        kinds = loose if len(loose) >= 3 else by_family[fid]
        facts = _facts(kinds)
        for key in affinity._keyed(table):
            if facts[key] * 2 < len(kinds):
                bad.append((fid, key, facts[key], len(kinds)))
    for gid, table in habits['groups'].items():
        kinds = [k for k in PROF['groups'][gid]['kinds'] if k in MONS]
        facts = _facts(kinds)
        for key in affinity._keyed(table):
            if facts[key] * 2 < len(kinds):
                bad.append((gid, key, facts[key], len(kinds)))
    assert not bad, bad


def test_every_family_has_its_plain_habit_lines():
    fams = set(family_lore.families())
    habits = affinity.lines()['habits']['families']
    assert fams <= set(habits), fams - set(habits)
    for fid in fams:
        for meet in ('weak', 'resisted', 'shrugs_off'):
            assert habits[fid].get(meet), (fid, meet)


def test_the_new_lines_use_no_singular_they():
    def walk(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, list):
            for y in x:
                yield from walk(y)
        elif isinstance(x, dict):
            for k, y in x.items():
                if not str(k).startswith('_'):
                    yield from walk(y)
    texts = list(walk(affinity.lines()['habits'])) + list(walk(affinity.lines()['felt']))
    texts += list(walk(kit_sense.data()['lines'])) + list(walk(enemy_lore.data()))
    for t in texts:
        # "they" is plural in every one of these lines (birds, the dead...)
        low = f" {t.lower()} "
        assert ' themself ' not in low and ' themselves ' not in low, t


# ---------------------------------------------------------------------------
# 2. The Strike Now preview
# ---------------------------------------------------------------------------
def _mace_hero(**over):
    p = Player()
    p.x, p.y = 5, 5
    p.weapon = _known(items.instantiate_weapon('mace', 'iron'))
    for k, v in over.items():
        setattr(p, k, v)
    return p


def test_an_unstudied_kinds_preview_shows_no_multiplier():
    p = _mace_hero()
    sk = _m('skeleton', hp=10 ** 6, max_hp=10 ** 6)
    shown = combat.strike_preview(p, sk, 5)
    plain = combat.strike_damage(p, sk, combat.effective_chain(p, sk, p.weapon, 5, consume=False,
                                                               strike_now=True),
                                 affinity_known=False)
    real = combat.strike_preview(p, sk, 5, known=True)
    assert shown == plain and real > shown * 1.8      # the mace's crushing x2 is not in it
    assert not combat.affinity_known(p, sk)
    # a kind known only by its family is not enough
    p.family_lore_grants = {'restless_dead': 2}
    assert combat.strike_preview(p, sk, 5) == plain


def test_a_studied_kinds_preview_shows_the_multiplier_and_matches_the_blow():
    p = _mace_hero()
    sk = _m('skeleton', hp=10 ** 6, max_hp=10 ** 6)
    p.studied_monster_ids.add('skeleton')
    assert combat.affinity_known(p, sk)
    shown = combat.strike_preview(p, sk, 5)
    assert shown == combat.strike_preview(p, sk, 5, known=True)
    got = []

    class _Q:
        def start_quiz(self, callback=None, **_kw):
            import types
            callback(types.SimpleNamespace(score=5, success=True))
    combat.player_attack(p, sk, _Q(), lambda dmg, *a, **k: got.append(dmg))
    assert got == [shown]
    # the family at Lore knows every kind of it
    q = _mace_hero(family_lore_grants={})
    q.family_lore_grants = {'restless_dead': family_lore.full_lore_tier()}
    assert combat.strike_preview(q, sk, 5) == shown


def test_the_real_blow_still_meets_the_weakness():
    """The hero who does not know the skeleton still smashes it at x2."""
    p = _mace_hero()
    sk = _m('skeleton', hp=10 ** 6, max_hp=10 ** 6)
    plain = combat.strike_damage(p, sk, 5, affinity_known=False)
    real = combat.strike_damage(p, sk, 5, consume=True, dice=lambda s: 0, affinity_known=False)
    assert real > plain * 1.8                           # consume: affinity_known is ignored


# ---------------------------------------------------------------------------
# 4. Kit Sense
# ---------------------------------------------------------------------------
def _hunter(fid='restless_dead', tier=None):
    p = Player()
    p.x, p.y = 5, 5
    p.weapon = _known(items.instantiate_weapon('longsword', 'iron'))
    p.inventory = [_known(items.instantiate_weapon('mace', 'silver'))]
    p.family_lore_grants = {fid: kit_sense.hunter_tier() if tier is None else tier}
    p.__dict__.pop('_family_tier_cache', None)
    return p


def test_kit_sense_is_the_hunter_tier():
    assert family_lore.tier_names()[kit_sense.hunter_tier() - 1] == 'Hunter'


def test_kit_sense_fires_at_hunter_with_the_right_weapon():
    p = _hunter()
    sk = _m('skeleton')
    line = kit_sense.on_sight(p, [sk], {}, floor=3, turn=10, rng=random.Random(1))
    assert 'Silver Mace' in line
    tool, gain = kit_sense.advise(p, sk)
    assert tool.item is p.inventory[0] and tool.mult == 3.0 and gain > 2.0


def test_kit_sense_says_nothing_below_hunter():
    p = _hunter(tier=kit_sense.hunter_tier() - 1)
    assert kit_sense.on_sight(p, [_m('skeleton')], {}, floor=3, turn=10) == ''


def test_kit_sense_says_nothing_when_the_best_is_in_hand():
    p = _hunter()
    p.weapon, p.inventory = p.inventory[0], [p.weapon]
    assert kit_sense.on_sight(p, [_m('skeleton')], {}, floor=3, turn=10) == ''


def test_kit_sense_once_per_group_sighting():
    p = _hunter()
    state = {}
    gap = int(kit_sense.data()['gap'])
    group = [_m('skeleton'), _m('skeleton', x=6)]
    assert kit_sense.on_sight(p, group, state, floor=3, turn=10)
    assert kit_sense.on_sight(p, group, state, floor=3, turn=11) == ''        # still in sight
    assert kit_sense.on_sight(p, [], state, floor=3, turn=12) == ''
    assert kit_sense.on_sight(p, group, state, floor=3, turn=11 + gap) == ''  # not long enough away
    assert kit_sense.on_sight(p, group, state, floor=3, turn=13 + 2 * gap)    # a new sighting
    assert kit_sense.on_sight(p, group, state, floor=4, turn=13 + 2 * gap)    # another floor


def test_kit_sense_reads_only_what_he_knows_of_his_own_weapon():
    """An unidentified silver mace is a mace to him: its crushing counts,
    its metal does not (and it is named as he knows it)."""
    p = _hunter()
    p.inventory[0].id_level = 0
    sk = _m('skeleton')
    tool, _gain = kit_sense.advise(p, sk)
    assert tool.mult == 2.0 and 'Silver' not in tool.name


def test_kit_sense_takes_a_new_tool_kind():
    """Slice 5's coatings and flasks plug in as providers."""
    p = _hunter()
    p.inventory = []
    sk = _m('skeleton')

    @kit_sense.provider
    def _flask(player, monster):
        return [kit_sense.Tool('flask', None, 'Flask of Holy Water', 2.0)]
    try:
        tool, _gain = kit_sense.advise(p, sk)
        assert tool.kind == 'flask'
        assert 'Flask of Holy Water' in kit_sense.line(tool, sk, rng=random.Random(1))
    finally:
        kit_sense.PROVIDERS.remove(_flask)
    assert kit_sense.advise(p, sk) is None or kit_sense.advise(p, sk)[0].kind == 'weapon'


def test_kit_sense_needs_arrows_for_a_bow():
    assert 'pierce' in MONS['harpy']['weaknesses']        # birds fall to an arrow
    p = _hunter('birds')
    p.weapon = _known(items.instantiate_weapon('mace', 'iron'))
    p.inventory = [_known(items.instantiate_weapon('longbow', 'yew'))]
    harpy = _m('harpy')
    assert kit_sense.advise(p, harpy) is None             # no arrows: no use
    p.inventory.append(items.make_item_by_id('ammo', 'steel_arrow'))
    got = kit_sense.advise(p, harpy)
    assert got and got[0].item is p.inventory[0]


# ---------------------------------------------------------------------------
# 5. Recall Lore is not about the creature in view (Brandon, 2026-11-14)
# ---------------------------------------------------------------------------
def test_the_targeted_recall_is_gone():
    """Slice 3 made Recall Lore read the creature in view; Brandon does not
    want that. Nothing of it is left in the module or its data."""
    for name in ('recall_parts', 'recall_text', 'recall_reach', 'recall_opens_page'):
        assert not hasattr(enemy_lore, name), name
    assert 'recall' not in enemy_lore.data()


# ---------------------------------------------------------------------------
# A real Game, headless
# ---------------------------------------------------------------------------
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
    g = Game(pygame.display.set_mode((1280, 720)), player_name='__test_know_your_enemy__')
    g.monsters = []
    g.pets = []
    g.dungeon.traps = {}
    g.state = STATE_PLAYER
    log = []
    monkeypatch.setattr(g, 'add_message', lambda text, kind='info', *a, **k: log.append(text))
    g._log = log
    return g


def _in_view(g, kind, dx=2):
    from dungeon import FLOOR
    x = min(max(g.player.x, 4), g.dungeon.width - 5)
    y = min(max(g.player.y, 4), g.dungeon.height - 5)
    for i in range(-3, 4):
        for j in range(-3, 4):
            g.dungeon.tiles[y + j][x + i] = FLOOR
    g.player.x, g.player.y = x, y
    m = _m(kind, x + dx, y)
    m._aware = True
    g.monsters.append(m)
    g._refresh_fov()
    g.visible |= {(x + i, y + j) for i in range(-3, 4) for j in range(-3, 4)}
    return m


def test_the_game_says_kit_sense_once_on_sight(game):
    sk = _in_view(game, 'skeleton')
    game.player.weapon = _known(items.instantiate_weapon('longsword', 'iron'))
    game.player.inventory.append(_known(items.instantiate_weapon('mace', 'silver')))
    game.player.family_lore_grants = {'restless_dead': kit_sense.hunter_tier()}
    family_lore.mark_all_told(game.player)
    game._family_turn()
    assert sum('Silver Mace' in t for t in game._log) == 1, game._log
    game.turn_count += 1
    game._family_turn()
    assert sum('Silver Mace' in t for t in game._log) == 1
    assert sk.alive


def _hints():
    with open(os.path.join(ROOT, 'data', 'hints.json'), encoding='utf-8') as f:
        return json.load(f)


@pytest.mark.parametrize('chain', [1, 2, 3, 4, 5])
def test_recall_lore_with_a_creature_in_view_is_still_a_random_hint(game, chain):
    """Brandon: "Recall lore is a Trivia quiz that gives a random hint,
    doesn't do anything with monsters you can see and is not targeted."
    A ghoul in view whose family is begun: the card is a hint of the chain's
    tier, the ghoul is no better known, and the cooldown rule holds."""
    ghoul = _in_view(game, 'ghoul')
    game.player.family_lore_grants = {family_lore.family_of(ghoul): 1}
    game.player.__dict__.pop('_family_tier_cache', None)
    before = family_lore.knowledge(game.player, ghoul)
    lore = set(game.player.lore_known_monster_ids)
    studied = set(game.player.studied_monster_ids)
    game._resolve_recall_lore(chain)
    assert game._lore_hint_text in _hints()[str(chain)]
    assert 'ghoul' not in game._lore_hint_text.lower()
    assert family_lore.knowledge(game.player, ghoul) == before != KNOWN
    assert game.player.lore_known_monster_ids == lore
    assert game.player.studied_monster_ids == studied
    assert game.player.recall_lore_cooldown == 50 + chain * 15
    assert game._lore_hint_text in game._recalled_hints


def test_recall_lore_with_nothing_in_view_gives_the_general_hints(game):
    game._resolve_recall_lore(3)
    assert game._lore_hint_text in _hints()['3']


def test_recall_lore_starts_the_same_with_or_without_a_creature(game):
    _in_view(game, 'ghoul')
    game.player.recall_lore_cooldown = 0
    game._start_recall_lore()
    assert '_recall_subject' not in game.__dict__
    assert game._log[-1] == "You close your eyes and search your memory..."
    assert not any('ghoul' in t.lower() for t in game._log)


# ---------------------------------------------------------------------------
# 6. The Wand of Probing
# ---------------------------------------------------------------------------
def test_probing_shows_resistances_and_status(game):
    ghoul = _in_view(game, 'ghoul')
    wand = items.make_item_by_id('wand', 'wand_of_probing')
    game._wand_override_target = ghoul
    game._apply_wand_effect(wand)
    said = ' '.join(game._log)
    assert f"{ghoul.hp}/{ghoul.max_hp} HP" in said
    # Each with how much it changes a blow, and the metals it cannot bear
    # (3.5.1 audit: affinity.bestiary_rows).
    assert 'Resists (Half Damage): Cold, Poison, Drain, Pierce' in said
    assert 'Weak To (Double Damage): Holy, Slash' in said and 'Immune To: Sleep' in said
    assert 'Bane Materials (Double Damage): ' in said and 'Silver' in said
    # It teaches the kind as a corpse study does (Brandon, 2026-11-14).
    assert 'ghoul' in game.player.lore_known_monster_ids              # its page opens
    assert 'ghoul' in game.player.studied_monster_ids
    assert 'You learn the ways of the Ghoul.' in game._log


def test_probing_lines_cover_shrugs_off_and_a_plain_creature():
    sw = enemy_lore.probe_lines(_m('scarab_swarm'))
    assert 'Shrugs Off (Quarter Damage): Slash, Pierce' in sw[1] and 'Resists (Half Damage): Blunt' in sw[1]
    from monster import fill
    gob = _m('goblin')
    assert enemy_lore.probe_lines(gob)[1] == fill(gob, enemy_lore.data()['probe']['nothing'])
    assert enemy_lore.probe_lines(gob)[1] == 'Nothing about him is weak or hard: every blow lands plain.'


# ---------------------------------------------------------------------------
# 6b. The quest teaches the boss
# ---------------------------------------------------------------------------
GATE_BOSSES = ('asterion_minotaur', 'medusa_gorgon', 'fafnir_dragon', 'fenrir_wolf', 'abaddon_destroyer')


def test_every_gate_boss_has_a_true_quest_line():
    for kind in GATE_BOSSES:
        e = enemy_lore.quest_entry(kind)
        assert e.get('lines') and e.get('page') and e.get('claims'), kind
        for field, claimed in e['claims'].items():
            assert set(claimed) <= set(MONS[kind][field]), (kind, field, claimed)
        assert e['claims'].get('weaknesses'), kind                    # it names his weakness
    # Vidar's shoe stays a secret
    assert 'shoe' not in ' '.join(enemy_lore.quest_lines('fenrir_wolf')).lower()
    assert 'sandal' not in ' '.join(enemy_lore.quest_lines('fenrir_wolf')).lower()


def test_the_quest_step_makes_the_boss_known(game):
    for kind in GATE_BOSSES:
        assert family_lore.knowledge(game.player, kind) == UNKNOWN
    game._quest_teaches('asterion_minotaur')
    assert family_lore.knowledge(game.player, 'asterion_minotaur') == KNOWN
    assert 'asterion_minotaur' not in game.player.studied_monster_ids
    assert any('a point between the ribs' in t for t in game._log)
    assert any('Bestiary' in t for t in game._log)
    n = len(game._log)
    game._quest_teaches('asterion_minotaur')                          # said again, page already open
    assert not any('Bestiary' in t for t in game._log[n:])


def test_ariadnes_shrine_teaches_asterion(game):
    from dungeon import WALL
    game.dungeon.ariadne_shrine_door = (2, 2)
    game.dungeon.tiles[2][2] = WALL
    game._activate_ariadne_shrine(None)
    assert family_lore.knowledge(game.player, 'asterion_minotaur') == KNOWN


def test_the_judgment_teaches_abaddon_whatever_the_verdict(game):
    game.karma = 0
    game._resolve_judgment()
    assert family_lore.knowledge(game.player, 'abaddon_destroyer') == KNOWN
    assert any('What is holy' in t for t in game._log)


# ---------------------------------------------------------------------------
# 7. The Bestiary page
# ---------------------------------------------------------------------------
def _page(game, kind):
    game.player.known_monster_ids.add(kind)
    game._open_encyclopedia()
    game._encyclopedia_load_entries('bestiary')
    entry = next(e for e in game.encyclopedia_entries if e.get('_id') == kind)
    return [str(t[0]) for t in game._encyclopedia_article_lines('bestiary', entry)]


def test_the_bestiary_page_at_known_shows_shrugs_off_and_its_nature(game):
    game.player.family_lore_grants = {'vermin': 1}                   # KIN: page, no weaknesses
    kin = _page(game, 'scarab_swarm')
    assert not any(t.startswith('Shrugs Off') or t.startswith('Immune To') for t in kin)
    assert any('not yet studied' in t for t in kin)
    game._open_kind_page('scarab_swarm')                              # KNOWN (as a quest step does)
    known = _page(game, 'scarab_swarm')
    assert 'Shrugs Off (Quarter Damage): Slash, Pierce' in known
    assert any(t.startswith('Immune To:') and 'Paralysis' in t for t in known)
    assert any(t.startswith('Weak To (Double Damage):') for t in known)
    assert any(t.startswith('Resists (Half Damage):') for t in known)


def test_kit_sense_names_the_arsenals_coatings_and_flasks():
    """Slice 5's provider in kit_sense (arsenal_tools): silver dust on the
    iron longsword meets a skeleton better than the bare blade does, and a
    thrown flask of holy water better still."""
    p = _hunter()
    dust = items.make_item_by_id('flask', 'silver_dust')
    p.inventory = [dust]
    sk = _m('skeleton')
    tool, _gain = kit_sense.advise(p, sk)
    assert tool.kind == 'coating' and tool.item is dust
    assert 'blade' in kit_sense.line(tool, sk, rng=random.Random(1)) or tool.name in         kit_sense.line(tool, sk, rng=random.Random(1))
    # Holy water both coats and throws: alone in the pack it is still named.
    water = items.make_item_by_id('flask', 'flask_of_holy_water')
    p.inventory = [water]
    tool, _gain = kit_sense.advise(p, sk)
    assert tool.item is water and tool.kind in ('coating', 'flask')
