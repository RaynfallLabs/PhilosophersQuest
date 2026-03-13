#!/usr/bin/env python3
"""
balance_simulator.py — Monte Carlo balance analysis for Philosopher's Quest
Usage: python balance_simulator.py [--runs N] [--max-level N] [--seed N]

Assumptions (documented in-line):
  - Quiz success model: Bernoulli p_correct(tier, WIS) per question
  - Combat = one quiz per attack attempt; monster retaliates if alive after
  - THAC0 system: monster hits if d20 >= THAC0 - player_AC (descending AC)
  - Gear: player equips best weapon/armor found on the floor each level
  - SP drain and starvation are ignored (food system not simulated)
  - Flee not modelled; player fights to death or victory
"""

import json, math, random, argparse, sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
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
    return monsters, weapons, armor, shields

# ---------------------------------------------------------------------------
# Dice helpers
# ---------------------------------------------------------------------------

def avg_dice(notation: str) -> float:
    """Return expected value of a dice expression like '2d6+3' or '1d4'."""
    if not notation:
        return 0.0
    total = 0.0
    for part in str(notation).lower().replace(' ', '').split('+'):
        if 'd' in part:
            n, d = part.split('d')
            n = int(n) if n else 1
            d = int(d)
            total += n * (d + 1) / 2.0
        elif part.lstrip('-').isdigit():
            total += int(part)
    return total

def roll_dice(notation: str) -> int:
    """Roll a dice expression and return the result."""
    if not notation:
        return 1
    total = 0
    for part in str(notation).lower().replace(' ', '').split('+'):
        if 'd' in part:
            n, d = part.split('d')
            n = int(n) if n else 1
            d = int(d)
            total += sum(random.randint(1, d) for _ in range(n))
        elif part.lstrip('-').isdigit():
            total += int(part)
    return max(1, total)

# ---------------------------------------------------------------------------
# Quiz success model
# ---------------------------------------------------------------------------
# Assumption: a competent player answers tier-1 math correctly ~70% of the time.
# Each tier above 1 reduces accuracy by 0.06 (harder questions).
# Each WIS point above 10 adds +0.02 (more timer headroom = less panic).
# These constants are tunable. Results show sensitivity in the output.

def p_correct(tier: int, wis: int) -> float:
    base = 0.70 - (tier - 1) * 0.06 + (wis - 10) * 0.02
    return max(0.35, min(0.92, base))

def roll_chain(p: float, max_chain: int) -> int:
    """Simulate a CHAIN quiz: answer correctly until wrong, cap at max_chain."""
    chain = 0
    while chain < max_chain:
        if random.random() < p:
            chain += 1
        else:
            break
    return chain

# ---------------------------------------------------------------------------
# Monster spawn weights (mirrors dungeon.py logic)
# ---------------------------------------------------------------------------

def build_monster_pool(monsters: dict, level: int) -> list:
    """Return a frequency-weighted list of monster IDs eligible at this level."""
    pool = []
    for mid, m in monsters.items():
        if m.get('frequency', 5) == 0:
            continue                        # boss-only, never randomly spawn
        min_lv = m.get('min_level', 1)
        max_lv = m.get('max_level', None)
        if min_lv > level:
            continue
        freq = m.get('frequency', 5)
        if max_lv and level > max_lv:
            freq = max(1, freq - (level - max_lv))  # decay past max_level
        pool.extend([mid] * freq)
    return pool

# ---------------------------------------------------------------------------
# Item pool helpers
# ---------------------------------------------------------------------------

def _spawn_weight(spawn_weights: dict, level: int) -> int:
    """Pick the weight entry whose level range contains `level`."""
    for key, w in spawn_weights.items():
        parts = str(key).split('-')
        if len(parts) == 2:
            lo, hi = int(parts[0]), int(parts[1])
            if lo <= level <= hi:
                return w
    return 0

def best_weapon_at_level(weapons: dict, level: int):
    """Return the highest-baseDamage weapon eligible to spawn at this level."""
    # Assumption: player picks up and uses the best damage weapon they find.
    best = None
    for wid, w in weapons.items():
        if w.get('min_level', 1) > level:
            continue
        sw = w.get('floorSpawnWeight') or w.get('floor_spawn_weight') or {}
        if sw and _spawn_weight(sw, level) == 0:
            continue
        if best is None or w.get('baseDamage', 4) > best[1].get('baseDamage', 4):
            best = (wid, w)
    return best[1] if best else None

