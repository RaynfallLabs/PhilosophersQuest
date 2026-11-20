"""
Monster behaviour, first wave (AI-1, 2026-11-19): the data the behaviours
read, written onto EXISTING kinds by their lore, and their tells.

Offline tooling (not loaded at runtime). Idempotent: every run sets the same
values; nothing is appended twice.

    py tools/content/monster_ai_pass_2026_11.py            # report
    py tools/content/monster_ai_pass_2026_11.py --write    # write the data

data/monsters.json keeps its layout (json indent 2, CRLF: the dump below
reproduces the file byte for byte); data/tells.json is edited as text, so its
compact lists stay as they are. New kinds are never added here (slice M adds
those at the end of monsters.json).

What each block is for, and the lore behind every choice, is in the comments
by it and in docs/systems/monsters.md, 'Monster behaviour, first wave'.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MONSTERS = ROOT / 'data' / 'monsters.json'
TELLS = ROOT / 'data' / 'tells.json'

# ---------------------------------------------------------------------------
# Kind fields: {kind: {field: value}} (a value None removes the field)
# ---------------------------------------------------------------------------
KIND_FIELDS: dict = {
    # --- Morale by Nature (src/morale.py): the kinds whose nerve is not
    # their family's. A fanatic never runs; bandits, a hired sword and a
    # cult's new recruit run for their friends and, caught with none, throw
    # down their weapons and beg (2e: surrender where mercy is expected);
    # the lizard-men, frog-men and cave-men hunt in tribes and run back to
    # them (their family, the serpents, would bolt); a knight holds his
    # ground longer than a brigand.
    'cult_zealot': {'morale_style': 'never'},
    'bandit_thug': {'morale_style': 'yield'},
    'bandit_thief': {'morale_style': 'yield'},
    'mercenary_veteran': {'morale_style': 'yield', 'morale': 11},
    'cult_initiate': {'morale_style': 'yield', 'morale': 7},
    'lizardfolk': {'morale_style': 'regroup', 'morale': 8},
    'bullywug': {'morale_style': 'regroup', 'morale': 6},
    'troglodyte': {'morale_style': 'regroup', 'morale': 8},
    'veteran_knight': {'morale_style': 'withdraw', 'morale': 14},
    'bandit_captain': {'morale': 11},
    # --- Life Drained (src/life_drain.py). The undead that FEED on what they
    # drain (drain_heals_self; the vampire and the vampire lord already did):
    # the Slavic and Greek blood-drinkers, the nosferatu, the strix (the
    # blood-drinking night bird of Rome) and the keres (Hesiod's death
    # spirits who drank the blood of the fallen). Half of what they drain.
    'vampire_spawn': {'drain_heals_self': 0.5},
    'nosferatu': {'drain_heals_self': 0.5},
    'strigoi': {'drain_heals_self': 0.5},
    'vrykolakas': {'drain_heals_self': 0.5},
    'vampire_lord': {'drain_heals_self': 0.75},
    'elder_vampire': {'drain_heals_self': 0.75},
    'strix': {'drain_heals_self': 0.5},
    'ker': {'drain_heals_self': 0.5},
    # The greatest of the dead still take a point of the hero's very
    # constitution (the old CON rule, once a floor) as well as his life.
    'lich': {'drain_con': True},
    'greater_lich': {'drain_con': True},
    'ancient_lich': {'drain_con': True},
    'arch_lich': {'drain_con': True},
    'death_lord': {'drain_con': True},
}

# Attack fields: {(kind, attack name): {field: value}}
ATTACK_FIELDS: dict = {
    # --- Life Drained: the classic drainers drained nothing. The barrow-
    # wight of the mound (Old English wiht, the Norse haugbui), the wraith,
    # the cairn-wight and the fetch (a man's own double, come for his life)
    # struck with plain necrotic. Their touch takes life now (their own
    # riders stay).
    ('wight', 'Draining Touch'): {'drains_life': True},
    ('wraith', 'Draining Touch'): {'drains_life': True},
    ('barrow_wight', 'Drain'): {'drains_life': True},
    ('cairn_wight', 'Drain'): {'drains_life': True},
    ('fetch', 'Life Drain'): {'drains_life': True},
}

# ---------------------------------------------------------------------------
# Tells (data/tells.json): key -> (after which key in 'order', entry)
# ---------------------------------------------------------------------------
TELLS_NEW = {
    'life_drain': ('drain_heals_self', {
        'sign': "The air about {the} is thin and cold, like the air of a tomb.",
        'does': "{His} touch takes life that rest will not give back: your greatest health falls with every blow {he} lands.",
        'counter': "Do not let {him} touch you often. What {he} takes comes back half with a night's sleep on the next floor down, and all of it from a physician or a strong prayer.",
    }),
    'breath_recharge': ('pull_chance', {
        'sign': "{The}'s chest heaves like a bellows.",
        'does': "{He} breathes, then must draw breath again: for a few turns {he} has only tooth and claw.",
        'counter': "Close in while {he} draws breath, or keep stone between you until {he} has spent it.",
    }),
    'heals_allies': ('summon_kind', {
        'sign': "{The} stays close behind the others, eyeing every wound.",
        'does': "{He} mends a badly hurt friend, then must rest {his} voice a few turns before the next.",
        'counter': "Kill {him} first, or finish the friend {he} has just mended before {he} can mend again.",
    }),
}
# Tells whose words change (a rule changed): key -> {part: text}
TELLS_CHANGED = {
    'summon_kind': {
        'does': "{He} can call others to {him}, a few at a time.",
        'counter': "Strike {him} while {he} chants: a blow breaks the call. Kill what {he} calls, and {he} must call again.",
    },
}


# ---------------------------------------------------------------------------
# The rest of the wave, by behaviour
# ---------------------------------------------------------------------------

# --- Light-Shy (src/light_shy.py). Trolls turn to stone in the sun
# (Asbjornsen and Moe), and so do the dwarves (Alviss in the Alvissmal; the
# Nibelung hoard-wardens are Alberich's dwarves); the dark elves (the
# dokkalfar), the shadows and the shades dwell where no light comes; the
# kobolds of the mines and the hidden folk of the rocks keep to the dark.
_SHY = ['troll', 'cave_troll', 'ice_troll', 'war_troll', 'troll_brute', 'chaos_troll',
        'nibelung_hoardwarden', 'dark_elf', 'drow_warrior', 'drow_mage', 'drow_priestess',
        'shadow', 'greater_shadow', 'shadow_master', 'soul_shadow', 'nightshade_spawn', 'shade',
        'nightwing', 'darkmantle', 'kobold', 'kobold_trapsetter', 'huldufolk_raider']
_STONE = ['troll', 'cave_troll', 'ice_troll', 'war_troll', 'troll_brute', 'chaos_troll',
          'nibelung_hoardwarden']
for _k in _SHY:
    KIND_FIELDS.setdefault(_k, {})['light_shy'] = True
for _k in _STONE:
    KIND_FIELDS.setdefault(_k, {})['turns_to_stone_in_light'] = True
# The troll's own lore says why (agent A's lore line, 2026-11-19).
LORE_EDITS = {
    'troll': ("Underground no sunrise comes.",
              "Underground no sunrise comes, but a strong light is the next best thing, "
              "and a troll hates it."),
}

# --- Snuff the Light: a wave drowns a torch, a whirlwind's gust or a
# jinni's dust-devil blows it out, the darkmantle wraps the head and the
# light with it, a shadow master's claw and a drow priestess's curse of
# darkness smother it.
ATTACK_FIELDS.update({
    ('water_elemental', 'Wave Crash'): {'snuffs_light': 'water'},
    ('air_elemental', 'Vortex'): {'snuffs_light': 'wind'},
    ('whirlwind_jinni', 'Dust-Devil Blow'): {'snuffs_light': 'wind'},
    ('darkmantle', 'Engulf Head'): {'snuffs_light': 'dark'},
    ('shadow_master', 'Shadow Claw'): {'snuffs_light': 'dark', 'snuff_chance': 0.5},
    ('drow_priestess', 'Divine Curse'): {'snuffs_light': 'dark'},
})

# --- Gone Again (src/gone_again.py): the house-spirits and imps that
# vanish into the dark (the boggart, the shade, the imp, the quasit, the
# shadow demon). Every non-phasing hit-and-run kind hides out of sight.
for _k in ('shade', 'shadow_demon', 'quasit', 'imp', 'boggart'):
    KIND_FIELDS.setdefault(_k, {})['hides_in_dark'] = True

# --- Raise the Alarm (src/alarm.py): Juno's geese, Odin's ravens, the
# kobold's yap and the goblin's yell, the gnoll's whooping laugh (the
# hyena's), a scout's warning, a drilled hobgoblin's order, a thug's whistle,
# a cult's cry, the Stymphalian flock, the harpies' shriek, the
# poltergeist's knocking.
_ALARMS = {
    'kobold': (10, "{The} yaps a warning!", "Somewhere ahead, a shrill yapping."),
    'kobold_trapsetter': (10, "{The} shrieks a warning!", "Somewhere near, a shrill shriek."),
    'kobold_pack_leader': (12, "{The} barks an order, and the warren stirs!",
                           "A barked order echoes, and something stirs."),
    'goblin': (10, "{The} yells to the others!", "Somewhere near, a thin voice yells."),
    'goblin_sniper': (10, "{The} whistles shrilly!", "A shrill whistle, close by."),
    'gnoll': (12, "{The} lets out a whooping laugh!", "A whooping laugh echoes from somewhere near."),
    'orc_scout': (12, "{The} bellows a warning!", "A bellow of warning, not far off."),
    'hobgoblin': (10, "{The} shouts an order!", "Somewhere near, a harsh order is shouted."),
    'bandit_thug': (10, "{The} whistles for his mates!", "A sharp whistle, not far off."),
    'cult_initiate': (10, "{The} cries out: \"An intruder!\"", "A voice cries out: \"An intruder!\""),
    'hugin_raven': (14, "{The} croaks and wheels away to tell!", "A raven croaks somewhere overhead."),
    'stymphalian_bird': (12, "{The} screeches, and the flock answers!", "A metallic screech rings out."),
    'harpy': (12, "{The} shrieks!", "A shriek, somewhere near."),
    'poltergeist': (10, "Something knocks loudly on the walls.", "Something knocks loudly on the walls."),
}
for _k, (_r, _line, _unseen) in _ALARMS.items():
    KIND_FIELDS.setdefault(_k, {})['alarm'] = {'radius': _r, 'line': _line, 'line_unseen': _unseen}

# --- Death Throes (src/death_throes.py): the bombardier beetle's spray
# (natural history), the burning skeleton and the molten elementals' last
# flare, the puffball and the myconids' spores, the plague corpse that
# bursts (the Black Death's fear of the dead), the jellies, the crystal
# ooze's shards. A share of each victim's own health.
_THROES = {
    'fire_beetle': {'type': 'fire', 'share': 0.05, 'radius': 1, 'effect': 'burning', 'effect_duration': 2,
                    'line': "{The}'s glands burst in a spray of fire!",
                    'warn_line': "{The}'s glands glow white-hot!"},
    'burning_skeleton': {'type': 'fire', 'share': 0.06, 'radius': 1, 'effect': 'burning', 'effect_duration': 2,
                         'line': "{The} bursts in a gout of flame!",
                         'warn_line': "Flames roar up through {the}'s ribs!"},
    'magma_elemental': {'type': 'fire', 'share': 0.08, 'radius': 1, 'effect': 'burning', 'effect_duration': 3,
                        'line': "{The} bursts in a spray of molten rock!",
                        'warn_line': "{The}'s crust cracks and glows white."},
    'lava_elemental': {'type': 'fire', 'share': 0.10, 'radius': 2, 'effect': 'burning', 'effect_duration': 3,
                       'line': "{The} bursts, flinging lava all about!",
                       'warn_line': "{The} swells and glows, about to burst."},
    'myconid_worker': {'type': 'poison', 'share': 0.0, 'radius': 1, 'effect': 'hallucinating', 'effect_duration': 3,
                       'line': "{The} bursts in a cloud of spores!",
                       'warn_line': "{The}'s cap swells and puffs."},
    'myconid_sovereign': {'type': 'poison', 'share': 0.04, 'radius': 2, 'effect': 'confused', 'effect_duration': 2,
                          'line': "{The} bursts in a great cloud of spores!",
                          'warn_line': "{The}'s gills swell with spores."},
    'gas_spore': {'type': 'poison', 'share': 0.10, 'radius': 1, 'effect': 'poisoned', 'effect_duration': 3,
                  'line': "{The} bursts in a cloud of choking gas!",
                  'warn_line': "{The} swells tight as a drum."},
    'plague_zombie': {'type': 'poison', 'share': 0.04, 'radius': 1, 'effect': 'diseased', 'effect_duration': 4,
                      'line': "{The} bursts, spattering you with rot!",
                      'warn_line': "{The}'s belly swells, tight and green."},
    'zombie_hulk': {'type': 'poison', 'share': 0.05, 'radius': 1, 'effect': 'diseased', 'effect_duration': 6,
                    'line': "{The} bursts, spattering everything with rot!",
                    'warn_line': "{The}'s bloated hide splits and seeps."},
    'plague_ooze': {'type': 'poison', 'share': 0.06, 'radius': 1, 'effect': 'diseased', 'effect_duration': 8,
                    'line': "{The} bursts in a spray of plague!",
                    'warn_line': "{The} bubbles and heaves."},
    'toxic_jelly': {'type': 'poison', 'share': 0.05, 'radius': 1, 'effect': 'poisoned', 'effect_duration': 3,
                    'line': "{The} bursts in a spray of venom!",
                    'warn_line': "{The} quivers and turns a sickly green."},
    'crystal_ooze': {'type': 'pierce', 'share': 0.05, 'radius': 1, 'effect': 'bleeding', 'effect_duration': 3,
                     'line': "{The} shatters into flying shards!",
                     'warn_line': "{The} cracks and rings like glass."},
    'pazuzu_spawn': {'type': 'poison', 'share': 0.06, 'radius': 2, 'effect': 'diseased', 'effect_duration': 8,
                     'line': "{The} bursts in a hot wind of plague!",
                     'warn_line': "A sick wind gathers about {the}."},
}
for _k, _t in _THROES.items():
    KIND_FIELDS.setdefault(_k, {})['death_throes'] = _t

# --- Grave Rot (src/grave_rot.py; FIELDS: `disease_linger`, an int on the
# kind): how long a sickness lingers is the
# kind's own (its rider's turns, times this). Mummy rot does not heal until
# it is cured (the tomb curse); the plague-bringers (Pazuzu, Hel's
# sickbed, the plague ooze and witch, the corpse-gnawers of Nidhogg) carry
# a sickness that lasts; the ghouls' and the otyugh's grave-filth and the
# aboleth's slime fester. A rat's bite, a zombie's claw, a wererat's or a
# death dog's bite keep their own few turns.
_LINGER = {'mummy': 10, 'pazuzu_spawn': 8, 'hels_handmaid': 8, 'plague_ooze': 8,
           'plague_witch': 6, 'nidhogg_brood': 6, 'aboleth_lesser': 5, 'otyugh': 5,
           'demon_general': 5, 'abyssal_dragon': 5, 'plague_zombie': 4, 'harrow_witch': 4,
           'ghast_eater': 4, 'huecuva': 3}
for _k, _n in _LINGER.items():
    KIND_FIELDS.setdefault(_k, {})['disease_linger'] = _n

# --- Back to the Web (src/relurk.py): spiders go back to their webs, the
# lurkers back to the ceiling, the jorogumo to her waterfall.
for _k in ('piercer', 'darkmantle', 'lurker_above', 'trapper', 'cloaker', 'giant_spider',
           'cave_spider', 'spider_queen', 'web_spinner', 'ettercap', 'jorogumo', 'crypt_thing'):
    KIND_FIELDS.setdefault(_k, {})['relurks'] = True

# --- Shove (src/shove.py): giants' clubs and fists (Thor at Utgard-Loki's
# hall), the ogres' clubs, the Minotaur's horns, a troll's smash, a bear's
# blow, a golem's slam. The giants aim (the trickster giants of the north).
_SHOVES = {
    ('hill_giant', 'Greatclub'): {'chance': 0.3, 'aim': True},
    ('stone_giant', 'Stone Fist'): {'chance': 0.3, 'aim': True},
    ('frost_giant', 'Ice Club'): {'chance': 0.3, 'aim': True},
    ('cyclops_brute', 'Fist Smash'): {'chance': 0.3},
    ('ettin', 'Left Club'): {'chance': 0.25},
    ('ogre', 'Club Smash'): {'chance': 0.25},
    ('two_headed_ogre', 'Right Club'): {'chance': 0.25},
    ('minotaur', 'Gore'): {'chance': 0.35},
    ('minotaur_warrior', 'Gore'): {'chance': 0.3},
    ('troll_brute', 'Smash'): {'chance': 0.25},
    ('war_troll', 'Warclub'): {'chance': 0.25},
    ('cave_bear', 'Claw'): {'chance': 0.2},
    ('iron_golem', 'Slam'): {'chance': 0.25},
    ('stone_golem', 'Earth Slam'): {'chance': 0.3},
}
for _key, _sp in _SHOVES.items():
    ATTACK_FIELDS.setdefault(_key, {})['shove'] = _sp

TELLS_NEW.update({
    'light_shy': ('regeneration', {
        'sign': "{The} squints and turns {his} face from every lamp.",
        'does': "{He} hates a bright light: in its glare {he} strikes worse, and a troll's wounds will not close in it.",
        'counter': "Carry a lit light or cast Light, and fight {him} inside its glow. The Light spell's glare hurts {him} most.",
    }),
    'snuffs_light': ('sp_drain', {
        'sign': "The flames near {the} gutter and bow.",
        'does': "{His} blows can put out the light in your hand, and a wet wick will not light again at once.",
        'counter': "Keep a spare light, or carry one that never goes out.",
    }),
    'raises_alarm': ('pack_bay', {
        'sign': "{The} keeps looking about, ready to shout.",
        'does': "When {he} first sees you {he} raises the alarm, and the rest come running.",
        'counter': "Kill or silence {him} before {he} sees you, or move quietly and keep out of sight.",
    }),
    'death_throes': ('splits', {
        'sign': "{The} looks swollen, as if something inside {him} wants out.",
        'does': "When {he} dies {he} bursts, and everything beside {him} is caught in it.",
        'counter': "When {he} swells, step back or finish {him} from a distance.",
    }),
    'relurks': ('can_phase_blink', {
        'sign': "Old webbing and husks hang above where {the} waits.",
        'does': "Hurt and out of your sight, {he} goes back into hiding to drop on you again.",
        'counter': "Finish {him} before {he} gets away, or carry a light into the dark where {he} hides.",
    }),
    'hides_in_dark': ('relurks', {
        'sign': "{The} is hard to keep in view, as if the shadows lean toward {him}.",
        'does': "When {he} breaks off {he} hides in the dark, unseen, until {he} strikes again.",
        'counter': "A lit light leaves {him} no dark to hide in.",
    }),
    'shove': ('can_charge', {
        'sign': "{The} is built like a battering ram.",
        'does': "{His} blows can throw you back a step, and a clever one throws you into what hurts.",
        'counter': "Fight {him} with your back to a wall, and keep clear of fire and pits.",
    }),
})


def apply_lore(d: dict) -> list:
    changes = []
    for kind, (old, new) in LORE_EDITS.items():
        lore = d[kind].get('lore', '')
        if new in lore:
            continue
        if lore.count(old) != 1:
            raise SystemExit(f"{kind}: lore text {old!r} not found once")
        d[kind]['lore'] = lore.replace(old, new)
        changes.append(f"{kind}: lore")
    return changes


def _dump_monsters(d) -> str:
    return (json.dumps(d, indent=2, ensure_ascii=False) + '\n').replace('\n', '\r\n')


def apply_monsters(d: dict) -> list:
    changes = []
    for kind, fields in KIND_FIELDS.items():
        m = d.get(kind)
        if not isinstance(m, dict):
            raise SystemExit(f"no kind {kind!r} in monsters.json")
        for k, v in fields.items():
            if v is None:
                if k in m:
                    del m[k]
                    changes.append(f"{kind}: -{k}")
            elif m.get(k) != v:
                m[k] = v
                changes.append(f"{kind}: {k}={v!r}")
    for (kind, aname), fields in ATTACK_FIELDS.items():
        m = d.get(kind)
        if not isinstance(m, dict):
            raise SystemExit(f"no kind {kind!r} in monsters.json")
        atk = next((a for a in m.get('attacks') or () if a.get('name') == aname), None)
        if atk is None:
            raise SystemExit(f"{kind} has no attack {aname!r}")
        for k, v in fields.items():
            if v is None:
                if k in atk:
                    del atk[k]
                    changes.append(f"{kind}/{aname}: -{k}")
            elif atk.get(k) != v:
                atk[k] = v
                changes.append(f"{kind}/{aname}: {k}={v!r}")
    return changes


def _entry_text(key: str, e: dict) -> str:
    body = ',\r\n'.join(f'      {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}'
                        for k, v in e.items())
    return f'    {json.dumps(key)}: {{\r\n{body}\r\n    }}'


def apply_tells(raw: str) -> tuple:
    """(new text, changes). Text edits keep the file's own layout."""
    d = json.loads(raw)
    changes = []
    for key, (after, e) in TELLS_NEW.items():
        if key in d['order']:
            continue
        if after not in d['order']:
            raise SystemExit(f"tells order has no {after!r}")
        old = f'"{after}",'
        if raw.count(old) != 1:
            raise SystemExit(f"tells order: {old} found {raw.count(old)} times")
        raw = raw.replace(old, f'"{after}", "{key}",', 1)
        # the entry goes last in 'effects'
        tail = raw.rstrip()
        assert tail.endswith('}\r\n}') or tail.endswith('}\n}') or tail.endswith('}')
        i = raw.rindex('    }\r\n  }')
        raw = raw[:i] + '    },\r\n' + _entry_text(key, e) + raw[i + len('    }'):]
        changes.append(f"tell {key}")
        d = json.loads(raw)                 # the next one may go after this one
    d = json.loads(raw)
    for key, parts in TELLS_CHANGED.items():
        for part, text in parts.items():
            cur = d['effects'][key].get(part)
            if cur == text:
                continue
            old = f'"{part}": {json.dumps(cur, ensure_ascii=False)}'
            seg_start = raw.index(f'    "{key}": {{')
            seg_end = raw.index('    }', seg_start)
            seg = raw[seg_start:seg_end]
            if seg.count(old) != 1:
                raise SystemExit(f"tell {key}.{part}: old text not found once")
            seg = seg.replace(old, f'"{part}": {json.dumps(text, ensure_ascii=False)}')
            raw = raw[:seg_start] + seg + raw[seg_end:]
            changes.append(f"tell {key}.{part}")
    json.loads(raw)
    return raw, changes


def main(argv) -> int:
    write = '--write' in argv
    raw_m = MONSTERS.read_text(encoding='utf-8')
    d = json.loads(raw_m)
    ch_m = apply_monsters(d) + apply_lore(d)
    raw_t = TELLS.read_bytes().decode('utf-8')
    new_t, ch_t = apply_tells(raw_t)
    for c in ch_m + ch_t:
        print(c)
    print(f"{len(ch_m)} monster changes, {len(ch_t)} tell changes")
    if write:
        if ch_m:
            with open(MONSTERS, 'w', encoding='utf-8', newline='') as f:
                f.write(_dump_monsters(d))
        if ch_t:
            with open(TELLS, 'w', encoding='utf-8', newline='') as f:
                f.write(new_t)
        print("written")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
