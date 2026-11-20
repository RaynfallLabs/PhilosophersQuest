"""Add the MONSTERS AND MAGIC magic items to the data (slice G, 2026-11-19).

    py tools/content/add_mm_magic_2026_11.py          write (safe to run again)
    py tools/content/add_mm_magic_2026_11.py --check  say what would change

What it writes, each entry set by its id (a re-run replaces its own entries and
touches nothing else; each file keeps its own indent and CRLF line endings):

* data/items/spellbook.json  sixteen spellbooks (the spells are in src/spells.py)
* data/items/scroll.json     seven scrolls (family wards, the Piper's tune) and the
                             five warding rites' ``ward_also`` and closing lore lines
* data/items/potion.json     seven potions and two oils, each with a real ``tier``
* data/items/wand.json       the Wand of Unstringing and the Krotala of Athena
* data/items/weapon.json     the Sceptre of Agamemnon
* data/item_worth.json       their worth (prices)
* data/hazards.json, data/fixtures.json   the conjured vine (Dionysus's Vine)
* data/items/recipes.json    the Theriac of Andromachus, brewed to carry
* data/hints.json            a hint or two a tier

The lore is each proposal's (_mm_2026_11_19/C/PROPOSALS.md), from real myth,
scripture, folklore and natural history; the numbers are fixed by each item's
tier (LORE, NOT FLOOR).
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHECK = '--check' in sys.argv
LORE = json.loads(r'''{
 "modify_protection_scrolls_keyed": "Keep every existing lore paragraph; add one closing line to each. Breastplate: 'Christ before and behind, on the right hand and the left: nothing that circles the reader finds a side unguarded.' Psalm 91: 'No arrow that flies by day and no terror by night comes near the reader while the words hold.' Aegis: 'The Gorgon at its centre looks back at any gaze that seeks the reader.' Furnace: 'Fire has no claim on the reader while the rite lasts.'",
 "galdr_stayed_spear_spell": "In the Havamal, Odin lists the charms he won on the windy tree, and the fifth is this: if he sees a spear flying at him, however hard it was thrown, he can stop it in the air. Galdr is sung, not written, and the singer must keep his eyes on the shaft. What he sees coming falls short; what he does not see still finds him.",
 "family_ward_lemuria_scroll": "Each May the Romans drove the hungry dead out of their houses. At midnight the father of the house walked barefoot, threw nine black beans over his shoulder without looking back and said, with these I redeem me and mine. The shades took the beans and left the living alone, so long as the living did not turn and strike them.",
 "tacitas_seal_silence_spell": "On the day the Romans fed their dead, an old woman sat among the girls and made an offering to Tacita, the goddess who cannot speak. She sewed shut a fish's mouth, sealed it with pitch and roasted it, and said she had bound every hostile tongue. The spell does the same to one creature: its mouth works and nothing comes out.",
 "oil_of_rue": "Aristotle noticed that a weasel going to fight a snake first eats wild rue, and the bestiaries said that is how the little weasel kills the basilisk whose look kills men. Herbalists press the bitter grey leaves into oil for anyone who must go where gorgons live. Rubbed on the eyelids and the skin, it lets nothing turn the wearer to stone for a while.",
 "moly_potion": "When Odysseus went alone to Circe's hall to save his crew, Hermes met him on the path and pulled up an herb with a black root and a milk-white flower, a plant hard for mortals to dig. Odysseus drank her cup and stayed a man. Steeped and bottled, moly keeps a mind its own: no glamour, no muddle, no false sight can take it.",
 "dionysus_vine_spell": "Tyrrhenian pirates once seized a young man on the shore, thinking him a rich king's son, and tried to bind him. The ropes fell off him, wine ran over the deck, a vine climbed the sail and ivy wound round the mast until the ship could not move. This spell calls a little of that god's green anger out of the stones.",
 "shrink_the_earth_spell": "Fei Changfang followed an old medicine seller who lived inside a gourd, and learned the arts of the immortals from him. The storytellers say he could fold the veins of the earth, so that a town a thousand li off stood a step away. The spell folds only a little ground: whatever the caster can see, close by, is one stride off.",
 "water_of_epidaurus_potion": "At Epidaurus the sick bathed in the sacred spring, then lay down to sleep in the long hall of Asclepius and waited for the god to come in a dream. The priests carved the cures in stone: the blind who saw, the lame who walked out. Water drawn from that spring gives back what the dead and the diseased have taken from a body.",
 "galdr_loosing_spell": "Among the charms Odin boasted of was one for a man in chains: he sings it, and the fetters spring off his feet and the cuffs off his hands. Every Norse captive wished he knew it. Sung in the dungeon, it breaks roots, webs and grips, and for a few breaths nothing can take hold again.",
 "wand_of_unstringing": "Young Joukahainen drove his sledge into old Vainamoinen's on the road and challenged him to a singing match. The old singer sang the boy's bow into a rainbow over the lake, his arrows into hawks, his sledge into the reeds and the boy himself into the swamp to his chin. Birch-wood cut where the duel was sung still carries the song: point it, and a creature's long weapons will not answer it.",
 "galdr_dulled_blades_spell": "The third of Odin's charms was a war-song: he sings it at his enemies and their swords go blunt, their staves soft, and nothing they swing will bite him. Norse fighters carved such songs on their own shields. This one is sung at a whole room at once.",
 "confusion_of_tongues_spell": "Genesis says the whole earth once had one language, and the builders of Babel meant to raise a tower to heaven. God came down and confused their speech, so that no one understood his neighbour, and the work stopped and the builders scattered. Spoken over a band of foes, it does the same: each one hears his fellows babble and fights alone.",
 "darkness_of_egypt_spell": "Exodus says that Moses stretched his hand toward the sky and a darkness fell on Egypt so thick it could be felt. For three days no one saw another or rose from his place, yet in the houses of Israel there was light. The spell lets that darkness fall on every foe in sight and leaves the caster's own eyes clear.",
 "deliver_us_from_evil_prayer": "The prayer Jesus taught his disciples ends with a plea: lead us not into temptation, but deliver us from evil. Monks and soldiers said it at every hour, and in the old stories the damned and the walking dead could not abide it. Heaven answers the faithful with a ring the evil dead and the fiends cannot cross to lay hands on them.",
 "family_ward_daniel_scroll": "King Darius was tricked into throwing his friend Daniel to the lions for praying to his God. At dawn the king ran to the den and Daniel answered him: an angel had shut the lions' mouths, and they had not touched him all night. Read aloud, these words close the jaws and sheathe the claws of every beast that hears them.",
 "family_ward_psylli_scroll": "Pliny wrote of the Psylli of Libya, whose bodies carried a poison deadly to snakes; they tested their babies by laying them among serpents. Lucan says Cato's army crossed the desert with Psylli at its side, sucking the venom out of bitten soldiers. The scroll is their old charm, and while it holds a serpent's bite is only a bite.",
 "family_ward_hoichi_scroll": "Hoichi was a blind lute-player who sang the Tale of the Heike so well that the drowned Heike ghosts called him to their graves night after night. To save him, his priest wrote the Heart Sutra over every inch of his body, so the ghost-samurai could not see him, but in his haste forgot the ears. Read over yourself, the sutra hides you from every ghost, and like the priest's, it has one weak place.",
 "nepenthe_potion": "At Menelaus's table, the talk of lost Odysseus made every man weep, so Helen slipped a drug into the wine that she had been given in Egypt by Polydamna, wife of Thon. Homer says that whoever drank it shed no tear that day, though he saw his own brother cut down before him. In the dungeon it does the same for fear.",
 "charm_of_prometheus_oil": "King Aeetes set Jason to yoke two bronze bulls that breathed fire. Medea gave him the charm of Prometheus, an ointment from a flower that grew where the eagle's blood-drops fell from the Titan's torn side. Anointed, Jason walked into the fire unburnt and the bulls' horns turned on him like reeds.",
 "cockcrow_spell": "Old belief held that the dead walk only until the cock crows; at his call every wandering spirit must go back to its grave. The poet Prudentius wrote a dawn hymn on it in the fourth century, and the ghost in Hamlet fades at the sound. The spell is that first crow, called early.",
 "goatherds_coffee_potion": "The story goes that a goatherd saw his goats dancing after they ate the red berries of a certain bush. He took the berries to the monks, who threw them in the fire in disgust, smelled the roasting and made a drink that kept them awake through the night. A flask of it keeps any sleep off you, however it comes.",
 "theriac_potion": "Nero's physician Andromachus took the antidote of Mithridates and added the flesh of vipers, until his paste held some sixty-four things bound in honey. For seventeen centuries it was the great cure for poison; in Venice it was compounded in public, over forty days, with officials watching every jar. A dose drives venom out and keeps it out.",
 "sanctuary_spell": "In medieval England a hunted man who reached a church and laid hold of its door ring could not be dragged away; his pursuers had to wait outside. At Durham the ring was a bronze lion's head on the north door. The spell raises that old law about the caster for a little while, and like the law, it shelters no one who fights.",
 "pans_panic_spell": "Before Marathon the runner Pheidippides met the god Pan on a mountain road, and Pan asked why Athens never honoured him, since he had always helped it. After the Persians broke and ran, the Athenians built him a shrine under the Acropolis. Sudden, senseless terror in a crowd still bears his name.",
 "elf_shot_spell": "The Anglo-Saxons blamed sudden pains and seizures in men and cattle on elf-shot, tiny arrows loosed by the elves that no one saw fly. Their leechbooks kept charms against it, and flint arrowheads turned up in fields were kept as the elves' own darts. The spell borrows one: the target stiffens where it stands.",
 "somnus_bough_spell": "On the last night of the voyage to Italy, the god of Sleep came down to Aeneas's helmsman Palinurus disguised as a friend. When the man would not leave the tiller, the god shook over his temples a branch wet with the dew of Lethe, and his eyes closed. The spell shakes that bough over a knot of foes.",
 "fern_flower_tincture_potion": "On Midsummer night, the Slavs said, a fern blooms once for a single hour, and spirits guard it from anyone unworthy. Whoever plucks the flower can see where treasure lies hidden in the earth. Its petals keep a little of that sight in a drop of spirit.",
 "family_ward_martha_scroll": "The Golden Legend tells that a dragon called the Tarasque lived in the Rhone and burned the farms of Tarascon. Martha went to it alone, sprinkled it with holy water and sang to it, and it came out tame as a lamb, so she led it into the town on her girdle. Her hymn takes the heat out of a dragon's breath and the weight out of its blows.",
 "family_ward_udug_hul_scroll": "The exorcists of Babylon kept a long series of clay tablets, the Udug Hul, against the evil spirits that crept in at doors and under beds. The priest named each demon, bound it by the great gods and ordered it out into the desert. Copied onto vellum, the old words still drive fiends back from the one who reads them.",
 "family_ward_pied_piper_scroll": "In 1284, the legend says, a piper in a coat of many colours came to Hamelin and offered to rid it of rats for a price. He played in the streets, every rat in town came out to follow him, and he led them into the river Weser to drown. This is the tune, written down: vermin that hear it have to go where it leads.",
 "krotala_of_athena_wand": "The man-eating birds of Lake Stymphalia hid in a marsh too soft to walk and too thick to shoot into. Athena gave Heracles a pair of bronze clappers made by Hephaestus, and their clatter was so dreadful that the whole flock burst up out of the reeds. Each charge is one great clash of bronze.",
 "galdr_settled_strife_spell": "Odin knew a song for a hall about to come to blows: when hatred rises between the sons of a war-leader, he sings it, and their hands drop from their sword hilts. The skalds said a king's peace was worth more than a king's army. The song works on anyone who can hate, which leaves out the beasts and the dead.",
 "mist_of_manannan_spell": "The Manx say that when raiders came, Manannan mac Lir, lord of the sea, drew his cloak of mist over the whole island and the ships sailed past it. The old Irish gods had a word for that veil, the feth fiada, which hid them from mortal eyes. Called down in the dungeon, it lets a creature see only what is right beside it.",
 "sceptre_of_agamemnon_rod": "Hephaestus forged a sceptre for Zeus, and it passed by Hermes to Pelops, to Atreus, to Thyestes and at last to Agamemnon, king of men. When the Greek army broke for the ships, Odysseus took it from his hand and drove the kings back to the assembly, and he beat the loud-mouthed Thersites with it until he sat down weeping. Centuries later the people of Chaeronea still made sacrifices to it every day.",
 "water_of_the_styx_potion": "Statius tells that Thetis carried her baby son down to the river Styx and dipped him in it, so that no weapon could pierce him, all except the heel she held him by. Achilles fought ten years at Troy without a wound until an arrow found that heel. A few drops of the river make a body iron for a little while, but never everywhere.",
 "feralia_hush_spell": "On the Feralia the Romans carried food to their family tombs and spoke softly, and old women made the silent goddess her offering. It was the one day of the year the city hushed for its dead. The spell is that hush laid on a room: every mouth in it works, and nothing comes out.",
 "eidolon_of_helen_spell": "Stesichorus and later Euripides told a stranger story of Troy: Helen never went there at all. Hera made an image of her out of cloud, Paris carried off the phantom, and the Greeks and Trojans fought ten years over a breath of air. The spell makes such an image of its caster and sets it walking.",
 "gates_of_alexander_spell": "The Quran tells of Dhul-Qarnayn, the two-horned king, who came to a people between two mountains plagued by Gog and Magog. He had them heap iron between the cliffs, blew it red-hot and poured molten copper over it, and the wall held. Medieval readers said the king was Alexander and placed his gates in the Caucasus. The spell pours a short span of that wall across a passage."
}''')


def _path(*p):
    return os.path.join(ROOT, *p)


def _dump(obj, indent: int, ascii_: bool) -> str:
    return json.dumps(obj, indent=indent, ensure_ascii=ascii_).replace('\n', '\r\n')


def write_roundtrip(rel: str, update, indent: int = 2, ascii_: bool = True, tail: str = '\r\n'):
    """A file json.dumps writes back byte for byte: load, update, dump."""
    p = _path(*rel.split('/'))
    old = open(p, 'rb').read().decode('utf-8')
    d = json.loads(old)
    update(d)
    new = _dump(d, indent, ascii_) + tail
    if new != old:
        if CHECK:
            print('would write', rel)
        else:
            open(p, 'wb').write(new.encode('utf-8'))
            print('wrote', rel)
    else:
        print('unchanged', rel)


def write_appended(rel: str, entries: dict, indent: int = 2, ascii_: bool = True):
    """A hand-kept file that json.dumps would reformat: our entries go at the
    end, in the file's own indent; a re-run cuts its old block first."""
    p = _path(*rel.split('/'))
    old = open(p, 'rb').read().decode('utf-8')
    d = json.loads(old)
    first = next(iter(entries))
    marker = '\r\n' + ' ' * indent + json.dumps(first) + ': {'
    body = old
    if first in d:
        cut = body.index(marker)
        body = body[:cut].rstrip(',') if False else body[:cut]
        body = body.rstrip()
        if body.endswith(','):
            body = body[:-1]
        body += '\r\n}' + ('\r\n' if old.endswith('\r\n') else '')
    end = body.rstrip().rfind('}')
    head = body[:end].rstrip()
    trailer = body[end:]
    blocks = []
    pad = ' ' * indent
    for k, v in entries.items():
        txt = json.dumps({k: v}, indent=indent, ensure_ascii=ascii_)
        inner = txt.strip()[1:-1].strip('\n')
        blocks.append(inner.replace('\n', '\r\n'))
    new = head + ',\r\n' + ',\r\n'.join(blocks) + '\r\n' + trailer
    new = new.replace('\r\n' + pad + '\r\n', '\r\n')
    json.loads(new)
    if new != old:
        if CHECK:
            print('would write', rel)
        else:
            open(p, 'wb').write(new.encode('utf-8'))
            print('wrote', rel)
    else:
        print('unchanged', rel)


