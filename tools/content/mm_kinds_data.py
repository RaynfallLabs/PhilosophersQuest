"""The data of the MONSTERS AND MAGIC kinds (slice M, 2026-11-19): read by
tools/content/add_mm_kinds_2026_11.py, which writes it into the game data.

Thirty-two new kinds from real myth, folklore, scripture and natural history
(the research: _mm_2026_11_19/A/PROPOSALS.md; D&D gave only the mechanics),
written by the monster lore rubric (docs/design/MONSTER_LORE_PASS_2026_11_19.md)
against the hero of each kind's own floor, and the upgrades to existing kinds
the plan kept. LORE, NOT FLOOR: every number is the creature's own.

Offline tooling (not loaded at runtime).
"""
from __future__ import annotations


def atk(name, damage, typ, delivery, effect=None, chance=None, turns=None, **kw):
    a = {'name': name, 'damage': damage, 'type': typ, 'delivery': delivery}
    if effect:
        a.update(effect=effect, effect_chance=chance, effect_duration=turns)
    if delivery == 'ranged' or kw.pop('ranged', False):
        a['ranged'] = True
    a.update(kw)
    return a


def kind(name, symbol, color, hp, speed, ai, thac0, peak, low, spread, weight, attacks, *,
         family, tags, res=(), weak=(), pronoun='it', opener=None, pack=None, item=0.05, **extra):
    tier = (peak - 1) // 20 + 1
    d = {
        'name': name, 'symbol': symbol, 'color': list(color), 'hp': hp, 'speed': speed,
        'ai_pattern': ai, 'thac0': thac0, 'peak_floor': peak, 'spread': spread,
        'peak_weight': weight, 'min_level': low, 'attacks': list(attacks),
        'resistances': list(res), 'weaknesses': list(weak), 'tags': list(tags),
        'family': family, 'pronoun': pronoun, 'harvest_tier': tier,
        'treasure': {'gold': [0, 0], 'item_chance': item, 'item_tier': tier},
        'lore': '', 'frequency': max(1, int(weight)), 'thac0_lore': thac0 + 1,
        'shrugs_off': [], 'status_immune': [], 'status_weak': [],
    }
    if pack:
        d['pack'] = True
        d['pack_size'] = list(pack)
    if opener:
        d['opener'] = {'attack': opener[0], 'range': opener[1]}
    d.update(extra)
    return d


# ---------------------------------------------------------------------------
# The new kinds. Tier 1: floors 1-20, tier 2: 21-40 ... (tier = (peak-1)//20+1).
# The tier census holds tier 1's ordinary kinds to 35%: eleven new tier-1
# kinds fit (the plan: the centaur moved to floor 21, the amphisbaena cut, and
# the myling cut for its folklore).
# ---------------------------------------------------------------------------
NEW = {}

NEW['mandrake'] = kind(
    'Mandrake', 'm', (150, 120, 80), '6d10+26', 6, 'ambush', 15, 12, 10, 5, 3.0,
    [atk('Root Lash', '1d6+1', 'blunt', 'blow'),
     atk('Sleep-Sap Spit', '1d3', 'poison', 'breath', 'sleeping', 0.3, 3, ranged=True)],
    family='plants', tags=['plant'], res=['poison'], weak=['fire'],
    death_throes={'type': 'magic', 'share': 0.05, 'radius': 2, 'delivery': 'voice',
                  'effect': 'stunned', 'effect_duration': 2, 'alarm_radius': 12,
                  'line': "The Mandrake shrieks as it dies, a cry that goes through stone!",
                  'warn_line': "A thin keening rises from the Mandrake's split root."},
    lore=("Theophrastus says the root-cutters drew circles round a mandrake with a sword before they "
          "dug it, and later herbals add the scream: pull one from the earth and its cry kills whoever "
          "hears it, so the wise tied a hungry dog to the root and walked away holding meat. Physicians "
          "boiled the forked root in wine to put a patient to sleep before the knife. Down here the "
          "roots have pulled themselves up on legs of their own, and they still scream when they die."))

NEW['kappa'] = kind(
    'Kappa', 'k', (90, 150, 80), '8d10+28', 12, 'aggressive', 13, 11, 9, 5, 3.0,
    [atk('Beak Bite', '1d6+2', 'pierce', 'bite'),
     atk('Sumo Grapple', '1d6+1', 'blunt', 'grapple', 'immobilized', 0.35, 2)],
    family='serpents', tags=['reptile'], res=['cold'], weak=['fire', 'iron'], opener=('Sumo Grapple', 1),
    on_stunned={'effect': 'weakened', 'turns': 12,
                'line': "The water spills from the Kappa's dish, and its arms go slack."},
    appeased_by={'food': 'plain',
                 'line': "The Kappa takes your offering, bows low, and goes back to its pool."},
    lore=("Japanese villagers kept children away from deep pools because of the kappa: a beaked, "
          "shelled little water-imp with a dish of water set into the top of its head. It drags "
          "swimmers and horses under and challenges travellers to wrestle. But it is very polite. Bow "
          "to a kappa and it must bow back; the water spills from its dish and its strength drains "
          "away with it. Farmers floated cucumbers downriver to keep it friendly, and a kappa given a "
          "gift of food will leave the giver alone."))

NEW['eloko'] = kind(
    'Eloko', 'e', (110, 150, 60), '7d10+27', 12, 'hit_and_run', 13, 13, 11, 5, 3.0,
    [atk('Bell Charm', '1d3', 'magic', 'voice', 'paralyzed', 0.35, 2),
     atk('Wide Jaws', '1d8+2', 'pierce', 'bite')],
    family='fair_folk', tags=['fey'], res=['poison'], weak=['fire'], pack=(2, 3), opener=('Bell Charm', 4),
    lore=("The Mongo people of the Congo forest tell of the biloko, small hungry spirits who live in "
          "hollow trees. Grass grows on them in place of hair, they dress in leaves, and their mouths "
          "open wide enough to swallow a man's head. Each one carries a little bell. Its chime is so "
          "sweet that a hunter forgets where he is going and walks toward it, and then he cannot move "
          "at all. Hunters wore charms to hide from them; down here a hunter stops his ears."))

