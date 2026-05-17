"""Generate spellbook.json entries for the 32 new spells added in the 2026
spell rebalance. Iconic tome names span medieval, mythological, and modern
fantasy traditions. peak_floor + spread match the spell's quiz_tier band.

The 5 Witcher signs + 3 Elder Blood spells are character-build signature
spells and intentionally have NO spellbook — they're granted at build select."""
import json
import os

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Band → (min_level, peak_floor, spread, quiz_threshold, mp_cost target)
TIER_BAND = {
    1: (1, 8, 8, 2, 6),
    2: (15, 25, 10, 3, 12),
    3: (35, 45, 10, 4, 18),
    4: (55, 65, 10, 4, 24),
    5: (75, 85, 10, 5, 30),
}

# spell_id -> (spellbook_id, display name, color RGB, lore_short)
NEW_SPELLBOOKS = {
    # ---------- T1 ----------
    'frost_touch_spell':       ('spellbook_frost_touch',     'Spellbook of Frost Touch',     [200, 230, 250],
        "Bound in seal-skin, the pages still cold to the touch decades after copying. The first ice-cantrip every Lapp shaman learned."),
    'cure_wounds_spell':       ('spellbook_cure_wounds',     'Spellbook of Cure Wounds',     [240, 200, 200],
        "Field-medicine compendium from a battlefield priest. The pages are stained with what looks like wine but smells like older liquid."),
    'mage_armor_spell':        ('spellbook_mage_armor',      'Spellbook of Mage Armor',      [160, 180, 240],
        "Mage Armor: the most fundamental defensive cantrip. Every wizards' college copy is dog-eared at this page."),
    'detect_magic_spell':      ('spellbook_detect_magic',    'Spellbook of Detect Magic',    [200, 200, 250],
        "Dee's earliest divination tract — translation from the original Enochian, partial fragments only."),
    'blink_spell':             ('spellbook_blink',           'Spellbook of Blink',           [200, 150, 250],
        "An apprentice's first teleportation primer. Includes a footnote warning against blinking over deep water."),

    # ---------- T2 ----------
    'lightning_bolt_spell':    ('spellbook_lightning_bolt',  'Spellbook of Lightning Bolt',  [240, 240, 80],
        "Tesla's diary copy of the bolt-line incantation. Margin notes question whether the chalk was the resonator."),
    'sleep_mass_spell':        ('spellbook_mass_sleep',      'Spellbook of Mass Sleep',      [120, 120, 200],
        "Lullaby of the Watchman of Antioch — read aloud, every sleeper in the room dreams of the same hill."),
    'detect_monsters_spell_t2': ('spellbook_detect_monsters_t2', 'Spellbook of Greater Detection', [120, 220, 200],
        "Detection cantrip transcribed from a Sufi divinatory manual. Each page bears a single eye in gold leaf."),
    'levitate_spell':          ('spellbook_levitate',        'Spellbook of Levitation',      [180, 220, 240],
        "St Joseph of Cupertino's confessional notes — the saint who could not stop floating. Several editions, all repudiated."),

    # ---------- T3 ----------
    'cone_of_cold_spell':      ('spellbook_cone_of_cold',    'Spellbook of Cone of Cold',    [100, 200, 240],
        "Annals of Norilsk: thirty years of arctic-mage observations bound by the Soviet Academy and promptly classified."),
    'greater_heal_spell':      ('spellbook_greater_heal',    'Spellbook of Greater Heal',    [240, 200, 180],
        "Galen's Greater Healing — recovered from the Library of Alexandria fire by an apprentice who lost his arm carrying it out."),
    'stoneskin_spell':         ('spellbook_stoneskin',       'Spellbook of Stoneskin',       [160, 160, 160],
        "Dwarven Cantor's diary — describes the breath-technique that hardens the body to stone for one full breath cycle of seconds."),
    'counterspell_spell':      ('spellbook_counterspell',    'Spellbook of Counterspell',    [200, 100, 240],
        "Mordenkainen's Argument — a single chapter on undoing another's working before it lands."),
    'dispel_magic_spell':      ('spellbook_dispel_magic',    'Spellbook of Dispel Magic',    [180, 80, 220],
        "The Latin original of the rite — late-Renaissance, copied off a folio Dee burned but didn't burn well enough."),
    'mapping_spell':           ('spellbook_mapping',         'Spellbook of Mapping',         [160, 200, 120],
        "Geomancer's pocket-folio: ink lines that reveal themselves when held over candle smoke."),

    # ---------- T4 ----------
    'chain_lightning_spell':   ('spellbook_chain_lightning_t4', 'Spellbook of Forked Lightning', [255, 240, 100],
        "Storm-singer's grimoire — the sequel to Lightning Bolt. The arc-jump math is in the appendix."),
    'greater_invisibility_spell': ('spellbook_greater_invis', 'Spellbook of Greater Invisibility', [180, 220, 220],
        "Tarnhelm research notes from the Bayreuth Festival library — three Wagner-era scholars vanished while reading it."),
    'mass_paralyze_spell':     ('spellbook_mass_paralyze',   'Spellbook of Mass Paralysis',  [200, 100, 100],
        "Carpathian witch's recipe — paralysis was always her preferred technique, never the killing blow."),
    'banishment_spell':        ('spellbook_banishment',      'Spellbook of Banishment',      [240, 200, 100],
        "Solomon's binding-rite, distilled to the essentials. Useful only against what came from elsewhere."),
    'phase_door_spell':        ('spellbook_phase_door',      'Spellbook of Phase Door',      [180, 180, 230],
        "Bilocation manual by the unknown St-Germain. The author's name still spreads slowly through the table of contents."),
    'turn_undead_spell':       ('spellbook_turn_undead',     'Spellbook of Turn Undead',     [240, 240, 200],
        "Vesper-prayer compendium — clerical, but the working incantation is the same one wizards use."),

    # ---------- T5 ----------
    'meteor_swarm_spell':      ('spellbook_meteor_swarm',    'Spellbook of Meteor Swarm',    [255, 100, 60],
        "Recovered from the Tunguska crater. Pages charred at edges; the central diagram is intact."),
    'storm_of_vengeance_spell': ('spellbook_storm_of_vengeance', 'Spellbook of Storm of Vengeance', [180, 120, 220],
        "Zeus-rite copied by an Athenian heretic in 320 BCE. He was struck by lightning shortly after. The book was not."),
    'wish_spell':              ('spellbook_wish',            'Spellbook of Wish',            [240, 200, 100],
        "A single page. The page is blank. Read it anyway."),
    'power_word_kill_spell':   ('spellbook_power_word_kill', 'Spellbook of Power Word Kill', [40, 40, 80],
        "The Vorpal Word, the cantrip the headsmen kept secret. One syllable. Several deaths."),
    'resurrection_spell':      ('spellbook_resurrection',    'Spellbook of Resurrection',    [240, 240, 200],
        "Lazarus liturgy — full text, with the rabbinical disclaimer that nobody who has tried it has reported their experience usefully."),
    'foresight_spell':         ('spellbook_foresight',       'Spellbook of Foresight',       [220, 200, 240],
        "Cassandra's notes, copied centuries later by a librarian who later refused to admit knowing what was in them."),
    'gate_spell':              ('spellbook_gate',            'Spellbook of Gate',            [220, 180, 60],
        "Crowley's annotated translation of the Lemegeton gate-rite. Several entries in the index are crossed out by a different hand."),
    'imprisonment_spell':      ('spellbook_imprisonment',    'Spellbook of Imprisonment',    [120, 120, 100],
        "Persian source-text on binding-into-stone — used originally against a particular djinn who was getting out of hand."),
    'mass_polymorph_spell':    ('spellbook_mass_polymorph',  'Spellbook of Mass Polymorph',  [180, 200, 160],
        "Circe's school-notes from her time on Aeaea. Footnotes mention various species considered for the conversion."),
    'annihilation_spell':      ('spellbook_annihilation',    'Spellbook of Annihilation',    [80, 0, 100],
        "Final chapter of the Liber Nihili — only the final chapter survives, and reads as a list of what no longer is."),
}


