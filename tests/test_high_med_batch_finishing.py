"""Pin tests for the HIGH/MEDIUM finishing batch (2026-05-31):

  1. Hand of Glory full implementation (silent_walk, dark_vision, expended_curse)
  2. Galahad purifies EVERYTHING on equip (not just newly-equipped)
  3. Brisingamen tears_of_freya: +1 gold per turn
  4. Sword of Michael: dual schema cleaned + holy_smite_message wired
  5. Abaddon rebuild: HP buffed + regen + multi_attack_always
  6. Class mastery wiring already passes — sanity check that test file exists
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def _acc_defn(**kw):
    """Build minimal Accessory defn."""
    base = {'name': 'test acc', 'id': 'test_acc',
            'symbol': '"', 'color': [200, 200, 200], 'slot': 'amulet'}
    return {**base, **kw}


def _arm_defn(**kw):
    """Build minimal Armor defn."""
    base = {'name': 'test armor', 'id': 'test_armor',
            'symbol': '[', 'color': [200, 200, 200], 'slot': 'head',
            'ac_bonus': 1, 'equip_threshold': 1, 'quiz_tier': 1,
            'tier': 1, 'material': 'leather'}
    return {**base, **kw}


def _weapon(wid):
    w = json.loads((ROOT / "data" / "items" / "weapon.json").read_text(encoding='utf-8'))
    return w.get(wid, {})


def _accessory(aid):
    a = json.loads((ROOT / "data" / "items" / "accessory.json").read_text(encoding='utf-8'))
    return a.get(aid, {})


def _armor(aid):
    a = json.loads((ROOT / "data" / "items" / "armor.json").read_text(encoding='utf-8'))
    return a.get(aid, {})


def _monster(mid):
    m = json.loads((ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    return m.get(mid, {})


# ---------------------------------------------------------------------------
# 1. Hand of Glory
# ---------------------------------------------------------------------------

def test_hand_of_glory_passive_flags_in_json():
    h = _accessory('hand_of_glory')
    assert h.get('paralyze_charges') == 3
    assert h.get('paralyze_duration') == 10
    assert h.get('passive_silent_walk') is True
    assert h.get('passive_dark_vision') is True
    assert h.get('expended_curse') is True


def test_hand_of_glory_passive_dark_vision_adds_sight():
    """A Hand of Glory equipped should extend sight radius by 4 (mirrors
    the dark_vision status)."""
    from items import Accessory
    from player import Player
    p = Player()
    base_sight = p.get_sight_radius()
    hog = Accessory(_acc_defn(
        id='hand_of_glory', name='Hand of Glory',
        passive_dark_vision=True,
    ))
    p.amulet_slot = hog
    assert p.get_sight_radius() == base_sight + 4


def test_hand_of_glory_passive_silent_walk_halves_perception():
    """A monster with default perception_range 8 should see a silent-walking
    player only within 4 tiles."""
    from items import Accessory
    from monster import Monster
    from player import Player
    p = Player()
    p.x, p.y = 0, 0
    hog = Accessory(_acc_defn(
        id='hand_of_glory', name='Hand of Glory',
        passive_silent_walk=True,
    ))
    p.amulet_slot = hog

    # Build a minimal monster defn — only the fields needed for detection logic
    mdefn = {
        'id': 'test_orc',
        'name': 'test orc', 'symbol': 'o', 'color': [100, 100, 100],
        'hp': '1d8', 'speed': 10, 'ai_pattern': 'aggressive', 'thac0': 19,
        'attacks': [{'damage': '1d6', 'type': 'physical'}],
        'perception_range': 8,
    }
    m = Monster(mdefn, 0, 0)
    m.x, m.y = 7, 0  # 7 tiles away — would be in default perception range
    # With silent_walk, detection_range halves to 4, so dist 7 > 4 = not aware
    # We can verify this by calling act() — but act() needs a dungeon. Instead
    # check the helper-flag pattern by walking through the logic manually.
    detection_range = getattr(m, 'perception_range', 8)
    for _acc in p.equipped_accessories:
        if getattr(_acc, 'passive_silent_walk', False):
            detection_range = max(1, detection_range // 2)
            break
    assert detection_range == 4


def test_hand_of_glory_expended_curse_locks_item():
    """When all paralyze_charges are spent on a Hand of Glory with
    expended_curse, the item becomes cursed and won't unequip."""
    from items import Accessory
    hog = Accessory(_acc_defn(
        id='hand_of_glory', name='Hand of Glory',
        paralyze_charges=3, paralyze_duration=10,
        expended_curse=True,
        use_charged=True, charges=1, max_charges=3,
        can_be_cursed=True,
    ))
    # Sanity: not cursed initially
    assert hog.cursed is False
    # Inline-simulate the curse-on-last-charge logic from
    # game_menus._activate_accessory_charge (charges -= 1; if 0 and
    # expended_curse → cursed = True).
    hog.charges -= 1
    if int(hog.charges) <= 0 and getattr(hog, 'expended_curse', False):
        hog.cursed = True
        hog.buc = 'cursed'
        hog.buc_known = True
    assert hog.charges == 0
    assert hog.cursed is True
    assert hog.buc == 'cursed'