# ---------------------------------------------------------------------------
# Spellbooks
# ---------------------------------------------------------------------------
BAND = {1: (1, 8, 8), 2: (15, 25, 10), 3: (35, 45, 10), 4: (55, 65, 10), 5: (75, 88, 10)}
BOOKS = [
    # id, spell id, spell name, mp, tier, unidentified name, colour, lore key
    ('spellbook_galdr_of_loosing', 'galdr_of_loosing_spell', 'Galdr of Loosing', 3, 1,
     'grey hide tome', [190, 190, 185], 'galdr_loosing_spell'),
    ('spellbook_cockcrow', 'cockcrow_spell', 'Cockcrow', 3, 1,
     'sun-stamped tome', [230, 110, 50], 'cockcrow_spell'),
    ('spellbook_sanctuary', 'sanctuary_spell', 'Sanctuary', 3, 1,
     'lion-ringed tome', [200, 160, 80], 'sanctuary_spell'),
    ('spellbook_elf_shot', 'elf_shot_spell', 'Elf-Shot', 3, 1,
     'flint-set tome', [60, 140, 70], 'elf_shot_spell'),
    ('spellbook_stayed_spear', 'stayed_spear_spell', 'Galdr of the Stayed Spear', 6, 2,
     'rune-cut slate tome', [130, 160, 190], 'galdr_stayed_spear_spell'),
    ('spellbook_tacitas_seal', 'tacitas_seal_spell', "Tacita's Seal", 6, 2,
     'wine-red stitched tome', [150, 40, 50], 'tacitas_seal_silence_spell'),
    ('spellbook_dionysus_vine', 'dionysus_vine_spell', "Dionysus's Vine", 7, 2,
     'vine-leaf tome', [70, 160, 60], 'dionysus_vine_spell'),
    ('spellbook_shrink_the_earth', 'shrink_the_earth_spell', 'Shrink the Earth', 6, 2,
     'gourd-stamped tome', [200, 130, 50], 'shrink_the_earth_spell'),
    ('spellbook_bough_of_somnus', 'bough_of_somnus_spell', 'Bough of Somnus', 6, 2,
     'midnight cloth tome', [40, 50, 120], 'somnus_bough_spell'),
    ('spellbook_dulled_blades', 'dulled_blades_spell', 'Galdr of Dulled Blades', 10, 3,
     'notched-blade tome', [170, 40, 40], 'galdr_dulled_blades_spell'),
    ('spellbook_confusion_of_tongues', 'confusion_of_tongues_spell', 'Confusion of Tongues', 10, 3,
     'clay-brown tome', [150, 100, 60], 'confusion_of_tongues_spell'),
    ('spellbook_darkness_of_egypt', 'darkness_of_egypt_spell', 'Darkness of Egypt', 10, 3,
     'black window tome', [40, 40, 40], 'darkness_of_egypt_spell'),
    ('spellbook_pans_panic', 'pans_panic_spell', "Pan's Panic", 9, 3,
     'reed-pipe tome', [70, 120, 60], 'pans_panic_spell'),
    ('spellbook_settled_strife', 'settled_strife_spell', 'Galdr of Settled Strife', 15, 4,
     'oxblood tome', [110, 30, 30], 'galdr_settled_strife_spell'),
    ('spellbook_mist_of_manannan', 'mist_of_manannan_spell', 'Mist of Manannan', 14, 4,
     'sea-fog tome', [140, 170, 150], 'mist_of_manannan_spell'),
    ('spellbook_hush_of_the_feralia', 'hush_of_the_feralia_spell', 'Hush of the Feralia', 15, 4,
     'ash-grey tome', [150, 150, 150], 'feralia_hush_spell'),
]