def main():
    sb_p = os.path.join(REPO, 'data', 'items', 'spellbook.json')
    with open(sb_p, encoding='utf-8') as f:
        books = json.load(f)

    # Need spell defs for tier/cost lookup
    import importlib, sys
    sys.path.insert(0, os.path.join(REPO, 'src'))
    import spells as _spells

    added = 0
    skipped = []
    for spell_id, (book_id, name, color, lore) in NEW_SPELLBOOKS.items():
        if spell_id not in _spells.LEARNABLE_SPELLS:
            skipped.append(spell_id)
            continue
        if book_id in books:
            print(f"  SKIP: {book_id} already exists")
            continue
        spell_def = _spells.LEARNABLE_SPELLS[spell_id]
        tier = spell_def['quiz_tier']
        min_level, peak_floor, spread, threshold, mp_target = TIER_BAND[tier]
        books[book_id] = {
            'name': name,
            'symbol': '+',
            'color': color,
            'weight_lb': 3.0,
            'min_level': min_level,
            'peak_floor': peak_floor,
            'spread': spread,
            'peak_weight': 0.3,
            'quiz_tier': tier,
            'quiz_threshold': threshold,
            'read_threshold': threshold,
            'spell_id': spell_id,
            'spell_name': spell_def['name'],
            'mp_cost': spell_def.get('mp_cost', mp_target),
            'unidentified_name': 'an unfamiliar tome',
            'sprite_desc': f"A {['', '', '', '', 'thick'][min(4, tier-1)]} tome bound in dark leather, "
                           f"the cover sigil glowing faintly.",
            'lore': lore,
        }
        added += 1

    with open(sb_p, 'w', encoding='utf-8') as f:
        json.dump(books, f, indent=2, ensure_ascii=False)
    print(f"Added {added} spellbooks. Total entries: {len(books)}")
    if skipped:
        print(f"Skipped (spell_id not in LEARNABLE_SPELLS): {skipped}")


if __name__ == '__main__':
    main()
