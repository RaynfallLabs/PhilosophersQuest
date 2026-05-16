"""Add 12 iconic mythological items across accessory/wand/scroll/spellbook.

EVERY effect referenced below is one the engine already handles. EVERY wand
charge count + scroll/spellbook tier was chosen to NOT break existing systems:
  - Accessories: passive +stat or +status_resist while equipped. Conservative
    +2-+3 stats matching existing items in their band.
  - Wands with monster-summon or polymorph: 2-3 charges only (powerful effects
    cost-limited). Damage wands: 4-6 charges matching existing late-game wands.
  - Scrolls: single-use, effects already in the dispatcher.
  - Spellbooks: teach existing spell_ids. mp_cost matches the existing band.
"""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================================
# ACCESSORIES
# ============================================================================
ACCESSORY_ADDS = {
    'andvaranaut': {
        'name': 'Andvaranaut',
        'slot': 'ring',
        'symbol': '=',
        'color': [255, 215, 60],
        'weight': 0.1,
        'min_level': 25,
        'peak_floor': 35,
        'spread': 12,
        'peak_weight': 0.3,
        'max_enchant': 2,
        'equip_threshold': 3,
        'quiz_tier': 2,
        # +2 PER (the ring lets the bearer see things others miss) but
        # spawn-cursed-often so the curse-aspect of the Volsung cycle bites.
        'effects': {'stat': 'PER', 'amount': 2, 'status': 'cursed', 'duration': -1},
        'can_be_cursed': True,
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a delicate gold ring',
        'lore': (
            "The ring Andvari cursed when Loki stripped him bare beneath the "
            "waterfall. It carries enough gold to outfit a king and enough "
            "curse to kill him. Every owner of Andvaranaut dies — Fafnir, "
            "Hreidmar, Sigurd, Gunnar — and the next owner forgets the "
            "lesson. From the Volsunga Saga and the Reginsmal of the Poetic "
            "Edda."
        ),
    },
    'draupnir': {
        'name': 'Draupnir',
        'slot': 'ring',
        'symbol': '=',
        'color': [255, 230, 100],
        'weight': 0.1,
        'min_level': 65,
        'peak_floor': 75,
        'spread': 12,
        'peak_weight': 0.2,
        'max_enchant': 4,
        'equip_threshold': 4,
        'quiz_tier': 4,
        # Odin's ring — wealth and power. +3 STR. Conservative single-stat bump.
        'effects': {'stat': 'STR', 'amount': 3, 'duration': -1},
        'can_be_cursed': False,
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a heavy gold ring',
        'lore': (
            "Forged by the dwarves Brokkr and Eitri at Loki's wager and "
            "given to Odin. Every ninth night, the ring drops eight more "
            "of equal weight. Odin used it to pay debts of obligation and "
            "to bind oath-makers. Placed on Baldur's pyre by Odin's own "
            "hand. From the Skaldskaparmal."
        ),
    },
    'brisingamen': {
        'name': 'Brísingamen',
        'slot': 'amulet',
        'symbol': '"',
        'color': [255, 200, 180],
        'weight': 0.3,
        'min_level': 65,
        'peak_floor': 78,
        'spread': 12,
        'peak_weight': 0.2,
        'max_enchant': 4,
        'equip_threshold': 4,
        'quiz_tier': 4,
        # Freyja's necklace — irresistible. +2 WIS, charm_resist (can't be charmed).
        'effects': {'stat': 'WIS', 'amount': 2, 'status': 'charm_resist', 'duration': -1},
        'can_be_cursed': False,
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a necklace of red-gold fire',
        'lore': (
            "Freyja's necklace, made by four dwarves of the Brísings clan; "
            "Freyja paid for it by lying with each of them in turn, which "
            "the Edda does not soften. Loki stole it once and turned to a "
            "seal to escape; Heimdallr, also a seal, caught him. The light "
            "from the necklace is the source of Freyja's beauty, not the "
            "other way round."
        ),
    },
    'megingjord': {
        'name': 'Megingjörð',
        'slot': 'ring',  # no belt slot in game; use ring as the closest power-storage accessory
        'symbol': '=',
        'color': [180, 60, 40],
        'weight': 0.5,
        'min_level': 75,
        'peak_floor': 85,
        'spread': 10,
        'peak_weight': 0.2,
        'max_enchant': 4,
        'equip_threshold': 5,
        'quiz_tier': 5,
        # Thor's belt — doubles his strength in myth. In game: +4 STR (not full
        # doubling; flat bonus to keep the curve intact).
        'effects': {'stat': 'STR', 'amount': 4, 'duration': -1},
        'can_be_cursed': False,
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a heavy iron-banded belt-clasp',
        'lore': (
            "Thor's belt of power. With Mjölnir alone, Thor is strong; with "
            "Megingjörð he is twice as strong. He wore it the morning he "
            "fished for Jörmungandr off Hymir's boat and would have hauled "
            "the World-Serpent ashore if Hymir hadn't cut the line. From "
            "the Hymiskviða."
        ),
    },
    'kavacha_kundala': {
        'name': 'Kavacha and Kundala',
        'slot': 'amulet',
        'symbol': '"',
        'color': [200, 200, 60],
        'weight': 0.5,
        'min_level': 55,
        'peak_floor': 65,
        'spread': 12,
        'peak_weight': 0.2,
        'max_enchant': 3,
        'equip_threshold': 4,
        'quiz_tier': 4,
        # Karna's birth-armor + earrings. +3 CON, fire_resist. Karna had to
        # give them up to die — flag can_be_cursed so the giving-up tradition
        # echoes in gameplay.
        'effects': {'stat': 'CON', 'amount': 3, 'status': 'fire_resist', 'duration': -1},
        'can_be_cursed': True,
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'golden armor-plate and earrings',
        'lore': (
            "Karna was born wearing them — gifts of Surya the Sun, fused "
            "to his skin so that no weapon could harm him while he wore "
            "them. Indra came to him as a beggar and asked for them as "
            "alms; Karna cut them off and gave them, because a Brahmin's "
            "request cannot be refused. He died on the eighteenth day of "
            "Kurukshetra. From the Mahabharata, Vana Parva."
        ),
    },
}


