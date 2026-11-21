#!/usr/bin/env python
"""The late game's instruments (2026-11-20, overnight): banes by lore, deep
health per kind, supply that follows residence, signature attacks that need
their counter, and learning across runs, as simulator knobs for the sweep
toward a late-game sweet spot (_mm_2026_11_19/late/STRUCTURAL_PROPOSAL.md,
banes/BANE_SPEC.md). They are instruments, not tuning: every knob defaults
off, and a default cell is the simulator exactly as it was (the hooks only
count). Nothing here edits src/ or data/.

THE PROJECT RULE IS "LORE, NOT FLOOR". The game never scales damage or
health by the floor at runtime, and no blanket multiplier is written into the
data either (CLAUDE.md, tests/test_lore_not_floor.py). The HP stand-in below
(hp_target) is a MEASUREMENT stand-in inside the simulator only: it writes,
once per kind at load, the health a later lore pass would write per kind from
that kind's own affinity, so the sweep can see where the curve wants to be. It
is never a rule for the game and never a schedule to paste into the data.

Knobs (merged into difficulty_sim.KNOB_DEFAULTS; every default is off)
------------------------------------------------------------------------
  overlay      A  path to a JSON of per-kind field overrides,
                  {kind: {field: value}} (weaknesses, resistances, shrugs_off,
                  hp, status_weak, attacks ...; null removes a field; a
                  top-level key starting "_" is a note, "_meta" may list
                  "new_substances"). A researcher's file in the BANE_SPEC
                  shape ({kind: {..., "proposed": {...}}}) is read through
                  its "proposed" lists. Unknown kinds are an error. It is
                  merged into data/monsters.json BEFORE any floor is made,
                  in every worker (run_cell calls install): the merged file
                  goes to <tempdir>/pq_sim_late/ and paths.data_path hands it
                  to every reader of data/monsters.json (dungeon's spawn pools
                  and so the Monster prototypes, level_manager's mini-bosses
                  and seal demons, boss_levels, black_knight, game_magic's
                  summons, container_system's mimics, affinity's refresh,
                  kind_data, family_lore, lore_powers, food_system, monster's
                  pronouns, domain_counters, the simulator's locusts); every
                  lru_cache in src/ and the tables read once are cleared.
  hp_target    E  > 0: the HP stand-in. Each ordinary kind (no boss, seal
                  demon, quest or allied kind; mini-bosses only with
                  hp_minis=1) that spawns and peaks at hp_from or deeper gets
                  its HP rewritten ONCE at load so that the careful hero's
                  expected blows with its best REACHABLE weakness (one a
                  weapon form, a weapon material, a coating or thrown flask, a
                  blessing, a spell element or a substance the overlay
                  declares can meet) is hp_target; a kind with none gets
                  hp_plain blows at its plain step (its best form's step).
                  The blow is the careful hero's at the kind's PEAK floor
                  (the table below), so a kind's health depends on its
                  nature and depth, never on the floor it is met on. The new
                  HP of every kind goes to a CSV (res['late']['hp_csv'], or
                  `--hp-csv`).
  hp_plain     E  blows at the plain step for a kind with no reachable weakness
  hp_from      E  the shallowest peak floor rewritten (21: floors 1-20 untouched)
  hp_minis     E  1 = mini-bosses too
  hp_table     E  path to a careful-blow table ('' = sim_late_blow.json here;
                  `--measure` writes a new one)
  supply       D  > 0: supply follows residence (SUPPLY below); 0 is today
  supply_ahead D  floors past this one whose residents the supply serves (5)
  sig          F  > 0: a signature attack (delivery gaze, voice or breath,
                  type drain, a heat or cold aura) on a hero WITHOUT its
                  counter does x sig damage; with the counter it is as today.
                  Counted in every cell (sig_bare, sig_ctr), multiplied only
                  when on.
  prep         F  1 = with sig or supply on, the careful kid (tactics=1)
                  readies his counters for the signature attacks of a group
                  he knows (or remembers): a mirror shield on when gazers are
                  half the group or more (it costs his shield's AC), wax
                  in for a voice, a resistance potion or a ready resistance
                  dish for a breath or an aura, a drain-resistance dish for a
                  drainer; all put back after the fight. 0 = he does not.
  recoat       D  1 = in a fight the careful kid (tactics=1) also coats his
                  blade for the foe in front of him (his action), by the rule
                  that coats it between fights (Run._coat_for: a kind he
                  knows, that will take more than one blow, a coating a
                  quarter better than his blade). 0 = between fights only, for
                  the group's first foe (the simulator as it was).
  campaign     H  N > 1: each seed line plays N runs in sequence, each to its
                  first death or the last floor; after each, the kid remembers
                  the kind that killed him and the 3 that hurt him most (as if
                  the death screen had named their bane): they count as known
                  for tactics (Run._knows) and prep, and supply buys for
                  them. The cell's trials are seed lines x N; res['late']
                  ['campaign'] holds survival and floors reached by run index.
String knobs (overlay, hp_table) take a path: no commas in it (the --knobs
text is split on commas; a Windows drive's colon is fine).

THE CAREFUL BLOW (E; measured with `--measure`: profile mastery, the kid model
at balance_study.KID_FAST, engagers 2, floors 1-100, 60 runs; written to
sim_late_blow.json). The melee blow of the careful kid on ordinary foes,
divided by the form x substance step it met (the plain blow), by 10-floor
band; "miss" is the share of attack actions whose first answer was wrong:

    floors   landed blow   miss   blow with misses   monsters met / floor
      1-10            77   5.3%                73         12.4
     11-20           259   5.7%               244         17.4
     21-30           733   8.8%               668         18.2
     31-40         1,400  10.7%             1,250         20.5
     41-50         2,324  13.2%             2,016         21.2
     51-60         3,270  14.1%             2,811         22.4
     61-70         6,009  15.0%             5,108         21.2
     71-80         9,579  14.8%             8,164         23.4
     81-90        13,874  14.5%            11,861         22.9
     91-100       19,414  14.7%            16,564         22.7

Tier 1 is floors 1-20 (its two rows), ..., tier 5 floors 81-100. Between band
centres the blow is interpolated in log space at the kind's PEAK floor; the
blows-to-kill curve of a band comes from its own landed blows and misses
(Monte Carlo with a fixed seed: no draw from the simulator's random stream).

SUPPLY (D). Each floor F the residents of floors F..F+supply_ahead (the real
spawn pools, domain_counters._floor_kinds: the overlay's kinds, the HP
stand-in's health) set the demand: for each floor f of the window (gate-boss
floors left out), monsters met on f (monsters_met in the table, the baseline's
ordinary monsters a floor) x each kind's share of the pool x the blows its
answered fight takes (its HP over the careful blow at its peak times its
answered step, through the blows-to-kill curve), split evenly over the kind's
carriable weaknesses (each non-form substance it is weak to that a coating can
carry; silver or cold iron by its tags as well, the materials'
effective_against). The floor offers supply x that window demand / (the
window's floors), so over a run supply=1 offers about as many carried blows
as the residents need, each arriving up to supply_ahead floors before its
kinds: the window decides WHICH substances, the division keeps the total
honest. Carriers are made whole (a coating's blows; the fraction carries
over), each to one channel by SUPPLY_SPLIT (deterministic, no draw): floor
loot (found as a floor's loot is: loot_fraction), a container (opens_chests
and one economics question at the floor's tier) or the stall (the run's
trader floors, traders.roll_plan: what accumulated since the last stall is set
out; with traders=0 it is unsold). At the stall a kid with tactics=1 buys, at
economy.stock_price with the half-floor reserve, a carrier whose substance a
known or remembered resident ahead is weak to, or the one the trader names
(the window's commonest), while he carries less of it than the window needs;
the rest is unsold. A smith (silvering or cold-iron service) works the
domain's commonest bane that is not an element into the wielded weapon for
good, at the silvering price (smithing.inlay's rule: a common weapon with no
inlay yet). Counters come the same three ways: a mirror shield once gazers
live ahead, beeswax earplugs once voices do, a resistance potion an encounter
with a fire, cold or lightning breath or aura (the game has no drain, poison
or acid potion: those encounters are counted as "no counter"). The counters
and potions weigh: Run._fit_pack leaves the spare ones after the flasks
(potions first, then the mirror, the wax last), as it leaves any load past
his line.
Report (blows): found, bought, inlays, used (a coated blow or a thrown flask
that met the weakness), wasted (a coated blow that met none, a coating scraped
off for another, a carrier shed for weight), left (carried when the run
ended), short (a blow that met no weakness on a kind with a carriable one).

CARRIERS (C). A substance the game has flasks for uses them (silver dust;
holy water, the Water of Siloam, the Water of Life; fire oil, Greek fire,
Medea's fire; frost salts; the venoms; acid is thrown). Any other substance id
(cold_iron, iron, lightning, bronze, bane_a ...) is the holy series by depth
(12, 16, 20 blows from floors 1, 25, 62) with its substance swapped and no
throw (make_coating), or a thrown flask (make_throw: damage by depth from the
acid series). A coating meets a weakness through the real
combat.weapon_type_multiplier (a coating is substance: combat._substances_of).
A smith's inlay of a new id registers it as a weapon material with no
effective_against (combat._MATERIAL_EFFECTIVE_AGAINST, where silver is), then
works it in as smithing.inlay does (into the weapon's damage_types).

SIGNATURE ATTACKS (F). The game has no runtime one-turn cap: "25% of the
hero's health a monster turn" is an authoring rule of the lore pass
(docs/design/MONSTER_LORE_PASS_2026_11_19.md section 1, measured by
tools/balance/monster_bands.turn_damage), written into each kind's dice;
Monster.attack and Player.take_damage clamp nothing. The simulator's own
dmg_cap knob (default off) is the only runtime clamp, and a bare signature
attack skips it (its written dice). The counters: gaze - counters.blocks_gaze
(a mirror shield, the Aegis), petrification proof, Perseus' Shield, blindness;
voice - counters.ears_stopped (the wax in); breath, aura - a resistance to its
element (a status from a potion or a dish, gear, a lining, a chain
resistance); drain - drain resistance (drain_resist).

THE KITCHEN'S RESISTANCE DISHES (F, checked 2026-11-20): the simulator cooks
them only by chance (a special dish is a spare single or a multi-dish chosen
by kitchen.dish_value at the floor's end), never for what lives ahead, and
their 60-240 turns mostly run out on the walk before the fight they would
answer. `prep` is the careful kid who cooks one as the creature comes in sight.

PROFILES (G): `cookonly` is mastery (the same kitchen and saver, gear, rest,
prayer, pet, quests, altars, magic, practice, and the traders' heal, potions
and sharpening) with no tactics: no study or probe (families=0), no coating,
flask, arsenal swap, stance, stall counter or smith inlay (tactics=0), and he
buys no answers (supply's stall needs tactics=1). `walkthrough` buys and uses
nothing either: a coating he finds is carried and never used.

Reading a cell: `py tools/balance/sim_late.py --summary <cell.pkl> [...]`.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
import re
import sys
import tempfile
from types import SimpleNamespace

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO = os.path.dirname(os.path.dirname(_HERE))
_SRC = os.path.join(_REPO, 'src')
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

KNOBS = {
    'overlay': '',
    'hp_target': 0.0,
    'hp_plain': 2.0,
    'hp_from': 21,
    'hp_minis': 0,
    'hp_table': '',
    'supply': 0.0,
    'supply_ahead': 5,
    'sig': 0.0,
    'prep': 1,
    'recoat': 0,
    'campaign': 1,
}
STRING_KNOBS = frozenset(('overlay', 'hp_table'))

FORMS = ('slash', 'pierce', 'blunt')
NAMED_FIELDS = ('is_boss', 'is_mini_boss', 'is_seal_demon', 'quest_only', 'unique', 'is_allied')
# Weakness types no carrier meets (a spell's, or nothing's): never reachable.
SPELL_ONLY = frozenset(('magic', 'shadow', 'drain', 'necrotic', 'radiant', 'force', 'psychic',
                        'sonic', 'physical', 'starvation', 'arcane', 'chaos', 'void'))
ELEMENTS = frozenset(('fire', 'cold', 'lightning', 'acid', 'poison', 'holy'))
INLAY_GAME = ('silver', 'cold_iron')         # smithing.INLAY_SUBSTANCES, met by tags as well
BOSS_FLOORS = (20, 40, 60, 80, 100)
SUPPLY_SPLIT = (('loot', 0.35), ('chest', 0.15), ('stall', 0.50))
SIG_KINDS = ('gaze', 'voice', 'breath', 'drain', 'aura')
# The flask series the game has, by the depth each first appears (min_level).
COAT_SERIES = {
    'silver': (('silver_dust', 1),),
    'holy': (('flask_of_holy_water', 1), ('water_of_siloam', 25), ('water_of_life', 62)),
    'fire': (('flask_of_fire_oil', 1), ('greek_fire', 20), ('medeas_fire', 50)),
    'cold': (('frost_salts', 1),),
    'poison': (('viper_venom', 1), ('upas_latex', 44), ('hydras_blood', 55), ('eitr_venom', 80)),
}
THROW_SERIES = {'acid': (('flask_of_acid', 1), ('aqua_regia', 30), ('alkahest', 66))}
CLONE_SERIES = COAT_SERIES['holy']           # any other substance: the holy series, swapped
RESIST_POTIONS = {'fire': 'potion_of_fire_resistance', 'cold': 'potion_of_cold_resistance',
                  'lightning': 'potion_of_shock_resistance'}
RESIST_STATUS = {'fire': 'fire_resist', 'cold': 'cold_resist', 'lightning': 'shock_resist',
                 'poison': 'poison_resist', 'acid': 'acid_resist', 'drain': 'drain_resist',
                 'magic': 'magic_resist'}
BLOW_FILE = os.path.join(_HERE, 'sim_late_blow.json')
_EPS = 1e-9


# =============================================================================
# Small helpers
# =============================================================================

_DICE = re.compile(r'^\s*(\d+)\s*[dD]\s*(\d+)\s*([+-]\s*\d+)?\s*$')


def dice_mean(expr) -> float:
    if isinstance(expr, (int, float)):
        return float(expr)
    s = str(expr or '0').strip()
    if s.lstrip('-').isdigit():
        return float(s)
    m = _DICE.match(s)
    if not m:
        return 0.0
    n, d = int(m.group(1)), int(m.group(2))
    k = int((m.group(3) or '0').replace(' ', ''))
    return n * (d + 1) / 2.0 + k


def peak_of(defn) -> int:
    return int(defn.get('peak_floor') or defn.get('min_level') or 1)


def tier_of(floor: int) -> int:
    return (max(1, int(floor)) - 1) // 20 + 1


def is_named_def(defn, minis: bool = False) -> bool:
    for f in NAMED_FIELDS:
        if f == 'is_mini_boss' and minis:
            continue
        if defn.get(f):
            return True
    return False


def spawns(defn) -> bool:
    return float(defn.get('peak_weight', 0) or 0) > 0


def real_monsters_path() -> str:
    return os.path.normpath(os.path.join(_REPO, 'data', 'monsters.json'))


_REAL_DEFS = None


def real_defs() -> dict:
    """data/monsters.json as written (read once; never the overlay)."""
    global _REAL_DEFS
    if _REAL_DEFS is None:
        with open(real_monsters_path(), encoding='utf-8') as f:
            _REAL_DEFS = json.load(f)
    return _REAL_DEFS


def _mon(defn) -> SimpleNamespace:
    return SimpleNamespace(weaknesses=list(defn.get('weaknesses') or ()),
                           resistances=list(defn.get('resistances') or ()),
                           shrugs_off=list(defn.get('shrugs_off') or ()),
                           tags=list(defn.get('tags') or ()))


# =============================================================================
# A. The overlay, in every worker
# =============================================================================

_STATE = {'key': None, 'file': None, 'defs': None, 'hp_rows': None, 'hp_csv': None,
          'new_subs': frozenset(), 'real_dp': None, 'target': None, 'overlay_kinds': 0}
_DERIVED = {}


def load_overlay(path: str) -> dict:
    """{kind: {field: value}} from an overlay or a researcher's file."""
    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    out = {}
    for kind, v in raw.items():
        if str(kind).startswith('_') or not isinstance(v, dict):
            continue
        fields = v['proposed'] if isinstance(v.get('proposed'), dict) else v
        out[str(kind)] = dict(fields)
    return out


