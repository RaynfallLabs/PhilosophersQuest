"""The named armour and shields on the armour ladder (bug bash 3.3.2, plan 6).

Offline content pass over data/items/armor.json and data/items/shield.json.
Idempotent: run it again and nothing changes.

Only body armour and shields give AC (gear.py); a minor piece carries one
enchantment of its own slot instead (enchantments.py). For each named piece:

- tier: a step above the commons found where it is found (the level bells
  at its peak floor), never under its authored tier; a quest or starting
  piece (found nowhere, or on floor 1) keeps its own. Its level is the
  tier's greater form (2 x tier).
- body armour and shields: AC is the template's base (template_basis) plus
  the tier's plus (gear.plus_for_level), as for a common piece of that level.
  A chain-equip piece keeps its AC (its tier ladder sets its full AC).
- a minor piece (helm, gloves, vambraces, greaves, boots, cloak, shirt): no
  AC, and the enchantment PICKS gives it (each chosen against the piece's
  lore, 2026-11-07); a chain-equip piece's tier ladder loses its AC too.
- threshold: the template's weight class and the tier's benefit, plus one
  for a unique (gear.equip_threshold); a trap that goes on with no quiz
  (threshold 0, the Duck of Doom) stays one.
Signature powers (damage resistances, specials, procs, statuses, chain
tiers) are kept.

    python tools/content/unique_armor_ladder_2026_11.py [--check]
"""
from __future__ import annotations

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'src'))

import jsonfmt  # noqa: E402

ARMOR = os.path.join(ROOT, 'data', 'items', 'armor.json')
SHIELD = os.path.join(ROOT, 'data', 'items', 'shield.json')

