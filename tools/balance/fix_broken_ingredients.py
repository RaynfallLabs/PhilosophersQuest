"""Generate the missing 33 ingredient.json entries for monsters whose
ingredient_id references nothing. Each new entry includes the 6-quality
single-cook recipe table that matches the existing schema (Q0 ruined,
Q1-Q2 just SP, Q3 stat-bonus, Q4 combat_stat/all_stats, Q5 the high prize).

SP per quality follows the existing pattern: roughly
  sp = quality * max(5, min_level * 0.7)

Bonus types per quality:
  Q0: none/0
  Q1-Q2: none/0 (just SP, no bonus)
  Q3: stat / 1-3 (lower min_level -> smaller amount, higher source -> larger)
  Q4: combat_stat / 1 OR all_stats / 1 (alternating for variety)
  Q5: two_stats / 2 OR all_stats / 2 (high prize)

Lore voice: geek-dad chronicle, short, grounded. Per-ingredient flavor.
"""
import json
import os


# Per-ingredient flavor data: (display_name, color RGB, weight_lb, lore_snippet,
#   sprite_desc, q3_stat, q5_stat_pair_or_all). Order: low-tier first.
INGREDIENT_FLAVOR = {
    # ----- New session monsters (27) -----
    'goblin_ear':       ('goblin ear', [120, 170, 80], 0.2,
        "Cured goblin ear, leathery and tough. Battle-trophy taken as much for sport as for stewpot — the warpriests claim chewing one preserves the taste of victory.",
        "A wrinkled green goblin ear strung on a leather thong",
        'DEX', ['DEX', 'PER']),
    'witch_finger':     ('witch finger', [80, 50, 60], 0.1,
        "The desiccated finger of a harrow-witch, still curling at the joint. Witches keep their hexes in their hands; cooking burns them out.",
        "A blackened mummified finger curled into a hook",
        'INT', ['INT', 'WIS']),
    'stone_moss':       ('stone moss', [80, 110, 70], 0.5,
        "Wet moss scraped from a moss sentinel's hide. Holds water like a sponge and tastes of cold earth.",
        "Damp grey-green moss clumped into a fist-sized mat",
        'CON', ['CON', 'WIS']),
    'serpent_venom':    ('serpent venom', [180, 60, 200], 0.1,
        "Sable serpent venom in a stoppered phial. Lethal raw; diluted in long-simmer broths it becomes nerve tonic.",
        "A small glass phial of dark purple venom with a wax-sealed stopper",
        'DEX', ['DEX', 'INT']),
    'patriarch_signet': ('patriarch signet', [180, 160, 80], 0.3,
        "The signet ring of the Iron Patriarch, pried from his slain finger. Stamped with the four-bar mark of a dead order. Crushed and powdered, it lends weight to a roast.",
        "A heavy iron signet ring stamped with four parallel bars",
        'STR', ['STR', 'CON']),
    'assassin_cowl':    ('assassin cowl', [40, 40, 50], 0.4,
        "The cowl of a mage-slayer, threaded with binding-runes that resist magic. Boiled, the threads release a tasteless oil.",
        "A dark wool hood with crimson rune-stitching along the seam",
        'DEX', ['DEX', 'PER']),
    'golem_core':       ('golem core', [120, 120, 130], 1.5,
        "The animating core stone of a slain golem — granite veined with sigils. Powdered into stew, it stiffens the diner's bones.",
        "A grey stone the size of a fist, faintly glowing along etched runic veins",
        'CON', ['STR', 'CON']),
    'plague_phylactery': ('plague phylactery', [120, 150, 80], 0.4,
        "A plague-witch's reliquary bottle holding a strand of her hair and a tooth. Properly purified, it grants immunity to what killed it.",
        "A small clay bottle sealed with green wax, sloshing faintly",
        'WIS', ['WIS', 'CON']),
    'vine_essence':     ('vine essence', [80, 150, 70], 0.3,
        "Pressed sap of the vine horror, thick and slow as molasses. Drinkers report dreams of constriction.",
        "A glass jar of viscous dark green liquid that clings to the sides",
        'CON', ['CON', 'INT']),
    'lich_dust':        ('lich dust', [200, 200, 220], 0.1,
        "Bone-dust scraped from a lich's reliquary, glittering faintly under low light. The lich's name is still half-pronounceable in it.",
        "A handful of luminous pale-grey powder in a folded parchment packet",
        'INT', ['INT', 'WIS']),
    'horror_ichor':     ('horror ichor', [60, 30, 80], 0.3,
        "The black blood of a lurking horror. Reacts with iron, hisses on contact with flame. Cooking it transmutes the malice into nourishment.",
        "A small iron vial of bubbling black liquid, the vial slightly corroded",
        'CON', ['CON', 'DEX']),
    'sentinel_plate':   ('sentinel plate', [140, 130, 110], 1.2,
        "A scale-plate from a throne sentinel's barding. Folded steel from a vanished smithing tradition; flakes into the pot like seasoning.",
        "A rectangular bronze scale-plate as long as a hand, with a holed corner",
        'STR', ['STR', 'WIS']),
    'crone_voice':      ('crone voice', [200, 100, 220], 0.0,
        "Captured in a stoppered conch — the death-whisper of the Whispering Crone. When uncapped over a simmering pot, the broth begins to mutter.",
        "A small pink conch sealed with black wax, faintly vibrating",
        'WIS', ['WIS', 'INT']),
    'demon_horn':       ('demon horn', [180, 60, 60], 0.6,
        "Spiral horn of a demonic trickster, hollow and resonant. Shavings flake easily and lend a peppery heat.",
        "A curved black-red horn the length of a forearm, hollow at the base",
        'STR', ['STR', 'DEX']),
    'deep_pearl':       ('deep pearl', [180, 200, 220], 0.3,
        "Pearl of a deep-one priest, secreted around grit from the abyssal floor. Crushed, it tastes of salt and old prayers.",
        "A blue-white pearl the size of a thumbnail, faintly luminescent",
        'WIS', ['WIS', 'INT']),
    'mimic_gold':       ('mimic gold', [220, 200, 80], 0.5,
        "Solidified saliva from a mimic, indistinguishable from coin gold until you bite it. Melts in low heat and recrystallizes around food.",
        "A bright gold coin with faint tooth-marks around the edge",
        'PER', ['PER', 'DEX']),
    'rime_tusk':        ('rime tusk', [200, 220, 240], 1.0,
        "Frost-permeated tusk of a frostfang giant. Never warms above ice-cold; shaving it onto a hot dish doesn't melt the shavings.",
        "A pale blue curved tusk as long as a forearm, faintly smoking with cold",
        'CON', ['CON', 'STR']),
    'necromantic_focus': ('necromantic focus', [80, 40, 100], 0.4,
        "The focus-bone of a crypt summoner — a finger-bone carved with a binding glyph. Boiled in a broth, the glyph dissolves and the broth steadies the cook's hand.",
        "A bone finger inscribed with a single dark-purple sigil",
        'WIS', ['INT', 'WIS']),
    'shadow_quiver':    ('shadow quiver', [40, 40, 60], 0.7,
        "A shadow archer's quiver, woven from solidified umbra. Holds nothing, weighs almost nothing, drinks light.",
        "A long dark cloth tube as light as paper, edges blurring against the eye",
        'DEX', ['DEX', 'PER']),
    'inquisitor_seal':  ('inquisitor seal', [180, 30, 30], 0.3,
        "A veiled inquisitor's torture-seal: a brass coin stamped with the hierarch's name. Carrying it makes a meal feel deserved.",
        "A red-brown brass disk with a stylized eye in the center",
        'WIS', ['WIS', 'PER']),
    'elemental_core':   ('elemental core', [220, 90, 40], 1.0,
        "The molten heart-stone of a lava elemental, kept burning by its own residual will. Wraps food in a lasting heat-aura.",
        "A glowing red-orange stone in a thick iron cage to prevent burns",
        'STR', ['STR', 'CON']),
    'archon_heart':     ('archon heart', [180, 40, 40], 1.5,
        "Heart of a blood archon, still warm hours after the kill. Cooked over slow heat, it renders down to a thick crimson stock.",
        "A massive dark red heart in a sealed clay vessel, still slowly beating",
        'STR', ['STR', 'CON']),
    'astral_filament':  ('astral filament', [200, 220, 240], 0.1,
        "Single strand of astral plane material, harvested from a slain astral horror. Visible only at certain angles; tastes like memory.",
        "A nearly-invisible thread coiled on a small black silk square",
        'INT', ['INT', 'WIS']),
    'kobold_scale':     ('kobold scale', [120, 80, 60], 0.2,
        "Hardened scale from a kobold dragonshield's hide. Boiled in vinegar, it makes a tangy chip that hardens the cook's stomach.",
        "A small reddish-brown scale the size of a coin, rough on one side",
        'CON', ['CON', 'DEX']),
    'gnoll_pelt':       ('gnoll pelt', [180, 140, 80], 1.0,
        "Coarse pelt of a gnoll alpha, smelling of carrion and laughter. Rendered down, the fat is surprisingly mild.",
        "A patch of mottled yellow-brown fur with darker spots, leather-backed",
        'STR', ['STR', 'PER']),
    'cobra_fang':       ('cobra fang', [220, 200, 180], 0.1,
        "Hollow fang of a charmed cobra, dripping with diluted venom. Properly handled, the venom becomes a quickening tonic.",
        "A pale curved fang with a hollow drip-channel, sealed in beeswax",
        'DEX', ['DEX', 'INT']),
    'venom_diadem':     ('venom diadem', [120, 60, 180], 0.4,
        "Headpiece worn by a viper priestess, set with desiccated serpent eyes. The serpents are still watching.",
        "A silver circlet inset with three small green-glass spheres",
        'WIS', ['WIS', 'PER']),

    # ----- Pre-existing broken refs (6) -----
    'swarmlord_chitin':     ('swarmlord chitin', [180, 160, 60], 0.6,
        "Chitin plate from a locust swarmlord, hollow and resonant. Hums faintly at certain frequencies; crushed, it crackles in the pan.",
        "A curved yellow-brown chitin shield the size of a saucer",
        'CON', ['CON', 'WIS']),
    'executioners_iron':    ("executioner's iron", [70, 70, 80], 1.4,
        "A small iron weight from the pit executioner's harness, ritually heavy. Filings dropped into a soup settle to the bottom and stay warm.",
        "A small black iron weight stamped with a single rune",
        'STR', ['STR', 'CON']),
    'void_feather':         ('void feather', [40, 0, 80], 0.05,
        "A flight feather from a void seraph — black at the quill, fading into nothing at the tip. Tastes of absence.",
        "A long black feather that seems to dissolve at the tip",
        'WIS', ['WIS', 'INT']),
    'herald_trumpet_brass': ('herald trumpet brass', [220, 180, 60], 0.5,
        "A fragment of the apocalypse herald's trumpet, still vibrating faintly. The vibration carries through metal and into the food.",
        "A curved sliver of yellow-gold brass with engraved scales of the apocalypse",
        'WIS', ['WIS', 'CON']),
    'wormwood_ash':         ('wormwood ash', [120, 100, 80], 0.2,
        "Bitter ash from a wormwood blight, the foundation of absinthe. Used sparingly.",
        "A folded paper packet of fine grey-green powder smelling of bitter herbs",
        'INT', ['INT', 'WIS']),
    'horseman_lance_shard': ('horseman lance shard', [180, 100, 60], 0.8,
        "A fragment of the iron horseman's lance — cold to the touch, faintly oily. Heats slowly even in the brightest flame.",
        "A jagged iron splinter as long as a hand, edges dark with old blood",
        'STR', ['STR', 'CON']),
}


