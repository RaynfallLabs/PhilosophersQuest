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
    lore=("Theophrastus tells that the cutters of roots drew circles about a mandrake with a sword before they dug, and the herbals of later days add that it screams when it is torn from the earth, and that its cry kills all who hear. The wise would therefore tie a hungry dog to the root and walk away holding meat. Physicians boiled the forked root in wine, that a patient might sleep before the knife. Down here the roots have drawn themselves up on legs of their own, and they scream still when they die."))

NEW['kappa'] = kind(
    'Kappa', 'k', (90, 150, 80), '8d10+28', 12, 'aggressive', 13, 11, 9, 5, 3.0,
    [atk('Beak Bite', '1d6+2', 'pierce', 'bite'),
     atk('Sumo Grapple', '1d6+1', 'blunt', 'grapple', 'immobilized', 0.35, 2)],
    family='serpents', tags=['reptile'], res=['cold'], weak=['fire', 'iron'], opener=('Sumo Grapple', 1),
    on_stunned={'effect': 'weakened', 'turns': 12,
                'line': "The water spills from the Kappa's dish, and its arms go slack."},
    appeased_by={'food': 'plain',
                 'line': "The Kappa takes your offering, bows low, and goes back to its pool."},
    lore=("Children in the villages of Japan were kept from deep pools for fear of the kappa, a little water-imp with a beak and a shell and a dish of water set into the crown of its head. It drags swimmers and horses under and challenges travellers to wrestle, but it is exceedingly courteous. If you bow to a kappa it must bow in return, and as the water spills from its dish its strength drains away with it. Farmers floated cucumbers down the rivers to keep it friendly, and a kappa that is given a gift of food will leave the giver alone."))

NEW['eloko'] = kind(
    'Eloko', 'e', (110, 150, 60), '7d10+27', 12, 'hit_and_run', 13, 13, 11, 5, 3.0,
    [atk('Bell Charm', '1d3', 'magic', 'voice', 'paralyzed', 0.35, 2),
     atk('Wide Jaws', '1d8+2', 'pierce', 'bite')],
    family='fair_folk', tags=['fey'], res=['poison'], weak=['fire'], pack=(2, 3), opener=('Bell Charm', 4),
    lore=("The Mongo people of the Congo forest tell of the biloko, small and hungry spirits that dwell in hollow trees, having grass for hair and leaves for raiment, and mouths that open wide enough to swallow a man's head. Each carries a little bell, and so sweet is its chime that a hunter forgets whither he was going and walks toward it, until he cannot move at all. Hunters in that forest wore charms to hide themselves, but a hunter in these depths must stop his ears against the bell."))

NEW['asanbosam'] = kind(
    'Asanbosam', 'V', (120, 90, 70), '13d10+44', 12, 'ambush', 11, 14, 11, 5, 3.0,
    [atk('Dangling-Leg Grab', '1d8+2', 'blunt', 'grapple', 'immobilized', 0.5, 2),
     atk('Iron-Toothed Bite', '1d10+3', 'drain', 'bite')],
    family='vampires_liches', tags=['undead'], res=['cold', 'poison'], weak=['fire', 'holy'],
    opener=('Dangling-Leg Grab', 1), drain_heals_self=0.5, hidden_overhead=True, relurks=True,
    lore=("High in the trees of the Ghanaian forest lived the sasabonsam that Akan hunters feared, long of leg, with teeth of iron, long matted hair, and feet that point both ways. It loved best to sit upon a high branch dangling its legs, that it might snare a hunter who walked beneath and haul him up among the leaves. Enslaved Akan people carried the tale across the sea, and in 1774 Edward Long set it down in Jamaica. Down here it hangs from the roof beams and the roots of the old halls, and nothing but a light will show it to you."))

NEW['ahuizotl'] = kind(
    'Ahuizotl', 'a', (40, 50, 60), '11d10+45', 14, 'ambush', 10, 16, 13, 5, 3.0,
    [atk("Child's Wail", '1d3', 'magic', 'voice', 'confused', 0.4, 4),
     atk('Hidden Hand Grab', '1d6+2', 'blunt', 'grapple', 'immobilized', 0.45, 2),
     atk('Drowning Squeeze', '1d8+3', 'blunt', 'grapple', 'strangulation', 0.3, 3)],
    family='serpents', tags=['beast'], res=['cold'], weak=['fire'], opener=("Child's Wail", 5),
    pull_chance=0.3, relurks=True,
    lore=("Sahagun learned from his Aztec informants of the ahuizotl of the lakes, a sleek little water beast like a dog, which had the hands of a monkey and one hand more at the very end of its tail. When it had not fed it would cry like a child upon the shore, or make the fish leap to draw the fishermen close, and then the hand on its tail seized them and dragged them under. Days afterward the drowned were found, and none but a priest dared touch them."))

