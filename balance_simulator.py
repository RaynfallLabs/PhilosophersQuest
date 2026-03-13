#!/usr/bin/env python3
"""
balance_simulator.py -- Monte Carlo balance analysis for Philosopher's Quest
Usage: python balance_simulator.py [--runs N] [--max-level N] [--seed N] [--skill low|med|high]

Model assumptions (all documented at point of use):
  - Quiz: Bernoulli success per question, parameterised by (tier, WIS, skill preset)
  - Combat: one CHAIN quiz per attack turn; monster retaliates if alive after player swing
  - THAC0: monster hits if d20 >= THAC0 - player_AC  (natural 1 always misses)
  - Armor equip: blocked by a geography THRESHOLD quiz; failing leaves armor unequipped
  - Gear: player finds best-available item each level with FIND_CHANCE probability
  - Enchant: weapons +0/+1/+2 on find (80/12/8%); armor cursed with -1/-2 on find (10%)
  - SP: drained per combat turn + base exploration cost; food items restore SP; SP=0 -> starvation
  - Flee: not modelled; fights to the death
  - Scrolls/wands/potions: not modelled (they improve survival beyond what we report here)
"""

import json, math, random, argparse
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / 'data'

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
# Dice helpers -- support NdX, NdX+M, NdX-M
# ---------------------------------------------------------------------------

def _parse_dice(notation: str) -> float:
    """Return expected value of a dice expression."""
    notation = str(notation).lower().replace(' ', '')
    # Split on + but preserve leading minus via a small trick
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
        return 2.5  # safe fallback

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
# Base accuracy by skill preset:
#   low  = 0.55  (struggling player, gets questions wrong under time pressure)
#   med  = 0.70  (competent player -- the default)
#   high = 0.85  (strong academic, fast recall)
# Per-tier penalty: each tier above 1 reduces p by 0.06 (harder questions).
# WIS bonus: +0.015 per WIS point above 10 (more seconds on timer = calmer answers).
# All clamped to [0.30, 0.94].

SKILL_BASE = {'low': 0.55, 'med': 0.70, 'high': 0.85}

def p_correct(tier: int, wis: int, skill: str = 'med') -> float:
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
    """
    P(passing a THRESHOLD quiz) = P(>= required correct out of total_qs).
    Uses binomial CDF.  Used for armor/accessory equip and armor-equip barrier.
    """
    # Sum P(exactly k correct) for k in [required, total_qs]
    success = 0.0
    for k in range(required, total_qs + 1):
        binom = math.comb(total_qs, k)
        success += binom * (p ** k) * ((1 - p) ** (total_qs - k))
    return success

# ---------------------------------------------------------------------------
# Monster spawn pool (exact mirror of dungeon.py logic)
# ---------------------------------------------------------------------------

def build_monster_pool(monsters: dict, level: int) -> list:
    """Frequency-weighted list of monster IDs eligible at this level."""
    pool = []
    for mid, m in monsters.items():
        freq = m.get('frequency', 5)
        if freq == 0:
            continue                     # boss-only monsters
        if m.get('min_level', 1) > level:
            continue
        max_lv = m.get('max_level')
        if max_lv and level > max_lv:
            freq = max(1, freq - (level - max_lv))   # decay past max_level
        pool.extend([mid] * freq)
    return pool

# ---------------------------------------------------------------------------
# Item-pool helpers
# ---------------------------------------------------------------------------

def _spawn_weight(spawn_weights: dict, level: int) -> int:
    """Resolve a floor_spawn_weight dict (keys like '1-20') at a given level."""
    for key, w in spawn_weights.items():
        parts = str(key).split('-')
        if len(parts) == 2:
            try:
                if int(parts[0]) <= level <= int(parts[1]):
                    return w
            except ValueError:
                pass
    return 0

def _is_spawnable(item: dict, level: int) -> bool:
    if item.get('min_level', 1) > level:
        return False
    sw = item.get('floorSpawnWeight') or item.get('floor_spawn_weight') or {}
    if sw and _spawn_weight(sw, level) == 0:
        return False
    return True