def quality_recipes(name: str, min_level: int, q3_stat: str, q5_pair: list) -> dict:
    """Generate the standard Q0-Q5 single-cook recipe table for an ingredient.
    SP scales as quality * max(5, min_level * 0.7); bonus types follow the
    house pattern (Q3 stat, Q4 all_stats, Q5 two_stats high prize)."""
    sp_step = max(5, int(round(min_level * 0.7)))
    return {
        '0': {'name': f'ruined {name}', 'sp': 0,
              'bonus_type': 'none', 'bonus_amount': 0},
        '1': {'name': f'{name} broth', 'sp': sp_step,
              'bonus_type': 'none', 'bonus_amount': 0},
        '2': {'name': f'decent {name} stew', 'sp': sp_step * 2,
              'bonus_type': 'none', 'bonus_amount': 0},
        '3': {'name': f'good {name} roast', 'sp': sp_step * 3,
              'bonus_type': 'stat', 'bonus_amount': 1 if min_level < 30 else 2,
              'bonus_stat': q3_stat},
        '4': {'name': f'great {name} feast', 'sp': sp_step * 4,
              'bonus_type': 'all_stats', 'bonus_amount': 1},
        '5': {'name': f"masterwork {name} cuisine", 'sp': sp_step * 5,
              'bonus_type': 'two_stats', 'bonus_amount': 2,
              'bonus_stats': q5_pair},
    }


