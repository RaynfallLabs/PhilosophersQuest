"""The nine deep kinds of the 2026-11-17 monster pass (ruling 12: every family
in every tier). Each one fills a family's empty depth with a creature named in
myth or literature, never a "greater X" (sources checked on Grokipedia first,
then Wikipedia).

Read by tools/balance/monster_pass_2026_11_17.py, which writes the kinds into
data/monsters.json with their numbers baked at their floor: health on the
floor's median (floor_curve.target_hp, a pack's share through
respawn_by_hp.SWARM_SEAT_MULT) and each blow a stated share (`w`) of the
floor's typical hit (floor_curve.target_dmg). LORE, NOT FLOOR: nothing here
or anywhere scales with the floor at run time.

    birds          Corpse-Swallower (Hraesvelgr's brood)   floor 72, the rime
    giants         Rime-Thurs (the hrimthursar)            floor 70, the rime
    goblinkin      Kallikantzaros                          floor 68, the rime
    goblinkin      Oni                                     floor 84, the abyss
    serpents       Mushmahhu (Tiamat's seven-headed one)   floor 88, the abyss
    shapeshifters  Nine-Tailed Fox (Tamamo-no-Mae)         floor 86, the abyss
    legend         Geryon (Dante's image of fraud)         floor 89, the abyss
    gorgons        Viy (Gogol)                             floor 90, the abyss
    constructs     Image of the Beast (Revelation 13)      floor 91, the abyss
"""
from __future__ import annotations


def blow(name, w, typ, delivery='blow', effect=None, chance=0.0, duration=0, **extra):
    """One attack: `w` is its share of the floor's typical hit."""
    a = {'name': name, 'w': w, 'type': typ, 'delivery': delivery}
    if effect:
        a.update(effect=effect, effect_chance=chance, effect_duration=duration)
    a.update(extra)
    return a