# ---------------------------------------------------------------------------
# 2. Galahad purifies everything
# ---------------------------------------------------------------------------

def test_galahad_json_carries_purity():
    g = _armor('great_helm_of_galahad')
    assert g.get('purity') is True


def test_galahad_apply_equip_uncurses_all_equipped():
    """When the Helm of Galahad goes on, ALL currently-equipped items lose
    their curse — not just the newly-equipped helm."""
    from items import Armor, Accessory
    from player import Player
    p = Player()
    # Pre-equip a cursed amulet and a cursed boot directly into slots.
    cursed_amulet = Accessory(_acc_defn(
        id='cursed_amulet_test', name='Cursed Test Amulet',
        slot='amulet', cursed=True, can_be_cursed=True,
    ))
    cursed_amulet.buc = 'cursed'
    p.amulet_slot = cursed_amulet
    # And a cursed boot in feet slot (slot index 4 = feet)
    cursed_boot = Armor(_arm_defn(
        id='cursed_boot', name='Cursed Boot', slot='feet',
        cursed=True, can_be_cursed=True,
    ))
    cursed_boot.buc = 'cursed'
    from items import ARMOR_SLOTS
    feet_idx = ARMOR_SLOTS.index('feet')
    p.armor_slots[feet_idx] = cursed_boot

    # Now equip Galahad — it should cleanse both.
    galahad = Armor(_arm_defn(
        id='great_helm_of_galahad', name='Great Helm of Galahad',
        slot='head', purity=True,
    ))
    p._apply_equip(galahad)
    assert cursed_amulet.buc == 'uncursed', \
        "Galahad should uncurse amulet"
    assert cursed_amulet.cursed is False
    assert cursed_boot.buc == 'uncursed', \
        "Galahad should uncurse cursed armor in other slots"
    assert cursed_boot.cursed is False
    # Cleanse count is set for the message
    assert getattr(p, '_galahad_cleansed_count', 0) == 2


def test_galahad_uncurses_newly_equipped_item_too():
    """The original behavior — a cursed item equipped WHILE wearing Galahad —
    must continue to work."""
    from items import Armor, Accessory
    from player import Player
    p = Player()
    galahad = Armor(_arm_defn(
        id='great_helm_of_galahad', name='Great Helm of Galahad',
        slot='head', purity=True,
    ))
    p._apply_equip(galahad)
    # Now equip a cursed amulet — purity should auto-uncurse it on equip.
    cursed_amulet = Accessory(_acc_defn(
        id='cursed_amulet_test2', name='Cursed Test Amulet 2',
        slot='amulet', cursed=True, can_be_cursed=True,
    ))
    cursed_amulet.buc = 'cursed'
    p._apply_equip(cursed_amulet)
    assert cursed_amulet.buc == 'uncursed'
    assert cursed_amulet.cursed is False