def best_weapon_at_level(weapons: dict, level: int) -> dict | None:
    """Highest-baseDamage weapon spawnable at this level."""
    best = None
    for w in weapons.values():
        if not _is_spawnable(w, level):
            continue
        if best is None or w.get('baseDamage', 0) > best.get('baseDamage', 0):
            best = w
    return best

def best_armor_ac_per_slot(armor: dict, shields: dict, level: int) -> int:
    """
    Sum the best AC bonus across ALL 8 armor slots + shield.
    Mirrors actual player: head, body, arms, hands, legs, feet, cloak, shirt.
    Previously only counted 'body' -- fixed to sum all slots.
    """
    best_per_slot: dict[str, int] = {}
    for a in armor.values():
        if not _is_spawnable(a, level):
            continue
        slot = a.get('slot', 'body')
        ac   = a.get('ac_bonus', 0)
        if ac > best_per_slot.get(slot, 0):
            best_per_slot[slot] = ac

    shield_ac = max((s.get('ac_bonus', 0) for s in shields.values()
                     if _is_spawnable(s, level)), default=0)
    return sum(best_per_slot.values()) + shield_ac

def food_sp_pool(food: dict, level: int) -> list[int]:
    """Return SP-restore values of food items spawnable at this level."""
    result = []
    for f in food.values():
        if _is_spawnable(f, level):
            result.append(f.get('sp_restore', 20))
    return result or [20]

# ---------------------------------------------------------------------------
# Player model
# ---------------------------------------------------------------------------
# Stats mirror src/player.py constants:
#   BASE_HP = 20,  BASE_SP = 200  (both add CON)
#   AC = 10 - floor((DEX-10)/2) - armor_bonus - shield_bonus
#   Quiz timer base = 10s + WIS points (WIS affects p_correct directly here)

class SimPlayer:
    def __init__(self, skill: str = 'med'):
        self.skill = skill
        # Base stats (all 10 -- default build, no secret build)
        self.STR = self.CON = self.DEX = self.INT = self.WIS = self.PER = 10

        self.max_hp = 20 + self.CON          # 30 HP  (src/player.py BASE_HP + CON)
        self.hp     = self.max_hp
        self.max_sp = 200 + self.CON         # 210 SP (src/player.py BASE_SP + CON)
        self.sp     = self.max_sp

        # Base AC before armor (descending: lower = better)
        self._base_ac    = 10 - (self.DEX - 10) // 2   # = 10
        self.armor_ac    = 0     # sum of all equipped armor + shield AC
        self.weapon_enchant = 0  # enchantment bonus on weapon

        # Starting weapon: iron_dagger (loaded from weapon.json)
        # Actual JSON values: baseDamage=3, chainMultipliers=[0.3,0.6,1.0,1.4,1.8,2.2,2.5]
        # maxChainLength=7, mathTier=1
        self.weapon_base_dmg  = 3
        self.weapon_mults     = [0.3, 0.6, 1.0, 1.4, 1.8, 2.2, 2.5]
        self.weapon_max_chain = 7
        self.weapon_quiz_tier = 1            # mathTier from JSON
        self.weapon_dmg_types = ['pierce']   # iron_dagger damage types

    @property
    def ac(self) -> int:
        return self._base_ac - self.armor_ac

    def upgrade_weapon(self, w: dict, enchant: int = 0):
        """
        Replace weapon if new one has higher effective base damage.
        Field name note: JSON uses 'mathTier' (camelCase), not 'quiz_tier'.
        """
        new_base = w.get('baseDamage', 0)
        if new_base + enchant > self.weapon_base_dmg + self.weapon_enchant:
            self.weapon_base_dmg  = new_base
            self.weapon_enchant   = enchant
            # chainMultipliers is camelCase in JSON -- matches items.py
            self.weapon_mults     = w.get('chainMultipliers', self.weapon_mults)
            self.weapon_max_chain = w.get('maxChainLength', len(self.weapon_mults))
            # JSON uses 'mathTier'; items.py does the same dual-key lookup
            self.weapon_quiz_tier = w.get('mathTier', w.get('quiz_tier', 1))
            self.weapon_dmg_types = w.get('damageTypes', ['slash'])

    def upgrade_armor(self, bonus: int):
        if bonus > self.armor_ac:
            self.armor_ac = bonus

    def drain_sp(self, amount: int):
        self.sp = max(0, self.sp - amount)

    def restore_sp(self, amount: int):
        self.sp = min(self.max_sp, self.sp + amount)

    def is_starving(self) -> bool:
        return self.sp == 0