def main():
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    monsters_p = os.path.join(repo, 'data', 'monsters.json')
    ings_p = os.path.join(repo, 'data', 'items', 'ingredient.json')

    with open(monsters_p, encoding='utf-8') as f:
        monsters = json.load(f)
    with open(ings_p, encoding='utf-8') as f:
        ings = json.load(f)

    # Find all broken ingredient_ids and their source monster
    broken = {}
    for mid, mv in monsters.items():
        iid = mv.get('ingredient_id')
        if iid and iid not in ings:
            broken.setdefault(iid, []).append((mid, mv))

    print(f"Broken ingredient_ids: {len(broken)}")
    added = 0
    skipped = []
    for iid, sources in sorted(broken.items()):
        if iid not in INGREDIENT_FLAVOR:
            skipped.append(iid)
            continue
        # Use the LOWEST-min_level source monster as canonical source
        sources.sort(key=lambda x: x[1].get('min_level', 0))
        source_id, source_def = sources[0]
        min_level = int(source_def.get('min_level', 1))
        name, color, weight, lore, sprite_desc, q3_stat, q5_pair = INGREDIENT_FLAVOR[iid]
        ings[iid] = {
            'name': name,
            'symbol': ',',
            'color': color,
            'weight': weight,
            'min_level': min_level,
            'source_monster': source_id,
            'recipes': quality_recipes(name, min_level, q3_stat, q5_pair),
            'sprite_desc': sprite_desc,
            'lore': lore,
        }
        added += 1

    with open(ings_p, 'w', encoding='utf-8') as f:
        json.dump(ings, f, indent=2, ensure_ascii=False)
    print(f"Added {added} ingredients. Skipped (no flavor data): {len(skipped)}")
    for s in skipped:
        print(f"  SKIPPED: {s}")


if __name__ == '__main__':
    main()
