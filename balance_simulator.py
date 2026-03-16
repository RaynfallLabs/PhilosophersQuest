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
  - Armor equip: gated by geography THRESHOLD quiz using item's quiz_tier
  - Accessories: history THRESHOLD quiz; beneficial effects modelled
  - Wands/scrolls: found per level, healing wands add to HP bank
  - Cooking: escalator_chain quiz; quality 0-5 maps to SP+HP restore
  - Mini-bosses: up to one per eligible level range; spawn_chance per monster.json
  - Death Pursuer: spawned on ascent from L100 with Stone; attacks every level, always hits
  - Flee: player can flee when HP < 25% max (60% success rate)
  - HP scaling: player gains HP_PER_LEVEL max HP each dungeon level descended
  - Stair-rest heal: max(HP_PER_LEVEL, 5% max_hp) on each stair use
  - SP: 25/level exploration + 2/combat turn; SP=0 -> 1 HP starvation/turn
  - Scoring: turns*10 + max_level*1000 + kills*100 + 50000 stone bonus
  - Two-phase run: descent then ascent after defeating Abaddon
"""

import json, math, random, argparse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / 'data'

# ---------------------------------------------------------------------------
# Tunable constants (game-balance levers)
# ---------------------------------------------------------------------------

HP_PER_LEVEL         = 8      # Max HP gained per dungeon level descended
                              # (matches player.py HP_PER_LEVEL = 8)
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
DEATH_ATTACK_DICE     = '2d20+47'   # Attack per level (avg ~68 HP); net -15 HP/floor after 6.5% heal
DEATH_ASCENT_REST_PCT = 0.065       # Stair-rest heal fraction on ascent

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
    return monsters, weapons, armor, shields, food, accessories, wands, ingredients, recipes

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

def simulate_cooking(player_wis: int, skill: str, level: int) -> tuple:
    """
    Simulate one cooking attempt (escalator_chain).
    Returns (sp_restored, hp_restored, quality).
    ingredient tier approximated by dungeon level.
    """
    base_p = p_correct(max(1, min(5, (level - 1) // 20 + 1)), player_wis, skill)
    quality = roll_escalator_chain(base_p)
    sp = max(0, COOKED_SP_BASE + quality * COOKED_SP_PER_QUALITY)
    hp = _cooking_hp_bonus(max(1, level), quality)
    return sp, hp, quality

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

    @property
    def ac(self) -> int:
        base = 10 - self._dex_ac - self.armor_ac
        if self.has_invis:
            base -= 2  # invisibility grants AC bonus
        return base

    def descend(self):
        """Called on each stair: gain HP_PER_LEVEL max HP + stair-rest heal."""
        self.max_hp += self.hp_per_level
        rest_heal = max(self.hp_per_level, int(self.max_hp * 0.05))
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

        # --- Player attacks ---
        n_attacks = 2 if player.has_haste else 1
        for _ in range(n_attacks):
            chain = roll_chain(p_cor, player.weapon_max_chain)
            chains.append(chain)
            player.quests_correct += chain
            if chain > 0:
                idx  = min(chain - 1, len(player.weapon_mults) - 1)
                mult = player.weapon_mults[idx]
                raw  = player.weapon_base_dmg + player.weapon_enchant
                dmg  = max(1, int(raw * mult * dmult))
                m_hp -= dmg
            if m_hp <= 0:
                break

        if m_hp <= 0:
            break

        # --- Monster retaliates ---
        if pursuer:
            # Death always hits with 2d20+60
            dmg = roll_dice('2d20+60')
            if player.take_damage(dmg):
                break
        else:
            if random.random() < hit_chance:
                attacks = monster.get('attacks', [{'damage': '1d4'}])
                total_mdmg = 0
                for atk in attacks:
                    total_mdmg += roll_dice(str(atk.get('damage', '1d4')))
                if player.take_damage(total_mdmg):
                    break

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

    # --- Exploration SP drain ---
    player.drain_sp(SP_EXPLORATION_PER_LEVEL)

    # --- Death Pursuer attack on ascent levels ---
    # Death attacks once per level during ascent (half-speed, but always present).
    # This happens after regular-floor combat but before the stair-rest heal.
    if death_pursues:
        death_atk = roll_dice(DEATH_ATTACK_DICE)
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
        if m.get('min_level', 1) > level:
            continue
        max_lv = m.get('max_level')
        if max_lv and level > max_lv:
            freq = max(1, freq - (level - max_lv))
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
                    sp_r, hp_r, _ = simulate_cooking(player.WIS, player.skill, level)
                    player.restore_sp(sp_r)
                    if hp_r > 0:
                        player.healing_bank += hp_r
        elif result['fled']:
            combats_fled += 1
        elif player.hp <= 0:
            death_cause = 'starvation' if result['starv_dmg'] > 0 else 'combat'

    # Post-combat healing
    player.use_healing(max_hp_fraction=0.75)

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
        rest_heal = max(hp_per_level, int(player.max_hp * DEATH_ASCENT_REST_PCT))
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
    monsters, weapons, armor, shields, food, accessories, wands, ingr, recipes = load_data()
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

        for s in result['per_level']:
            lv    = s['level']
            phase = s['phase']

            if phase == 'descent':
                d_reached[lv]   += 1
                d_hp_lost[lv].append(s['hp_lost'])
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
        approx_max_hp = (20 + bstat['CON']) + hp_per_level * (lv - 1)
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
            approx_max = (20 + bstat['CON']) + hp_per_level * lv
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