# ---------------------------------------------------------------------------
# Damage type resistance helper
# ---------------------------------------------------------------------------

def dtype_multiplier(weapon_types: list, monster: dict) -> float:
    """
    Mirrors combat.py _damage_multiplier: take the MAX multiplier across
    all weapon damage types vs monster's resistances/weaknesses.
    Returns 0.5 (resist), 1.0 (neutral), or 1.5 (weakness).
    """
    resistances = set(monster.get('resistances', []))
    weaknesses  = set(monster.get('weaknesses',  []))
    best = 1.0
    for dt in weapon_types:
        if dt in weaknesses:
            best = max(best, 1.5)
        elif dt in resistances:
            best = min(best, 0.5) if best == 1.0 else best
    return best

# ---------------------------------------------------------------------------
# Single combat
# ---------------------------------------------------------------------------

# SP cost per combat turn (player moves, swings, receives hits)
SP_PER_COMBAT_TURN = 2

def simulate_combat(player: SimPlayer, monster: dict) -> dict:
    """
    One player-vs-monster fight.
    - Player attacks: CHAIN quiz -> chain length -> damage
    - Enchant bonus added to base before multiplier (mirrors combat.py line 75)
    - Monster retaliates each turn it survives
    - SP drains SP_PER_COMBAT_TURN per round; SP=0 adds 1 starvation dmg/turn
    - Damage types checked vs monster resistances/weaknesses
    """
    m_hp   = roll_dice(str(monster.get('hp', '1d6')))
    p_cor  = p_correct(player.weapon_quiz_tier, player.WIS, player.skill)
    dmult  = dtype_multiplier(player.weapon_dmg_types, monster)

    # THAC0 system: monster hits if d20 >= THAC0 - player_AC; nat-1 always misses
    thac0       = monster.get('thac0', 20)
    roll_needed = max(2, thac0 - player.ac)
    hit_chance  = max(0.0, min(1.0, (21 - roll_needed) / 20.0))

    chains           = []
    player_hp_before = player.hp
    turns            = 0
    starvation_dmg   = 0

    while m_hp > 0 and player.hp > 0:
        turns += 1
        player.drain_sp(SP_PER_COMBAT_TURN)

        # Starvation: 1 HP/turn at SP=0 (src/main.py _tick_sp)
        if player.is_starving():
            player.hp -= 1
            starvation_dmg += 1
            if player.hp <= 0:
                break

        # --- Player attacks (one CHAIN quiz = one attack turn) ---
        chain = roll_chain(p_cor, player.weapon_max_chain)
        chains.append(chain)
        if chain > 0:
            idx  = min(chain - 1, len(player.weapon_mults) - 1)
            mult = player.weapon_mults[idx]
            # Enchant adds to base BEFORE multiplier, matching combat.py
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

    won = m_hp <= 0
    return {
        'won':          won,
        'hp_lost':      max(0, player_hp_before - player.hp),
        'turns':        turns,
        'chains':       chains,
        'starv_dmg':    starvation_dmg,
    }

# ---------------------------------------------------------------------------
# Single level simulation
# ---------------------------------------------------------------------------

# Base exploration SP cost per level (movement before/between fights)
SP_EXPLORATION_PER_LEVEL = 25

# Geography threshold quiz barrier to equip armor (mirrors game requirement).
# default armor equip_threshold=2, total_qs=ceil(2*1.5)=3, quiz_tier=1
ARMOR_EQUIP_REQUIRED = 2
ARMOR_EQUIP_TOTAL    = 3   # ceil(required * 1.5)
ARMOR_QUIZ_TIER      = 1   # geography tier 1 for early armor

# Weapon/armor find chance per level (not every level has ideal loot)
FIND_CHANCE = 0.55

