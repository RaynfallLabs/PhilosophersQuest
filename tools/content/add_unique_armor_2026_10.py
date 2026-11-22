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
        "None among the Greeks could box so well as Polydeuces, who sailed with Jason in the Argo. When the ship put in among the Bebryces their king Amycus would let no stranger depart unless he boxed with him, and no stranger had ever won, but Polydeuces bound his fists with straps of ox-hide, let the bigger man grow weary and felled him with one blow above the ear. A boxer learns before all else how to endure a blow, and so will the wearer of these straps.",
        resist={'blunt': 0.85}, toughness_bonus=0.03),
    'gloves_of_wayland': piece(
        "Wayland's Forge Gloves", 'hands', 2, 26, 17, 2, 3400, 1.0, 'leather', 'leather_gloves',
        [95, 75, 60], 'a pair of scorched leather gloves that smell of charcoal',
        "The finest smith in all the tales of the North was Wayland. King Nidud, who coveted his work and feared his freedom, cut the sinews behind his knees and set him upon an island to labour at the forge, but he who could not walk away made himself wings, one feather after another, and flew. Hands that have wrought so patiently under guard will not tremble when time runs short.",
        resist={'fire': 0.8}, quiz_timer_bonus=1),
    'glove_of_tyr': piece(
        'Glove of Tyr', 'hands', 4, 64, 55, 3, 7800, 1.5, 'legendary', 'plate_gauntlets',
        [120, 130, 150], 'a single left-hand war glove; there was never a right',
        "Fenrir the wolf would not suffer the ribbon Gleipnir near him unless one of the gods laid a hand between his jaws as a pledge of good faith. All of them knew that the pledge was false, and Tyr alone stepped forward. When the ribbon held, the wolf bit, and Tyr was one-handed ever after. It is by him that men swore their oaths, and this is the glove of the hand that was left to him.",
        resist={'pierce': 0.8}, toughness_bonus=0.06),
    'jarngreipr_gauntlets': piece(
        'Jarngreipr', 'hands', 5, 82, 72, 4, 9600, 3.0, 'legendary', 'plate_gauntlets',
        [110, 110, 125], 'a pair of iron gauntlets too heavy for their size',
        "Jarngreipr, which is to say the iron grippers, are counted by Snorri among three treasures of Thor, along with the hammer Mjolnir and the belt that doubles his strength. When the dwarves forged the hammer Loki took the shape of a fly and bit the one who worked the bellows, so that the handle came out too short and Thor cannot swing it without these gloves. A grip does not slip in them, and a blow carries somewhat further than it should.",
        resist={'lightning': 0.6}, chain_bonus=1),

    # ------------------------------------------------------------ arms
    'bracers_of_atalanta': piece(
        'Bracers of Atalanta', 'arms', 1, 10, 5, 1, 1000, 0.5, 'leather', 'leather_bracers',
        [170, 140, 90], 'a pair of light leather bracers scuffed by brambles',
        "Atalanta was left upon a hillside by a father who had wished for a son, and a she-bear nursed her and hunters brought her up. She would marry only the man who could outrun her, and of the many who tried one won, by rolling three golden apples in her path. When the Calydonian Boar was hunted it was she who drew first blood, though a band of heroes could not, and in all that hunt there was nothing that could lay a hand on her.",
        dodge_bonus=0.04),
    'vambraces_of_roland': piece(
        'Vambraces of Roland', 'arms', 3, 50, 40, 3, 6000, 2.0, 'legendary', 'steel_vambraces',
        [180, 180, 195], 'a pair of dented steel arm-guards with a Frankish cross',
        "Roland had command of the rear guard in 778, when Charlemagne's army marched homeward out of Spain through the pass of Roncevaux. The Song of Roland tells that three times his friend Oliver begged him to sound the horn and call back the king, and three times his pride refused. When none was left to save he blew at last, so hard that his temples burst. The rear guard held the pass to the last man, and to the end the arms that bore these vambraces did not drop.",
        resist={'slash': 0.85}, toughness_bonus=0.05),
    'vambraces_of_the_first_winter': piece(
        'Vambraces of the First Winter', 'arms', 5, 85, 80, 5, 11500, 3.0, 'legendary', 'plate_vambraces',
        [170, 210, 235], 'a pair of arm-guards of blue ice that does not melt',
        "Before ever there was earth or sky there was a great gap, with fire to the south and ice to the north, and where the two met the ice dripped and the drops became the giant Ymir. Odin and his brothers slew him and built the world out of his body. The creature that bore these vambraces claims to be older than that slaying, and the ice in them is of the first morning, so that no cold since then has had any power to harm them.",
        resist={'cold': 0.3}, toughness_bonus=0.05, drop_only=True),

    # ------------------------------------------------------------ shirt
    'hair_shirt_of_becket': piece(
        "Becket's Hair Shirt", 'shirt', 1, 12, 5, 1, 1000, 1.0, 'cloth', 'padded_shirt',
        [125, 105, 85], 'a rough undershirt of goat hair',
        "Thomas Becket was friend and chancellor to the king, and loved fine raiment and good food. Henry II made him Archbishop of Canterbury, looking to have an ally there, but Becket took the part of the Church. On 29 December 1170 four of the king's knights cut him down in his own cathedral, and when the monks came to unclothe the body they found beneath the robes this shirt of coarse hair, which he had long worn against his skin where none could see it.",
        toughness_bonus=0.04),
    'shirt_of_aslaug': piece(
        "Aslaug's Shirt", 'shirt', 3, 60, 50, 4, 7200, 1.0, 'legendary', 'padded_shirt',
        [150, 150, 165], 'a grey shirt woven without a single seam showing',
        "Aslaug, the daughter of Sigurd the dragon-slayer, was wife to Ragnar Lodbrok. When he would sail for England against her counsel she gave him a shirt of her own weaving and told him that no blade would bite him while he wore it. King Aella's men could not wound him, and when they cast him into a pit of serpents the snakes also would not touch him, until Aella had the shirt stripped from his back.",
        resist={'slash': 0.8, 'pierce': 0.8, 'poison': 0.7}),
    'seamless_tunic': piece(
        'The Seamless Tunic', 'shirt', 4, 76, 66, 4, 9000, 0.5, 'legendary', 'padded_shirt',
        [225, 215, 195], 'a plain tunic woven in one piece from the top down',
        "The soldiers at the cross, as John's gospel tells, parted the clothes of Jesus into four shares, one to each, and the tunic remained. It was without seam, being woven in one piece from the top down, and when they had looked upon it they said, let us not tear it, and threw dice for it instead. So four hard men, with a day's killing behind them, agreed that this one thing should stay whole.",
        resist={'magic': 0.8}, toughness_bonus=0.05),

    # ------------------------------------------------------------ cloak
    'half_cloak_of_martin': piece(
        "Martin's Half Cloak", 'cloak', 1, 8, 5, 1, 800, 1.0, 'cloth', 'cloak',
        [175, 45, 45], "half of a red soldier's cloak, cut clean with a blade",
        "As a young horseman of Rome at Amiens, Martin met upon a winter's day a beggar at the city gate who had scarcely any clothing. Having no money left, he drew his sword, cut his army cloak in two and gave the man the half. The other half the Frankish kings afterward kept as their holiest relic, and as its Latin name was cappa, its keepers were the cappellani and the room where it hung was the cappella, from which all chaplains and chapels have their names.",
        resist={'cold': 0.8}, toughness_bonus=0.03),
    'anansi_web_cloak': piece(
        "Anansi's Web Cloak", 'cloak', 5, 92, 80, 4, 12500, 0.5, 'legendary', 'cloak',
        [220, 180, 40], 'a cloak of gold thread stitched all over with a pattern of spider web',
        "All stories belonged once to Nyame the sky god, as the Akan people of West Africa tell, until Anansi the spider sought to buy them. Nyame named a price that none could pay, the hornets, the python and the leopard, all alive, but Anansi, who was small and weak, tricked each of them into binding itself. From that day every story is a spider story, and it is the teller of the tale who decides how it shall end.",
        resist={'poison': 0.5}, story_thread=True, drop_only=True,
        special="Once a floor, a blow that would take a quarter of your health leaves only a scratch."),
    'arachne_silk_cloak': piece(
        "Arachne's Silk Cloak", 'cloak', 1, 9, 5, 2, 1800, 0.5, 'silk', 'cloak',
        [220, 220, 235], 'a pale cloak of silk too fine to have been spun by hand',
        "So well did Arachne of Lydia weave that the nymphs forsook their rivers to watch her, and she boasted that not Athena herself could teach her anything. The goddess came and wove beside her and, as Ovid tells, could find no fault in the girl's work, and tore it up for that very cause. Arachne was turned into a spider and has been weaving ever since, and whatever touches her thread is not soon free of it.",
        resist={'pierce': 0.85}, webbed_strike=True, drop_only=True,
        special="A monster that strikes you hand to hand is slowed for 3 turns."),
    'erlking_mantle': piece(
        'Mantle of the Erlking', 'cloak', 2, 29, 20, 3, 4200, 2.0, 'legendary', 'cloak',
        [60, 95, 70], 'a mantle the green-grey of alder bark, cold to the touch',
        "Homeward through the night wood rode a father with his sick son in his arms, as Goethe told it in a poem of 1782, and the boy cried that the Erlking was calling to him. The father heard nothing but wind in the dry leaves and saw nothing but mist and old willows, and he rode the harder, yet when he reached the yard the child was dead. The boy had heard all that moved in that wood, and whoever puts on the king's mantle will hear as much.",
        resist={'cold': 0.85}, forest_hearing=6, drop_only=True,
        special="You sense every monster within 6 tiles, even through walls."),
    'falcon_cloak_of_freyja': piece(
        "Freyja's Falcon Cloak", 'cloak', 5, 80, 70, 4, 9400, 1.0, 'legendary', 'cloak',
        [155, 125, 85], 'a cloak of barred brown feathers that lifts in still air',
        "Freyja had a cloak of falcon's feathers in which the wearer might fly, though she seldom used it herself. Loki borrowed it twice: once to learn which giant had stolen the hammer of Thor, and once to bear the goddess Idunn home in the shape of a nut, with an eagle but a wingbeat behind him. Each time he outflew what hunted him, though only by a little.",
        dodge_bonus=0.06),
    'mantle_of_muspelheim': piece(
        "Surtur's Ember Mantle", 'cloak', 5, 90, 80, 4, 12000, 3.0, 'legendary', 'cloak',
        [230, 90, 30], 'a mantle that glows at the hem like a banked fire',
        "Since before the gods were, Surtur has stood upon the border of Muspelheim to await the horn that shall summon him to burn the world, and in so long a waiting he has grown well used to heat. His mantle holds it still, so that fire runs off the wearer as rain off a slate roof and the body wrapped in it is harder to hurt by any means.",
        resist={'fire': 0.3}, toughness_bonus=0.05, drop_only=True),

    'nidhoggr_scale': piece(
        "Nidhoggr's Scale", 'cloak', 5, 95, 85, 4, 13000, 3.0, 'legendary', 'cloak',
        [80, 200, 80], 'a single dark green scale as wide as a cloak',
        "Beneath the world-tree Yggdrasil the dragon Nidhoggr lies gnawing at the root. An eagle sits in the topmost boughs, and all day a squirrel named Ratatosk runs up and down the trunk bearing insults from the one to the other. The dragon has chewed there since the world began, amid the wet and rot at the bottom of all things, and nothing in that place has ever eaten into his hide.",
        resist={'acid': 0.2, 'poison': 0.3, 'cold': 0.5}, drop_only=True),

    # ------------------------------------------------------------ body
    'serpent_scale_mail': piece(
        'Serpent Scale Mail', 'body', 4, 66, 56, 7, 8500, 20.0, 'legendary', 'scale',
        [60, 160, 100], 'a coat of green scales, each one the size of a hand',
        "Of the three children of Loki one was the serpent Jormungandr, which Odin flung into the sea that rings the world, and there it grew until it could circle the earth and take its own tail in its mouth. Thor hooked it once with an ox head for bait and hauled until his feet broke through the bottom of the boat, and by its venom he shall die at the last. These scales were taken from a young one, and there is no poison that can pass through them.",
        resist={'poison': 0.1, 'cold': 0.8}, drop_only=True),

    # ------------------------------------------------------------ legs
    'green_girdle': piece(
        'The Green Girdle', 'legs', 4, 74, 64, 3, 9000, 0.5, 'legendary', 'leather_leggings',
        [70, 170, 80], 'a belt of green silk worked with gold thread',
        "Sir Gawain was bound to take upon his bare neck one stroke of the Green Knight's axe. On the night before, his host's wife offered him a girdle of green silk, saying that no man who wore it could be killed, and he took it and told no one. The axe came down and did but nick him, and then the Green Knight laughed, named the girdle and forgave him. Gawain wore it home for a mark of his shame, and all the Round Table put on green to share it with him.",
        story_thread=True, drop_only=True,
        special="Once a floor, a blow that would take a quarter of your health leaves only a scratch."),
    'breeches_of_ragnar': piece(
        "Ragnar's Shaggy Breeches", 'legs', 3, 55, 45, 3, 6500, 4.0, 'legendary', 'leather_leggings',
        [65, 52, 40], 'a pair of shaggy breeches stiff with old pitch',
        "A great serpent lay coiled about the house of a jarl's daughter, and her father promised her to the one who should kill it. Young Ragnar had shaggy breeches and a cloak made, boiled them in pitch and rolled in sand until they set hard, and the venom ran off them. So he won the princess, and a name to bear all his life, for Lodbrok means Shaggy Breeches.",
        resist={'poison': 0.5, 'pierce': 0.85}),
    'greaves_of_goliath': piece(
        'Greaves of Goliath', 'legs', 4, 74, 64, 5, 8800, 9.0, 'legendary', 'plate_greaves',
        [190, 140, 70], 'a pair of bronze greaves made for a man nine feet tall',
        "Goliath went out to war in a helmet of bronze and a coat of mail that weighed five thousand shekels, with bronze greaves upon his legs and a shield-bearer before him, as the first book of Samuel reckons it piece by piece. For forty days no soldier of Israel would face him, until David, a shepherd boy, refused all armour and brought a sling. These greaves served him faultlessly, but they could not guard his forehead, where the stone struck him.",
        resist={'slash': 0.8, 'blunt': 0.9}, toughness_bonus=0.05),
}

SHIELD = {
    'hrungnirs_stone_shield': {
        'name': "Hrungnir's Stone Shield", 'symbol': ')', 'color': [150, 150, 150], 'weight': 16.0,
        'min_level': 80, 'tier': 5, 'material': 'legendary', 'ac_bonus': 6, 'equip_threshold': 4,
        'quiz_tier': 5, 'damage_resistances': {'blunt': 0.6, 'slash': 0.8},
        'can_be_cursed': False, 'enchant_bonus': 0,
        'unidentified_name': 'a slab of grey stone with a grip cut into the back',
        'lore': "Hrungnir, the strongest of the giants, came to his duel with Thor bearing this shield of stone, broad as a door. But Thjalfi, the servant of Thor, ran to him and said that he held it amiss, since his master meant to come at him from beneath the earth. The giant believed him and laid the shield flat and stood upon it, and Thor came from in front with the hammer. The shield was never at fault, and it will guard very well whoever holds it upright.",
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
