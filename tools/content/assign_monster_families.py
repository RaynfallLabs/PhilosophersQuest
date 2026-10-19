"""Give every monster in data/monsters.json its ONE family (offline tool).

MONSTER_FAMILIES_DESIGN.md: families are sorted by what a creature IS, so each
family has one signature the hero can learn. The game reads the written
`family` field (src/family_lore.py); this script is how the field is
proposed, written and re-checked. Tags are NOT changed: they still drive
weapons and materials (silver still bites a dracolich filed under Dragons).

    python tools/content/assign_monster_families.py            # report
    python tools/content/assign_monster_families.py --write    # write the field
    python tools/content/assign_monster_families.py --check    # exit 1 on any drift
    python tools/content/assign_monster_families.py --sheet    # decision record
    python tools/content/assign_monster_families.py --rates 6    # what a run meets, and its ladder

How a family is chosen:
  1. FINAL: every monster that fits two or more families, settled by its
     LORE (its own `lore` text and the source myth), never by its tags or by
     which family would balance the counts (Brandon, 2026-10-18: "settle each
     one yourself, finally, by its lore"). Each pick carries the runner-up
     and a one-line reason; `--sheet` prints them as a table.
  2. Otherwise a rule classifier over tags and the id's words (`classify`).

`family_for(mid, defn)` is what the monster generators call for a NEW
monster, so a regeneration keeps the field (they keep a written family
first, so a later hand edit survives too).

Death, the secret cow and the ethereal unicorn are not in monsters.json
(they are built in code) and have no family. The Bones ghost is a Ghost
(src/family_lore.py SPECIAL_KINDS).
"""
from __future__ import annotations

import collections
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import jsonfmt  # noqa: E402

MONSTERS = ROOT / 'data' / 'monsters.json'
FAMILIES = ROOT / 'data' / 'monster_families.json'

# The 22 families (ids as written in monsters.json). Spiders were merged
# into Vermin (2026-10-18): a run meets only about four spider kinds, too
# few for a ladder, and the medieval 'vermin' took in spiders too.
FAMILY_IDS = (
    'restless_dead', 'ghosts', 'vampires_liches', 'demons', 'dragons',
    'giants', 'goblinkin', 'mortals', 'fair_folk', 'great_beasts', 'vermin',
    'serpents', 'birds', 'gorgons', 'legend', 'shapeshifters',
    'constructs', 'elementals', 'oozes', 'aberrations', 'plants', 'celestials',
)

