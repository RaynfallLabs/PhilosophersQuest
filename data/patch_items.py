"""Patch item JSON files: add tier 3-5 scrolls, tier 5 wands, 3 new lockpicks, 10 tier-4 accessories."""
import json, os

BASE = os.path.join(os.path.dirname(__file__), 'items')

def patch(fname, new_items):
    path = os.path.join(BASE, fname)
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    added = 0
    for k, v in new_items.items():
        if k not in data:
            data[k] = v
            added += 1
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  {fname}: +{added} items (skipped {len(new_items)-added} existing)")

# ── SCROLLS ───────────────────────────────────────────────────────────────────
NEW_SCROLLS = {
  "scroll_of_sleep": {
    "name": "scroll of sleep", "symbol": "?", "color": [160, 160, 240],
    "weight": 0.1, "min_level": 5, "quiz_tier": 3, "quiz_threshold": 4,
    "effect": "sleep_monsters", "power": "",
    "unidentified_name": "drowsy scroll",
    "lore": "Penned by the dream-weavers of Morpheus in ink distilled from poppy essence, this scroll releases a wave of irresistible somnolence. Every creature in sight is swept into deep slumber — only the reader, having spoken the words aloud, remains awake and free to act."
  },
  "scroll_of_haste": {
    "name": "scroll of haste", "symbol": "?", "color": [240, 240, 80],
    "weight": 0.1, "min_level": 8, "quiz_tier": 3, "quiz_threshold": 4,
    "effect": "haste_self", "power": "15",
    "unidentified_name": "blurred scroll",
    "lore": "Written in quicksilver ink by fleet-footed Hermes himself — or so the seller claimed — this scroll binds the speed-essence of the divine messenger into the reader's limbs. For a short time, reality slows around you while you move at twice the natural pace."
  },
  "scroll_of_enchant_armor": {
    "name": "scroll of enchant armor", "symbol": "?", "color": [200, 160, 255],
    "weight": 0.1, "min_level": 6, "quiz_tier": 3, "quiz_threshold": 4,
    "effect": "enchant_armor", "power": "",
    "unidentified_name": "gleaming scroll",
    "lore": "The armorers' guilds of three ages of the world spent centuries perfecting this scroll. Reading it aloud over a worn piece of armor causes the metal (or leather, or hide) to tighten, harden, and align — one permanent layer of reinforcement added to whatever protection you bear."
  },
  "scroll_of_teleportation": {
    "name": "scroll of teleportation", "symbol": "?", "color": [100, 220, 255],
    "weight": 0.1, "min_level": 12, "quiz_tier": 4, "quiz_threshold": 5,
    "effect": "teleport_self", "power": "",
    "unidentified_name": "trembling scroll",
    "lore": "The spatial theorists of Alexandria considered this scroll a philosophical as much as a practical achievement. Reading it dissolves your relationship with the current point in space and reconstitutes you at some other floor tile, selected at the whim of the dungeon."
  },
  "scroll_of_charging": {
    "name": "scroll of charging", "symbol": "?", "color": [120, 200, 140],
    "weight": 0.1, "min_level": 15, "quiz_tier": 4, "quiz_threshold": 5,
    "effect": "charging", "power": "",
    "unidentified_name": "crackling scroll",
    "lore": "Inscribed by the artificers who first learned to trap raw magical force in crystalline matrices, this scroll rekindles exhausted power. Upon reading, ambient magical energy floods into every wand in the reader's possession, refreshing their reserves by one full charge each."
  },
  "scroll_of_identify_all": {
    "name": "scroll of mass identify", "symbol": "?", "color": [255, 230, 130],
    "weight": 0.1, "min_level": 14, "quiz_tier": 4, "quiz_threshold": 5,
    "effect": "identify_all", "power": "",
    "unidentified_name": "revealing scroll",
    "lore": "A far more powerful version of the common identification scroll. This text requires the reader to articulate the true name of knowledge itself. Upon completion, every obscured, unnamed, and unexamined item in one's possession is simultaneously revealed in full."
  },
  "scroll_of_annihilation": {
    "name": "scroll of annihilation", "symbol": "?", "color": [255, 80, 80],
    "weight": 0.1, "min_level": 30, "quiz_tier": 5, "quiz_threshold": 6,
    "effect": "annihilate", "power": "",
    "unidentified_name": "scorched scroll",
    "lore": "The most feared text in the dungeon archivist's catalogue. Its words were first spoken on the day the great library of Carthage burned. Reading it perfectly causes every creature in sight to dissolve in a flash of obliterating white energy, leaving only silence and ash."
  },
  "scroll_of_time_stop": {
    "name": "scroll of time stop", "symbol": "?", "color": [200, 220, 255],
    "weight": 0.1, "min_level": 40, "quiz_tier": 5, "quiz_threshold": 6,
    "effect": "time_stop_scroll", "power": "10",
    "unidentified_name": "frozen scroll",
    "lore": "The theoretical framework for this scroll was laid by Zeno of Elea, who proved logically that motion is an illusion. Ten turns of absolute stillness surround the reader: monsters freeze mid-stride, arrows hang in mid-air, the dungeon holds its breath."
  },
  "scroll_of_great_power": {
    "name": "scroll of great power", "symbol": "?", "color": [255, 215, 0],
    "weight": 0.1, "min_level": 50, "quiz_tier": 5, "quiz_threshold": 6,
    "effect": "great_power", "power": "",
    "unidentified_name": "blazing scroll",
    "lore": "The capstone work of the philosopher Porphyry, who spent forty years distilling the essence of Aristotle's categories into a single transformative incantation. Those few who have read it perfectly emerge changed: stronger, hardier, swifter, keener, wiser, more perceptive. Every faculty permanently elevated by one degree."
  }
}