# Each kind: its data (no hp, damage, thac0 or spawn band: the pass bakes
# those) plus 'peak', 'aim' (its lore aim against the band's median: lower
# is straighter) and 'seat' (a pack's share, respawn_by_hp.SWARM_SEAT_MULT).
NEW_KINDS: dict[str, dict] = {
    'hraesvelg_eagle': {
        'peak': 72, 'aim': 0, 'seat': 1.0,
        'name': 'Corpse-Swallower', 'symbol': 'B', 'color': [210, 215, 225], 'speed': 14,
        'ai_pattern': 'aggressive', 'peak_weight': 2.0, 'frequency': 2,
        'attacks': [
            blow('Corpse-Swallowing Bite', 1.1, 'pierce', 'bite', 'bleeding', 0.4, 4),
            blow("Wind from the World's Edge", 0.9, 'cold', 'blow', 'slowed', 0.4, 3),
        ],
        'tags': ['beast'], 'family': 'birds', 'pronoun': 'it', 'size': 'huge',
        'treasure': {'gold': [0, 0], 'item_chance': 0.3, 'item_tier': 4, 'purse': 'none'},
        'lore': ("Vafthrudnir told Odin of him in their contest of wisdom: Hraesvelgr, the "
                 "Corpse-Swallower, a giant in an eagle's shape who sits at heaven's end, and "
                 "from his wings comes every wind that blows over men. Snorri set him at the "
                 "northern edge of the sky. The great eagles of the rime halls are his brood. "
                 "Their stoop is a gale with talons in it, and the wind of their wings is the "
                 "cold of the world's end."),
    },
    'rime_thurs': {
        'peak': 70, 'aim': -1, 'seat': 1.0,
        'name': 'Rime-Thurs', 'symbol': 'H', 'color': [170, 200, 225], 'speed': 9,
        'ai_pattern': 'aggressive', 'peak_weight': 2.5, 'frequency': 2,
        'attacks': [
            blow('Rime Maul', 1.15, 'blunt', 'blow', 'stunned', 0.2, 1),
            blow('Breath of Elivagar', 0.95, 'cold', 'breath', 'frozen', 0.3, 2),
            blow('Hurled Ice', 0.8, 'cold', 'ranged', ranged=True),
        ],
        'tags': ['giant', 'humanoid'], 'family': 'giants', 'pronoun': 'he', 'size': 'huge',
        'treasure': {'gold': [0, 0], 'item_chance': 0.35, 'item_tier': 4, 'purse': 'sack'},
        'lore': ("Snorri says the first giant, Ymir, grew where the rime of the venomous rivers "
                 "Elivagar met the warm air out of Muspell, and the rime-thurses are his line. "
                 "When Odin and his brothers killed Ymir, his blood drowned them all but "
                 "Bergelmir, who got away in a boat with his wife, and the old giant race came "
                 "again from him. A rime-thurs is of that oldest blood, older than the frost "
                 "giants of the jarls' halls, and at Ragnarok, the Voluspa says, Hrym will lead "
                 "them out of the east."),
    },
    'kallikantzaros': {
        'peak': 68, 'aim': 0, 'seat': 2.5,
        'name': 'Kallikantzaros', 'symbol': 'k', 'color': [70, 50, 40], 'speed': 13,
        'ai_pattern': 'aggressive', 'peak_weight': 2.0, 'frequency': 3,
        'pack': True, 'pack_size': [3, 4],
        'attacks': [
            blow('Long Nails', 1.0, 'slash', 'blow', 'bleeding', 0.3, 3),
            blow('Saw-Worn Fangs', 1.0, 'pierce', 'bite'),
            blow('Fistful of Soot', 0.6, 'blunt', 'ranged', 'blinded', 0.3, 2, ranged=True),
        ],
        'tags': ['goblinoid'], 'family': 'goblinkin', 'pronoun': 'he', 'size': 'small',
        'treasure': {'gold': [0, 0], 'item_chance': 0.2, 'item_tier': 4, 'purse': 'purse'},
        'lore': ("Greek villages keep the hearth burning through the twelve days of Christmas, "
                 "because that is when the kallikantzaroi come up. The rest of the year they live "
                 "under the earth, sawing at the World Tree that holds it up. Every winter they "
                 "are nearly through, and every winter they leave the work to come up and make "
                 "mischief, and the tree heals while they are gone. They are small, shaggy and "
                 "black with soot, with red eyes and long nails. They fear fire, and holy water "
                 "at Epiphany drives them all back down. In the rime halls the winter never ends, "
                 "and neither does their holiday."),
    },
    'oni': {
        'peak': 84, 'aim': 0, 'seat': 2.0,
        'name': 'Oni', 'symbol': 'O', 'color': [190, 60, 50], 'speed': 10,
        'ai_pattern': 'aggressive', 'peak_weight': 2.0, 'frequency': 3,
        'pack': True, 'pack_size': [2, 3],
        'attacks': [
            blow('Iron Kanabo', 1.2, 'blunt', 'blow', 'stunned', 0.25, 1),
            blow('Fanged Bite', 0.9, 'pierce', 'bite'),
            blow("Hell-Warden's Roar", 0.7, 'magic', 'voice', 'feared', 0.3, 3),
        ],
        'tags': ['goblinoid', 'demon'], 'family': 'goblinkin', 'pronoun': 'he', 'size': 'large',
        'treasure': {'gold': [0, 0], 'item_chance': 0.3, 'item_tier': 5, 'purse': 'purse'},
        'lore': ("In the Buddhist hells of Japan the oni are the jailers: horned and fanged, red "
                 "or blue of skin, in loincloths of tiger skin, carrying the iron club called the "
                 "kanabo. They punish the dead as King Enma sentences them. Some came up into the "
                 "world. Shuten-doji's band of Mount Oe raided the capital until Minamoto no "
                 "Raiko and his four retainers came disguised as mountain monks, gave them drugged "
                 "sake, and took the chief's head while he slept. On Setsubun every house still "
                 "throws roasted beans out of the door, shouting, 'Oni out, luck in!'"),
    },
    'mushmahhu': {
        'peak': 88, 'aim': 0, 'seat': 1.0,
        'name': 'Mushmahhu', 'symbol': 'S', 'color': [90, 125, 60], 'speed': 11,
        'ai_pattern': 'aggressive', 'peak_weight': 2.0, 'frequency': 2,
        'multi_attack_count': 2,
        'attacks': [
            blow('Seven-Headed Bite', 0.6, 'pierce', 'bite', 'poisoned', 0.4, 5),
            blow('Spit of Venom-Blood', 0.55, 'poison', 'breath', 'poisoned', 0.5, 6),
            blow('Constricting Coils', 0.55, 'blunt', 'grapple', 'immobilized', 0.3, 2),
        ],
        'tags': ['beast', 'reptile'], 'family': 'serpents', 'pronoun': 'it', 'size': 'huge',
        'treasure': {'gold': [0, 0], 'item_chance': 0.4, 'item_tier': 5, 'purse': 'none'},
        'lore': ("The Enuma Elish names the eleven monsters Tiamat made to fight the younger "
                 "gods, filled with venom for blood, and the Exalted Serpent, the mushmahhu, is "
                 "third among them. Older Sumerian hymns praise the god Ninurta for capturing a "
                 "serpent with seven heads and hanging it on his chariot as a trophy. Its seven "
                 "heads strike from seven sides, and a blade that bites deep comes back smoking "
                 "with its blood."),
    },
    'kyubi_kitsune': {
        'peak': 86, 'aim': -1, 'seat': 1.0,
        'name': 'Nine-Tailed Fox', 'symbol': 'f', 'color': [240, 225, 200], 'speed': 13,
        'ai_pattern': 'ranged', 'peak_weight': 2.0, 'frequency': 2,
        'can_phase_blink': True, 'phase_blink_chance': 0.25,
        'attacks': [
            blow('Fox-Fire', 1.0, 'fire', 'ranged', 'burning', 0.3, 3, ranged=True),
            blow('Bewitching Gaze', 0.8, 'magic', 'gaze', 'confused', 0.35, 3),
            blow('Nine Tails', 1.0, 'blunt', 'sting'),
            blow('Fox Bite', 1.05, 'pierce', 'bite'),
        ],
        'tags': ['beast', 'shapeshifter'], 'family': 'shapeshifters', 'pronoun': 'she',
        'size': 'medium',
        'treasure': {'gold': [0, 0], 'item_chance': 0.4, 'item_tier': 5, 'purse': 'none'},
        'lore': ("A fox that lives a thousand years grows nine tails and can take any shape it "
                 "likes. The Japanese tale says one became Tamamo-no-Mae, the loveliest and "
                 "cleverest lady at the court of Emperor Toba, until the emperor fell sick and the "
                 "court diviner Abe no Yasunari named what she was. She fled, an army hunted her "
                 "down on the plain of Nasu, and her spirit went into a boulder, the Killing "
                 "Stone, that poisoned whatever touched it. Later tellers gave her earlier lives, "
                 "as Daji, who ruined the last king of the Shang. The Killing Stone split in two "
                 "in 2022."),
    },
    'geryon': {
        'peak': 89, 'aim': 0, 'seat': 1.0,
        'name': 'Geryon', 'symbol': 'G', 'color': [150, 110, 80], 'speed': 12,
        'ai_pattern': 'aggressive', 'peak_weight': 1.5, 'frequency': 2, 'proper_noun': True,
        'attacks': [
            blow('Forked Sting', 1.2, 'pierce', 'sting', 'poisoned', 0.45, 6),
            blow('Gaze of the Honest Face', 0.7, 'magic', 'gaze', 'confused', 0.35, 3),
            blow('Hairy Paws', 0.95, 'slash', 'blow'),
        ],
        'tags': ['beast', 'demon'], 'family': 'legend', 'pronoun': 'he', 'size': 'huge',
        'treasure': {'gold': [0, 0], 'item_chance': 0.45, 'item_tier': 5, 'purse': 'none'},
        'lore': ("Virgil called it up out of the pit at the edge of the seventh circle, and "
                 "Dante watched it come: the face of a just man, kind and open, on the body of a "
                 "serpent painted all over with knots and wheels, two hairy paws, and a forked "
                 "sting at the tip of its tail. Dante calls it the filthy image of fraud. It "
                 "carried the two poets down through the dark to the ditches where the cheats "
                 "are punished. The Greeks had a Geryon too, a three-bodied giant whose red "
                 "cattle Heracles took; Dante kept the name and gave it the face of a lie."),
    },
    'viy': {
        'peak': 90, 'aim': -1, 'seat': 1.0,
        'name': 'Viy', 'symbol': 'V', 'color': [95, 85, 70], 'speed': 6,
        'ai_pattern': 'aggressive', 'peak_weight': 1.5, 'frequency': 2, 'proper_noun': True,
        'attacks': [
            blow('Gaze Under the Lids', 1.3, 'magic', 'gaze', 'paralyzed', 0.35, 2),
            blow('Root-Fingered Grab', 1.0, 'blunt', 'grapple', 'immobilized', 0.3, 2),
            blow('Iron Face', 0.8, 'blunt', 'blow'),
        ],
        'tags': ['demon'], 'family': 'gorgons', 'pronoun': 'he', 'size': 'large',
        'treasure': {'gold': [0, 0], 'item_chance': 0.45, 'item_tier': 5, 'purse': 'none'},
        'lore': ("Gogol wrote that Viy is a colossal creation of the common people's "
                 "imagination: the chief of the gnomes, whose eyelids hang down to the ground. "
                 "In his tale the dead witch calls him into the church on the third night, a "
                 "squat thing caked in black earth, with an iron face and arms and legs like "
                 "roots. 'Lift my eyelids,' he says, and his servants lift them. The student "
                 "Khoma Brut had been told not to look. He looked, and died of fright. The lids "
                 "are heavy and slow to lift, so there is a moment before Viy sees you. A mirror "
                 "or a blindfold is the answer; never meet his eyes."),
    },
    'image_of_the_beast': {
        'peak': 91, 'aim': 0, 'seat': 1.0,
        'name': 'Image of the Beast', 'symbol': 'I', 'color': [200, 165, 70], 'speed': 6,
        'ai_pattern': 'aggressive', 'peak_weight': 1.5, 'frequency': 2,
        'attacks': [
            blow('Lion-Mouthed Roar', 0.8, 'magic', 'voice', 'feared', 0.35, 3),
            blow('Curse of the Image', 1.3, 'drain', 'voice'),
            blow('Golden Weight', 1.0, 'blunt', 'blow', 'stunned', 0.2, 1),
        ],
        'tags': ['construct'], 'family': 'constructs', 'pronoun': 'it', 'size': 'huge',
        'treasure': {'gold': [0, 0], 'item_chance': 0.5, 'item_tier': 5, 'purse': 'none'},
        'lore': ("John saw a second beast come up out of the earth, and it told the people to "
                 "make an image of the first beast, and gave the image breath, so that the image "
                 "should both speak and cause all who would not worship it to be killed "
                 "(Revelation 13). The images stand in the lowest halls still, golden and "
                 "speaking. Its voice commands, and a hero who will not bow is struck down by the "
                 "word. Wax in the ears keeps the command out, and it is a made thing: a hammer "
                 "unmakes it."),
    },
}

# The kitchen: each new kind joins the kin group of its nearest kin
# (tools/content/kitchen/kin_groups.txt; close kin share one ingredient).
KIN_GROUP = {
    'hraesvelg_eagle': 'roc_chick',        # the great eagles: Roc Drumstick
    'rime_thurs': 'frost_giant',           # Frost Giant Rime Ham
    'kallikantzaros': 'goblin',            # Goblin Gristle
    'oni': 'ogre',                         # the ogres: Ogre Bangers
    'mushmahhu': 'world_serpent',          # World Serpent Scale: venom for blood
    'kyubi_kitsune': 'puca',               # the shape-changers' mote
    'geryon': 'manticore',                 # the man-faced, sting-tailed beasts
    'viy': 'spriggan',                     # the earth-folk's Root-Acorn: his limbs are roots
    'image_of_the_beast': 'talos',         # the made men of metal: Talos Bronze Heart
}