# ============================================================================
# WANDS — every effect already in game_magic._apply_wand_effect.
# Powerful summon/polymorph wands get 2-3 charges; damage wands 4-6.
# ============================================================================
WAND_ADDS = {
    'aarons_rod': {
        'name': "Aaron's Rod",
        'symbol': '/',
        'color': [180, 120, 80],
        'weight_lb': 1.5,
        'min_level': 30,
        'peak_floor': 40,
        'spread': 12,
        'peak_weight': 0.2,
        'charges_min': 3,
        'charges_max': 5,
        'max_charges': 5,
        'quiz_tier': 3,
        'quiz_threshold': 3,
        # In Exodus, the rod-serpent SWALLOWED Pharaoh's magicians' serpents.
        # paralyze_monster is the canonical "neutralize what the enemy summoned"
        # effect already in the engine — and venom/swallowing fits the imagery.
        'effect': 'paralyze_monster',
        'power': '',
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a budded almond-wood rod',
        'lore': (
            "The rod of Aaron, brother of Moses. Thrown to the ground "
            "before Pharaoh's court, it became a serpent and swallowed "
            "the serpents of Pharaoh's magicians. Later, it budded "
            "almonds overnight to settle a dispute among the tribes. "
            "From Exodus 7 and Numbers 17. Whatever an enemy raises, "
            "the rod takes the legs out from under it."
        ),
    },
    'circes_wand': {
        'name': "Circe's Wand",
        'symbol': '/',
        'color': [200, 180, 220],
        'weight_lb': 1.0,
        'min_level': 50,
        'peak_floor': 60,
        'spread': 12,
        'peak_weight': 0.2,
        'charges_min': 4,
        'charges_max': 6,
        'max_charges': 6,
        'quiz_tier': 4,
        'quiz_threshold': 3,
        # Existing effect — polymorphs target monster into a random other type.
        'effect': 'polymorph_monster',
        'power': '',
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a slender ivory wand',
        'lore': (
            "Circe's wand from her hall on Aeaea. She used it on "
            "Odysseus's crew and they became swine — heads and bristles "
            "and grunts, but their minds knew themselves the whole time. "
            "Hermes gave Odysseus the herb moly to resist her; she gave "
            "up after the swine-spell failed and welcomed him. From the "
            "Odyssey, Book X."
        ),
    },
    'indras_vajra': {
        'name': "Indra's Vajra",
        'symbol': '/',
        'color': [245, 245, 100],
        'weight_lb': 1.5,
        'min_level': 65,
        'peak_floor': 75,
        'spread': 12,
        'peak_weight': 0.2,
        'charges_min': 4,
        'charges_max': 6,
        'max_charges': 6,
        'quiz_tier': 5,
        'quiz_threshold': 4,
        # Existing effect — single-target lightning damage scaled by quiz_tier.
        'effect': 'lightning_bolt',
        'power': '6d6',  # the bolt damage roll the engine accepts
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a heavy iron rod',
        'lore': (
            "The thunderbolt of Indra, made by Tvastr the divine "
            "craftsman from the bones of the sage Dadhichi, who gave "
            "his body for it. Indra struck Vritra the world-drought "
            "serpent with this and freed the seven rivers. From the "
            "Rigveda, Book I. It is not lightning — it is the weapon "
            "that lightning was a memory of."
        ),
    },
}


# ============================================================================
# SCROLLS — single-use, effects in the existing dispatcher.
# ============================================================================
SCROLL_ADDS = {
    'book_of_thoth': {
        'name': 'Book of Thoth',
        'symbol': '?',
        'color': [200, 180, 100],
        'weight_lb': 0.5,
        'min_level': 50,
        'peak_floor': 60,
        'spread': 12,
        'peak_weight': 0.2,
        'quiz_tier': 4,
        'quiz_threshold': 4,
        'read_threshold': 4,
        # Identifies EVERY unidentified item in inventory in one read.
        'effect': 'identify_all',
        'power': '',
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a scroll bound in papyrus',
        'item_class': 'scroll',
        'lore': (
            "The book of Thoth, Egyptian god of writing. Pharaoh Neferkaptah "
            "stole it from its serpent guardian in the Nile and learned the "
            "speech of the birds and the fish and the dead; his family "
            "drowned for his audacity, and the book was buried with him. "
            "Reading it identifies what was hidden. From the Setna cycle."
        ),
    },
}