def book_entries() -> dict:
    out = {}
    for bid, sid, sname, mp, tier, unid, col, lk in BOOKS:
        ml, pk, sp = BAND[tier]
        out[bid] = {
            'name': f'Spellbook of {sname}', 'symbol': '+', 'color': col,
            'weight_lb': 3.0, 'min_level': ml, 'peak_floor': pk, 'spread': sp,
            'peak_weight': 0.3, 'tier': tier, 'quiz_tier': tier, 'quiz_threshold': 1,
            'spell_id': sid, 'spell_name': sname, 'mp_cost': mp,
            'unidentified_name': unid, 'lore': LORE[lk], 'weight': 0.3,
        }
    return out


# ---------------------------------------------------------------------------
# Scrolls
# ---------------------------------------------------------------------------
SCROLL_BAND = {1: (1, 10, 6), 2: (8, 26, 8), 3: (20, 50, 10), 4: (40, 70, 10), 5: (60, 88, 10)}
SCROLLS = {
    'scroll_of_the_lemuria': dict(
        name='scroll of the Lemuria', tier=1, unid='black-threaded scroll', color=[60, 50, 40],
        lore='family_ward_lemuria_scroll', effect='family_ward', ward='ward_lemuria', turns=15,
        read_line=("You throw nine black beans over your shoulder without looking back. "
                   "The restless dead will not strike you up close until you strike one")),
    'scroll_of_the_hamelin_piper': dict(
        name='scroll of the Hamelin Piper', tier=1, unid='ribbon-striped scroll', color=[220, 180, 60],
        lore='family_ward_pied_piper_scroll', effect='family_rout', family='vermin',
        status='feared', turns=12,
        read_line="You play the tune written on the scroll, and every vermin in sight must go where it leads.",
        none_line="You play the Piper's tune, and no rat or crawling thing in sight hears it."),
    'scroll_of_daniel': dict(
        name='scroll of Daniel', tier=2, unid='brass-ringed vellum', color=[220, 190, 90],
        lore='family_ward_daniel_scroll', effect='family_ward', ward='ward_daniel', turns=20,
        read_line=("You read how the angel shut the lions' mouths. Great beasts will not bite "
                   "or claw you until you strike one")),
    'scroll_of_the_psylli': dict(
        name='scroll of the Psylli', tier=2, unid='papyrus roll', color=[200, 180, 120],
        lore='family_ward_psylli_scroll', effect='family_ward', ward='ward_psylli', turns=25,
        read_line=("You speak the Psylli's old charm. A serpent's bite cannot poison you "
                   "and its coils cannot hold you")),
    'scroll_of_the_heart_sutra': dict(
        name='scroll of the Heart Sutra', tier=3, unid='rice-paper scroll', color=[235, 235, 225],
        lore='family_ward_hoichi_scroll', effect='family_ward', ward='ward_hoichi', turns=20,
        read_line=("You read the sutra over yourself, every inch of skin. The ghosts cannot see "
                   "you, but strike one and they will all find you")),
    'scroll_of_saint_martha': dict(
        name="scroll of Saint Martha's Hymn", tier=4, unid='blue-corded vellum', color=[200, 220, 240],
        lore='family_ward_martha_scroll', effect='family_ward', ward='ward_martha', turns=25,
        read_line=("You sing Saint Martha's hymn. Dragons hurt you half as much, breath "
                   "and bite alike")),
    'scroll_of_the_udug_hul': dict(
        name='scroll of the Udug Hul', tier=5, unid='gold-wired scroll', color=[190, 120, 80],
        lore='family_ward_udug_hul_scroll', effect='family_ward', ward='ward_udug_hul', turns=30,
        read_line=("You name the evil spirits by the great gods and order them out into the "
                   "desert. Demons cannot strike you up close, and their curses and terrors "
                   "do not take hold, until you strike one")),
}
# The five warding rites: what each one's own story also keeps off.
WARD_ALSO = {
    'scroll_of_protection': ([['all_round_ward', 20]],
        "Christ before and behind, on the right hand and the left: no pack that circles "
        "you finds a side unguarded",
        "Christ before and behind, on the right hand and the left: nothing that circles "
        "the reader finds a side unguarded."),
    'scroll_of_greater_protection': ([['missile_ward', 30], ['fear_immune', 30]],
        "No arrow that flies by day and no terror by night comes near you while the words hold",
        "No arrow that flies by day and no terror by night comes near the reader while the "
        "words hold."),
    'scroll_of_aegis': ([['petrify_immune', 50]],
        "The Gorgon at the shield's heart looks back at any gaze that seeks you",
        "The Gorgon at its centre looks back at any gaze that seeks the reader."),
    'scroll_of_absolute_ward': ([['fire_shield', 80]],
        "As the three in the furnace walked in the fire unburnt, fire has no claim on you",
        "Fire has no claim on the reader while the rite lasts."),
}