def best_armor_ac_at_level(armor: dict, shields: dict, level: int) -> int:
    """Return total AC bonus (armor + shield) a lucky player might have by this level."""
    # Sum the best per-slot armor and one shield available at this level.
    # Assumption: player equips one piece per slot; simulate only body + shield for brevity.
    body_ac = 0
    for aid, a in armor.items():
        if a.get('min_level', 1) > level:
            continue
        sw = a.get('floorSpawnWeight') or a.get('floor_spawn_weight') or {}
        if sw and _spawn_weight(sw, level) == 0:
            continue
        if a.get('slot', 'body') == 'body':
            body_ac = max(body_ac, a.get('ac_bonus', 0))

    shield_ac = 0
    for sid, s in shields.items():
        if s.get('min_level', 1) > level:
            continue
        shield_ac = max(shield_ac, s.get('ac_bonus', 0))

    return body_ac + shield_ac

# ---------------------------------------------------------------------------
# Player simulation model
# ---------------------------------------------------------------------------

class SimPlayer:
    """Lightweight mutable player state for one simulated run."""

    # Assumption: all base stats = 10 (no secret build, no level-up bonuses).
    def __init__(self):
        self.WIS = 10
        self.CON = 10
        self.DEX = 10
        self.max_hp = 20 + self.CON        # 30 HP
        self.hp     = self.max_hp
        self.ac     = 10 - (self.DEX - 10) // 2   # AC = 10

        # Starting gear (iron dagger + no armor)
        self.weapon_base_dmg  = 4          # iron_dagger baseDamage
        self.weapon_mults     = [0.5, 1.0, 1.5, 2.0, 2.5]
        self.weapon_max_chain = 5
        self.weapon_quiz_tier = 1
        self.armor_ac_bonus   = 0          # +AC from equipped armor/shield

    def effective_ac(self) -> int:
        return self.ac - self.armor_ac_bonus  # lower = better

    def upgrade_weapon(self, w: dict):
        if w.get('baseDamage', 0) > self.weapon_base_dmg:
            self.weapon_base_dmg  = w['baseDamage']
            self.weapon_mults     = w.get('chainMultipliers', self.weapon_mults)
            self.weapon_max_chain = w.get('maxChainLength', len(self.weapon_mults))
            self.weapon_quiz_tier = w.get('quiz_tier', 1)

    def upgrade_armor(self, bonus: int):
        self.armor_ac_bonus = max(self.armor_ac_bonus, bonus)

# ---------------------------------------------------------------------------
# Single combat simulation
# ---------------------------------------------------------------------------

def simulate_combat(player: SimPlayer, monster: dict) -> dict:
    """
    Simulate one player-vs-monster fight.
    Returns stats dict with hp_lost, turns, won, chain_lengths.
    """
    m_hp = roll_dice(str(monster.get('hp', '1d6')))
    p_cor = p_correct(player.weapon_quiz_tier, player.WIS)
    chains = []
    player_hp_before = player.hp
    turns = 0

    while m_hp > 0 and player.hp > 0:
        turns += 1

        # --- Player attacks ---
        chain = roll_chain(p_cor, player.weapon_max_chain)
        chains.append(chain)
        if chain > 0:
            idx = min(chain - 1, len(player.weapon_mults) - 1)
            mult = player.weapon_mults[idx]
            dmg = max(1, int(player.weapon_base_dmg * mult))
            m_hp -= dmg

        if m_hp <= 0:
            break

        # --- Monster retaliates ---
        # THAC0 system: hit if d20 >= THAC0 - player_AC
        thac0 = monster.get('thac0', 20)
        roll_needed = thac0 - player.effective_ac()
        if random.randint(1, 20) >= max(2, roll_needed):
            attacks = monster.get('attacks', [{'damage': '1d4'}])
            for atk in attacks:
                dmg_m = roll_dice(str(atk.get('damage', '1d4')))
                player.hp -= dmg_m

    won = m_hp <= 0
    return {
        'won':      won,
        'hp_lost':  max(0, player_hp_before - player.hp),
        'turns':    turns,
        'chains':   chains,
        'avg_chain': sum(chains) / len(chains) if chains else 0,
    }

# ---------------------------------------------------------------------------
# Single level simulation
# ---------------------------------------------------------------------------