PICKS = {
    'helm_of_hades': ('night_eyes', 'The Helm of Darkness is the cap of the lord of the dark realm, and it already works in the dark (tier passive_stealth_in_dark); Night Eyes lets its wearer see in the dark it hides him in.'),
    'helm_of_achilles': ('iron_will', 'When Thetis laid the armour down the Myrmidons trembled and would not look at it; only Achilles looked, and his anger grew. The wearer is the one who meets the terrible sight unafraid: Iron Will (gaze and fear).'),
    'great_helm_of_galahad': ('true_sight', "Galahad alone looked into the Grail and saw what no other knight could; True Sight shows what is hidden from ordinary eyes. Tier IV meets True Sight's from_tier 4."),
    'aegishjalmr': ('the_reader', "Its own lore ends that it is less a helmet than a sign: the Helm of Awe is a stave from the Icelandic books of magic, marked on the brow. A written sign out of a grimoire is the Reader's (grammar: scrolls and spellbooks); its fear and Fafnir's-glare powers stay in its chain-equip tiers."),
    'blindfold': ('iron_will', 'Its whole reason is that some things in the dark do their harm through the eyes; Iron Will turns aside gaze attacks and shrugs off blinding, confusion and fear.'),
    'trainers_cap': ('the_eagle', "A trainer's cap is a spotter's cap, its brim shaped by long roads and its wearer's eye always on the tall grass for the next creature. Nothing in the head stable speaks to pets, so the Eagle (Perception) is the nearest fit to a life of looking for creatures."),
    'cow_kings_horns': ('searching', 'Its lore is about whoever finally answered the long rumour that there was no such herd and no such king: the hero who found the hidden place everyone said did not exist. Searching finds what is hidden.'),
    'tarnhelm': ('telepathy', "Wagner's Alberich used the Tarnhelm to walk unseen among the Nibelungs he drove, watching every one of them; a master who knows where all his people are through the walls is Telepathy. Tier III meets Telepathy's from_tier 3."),
    'coif_of_beowulf': ('night_eyes', 'Beowulf lay awake in the dark hall of Heorot while his men slept and watched Grendel come in out of the night; Night Eyes is that night watch. Iron Will would overlap its grendel_grip (sleep and stun already break at once).'),
    'helm_of_gilgamesh': ('the_scholar', 'The epic opens on Gilgamesh as the one who saw the Deep, learned the secret things and brought back word from before the Flood: the first king of knowing, which is the Scholar (philosophy: identifying).'),
    'helm_of_leonidas': ('iron_will', 'The Spartans dressed their hair before a fight they meant to die in and held Thermopylae to the last man; no helm in the game is more plainly the will that fear cannot move.'),
    'helm_of_aragorn': ('alertness', 'The man who claimed it spent most of his life as Strider, a ranger of the North keeping unseen watch on the borders for what was coming; Alertness warns of what is coming. Tier V; Alertness rolls from tier II.'),
    'crown_of_brahma': ('the_eagle', 'Brahma grew a face for each quarter of the sky so that nothing he made could pass out of his sight, and its wearer is not easily approached from behind; the Eagle (Perception, the sight radius) is that all-seeing reach, beside its four-faces tier.'),
    'duck_of_doom': ('iron_will', "A gag piece; nothing in the head stable matches it, so the slot's guard by default. Its one instruction, be patient with it, is the only will it teaches."),
    'gauntlets_of_mars': ('life_grip', 'The lore deliberately makes this the Roman Mars, a god of fields and boundaries before he was a god of war, whose gauntlets are happiest holding a line; holding ground against the hands that grab and pin is Life-Grip.'),
    'cestus_of_polydeuces': ('striking', "The cestus is the boxer's weighted hand-wrap, and Polydeuces dropped the never-beaten Amycus with one blow above the ear; Striking adds to the damage of your blows."),
    'gloves_of_wayland': ('the_locksmith', "Wayland was the master smith held prisoner on an island who worked his own way out; a smith's patient hands that free their owner are the Locksmith's."),
    'glove_of_tyr': ('striking', 'Snorri calls Tyr the boldest of the gods, with power over victory in battle, and his name was cut on sword hilts for victory; the glove from the hand he kept is a fighting hand, so Striking.'),
    'jarngreipr_gauntlets': ('ogre_power', "Jarngreipr are Thor's iron grippers, without which even he cannot swing Mjolnir; the iron gloves of the strongest god are the first gauntlets of power, so Ogre Power (Strength)."),
    'vambraces_of_achilles': ('deflection', "Hephaestus' armour for Achilles is the armour spears could not pierce: Aeneas' spear stuck in the shield and Hector's rebounded from it. Deflection turns aside thrown things."),
    'bracers_of_cu_chulainn': ('swift_strokes', "In the riastrad Cu Chulainn struck faster than eyes could follow; Swift Strokes adds seconds to every fight's clock, so more blows land and its every-third-blow wound opens more often."),
    'bracers_of_arjuna': ('archery', 'Arjuna was the finest archer of the Pandavas and drew Gandiva with either hand; Archery adds to the damage of your shots and stacks with its Gita-focus first shot.'),
    'bracers_of_atalanta': ('archery', "Atalanta drew first blood from the Calydonian Boar with an arrow when a band of heroes could not; the huntress' bracer is an archer's bracer. Her untouchability is already its dodge_bonus."),
    'vambraces_of_roland': ('parrying', "Roland's rear guard was surrounded at Roncevaux and held the pass sword in hand until the last man; Parrying turns the blows from beside you that would land."),
    'vambraces_of_the_first_winter': ('deflection', "Nothing in the arms stable speaks to primordial ice, so the slot's guard by default; Deflection turns aside rays and their riders, freezing among them, which suits ice that no cold since can teach."),
    'leggings_of_enkidu': ('mailed_shins', "Enkidu grew up wild among the gazelles and tore up the hunters' traps; leggings stitched from the wild years are proof against the teeth and stings of beasts, which is Mailed Shins."),
    'kilt_of_the_pharaoh': ('the_kneeler', 'The pharaoh was the priest-king who made the offerings, and a king was buried with his wardrobe because he trusted in the life after; that faith is the Kneeler (theology: prayer).'),
    'greaves_of_qin': ('mailed_shins', "Lacquered leather plates laced with cord, which very little eats through; the guard of the greave is the lore's greave."),
    'girdle_of_hippolyta': ('mailed_shins', "Nothing in the legs stable (Mailed Shins, the Kneeler) fits Ares' war belt, so the slot's guard by default; its Amazon charge stays."),
    'breeches_of_ragnar': ('mailed_shins', "Ragnar boiled his shaggy breeches in pitch and rolled them in sand so the serpent's venom ran off them: Mailed Shins turns aside bites and stings and shrugs off poison, the very deed that named him Lodbrok."),
    'greaves_of_goliath': ('mailed_shins', "Samuel lists bronze greaves on his legs, and they did their job perfectly; it was the forehead the stone found. The guard of the greave is the greave's own."),
    'green_girdle': ('the_kneeler', 'Gawain prayed to the Virgin on Christmas Eve and the castle appeared, confessed before the axe, and wore the girdle home as a mark of penance the whole Round Table took up: the Kneeler.'),
    'greaves_of_hermes': ('speed', "Its lore and power are one: whoever straps on the winged shin-guards of the messenger god finds the world has slowed (onEquipStatus 'hasted'), so Speed becomes the laddered form of it. Tier IV meets Speed's from_tier 4."),
    'boots_of_seven_leagues': ('speed', "Perrault's ogre's boots cover seven leagues at a stride and still want to go (onEquipStatus 'hasted'); Speed is that haste on the ladder, and the 7-tile dash stays its own. Tier IV meets Speed's from_tier 4."),
    'winged_sandals_of_hermes': ('levitation', "Homer's golden sandals carried Hermes over the wet sea and the boundless land, and Perseus outflew the Gorgons in them: wings on the feet lift you over the floor. Tier III meets Levitation's from_tier 3."),
    'hermes_sandals_early': ('the_wanderer', "A mortal cobbler's copy that a grateful courier hung on a temple wall after a safe journey: an offering to the god of travellers, which is the Wanderer (geography)."),
    'sandals_of_perseus': ('the_wanderer', 'These are what Perseus had on his feet when he set out from Seriphos, before any god lent him wings: a hero starts walking first. The plain sandals of the journey are the Wanderer.'),
    'sandals_of_theseus': ('free_stride', 'On the land road Theseus met Sinis, who tied men to bent pines, and Procrustes, who fitted them to his bed; no hold on that road kept him, and Free Stride shrugs off holds and slowing.'),
    'boots_of_thor': ('free_stride', 'Thor could not ride the rainbow bridge, so he waded four rivers every day and forded Vimur while a giantess swelled the flood; nothing slows him, which is Free Stride.'),
    'cloak_of_the_morrigan': ('displacement', 'The Phantom Queen came at Cu Chulainn as an eel, a wolf and a heifer, and to battles as a crow; a shape-shifter is never where the blow is aimed, which is Displacement. Tier IV meets its from_tier 3.'),
    'mantle_of_elijah': ('elementward', 'A chariot of fire took Elijah up and the mantle fell; its lore ends that fire has reason to respect it. Elementward turns aside fire and shrugs off burning. Tier II meets its from_tier 2.'),
    'cloak_of_sun_wukong': ('displacement', "Its wearer is seldom quite where he seems, and it already grants on_equip_status 'displacement'; the Monkey King's habit becomes the laddered Displacement."),
    'cloak_of_odin': ('elementward', 'In Grimnismal King Geirrod set the disguised Odin between two fires for eight nights until his cloak caught, and the cloak already keeps off the northern cold (cold 0.8); Elementward turns aside fire and cold. Tier II meets its from_tier 2 (Displacement, for his disguises, does not roll at tier II).'),
    'cloak_of_mulan': ('displacement', 'Her comrades of ten years never knew her, and the ballad ends that when two hares run side by side no one can tell which is which; a disguise that shows the foe someone who is not there is Displacement. Tier III meets its from_tier 3.'),
    'half_cloak_of_martin': ('elementward', 'Martin cut his army cloak in two for a beggar freezing at the gate of Amiens in winter; the half that keeps out the cold is Elementward (cold, and freezing).'),
    'anansi_web_cloak': ('displacement', 'Anansi the trickster bought every story by tricking the hornets, the python and the leopard into tying themselves up; the teller decides how it ends, and the foe swings at the story. Displacement. Tier V.'),
    'arachne_silk_cloak': ('vapourward', "In Ovid, Athena sprinkled Arachne with the juice of Hecate's herb and she became a spider; the cloak of the one changed by a sprinkling turns aside spray. The nearer of the slot's two guards; nothing else in the stable fits."),
    'erlking_mantle': ('vapourward', "In Goethe's poem the father sees only a streak of mist where his son sees the Erlking; the mantle of the king of the night fog turns aside breath and vapour. Tier II meets Vapourward's from_tier 2."),
    'falcon_cloak_of_freyja': ('displacement', 'Loki in the falcon cloak twice stayed a wingbeat ahead of what chased him; a flier who is never quite where the blow comes is Displacement, beside its dodge_bonus. Tier V.'),
    'mantle_of_muspelheim': ('elementward', 'Surtur has stood at the border of the fire-world since before the gods, and fire slides off his mantle like rain off slate; Elementward is fire turned aside. Tier V.'),
    'nidhoggr_scale': ('vapourward', "A dragon's own scale is proof against dragons' breath, and Voluspa puts Nidhoggr at Nastrond where venom drips through the roof into the wet and rot; Vapourward turns aside breath and spray. Tier V."),
    'robe_of_the_magus': ('the_hair_shirt', "The Magi were Persia's priests, and they followed the star to Bethlehem to worship; the priest's robe shortens the wait between prayers. Its spellcraft stays in its chain-equip tiers."),
    'robes_of_solomon': ('the_hair_shirt', "Solomon's wisdom was the answer to his prayer at Gibeon, and he gave the great prayer at the Temple's dedication; a king whose prayer was answered past what he asked. The Hair Shirt shortens the wait between prayers."),
    'hair_shirt_of_becket': ('the_hair_shirt', "The enchantment is named for it: the monks found the coarse hair shirt Becket wore unseen under his archbishop's robes."),
    'shirt_of_aslaug': ('vigor', "Aslaug's shirt kept blades from biting Ragnar and the snakes of Aella's pit from touching him until it was pulled off; Vigor turns aside poison and shrugs off poison and bleeding."),
    'seamless_tunic': ('vigor', 'Four soldiers agreed that the seamless tunic should not be torn but stay whole; Vigor keeps a body whole, shrugging off bleeding, disease and weakness.'),
}