# ---------------------------------------------------------------------------
# 1. Lore-settled picks: (family, runner-up, reason). Final, not provisional.
# ---------------------------------------------------------------------------
FINAL = {
    # --- the draft's word-match slips ---------------------------------------
    'battle_mage': ('mortals', '-', "A tattooed human war-wizard; the draft matched 'bat' inside his id."),
    'locust_cultist': ('mortals', 'vermin', "Soldiers of the Cult of the Locust: men who serve the swarm, not insects."),
    'locust_herald': ('mortals', 'vermin', "A messenger of the Locust cult, a man who talks well and fights badly."),
    'void_crawler': ('aberrations', 'vermin', "A many-limbed thing that came through where magic wore the world thin."),
    'snake_charmer': ('mortals', 'serpents', "A human charmer out of the bazaars of Samarkand; the snakes are his tools."),
    'spectral_lord': ('ghosts', 'restless_dead', "A warlord's ambition drawn in pale light; steel passes through it like smoke."),
    'gelatinous_titan': ('oozes', 'giants', "A gelatinous cube grown to fill a corridor: an ooze, whatever its name."),
    'primordial_titan': ('giants', 'aberrations', "One of Earth's first monstrous children, older than Kronos: a titan."),
    'totentanz_dancer': ('restless_dead', 'ghosts', "The skeletons of the Dance of Death, come down off the church wall."),
    # --- vermin ---------------------------------------------------------------
    'carrion_crawler': ('vermin', 'aberrations', "A carrion-eating caterpillar as long as a horse: an outsized cave insect."),
    'grick': ('vermin', 'aberrations', "A rock-coloured worm that waits in cracks: a dungeon pest, not a thing from beyond."),
    'frost_crawler': ('vermin', 'elementals', "A wagon-long centipede of the frozen levels; the frost is where it lives, not what it is."),
    'khrafstra_swarm': ('vermin', 'demons', "The Avesta's noxious creatures are snakes, scorpions and stinging flies: vermin, though evil made them."),
    'grid_bug': ('vermin', 'aberrations', "A tiny scuttling bug with a static bite."),
    'piercer': ('vermin', 'aberrations', "A cave snail whose shell is a stone spike."),
    'stirge_swarm': ('vermin', 'birds', "Fist-sized, bat-winged bloodsuckers that come in swarms."),
    'bat': ('vermin', 'birds', "A cave bat: a mammal pest, not a bird."),
    # --- goblinkin ------------------------------------------------------------
    'kobold': ('goblinkin', 'fair_folk', "The German mine-sprite is the goblin's own cousin in name and nature; here a warren of trap-makers."),
    'kobold_sorcerer': ('goblinkin', 'fair_folk', "A caster of the kobold warrens, kin to the goblins."),
    'kobold_trapsetter': ('goblinkin', 'fair_folk', "The kobold warren's pit-and-tripwire maker."),
    'kobold_dragonshield': ('goblinkin', 'dragons', "A kobold in a dead dragon's belly plates; the armour is borrowed, the kobold is not a dragon."),
    'kobold_pack_leader': ('goblinkin', 'fair_folk', "The chief of a kobold warren."),
    # --- the fair folk --------------------------------------------------------
    'dark_elf': ('fair_folk', 'mortals', "Snorri's dark elves who live down in the earth: elves, not men."),
    'drow_warrior': ('fair_folk', 'mortals', "Trained from the cradle in the dark elves' sunless cities."),
    'drow_mage': ('fair_folk', 'mortals', "A sorcerer of the dark elves."),
    'drow_priestess': ('fair_folk', 'mortals', "A priestess of the dark elves."),
    'banshee': ('fair_folk', 'ghosts', "Bean sidhe means 'woman of the fairy mound': a fairy herald of death, not a dead woman."),
    'dullahan_spawn': ('fair_folk', 'ghosts', "The Dullahan is an Irish unseelie rider who names the dying and cannot bear gold, a fairy's weakness."),
    'changeling': ('fair_folk', 'shapeshifters', "The fairies' own child, left in a stolen baby's cradle."),
    'green_knight': ('fair_folk', 'mortals', "Bertilak under Morgan le Fay's enchantment, who picks up his own head: the otherworld is the heart of his tale."),
    'mara': ('fair_folk', 'ghosts', "The Norse night-hag a witch sends to trample sleepers: a spirit of folk belief, never a dead soul."),
    'wild_hunt_captain': ('fair_folk', 'ghosts', "The sky riders of Herne and of King Herla, who came back from the fairy king's hall unable to dismount."),
    'nibelung_hoardwarden': ('fair_folk', 'mortals', "Alberich's dwarf wardens in the Tarnkappe: the hidden folk of the earth, kin to the dark elves."),
    'baba_yaga': ('fair_folk', 'mortals', "The bony-legged hag of the Russian forest in her chicken-legged hut: a hag, not a village witch."),
    # --- ghosts ---------------------------------------------------------------
    'hecate_hound': ('ghosts', 'restless_dead', "Hecate's spectral hounds that patrol the edge of the underworld."),
    'shadow_hound': ('ghosts', 'great_beasts', "Black Shuck's kind, 'cold, half there': a phantom dog."),
    'fetch': ('ghosts', 'shapeshifters', "The Irish fetch is a wraith: the apparition of a living person's double."),
    'whispering_crone': ('ghosts', 'vampires_liches', "Buried alive, she whispers from the grave and the spectres answer her."),
    'ker': ('ghosts', 'demons', "Hesiod's Keres are death-spirits that fight over the blood of the fallen."),
    'sluagh': ('ghosts', 'fair_folk', "The host of the unforgiven dead, turned away by Heaven and earth alike."),
    # --- the restless dead ----------------------------------------------------
    'hels_handmaid': ('restless_dead', 'ghosts', "Hel's slow-walking servants among her dead, who stand up what the living put down."),
    'skeletal_giant': ('restless_dead', 'giants', "A giant's bones made to walk: undeath is what moves it."),
    'gashadokuro': ('restless_dead', 'giants', "The starving skeleton built from the bones of the unburied dead."),
    'undead_colossus': ('restless_dead', 'constructs', "A necromancer's raising of dead giants' limbs; it drains the living."),
    'bone_titan': ('restless_dead', 'constructs', "Giants' skeletons raised by a necromancer to hold a wing of the dungeon."),
    'flesh_colossus': ('restless_dead', 'constructs', "A battlefield of corpses a necromancer stitched into one; it mends itself with the dead."),
    'bone_collector': ('restless_dead', 'constructs', "The bones of failed adventurers that breathe and hunt for one more piece."),
    'charnel_hound': ('restless_dead', 'constructs', "The necromancer's copy of the church grim: a pack's worth of dog bones raised."),
    'bone_golem': ('constructs', 'restless_dead', "A golem; its own lore says no ghost lives in it and it follows its last order."),
    'hrungnirs_ghost': ('giants', 'ghosts', "Hrungnir was the strongest of the stone-hearted giants; his ghost still hurls stone and wants a rematch."),
    'wendigo': ('shapeshifters', 'giants', "A starving person who ate human flesh and became the ice-hearted cannibal."),
    # --- vampires and liches --------------------------------------------------
    'death_mage': ('vampires_liches', 'restless_dead', "A necromancer gone halfway into the grave to keep studying: an undead sorcerer."),
    'bone_witch': ('vampires_liches', 'restless_dead', "A Baba Yaga who kept nothing but the bones and all of the witchcraft."),
    'necromancer_lord': ('vampires_liches', 'restless_dead', "Koschei the Deathless hid his death in a needle: the first phylactery."),
    'pale_master': ('vampires_liches', 'restless_dead', "A necromancer who would not wait for death and grafted the grave onto himself."),
    'skeleton_necromancer': ('vampires_liches', 'restless_dead', "A necromancer who outlived his own body and kept his art."),
    'crypt_summoner': ('vampires_liches', 'restless_dead', "A dead necromancer still keeping the ledger of his crypt."),
    'neferkaptah_risen': ('vampires_liches', 'restless_dead', "The magician prince who took the Book of Thoth, still a sorcerer in death."),
    'banshee_lich': ('vampires_liches', 'ghosts', "A lich: the name is the voice it kept, the undeath is the sorcerer's."),
    'jiangshi': ('vampires_liches', 'restless_dead', "The hopping corpse that drinks the breath of life: China's vampire."),
    # --- demons ---------------------------------------------------------------
    'abyssal_mimic': ('demons', 'aberrations', "Something from the pit crawled inside a mimic and stayed; fire and prayer show its real shape."),
    'hellmouth': ('demons', 'aberrations', "The jaws of Leviathan: Hell's own mouth from the Doom paintings."),
    'deadite': ('demons', 'restless_dead', "A Kandarian demon wearing a body, living or dead."),
    'fresh_deadite': ('demons', 'restless_dead', "A Kandarian demon in a body only just taken."),
    'risen_deadite': ('demons', 'restless_dead', "A Kandarian demon that climbed into a corpse."),
    'iron_horseman': ('demons', 'constructs', "A thing that rides in the dust of the Four Horsemen, rider and mount grown into one iron shape."),
    'erinyes_greater': ('demons', 'legend', "The Furies who hunted Orestes: underworld spirits of vengeance, kin to Hell's erinyes."),
    'erinyes_lesser': ('demons', 'legend', "Its own lore names them Hell's devils of that name."),
    'void_seraph': ('demons', 'celestials', "A seraph that fell and kept its wings."),
    'azarael': ('demons', 'celestials', "One of the Powers who fell with Lucifer."),
    'abaddon_destroyer': ('demons', 'celestials', "The angel of the bottomless pit and king of its locusts."),
    'camazotz': ('demons', 'great_beasts', "The death bat of Xibalba, servant of the underworld lords."),
    'empusa': ('demons', 'shapeshifters', "Hecate's demonesses; the shapes are only their disguise."),
    'succubus_shade': ('demons', 'ghosts', "A succubus of the old demonologies, worn thin but still a demon."),
    'cerberus': ('legend', 'demons', "Echidna's child, the hound of Hades from Heracles' twelfth labour."),
    'hell_bovine': ('great_beasts', 'demons', "Cattle, however infernal their pasture."),
    'cow_king': ('great_beasts', 'demons', "The king of the hell bovines: a bull with a crown."),
    'sets_jackal': ('great_beasts', 'demons', "Jackals of the red desert that hunt the living for Set."),
    # --- dragons and serpents -------------------------------------------------
    'dracolich': ('dragons', 'vampires_liches', "A dragon that bound its soul to keep its hoard; the bones kept the cunning and the hoard."),
    'elder_dracolich': ('dragons', 'vampires_liches', "The oldest of the dead dragons, still a dragon in bone."),
    'lich_dragon_spawn': ('dragons', 'vampires_liches', "The dead-hatched get of a dracolich: a dragon's cunning, none of its warmth."),
    'spectral_dragon': ('dragons', 'ghosts', "A dragon's greed for its hoard that outlasted its flesh."),
    'undead_dragon_lesser': ('dragons', 'restless_dead', "A dragon of Cadmus's line raised whole; the dragon is the point."),
    'abyssal_dragon': ('dragons', 'demons', "A dragon hatched and reared in the pit: Saint George would know the shape."),
    'dahaka_wyrm': ('dragons', 'demons', "Azhi Dahaka, the three-headed dragon of the Avesta."),
    'tiamat': ('dragons', 'legend', "The game wakes her in her later shape: five dragon heads, queen of dragonkind."),
    'lindworm': ('dragons', 'serpents', "The wingless dragon of the Danish tale of King Lindworm."),
    'nidhogg_brood': ('dragons', 'serpents', "Brood of Nidhoggr, the corpse-gnawing dragon at Yggdrasil's root."),
    'nidhoggr_fragment': ('dragons', 'serpents', "A piece of Nidhoggr, who flies with corpses under his wings after Ragnarok."),
    'world_serpent': ('serpents', 'dragons', "The Midgard Serpent's kind: a sea snake grown until it circles the world."),
    'jormungandr_juvenile': ('serpents', 'dragons', "Loki's serpent child, the young Midgard Serpent, and its venom kills Thor."),
    'behir_lesser': ('serpents', 'legend', "Forty feet of many-legged serpent that crushes what its lightning spares."),
    'sobek_warrior': ('serpents', 'mortals', "Crocodile-headed soldiers of Sobek who fight as the river beast does."),
    'kuo_toa': ('serpents', 'aberrations', "Slime-skinned fish-folk of the sunless seas: swamp-kin."),
    'viper_priestess': ('mortals', 'serpents', "Priestesses of the Minoan snake goddess: women who serve the serpent."),
    'deep_one_priest': ('aberrations', 'serpents', "Lovecraft's deep ones, praying to something under the sea."),
    'hydra': ('legend', 'serpents', "The Lernaean Hydra of Heracles' second labour."),
    'mythic_hydra': ('legend', 'serpents', "Of the Lernaean Hydra's blood, grown for centuries."),
    'echidna': ('legend', 'serpents', "The mother of monsters herself, half nymph and half serpent."),
    'lamia': ('legend', 'serpents', "The Libyan queen whom Hera's jealousy turned into a child-stealer."),
    'tiamat_blood': ('oozes', 'aberrations', "Tiamat's divided blood still crawls, and a small cut makes two of it."),
    'basilisk': ('gorgons', 'serpents', "Pliny's king of serpents whose look kills: the killing gaze is the point."),
    'basilisk_lesser': ('gorgons', 'serpents', "A young basilisk, gaze and all."),
    'elder_basilisk': ('gorgons', 'serpents', "An old basilisk, gaze and all."),
    'cockatrice': ('gorgons', 'birds', "The rooster-headed serpent whose touch turns flesh to stone."),
    'catoblepas': ('gorgons', 'great_beasts', "Pliny's downward-looking beast; whoever meets its eyes drops dead."),
    # --- giants, elementals, constructs, plants -------------------------------
    'surtur': ('giants', 'elementals', "A fire jotunn: a giant first, fire second."),
    'ymir_last_spawn': ('giants', 'elementals', "Ymir was the first frost giant, father of all the jotnar."),
    'titanspawn': ('giants', 'elementals', "What leaks up from the Titans in Tartarus, an old anger in bedrock."),
    'mere_wife': ('giants', 'legend', "Grendel's mother, of the giant-kin of Cain; only a giant's blade bit her."),
    'cacus': ('giants', 'legend', "Vulcan's fire-breathing giant son, strangled by Hercules."),
    'asag_stone_warrior': ('elementals', 'constructs', "Fathered by Asag on the mountains: stone born alive, never carved."),
    'gorgon_warrior': ('constructs', 'gorgons', "Topsell's gorgon cast in bronze by dungeon smiths."),
    'gilded_mimic': ('aberrations', 'constructs', "A mimic old enough to spread itself out as a whole hoard."),
    'moss_sentinel': ('plants', 'constructs', "Moss crept over a forgotten stone and gave it a body."),
    'corrupted_treant': ('plants', 'fair_folk', "A tree-shepherd poisoned at the roots: a tree first."),
    'wormwood_blight': ('plants', 'demons', "What grew where the star Wormwood's ash settled: a spore-shedding blight."),
    'lahamu': ('aberrations', 'oozes', "A shifting bulk of clay and coils from the first silt of creation."),
    # --- birds, beasts, legend, spiders, shapeshifters ------------------------
    'tengu_warrior': ('birds', 'fair_folk', "The crow-headed tengu of Japan's mountains."),
    'harpy': ('birds', 'legend', "A woman's face on a vulture's body: the snatchers who plagued Phineus."),
    'peryton': ('birds', 'legend', "Borges' winged stags with the plumage of birds."),
    'griffin': ('birds', 'legend', "Eagle before and lion behind: a winged watchman of the gold mountains."),
    'anzu_bird': ('birds', 'legend', "The lion-headed eagle of Sumer who stole the Tablet of Destinies."),
    'girtablilu': ('legend', 'vermin', "The scorpion-man who guarded the gate of Mount Mashu for Gilgamesh."),
    'carbuncle': ('legend', 'great_beasts', "Known only from explorers' tales of a jewel shining in the night forest."),
    'bonnacon': ('legend', 'great_beasts', "A marvel of the medieval bestiaries with curled horns and burning dung."),
    'death_dog': ('great_beasts', 'legend', "Orthrus's breed gone to seed: two-headed dogs."),
    'hook_horror': ('great_beasts', 'aberrations', "A beetle-bodied pack predator of the deep caves that talks by clacking."),
    'darkmantle': ('aberrations', 'vermin', "It spills a magical blackness no flame can push back."),
    'displacer_beast': ('great_beasts', 'aberrations', "A six-legged panther that throws its image to one side."),
    'blink_dog': ('great_beasts', 'fair_folk', "Teleporting canines that live in packs."),
    'anansi': ('vermin', 'fair_folk', "The Akan spider-trickster; every tale is a 'spider story'."),
    'jorogumo': ('vermin', 'shapeshifters', "A four-hundred-year-old spider that learns a woman's shape."),
    'each_uisce': ('shapeshifters', 'fair_folk', "The Highland water horse that waits as a horse or a handsome stranger."),
    'puca': ('shapeshifters', 'fair_folk', "Comes as a black horse, a goat, a hare or a small dark man."),
    'lyssa_madness': ('celestials', 'demons', "The spirit of mad rage the gods send, who protests the order and obeys."),
    'sown_warrior': ('mortals', 'legend', "Armed men who came up from the dragon's teeth Cadmus sowed."),
    'mind_flayer_thrall': ('mortals', 'aberrations', "A scholar or soldier whose mind a flayer emptied."),
}