def simulate_level(player: SimPlayer, level: int,
                   monsters: dict, weapons: dict,
                   armor: dict, shields: dict) -> dict:
    """
    Simulate one dungeon level: gear upgrade + N monster combats.
    Returns per-level stats dict.
    """
    # Gear upgrade — Assumption: player finds and equips the best available
    # weapon and armor on this level with 60% probability per slot.
    # (Reflects that not every room has loot and not every item is optimal.)
    FIND_CHANCE = 0.60
    if random.random() < FIND_CHANCE:
        w = best_weapon_at_level(weapons, level)
        if w:
            player.upgrade_weapon(w)

    if random.random() < FIND_CHANCE:
        ac_bonus = best_armor_ac_at_level(armor, shields, level)
        player.upgrade_armor(ac_bonus)

    # Spawn N monsters — mirrors dungeon.py count formula
    min_m = min(3 + (level - 1), 12)
    max_m = min(5 + level, 18)
    n_monsters = random.randint(min_m, max_m)

    pool = build_monster_pool(monsters, level)
    if not pool:
        return {'combats': 0, 'hp_lost': 0, 'deaths': 0, 'won': 0, 'chains': []}

    combats_won = 0
    total_hp_lost = 0
    all_chains = []
    died = False

    for _ in range(n_monsters):
        if player.hp <= 0:
            died = True
            break
        mid = random.choice(pool)
        result = simulate_combat(player, monsters[mid])
        total_hp_lost += result['hp_lost']
        all_chains.extend(result['chains'])
        if result['won']:
            combats_won += 1

    # Partial HP regen between levels — Assumption: rest at stairs restores 20% max HP.
    player.hp = min(player.max_hp, player.hp + int(player.max_hp * 0.20))

    return {
        'combats':  n_monsters,
        'won':      combats_won,
        'hp_lost':  total_hp_lost,
        'deaths':   1 if died else 0,
        'chains':   all_chains,
    }

# ---------------------------------------------------------------------------
# Full run simulation
# ---------------------------------------------------------------------------

def simulate_run(max_level: int, monsters: dict, weapons: dict,
                 armor: dict, shields: dict) -> dict:
    """Simulate one complete run through max_level dungeon levels."""
    player   = SimPlayer()
    per_lv   = []
    died_on  = None

    for lv in range(1, max_level + 1):
        stats = simulate_level(player, lv, monsters, weapons, armor, shields)
        stats['level'] = lv
        stats['hp_remaining'] = player.hp
        per_lv.append(stats)

        if stats['deaths'] or player.hp <= 0:
            died_on = lv
            break

    return {
        'survived':  died_on is None,
        'died_on':   died_on,
        'per_level': per_lv,
    }

# ---------------------------------------------------------------------------
# Aggregation & reporting
# ---------------------------------------------------------------------------