NEW['asanbosam'] = kind(
    'Asanbosam', 'V', (120, 90, 70), '13d10+44', 12, 'ambush', 11, 14, 11, 5, 3.0,
    [atk('Dangling-Leg Grab', '1d8+2', 'blunt', 'grapple', 'immobilized', 0.5, 2),
     atk('Iron-Toothed Bite', '1d10+3', 'drain', 'bite')],
    family='vampires_liches', tags=['undead'], res=['cold', 'poison'], weak=['fire', 'holy'],
    opener=('Dangling-Leg Grab', 1), drain_heals_self=0.5, hidden_overhead=True, relurks=True,
    lore=("Akan hunters of the Ghanaian forest feared the sasabonsam: a long-legged thing with iron "
          "teeth and long matted hair that lives high in the trees, its feet pointing both ways. Its "
          "favourite trick is to sit on a high branch and dangle its legs, to snare a hunter walking "
          "beneath and haul him up into the leaves. Enslaved Akan people carried the tale across the "
          "sea, and Edward Long wrote it down in Jamaica in 1774. Down here it hangs from the roof "
          "beams and the roots of the old halls, where only a light shows it."))

NEW['ahuizotl'] = kind(
    'Ahuizotl', 'a', (40, 50, 60), '11d10+45', 14, 'ambush', 10, 16, 13, 5, 3.0,
    [atk("Child's Wail", '1d3', 'magic', 'voice', 'confused', 0.4, 4),
     atk('Hidden Hand Grab', '1d6+2', 'blunt', 'grapple', 'immobilized', 0.45, 2),
     atk('Drowning Squeeze', '1d8+3', 'blunt', 'grapple', 'strangulation', 0.3, 3)],
    family='serpents', tags=['beast'], res=['cold'], weak=['fire'], opener=("Child's Wail", 5),
    pull_chance=0.3, relurks=True,
    lore=("Sahagun's Aztec informants described the ahuizotl of the lakes: a sleek little dog-like "
          "water beast with hands like a monkey's and one more hand at the very end of its tail. When "
          "it has not fed it cries like a child on the shore, or makes the fish leap to bring "
          "fishermen close. Then the tail-hand seizes them and drags them under. The drowned were "
          "found days later, and only a priest dared touch them."))

NEW['khalkotauros'] = kind(
    'Khalkotauros', 'q', (190, 140, 70), '22d10+80', 12, 'aggressive', 11, 17, 15, 5, 3.0,
    [atk('Bronze Gore', '2d8+4', 'pierce', 'trample'),
     atk('Furnace Breath', '2d6', 'fire', 'breath', 'burning', 0.4, 4)],
    family='constructs', tags=['construct'], res=['fire', 'poison'], weak=['cold'], pack=(2, 2),
    opener=('Furnace Breath', 3), can_charge=True, charge_bonus_mult=1.3,
    lore=("Hephaestus forged two bulls of bronze for King Aeetes of Colchis, with brazen hooves and "
          "mouths that breathed fire. Aeetes set Jason to yoke them and plough the field of Ares in a "
          "single day. Medea gave him an ointment that kept fire and bronze from his skin for that one "
          "day, and he forced them to their knees. The pairs that stamp through these halls have never "
          "felt a yoke."))

NEW['cu_sith'] = kind(
    'Cu-Sith', 'd', (60, 110, 70), '20d10+74', 16, 'aggressive', 10, 17, 14, 5, 3.0,
    [atk('Silent Bite', '2d6+3', 'pierce', 'bite')],
    family='fair_folk', tags=['beast'], res=['cold'], weak=['iron'],
    countdown_voice={
        'every': 3, 'count': 3,
        'attack': atk('Third Bark', '1d4', 'magic', 'voice', 'feared', 0.6, 4),
        'lines': ["The Cu-Sith barks once. The sound rolls through the halls.",
                  "The Cu-Sith barks a second time. Get out of its sight!",
                  "The Cu-Sith barks the third time!"],
        'unseen': ["Somewhere out of sight a great hound barks once, slow and deep.",
                   "The hound barks a second time, nearer.",
                   "The third bark!"],
        'safe_line': "Stone stands between you and the Cu-Sith: it falls silent.",
    },
    lore=("Highlanders said the cu-sith, the fairy hound, was as big as a yearling bullock, dark "
          "green and shaggy, with a long tail plaited flat on its back and paws as broad as a man's "
          "hand. It hunted in silence. When it chose to, it barked three times with long pauses "
          "between, and anyone who heard the first bark ran for a house and barred the door, for "
          "whoever was still out in the open at the third was overtaken by terror. Down here there are "
          "no houses, but a wall is a wall, and stone between you and it is shelter enough."))

NEW['bulgasari'] = kind(
    'Bulgasari', 'B', (110, 110, 120), '26d10+99', 9, 'aggressive', 11, 18, 15, 5, 3.0,
    [atk('Iron-Eating Bite', '2d6+4', 'pierce', 'bite', 'rust', 0.2, 1),
     atk('Trunk Slam', '2d8+2', 'blunt', 'blow')],
    family='constructs', tags=['construct'], res=['cold', 'poison'], weak=['fire'],
    metal_eater={'wear_chance': 0.2, 'heal_share': 0.04, 'grow_cap': 0.12,
                 'line': "The Bulgasari's hide closes on your {weapon} and gnaws it."},
    lore=("Korean storytellers of the last Goryeo days told of a prisoner monk who shaped a little "
          "beast out of grains of rice and gave it life. It ate the needle he fed it, then every "
          "needle, spoon, ploughshare and spear in the land, and grew with every meal until no iron "
          "blade could wound it. Its name was read as 'the one that cannot be killed', though the "
          "tellers say fire was its end. The ones down here are still growing."))

NEW['vetala'] = kind(
    'Vetala', 'V', (170, 160, 140), '16d10+61', 10, 'aggressive', 11, 18, 15, 5, 3.0,
    [atk('Corpse Claws', '1d10+3', 'slash', 'blow'),
     atk('Riddling Whisper', '1d4', 'magic', 'voice', 'confused', 0.4, 5)],
    family='demons', tags=['demon'], res=['poison', 'drain', 'cold'], weak=['holy', 'fire'],
    corpse_hop={'radius': 6, 'max_hops': 2, 'hp_share': 0.4,
                'line': "The Vetala laughs as its body falls, and the corpse nearby sits up.",
                'unseen': "Somewhere close a high laugh, and a dead thing stirs."},
    lore=("In the Twenty-Five Tales of the Vetala, King Vikramaditya must carry a corpse down from a "
          "tree in a cremation ground. A vetala, a spirit that lives in dead bodies, rides inside it, "
          "and on the walk it tells a story that ends in a riddle. Each time the king answers, the "
          "vetala laughs and flies back to its tree. Down here it needs no tree: when one body falls, "
          "it slips into the nearest dead one and gets up again."))