NEW['khalkotauros'] = kind(
    'Khalkotauros', 'q', (190, 140, 70), '22d10+80', 12, 'aggressive', 11, 17, 15, 5, 3.0,
    [atk('Bronze Gore', '2d8+4', 'pierce', 'trample'),
     atk('Furnace Breath', '2d6', 'fire', 'breath', 'burning', 0.4, 4)],
    family='constructs', tags=['construct'], res=['fire', 'poison'], weak=['cold'], pack=(2, 2),
    opener=('Furnace Breath', 3), can_charge=True, charge_bonus_mult=1.3,
    lore=("For Aeetes, the king of Colchis, Hephaestus forged two bulls of bronze with brazen hooves and mouths that breathed fire, and the king set Jason to yoke them and plough the field of Ares in a single day. Medea gave the hero an ointment that kept fire and bronze from his skin for that one day, and so he forced them to their knees. But the pairs that stamp through these halls have never in all their days submitted to a yoke."))

NEW['cu_sith'] = kind(
    'Cu-Sith', 'd', (60, 110, 70), '20d10+74', 16, 'aggressive', 10, 17, 14, 5, 3.0,
    [atk('Silent Bite', '2d6+3', 'pierce', 'bite')],
    family='fair_folk', tags=['beast'], res=['cold'], weak=['iron'],
    countdown_voice={
        'every': 3, 'count': 3,
        'attack': atk('Third Bark', '1d4', 'magic', 'voice', 'feared', 0.6, 4),
        'lines': ["The Cu-Sith barks once, and the sound rolls through the halls.",
                  "The Cu-Sith barks a second time. Get out of its sight!",
                  "The Cu-Sith barks the third time!"],
        'unseen': ["Somewhere out of sight a great hound barks once, slow and deep.",
                   "The hound barks a second time, nearer.",
                   "The third bark!"],
        'safe_line': "Stone stands between you and the Cu-Sith, and it falls silent.",
    },
    lore=("As big as a yearling bullock was the cu-sith, the hound of the fairies, so the Highlanders said, dark green and shaggy, with paws as broad as a man's hand and a long tail plaited flat upon its back. It hunted in silence, but when it chose it would bark three times with long pauses between. Whoever heard the first bark ran for a house and barred the door, for terror overtook all who were still in the open at the third. There are no houses in these depths, yet any wall will serve as well, and stone between you and the hound is shelter enough."))

NEW['bulgasari'] = kind(
    'Bulgasari', 'B', (110, 110, 120), '26d10+99', 9, 'aggressive', 11, 18, 15, 5, 3.0,
    [atk('Iron-Eating Bite', '2d6+4', 'pierce', 'bite', 'rust', 0.2, 1),
     atk('Trunk Slam', '2d8+2', 'blunt', 'blow')],
    family='constructs', tags=['construct'], res=['cold', 'poison'], weak=['fire'],
    metal_eater={'wear_chance': 0.2, 'heal_share': 0.04, 'grow_cap': 0.12,
                 'line': "The Bulgasari's hide closes on your {weapon} and gnaws it."},
    lore=("A monk who lay in prison in the last days of Goryeo, so the storytellers of Korea relate, shaped a little beast out of grains of rice and gave it life. It ate the needle that he fed to it, and thereafter every needle, spoon, ploughshare and spear in the land, growing with each meal until no iron blade could wound it. Its name was read as 'the one that cannot be killed', yet the tellers say that fire was its end. Those that dwell here below are growing still upon whatever iron they find."))

NEW['vetala'] = kind(
    'Vetala', 'V', (170, 160, 140), '16d10+61', 10, 'aggressive', 11, 18, 15, 5, 3.0,
    [atk('Corpse Claws', '1d10+3', 'slash', 'blow'),
     atk('Riddling Whisper', '1d4', 'magic', 'voice', 'confused', 0.4, 5)],
    family='demons', tags=['demon'], res=['poison', 'drain', 'cold'], weak=['holy', 'fire'],
    corpse_hop={'radius': 6, 'max_hops': 2, 'hp_share': 0.4,
                'line': "The Vetala laughs as its body falls, and the corpse nearby sits up.",
                'unseen': "Somewhere close a high voice laughs, and a dead thing stirs."},
    lore=("It was laid upon King Vikramaditya, in the Twenty-Five Tales of the Vetala, to bear a corpse down from a tree in a cremation ground, and within it rode a vetala, which is a spirit that lives in the bodies of the dead. Upon the road it would tell a story that ended in a riddle, and each time the king answered, it laughed and flew back to its tree. Down here it has no need of a tree, for when one body falls it slips into the nearest dead one and rises up again."))

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
    lore=("Among the Nahua a sorcerer who could put on the shape of a beast was called nahualli. The informants of Sahagun said that such a man went abroad by night as a jaguar, a dog or a turkey to bring sickness and ill luck upon his neighbours, and came home a man before the dawn, and Hernando Ruiz de Alarcon heard the spells by which they called upon Tezcatlipoca for the change. If the sorcerer is wounded sorely enough, the jaguar will come forth out of him."))

NEW['likho'] = kind(
    'Likho', 'L', (90, 80, 90), '25d10+93', 10, 'aggressive', 11, 20, 17, 5, 3.0,
    [atk('Baleful Gaze', '1d4', 'magic', 'gaze', 'fumbling', 0.35, 16),
     atk('Leaping Grab', '1d6+2', 'blunt', 'grapple', 'fumbling', 0.5, 12),
     atk('Gnarled Hands', '2d6+3', 'slash', 'blow')],
    family='fair_folk', tags=['fey'], res=['cold', 'poison'], weak=['fire'], pronoun='she',
    opener=('Baleful Gaze', 3), blinded_loses=['Baleful Gaze'],
    lore=("Russian peasants took great care never to waken Likho, the one-eyed hag of ill luck. Yet a blacksmith and a tailor went in search of her out of curiosity, in the tale that Afanasyev wrote down, and she devoured the tailor. The smith escaped only by burning out her single eye with a hot awl and creeping forth among her sheep beneath a sheepskin. When Likho leaps upon a man's neck, every plan that he makes thereafter goes wrong."))