# ── WANDS ─────────────────────────────────────────────────────────────────────
NEW_WANDS = {
  "wand_of_nova": {
    "name": "wand of nova", "symbol": "/", "color": [255, 200, 80],
    "weight": 0.5, "min_level": 60, "quiz_tier": 5, "quiz_threshold": 4,
    "charges_min": 2, "charges_max": 4, "max_charges": 4,
    "effect": "nova", "power": "4d8",
    "unidentified_name": "blazing wand",
    "containerLootTier": "legendary",
    "floorSpawnWeight": {"81-100": 1},
    "lore": "Recovered from the ruins of the great star-mages' observatory, this wand releases a burst of stellar energy that radiates to every corner of the floor. No creature on the level is safe when it fires. The light of a dying star, compressed and redirected.",
    "identified": False
  },
  "wand_of_life_force": {
    "name": "wand of life force", "symbol": "/", "color": [180, 80, 255],
    "weight": 0.5, "min_level": 70, "quiz_tier": 5, "quiz_threshold": 4,
    "charges_min": 3, "charges_max": 5, "max_charges": 5,
    "effect": "life_transfer", "power": "",
    "unidentified_name": "pulsing wand",
    "containerLootTier": "legendary",
    "floorSpawnWeight": {"81-100": 1},
    "lore": "Forged by necromancers who believed that life energy is conserved rather than destroyed, this wand creates a conduit between wielder and target. The target's vitality flows directly into the user. The more wounded your enemy, the more you gain.",
    "identified": False
  },
  "wand_of_abjuration": {
    "name": "wand of abjuration", "symbol": "/", "color": [140, 200, 255],
    "weight": 0.5, "min_level": 65, "quiz_tier": 5, "quiz_threshold": 4,
    "charges_min": 3, "charges_max": 5, "max_charges": 5,
    "effect": "abjuration", "power": "",
    "unidentified_name": "clear wand",
    "containerLootTier": "legendary",
    "floorSpawnWeight": {"81-100": 1},
    "lore": "A masterwork of defensive magic theory. This wand simultaneously strips all applied enchantments from a target and purges the wielder of their own afflictions. Wielded in desperation or with surgical precision, it can turn the tide of a losing battle by resetting the magical state of both combatants.",
    "identified": False
  }
}