NEW['nahual'] = kind(
    'Nahual', 'h', (170, 130, 60), '25d10+92', 12, 'ranged', 10, 21, 17, 5, 3.0,
    [atk('Sickness Hex', '1d6+2', 'magic', 'ranged', 'diseased', 0.4, 6),
     atk('Obsidian Knife', '1d6+3', 'slash', 'blow')],
    family='shapeshifters', tags=['humanoid', 'shapeshifter', 'caster'], weak=['silver'], pronoun='he',
    item=0.2, enrage_at_hp_pct=0.5, enraged_pattern='aggressive',
    enrage_message="The Nahual's eyes go yellow, and he drops into a hunter's crouch.",
    enraged_form={'attacks': [atk('Jaguar Claws', '1d8+3', 'slash', 'blow', 'bleeding', 0.3, 4),
                              atk('Skull-Piercing Bite', '2d6+3', 'pierce', 'bite')],
                  'speed': 16, 'multi_attack_count': 2,
                  'line': "Spots spread over the sorcerer's skin, and a jaguar drops to all fours!"},
    lore=("The Nahua spoke of the nahualli, a sorcerer who could put on the shape of a beast. "
          "Sahagun's informants said such a man went out by night as a jaguar, a dog or a turkey to "
          "bring sickness and ill luck on his neighbours, and came home a man before dawn. Hernando "
          "Ruiz de Alarcon heard the spells they used to call on Tezcatlipoca for the change. Wound "
          "the sorcerer badly enough and the jaguar comes out."))

NEW['likho'] = kind(
    'Likho', 'L', (90, 80, 90), '25d10+93', 10, 'aggressive', 11, 20, 17, 5, 3.0,
    [atk('Baleful Gaze', '1d4', 'magic', 'gaze', 'fumbling', 0.35, 16),
     atk('Leaping Grab', '1d6+2', 'blunt', 'grapple', 'fumbling', 0.5, 12),
     atk('Gnarled Hands', '2d6+3', 'slash', 'blow')],
    family='fair_folk', tags=['fey'], res=['cold', 'poison'], weak=['fire'], pronoun='she',
    opener=('Baleful Gaze', 3), blinded_loses=['Baleful Gaze'],
    lore=("Russian peasants were careful never to wake Likho, the one-eyed hag of ill luck. In the "
          "tale Afanasyev wrote down, a blacksmith and a tailor go looking for her out of curiosity. "
          "She eats the tailor, and the smith only escapes by burning out her single eye with a hot "
          "awl and crawling out under a sheepskin among her sheep. When Likho leaps onto a man's "
          "neck, every plan he makes goes wrong."))

NEW['centaur'] = kind(
    'Centaur', 'C', (150, 100, 60), '30d10+115', 15, 'ranged', 9, 21, 18, 5, 3.0,
    [atk('Horn Bow', '1d10+3', 'pierce', 'ranged'),
     atk('Hoof Trample', '2d6+4', 'blunt', 'trample')],
    family='legend', tags=['humanoid', 'beast'], pronoun='he', pack=(2, 3), opener=('Horn Bow', 6),
    can_charge=True, charge_bonus_mult=1.3, item=0.15,
    lore=("Homer calls the centaurs the beast-men of the mountains: man to the waist and horse below. "
          "At the wedding of the Lapith king Pirithous they drank the wine, tried to carry off the "
          "bride, and began the battle Ovid tells blow by blow, fought with tables, antlers and "
          "torches. In Dante's Hell they gallop the banks of the river of boiling blood with their "
          "bows drawn, and the archer of the zodiac is one of them. They shoot from the gallop and "
          "ride down whatever they cannot hit."))

NEW['blue_men_of_the_minch'] = kind(
    'Blue Man of the Minch', 'b', (90, 120, 190), '28d10+105', 13, 'ranged', 10, 22, 18, 5, 3.0,
    [atk('Squall Spray', '1d8+3', 'cold', 'breath', 'slowed', 0.4, 6, ranged=True),
     atk('Undertow Grab', '1d10+3', 'blunt', 'grapple', 'immobilized', 0.3, 2)],
    family='fair_folk', tags=['fey'], res=['cold', 'lightning'], weak=['fire'], pronoun='he',
    pack=(2, 3), item=0.15,
    parley={'subject': 'grammar', 'storm': 'Squall Spray',
            'call': "The Blue Men rise to the waist and their chief calls out two lines of verse. "
                    "Answer him well and they let you pass.",
            'right': "The chief of the Blue Men laughs at your answer, and they sink back into the "
                     "dark water. They will let you be.",
            'wrong': "Your answer stumbles. The Blue Men howl, and the squall comes down on you!",
            'unasked': "The Blue Men watch you from the water, waiting for an answer."},
    lore=("Between the Isle of Lewis and the Shiant Isles runs the Stream of the Blue Men, where "
          "blue-skinned, grey-faced men swim beside the boats and raise sudden gales. Their chief "
          "calls out two lines of verse to the captain. A captain who answers in rhyme, quick and "
          "well, may sail on; one who stumbles is sunk. In these drowned halls they ask the same of "
          "anyone who passes."))

NEW['vila'] = kind(
    'Vila', 'F', (230, 230, 200), '105d10+382', 15, 'ranged', 3, 45, 42, 9, 2.0,
    [atk('Throat Arrow', '2d8+10', 'pierce', 'ranged', 'silenced', 0.35, 10),
     atk('Whirlwind', '2d6+8', 'blunt', 'ranged', 'slowed', 0.4, 6)],
    family='fair_folk', tags=['fey'], res=['magic', 'cold'], weak=[], pronoun='she',
    opener=('Throat Arrow', 6), can_phase_blink=True, phase_blink_chance=0.15, item=0.2,
    lore=("In the Serbian epic songs the vila is a fairy of the mountains and the clouds, long-haired "
          "and robed in white, who shoots arrows and raises whirlwinds. The vila Ravijojla shot the "
          "hero Milos because his singing on her mountain angered her, and healed him again only when "
          "Prince Marko rode her down. Steal a vila's hair or her girdle and she must serve you. Down "
          "here nobody has stolen anything from them yet."))