def overlay_meta(path: str) -> dict:
    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    return raw.get('_meta') or {}


def merge_overlay(defs: dict, ov: dict) -> dict:
    unknown = sorted(k for k in ov if k not in defs)
    if unknown:
        raise ValueError(f"overlay names kinds data/monsters.json does not have: {unknown[:8]}"
                         + (f" (+{len(unknown) - 8} more)" if len(unknown) > 8 else ''))
    out = dict(defs)
    for kind, fields in ov.items():
        d = dict(defs[kind])
        for k, v in fields.items():
            if v is None:
                d.pop(k, None)
            else:
                d[k] = copy.deepcopy(v)
        out[kind] = d
    return out


def known_carried() -> frozenset:
    """Substances (not forms) some carrier of the game meets: the weapon
    materials, the flasks' coatings and throws, a blessing, the spell elements."""
    v = _DERIVED.get('known')
    if v is not None:
        return v
    import combat
    import coatings
    combat._load_material_tags()
    out = set(combat._MATERIAL_EFFECTIVE_AGAINST) | set(ELEMENTS)
    for d in (coatings.flask_defs() or {}).values():
        if not isinstance(d, dict):
            continue
        for key, field in (('coat', 'substance'), ('throw', 'damage_type')):
            s = (d.get(key) or {}).get(field)
            if s:
                out.add(str(s))
    v = _DERIVED['known'] = frozenset(out - set(FORMS) - SPELL_ONLY)
    return v


def declared_new(ov: dict, meta: dict) -> frozenset:
    """The new substances an overlay brings: any weakness it writes that no
    carrier of today meets (and is not a spell's), and _meta.new_substances."""
    have = known_carried()
    out = set(str(s) for s in (meta.get('new_substances') or ()))
    for fields in ov.values():
        for s in fields.get('weaknesses') or ():
            s = str(s)
            if s not in have and s not in FORMS and s not in SPELL_ONLY:
                out.add(s)
    return frozenset(out)


def reachable() -> frozenset:
    """Every substance a careful hero can bring (E's 'reachable'); supply
    makes carriers for the same set."""
    return known_carried() | _STATE['new_subs']


def _key(knobs: dict):
    ov = str(knobs.get('overlay') or '')
    hp = float(knobs.get('hp_target') or 0.0)
    if not ov and hp <= 0:
        return None
    parts = []
    if ov:
        ap = os.path.abspath(ov)
        st = os.stat(ap)
        parts.append(('ov', ap, st.st_mtime_ns, st.st_size))
    if hp > 0:
        tbl = str(knobs.get('hp_table') or '')
        parts.append(('hp', hp, float(knobs.get('hp_plain', 2.0)), int(knobs.get('hp_from', 21)),
                      int(knobs.get('hp_minis', 0)), os.path.abspath(tbl) if tbl else '',
                      os.stat(tbl).st_mtime_ns if tbl else 0))
    return tuple(parts)


def _redirect(*parts):
    real = _STATE['real_dp']
    p = real(*parts)
    f = _STATE['file']
    if f and os.path.normcase(p) == _STATE['target']:
        return f
    return p


def _patch_paths() -> None:
    import paths
    if _STATE['real_dp'] is None:
        _STATE['real_dp'] = paths.data_path
        _STATE['target'] = os.path.normcase(paths.data_path('data', 'monsters.json'))
    real = _STATE['real_dp']
    paths.data_path = _redirect
    for mod in list(sys.modules.values()):
        try:
            if getattr(mod, 'data_path', None) is real:
                setattr(mod, 'data_path', _redirect)
        except Exception:
            pass