def _depth_tier(pf: int) -> int:
    import gear
    w = gear.level_weights(pf)
    lv = max(range(1, gear.MAX_LEVEL + 1), key=lambda L: w[L - 1])
    return gear.tier_for_level(lv)


# Secret Build starting pieces (src/welcome_screen.py): a hero's own kit is
# floor-one gear and keeps its own tier.
STARTERS = ('shield_of_the_spartans', 'hermes_sandals_early', 'cloth_of_penelope',
            'trainers_cap')

# A chain rung whose only bonus was AC (gone from the minor slots) gets the
# piece's first lore power instead: the Helm of Darkness hides its wearer in
# the dark from the first rung.
RUNG_FILL = {'helm_of_hades': {'1': {'passive_stealth_in_dark': True}}}


def tier_of(e: dict, k: str = '') -> int:
    authored = max(1, min(5, int(e.get('tier', 1) or 1)))
    pf = int(e.get('peak_floor', 0) or 0)
    if e.get('plot_locked') or pf <= 1 or pf >= 999 or k in STARTERS:
        return authored
    return max(1, min(5, max(_depth_tier(pf) + 1, authored)))


def ladder(e: dict, category: str, k: str) -> dict:
    import gear
    import items
    e = dict(e)
    t = tier_of(e, k)
    level = gear.level_for_tier(t, greater=True)
    tpl = items.get_template(category, e.get('template_basis') or '') or {}
    wc = gear.weight_class(tpl) if tpl else 'light'
    slot = e.get('slot', 'shield') if category == 'armor' else 'shield'
    chain = bool(e.get('equip_chain_mode'))
    e['tier'] = t
    e['quiz_tier'] = t
    if int(e.get('equip_threshold', 1) or 0) > 0:
        # (0 is a trap that goes on with no quiz at all: the Duck of Doom.)
        e['equip_threshold'] = gear.equip_threshold(wc, level, unique=True)
    if slot in gear.MINOR_SLOTS:
        e['ac_bonus'] = 0
        e['enchant_bonus'] = 0
        e['ench_id'] = PICKS[k][0]
        e['ench_level'] = level
        for rung, tb in (e.get('tier_bonuses') or {}).items():
            if isinstance(tb, dict):
                tb.pop('ac_bonus', None)
                if not tb:
                    tb.update(RUNG_FILL.get(k, {}).get(rung, {}))
    elif not chain:
        e['ac_bonus'] = int(tpl.get('base_ac_value', e.get('ac_bonus', 0)) or 0)
        e['enchant_bonus'] = min(gear.core_enchant_cap(), gear.plus_for_level(level))
        e['ench_level'] = level
    return e


def run(path: str, category: str, check: bool) -> bool:
    import copy
    d, fmt = jsonfmt.load(path)
    new = {}
    for k, e in d.items():
        named = isinstance(e, dict) and e.get('is_unique')
        new[k] = ladder(copy.deepcopy(e), category, k) if named else e
    if new == d:
        return False
    if not check:
        jsonfmt.save(path, new, fmt)
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='report only; exit 1 if it would change')
    a = ap.parse_args(argv)
    changed = [run(ARMOR, 'armor', a.check), run(SHIELD, 'shields', a.check)]
    if a.check:
        return 1 if any(changed) else 0
    print('armor.json', 'changed' if changed[0] else 'unchanged',
          '| shield.json', 'changed' if changed[1] else 'unchanged')
    return 0


if __name__ == '__main__':
    sys.exit(main())
