"""Build balance_curves_agent_a.json deliverable. One-shot script."""
import json
import re
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.chdir(ROOT)


def avg_dice(s):
    if isinstance(s, (int, float)):
        return float(s)
    if not isinstance(s, str):
        return 0
    s = s.strip()
    m = re.match(r'(\d+)d(\d+)([+-]\d+)?', s)
    if m:
        n, sides, bonus = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        return n * (sides + 1) / 2 + bonus
    try:
        return float(s)
    except Exception:
        return 0


with open('data/monsters.json', encoding='utf-8') as f:
    monsters = json.load(f)
with open('data/items/weapon.json', encoding='utf-8') as f:
    weapons = json.load(f)
with open('data/items/armor.json', encoding='utf-8') as f:
    armor = json.load(f)
with open('data/items/shield.json', encoding='utf-8') as f:
    shields = json.load(f)
with open('data/items/accessory.json', encoding='utf-8') as f:
    accessories = json.load(f)
with open('data/items/artifact.json', encoding='utf-8') as f:
    artifacts = json.load(f)
with open('data/items/wand.json', encoding='utf-8') as f:
    wands = json.load(f)
with open('data/items/scroll.json', encoding='utf-8') as f:
    scrolls = json.load(f)
with open('data/items/spellbook.json', encoding='utf-8') as f:
    spellbooks = json.load(f)

# monsters_by_floor: introductions + pool size per floor
floor_pool = defaultdict(list)
for mid, m in monsters.items():
    if mid == 'death':
        continue
    if m.get('frequency', 0) is None or (isinstance(m.get('frequency'), (int, float)) and m.get('frequency', 0) <= 0):
        # boss/scripted-only - skip pool count
        continue
    if m.get('is_boss') or m.get('is_mini_boss'):
        continue
    lo = m.get('min_level', 1)
    hi = m.get('max_level', 100)
    for f in range(lo, hi + 1):
        floor_pool[f].append(mid)

monster_intro_by_floor = defaultdict(list)
for mid, m in monsters.items():
    if mid == 'death':
        continue
    monster_intro_by_floor[m.get('min_level', 1)].append({
        'id': mid,
        'name': m.get('name'),
        'hp_avg': round(avg_dice(m.get('hp', 0)), 1),
        'hp_raw': m.get('hp'),
        'thac0': m.get('thac0'),
        'speed': m.get('speed'),
        'ai': m.get('ai_pattern'),
        'attacks': [a.get('damage') for a in m.get('attacks', [])],
        'is_boss': bool(m.get('is_boss')),
        'is_mini_boss': bool(m.get('is_mini_boss')),
        'max_level': m.get('max_level'),
        'frequency': m.get('frequency'),
    })

monsters_by_floor = []
for floor in range(1, 101):
    pool_size = len(floor_pool[floor])
    intros = monster_intro_by_floor.get(floor, [])
    monsters_by_floor.append({
        'floor': floor,
        'pool_size_normal': pool_size,
        'new_intros_count': len(intros),
        'introductions': intros,
    })


def items_by_min_level(d):
    out = []
    for iid, it in sorted(d.items(), key=lambda kv: (kv[1].get('min_level', 1), kv[0])):
        row = {
            'id': iid,
            'name': it.get('name'),
            'min_level': it.get('min_level'),
            'tier': it.get('tier'),
            'ac_bonus': it.get('ac_bonus'),
            'enchant_bonus': it.get('enchant_bonus'),
            'damage_resistances': it.get('damage_resistances'),
            'equip_threshold': it.get('equip_threshold'),
            'slot': it.get('slot'),
            'effects': it.get('effects'),
            'quiz_tier': it.get('quiz_tier'),
        }
        out.append(row)
    return out


weapons_by_min_level = []
for wid, w in sorted(weapons.items(), key=lambda kv: (kv[1].get('min_level', 1), kv[0])):
    weapons_by_min_level.append({
        'id': wid,
        'name': w.get('name'),
        'min_level': w.get('min_level'),
        'tier': w.get('tier'),
        'mathTier': w.get('mathTier'),
        'baseDamage': w.get('baseDamage'),
        'chainMultipliers': w.get('chainMultipliers'),
        'maxChainLength': w.get('maxChainLength'),
        'two_handed': w.get('twoHanded'),
        'class': w.get('class'),
        'value': w.get('value'),
        'quiz_tier': w.get('quiz_tier'),
    })

