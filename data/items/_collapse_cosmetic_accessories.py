"""One-cosmetic-per-item migration (2026-06-07).

See proposals/design/one_cosmetic_appearances.md.

Rings and amulets carried up to 8 cosmetic appearance-variants per FUNCTIONAL
type (8x "ring of warning", 7x "ring of searching", ...), every one a separate
JSON item that spawned independently. This made the unidentified-appearance pool
a lie ("which silver/malachite/ivory ring is searching?") and rained
mechanically-identical duplicates into the pack.

This script does three things to data/items/accessory.json (round-trip guarded,
idempotent):

  1. COLLAPSE purely-cosmetic groups -> ONE canonical entry per functional type.
     {warning, searching, telepathy, regeneration, the 5 resist rings, the 3
     cosmetic amulets}. The survivor keeps effects/slot/min_level/quiz_tier/etc.;
     its per-variant material `unidentified_name` is replaced with a neutral
     fallback ("a ring" / "an amulet") because the real look is dealt PER RUN
     from the appearance pool (see #3). Its `color` is set neutral for the same
     reason. floorSpawnWeight is restored to the natural single-item value (the
     1/N stopgap in _fix_accessory_spawn_weights.py is superseded).

  2. DISAMBIGUATE tiered stat groups (strength/con/dex/int/wis/per). These are
     NOT cosmetic dupes -- they are +1/+2/+3 POWER TIERS that shared one display
     name. Rename so each tier is honest:
         +1 -> "ring of <stat>"            (base name kept on lowest tier)
         +2 -> "ring of greater <stat>"
         +3 -> "ring of master <stat>"
     Amulets only have +2/+3, so: "amulet of <stat>" (+2) / "amulet of greater
     <stat>" (+3). Same-tier cosmetic dupes (+3 adamantine/mithril; the two +2
     rings; ...) MERGE into one survivor per tier. Power + bell-curve floor
     weights are PRESERVED byte-for-byte on the survivor. After renaming each
     tier is its own 1:1 type and flows through the appearance pool too.

  3. EMIT data/items/accessory_appearances.json -- a per-slot pool of
     {name,color} looks harvested from the deleted variants' own
     unidentified_name/color pairs (well-written, plentiful). main.py shuffles
     this once per run and deals one look to each unidentified accessory type.

It also writes the deleted-id -> survivor-id remap to stdout (and asserts it
matches src/items.py LEGACY_ACCESSORY_ID_REMAP, the table save-load uses to heal
old saves holding now-removed ids).

Run:   python data/items/_collapse_cosmetic_accessories.py
       python data/items/_collapse_cosmetic_accessories.py --check
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ACC_PATH = HERE / 'accessory.json'
APPEAR_PATH = HERE / 'accessory_appearances.json'

# ----------------------------------------------------------------------
# Group definitions
# ----------------------------------------------------------------------
# Cosmetic groups: every variant has IDENTICAL effects. We keep ONE survivor
# (the first listed id) under a canonical id, and delete the rest. The survivor
# is re-keyed to the canonical id and stripped of its material look.

# {canonical_id: (display_name, slot, [variant ids in spawn-priority order])}
# The survivor INHERITS the first variant's mechanical fields (effects,
# min_level, quiz_tier, equip_threshold, spread, peak_floor, floorSpawnWeight,
# weight, symbol) so the canonical entry behaves exactly like the group did.
COSMETIC_GROUPS = {
    'ring_of_warning': ('ring of warning', 'ring', [
        'ring_warning_oak', 'ring_warning_runed_metal', 'ring_warning_ancient_copper',
        'ring_warning_bone', 'ring_warning_twisted_iron', 'ring_warning_carved_jade',
        'ring_warning_rough_stone', 'ring_warning_grey_granite']),
    'ring_of_searching': ('ring of searching', 'ring', [
        'ring_searching_silver', 'ring_searching_polished_crystal', 'ring_searching_malachite',
        'ring_searching_engraved_pewter', 'ring_searching_gleaming_iron',
        'ring_searching_pale_ivory', 'ring_searching_mossy_stone']),
    'ring_of_telepathy': ('ring of telepathy', 'ring', [
        'ring_telepathy_sapphire', 'ring_telepathy_lapis_lazuli', 'ring_telepathy_cobalt_blue',
        'ring_telepathy_dark_obsidian', 'ring_telepathy_moonstone', 'ring_telepathy_twilight_crystal']),
    'ring_of_regeneration': ('ring of regeneration', 'ring', [
        'ring_regen_emerald', 'ring_regen_peridot', 'ring_regen_serpentine',
        'ring_regen_verdant_jade', 'ring_regen_living_wood']),
    'ring_of_fire_resist': ('ring of fire resist', 'ring', ['ring_fire_res_a', 'ring_fire_res_b']),
    'ring_of_cold_resist': ('ring of cold resist', 'ring', ['ring_cold_res_a', 'ring_cold_res_b']),
    'ring_of_shock_resist': ('ring of shock resist', 'ring', ['ring_shock_res_a', 'ring_shock_res_b']),
    'ring_of_poison_resist': ('ring of poison resist', 'ring', ['ring_poison_res_a', 'ring_poison_res_b']),
    'ring_of_sleep_resist': ('ring of sleep resist', 'ring', ['ring_sleep_res_a', 'ring_sleep_res_b']),
    'amulet_of_warning': ('amulet of warning', 'amulet', ['amulet_warning_leather', 'amulet_warning_copper']),
    'amulet_of_searching': ('amulet of searching', 'amulet', ['amulet_searching_bone', 'amulet_searching_bronze']),
    'amulet_of_telepathy': ('amulet of telepathy', 'amulet', ['amulet_telepathy_silver', 'amulet_telepathy_jade']),
}

# Tiered stat groups: variants differ by `amount`. Survivor per tier keeps its
# own mechanical fields (power + spawn weights) but is RENAMED + re-keyed to a
# canonical id. Within a tier, the first id is the survivor and any same-tier
# dupes are deleted (remapped onto the survivor).
#
# {stat: (slot, base_word, {amount: [ids at that amount, survivor first]})}
#
# The tier ADJECTIVE depends on slot, because the lowest tier present differs:
# rings run +1/+2/+3 so the base name lives on +1; amulets only have +2/+3 so
# the base name lives on +2 (per the design proposal). This keeps the existing
# `amulet_of_strength` mastery slug valid (it points at the +2 amulet) and means
# the only new amulet slug needed is the +3 "greater" tier.
_TIER_WORD_RING   = {1: '', 2: 'greater', 3: 'master'}
_TIER_WORD_AMULET = {2: '', 3: 'greater'}


def _tier_word(slot: str, tier: int) -> str:
    table = _TIER_WORD_AMULET if slot == 'amulet' else _TIER_WORD_RING
    return table[tier]

TIERED_GROUPS = {
    # rings -- 3 tiers each (+1/+2/+3)
    'ring/strength':     ('ring', 'strength', {
        1: ['ring_strength_iron'], 2: ['ring_strength_steel'],
        3: ['ring_strength_adamantine', 'ring_strength_mithril']}),
    'ring/constitution': ('ring', 'constitution', {
        1: ['ring_constitution_ruby'], 2: ['ring_constitution_coral', 'ring_constitution_carnelian'],
        3: ['ring_constitution_garnet']}),
    'ring/dexterity':    ('ring', 'dexterity', {
        1: ['ring_dexterity_quicksilver'], 2: ['ring_dexterity_thin_wire', 'ring_dexterity_spun_glass'],
        3: ['ring_dexterity_featherweight']}),
    'ring/intellect':    ('ring', 'intellect', {
        1: ['ring_intellect_amethyst'], 2: ['ring_intellect_purple_glass', 'ring_intellect_arcane_pewter'],
        3: ['ring_intellect_prismatic']}),
    'ring/wisdom':       ('ring', 'wisdom', {
        1: ['ring_wisdom_opal'], 2: ['ring_wisdom_pearl', 'ring_wisdom_ivory'],
        3: ['ring_wisdom_white_quartz']}),
    'ring/perception':   ('ring', 'perception', {
        1: ['ring_perception_topaz'], 2: ['ring_perception_amber', 'ring_perception_citrine'],
        3: ['ring_perception_hawks_eye']}),
    # amulets -- 2 tiers each (+2/+3); base name kept on the +2 tier
    'amulet/strength':     ('amulet', 'strength', {
        2: ['amulet_strength_iron_medallion'], 3: ['amulet_strength_titan_iron_pendant']}),
    'amulet/constitution': ('amulet', 'constitution', {
        2: ['amulet_constitution_ruby_pendant'], 3: ['amulet_constitution_guardian_ruby_locket']}),
    'amulet/dexterity':    ('amulet', 'dexterity', {
        2: ['amulet_dexterity_quicksilver_charm'], 3: ['amulet_dexterity_air_light_locket']}),
    'amulet/intellect':    ('amulet', 'intellect', {
        2: ['amulet_intellect_amethyst_talisman'], 3: ['amulet_intellect_brilliant_crystal_medallion']}),
    'amulet/wisdom':       ('amulet', 'wisdom', {
        2: ['amulet_wisdom_opal_locket'], 3: ['amulet_wisdom_sage_ivory_locket']}),
    'amulet/perception':   ('amulet', 'perception', {
        2: ['amulet_perception_eagle_eye_pendant'], 3: ['amulet_perception_hawk_feather_talisman']}),
}

# Neutral fallback look per slot (overwritten per run by the appearance map; only
# seen if the appearance map is somehow missing).
NEUTRAL = {
    'ring':   {'name': 'a ring', 'color': [200, 200, 210]},
    'amulet': {'name': 'an amulet', 'color': [200, 200, 210]},
}

# Restore the natural single-item floorSpawnWeight for the cosmetic survivors.
# These groups had their weights divided by variant-count (the
# _fix_accessory_spawn_weights.py stopgap) -- e.g. warning landed at 10 (80/8),
# searching 11 (80/7). Now that each is ONE item, give it the per-type rate a
# 1:1 common of its tier carries: tier-1 utility rings mirror the strength
# ring's bell (20 tapering to 10); tier-2 mirror the resist ring's bell (40
# tapering to 20). Declared (not multiplied) so the migration stays idempotent.
_T1_BELL = {'1-20': 20, '21-40': 20, '41-60': 20, '61-80': 10, '81-100': 10}
_T2_BELL = {'1-20': 40, '21-40': 40, '41-60': 40, '61-80': 40, '81-100': 20}
RESTORE_WEIGHT = {
    'ring_of_warning':      _T1_BELL,
    'ring_of_searching':    _T1_BELL,
    'ring_of_telepathy':    _T2_BELL,
    'ring_of_regeneration': _T2_BELL,
    # resist rings + cosmetic amulets already sit at their natural per-type rate
    # (their _a/_b groups divided 80/2 -> 40, which is the intended common rate),
    # so they are intentionally absent here and keep their existing weights.
}


def _canonical_tier_id(slot: str, base_word: str, tier: int) -> str:
    word = _tier_word(slot, tier)
    prefix = f"{word}_" if word else ''
    return f"{slot}_of_{prefix}{base_word}"


def build(acc: dict) -> tuple[dict, dict, dict]:
    """Return (new_acc, remap, appearance_pool).

    new_acc        -- the rewritten accessory dict
    remap          -- {deleted_or_renamed_old_id: survivor_canonical_id}
    appearance_pool-- {'ring': [...], 'amulet': [...]} of {name,color}
    """
    new_acc = dict(acc)  # start from a shallow copy; we'll pop + re-add
    remap: dict[str, str] = {}
    pool: dict[str, list] = {'ring': [], 'amulet': []}
    pool_seen: dict[str, set] = {'ring': set(), 'amulet': set()}

    def harvest(defn: dict, slot: str):
        nm = defn.get('unidentified_name')
        col = defn.get('color')
        if not nm or not isinstance(col, list):
            return
        key = nm.strip().lower()
        if key in pool_seen[slot]:
            return
        pool_seen[slot].add(key)
        pool[slot].append({'name': nm, 'color': list(col)})

    # ---- Cosmetic groups ----
    for canon_id, (name, slot, variant_ids) in COSMETIC_GROUPS.items():
        present = [vid for vid in variant_ids if vid in acc]
        if not present:
            continue
        survivor_src = acc[present[0]]
        # Harvest looks from ALL variants (including survivor) for the pool.
        for vid in present:
            harvest(acc[vid], slot)
        # Build the canonical survivor from the first variant's mechanical fields.
        survivor = dict(survivor_src)
        survivor['name'] = name
        survivor['slot'] = slot
        survivor['unidentified_name'] = NEUTRAL[slot]['name']
        survivor['color'] = list(NEUTRAL[slot]['color'])
        survivor['is_unique'] = False
        if canon_id in RESTORE_WEIGHT:
            survivor['floorSpawnWeight'] = dict(RESTORE_WEIGHT[canon_id])
        # Remove all variant ids from the output, then add the canonical one.
        for vid in present:
            new_acc.pop(vid, None)
            if vid != canon_id:
                remap[vid] = canon_id
        new_acc[canon_id] = survivor

    # ---- Tiered groups ----
    for _grp, (slot, base_word, by_amount) in TIERED_GROUPS.items():
        for tier, ids in by_amount.items():
            present = [i for i in ids if i in acc]
            if not present:
                continue
            canon_id = _canonical_tier_id(slot, base_word, tier)
            # name like "ring of strength" / "ring of greater strength" /
            # "amulet of strength" (+2 base) / "amulet of greater strength" (+3)
            word = _tier_word(slot, tier)
            name = f"{slot} of {word + ' ' if word else ''}{base_word}"
            survivor_src = acc[present[0]]
            for vid in present:
                harvest(acc[vid], slot)
            survivor = dict(survivor_src)
            survivor['name'] = name
            survivor['slot'] = slot
            survivor['unidentified_name'] = NEUTRAL[slot]['name']
            survivor['color'] = list(NEUTRAL[slot]['color'])
            survivor['is_unique'] = False
            for vid in present:
                new_acc.pop(vid, None)
                if vid != canon_id:
                    remap[vid] = canon_id
            new_acc[canon_id] = survivor

    return new_acc, remap, pool


def _detect_ensure_ascii(orig_text: str, data: dict) -> bool:
    body = orig_text.rstrip('\n')
    for ea in (False, True):
        if json.dumps(data, indent=2, ensure_ascii=ea) == body:
            return ea
    raise AssertionError('cannot round-trip accessory.json (formatting mismatch)')


def main(check: bool = False):
    orig = ACC_PATH.read_text(encoding='utf-8')
    acc = json.loads(orig)
    trailing = orig[len(orig.rstrip('\n')):]
    ensure_ascii = _detect_ensure_ascii(orig, acc)

    new_acc, remap, pool = build(acc)

    removed = len(acc) - len(new_acc)
    print(f"accessory.json: {len(acc)} -> {len(new_acc)} entries ({removed} removed)")
    print(f"appearance pool: {len(pool['ring'])} ring looks, {len(pool['amulet'])} amulet looks")
    print(f"remap table: {len(remap)} deleted/renamed ids -> survivors")
    for old, new in sorted(remap.items()):
        print(f"    {old:42} -> {new}")

    if check:
        print("\n[--check] no files written.")
        return new_acc, remap, pool

    ACC_PATH.write_text(json.dumps(new_acc, indent=2, ensure_ascii=ensure_ascii) + trailing,
                        encoding='utf-8')
    # The appearance pool is harvested from the variants' looks. On an
    # already-migrated file the variants are gone, so `pool` comes back empty —
    # do NOT clobber a previously-written good pool with an empty one. The pool
    # is committed reference data generated on the FIRST (clean) run.
    if pool['ring'] and pool['amulet']:
        APPEAR_PATH.write_text(json.dumps(pool, indent=2, ensure_ascii=False) + '\n',
                               encoding='utf-8')
        print(f"\nwrote {ACC_PATH.name} and {APPEAR_PATH.name}")
    else:
        print(f"\nwrote {ACC_PATH.name} (pool empty on re-run -> "
              f"{APPEAR_PATH.name} left intact)")
    return new_acc, remap, pool


if __name__ == '__main__':
    main(check='--check' in sys.argv)
