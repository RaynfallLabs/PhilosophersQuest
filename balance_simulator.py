#!/usr/bin/env python3
"""
balance_simulator.py -- Monte Carlo balance analysis for Philosopher's Quest
Usage:
  python balance_simulator.py [--runs N] [--max-level N] [--seed N]
                               [--skill low|med|high] [--hp-per-level N]
                               [--build NAME] [--compare-builds]
                               [--monster-scale F] [--boss-hp-scale F]
                               [--show-minibosses] [--show-scoring]

Full 100-level run: descent L1->100, mandatory boss fights at L20/40/60/80/100,
collect the Philosopher's Stone, then ascend L99->1 with Death in pursuit.

Model assumptions:
  - Gear: weighted random sampling from floorSpawnWeight zones
  - Quiz: Bernoulli success parameterised by (tier, WIS, skill preset)
  - Combat: one CHAIN quiz per attack turn; monster retaliates if alive
  - THAC0: monster hits if d20 >= THAC0 - player_AC  (natural 1 always misses)
  - STR scaling: str_factor = 1.0 + max(0, STR-10)*0.03 applied to player damage
  - Armor equip: gated by geography THRESHOLD quiz using item's quiz_tier
  - Accessories: history THRESHOLD quiz; beneficial effects modelled
  - Wands/scrolls: found per level, healing wands add to HP bank
  - Cooking: escalator_chain quiz; quality 0-5 maps to SP+HP restore
  - Mini-bosses: up to one per eligible level range; spawn_chance per monster.json
  - Death Pursuer: spawned on ascent from L100 with Stone; attacks every level, always hits
  - Flee: player can flee when HP < 25% max (60% success rate)
  - HP scaling: cooking-based (compound recipes + T4-T5 single cooks at Q3+)
  - Stair-rest heal: max(8, 5% max_hp) on each stair use (no auto max HP)
  - SP: 25/level exploration + 2/combat turn; SP=0 -> 1 HP starvation/turn
  - Scoring: turns*10 + max_level*1000 + kills*100 + 50000 stone bonus
  - Two-phase run: descent then ascent after defeating Abaddon
  - Quirk system: key passive/active quirks modelled (eye_storm, runic_armor,
      ramanujan, battle_trance, life_drain, metabolic, iron_ration, phoenix_rising)
  - Monster status effects: poison/burn DoT, disease stat drain, paralysis/confuse lost turns
  - Mystery system: 12 mysteries with stat/HP/item rewards, 60% spawn chance
  - Scroll effects: enchant armor, great power, healing, annihilate
  - Container loot: 1+ per level with gold and item drops
  - Special rooms: 35% chance (treasury, library, shrine)
  - Spell system: 13 spells, science chain quiz, chain-scaled effects
  - Prayer system: theology escalator chain, HP/SP restore + stat blessings

Calibration (2026-03-16, seed=42, 3000 runs):
  - generic build, skill=high: ~3.7% (baseline 3.47% + quirks add ~0.3%)
  - generic build, skill=med:  0.00%
  - generic build, skill=low:  0.00%
  - Target: 1.5-3% high-skill (original 2.9% drifted slightly due to food/item improvements)
"""

import json, math, random, argparse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / 'data'

# ---------------------------------------------------------------------------
# Tunable constants (game-balance levers)
# ---------------------------------------------------------------------------

HP_PER_LEVEL         = 0      # No auto max HP on stairs (HP comes from cooking)
HP_PER_LEVEL_REST    = 8      # Floor for stair-rest healing calculation
FLEE_THRESHOLD       = 0.25   # Attempt flee when HP < this fraction of max
FLEE_SUCCESS_RATE    = 0.60   # Probability of escaping successfully
HEAL_FIND_CHANCE     = 0.35   # Per-level chance of finding a healing scroll/wand
HEAL_MIN             = 8      # Min HP from one healing scroll
HEAL_MAX             = 18     # Max HP from one healing scroll
SP_PER_COMBAT_TURN   = 2      # SP drained per round of combat
SP_EXPLORATION_PER_LEVEL = 25 # SP drained by floor exploration

# Armor equip threshold
DEFAULT_ARMOR_QUIZ_TIER  = 1
DEFAULT_EQUIP_REQUIRED   = 2
DEFAULT_EQUIP_TOTAL      = 3

# Weapon / armor find chances per level
WEAPON_FIND_CHANCE   = 0.60
ARMOR_FIND_CHANCE    = 0.55

# Accessory system
ACC_FIND_CHANCE      = 0.30   # Chance to find an accessory per level
ACC_EQUIP_REQUIRED   = 2      # Default history quiz threshold to equip
ACC_EQUIP_TOTAL      = 3
# Fraction of accessories that give a meaningful combat benefit
ACC_REGEN_CHANCE     = 0.12   # Regen ring: +1 HP/turn in combat
ACC_LIFESAVE_CHANCE  = 0.05   # Life-save amulet: survive one killing blow
ACC_HASTE_CHANCE     = 0.08   # Hasted: extra attack per turn
ACC_INVIS_CHANCE     = 0.08   # Invisible: -30% monster hit chance

# Cooking system
HARVEST_CHANCE       = 0.30   # Per-monster-kill chance to get a cookable corpse
COOK_ATTEMPT_CHANCE  = 0.70   # Probability player tries to cook a harvested corpse
# Cooking escalator chain: p starts at base, drops 0.05 per question
COOK_ESCALATOR_DROP  = 0.05
COOK_MAX_QUALITY     = 5
# SP restore from a cooked meal (quality 1-2 = SP only; 3-5 = SP + HP)
COOKED_SP_BASE       = 50     # Average SP per quality level
COOKED_SP_PER_QUALITY = 10

# Wand system
WAND_FIND_CHANCE     = 0.20   # Per-level chance to find a wand
WAND_CHARGES_MEAN    = 4      # Average charges in a found wand
WAND_HEAL_CHANCE     = 0.15   # Fraction of found wands that are healing wands
WAND_HEAL_POWER      = '2d8'  # wand_of_healing power
WAND_EXTRA_HEAL_MIN  = 5      # wand_of_extra_healing min level to find
WAND_EXTRA_POWER     = '4d8'

# Enchantment distribution when finding a weapon
ENCHANT_DIST = [(0, 0.80), (1, 0.12), (2, 0.08)]

# Floor trap system (1-3 traps per level; player triggers ~40% of them)
TRAP_SPAWN_PER_LEVEL_MIN = 1     # Min traps spawned per level
TRAP_SPAWN_PER_LEVEL_MAX = 3     # Max traps spawned per level
TRAP_TRIGGER_CHANCE      = 0.40  # Fraction of traps the player steps on
TRAP_AVG_DAMAGE          = 8     # Average HP damage from pit/arrow/acid traps
TRAP_ALARM_CHANCE        = 0.20  # Fraction of traps that are alarm type (no direct damage)
TRAP_TELEPORT_CHANCE     = 0.20  # Fraction of traps that teleport (no direct damage)
TRAP_DAMAGE_CHANCE       = 1.0 - TRAP_ALARM_CHANCE - TRAP_TELEPORT_CHANCE  # 60% deal direct damage

# Merchant shop system (20% chance per level, player spends healing-bank gold)
MERCHANT_SPAWN_CHANCE    = 0.20  # Probability a merchant appears per floor
MERCHANT_HEAL_CHANCE     = 0.40  # If merchant present, player buys a healing potion
MERCHANT_HEAL_VALUE      = 20    # Average HP value of purchased healing potions
MERCHANT_GOLD_COST       = 30    # Average gold spent per purchase

# Enchantment scroll system (new scrolls; 15% chance to find, +1 enchant to weapon)
ENCHANT_SCROLL_FIND_CHANCE = 0.15   # Per-level chance to find scroll of enchantment
ENCHANT_SCROLL_GRAMMAR_P   = 0.70   # Chance player can read the scroll (grammar quiz, tier 3)

# Mana potion system (only relevant for mages; modelled as minor healing equivalent)
MANA_POTION_FIND_CHANCE  = 0.10   # Per-level chance to find potion of mana/brilliance
MANA_POTION_HP_EQUIV     = 5      # Effective HP equivalent (mana → spells → damage reduction)

# Potion system (1-2 potions spawn per level; fractions match actual potion.json distribution)
# 100 potions total: 10 healing (heal×4, extra×3, full×3), 51 harmful, 39 beneficial non-heal
POTION_SPAWN_MIN      = 1     # Min potions per level
POTION_SPAWN_MAX      = 2     # Max potions per level
POTION_HEAL_FRACTION  = 0.10  # Fraction that are heal-type (10/100 in potion.json)
POTION_HEAL_AVG       = 25    # Average HP from a healing potion (heal=13, extra=26, full=≈50; avg)
POTION_NEGATIVE_FRAC  = 0.51  # Fraction that are harmful (51/100 in potion.json)
POTION_IDENTIFY_CHANCE = 0.30 # Per-potion chance player identifies it before drinking (via scroll/amulet)
POTION_UNID_DRINK_CHANCE = 0.30  # Chance player tries an unidentified potion anyway
POTION_NEG_DAMAGE_MIN  = 8    # Min HP damage from a negative potion (poison, paralysis, etc.)
POTION_NEG_DAMAGE_MAX  = 25   # Max HP damage from a negative potion

# Death Pursuer (spawned when ascending from L100 with Philosopher's Stone)
DEATH_ATTACK_DICE     = '3d20+50'   # Attack per level (avg ~81.5 HP)
DEATH_ASCENT_REST_PCT = 0.04        # Stair-rest heal fraction on ascent

# ---------------------------------------------------------------------------
# NEW SYSTEMS: Status effects, mysteries, scrolls, containers, spells, prayer
# ---------------------------------------------------------------------------

# Monster status effects (applied to player during combat)
# Fraction of monsters that have status effects on their attacks
STATUS_POISON_FRAC   = 0.19   # ~69/368 monsters inflict poison
STATUS_BURN_FRAC     = 0.06   # ~23/368 monsters inflict burning
STATUS_DISEASE_FRAC  = 0.01   # ~4/368 monsters inflict disease
STATUS_CONFUSE_FRAC  = 0.21   # ~76/368 monsters inflict confused
STATUS_PARALYZE_FRAC = 0.14   # ~50/368 monsters inflict paralyzed
STATUS_EFFECT_CHANCE = 0.35   # Average effect proc chance per hit
POISON_DMG_PER_TURN  = 1      # Player poison DoT
BURN_DMG_PER_TURN    = 1      # Player burn DoT
DISEASE_STAT_LOSS_P  = 0.08   # Per-turn chance disease reduces STR or CON by 1
STATUS_AVG_DURATION  = 6      # Average turns a status effect lasts
CONFUSE_MISS_CHANCE  = 0.30   # Confused player misses 30% of attacks
PARALYZE_LOST_TURNS  = 3      # Average turns lost to paralysis per proc

# Container system
CONTAINER_GUARANTEED  = 1     # Guaranteed containers per level
CONTAINER_EXTRA_CHANCE = 0.55 # Chance for each additional container
CONTAINER_EXTRA_DECAY  = 0.45 # Multiplier for successive extra containers
CONTAINER_LOCKPICK_P   = 0.65 # Average chance of successfully picking a lock
CONTAINER_GOLD_BASE    = 20   # Base gold per container (scales with level)
CONTAINER_GOLD_LEVEL_SCALE = 5  # Additional gold per level
CONTAINER_ITEM_CHANCE  = 0.70 # Chance container holds a useful item (weapon/armor/scroll)
CONTAINER_TRAP_CHANCE  = 0.30 # Chance trapped container deals damage on failure
CONTAINER_TRAP_DMG     = 8    # Average trap damage
MIMIC_CHANCE           = 0.08 # 8% of containers are mimics

# Special rooms (35% chance per level)
SPECIAL_ROOM_CHANCE   = 0.35
# Room types: treasury(33%), library(33%), shrine(17%), monster_den(17%)
TREASURY_EXTRA_CONTAINERS = 2
TREASURY_GOLD_MULT    = 5     # level * this for treasury gold
LIBRARY_SCROLLS       = 3
LIBRARY_SPELLBOOK_CHANCE = 0.50

# Mystery system (12 mysteries, 60% spawn chance on eligible floors)
MYSTERY_SPAWN_CHANCE  = 0.60
# Mysteries: (id, floor_min, floor_max, quiz_subject, quiz_mode, tier, threshold,
#             reward_type, reward_value)
MYSTERY_TABLE = [
    # Early game
    ('crucible',  10, 22, 'philosophy', 'threshold', 1, 3, 'gold', 400),
    ('cauldron',  14, 26, 'cooking', 'escalator_chain', 2, 5, 'effects', ('searching', 'warning')),
    ('pandora',   20, 30, 'economics', 'threshold', 2, 4, 'effects_inverted', ('magic_resist', 'displacement')),
    ('sphinx',    22, 35, 'philosophy', 'escalator_threshold', 3, 4, 'stats', {'WIS': 2, 'INT': 1}),
    ('oracle',    25, 35, 'theology', 'threshold', 3, 5, 'quirk_reveal', 3),
    # Mid game
    ('solomon',   30, 42, 'history', 'threshold', 3, 6, 'stats', {'WIS': 2}),
    ('forge',     33, 45, 'math', 'escalator_threshold', 3, 4, 'stats_weapon', {'STR': 2, 'weapon_enchant': 4}),
    ('fleece',    38, 50, 'animal', 'chain', 3, 5, 'effects', ('regenerating', 'poison_resist')),
    ('mimir',     42, 55, 'philosophy', 'chain', 4, 6, 'stats', {'INT': 3}),
    ('grail',     45, 55, 'theology', 'threshold', 3, 5, 'stats_hp', {'CON': 2, 'max_hp': 30}),
    # Late game
    ('fisher',    58, 72, 'theology', 'threshold', 4, 5, 'stats_hp', {'max_hp': 30}),
    ('sisyphus',  78, 92, 'physical', 'physical', 0, 0, 'stats', {'STR': 3, 'INT': 1}),
]