armor_by_min_level = items_by_min_level(armor)
shields_by_min_level = items_by_min_level(shields)
accessories_by_min_level = items_by_min_level(accessories)
artifacts_by_min_level = items_by_min_level(artifacts)

wands_by_tier = []
for wid, w in sorted(wands.items(), key=lambda kv: (kv[1].get('min_level', 1), kv[0])):
    wands_by_tier.append({
        'id': wid, 'name': w.get('name'), 'min_level': w.get('min_level'),
        'effect': w.get('effect'), 'power': w.get('power'),
        'charges_min': w.get('charges_min'), 'charges_max': w.get('charges_max'),
        'quiz_threshold': w.get('quiz_threshold'), 'quiz_tier': w.get('quiz_tier'),
    })

scrolls_by_tier = []
for sid, s in sorted(scrolls.items(), key=lambda kv: (kv[1].get('min_level', 1), kv[0])):
    scrolls_by_tier.append({
        'id': sid, 'name': s.get('name'), 'min_level': s.get('min_level'),
        'effect': s.get('effect'), 'power': s.get('power'),
        'quiz_tier': s.get('quiz_tier'),
    })

spellbooks_by_tier = []
for sid, s in sorted(spellbooks.items(), key=lambda kv: (kv[1].get('min_level', 1), kv[0])):
    spellbooks_by_tier.append({
        'id': sid, 'name': s.get('name'), 'min_level': s.get('min_level'),
        'spell_id': s.get('spell_id'), 'mp_cost': s.get('mp_cost'),
        'quiz_tier': s.get('quiz_tier'),
    })

# Spells from spells.py
sys.path.insert(0, 'src')
from spells import LEARNABLE_SPELLS  # type: ignore

spells_by_tier = []
for sid, s in sorted(LEARNABLE_SPELLS.items(), key=lambda kv: (kv[1].get('quiz_tier', 0), kv[0])):
    spells_by_tier.append({
        'id': sid, 'name': s.get('name'), 'quiz_tier': s.get('quiz_tier'),
        'mp_cost': s.get('mp_cost'), 'power': s.get('power'),
        'effect': s.get('effect'), 'needs_target': s.get('needs_target'),
        'desc': s.get('desc'),
    })

# Boss stats
boss_stats = {}
for bid in ['asterion_minotaur', 'medusa_gorgon', 'fafnir_dragon', 'fenrir_wolf', 'abaddon_destroyer']:
    if bid in monsters:
        m = monsters[bid]
        boss_stats[bid] = {
            'name': m.get('name'),
            'floor': m.get('min_level'),
            'hp': m.get('hp'),
            'speed': m.get('speed'),
            'thac0': m.get('thac0'),
            'ai': m.get('ai_pattern'),
            'attacks': m.get('attacks'),
            'resistances': m.get('resistances'),
            'specials': {k: m.get(k) for k in ['gaze_paralyze', 'can_phase_walls', 'locust_count', 'rage_damage_bonus', 'regen'] if k in m},
        }

minibosses = []
for mid, m in monsters.items():
    if m.get('is_mini_boss'):
        minibosses.append({
            'id': mid, 'name': m.get('name'),
            'floor': m.get('min_level'),
            'hp': m.get('hp'), 'thac0': m.get('thac0'),
            'attacks': [a.get('damage') for a in m.get('attacks', [])],
            'ai': m.get('ai_pattern'),
        })

death_chase_difficulty = {
    'speeds_by_floor_during_escape': {
        'floors_76-100_just_after_L100_ascent': 50,
        'floors_51-75_ascending': 75,
        'floors_26-50_ascending': 100,
        'floors_1-25_ascending_final_sprint': 125,
    },
    'damage_per_hit': '2d12+15 (avg 28)',
    'thac0': -20,
    'always_hits': True,
    'invulnerable': True,
    'freezable': True,
    'freeze_method': 'theology threshold prayer; freeze_turns = min(8, 3+effective_chain)',
    'prayer_cooldown_base': '100-280 turns (effective_chain * 25 + 80, min 100)',
    'fisher_king_halves_cooldown': True,
    'fisher_king_mystery_also_halves': True,
    'compound_halving_means': 'with both Fisher King quirks active, prayer cooldown can drop to floor of 1, making freeze infinite',
    'speed_pct_125_means': 'normal turn + 25% chance of bonus move; can outpace player',
    'source': ['src/main.py:1283-1316', 'src/monster.py:1006-1078', 'src/game_divine.py:780-797'],
}