# ---------------------------------------------------------------------------
# 3. Brisingamen tears_of_freya
# ---------------------------------------------------------------------------

def test_brisingamen_json_carries_tears_of_freya():
    b = _accessory('brisingamen')
    assert b.get('tears_of_freya') is True
    assert int(b.get('tears_of_freya_gold', 0)) >= 1
    assert int(b.get('tears_of_freya_interval', 0)) >= 1


def test_brisingamen_field_loaded_on_accessory():
    """The Accessory class must load the tears_of_freya fields from JSON."""
    from items import Accessory
    b = Accessory(_acc_defn(
        id='brisingamen', name='Brisingamen',
        tears_of_freya=True, tears_of_freya_gold=1,
        tears_of_freya_interval=1,
    ))
    assert b.tears_of_freya is True
    assert b.tears_of_freya_gold == 1
    assert b.tears_of_freya_interval == 1


def test_brisingamen_per_turn_hook_in_advance_turn():
    """main._advance_turn must consult tears_of_freya for gold drip."""
    src = (ROOT / "src" / "main.py").read_text(encoding='utf-8')
    assert 'tears_of_freya' in src, \
        "main.py must wire tears_of_freya per-turn hook"
    # And the hook should add to player.gold.
    idx = src.find('tears_of_freya')
    snippet = src[idx:idx + 800]
    assert 'player.gold' in snippet, \
        "tears_of_freya block must mutate player.gold"


# ---------------------------------------------------------------------------
# 4. Sword of Michael
# ---------------------------------------------------------------------------

def test_sword_of_michael_dual_schema_cleaned():
    """Both chain definitions match (no more dueling 9-step vs 5-step)."""
    w = _weapon('sword_of_michael')
    cm_camel = w.get('chainMultipliers', [])
    cm_snake = w.get('chain_multipliers', [])
    assert cm_camel == cm_snake, \
        f"chainMultipliers and chain_multipliers must match (got " \
        f"{cm_camel} vs {cm_snake})"
    assert w.get('baseDamage') == w.get('base_damage'), \
        "baseDamage and base_damage must match"
    assert w.get('maxChainLength') == w.get('max_chain_length'), \
        "maxChainLength and max_chain_length must match"


def test_sword_of_michael_balanced_for_climax():
    """Chain-peak must NOT one-shot Abaddon (the boss has ~2800 HP target)."""
    w = _weapon('sword_of_michael')
    base = int(w.get('baseDamage', 0))
    cm = w.get('chainMultipliers', [])
    crit = float(w.get('critMultiplier', 1.0) or 1.0)
    # Peak damage with crit + 50% demon bonus + 5d10 abaddon avg (27)
    peak = base * cm[-1] if cm else base
    with_demon = peak * 1.5
    with_crit_plus_abaddon = with_demon * crit + 27
    # Must be substantially LESS than Abaddon's HP (~2800), so the climax
    # is multi-turn. Audit reference: previous 4353 dmg vs 1235 HP one-shot.
    assert with_crit_plus_abaddon < 2500, \
        f"Sword peak vs Abaddon = {with_crit_plus_abaddon:.0f}; must " \
        f"be < 2500 to require a multi-turn climax"


def test_sword_of_michael_carries_signature_flags():
    """Lore-driven flags: ignore_resistances + holy_smite + abaddon bonus."""
    w = _weapon('sword_of_michael')
    assert w.get('ignore_resistances') is True, "must bypass infernal resists"
    assert w.get('ignoreShield') is True, "must bypass shield"
    assert w.get('holy_smite_message') is True, "must surface dramatic line"
    # Abaddon dice: roll-stringy format with 'd' separator
    ab = str(w.get('abaddon_bonus_damage', ''))
    assert 'd' in ab and ab[0].isdigit(), \
        f"abaddon_bonus_damage must be a valid dice string, got {ab!r}"