NEW['myrmekes'] = kind(
    'Gold-Digging Ant', 'a', (200, 160, 60), '65d10+236', 17, 'aggressive', 5, 44, 41, 9, 2.0,
    [atk('Mandible Bite', '2d6+6', 'slash', 'bite'),
     atk('Formic Spray', '1d8+4', 'acid', 'breath', 'corroding', 0.3, 6, ranged=True)],
    family='vermin', tags=['beast'], res=['fire', 'poison'], weak=['cold'], pack=(3, 4),
    opener=('Mandible Bite', 1),
    gold_gatherer={'radius': 2, 'turns': 3,
                   'line': "The Gold-Digging Ant stops to gather up the gold."},
    lore=("Herodotus heard from the Persians of ants in the deserts of north India, smaller than dogs "
          "but bigger than foxes, that throw up gold-bearing sand as they dig. The Indians came for "
          "the gold at midday, when the heat drove the ants underground, filled their sacks and rode "
          "off at once, for the ants follow a thief by scent and run faster than any beast. Scholars "
          "today think the tale began with the marmots of the Himalaya. These are not marmots."))

NEW['ponaturi'] = kind(
    'Ponaturi', 'g', (170, 200, 190), '116d10+425', 13, 'aggressive', 4, 46, 42, 9, 2.0,
    [atk('Bone Club', '2d10+12', 'blunt', 'blow'),
     atk('Sea-Spear', '2d8+10', 'pierce', 'blow')],
    family='goblinkin', tags=['humanoid'], res=['cold', 'poison'], weak=['fire'], pronoun='he',
    pack=(2, 4), opener=('Sea-Spear', 1), light_shy=True,
    lore=("The Maori tell of the Ponaturi, a hostile people who live in a land under the sea and "
          "come ashore at night to sleep in their great house, Manawa-tane. The Ponaturi killed "
          "Tawhaki's father and kept his mother to watch the door. Tawhaki and his mother stopped "
          "every chink of the house, so the Ponaturi slept on into the morning, then threw the door "
          "open. The sunlight killed them where they lay."))

NEW['taniwha'] = kind(
    'Taniwha', 'S', (60, 100, 90), '242d10+892', 11, 'aggressive', 4, 47, 43, 9, 2.0,
    [atk('Gulping Jaws', '3d10+15', 'pierce', 'bite',
         hold={'kind': 'swallow', 'share': 0.04, 'type': 'acid', 'break_share': 0.15,
               'break_chain': 8, 'max_turns': 4, 'save': 'STR'}),
     atk('Tail Lash', '3d8+12', 'blunt', 'sting', 'stunned', 0.25, 2)],
    family='serpents', tags=['beast', 'reptile'], res=['cold'], weak=['fire'],
    opener=('Gulping Jaws', 1),
    lore=("Many taniwha of the Maori are guardians of a river or a tribe, but some ate people. "
          "Tutaeporoporo of the Whanganui River swallowed travellers and whole canoes, until the "
          "warrior Ao-kehu hid in a hollow log, let the taniwha swallow it, and cut his way out from "
          "inside. Another, Ngarara Huarau, was lured from its cave and burned. The taniwha that lie "
          "in these flooded deeps guard nothing but themselves."))

NEW['impundulu'] = kind(
    'Impundulu', 'B', (40, 40, 40), '141d10+516', 16, 'hit_and_run', 3, 48, 44, 9, 2.0,
    [atk('Lightning Stoop', '3d8+12', 'lightning', 'blow', 'stunned', 0.3, 2),
     atk('Blood-Drinking Bite', '2d8+10', 'drain', 'bite')],
    family='birds', tags=['beast'], res=['lightning', 'poison'], weak=['fire'],
    opener=('Lightning Stoop', 1), drain_heals_self=0.5,
    lore=("In Zulu and Xhosa belief the impundulu, the lightning bird, is a black-and-white bird as "
          "tall as a man that strikes the earth as lightning. It is a witch's servant, handed down from "
          "mother to daughter, and it hungers for blood. Spears and guns do not harm it, and it cannot "
          "be drowned or poisoned, but fire destroys it. Its fat, dug from the place where lightning "
          "struck, is a powerful medicine."))

NEW['mapinguari'] = kind(
    'Mapinguari', 'Y', (150, 80, 50), '236d10+862', 9, 'aggressive', 4, 49, 45, 9, 2.0,
    [atk('Hooked Claws', '3d8+12', 'slash', 'blow'),
     atk('Belly Maw', '3d10+10', 'pierce', 'bite', 'bleeding', 0.3, 5)],
    family='great_beasts', tags=['beast'], weak=['fire'], multi_attack_count=2,
    aura={'kind': 'stench', 'radius': 1, 'effect': 'weakened', 'chance': 0.35, 'turns': 4,
          'save': 'CON', 'line': "The reek of the Mapinguari turns your stomach."},
    weak_spot_chain=10,
    weak_spot_line="Your blow finds the soft place at the Mapinguari's navel!",
    lore=("Rubber-tappers and the peoples of the Amazon speak of the mapinguari: a tall, shaggy beast "
          "with one eye, feet turned backward, and a mouth in its belly. A stench like rot and dung "
          "rolls ahead of it and leaves hunters dizzy and sick. Its hide turns arrows and knives "
          "everywhere except at the navel. The biologist David Oren wondered whether the tales "
          "remember the giant ground sloths that lived here at the end of the Ice Age."))

NEW['preta'] = kind(
    'Preta', 'G', (160, 150, 140), '131d10+480', 12, 'aggressive', 4, 50, 46, 9, 2.0,
    [atk('Hungry Touch', '2d8+10', 'drain', 'touch', steal='offering', steal_chance=0.3),
     atk('Needle-Throat Wail', '1d8+4', 'magic', 'voice', 'weakened', 0.4, 12)],
    family='ghosts', tags=['undead'], res=['cold', 'drain'], weak=['holy', 'fire'], sp_drain=15,
    appeased_by={'food': 'plain',
                 'line': "The Preta falls on your offering, and for a while its hunger is quiet."},
    lore=("Buddhists and Hindus tell of the preta, the hungry ghost: a spirit of greed with a belly "
          "like a drum and a throat as thin as a needle, so that nothing it eats can fill it, and "
          "food turns to fire in its mouth. In the Ullambana story the monk Maudgalyayana found his "
          "own mother among them. Offerings of food, freely given, are the old way to ease a preta, "
          "and every year the Ghost Festival sets out a meal for them."))