# ---------------------------------------------------------------------------
# 2. The rule classifier, for everything FINAL does not settle.
# ---------------------------------------------------------------------------
def _words(mid: str) -> set:
    return set(mid.split('_'))


def _any_word(mid: str, *words) -> bool:
    w = _words(mid)
    return any(x in w for x in words)


def _any_sub(mid: str, *subs) -> bool:
    return any(s in mid for s in subs)


def classify(mid: str, defn: dict) -> str | None:
    """A family from the tags and the id's words. Word matches, not
    substrings, wherever a short word could hide inside another id
    ('bat' in battle_mage)."""
    t = set(defn.get('tags') or [])
    if 'celestial' in t:
        return 'celestials'
    if 'dragon' in t:
        return 'dragons'
    if 'demon' in t:
        return 'demons'
    if _any_sub(mid, 'medusa', 'gorgon', 'stheno', 'euryale', 'basilisk', 'cockatrice',
                'catoblepas') and 'construct' not in t:
        return 'gorgons'
    if 'undead' in t:
        if _any_sub(mid, 'vampire', 'nosferatu', 'strigoi', 'vrykolakas', 'jiangshi', 'lich'):
            return 'vampires_liches'
        if _any_sub(mid, 'wraith', 'specter', 'spectre', 'spectral', 'shadow', 'shade', 'banshee',
                    'poltergeist', 'allip', 'wisp', 'spirit', 'ghost', 'haunting', 'sluagh', 'echo',
                    'fetch', 'filcher', 'soul_eater', 'lesser_death', 'nightwing', 'hollow_one',
                    'forsaken', 'crone'):
            return 'ghosts'
        return 'restless_dead'
    if 'giant' in t or 'troll' in t or _any_sub(mid, 'ogre', 'ettin', 'cyclops', 'titan',
                                                 'fomorian'):
        return 'giants'
    if 'shapeshifter' in t and _any_sub(mid, 'were'):
        return 'shapeshifters'
    if 'construct' in t:
        return 'constructs'
    if 'elemental' in t or _any_sub(mid, 'djinn', 'jinni', 'xorn'):
        return 'elementals'
    if _any_sub(mid, 'ooze', 'jelly', 'pudding', 'slime', 'gelatinous', 'acid_blob'):
        return 'oozes'
    if 'plant' in t:
        return 'plants'
    if _any_sub(mid, 'spider', 'arachne', 'ettercap', 'web_spinner'):
        return 'vermin'            # spiders belong to Vermin, Spiders and Swarms
    if _any_sub(mid, 'eagle', 'roc_', 'stymphalian', 'raven', 'thunderbird', 'strix', 'harpy'):
        return 'birds'
    if _any_sub(mid, 'chimera', 'manticore', 'sphinx', 'scylla', 'charybdis', 'ammit', 'minotaur',
                'kusarikku', 'nue'):
        return 'legend'
    if 'fey' in t:
        return 'fair_folk'
    if t & {'goblin', 'goblinoid', 'orc', 'kobold', 'gnoll'}:
        return 'goblinkin'
    if 'reptile' in t or _any_word(mid, 'frog', 'toad', 'bullywug', 'troglodyte', 'serpent',
                                    'snake', 'cobra', 'python', 'naga', 'lizard', 'lizardfolk'):
        return 'serpents'
    if _any_word(mid, 'rat', 'beetle', 'centipede', 'scorpion', 'wasp', 'mantis', 'grub', 'scarab',
                 'crawler'):
        return 'vermin'
    if 'aberration' in t:
        return 'aberrations'
    if 'beast' in t:
        return 'great_beasts'
    if 'humanoid' in t:
        return 'mortals'
    return None