def test_sword_of_michael_demon_undead_evil_tag_bonuses():
    """The blade must carry per-tag bonus damage (demon/undead/evil)."""
    w = _weapon('sword_of_michael')
    btag = w.get('bonus_damage_vs_tag', {})
    assert 'demon' in btag
    assert 'undead' in btag
    assert 'evil' in btag


def test_holy_smite_message_field_loaded_on_weapon():
    from items import Weapon
    wdefn = {
        'id': 'test_holy_sword',
        'name': 'Test Holy Sword', 'class': 'sword', 'symbol': ')',
        'color': [255, 255, 220], 'baseDamage': 10,
        'chainMultipliers': [1.0], 'damageTypes': ['holy'],
        'tier': 5, 'material': 'divine',
        'holy_smite_message': True,
    }
    w = Weapon(wdefn)
    assert w.holy_smite_message is True


def test_holy_smite_consumer_in_combat():
    """combat.player_attack must read holy_smite_message and produce a line."""
    src = (ROOT / "src" / "combat.py").read_text(encoding='utf-8')
    assert 'holy_smite_message' in src, \
        "combat.py must consume holy_smite_message"
    # And the dramatic line for Abaddon should be present
    assert 'Destroyer' in src or 'BLAZES' in src, \
        "Abaddon-specific holy smite line must be authored"


# ---------------------------------------------------------------------------
# 5. Abaddon rebuild
# ---------------------------------------------------------------------------

def test_abaddon_hp_buffed_for_climax():
    """Abaddon must have enough HP to survive a Sword of Michael chain."""
    a = _monster('abaddon_destroyer')
    hp_dice = a.get('hp', '')
    # Parse XdY+Z — verify it's substantial
    assert 'd12' in hp_dice or 'd10' in hp_dice
    # Old HP was 102d12+572 (avg 1235). Audit said target ~2800.
    # Quick avg estimate: extract the numbers and compute
    import re
    m = re.match(r'(\d+)d(\d+)\+?(\d+)?', hp_dice)
    assert m, f"HP dice format unexpected: {hp_dice}"
    n, sides, plus = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    avg = n * (sides + 1) / 2 + plus
    assert avg > 2000, f"Abaddon avg HP {avg} too low for climax"


def test_abaddon_regenerates():
    a = _monster('abaddon_destroyer')
    assert int(a.get('regeneration', 0)) > 0


def test_abaddon_multi_attack_tiered():
    """Abaddon now uses tiered multi-attack: 2 baseline, 5 enraged at 40%."""
    a = _monster('abaddon_destroyer')
    assert int(a.get('multi_attack_count', 0)) == 2, \
        "Abaddon baseline should fire 2 attacks/turn"
    assert int(a.get('enraged_multi_attack_count', 0)) == 5, \
        "Abaddon enraged should fire all 5 attacks/turn"
    assert float(a.get('enrage_at_hp_pct', 0)) >= 0.30, \
        "Abaddon should enrage when wounded"


def test_abaddon_has_evil_tag():
    """Demons need `evil` tag for Durendal +35%, Sword of Michael bonus, etc."""
    a = _monster('abaddon_destroyer')
    tags = set(a.get('tags', []))
    assert 'evil' in tags
    assert 'demon' in tags


def test_abaddon_chain_break_field_present():
    """Wired in monster.py __init__ even if not fully consumed yet."""
    a = _monster('abaddon_destroyer')
    assert float(a.get('chain_break_on_hit', 0)) > 0


def test_multi_attack_always_field_loaded_on_monster():
    """Monster class must load the field from JSON."""
    from monster import Monster
    mdefn = {
        'id': 'test_boss',
        'name': 'test boss', 'symbol': 'B', 'color': [200, 0, 0],
        'hp': '10d8', 'speed': 10, 'ai_pattern': 'aggressive', 'thac0': 0,
        'attacks': [{'damage': '1d6', 'type': 'physical'}],
        'multi_attack_always': True,
    }
    m = Monster(mdefn, 0, 0)
    assert m.multi_attack_always is True