NEW['centaur'] = kind(
    'Centaur', 'C', (150, 100, 60), '30d10+115', 15, 'ranged', 9, 21, 18, 5, 3.0,
    [atk('Horn Bow', '1d10+3', 'pierce', 'ranged'),
     atk('Hoof Trample', '2d6+4', 'blunt', 'trample')],
    family='legend', tags=['humanoid', 'beast'], pronoun='he', pack=(2, 3), opener=('Horn Bow', 6),
    can_charge=True, charge_bonus_mult=1.3, item=0.15,
    lore=("Men to the waist and horses below, the centaurs are named by Homer the beast-men of the mountains. At the wedding of the Lapith king Pirithous they drank the wine and would have carried off the bride, and so began the battle of which Ovid tells every blow, fought with tables, antlers and torches. In Dante's Hell they gallop with bent bows along the river of boiling blood, and one of that people is the archer of the zodiac. They shoot at the gallop, and whatever their arrows cannot hit they ride down beneath their hooves."))

NEW['blue_men_of_the_minch'] = kind(
    'Blue Man of the Minch', 'b', (90, 120, 190), '28d10+105', 13, 'ranged', 10, 22, 18, 5, 3.0,
    [atk('Squall Spray', '1d8+3', 'cold', 'breath', 'slowed', 0.4, 6, ranged=True),
     atk('Undertow Grab', '1d10+3', 'blunt', 'grapple', 'immobilized', 0.3, 2)],
    family='fair_folk', tags=['fey'], res=['cold', 'lightning'], weak=['fire'], pronoun='he',
    pack=(2, 3), item=0.15,
    parley={'subject': 'grammar', 'storm': 'Squall Spray',
            'call': "The Blue Men rise to the waist and their chief calls out two lines of verse. "
                    "Answer him well and they let you pass.",
            'right': "The chief of the Blue Men laughs at your answer, and they sink back into the dark water, content to let you be.",
            'wrong': "At your stumbling answer the Blue Men howl, and the squall comes down on you!",
            'unasked': "The Blue Men watch you from the water, waiting for an answer."},
    lore=("Between the Isle of Lewis and the Shiant Isles runs the Stream of the Blue Men, where men blue of skin and grey of face swim beside the boats and raise sudden gales. Their chief calls out two lines of verse to the captain, and if he answers in rhyme, quick and well, he may sail on, but if he stumbles he is sunk. In these drowned halls they ask the same of every traveller who would pass them by."))

NEW['vila'] = kind(
    'Vila', 'F', (230, 230, 200), '105d10+382', 15, 'ranged', 3, 45, 42, 9, 2.0,
    [atk('Throat Arrow', '2d8+10', 'pierce', 'ranged', 'silenced', 0.35, 10),
     atk('Whirlwind', '2d6+8', 'blunt', 'ranged', 'slowed', 0.4, 6)],
    family='fair_folk', tags=['fey'], res=['magic', 'cold'], weak=[], pronoun='she',
    opener=('Throat Arrow', 6), can_phase_blink=True, phase_blink_chance=0.15, item=0.2,
    lore=("The vila of the Serbian epic songs is a fairy of the mountains and the clouds, robed in white and long of hair, who shoots with arrows and raises whirlwinds. Once the hero Milos sang upon the mountain of the vila Ravijojla, and his singing so angered her that she shot him, nor would she heal him until Prince Marko rode her down. Whoever steals a vila's hair or her girdle may command her service, but none has yet stolen anything from those who dwell down here."))

NEW['myrmekes'] = kind(
    'Gold-Digging Ant', 'a', (200, 160, 60), '65d10+236', 17, 'aggressive', 5, 44, 41, 9, 2.0,
    [atk('Mandible Bite', '2d6+6', 'slash', 'bite'),
     atk('Formic Spray', '1d8+4', 'acid', 'breath', 'corroding', 0.3, 6, ranged=True)],
    family='vermin', tags=['beast'], res=['fire', 'poison'], weak=['cold'], pack=(3, 4),
    opener=('Mandible Bite', 1),
    gold_gatherer={'radius': 2, 'turns': 3,
                   'line': "The Gold-Digging Ant stops to gather up the gold."},
    lore=("Herodotus learned from the Persians that in the deserts of northern India there were ants, smaller than dogs but bigger than foxes, which cast up sand full of gold as they dug. The Indians came for the gold at midday, when the heat had driven the ants below, and they filled their sacks and rode away at once, for the ants follow a thief by scent and run faster than any beast. Scholars of our own day believe that the tale began with the marmots of the Himalaya, but those that dig in these depths are no marmots."))

