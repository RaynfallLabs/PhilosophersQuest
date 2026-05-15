import json, re, os, sys

def parse_dice_avg(s):
    s = str(s)
    mt = re.match(r'(\d+)d(\d+)(?:\+(\d+))?', s)
    if mt:
        n, d, b = int(mt.group(1)), int(mt.group(2)), int(mt.group(3) or 0)
        return n*(d+1)/2 + b
    try: return float(s)
    except: return 0

ROOT = 'C:/Users/brand/Documents/PhilosophersQuest'
sys.path.insert(0, ROOT + '/src')

# -------- Monsters by floor band --------
with open(ROOT + '/data/monsters.json', encoding='utf-8') as f:
    monsters = json.load(f)

bands = {}
spawn_bands = {}
for mid, v in monsters.items():
    ml = v.get('min_level', 1)
    b = ((ml-1) // 10) * 10 + 1
    bands.setdefault(b, []).append((mid, v))
    if v.get('frequency', 0) > 0:
        spawn_bands.setdefault(b, []).append((mid, v))

floors_out = []
for b in sorted(bands.keys()):
    rows = []
    for mid, v in bands[b]:
        max_atk = max((parse_dice_avg(a.get('damage','0')) for a in v.get('attacks',[{}])), default=0)
        hp_avg = round(parse_dice_avg(v.get('hp', '1')), 1)
        rows.append({
            'id': mid,
            'name': v.get('name', mid),
            'min_level': v.get('min_level', 1),
            'hp_avg': hp_avg,
            'max_dmg_avg': round(max_atk, 1),
            'thac0': v.get('thac0', 20),
            'ai': v.get('ai_pattern', 'aggressive'),
            'speed': v.get('speed', 10),
            'frequency': v.get('frequency', 1),
        })
    rows.sort(key=lambda r: -r['hp_avg'])
    spawnable_count = len(spawn_bands.get(b, []))
    floors_out.append({
        'floor_band': 'L%d-L%d' % (b, b+9),
        'min_level_low': b,
        'min_level_high': b+9,
        'total_count': len(rows),
        'spawnable_count': spawnable_count,
        'median_hp': sorted([r['hp_avg'] for r in rows])[len(rows)//2] if rows else 0,
        'max_hp': max([r['hp_avg'] for r in rows], default=0),
        'median_max_dmg': sorted([r['max_dmg_avg'] for r in rows])[len(rows)//2] if rows else 0,
        'max_max_dmg': max([r['max_dmg_avg'] for r in rows], default=0),
        'min_thac0': min([r['thac0'] for r in rows], default=20),
        'top_monsters': rows[:5],
    })

# -------- Weapons by min_level --------
with open(ROOT + '/data/items/weapon.json', encoding='utf-8') as f:
    weapons = json.load(f)
weap_out = []
for wid, v in weapons.items():
    cm = v.get('chainMultipliers') or [1]
    base = v.get('baseDamage', 0)
    weap_out.append({
        'id': wid,
        'name': v.get('name', wid),
        'min_level': v.get('min_level', 1),
        'baseDamage': base,
        'max_chain': v.get('maxChainLength', len(cm)),
        'peak_chain_multiplier': cm[-1] if cm else 1,
        'peak_damage': round(base * (cm[-1] if cm else 1), 1),
        'two_handed': v.get('twoHanded', False),
        'damage_types': v.get('damageTypes', []),
    })
weap_out.sort(key=lambda w: (w['min_level'], -w['peak_damage']))

# -------- Armor by min_level --------
with open(ROOT + '/data/items/armor.json', encoding='utf-8') as f:
    armors = json.load(f)
armor_out = []
for aid, v in armors.items():
    armor_out.append({
        'id': aid,
        'name': v.get('name', aid),
        'min_level': v.get('min_level', 1),
        'slot': v.get('slot', '?'),
        'ac_bonus': v.get('ac_bonus', 0),
        'damage_resistances': v.get('damage_resistances', {}),
    })
armor_out.sort(key=lambda a: (a['min_level'], -a['ac_bonus']))

# -------- Shields by min_level --------
with open(ROOT + '/data/items/shield.json', encoding='utf-8') as f:
    shields = json.load(f)
shield_out = []
for sid, v in shields.items():
    shield_out.append({
        'id': sid,
        'name': v.get('name', sid),
        'min_level': v.get('min_level', 1),
        'ac_bonus': v.get('ac_bonus', 0),
        'effects': v.get('effects'),
        'quiz_timer_bonus': v.get('quiz_timer_bonus', 0),
    })
shield_out.sort(key=lambda s: (s['min_level'], -s['ac_bonus']))

# -------- Accessories by min_level --------
with open(ROOT + '/data/items/accessory.json', encoding='utf-8') as f:
    accs = json.load(f)
acc_out = []
for aid, v in accs.items():
    eff = v.get('effects', v.get('effect', {}))
    stat = amount = status = None
    if isinstance(eff, dict):
        stat = eff.get('stat')
        amount = eff.get('amount')
        status = eff.get('status')
    acc_out.append({
        'id': aid,
        'name': v.get('name', aid),
        'min_level': v.get('min_level', 1),
        'slot': v.get('slot', 'ring'),
        'stat': stat,
        'stat_amount': amount,
        'status': status,
    })
acc_out.sort(key=lambda a: (a['min_level'], -(a['stat_amount'] or 0)))

# -------- Spells by tier --------
from spells import LEARNABLE_SPELLS
spells_out = []
for sid, v in LEARNABLE_SPELLS.items():
    spells_out.append({
        'id': sid,
        'name': v.get('name', sid),
        'quiz_tier': v.get('quiz_tier', 1),
        'mp_cost': v.get('mp_cost', 0),
        'effect': v.get('effect', ''),
        'power': v.get('power', ''),
        'needs_target': v.get('needs_target', False),
    })
spells_out.sort(key=lambda s: (s['quiz_tier'], s['mp_cost']))

# -------- Wands by min_level --------
with open(ROOT + '/data/items/wand.json', encoding='utf-8') as f:
    wands = json.load(f)
wand_out = []
for wid, v in wands.items():
    wand_out.append({
        'id': wid,
        'name': v.get('name', wid),
        'min_level': v.get('min_level', 1),
        'quiz_tier': v.get('quiz_tier', 1),
        'quiz_threshold': v.get('quiz_threshold', 0),
        'effect': v.get('effect', ''),
        'power': v.get('power', ''),
        'charges_min': v.get('charges_min', 0),
        'charges_max': v.get('charges_max', 0),
    })
wand_out.sort(key=lambda w: (w['min_level'], -w.get('quiz_tier', 0)))

# -------- Scrolls by min_level --------
with open(ROOT + '/data/items/scroll.json', encoding='utf-8') as f:
    scrolls = json.load(f)
scroll_out = []
for sid, v in scrolls.items():
    scroll_out.append({
        'id': sid,
        'name': v.get('name', sid),
        'min_level': v.get('min_level', 1),
        'quiz_tier': v.get('quiz_tier', 1),
        'quiz_threshold': v.get('quiz_threshold', 0),
        'effect': v.get('effect', ''),
    })
scroll_out.sort(key=lambda s: (s['min_level'], -s.get('quiz_tier', 0)))

# -------- Boss stats --------
def boss_summary(boss_id):
    b = monsters.get(boss_id)
    if not b: return None
    attacks = []
    for a in b.get('attacks', []):
        attacks.append({
            'name': a.get('name'),
            'damage': a.get('damage'),
            'damage_avg': round(parse_dice_avg(a.get('damage', '0')), 1),
            'type': a.get('type'),
            'effect': a.get('effect'),
            'piercing': a.get('piercing', False),
        })
    return {
        'id': boss_id,
        'name': b.get('name'),
        'min_level': b.get('min_level'),
        'hp': b.get('hp'),
        'thac0': b.get('thac0'),
        'speed': b.get('speed'),
        'ai_pattern': b.get('ai_pattern'),
        'attacks': attacks,
        'resistances': b.get('resistances', []),
        'weaknesses': b.get('weaknesses', []),
        'tags': b.get('tags', []),
        'locust_interval': b.get('locust_interval'),
        'locust_count': b.get('locust_count'),
    }

boss_stats = {
    'asterion_minotaur_L20': boss_summary('asterion_minotaur'),
    'medusa_gorgon_L40':     boss_summary('medusa_gorgon'),
    'fafnir_dragon_L60':     boss_summary('fafnir_dragon'),
    'fenrir_wolf_L80':       boss_summary('fenrir_wolf'),
    'abaddon_destroyer_L100':boss_summary('abaddon_destroyer'),
    'cow_king_L999':         boss_summary('cow_king'),
    'abyssal_locust_summon': boss_summary('abyssal_locust'),
}

# -------- Death chase --------
death_chase = {
    'speed_phases': [
        {'player_floor_range': '>75 (76-100)', 'death_speed_pct': 50, 'msg': 'initial spawn'},
        {'player_floor_range': '51-75', 'death_speed_pct': 75},
        {'player_floor_range': '26-50', 'death_speed_pct': 100},
        {'player_floor_range': '1-25',  'death_speed_pct': 125},
    ],
    'attack': {'damage': '2d12+15', 'damage_avg': 28.0, 'thac0': -20, 'always_hits': True},
    'invincible': True,
    'freezable_by': 'prayer (theology escalator-chain)',
    'freeze_turns_formula': 'min(8, 3 + effective_chain_score)',
    'freeze_turns_range': '4 turns (chain 1) to 8 turns (chain 5+)',
    'prayer_cooldown_after_freeze': 'max(100, 80 + effective*25) turns',
    'time_stopped_blocks_death': True,
    'time_stop_sources': [
        'scroll_of_time_stop (L40)',
        'wand_of_time_stop (L60)',
        'time_freeze_spell (T5)',
        'time_dilation quirk power (25 in a row)',
        'flux_capacitor (special drop)',
    ],
    'death_can_be_destroyed_by': 'abyssal_shimmer + complete_tablet_of_second_death',
    'evidence': {
        'monster_def': 'src/monster.py:1006-1078',
        'speed_escalation': 'src/main.py:1283-1316',
        'prayer_freeze': 'src/game_divine.py:791-797',
        'time_stop_block': 'src/game_combat.py:1353-1354',
    },
}

# -------- Secret victory path --------
secret_victory = {
    'requires': [
        'philosophers_stone (boss drop L100)',
        'tablet_of_second_death (random 80-99)',
        'philosophers_wrench (random 21-49)',
        'abyssal_shimmer (random 1-20)',
    ],
    'item_levels': {
        'shimmer': 'randint(1, 20)',
        'wrench':  'randint(21, 49)',
        'fire_scroll': 'randint(50, 79)',
        'tablet':  'randint(80, 99)',
        'philosophers_stone': 'placed at L100 on Abaddon defeat',
    },
    'evidence_lore_levels': 'src/main.py:115-121',
    'reward': 'scroll_of_death_bane (6th boss reward)',
    'narrative_quote': '"Then Death and Hades were thrown into the lake of fire."',
    'requires_carrying_all_items_during_chase': True,
}

# -------- Score economy --------
score_econ = {
    'per_turn': 10,
    'per_max_floor': 1000,
    'per_kill': 100,
    'stone_bonus': 50000,
    'grade_thresholds': {
        'S':  200000, 'A+': 100000, 'A':   60000, 'B+':  30000,
        'B':   15000, 'C':    7000, 'D':    3000, 'F':       0,
    },
    'evidence': 'src/main.py:1478-1507',
}

# -------- Player baseline --------
player_baseline = {
    'BASE_HP': 20,
    'BASE_SP': 200,
    'BASE_MP': 10,
    'starting_max_hp_with_default_stats': 30,
    'CARRY_BASE': 50,
    'CARRY_PER_STR': 5,
    'evidence': 'src/player.py:1-32',
    'STAIR_REST_CAP_ASC': 22,
    'STAIR_REST_CAP_DESC': 0,
    'ascent_heal_per_stair': '4% of max_hp (capped at 22)',
    'descent_heal_per_stair': 0,
    'COOKING_HP_SOFTCAP': 1000,
    'cooking_hp_diminishing_floor': 0.20,
    'best_ac_reachable_at_L100': '-33 with full late-game armor + tower_shield_of_ajax + DEX 20',
    'note_ac_math': 'AC = 10 - dex_mod(5) - armor_bonus(32) - shield_bonus(6)',
    'evidence_cooking': 'src/player.py:194-207',
}

# -------- Quirks --------
from quirk_system import _QUIRK_NAMES, _QUIRK_EFFECTS, _QUIRK_TRIGGER, _QUIRK_PROGRESS
quirks_out = []
for qid, name in _QUIRK_NAMES.items():
    eff = _QUIRK_EFFECTS.get(qid, '')
    is_power = '[POWER' in eff
    prog = _QUIRK_PROGRESS.get(qid, ('?', 0, False))
    quirks_out.append({
        'id': qid,
        'name': name,
        'effect': eff,
        'trigger': _QUIRK_TRIGGER.get(qid, ''),
        'progress_key': prog[0] if prog else '?',
        'threshold': prog[1] if prog else 0,
        'is_power': is_power,
    })

# -------- Quiz timer --------
from player import Player
quiz_timers = {}
for subj, (base, scale) in Player.SUBJECT_TIMER.items():
    quiz_timers[subj] = {
        'base_seconds': base,
        'wis_scale': scale,
        'at_wis_10':  round(base + 10*scale),
        'at_wis_15':  round(base + 15*scale),
        'at_wis_20':  round(base + 20*scale),
    }

# -------- Subject -> Action map --------
subject_action_freq = {
    'math':       {'action': 'combat attack',     'mode': 'chain',               'frequency': 'constant'},
    'geography':  {'action': 'equip armor/shield','mode': 'threshold',           'frequency': 'occasional'},
    'history':    {'action': 'equip accessory',   'mode': 'threshold',           'frequency': 'occasional'},
    'animal':     {'action': 'harvest corpse',    'mode': 'threshold',           'frequency': 'common'},
    'cooking':    {'action': 'prepare food',      'mode': 'escalator_chain',     'frequency': 'common'},
    'science':    {'action': 'magic/wand',        'mode': 'escalator_chain (spells) / threshold (wands)', 'frequency': 'occasional'},
    'philosophy': {'action': 'identify item',     'mode': 'threshold',           'frequency': 'common'},
    'grammar':    {'action': 'read scroll',       'mode': 'threshold',           'frequency': 'common'},
    'economics':  {'action': 'lockpick',          'mode': 'threshold',           'frequency': 'occasional'},
    'theology':   {'action': 'pray',              'mode': 'escalator_chain',     'frequency': 'rare-high-stakes'},
    'trivia':     {'action': 'recall lore',       'mode': 'escalator_chain',     'frequency': 'player-initiated'},
}

# ----- Compose final JSON -----
out = {
    '_meta': {
        'auditor': 'agent_b',
        'date': '2026-05-15',
        'evidence_base': {
            'monsters_json': 'data/monsters.json (458 monster defs)',
            'monsters_spawnable_count': 418,
            'items_dir': 'data/items/',
            'boss_levels': 'src/boss_levels.py',
            'death_pursuit': 'src/main.py:1254-1316 + src/monster.py:1006-1078',
            'quirks': 'src/quirk_system.py:1096-1199',
            'spells': 'src/spells.py',
        },
    },
    'monsters_by_floor':      floors_out,
    'weapons_by_min_level':   weap_out,
    'armor_by_min_level':     armor_out,
    'shields_by_min_level':   shield_out,
    'accessories_by_min_level': acc_out,
    'spells_by_tier':         spells_out,
    'wands_by_min_level':     wand_out,
    'scrolls_by_min_level':   scroll_out,
    'boss_stats':             boss_stats,
    'death_chase_difficulty': death_chase,
    'secret_victory_path':    secret_victory,
    'score_economy':          score_econ,
    'player_baseline':        player_baseline,
    'quirks':                 quirks_out,
    'quiz_timers':            quiz_timers,
    'subject_action_mapping': subject_action_freq,
    '_data_gaps': [
        'Per-floor accessory spawn pool isn\'t directly listed; spawn is by min_level + floorSpawnWeight.',
        'Cooking max-HP growth depends on player choice; an "optimized" L100 player is assumed cooking softcap-saturated.',
        'wand min_level field for some entries appears to mix dungeon-depth and quiz-tier semantics (e.g. wand_of_fire ml=2 is depth, others use 50-80).',
        'Death chase speed escalation thresholds (level<=25 etc) are intended for ASCENT only; code does not distinguish direction explicitly.',
        'food/HP-restore is mainly via meals and stair-rest; HP from raw food potions is small (per CLAUDE.md context).',
    ],
}

out_path = ROOT + '/tools/audit/deliverables/balance_curves_agent_b.json'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2)

sz = os.path.getsize(out_path)
print('wrote', out_path, 'size=', sz, 'bytes')