def family_for(mid: str, defn: dict) -> str | None:
    """The family a monster should carry: the lore-settled pick, else the
    classifier's. What the monster generators call for a new monster."""
    if mid in FINAL:
        return FINAL[mid][0]
    return classify(mid, defn)


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
def _with_family(defn: dict, fam: str) -> dict:
    """The monster's dict with `family` set, written right after `tags`."""
    if defn.get('family') == fam:
        return defn
    out = {}
    for k, v in defn.items():
        if k == 'family':
            continue
        out[k] = v
        if k == 'tags':
            out['family'] = fam
    if 'family' not in out:
        out['family'] = fam
    return out


def proposals(data: dict) -> dict:
    return {mid: family_for(mid, d) for mid, d in data.items()}


def check(data: dict) -> list[str]:
    errs = []
    want = proposals(data)
    for mid, d in data.items():
        fam = d.get('family')
        if fam not in FAMILY_IDS:
            errs.append(f'{mid}: family {fam!r} is not one of the 22')
        elif fam != want[mid]:
            errs.append(f'{mid}: written {fam!r}, the script says {want[mid]!r}')
    for mid in FINAL:
        if mid not in data:
            errs.append(f'FINAL names {mid!r}, which is not in monsters.json')
    return errs


def report(data: dict) -> None:
    want = proposals(data)
    sizes = collections.Counter(want.values())
    for fam in FAMILY_IDS:
        print(f'{fam:16} {sizes.get(fam, 0):4}')
    missing = [m for m, f in want.items() if f is None]
    print('no family:', missing or 'none')
    flips = [m for m in FINAL if m in data and classify(m, data[m]) != FINAL[m][0]]
    print(f'{len(FINAL)} lore-settled picks, {len(flips)} of them overrule the classifier')