NEW['ponaturi'] = kind(
    'Ponaturi', 'g', (170, 200, 190), '116d10+425', 13, 'aggressive', 4, 46, 42, 9, 2.0,
    [atk('Bone Club', '2d10+12', 'blunt', 'blow'),
     atk('Sea-Spear', '2d8+10', 'pierce', 'blow')],
    family='goblinkin', tags=['humanoid'], res=['cold', 'poison'], weak=['fire'], pronoun='he',
    pack=(2, 4), opener=('Sea-Spear', 1), light_shy=True,
    lore=("Beneath the sea lies the country of the Ponaturi, a hostile people of whom the Maori tell, who came ashore by night to sleep in their great house, Manawa-tane. They killed the father of Tawhaki and kept his mother to watch the door, and so Tawhaki and his mother stopped every chink of that house, that the Ponaturi might sleep on into the morning. Then mother and son threw wide the door, and the sunlight slew the sleepers where they lay."))

NEW['taniwha'] = kind(
    'Taniwha', 'S', (60, 100, 90), '242d10+892', 11, 'aggressive', 4, 47, 43, 9, 2.0,
    [atk('Gulping Jaws', '3d10+15', 'pierce', 'bite',
         hold={'kind': 'swallow', 'share': 0.04, 'type': 'acid', 'break_share': 0.15,
               'break_chain': 8, 'max_turns': 4, 'save': 'STR'}),
     atk('Tail Lash', '3d8+12', 'blunt', 'sting', 'stunned', 0.25, 2)],
    family='serpents', tags=['beast', 'reptile'], res=['cold'], weak=['fire'],
    opener=('Gulping Jaws', 1),
    lore=("Many of the taniwha of the Maori are guardians of a river or a tribe, yet some there were that ate people. Such was Tutaeporoporo of the Whanganui River, who swallowed travellers and whole canoes, until the warrior Ao-kehu hid in a hollow log and let himself be swallowed in it, and cut his way out from within. Such also was Ngarara Huarau, which was lured from its cave and burned. Those that lie in these flooded deeps are guardians of nothing but themselves."))

NEW['impundulu'] = kind(
    'Impundulu', 'B', (40, 40, 40), '141d10+516', 16, 'hit_and_run', 3, 48, 44, 9, 2.0,
    [atk('Lightning Stoop', '3d8+12', 'lightning', 'blow', 'stunned', 0.3, 2),
     atk('Blood-Drinking Bite', '2d8+10', 'drain', 'bite')],
    family='birds', tags=['beast'], res=['lightning', 'poison'], weak=['fire'],
    opener=('Lightning Stoop', 1), drain_heals_self=0.5,
    lore=("The Zulu and the Xhosa hold that the impundulu, the lightning bird, strikes the earth as lightning. It is black and white and as tall as a man, a witch's servant that is handed down from mother to daughter, and it hungers for blood. Neither spears nor guns can harm it, nor can it be drowned or poisoned, yet fire will destroy it, and its fat, if it is dug from the place where the lightning struck, makes a powerful medicine."))

NEW['mapinguari'] = kind(
    'Mapinguari', 'Y', (150, 80, 50), '236d10+862', 9, 'aggressive', 4, 49, 45, 9, 2.0,
    [atk('Hooked Claws', '3d8+12', 'slash', 'blow'),
     atk('Belly Maw', '3d10+10', 'pierce', 'bite', 'bleeding', 0.3, 5)],
    family='great_beasts', tags=['beast'], weak=['fire'], multi_attack_count=2,
    aura={'kind': 'stench', 'radius': 1, 'effect': 'weakened', 'chance': 0.35, 'turns': 4,
          'save': 'CON', 'line': "The reek of the Mapinguari turns your stomach."},
    weak_spot_chain=10,
    weak_spot_line="Your blow finds the soft place at the Mapinguari's navel!",
    lore=("Tall and shaggy is the mapinguari of which the rubber-tappers and the peoples of the Amazon speak, a beast with one eye, with feet turned backward and with a mouth in its belly. Before it rolls a stench like rot and dung that leaves hunters dizzy and sick, and its hide will turn arrows and knives everywhere except at the navel. The biologist David Oren has wondered whether the tales preserve a memory of the giant ground sloths that lived in that land at the end of the Ice Age."))

NEW['preta'] = kind(
    'Preta', 'G', (160, 150, 140), '131d10+480', 12, 'aggressive', 4, 50, 46, 9, 2.0,
    [atk('Hungry Touch', '2d8+10', 'drain', 'touch', steal='offering', steal_chance=0.3),
     atk('Needle-Throat Wail', '1d8+4', 'magic', 'voice', 'weakened', 0.4, 12)],
    family='ghosts', tags=['undead'], res=['cold', 'drain'], weak=['holy', 'fire'], sp_drain=15,
    appeased_by={'food': 'plain',
                 'line': "The Preta falls on your offering, and for a while its hunger is quiet."},
    lore=("A belly like a drum and a throat as thin as a needle are the lot of the preta, the hungry ghost of which Buddhists and Hindus tell. It is a spirit of greed that nothing it eats can fill, and in its mouth all food turns to fire. The monk Maudgalyayana, in the Ullambana story, found his own mother among these spirits. From of old a preta has been eased by offerings of food freely given, and so every year at the Ghost Festival a meal is set out for them."))

