"""The monster pass of 2026-11-17 (Brandon's rulings 11 and 12, 2026-11-16).

Ruling 11: "monsters re-placed deeper + deep kinds: yes" (the question was:
move the lore-mighty kinds deeper, their stats re-baked at the new depth,
and add deep kinds from lore, until every tier holds 10-35% of the ordinary
kinds). Ruling 12: "every family in every tier: yes".

LORE, NOT FLOOR. Each move below says what the creature IS in its myth or
source and so which depth its power belongs to. The numbers are then
written into data/monsters.json as base data, once, here:

  * spawn: peak_floor is the new depth, spread and min_level follow the
    respawn rule (tools/balance/respawn_by_hp.py spread_for / lead_for);
  * health: the median of the new floor (floor_curve.target_hp), so the
    respawn tool, which seats every kind on the floor its HP fits, keeps
    it there (a pack's share through SWARM_SEAT_MULT, as before);
  * blows: each attack keeps its name, type, effect and delivery and is
    re-sized so the kind hits as hard against its new neighbours as it did
    against its old ones (the median blow of the kinds this pass leaves
    alone near each floor, `Floors`: the floor_curve damage anchors run
    under the data on floors 20-50), within KEEP_LO..KEEP_HI; no blow passes
    the spike cap there;
  * aim: the written THAC0 keeps the kind's distance from the median of the
    kinds that stay near its floor, old floor to new (the data's THAC0s are
    not at rebake_thac0.py's output today, 289 of them off it before this
    pass, so that tool is not re-run here: it would re-aim everyone);
    thac0_lore is re-based the same way, for the day it is;
  * weight: a kind moved into a deeper tier is no more common there than
    the kinds already there (their median peak_weight);
  * regeneration grows with the square root of the new health; the harvest
    tier and the treasure's item tier are raised to the new band
    (ruling 2, tier by depth).

Nothing is ever multiplied by the floor at run time. After this tool:

    py tools/balance/monster_pass_2026_11_17.py --write
    py tools/balance/gold_by_lore.py           # gold for the new depth's income
    py tools/content/affinity_pass.py --write
    py tools/balance/respawn_by_hp.py          # must propose no change
    py tools/balance/weapon_curve.py --write   # weapons follow the monster curve
    py tools/content/kitchen/part_freq.py --trials 45   # then build_kitchen.py

`py tools/balance/monster_pass_2026_11_17.py` alone prints the census and the
spawn-curve checks for the plan, writing nothing. Idempotent: a kind already
on its new floor is left alone.
"""
from __future__ import annotations

import argparse
import collections
import json
import math
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'content'))

import respawn_by_hp as rs  # noqa: E402

MONSTERS = os.path.join(ROOT, 'data', 'monsters.json')

# Blows keep this much of how far above or below its old floor's typical hit
# a kind struck (1.0 = exactly the floor's), and never more than SPIKE x the
# new floor's typical hit in one blow.
KEEP_LO, KEEP_HI = 0.85, 1.2
SPIKE = 2.4