# Scroll effect system (beyond basic healing/enchant weapon already modelled)
SCROLL_ENCHANT_ARMOR_FIND  = 0.08  # Per-level chance to find enchant armor scroll
SCROLL_GREAT_POWER_FIND    = 0.03  # Per-level chance (min_level=50)
SCROLL_HEAL_FIND           = 0.10  # Per-level chance (already partially covered by HEAL_FIND_CHANCE)
SCROLL_ANNIHILATE_FIND     = 0.02  # Per-level chance (min_level=30)
SCROLL_GRAMMAR_P_BASE      = 0.70  # Base read success chance

# Spell system
SPELLBOOK_FIND_CHANCE  = 0.12  # Per-level chance to find a spellbook
SPELL_LEARN_CHANCE     = 0.60  # Chance to pass grammar threshold to learn
SPELL_CAST_CHAIN_AVG   = 2.5   # Average chain score when casting (out of 5)
SPELL_CAST_SCALE       = 0.50  # Average chain_scale = avg_chain / 5
# MP pool
SPELL_MP_REGEN         = 0     # No natural MP regen
SPELL_AVG_CAST_COST    = 7     # Average MP cost across all spells

# Prayer system
PRAYER_CHANCE_PER_LEVEL = 0.07  # ~1 altar per 15 levels = 6.7% per level
PRAYER_CHAIN_AVG        = 2.0   # Average theology escalator chain (conservative)

# Bosses (freq=0 monsters placed at fixed milestone levels)
BOSS_LEVELS = {20: 'asterion_minotaur',
               40: 'medusa_gorgon',
               60: 'fafnir_dragon',
               80: 'fenrir_wolf',
               100: 'abaddon_destroyer'}

SKILL_BASE = {'low': 0.55, 'med': 0.70, 'high': 0.85}

# ---------------------------------------------------------------------------
# Secret build stat profiles (mirroring SECRET_BUILDS in main.py)
# ---------------------------------------------------------------------------