score_economy = {
    'per_turn': 10,
    'per_max_floor_reached': 1000,
    'per_kill': 100,
    'stone_bonus': 50000,
    'complete_tablet_also_50k': True,
    'grade_thresholds': {'S': 200000, 'A+': 100000, 'A': 60000, 'B+': 30000, 'B': 15000, 'C': 7000, 'D': 3000, 'F': 0},
    'source': 'src/main.py:1478-1507',
}

secret_victory_path = {
    'shimmer_band': '1-20',
    'wrench_band': '21-49',
    'fire_scroll_band': '50-79',
    'tablet_band': '80-99',
    'source': 'src/main.py:116-122',
    'note': 'One of each placed once per run, at random level within band. Path: Stone (L100 boss drop) + Tablet + Wrench + Fire Scroll + Shimmer triggers _trigger_abyss to kill Death and gain Scroll of Death\'s Bane.',
}

status_tick_status = {
    'monster_tick_effects_called': False,
    'source': 'src/monster.py:54 (defined) but never called in main loop per data/audit/consensus.json P3',
    'effects_silently_broken': ['bleeding', 'poison', 'burning', 'petrifying'],
    'balance_implication': 'All damage-over-time monster debuffs and petrification kill path are non-functional. Existing balance assumes these never tick on monsters.',
}

power_quirks_summary = [
    {'id': 'philosophers_stone', 'uses': 1, 'effect': 'Blessed + Brilliance 10t', 'unlock': '200 items identified'},
    {'id': 'atlas_burden', 'uses': 2, 'effect': 'Heroism 20t', 'unlock': '100 atlas_burden_turns'},
    {'id': 'zeus_bolt', 'uses': 3, 'effect': 'Shock Resist + Hasted 15t', 'unlock': '15 hasted floors'},
    {'id': 'gorgon_ward', 'uses': 2, 'effect': 'Sleep Resist + Displacement 15t', 'unlock': '3 petrify survivals'},
    {'id': 'phoenix_rising', 'uses': 1, 'effect': 'Fully restore HP', 'unlock': '10 near-death survivals'},
    {'id': 'iron_will', 'uses': 2, 'effect': 'Shielded + Reflecting 10t', 'unlock': '10 paralyzed hits'},
    {'id': 'battle_trance', 'uses': 3, 'effect': 'Heroism 15t', 'unlock': '200 battle_trance kills'},
    {'id': 'second_sight', 'uses': 3, 'effect': 'Telepathy + Clairvoyance 15t', 'unlock': '5 blind lore'},
    {'id': 'iron_ration', 'uses': 5, 'effect': 'Restore 100 SP', 'unlock': '15000 tile moves'},
    {'id': 'shadow_step', 'uses': 3, 'effect': 'Invisible + Phasing 5t', 'unlock': '2500 invisible moves'},
    {'id': 'focused_scholar', 'uses': 2, 'effect': 'Brilliance 10t (INT+1 WIS+1)', 'unlock': '500 correct answers'},
    {'id': 'eye_storm', 'uses': 3, 'effect': 'Invisible + Blessed 10t', 'unlock': '5 clean floors'},
    {'id': 'time_dilation', 'uses': 1, 'effect': 'Freeze time 10t (all monsters paused)', 'unlock': '25 consecutive correct'},
    {'id': 'ouroboros', 'uses': 1, 'effect': 'Haste+Shield+Regen 20t', 'unlock': 'quirk'},
    {'id': 'arcane_surge', 'uses': 2, 'effect': 'Brilliance 10t + restore all MP', 'unlock': '20 spell casts'},
    {'id': 'wandering_star', 'uses': 0, 'cooldown': 50, 'effect': 'Random teleport (always available)', 'unlock': '15 teleports'},
    {'id': 'sage_counsel', 'uses': 3, 'effect': 'Blessed 15t (+25% quiz timer)', 'unlock': 'quirk'},
]

stat_scaling = {
    'base_hp': 30,
    'base_sp': 210,
    'base_mp': 20,
    'hp_per_con': 1,
    'cooking_hp_softcap': 1000,
    'cooking_hp_floor_factor': 0.20,
    'best_con_accessory_stack': '+5 amulet of titan + +5 Idunns Apple + +4 ring of endurance = +14 CON',
    'max_typical_late_game_hp_no_cooking': '~44 (30 base + 14 CON) — dangerously low',
    'max_typical_late_game_hp_with_full_cooking_softcap': '~1030 (cooking dominates HP economy)',
    'wis_to_quiz_timer': 'math: +0.8s/WIS; theology: +1.7s/WIS; range 0.8-1.7s per point',
    'wis_subject_timer_floor': 'math @ WIS 10 = 16s, theology @ WIS 10 = 65s based on SUBJECT_TIMER',
    'sources': ['src/player.py:1-30', 'src/player.py:194-207'],
}