def _unpatch_paths() -> None:
    real = _STATE['real_dp']
    if real is None:
        return
    import paths
    paths.data_path = real
    for mod in list(sys.modules.values()):
        try:
            if getattr(mod, 'data_path', None) is _redirect:
                setattr(mod, 'data_path', real)
        except Exception:
            pass


_RESETS = {'kind_data': ('_DEFS',), 'family_lore': ('_KINDS',),
           'food_system': ('_monster_floor_cache',), 'lore_powers': ('_DEFS',),
           'monster': ('_KIND_PRONOUNS',)}


def clear_caches() -> None:
    """Every lru_cache in src/, and the monster tables read once."""
    src = os.path.normcase(os.path.abspath(_SRC))
    for name, mod in list(sys.modules.items()):
        try:
            f = getattr(mod, '__file__', None) or ''
            if not f or not os.path.normcase(os.path.abspath(f)).startswith(src):
                continue
            items = list(vars(mod).items())
        except Exception:
            continue
        for _attr, obj in items:
            try:
                cc = getattr(obj, 'cache_clear', None)
                if callable(cc) and getattr(obj, '__module__', None) == name:
                    cc()
            except Exception:
                pass
    for mn, attrs in _RESETS.items():
        m = sys.modules.get(mn)
        if m is not None:
            for a in attrs:
                if hasattr(m, a):
                    setattr(m, a, None)
    ds = sys.modules.get('difficulty_sim')
    if ds is not None and isinstance(getattr(ds, '_POOL_CACHE', None), dict):
        ds._POOL_CACHE.clear()
    _DERIVED.clear()


def _write(defs, tag: str = 'monsters', suffix: str = '.json', blob: bytes = None) -> str:
    """A content-named file in <tempdir>/pq_sim_late (never in the repo)."""
    if blob is None:
        blob = json.dumps(defs, sort_keys=True, ensure_ascii=False).encode('utf-8')
    h = hashlib.sha256(blob).hexdigest()[:16]
    d = os.path.join(tempfile.gettempdir(), 'pq_sim_late')
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f'{tag}_{h}{suffix}')
    if not os.path.exists(path):
        tmp = f'{path}.{os.getpid()}.tmp'
        with open(tmp, 'wb') as f:
            f.write(blob)
        try:
            os.replace(tmp, path)
        except OSError:
            if not os.path.exists(path):
                raise
            os.remove(tmp)
    return path


def install(knobs: dict) -> None:
    """Make this process's monster data the overlay's (and the HP stand-in's),
    or put it back as written. Idempotent; run_cell calls it in every worker
    before the first floor is made."""
    install_runtime()
    key = _key(knobs)
    if key == _STATE['key']:
        return
    if key is None:
        uninstall()
        return
    _unpatch_paths()
    _STATE.update(file=None, defs=None, new_subs=frozenset())
    clear_caches()
    defs = real_defs()
    ov_path = str(knobs.get('overlay') or '')
    n_ov = 0
    if ov_path:
        ov = load_overlay(ov_path)
        defs = merge_overlay(defs, ov)
        _STATE['new_subs'] = declared_new(ov, overlay_meta(ov_path))
        n_ov = len(ov)
    rows = None
    if float(knobs.get('hp_target') or 0) > 0:
        defs, rows = hp_standin(defs, knobs)
    path = _write(defs)
    csv = _write(None, 'hp', '.csv', blob=hp_csv_text(rows).encode('utf-8')) if rows is not None else None
    _STATE.update(key=key, file=path, defs=defs, hp_rows=rows, hp_csv=csv, overlay_kinds=n_ov)
    _patch_paths()
    clear_caches()


def uninstall() -> None:
    """The data as written again (a no-op when nothing is installed)."""
    if _STATE['key'] is None and _STATE['file'] is None:
        return
    _STATE.update(key=None, file=None, defs=None, hp_rows=None, hp_csv=None,
                  new_subs=frozenset(), overlay_kinds=0)
    _unpatch_paths()
    clear_caches()


def active_defs() -> dict:
    return _STATE['defs'] if _STATE['defs'] is not None else real_defs()


def info() -> dict:
    """What this process has installed, for the cell's result."""
    return dict(overlay_file=_STATE['file'], hp_csv=_STATE['hp_csv'],
                overlay_kinds=_STATE['overlay_kinds'], new_substances=sorted(_STATE['new_subs']),
                hp_rewritten=len(_STATE['hp_rows'] or ()))


# =============================================================================
# E. The careful blow and the HP stand-in
# =============================================================================

_TABLE = {}


def blow_table(path: str = '') -> dict:
    path = os.path.abspath(path or BLOW_FILE)
    t = _TABLE.get(path)
    if t is None:
        with open(path, encoding='utf-8') as f:
            t = json.load(f)
        t['_curves'] = {}
        _TABLE[path] = t
    return t


def _band_row(table: dict, floor: int) -> dict:
    rows = table['bands']
    for r in rows:
        if r['lo'] <= floor <= r['hi']:
            return r
    return rows[0] if floor < rows[0]['lo'] else rows[-1]


def careful_blow(floor: int, table: dict = None) -> float:
    """The careful kid's landed blow (the plain blow, before the affinity step)
    at a floor, log-interpolated between band centres."""
    table = table or blow_table()
    pts = [((r['lo'] + r['hi']) / 2.0, max(1e-6, float(r['landed_mean']))) for r in table['bands']]
    f = float(floor)
    if f <= pts[0][0]:
        return pts[0][1]
    if f >= pts[-1][0]:
        return pts[-1][1]
    for (fa, va), (fb, vb) in zip(pts, pts[1:]):
        if fa <= f <= fb:
            t = (f - fa) / (fb - fa)
            return math.exp(math.log(va) + t * (math.log(vb) - math.log(va)))
    return pts[-1][1]


_XGRID = [0.05 * (1.12 ** i) for i in range(48)]       # 0.05 .. about 10 landed blows of HP
CURVE_TRIALS = 1000


def _curve(table: dict, row: dict) -> list:
    """[(x, E[attack actions to kill])], x the HP in the band's landed blows."""
    key = (row['lo'], row['hi'])
    c = table['_curves'].get(key)
    if c is not None:
        return c
    rng = random.Random(9173 + int(row['lo']))       # its own stream, never the simulator's
    q = sorted(float(v) for v in row['q']) or [1.0]
    miss = float(row.get('miss', 0.0))
    n = len(q)
    out = []
    for x in _XGRID:
        tot = 0
        for _ in range(CURVE_TRIALS):
            s, k = 0.0, 0
            while s < x and k < 60:
                k += 1
                if rng.random() >= miss:
                    s += q[min(n - 1, int(rng.random() * n))]
            tot += k
        out.append((x, tot / CURVE_TRIALS))
    for i in range(1, len(out)):                     # monotone (the Monte Carlo wobbles a hair)
        if out[i][1] < out[i - 1][1]:
            out[i] = (out[i][0], out[i - 1][1])
    table['_curves'][key] = out
    return out