NEW['upas_tree'] = kind(
    'Upas Tree', 'T', (200, 200, 170), '254d10+927', 0, 'sessile', 6, 52, 48, 9, 2.0,
    [atk('Ipoh Sap', '2d8+8', 'poison', 'ranged', 'poisoned', 0.5, 8),
     atk('Root Wrap', '3d8+10', 'blunt', 'grapple', 'immobilized', 0.35, 2)],
    family='plants', tags=['plant'], res=['poison'], weak=['fire'], opener=('Ipoh Sap', 5), item=0.25,
    aura={'kind': 'stench', 'radius': 2, 'effect': 'poisoned', 'chance': 0.4, 'turns': 4,
          'save': 'CON', 'line': "The air round the Upas Tree burns in your throat."},
    lore=("The London Magazine printed in 1783 a Dutch surgeon's tale of the upas tree of Java, whose poison killed every living thing for fifteen miles about, so that condemned criminals were sent to fetch its sap and few came back. The tale was a tall one, but the tree is real, and its milky latex is the ipoh poison with which island hunters tipped their blowgun darts. The upas trees of the deep need no tall tale to make them deadly."))

NEW['nuckelavee'] = kind(
    'Nuckelavee', 'N', (150, 50, 50), '248d10+908', 15, 'aggressive', 3, 53, 48, 9, 2.0,
    [atk('Mortasheen Breath', '2d8+10', 'poison', 'breath', 'diseased', 0.5, 8),
     atk('Long Arms', '3d8+14', 'slash', 'blow'),
     atk('Hoof Trample', '3d10+14', 'blunt', 'trample')],
    family='demons', tags=['demon'], res=['poison', 'cold'], weak=['holy'],
    opener=('Mortasheen Breath', 3), can_charge=True, charge_bonus_mult=1.3, moves=[],
    lore=("Orkney islanders would not speak the name of the nuckelavee, which came out of the sea like a horse and rider grown into one body, and had no skin, so that the black blood could be seen running in its veins. Its breath withered the crops and brought upon the cattle the plague called mortasheen. An old man named Tammas told Walter Traill Dennison how it pursued him along the shore one night, and how he saved himself by leaping a burn of fresh water, where on that night it would not follow him."))

NEW['star_jelly'] = kind(
    'Star Jelly', 'J', (220, 220, 240), '253d10+924', 6, 'ambush', 6, 55, 50, 9, 2.0,
    [atk('Starfall Drop', '3d10+12', 'blunt', 'blow', 'corroding', 0.5, 6),
     atk('Starlight Touch', '2d6+8', 'cold', 'touch', 'slowed', 0.4, 6)],
    family='oozes', tags=['aberration'], res=['acid', 'cold'], weak=['fire'], opener=('Starfall Drop', 1),
    light_shy=True, hidden_overhead=True,
    lore=("After a night of falling stars the shepherds of Wales would find upon the grass a pale and trembling jelly that melted away within days, and they called it pwdre ser, the rot of the stars. Medieval physicians spread it upon sores, and naturalists today lay the blame on frog spawn or a swollen alga of the soil. The jelly that drops from the roofs in these depths has no such homely birth, and it shrinks away from any light."))

NEW['psoglav'] = kind(
    'Psoglav', 'P', (110, 90, 70), '266d10+973', 13, 'aggressive', 2, 62, 58, 9, 2.0,
    [atk('Iron-Toothed Bite', '3d8+16', 'pierce', 'bite', 'bleeding', 0.35, 5),
     atk('Horse-Leg Kick', '3d6+14', 'blunt', 'blow', 'stunned', 0.25, 2)],
    family='goblinkin', tags=['humanoid'], res=['cold'], weak=['fire'], pronoun='he', pack=(2, 3),
    opener=('Iron-Toothed Bite', 1), perception_range=5, item=0.2,
    lore=("Villagers of Bosnia, Montenegro and Serbia told of the psoglavci, the dog-heads, who are men with the legs of horses and the heads of dogs, with teeth of iron and a single eye in the middle of the forehead. They live in caves in a land without sun, where precious stones give light in the darkness. With their one eye they see but poorly, yet their noses miss nothing, and they dig the dead out of their graves to eat them."))

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
    lore=("On the island of Waq-waq at the edge of the world, as the wonder-books of Arabs and Persians relate, there grows a tree whose fruit has the shape of people, and when it is ripe it falls, crying 'waq, waq!'. In later paintings its branches end in the heads of men and beasts, all calling at once. Such a tree, standing in the dark, cries out at anything that moves, and then everything near at hand comes to the sound of its crying."))

NEW['yuki_onna'] = kind(
    'Yuki-Onna', 'F', (230, 240, 255), '281d10+1034', 13, 'ranged', 1, 66, 62, 9, 2.0,
    [atk('Freezing Breath', '2d10+16', 'cold', 'breath', 'frozen', 0.45, 3, ranged=True),
     atk('Pale Touch', '3d8+14', 'drain', 'touch')],
    family='fair_folk', tags=['fey'], res=['cold'], weak=['fire'], pronoun='she',
    opener=('Freezing Breath', 4), can_phase_blink=True, phase_blink_chance=0.2, item=0.15,
    lore=("Two woodcutters took shelter in a hut from a blizzard, in the tale that Lafcadio Hearn wrote down, and there a woman in white breathed upon the old man until he froze. The snow woman spared the young one, whose name was Minokichi, and had his promise never to tell of it. Years afterward he told the story to his wife, and his wife was the snow woman herself, yet for their children's sake she did not kill him, but melted away into the mist and was gone."))