def scroll_update(d: dict) -> None:
    for sid, s in SCROLLS.items():
        ml, pk, sp = SCROLL_BAND[s['tier']]
        e = {'name': s['name'], 'symbol': '?', 'color': s['color'], 'weight_lb': 0.1,
             'min_level': ml, 'peak_floor': pk, 'spread': sp, 'tier': s['tier'],
             'quiz_tier': s['tier'], 'quiz_threshold': 1, 'effect': s['effect'], 'power': '',
             'unidentified_name': s['unid'], 'lore': LORE[s['lore']], 'weight': 0.1,
             'peak_weight': 0.25, 'turns': s['turns'], 'read_line': s['read_line']}
        for k in ('ward', 'family', 'status', 'none_line'):
            if k in s:
                e[k] = s[k]
        d[sid] = e
    for sid, (also, line, closing) in WARD_ALSO.items():
        e = d[sid]
        e['ward_also'] = also
        e['ward_line'] = line
        if not e['lore'].endswith(closing):
            e['lore'] = e['lore'].rstrip() + ' ' + closing


# ---------------------------------------------------------------------------
# Potions and oils
# ---------------------------------------------------------------------------
POTIONS = {
    'goatherds_coffee': dict(name="Goatherd's Coffee", unid='dark bitter-smelling flask',
        color=[110, 70, 40], tier=1, min_level=1, effect='wakeful', duration=60,
        bands={'1-20': 12, '21-40': 4, '41-60': 1}, lore='goatherds_coffee_potion',
        drink_line='nothing can put you to sleep for 60 turns'),
    'nepenthe': dict(name='Nepenthe', unid='blue faience bottle', color=[60, 200, 200], tier=2,
        min_level=12, effect='fearless', duration=50,
        bands={'1-20': 2, '21-40': 8, '41-60': 3, '61-80': 1}, lore='nepenthe_potion',
        drink_line='fear leaves you, and nothing can frighten you for 50 turns'),
    'oil_of_rue': dict(name='oil of rue', unid='grey-green oily flask', color=[130, 150, 90], tier=2,
        min_level=10, effect='stoneproof', duration=40,
        bands={'1-20': 2, '21-40': 6, '41-60': 3, '61-80': 1}, lore='oil_of_rue',
        drink_line='stone creeping in stops, and nothing can turn you to stone for 40 turns'),
    'fern_flower_tincture': dict(name='Fern-Flower Tincture', unid='tall green vial with a red spark',
        color=[60, 150, 70], tier=2, min_level=10, effect='treasure_sight', duration=0,
        bands={'1-20': 3, '21-40': 7, '41-60': 2}, lore='fern_flower_tincture_potion',
        drink_line="every treasure, chest and coin on the floor is marked on your map"),
    'moly': dict(name='Moly', unid='vial with a white-flowered root', color=[235, 235, 225], tier=3,
        min_level=30, effect='clear_mind', duration=60,
        bands={'21-40': 3, '41-60': 9, '61-80': 4, '81-100': 1}, lore='moly_potion',
        drink_line='confusion, charm and false sight leave you and cannot take hold for 60 turns'),
    'theriac': dict(name='Theriac of Andromachus', unid='squat jar of brown paste',
        color=[120, 80, 40], tier=3, min_level=25, effect='antidote', duration=80,
        bands={'21-40': 3, '41-60': 9, '61-80': 3}, lore='theriac_potion',
        drink_line='poison and disease are cured, and no poison can take you for 80 turns'),
    'water_of_epidaurus': dict(name='Water of Epidaurus', unid='serpent-wound stone flask',
        color=[150, 190, 220], tier=4, min_level=45, effect='restoration', duration=0,
        bands={'41-60': 2, '61-80': 7, '81-100': 4}, lore='water_of_epidaurus_potion',
        drink_line='every stat point a drain, a poison or a disease took from you comes back'),
    'charm_of_prometheus': dict(name='Charm of Prometheus', unid='saffron oil flask',
        color=[240, 150, 40], tier=4, min_level=45, effect='fireproof', duration=30,
        bands={'41-60': 2, '61-80': 6, '81-100': 3}, lore='charm_of_prometheus_oil',
        drink_line='fire cannot hurt you for 30 turns, and blows land half as hard'),
    'water_of_the_styx': dict(name='Water of the Styx', unid='black glass vial', color=[40, 40, 60],
        tier=5, min_level=70, effect='styx_dipped', duration=6, bands={'81-100': 2},
        lore='water_of_the_styx_potion', rare=True,
        drink_line='for 6 turns no blow, bite or claw can wound you, but an unseen blow finds the heel'),
}