# ── LOCKPICKS ─────────────────────────────────────────────────────────────────
NEW_LOCKPICKS = {
  "mithril_lockpick": {
    "name": "mithril lockpick", "symbol": "~", "color": [180, 220, 255],
    "weight": 0.1, "min_level": 12,
    "max_durability": 15, "durability": 15,
    "durability_loss_success": 0, "durability_loss_failure": 1,
    "unidentified_name": "silvery pick",
    "lore": "Drawn from a single strand of mithril by elvish jewelers, this pick is supernaturally light and rigid. It transmits the subtlest mechanical signals through its shaft into the wielder's fingertips, making even complex lock mechanisms feel transparent. Success never dulls it — only failure leaves a mark."
  },
  "diamond_lockpick": {
    "name": "diamond lockpick", "symbol": "~", "color": [220, 245, 255],
    "weight": 0.1, "min_level": 28,
    "max_durability": 25, "durability": 25,
    "durability_loss_success": 0, "durability_loss_failure": 0,
    "unidentified_name": "crystalline pick",
    "lore": "Ground from a single diamond crystal by the artificer-monks of the high reaches, this pick is functionally indestructible. It cannot be broken by failure or success — only lost. Thieves who carry one treat it as a sacred object, the highest expression of their craft."
  },
  "philosophers_pick": {
    "name": "philosopher's pick", "symbol": "~", "color": [255, 240, 180],
    "weight": 0.1, "min_level": 50,
    "max_durability": 99, "durability": 99,
    "durability_loss_success": 0, "durability_loss_failure": 0,
    "unidentified_name": "radiant pick",
    "lore": "Legend holds that this was fashioned by Daedalus himself after escaping the Labyrinth — an instrument capable of opening any lock in any world. It never dulls, never breaks, and never fails in the hands of the learned. To carry it is to carry the proof that all barriers are merely puzzles awaiting the correct solution."
  }
}