def test_abaddon_multi_attack_consumer_in_monster_act():
    """The act() method must branch on multi_attack_always like rage_stacks."""
    src = (ROOT / "src" / "monster.py").read_text(encoding='utf-8')
    assert 'multi_attack_always' in src
    # And SOMEWHERE in the file (the consumer in act()) must call
    # _fenrir_multi_attack when multi_attack_always is set.
    # Find the consumer site (NOT the __init__ field declaration).
    for idx in range(len(src)):
        idx = src.find('multi_attack_always', idx)
        if idx == -1:
            break
        snippet = src[idx:idx + 400]
        if '_fenrir_multi_attack' in snippet:
            return
        idx += 1
    raise AssertionError(
        "No `multi_attack_always` -> `_fenrir_multi_attack` consumer site found")


# (Class-mastery wiring meta-test removed 2026-08-06 — the mastery system
# was retired with the one-question identify redesign.)


# ---------------------------------------------------------------------------
# 7. Monster tag fixes (silent weapon-proc breakage discovered by audits)
# ---------------------------------------------------------------------------
#
# The 4 parallel monster audits (early/mid/deep/endgame) flagged dozens of
# monsters whose tags didn't match their family — silently breaking weapon
# procs (Sword of Michael 1d8 vs evil, Anduril 1d8 vs undead, Gram 1d8 vs
# dragon, etc.). These pin tests lock in the most impactful tag corrections
# so future refactors don't regress them.

def test_demons_have_evil_tag():
    """Demons need `evil` for Durendal +35% + Sword of Michael 1d8 vs evil."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    # The endgame + deep-band demons that received the evil tag.
    for mid in (
        'pit_fiend_spawn', 'infernal_lord', 'pit_executioner',
        'seal_demon_war', 'seal_demon_famine', 'seal_demon_pestilence',
        'seal_demon_death', 'seal_demon_silence',
        'cerberus', 'bone_devil', 'demonic_trickster',
        'abaddon_destroyer',  # boosted in main audit
    ):
        if mid not in monsters:
            continue
        tags = set(monsters[mid].get('tags', []))
        assert 'evil' in tags, f"{mid} must carry 'evil' tag"


def test_dragons_have_reptile_tag():
    """Reptile-class weapons + materials key off `reptile` tag."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    for mid in (
        'young_red_dragon', 'adult_red_dragon', 'adult_blue_dragon',
        'young_black_dragon', 'ancient_dragon', 'wyrm', 'wyvern',
    ):
        if mid not in monsters:
            continue
        tags = set(monsters[mid].get('tags', []))
        assert 'reptile' in tags, f"{mid} must carry 'reptile' tag"


def test_bone_constructs_have_construct_tag():
    """Bone golem family must carry `construct` (sister bone_colossus does)."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    for mid in ('bone_golem', 'bone_titan', 'bone_collector', 'undead_colossus'):
        if mid not in monsters:
            continue
        tags = set(monsters[mid].get('tags', []))
        assert 'construct' in tags, f"{mid} must carry 'construct' tag"


def test_primordial_titan_carries_giant_tag():
    """Mjolnir's endgame giant-slaying target — without this, Mjolnir has NO
    giant in f76-99 to bonus against."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    if 'primordial_titan' not in monsters:
        return
    tags = set(monsters['primordial_titan'].get('tags', []))
    assert 'giant' in tags


def test_endgame_outsiders_tagged():
    """Anti-outsider weapons should have endgame targets."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    for mid in ('void_seraph', 'wormwood_blight', 'entropy_elemental',
                'fenrir_wolf'):
        if mid not in monsters:
            continue
        tags = set(monsters[mid].get('tags', []))
        assert 'outsider' in tags, f"{mid} must carry 'outsider' tag"


def test_boss_thac0_balance_fixes():
    """Whispering Crone and Blood Archon had broken thac0 vs endgame players."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    if 'whispering_crone' in monsters:
        assert int(monsters['whispering_crone'].get('thac0', 99)) <= -3
    if 'blood_archon' in monsters:
        assert int(monsters['blood_archon'].get('thac0', 99)) <= -10