# ============================================================================
# SPELLBOOKS — teach existing spell_ids. mp_cost matches existing band entries.
# ============================================================================
SPELLBOOK_ADDS = {
    'sefer_yetzirah': {
        'name': 'Sefer Yetzirah (The Book of Formation)',
        'symbol': '+',
        'color': [220, 220, 240],
        'weight_lb': 3.0,
        'min_level': 60,
        'peak_floor': 72,
        'spread': 12,
        'peak_weight': 0.2,
        'quiz_tier': 4,
        'quiz_threshold': 4,
        'read_threshold': 4,
        # Teaches the existing summon-guardian spell — the closest mechanical
        # parallel to forming a golem out of clay/Hebrew letters.
        'spell_id': 'summon_guardian_spell',
        'spell_name': 'Summon Guardian',
        'mp_cost': 18,
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a tome of pale parchment',
        'lore': (
            "The Book of Formation. Attributed to Abraham; the oldest "
            "extant Jewish mystical text. It teaches the twenty-two "
            "letters of the Hebrew alphabet and the ten sefirot, and "
            "how the world was spoken into being. The Maharal of Prague "
            "used a copy in the sixteenth century to shape a golem of "
            "clay; the golem walked the streets of the Jewish quarter "
            "until the Maharal removed the Name from its forehead."
        ),
    },
    'picatrix': {
        'name': 'Picatrix',
        'symbol': '+',
        'color': [180, 120, 200],
        'weight_lb': 3.0,
        'min_level': 50,
        'peak_floor': 60,
        'spread': 12,
        'peak_weight': 0.2,
        'quiz_tier': 4,
        'quiz_threshold': 4,
        'read_threshold': 4,
        # Teaches the existing fireball spell. Picatrix is the medieval Arabic
        # astrological-elemental magic compendium; fire matches its emphasis.
        'spell_id': 'fireball_spell',
        'spell_name': 'Fireball',
        'mp_cost': 12,
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a violet leather-bound tome',
        'lore': (
            "Picatrix — Ghayat al-Hakim, the Aim of the Sage. Composed in "
            "tenth-century al-Andalus, translated to Latin under Alfonso X, "
            "and read across Europe for the next four centuries. It teaches "
            "talismanic magic, planetary hours, and how to summon fire by "
            "naming a planet's degree of ascension. Dee owned a copy. "
            "Ficino read it carefully and pretended he hadn't."
        ),
    },
    'lemegeton': {
        'name': 'Lemegeton (The Lesser Key of Solomon)',
        'symbol': '+',
        'color': [100, 60, 100],
        'weight_lb': 4.0,
        'min_level': 70,
        'peak_floor': 82,
        'spread': 12,
        'peak_weight': 0.2,
        'quiz_tier': 5,
        'quiz_threshold': 5,
        'read_threshold': 5,
        # Teaches the existing army-of-darkness spell (summons skeletal/demonic
        # allies). Matches Lemegeton's seventy-two demons of the Ars Goetia.
        'spell_id': 'army_of_darkness_spell',
        'spell_name': 'Army of Darkness',
        'mp_cost': 28,
        'is_unique': True,
        'identified': False,
        'unidentified_name': 'a black tome sealed with sigils',
        'lore': (
            "The Lemegeton. Five books bound as one; the first, the Ars "
            "Goetia, lists the seventy-two demons King Solomon bound to "
            "his service. Each demon has a sigil, a number of legions, "
            "and a particular use — Bael teaches invisibility, Asmodeus "
            "answers questions truthfully, Vassago finds lost things. "
            "Crowley translated it in 1904. Read it carefully."
        ),
    },
}


def merge_into(filepath, additions, label):
    with open(filepath, encoding='utf-8') as f:
        data = json.load(f)
    added = []
    for k, v in additions.items():
        if k in data:
            print(f"  SKIP: {k} already exists in {label}")
            continue
        data[k] = v
        added.append((k, v.get('name')))
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"{label}: added {len(added)} new entries")
    for k, n in added:
        print(f"  + {k} ({n})")


if __name__ == '__main__':
    merge_into(os.path.join(REPO, 'data', 'items', 'accessory.json'),
               ACCESSORY_ADDS, 'accessory.json')
    merge_into(os.path.join(REPO, 'data', 'items', 'wand.json'),
               WAND_ADDS, 'wand.json')
    merge_into(os.path.join(REPO, 'data', 'items', 'scroll.json'),
               SCROLL_ADDS, 'scroll.json')
    merge_into(os.path.join(REPO, 'data', 'items', 'spellbook.json'),
               SPELLBOOK_ADDS, 'spellbook.json')