# ── ACCESSORIES (10 new tier 4) ───────────────────────────────────────────────
NEW_ACCESSORIES = {
  "ring_of_thunder": {
    "name": "Ring of Thunder", "symbol": "=", "color": [180, 200, 255],
    "weight": 0.1, "min_level": 20, "slot": "ring",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "INT", "amount": 2, "status": "shock_resist", "duration": -1},
    "identified": False, "unidentified_name": "crackling ring",
    "lore": "Forged in the heart of a perpetual thunderstorm by an Aztec storm-caller, this ring hums with suppressed electrical charge. Lightning that strikes the wearer grounds harmlessly through the stone, while the storm energy sharpens the intellect to razor clarity."
  },
  "amulet_of_the_titan": {
    "name": "Amulet of the Titan", "symbol": "\"", "color": [220, 160, 80],
    "weight": 0.3, "min_level": 22, "slot": "amulet",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "STR", "amount": 3},
    "identified": False, "unidentified_name": "heavy amulet",
    "lore": "Cast from ore pulled from the bones of fallen Titans by Hephaestus as a jest, this amulet transfers a sliver of Titanic strength to the wearer. Those with the constitution to bear it find themselves capable of feats of impossible might."
  },
  "ring_of_the_deep": {
    "name": "Ring of the Deep", "symbol": "=", "color": [60, 140, 200],
    "weight": 0.1, "min_level": 18, "slot": "ring",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "CON", "amount": 2, "status": "cold_resist", "duration": -1},
    "identified": False, "unidentified_name": "cold blue ring",
    "lore": "Carved from a bioluminescent crystal found only at extreme ocean depth, this ring adapts the wearer's constitution to the crushing cold of the abyss. Divers of the Phoenician coast traded entire fortunes for such rings, which allowed descent to waters where no natural body could survive."
  },
  "amulet_of_insight": {
    "name": "Amulet of Insight", "symbol": "\"", "color": [255, 240, 140],
    "weight": 0.2, "min_level": 20, "slot": "amulet",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "WIS", "amount": 3},
    "identified": False, "unidentified_name": "warm amulet",
    "lore": "Handed down through thirty-six generations of oracle-priests at Delphi, this focus crystal was used to receive the god's voice without distortion. The priests believed wisdom was not intelligence but receptivity — and this amulet sharpens that receptivity to inhuman degree."
  },
  "ring_of_the_assassin": {
    "name": "Ring of the Assassin", "symbol": "=", "color": [100, 100, 140],
    "weight": 0.1, "min_level": 25, "slot": "ring",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "DEX", "amount": 3, "status": "invisible", "duration": -1},
    "identified": False, "unidentified_name": "dark ring",
    "lore": "The signet of the Hashshashin grandmaster, recovered after the sack of Alamut. The ring's stone refracts light around the wearer with unsettling precision. Paired with the supernatural quickness it grants, its bearer becomes effectively impossible to track in dim light."
  },
  "amulet_of_fortitude": {
    "name": "Amulet of Fortitude", "symbol": "\"", "color": [80, 200, 120],
    "weight": 0.2, "min_level": 24, "slot": "amulet",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "CON", "amount": 3, "status": "regenerating", "duration": -1},
    "identified": False, "unidentified_name": "pulsing amulet",
    "lore": "A gift from Asclepius to a mortal champion whose constitution had been ravaged by poison. The carved serpent at its centre channels a fraction of divine healing energy into the wearer continuously. Wounds knit, poisons fade, and exhaustion retreats in its presence."
  },
  "ring_of_far_sight": {
    "name": "Ring of Far Sight", "symbol": "=", "color": [200, 240, 180],
    "weight": 0.1, "min_level": 22, "slot": "ring",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "PER", "amount": 3, "status": "warning", "duration": -1},
    "identified": False, "unidentified_name": "pale green ring",
    "lore": "Fashioned by the eagle-eyed sentinels of the Watchtower of Rhodes, worn by scouts who needed to perceive threats at inhuman range. The iris of its gem dilates and contracts like an eye, and something in that motion transmits itself to the wearer — both sight and instinct are magnified."
  },
  "amulet_of_the_archmage": {
    "name": "Amulet of the Archmage", "symbol": "\"", "color": [200, 140, 255],
    "weight": 0.2, "min_level": 28, "slot": "amulet",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "INT", "amount": 3, "status": "fire_resist", "duration": -1},
    "identified": False, "unidentified_name": "hot amulet",
    "lore": "The ceremonial amulet of the Dean of the Arcane Faculty — a position first held by Thales, who wore it when demonstrating that fire could not harm a mind that understood its nature. Since then it has passed through the hands of thirty-seven archmages, each adding a layer of heat-resistant enchantment."
  },
  "ring_of_displacement": {
    "name": "Ring of Displacement", "symbol": "=", "color": [210, 210, 220],
    "weight": 0.1, "min_level": 26, "slot": "ring",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "DEX", "amount": 2, "status": "displacement", "duration": -1},
    "identified": False, "unidentified_name": "blurring ring",
    "lore": "The gem in this ring is a shard of a displacer beast's crystallized nervous tissue — the organ responsible for the beast's light-bending ability. It projects a constant false image approximately one step from the wearer's true position, causing every attack to land on air."
  },
  "amulet_of_protection": {
    "name": "Amulet of Protection", "symbol": "\"", "color": [140, 180, 220],
    "weight": 0.2, "min_level": 22, "slot": "amulet",
    "quiz_tier": 4, "equip_threshold": 5,
    "effects": {"stat": "CON", "amount": 2, "status": "magic_resist", "duration": -1},
    "identified": False, "unidentified_name": "cool amulet",
    "lore": "Blessed by the last high priest of Esagila, the great ziggurat of Babylon, this amulet projects an invisible ward that absorbs and dissipates magical energy before it can take hold. Even the most precisely aimed enchantments fray and fail against its steady resistance."
  }
}

print("Patching item files...")
patch('scroll.json',    NEW_SCROLLS)
patch('wand.json',      NEW_WANDS)
patch('lockpick.json',  NEW_LOCKPICKS)
patch('accessory.json', NEW_ACCESSORIES)
print("Done.")