# ---------------------------------------------------------------------------
# The moves: kind -> (new peak floor, why). Grouped by what the domain of the
# new depth is (src/decor.py, data/domains.json): floors 21-40 Medusa's
# temple (the Greek monsters, the serpent folk, the mid-level killers);
# 41-60 the Scorched Deep under Fafnir (fire and earth, the dark elves, and
# Egypt's dead around Setne's Tomb, floors 45-65); 61-80 Fenrir's rime
# halls (the Norse powers of Ragnarok); 81-100 the abyss under Abaddon
# (Tiamat's brood and the powers of the end).
# ---------------------------------------------------------------------------
MOVES: dict[str, tuple[int, str]] = {
    # --- the temple, 21-40: the Greek labours and the classical monsters ---
    'stymphalian_bird': (32, "Ares' man-eating birds with bronze feathers: Heracles' sixth labour, with the Greek monsters of Medusa's temple"),
    'peryton': (28, "Borges's sibyl foretold the perytons would bring down Rome; each must kill a man to win back its shadow"),
    'griffin': (30, "Herodotus's griffins guard the mountain gold against whole tribes: a watchman of the temple's treasure, not a floor-8 bird"),
    'pegasus': (36, "born of Medusa's blood when Perseus beheaded her: Pegasus belongs in Medusa's temple"),
    'chimera': (31, "Homer's fire-breathing lion-goat-serpent that burned Lycia until Bellerophon came on Pegasus"),
    'manticore': (29, "Ctesias's man-eater with three rows of teeth and a tail that shoots spines, which leaves not even the bones"),
    'sphinx': (35, "the riddling Sphinx of Thebes, who ate every traveller until Oedipus: Greek, the temple's"),
    'cyclops': (30, "Polyphemus's people, the one-eyed giants of the Odyssey who ate Odysseus's men"),
    'cyclops_brute': (26, "a brute of Polyphemus's people: Greek, the temple's"),
    'basilisk': (28, "Pliny's king of serpents, whose glance kills and whose breath splits rock: with Medusa's kin, the gorgons of the temple"),
    'empusa': (33, "Hecate's man-eating demoness with one leg of bronze, sent to the crossroads: Greek, the temple's"),
    'erinyes_lesser': (33, "the Furies, the Greek avengers of kin-blood, who hounded Orestes across the world"),
    'hecate_hound': (32, "Hecate's spectral hounds that guard the edge of the underworld: Greek, the temple's"),
    'dryad_guardian': (34, "the oak-nymph of Demeter's grove whose dying curse starved King Erysichthon: the temple's sacred grove"),
    'naga_guardian': (27, "a serpent lord set over a sacred vault: the temple is the serpents' own domain"),
    'yuan_ti_pureblood': (37, "the serpent folk who still worship their dead snake god: the temple's congregation"),
    'snake_charmer': (25, "a cultist of the serpent folk: the temple's"),
    'cath_palug': (30, "the Welsh Triads' monstrous cat that ate nine score warriors on Anglesey before Cai killed it"),
    'nue': (30, "the chimera of the Heike that sickened Emperor Konoe with terror until Yorimasa shot it from the cloud"),
    # --- the temple: mid-level killers (their D&D or folklore standing) ---
    'cloaker': (27, "the cloaker (CR 8) drapes its victim and moans whole parties into terror: a mid-dungeon horror"),
    'roper': (26, "the roper (CR 5) waits as a stalagmite and hauls prey in on six draining strands"),
    'lurker_above': (26, "a ray the size of a ceiling that drops and smothers a whole man: a mid-dungeon ambusher"),
    'trapper': (26, "a floor-sized ambusher that rolls up whoever crosses it, cousin to the lurker above"),
    'otyugh': (28, "the offal-eater (CR 5) whose bite carries the filth it lives in"),
    'aboleth_lesser': (34, "the aboleths remember the world's first sea and enslave minds; even a young one is a deep power"),
    'bone_devil': (30, "a jailer and torturer of Hell (CR 9), the devils' taskmaster"),
    'hezrou': (28, "the toad-demon (CR 8) whose stench sickens: a demon of the mid-depths"),
    'vrock': (26, "the vulture-demon (CR 6) whose dance shakes the floor"),
    'barbed_devil': (28, "a gate-guard of Hell (CR 5), barbed all over"),
    'chain_devil_spawn': (27, "brood of the chain devil (CR 8), Hell's flayer"),
    'night_hag': (31, "the mare who rides one sleeper night after night until nothing is left to ride"),
    'annis_hag': (29, "Black Annis of the Dane Hills, who dug her own cave with iron claws and ate children"),
    'banshee': (16, "the woman of the fairy mound whose keening, down here, does the killing (still floors 1-20: the kitchen's early Wisdom dishes are hers)"),
    'dullahan_spawn': (29, "the headless rider of the Irish roads: where he stops and speaks a name, that one dies"),
    'drow_priestess': (26, "the dark elves' ruling priestess (CR 8), whose curse ends a bloodline in a night"),
    'drow_mage': (31, "a dark elf war-mage (CR 7)"),
    'nightshade_spawn': (28, "brood of the nightshades, 'still among the most powerful undead a delver will meet'"),
    'sluagh': (27, "the Highland host of the unforgiven dead, who fly in from the west to take the dying"),
    'greater_shadow': (29, "a shade that has drunk blood for centuries, as Odysseus's dead did at the trench"),
    'lesser_death': (30, "a shadow of Thanatos, who held all death in chains until Sisyphus tricked him"),
    'clay_golem': (35, "the Golem of Prague's kind: clay given the Name, a guardian of the mid-depths"),
    'shield_guardian': (33, "a wizard's bodyguard (CR 7) that drinks spells meant for its master"),
    'gorgon_warrior': (29, "Topsell's bronze bull, whose breath kills (the D&D gorgon, CR 5)"),
    'fomorian': (34, "Balor's people, who ruled Ireland from the sea until Mag Tuired; their evil eye kills"),
    'wight_lord': (31, "Thorolf Lame-Foot of the Eyrbyggja Saga, who killed a valley's shepherds and herds from his grave"),
    'dread_knight': (27, "a fallen paladin, his holy power turned to unholy strength"),
    'skeletal_giant': (27, "the giant dead whose bones Herodotus says the Spartans carried home as a hero's"),
    'mohrg': (34, "the risen corpse of an unhanged murderer (CR 8), still killing"),
    'ossuary_horror': (26, "the bones of Sedlec's tens of thousands, strung together and walking"),
    'mind_flayer_thrall': (30, "a thrall goes where the mind flayers rule (floor 31)"),
    'each_uisce': (27, "the each-uisge, the deadliest of the water-horses, who drowns and eats its rider"),
    'strigoi': (25, "the Romanian dead who feed on their own families first: a village-killer"),
    'vrykolakas': (26, "the Greek islands' dead who call a name once at the door, and whoever answers dies"),
    'necromancer_lord': (25, "a lord of the necromancers: his dead march in the mid-depths"),
    'spider_queen': (26, "Arachne's line, who wove the gods at their worst and was made a spider"),
    'black_pudding': (25, "a heap of living tar (CR 4) that a blade only multiplies"),
    'shambling_mound': (28, "the walking bog-heap (CR 5) that smothers what it catches"),
    'wyvern_greater': (35, "a wyvern whose wings fill a corridor and whose sting never misses"),
    'harrow_witch': (24, "a witch of the cult circles of the mid-depths"),
    'hill_giant': (27, "twice a tall man's height, boulders for missiles (CR 5)"),
    'ettin': (25, "the two-headed eoten, the jotunn of the English (CR 4)"),
    'thunderbird_lesser': (33, "the Thunderbird whose wingbeat is thunder, at war with the horned serpents of the deep places"),
    'tengu_warrior': (23, "the crow-headed swordmasters of Mount Kurama, who taught the boy Yoshitsune"),
    'hobgoblin_warlord': (24, "a war-band's warlord, who kills his own cowards first"),
    'orc_warchief': (23, "an orc who killed every challenger for the title"),
    'gnoll_fang_of_yeenoghu': (24, "marked by the demon lord Yeenoghu himself; a fang never retreats"),
    'shadow_demon': (25, "a fiend that lost its body and kept its hatred (CR 4)"),
    'succubus_shade': (26, "the succubus of the old demonologies, who feeds on a sleeper's strength (CR 4)"),
    'incubus': (27, "the incubus of the medieval churchmen, who leaves sleepers pale and wasted (CR 4)"),
    'drow_warrior': (28, "a dark elf trained from the cradle, whose bolts put men to sleep for the mines (CR 5)"),
    'revenant': (29, "William of Newburgh's revenants, who walked out of their graves to repay a wrong (CR 5)"),
    'weretiger': (26, "the harimau jadian of the Malay villages, a man who becomes a tiger after dark (CR 4)"),
    'flesh_golem': (27, "Frankenstein's stitched man, given life by the storm (CR 5)"),
    'wyvern': (31, "the heralds' two-legged dragon with a sting that never misses (CR 6)"),
    'young_black_dragon': (33, "a young black dragon (CR 7) already counting its hoard"),
    'pale_master': (30, "a master of the necromancers' art, more dead than living"),
    'stone_golem_lesser': (30, "a guardian statue given motion, too heavy for a blade"),
    'goblin_warpriest': (21, "the war-band's priest, who blesses the raid"),
    'orc_marauder': (21, "the orc raiders who burn what they cannot carry"),
    'sable_serpent': (21, "the black serpent country folk would not name after dark"),
    'demonic_imp': (22, "an imp swollen on Hell's own fire"),
    'will_o_wisp': (21, "the foolish fire that leads travellers off the path and into the bog"),
    'wight': (22, "a dead lord of the barrows who still expects obedience; lesser dead gather to him"),
    'giant_scorpion': (21, "the Earth's scorpion that stung Orion, the hunter who boasted he would kill every beast"),
    'light_elf_hostile': (62, "Snorri's Light Elves of Alfheim, fairer than the sun: soured, they are Norse powers, at home in the rime halls"),
    'fionn_hound': (23, "of the blood of Bran and Sceolang, Fionn mac Cumhaill's hounds with human wits"),
    'redcap': (21, "the Border goblin who dyes his cap in travellers' blood; no human strength can stop him"),
    'spriggan': (22, "the Cornish ghosts of the old giants, who swell to a giant's size when their gold is touched"),
    'bearded_devil': (23, "a shock-trooper of Hell's legions (CR 3) whose beard-tendrils poison"),
    'green_hag': (22, "Jenny Greenteeth and Peg Powler, who drown children in the ponds"),
    'orc_priest': (22, "the war-band's healer, who keeps the raiders on their feet"),
    'displacer_beast': (24, "a six-legged hunter that is never where it seems (CR 3)"),
    'hook_horror': (23, "nine feet of beetle and bone hooks that clicks to its pack across the caves"),
    'bugbear_chieftain': (23, "the chief of the bugbears, who leads the raids from the front"),
    'myconid_sovereign': (22, "the mind of a fungus that spans miles of soil"),
    'clockwork_horror': (32, "a brass spider with saw legs that takes apart what it catches"),
    # --- the Scorched Deep, 41-60: fire, stone, the dark elves, the deep's beasts ---
    'dark_elf': (43, "Snorri's dark elves live down in the earth, blacker than pitch; their cities are in the lowest tunnels and only scouts come up"),
    'magma_elemental': (44, "Typhon's fire under Etna, living magma: the Scorched Deep's fire vents"),
    'greater_fire_elemental': (50, "a pillar of white-hot flame that melts stone: the Scorched Deep"),
    'greater_earth_elemental': (46, "summoned from the deepest strata, where rock has never seen light"),
    'ruinous_djinn': (54, "a rebel jinni of smokeless fire, of those Solomon sealed in brass: the Scorched Deep"),
    'dire_lion': (47, "the Ice Age cave lion of Chauvet, taller than any lion alive, kept in the deep caves"),
    'unicorn_corrupted': (46, "the unicorn whose horn makes poisoned water clean, turned to poison: a holy beast's fall is a deep power"),
    'werebear': (45, "Bodvar Bjarki fought King Hrolf's last battle as a bear that no weapon could bite"),
    'werewolf_alpha': (48, "Sigmund and Sinfjotli's cursed wolf skins of the Volsunga Saga"),
    'roc_adult': (50, "Sinbad's roc that carries elephants, which roosts over the Valley of Diamonds: the deep's gem-halls"),
    'vine_horror': (44, "a creeper grown on the blood of the unburied, filling a hall"),
    'gelatinous_titan': (46, "a cube that has eaten for so long it fills the passage wall to wall"),
    'chimera_alpha': (46, "the eldest of the chimera's line goes deeper than the young"),
    'manticore_elder': (48, "the eldest manticores go deeper than the young"),
    'nightwing': (52, "the greatest of the nightshades, a bat-shaped shadow that blots out the stars"),
    'spectral_lord': (46, "a warlord or archmage whose ambition outlasted the body by centuries"),
    'phase_spider_matriarch': (50, "the mother of the phase spiders, who walk the fourth dimension"),
    # --- Egypt's dead around Setne's Tomb (floors 45-65) ---
    'thoth_construct': (54, "the keepers of Thoth's own writings, near the tomb where the Book of Thoth lies"),
    'anubis_guardian': (48, "Anubis's door-wardens, who weigh the hearts of the dead in the Hall of Two Truths"),
    'sphinx_guardian': (56, "the Great Sphinx of Giza, which promised a prince a throne"),
    'sphinx_lesser': (44, "the sphinxes of Karnak's mile-long avenue, guardians of the god's road"),
    'ammit_spawn': (53, "the brood of Ammit, the Devourer who eats the hearts that fail the weighing"),
    'soul_eater_spawn': (50, "Ammit's second death, the soul eaten and gone: Egypt's dead"),
    'mummy': (51, "a king embalmed for seventy days: Egypt's dead, with Setne's Tomb"),
    'sobek_warrior': (49, "the temple soldiers of Sobek, the crocodile god of the Nile"),
    'ra_serpent': (52, "the uraeus, the fiery Eye of Ra on the pharaoh's crown, spitting flame"),
    'khepri_beetle': (55, "the sacred beetles of Khepri, who rolls the sun over the horizon"),
    'scarab_swarm': (45, "the tomb scarabs laid over the hearts of Egypt's dead"),
    'death_beetle': (47, "Egypt's heart-scarab and England's deathwatch beetle: the tomb's"),
    'catoblepas': (46, "Pliny's beast of the source of the Nile, whose look kills"),
    # --- Fenrir's rime halls, 61-80: the Norse powers of Ragnarok ---
    'fenrir_pup': (70, "Fenrir's own whelp: it belongs in Fenrir's halls"),
    'winter_wolf': (64, "kin of Skoll and Hati, the wolves that will swallow the sun and the moon"),
    'einherjar_ghost': (66, "Odin's chosen dead, who will fight beside him at Ragnarok"),
    'valkyrie_shade': (70, "one of Odin's choosers of the slain, fallen from his favour"),
    'berserker_spirit': (62, "the bear-shirts' howling trance, the berserkers of Harald Fairhair's prow"),
    'draugr': (63, "the Norse barrow-dead who swell to a giant's size and ride the farm roofs at night"),
    'draugr_wight': (68, "a barrow-king like Karr the Old, whom Grettir the Strong barely wrestled down"),
    'ice_troll': (63, "the Norse frost trolls of the glacier caves"),
    'jormungandr_spawn': (72, "the World Serpent's brood, beside the world serpent (floor 75)"),
    'sea_serpent_norse': (64, "Olaus Magnus's two-hundred-foot serpent of the sea caves of Bergen"),
    'nidhogg_brood': (68, "the brood of Nidhoggr, who gnaws Yggdrasil's root in cold Niflheim"),
    'frost_crawler': (63, "it comes up from the frozen lower levels where water never thaws"),
    'elder_werewolf': (66, "Lycaon's curse, worn so long the man never comes back: with Fenrir, the father of wolves"),
    'elder_basilisk': (64, "the oldest of the serpent-kings, grown to an ox; its venom runs up the spear that strikes it"),
    'corrupted_treant': (66, "a forest shepherd older than the kingdoms above, rotted to the heartwood"),
    'mara': (72, "the Ynglinga Saga's mara that trampled King Vanlandi: a Norse night-terror, at home in the rime halls"),
    'scylla': (74, "Scylla's rock faces Charybdis (floor 78) across the strait"),
    'charybdis_spawn': (72, "the whirlpool's brood, beside Charybdis (floor 78)"),
    # --- the abyss, 81-100: Tiamat's brood and the powers of the end ---
    'lahamu': (92, "Tiamat's firstborn, the first gods of the Enuma Elish: with Tiamat and her blood (floors 85-95)"),
    'ugallu_demon': (84, "one of the eleven monsters Tiamat made to fight the younger gods"),
    'kusarikku': (90, "the Bull-Man, one of Tiamat's eleven monsters"),
    'anzu_bird': (86, "Anzu stole the Tablet of Destinies and commanded fate itself until Ninurta brought him down"),
    'pazuzu_spawn': (82, "the brood of Pazuzu, king of the wind demons, with the Babylonian powers of the abyss"),
    'titan': (86, "Zeus chained the Titans in Tartarus, the pit beneath Hades"),
    'lich_sovereign': (88, "the sovereign of the liches, who rules the dead from the abyss"),
    'cerberus': (83, "the hound of Hades, who keeps the dead in; Dante set him in Hell's third circle"),
    'death_lord': (86, "a rider in the train of Revelation's pale horse, whose rider is Death"),
    'chaos_spawn': (88, "a scrap of Hesiod's first Chaos, the yawning gap before earth and sky"),
}