def run_simulation(runs: int, max_level: int, seed: int):
    random.seed(seed)
    monsters, weapons, armor, shields = load_data()

    # Per-level accumulators
    survived_to   = defaultdict(int)    # level -> runs that reached it alive
    deaths_on     = defaultdict(int)    # level -> deaths on that level
    hp_lost_lv    = defaultdict(list)   # level -> list of hp_lost values
    chains_lv     = defaultdict(list)   # level -> all chain lengths
    combats_won   = defaultdict(int)
    combats_total = defaultdict(int)
    turns_lv      = defaultdict(list)

    total_survived = 0

    for _ in range(runs):
        result = simulate_run(max_level, monsters, weapons, armor, shields)
        if result['survived']:
            total_survived += 1
            survived_to[max_level] += 1

        for lvstats in result['per_level']:
            lv = lvstats['level']
            survived_to[lv] += 1         # reached this level alive (even if died here)
            hp_lost_lv[lv].append(lvstats['hp_lost'])
            chains_lv[lv].extend(lvstats['chains'])
            combats_won[lv]   += lvstats['won']
            combats_total[lv] += lvstats['combats']
            if lvstats['deaths']:
                deaths_on[lv] += 1

    # ---- Print report --------------------------------------------------------
    W = 72
    print('=' * W)
    print(' Philosopher\'s Quest — Balance Simulation Report')
    print(f' {runs} runs · max level {max_level} · seed {seed}')
    print(f' Quiz model: p_correct = 0.70 - (tier-1)×0.06 + (WIS-10)×0.02')
    print(f' Gear model: 60% chance to find best available weapon/armor per level')
    print(f' Recovery  : +20% max HP regen between levels')
    print('=' * W)

    # Survival rates
    print(f'\n{"LEVEL":<8} {"REACHED":>8} {"DIED":>8} {"SURV%":>8} {"AVG HP LOST":>12} {"WIN%":>8} {"AVG CHAIN":>10}')
    print('-' * W)

    start_hp = 30  # SimPlayer default max_hp
    red_flags = []

    for lv in range(1, max_level + 1):
        reached   = survived_to.get(lv, 0)
        died      = deaths_on.get(lv, 0)
        if reached == 0:
            continue
        surv_pct  = 100.0 * (reached - died) / reached
        avg_hp    = sum(hp_lost_lv[lv]) / max(1, len(hp_lost_lv[lv]))
        hp_pct    = 100.0 * avg_hp / start_hp
        win_pct   = 100.0 * combats_won[lv] / max(1, combats_total[lv])
        clist     = chains_lv[lv]
        avg_chain = sum(clist) / max(1, len(clist))

        flag = ''
        if hp_pct > 60:
            flag = '! HIGH DMG'
            red_flags.append(f'Level {lv}: avg HP lost {avg_hp:.1f} = {hp_pct:.0f}% of max HP -> too punishing')
        if surv_pct < 70 and lv <= 3:
            flag = flag or '! LETHAL'
            red_flags.append(f'Level {lv}: only {surv_pct:.1f}% survive -> early lethality spike')
        if win_pct < 50:
            flag = flag or '! LOW WIN'
            red_flags.append(f'Level {lv}: combat win rate {win_pct:.1f}% < 50% -> monsters too strong')

        print(f'{lv:<8} {reached:>8} {died:>8} {surv_pct:>7.1f}% {avg_hp:>10.1f} ({hp_pct:>4.0f}%) {win_pct:>6.1f}%  {avg_chain:>7.2f}  {flag}')

    # Overall survival
    print('-' * W)
    overall_pct = 100.0 * total_survived / runs
    print(f'\nOverall survival to level {max_level}: {total_survived}/{runs} = {overall_pct:.1f}%')

    # Death distribution
    print(f'\nDEATH DISTRIBUTION:')
    total_deaths = sum(deaths_on.values())
    for lv in sorted(deaths_on):
        pct = 100.0 * deaths_on[lv] / max(1, total_deaths)
        bar = '#' * int(pct / 2)
        print(f'  Level {lv:>3}: {deaths_on[lv]:>5} deaths ({pct:>5.1f}%)  {bar}')

    # Gear baseline at key levels
    print(f'\nGEAR BASELINE (best available, no quiz required):')
    for lv in [1, 3, 5, 8, 10] if max_level >= 10 else range(1, max_level + 1, max(1, max_level // 5)):
        w = best_weapon_at_level(weapons, lv)
        ac = best_armor_ac_at_level(armor, shields, lv)
        if w:
            bd = w.get('baseDamage', '?')
            wn = w.get('name', '?')
            print(f'  Level {lv:>3}: weapon={wn} (base {bd} dmg)  armor AC bonus={ac}')

    # Chain length insights
    print(f'\nCHAIN LENGTH INSIGHTS (combat quiz, WIS=10, tier 1 -> p=0.70):')
    p = p_correct(1, 10)
    for chain in range(0, 7):
        prob = (p ** chain) * (1 - p) if chain < 6 else p ** 6
        mults = [0.5, 1.0, 1.5, 2.0, 2.5]
        if chain == 0:
            dmg_str = '0 (miss)'
        else:
            m = mults[min(chain-1, len(mults)-1)]
            dmg_str = f'4 x {m} = {4*m:.1f} (iron dagger start)'
        print(f'  Chain {chain}: P={prob:.3f}  ->  {dmg_str}')

    # Red flags summary
    if red_flags:
        print(f'\nRED FLAGS:')
        seen = set()
        for flag in red_flags:
            if flag not in seen:
                print(f'  [!] {flag}')
                seen.add(flag)
    else:
        print(f'\n[OK] No critical balance flags detected at p_correct=0.70 baseline.')

    print('=' * W)
    print('NOTE: This model ignores SP drain, flee, potions, scrolls, and wands.')
    print('Adjust --runs for stability; re-tune p_correct constants for different')
    print('player skill assumptions.')
    print('=' * W)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Philosopher\'s Quest balance simulator')
    parser.add_argument('--runs',      type=int, default=500,  help='Number of simulation runs (default: 500)')
    parser.add_argument('--max-level', type=int, default=10,   help='Deepest dungeon level to simulate (default: 10)')
    parser.add_argument('--seed',      type=int, default=42,   help='Random seed for reproducibility (default: 42)')
    args = parser.parse_args()

    run_simulation(args.runs, args.max_level, args.seed)

if __name__ == '__main__':
    main()