NEW['upas_tree'] = kind(
    'Upas Tree', 'T', (200, 200, 170), '254d10+927', 0, 'sessile', 6, 52, 48, 9, 2.0,
    [atk('Ipoh Sap', '2d8+8', 'poison', 'ranged', 'poisoned', 0.5, 8),
     atk('Root Wrap', '3d8+10', 'blunt', 'grapple', 'immobilized', 0.35, 2)],
    family='plants', tags=['plant'], res=['poison'], weak=['fire'], opener=('Ipoh Sap', 5), item=0.25,
    aura={'kind': 'stench', 'radius': 2, 'effect': 'poisoned', 'chance': 0.4, 'turns': 4,
          'save': 'CON', 'line': "The air round the Upas Tree burns in your throat."},
    lore=("In 1783 the London Magazine printed a Dutch surgeon's tale of the upas tree of Java, whose "
          "poison killed every living thing for fifteen miles, so that condemned criminals were sent "
          "to fetch its sap and few came back. The story was a tall one, but the tree is real: its "
          "milky latex is the ipoh poison that island hunters put on their blowgun darts. The upas "
          "trees of the deep need no tall tale."))

NEW['nuckelavee'] = kind(
    'Nuckelavee', 'N', (150, 50, 50), '248d10+908', 15, 'aggressive', 3, 53, 48, 9, 2.0,
    [atk('Mortasheen Breath', '2d8+10', 'poison', 'breath', 'diseased', 0.5, 8),
     atk('Long Arms', '3d8+14', 'slash', 'blow'),
     atk('Hoof Trample', '3d10+14', 'blunt', 'trample')],
    family='demons', tags=['demon'], res=['poison', 'cold'], weak=['holy'],
    opener=('Mortasheen Breath', 3), can_charge=True, charge_bonus_mult=1.3, moves=[],
    lore=("Orkney islanders would not say its name. The nuckelavee came out of the sea as a horse and "
          "rider grown into one body, with no skin, so that black blood could be seen running in its "
          "veins. Its breath withered crops and brought the mortasheen plague on the cattle. Walter "
          "Traill Dennison heard from an old man, Tammas, how it chased him along the shore one "
          "night, and how he escaped by leaping a burn of fresh water, which it cannot cross."))

NEW['star_jelly'] = kind(
    'Star Jelly', 'J', (220, 220, 240), '253d10+924', 6, 'ambush', 6, 55, 50, 9, 2.0,
    [atk('Starfall Drop', '3d10+12', 'blunt', 'blow', 'corroding', 0.5, 6),
     atk('Starlight Touch', '2d6+8', 'cold', 'touch', 'slowed', 0.4, 6)],
    family='oozes', tags=['aberration'], res=['acid', 'cold'], weak=['fire'], opener=('Starfall Drop', 1),
    light_shy=True, hidden_overhead=True,
    lore=("Welsh shepherds called it pwdre ser, the rot of the stars: a pale, trembling jelly found "
          "on the grass after a night of falling stars, which melts away within days. Medieval "
          "physicians spread it on sores. Naturalists today blame frog spawn or a swollen soil alga. "
          "The jelly that drops from the roofs down here comes from nothing so ordinary, and it "
          "shrinks from any light."))

NEW['psoglav'] = kind(
    'Psoglav', 'P', (110, 90, 70), '266d10+973', 13, 'aggressive', 2, 62, 58, 9, 2.0,
    [atk('Iron-Toothed Bite', '3d8+16', 'pierce', 'bite', 'bleeding', 0.35, 5),
     atk('Horse-Leg Kick', '3d6+14', 'blunt', 'blow', 'stunned', 0.25, 2)],
    family='goblinkin', tags=['humanoid'], res=['cold'], weak=['fire'], pronoun='he', pack=(2, 3),
    opener=('Iron-Toothed Bite', 1), perception_range=5, item=0.2,
    lore=("In the villages of Bosnia, Montenegro and Serbia they told of the psoglavci, the dog-heads: "
          "men with horse's legs, a dog's head, iron teeth and a single eye in the middle of the "
          "forehead. They live in caves in a land without sun, where precious stones light the dark. "
          "Their one eye sees poorly but their noses miss nothing, and they dig the dead out of their "
          "graves to eat them."))

NEW['waq_waq_tree'] = kind(
    'Waq-Waq Tree', 'T', (120, 150, 90), '360d10+1318', 0, 'sessile', 3, 63, 58, 9, 2.0,
    [atk('Screaming Chorus', '2d6+10', 'magic', 'voice', 'feared', 0.4, 4),
     atk('Falling Fruit', '3d8+14', 'blunt', 'ranged')],
    family='plants', tags=['plant'], res=['poison'], weak=['fire'], opener=('Screaming Chorus', 6),
    # Everything near comes to hear it (AI-1's alarm rouses only its own side,
    # the plants, unless `tags` names more): the living that hear, at a
    # capped reach (A's risk note).
    alarm={'radius': 10,
           'tags': ['humanoid', 'beast', 'reptile', 'aberration', 'fey', 'giant', 'demon',
                    'dragon', 'shapeshifter', 'goblinoid'],
           'line': "Every head on the Waq-Waq Tree cries out at once: 'Waq! Waq!'",
           'line_unseen': "Somewhere ahead, a chorus of voices cries 'Waq! Waq!'"},
    lore=("Arab and Persian wonder-books tell of the island of Waq-waq at the edge of the world, where "
          "a tree bears fruit in the shape of people. When the fruit ripens it falls, crying 'waq, "
          "waq!'. Later painters gave the tree branches that end in the heads of men and beasts, all "
          "calling at once. A waq-waq tree in the dark cries out at anything that moves, and "
          "everything nearby comes to hear it."))