NEW['yacumama'] = kind(
    'Yacumama', 'S', (50, 80, 50), '699d10+2562', 9, 'ambush', 1, 70, 65, 9, 2.0,
    [atk('Drawing Breath', '1d6+6', 'magic', 'breath', 'slowed', 0.4, 6, ranged=True, pulls=2,
         pull_line="The Yacumama breathes in, and the air drags you toward its coils!"),
     atk('Crushing Coils', '4d10+20', 'blunt', 'grapple', 'strangulation', 0.35, 3),
     atk('Gaping Jaws', '4d8+20', 'pierce', 'bite')],
    family='serpents', tags=['beast', 'reptile'], res=['cold', 'poison'], weak=['fire'],
    opener=('Drawing Breath', 5),
    lore=("Mother of the waters is the meaning of yacumama, and by that name the peoples of the Peruvian Amazon speak of an anaconda fifty yards long that lies in the deep pools where a river rises. The Nuttall Encyclopaedia of 1907 says that it draws in any creature within a hundred yards, as if the river itself were breathing in. Therefore the fishermen blew upon a conch before they waded, that the yacumama might show itself if it lay there."))

NEW['tsuchigumo'] = kind(
    'Tsuchigumo', 'X', (120, 100, 60), '714d10+2621', 11, 'ambush', 0, 72, 67, 9, 2.0,
    [atk('Fever Curse', '2d8+14', 'magic', 'voice', 'weakened', 0.5, 20),
     atk('Web Cast', '2d6+12', 'magic', 'ranged', 'immobilized', 0.45, 2),
     atk('Earth Spider Fangs', '4d10+22', 'poison', 'bite', 'poisoned', 0.4, 8)],
    family='vermin', tags=['beast'], res=['poison'], weak=['fire'], opener=('Web Cast', 4), item=0.25,
    relurks=True,
    lore=("While the warrior Minamoto no Raiko lay sick of a fever that no medicine could break, as the Heike tells, there came by night to his bedside a strange monk, taller than any man, who sought to bind him with rope. Raiko slashed at him with his sword, and the next day his men followed a trail of blood to a mound behind the Kitano Shrine and found a great earth spider lying there. In the picture scroll of the Tsuchigumo another was cut open, and one thousand nine hundred and ninety skulls rolled out of its belly."))

NEW['bhuta_vahana_yanta'] = kind(
    'Relic Guardian', 'G', (190, 150, 90), '863d10+3168', 8, 'sessile', -2, 83, 78, 12, 2.0,
    [atk('Whirling Swords', '3d8+18', 'slash', 'blow'),
     atk('Whirling Swords Backstroke', '3d8+18', 'slash', 'blow'),
     atk('Whirling Swords Low Cut', '3d8+18', 'slash', 'blow', 'bleeding', 0.3, 5)],
    family='constructs', tags=['construct'], res=['poison', 'cold', 'fire'], weak=['lightning'],
    pack=(2, 2), multi_attack_count=3, item=0.3,
    lore=("King Ajatashatru laid the relics of the Buddha in a deep chamber, as the Pali Lokapannatti tells, and set over them machines driven by spirits, the bhuta vahana yanta, that were built from plans brought out of the land of the Romans. None could pass those guardians until, long afterward, the emperor Ashoka learned their secret and stilled them. The machines of these depths still keep their watch, and there is never an hour when their swords cease from turning."))

NEW['reem'] = kind(
    "Re'em", 'Q', (80, 60, 40), '1205d10+4417', 13, 'aggressive', -2, 85, 80, 12, 2.0,
    [atk("Horns of the Re'em", '5d10+40', 'pierce', 'blow', 'stunned', 0.3, 2),
     atk('Hill-Shaking Trample', '5d8+36', 'blunt', 'trample')],
    family='great_beasts', tags=['beast'], opener=("Horns of the Re'em", 1), can_charge=True,
    charge_bonus_mult=1.5, footprint=[2, 2],
    lore=("The re'em of the Hebrew Bible is a wild ox of terrible strength, which the translators of King James called the unicorn, and Job was asked whether it would ever serve him or harrow his valleys. The rabbis held it too great for Noah's ark and puzzled over the manner of its saving. A midrash tells how David in his youth climbed a sleeping re'em, thinking it a hill, and was borne up toward the sky upon its horns when it woke, but the re'em of the deep halls are awake already."))

NEW['eitr'] = kind(
    'Eitr', 'P', (40, 90, 70), '863d10+3163', 7, 'aggressive', 0, 86, 81, 12, 2.0,
    [atk('Venom-Rime Touch', '4d10+30', 'poison', 'touch', 'poisoned', 0.5, 8),
     atk('Freezing Slag', '3d10+26', 'cold', 'blow', 'frozen', 0.35, 2)],
    family='oozes', tags=['aberration'], res=['poison', 'cold', 'acid'], weak=['fire'],
    trail_hazard={'hazard': 'venom_pool', 'turns': 20},
    lore=("Poisonous rivers, the Elivagar, flowed in the beginning from the wellspring in Niflheim, as Snorri tells, and their venom, which is named eitr, hardened like slag from a furnace and spread as rime through the void. Where that rime met the heat of Muspell the first giant, Ymir, was born, but some part of the eitr never hardened. It crawls yet in the deepest cold, and whatever it touches is frozen and sickened at the same moment."))

