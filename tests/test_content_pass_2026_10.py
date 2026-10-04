"""Data-layer guards for the 2026-10 monster / item content pass.

Lore quality itself is a reading job, not a test. These pin the mechanical
facts the pass established so later edits cannot quietly undo them:
vocabularies, the armor resistance convention, unidentified-name uniqueness,
potion spawn shares, the chest loot weighting, and powers that were authored
but never wired.
"""
import json
import os
import random
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, os.path.join(ROOT, 'src'))


def _load(*parts):
    with open(os.path.join(ROOT, 'data', *parts), encoding='utf-8') as f:
        return json.load(f)


MONSTERS = _load('monsters.json')

DAMAGE_TYPES = {'slash', 'pierce', 'blunt', 'fire', 'cold', 'lightning', 'poison',
                'acid', 'holy', 'shadow', 'necrotic', 'magic', 'drain'}
MATERIAL_BANES = {'silver', 'iron'}
TAGS = {'undead', 'humanoid', 'beast', 'demon', 'aberration', 'caster', 'dragon',
        'fey', 'construct', 'elemental', 'evil', 'reptile', 'plant', 'celestial',
        'giant', 'outsider', 'orc', 'legendary', 'goblinoid', 'bandit', 'cultist',
        'shapeshifter', 'kobold', 'gnoll', 'boss', 'female_attractive', 'troll',
        'goblin'}


# --------------------------------------------------------------------- monsters

def test_monster_resistances_and_weaknesses_use_the_vocabulary():
    bad = []
    for mid, m in MONSTERS.items():
        for r in m.get('resistances') or []:
            if r not in DAMAGE_TYPES:
                bad.append((mid, 'resists', r))
        for w in m.get('weaknesses') or []:
            if w not in DAMAGE_TYPES | MATERIAL_BANES:
                bad.append((mid, 'weak', w))
    assert not bad, bad


def test_no_monster_both_resists_and_is_weak_to_a_type():
    bad = [(mid, sorted(set(m.get('resistances') or []) & set(m.get('weaknesses') or [])))
           for mid, m in MONSTERS.items()
           if set(m.get('resistances') or []) & set(m.get('weaknesses') or [])]
    assert not bad, bad


def test_monster_tags_use_the_vocabulary():
    bad = [(mid, t) for mid, m in MONSTERS.items() for t in m.get('tags') or []
           if t not in TAGS]
    assert not bad, bad


def test_every_monster_has_tags_and_real_lore():
    thin = [(mid, len((m.get('lore') or '').split())) for mid, m in MONSTERS.items()
            if not m.get('tags') or len((m.get('lore') or '').split()) < 25]
    assert not thin, thin


def test_bane_tags_reach_the_creatures_they_are_named_for():
    """Giant-slaying, troll-bane and goblin-bane weapons key on tags. Before
    this pass the classic giants and trolls were tagged only `humanoid`."""
    for mid in ('hill_giant', 'stone_giant', 'frost_giant', 'fire_giant',
                'cloud_giant', 'storm_giant'):
        assert 'giant' in MONSTERS[mid]['tags'], mid
    for mid in ('troll', 'ice_troll', 'cave_troll'):
        assert 'troll' in MONSTERS[mid]['tags'], mid
    assert {'goblin', 'goblinoid'} <= set(MONSTERS['goblin']['tags'])


def test_classic_vulnerabilities_are_present():
    assert 'blunt' in MONSTERS['skeleton']['weaknesses']
    assert 'pierce' in MONSTERS['skeleton']['resistances']
    assert 'silver' in MONSTERS['werewolf']['weaknesses']
    assert 'fire' in MONSTERS['troll']['weaknesses']
    # Sigurd killed Fafnir with one thrust from below.
    assert 'pierce' in MONSTERS['fafnir_dragon']['weaknesses']


def test_attack_names_survive_the_ranged_keyword_matching():
    """monster.py picks ranged / gaze / breath behaviour by lowercase keyword
    in the attack name. Attack names are proper labels now; the keywords must
    still be found."""
    import monster as _monster_mod  # noqa: F401  (import check)
    assert any('breath' in a['name'].lower() for a in MONSTERS['ancient_dragon']['attacks'])
    assert any('arrow' in a['name'].lower() for a in MONSTERS['skeletal_archer']['attacks'])
    lowercase = [(mid, a['name']) for mid, m in MONSTERS.items()
                 for a in m.get('attacks') or [] if a['name'] != a['name'].strip()
                 or '_' in a['name'] or a['name'][:1].islower()]
    assert not lowercase, lowercase[:10]


def test_monster_attack_log_lines_stay_lowercase_mid_sentence():
    """Brandon's rule: names are capitalised as labels, but common words stay
    lowercase inside a log sentence ("hits you with ice club")."""
    src = open(os.path.join(ROOT, 'src', 'monster.py'), encoding='utf-8').read()
    assert "hits you with {atk['name'].replace('_', ' ').lower()}" in src
    assert "hits you with {atk['name'].replace('_', ' ')}" not in src


# ------------------------------------------------------------------------ items

@pytest.mark.parametrize('cls', ['wand', 'scroll', 'spellbook', 'potion'])
def test_no_two_items_of_a_class_share_an_unidentified_name(cls):
    """Two different wands that look the same cannot be told apart and make
    the appearance worthless as a clue."""
    seen = {}
    dupes = []
    for iid, d in _load('items', f'{cls}.json').items():
        name = (d.get('unidentified_name') or '').strip().lower()
        if not name:
            continue
        if name in seen:
            dupes.append((name, seen[name], iid))
        seen[name] = iid
    assert not dupes, dupes