def sheet(data: dict) -> str:
    """The decision record as a Markdown table."""
    names = {}
    try:
        names = {k: v.get('name', k) for k, v in json.load(open(FAMILIES, encoding='utf-8'))['families'].items()}
    except (OSError, ValueError, KeyError):
        pass
    rows = ['| Monster id | Name | Chosen family | Runner-up | Lore reason |',
            '|---|---|---|---|---|']
    for mid, (fam, alt, why) in sorted(FINAL.items(), key=lambda kv: (kv[1][0], kv[0])):
        name = data.get(mid, {}).get('name', mid)
        rows.append(f"| {mid} | {name} | {names.get(fam, fam)} | {names.get(alt, alt)} | {why} |")
    return '\n'.join(rows)


def run_counts(seeds: int = 6) -> dict:
    """What a run meets on floors 1-100, from the real LevelManager (Bones
    stubbed out), averaged over `seeds` runs: {family: (distinct kinds,
    monsters spawned)}. Every monster spawned is a corpse the hero could
    study if he kills it."""
    import contextlib
    import io
    import random
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
    sys.path.insert(0, str(ROOT / 'src'))
    with contextlib.redirect_stdout(io.StringIO()):
        import level_manager as lmm
    lmm.LevelManager._maybe_spawn_bones = staticmethod(lambda *a, **k: None)
    data = json.load(open(MONSTERS, encoding='utf-8'))
    fam = {m: (d.get('family') or family_for(m, d)) for m, d in data.items()}
    kinds = collections.defaultdict(list)
    bodies = collections.defaultdict(list)
    for s in range(seeds):
        random.seed(1000 + s)
        lm = lmm.LevelManager()
        seen = collections.defaultdict(set)
        count = collections.Counter()
        for fl in range(1, 101):
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    _dun, mons, _items = lm.generate(fl)
            except Exception as e:      # a broken floor is reported, not fatal
                print('generation error on floor', fl, e)
                continue
            for m in mons:
                f = fam.get(m.kind)
                if f:
                    seen[f].add(m.kind)
                    count[f] += 1
        for f in FAMILY_IDS:
            kinds[f].append(len(seen.get(f, ())))
            bodies[f].append(count.get(f, 0))

    def avg(v):
        return sum(v) / max(1, len(v))
    return {f: (avg(kinds[f]), avg(bodies[f])) for f in FAMILY_IDS}


