"""The monster-effects pass (Brandon, 2026-11-22: "All as recommended" on
MONSTER_EFFECTS_AUDIT_2026_11_22.md). The record of the data it changed.

Every kind is named here with the reason its lore gives. Nothing is picked
by a floor and nothing is multiplied (LORE, NOT FLOOR).

    py tools/content/effects_pass_2026_11_22.py          write
    py tools/content/effects_pass_2026_11_22.py --check  fail on drift

It is idempotent: it writes the values below, whatever was there.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
import jsonfmt  # noqa: E402

# (kind, attack): what the attack lays now.
RIDERS = {
    # -- Paralysis given back to lore (audit section 7): eight kinds.
    ('mimic', 'Bite'): dict(effect='immobilized', effect_duration=3),          # stuck to it
    ('barrow_wight', 'Entangle'): dict(effect='immobilized', effect_duration=3),
    ('tomb_guardian', 'Bind'): dict(effect='immobilized', effect_duration=3),
    ('banshee', 'Death Wail'): dict(effect='feared', effect_duration=3),       # her wail is dread
    ('nosferatu', 'Drain'): dict(effect='weakened', effect_duration=6),        # the blood he took
    ('eloko', 'Bell Charm'): dict(effect='charmed', effect_duration=3),        # the bell calls you to it
    # A young or lesser stone-maker stiffens and lets go: never death.
    ('cockatrice', 'Beak'): dict(effect='petrifying', effect_duration=4, lethal=False),
    ('cockatrice', 'Petrifying Touch'): dict(effect='petrifying', effect_duration=4, lethal=False),
    ('basilisk_lesser', 'Petrifying Gaze'): dict(effect='petrifying', effect_duration=4, lethal=False),

    # -- The stone of the true basilisks and gorgons ends in stone: ten
    #    turns to find the cure (Oil of Rue, guaranteed at the stalls).
    ('basilisk', 'Stony Gaze'): dict(effect='petrifying', effect_duration=10, lethal=True),
    ('elder_basilisk', 'Petrifying Bite'): dict(effect='petrifying', effect_duration=10, lethal=True),
    ('medusa', 'Stony Gaze'): dict(effect='petrifying', effect_duration=10, lethal=True),
    ('gorgon_warrior', 'Petrifying Breath'): dict(effect='petrifying', effect_duration=10, lethal=True),

    # -- What is named a charm is one.
    ('vampire_thrall', 'Mesmerize'): dict(effect='charmed'),
    ('satyr_trickster', 'Panpipe Charm'): dict(effect='charmed'),
    ('harpy', 'Charm Song'): dict(effect='charmed'),
    ('succubus_shade', 'Entrancing Gaze'): dict(effect='charmed'),
    ('incubus', 'Charm Gaze'): dict(effect='charmed'),
    ('erlking', 'Lure'): dict(effect='charmed'),
    ('vampire_spawn', 'Charm Gaze'): dict(effect='charmed'),
    ('vampire', 'Charm'): dict(effect='charmed'),
    ('dryad_guardian', 'Charm Gaze'): dict(effect='charmed'),
    ('vampire_lord', 'Charm Gaze'): dict(effect='charmed'),
    ('elder_beholder', 'Charm Ray'): dict(effect='charmed'),
    ('kyubi_kitsune', 'Bewitching Gaze'): dict(effect='charmed'),

    # -- The eaters of minds eat a memory (Forget).
    ('intellect_devourer', 'Devour Intellect'): dict(effect='forgetting', effect_chance=0.4, effect_duration=6),
    ('mind_flayer_thrall', 'Mind Drain'): dict(effect='forgetting', effect_chance=0.35, effect_duration=6),
    ('mind_flayer', 'Tentacle'): dict(effect='forgetting', effect_chance=0.35, effect_duration=6),
    ('elder_mind_flayer', 'Brain Extraction'): dict(effect='forgetting', effect_chance=0.4, effect_duration=6),
    ('astral_horror', 'Mind Drain'): dict(effect='forgetting', effect_duration=6),

    # -- The Likho's bad luck is a fumble, six turns of it.
    ('likho', 'Baleful Gaze'): dict(effect='fumbling', effect_duration=6),
    ('likho', 'Leaping Grab'): dict(effect='fumbling', effect_duration=6),
}

# Slowed now gives the world two turns for every action, by any key, so the
# creatures of the upper dungeon slow for less (audit section 4). Two turns:
# a knock, a bite or a shot that staggers. Three: what clings or numbs (a
# web, glue, mire, grave-cold).
SLOW_TWO = {
    'giant_frog': 'Tongue Lash', 'stirge_swarm': 'Bloodsuck', 'gravehound': 'Bite',
    'skeleton_warrior': 'Shield Bash', 'charnel_hound': 'Bone Crunch',
    'gnoll_archer': 'Yew Longbow', 'bugbear': 'Club Smash', 'animated_armor': 'Shield Bash',
    'roc_chick': 'Talon Grip', 'hobgoblin_captain': 'Shield Bash',
    'mercenary_veteran': 'Shield Bash', 'calydonian_boar': 'Trampling Charge',
    'dire_bear': 'Maul', 'minotaur_warrior': 'Gore', 'lindworm': 'Tail Sweep',
    'bone_archer': 'Cursed Shot', 'battle_mage': 'Frost Bolt', 'soul_shadow': 'Soul Siphon',
    'grave_guardian': 'Ward', 'mud_crawler': 'Claw',
}
SLOW_THREE = {
    'brown_mold': 'Cold Drain', 'web_spinner': 'Web Shot', 'crystal_ooze': 'Engulf',
    'yellow_musk_creeper': 'Tendril Lash', 'kuo_toa': 'Sticky Shield',
    'mimic': 'Adhesive Slam', 'duat_shade': 'Shadow Touch', 'arachne': 'Web',
    'giant_spider': 'Web Spray', 'desert_wraith': 'Dehydration', 'ettercap': 'Web',
    'ice_elemental': 'Freezing Touch', 'wraith': 'Draining Touch', 'specter': 'Draining Touch',
    # ...and the four that begin on floors 18-19 (grave-cold, a hag's mire,
    # the spriggan's weight, the Minch's water).
    'wight': 'Draining Touch',
    'green_hag': 'Weakening Curse',
    'spriggan': 'Wither Curse',
    'blue_men_of_the_minch': 'Squall Spray',
}


# Slowed is four turns at most now (audit section 4: it takes every action,
# by any key). These named more; each says the four it lays.
SLOWED_FOUR = [
    ('frost_crawler', 'Chill Aura'),
    ('vampire_spawn', 'Bite'),
    ('vampire', 'Bite'),
    ('beholder', 'Slow Ray'),
    ('ancient_dragon', 'Tail Strike'),
    ('death_lord', 'Death Gaze'),
    ('empusa', 'Blood Drain'),
    ('cyclops', 'Crush'),
    ('scylla', 'Dog-Head Bite'),
    ('charybdis_spawn', 'Whirlpool Drag'),
    ('valkyrie_shade', 'Soul Mark'),
    ('fenrir_pup', 'Savage Bite'),
    ('draugr', 'Curse Touch'),
    ('sluagh', 'Swarming Descent'),
    ('kusarikku', 'Chaos Stomp'),
    ('aboleth_lesser', 'Tentacles'),
    ('chain_devil_spawn', 'Chain Lash'),
    ('pit_fiend_spawn', 'Tail Crush'),
    ('stone_golem_lesser', 'Slow Aura'),
    ('clay_golem', 'Slam'),
    ('roper', 'Strands'),
    ('behir_lesser', 'Constrict'),
    ('necromancer_lord', 'Withering Grasp'),
    ('ossuary_horror', 'Absorb'),
    ('undead_dragon_lesser', 'Necrotic Breath'),
    ('spider_queen', 'Web Spray'),
    ('death_beetle', 'Death Rattle'),
    ('roc_adult', 'Talon Crush'),
    ('annis_hag', 'Crushing Claw'),
    ('shambling_mound', 'Slam'),
    ('shambling_mound', 'Engulf'),
    ('sea_dragon_spawn', 'Tail Slam'),
    ('cloud_giant', 'Gale Strike'),
    ('storm_giant', 'Thunderstrike'),
    ('elder_werewolf', 'Bite'),
    ('elder_beholder', 'Slow Ray'),
    ('lich_sovereign', 'Soul Frost'),
    ('world_serpent', 'Venomous Bite'),
    ('dread_knight_legion', 'Death Aura'),
    ('frostfang_giant', 'Frost Breath'),
    ('hels_handmaid', "Slow-Walker's Touch"),
    ('vila', 'Whirlwind'),
    ('star_jelly', 'Starlight Touch'),
    ('yacumama', 'Drawing Breath'),
]

# Weakened is eight turns at most now (audit section 4: a Constitution save,
# a cap of eight, no stacking). These named more; each says the eight it lays.
WEAKENED_EIGHT = [
    ('gelatinous_cube', 'Dissolve'),
    ('abyssal_mimic', 'Soul Drain'),
    ('acid_blob', 'Engulf'),
    ('shadow', 'Shadow Touch'),
    ('specter', 'Wail'),
    ('lich_apprentice', 'Curse Bolt'),
    ('death_knight', 'Accursed Blade'),
    ('death_lord', 'Soul Rend'),
    ('soul_eater', 'Soul Drain'),
    ('orc_shaman', 'Hex Bolt'),
    ('ammit_spawn', 'Devour Soul'),
    ('succubus_shade', 'Soul Kiss'),
    ('death_mage', 'Wither'),
    ('bone_witch', 'Curse Bolt'),
    ('greater_shadow', 'Strength Drain'),
    ('shadow_master', 'Shadow Claw'),
    ('abyssal_overlord', 'Soul Crush'),
    ('corrosive_ooze', 'Dissolve'),
    ('dracolich', 'Death Breath'),
    ('arch_lich', 'Soul Rend'),
    ('elder_dracolich', 'Void Breath'),
    ('void_wyrm', 'Void Bite'),
    ('entropy_elemental', 'Entropy Touch'),
    ('orc_priest', 'Blood Prayer'),
    ('skeleton_necromancer', 'Withering Touch'),
    ('skeleton_lich', 'Lich Claw'),
    ('cult_initiate', 'Chanted Hex'),
    ('cult_priest', 'Litany of Pain'),
    ('cult_zealot', 'Two-Handed Cleaver'),
    ('draugr_wight', 'Draining Touch'),
    ('demonic_imp', 'Soul-Pinch'),
    ('harrow_witch', 'Hex Bolt'),
    ('gilded_mimic', 'Gold-Strangling Tongue'),
    ('crypt_summoner', 'Grave Hex'),
    ('astral_horror', 'Psychic Lash'),
    ('ammit_devourer', 'Weighing of the Heart'),
    ('lyssa_madness', 'Rabid Bite'),
    ('preta', 'Needle-Throat Wail'),
    ('tsuchigumo', 'Fever Curse'),
]


# A gore, a tusk or an antler is a thrust, not a trample (3.6.1 balance run,
# 2026-11-22: Asterion's Gore floored the hero as his Trample does, and the
# floor-20 gate got harder). Still a trample for the boots' guard.
THRUSTS = [
    ('asterion_minotaur', 'Gore'), ('minotaur', 'Gore'), ('minotaur_warrior', 'Gore'),
    ('chimera', 'Goat Gore'), ('chimera_alpha', 'Goat Gore'), ('kusarikku', 'Bull Gore'),
    ('unicorn_corrupted', 'Dark Horn Gore'), ('peryton', 'Antler Gore'), ('hell_bovine', 'Gore'),
    ('calydonian_boar', 'Tusk Gore'), ('khalkotauros', 'Bronze Gore'),
]


def monsters_pass(data: dict) -> None:
    for kind, name in THRUSTS:
        hits = [a for a in data[kind]['attacks'] if a['name'] == name]
        if len(hits) != 1 or hits[0].get('delivery') != 'trample':
            raise SystemExit(f'{kind}: no trample named {name!r}')
        hits[0]['floors'] = False
    wanted = {k: dict(v) for k, v in RIDERS.items()}
    for turns, table in ((2, SLOW_TWO), (3, SLOW_THREE)):
        for kind, name in table.items():
            wanted[(kind, name)] = dict(effect_duration=turns)
    for turns, table in ((4, SLOWED_FOUR), (8, WEAKENED_EIGHT)):
        for pair in table:
            wanted[pair] = dict(effect_duration=turns)
    for (kind, name), fields in wanted.items():
        hits = [a for a in data[kind]['attacks'] if a['name'] == name]
        if len(hits) != 1:
            raise SystemExit(f'{kind}: {len(hits)} attacks named {name!r}')
        atk = hits[0]
        if fields.get('lethal') is False:
            fields.pop('lethal')
            atk.pop('lethal', None)
        atk.update(fields)


def chest_rows(text: str) -> str:
    """Both chest hexes are hexes: what he wears will not come off. The
    gorgon carved on a lid is a gorgon: her stone killed before this pass
    and still does, on a gorgon's count of ten (it was five). The file is
    hand-aligned, a row a trap, so its text is edited, not re-dumped."""
    import re
    text = re.sub(r'("type": "hex(?:_heavy)?",[^\n]*"effect": )"cursed"', r'\1"hexed"', text)
    return re.sub(r'("type": "petrify",[^\n]*"effect": "petrifying",) *"effect_duration": *\d+,'
                  r'(?: *"lethal": *true,)?',
                  r'\1"effect_duration": 10, "lethal": true,', text)


def guards_pass(data: dict) -> None:
    """The pieces that guarded against what these attacks used to lay guard
    against what they lay now."""
    add = {'head': ['charmed', 'forgetting'], 'hands': ['petrifying'], 'feet': ['knocked_down']}
    fams = data['families']
    for slot, riders in add.items():
        for r in riders:
            if r not in fams[slot]['riders_any']:
                fams[slot]['riders_any'].append(r)
    fams['head']['stops'] = 'fear, confusion, charm, forgetting, sleep, stunning and blindness'
    fams['hands']['stops'] = 'paralysis, stone and being held'
    fams['feet']['stops'] = 'slowing, holds, freezing, falls and being knocked senseless'


# A family technique keeps off what its creatures lay now, where it kept
# off what they used to lay: (technique, riders added, its words).
FAMILY_WARDS = {
    'aberrations_steel_mind': (['immobilized', 'forgetting', 'charmed'],
        "You get +1 on saving throws against their confusion, charm, paralysis, holding and mind-eating, "
        "and their hallucinations last a tenth less time."),
    'birds_hooded': (['charmed'],
        "You get +1 on saving throws against their blinding, confusion and charm, "
        "as a falconer's hood calms a hawk."),
    'demons_circle_of_salt': (['charmed'],
        "You get +1 on saving throws against their burning, confusion and charm, "
        "and their burning lasts a tenth less time."),
    'restless_dead_grave_salt': (['immobilized'],
        "You get +1 on saving throws against their paralysis, holding, disease and life drain, "
        "and their disease lasts a tenth less time."),
    'vampires_liches_garlic_and_ash': (['weakened'],
        "You get +1 on saving throws against their life drain, paralysis and weakness, "
        "and their bite no longer heals them."),
    'circle_unbent_mind': (['forgetting'],
        "You get +1 on every saving throw against confusion, charm, fear and mind-eating, from anything."),
}


def families_pass(data: dict) -> None:
    done = set()

    def walk(o, owner=''):
        if isinstance(o, dict):
            owner = o.get('id', owner)
            if owner in FAMILY_WARDS and o.get('effect') == 'save_bonus' and isinstance(
                    (o.get('params') or {}).get('effects'), list):
                add, words = FAMILY_WARDS[owner]
                for r in add:
                    if r not in o['params']['effects']:
                        o['params']['effects'].append(r)
                for key in ('text', 'desc', 'does'):
                    if key in o:
                        o[key] = words
                        break
                done.add(owner)
            for v in o.values():
                walk(v, owner)
        elif isinstance(o, list):
            for v in o:
                walk(v, owner)
    walk(data)
    if done != set(FAMILY_WARDS):
        raise SystemExit(f'family techniques not found: {sorted(set(FAMILY_WARDS) - done)}')


def wards_pass(data: dict) -> None:
    add = {'ward_psylli': ['petrifying'], 'ward_udug_hul': ['charmed', 'hexed']}
    for wid, riders in add.items():
        have = data['family_wards'][wid]['riders']
        for r in riders:
            if r not in have:
                have.append(r)


PASSES = {
    'data/monsters.json': monsters_pass,
    'data/monster_families.json': families_pass,
    'data/wards.json': wards_pass,
    'data/armor_guards.json': guards_pass,
}
TEXT_PASSES = {
    'data/chest_traps.json': chest_rows,
}


def run(check: bool = False) -> list:
    drift = []
    for rel, fn in PASSES.items():
        path = os.path.join(ROOT, *rel.split('/'))
        data, fmt = jsonfmt.load(path)
        import copy
        before = copy.deepcopy(data)
        fn(data)
        if data == before:
            continue
        drift.append(rel)
        if not check:
            jsonfmt.save(path, data, fmt)
    for rel, fn in TEXT_PASSES.items():
        path = os.path.join(ROOT, *rel.split('/'))
        with open(path, 'rb') as f:
            text = f.read().decode('utf-8')
        new = fn(text)
        if new != text:
            drift.append(rel)
            if not check:
                with open(path, 'wb') as f:
                    f.write(new.encode('utf-8'))
    return drift


if __name__ == '__main__':
    _check = '--check' in sys.argv
    _got = run(_check)
    print(('drifted: ' if _check else 'wrote: ') + (', '.join(_got) or 'nothing'))
    sys.exit(1 if _check and _got else 0)