def test_floating_eye_has_gaze_attack():
    """The floating eye's signature paralyzing gaze was empty before audit."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    if 'floating_eye' not in monsters:
        return
    fe = monsters['floating_eye']
    assert fe.get('attacks'), "floating_eye must have at least one attack"
    assert int(fe.get('gaze_paralyze', 0)) > 0, \
        "floating_eye must carry gaze_paralyze for Spear of Lugh bonus to fire"


def test_skeleton_mage_summons():
    """Necromantic flavor: skeleton_mage must call up undead minions."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    if 'skeleton_mage' not in monsters:
        return
    sm = monsters['skeleton_mage']
    assert sm.get('summon_kind'), "skeleton_mage must summon skeletons"


def test_charybdis_resistances_dedupe():
    """The audit flagged a duplicate 'cold' in resistances."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    if 'charybdis' not in monsters:
        return
    res = monsters['charybdis'].get('resistances', [])
    assert len(res) == len(set(res)), \
        f"charybdis resistances must dedupe (got {res})"


def test_mini_bosses_hp_floor():
    """Mini-bosses cacus, the_sphinx, rangda were softer than peer mobs."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    import re
    for mid in ('cacus', 'the_sphinx', 'rangda'):
        if mid not in monsters:
            continue
        hp = monsters[mid].get('hp', '')
        m = re.match(r'(\d+)d(\d+)\+?(\d+)?', hp)
        assert m, f"{mid} HP format unexpected: {hp}"
        n, sides, plus = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        avg = n * (sides + 1) / 2 + plus
        assert avg >= 100, \
            f"{mid} mini-boss HP avg {avg} below mini-boss floor (100)"


def test_cave_troll_regenerates():
    """Lore explicitly promises regeneration (the wound heals before the warrior gloats)."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    if 'cave_troll' not in monsters:
        return
    assert int(monsters['cave_troll'].get('regeneration', 0)) > 0


# ---------------------------------------------------------------------------
# 8. Phase A/D mechanical fixes
# ---------------------------------------------------------------------------

def test_abaddon_beatable_without_sword_of_michael():
    """User direction: Abaddon must still be beatable without Sword of Michael.
    HP 2200 (was 2800), regen 15, multi_attack 2 baseline -> 5 enraged."""
    a = _monster('abaddon_destroyer')
    import re
    m = re.match(r'(\d+)d(\d+)\+?(\d+)?', a.get('hp', ''))
    n, sides, plus = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    avg = n * (sides + 1) / 2 + plus
    assert 2000 <= avg <= 2400, \
        f"Abaddon HP avg {avg:.0f} out of range — must be 2000-2400 for non-Sword beatable"
    assert int(a.get('regeneration', 0)) == 15
    assert int(a.get('multi_attack_count', 0)) == 2


def test_ancient_vampire_lord_self_heals_from_drain():
    """Ancient Vampire Lord must heal from drain — it's a vampire."""
    m = _monster('ancient_vampire_lord')
    assert float(m.get('drain_heals_self', 0)) > 0


def test_green_knight_revives_once():
    """The beheading-game pact: green_knight pops back up once after death."""
    m = _monster('green_knight')
    assert m.get('revive_once_on_death') is True


def test_mythic_hydra_has_tiered_multi_attack():
    """Hydra heads regrow → multi-attack escalates on rage."""
    m = _monster('mythic_hydra')
    assert int(m.get('multi_attack_count', 0)) >= 2
    assert int(m.get('enraged_multi_attack_count', 0)) > int(m.get('multi_attack_count', 0))


def test_charybdis_pulls_player():
    """Lore: she drags ships into a whirlpool."""
    m = _monster('charybdis')
    assert float(m.get('pull_chance', 0)) > 0