NEW['yuki_onna'] = kind(
    'Yuki-Onna', 'F', (230, 240, 255), '281d10+1034', 13, 'ranged', 1, 66, 62, 9, 2.0,
    [atk('Freezing Breath', '2d10+16', 'cold', 'breath', 'frozen', 0.45, 3, ranged=True),
     atk('Pale Touch', '3d8+14', 'drain', 'touch')],
    family='fair_folk', tags=['fey'], res=['cold'], weak=['fire'], pronoun='she',
    opener=('Freezing Breath', 4), can_phase_blink=True, phase_blink_chance=0.2, item=0.15,
    lore=("Lafcadio Hearn wrote down the tale of the snow woman: two woodcutters sheltering in a hut "
          "through a blizzard, and a woman in white who breathes on the old man until he freezes. She "
          "spares the young one, Minokichi, and makes him promise never to tell. Years later he tells "
          "his wife the story, and his wife is the snow woman. For their children's sake she does not "
          "kill him; she melts away into the mist instead."))

NEW['yacumama'] = kind(
    'Yacumama', 'S', (50, 80, 50), '699d10+2562', 9, 'ambush', 1, 70, 65, 9, 2.0,
    [atk('Drawing Breath', '1d6+6', 'magic', 'breath', 'slowed', 0.4, 6, ranged=True, pulls=2,
         pull_line="The Yacumama breathes in, and the air drags you toward its coils!"),
     atk('Crushing Coils', '4d10+20', 'blunt', 'grapple', 'strangulation', 0.35, 3),
     atk('Gaping Jaws', '4d8+20', 'pierce', 'bite')],
    family='serpents', tags=['beast', 'reptile'], res=['cold', 'poison'], weak=['fire'],
    opener=('Drawing Breath', 5),
    lore=("The peoples of the Peruvian Amazon speak of the yacumama, the mother of the waters: an "
          "anaconda fifty yards long that lies in the deep pools at a river's head. The Nuttall "
          "Encyclopaedia of 1907 says it draws in any creature that comes within a hundred yards, as "
          "if the river itself were breathing in. Fishermen blew a conch before they waded in, so "
          "that the yacumama would show itself if it was there."))

NEW['tsuchigumo'] = kind(
    'Tsuchigumo', 'X', (120, 100, 60), '714d10+2621', 11, 'ambush', 0, 72, 67, 9, 2.0,
    [atk('Fever Curse', '2d8+14', 'magic', 'voice', 'weakened', 0.5, 20),
     atk('Web Cast', '2d6+12', 'magic', 'ranged', 'immobilized', 0.45, 2),
     atk('Earth Spider Fangs', '4d10+22', 'poison', 'bite', 'poisoned', 0.4, 8)],
    family='vermin', tags=['beast'], res=['poison'], weak=['fire'], opener=('Web Cast', 4), item=0.25,
    relurks=True,
    lore=("The Heike tells how the warrior Minamoto no Raiko lay sick with a fever no medicine could "
          "break, and how a strange monk, taller than any man, came to his bedside at night and tried "
          "to bind him with rope. Raiko slashed at him with his sword, and the next day his men "
          "followed a trail of blood to a mound behind the Kitano Shrine, where a great earth spider "
          "lay. In the picture scroll of the Tsuchigumo, when another was cut open, one thousand nine "
          "hundred and ninety skulls rolled out of its belly."))

NEW['bhuta_vahana_yanta'] = kind(
    'Relic Guardian', 'G', (190, 150, 90), '863d10+3168', 8, 'sessile', -2, 83, 78, 12, 2.0,
    [atk('Whirling Swords', '3d8+18', 'slash', 'blow'),
     atk('Whirling Swords Backstroke', '3d8+18', 'slash', 'blow'),
     atk('Whirling Swords Low Cut', '3d8+18', 'slash', 'blow', 'bleeding', 0.3, 5)],
    family='constructs', tags=['construct'], res=['poison', 'cold', 'fire'], weak=['lightning'],
    pack=(2, 2), multi_attack_count=3, item=0.3,
    lore=("The Pali Lokapannatti tells how King Ajatashatru laid the Buddha's relics in a deep "
          "chamber and set spirit-driven machines to guard them, the bhuta vahana yanta, built from "
          "plans brought out of the land of the Romans. No one could pass them until the emperor "
          "Ashoka, long after, learned their secret and stilled them. The machines down here still "
          "keep their watch, and their swords never stop turning."))

NEW['reem'] = kind(
    "Re'em", 'Q', (80, 60, 40), '1205d10+4417', 13, 'aggressive', -2, 85, 80, 12, 2.0,
    [atk("Horns of the Re'em", '5d10+40', 'pierce', 'blow', 'stunned', 0.3, 2),
     atk('Hill-Shaking Trample', '5d8+36', 'blunt', 'trample')],
    family='great_beasts', tags=['beast'], opener=("Horns of the Re'em", 1), can_charge=True,
    charge_bonus_mult=1.5, footprint=[2, 2],
    lore=("The Hebrew Bible's re'em is a wild ox of terrible strength; Job is asked whether it will "
          "ever serve him or harrow his valleys, and the King James translators called it the "
          "unicorn. The rabbis said it was too big for Noah's ark, and puzzled over how it was saved. "
          "A midrash tells how young David took a sleeping re'em for a hill, climbed it, and was "
          "carried up toward the sky on its horns when it woke. The re'em of the deep halls are "
          "awake."))

NEW['eitr'] = kind(
    'Eitr', 'P', (40, 90, 70), '863d10+3163', 7, 'aggressive', 0, 86, 81, 12, 2.0,
    [atk('Venom-Rime Touch', '4d10+30', 'poison', 'touch', 'poisoned', 0.5, 8),
     atk('Freezing Slag', '3d10+26', 'cold', 'blow', 'frozen', 0.35, 2)],
    family='oozes', tags=['aberration'], res=['poison', 'cold', 'acid'], weak=['fire'],
    trail_hazard={'hazard': 'venom_pool', 'turns': 20},
    lore=("Snorri tells that in the beginning poisonous rivers, the Elivagar, flowed out of the "
          "wellspring in Niflheim. Their venom, the eitr, hardened like slag from a furnace and spread "
          "through the void as rime, and where that rime met the heat of Muspell the first giant, "
          "Ymir, was born. Some of the eitr never hardened. It still crawls in the deepest cold, and "
          "what it touches freezes and sickens at once."))