# Enchantment distribution when finding a weapon (+0 most common)
# Mirrors dungeon.py which can yield enchanted weapons from containers/drops
ENCHANT_DIST = [(0, 0.80), (1, 0.12), (2, 0.08)]

def roll_enchant() -> int:
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
                   food: dict) -> dict:
    """
    Simulate one dungeon level.
    Order: gear upgrade -> food spawn/eat -> combat loop -> starvation check.
    """
    # --- Weapon upgrade ---
    if random.random() < FIND_CHANCE:
        w = best_weapon_at_level(weapons, level)
        if w:
            player.upgrade_weapon(w, enchant=roll_enchant())

    # --- Armor upgrade (gated by geography quiz) ---
    if random.random() < FIND_CHANCE:
        geo_p    = p_correct(ARMOR_QUIZ_TIER, player.WIS, player.skill)
        can_equip = random.random() < p_threshold(ARMOR_EQUIP_REQUIRED,
                                                   ARMOR_EQUIP_TOTAL, geo_p)
        if can_equip:
            bonus = best_armor_ac_per_slot(armor, shields, level)
            player.upgrade_armor(bonus)
        # If quiz fails: player carries but does not benefit from the armor

    # --- Food spawn (1-3 items per level; mirrors dungeon.py spawn_items) ---
    sp_pool  = food_sp_pool(food, level)
    n_food   = random.randint(1, 3)
    food_sp  = sum(random.choice(sp_pool) for _ in range(n_food))
    # Player eats all food found immediately when SP < 80% (hungry/starving)
    if player.sp < player.max_sp * 0.80:
        player.restore_sp(food_sp)

    # --- Exploration SP drain (moving through the floor before/between fights) ---
    player.drain_sp(SP_EXPLORATION_PER_LEVEL)

    # --- Combat encounters ---
    # Monster count from dungeon.py spawn_monsters (fixed from original simulator)
    min_m = min(3 + level // 10, 10)
    max_m = min(5 + level // 5, 15)
    n_monsters = random.randint(min_m, max_m)

    pool = build_monster_pool(monsters, level)
    if not pool:
        return {'combats': 0, 'hp_lost': 0, 'sp_drained': 0,
                'death': None, 'won': 0, 'chains': [], 'starv_dmg': 0}

    combats_won  = 0
    total_hp_lost = 0
    all_chains   = []
    total_starv  = 0
    death_cause  = None

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
        elif player.hp <= 0:
            death_cause = 'starvation' if result['starv_dmg'] > 0 else 'combat'

    # Eat any remaining food after combat if still hungry
    if player.sp < player.max_sp * 0.80 and player.hp > 0:
        player.restore_sp(food_sp // 2)

    return {
        'combats':    n_monsters,
        'won':        combats_won,
        'hp_lost':    total_hp_lost,
        'sp_drained': SP_EXPLORATION_PER_LEVEL + total_starv * SP_PER_COMBAT_TURN,
        'death':      death_cause,
        'chains':     all_chains,
        'starv_dmg':  total_starv,
    }

# ---------------------------------------------------------------------------
# Full run
# ---------------------------------------------------------------------------

def simulate_run(max_level: int, monsters: dict, weapons: dict,
                 armor: dict, shields: dict, food: dict,
                 skill: str = 'med') -> dict:
    player  = SimPlayer(skill=skill)
    per_lv  = []
    died_on = None
    death_cause = None

    for lv in range(1, max_level + 1):
        stats = simulate_level(player, lv, monsters, weapons, armor, shields, food)
        stats['level']        = lv
        stats['hp_remaining'] = player.hp
        stats['sp_remaining'] = player.sp
        per_lv.append(stats)

        if stats['death'] or player.hp <= 0:
            died_on     = lv
            death_cause = stats['death'] or ('starvation' if player.sp == 0 else 'combat')
            break

    return {
        'survived':    died_on is None,
        'died_on':     died_on,
        'death_cause': death_cause,
        'per_level':   per_lv,
    }

# ---------------------------------------------------------------------------
# Aggregation + report
# ---------------------------------------------------------------------------

def run_simulation(runs: int, max_level: int, seed: int, skill: str):
    random.seed(seed)
    monsters, weapons, armor, shields, food = load_data()

    dummy = SimPlayer()
    start_hp = dummy.max_hp
    start_sp = dummy.max_sp

    survived_to    = defaultdict(int)
    deaths_on      = defaultdict(int)
    death_cause    = defaultdict(lambda: defaultdict(int))  # lv -> cause -> count
    hp_lost_lv     = defaultdict(list)
    sp_remaining_lv = defaultdict(list)   # actual SP left at end of level
    chains_lv      = defaultdict(list)
    combats_won    = defaultdict(int)
    combats_total  = defaultdict(int)
    starv_dmg_lv   = defaultdict(list)
    total_survived = 0

    for _ in range(runs):
        result = simulate_run(max_level, monsters, weapons, armor, shields,
                              food, skill=skill)
        if result['survived']:
            total_survived += 1

        for s in result['per_level']:
            lv = s['level']
            survived_to[lv]        += 1
            hp_lost_lv[lv].append(s['hp_lost'])
            sp_remaining_lv[lv].append(s['sp_remaining'])
            chains_lv[lv].extend(s['chains'])
            combats_won[lv]        += s['won']
            combats_total[lv]      += s['combats']
            starv_dmg_lv[lv].append(s['starv_dmg'])
            if s['death']:
                deaths_on[lv] += 1
                death_cause[lv][s['death']] += 1

    # ---- Report ---------------------------------------------------------------
    W = 80
    print('=' * W)
    print('  Philosopher\'s Quest -- Balance Simulation Report')
    print(f'  {runs} runs  |  max level {max_level}  |  seed {seed}  |  skill preset: {skill}')
    print(f'  Quiz model : p_correct = {SKILL_BASE[skill]:.2f} - (tier-1)*0.06 + (WIS-10)*0.015')
    print(f'  Armor equip: geography threshold quiz (need {ARMOR_EQUIP_REQUIRED}/{ARMOR_EQUIP_TOTAL} correct, tier {ARMOR_QUIZ_TIER})')
    print(f'  SP model   : {SP_EXPLORATION_PER_LEVEL} SP/level exploration + {SP_PER_COMBAT_TURN} SP/combat turn; starvation=1 HP/turn at SP=0')
    print(f'  Gear find  : {FIND_CHANCE*100:.0f}% chance/level; weapon enchant +0/+1/+2 at 80/12/8%')
    print('=' * W)

    red_flags = []

    print(f'\n{"LV":<4} {"REACHED":>7} {"DIED":>6} {"SURV%":>7} {"HP_LOST":>9} {"SP_LEFT":>8} {"WIN%":>7} {"AVG_CHAIN":>10}  NOTE')
    print('-' * W)

    for lv in range(1, max_level + 1):
        reached = survived_to.get(lv, 0)
        if reached == 0:
            break
        died      = deaths_on.get(lv, 0)
        surv_pct  = 100.0 * (reached - died) / reached
        avg_hp    = sum(hp_lost_lv[lv]) / len(hp_lost_lv[lv])
        hp_pct    = 100.0 * avg_hp / start_hp
        avg_sp_remaining = sum(sp_remaining_lv[lv]) / len(sp_remaining_lv[lv])
        win_pct   = 100.0 * combats_won[lv] / max(1, combats_total[lv])
        clist     = chains_lv[lv]
        avg_chain = sum(clist) / max(1, len(clist))
        avg_starv = sum(starv_dmg_lv[lv]) / len(starv_dmg_lv[lv])

        notes = []
        if hp_pct > 60:
            notes.append('HIGH_DMG')
            red_flags.append(f'L{lv}: avg HP lost {avg_hp:.1f} ({hp_pct:.0f}% of max) -> too punishing')
        if surv_pct < 70 and lv <= 5:
            notes.append('LETHAL')
            red_flags.append(f'L{lv}: survival {surv_pct:.1f}% -> difficulty spike')
        if win_pct < 45:
            notes.append('LOW_WIN')
            red_flags.append(f'L{lv}: combat win rate {win_pct:.1f}% -> monsters too strong')
        if avg_starv > 2:
            notes.append('STARVATION')
            red_flags.append(f'L{lv}: avg {avg_starv:.1f} starvation HP lost -> food supply too thin')

        note_str = ' '.join(f'[{n}]' for n in notes)
        print(f'{lv:<4} {reached:>7} {died:>6} {surv_pct:>6.1f}% {avg_hp:>7.1f}({hp_pct:>3.0f}%) {avg_sp_remaining:>7.0f} {win_pct:>6.1f}% {avg_chain:>9.2f}  {note_str}')

    print('-' * W)
    print(f'\nOverall survival to level {max_level}: {total_survived}/{runs} ({100*total_survived/runs:.1f}%)')

    # Death distribution + cause breakdown
    print(f'\nDEATH DISTRIBUTION:')
    total_deaths = sum(deaths_on.values())
    for lv in sorted(deaths_on):
        pct   = 100.0 * deaths_on[lv] / max(1, total_deaths)
        bar   = '#' * int(pct / 2)
        causes = death_cause[lv]
        cause_str = '  '.join(f'{c}={n}' for c, n in sorted(causes.items()))
        print(f'  L{lv:>3}: {deaths_on[lv]:>5} deaths ({pct:>5.1f}%)  {bar}  [{cause_str}]')

    # Gear baseline -- all slots, all levels
    print(f'\nGEAR CEILING (best spawnable, per slot, no quiz required):')
    print(f'  {"LV":<5} {"BEST WEAPON (base+max_enchant)":35} {"TOTAL AC BONUS":>15}')
    sample_levels = sorted(set([1, 2, 3, 5, 7, 10, 15, 20]) & set(range(1, max_level + 2)))
    for lv in sample_levels:
        if lv > max_level:
            continue
        w  = best_weapon_at_level(weapons, lv)
        ac = best_armor_ac_per_slot(armor, shields, lv)
        if w:
            bd   = w.get('baseDamage', '?')
            name = w.get('name', '?')[:32]
            tier = w.get('mathTier', w.get('quiz_tier', '?'))
            print(f'  {lv:<5} {name:<35} (base {bd:>2}, mathTier {tier})   AC+{ac}')

    # Chain probability table (starting dagger -- actual JSON values)
    base_mults = [0.3, 0.6, 1.0, 1.4, 1.8, 2.2, 2.5]
    base_dmg   = 3
    p_base     = p_correct(1, 10, skill)
    print(f'\nCHAIN TABLE  (iron_dagger: base {base_dmg}  |  skill={skill}  p={p_base:.2f}):')
    print(f'  {"CHAIN":>6}  {"P(chain=k)":>11}  {"DAMAGE":>8}  {"E[dmg contrib]":>16}')
    q = 1.0
    for k in range(0, len(base_mults) + 1):
        if k == 0:
            prob = 1 - p_base
            dmg_str = '0 (miss)'
            edm_str = '0.00'
        else:
            prob = (p_base ** k) * (1 - p_base) if k < len(base_mults) else p_base ** len(base_mults)
            m    = base_mults[k - 1]
            dmg  = max(1, int(base_dmg * m))
            edm  = prob * dmg
            dmg_str = f'{base_dmg} x {m:.1f} = {dmg}'
            edm_str = f'{edm:.2f}'
        print(f'  {k:>6}  {prob:>11.4f}  {dmg_str:>8}  {edm_str:>16}')

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
    print('Caveats: flee/scrolls/wands/potions not modelled (all improve survival).')
    print('Re-run with --skill low/high to bracket the expected player range.')
    print('=' * W)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description='Philosopher\'s Quest balance simulator')
    ap.add_argument('--runs',      type=int,   default=500,   help='Simulation runs (default 500)')
    ap.add_argument('--max-level', type=int,   default=10,    help='Deepest level to simulate (default 10)')
    ap.add_argument('--seed',      type=int,   default=42,    help='RNG seed (default 42)')
    ap.add_argument('--skill',     type=str,   default='med',
                    choices=['low', 'med', 'high'],           help='Player skill preset (default med)')
    args = ap.parse_args()
    run_simulation(args.runs, args.max_level, args.seed, args.skill)

if __name__ == '__main__':
    main()