def potion_entries() -> dict:
    out = {}
    for pid, s in POTIONS.items():
        e = {'name': s['name'], 'unidentified_name': s['unid'], 'symbol': '!', 'color': s['color'],
             'weight': 0.4, 'min_level': s['min_level'], 'effect': s['effect'], 'power': '',
             'duration': s['duration'], 'floorSpawnWeight': s['bands'], 'tier': s['tier'],
             'lore': LORE[s['lore']], 'drink_line': s['drink_line'], 'peak_weight': 0.5}
        if s.get('rare'):
            e['rare'] = True
            e['containerLootTier'] = 'rare'
        out[pid] = e
    return out


# ---------------------------------------------------------------------------
# Wands and the sceptre
# ---------------------------------------------------------------------------
WANDS = {
    'wand_of_unstringing': {
        'name': 'wand of unstringing', 'symbol': '/', 'color': [230, 225, 210], 'weight_lb': 1.0,
        'min_level': 20, 'peak_floor': 50, 'spread': 10, 'charges_min': 4, 'charges_max': 6,
        'max_charges': 6, 'tier': 3, 'quiz_tier': 3, 'quiz_threshold': 1,
        'effect': 'unstring_monster', 'power': '8', 'unidentified_name': 'string-wound wand',
        'lore': LORE['wand_of_unstringing'], 'container_loot_tier': 'uncommon', 'weight': 0.3,
        'peak_weight': 0.25},
    'krotala_of_athena': {
        'name': 'Krotala of Athena', 'symbol': '/', 'color': [230, 180, 60], 'weight_lb': 1.0,
        'min_level': 8, 'peak_floor': 26, 'spread': 8, 'charges_min': 5, 'charges_max': 8,
        'max_charges': 8, 'tier': 2, 'quiz_tier': 2, 'quiz_threshold': 1,
        'effect': 'family_rout', 'power': '10', 'family': 'birds', 'status': 'feared',
        'unidentified_name': 'pair of bronze clappers', 'lore': LORE['krotala_of_athena_wand'],
        'zap_line': "You clash the bronze krotala, and the din is dreadful: every bird in sight bursts up and flies.",
        'none_line': "You clash the bronze, and the din rolls round the walls. No bird is in sight to fly from it.",
        'container_loot_tier': 'uncommon', 'weight': 0.3, 'peak_weight': 0.25},
}
SCEPTRE = {
    'name': 'Sceptre of Agamemnon', 'class': 'mace', 'weapon_class': 'mace', 'variant': '1h',
    'tier': 3, 'material': 'bronze', 'is_unique': True, 'mathTier': 3, 'quiz_tier': 3,
    'baseDamage': 100, 'base_damage': 100,
    'chainMultipliers': [0.5, 0.85, 1.0, 1.45, 2.0], 'chain_multipliers': [0.5, 0.85, 1.0, 1.45, 2.0],
    'maxChainLength': 5, 'max_chain_length': 5, 'weapon_class_chain': 'normal',
    'damageTypes': ['blunt'], 'damage_types': ['blunt'], 'symbol': ')', 'color': [220, 180, 80],
    'weight': 3.0, 'twoHanded': False, 'two_handed': False, 'reach': 1, 'stunChance': 0.0,
    'bleedChance': 0.0, 'knockback': False, 'ignoreShield': False, 'requiresAmmo': None,
    'floorSpawnWeight': {'1-20': 0, '21-40': 0, '41-60': 2, '61-80': 0, '81-100': 0},
    'containerLootTier': 'rare', 'container_loot_tier': 'rare', 'value': 3000,
    'min_level': 41, 'peak_floor': 50, 'spread': 8, 'peak_weight': 0.5, 'max_enchant': 3,
    'unidentified_name': 'a gold-studded rod with an eagle on top', 'identified': False,
    'lore': LORE['sceptre_of_agamemnon_rod'], 'template_basis': 'mace',
    'effects': {'status': 'silenced', 'effect_chance': 1.0, 'effect_duration': 2,
                'families': ['mortals', 'goblinkin'], 'target_words': 'a man or a goblin'},
    # The card's line for its V power (game_render reads it; game_wards does it).
    'power_line': ("Power (V), once a floor: Call the Assembly. Answer a chain of history "
                   "questions; every man and goblin in sight runs, 2 turns for each right "
                   "answer (12 at most), and a war band in sight loses its leader's hold."),
    'chain_exponent': 1.15,
}