# Re-seated inside floors 1-20 (still tier 1): the kinds with more to them
# than the first few floors' rats and goblins, set down where the creatures
# above have gone, so floors 7-20 keep a full and fair population of their
# own (tests/test_spawn_curve.py: the typical monster of every floor has
# about that floor's health, and no floor runs thin).
MOVES.update({
    'wraith': (15, "a wraith (CR 5) drains the life from the living; no floor-1 fodder"),
    'troll': (16, "the troll (CR 5) closes its wounds as fast as they are cut"),
    'minotaur_warrior': (17, "the Minotaur's descendants hold the labyrinth around Asterion (floor 20)"),
    'ghast': (12, "the ghoul's cleverer cousin, who leads the pack and lays the ambush"),
    'barrow_wight': (13, "a mound-dweller like Karr the Old, who seized Grettir in the dark"),
    'tomb_guardian': (14, "a lesser king's answer to Qin Shi Huang's clay army"),
    'zombie_hulk': (15, "a necromancer's battering ram"),
    'lich_thrall': (14, "a lich's servant, raised with a scrap of its master's craft"),
    'death_mage': (24, "a necromancer who has died and kept casting: a power of the mid-depths"),
    'specter': (16, "nothing left of it but the hunger; it walks through stone"),
    'sea_hag': (24, "of the sort of Grendel's mother, whom Beowulf's sword would not bite"),
    'grell': (14, "a floating brain with a beak and ten paralysing tentacles"),
    'gibbering_mouther': (12, "a heap of mouths and eyes whose babble breaks the mind"),
    'dire_bear': (14, "the great bear of the old forests"),
    'phase_spider': (24, "a spider (CR 3) that steps out of the world and back in behind its prey"),
    'ettercap': (12, "the spider-keeper, who spins traps across the halls"),
    'drake_fire': (15, "a wingless fire-dragon of the drakes"),
    'drake_cold': (13, "a wingless frost-dragon of the drakes"),
    'lindworm': (18, "King Lindworm of the Danish tale, who devoured his brides"),
    'ice_elemental': (13, "living ice from the meltwater caverns"),
    'xorn': (16, "the stone-swimmer that eats gems and metal"),
    'werewolf': (17, "the werewolf of every country's tale"),
    'pegasus_corrupted': (16, "a winged horse of Pegasus's line, darkened by the deep"),
    'ogre': (13, "the man-eating ogre of the fairy tales"),
    'two_headed_ogre': (16, "an ogre with two heads and twice the appetite"),
    'komodo_brute': (13, "a dragon-lizard whose bite festers"),
    'desert_wraith': (12, "a traveller dried by Set's red land, who never found his tomb"),
    'hobgoblin_captain': (11, "a hobgoblin officer of the war-bands"),
    'mercenary_veteran': (12, "a veteran sell-sword of many wars"),
    'nosferatu': (12, "Stoker's word for the vampire: nothing courtly left in this breed"),
    'shadow': (17, "the shadow that drains strength with a touch"),
    'kobold_dragonshield': (16, "a kobold sworn to a dragon's service"),
    'intellect_devourer': (11, "a brain on legs that eats a mind and wears the body"),
    'ochre_jelly': (12, "a jelly that splits when struck"),
    'giant_spider': (11, "a spider the size of a horse"),
    'roc_chick': (11, "a roc chick already big enough to carry off a goat"),
    'cockatrice': (10, "the rooster-serpent whose touch turns flesh to stone"),
    'harpy': (8, "the snatchers of the Argonauts' tale, who stole King Phineus's food"),
    'giant_eagle': (9, "a giant eagle of the mountain eyries"),
    'cave_bear': (9, "the Ice Age cave bear, taller than any grizzly"),
    'nothic': (9, "a wizard's ruin, all one eye and hunger for secrets"),
    'animated_armor': (8, "a suit of armour that walks without a knight"),
    'wolf_pack_leader': (8, "the wolf who leads the pack"),
    'greater_imp': (9, "an imp grown greater on Hell's errands"),
    'cairn_wight': (9, "a wight of the Highland cairns"),
    'satyr_warrior': (7, "Dionysus's rout, armed"),
    'bugbear': (7, "the hulking bugbear of the nursery tales, grown real"),
    'carrion_crawler': (7, "the paralysing carrion-eater of the caves"),
    'grick': (8, "a worm with a beak and four tentacles that waits in the dark"),
    'rock_python': (8, "a python that crushes its prey"),
    'lizardfolk_shaman': (9, "a shaman of the lizard-folk"),
    'troglodyte': (7, "the cave-folk whose stench sickens before their clubs land"),
    'assassin_vine': (8, "the strangler fig that squeezes its host for years"),
    'nightmare_shade': (8, "a shade of the bad dream itself"),
    'duat_shade': (9, "a soul that failed the weighing in the Duat"),
    'giant_wasp': (6, "a wasp the size of a dog"),
    'kuo_toa': (6, "the fish-folk of the drowned halls"),
    'mud_crawler': (6, "a crawler of the flooded halls"),
    'phase_spider_lesser': (7, "a young phase spider, already slipping out of the world"),
    'piercer': (6, "a stalactite that drops on whoever walks beneath"),
    'satyr_trickster': (7, "a satyr of Dionysus's rout, all tricks and panic"),
    'wererat': (8, "the rat-man of the city sewers"),
    'huecuva': (7, "the Mapuche spirit of blight, in a vow-breaker's bones"),
    'skeleton_archer': (6, "a skeleton with a bow and a soldier's aim"),
    'orc_berserker': (5, "an orc in the battle-fury, past feeling his wounds"),
    'shadow_hound': (5, "a hound of shadow that hunts by the dark"),
    'swamp_serpent': (5, "a serpent of the flooded halls"),
    'crypt_thing': (5, "a crypt's own guardian, which sends intruders elsewhere"),
    'grave_guardian': (5, "a champion buried standing at the crypt door, sword in hand, held by his oath"),
    'vampire_thrall': (5, "a vampire's thrall, fed on its master's blood"),
})

