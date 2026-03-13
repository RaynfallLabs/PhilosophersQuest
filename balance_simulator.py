#!/usr/bin/env python3
"""
balance_simulator.py -- Monte Carlo balance analysis for Philosopher's Quest
Usage:
  python balance_simulator.py [--runs N] [--max-level N] [--seed N]
                               [--skill low|med|high] [--hp-per-level N]

Full 100-level run: descent L1->100, mandatory boss fights at L20/40/60/80/100,
collect the Philosopher's Stone, then ascend L99->1.

Model assumptions:
  - Gear: weighted random sampling from floorSpawnWeight zones (major fix)
  - Quiz: Bernoulli success parameterised by (tier, WIS, skill preset)
  - Combat: one CHAIN quiz per attack turn; monster retaliates if alive
  - THAC0: monster hits if d20 >= THAC0 - player_AC  (natural 1 always misses)
  - Armor equip: gated by geography THRESHOLD quiz using item's quiz_tier
  - Flee: player can flee when HP < 25% max (60% success rate)
  - HP scaling: player gains HP_PER_LEVEL max HP each dungeon level descended
  - Healing: food hp_restore + scrolls/wands accumulated and used between fights
  - SP: 25/level exploration + 2/combat turn; SP=0 -> 1 HP starvation/turn
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

HP_PER_LEVEL        = 5      # Max HP gained per dungeon level descended
                             # (matches player.py HP_PER_LEVEL = 5)
FLEE_THRESHOLD      = 0.25   # Attempt flee when HP < this fraction of max
FLEE_SUCCESS_RATE   = 0.60   # Probability of escaping successfully
HEAL_FIND_CHANCE    = 0.40   # Per-level chance of finding a healing item
HEAL_MIN            = 8      # Min HP from one healing item
HEAL_MAX            = 18     # Max HP from one healing item
SP_PER_COMBAT_TURN  = 2      # SP drained per round of combat
SP_EXPLORATION_PER_LEVEL = 25 # SP drained by floor exploration

# Armor equip threshold (from armor item's quiz_tier / equip_threshold)
# Default used when item fields are absent
DEFAULT_ARMOR_QUIZ_TIER  = 1
DEFAULT_EQUIP_REQUIRED   = 2
DEFAULT_EQUIP_TOTAL      = 3  # ceil(required * 1.5)

# Weapon find chance per level
WEAPON_FIND_CHANCE = 0.60
ARMOR_FIND_CHANCE  = 0.55

# Enchantment distribution when finding a weapon
ENCHANT_DIST = [(0, 0.80), (1, 0.12), (2, 0.08)]

# Bosses (freq=0 monsters placed at fixed milestone levels)
BOSS_LEVELS = {20: 'asterion_minotaur',
               40: 'medusa_gorgon',
               60: 'fafnir_dragon',
               80: 'fenrir_wolf',
               100: 'abaddon_destroyer'}

SKILL_BASE = {'low': 0.55, 'med': 0.70, 'high': 0.85}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def _load(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def load_data():
    monsters = _load(DATA / 'monsters.json')
    weapons  = _load(DATA / 'items' / 'weapon.json')
    armor    = _load(DATA / 'items' / 'armor.json')
    shields  = _load(DATA / 'items' / 'shield.json')
    food     = _load(DATA / 'items' / 'food.json')
    return monsters, weapons, armor, shields, food

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

def p_threshold(required: int, total_qs: int, p: float) -> float:
    """P(passing THRESHOLD quiz) = P(>= required correct out of total_qs)."""
    success = 0.0
    for k in range(required, total_qs + 1):
        binom = math.comb(total_qs, k)
        success += binom * (p ** k) * ((1 - p) ** (total_qs - k))
    return success

# ---------------------------------------------------------------------------
# Gear helpers -- weighted random sampling (major bug fix from v1)
# ---------------------------------------------------------------------------

def _spawn_weight(spawn_weights: dict, level: int) -> int:
    """Resolve a floorSpawnWeight dict (keys '1-20') at a given dungeon level."""
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
    """
    Pick a weapon using floorSpawnWeight zone probabilities.
    This correctly models that iron weapons dominate at L1-20 and
    adamantine weapons dominate at L81-100, rather than always returning
    the highest-base-damage item with any nonzero weight.
    """
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
            # No floorSpawnWeight: constant moderate weight past min_level
            wt = 10
        if wt > 0:
            pool.append(w)
            weights.append(wt)
    if not pool:
        return None
    return random.choices(pool, weights=weights, k=1)[0]

def weighted_armor_sample(armor: dict, level: int, slot: str) -> 'dict | None':
    """
    Pick an armor piece for the given slot, weighted by how recently
    it became available.  Newer gear (min_level close to current level)
    gets higher weight; very old gear (min_level << level) gets lower.
    """
    pool    = []
    weights = []
    for a in armor.values():
        if a.get('slot') != slot:
            continue
        ml = a.get('min_level', 1)
        if ml > level:
            continue
        age = level - ml          # how many levels ago this tier opened
        wt  = max(2, 100 - age)   # recent = weight ~100, very old = weight 2
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
    def __init__(self, skill: str = 'med', hp_per_level: int = HP_PER_LEVEL):
        self.skill        = skill
        self.hp_per_level = hp_per_level

        # Default stats (no secret build)
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10

        self.base_max_hp   = 20 + self.CON       # 30 at start
        self.max_hp        = self.base_max_hp
        self.hp            = self.max_hp
        self.max_sp        = 200 + self.CON       # 210
        self.sp            = self.max_sp

        # Descending AC: lower = better
        self._dex_ac       = (self.DEX - 10) // 2
        self.armor_ac      = 0   # sum of equipped armor + shield bonuses
        self.equipped_armor_per_slot: dict[str, int] = {}  # slot -> ac_bonus
        self.shield_ac     = 0

        # Healing bank: HP available from carried healing items
        self.healing_bank  = 0

        # Starting weapon: iron_dagger
        self.weapon_base_dmg  = 3
        self.weapon_enchant   = 0
        self.weapon_mults     = [0.3, 0.6, 1.0, 1.4, 1.8, 2.2, 2.5]
        self.weapon_max_chain = 7
        self.weapon_quiz_tier = 1
        self.weapon_dmg_types = ['pierce']
        self.weapon_name      = 'iron_dagger'

    @property
    def ac(self) -> int:
        return 10 - self._dex_ac - self.armor_ac

    def descend(self):
        """Called on each stair descent: gain HP_PER_LEVEL max HP + scaled stair-rest heal."""
        self.max_hp += self.hp_per_level
        # Stair-rest healing scales with max HP (5%) so deep-level players recover meaningfully.
        # At L1: ~2 HP; at L20: ~9 HP; at L60: ~25 HP; at L100: ~41 HP
        rest_heal = max(self.hp_per_level, int(self.max_hp * 0.05))
        self.hp   = min(self.hp + rest_heal, self.max_hp)

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
        """Use healing bank if HP < max_hp_fraction. Returns HP restored."""
        if self.healing_bank <= 0:
            return 0
        target = int(self.max_hp * max_hp_fraction)
        if self.hp >= target:
            return 0
        heal = min(self.healing_bank, target - self.hp)
        self.hp          += heal
        self.healing_bank -= heal
        return heal

    def is_starving(self) -> bool:
        return self.sp == 0

# ---------------------------------------------------------------------------
# Damage type resistance
# ---------------------------------------------------------------------------

def dtype_multiplier(weapon_types: list, monster: dict) -> float:
    """MAX multiplier across weapon types vs monster resistances/weaknesses."""
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
                    pre_fight_heal: bool = True) -> dict:
    """
    One player-vs-monster fight.
    Returns dict with: won, fled, hp_lost, turns, chains, starv_dmg
    """
    # Pre-fight healing when HP is critically low (40% threshold, not 70%)
    # Lower threshold preserves the healing bank for emergencies and boss pre-heals
    if pre_fight_heal:
        player.use_healing(max_hp_fraction=0.40)

    m_hp   = roll_dice(str(monster.get('hp', '1d6')))
    p_cor  = p_correct(player.weapon_quiz_tier, player.WIS, player.skill)
    dmult  = dtype_multiplier(player.weapon_dmg_types, monster)

    thac0       = monster.get('thac0', 20)
    roll_needed = max(2, thac0 - player.ac)
    hit_chance  = max(0.0, min(1.0, (21 - roll_needed) / 20.0))

    chains           = []
    player_hp_before = player.hp
    turns            = 0
    starvation_dmg   = 0
    fled             = False

    while m_hp > 0 and player.hp > 0:
        turns += 1
        player.drain_sp(SP_PER_COMBAT_TURN)

        # Starvation: 1 HP/turn at SP=0
        if player.is_starving():
            player.hp -= 1
            starvation_dmg += 1
            if player.hp <= 0:
                break

        # Flee check when HP critically low
        if allow_flee and player.hp < player.max_hp * FLEE_THRESHOLD:
            if random.random() < FLEE_SUCCESS_RATE:
                fled = True
                break
            # Failed flee: still fight this turn

        # --- Player attacks ---
        chain = roll_chain(p_cor, player.weapon_max_chain)
        chains.append(chain)
        if chain > 0:
            idx  = min(chain - 1, len(player.weapon_mults) - 1)
            mult = player.weapon_mults[idx]
            raw  = player.weapon_base_dmg + player.weapon_enchant
            dmg  = max(1, int(raw * mult * dmult))
            m_hp -= dmg

        if m_hp <= 0:
            break

        # --- Monster retaliates ---
        if random.random() < hit_chance:
            attacks = monster.get('attacks', [{'damage': '1d4'}])
            for atk in attacks:
                player.hp -= roll_dice(str(atk.get('damage', '1d4')))

    won = m_hp <= 0 and not fled
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
                   food: dict,
                   is_boss_level: bool = False,
                   boss_id: str = '',
                   monster_scale: float = 1.0,
                   boss_hp_scale: float = 1.0) -> dict:
    """
    Simulate one dungeon level (either descent or ascent).
    Order: gear upgrades -> food/healing finds -> exploration drain -> combat
    """

    # --- Weapon upgrade (weighted sampling) ---
    if random.random() < WEAPON_FIND_CHANCE:
        w = weighted_weapon_sample(weapons, level)
        if w:
            player.upgrade_weapon(w, enchant=_roll_enchant())

    # --- Armor upgrades (per slot, gated by geography quiz) ---
    geo_p = p_correct(DEFAULT_ARMOR_QUIZ_TIER, player.WIS, player.skill)
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

    # --- Food & healing items ---
    # Food: 1-3 SP-restoring items; some also have hp_restore
    spawnable_food = [f for f in food.values() if f.get('min_level', 1) <= level]
    if spawnable_food:
        n_food = random.randint(1, 3)
        for _ in range(n_food):
            f = random.choice(spawnable_food)
            # SP restore
            if player.sp < player.max_sp * 0.80:
                player.restore_sp(f.get('sp_restore', 20))
            # HP restore goes to healing bank
            hp_r = f.get('hp_restore', 0)
            if hp_r > 0:
                player.healing_bank += hp_r

    # Healing items (scrolls/wands with healing effects): modeled as HP bank
    if random.random() < HEAL_FIND_CHANCE:
        heal_amt = random.randint(HEAL_MIN, HEAL_MAX)
        player.healing_bank += heal_amt

    # --- Exploration SP drain ---
    player.drain_sp(SP_EXPLORATION_PER_LEVEL)

    # --- Boss fight (mandatory) ---
    if is_boss_level and boss_id and boss_id in monsters:
        boss = dict(monsters[boss_id])  # copy so we can scale HP
        # Scale boss HP if boss_hp_scale != 1.0
        if boss_hp_scale != 1.0:
            raw_hp = avg_dice(str(boss.get('hp', 10)))
            scaled = max(1, int(raw_hp * boss_hp_scale))
            boss['hp'] = scaled
        # Use all available healing before boss fight
        player.use_healing(max_hp_fraction=1.0)
        result = simulate_combat(player, boss, allow_flee=False, pre_fight_heal=False)
        chains = result['chains']
        return {
            'combats':    1,
            'won':        1 if result['won'] else 0,
            'fled':       0,
            'boss_killed': result['won'],
            'hp_lost':    result['hp_lost'],
            'sp_drained': 0,
            'death':      None if (player.hp > 0) else
                          ('starvation' if result['starv_dmg'] > 0 else 'combat'),
            'chains':     chains,
            'starv_dmg':  result['starv_dmg'],
        }

    # --- Regular monster encounters ---
    # Formula matches updated dungeon.py; monster_scale can tune further
    min_m = int(min(2 + level // 15, 7)  * monster_scale)
    max_m = int(min(3 + level // 8,  11) * monster_scale)
    min_m = max(1, min_m)
    max_m = max(min_m, max_m)
    n_monsters = random.randint(min_m, max_m)

    # Build spawn pool (exclude freq=0 bosses)
    pool = []
    for mid, m in monsters.items():
        freq = m.get('frequency', 5)
        if freq == 0:
            continue
        if m.get('min_level', 1) > level:
            continue
        max_lv = m.get('max_level')
        if max_lv and level > max_lv:
            freq = max(1, freq - (level - max_lv))
        pool.extend([mid] * freq)

    if not pool:
        return {'combats': 0, 'won': 0, 'fled': 0, 'boss_killed': False,
                'hp_lost': 0, 'sp_drained': 0, 'death': None,
                'chains': [], 'starv_dmg': 0}

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
    }

# ---------------------------------------------------------------------------
# Full run (two-phase: descent + ascent)
# ---------------------------------------------------------------------------

def simulate_run(max_level: int, monsters: dict, weapons: dict,
                 armor: dict, shields: dict, food: dict,
                 skill: str = 'med',
                 hp_per_level: int = HP_PER_LEVEL,
                 monster_scale: float = 1.0,
                 boss_hp_scale: float = 1.0) -> dict:
    """
    Simulate a complete run:
      Phase 1: Descend L1 -> max_level, fight bosses at milestone levels
      Phase 2: Ascend L(max_level-1) -> 1 after defeating the final boss
    Returns per-level stats for both phases.
    """
    player  = SimPlayer(skill=skill, hp_per_level=hp_per_level)
    per_lv  = []
    died_on = None
    death_cause = None

    # -- Phase 1: Descent --
    for lv in range(1, max_level + 1):
        is_boss = lv in BOSS_LEVELS and lv <= max_level
        boss_id = BOSS_LEVELS.get(lv, '')

        stats = simulate_level(player, lv, monsters, weapons, armor, shields,
                               food, is_boss_level=is_boss, boss_id=boss_id,
                               monster_scale=monster_scale,
                               boss_hp_scale=boss_hp_scale)
        player.descend()
        stats['level']        = lv
        stats['phase']        = 'descent'
        stats['hp_remaining'] = player.hp
        stats['sp_remaining'] = player.sp
        stats['player_max_hp']= player.max_hp
        per_lv.append(stats)

        if stats['death'] or player.hp <= 0:
            died_on     = lv
            death_cause = stats['death'] or (
                'starvation' if player.sp == 0 else 'combat')
            return {
                'survived': False,
                'died_on':  died_on,
                'phase':    'descent',
                'death_cause': death_cause,
                'per_level':   per_lv,
            }

        # Boss at this level must be killed to continue
        if is_boss and not stats.get('boss_killed'):
            died_on     = lv
            death_cause = 'boss'
            per_lv[-1]['death'] = 'boss'
            return {
                'survived': False,
                'died_on':  died_on,
                'phase':    'descent',
                'death_cause': death_cause,
                'per_level':   per_lv,
            }

    # -- Phase 2: Ascent (L99 -> L1 after collecting Philosopher's Stone) --
    for lv in range(max_level - 1, 0, -1):
        stats = simulate_level(player, lv, monsters, weapons, armor, shields,
                               food, is_boss_level=False,
                               monster_scale=monster_scale)
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
            return {
                'survived': False,
                'died_on':  died_on,
                'phase':    'ascent',
                'death_cause': death_cause,
                'per_level':   per_lv,
            }

    return {
        'survived':    True,
        'died_on':     None,
        'phase':       'complete',
        'death_cause': None,
        'per_level':   per_lv,
    }

# ---------------------------------------------------------------------------
# Aggregation + report
# ---------------------------------------------------------------------------

def run_simulation(runs: int, max_level: int, seed: int, skill: str,
                   hp_per_level: int = HP_PER_LEVEL,
                   monster_scale: float = 1.0,
                   boss_hp_scale: float = 1.0):
    random.seed(seed)
    monsters, weapons, armor, shields, food = load_data()

    # --- Accumulators ---
    # Per descent-level stats
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
    d_boss_kill    = defaultdict(int)   # boss kill rate per boss level
    d_boss_attempt = defaultdict(int)

    # Per ascent-level stats (keyed by level, but phase='ascent')
    a_reached = defaultdict(int)
    a_died    = defaultdict(int)
    a_death_cause = defaultdict(lambda: defaultdict(int))
    a_hp_lost = defaultdict(list)

    total_survived = 0
    died_descent   = 0
    died_ascent    = 0

    for _ in range(runs):
        result = simulate_run(max_level, monsters, weapons, armor, shields,
                              food, skill=skill, hp_per_level=hp_per_level,
                              monster_scale=monster_scale,
                              boss_hp_scale=boss_hp_scale)
        if result['survived']:
            total_survived += 1

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
    W = 90
    print('=' * W)
    print('  Philosopher\'s Quest -- Balance Simulation (Full 100-Level Run)')
    print(f'  {runs} runs | max_level {max_level} | seed {seed} | skill={skill} | HP+{hp_per_level}/lv | monster_scale={monster_scale:.2f} | boss_hp_scale={boss_hp_scale:.2f}')
    print(f'  Quiz: p = {SKILL_BASE[skill]:.2f} - (tier-1)*0.06 + (WIS-10)*0.015  |  flee at {FLEE_THRESHOLD*100:.0f}% HP ({FLEE_SUCCESS_RATE*100:.0f}% success)')
    print(f'  Gear: weapon={WEAPON_FIND_CHANCE*100:.0f}%/lv (weighted zone), armor={ARMOR_FIND_CHANCE*100:.0f}%/slot/lv (weighted tier)')
    print(f'  Heal: {HEAL_FIND_CHANCE*100:.0f}% find/lv, {HEAL_MIN}-{HEAL_MAX} HP/item | SP: {SP_EXPLORATION_PER_LEVEL}/lv + {SP_PER_COMBAT_TURN}/turn')
    print(f'  Bosses: ' + '  '.join(f'L{lv}={bid}' for lv, bid in BOSS_LEVELS.items() if lv <= max_level))
    print('=' * W)

    red_flags = []

    # -- Descent table (grouped by 10-level bands if max_level is large) --
    print(f'\n--- DESCENT ---')
    step = 10 if max_level >= 50 else 1
    print(f'{"LV":<5} {"REACHED":>7} {"DIED":>6} {"SURV%":>7} {"HP_LOST":>10} {"SP_LEFT":>8} {"WIN%":>7} {"FLEE%":>7} {"CHAIN":>7}  NOTE')
    print('-' * W)

    for lv in range(1, max_level + 1):
        reached = d_reached.get(lv, 0)
        if reached == 0:
            break
        died     = d_died.get(lv, 0)
        surv_pct = 100.0 * (reached - died) / reached
        avg_hl   = sum(d_hp_lost[lv]) / len(d_hp_lost[lv])
        # HP lost as % of CURRENT max_hp (which grows with HP_PER_LEVEL)
        # Approximate max_hp at this level:
        approx_max_hp = 30 + hp_per_level * (lv - 1)  # rough estimate
        hp_pct   = 100.0 * avg_hl / max(1, approx_max_hp)
        avg_sp   = sum(d_sp_rem[lv]) / len(d_sp_rem[lv])
        win_pct  = 100.0 * d_won[lv] / max(1, d_combats[lv])
        flee_pct = 100.0 * d_fled[lv] / max(1, d_combats[lv])
        clist    = d_chains[lv]
        avg_ch   = sum(clist) / max(1, len(clist))

        notes = []
        if hp_pct > 70 and lv > 5:
            notes.append('HIGH_DMG')
            red_flags.append(f'L{lv} descent: avg HP lost {avg_hl:.1f} ({hp_pct:.0f}% of ~{approx_max_hp}) -> too punishing')
        if surv_pct < 70 and lv <= 10:
            notes.append('LETHAL')
            red_flags.append(f'L{lv}: survival {surv_pct:.1f}% in first 10 levels -> too hard early')
        if win_pct < 40:
            notes.append('LOW_WIN')
            red_flags.append(f'L{lv}: combat win rate {win_pct:.1f}% -> monsters too strong')
        if lv in BOSS_LEVELS and lv <= max_level:
            bkill = d_boss_kill.get(lv, 0)
            batmp = d_boss_attempt.get(lv, 1)
            bpct  = 100.0 * bkill / max(1, batmp)
            notes.append(f'BOSS:{bpct:.0f}%')
            if bpct < 20:
                red_flags.append(f'L{lv} boss kill rate {bpct:.1f}% -> boss too strong')

        note_str = ' '.join(f'[{n}]' for n in notes)
        if step == 1 or (lv % step == 0) or (lv <= 5) or (lv in BOSS_LEVELS) or died > 0:
            print(f'{lv:<5} {reached:>7} {died:>6} {surv_pct:>6.1f}% {avg_hl:>8.1f}({hp_pct:>3.0f}%) {avg_sp:>7.0f} {win_pct:>6.1f}% {flee_pct:>6.1f}% {avg_ch:>6.2f}  {note_str}')

    print('-' * W)

    # -- Ascent table (condensed) --
    ascent_any = sum(1 for v in a_reached.values() if v > 0)
    if ascent_any:
        print(f'\n--- ASCENT (after collecting Philosopher\'s Stone) ---')
        print(f'{"LV":<5} {"REACHED":>7} {"DIED":>6} {"SURV%":>7} {"HP_LOST":>10}')
        print('-' * 40)
        # Show only levels where deaths occur or every 10
        for lv in sorted(a_reached.keys(), reverse=True):
            reached = a_reached[lv]
            if reached == 0:
                continue
            died    = a_died.get(lv, 0)
            surv    = 100.0 * (reached - died) / reached
            avg_hl  = sum(a_hp_lost[lv]) / len(a_hp_lost[lv]) if a_hp_lost[lv] else 0
            approx_max = 30 + hp_per_level * lv  # descending, player at ~Lmax HP
            hp_pct  = 100.0 * avg_hl / max(1, approx_max)
            if died > 0 or lv % 10 == 0 or lv <= 5:
                print(f'{lv:<5} {reached:>7} {died:>6} {surv:>6.1f}% {avg_hl:>8.1f}({hp_pct:>3.0f}%)')
        print('-' * 40)

    # -- Overall survival --
    print(f'\n{"="*W}')
    print(f'OVERALL RESULTS ({skill} skill, HP+{hp_per_level}/level):')
    print(f'  Full run completions : {total_survived}/{runs} ({100*total_survived/runs:.1f}%)')
    print(f'  Died on descent      : {died_descent}/{runs} ({100*died_descent/runs:.1f}%)')
    print(f'  Died on ascent       : {died_ascent}/{runs} ({100*died_ascent/runs:.1f}%)')

    # Death distribution
    print(f'\nDEATH DISTRIBUTION (descent):')
    all_deaths = {lv: d_died[lv] for lv in sorted(d_died.keys()) if d_died[lv] > 0}
    total_d = sum(all_deaths.values())
    if total_d:
        for lv, cnt in all_deaths.items():
            pct   = 100.0 * cnt / total_d
            bar   = '#' * int(pct / 2)
            causes = '  '.join(f'{c}={n}' for c, n in sorted(d_death_cause[lv].items()))
            print(f'  L{lv:>3}: {cnt:>5} ({pct:>5.1f}%)  {bar:<20}  [{causes}]')

    # Gear ceiling
    print(f'\nGEAR CEILING (theoretical max per tier, not average find):')
    sample_levels = [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    sample_levels = [lv for lv in sample_levels if lv <= max_level]
    print(f'  {"LV":<5} {"BEST WEAPON":30} {"base":>5} {"tier":>5} {"TOTAL_AC":>9}')
    for lv in sample_levels:
        w  = best_weapon_at_level(weapons, lv)
        ac = best_armor_ac_at_level(armor, shields, lv)
        if w:
            name  = w.get('name', '?')[:28]
            bd    = w.get('baseDamage', '?')
            tier  = w.get('mathTier', '?')
            print(f'  {lv:<5} {name:<30} {str(bd):>5} {str(tier):>5} {"AC+"+str(ac):>9}')

    # Chain table for current weapon tier
    p_base = p_correct(1, 10, skill)
    print(f'\nCHAIN TABLE (iron_dagger @ L1, p={p_base:.2f}):')
    base_mults = [0.3, 0.6, 1.0, 1.4, 1.8, 2.2, 2.5]
    base_dmg   = 3
    print(f'  {"CHAIN":>6} {"P":>8} {"DMG":>12} {"E[dmg]":>8}')
    for k in range(len(base_mults) + 1):
        if k == 0:
            prob = 1 - p_base
            print(f'  {k:>6} {prob:>8.4f} {"miss":>12} {"0.00":>8}')
        else:
            prob = (p_base ** k) * (1 - p_base) if k < len(base_mults) else p_base ** len(base_mults)
            m    = base_mults[k - 1]
            dmg  = max(1, int(base_dmg * m))
            print(f'  {k:>6} {prob:>8.4f} {f"{base_dmg} x {m:.1f} = {dmg}":>12} {prob*dmg:>8.2f}')

    p_deep = p_correct(5, 10, skill)
    print(f'\nCHAIN TABLE (adamantine_zweihander @ L90, base=32, p={p_deep:.2f}):')
    deep_mults = [0.5, 1.0, 1.8, 2.5, 3.2, 4.0, 4.8, 5.5]
    for k in range(7):
        if k == 0:
            prob = 1 - p_deep
            print(f'  {k:>6} {prob:>8.4f} {"miss":>14} {"0.00":>8}')
        else:
            prob = (p_deep ** k) * (1 - p_deep) if k < 6 else p_deep ** 6
            m    = deep_mults[k - 1]
            dmg  = max(1, int(32 * m))
            print(f'  {k:>6} {prob:>8.4f} {f"32 x {m:.1f} = {dmg}":>14} {prob*dmg:>8.2f}')

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
            print(f'  L{lv:>3} {bname:30s} attempts={batmp:>5} kills={bkill:>5} ({bpct:>5.1f}%)')

    # Red flags
    if red_flags:
        print(f'\nRED FLAGS:')
        seen = set()
        for f in red_flags:
            if f not in seen:
                print(f'  [!] {f}')
                seen.add(f)
    else:
        print(f'\n[OK] No critical flags at skill={skill}.')

    print('=' * W)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description='Philosopher\'s Quest balance simulator -- full 100-level run')
    ap.add_argument('--runs',         type=int, default=500,
                    help='Simulation runs (default 500)')
    ap.add_argument('--max-level',    type=int, default=100,
                    help='Deepest level to simulate (default 100)')
    ap.add_argument('--seed',         type=int, default=42,
                    help='RNG seed (default 42)')
    ap.add_argument('--skill',        type=str, default='med',
                    choices=['low', 'med', 'high'],
                    help='Player skill preset (default med)')
    ap.add_argument('--hp-per-level',    type=int,   default=HP_PER_LEVEL,
                    help=f'Max HP gained per dungeon level (default {HP_PER_LEVEL})')
    ap.add_argument('--monster-scale',   type=float, default=1.0,
                    help='Scale monster count per level (0.7 = 30 pct fewer, default 1.0)')
    ap.add_argument('--boss-hp-scale',   type=float, default=1.0,
                    help='Scale boss HP (0.5 = halve boss HP, default 1.0)')
    args = ap.parse_args()
    run_simulation(args.runs, args.max_level, args.seed,
                   args.skill, args.hp_per_level,
                   args.monster_scale, args.boss_hp_scale)

if __name__ == '__main__':
    main()