@pytest.mark.parametrize('cls,floor_words', [
    ('weapon', 30), ('shield', 30), ('accessory', 20), ('wand', 25),
    ('spellbook', 25), ('potion', 30), ('food', 25), ('ammo', 20)])
def test_item_lore_is_not_a_one_liner(cls, floor_words):
    thin = [(iid, len((d.get('lore') or '').split()))
            for iid, d in _load('items', f'{cls}.json').items()
            if len((d.get('lore') or '').split()) < floor_words]
    assert not thin, thin


def test_armor_damage_resistances_are_multipliers():
    """player.get_armor_resistance MULTIPLIES damage by the stored value, so
    0.85 means 15% off and 0.15 means 85% off. Most of the data had been
    written the other way round: a floor-18 shield took 85% off pierce and the
    "immune" shields (1.0) did nothing. Early gear must not gut a damage type."""
    for cls in ('armor', 'shield'):
        for iid, d in _load('items', f'{cls}.json').items():
            res = d.get('damage_resistances') or {}
            for dtype, mult in res.items():
                assert 0.0 <= mult <= 1.0, (iid, dtype, mult)
                if (d.get('peak_floor') or 0) and d['peak_floor'] < 55:
                    assert mult >= 0.5, (iid, d['peak_floor'], dtype, mult)


def test_previously_inert_weapon_bonuses_are_live():
    from items import load_items
    by_id = {w.id: w for w in load_items('weapon')}
    # authored as a dict that nothing read
    assert by_id['sword_of_michael'].bonus_damage_vs_tag.get('demon')
    # authored under a tag the loader skipped
    assert by_id['theseus_club'].bonus_damage_vs_tag.get('humanoid')
    # the dragon-slayer had no dragon bonus
    assert by_id['gram'].bonus_damage_vs_tag.get('dragon')
    assert 'giant' in by_id['sling_of_david'].effective_against
    assert 'giant' in by_id['mjolnir'].effective_against


def test_accessory_statuses_are_real_effects():
    from status_effects import EFFECT_INFO
    bad = []
    for iid, d in _load('items', 'accessory.json').items():
        st = (d.get('effects') or {}).get('status')
        if st and st not in EFFECT_INFO:
            bad.append((iid, st))
    assert not bad, bad


def test_haste_and_time_stop_scrolls_are_not_scaled_twice():
    """`power` is authored per tier and the handler multiplies by a tier factor
    again. The top haste scroll gave 95 turns and the top time stop 62."""
    scrolls = _load('items', 'scroll.json')
    assert int(scrolls['scroll_of_alacrity']['power']) <= 20
    assert int(scrolls['scroll_of_timeless']['power']) <= 12


# ----------------------------------------------------------------- potion spawn

HARMFUL = {'confusion', 'blindness', 'poison', 'paralysis', 'hallucination',
           'sleep', 'weakness', 'slow', 'drain_str', 'drain_con', 'drain_wis',
           'drain_int', 'sickness', 'fumbling', 'fear'}
HEALING = {'heal', 'extra_heal', 'full_heal'}


def _potion_shares(level):
    from dungeon import _food_weight
    tot = harm = heal = 0.0
    for d in _load('items', 'potion.json').values():
        w = _food_weight(d.get('floorSpawnWeight') or d.get('floor_spawn_weight') or {}, level)
        tot += w
        if d['effect'] in HARMFUL:
            harm += w
        if d['effect'] in HEALING:
            heal += w
    return harm / tot, heal / tot


@pytest.mark.parametrize('level', [1, 5, 10, 15, 20, 30, 45, 60, 75, 90, 100])
def test_potion_weights_favour_the_player(level):
    """By weight, harmful potions stay under a third and HP healing keeps a
    real share on every floor (it had thinned to 8% in the deep dungeon)."""
    harm, heal = _potion_shares(level)
    assert harm <= 0.34, (level, round(harm, 2))
    assert heal >= 0.12, (level, round(heal, 2))


def test_permanent_stat_loss_is_not_among_a_new_characters_first_potions():
    from dungeon import _food_weight
    sick = _load('items', 'potion.json')['potion_of_sickness']
    for level in range(1, 21):
        assert _food_weight(sick['floorSpawnWeight'], level) == 0, level


# ------------------------------------------------------------------- chest loot

class _Fake:
    def __init__(self, cls, weights=None, peak=0, pw=0.0):
        self.item_class = cls
        self.floor_spawn_weight = weights or {}
        self.peak_floor = peak
        self.peak_weight = pw
        self.spread = 10


def test_chest_common_picks_honour_spawn_weights():
    """A chest used to pick uniformly among eligible kinds, ignoring the spawn
    tables: a zero-weight potion was as likely as a healing potion."""
    from container_system import _weighted_common_pick
    common = _Fake('potion', {'1-100': 90})
    rare = _Fake('potion', {'1-100': 10})
    never = _Fake('potion', {'1-20': 0, '21-100': 50})
    rng = random.Random(7)
    picks = [_weighted_common_pick([common, rare, never], 10, rng) for _ in range(2000)]
    assert never not in picks
    assert picks.count(common) > 6 * picks.count(rare)
    # deeper, the third potion comes in
    assert never in [_weighted_common_pick([common, rare, never], 40, rng) for _ in range(500)]


def test_chest_pick_falls_back_when_every_weight_is_zero():
    from container_system import _weighted_common_pick
    a = _Fake('potion', {'50-100': 5})
    rng = random.Random(1)
    assert _weighted_common_pick([a], 3, rng) is a