WORTH = {
    'spellbook_galdr_of_loosing': 0.8, 'spellbook_cockcrow': 0.8, 'spellbook_sanctuary': 0.8,
    'spellbook_elf_shot': 0.8, 'spellbook_stayed_spear': 1.0, 'spellbook_tacitas_seal': 1.0,
    'spellbook_dionysus_vine': 1.0, 'spellbook_shrink_the_earth': 1.2,
    'spellbook_bough_of_somnus': 0.9, 'spellbook_dulled_blades': 1.0,
    'spellbook_confusion_of_tongues': 1.0, 'spellbook_darkness_of_egypt': 1.0,
    'spellbook_pans_panic': 0.9, 'spellbook_settled_strife': 1.2,
    'spellbook_mist_of_manannan': 1.2, 'spellbook_hush_of_the_feralia': 1.1,
    'scroll_of_the_lemuria': 1.0, 'scroll_of_the_hamelin_piper': 0.8, 'scroll_of_daniel': 1.0,
    'scroll_of_the_psylli': 0.9, 'scroll_of_the_heart_sutra': 1.0, 'scroll_of_saint_martha': 1.2,
    'scroll_of_the_udug_hul': 1.5, 'scroll_of_greater_protection': 1.3, 'scroll_of_aegis': 1.3,
    'scroll_of_absolute_ward': 1.3,
    'goatherds_coffee': 0.6, 'nepenthe': 1.0, 'oil_of_rue': 1.5, 'fern_flower_tincture': 0.8,
    'moly': 1.5, 'theriac': 1.5, 'water_of_epidaurus': 2.0, 'charm_of_prometheus': 2.0,
    'water_of_the_styx': 4.0, 'wand_of_unstringing': 1.2, 'krotala_of_athena': 0.8,
}