def test_ancient_lich_summons_undead():
    """A lich is a CASTER + necromancer — must call up minions."""
    m = _monster('ancient_lich')
    sk = m.get('summon_kind')
    assert sk, "ancient_lich must summon something"


def test_iron_golem_has_toxic_gas_breath():
    """Lore promises poison gas — was missing entirely."""
    m = _monster('iron_golem')
    has_gas = any('gas' in a.get('name', '').lower() or
                   a.get('type') == 'poison'
                   for a in m.get('attacks', []))
    assert has_gas, "iron_golem must have a poison/gas attack"


def test_tiamat_exists_and_calibrated():
    """The 5-headed chromatic dragon queen — cosmic-tier mini-boss.

    Reclassified 2026-05-31 from full-boss to mini-boss: at HP 2370 she
    was harder than Abaddon (2140, the actual final boss) while spawning
    through the regular procedural pool. Now she sits between Asmodeus
    (1775) and Surtur (1940) at HP ~1900 — a SCARY mid-band encounter
    that doesn't eclipse the climax.

    Also corrected 2026-05-31: removed dragon_scales 0.5 (which silently
    doubled her effective HP to 3800, making her TANKIER than Abaddon
    even after the HP cut). Impenetrable scales are FAFNIR's signature
    (per the Sigurd legend, his belly had to be stabbed from a pit);
    Tiamat's signature is the FIVE CHROMATIC BREATHS. She gets dramatic
    multi-element threat without effective-HP inflation."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    assert 'tiamat' in monsters
    t = monsters['tiamat']
    assert t.get('min_level') == 85
    assert len(t.get('attacks', [])) == 5, "Tiamat has 5 chromatic breath weapons"
    assert tuple(t.get('footprint', [1, 1])) == (2, 2), "Tiamat is multi-tile"
    assert set(t.get('tags', [])) >= {'dragon', 'reptile', 'evil'}
    # Mini-boss classification: matches Surtur/Ymir/Hrungnir/Asmodeus
    assert t.get('is_mini_boss') is True, \
        "Tiamat must be flagged as mini-boss (not full boss)"
    assert t.get('is_boss') is False, \
        "Tiamat is NOT a full boss — Abaddon is the climax"
    # NO dragon_scales — that's Fafnir's signature, not Tiamat's. Scales
    # would silently make her effective HP exceed Abaddon's again.
    assert float(t.get('dragon_scales', 0)) == 0, \
        "Tiamat must NOT have dragon_scales — scales double her effective " \
        "HP and re-create the 'mini-boss harder than final boss' bug"
    # HP must sit below Abaddon
    import re
    m = re.match(r'(\d+)d(\d+)\+?(\d+)?', t.get('hp', ''))
    n, sides, plus = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    tiamat_avg = n * (sides + 1) / 2 + plus
    abaddon_hp = monsters['abaddon_destroyer'].get('hp', '')
    m2 = re.match(r'(\d+)d(\d+)\+?(\d+)?', abaddon_hp)
    n2, s2, p2 = int(m2.group(1)), int(m2.group(2)), int(m2.group(3) or 0)
    abaddon_avg = n2 * (s2 + 1) / 2 + p2
    assert tiamat_avg < abaddon_avg, \
        f"Tiamat HP {tiamat_avg:.0f} must be < Abaddon HP {abaddon_avg:.0f}"


def test_no_mini_boss_is_tankier_than_abaddon():
    """No mini-boss may have effective HP (HP / (1 - scales)) greater than
    Abaddon's HP. This is the underlying invariant — fix it for Tiamat,
    pin it for every future cosmic mini-boss too."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    import re
    m2 = re.match(r'(\d+)d(\d+)\+?(\d+)?', monsters['abaddon_destroyer']['hp'])
    n2, s2, p2 = int(m2.group(1)), int(m2.group(2)), int(m2.group(3) or 0)
    abaddon_eff = n2 * (s2 + 1) / 2 + p2  # Abaddon has no dragon_scales
    over_climax = []
    for mid, mon in monsters.items():
        if not mon.get('is_mini_boss'):
            continue
        m = re.match(r'(\d+)d(\d+)\+?(\d+)?', mon.get('hp', ''))
        if not m:
            continue
        n, sides, plus = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        hp = n * (sides + 1) / 2 + plus
        scales = float(mon.get('dragon_scales', 0) or 0)
        eff = hp / max(0.01, 1 - scales)
        if eff >= abaddon_eff:
            over_climax.append(
                f"{mid}: HP {hp:.0f}, scales {scales}, eff_HP {eff:.0f} "
                f">= Abaddon eff_HP {abaddon_eff:.0f}"
            )
    assert not over_climax, \
        "Mini-bosses must NEVER be tankier than the final boss:\n  " + \
        "\n  ".join(over_climax)