# More moves across a tier line inside the deep, for the same reasons.
MOVES.update({
    'abyssal_overlord': (85, "an overlord rules a whole layer of the Abyss: it belongs in the abyss"),
    'arch_demon': (84, "a prince of Hell of the rank Binsfeld gave the seven sins: with the princes in the abyss"),
    'entropy_wraith': (86, "a wraith worn through to a hole in the shape of a ghost, where things come apart: the unmaking at the end"),
    'greater_lich': (64, "of Koschei the Deathless's kind, whose death is hidden in a needle in an egg in a duck in a hare in an iron chest"),
    'frostfang_giant': (70,"Jotunheim's outcast frost giants: the rime halls, where the swan-shirt story already meets one (floors 71-80)"),
})

# Lore that the move brings out: kind -> fields written as they are here.
RETUNE: dict[str, dict] = {
    # "it rules the dead here exactly as it once ruled the living... The crown
    # is still on the skull. The court still bows." In the abyss its court
    # comes when it calls: the dead knights who serve it (and the abyss keeps
    # a summoner among every fifty of its kinds: test_late_game_monsters).
    'lich_sovereign': {'summon_kind': ['grave_knight', 'death_knight'], 'summon_max': 3,
                       'summon_cooldown': 8},
}

# The deep kinds added where a family had no member at a depth (their full
# data: tools/content/monster_pass_new_kinds_2026_11_17.py).
from monster_pass_new_kinds_2026_11_17 import NEW_KINDS  # noqa: E402