VINE_HAZARD = {
    'trigger': 'step', 'chance': 0.6, 'status': ['immobilized', 2, 4], 'save': True,
    'hero': "The god's vines wind round your legs and hold you fast!",
    'monster': "The vines wind round {the} and hold {him} fast!",
    'arrival': "Vines and ivy have grown up out of the stone here.",
}
VINE_FIXTURE = {
    'name': 'grapevine and ivy', 'layer': 'floor',
    'look': ("Grapevine and ivy, grown up out of the stone in a moment and still moving. "
             "Whatever walks through them is held. They will not last."),
}
THERIAC_RECIPE = {
    'name': 'Theriac of Andromachus', 'ingredients': ['cobra_prime', 'swamp_moss', 'cave_mushroom'],
    'benefit': 'carry',
    'flavor': ("Andromachus's antidote: viper flesh, cave herbs and moss pounded together and "
               "bound, as Nero's physician bound his, to drive venom out."),
    'makes': 'potion:theriac', 'art': 'dish_stew_t1_special',
}
HINTS = {
    '2': ["An archer you can see cannot hurt you while the Galdr of the Stayed Spear holds.",
          "A silenced foe cannot wail, sing, summon or heal. Seal the healer's mouth first."],
    '3': ["A scroll of greater protection turns every arrow aside, seen or unseen.",
          "Confusion of Tongues breaks a war band or a pack into creatures that fight alone."],
    '4': ["Zap an archer or a slinger with the Wand of Unstringing and it has to come to you.",
          "Water of Epidaurus gives back every stat point a drain or a disease took."],
    '5': ["The Water of the Styx turns every blow, bite and claw, but an unseen blow finds the heel.",
          "Demons cannot strike you up close while the Udug Hul holds, until you strike one."],
}


