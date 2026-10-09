"""
The October 2026 unique-armor pass: named pieces for the slots that
had almost none (hands, shirt, arms, early and late cloaks, deep legs), and
a named drop for the three legends that had none (Surtur, Ymir's Last Spawn,
Hrungnir's Ghost) and the six mini-bosses that had lost theirs.

Offline tooling (not loaded at runtime). Idempotent.

    python tools/content/add_unique_armor_2026_10.py            # report
    python tools/content/add_unique_armor_2026_10.py --write    # write data (icons: tools/content/art/build.py)

LORE, NOT FLOOR: each piece is what its story says it is, and sits on the
floor where that much armor belongs. Its numbers are fixed here and nothing
scales them in play. Every effect used is one the game already reads:
resistances, `dodge_bonus`, `toughness_bonus`, `quiz_timer_bonus`,
`chain_bonus`, and the three cloak rules that were written and tested but
carried by no item (`story_thread`, `webbed_strike`, `forest_hearing`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

# band: tier, quiz_tier, equip_threshold, max_enchant, peak_weight, spread
BANDS = {
    1: dict(tier=1, quiz_tier=1, equip_threshold=2, max_enchant=2, peak_weight=0.5,  spread=10),
    2: dict(tier=2, quiz_tier=2, equip_threshold=3, max_enchant=2, peak_weight=0.45, spread=10),
    3: dict(tier=3, quiz_tier=3, equip_threshold=3, max_enchant=2, peak_weight=0.4,  spread=10),
    4: dict(tier=4, quiz_tier=4, equip_threshold=4, max_enchant=2, peak_weight=0.35, spread=12),
    5: dict(tier=5, quiz_tier=5, equip_threshold=4, max_enchant=3, peak_weight=0.35, spread=10),
}


def piece(name, slot, band, peak, min_level, ac, value, weight, material, template,
          color, unidentified, lore, resist=None, drop_only=False, **extra):
    d = {
        'name': name, 'symbol': '[', 'color': color, 'weight': weight,
        'min_level': min_level, 'slot': slot, 'material': material,
        'ac_bonus': ac, 'enchant_bonus': 0,
        'damage_resistances': resist or {},
        'can_be_cursed': False, 'cursed': False, 'identified': False,
        'unidentified_name': unidentified, 'floorSpawnWeight': {},
        'value': value, 'lore': lore, 'peak_floor': peak,
        'template_basis': template, 'is_unique': True,
        'containerLootTier': 'rare', 'container_loot_tier': 'rare',
    }
    d.update(BANDS[band])
    if drop_only:
        d['peak_weight'] = 0.0          # only its monster carries it
    d.update(extra)
    return d


ARMOR = {
    # ------------------------------------------------------------ hands
    'cestus_of_polydeuces': piece(
        'Cestus of Polydeuces', 'hands', 1, 9, 5, 1, 900, 1.0, 'leather', 'leather_gloves',
        [150, 100, 60], 'a pair of ox-hide straps wound for the knuckles',
        "Polydeuces sailed with Jason on the Argo, and he was the best boxer among the Greeks. "
        "When the ship put in among the Bebryces, their king Amycus would let no stranger leave "
        "without boxing him, and no stranger had ever won. Polydeuces wound ox-hide straps around "
        "his fists, let the bigger man tire himself, and dropped him with one blow above the ear. "
        "A boxer's first lesson is how to take a punch.",
        resist={'blunt': 0.85}, toughness_bonus=0.03),
    'gloves_of_wayland': piece(
        "Wayland's Forge Gloves", 'hands', 2, 26, 17, 2, 3400, 1.0, 'leather', 'leather_gloves',
        [95, 75, 60], 'a pair of scorched leather gloves that smell of charcoal',
        "Wayland was the finest smith in the northern stories. King Nidud wanted his work and "
        "feared his freedom, so he cut the tendons behind Wayland's knees and set him on an "
        "island to forge. Wayland could not walk away. He made a pair of wings instead, one "
        "feather at a time, and flew. Hands that worked that carefully under guard do not shake "
        "when the clock is running.",
        resist={'fire': 0.8}, quiz_timer_bonus=1),
    'glove_of_tyr': piece(
        'Glove of Tyr', 'hands', 4, 64, 55, 3, 7800, 1.5, 'legendary', 'plate_gauntlets',
        [120, 130, 150], 'a single left-hand war glove; there was never a right',
        "When the gods bound the wolf Fenrir, the wolf would not let the ribbon Gleipnir near him "
        "unless one of them laid a hand between his jaws as a pledge of good faith. Every god "
        "knew the pledge was false. Only Tyr stepped forward. The ribbon held, the wolf bit, and "
        "Tyr was one-handed ever after. He is the god men swore oaths by. This is the glove from "
        "the hand he kept.",
        resist={'pierce': 0.8}, toughness_bonus=0.06),
    'jarngreipr_gauntlets': piece(
        'Jarngreipr', 'hands', 5, 82, 72, 4, 9600, 3.0, 'legendary', 'plate_gauntlets',
        [110, 110, 125], 'a pair of iron gauntlets too heavy for their size',
        "Snorri lists three treasures of Thor: the hammer Mjolnir, the belt that doubles his "
        "strength, and the iron gloves called Jarngreipr, the iron grippers. The dwarves forged "
        "the hammer with its handle too short, because Loki, in the shape of a fly, bit the "
        "dwarf working the bellows. Thor cannot swing it without the gloves. With them on, a grip "
        "does not slip and a blow carries a little further than it should.",
        resist={'lightning': 0.6}, chain_bonus=1),

    # ------------------------------------------------------------ arms
    'bracers_of_atalanta': piece(
        'Bracers of Atalanta', 'arms', 1, 10, 5, 1, 1000, 0.5, 'leather', 'leather_bracers',
        [170, 140, 90], 'a pair of light leather bracers scuffed by brambles',
        "Atalanta's father wanted a son and left her on a hillside. A she-bear nursed her and "
        "hunters raised her. She drew first blood from the Calydonian Boar when a band of heroes "
        "could not, and she promised to marry only a man who could outrun her. Many tried. One "
        "won, by rolling three golden apples across her path. Nothing in the hunt could lay a "
        "hand on her.",
        dodge_bonus=0.04),
    'vambraces_of_roland': piece(
        'Vambraces of Roland', 'arms', 3, 50, 40, 3, 6000, 2.0, 'legendary', 'steel_vambraces',
        [180, 180, 195], 'a pair of dented steel arm-guards with a Frankish cross',
        "In 778 Charlemagne's army marched home from Spain through the pass of Roncevaux, and "
        "Roland commanded the rear guard. The Song of Roland says his friend Oliver begged him "
        "three times to sound the horn and call the king back, and three times Roland refused "
        "out of pride. He blew it at last, so hard his temples burst, when there was no one "
        "left to save. The rear guard held the pass until the last man. These arms did not drop.",
        resist={'slash': 0.85}, toughness_bonus=0.05),
    'vambraces_of_the_first_winter': piece(
        'Vambraces of the First Winter', 'arms', 5, 85, 80, 5, 11500, 3.0, 'legendary', 'plate_vambraces',
        [170, 210, 235], 'a pair of arm-guards of blue ice that does not melt',
        "Before there was earth or sky there was a gap, with fire to the south and ice to the "
        "north. Where they met, the ice dripped, and the drops became the giant Ymir. Odin and "
        "his brothers killed him and built the world from his body. The thing that carried "
        "these says it is older than that killing. The ice in them is from the first morning, "
        "and no cold since has been able to teach it anything.",
        resist={'cold': 0.3}, toughness_bonus=0.05, drop_only=True),

    # ------------------------------------------------------------ shirt
    'hair_shirt_of_becket': piece(
        "Becket's Hair Shirt", 'shirt', 1, 12, 5, 1, 1000, 1.0, 'cloth', 'padded_shirt',
        [125, 105, 85], 'a rough undershirt of goat hair',
        "Thomas Becket was the king's friend and chancellor, fond of fine clothes and good "
        "food. Henry II made him Archbishop of Canterbury expecting an ally, and Becket took "
        "the Church's side instead. On 29 December 1170 four of the king's knights cut him "
        "down in his own cathedral. When the monks undressed the body they found a shirt of "
        "coarse hair under the robes, worn against the skin where no one could see it.",
        toughness_bonus=0.04),
    'shirt_of_aslaug': piece(
        "Aslaug's Shirt", 'shirt', 3, 60, 50, 4, 7200, 1.0, 'legendary', 'padded_shirt',
        [150, 150, 165], 'a grey shirt woven without a single seam showing',
        "Aslaug was the daughter of Sigurd the dragon-slayer and the wife of Ragnar Lodbrok. "
        "When Ragnar sailed for England against her advice, she gave him a shirt she had woven "
        "herself and told him no blade would bite him in it. King Aella's men could not wound "
        "him. They threw him into a pit of snakes, and the snakes would not touch him either, "
        "until Aella had the shirt pulled off.",
        resist={'slash': 0.8, 'pierce': 0.8, 'poison': 0.7}),
    'seamless_tunic': piece(
        'The Seamless Tunic', 'shirt', 4, 76, 66, 4, 9000, 0.5, 'legendary', 'padded_shirt',
        [225, 215, 195], 'a plain tunic woven in one piece from the top down',
        "John's gospel says the soldiers at the cross divided the clothes of Jesus into four "
        "shares, one each. The tunic was left over. It had no seam: it was woven in one piece "
        "from the top down. They looked at it and said, let us not tear it, and they threw "
        "dice for it instead. Four hard men with a day's killing behind them agreed that this "
        "one thing should stay whole.",
        resist={'magic': 0.8}, toughness_bonus=0.05),

    # ------------------------------------------------------------ cloak
    'half_cloak_of_martin': piece(
        "Martin's Half Cloak", 'cloak', 1, 8, 5, 1, 800, 1.0, 'cloth', 'cloak',
        [175, 45, 45], "half of a red soldier's cloak, cut clean with a blade",
        "Martin was a young Roman cavalryman at Amiens. One winter day he met a beggar at the "
        "city gate with almost nothing on. Martin had no money left, so he drew his sword, cut "
        "his army cloak in two, and gave the man half. The Frankish kings later kept the other "
        "half as their holiest relic. Its Latin name was cappa, its keepers were the cappellani, "
        "and the room it hung in was the cappella: chaplains and chapels are named for it.",
        resist={'cold': 0.8}, toughness_bonus=0.03),
    'anansi_web_cloak': piece(
        "Anansi's Web Cloak", 'cloak', 5, 92, 80, 4, 12500, 0.5, 'legendary', 'cloak',
        [220, 180, 40], 'a cloak of gold thread stitched all over with a pattern of spider web',
        "The Akan people of West Africa say that once every story belonged to Nyame, the sky "
        "god, and that Anansi the spider asked to buy them. Nyame named a price no one could "
        "pay: the hornets, the python and the leopard, alive. Anansi was small and weak, so he "
        "tricked each one into tying itself up. Since then all stories are spider stories, and "
        "the one who tells the story decides how it ends.",
        resist={'poison': 0.5}, story_thread=True, drop_only=True,
        special="Once a floor, a blow that would take a quarter of your health leaves only a scratch."),
    'arachne_silk_cloak': piece(
        "Arachne's Silk Cloak", 'cloak', 1, 9, 5, 2, 1800, 0.5, 'silk', 'cloak',
        [220, 220, 235], 'a pale cloak of silk too fine to have been spun by hand',
        "Arachne of Lydia wove so well that the nymphs left their rivers to watch, and she said "
        "aloud that not even Athena could teach her anything. Athena came and they wove side by "
        "side. Ovid says the goddess could find no fault in the girl's work, and tore it up for "
        "that. Arachne was changed into a spider and has been weaving ever since. Whatever "
        "touches her thread stays touched.",
        resist={'pierce': 0.85}, webbed_strike=True, drop_only=True,
        special="A monster that strikes you hand to hand is slowed for 3 turns."),
    'erlking_mantle': piece(
        'Mantle of the Erlking', 'cloak', 2, 29, 20, 3, 4200, 2.0, 'legendary', 'cloak',
        [60, 95, 70], 'a mantle the green-grey of alder bark, cold to the touch',
        "In Goethe's poem of 1782 a father rides home through the night wood with his sick son "
        "in his arms. The boy says the Erlking is calling to him. The father hears only wind in "
        "dry leaves and sees only mist and old willows. He rides harder. When he reaches the "
        "yard the child is dead. The boy heard everything that moved in that wood. So does "
        "whoever wears the king's mantle.",
        resist={'cold': 0.85}, forest_hearing=6, drop_only=True,
        special="You sense every monster within 6 tiles, even through walls."),
    'falcon_cloak_of_freyja': piece(
        "Freyja's Falcon Cloak", 'cloak', 5, 80, 70, 4, 9400, 1.0, 'legendary', 'cloak',
        [155, 125, 85], 'a cloak of barred brown feathers that lifts in still air',
        "Freyja owned a cloak of falcon feathers, and whoever wore it could fly. She rarely "
        "used it herself. Loki borrowed it twice: once to find out which giant had stolen "
        "Thor's hammer, and once to carry the goddess Idunn home in the shape of a nut with an "
        "eagle a wingbeat behind him. Both times he was faster than what was chasing him, "
        "though only just.",
        dodge_bonus=0.06),
    'mantle_of_muspelheim': piece(
        "Surtur's Ember Mantle", 'cloak', 5, 90, 80, 4, 12000, 3.0, 'legendary', 'cloak',
        [230, 90, 30], 'a mantle that glows at the hem like a banked fire',
        "Surtur has stood at the border of Muspelheim since before the gods, waiting for the "
        "horn that calls him to burn the world. He has had a long time to get used to heat. "
        "The mantle off his shoulders still holds it: fire slides off the wearer like rain off "
        "a slate roof, and a body wrapped in it is harder to hurt by any means.",
        resist={'fire': 0.3}, toughness_bonus=0.05, drop_only=True),

    'nidhoggr_scale': piece(
        "Nidhoggr's Scale", 'cloak', 5, 95, 85, 4, 13000, 3.0, 'legendary', 'cloak',
        [80, 200, 80], 'a single dark green scale as wide as a cloak',
        "Nidhoggr lies under the world-tree Yggdrasil and gnaws at its root. An eagle sits in "
        "the top branches, and a squirrel named Ratatosk runs up and down the trunk all day "
        "carrying insults from one to the other. The dragon has been chewing since the world "
        "began, in the wet and the rot at the bottom of everything, and nothing down there has "
        "ever eaten into its hide.",
        resist={'acid': 0.2, 'poison': 0.3, 'cold': 0.5}, drop_only=True),

    # ------------------------------------------------------------ body
    'serpent_scale_mail': piece(
        'Serpent Scale Mail', 'body', 4, 66, 56, 7, 8500, 20.0, 'legendary', 'scale',
        [60, 160, 100], 'a coat of green scales, each one the size of a hand',
        "Jormungandr was one of Loki's three children. Odin threw the snake into the sea that "
        "rings the world, and it grew there until it could circle the earth and bite its own "
        "tail. Thor once hooked it with an ox head for bait and hauled until his feet went "
        "through the bottom of the boat. Its venom is the thing that will kill him at the end. "
        "These scales came off a young one, and no poison gets through them.",
        resist={'poison': 0.1, 'cold': 0.8}, drop_only=True),

    # ------------------------------------------------------------ legs
    'green_girdle': piece(
        'The Green Girdle', 'legs', 4, 74, 64, 3, 9000, 0.5, 'legendary', 'leather_leggings',
        [70, 170, 80], 'a belt of green silk worked with gold thread',
        "Sir Gawain owed the Green Knight one blow of the axe on his bare neck. The night "
        "before, his host's wife offered him a green silk girdle and said no man wearing it "
        "could be killed. Gawain took it and told no one. The axe came down and only nicked "
        "him. Then the Green Knight laughed, named the girdle, and forgave him. Gawain wore it "
        "home as a mark of shame, and the whole Round Table put on green to wear it with him.",
        story_thread=True, drop_only=True,
        special="Once a floor, a blow that would take a quarter of your health leaves only a scratch."),
    'breeches_of_ragnar': piece(
        "Ragnar's Shaggy Breeches", 'legs', 3, 55, 45, 3, 6500, 4.0, 'legendary', 'leather_leggings',
        [65, 52, 40], 'a pair of shaggy breeches stiff with old pitch',
        "A great serpent lay coiled around the house of a jarl's daughter, and the jarl promised "
        "her to whoever killed it. Young Ragnar had a pair of shaggy breeches and a cloak made, "
        "boiled them in pitch, and rolled in sand until they set hard. The serpent's venom ran "
        "off them. He won the princess and a nickname for life: Lodbrok means Shaggy Breeches.",
        resist={'poison': 0.5, 'pierce': 0.85}),
    'greaves_of_goliath': piece(
        'Greaves of Goliath', 'legs', 4, 74, 64, 5, 8800, 9.0, 'legendary', 'plate_greaves',
        [190, 140, 70], 'a pair of bronze greaves made for a man nine feet tall',
        "The first book of Samuel counts out Goliath's armor piece by piece: a bronze helmet, "
        "a coat of mail weighing five thousand shekels, bronze greaves on his legs, and a "
        "shield-bearer walking in front. For forty days no soldier in Israel would face him. "
        "A shepherd boy named David refused armor altogether and brought a sling. The greaves "
        "did their job perfectly. The stone hit him in the forehead.",
        resist={'slash': 0.8, 'blunt': 0.9}, toughness_bonus=0.05),
}

SHIELD = {
    'hrungnirs_stone_shield': {
        'name': "Hrungnir's Stone Shield", 'symbol': ')', 'color': [150, 150, 150], 'weight': 16.0,
        'min_level': 80, 'tier': 5, 'material': 'legendary', 'ac_bonus': 6, 'equip_threshold': 4,
        'quiz_tier': 5, 'damage_resistances': {'blunt': 0.6, 'slash': 0.8},
        'can_be_cursed': False, 'enchant_bonus': 0,
        'unidentified_name': 'a slab of grey stone with a grip cut into the back',
        'lore': "Hrungnir came to his duel with Thor carrying a shield of stone as broad as a door. "
                "Thor's servant Thjalfi ran up and told him he was holding it wrong: Thor meant "
                "to come at him from under the ground. So the strongest of the giants laid his "
                "shield flat and stood on it, and Thor came from the front with the hammer. It "
                "is a very good shield. It does the most good held up.",
        'floorSpawnWeight': {}, 'is_unique': True, 'template_basis': 'heavy_wooden',
        'peak_floor': 82, 'spread': 10, 'peak_weight': 0.0, 'max_enchant': 3,
        'identified': False, 'id_level': 0, 'value': 11000,
        'containerLootTier': 'rare', 'container_loot_tier': 'rare',
    },
}

# monster -> the named thing it carries
DROPS = {
    'surtur': 'mantle_of_muspelheim',
    'ymir_last_spawn': 'vambraces_of_the_first_winter',
    'hrungnirs_ghost': 'hrungnirs_stone_shield',
    # Six mini-bosses whose named drops were deleted in v2.18.0 as
    # "unreachable quest armor" (they were marked min_level 9999 because
    # only their monster carried them, which is how a named drop works).
    'arachne': 'arachne_silk_cloak',
    'erlking': 'erlking_mantle',
    'anansi': 'anansi_web_cloak',
    'green_knight': 'green_girdle',
    'jormungandr_juvenile': 'serpent_scale_mail',
    'nidhoggr_fragment': 'nidhoggr_scale',
}



def _jload(rel):
    p = ROOT / rel
    raw = open(p, encoding='utf-8', newline='').read()
    return p, raw, json.loads(raw)


def _jsave(p, raw, d):
    out = json.dumps(d, indent=2, ensure_ascii=False) + '\n'
    open(p, 'w', encoding='utf-8', newline='').write(out.replace('\n', '\r\n') if '\r\n' in raw else out)


def main(argv):
    write = '--write' in argv
    pa, rawa, armor = _jload('data/items/armor.json')
    ps, raws, shield = _jload('data/items/shield.json')
    pm, rawm, mons = _jload('data/monsters.json')
    for tid in {d['template_basis'] for d in ARMOR.values()}:
        assert (ROOT / 'data' / 'templates' / 'armor' / f'{tid}.json').exists(), tid
    new_a = [k for k in ARMOR if k not in armor]
    new_s = [k for k in SHIELD if k not in shield]
    print(f'armor: {len(ARMOR)} listed, {len(new_a)} new; shields: {len(SHIELD)} listed, {len(new_s)} new')
    for mid, iid in DROPS.items():
        print(f'  {mid}: carries {mons[mid].get("treasure", {}).get("unique_drop_id")} -> {iid}')
    if not write:
        return 0
    armor.update(ARMOR)
    shield.update(SHIELD)
    for mid, iid in DROPS.items():
        mons[mid].setdefault('treasure', {})['unique_drop_id'] = iid
    _jsave(pa, rawa, armor)
    _jsave(ps, raws, shield)
    _jsave(pm, rawm, mons)
    print('written. Draw their icons with: python tools/content/art/build.py --write armor')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