def derive_thresholds(kinds_per_run: float) -> list:
    """A family's ladder (Brandon and the coordinator, 2026-10-18): the
    DISTINCT kinds to study for tiers 1-5 are the kinds a run meets times
    12%, 25%, 40%, 55% and 70%, at least 2, 3, 4, 5 and 6, each tier above
    the last."""
    out = [max(mn, round(f * kinds_per_run))
           for f, mn in zip((0.12, 0.25, 0.40, 0.55, 0.70), (2, 3, 4, 5, 6))]
    for i in range(1, 5):
        out[i] = max(out[i], out[i - 1] + 1)
    return out


def main(argv) -> int:
    data, fmt = jsonfmt.load(MONSTERS)
    if '--sheet' in argv:
        print(sheet(data))
        return 0
    if '--rates' in argv:
        i = argv.index('--rates')
        seeds = int(argv[i + 1]) if len(argv) > i + 1 and argv[i + 1].isdigit() else 6
        sizes = collections.Counter(d.get('family') or family_for(m, d) for m, d in data.items())
        rates = run_counts(seeds)
        written = {}
        try:
            written = {f: v.get('thresholds') for f, v in
                       json.load(open(FAMILIES, encoding='utf-8'))['families'].items()}
        except (OSError, ValueError, KeyError):
            pass
        print(f'{"family":16} kinds  kinds/run  corpses/run  derived thresholds   written')
        for f in FAMILY_IDS:
            k, c = rates[f]
            print(f'{f:16} {sizes.get(f, 0):5}  {k:9.1f}  {c:11.1f}  '
                  f'{str(derive_thresholds(k)):20} {written.get(f)}')
        return 0
    if '--check' in argv:
        errs = check(data)
        print('\n'.join(errs) or f'all {len(data)} monsters carry a valid family that matches the script')
        return 1 if errs else 0
    report(data)
    if '--write' in argv:
        want = proposals(data)
        bad = [m for m, f in want.items() if f not in FAMILY_IDS]
        if bad:
            print('refusing to write: no family for', bad)
            return 1
        out = {mid: _with_family(d, want[mid]) for mid, d in data.items()}
        changed = sum(1 for mid in data if data[mid].get('family') != want[mid])
        if changed:
            jsonfmt.save(MONSTERS, out, fmt)
        print(f'written: {changed} monsters changed')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