NEW['bakunawa'] = kind(
    'Bakunawa', 'S', (60, 40, 80), '1290d10+4730', 12, 'aggressive', -3, 88, 84, 12, 2.0,
    [atk('Moon-Swallowing Jaws', '4d10+30', 'magic', 'bite', 'blinded', 0.4, 8, snuffs_light='dark',
         snuff_chance=0.5),
     atk('Coiling Crush', '5d10+36', 'blunt', 'grapple', 'immobilized', 0.3, 2),
     atk('Horned Strike', '4d8+34', 'pierce', 'blow')],
    family='serpents', tags=['beast', 'reptile'], res=['cold', 'lightning'], weak=['fire'],
    lore=("The Visayan peoples of the Philippines say the god Bathala hung seven moons in the sky, and "
          "the sea serpent Bakunawa rose and swallowed six of them. When it rises for the last moon, "
          "Bulan, the people run outside and beat pots, gongs and drums until the noise makes it spit "
          "the moon back out. That is what an eclipse is. The bakunawa coiled in these deeps swallows "
          "any light it sees."))

# Their family_affinity.json `kinds` entries (the affinity pass writes each
# kind's five lists from these: tools/content/affinity_pass.py). `form`
# only where the creature differs from its family; status from its lore.
AFFINITY = {
    'mandrake': {'lore': "A root has no mind to frighten or charm, and it never sleeps; its sap is a "
                         "soporific, not a poison to it.",
                 'source': "Theophrastus, Historia Plantarum 9.8; Dioscorides on the root boiled in wine.",
                 'status_immune': ['sleeping', 'confused', 'charmed', 'feared', 'blinded']},
    'kappa': {'lore': "Knock a kappa senseless and the water spills from its dish: a stun is its "
                      "undoing.", 'source': "Yanagita Kunio, Tono Monogatari (1910), tales 55-59.",
              'status_weak': ['stunned']},
    'eloko': {'lore': "The biloko are spirits of the forest: no sleep for them.",
              'source': "Mongo-Nkundo tales (Gustaaf Hulstaert).", 'status_immune': ['sleeping']},
    'asanbosam': {'lore': "A thing of the high branches with iron teeth; no charm turns it.",
                  'source': "Akan folklore; Edward Long, The History of Jamaica (1774).",
                  'status_immune': ['charmed']},
    'ahuizotl': {'lore': "A lake beast with a child's cry and a hand on its tail: flesh and blood, "
                         "and nothing stranger.", 'source': "Sahagun, Florentine Codex, Book 11.",
                 'status_immune': []},
    'khalkotauros': {'lore': "Bronze made by Hephaestus breathes fire and cannot burn; a blade "
                             "glances off the plates, but a hammer dents them.",
                     'source': "Apollonius of Rhodes, Argonautica 3.1278-1407.",
                     'status_immune': ['burning', 'poisoned', 'sleeping', 'charmed', 'feared', 'confused']},
    'cu_sith': {'lore': "The fairy hound never sleeps on the hunt and no charm turns it.",
                'source': "J. G. Campbell, Superstitions of the Highlands and Islands of Scotland (1900).",
                'status_immune': ['sleeping', 'charmed']},
    'bulgasari': {'lore': "A beast grown from rice and iron: a blade sinks into the metal of its hide "
                          "and is eaten; a hammer still bruises it.",
                  'source': "Jo Jae-sam, Songnam Japji; the Encyclopedia of Korean Culture.",
                  'status_immune': ['poisoned', 'sleeping', 'charmed', 'feared', 'confused']},
    'vetala': {'lore': "A spirit in a dead body feels no fear, no sleep and no poison.",
               'source': "Somadeva, Kathasaritsagara (the Vetala Panchavimshati).",
               'status_immune': ['sleeping', 'poisoned', 'charmed', 'feared']},
    'nahual': {'lore': "A man under the skin: what frightens a man frightens him.",
               'source': "Sahagun, Florentine Codex, Book 10.", 'status_immune': []},
    'likho': {'lore': "Likho has one eye: put it out, as the smith did, and she is helpless.",
              'source': "Afanasyev, Narodnye russkie skazki, 'Likho One-Eyed'.",
              'status_immune': ['sleeping'], 'status_weak': ['blinded']},
    'centaur': {'lore': "Wild horse-men, fearless in battle, and wine sends them reeling: the "
                        "Lapith wedding began when they drank it.",
                'source': "Ovid, Metamorphoses 12.210-535.",
                'status_immune': ['feared'], 'status_weak': ['confused']},
    'blue_men_of_the_minch': {'lore': "Sea-men of the fair folk who raise the gales: no sleep takes "
                                      "them.", 'source': "J. G. Campbell (1900).",
                              'status_immune': ['sleeping']},
    'vila': {'lore': "A fairy of the clouds: no sleep, no charm.",
             'source': "Vuk Karadzic, Srpske narodne pjesme (1841-62).",
             'status_immune': ['sleeping', 'charmed']},
    'myrmekes': {'lore': "Desert ants that dig all day: a cold night slows them, a hammer cracks "
                         "their shells.", 'source': "Herodotus, Histories 3.102-105.",
                 'form': {'blunt': 'weak'}, 'status_immune': ['sleeping']},
    'ponaturi': {'lore': "A people of the dark under the sea: the light that killed them in Tawhaki's "
                         "tale dazzles them.", 'source': "Sir George Grey, Polynesian Mythology (1855).",
                 'status_immune': [], 'status_weak': ['blinded']},
    'taniwha': {'lore': "A water-dragon whose scaled hide turns a thrust; no sleep for a guardian.",
                'source': "Te Ara, the Encyclopedia of New Zealand: 'Taniwha'.",
                'form': {'pierce': 'resist'}, 'status_immune': ['sleeping']},
    'impundulu': {'lore': "Spears and guns do not harm the lightning bird, and it cannot be poisoned; "
                          "fire destroys it.",
                  'source': "Axel-Ivar Berglund, Zulu Thought-Patterns and Symbolism (1975).",
                  'form': {'slash': 'resist', 'pierce': 'resist', 'blunt': 'resist'},
                  'status_immune': ['poisoned']},
    'mapinguari': {'lore': "Its hide turns arrows and knives everywhere but at the navel; its own "
                           "stench does not trouble it.", 'source': "David Oren, Ciencia Hoje (1993).",
                   'form': {'slash': 'resist', 'pierce': 'resist', 'blunt': 'resist'},
                   'status_immune': ['poisoned', 'confused']},
    'preta': {'lore': "A hungry ghost has no sleep and no blood for poison, and nothing charms it "
                      "but food.", 'source': "The Petavatthu; the Ullambana Sutra.",
              'status_immune': ['sleeping', 'poisoned', 'charmed']},
    'upas_tree': {'lore': "A tree that poisons the air is proof against poison, and a tree does "
                          "not fear or sleep.", 'source': "Erasmus Darwin, The Loves of the Plants (1789).",
                  'form': {'slash': 'weak', 'pierce': 'resist'},
                  'status_immune': ['sleeping', 'poisoned', 'confused', 'charmed', 'feared', 'blinded']},
    'nuckelavee': {'lore': "The demon of the Orkney shore fears nothing but fresh water.",
                   'source': "Walter Traill Dennison, The Scottish Antiquary (1891).",
                   'status_immune': ['sleeping', 'feared']},
    'star_jelly': {'lore': "A trembling jelly with no eyes, no mind and no blood.",
                   'source': "John of Gaddesden, Rosa Anglica (c. 1314).",
                   'status_immune': ['blinded', 'sleeping', 'confused', 'feared', 'charmed', 'poisoned']},
    'psoglav': {'lore': "Its one eye sees poorly in any case: blinding it does nothing.",
                'source': "Tihomir Djordjevic (1953); Srpski mitoloski recnik (1970).",
                'status_immune': ['blinded']},
    'waq_waq_tree': {'lore': "A tree of heads that cry: it does not sleep, fear or see as we do.",
                     'source': "The Arabic and Persian wonder-books; al-Qazwini, 'Aja'ib al-makhluqat.",
                     'form': {'slash': 'weak', 'pierce': 'resist'},
                     'status_immune': ['sleeping', 'poisoned', 'charmed', 'feared', 'blinded']},
    'yuki_onna': {'lore': "The snow woman cannot be frozen, and her blizzard never sleeps; a "
                          "blade passes through her like snow.", 'source': "Lafcadio Hearn, Kwaidan (1904).",
                  'form': {'slash': 'resist', 'pierce': 'resist'},
                  'status_immune': ['frozen', 'sleeping', 'charmed']},
    'yacumama': {'lore': "The mother of the waters never sleeps in her pool.",
                 'source': "The Nuttall Encyclopaedia (1907): 'Yacu-mama'.",
                 'status_immune': ['sleeping']},
    'tsuchigumo': {'lore': "A swollen hairy body that shrugs off a club; a sword cut it down.",
                   'source': "The Heike Monogatari, Tsurugi no maki.",
                   'form': {'blunt': 'resist', 'slash': 'weak'}, 'status_immune': ['sleeping']},
    'bhuta_vahana_yanta': {'lore': "Machines of bronze and wood driven by spirits: no mind, no "
                                   "blood, no sleep, no eyes to blind.",
                           'source': "The Pali Lokapannatti (c. 11th-12th century).",
                           'status_immune': ['sleeping', 'poisoned', 'charmed', 'feared', 'confused',
                                             'paralyzed', 'stunned', 'blinded']},
    'reem': {'lore': "A wild ox as big as a hill fears nothing that walks.",
             'source': "Job 39:9-12; the King James 'unicorn'.", 'status_immune': ['feared']},
    'eitr': {'lore': "The first poison of the world: it cannot be poisoned or frozen.",
             'source': "Snorri Sturluson, Prose Edda, Gylfaginning 5.",
             'status_immune': ['frozen', 'poisoned', 'sleeping', 'blinded', 'confused', 'charmed', 'feared']},
    'bakunawa': {'lore': "A serpent that swallows moons is not blinded by any light.",
                 'source': "Alonso de Mentrida (1637); Fernando Buyser (1913).",
                 'status_immune': ['sleeping', 'blinded']},
}