SECRET_BUILDS = {
    # Generic starting profile (no build entered)
    'generic':      {'STR':10,'CON':10,'DEX':10,'INT':10,'WIS':10,'PER':10},
    # Philosopher archetype builds
    'aletheia':     {'STR': 8,'CON':10,'DEX':10,'INT':16,'WIS':18,'PER':12},
    'sophon':       {'STR': 8,'CON': 9,'DEX':12,'INT':18,'WIS':16,'PER':11},
    'zeno':         {'STR':10,'CON':10,'DEX':10,'INT':14,'WIS':18,'PER':12},
    'hypatia':      {'STR': 8,'CON': 9,'DEX':12,'INT':17,'WIS':17,'PER':11},
    # Warrior archetype builds
    'kratos':       {'STR':18,'CON':16,'DEX':12,'INT': 8,'WIS':10,'PER': 8},
    'leonidas':     {'STR':17,'CON':15,'DEX':14,'INT': 8,'WIS': 9,'PER':11},
    'bjorn':        {'STR':18,'CON':14,'DEX':13,'INT': 8,'WIS':10,'PER':11},
    'boudicca':     {'STR':16,'CON':15,'DEX':14,'INT':10,'WIS':10,'PER':10},
    # Rogue archetype builds
    'shadow':       {'STR':10,'CON':10,'DEX':18,'INT':12,'WIS':10,'PER':18},
    'velvet':       {'STR': 9,'CON':10,'DEX':17,'INT':13,'WIS':11,'PER':18},
    'flicker':      {'STR':10,'CON': 9,'DEX':18,'INT':11,'WIS':10,'PER':17},
    'cipher':       {'STR': 9,'CON':10,'DEX':16,'INT':14,'WIS':11,'PER':18},
    # Mage archetype builds
    'merlin':       {'STR': 7,'CON': 9,'DEX':10,'INT':18,'WIS':15,'PER':12},
    'morgana':      {'STR': 7,'CON': 9,'DEX':11,'INT':18,'WIS':14,'PER':14},
    # Special builds
    'corwin':       {'STR':15,'CON':14,'DEX':15,'INT':14,'WIS':14,'PER':14},
    'fianna':       {'STR':14,'CON':13,'DEX':12,'INT':13,'WIS':14,'PER':14},
    'fluffs':       {'STR': 6,'CON':18,'DEX': 8,'INT':10,'WIS':12,'PER':18},
    'robyn':        {'STR': 9,'CON':10,'DEX':16,'INT':17,'WIS':14,'PER':14},
    'dad':          {'STR':20,'CON':20,'DEX':20,'INT':20,'WIS':20,'PER':20},
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def load_data():
    monsters    = _load(DATA / 'monsters.json')
    weapons     = _load(DATA / 'items' / 'weapon.json')
    armor       = _load(DATA / 'items' / 'armor.json')
    shields     = _load(DATA / 'items' / 'shield.json')
    food        = _load(DATA / 'items' / 'food.json')
    accessories = _load(DATA / 'items' / 'accessory.json')
    wands       = _load(DATA / 'items' / 'wand.json')
    ingredients = _load(DATA / 'items' / 'ingredient.json')
    recipes     = _load(DATA / 'items' / 'recipes.json')
    scrolls     = _load(DATA / 'items' / 'scroll.json')
    return monsters, weapons, armor, shields, food, accessories, wands, ingredients, recipes, scrolls

# Pre-compute mini-boss table from monsters.json
def _build_miniboss_table(monsters: dict) -> list:
    """Return list of (id, min_level, max_level, spawn_chance, monster_data)."""
    table = []
    for mid, m in monsters.items():
        if m.get('is_mini_boss'):
            table.append((mid,
                           m.get('min_level', 1),
                           m.get('max_level', 100),
                           m.get('spawn_chance', 0.0),
                           m))
    return table

# ---------------------------------------------------------------------------
# Dice helpers
# ---------------------------------------------------------------------------

def _parse_dice(notation: str) -> float:
    notation = str(notation).lower().replace(' ', '')
    total = 0.0
    sign  = 1
    token = ''
    for ch in notation + '+':
        if ch in '+-' and token:
            if 'd' in token:
                n, d = token.split('d')
                n = int(n) if n else 1
                total += sign * n * (int(d) + 1) / 2.0
            else:
                total += sign * int(token)
            token = ''
            sign = 1 if ch == '+' else -1
        else:
            token += ch
    return total

def avg_dice(notation: str) -> float:
    try:
        return _parse_dice(notation)
    except Exception:
        return 2.5

def roll_dice(notation: str) -> int:
    notation = str(notation).lower().replace(' ', '')
    total = 0
    sign  = 1
    token = ''
    for ch in notation + '+':
        if ch in '+-' and token:
            if 'd' in token:
                n, d = token.split('d')
                n = int(n) if n else 1
                total += sign * sum(random.randint(1, int(d)) for _ in range(n))
            else:
                total += sign * int(token)
            token = ''
            sign = 1 if ch == '+' else -1
        else:
            token += ch
    return max(1, total)

# ---------------------------------------------------------------------------
# Quiz success models
# ---------------------------------------------------------------------------

def p_correct(tier: int, wis: int, skill: str = 'med') -> float:
    """P(correct answer): base - tier_penalty + wis_bonus, clamped [0.30, 0.94]."""
    base = SKILL_BASE[skill] - (tier - 1) * 0.06 + (wis - 10) * 0.015
    return max(0.30, min(0.94, base))

def roll_chain(p: float, max_chain: int) -> int:
    """Simulate a CHAIN quiz: correct answers accumulate until wrong or cap."""
    chain = 0
    while chain < max_chain:
        if random.random() < p:
            chain += 1
        else:
            break
    return chain

def roll_escalator_chain(base_p: float, max_q: int = COOK_MAX_QUALITY,
                          drop_per_q: float = COOK_ESCALATOR_DROP) -> int:
    """
    Simulate an ESCALATOR_CHAIN quiz (cooking).
    Each correct answer reduces p by drop_per_q.
    Returns chain length (= quality score 0-5).
    """
    chain = 0
    p = base_p
    while chain < max_q:
        if random.random() < max(0.10, p):
            chain += 1
            p -= drop_per_q
        else:
            break
    return chain

def p_threshold(required: int, total_qs: int, p: float) -> float:
    """P(passing THRESHOLD quiz) = P(>= required correct out of total_qs)."""
    success = 0.0
    for k in range(required, total_qs + 1):
        binom = math.comb(total_qs, k)
        success += binom * (p ** k) * ((1 - p) ** (total_qs - k))
    return success

# ---------------------------------------------------------------------------
# Cooking model
# ---------------------------------------------------------------------------

def _cooking_hp_bonus(ingredient_min_level: int, quality: int) -> int:
    """
    HP restored by a cooked single-ingredient meal.
    Matches food_system._cooking_hp_bonus exactly.
    Tier 1 (L1-20): Q3=3  Q4=5  Q5=8
    Tier 2 (L21-40): Q3=5  Q4=8  Q5=12
    Tier 3 (L41-60): Q3=8  Q4=12 Q5=18
    Tier 4 (L61-80): Q3=12 Q4=18 Q5=25
    Tier 5 (L81-100): Q3=18 Q4=25 Q5=35
    """
    if quality < 3:
        return 0
    tier = max(1, min(5, (ingredient_min_level - 1) // 20 + 1))
    table = {1: (3, 5, 8), 2: (5, 8, 12), 3: (8, 12, 18), 4: (12, 18, 25), 5: (18, 25, 35)}
    return table[tier][quality - 3]

# Permanent +max_hp from compound recipes (tier, quality) -> bonus
_COMPOUND_MAX_HP = {
    (1, 3):  6, (1, 4): 10, (1, 5): 15,
    (2, 3): 10, (2, 4): 16, (2, 5): 22,
    (3, 3): 14, (3, 4): 21, (3, 5): 29,
    (4, 3): 17, (4, 4): 24, (4, 5): 33,
    (5, 3): 20, (5, 4): 30, (5, 5): 40,
}
# Permanent +max_hp from T4-T5 single ingredient cooks (Q3+)
_SINGLE_MAX_HP = {
    (4, 3):  2, (4, 4):  3, (4, 5):  5,
    (5, 3):  3, (5, 4):  5, (5, 5):  8,
}

# Compound recipe availability: fraction of cooked monsters that also have
# a compound recipe available (depends on recipe coverage and ingredient pairing)
COMPOUND_RECIPE_CHANCE = 0.70  # ~70% of cooked ingredients also yield a compound recipe
                               # (assumes 90%+ recipe coverage + multi-recipe ingredients)

def simulate_cooking(player_wis: int, skill: str, level: int) -> tuple:
    """
    Simulate one cooking attempt (escalator_chain).
    Returns (sp_restored, hp_restored, quality, max_hp_gained).
    Max HP bonus tier is based on dungeon floor (not ingredient min_level),
    since most ingredients are T1 but deep cooking should yield higher bonuses.
    """
    floor_tier = max(1, min(5, (level - 1) // 20 + 1))
    base_p = p_correct(floor_tier, player_wis, skill)
    quality = roll_escalator_chain(base_p)
    sp = max(0, COOKED_SP_BASE + quality * COOKED_SP_PER_QUALITY)
    hp = _cooking_hp_bonus(max(1, level), quality)
    max_hp_gain = 0
    # Single ingredient max HP (T4-T5 floor tier, Q3+)
    max_hp_gain += _SINGLE_MAX_HP.get((floor_tier, quality), 0)
    # Compound recipe chance
    if quality >= 3 and random.random() < COMPOUND_RECIPE_CHANCE:
        max_hp_gain += _COMPOUND_MAX_HP.get((floor_tier, quality), 0)
    return sp, hp, quality, max_hp_gain

# ---------------------------------------------------------------------------
# Quirk unlock checker
# ---------------------------------------------------------------------------

def _check_quirk_unlocks(player: 'SimPlayer', floor_was_clean: bool) -> list:
    """
    Check all quirk unlock conditions and apply bonuses when first triggered.
    Returns list of newly unlocked quirk IDs (for reporting).
    Call once per level AFTER combat, with floor_was_clean=True if player
    took no HP damage this level.
    """
    newly = []

    # --- Clean-floor streak tracking ---
    if floor_was_clean:
        player.clean_floors += 1
    else:
        player.clean_floors = 0
    player.floors_explored += 1

    # eye_storm: 7 consecutive clean floors → +3 max HP
    if 'eye_storm' not in player.quirk_unlocked and player.clean_floors >= 7:
        player.quirk_unlocked.add('eye_storm')
        player.max_hp += 3
        player.hp = min(player.hp + 3, player.max_hp)
        newly.append('eye_storm')

    # runic_armor: 200 hits taken → +2 AC
    # (game threshold 50 hits; sim turns ≈ 4x less granular → scale up)
    if 'runic_armor' not in player.quirk_unlocked and player.hits_taken >= 200:
        player.quirk_unlocked.add('runic_armor')
        player.armor_ac += 2
        newly.append('runic_armor')

    # temporal_shield: 500 hits taken → +1 more AC
    if 'temporal_shield' not in player.quirk_unlocked and player.hits_taken >= 500:
        player.quirk_unlocked.add('temporal_shield')
        player.armor_ac += 1
        newly.append('temporal_shield')

    # ramanujan: 3000 correct → max HP +12 (direct bonus; sim counts all subjects so
    # threshold calibrated to unlock only in very deep/successful runs)
    if 'ramanujan' not in player.quirk_unlocked and player.quests_correct >= 3000:
        player.quirk_unlocked.add('ramanujan')
        player.max_hp += 12
        player.hp = min(player.hp + 12, player.max_hp)
        newly.append('ramanujan')

    # battle_trance: 600 kills → max HP +8 (direct combat survivability bonus)
    if 'battle_trance' not in player.quirk_unlocked and player.kills >= 600:
        player.quirk_unlocked.add('battle_trance')
        player.max_hp += 8
        player.hp = min(player.hp + 8, player.max_hp)
        newly.append('battle_trance')

    # life_drain: 800 kills → 2 uses of +20 HP steal mid-combat
    if 'life_drain' not in player.quirk_unlocked and player.kills >= 800:
        player.quirk_unlocked.add('life_drain')
        player.life_drain_uses = 2
        newly.append('life_drain')

    # metabolic: ~5000 simulator turns → 2x restore 100 SP (reduced from 3 to limit impact)
    if 'metabolic' not in player.quirk_unlocked and player.turns >= 5000:
        player.quirk_unlocked.add('metabolic')
        player.metabolic_uses = 2
        newly.append('metabolic')

    # iron_ration: ~8000 simulator turns → max SP +50 (late-run reward)
    if 'iron_ration' not in player.quirk_unlocked and player.turns >= 8000:
        player.quirk_unlocked.add('iron_ration')
        player.max_sp += 50
        newly.append('iron_ration')

    # phoenix_rising: 10 near-death hits (HP ≤ 5% when hit) → 10 auto-revives
    if 'phoenix_rising' not in player.quirk_unlocked and player.near_death_hits >= 10:
        player.quirk_unlocked.add('phoenix_rising')
        player.phoenix_uses = 10
        newly.append('phoenix_rising')

    return newly


# ---------------------------------------------------------------------------
# Gear helpers -- weighted random sampling
# ---------------------------------------------------------------------------

def _spawn_weight(spawn_weights: dict, level: int) -> int:
    for key, w in spawn_weights.items():
        parts = str(key).split('-')
        if len(parts) == 2:
            try:
                if int(parts[0]) <= level <= int(parts[1]):
                    return int(w)
            except ValueError:
                pass
    return 0

def weighted_weapon_sample(weapons: dict, level: int) -> 'dict | None':
    pool    = []
    weights = []
    for w in weapons.values():
        sw = w.get('floorSpawnWeight') or {}
        if sw:
            wt = _spawn_weight(sw, level)
        else:
            ml = w.get('min_level', 1)
            if ml > level:
                continue
            wt = 10
        if wt > 0:
            pool.append(w)
            weights.append(wt)
    if not pool:
        return None
    return random.choices(pool, weights=weights, k=1)[0]

def weighted_armor_sample(armor: dict, level: int, slot: str) -> 'dict | None':
    pool    = []
    weights = []
    for a in armor.values():
        if a.get('slot') != slot:
            continue
        ml = a.get('min_level', 1)
        if ml > level:
            continue
        age = level - ml
        wt  = max(2, 100 - age)
        pool.append(a)
        weights.append(wt)
    if not pool:
        return None
    return random.choices(pool, weights=weights, k=1)[0]

def weighted_shield_sample(shields: dict, level: int) -> 'dict | None':
    pool    = []
    weights = []
    for s in shields.values():
        ml = s.get('min_level', 1)
        if ml > level:
            continue
        age = level - ml
        wt  = max(2, 100 - age)
        pool.append(s)
        weights.append(wt)
    if not pool:
        return None
    return random.choices(pool, weights=weights, k=1)[0]

def weighted_accessory_sample(accessories: dict, level: int) -> 'dict | None':
    pool    = []
    weights = []
    for a in accessories.values():
        sw = a.get('floorSpawnWeight') or {}
        if sw:
            wt = _spawn_weight(sw, level)
        else:
            ml = a.get('min_level', 1)
            wt = 10 if ml <= level else 0
        if wt > 0:
            pool.append(a)
            weights.append(wt)
    if not pool:
        return None
    return random.choices(pool, weights=weights, k=1)[0]

def best_armor_ac_at_level(armor: dict, shields: dict, level: int) -> int:
    """Theoretical best AC sum (for gear ceiling display only)."""
    best_per_slot: dict[str, int] = {}
    for a in armor.values():
        if a.get('min_level', 1) > level:
            continue
        slot = a.get('slot', 'body')
        ac   = a.get('ac_bonus', 0)
        if ac > best_per_slot.get(slot, 0):
            best_per_slot[slot] = ac
    shield_ac = max((s.get('ac_bonus', 0) for s in shields.values()
                     if s.get('min_level', 1) <= level), default=0)
    return sum(best_per_slot.values()) + shield_ac

def best_weapon_at_level(weapons: dict, level: int) -> 'dict | None':
    """Theoretical best weapon (for gear ceiling display only)."""
    best = None
    for w in weapons.values():
        sw = w.get('floorSpawnWeight') or {}
        if sw and _spawn_weight(sw, level) == 0:
            continue
        if w.get('min_level', 1) > level:
            continue
        if best is None or w.get('baseDamage', 0) > best.get('baseDamage', 0):
            best = w
    return best

# ---------------------------------------------------------------------------
# Player model
# ---------------------------------------------------------------------------

ARMOR_SLOTS = ['head', 'body', 'arms', 'hands', 'legs', 'feet', 'cloak', 'shirt']

class SimPlayer:
    def __init__(self, skill: str = 'med', hp_per_level: int = HP_PER_LEVEL,
                 build: dict = None):
        self.skill        = skill
        self.hp_per_level = hp_per_level

        # Apply build stats (or defaults)
        b = build or {}
        self.STR = b.get('STR', 10)
        self.CON = b.get('CON', 10)
        self.DEX = b.get('DEX', 10)
        self.INT = b.get('INT', 10)
        self.WIS = b.get('WIS', 10)
        self.PER = b.get('PER', 10)

        self.base_max_hp   = 20 + self.CON
        self.max_hp        = self.base_max_hp
        self.hp            = self.max_hp
        self.max_sp        = 200 + self.CON
        self.sp            = self.max_sp

        # Descending AC: lower = better
        self._dex_ac       = (self.DEX - 10) // 2
        self.armor_ac      = 0
        self.equipped_armor_per_slot: dict[str, int] = {}
        self.shield_ac     = 0

        # Healing bank: HP available from carried healing items
        self.healing_bank  = 0

        # Starting weapon: iron_dagger (bow for Robyn)
        self.weapon_base_dmg  = 3
        self.weapon_enchant   = 0
        self.weapon_mults     = [0.3, 0.6, 1.0, 1.4, 1.8, 2.2, 2.5]
        self.weapon_max_chain = 7
        self.weapon_quiz_tier = 1
        self.weapon_dmg_types = ['pierce']
        self.weapon_name      = 'iron_dagger'

        # Accessory passive effects
        self.has_regen      = False   # +1 HP/turn during combat
        self.has_life_save  = False   # survive one killing blow
        self.life_save_used = False
        self.has_haste      = False   # extra attack per combat turn
        self.has_invis      = False   # monster hit chance -30%

        # Scoring
        self.kills          = 0
        self.gold           = 0
        self.turns          = 0
        self.quests_correct = 0
        self.quests_wrong   = 0

        # Dad immortality flag
        self.immortal       = b.get('_immortal', False)

        # Passive HP regen: 1 HP every N turns (matches _tick_hp_regen in main.py)
        self._regen_turn    = 0    # tracks fractional turns for regen tick
        self.passive_regen_interval = max(10, 20 - max(0, self.CON - 12))

        # Status effect tracking (simplified: just turn counters)
        self.status_poison_turns   = 0
        self.status_burn_turns     = 0
        self.status_disease_turns  = 0
        self.status_confused_turns = 0
        self.status_paralyzed_turns = 0
        self.has_poison_resist     = False
        self.has_fire_resist       = False

        # Spell system
        self.max_mp    = 10 + self.INT
        self.mp        = self.max_mp
        self.known_spells = 0  # number of spells learned (simplified)
        self.has_shield_spell = False
        self.has_heal_spell   = False

        # Mystery tracking
        self.mysteries_solved = set()

        # Prayer cooldown
        self.prayer_cooldown = 0

        # Container tracking
        self.lockpick_charges = 5  # Start with basic lockpick

        # Quirk system tracking
        self.quirk_unlocked    = set()   # set of unlocked quirk IDs
        self.hits_taken        = 0       # monster attacks landed (for runic_armor)
        self.near_death_hits   = 0       # hits taken while HP <= 5% max (phoenix_rising)
        self.clean_floors      = 0       # consecutive floors taking no HP damage
        self.floors_explored   = 0       # total floors completed
        # Active power charges (unlocked mid-run)
        self.metabolic_uses    = 0       # SP restore +100 (3 uses, unlocks ~floor 40)
        self.phoenix_uses      = 0       # auto-revive to full HP (10 uses, hard unlock)
        self.life_drain_uses   = 0       # steal +25 HP mid-combat (3 uses)

    @property
    def ac(self) -> int:
        base = 10 - self._dex_ac - self.armor_ac
        if self.has_invis:
            base -= 2  # invisibility grants AC bonus
        return base

    def descend(self):
        """Called on each stair: stair-rest heal only (no auto max HP)."""
        rest_heal = max(HP_PER_LEVEL_REST, int(self.max_hp * 0.05))
        self.hp   = min(self.hp + rest_heal, self.max_hp)
        # Regen: also tick during movement between levels
        if self.has_regen:
            self.hp = min(self.hp + 5, self.max_hp)  # ~5 ticks between stairs

    def upgrade_weapon(self, w: dict, enchant: int = 0):
        new_base = w.get('baseDamage', 0) + enchant
        if new_base > self.weapon_base_dmg + self.weapon_enchant:
            self.weapon_base_dmg  = w.get('baseDamage', 0)
            self.weapon_enchant   = enchant
            self.weapon_mults     = w.get('chainMultipliers', self.weapon_mults)
            self.weapon_max_chain = w.get('maxChainLength', len(self.weapon_mults))
            self.weapon_quiz_tier = w.get('mathTier', w.get('quiz_tier', 1))
            self.weapon_dmg_types = w.get('damageTypes', ['slash'])
            self.weapon_name      = w.get('name', '?')

    def upgrade_armor_slot(self, slot: str, ac_bonus: int):
        if ac_bonus > self.equipped_armor_per_slot.get(slot, 0):
            self.equipped_armor_per_slot[slot] = ac_bonus
            self.armor_ac = sum(self.equipped_armor_per_slot.values()) + self.shield_ac

    def upgrade_shield(self, ac_bonus: int):
        if ac_bonus > self.shield_ac:
            self.shield_ac = ac_bonus
            self.armor_ac  = sum(self.equipped_armor_per_slot.values()) + self.shield_ac

    def drain_sp(self, amount: int):
        self.sp = max(0, self.sp - amount)

    def restore_sp(self, amount: int):
        self.sp = min(self.max_sp, self.sp + amount)

    def use_healing(self, max_hp_fraction: float = 1.0) -> int:
        if self.healing_bank <= 0:
            return 0
        target = int(self.max_hp * max_hp_fraction)
        if self.hp >= target:
            return 0
        heal = min(self.healing_bank, target - self.hp)
        self.hp           += heal
        self.healing_bank -= heal
        return heal

    def take_damage(self, amount: int) -> bool:
        """Apply damage; return True if killed (HP <= 0)."""
        if self.immortal:
            return False
        self.hp -= amount
        if self.hp <= 0 and self.has_life_save and not self.life_save_used:
            self.hp = 1
            self.life_save_used = True
        return self.hp <= 0

    def is_starving(self) -> bool:
        return self.sp == 0

    def tick_passive_regen(self, n_turns: int = 1):
        """Accumulate passive regen ticks; heal 1 HP per interval turns if below max."""
        if self.hp >= self.max_hp:
            self._regen_turn = 0
            return
        self._regen_turn += n_turns
        healed = self._regen_turn // self.passive_regen_interval
        if healed > 0:
            self._regen_turn %= self.passive_regen_interval
            self.hp = min(self.hp + healed, self.max_hp)

# ---------------------------------------------------------------------------
# Damage type resistance
# ---------------------------------------------------------------------------

def dtype_multiplier(weapon_types: list, monster: dict) -> float:
    resistances = set(monster.get('resistances', []))
    weaknesses  = set(monster.get('weaknesses',  []))
    best = 1.0
    for dt in weapon_types:
        if dt in weaknesses:
            best = max(best, 1.5)
        elif dt in resistances and best <= 1.0:
            best = 0.5
    return best

# ---------------------------------------------------------------------------
# Single combat
# ---------------------------------------------------------------------------

def simulate_combat(player: SimPlayer, monster: dict,
                    allow_flee: bool = True,
                    pre_fight_heal: bool = True,
                    pursuer: bool = False) -> dict:
    """
    One player-vs-monster fight.
    pursuer=True: unkillable Death pursuer (2d20+60, THAC0=-20, no flee).
    Returns dict with: won, fled, hp_lost, turns, chains, starv_dmg
    """
    if pre_fight_heal:
        player.use_healing(max_hp_fraction=0.40)

    m_hp   = roll_dice(str(monster.get('hp', '1d6')))
    p_cor  = p_correct(player.weapon_quiz_tier, player.WIS, player.skill)
    dmult  = dtype_multiplier(player.weapon_dmg_types, monster)

    thac0       = monster.get('thac0', 20)
    roll_needed = max(2, thac0 - player.ac)
    hit_chance  = max(0.0, min(1.0, (21 - roll_needed) / 20.0))
    # Invisibility: reduce monster hit chance by 30%
    if player.has_invis:
        hit_chance *= 0.70

    chains           = []
    player_hp_before = player.hp
    turns            = 0
    starvation_dmg   = 0
    fled             = False

    while m_hp > 0 and player.hp > 0:
        turns += 1
        player.turns += 1
        player.drain_sp(SP_PER_COMBAT_TURN)

        # Starvation: 1 HP/turn at SP=0
        if player.is_starving():
            if player.take_damage(1):
                starvation_dmg += 1
                break
            starvation_dmg += 1

        # Regen ring: +1 HP/turn
        if player.has_regen:
            player.hp = min(player.hp + 1, player.max_hp)

        # Passive HP regen (1 HP every N turns regardless of equipment)
        player.tick_passive_regen(1)

        # Flee check when HP critically low (not for pursuer or bosses)
        if allow_flee and not pursuer and player.hp < player.max_hp * FLEE_THRESHOLD:
            if random.random() < FLEE_SUCCESS_RATE:
                fled = True
                break

        # --- Player attacks (with STR scaling) ---
        str_factor = 1.0 + max(0, player.STR - 10) * 0.03
        n_attacks = 2 if player.has_haste else 1
        for _ in range(n_attacks):
            # Confused: 30% chance to miss entirely
            if player.status_confused_turns > 0 and random.random() < CONFUSE_MISS_CHANCE:
                chains.append(0)
                continue
            chain = roll_chain(p_cor, player.weapon_max_chain)
            chains.append(chain)
            player.quests_correct += chain
            if chain > 0:
                idx  = min(chain - 1, len(player.weapon_mults) - 1)
                mult = player.weapon_mults[idx]
                raw  = player.weapon_base_dmg + player.weapon_enchant
                dmg  = max(1, int(raw * mult * dmult * str_factor))
                m_hp -= dmg
            if m_hp <= 0:
                break

        if m_hp <= 0:
            break

        # --- Monster retaliates ---
        if pursuer:
            # Death always hits with 2d20+60
            dmg = roll_dice('2d20+60')
            player.hits_taken += 1
            if player.hp <= player.max_hp * 0.05:
                player.near_death_hits += 1
                if player.phoenix_uses > 0:
                    player.hp = player.max_hp
                    player.phoenix_uses -= 1
                    continue
            if player.take_damage(dmg):
                break
        else:
            if random.random() < hit_chance:
                attacks = monster.get('attacks', [{'damage': '1d4'}])
                total_mdmg = 0
                for atk in attacks:
                    total_mdmg += roll_dice(str(atk.get('damage', '1d4')))
                player.hits_taken += 1
                if player.hp <= player.max_hp * 0.05:
                    player.near_death_hits += 1
                    if player.phoenix_uses > 0:
                        player.hp = player.max_hp
                        player.phoenix_uses -= 1
                        continue
                # Use life_drain when HP critically low (< 30%)
                if player.life_drain_uses > 0 and player.hp < player.max_hp * 0.30:
                    player.hp = min(player.max_hp, player.hp + 20)
                    player.life_drain_uses -= 1
                if player.take_damage(total_mdmg):
                    break

                # --- Status effect application from monster attacks ---
                if random.random() < STATUS_EFFECT_CHANCE:
                    # Determine which effect based on monster type distribution
                    eff_roll = random.random()
                    total_frac = (STATUS_POISON_FRAC + STATUS_BURN_FRAC +
                                  STATUS_DISEASE_FRAC + STATUS_CONFUSE_FRAC +
                                  STATUS_PARALYZE_FRAC)
                    if eff_roll < STATUS_POISON_FRAC / total_frac:
                        if not player.has_poison_resist:
                            player.status_poison_turns = max(player.status_poison_turns,
                                                            STATUS_AVG_DURATION)
                    elif eff_roll < (STATUS_POISON_FRAC + STATUS_BURN_FRAC) / total_frac:
                        if not player.has_fire_resist:
                            player.status_burn_turns = max(player.status_burn_turns,
                                                          STATUS_AVG_DURATION)
                    elif eff_roll < (STATUS_POISON_FRAC + STATUS_BURN_FRAC +
                                     STATUS_DISEASE_FRAC) / total_frac:
                        if not player.has_poison_resist:
                            player.status_disease_turns = max(player.status_disease_turns,
                                                             STATUS_AVG_DURATION)
                    elif eff_roll < (STATUS_POISON_FRAC + STATUS_BURN_FRAC +
                                     STATUS_DISEASE_FRAC + STATUS_CONFUSE_FRAC) / total_frac:
                        player.status_confused_turns = max(player.status_confused_turns,
                                                          STATUS_AVG_DURATION)
                    else:
                        player.status_paralyzed_turns = max(player.status_paralyzed_turns,
                                                           PARALYZE_LOST_TURNS)

        # --- Status effect ticks (DoT applied per combat turn) ---
        if player.status_poison_turns > 0:
            player.take_damage(POISON_DMG_PER_TURN)
            player.status_poison_turns -= 1
            if player.hp <= 0:
                break
        if player.status_burn_turns > 0:
            player.take_damage(BURN_DMG_PER_TURN)
            player.status_burn_turns -= 1
            if player.hp <= 0:
                break
        if player.status_disease_turns > 0:
            if random.random() < DISEASE_STAT_LOSS_P:
                stat = random.choice(['STR', 'CON'])
                if stat == 'STR' and player.STR > 3:
                    player.STR -= 1
                elif stat == 'CON' and player.CON > 3:
                    player.CON -= 1
            player.status_disease_turns -= 1
        if player.status_confused_turns > 0:
            player.status_confused_turns -= 1
        if player.status_paralyzed_turns > 0:
            player.status_paralyzed_turns -= 1
            continue  # Skip this turn entirely (paralyzed)

    won = (m_hp <= 0 and not fled and not pursuer)
    if won:
        player.kills += 1
        gold_range = monster.get('treasure', {}).get('gold', [0, 5])
        if isinstance(gold_range, list) and len(gold_range) == 2:
            player.gold += random.randint(int(gold_range[0]), int(gold_range[1]))

    return {
        'won':       won,
        'fled':      fled,
        'hp_lost':   max(0, player_hp_before - player.hp),
        'turns':     turns,
        'chains':    chains,
        'starv_dmg': starvation_dmg,
    }

# ---------------------------------------------------------------------------
# Mystery, prayer, and spell helpers
# ---------------------------------------------------------------------------

def _attempt_mystery(player: SimPlayer, subject: str, mode: str,
                     tier: int, threshold: int) -> bool:
    """Simulate a mystery quiz attempt. Returns True if solved."""
    if mode == 'physical':
        # Sisyphus: STR-based physical challenge, ~50% success
        return player.STR >= 14 or random.random() < 0.40

    p = p_correct(tier, player.WIS, player.skill)

    if mode == 'threshold':
        total_qs = max(threshold, int(threshold * 1.4))
        return random.random() < p_threshold(threshold, total_qs, p)
    elif mode == 'escalator_threshold':
        # Escalator: questions get harder, need threshold correct
        chain = roll_escalator_chain(p, max_q=threshold + 2, drop_per_q=0.06)
        return chain >= threshold
    elif mode in ('chain', 'escalator_chain'):
        chain = roll_escalator_chain(p, max_q=threshold + 2, drop_per_q=0.05)
        return chain >= threshold
    return False


def _apply_mystery_reward(player: SimPlayer, rtype: str, rval) -> None:
    """Apply mystery rewards to player."""
    if rtype == 'gold':
        player.gold += rval
    elif rtype == 'stats':
        for stat, bonus in rval.items():
            if stat == 'WIS':
                player.WIS += bonus
            elif stat == 'INT':
                player.INT += bonus
                player.max_mp = 10 + player.INT
            elif stat == 'STR':
                player.STR += bonus
            elif stat == 'CON':
                player.CON += bonus
                player.max_hp += bonus
                player.hp = min(player.hp + bonus, player.max_hp)
    elif rtype == 'stats_hp':
        for stat, bonus in rval.items():
            if stat == 'CON':
                player.CON += bonus
                player.max_hp += bonus
                player.hp = min(player.hp + bonus, player.max_hp)
            elif stat == 'max_hp':
                player.max_hp += bonus
                player.hp = min(player.hp + bonus, player.max_hp)
    elif rtype == 'stats_weapon':
        for stat, bonus in rval.items():
            if stat == 'STR':
                player.STR += bonus
            elif stat == 'weapon_enchant':
                player.weapon_enchant += bonus
    elif rtype == 'effects':
        for eff in rval:
            if eff == 'regenerating':
                player.has_regen = True
            elif eff == 'poison_resist':
                player.has_poison_resist = True
            elif eff == 'searching' or eff == 'warning':
                pass  # Map awareness, minor benefit
    elif rtype == 'effects_inverted':
        # Pandora: failing grants the reward (inverted quiz)
        for eff in rval:
            if eff == 'magic_resist':
                pass  # Minor damage reduction
            elif eff == 'displacement':
                pass  # 30% dodge, minor


def _simulate_prayer(player: SimPlayer, level: int) -> None:
    """Simulate a prayer at an altar. Theology escalator chain."""
    floor_tier = max(1, min(5, (level - 1) // 20 + 1))
    p = p_correct(floor_tier, player.WIS, player.skill)
    chain = roll_escalator_chain(p, max_q=8, drop_per_q=0.06)

    if chain <= 0:
        return
    elif chain == 1:
        # Minor comfort: +5% SP or remove minor status
        player.restore_sp(int(player.max_sp * 0.05))
        player.status_confused_turns = 0
        player.status_poison_turns = 0
    elif chain == 2:
        # Major cleansing
        player.restore_sp(int(player.max_sp * 0.10))
        player.status_disease_turns = 0
        player.status_paralyzed_turns = 0
    elif chain == 3:
        # Full purification
        player.restore_sp(int(player.max_sp * 0.20))
        player.hp = min(player.hp + int(player.max_hp * 0.20), player.max_hp)
        player.status_poison_turns = 0
        player.status_burn_turns = 0
        player.status_disease_turns = 0
        player.status_confused_turns = 0
        player.status_paralyzed_turns = 0
    elif chain == 4:
        player.restore_sp(int(player.max_sp * 0.30))
    elif chain == 5:
        player.restore_sp(int(player.max_sp * 0.60))
        player.hp = min(player.hp + int(player.max_hp * 0.20), player.max_hp)
    elif chain == 6:
        player.sp = player.max_sp
        player.hp = min(player.hp + int(player.max_hp * 0.50), player.max_hp)
    elif chain >= 7:
        player.sp = player.max_sp
        player.hp = player.max_hp
        if chain >= 8 and player.WIS < 23:  # WIS+1 cap at +3
            player.WIS += 1


# ---------------------------------------------------------------------------
# Single level simulation
# ---------------------------------------------------------------------------

def _roll_enchant() -> int:
    r = random.random()
    cumulative = 0.0
    for val, prob in ENCHANT_DIST:
        cumulative += prob
        if r < cumulative:
            return val
    return 0

def simulate_level(player: SimPlayer, level: int,
                   monsters: dict, weapons: dict,
                   armor: dict, shields: dict,
                   food: dict, accessories: dict,
                   wands: dict,
                   miniboss_table: list,
                   placed_minibosses: set,
                   is_boss_level: bool = False,
                   boss_id: str = '',
                   monster_scale: float = 1.0,
                   boss_hp_scale: float = 1.0,
                   death_pursues: bool = False) -> dict:
    """
    Simulate one dungeon level.
    Order: gear upgrades -> accessories -> wands -> food/healing -> exploration drain
           -> mini-boss (if eligible) -> regular combat -> cooking
           -> Death Pursuer attack (if ascent)
    """
    EXPLORATION_TURNS = 20  # Approximate exploration turns per level
    player.turns += EXPLORATION_TURNS
    player.tick_passive_regen(EXPLORATION_TURNS)  # Passive regen during exploration

    # --- Weapon upgrade ---
    if random.random() < WEAPON_FIND_CHANCE:
        w = weighted_weapon_sample(weapons, level)
        if w:
            player.upgrade_weapon(w, enchant=_roll_enchant())

    # --- Armor upgrades (per slot, gated by geography quiz) ---
    for slot in ARMOR_SLOTS:
        if random.random() < ARMOR_FIND_CHANCE:
            a = weighted_armor_sample(armor, level, slot)
            if a is None:
                continue
            quiz_tier  = a.get('quiz_tier', DEFAULT_ARMOR_QUIZ_TIER)
            required   = a.get('equip_threshold', DEFAULT_EQUIP_REQUIRED)
            total_qs   = max(required, int(required * 1.5))
            slot_geo_p = p_correct(quiz_tier, player.WIS, player.skill)
            if random.random() < p_threshold(required, total_qs, slot_geo_p):
                player.upgrade_armor_slot(slot, a.get('ac_bonus', 0))

    # Shield upgrade
    if random.random() < ARMOR_FIND_CHANCE:
        s = weighted_shield_sample(shields, level)
        if s:
            geo_p_s = p_correct(DEFAULT_ARMOR_QUIZ_TIER, player.WIS, player.skill)
            if random.random() < p_threshold(2, 3, geo_p_s):
                player.upgrade_shield(s.get('ac_bonus', 0))

    # --- Accessory find (gated by history threshold quiz) ---
    if random.random() < ACC_FIND_CHANCE:
        acc = weighted_accessory_sample(accessories, level)
        if acc:
            hist_tier = acc.get('quiz_tier', 1)
            required  = acc.get('equip_threshold', ACC_EQUIP_REQUIRED)
            total_qs  = max(required, int(required * 1.5))
            hist_p    = p_correct(hist_tier, player.WIS, player.skill)
            if random.random() < p_threshold(required, total_qs, hist_p):
                # Determine effect category
                effect = acc.get('effects', {}).get('status', '')
                if effect in ('regenerating', 'regeneration') and not player.has_regen:
                    player.has_regen = True
                elif effect == 'life_save' and not player.has_life_save:
                    player.has_life_save = True
                elif effect == 'hasted' and not player.has_haste:
                    player.has_haste = True
                elif effect == 'invisible' and not player.has_invis:
                    player.has_invis = True
                # Warning/telepathy/etc. give map awareness — modelled as -10% surprise penalty removed
                # (no direct numeric impact in the model, but acknowledged)

    # During ascent (Death pursues), player is fleeing — no time to loot/shop.
    # Item find rates are reduced by 75%; no merchant visits; no enchantment.
    _item_scale = 0.25 if death_pursues else 1.0

    # --- Wand find ---
    if random.random() < WAND_FIND_CHANCE * _item_scale:
        # Determine if it's a healing wand
        if random.random() < WAND_HEAL_CHANCE:
            # Healing wand: 2d8 per charge, ~4 charges
            charges = random.randint(3, 5)
            power = WAND_EXTRA_POWER if level >= WAND_EXTRA_HEAL_MIN else WAND_HEAL_POWER
            # Science quiz to zap: tier 1-2, threshold 2-3
            sci_p = p_correct(1, player.WIS, player.skill)
            if random.random() < p_threshold(2, 3, sci_p):
                for _ in range(charges):
                    player.healing_bank += roll_dice(power)

    # --- Food & healing items ---
    spawnable_food = [f for f in food.values() if f.get('min_level', 1) <= level]
    if spawnable_food and random.random() < _item_scale:
        n_food = random.randint(1, 3)
        for _ in range(n_food):
            f = random.choice(spawnable_food)
            if player.sp < player.max_sp * 0.80:
                player.restore_sp(f.get('sp_restore', 20))
            hp_r = f.get('hp_restore', 0)
            if hp_r > 0:
                player.healing_bank += hp_r

    # Healing scrolls / wands (lump)
    if random.random() < HEAL_FIND_CHANCE * _item_scale:
        player.healing_bank += random.randint(HEAL_MIN, HEAL_MAX)

    # Potions (1-2 per level, mix of beneficial and harmful)
    n_potions = random.randint(POTION_SPAWN_MIN, POTION_SPAWN_MAX)
    n_potions = max(0, int(n_potions * _item_scale + 0.5))
    for _ in range(n_potions):
        r = random.random()
        if r < POTION_HEAL_FRACTION:
            # Healing potion — always worth quaffing; player uses it if identified
            if random.random() < POTION_IDENTIFY_CHANCE or random.random() < POTION_UNID_DRINK_CHANCE:
                player.healing_bank += POTION_HEAL_AVG
        elif r < POTION_HEAL_FRACTION + POTION_NEGATIVE_FRAC:
            # Harmful potion — player drinks only if unidentified and guesses wrong
            if random.random() > POTION_IDENTIFY_CHANCE:  # not identified
                if random.random() < POTION_UNID_DRINK_CHANCE:
                    dmg = random.randint(POTION_NEG_DAMAGE_MIN, POTION_NEG_DAMAGE_MAX)
                    player.take_damage(dmg)
        # else: neutral/buff potion (levitation, haste, etc.) — minor benefit, skip numeric model

    # --- Floor traps ---
    n_traps = random.randint(TRAP_SPAWN_PER_LEVEL_MIN, TRAP_SPAWN_PER_LEVEL_MAX)
    for _ in range(n_traps):
        if random.random() < TRAP_TRIGGER_CHANCE:
            trap_roll = random.random()
            if trap_roll >= TRAP_ALARM_CHANCE + TRAP_TELEPORT_CHANCE:
                # Damaging trap
                trap_dmg = random.randint(max(1, TRAP_AVG_DAMAGE - 5), TRAP_AVG_DAMAGE + 5)
                # High-level traps scale up slightly
                trap_dmg = int(trap_dmg * (1 + level / 150))
                player.take_damage(trap_dmg)
            # Alarm and teleport traps: no direct damage (alarm summons monsters already in model)

    # --- Merchant shop (not available during Death chase) ---
    if not death_pursues and random.random() < MERCHANT_SPAWN_CHANCE:
        if random.random() < MERCHANT_HEAL_CHANCE and player.gold >= MERCHANT_GOLD_COST:
            player.gold -= MERCHANT_GOLD_COST
            player.healing_bank += MERCHANT_HEAL_VALUE

    # --- Mana potions (benefit modelled as small healing-bank boost) ---
    if random.random() < MANA_POTION_FIND_CHANCE * _item_scale:
        player.healing_bank += MANA_POTION_HP_EQUIV

    # --- Enchantment scrolls (boost weapon enchant by 1) ---
    if not death_pursues and random.random() < ENCHANT_SCROLL_FIND_CHANCE:
        gram_p = p_correct(3, player.WIS, player.skill)
        if random.random() < gram_p * ENCHANT_SCROLL_GRAMMAR_P:
            player.weapon_enchant = getattr(player, 'weapon_enchant', 0) + 1

    # --- Scroll of Enchant Armor (+1 AC) ---
    if not death_pursues and random.random() < SCROLL_ENCHANT_ARMOR_FIND * _item_scale:
        gram_p = p_correct(3, player.WIS, player.skill)
        if random.random() < gram_p * SCROLL_GRAMMAR_P_BASE:
            if player.armor_ac > 0:  # must have armor equipped
                player.armor_ac += 1

    # --- Scroll of Great Power (+1 all stats, min_level=50) ---
    if not death_pursues and level >= 50 and random.random() < SCROLL_GREAT_POWER_FIND * _item_scale:
        gram_p = p_correct(5, player.WIS, player.skill)
        if random.random() < gram_p * SCROLL_GRAMMAR_P_BASE:
            player.STR += 1
            player.CON += 1
            player.DEX += 1
            player.INT += 1
            player.WIS += 1
            player.PER += 1
            # CON bonus: +1 max HP
            player.max_hp += 1
            player.hp = min(player.hp + 1, player.max_hp)

    # --- Scroll of Healing (3d6 HP, stacks with existing heal find) ---
    if random.random() < SCROLL_HEAL_FIND * _item_scale:
        gram_p = p_correct(1, player.WIS, player.skill)
        if random.random() < gram_p * SCROLL_GRAMMAR_P_BASE:
            player.healing_bank += roll_dice('3d6')

    # --- Scroll of Annihilate (kills visible monsters, min_level=30) ---
    # Modelled as: saves ~1 combat encounter worth of HP damage
    if not death_pursues and level >= 30 and random.random() < SCROLL_ANNIHILATE_FIND * _item_scale:
        gram_p = p_correct(5, player.WIS, player.skill)
        if random.random() < gram_p * SCROLL_GRAMMAR_P_BASE:
            # Effectively prevents one combat's worth of damage
            player.healing_bank += int(player.max_hp * 0.15)

    # --- Container loot system ---
    n_containers = CONTAINER_GUARANTEED
    extra_chance = CONTAINER_EXTRA_CHANCE
    while random.random() < extra_chance:
        n_containers += 1
        extra_chance *= CONTAINER_EXTRA_DECAY
    n_containers = max(0, int(n_containers * _item_scale + 0.5))
    for _ in range(n_containers):
        # Mimic check
        if random.random() < MIMIC_CHANCE:
            # Mimic fight: treat as a regular monster of appropriate level
            mimic_hp = 10 + level * 2
            mimic_monster = {'hp': str(mimic_hp), 'thac0': max(5, 20 - level // 5),
                            'attacks': [{'damage': f'2d{min(8, 4 + level // 20)}'}],
                            'resistances': [], 'weaknesses': [], 'treasure': {'gold': [10, 30]}}
            result = simulate_combat(player, mimic_monster)
            if player.hp <= 0:
                return {
                    'combats': 1, 'won': 0, 'fled': 0, 'boss_killed': False,
                    'hp_lost': result['hp_lost'], 'sp_drained': 0,
                    'death': 'combat', 'chains': result['chains'],
                    'starv_dmg': 0, 'miniboss_killed': False,
                }
            continue

        # Lockpick attempt
        if player.lockpick_charges > 0:
            lock_tier = max(1, min(5, (level - 1) // 20 + 1))
            lock_p = p_correct(lock_tier, player.WIS, player.skill)
            if random.random() < CONTAINER_LOCKPICK_P * lock_p:
                # Success: get gold + possible item
                gold = CONTAINER_GOLD_BASE + level * CONTAINER_GOLD_LEVEL_SCALE
                gold = random.randint(int(gold * 0.5), int(gold * 1.5))
                player.gold += gold
                if random.random() < CONTAINER_ITEM_CHANCE:
                    # Useful item: weapon/armor/scroll - modelled as small healing bank boost
                    player.healing_bank += random.randint(5, 15)
                player.lockpick_charges -= 1
            else:
                # Failed: possible trap damage (scales with container tier)
                if random.random() < CONTAINER_TRAP_CHANCE:
                    trap_base = max(2, CONTAINER_TRAP_DMG * lock_tier // 3)
                    trap_dmg = random.randint(max(1, trap_base - 2), trap_base + 3)
                    player.take_damage(trap_dmg)
                    if player.hp <= 0:
                        return {
                            'combats': 0, 'won': 0, 'fled': 0, 'boss_killed': False,
                            'hp_lost': trap_dmg, 'sp_drained': 0,
                            'death': 'trap', 'chains': [],
                            'starv_dmg': 0, 'miniboss_killed': False,
                        }
                player.lockpick_charges -= 1

    # Replenish lockpicks (find ~1 per 3 levels)
    if random.random() < 0.33:
        player.lockpick_charges += random.randint(3, 8)

    # --- Special rooms (35% chance) ---
    if not death_pursues and random.random() < SPECIAL_ROOM_CHANCE:
        room_roll = random.random()
        if room_roll < 0.33:
            # Treasury: extra containers + gold
            for _ in range(TREASURY_EXTRA_CONTAINERS):
                gold = level * TREASURY_GOLD_MULT
                player.gold += random.randint(int(gold * 0.5), int(gold * 1.5))
                if random.random() < CONTAINER_ITEM_CHANCE:
                    player.healing_bank += random.randint(5, 15)
        elif room_roll < 0.66:
            # Library: scrolls + possible spellbook
            for _ in range(LIBRARY_SCROLLS):
                # Each scroll has a chance to be useful (heal, enchant, etc.)
                if random.random() < 0.30:
                    player.healing_bank += roll_dice('3d6')
                elif random.random() < 0.20:
                    player.weapon_enchant += 1
            if random.random() < LIBRARY_SPELLBOOK_CHANCE:
                # Learn a spell
                gram_p = p_correct(2, player.WIS, player.skill)
                if random.random() < SPELL_LEARN_CHANCE * gram_p:
                    player.known_spells += 1
                    if player.known_spells >= 3:
                        player.has_heal_spell = True
                    if player.known_spells >= 2:
                        player.has_shield_spell = True
        else:
            # Shrine: prayer opportunity
            if player.prayer_cooldown <= 0:
                _simulate_prayer(player, level)
                player.prayer_cooldown = 100

    # --- Spellbook find (standard) ---
    if not death_pursues and random.random() < SPELLBOOK_FIND_CHANCE * _item_scale:
        gram_p = p_correct(2, player.WIS, player.skill)
        if random.random() < SPELL_LEARN_CHANCE * gram_p:
            player.known_spells += 1
            if player.known_spells >= 3:
                player.has_heal_spell = True
            if player.known_spells >= 2:
                player.has_shield_spell = True

    # --- Spell usage (pre-combat buffs + healing between fights) ---
    if player.known_spells > 0 and player.mp >= SPELL_AVG_CAST_COST:
        # Use heal spell if available and HP < 60%
        if player.has_heal_spell and player.hp < player.max_hp * 0.60:
            sci_p = p_correct(3, player.WIS, player.skill)
            chain = roll_chain(sci_p, 5)
            if chain > 0:
                heal = int(roll_dice('3d8') * chain / 5.0)
                player.hp = min(player.hp + heal, player.max_hp)
            player.mp -= 8
        # Use shield spell for tough fights
        elif player.has_shield_spell and player.mp >= 5:
            # Shield effectively reduces incoming damage ~20% for next combat
            player.healing_bank += int(player.max_hp * 0.05)
            player.mp -= 5

    # --- Mystery system ---
    if not death_pursues:
        for mid, m_min, m_max, m_subj, m_mode, m_tier, m_thresh, m_rtype, m_rval in MYSTERY_TABLE:
            if mid in player.mysteries_solved:
                continue
            if m_min <= level <= m_max:
                if random.random() < MYSTERY_SPAWN_CHANCE:
                    # Attempt to solve the mystery
                    solved = _attempt_mystery(player, m_subj, m_mode, m_tier, m_thresh)
                    if solved:
                        player.mysteries_solved.add(mid)
                        _apply_mystery_reward(player, m_rtype, m_rval)
                    break  # At most one mystery per level

    # --- Prayer at altar (natural altars every 15 levels) ---
    if player.prayer_cooldown > 0:
        player.prayer_cooldown -= 1
    if not death_pursues and level % 15 == 1 and player.prayer_cooldown <= 0:
        _simulate_prayer(player, level)
        player.prayer_cooldown = 100

    # --- Exploration SP drain ---
    player.drain_sp(SP_EXPLORATION_PER_LEVEL)

    # --- Metabolic power: restore 100 SP if critically low ---
    if player.metabolic_uses > 0 and player.sp < 50:
        player.restore_sp(100)
        player.metabolic_uses -= 1

    # --- Death Pursuer attack on ascent levels ---
    # Death attacks once per level during ascent. Damage escalates as Death
    # gets angrier (floors_chased increases as player ascends from L99 to L1).
    # Base damage + 1% per floor chased (so +50% by L50, +99% by L1).
    if death_pursues:
        floors_chased = 100 - level
        escalation = 1.0 + floors_chased * 0.007  # +0.7% per floor
        death_atk = int(roll_dice(DEATH_ATTACK_DICE) * escalation)
        if player.take_damage(death_atk):
            return {
                'combats': 0, 'won': 0, 'fled': 0, 'boss_killed': False,
                'hp_lost': death_atk, 'sp_drained': 0,
                'death': 'death_pursuer', 'chains': [], 'starv_dmg': 0,
                'miniboss_killed': False,
            }

    # --- Boss fight (mandatory) ---
    if is_boss_level and boss_id and boss_id in monsters:
        boss = dict(monsters[boss_id])
        if boss_hp_scale != 1.0:
            raw_hp = avg_dice(str(boss.get('hp', 10)))
            boss['hp'] = max(1, int(raw_hp * boss_hp_scale))
        player.use_healing(max_hp_fraction=1.0)
        result = simulate_combat(player, boss, allow_flee=False, pre_fight_heal=False)
        chains = result['chains']
        return {
            'combats':        1,
            'won':            1 if result['won'] else 0,
            'fled':           0,
            'boss_killed':    result['won'],
            'hp_lost':        result['hp_lost'],
            'sp_drained':     0,
            'death':          None if (player.hp > 0) else
                              ('starvation' if result['starv_dmg'] > 0 else 'combat'),
            'chains':         chains,
            'starv_dmg':      result['starv_dmg'],
            'miniboss_killed': False,
        }

    # --- Mini-boss check ---
    miniboss_killed = False
    for mid, mn_lv, mx_lv, sp_chance, mb_data in miniboss_table:
        if mid in placed_minibosses:
            continue
        if mn_lv <= level <= mx_lv:
            if random.random() < sp_chance:
                placed_minibosses.add(mid)
                # Mini-boss fight: harder than regular, no flee
                mb = dict(mb_data)
                player.use_healing(max_hp_fraction=0.60)
                result = simulate_combat(player, mb, allow_flee=False,
                                         pre_fight_heal=False)
                if player.hp <= 0:
                    return {
                        'combats': 1, 'won': 0, 'fled': 0, 'boss_killed': False,
                        'hp_lost': result['hp_lost'], 'sp_drained': 0,
                        'death': 'starvation' if result['starv_dmg'] > 0 else 'combat',
                        'chains': result['chains'], 'starv_dmg': result['starv_dmg'],
                        'miniboss_killed': False,
                    }
                miniboss_killed = result['won']
                break  # at most one mini-boss per level

    # --- Regular monster encounters ---
    min_m = int(min(2 + level // 15, 7)  * monster_scale)
    max_m = int(min(3 + level // 8,  11) * monster_scale)
    min_m = max(1, min_m)
    max_m = max(min_m, max_m)
    n_monsters = random.randint(min_m, max_m)

    pool = []
    for mid, m in monsters.items():
        freq = m.get('frequency', 5)
        if freq == 0:
            continue
        if m.get('is_mini_boss'):
            continue  # mini-bosses handled separately
        min_lv = m.get('min_level', 1)
        if min_lv > level:
            continue
        max_lv = m.get('max_level')
        use_proximity = level >= 30
        if max_lv and level > max_lv:
            over = level - max_lv
            if use_proximity:
                freq = freq - over
                if freq <= 0:
                    continue
            else:
                freq = max(1, freq - over)
        if use_proximity:
            distance = level - min_lv
            prox_scale = max(0, (level - 30) // 10)
            if distance <= 5:
                freq *= (2 + prox_scale)
            elif distance <= 15:
                freq *= max(1, 1 + prox_scale // 2)
        pool.extend([mid] * freq)

    if not pool:
        return {'combats': 0, 'won': 0, 'fled': 0, 'boss_killed': False,
                'hp_lost': 0, 'sp_drained': 0, 'death': None,
                'chains': [], 'starv_dmg': 0, 'miniboss_killed': miniboss_killed}

    combats_won   = 0
    combats_fled  = 0
    total_hp_lost = 0
    all_chains    = []
    total_starv   = 0
    death_cause   = None

    for _ in range(n_monsters):
        if player.hp <= 0:
            death_cause = 'starvation' if player.is_starving() else 'combat'
            break

        mid    = random.choice(pool)
        result = simulate_combat(player, monsters[mid])
        total_hp_lost += result['hp_lost']
        all_chains.extend(result['chains'])
        total_starv   += result['starv_dmg']
        if result['won']:
            combats_won += 1
            # Cooking pipeline: harvest corpse, attempt to cook
            if random.random() < HARVEST_CHANCE:
                if random.random() < COOK_ATTEMPT_CHANCE:
                    sp_r, hp_r, _, max_hp_r = simulate_cooking(player.WIS, player.skill, level)
                    player.restore_sp(sp_r)
                    if hp_r > 0:
                        player.healing_bank += hp_r
                    if max_hp_r > 0:
                        player.max_hp += max_hp_r
                        player.hp = min(player.hp + max_hp_r, player.max_hp)
        elif result['fled']:
            combats_fled += 1
        elif player.hp <= 0:
            death_cause = 'starvation' if result['starv_dmg'] > 0 else 'combat'

    # Post-combat healing
    player.use_healing(max_hp_fraction=0.75)

    # Quirk unlock check (floor clean = no HP damage from monsters this level)
    _check_quirk_unlocks(player, floor_was_clean=(total_hp_lost == 0 and not death_cause))

    return {
        'combats':     n_monsters,
        'won':         combats_won,
        'fled':        combats_fled,
        'boss_killed': False,
        'hp_lost':     total_hp_lost,
        'sp_drained':  SP_EXPLORATION_PER_LEVEL + total_starv * SP_PER_COMBAT_TURN,
        'death':       death_cause,
        'chains':      all_chains,
        'starv_dmg':   total_starv,
        'miniboss_killed': miniboss_killed,
    }

# ---------------------------------------------------------------------------
# Full run (two-phase: descent + ascent)
# ---------------------------------------------------------------------------

def simulate_run(max_level: int, monsters: dict, weapons: dict,
                 armor: dict, shields: dict, food: dict,
                 accessories: dict, wands: dict,
                 miniboss_table: list,
                 skill: str = 'med',
                 hp_per_level: int = HP_PER_LEVEL,
                 monster_scale: float = 1.0,
                 boss_hp_scale: float = 1.0,
                 build: dict = None) -> dict:
    """
    Simulate a complete run:
      Phase 1: Descend L1 -> max_level, fight bosses at milestone levels
      Phase 2: Ascend L(max_level-1) -> 1 with Death in pursuit
    """
    player          = SimPlayer(skill=skill, hp_per_level=hp_per_level, build=build)
    per_lv          = []
    died_on         = None
    death_cause     = None
    placed_mbs      = set()
    miniboss_kills  = 0

    # -- Phase 1: Descent --
    for lv in range(1, max_level + 1):
        is_boss = lv in BOSS_LEVELS and lv <= max_level
        boss_id = BOSS_LEVELS.get(lv, '')

        stats = simulate_level(
            player, lv, monsters, weapons, armor, shields,
            food, accessories, wands, miniboss_table, placed_mbs,
            is_boss_level=is_boss, boss_id=boss_id,
            monster_scale=monster_scale,
            boss_hp_scale=boss_hp_scale,
            death_pursues=False,
        )
        player.descend()
        if stats.get('miniboss_killed'):
            miniboss_kills += 1

        stats['level']         = lv
        stats['phase']         = 'descent'
        stats['hp_remaining']  = player.hp
        stats['sp_remaining']  = player.sp
        stats['player_max_hp'] = player.max_hp
        per_lv.append(stats)

        if stats['death'] or player.hp <= 0:
            died_on     = lv
            death_cause = stats['death'] or (
                'starvation' if player.sp == 0 else 'combat')
            return _run_result(False, died_on, 'descent', death_cause, per_lv,
                               player, miniboss_kills)

        if is_boss and not stats.get('boss_killed'):
            died_on     = lv
            death_cause = 'boss'
            per_lv[-1]['death'] = 'boss'
            return _run_result(False, died_on, 'descent', death_cause, per_lv,
                               player, miniboss_kills)

    # -- Phase 2: Ascent (L99 -> L1) with Death Pursuer --
    death_pursues = (max_level == 100)  # Death only spawns on full runs
    for lv in range(max_level - 1, 0, -1):
        stats = simulate_level(
            player, lv, monsters, weapons, armor, shields,
            food, accessories, wands, miniboss_table, placed_mbs,
            is_boss_level=False,
            monster_scale=monster_scale,
            death_pursues=death_pursues,
        )
        # No descend() on ascent; stair-rest heal is reduced (player is rushing up)
        rest_heal = max(HP_PER_LEVEL_REST, int(player.max_hp * DEATH_ASCENT_REST_PCT))
        player.hp = min(player.hp + rest_heal, player.max_hp)

        if stats.get('miniboss_killed'):
            miniboss_kills += 1

        stats['level']         = lv
        stats['phase']         = 'ascent'
        stats['hp_remaining']  = player.hp
        stats['sp_remaining']  = player.sp
        stats['player_max_hp'] = player.max_hp
        per_lv.append(stats)

        if stats['death'] or player.hp <= 0:
            died_on     = lv
            death_cause = stats['death'] or (
                'starvation' if player.sp == 0 else 'combat')
            return _run_result(False, died_on, 'ascent', death_cause, per_lv,
                               player, miniboss_kills)

    return _run_result(True, None, 'complete', None, per_lv, player, miniboss_kills)


def _run_result(survived, died_on, phase, death_cause, per_lv, player, miniboss_kills):
    score = _calc_score(player, survived)
    # Find max HP when player reached L100
    max_hp_100 = None
    for s in per_lv:
        if s['phase'] == 'descent' and s['level'] == 100:
            max_hp_100 = s.get('player_max_hp')
    return {
        'survived':      survived,
        'died_on':       died_on,
        'phase':         phase,
        'death_cause':   death_cause,
        'per_level':     per_lv,
        'miniboss_kills': miniboss_kills,
        'score':         score,
        'kills':         player.kills,
        'gold':          player.gold,
        'turns':         player.turns,
        'correct':       player.quests_correct,
        'wrong':         player.quests_wrong,
        'deepest_level': max((s['level'] for s in per_lv if s['phase'] == 'descent'),
                             default=0),
        'quirks':        set(player.quirk_unlocked),
        'mysteries':     set(player.mysteries_solved),
        'max_hp_at_100': max_hp_100,
    }


def _calc_score(player: SimPlayer, survived: bool) -> int:
    """Match scoring in main.py: turns*10 + max_level*1000 + kills*100 + 50000 stone."""
    s  = player.turns * 10
    s += player.kills * 100
    if survived:
        s += 50000
    return s

def _grade(score: int) -> str:
    for threshold, grade in [(200000,'S'), (100000,'A+'), (60000,'A'),
                              (30000,'B+'), (15000,'B'), (7000,'C'),
                              (3000,'D')]:
        if score >= threshold:
            return grade
    return 'F'

# ---------------------------------------------------------------------------
# Aggregation + report
# ---------------------------------------------------------------------------

def run_simulation(runs: int, max_level: int, seed: int, skill: str,
                   hp_per_level: int = HP_PER_LEVEL,
                   monster_scale: float = 1.0,
                   boss_hp_scale: float = 1.0,
                   build_name: str = 'generic',
                   show_minibosses: bool = False,
                   show_scoring: bool = False,
                   compare_builds: bool = False):

    random.seed(seed)
    monsters, weapons, armor, shields, food, accessories, wands, ingr, recipes, scrolls = load_data()
    miniboss_table = _build_miniboss_table(monsters)

    if compare_builds:
        _run_compare_builds(runs, max_level, seed, skill, hp_per_level,
                            monster_scale, boss_hp_scale,
                            monsters, weapons, armor, shields, food,
                            accessories, wands, miniboss_table)
        return

    build = SECRET_BUILDS.get(build_name, SECRET_BUILDS['generic'])

    # --- Accumulators ---
    d_reached      = defaultdict(int)
    d_died         = defaultdict(int)
    d_death_cause  = defaultdict(lambda: defaultdict(int))
    d_hp_lost      = defaultdict(list)
    d_max_hp       = defaultdict(list)  # track actual player max HP at each level
    d_sp_rem       = defaultdict(list)
    d_chains       = defaultdict(list)
    d_won          = defaultdict(int)
    d_combats      = defaultdict(int)
    d_fled         = defaultdict(int)
    d_starv        = defaultdict(list)
    d_boss_kill    = defaultdict(int)
    d_boss_attempt = defaultdict(int)
    d_mb_kill      = defaultdict(int)   # mini-boss kills per level range

    a_reached      = defaultdict(int)
    a_died         = defaultdict(int)
    a_death_cause  = defaultdict(lambda: defaultdict(int))
    a_hp_lost      = defaultdict(list)

    total_survived      = 0
    died_descent        = 0
    died_ascent         = 0
    total_miniboss_kills = 0
    scores              = []
    total_kills         = []
    total_turns         = []
    grade_counts        = defaultdict(int)
    death_pursuer_kills = 0
    quirk_unlock_counts = defaultdict(int)  # quirk_id -> runs that unlocked it
    mystery_solve_counts = defaultdict(int)  # mystery_id -> runs that solved it
    max_hp_at_l100      = []  # track max HP at L100 for cooking HP analysis
    trap_deaths         = 0
    mimic_deaths        = 0

    for _ in range(runs):
        result = simulate_run(
            max_level, monsters, weapons, armor, shields, food,
            accessories, wands, miniboss_table,
            skill=skill, hp_per_level=hp_per_level,
            monster_scale=monster_scale,
            boss_hp_scale=boss_hp_scale,
            build=build,
        )

        if result['survived']:
            total_survived += 1
        scores.append(result['score'])
        total_kills.append(result['kills'])
        total_turns.append(result['turns'])
        total_miniboss_kills += result['miniboss_kills']
        grade_counts[_grade(result['score'])] += 1
        if result['death_cause'] == 'death_pursuer':
            death_pursuer_kills += 1
        if result['death_cause'] == 'trap':
            trap_deaths += 1
        for qid in result.get('quirks', set()):
            quirk_unlock_counts[qid] += 1
        for mid in result.get('mysteries', set()):
            mystery_solve_counts[mid] += 1
        if result.get('max_hp_at_100'):
            max_hp_at_l100.append(result['max_hp_at_100'])

        for s in result['per_level']:
            lv    = s['level']
            phase = s['phase']

            if phase == 'descent':
                d_reached[lv]   += 1
                d_hp_lost[lv].append(s['hp_lost'])
                d_max_hp[lv].append(s.get('player_max_hp', 30))
                d_sp_rem[lv].append(s['sp_remaining'])
                d_chains[lv].extend(s['chains'])
                d_won[lv]       += s['won']
                d_combats[lv]   += s['combats']
                d_fled[lv]      += s.get('fled', 0)
                d_starv[lv].append(s['starv_dmg'])
                if lv in BOSS_LEVELS:
                    d_boss_attempt[lv] += 1
                    if s.get('boss_killed'):
                        d_boss_kill[lv] += 1
                if s['death']:
                    d_died[lv]  += 1
                    d_death_cause[lv][s['death']] += 1
            elif phase == 'ascent':
                a_reached[lv]   += 1
                a_hp_lost[lv].append(s['hp_lost'])
                if s['death']:
                    a_died[lv]  += 1
                    a_death_cause[lv][s['death']] += 1

        if result['phase'] == 'descent' and result['died_on'] is not None:
            died_descent += 1
        elif result['phase'] == 'ascent' and result['died_on'] is not None:
            died_ascent  += 1

    # ---- Report ----------------------------------------------------------------
    W = 95
    print('=' * W)
    print('  Philosopher\'s Quest -- Comprehensive Balance Simulation')
    print(f'  {runs} runs | max_level={max_level} | seed={seed} | skill={skill} | '
          f'build={build_name} | HP+{hp_per_level}/lv')
    print(f'  quiz p={SKILL_BASE[skill]:.2f}-(tier-1)*0.06+(WIS-10)*0.015 | '
          f'flee@{FLEE_THRESHOLD*100:.0f}%HP({FLEE_SUCCESS_RATE*100:.0f}%)')
    print(f'  gear: wpn={WEAPON_FIND_CHANCE*100:.0f}%/lv, '
          f'armor={ARMOR_FIND_CHANCE*100:.0f}%/slot/lv, '
          f'acc={ACC_FIND_CHANCE*100:.0f}%/lv, '
          f'wand={WAND_FIND_CHANCE*100:.0f}%/lv')
    print(f'  SP: {SP_EXPLORATION_PER_LEVEL}/lv + {SP_PER_COMBAT_TURN}/turn | '
          f'heal: {HEAL_FIND_CHANCE*100:.0f}% {HEAL_MIN}-{HEAL_MAX}HP/lv | '
          f'harvest: {HARVEST_CHANCE*100:.0f}% cook: {COOK_ATTEMPT_CHANCE*100:.0f}%')
    print(f'  potions: {POTION_SPAWN_MIN}-{POTION_SPAWN_MAX}/lv '
          f'({POTION_HEAL_FRACTION*100:.0f}% heal/{POTION_NEGATIVE_FRAC*100:.0f}% neg) | '
          f'Death: {DEATH_ATTACK_DICE} | ascent stair-rest: max({hp_per_level}, {DEATH_ASCENT_REST_PCT*100:.0f}%HP)')
    bstat = build or SECRET_BUILDS['generic']
    print(f'  Build stats: STR={bstat["STR"]} CON={bstat["CON"]} DEX={bstat["DEX"]} '
          f'INT={bstat["INT"]} WIS={bstat["WIS"]} PER={bstat["PER"]}')
    print(f'  Mini-bosses: {len(miniboss_table)} total, each spawns at most once per run')
    print(f'  Systems: combat+STR scaling, status effects, mysteries, scrolls, containers,')
    print(f'           special rooms, spells, prayer, quirks, cooking HP, merchants, potions')
    print('=' * W)

    red_flags = []

    # -- Descent table --
    print(f'\n--- DESCENT ---')
    step = 10 if max_level >= 50 else 1
    print(f'{"LV":<5} {"REACH":>6} {"DIED":>5} {"SURV%":>6} '
          f'{"HP_LOST":>9} {"SP":>6} {"WIN%":>6} {"FLEE%":>6} {"CHAIN":>6}  NOTE')
    print('-' * W)

    for lv in range(1, max_level + 1):
        reached = d_reached.get(lv, 0)
        if reached == 0:
            break
        died     = d_died.get(lv, 0)
        surv_pct = 100.0 * (reached - died) / reached
        avg_hl   = sum(d_hp_lost[lv]) / len(d_hp_lost[lv])
        approx_max_hp = int(sum(d_max_hp[lv]) / len(d_max_hp[lv])) if d_max_hp[lv] else 30
        hp_pct   = 100.0 * avg_hl / max(1, approx_max_hp)
        avg_sp   = sum(d_sp_rem[lv]) / len(d_sp_rem[lv])
        win_pct  = 100.0 * d_won[lv] / max(1, d_combats[lv])
        flee_pct = 100.0 * d_fled[lv] / max(1, d_combats[lv])
        clist    = d_chains[lv]
        avg_ch   = sum(clist) / max(1, len(clist))

        notes = []
        if hp_pct > 70 and lv > 5:
            notes.append('HIGH_DMG')
            red_flags.append(f'L{lv} descent: avg HP lost {avg_hl:.1f} ({hp_pct:.0f}% of ~{approx_max_hp})')
        if surv_pct < 70 and lv <= 10:
            notes.append('LETHAL')
            red_flags.append(f'L{lv}: survival {surv_pct:.1f}% in first 10 levels')
        if win_pct < 40:
            notes.append('LOW_WIN')
            red_flags.append(f'L{lv}: combat win rate {win_pct:.1f}%')
        if lv in BOSS_LEVELS and lv <= max_level:
            bkill = d_boss_kill.get(lv, 0)
            batmp = d_boss_attempt.get(lv, 1)
            bpct  = 100.0 * bkill / max(1, batmp)
            notes.append(f'BOSS:{bpct:.0f}%')
            if bpct < 20:
                red_flags.append(f'L{lv} boss kill {bpct:.1f}% -> too strong')

        note_str = ' '.join(f'[{n}]' for n in notes)
        if step == 1 or (lv % step == 0) or (lv <= 5) or (lv in BOSS_LEVELS) or died > 0:
            print(f'{lv:<5} {reached:>6} {died:>5} {surv_pct:>5.1f}% '
                  f'{avg_hl:>7.1f}({hp_pct:>2.0f}%) {avg_sp:>5.0f} '
                  f'{win_pct:>5.1f}% {flee_pct:>5.1f}% {avg_ch:>5.2f}  {note_str}')

    print('-' * W)

    # -- Ascent table --
    ascent_any = sum(1 for v in a_reached.values() if v > 0)
    if ascent_any:
        death_avg = avg_dice(DEATH_ATTACK_DICE)
        print(f'\n--- ASCENT (Death Pursuer active: {DEATH_ATTACK_DICE} avg {death_avg:.0f} dmg/level) ---')
        print(f'{"LV":<5} {"REACH":>6} {"DIED":>5} {"SURV%":>6} {"HP_LOST":>9}  CAUSE')
        print('-' * 50)
        for lv in sorted(a_reached.keys(), reverse=True):
            reached = a_reached[lv]
            if reached == 0:
                continue
            died    = a_died.get(lv, 0)
            surv    = 100.0 * (reached - died) / reached
            avg_hl  = sum(a_hp_lost[lv]) / len(a_hp_lost[lv]) if a_hp_lost[lv] else 0
            approx_max = 800  # rough estimate for endgame max HP
            hp_pct  = 100.0 * avg_hl / max(1, approx_max)
            causes  = '  '.join(f'{c}={n}' for c, n in a_death_cause[lv].items())
            if died > 0 or lv % 10 == 0 or lv <= 5:
                print(f'{lv:<5} {reached:>6} {died:>5} {surv:>5.1f}% '
                      f'{avg_hl:>7.1f}({hp_pct:>2.0f}%)  {causes}')
        print('-' * 50)

    # -- Overall survival --
    print(f'\n{"="*W}')
    print(f'OVERALL RESULTS  (skill={skill}, build={build_name}, HP+{hp_per_level}/level):')
    print(f'  Full completions   : {total_survived}/{runs} ({100*total_survived/runs:.2f}%)')
    print(f'  Died on descent    : {died_descent}/{runs} ({100*died_descent/runs:.1f}%)')
    print(f'  Died on ascent     : {died_ascent}/{runs} ({100*died_ascent/runs:.1f}%)')
    dp_pct = 100 * death_pursuer_kills / max(1, died_ascent + total_survived)
    print(f'  Killed by Death    : {death_pursuer_kills} ({dp_pct:.1f}% of ascents)')
    avg_mb = total_miniboss_kills / runs
    print(f'  Mini-boss kills/run: {avg_mb:.2f} (out of {len(miniboss_table)} possible)')

    # Death distribution
    print(f'\nDEATH DISTRIBUTION (descent):')
    all_deaths = {lv: d_died[lv] for lv in sorted(d_died.keys()) if d_died[lv] > 0}
    total_d = sum(all_deaths.values())
    if total_d:
        for lv, cnt in all_deaths.items():
            pct   = 100.0 * cnt / total_d
            bar   = '#' * int(pct / 2)
            causes = '  '.join(f'{c}={n}' for c, n in sorted(d_death_cause[lv].items()))
            print(f'  L{lv:>3}: {cnt:>5} ({pct:>5.1f}%)  {bar:<18}  [{causes}]')

    # Boss kill rate summary
    if any(lv in BOSS_LEVELS for lv in range(1, max_level + 1)):
        print(f'\nBOSS KILL RATES:')
        for lv in sorted(BOSS_LEVELS.keys()):
            if lv > max_level:
                continue
            bkill  = d_boss_kill.get(lv, 0)
            batmp  = d_boss_attempt.get(lv, 0)
            bname  = BOSS_LEVELS[lv]
            bpct   = 100.0 * bkill / max(1, batmp)
            # Note: conditional kill rates are naturally high (survivor bias).
            # Flag extreme outliers only.
            flag   = ' [!] too hard' if bpct < 20 else (' [!] too easy' if bpct > 97 else '')
            print(f'  L{lv:>3} {bname:30s}  attempts={batmp:>5}  kills={bkill:>5} ({bpct:>5.1f}%){flag}')

    # Mini-boss report
    if show_minibosses:
        print(f'\nMINI-BOSS ENCOUNTER TABLE ({len(miniboss_table)} bosses, one per run max):')
        print(f'  {"ID":30} {"RANGE":>10} {"CHANCE":>8}  Notes')
        for mid, mn_lv, mx_lv, sp_chance, _ in miniboss_table:
            print(f'  {mid:30} L{mn_lv:>2}-{mx_lv:>2}   {sp_chance*100:>5.0f}%')

    # Scoring report
    if show_scoring and scores:
        print(f'\nSCORING ANALYSIS (turns*10 + kills*100 + 50000 stone):')
        scores.sort()
        pct50  = scores[len(scores)//2]
        pct90  = scores[int(len(scores)*0.90)]
        pct99  = scores[int(len(scores)*0.99)]
        avg_sc = sum(scores) / len(scores)
        avg_kl = sum(total_kills) / len(total_kills)
        avg_tr = sum(total_turns) / len(total_turns)
        print(f'  Avg kills/run : {avg_kl:.1f}')
        print(f'  Avg turns/run : {avg_tr:.1f}')
        print(f'  Avg score     : {avg_sc:.0f}  ({_grade(int(avg_sc))})')
        print(f'  Median score  : {pct50}  ({_grade(pct50)})')
        print(f'  90th pct      : {pct90}  ({_grade(pct90)})')
        print(f'  99th pct      : {pct99}  ({_grade(pct99)})')
        print(f'  Grade distribution:')
        for g in ['S','A+','A','B+','B','C','D','F']:
            cnt = grade_counts.get(g, 0)
            bar = '#' * max(0, int(40 * cnt / runs))
            print(f'    {g:>3}: {cnt:>5} ({100*cnt/runs:>5.1f}%)  {bar}')

    # Gear ceiling
    print(f'\nGEAR CEILING (theoretical max per tier):')
    sample_levels = [lv for lv in [1,5,10,20,30,40,50,60,70,80,90,100] if lv <= max_level]
    print(f'  {"LV":<5} {"BEST WEAPON":30} {"base":>5} {"tier":>5} {"TOTAL_AC":>9}')
    for lv in sample_levels:
        w  = best_weapon_at_level(weapons, lv)
        ac = best_armor_ac_at_level(armor, shields, lv)
        if w:
            name  = w.get('name', '?')[:28]
            bd    = w.get('baseDamage', '?')
            tier  = w.get('mathTier', '?')
            print(f'  {lv:<5} {name:<30} {str(bd):>5} {str(tier):>5} {"AC+"+str(ac):>9}')

    # Chain table
    p_base = p_correct(1, bstat['WIS'], skill)
    print(f'\nCHAIN TABLE (iron_dagger @ L1, p={p_base:.2f}, WIS={bstat["WIS"]}):')
    base_mults = [0.3, 0.6, 1.0, 1.4, 1.8, 2.2, 2.5]
    base_dmg   = 3
    print(f'  {"CHAIN":>6} {"P":>8} {"DMG":>14} {"E[dmg]":>8}')
    for k in range(len(base_mults) + 1):
        if k == 0:
            prob = 1 - p_base
            print(f'  {k:>6} {prob:>8.4f} {"miss":>14} {"0.00":>8}')
        else:
            prob = (p_base ** k) * (1 - p_base) if k < len(base_mults) else p_base ** len(base_mults)
            m    = base_mults[k - 1]
            dmg  = max(1, int(base_dmg * m))
            print(f'  {k:>6} {prob:>8.4f} {f"{base_dmg} x {m:.1f} = {dmg}":>14} {prob*dmg:>8.2f}')

    # Cooking quality model
    cook_p = p_correct(max(1, min(5, 1)), bstat['WIS'], skill)
    print(f'\nCOOKING MODEL (escalator chain, base p={cook_p:.2f}):')
    cook_dist = defaultdict(int)
    for _ in range(10000):
        q = roll_escalator_chain(cook_p)
        cook_dist[q] += 1
    print(f'  {"QUALITY":>8} {"FREQ":>8} {"SP":>6} {"HP(T1)":>8} {"HP(T5)":>8}')
    for q in range(6):
        freq = cook_dist[q] / 100
        sp = COOKED_SP_BASE + q * COOKED_SP_PER_QUALITY
        hp1 = _cooking_hp_bonus(1, q)
        hp5 = _cooking_hp_bonus(81, q)
        print(f'  {q:>8} {freq:>7.1f}%  {sp:>5}  {hp1:>7}  {hp5:>7}')

    # Quirk unlock rates
    TRACKED_QUIRKS = [
        ('eye_storm',       'Eye of the Storm    (5 clean floors  -> +3 max HP)'),
        ('runic_armor',     'Runic Armor         (50 hits taken   -> +2 AC)'),
        ('temporal_shield', 'Temporal Shield     (150 hits taken  -> +1 AC)'),
        ('ramanujan',       'Ramanujan           (500 correct     -> WIS+2)'),
        ('battle_trance',   'Battle Trance       (200 kills       -> WIS+1)'),
        ('life_drain',      'Life Drain          (200 kills       -> 3x +25HP steal)'),
        ('metabolic',       'Metabolic Surge     (~1700 turns     -> 3x +100SP)'),
        ('iron_ration',     'Iron Ration         (~5000 turns     -> max SP+50)'),
        ('phoenix_rising',  'Phoenix Rising      (10 near-death   -> 10x auto-revive)'),
    ]
    print(f'\nQUIRK UNLOCK RATES (skill={skill}):')
    print(f'  {"QUIRK":<55} {"RUNS":>6}  {"PCT":>7}')
    print(f'  {"-"*55}  {"-"*6}  {"-"*7}')
    for qid, label in TRACKED_QUIRKS:
        cnt = quirk_unlock_counts.get(qid, 0)
        pct = 100.0 * cnt / runs
        bar = '#' * max(0, int(pct / 2))
        print(f'  {label:<55} {cnt:>6}  {pct:>6.1f}%  {bar}')

    # Mystery solve rates
    print(f'\nMYSTERY SOLVE RATES (skill={skill}):')
    print(f'  {"MYSTERY":<20} {"FLOOR":>8} {"SOLVED":>7} {"PCT":>7}')
    print(f'  {"-"*20}  {"-"*8} {"-"*7} {"-"*7}')
    for mid, m_min, m_max, *_ in MYSTERY_TABLE:
        cnt = mystery_solve_counts.get(mid, 0)
        pct = 100.0 * cnt / runs
        print(f'  {mid:<20} L{m_min:>2}-{m_max:<3}  {cnt:>6}  {pct:>6.1f}%')
    total_mysteries = sum(mystery_solve_counts.values())
    avg_mysteries = total_mysteries / runs
    print(f'  Average mysteries solved per run: {avg_mysteries:.2f}')

    # Max HP at L100 analysis (cooking HP growth)
    if max_hp_at_l100:
        avg_max_hp = sum(max_hp_at_l100) / len(max_hp_at_l100)
        max_hp_at_l100.sort()
        med_hp = max_hp_at_l100[len(max_hp_at_l100) // 2]
        min_hp = max_hp_at_l100[0]
        max_hp = max_hp_at_l100[-1]
        print(f'\nMAX HP AT L100 (cooking-based growth, {len(max_hp_at_l100)} runs reached):')
        print(f'  Average: {avg_max_hp:.0f}  Median: {med_hp}  Min: {min_hp}  Max: {max_hp}')
        if avg_max_hp < 500:
            red_flags.append(f'Max HP at L100 only {avg_max_hp:.0f} avg (target 800-900)')
        elif avg_max_hp > 1200:
            red_flags.append(f'Max HP at L100 is {avg_max_hp:.0f} avg (too high, target 800-900)')

    # New system summary
    print(f'\nNEW SYSTEMS SUMMARY:')
    print(f'  Trap deaths      : {trap_deaths}/{runs} ({100*trap_deaths/runs:.2f}%)')
    print(f'  Status effects   : Modelled (poison/burn DoT, disease stat drain, confuse/paralyze)')
    print(f'  Containers       : {CONTAINER_GUARANTEED}+ per level, lockpick-gated')
    print(f'  Special rooms    : {SPECIAL_ROOM_CHANCE*100:.0f}% per level (treasury/library/shrine)')
    print(f'  Spell system     : {SPELLBOOK_FIND_CHANCE*100:.0f}% spellbook/lv, science chain casting')
    print(f'  Prayer system    : Altars every 15 levels + shrine rooms')

    # Red flags
    if red_flags:
        print(f'\nRED FLAGS:')
        seen = set()
        for f in red_flags:
            if f not in seen:
                print(f'  [!] {f}')
                seen.add(f)
    else:
        print(f'\n[OK] No critical flags at skill={skill}, build={build_name}.')

    print('=' * W)


def _run_compare_builds(runs, max_level, seed, skill, hp_per_level,
                        monster_scale, boss_hp_scale,
                        monsters, weapons, armor, shields, food,
                        accessories, wands, miniboss_table):
    """Run all SECRET_BUILDS and print a comparison table."""
    W = 100
    print('=' * W)
    print(f'  BUILD COMPARISON  ({runs} runs each | skill={skill} | HP+{hp_per_level}/lv)')
    print('=' * W)
    print(f'  {"BUILD":12} {"STR":>4}{"CON":>4}{"DEX":>4}{"INT":>4}{"WIS":>4}{"PER":>4} '
          f'  {"WIN%":>6} {"D-DEATH":>8} {"A-DEATH":>8} {"MB/run":>7} {"AvgScore":>9}')
    print('-' * W)

    build_results = []
    for bname, bstats in SECRET_BUILDS.items():
        random.seed(seed)
        survived = 0
        ddeath = 0
        adeath = 0
        mb_kills = 0
        scores = []
        for _ in range(runs):
            r = simulate_run(
                max_level, monsters, weapons, armor, shields, food,
                accessories, wands, miniboss_table,
                skill=skill, hp_per_level=hp_per_level,
                monster_scale=monster_scale, boss_hp_scale=boss_hp_scale,
                build=bstats,
            )
            if r['survived']:
                survived += 1
            if r['phase'] == 'descent' and r['died_on']:
                ddeath += 1
            elif r['phase'] == 'ascent' and r['died_on']:
                adeath += 1
            mb_kills += r['miniboss_kills']
            scores.append(r['score'])

        win_pct  = 100 * survived / runs
        avg_sc   = sum(scores) / len(scores) if scores else 0
        avg_mb   = mb_kills / runs
        build_results.append((bname, bstats, win_pct, ddeath, adeath, avg_mb, avg_sc))

    # Sort by completion rate
    build_results.sort(key=lambda x: -x[2])
    for bname, bs, win_pct, dd, ad, avg_mb, avg_sc in build_results:
        flag = ' <<' if win_pct > 5.0 else (' >>' if win_pct < 0.5 else '')
        print(f'  {bname:12} {bs["STR"]:>4}{bs["CON"]:>4}{bs["DEX"]:>4}'
              f'{bs["INT"]:>4}{bs["WIS"]:>4}{bs["PER"]:>4} '
              f'  {win_pct:>5.2f}%  {dd:>7}  {ad:>7}  {avg_mb:>6.2f}  {avg_sc:>9.0f}{flag}')

    print('=' * W)
    print('  [OK] Dad excluded from ranking (immortal build).')
    print('=' * W)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description='Philosopher\'s Quest comprehensive balance simulator')
    ap.add_argument('--runs',            type=int,   default=500,
                    help='Simulation runs (default 500)')
    ap.add_argument('--max-level',       type=int,   default=100,
                    help='Deepest level to simulate (default 100)')
    ap.add_argument('--seed',            type=int,   default=42,
                    help='RNG seed (default 42)')
    ap.add_argument('--skill',           type=str,   default='med',
                    choices=['low', 'med', 'high'],
                    help='Player skill preset (default med)')
    ap.add_argument('--hp-per-level',    type=int,   default=HP_PER_LEVEL,
                    help=f'Max HP gained per dungeon level (default {HP_PER_LEVEL})')
    ap.add_argument('--monster-scale',   type=float, default=1.0,
                    help='Scale monster count per level (default 1.0)')
    ap.add_argument('--boss-hp-scale',   type=float, default=1.0,
                    help='Scale boss HP (default 1.0)')
    ap.add_argument('--build',           type=str,   default='generic',
                    choices=list(SECRET_BUILDS.keys()),
                    help='Secret build to simulate (default generic)')
    ap.add_argument('--compare-builds',  action='store_true',
                    help='Run all builds and print comparison table')
    ap.add_argument('--show-minibosses', action='store_true',
                    help='Print full mini-boss encounter table')
    ap.add_argument('--show-scoring',    action='store_true',
                    help='Print score distribution and grade breakdown')
    args = ap.parse_args()

    run_simulation(
        args.runs, args.max_level, args.seed, args.skill,
        args.hp_per_level, args.monster_scale, args.boss_hp_scale,
        build_name=args.build,
        show_minibosses=args.show_minibosses,
        show_scoring=args.show_scoring,
        compare_builds=args.compare_builds,
    )

if __name__ == '__main__':
    main()