def blows_to_kill(x: float, floor: int, table: dict = None) -> float:
    """Expected attack actions to kill HP of x landed blows (floor's band)."""
    table = table or blow_table()
    c = _curve(table, _band_row(table, floor))
    if x <= c[0][0]:
        return c[0][1]
    for (xa, ya), (xb, yb) in zip(c, c[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    (xa, ya), (xb, yb) = c[-2], c[-1]
    return yb + (yb - ya) * (x - xb) / (xb - xa)


def x_for_blows(b: float, floor: int, table: dict = None) -> float:
    """The HP, in the band's landed blows, the careful kid needs b attacks for."""
    table = table or blow_table()
    c = _curve(table, _band_row(table, floor))
    if b <= c[0][1]:
        return c[0][0]
    for (xa, ya), (xb, yb) in zip(c, c[1:]):
        if ya <= b <= yb:
            return xa + (xb - xa) * ((b - ya) / (yb - ya) if yb > ya else 0.0)
    (xa, ya), (xb, yb) = c[-2], c[-1]
    return xb + (xb - xa) * (b - yb) / max(_EPS, (yb - ya))


def steps(defn, reach=None) -> tuple:
    """(answered step or None, plain step) of a kind: its best form's step
    times the weak step when a reachable substance is a weakness, held to the
    cap; None when neither a form nor a substance meets a weakness."""
    import affinity
    import combat
    combat._load_material_tags()
    reach = reachable() if reach is None else reach
    mon = _mon(defn)
    tags = set(mon.tags)
    form = max(affinity.step(f, mon) for f in FORMS)
    sub = 1.0
    for s in sorted(reach):
        if affinity.step(s, mon, also_weak=combat._material_weak(s, tags)) > 1.0:
            sub = affinity.weak_step()
            break
    if form > 1.0 or sub > 1.0:
        return affinity.capped(form * sub), form
    return None, form


def hp_standin(defs: dict, knobs: dict) -> tuple:
    """defs with each ordinary deep kind's HP written for its answered fight,
    and the rows [(kind, peak, fight, step, old_hp, new_hp)]."""
    table = blow_table(str(knobs.get('hp_table') or ''))
    target = float(knobs['hp_target'])
    plain_b = float(knobs.get('hp_plain', 2.0))
    lo = int(knobs.get('hp_from', 21))
    minis = bool(int(knobs.get('hp_minis', 0) or 0))
    reach = reachable()
    out = dict(defs)
    rows = []
    for kind in sorted(defs):
        d = defs[kind]
        if not isinstance(d, dict) or 'hp' not in d:
            continue
        pk = peak_of(d)
        if pk < lo or is_named_def(d, minis):
            continue
        if not spawns(d) and not (minis and d.get('is_mini_boss')):
            continue
        ans, plain = steps(d, reach)
        if ans is not None:
            b, step, how = target, ans, 'answered'
        else:
            b, step, how = plain_b, plain, 'plain'
        x = x_for_blows(b, pk, table)
        new = max(1, int(round(x * careful_blow(pk, table) * step)))
        nd = dict(d)
        nd['hp'] = new
        out[kind] = nd
        rows.append((kind, pk, how, round(step, 4), round(dice_mean(d['hp']), 1), new))
    return out, rows


def hp_csv_text(rows) -> str:
    lines = ['kind,peak_floor,fight,step,old_hp,new_hp,ratio']
    for kind, pk, how, step, old, new in rows or ():
        lines.append(f"{kind},{pk},{how},{step:g},{old:g},{new},{new / max(1e-9, old):.3f}")
    return '\n'.join(lines) + '\n'


# =============================================================================
# The run's late-game state (Run.__init__ calls attach)
# =============================================================================

def attach(run) -> None:
    run.late = dict(carry={}, chan={}, stall=[], kit=[], mirror=None, plugs=None,
                    swapped=None, dmg_by_kind={}, prepped=False, ctr_carry={})
    run.late_memory = set()
    run.p.__dict__['_sim_late'] = run


def kit(run) -> list:
    """What the late knobs give him to carry besides the flasks (counters,
    resistance potions): Run._sync_pack puts it in the pack."""
    late = getattr(run, 'late', None)
    return list(late['kit']) if late else []


def shed_kit(run, over: float, fs) -> float:
    """Run._fit_pack, after the flasks: the counters he can spare, the
    resistance potions first, then the mirror shield, the wax last. Returns
    what is still over the line."""
    late = getattr(run, 'late', None)
    if not late or not late['kit']:
        return over
    order = {'potion': 0, 'mirror': 1, 'plugs': 2}
    for it in sorted(late['kit'], key=lambda x: order.get(what_counter(x), 0)):
        if over <= 0:
            break
        w = float(getattr(it, 'weight', 0) or 0)
        if w <= 0:
            continue
        late['kit'].remove(it)
        for k in ('mirror', 'plugs'):
            if late.get(k) is it:
                late[k] = None
        over -= w
        fs['left_lb'] = fs.get('left_lb', 0.0) + w
        fs['sup_shed_ctr'] = fs.get('sup_shed_ctr', 0) + 1
    return over


def _fsd(fs, key: str, sub, n=1) -> None:
    d = fs.setdefault(key, {})
    d[str(sub)] = d.get(str(sub), 0) + n


# =============================================================================
# C. Bane carriers for any substance id
# =============================================================================

def _series_pick(series, floor: int) -> str:
    pick = series[0][0]
    for tid, at in series:
        if floor >= at:
            pick = tid
    return pick


def _title(sub: str) -> str:
    return str(sub).replace('_', ' ').title()


def make_coating(sub: str, floor: int):
    """A coating of `sub` at this depth (a Flask): the game's own where it has
    one, else the holy series with the substance swapped."""
    import items
    sub = str(sub)
    if sub in COAT_SERIES:
        it = copy.copy(items.make_item_by_id('flask', _series_pick(COAT_SERIES[sub], floor)))
        it.coat = dict(it.coat or {})
        it.throw = dict(it.throw) if it.throw else None
    else:
        tpl = _series_pick(CLONE_SERIES, floor)
        it = copy.copy(items.make_item_by_id('flask', tpl))
        blows = int((it.coat or {}).get('blows', 12) or 12)
        it.id = f'sim_coat_{sub}_{tpl}'
        it.name = f'Flask of {_title(sub)}'
        it.unidentified_name = it.name
        it.coat = {'substance': sub, 'blows': blows}
        it.throw = None
    it.__dict__['_late_sub'] = sub
    return it


def _throw_damage(floor: int) -> int:
    """A thrown flask's damage at a depth: the acid series, log-interpolated."""
    import coatings
    pts = []
    for tid, _at in THROW_SERIES['acid']:
        d = (coatings.flask_defs().get(tid) or {}).get('throw') or {}
        pts.append((float(d.get('sized_at', 1)), float(d.get('damage', 1))))
    f = float(floor)
    if f <= pts[0][0]:
        return int(pts[0][1])
    for (fa, va), (fb, vb) in zip(pts, pts[1:]):
        if fa <= f <= fb:
            t = (f - fa) / (fb - fa)
            return int(round(math.exp(math.log(va) + t * (math.log(vb) - math.log(va)))))
    (fa, va), (fb, vb) = pts[-2], pts[-1]
    return int(round(vb * math.exp((math.log(vb) - math.log(va)) * (f - fb) / (fb - fa))))


def make_throw(sub: str, floor: int):
    """A thrown flask of `sub` (its damage by depth from the acid series)."""
    import items
    sub = str(sub)
    if sub in THROW_SERIES:
        it = copy.copy(items.make_item_by_id('flask', _series_pick(THROW_SERIES[sub], floor)))
        it.throw = dict(it.throw or {})
    else:
        tpl = _series_pick(THROW_SERIES['acid'], floor)
        it = copy.copy(items.make_item_by_id('flask', tpl))
        it.id = f'sim_throw_{sub}_{tpl}'
        it.name = f'Flask of {_title(sub)}'
        it.unidentified_name = it.name
        it.throw = {'damage_type': sub, 'damage': _throw_damage(floor), 'sized_at': int(floor)}
        it.coat = None
    it.__dict__['_late_sub'] = sub
    return it


def make_carrier(sub: str, floor: int):
    return make_throw(sub, floor) if sub in THROW_SERIES else make_coating(sub, floor)


def carrier_blows(it) -> int:
    c = getattr(it, 'coat', None)
    if isinstance(c, dict) and c.get('substance'):
        return int(c.get('blows', 12) or 12)
    return 1


def _unit_blows(sub: str, floor: int) -> int:
    key = ('unit', sub, _series_pick(THROW_SERIES.get(sub) or COAT_SERIES.get(sub) or CLONE_SERIES, floor))
    v = _DERIVED.get(key)
    if v is None:
        v = _DERIVED[key] = carrier_blows(make_carrier(sub, floor))
    return v


def register_substance(sub: str) -> None:
    """A new id worked into a weapon counts as its substance (not a form), as
    a weapon material's does: an entry with no effective_against."""
    import combat
    combat._load_material_tags()
    if sub not in combat._MATERIAL_EFFECTIVE_AGAINST and sub not in FORMS:
        combat._MATERIAL_EFFECTIVE_AGAINST[sub] = set()
        combat._MATERIAL_VULNERABILITIES.setdefault(sub, set())


def can_bane_inlay(w, sub: str) -> bool:
    import smithing
    if w is None or not sub or sub in ELEMENTS or sub in FORMS:
        return False
    if not smithing.is_common_weapon(w) or smithing.inlay_of(w):
        return False
    return sub != str(getattr(w, 'material', '')) and sub not in (w.damage_types or ())


def bane_inlay(w, sub: str) -> bool:
    """smithing.inlay for any substance id (the simulator's smith)."""
    import smithing
    if not can_bane_inlay(w, sub):
        return False
    if sub in smithing.INLAY_SUBSTANCES:
        return smithing.inlay(w, sub)
    register_substance(sub)
    w.inlay = sub
    w.damage_types = list(w.damage_types or ()) + [sub]
    return True


# =============================================================================
# D. Supply follows residence
# =============================================================================

def monsters_met(floor: int) -> float:
    for r in blow_table().get('monsters_met') or ():
        if r['lo'] <= floor <= r['hi']:
            return float(r['met'])
    return 15.0


def kind_subs(kind: str, defn: dict) -> tuple:
    """The carriable substances a kind is weak to (its weaknesses; silver or
    cold iron by its tags as well)."""
    key = ('subs', kind)
    v = _DERIVED.get(key)
    if v is not None:
        return v
    import combat
    combat._load_material_tags()
    sup = reachable()
    weak = [str(s) for s in (defn.get('weaknesses') or ()) if str(s) in sup]
    tags = set(defn.get('tags') or ())
    for s in INLAY_GAME:
        if s not in weak and combat._material_weak(s, tags):
            weak.append(s)
    v = _DERIVED[key] = tuple(dict.fromkeys(weak))
    return v


def answered_blows(kind: str, defn: dict) -> float:
    """Expected attack actions of the careful kid's answered fight."""
    key = ('bl', kind)
    v = _DERIVED.get(key)
    if v is None:
        pk = peak_of(defn)
        ans, plain = steps(defn)
        step = ans if ans is not None else plain
        x = dice_mean(defn.get('hp', 1)) / max(1e-6, careful_blow(pk) * max(0.05, step))
        v = _DERIVED[key] = max(1.0, blows_to_kill(x, pk))
    return v


def sig_of(atk: dict, guards=None) -> str:
    """'gaze', 'voice', 'breath', 'drain' or '' for one attack."""
    if guards is None:
        import guards
    if str(atk.get('type', '')) == 'drain':
        return 'drain'
    d = guards.delivery(atk)
    return d if d in ('gaze', 'voice', 'breath') else ''


def signatures(defn) -> dict:
    """{'gaze': 1, 'voice': 1, 'drain': 1, 'breath': {el: 1}, 'aura': {el: 1}}:
    a kind's signature attacks, by its own attacks and aura."""
    import guards
    out = {}
    for a in defn.get('attacks') or ():
        if not isinstance(a, dict):
            continue
        k = sig_of(a, guards)
        if k == 'breath':
            out.setdefault('breath', {})[str(a.get('type', 'fire'))] = 1
        elif k:
            out[k] = 1
    au = defn.get('aura')
    if isinstance(au, dict) and au.get('kind') in ('heat', 'cold'):
        el = str(au.get('type') or ('fire' if au['kind'] == 'heat' else 'cold'))
        out.setdefault('aura', {})[el] = 1
    return out


def window(floor: int, ahead: int) -> dict:
    """The residents of floors floor..floor+ahead: demand by substance (blows),
    the kinds weak to each, the encounters with each signature attack."""
    key = ('win', int(floor), int(ahead))
    w = _DERIVED.get(key)
    if w is not None:
        return w
    import domain_counters
    defs = active_defs()
    dem, kinds_by, enc = {}, {}, {}
    floors = [f for f in range(int(floor), min(100, int(floor) + int(ahead)) + 1)
              if f not in BOSS_FLOORS]
    for f in floors:
        met = monsters_met(f)
        for kind, share, d0 in domain_counters._floor_kinds(f):
            defn = defs.get(kind) or d0
            subs = kind_subs(kind, defn)
            if subs:
                b = answered_blows(kind, defn)
                for s in subs:
                    dem[s] = dem.get(s, 0.0) + met * share * b / len(subs)
                    kinds_by.setdefault(s, set()).add(kind)
            for sk, v in signatures(defn).items():
                for el in (v if isinstance(v, dict) else ('',)):
                    enc[(sk, el)] = enc.get((sk, el), 0.0) + met * share
    w = _DERIVED[key] = dict(demand=dem, kinds=kinds_by, enc=enc, floors=max(1, len(floors)))
    return w


def domain_bane(floor: int) -> str:
    """The commonest bane of the floor's 20-floor domain that a smith can work
    in (not an element)."""
    key = ('dom', tier_of(floor))
    v = _DERIVED.get(key)
    if v is None:
        lo = (tier_of(floor) - 1) * 20 + 1
        tot = {}
        for f in range(lo, lo + 20, 5):
            for s, b in window(f, 4)['demand'].items():
                if s not in ELEMENTS:
                    tot[s] = tot.get(s, 0.0) + b
        v = _DERIVED[key] = (max(sorted(tot), key=lambda s: tot[s]) if tot else '')
    return v


def _channel(run, sub: str) -> str:
    ch = run.late['chan'].setdefault(sub, {c: 0.0 for c, _ in SUPPLY_SPLIT})
    for c, sh in SUPPLY_SPLIT:
        ch[c] += sh
    pick = max((c for c, _ in SUPPLY_SPLIT), key=lambda c: ch[c])
    ch[pick] -= 1.0
    return pick


def what_counter(it) -> str:
    return str(it.__dict__.get('_late_ctr', '') or '') if it is not None else ''


def _deliver(run, it, chan: str, blows: int) -> None:
    """One carrier (or counter) on its way: floor loot, a chest or the stall."""
    fs = run.fs
    it.__dict__['_late_src'] = chan
    if chan == 'stall':
        if not run.knobs.get('traders'):
            fs['sup_unsold'] = fs.get('sup_unsold', 0) + (0 if what_counter(it) else blows)
            return
        run.late['stall'].append(it)
        fs['sup_offered_stall'] = fs.get('sup_offered_stall', 0) + (0 if what_counter(it) else blows)
        return
    if chan == 'loot':
        got = random.random() < float(run.prof.get('loot_fraction', 1.0))
    else:
        got = bool(run.prof.get('opens_chests')) and run.quiz.one_question(max(1, tier_of(run.floor)))
    if not got:
        fs['sup_missed'] = fs.get('sup_missed', 0) + (0 if what_counter(it) else blows)
        return
    _take(run, it, blows, 'sup_found')


def _take(run, it, blows: int, book: str) -> None:
    fs = run.fs
    ctr = what_counter(it)
    if ctr:
        run.late['kit'].append(it)
        if ctr in ('mirror', 'plugs') and run.late.get(ctr) is None:
            run.late[ctr] = it
        fs[book + '_ctr'] = fs.get(book + '_ctr', 0) + 1
    else:
        it.__dict__['_late_sup'] = True
        run.flasks.append(it)
        fs[book] = fs.get(book, 0) + blows
        _fsd(fs, book + '_sub', it.__dict__.get('_late_sub', '?'), blows)
    run._sync_pack()


def floor_start(run, floor: int) -> None:
    """D: this floor's carriers and counters for the residents ahead (Run.play_floor,
    before the floor's stall)."""
    sup = float(run.kv('supply') or 0.0)
    if sup <= 0:
        return
    ahead = int(run.knobs.get('supply_ahead', 5) or 0)
    w = window(floor, ahead)
    late = run.late
    for s in sorted(w['demand']):
        late['carry'][s] = late['carry'].get(s, 0.0) + sup * w['demand'][s] / w['floors']
        b = _unit_blows(s, floor)
        while late['carry'][s] >= b:
            late['carry'][s] -= b
            _deliver(run, make_carrier(s, floor), _channel(run, s), b)
    _counters_due(run, floor, w, sup)


def _make_counter(kind: str, floor: int, el: str = ''):
    import items
    it = None
    if kind == 'mirror':
        import smithing
        for mid in reversed(list(smithing.order_materials(floor) or ())):
            try:
                it = smithing.make_order('shield', 'mirror_shield', mid)
            except Exception:
                it = None
            if it is not None:
                break
        if it is None:
            try:
                it = items.instantiate_shield('mirror_shield', 'steel')
            except Exception:
                it = None
    elif kind == 'plugs':
        it = items.make_item_by_id('accessory', 'beeswax_earplugs')
    elif kind == 'potion':
        pid = RESIST_POTIONS.get(el)
        it = items.make_item_by_id('potion', pid) if pid else None
    if it is not None:
        it = copy.copy(it)
        it.identified = True
        it.__dict__['_late_ctr'] = kind
        it.__dict__['_late_el'] = el
    return it


def _counters_due(run, floor: int, w: dict, sup: float) -> None:
    """Counters for the residents' signature attacks: a mirror shield once
    gazers live ahead, wax once voices do, a resistance potion an encounter
    with a breath or aura of fire, cold or lightning (x supply)."""
    late, fs = run.late, run.fs
    enc = w['enc']
    for sk, kind in (('gaze', 'mirror'), ('voice', 'plugs')):
        if enc.get((sk, ''), 0.0) * sup >= 0.5 and not late.get(kind + '_due'):
            it = _make_counter(kind, floor)
            if it is not None:
                late[kind + '_due'] = True
                _deliver(run, it, _channel(run, '#' + kind), 1)
    for (sk, el), n in sorted(enc.items()):
        if sk not in ('breath', 'aura', 'drain'):
            continue
        if el not in RESIST_POTIONS:
            fs['sup_ctr_none'] = fs.get('sup_ctr_none', 0.0) + sup * n / w['floors']
            continue
        k = '#pot_' + el
        late['ctr_carry'][k] = late['ctr_carry'].get(k, 0.0) + sup * n / w['floors']
        while late['ctr_carry'][k] >= 1.0:
            late['ctr_carry'][k] -= 1.0
            it = _make_counter('potion', floor, el)
            if it is None:
                break
            _deliver(run, it, _channel(run, k), 1)


def _carried_blows(run, sub: str) -> int:
    n = sum(carrier_blows(it) for it in run.flasks
            if (getattr(it, 'coat', None) or {}).get('substance') == sub
            or it.__dict__.get('_late_sub') == sub)
    w = run.p.weapon
    c = getattr(w, 'coating', None) if w is not None else None
    if isinstance(c, dict) and c.get('substance') == sub:
        n += int(c.get('blows', 0) or 0)
    return n


def shop(run, floor: int, defn: dict, svc: set, inc: float, reserve: float) -> None:
    """D at a stall (inside Run.shop): what supply set out since the last
    stall, bought by a kid with tactics; then the smith's inlay."""
    late = run.late
    stock, late['stall'] = late['stall'], []
    if float(run.kv('supply') or 0.0) <= 0:
        return
    fs = run.fs
    if not run.knobs.get('tactics'):
        fs['sup_unsold'] = fs.get('sup_unsold', 0) + sum(
            carrier_blows(x) for x in stock if not what_counter(x))
        return
    import economy
    markup = float(defn.get('markup', 1.0) or 1.0)
    w = window(floor, int(run.knobs.get('supply_ahead', 5) or 0))
    pitch = max(sorted(w['demand']), key=lambda s: w['demand'][s]) if w['demand'] else ''
    mem = getattr(run, 'late_memory', None) or set()

    def wanted(sub):
        return sub == pitch or any(k in mem or run._knows(k) for k in sorted(w['kinds'].get(sub, ())))

    for it in stock:
        ctr = what_counter(it)
        price = economy.stock_price(it, floor, markup)
        if ctr:
            if ctr in ('mirror', 'plugs') and late.get(ctr) is not None:
                continue
            if run._pay(price, reserve):
                _take(run, it, 1, 'sup_bought')
            continue
        sub = it.__dict__.get('_late_sub', '')
        b = carrier_blows(it)
        why = ('unwanted' if not wanted(sub) else
               'enough' if _carried_blows(run, sub) >= w['demand'].get(sub, 0.0) else
               'gold' if not run._pay(price, reserve) else '')
        if why:
            fs['sup_unsold'] = fs.get('sup_unsold', 0) + b
            _fsd(fs, 'sup_unsold_why', why, b)
            continue
        _take(run, it, b, 'sup_bought')
    if svc & {'silvering', 'cold_iron_inlay'}:
        sub = domain_bane(floor)
        wpn = run.p.weapon
        if sub and can_bane_inlay(wpn, sub):
            if run._pay(economy.SERVICE_SHARE['silvering'] * inc, reserve, 'service') \
                    and bane_inlay(wpn, sub):
                fs['sup_inlay'] = fs.get('sup_inlay', 0) + 1
                _fsd(fs, 'sup_inlay_sub', sub)


# ---- the carriers in use (Run._coat_for, _throw_flask, _player_attack, _sync_pack)

def on_coat(run, weapon, flask) -> None:
    """Before a coating goes on: a supplied one scraped off is wasted."""
    c = getattr(weapon, 'coating', None) if weapon is not None else None
    if isinstance(c, dict) and int(c.get('blows', 0) or 0) > 0 and c.get('_late_sup'):
        run.fs['sup_wasted'] = run.fs.get('sup_wasted', 0) + int(c['blows'])
    if flask is not None:
        flask.__dict__['_late_spent'] = True


def after_coat(run, weapon, flask) -> None:
    c = getattr(weapon, 'coating', None) if weapon is not None else None
    if not isinstance(c, dict):
        return
    _fsd(run.fs, 'coat_sub', c.get('substance', ''))
    if flask is not None and flask.__dict__.get('_late_sup'):
        c['_late_sup'] = True


def on_throw(run, flask, target) -> None:
    """Before a thrown flask bursts (Run._throw_flask)."""
    import coatings
    _dmg, dtype = coatings.thrown_damage(flask, target)
    _fsd(run.fs, 'throw_sub', dtype)
    flask.__dict__['_late_spent'] = True
    if flask.__dict__.get('_late_sup'):
        key = 'sup_used' if dtype in (getattr(target, 'weaknesses', None) or ()) else 'sup_wasted'
        run.fs[key] = run.fs.get(key, 0) + 1


def on_shed(run, before: list) -> None:
    """Supplied carriers left behind for weight (Run._fit_pack)."""
    if run.fs is None:
        return
    now = {id(x) for x in run.flasks}
    for it in before:
        if (id(it) not in now and it.__dict__.get('_late_sup')
                and not it.__dict__.get('_late_spent')):
            b = carrier_blows(it)
            run.fs['sup_wasted'] = run.fs.get('sup_wasted', 0) + b
            run.fs['sup_shed'] = run.fs.get('sup_shed', 0) + b


def recoat(run, target) -> bool:
    """recoat=1, in a fight (Run.fight's choice of action): a coating for the
    foe in front of him, his action. True when it went on."""
    if not int(run.knobs.get('recoat', 0) or 0) or not run.knobs.get('tactics'):
        return False
    n0 = run.fs.get('coatings', 0)
    run._coat_for(target)
    if run.fs.get('coatings', 0) > n0:
        run.fs['recoats'] = run.fs.get('recoats', 0) + 1
        return True
    return False


def blow_class(weapon, target) -> str:
    """'a' (met a weakness), 'r' (resisted) or 'p' (plain): the real
    combat.weapon_type_multiplier, form x substance, held to the cap."""
    import affinity
    import combat
    try:
        f, s = combat.weapon_type_multiplier(weapon, target)
        m = affinity.capped(float(f) * float(s))
    except Exception:
        m = 1.0
    return 'a' if m > 1.0 + _EPS else 'r' if m < 1.0 - _EPS else 'p'


def blow_pre(run, target) -> tuple:
    """Before a melee blow (Run._player_attack): what it will meet, the coating."""
    w = run.p.weapon
    cls = blow_class(w, target)
    d = target.__dict__.setdefault('_late_bl', {'a': 0, 'p': 0, 'r': 0})
    d[cls] += 1
    fs = run.fs
    fs['bl_' + cls] = fs.get('bl_' + cls, 0) + 1
    if cls != 'a':
        sup = reachable()
        if any(str(s) in sup for s in (getattr(target, 'weaknesses', None) or ())):
            fs['sup_short'] = fs.get('sup_short', 0) + 1
    c = getattr(w, 'coating', None) if w is not None else None
    coat = ((str(c.get('substance', '')), int(c.get('blows', 0) or 0), bool(c.get('_late_sup')))
            if isinstance(c, dict) and int(c.get('blows', 0) or 0) > 0 else None)
    if _MEASURE['on']:
        _MEASURE['last'] = None
    return cls, coat, w


def blow_post(run, target, pre) -> None:
    cls, coat, w = pre
    if _MEASURE['on']:
        _measure_blow(run, target, w)
    if coat is None:
        return
    c = getattr(w, 'coating', None) if w is not None else None
    left = int(c.get('blows', 0) or 0) if isinstance(c, dict) else 0
    if left >= coat[1]:
        return                                   # it missed: nothing spent
    sub, _b, from_sup = coat
    import combat
    combat._load_material_tags()
    weak = sub in (getattr(target, 'weaknesses', None) or ()) or combat._material_weak(
        sub, set(getattr(target, 'tags', None) or ()))
    _fsd(run.fs, 'coat_blow_met' if weak else 'coat_blow_none', sub)
    if from_sup:
        key = 'sup_used' if weak else 'sup_wasted'
        run.fs[key] = run.fs.get(key, 0) + 1


def on_record(run, m) -> None:
    """A monster's fight is booked (Run._record_monster)."""
    fs = run.fs
    d = m.__dict__.get('_late_bl') or {}
    if not m.alive:
        for c in 'apr':
            fs['kb_' + c] = fs.get('kb_' + c, 0) + int(d.get(c, 0))
        if d.get('a'):
            fs['k_ans'] = fs.get('k_ans', 0) + 1
    if getattr(m, '_sim_dmg', 0):
        kind = getattr(m, 'kind', '') or '?'
        dk = run.late['dmg_by_kind']
        dk[kind] = dk.get(kind, 0.0) + float(m._sim_dmg) / max(1, run.p.max_hp)


def on_fight(run, group) -> None:
    """A fight's blows: answered when at least half of them met a weakness."""
    tot = {'a': 0, 'p': 0, 'r': 0}
    for m in group:
        for c, n in (m.__dict__.get('_late_bl') or {}).items():
            tot[c] = tot.get(c, 0) + n
    n = sum(tot.values())
    if not n:
        return
    fs = run.fs
    pre = 'n' if any(getattr(m, 'is_boss', False) or getattr(m, 'is_mini_boss', False)
                     or getattr(m, 'is_seal_demon', False) for m in group) else 'o'
    fs[pre + 'f_blows'] = fs.get(pre + 'f_blows', 0) + 1
    if tot['a'] * 2 >= n:
        fs[pre + 'f_ans'] = fs.get(pre + 'f_ans', 0) + 1


def run_end(run) -> None:
    """The run is over: the supplied blows he still carries are left over."""
    fs = run.fs
    if fs is None:
        return
    left = sum(carrier_blows(it) for it in run.flasks if it.__dict__.get('_late_sup'))
    w = run.p.weapon
    c = getattr(w, 'coating', None) if w is not None else None
    if isinstance(c, dict) and c.get('_late_sup'):
        left += int(c.get('blows', 0) or 0)
    if left:
        fs['sup_left'] = fs.get('sup_left', 0) + left


# =============================================================================
# F. Signature attacks need their counter
# =============================================================================

_ORIG = {}


def install_runtime() -> None:
    """The class-level hook on Monster._resolve_blow, a pass-through for every
    player the simulator did not make (no `_sim_late`); and the careful-blow
    meter when measuring. Idempotent; never at import."""
    if _MEASURE['on']:
        _measure_install()
    if 'resolve' in _ORIG:
        return
    from monster import Monster
    orig = Monster._resolve_blow
    _ORIG['resolve'] = orig

    def _resolve_blow(self, atk, player, in_flurry=False):
        run = getattr(player, '__dict__', {}).get('_sim_late')
        if run is None:
            return orig(self, atk, player, in_flurry)
        return _sig_blow(run, orig, self, atk, player, in_flurry)
    _resolve_blow._sim_late_hook = True
    Monster._resolve_blow = _resolve_blow


def resists(p, el: str) -> bool:
    """A resistance to `el`: a status (a potion or a dish), gear, a lining or
    a chain resistance."""
    if not el:
        return False
    from status_effects import DAMAGE_HALVED, DAMAGE_IMMUNITY, SHIELD_IMMUNITY
    for table in (DAMAGE_IMMUNITY, DAMAGE_HALVED, SHIELD_IMMUNITY):
        s = table.get(el)
        if s and p.has_effect(s):
            return True
    try:
        if float((getattr(p, 'resistances', None) or {}).get(el, 1.0)) < 1.0 - _EPS:
            return True
        if float(p.get_armor_resistance(el)) < 1.0 - _EPS:
            return True
        if int((getattr(p, 'damage_resistances', None) or {}).get(el, 0) or 0) > 0:
            return True
    except Exception:
        pass
    try:
        import smithing
        if smithing.lining_mult(p, el) < 1.0 - _EPS:
            return True
    except Exception:
        pass
    return False


def has_counter(p, m, atk: dict, kind: str) -> bool:
    if kind == 'gaze':
        import counters
        if counters.blocks_gaze(p, m) is not None or p.has_effect('petrify_immune'):
            return True
        if getattr(getattr(p, 'shield', None), 'id', '') in ('aegis_of_athena', 'greater_aegis_of_athena'):
            return True
        try:
            import monster as _monster
            return p.get_sight_radius() == 0 or bool(_monster._edge_gaze_immune(p, m))
        except Exception:
            return False
    if kind == 'voice':
        import counters
        return bool(counters.ears_stopped(p))
    if kind == 'drain':
        return resists(p, 'drain')
    return resists(p, str(atk.get('type', '')))


def _sig_blow(run, orig, m, atk, p, in_flurry):
    kind = sig_of(atk)
    if not kind:
        return orig(m, atk, p, in_flurry)
    ctr = has_counter(p, m, atk, kind)
    sig = float(run.knobs.get('sig', 0.0) or 0.0)
    hp0 = p.hp
    if ctr or sig <= 0:
        r = orig(m, atk, p, in_flurry)
    else:
        if atk.get('_sim_full_damage'):
            atk = dict(atk, damage=atk['_sim_full_damage'])
        p.__dict__['_sig_mult'] = sig
        try:
            r = orig(m, atk, p, in_flurry)
        finally:
            p.__dict__['_sig_mult'] = 1.0
    fs = run.fs
    if fs is not None:
        side = 'sig_ctr' if ctr else 'sig_bare'
        _fsd(fs, side, kind)
        lost = max(0, hp0 - p.hp)
        if lost:
            _fsd(fs, side + '_dmg', kind, lost / max(1, p.max_hp))
    return r


def aura_begin(run) -> None:
    run.p.__dict__['_sim_aura'] = True


def aura_end(run) -> None:
    run.p.__dict__['_sim_aura'] = False


def aura_amount(p, amount, damage_type):
    """SimPlayer.take_damage inside the aura pulse: heat or cold, x sig on a
    hero with no resistance to it."""
    run = p.__dict__.get('_sim_late')
    if run is None or amount <= 0:
        return amount
    ctr = resists(p, str(damage_type))
    fs = run.fs
    if fs is not None:
        _fsd(fs, 'sig_ctr' if ctr else 'sig_bare', 'aura')
    sig = float(run.knobs.get('sig', 0.0) or 0.0)
    if ctr or sig <= 0:
        return amount
    return max(1, int(round(amount * sig)))


# ---- prep: the careful kid readies his counters for what he knows

def _resist_dish(run, el: str):
    import kitchen
    want = RESIST_STATUS.get(el)
    if not want or getattr(run, 'dishes_left', 0) <= 0:
        return None
    ready = [r for r in run._ready('special') if kitchen.dish_power(r) == want]
    return max(ready, key=lambda r: kitchen.dish_value(run.p, r)) if ready else None


def prep(run, group) -> None:
    """Before a fight (Run._fight_and_account): see the docstring's `prep`."""
    k = run.knobs
    if not (int(k.get('prep', 1) or 0) and k.get('tactics')
            and (float(run.kv('sig') or 0) > 0 or float(run.kv('supply') or 0) > 0)):
        return
    p, late, fs = run.p, run.late, run.fs
    need = {}
    for m in group:
        kind = getattr(m, 'kind', '')
        if not run._knows(kind):
            continue
        for sk, v in signatures(active_defs().get(kind) or {}).items():
            need.setdefault(sk, set()).update(v if isinstance(v, dict) else ())
    if not need:
        return
    late['prepped'] = True
    mirror = late.get('mirror')
    gazers = sum(1 for m in group if run._knows(getattr(m, 'kind', ''))
                 and 'gaze' in signatures(active_defs().get(getattr(m, 'kind', '')) or {}))
    if ('gaze' in need and mirror is not None and p.shield is not mirror
            and 2 * gazers >= len(group)):           # the gaze is the fight's threat, not a side one
        import counters
        w = p.weapon
        if counters.blocks_gaze(p) is None and not (w is not None and getattr(w, 'two_handed', False)):
            late['swapped'] = p.shield
            late['kit'] = [x for x in late['kit'] if x is not mirror]
            p.shield = mirror
            fs['prep_mirror'] = fs.get('prep_mirror', 0) + 1
    if 'voice' in need and late.get('plugs') is not None and not getattr(p, 'ears_stopped', False):
        p.ears_stopped = True
        fs['prep_wax'] = fs.get('prep_wax', 0) + 1
    els = set(need.get('breath', ())) | set(need.get('aura', ()))
    if 'drain' in need:
        els.add('drain')
    import food_system
    for el in sorted(els):
        if resists(p, el):
            continue
        pot = next((x for x in late['kit'] if what_counter(x) == 'potion'
                    and x.__dict__.get('_late_el') == el), None)
        if pot is not None:
            late['kit'].remove(pot)
            food_system.drink_potion(p, pot)
            fs['prep_potion'] = fs.get('prep_potion', 0) + 1
            continue
        rec = _resist_dish(run, el)
        if rec is not None and run._cook_dish(rec):
            fs['prep_dish'] = fs.get('prep_dish', 0) + 1
    run._sync_pack()


def unprep(run) -> None:
    """After the fight: the shield he wore before, the wax out."""
    late = getattr(run, 'late', None)
    if not late or not late.get('prepped'):
        return
    late['prepped'] = False
    p = run.p
    mirror = late.get('mirror')
    if mirror is not None and p.shield is mirror:
        p.shield = late.get('swapped')
        late['kit'].append(mirror)
    late['swapped'] = None
    if getattr(p, 'ears_stopped', False) and late.get('plugs') is not None:
        p.ears_stopped = False
    run._sync_pack()


# =============================================================================
# H. Learning across runs
# =============================================================================

def learned(run) -> set:
    """What the death screen taught: his killer and the 3 that hurt him most."""
    out = set()
    if run.ever_died and run.last_hit_by and run.last_hit_by != '?':
        out.add(run.last_hit_by)
    dk = run.late['dmg_by_kind']
    for kind in sorted(dk, key=lambda k: (-dk[k], k))[:3]:
        if kind != '?':
            out.add(kind)
    return out


def campaign_line(ds, cache, profile, accuracy, speed, policy, engagers, knobs, lo, hi,
                  total, boss_rows, late) -> None:
    """One seed line of a campaign: N runs in sequence, each to its first
    death or floor hi, each remembering what the ones before it learned."""
    n = max(1, int(knobs.get('campaign', 1) or 1))
    memory = set()
    camp = late.setdefault('campaign', [dict(runs=0, survived=0, floors=[], learned=0)
                                        for _ in range(n)])
    per = late.setdefault('campaign_stats', [{} for _ in range(n)])
    for i in range(n):
        run = ds.Run(cache, profile, accuracy, speed, policy, engagers, knobs)
        run.late_memory = set(memory)
        for f in range(1, lo):
            run.play_floor(f, fights=False)
        if lo > 1:
            run.stats = {}
            run.p.hp = run.p.max_hp
        reached = hi + 1
        for f in range(lo, hi + 1):
            run.play_floor(f)
            if run.ever_died:
                reached = f
                break
        run_end(run)
        ds.merge_stats(total, run.stats)
        ds.merge_stats(per[i], run.stats)
        boss_rows += run.boss_rows
        c = camp[i]
        c['runs'] += 1
        c['survived'] += 0 if run.ever_died else 1
        c['floors'].append(reached)
        c['learned'] += len(memory)
        memory |= learned(run)


def cell_begin() -> None:
    _MEASURE['log'] = {}


def cell_late(knobs: dict) -> dict:
    out = dict(info(), campaign_n=max(1, int(knobs.get('campaign', 1) or 1)))
    if _MEASURE['on']:
        out['blowlog'] = dict(_MEASURE['log'])
    return out


def merge_late(a: dict, b: dict) -> None:
    """balance_study.merge: the late-game parts of two chunks of one cell."""
    la, lb = a.get('late'), b.get('late')
    if lb is None:
        return
    if la is None:
        a['late'] = lb
        return
    ca, cb = la.get('campaign'), lb.get('campaign')
    if cb:
        if not ca:
            la['campaign'], la['campaign_stats'] = cb, lb.get('campaign_stats')
        else:
            import difficulty_sim as ds
            for x, y in zip(ca, cb):
                for k in ('runs', 'survived', 'floors', 'learned'):
                    x[k] += y[k]
            for x, y in zip(la.get('campaign_stats') or (), lb.get('campaign_stats') or ()):
                ds.merge_stats(x, y)
    for k, v in (lb.get('blowlog') or {}).items():
        t = la.setdefault('blowlog', {}).setdefault(k, dict(n=0, miss=0, sum=0.0, samples=[]))
        t['n'] += v['n']
        t['miss'] += v['miss']
        t['sum'] += v['sum']
        t['samples'] = (t['samples'] + v['samples'])[:MEASURE_KEEP * 4]


# =============================================================================
# The careful blow, measured (--measure)
# =============================================================================

_MEASURE = {'on': bool(os.environ.get('PQ_SIM_LATE_MEASURE')), 'last': None, 'log': {}}
MEASURE_KEEP = 4000


def _measure_install() -> None:
    import combat
    if getattr(combat.strike_damage, '_sim_late_measure', False):
        return
    real = combat.strike_damage

    def strike_damage(*a, **kw):
        v = real(*a, **kw)
        _MEASURE['last'] = v
        return v
    strike_damage._sim_late_measure = True
    combat.strike_damage = strike_damage


def _measure_blow(run, target, w) -> None:
    if (getattr(target, 'is_boss', False) or getattr(target, 'is_mini_boss', False)
            or getattr(target, 'is_seal_demon', False)):
        return
    import affinity
    import combat
    band = (max(1, int(run.floor)) - 1) // 10
    t = _MEASURE['log'].setdefault(band, dict(n=0, miss=0, sum=0.0, samples=[]))
    t['n'] += 1
    v = _MEASURE['last']
    if v is None:
        t['miss'] += 1
        return
    try:
        f, s = combat.weapon_type_multiplier(w, target)
        step = max(0.05, affinity.capped(float(f) * float(s)))
    except Exception:
        step = 1.0
    plain = float(v) / step
    t['sum'] += plain
    smp = t['samples']
    if len(smp) < MEASURE_KEEP:
        smp.append(plain)
    else:
        r = random.Random(t['n'] * 7919)          # its own stream
        j = int(r.random() * t['n'])
        if j < MEASURE_KEEP:
            smp[j] = plain


def build_table(blowlog: dict, stats: dict, trials: int) -> dict:
    """sim_late_blow.json from a measurement cell."""
    bands = []
    for b in range(10):
        t = blowlog.get(b) or blowlog.get(str(b))
        if not t or t['n'] - t['miss'] <= 0:
            continue
        landed = t['n'] - t['miss']
        mean = t['sum'] / landed
        smp = sorted(t['samples'])
        q = [smp[min(len(smp) - 1, int((i + 0.5) / 40 * len(smp)))] / mean for i in range(40)]
        bands.append(dict(lo=b * 10 + 1, hi=b * 10 + 10, landed_mean=round(mean, 2),
                          miss=round(t['miss'] / t['n'], 4), mean=round(t['sum'] / t['n'], 2),
                          blows=t['n'], q=[round(x, 4) for x in q]))
    met = []
    for b in range(10):
        fl = [f for f in stats if b * 10 + 1 <= f <= b * 10 + 10 and f not in BOSS_FLOORS]
        v = sum(stats[f].get('visits', 0) for f in fl)
        m = sum(stats[f].get('monsters', 0) for f in fl)
        if v:
            met.append(dict(lo=b * 10 + 1, hi=b * 10 + 10, met=round(m / v, 2)))
    return dict(_doc=("The careful kid's melee blow before the affinity step, by 10-floor band "
                      "(tools/balance/sim_late.py --measure): landed_mean, miss (share of attack "
                      "actions whose first answer was wrong), mean (with the misses), q (40 "
                      "quantiles of the landed blow over landed_mean); monsters_met: ordinary "
                      "monsters met a floor (gate-boss floors left out). Profile mastery, the kid "
                      "model x1.2 (balance_study.KID_FAST), engagers 2, floors 1-100, default "
                      "knobs."),
                trials=trials, bands=bands, monsters_met=met)


def table_doc(table: dict) -> str:
    met = {(r['lo'], r['hi']): r['met'] for r in table.get('monsters_met') or ()}
    lines = ['    floors   landed blow   miss   blow with misses   monsters met / floor']
    for r in table['bands']:
        lines.append(f"    {r['lo']:>3}-{r['hi']:<3}  {r['landed_mean']:>11,.0f}  {100 * r['miss']:4.1f}%"
                     f"  {r['mean']:>16,.0f}   {met.get((r['lo'], r['hi']), 0):>10.1f}")
    return '\n'.join(lines)


# =============================================================================
# I. The cell report
# =============================================================================

DOMAINS = ((1, 20), (21, 40), (41, 60), (61, 80), (81, 100))


def _agg(stats: dict, a: int, b: int) -> dict:
    s = {}
    for f, fs in stats.items():
        if not (a <= f <= b):
            continue
        for k, v in fs.items():
            if isinstance(v, dict):
                d = s.setdefault(k, {})
                for n, c in v.items():
                    if isinstance(c, (int, float)):
                        d[n] = d.get(n, 0) + c
            elif isinstance(v, (int, float)):
                s[k] = s.get(k, 0) + v
    return s


def summary_rows(res: dict, stats: dict = None, runs: int = None) -> list:
    """The table by 20-floor domain (gate-boss floors inside their domain)."""
    stats = res['stats'] if stats is None else stats
    runs = res['trials'] if runs is None else runs
    out = []
    for a, b in DOMAINS:
        s = _agg(stats, a, b)
        if not s:
            continue
        v = max(1, s.get('visits', 0))
        kills = max(1, s.get('kills', 0))
        out.append(dict(
            band=f'{a}-{b}', visits=s.get('visits', 0),
            first=100.0 * s.get('first_deaths', 0) / max(1, runs),
            ka=s.get('kb_a', 0) / kills, kp=s.get('kb_p', 0) / kills, kr=s.get('kb_r', 0) / kills,
            cost=100.0 * s.get('ofight_cost', 0.0) / max(1, s.get('ofights', 0)),
            ncost=100.0 * s.get('nfight_cost', 0.0) / max(1, s.get('nfights', 0)),
            ans=100.0 * s.get('of_ans', 0) / max(1, s.get('of_blows', 0)),
            found=s.get('sup_found', 0) / v, bought=s.get('sup_bought', 0) / v,
            used=s.get('sup_used', 0) / v,
            wasted=(s.get('sup_wasted', 0) + s.get('sup_left', 0)) / v,
            short=s.get('sup_short', 0) / v, inlay=int(s.get('sup_inlay', 0)),
            sig_bare=sum((s.get('sig_bare') or {}).values()) / v,
            sig_ctr=sum((s.get('sig_ctr') or {}).values()) / v,
            sig_bare_dmg=100.0 * sum((s.get('sig_bare_dmg') or {}).values()) / v,
            s=s))
    return out


def summary(res: dict, out=sys.stdout, name: str = '') -> None:
    """A compact table of one cell (its pickle's dict)."""
    import difficulty_sim as ds
    w = out.write
    cell = res.get('cell') or {}
    w(f"\n== {name or cell.get('name', '')}  profile={res['profile']}  runs={res['trials']}  "
      f"engagers={res['engagers']}  floors={res['floors'][0]}-{res['floors'][1]}\n")
    w(f"   knobs: {ds.knobs_label(res['knobs'])}\n")
    lt = res.get('late') or {}
    if lt.get('overlay_kinds') or lt.get('hp_rewritten'):
        w(f"   overlay kinds {lt.get('overlay_kinds', 0)}; new substances "
          f"{', '.join(lt.get('new_substances') or []) or '-'}; HP rewritten for "
          f"{lt.get('hp_rewritten', 0)} kinds{'  (' + lt['hp_csv'] + ')' if lt.get('hp_csv') else ''}\n")
    w("   floors  1st deaths  blows a kill      fight cost %   answered  supply, blows a floor"
      "                    signature hits a floor\n")
    w("           /100 runs   ans  plain res   ordin.  named  fights %  found bought used wasted"
      " short inlays   bare  ctr  bare dmg %\n")
    for r in summary_rows(res):
        w(f"   {r['band']:<7} {r['first']:6.1f}      {r['ka']:4.2f} {r['kp']:4.2f} {r['kr']:4.2f}"
          f"   {r['cost']:5.1f}  {r['ncost']:5.1f}   {r['ans']:5.1f}   {r['found']:5.1f} {r['bought']:5.1f}"
          f" {r['used']:5.1f} {r['wasted']:5.1f} {r['short']:5.1f} {r['inlay']:5d}"
          f"   {r['sig_bare']:4.1f} {r['sig_ctr']:4.1f}  {r['sig_bare_dmg']:5.1f}\n")
    tot = _agg(res['stats'], 1, 100)
    surv = 100.0 * (1 - tot.get('first_deaths', 0) / max(1, res['trials']))
    w(f"   survive to the end: {surv:.1f}%\n")
    cs = tot.get('coat_sub') or {}
    if cs:
        met = tot.get('coat_blow_met') or {}
        w("   coatings put on (coated blows that met a weakness): " + ', '.join(
            f"{k} {v} ({met.get(k, 0)})" for k, v in sorted(cs.items(), key=lambda kv: -kv[1])) + "\n")
    sb, sc = tot.get('sig_bare') or {}, tot.get('sig_ctr') or {}
    if sb or sc:
        w("   signature hits bare / countered: " + ', '.join(
            f"{k} {sb.get(k, 0)}/{sc.get(k, 0)}" for k in SIG_KINDS if sb.get(k) or sc.get(k)))
        pr = [(k, tot.get(k, 0)) for k in ('prep_mirror', 'prep_wax', 'prep_potion', 'prep_dish')]
        if any(v for _, v in pr):
            w(";  prepared: " + ', '.join(f"{k[5:]} {v}" for k, v in pr))
        w("\n")
    if tot.get('sup_offered_stall') or tot.get('sup_found') or tot.get('sup_missed'):
        w(f"   supply (blows): offered on stalls {tot.get('sup_offered_stall', 0)}, unsold "
          f"{tot.get('sup_unsold', 0)} {tot.get('sup_unsold_why') or ''}, not found {tot.get('sup_missed', 0)}, shed "
          f"{tot.get('sup_shed', 0)}, left at the end {tot.get('sup_left', 0)}; counters found "
          f"{tot.get('sup_found_ctr', 0)}, bought {tot.get('sup_bought_ctr', 0)}; encounters with no "
          f"counter in the game {tot.get('sup_ctr_none', 0):.0f}\n")
        subs = {}
        for key in ('sup_found_sub', 'sup_bought_sub'):
            for k, v in (tot.get(key) or {}).items():
                subs[k] = subs.get(k, 0) + v
        if subs:
            w("   supplied by substance: " + ', '.join(
                f"{k} {v}" for k, v in sorted(subs.items(), key=lambda kv: -kv[1])) + "\n")
    camp = lt.get('campaign')
    if camp:
        w(f"   campaign  run   runs  survive %  median floor reached ({res['floors'][1] + 1} = the end)\n")
        for i, c in enumerate(camp):
            fl = sorted(c['floors'])
            med = fl[len(fl) // 2] if fl else 0
            w(f"            {i + 1:>3}  {c['runs']:>5}  {100.0 * c['survived'] / max(1, c['runs']):8.1f}"
              f"  {med:>6}\n")


def load_cell(path: str) -> dict:
    import pickle
    with open(path, 'rb') as f:
        return pickle.load(f)


# =============================================================================
# Command line
# =============================================================================

def _measure_job(job):
    import sim_late as sl                       # the module the simulator's hooks use
    sl._MEASURE['on'] = True
    import balance_study as bs
    return bs.run(job)


def measure(out_path: str, runs: int = 60, workers: int = 10) -> dict:
    """The careful blow: mastery, the kid model at KID_FAST, engagers 2,
    floors 1-100, default knobs; writes the table (sim_late_blow.json)."""
    import multiprocessing as mp
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    os.environ['PQ_SIM_LATE_MEASURE'] = '1'
    import balance_study as bs
    import monte_carlo as mc
    jobs = bs.chunks([bs.cell('measure', 'mastery', 'kid', bs.KID_FAST, '', (1, 100), 2)], runs)
    merged = None
    with mp.Pool(max(1, min(workers, len(jobs))), initializer=mc._low_priority) as pool:
        for res in pool.imap_unordered(_measure_job, jobs):
            merged = bs.merge(merged, res)
    table = build_table((merged.get('late') or {}).get('blowlog') or {}, merged['stats'],
                        merged['trials'])
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(table, f, indent=1)
    return table


def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="The late game's simulator instruments.")
    ap.add_argument('--summary', nargs='+', metavar='PKL', help="print a cell's late-game table")
    ap.add_argument('--measure', metavar='JSON', help="measure the careful blow into JSON")
    ap.add_argument('--runs', type=int, default=60)
    ap.add_argument('--workers', type=int, default=int(os.environ.get('MC_WORKERS') or 10))
    ap.add_argument('--hp-csv', metavar='CSV', help="write the HP stand-in's table for --knobs")
    ap.add_argument('--knobs', default='', help="knobs for --hp-csv (hp_target=1.7,overlay=...)")
    a = ap.parse_args(argv)
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    if a.summary:
        for path in a.summary:
            summary(load_cell(path), name=os.path.splitext(os.path.basename(path))[0])
        return 0
    if a.measure:
        print(table_doc(measure(a.measure, a.runs, a.workers)))
        return 0
    if a.hp_csv:
        import difficulty_sim as ds
        knobs = ds.parse_knobs(a.knobs)
        if float(knobs.get('hp_target') or 0) <= 0:
            raise SystemExit('--hp-csv needs hp_target > 0 in --knobs')
        install(knobs)
        with open(a.hp_csv, 'w', encoding='utf-8') as f:
            f.write(hp_csv_text(_STATE['hp_rows'] or []))
        print(f"{len(_STATE['hp_rows'] or [])} kinds -> {a.hp_csv}")
        return 0
    ap.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