SIZES = {
    'mandrake': 'tiny', 'kappa': 'small', 'eloko': 'small', 'asanbosam': 'medium', 'ahuizotl': 'small',
    'khalkotauros': 'large', 'cu_sith': 'large', 'bulgasari': 'large', 'vetala': 'medium',
    'nahual': 'medium', 'likho': 'medium', 'centaur': 'large', 'blue_men_of_the_minch': 'medium',
    'vila': 'medium', 'myrmekes': 'small', 'ponaturi': 'medium', 'taniwha': 'huge',
    'impundulu': 'medium', 'mapinguari': 'huge', 'preta': 'medium', 'upas_tree': 'huge',
    'nuckelavee': 'large', 'star_jelly': 'large', 'psoglav': 'medium', 'waq_waq_tree': 'large',
    'yuki_onna': 'medium', 'yacumama': 'huge', 'tsuchigumo': 'huge', 'bhuta_vahana_yanta': 'large',
    'reem': 'huge', 'eitr': 'large', 'bakunawa': 'huge',
}

# How each knows where the hero is (data/senses.json; a kind's own list
# replaces its family's). Ants and dog-heads by nose, far; the fairy hound by
# nose like any hound.
SENSES = {'cu_sith': ['scent'], 'myrmekes': ['scent'], 'psoglav': ['scent']}
SENSE_RANGES = {'myrmekes': {'scent': 12}, 'psoglav': {'scent': 12}}

# Harvest: a distinctive creature gets its own part; close kin share one by
# lore; a person is searched (harvest_map.json "people").
HARVEST_SHARE = {
    # (Tier 1 kinds take a tier 1 part: Hecate's hounds of the underworld for
    # the fairy hound, the banshee's omen of doom for ill luck itself, the
    # nosferatu's blood-marrow for the tree-vampire. No tier 3 tree, tier 4
    # spider or tier 5 construct part exists: the upas, the tsuchigumo and
    # the relic guardians keep their kin's.)
    'cu_sith': 'hecate_hound_prime', 'khalkotauros': 'talos_prime', 'likho': 'banshee_prime',
    'asanbosam': 'nosferatu_prime', 'nuckelavee': 'hezrou_prime', 'upas_tree': 'corrupted_treant_prime',
    'tsuchigumo': 'giant_spider_prime', 'bhuta_vahana_yanta': 'iron_sentinel_prime',
    'eitr': 'plague_ooze_prime',
}
PEOPLE = ('vetala', 'nahual', 'centaur', 'blue_men_of_the_minch', 'ponaturi', 'psoglav', 'yuki_onna')