deliverable = {
    '_meta': {
        'agent': 'agent_a',
        'date': '2026-05-15',
        'sources': {
            'monsters': 'data/monsters.json',
            'weapons': 'data/items/weapon.json',
            'armor': 'data/items/armor.json',
            'shields': 'data/items/shield.json',
            'accessories': 'data/items/accessory.json',
            'artifacts': 'data/items/artifact.json',
            'wands': 'data/items/wand.json',
            'scrolls': 'data/items/scroll.json',
            'spellbooks': 'data/items/spellbook.json',
            'spells': 'src/spells.py',
            'bosses': 'src/boss_levels.py + data/monsters.json',
            'score_economy': 'src/main.py:1478-1507',
            'death_chase': 'src/main.py:1283-1316 + src/monster.py:1006-1078',
            'prayer_freeze': 'src/game_divine.py:780-797',
            'secret_victory': 'src/main.py:116-122, src/main.py:1373-1406',
            'player_stats': 'src/player.py:1-210',
            'power_quirks': 'src/quirk_system.py:1054-1090',
        }
    },
    'monsters_by_floor': monsters_by_floor,
    'weapons_by_min_level': weapons_by_min_level,
    'armor_by_min_level': armor_by_min_level,
    'shields_by_min_level': shields_by_min_level,
    'accessories_by_min_level': accessories_by_min_level,
    'artifacts_by_min_level': artifacts_by_min_level,
    'spells_by_tier': spells_by_tier,
    'wands_by_tier': wands_by_tier,
    'scrolls_by_tier': scrolls_by_tier,
    'spellbooks_by_tier': spellbooks_by_tier,
    'boss_stats': {
        'abaddon': boss_stats.get('abaddon_destroyer'),
        'fenrir': boss_stats.get('fenrir_wolf'),
        'fafnir': boss_stats.get('fafnir_dragon'),
        'medusa': boss_stats.get('medusa_gorgon'),
        'asterion': boss_stats.get('asterion_minotaur'),
        'minibosses': minibosses,
    },
    'death_chase_difficulty': death_chase_difficulty,
    'score_economy': score_economy,
    'secret_victory_path': secret_victory_path,
    'power_quirks': power_quirks_summary,
    'stat_scaling': stat_scaling,
    'monster_tick_status': status_tick_status,
    '_data_gaps': [
        'No XP/level progression for player — stat growth is only via prayer boons (+1 WIS up to 3x), cooking max-HP, accessory bonuses, quirk-granted +CON, and rare scrolls.',
        'Chain multipliers: weapon final hit at maxChainLength 6 = 3.2x base damage; combined with crit/quirks not modeled here.',
        'Frequency=0 monsters skipped from pool count (they are boss/scripted-spawn).',
        'min_level 9999 indicates artifact/unique items spawned only by code, not RNG.',
        'min_level 999 indicates Moo Moo Farm cow-level placement.',
        'Co-spawn behaviour on hand-crafted boss levels (20/40/60/80/100) not verified — pool may not apply.',
        'cooking_hp_gained softcap (1000) is per-run; HP economy dominated by cooking.',
        'Several known broken items per data/audit/consensus.json — _base_STR potion silent failure, etc. Balance findings assume current as-shipped behaviour.',
    ],
}

os.makedirs('tools/audit/deliverables', exist_ok=True)
with open('tools/audit/deliverables/balance_curves_agent_a.json', 'w', encoding='utf-8') as f:
    json.dump(deliverable, f, indent=2, ensure_ascii=False)
print('Wrote tools/audit/deliverables/balance_curves_agent_a.json')
print(f'  size: {os.path.getsize("tools/audit/deliverables/balance_curves_agent_a.json")} bytes')
print(f'  monsters_by_floor: {len(monsters_by_floor)}')
print(f'  weapons: {len(weapons_by_min_level)}')
print(f'  armor: {len(armor_by_min_level)}')
print(f'  shields: {len(shields_by_min_level)}')
print(f'  accessories: {len(accessories_by_min_level)}')
print(f'  spells: {len(spells_by_tier)}')
print(f'  wands: {len(wands_by_tier)}')
print(f'  minibosses: {len(minibosses)}')