NEW['bakunawa'] = kind(
    'Bakunawa', 'S', (60, 40, 80), '1290d10+4730', 12, 'aggressive', -3, 88, 84, 12, 2.0,
    [atk('Moon-Swallowing Jaws', '4d10+30', 'magic', 'bite', 'blinded', 0.4, 8, snuffs_light='dark',
         snuff_chance=0.5),
     atk('Coiling Crush', '5d10+36', 'blunt', 'grapple', 'immobilized', 0.3, 2),
     atk('Horned Strike', '4d8+34', 'pierce', 'blow')],
    family='serpents', tags=['beast', 'reptile'], res=['cold', 'lightning'], weak=['fire'],
    lore=("Seven moons were hung in the sky by the god Bathala, so the Visayan peoples of the Philippines say, until the sea serpent Bakunawa rose up and swallowed six. An eclipse comes whenever it rises for Bulan, the last moon, and then the people run out of doors and beat upon pots and gongs and drums until the noise drives it to spit the moon out again. The bakunawa coiled in these deeps will swallow any light that it sees."))

# Their family_affinity.json `kinds` entries (the affinity pass writes each
# kind's five lists from these: tools/content/affinity_pass.py). `form`
# only where the creature differs from its family; status from its lore.
AFFINITY = {
    'mandrake': {'lore': "A root has no mind to be frightened or charmed and it never sleeps, and its sap, which brings slumber to others, is no poison to itself.",
                 'source': "Theophrastus, Historia Plantarum 9.8; Dioscorides on the root boiled in wine.",
                 'status_immune': ['sleeping', 'confused', 'charmed', 'feared', 'blinded']},
    'kappa': {'lore': "When a kappa is knocked senseless the water spills from its dish, and so a stun is its undoing.", 'source': "Yanagita Kunio, Tono Monogatari (1910), tales 55-59.",
              'status_weak': ['stunned']},
    'eloko': {'lore': "The biloko are spirits of the forest, and no sleep comes to them.",
              'source': "Mongo-Nkundo tales (Gustaaf Hulstaert).", 'status_immune': ['sleeping']},
    'asanbosam': {'lore': "It dwells in the high branches and has teeth of iron, and no charm can turn it.",
                  'source': "Akan folklore; Edward Long, The History of Jamaica (1774).",
                  'status_immune': ['charmed']},
    'ahuizotl': {'lore': "The beast of the lake cries like a child and has a hand upon its tail, yet it is flesh and blood and nothing stranger.", 'source': "Sahagun, Florentine Codex, Book 11.",
                 'status_immune': []},
    'khalkotauros': {'lore': "The bronze bulls of Hephaestus breathe fire and cannot burn, and a blade glances from their plates, but a hammer dents them.",
                     'source': "Apollonius of Rhodes, Argonautica 3.1278-1407.",
                     'status_immune': ['burning', 'poisoned', 'sleeping', 'charmed', 'feared', 'confused']},
    'cu_sith': {'lore': "The hound of the fairies never sleeps upon the hunt, and no charm can turn it aside.",
                'source': "J. G. Campbell, Superstitions of the Highlands and Islands of Scotland (1900).",
                'status_immune': ['sleeping', 'charmed']},
    'bulgasari': {'lore': "This beast was grown from rice and iron, and a blade that sinks into the metal of its hide is eaten, but a hammer bruises it still.",
                  'source': "Jo Jae-sam, Songnam Japji; the Encyclopedia of Korean Culture.",
                  'status_immune': ['poisoned', 'sleeping', 'charmed', 'feared', 'confused']},
    'vetala': {'lore': "A spirit that wears a dead body knows neither fear nor sleep nor poison.",
               'source': "Somadeva, Kathasaritsagara (the Vetala Panchavimshati).",
               'status_immune': ['sleeping', 'poisoned', 'charmed', 'feared']},
    'nahual': {'lore': "Beneath the skin he is a man, and whatever frightens men frightens him.",
               'source': "Sahagun, Florentine Codex, Book 10.", 'status_immune': []},
    'likho': {'lore': "Likho has but one eye, and if you put it out, as the smith did, she is helpless.",
              'source': "Afanasyev, Narodnye russkie skazki, 'Likho One-Eyed'.",
              'status_immune': ['sleeping'], 'status_weak': ['blinded']},
    'centaur': {'lore': "The horse-men are wild and fearless in battle, but wine sends them reeling, and when they drank it at the wedding of the Lapiths the fight began.",
                'source': "Ovid, Metamorphoses 12.210-535.",
                'status_immune': ['feared'], 'status_weak': ['confused']},
    'blue_men_of_the_minch': {'lore': "The sea-men of the fair folk raise up the gales, and sleep never takes them.", 'source': "J. G. Campbell (1900).",
                              'status_immune': ['sleeping']},
    'vila': {'lore': "A fairy of the clouds can be neither lulled to sleep nor charmed.",
             'source': "Vuk Karadzic, Srpske narodne pjesme (1841-62).",
             'status_immune': ['sleeping', 'charmed']},
    'myrmekes': {'lore': "These ants of the desert dig all day, but a cold night slows them and a hammer cracks their shells.", 'source': "Herodotus, Histories 3.102-105.",
                 'form': {'blunt': 'weak'}, 'status_immune': ['sleeping']},
    'ponaturi': {'lore': "They are a people of the dark beneath the sea, and they are dazzled by the light that slew them in the tale of Tawhaki.", 'source': "Sir George Grey, Polynesian Mythology (1855).",
                 'status_immune': [], 'status_weak': ['blinded']},
    'taniwha': {'lore': "The water-dragon has scales that turn a thrust, and no sleep comes to such a guardian.",
                'source': "Te Ara, the Encyclopedia of New Zealand: 'Taniwha'.",
                'form': {'pierce': 'resist'}, 'status_immune': ['sleeping']},
    'impundulu': {'lore': "Neither spear nor gun can harm the lightning bird, nor can it be poisoned, but fire destroys it.",
                  'source': "Axel-Ivar Berglund, Zulu Thought-Patterns and Symbolism (1975).",
                  'form': {'slash': 'resist', 'pierce': 'resist', 'blunt': 'resist'},
                  'status_immune': ['poisoned']},
    'mapinguari': {'lore': "Arrows and knives are turned by its hide everywhere save at the navel, and its own stench troubles it not at all.", 'source': "David Oren, Ciencia Hoje (1993).",
                   'form': {'slash': 'resist', 'pierce': 'resist', 'blunt': 'resist'},
                   'status_immune': ['poisoned', 'confused']},
    'preta': {'lore': "The hungry ghost has no sleep and no blood for poison, and nothing but food will charm it.", 'source': "The Petavatthu; the Ullambana Sutra.",
              'status_immune': ['sleeping', 'poisoned', 'charmed']},
    'upas_tree': {'lore': "A tree that poisons the very air is proof against poison, and being a tree it neither fears nor sleeps.", 'source': "Erasmus Darwin, The Loves of the Plants (1789).",
                  'form': {'slash': 'weak', 'pierce': 'resist'},
                  'status_immune': ['sleeping', 'poisoned', 'confused', 'charmed', 'feared', 'blinded']},
    'nuckelavee': {'lore': "The demon of the Orkney shore fears nothing in the world but fresh water.",
                   'source': "Walter Traill Dennison, The Scottish Antiquary (1891).",
                   'status_immune': ['sleeping', 'feared']},
    'star_jelly': {'lore': "The trembling jelly has no eyes and no mind, nor any blood.",
                   'source': "John of Gaddesden, Rosa Anglica (c. 1314).",
                   'status_immune': ['blinded', 'sleeping', 'confused', 'feared', 'charmed', 'poisoned']},
    'psoglav': {'lore': "Its single eye sees so poorly that to blind it avails nothing.",
                'source': "Tihomir Djordjevic (1953); Srpski mitoloski recnik (1970).",
                'status_immune': ['blinded']},
    'waq_waq_tree': {'lore': "This tree bears heads that cry, yet it does not sleep or fear or see as we do.",
                     'source': "The Arabic and Persian wonder-books; al-Qazwini, 'Aja'ib al-makhluqat.",
                     'form': {'slash': 'weak', 'pierce': 'resist'},
                     'status_immune': ['sleeping', 'poisoned', 'charmed', 'feared', 'blinded']},
    'yuki_onna': {'lore': "The snow woman cannot be frozen and her blizzard never sleeps, and a blade passes through her as through snow.", 'source': "Lafcadio Hearn, Kwaidan (1904).",
                  'form': {'slash': 'resist', 'pierce': 'resist'},
                  'status_immune': ['frozen', 'sleeping', 'charmed']},
    'yacumama': {'lore': "The mother of the waters lies in her pool and never sleeps.",
                 'source': "The Nuttall Encyclopaedia (1907): 'Yacu-mama'.",
                 'status_immune': ['sleeping']},
    'tsuchigumo': {'lore': "Its swollen and hairy body cares nothing for a club, and it was a sword that cut it down.",
                   'source': "The Heike Monogatari, Tsurugi no maki.",
                   'form': {'blunt': 'resist', 'slash': 'weak'}, 'status_immune': ['sleeping']},
    'bhuta_vahana_yanta': {'lore': "Spirits drive these engines of bronze and wood, which have no mind, no blood, no sleep and no eyes to blind.",
                           'source': "The Pali Lokapannatti (c. 11th-12th century).",
                           'status_immune': ['sleeping', 'poisoned', 'charmed', 'feared', 'confused',
                                             'paralyzed', 'stunned', 'blinded']},
    'reem': {'lore': "The wild ox as big as a hill has no fear of anything that walks.",
             'source': "Job 39:9-12; the King James 'unicorn'.", 'status_immune': ['feared']},
    'eitr': {'lore': "The first poison of the world can be neither poisoned nor frozen.",
             'source': "Snorri Sturluson, Prose Edda, Gylfaginning 5.",
             'status_immune': ['frozen', 'poisoned', 'sleeping', 'blinded', 'confused', 'charmed', 'feared']},
    'bakunawa': {'lore': "The serpent that swallows moons cannot be blinded by any light.",
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