# Hints this tool once wrote that the audit of 2026-11-20 found untrue
# (the Wand of Unstringing no longer touches a breath).
RETIRED_HINTS = [('4', "Zap an archer or a dragon with the Wand of Unstringing and it has to come to you.")]


def main():
    write_roundtrip('data/items/spellbook.json', lambda d: d.update(book_entries()), tail='')
    write_roundtrip('data/items/scroll.json', scroll_update)
    write_appended('data/items/potion.json', potion_entries())
    write_roundtrip('data/items/wand.json', lambda d: d.update(WANDS))
    write_roundtrip('data/items/weapon.json', lambda d: d.update({'sceptre_of_agamemnon': SCEPTRE}),
                    ascii_=False)
    write_roundtrip('data/item_worth.json', lambda d: d['by_id'].update(WORTH))
    write_roundtrip('data/hazards.json', lambda d: d['hazards'].update({'conjured_vine': VINE_HAZARD}))
    write_roundtrip('data/fixtures.json', lambda d: d['fixtures'].update({'conjured_vine': VINE_FIXTURE}))
    write_appended('data/items/recipes.json', {'brew_theriac': THERIAC_RECIPE}, indent=1)
    # The kitchen's record of each dish's picture (tools/content/kitchen/dish_art.py
    # picks it: a stew of the first tier for this brew).
    write_roundtrip('tools/content/kitchen/dish_art.json',
                    lambda d: d.update({'brew_theriac': THERIAC_RECIPE['art']}), indent=1, tail='')

    def hints(d):
        for t, old in RETIRED_HINTS:
            if old in d[t]:
                d[t].remove(old)
        for t, lst in HINTS.items():
            for h in lst:
                if h not in d[t]:
                    d[t].append(h)
    write_roundtrip('data/hints.json', hints)


if __name__ == '__main__':
    main()