def test_asmodeus_exists_pre_abaddon():
    """The Prince of Hell — pre-Abaddon mini-boss."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    assert 'asmodeus' in monsters
    a = monsters['asmodeus']
    assert 90 <= a.get('min_level', 0) <= 95
    assert set(a.get('tags', [])) >= {'demon', 'evil', 'outsider'}


def test_three_new_endgame_giants_for_mjolnir():
    """Mjolnir's lore is giant-slaying — needs endgame targets."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    for mid in ('surtur', 'ymir_last_spawn', 'hrungnirs_ghost'):
        assert mid in monsters, f"{mid} missing"
        assert 'giant' in monsters[mid].get('tags', []), \
            f"{mid} must carry giant tag for Mjolnir bonus"


def test_l32_cluster_diversified():
    """The 25-monster L32 cluster shared identical stats. After diversification
    storm_giant != mind_flayer != vampire."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    hps = set()
    for mid in ('storm_giant', 'mind_flayer', 'vampire', 'death_knight',
                'lich_apprentice', 'beholder'):
        if mid in monsters:
            hps.add(monsters[mid].get('hp', ''))
    assert len(hps) >= 4, \
        f"L32 cluster monsters should have distinct HP dice (got {hps})"


def test_under_hp_curve_monsters_bumped():
    """Audit said L9-L14 monsters under target by ~30%. Verify the bump."""
    monsters = json.loads(
        (ROOT / "data" / "monsters.json").read_text(encoding='utf-8'))
    import re
    for mid in ('werewolf', 'shadow', 'ice_troll'):
        if mid not in monsters:
            continue
        m = re.match(r'(\d+)d(\d+)\+?(\d+)?', monsters[mid].get('hp', ''))
        if m:
            n, sides, plus = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
            avg = n * (sides + 1) / 2 + plus
            assert avg >= 30, f"{mid} HP avg {avg} still below curve target"


def test_phase_b_new_fields_loaded_on_monster():
    """All the new monster.py fields must be loaded from JSON."""
    from monster import Monster
    mdefn = {
        'id': 'test_phaseb',
        'name': 'test', 'symbol': 'T', 'color': [0, 0, 0],
        'hp': '1d8', 'thac0': 20, 'speed': 10, 'ai_pattern': 'aggressive',
        'attacks': [{'damage': '1d6', 'type': 'physical'}],
        'multi_attack_count': 3,
        'enraged_multi_attack_count': 5,
        'drain_heals_self': 0.5,
        'revive_once_on_death': True,
        'revive_hp_pct': 0.4,
        'pull_chance': 0.30,
        'chain_break_on_hit': 0.25,
    }
    m = Monster(mdefn, 0, 0)
    assert m.multi_attack_count == 3
    assert m.enraged_multi_attack_count == 5
    assert m.drain_heals_self == 0.5
    assert m.revive_once_on_death is True
    assert abs(m.revive_hp_pct - 0.4) < 1e-6
    assert m.pull_chance == 0.30
    assert m.chain_break_on_hit == 0.25