PLANNED_NEW = {k: (v['peak'], v['family']) for k, v in NEW_KINDS.items()}
SIZES = os.path.join(ROOT, 'data', 'monster_sizes.json')


def load() -> dict:
    with open(MONSTERS, encoding='utf-8') as f:
        return json.load(f)


def band(floor) -> int:
    return max(1, min(5, (int(floor) - 1) // 20 + 1))


def _die_for(peak: int) -> int:
    return 12 if peak > 60 else 10


def hp_dice(target: float, peak: int) -> str:
    """Health dice in the deep kinds' style (about 0.6 of it in the dice)."""
    die = _die_for(peak)
    avg = (die + 1) / 2
    n = max(1, int(round(0.6 * target / avg)))
    mod = int(round(target - n * avg))
    return f"{n}d{die}+{mod}" if mod > 0 else (f"{n}d{die}{mod}" if mod < 0 else f"{n}d{die}")


def blow_dice(avg: float, peak: int) -> str:
    die = 10 if peak > 60 else 8
    if avg < 4:
        return '1d4' if avg < 3 else '1d6'
    dav = (die + 1) / 2
    n = max(1, int(round(0.35 * avg / dav)))
    mod = int(round(avg - n * dav))
    return f"{n}d{die}+{mod}" if mod > 0 else f"{n}d{die}"


class Floors:
    """What the kinds this pass leaves alone look like, floor by floor: the
    median blow (respawn_by_hp.monster_damage) and the median spawn weight of
    the ordinary random spawns peaking near a floor. The floor_curve damage
    anchors run under the data on floors 20-50 (the kinds there hit about
    twice the anchor), so a moved kind is sized against its new neighbours,
    not against the anchor, and the floor plays as it did."""

    def __init__(self, mons: dict):
        self.rows = []
        for k, m in mons.items():
            if k in MOVES or k in NEW_KINDS or not rs.is_random_spawn(m):
                continue
            if m.get('is_boss') or m.get('is_mini_boss') or m.get('is_seal_demon'):
                continue
            self.rows.append((int(m['peak_floor']), rs.monster_damage(m), float(m['peak_weight']),
                              float(m.get('thac0', 20)), float(m.get('thac0_lore', m.get('thac0', 20)))))

    def _near(self, floor: int, col: int) -> float:
        for width in (3, 5, 8, 12, 20):
            vals = [r[col] for r in self.rows if abs(r[0] - floor) <= width]
            if len(vals) >= 8:
                return statistics.median(vals)
        return statistics.median(r[col] for r in self.rows)

    def dmg(self, floor: int) -> float:
        return self._near(floor, 1)

    def weight(self, floor: int) -> float:
        return self._near(floor, 2)

    def aim(self, floor: int) -> float:
        """Median written THAC0 of the ordinary kinds near this floor."""
        return self._near(floor, 3)

    def lore_aim(self, floor: int) -> float:
        return self._near(floor, 4)


def move_one(mid: str, m: dict, peak: int, med: dict) -> dict:
    """Re-bake one kind at `peak`. Returns a change note."""
    old_peak = int(m.get('peak_floor') or m.get('min_level') or 1)
    old_hp = rs.dice_avg(m['hp'])
    seat = rs.SWARM_SEAT_MULT.get(mid, 1.0)
    want = rs.target_hp(peak) / seat
    new_hp = hp_dice(want, peak)
    # The respawn tool must seat it here: nudge the health until it does.
    for _ in range(40):
        got = rs.fit_floor(rs.dice_avg(new_hp) * seat)
        if got == peak:
            break
        want *= 1.02 if got < peak else 0.98
        new_hp = hp_dice(want, peak)
    note = {'id': mid, 'from': old_peak, 'to': peak, 'hp': (m['hp'], new_hp)}
    m['hp'] = new_hp
    # Blows: as hard against its new neighbours as against its old ones,
    # within KEEP_LO..KEEP_HI, and no blow past the spike cap.
    floors = med[2]
    old_dmg = rs.monster_damage(m)
    if old_dmg > 0:
        r = max(KEEP_LO, min(KEEP_HI, old_dmg / floors.dmg(old_peak)))
        k = floors.dmg(peak) * r / old_dmg
        cap = SPIKE * rs.target_dmg(peak)
        for a in m.get('attacks') or []:
            cur = rs.dice_avg(a.get('damage', 0))
            if cur <= 0:
                continue
            a['damage'] = blow_dice(min(cap, cur * k), peak)
    # Aim: the same distance from its neighbours' median as before, both the
    # written THAC0 (against the kinds that stay) and the lore THAC0 (so a
    # later rebake_thac0 run keeps it there too).
    old_lore = float(m.get('thac0_lore', m.get('thac0', 20)))
    m['thac0_lore'] = int(round(floors.lore_aim(peak) + (old_lore - floors.lore_aim(old_peak))))
    old_aim = float(m.get('thac0', 20))
    m['thac0'] = int(round(floors.aim(peak) + (old_aim - floors.aim(old_peak))))
    # Spawn: no more common at its new depth than the kinds already there.
    m['peak_floor'] = peak
    m['spread'] = rs.spread_for(peak)
    m['min_level'] = max(1, peak - rs.lead_for(peak))
    if band(peak) > band(old_peak):
        m['peak_weight'] = round(min(float(m.get('peak_weight') or 1.0), floors.weight(peak)), 1)
    if m.get('regeneration'):
        m['regeneration'] = int(round(m['regeneration'] * math.sqrt(rs.dice_avg(new_hp) / old_hp)))
    t = band(peak)
    m['harvest_tier'] = max(int(m.get('harvest_tier') or 1), t)
    tr = m.get('treasure')
    if isinstance(tr, dict):
        tr['item_tier'] = max(int(tr.get('item_tier') or 1), t)
    return note


def new_one(mid: str, spec: dict, med: dict) -> dict:
    """A new kind's record, its numbers baked at its floor."""
    peak, seat = int(spec['peak']), float(spec.get('seat', 1.0))
    if abs(rs.SWARM_SEAT_MULT.get(mid, 1.0) - seat) > 1e-9:
        raise SystemExit(f"{mid}: put {seat} in respawn_by_hp.SWARM_SEAT_MULT first")
    want = rs.target_hp(peak) / seat
    hp = hp_dice(want, peak)
    for _ in range(40):
        got = rs.fit_floor(rs.dice_avg(hp) * seat)
        if got == peak:
            break
        want *= 1.02 if got < peak else 0.98
        hp = hp_dice(want, peak)
    cap = SPIKE * rs.target_dmg(peak)
    attacks = []
    for a in spec['attacks']:
        a = dict(a)
        w = a.pop('w')
        a['damage'] = blow_dice(min(cap, w * med[2].dmg(peak)), peak)
        attacks.append(a)
    lore_aim = int(round(med[2].lore_aim(peak) + int(spec.get('aim', 0))))
    written_aim = int(round(med[2].aim(peak) + int(spec.get('aim', 0))))
    skip = ('peak', 'aim', 'seat', 'size', 'attacks')
    m = {k: v for k, v in spec.items() if k not in skip}
    rec = {
        'name': m.pop('name'), 'symbol': m.pop('symbol'), 'color': m.pop('color'),
        'hp': hp, 'speed': m.pop('speed', 10), 'ai_pattern': m.pop('ai_pattern', 'aggressive'),
        'thac0': written_aim, 'peak_floor': peak, 'spread': rs.spread_for(peak),
        'peak_weight': m.pop('peak_weight', 2.0), 'min_level': max(1, peak - rs.lead_for(peak)),
        'attacks': attacks, 'resistances': [], 'weaknesses': [], 'tags': m.pop('tags'),
        'family': m.pop('family'), 'pronoun': m.pop('pronoun'), 'harvest_tier': band(peak),
        'treasure': m.pop('treasure'), 'lore': m.pop('lore'), 'frequency': m.pop('frequency', 2),
    }
    rec.update(m)
    rec.update({'thac0_lore': lore_aim, 'shrugs_off': [], 'status_immune': [], 'status_weak': []})
    return rec


def apply(mons: dict) -> list:
    med = (None, None, Floors(mons))     # (kept as a tuple: med[2] is what is used)
    notes = []
    for mid, (peak, _why) in MOVES.items():
        m = mons[mid]
        if int(m.get('peak_floor') or 0) == peak:
            continue
        notes.append(move_one(mid, m, peak, med))
    for mid, spec in NEW_KINDS.items():
        if mid not in mons:
            mons[mid] = new_one(mid, spec, med)
            notes.append({'id': mid, 'from': None, 'to': spec['peak'], 'hp': (None, mons[mid]['hp'])})
    for mid, fields in RETUNE.items():
        mons[mid].update(fields)
    return notes


def write_sizes() -> int:
    import jsonfmt
    data, fmt = jsonfmt.load(SIZES)
    n = 0
    for mid, spec in NEW_KINDS.items():
        if data['sizes'].get(mid) != spec['size']:
            data['sizes'][mid] = spec['size']
            n += 1
    if n:
        jsonfmt.save(SIZES, data, fmt)
    return n


def census(mons: dict, planned_new: bool = True) -> tuple:
    ordinary = collections.Counter()
    fam = collections.defaultdict(collections.Counter)
    for k, m in mons.items():
        if m.get('is_boss') or m.get('is_mini_boss'):
            continue
        pf = m.get('peak_floor') or m.get('min_level')
        if not pf or pf <= 0 or pf > 100:
            continue
        ordinary[band(pf)] += 1
        fam[m.get('family') or 'none'][band(pf)] += 1
    if planned_new:
        for k, (pf, f) in PLANNED_NEW.items():
            if k in mons:
                continue
            ordinary[band(pf)] += 1
            fam[f][band(pf)] += 1
    return ordinary, fam


def verdict(c: collections.Counter) -> str:
    counts = [c.get(i, 0) for i in range(1, 6)]
    n = sum(counts)
    if min(counts) == 0:
        return 'gap'
    if n < 10:
        return 'ok'
    share = [x / n for x in counts]
    return 'lopsided' if max(share) > 0.35 or min(share) < 0.10 else 'ok'


def spawn_checks(mons: dict) -> list:
    """The tests/test_spawn_curve.py conditions, on this data."""
    placement = {mid: (d['peak_floor'], d['spread'], d['min_level'])
                 for mid, d in mons.items() if rs.is_random_spawn(d)}
    bad = []
    for lvl in range(1, 101):
        st = rs.floor_stats(mons, placement, lvl)
        ratio = st['hp50'] / rs.target_hp(lvl)
        if not 0.55 <= ratio <= 1.25:
            bad.append(f"floor {lvl}: median HP ratio {ratio:.2f}")
        if st['kinds'] < 20 or st['neff'] < 8:
            bad.append(f"floor {lvl}: thin ({st['kinds']} kinds, Neff {st['neff']:.1f})")
    for mid, (peak, _s, min_level) in placement.items():
        spike = rs.max_attack(mons[mid])
        if spike > 5.0 * rs.target_dmg(min_level):
            bad.append(f"{mid}: spike {spike:.0f} at min_level {min_level}")
    copy = json.loads(json.dumps(mons))
    fixes = rs.apply_stat_fixes(copy)
    if fixes:
        bad += ['stat fix: ' + x for x in fixes]
    plan = rs.plan(copy)
    drift = {k: (placement[k], v) for k, v in plan.items() if placement.get(k) != v}
    if drift:
        bad += [f"respawn would move {k}: {a} -> {b}" for k, (a, b) in list(drift.items())[:20]]
    return bad


def floor_table(mons: dict) -> str:
    placement = {mid: (d['peak_floor'], d['spread'], d['min_level'])
                 for mid, d in mons.items() if rs.is_random_spawn(d)}
    out = []
    for lvl in (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 20, 22, 25, 30, 35, 40, 45, 50, 55, 60,
                65, 70, 75, 80, 85, 90, 95, 100):
        st = rs.floor_stats(mons, placement, lvl)
        out.append(f"L{lvl:3} kinds {st['kinds']:4} neff {st['neff']:6.1f} "
                   f"hp50/target {st['hp50'] / rs.target_hp(lvl):4.2f}")
    return '\n'.join(out)


def report(mons: dict) -> None:
    ordinary, fam = census(mons)
    counts = [ordinary.get(i, 0) for i in range(1, 6)]
    n = sum(counts)
    print('ordinary', counts, [f"{c / n:.0%}" for c in counts], verdict(ordinary))
    for f in sorted(fam):
        c = fam[f]
        print(f"  {f:16}", [c.get(i, 0) for i in range(1, 6)], verdict(c))
    t1 = sum(1 for k in MOVES if band(load()[k].get('peak_floor') or 1) == 1)
    print(f"moves: {len(MOVES)} ({t1} out of tier 1); new kinds planned: {len(PLANNED_NEW)}")


def main(argv=None) -> int:
    import lore_pass_guard
    lore_pass_guard.refuse("monster_pass_2026_11_17", argv)
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--floors', action='store_true')
    a = ap.parse_args(argv)
    mons = load()
    notes = apply(mons)
    report(mons)
    bad = spawn_checks(mons)
    print(f"{len(notes)} kinds re-baked; spawn-curve problems: {len(bad)}")
    for b in bad[:40]:
        print('  ', b)
    if a.floors:
        print(floor_table(mons))
    if a.write:
        with open(MONSTERS, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(mons, f, indent=2, ensure_ascii=False)
            f.write('\n')
        print('written', MONSTERS, '; sizes added:', write_sizes())
    return 0


if __name__ == '__main__':
    sys.exit(main())
