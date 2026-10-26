#!/usr/bin/env python
"""Loot census: what a run hands out, floor by floor, and what it does to AC.

Question it answers: "how much gear, how many rings, how much treasure and
gold does the dungeon give a player who explores it, and how fast does that
lower the hero's armor class and raise the stats rings lend?"

Everything is the game's own code: one LevelManager per run generates
floors 1..N in order (so named uniques stay once a run), every chest is
opened with container_system._generate_loot_from_template and chest_gold,
and every monster's death is rolled through CombatMixin._drop_treasure.
Nothing about the player is modelled except the kit rule below.

Each find is booked by SOURCE:
  floor     ordinary room loot (spawn_items' per-room rolls)
  special   a treasury / library / barracks / throne room / zoo
  chamber   a hidden treasure chamber's cache (dungeon.spawn_chamber_cache)
  vault     a closed vault
  chest     what came out of a chest when it was opened
  drop      a monster's death drop

The kit (KIT_RULE): wear the best piece found so far in every armor slot
and the shield, never a cursed one (a careful player identifies first);
ring slots and the amulet go to whatever lowers AC most (protection rings,
then blessed pieces, which are worth 1 AC each, Player.get_ac). Stat rings
are reported separately: the stat points the best four rings and the best
amulet would lend.

Usage:
    python tools/balance/loot_census.py --runs 40 --floors 1-30
    python tools/balance/loot_census.py --runs 40 --floors 1-30 --share 0.85

`--share` is the share of the floor a player actually finds, the chests he
opens and the monsters he kills (difficulty_sim's 'prepared' finds 0.85).

`--whatif` tries a proposed change without touching the game: it patches the
game's own functions in this process only (apply_whatif below). Comma list:
  chests        one ordinary chest a floor, then a 2nd at 55%, a 3rd at 55% x 25%,
                a 4th at x 11% (what the comment in spawn_items describes; the
                code rolls the 55% per ROOM until one lands, then 25% per room...)
  chestsize     items per chest by tier 1-2 / 2 / 2-3+1 / 2-3+1 / 3-4+1
  jewelry       the jewelry box table first proposed (treasure 60 / accessory 20 /
                gold 20); the game now uses 15 / 20 / 65
  chamber       (now the game's own rule) a hidden chamber holds coin, treasure, potions and
                scrolls, not gear or rings
  floorgear=P   ordinary-room gear chance P (the game: dungeon.ROOM_GEAR_CHANCE)
  flooracc=S    keep this share of ordinary-room rings and amulets
  dropacc=S     keep this share of monster-dropped rings and amulets
  rings=N       ring slots (the game: 4)
  chestgear=N   (the game now does this with N=1) a plain chest holds at most N pieces of gear; each
                piece over is replaced by a draw from the chest's other
                categories (potions, scrolls, ammo...), so it is not emptier
  potions=K     K more potions on every ordinary floor
  rare=M        every chest template's named-unique chance times M
difficulty_sim can take the same patches: see apply_whatif's docstring.

Never writes inside the repo; never touches the save directory.
"""
from __future__ import annotations

import argparse
import collections
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import difficulty_sim  # noqa: E402,F401  (imported for its side effects: sys.path, item cache, bones stub)

import container_system       # noqa: E402
import items as items_mod     # noqa: E402
import level_manager as lm_mod  # noqa: E402
import treasure as tr         # noqa: E402
from items import (Accessory, Ammo, Armor, Artifact, Container, Food,  # noqa: E402
                   GoldPile, Ingredient, Potion, Scroll, Shield, Spellbook,
                   Treasure, Wand, Weapon)
from game_combat import CombatMixin   # noqa: E402

SOURCES = ('floor', 'special', 'chamber', 'vault', 'chest', 'drop')
CATS = ('weapon', 'armor', 'shield', 'ring', 'amulet', 'belt', 'stat_acc',
        'ac_acc', 'wand', 'scroll', 'spellbook', 'potion', 'food',
        'ingredient', 'ammo', 'treasure', 'artifact', 'unique', 'other')


class _DropStub:
    """Just enough of a Game for CombatMixin._drop_treasure to run."""
    _drop_treasure = CombatMixin._drop_treasure
    _spawn_treasure_item = CombatMixin._spawn_treasure_item
    _spawn_archer_ammo = CombatMixin._spawn_archer_ammo

    def __init__(self, floor):
        self.dungeon_level = floor
        self.ground_items = []
        self.uniques = 0

    def add_message(self, *a, **k):
        pass

    def _a_or_an(self, s):
        return s

    def _display_name(self, it):
        return getattr(it, 'name', '?')

    def _spawn_boss_scroll(self, *a, **k):
        pass

    def _spawn_unique_item(self, *a, **k):
        self.uniques += 1


def categories(it) -> list:
    """Every census category this item counts toward (an accessory counts
    as its slot and, when it lends a stat or AC, as that too)."""
    if getattr(it, 'is_unique', False) and isinstance(it, (Weapon, Armor, Shield, Accessory)):
        return ['unique']
    if isinstance(it, Weapon):
        return ['weapon'] if getattr(it, 'requires_ammo', None) is None else ['other']
    if isinstance(it, Armor):
        return ['armor']
    if isinstance(it, Shield):
        return ['shield']
    if isinstance(it, Accessory):
        out = [{'amulet': 'amulet', 'belt': 'belt'}.get(getattr(it, 'slot', 'ring'), 'ring')]
        fx = getattr(it, 'effects', {}) or {}
        if fx.get('stat') == 'AC':
            out.append('ac_acc')
        elif fx.get('stat') or fx.get('stat2'):
            out.append('stat_acc')
        return out
    for cls, name in ((Wand, 'wand'), (Scroll, 'scroll'), (Spellbook, 'spellbook'),
                      (Potion, 'potion'), (Food, 'food'), (Ingredient, 'ingredient'),
                      (Ammo, 'ammo'), (Treasure, 'treasure'), (Artifact, 'artifact')):
        if isinstance(it, cls):
            return [name]
    return ['other']


def _rooms_by_source(dungeon):
    """[(Room, source)] for the rooms whose loot is booked apart."""
    out = []
    for ch in getattr(dungeon, 'hidden_chambers', []) or []:
        if ch.get('type') == 'treasure':
            out.append((ch['room'], 'chamber'))
    if getattr(dungeon, 'vault', None):
        out.append((dungeon.vault['room'], 'vault'))
    centres = set((getattr(dungeon, 'special_rooms', {}) or {}).keys())
    for r in getattr(dungeon, 'rooms', []) or []:
        if r.center in centres:
            out.append((r, 'special'))
    return out


def _source_of(it, rooms) -> str:
    for r, src in rooms:
        if r.x <= it.x < r.x + r.width and r.y <= it.y < r.y + r.height:
            return src
    return 'floor'


# ----------------------------------------------------------------- what-if
WHATIF = {}                     # name -> value, set by apply_whatif
CHEST_KEEP = (1.0, 0.55, 0.55 * 0.25, 0.55 * 0.25 * 0.11, 0.0)
LEAN_CHEST_ITEMS = {1: (1, 2, 0), 2: (2, 2, 0), 3: (2, 3, 1), 4: (2, 3, 1), 5: (3, 4, 1)}
JEWELRY_LOOT = {'treasure': 60, 'accessory': 20, 'gold_bonus': 20}
FLOOR_GEAR_CHANCE = None        # dungeon.ROOM_GEAR_CHANCE, read at patch time


def parse_whatif(text: str) -> dict:
    out = {}
    for part in (text or '').split(','):
        part = part.strip()
        if not part:
            continue
        k, _, v = part.partition('=')
        out[k.strip()] = float(v) if v else True
    return out


def _is_gear_or_ring(it) -> bool:
    return isinstance(it, (Weapon, Armor, Shield, Accessory))


def apply_whatif(spec: dict) -> None:
    """Patch the game's loot functions in THIS process to try a change.

    Patches dungeon.spawn_items (level_manager imports it at call time, so the
    floor pass and the hidden-chamber pass both see the wrapper), the chest
    item table and the jewelry box's loot table. Drop and ring-slot changes
    are read by the census (and by a difficulty_sim wrapper) from WHATIF.
    """
    import dungeon as dungeon_mod
    WHATIF.clear()
    WHATIF.update(spec)
    if spec.get('chestsize'):
        container_system.ITEMS_BY_CHEST_TIER.update(LEAN_CHEST_ITEMS)
    if spec.get('jewelry'):
        tpl = items_mod.load_chest_templates().get('jewelry_box')
        if tpl:
            tpl['loot_table'] = dict(JEWELRY_LOOT)
    if spec.get('rare'):
        for tpl in items_mod.load_chest_templates().values():
            tpl['rare_chance_chain3'] = float(tpl.get('rare_chance_chain3', 0.0)) * float(spec['rare'])
    real = getattr(dungeon_mod, '_real_spawn_items', None) or dungeon_mod.spawn_items
    dungeon_mod._real_spawn_items = real

    def spawn_items(rooms, level, dungeon, structures=True):
        got = real(rooms, level, dungeon, structures=structures)
        if not structures:                       # the hidden-chamber pass
            if spec.get('chamber'):
                got = [it for it in got if not _is_gear_or_ring(it)
                       and not isinstance(it, Container)]
            return got
        special = _rooms_by_source(dungeon)
        room_gear = float(dungeon_mod.ROOM_GEAR_CHANCE)
        keep_gear = min(1.0, float(spec.get('floorgear', room_gear)) / room_gear)
        keep_acc = float(spec.get('flooracc', 1.0))
        out, n_chests = [], 0
        for it in got:
            if _source_of(it, special) == 'floor':
                if isinstance(it, Container) and spec.get('chests'):
                    p = CHEST_KEEP[min(n_chests, len(CHEST_KEEP) - 1)]
                    n_chests += 1
                    if random.random() >= p:
                        continue
                elif isinstance(it, (Weapon, Armor, Shield)) and not getattr(it, 'is_unique', False):
                    if random.random() >= keep_gear:
                        continue
                elif isinstance(it, Accessory) and not getattr(it, 'is_unique', False):
                    if random.random() >= keep_acc:
                        continue
            out.append(it)
        extra = int(spec.get('potions', 0))
        if extra and len(rooms) > 1:
            pots = dungeon_mod._item_eligible_weighted(items_mod.load_items('potion'), level)
            for _ in range(extra):
                dungeon_mod._place_one(pots, random.choice(rooms[1:]), dungeon, out, random)
        return out

    dungeon_mod.spawn_items = spawn_items

    if spec.get('chestgear'):
        real_loot = (getattr(container_system, '_real_generate_loot', None)
                     or container_system._generate_loot_from_template)
        container_system._real_generate_loot = real_loot
        cap = int(spec['chestgear'])

        def generate_loot(container, dungeon_level):
            loot = real_loot(container, dungeon_level)
            if int(getattr(container, 'tier', 1) or 1) > 2:
                return loot
            tpl = items_mod.get_chest_template(getattr(container, 'template_id', '')) or {}
            others = {c: w for c, w in (tpl.get('loot_table') or {}).items()
                      if c not in ('weapon_common', 'armor_common', 'shield_common', 'gear',
                                   'gold_bonus')}
            level_cap = container_system._floor_level_cap(container, dungeon_level)
            pool = container_system._build_common_pool(tpl, level_cap)
            out, n_gear = [], 0
            for it in loot:
                if isinstance(it, (Weapon, Armor, Shield)) and not getattr(it, 'is_unique', False):
                    n_gear += 1
                    if n_gear > cap:
                        sub = None
                        if others:
                            cat = container_system._weighted_pick_category(others, random)
                            sub = container_system._pull_common_from_category(
                                cat, pool, level_cap, random)
                        if sub is not None:
                            out.append(sub)
                        continue
                out.append(it)
            return out

        container_system._generate_loot_from_template = generate_loot


def keep_drop(it) -> bool:
    """A monster's drop survives the dropacc what-if."""
    if isinstance(it, Accessory) and not getattr(it, 'is_unique', False):
        return random.random() < float(WHATIF.get('dropacc', 1.0))
    return True


def generate(lm, floor):
    for _ in range(8):
        try:
            return lm.generate(floor)
        except (IndexError, ValueError):
            continue
    raise RuntimeError(f'floor {floor} would not generate')


def ring_slots() -> int:
    return int(WHATIF.get('rings', 4))


class Kit:
    """The best non-cursed piece found so far, per slot."""

    def __init__(self):
        self.armor = {}       # slot -> best AC value (ac_bonus + enchant + blessed)
        self.shield = 0
        self.acc_ac = []      # AC each ring/amulet/belt would give (protection + blessing)
        self.ring_stats = []  # stat points a ring lends
        self.amulet_stats = []
        self.by_stat = collections.defaultdict(lambda: ([], []))   # stat -> (rings, amulets)

    def add(self, it):
        if getattr(it, 'buc', 'uncursed') == 'cursed':
            return
        bless = 1 if getattr(it, 'buc', 'uncursed') == 'blessed' else 0
        if isinstance(it, Armor) and not getattr(it, 'is_unique', False):
            v = int(it.ac_bonus) + int(getattr(it, 'enchant_bonus', 0)) + bless
            self.armor[it.slot] = max(self.armor.get(it.slot, -99), v)
        elif isinstance(it, Shield) and not getattr(it, 'is_unique', False):
            v = int(it.ac_bonus) + int(getattr(it, 'enchant_bonus', 0)) + bless
            self.shield = max(self.shield, v)
        elif isinstance(it, Accessory) and not getattr(it, 'is_unique', False):
            fx = getattr(it, 'effects', {}) or {}
            ac = (int(fx.get('amount', 0)) if fx.get('stat') == 'AC' else 0) + bless
            slot = getattr(it, 'slot', 'ring')
            if slot in ('ring', 'amulet', 'belt') and ac > 0:
                self.acc_ac.append((slot, ac))
            amt = sum(int(fx.get(k, 0)) for k, s in (('amount', 'stat'), ('amount2', 'stat2'))
                      if fx.get(s) and fx.get(s) != 'AC' and int(fx.get(k, 0)) > 0)
            if amt > 0:
                (self.amulet_stats if slot == 'amulet' else self.ring_stats).append(amt)
                for k, st in (('amount', 'stat'), ('amount2', 'stat2')):
                    if fx.get(st) and fx.get(st) != 'AC' and int(fx.get(k, 0)) > 0:
                        self.by_stat[fx[st]][1 if slot == 'amulet' else 0].append(int(fx[k]))

    def gear_ac(self) -> int:
        return sum(v for v in self.armor.values() if v > 0) + self.shield

    def accessory_ac(self) -> int:
        rings = sorted((a for s, a in self.acc_ac if s == 'ring'), reverse=True)[:ring_slots()]
        amulet = max((a for s, a in self.acc_ac if s == 'amulet'), default=0)
        belt = max((a for s, a in self.acc_ac if s == 'belt'), default=0)
        return sum(rings) + amulet + belt

    def ac(self) -> int:
        """Player.get_ac at DEX 10 with this kit worn."""
        return 10 - self.gear_ac() - self.accessory_ac()

    def best_one_stat(self) -> int:
        """Most points of ONE stat the rings and amulet could stack."""
        best = 0
        for rings, amulets in self.by_stat.values():
            best = max(best, sum(sorted(rings, reverse=True)[:ring_slots()]) + max(amulets, default=0))
        return best

    def best_one_stat_unstacked(self) -> int:
        """The same, if only the strongest ring or amulet of a stat counted."""
        return max((max(rings + amulets, default=0) for rings, amulets in self.by_stat.values()),
                   default=0)

    def stat_points(self) -> int:
        """Stat points the best four rings and best amulet would lend."""
        return (sum(sorted(self.ring_stats, reverse=True)[:ring_slots()])
                + max(self.amulet_stats, default=0))


def census(runs: int, floors: range, share: float, seed: int):
    random.seed(seed)
    per = collections.defaultdict(lambda: collections.defaultdict(float))   # floor -> key -> sum
    kit_rows = collections.defaultdict(list)    # floor -> [(ac, gear_ac, acc_ac, stat_pts, n_rings)]
    thac0 = collections.defaultdict(list)       # floor -> ordinary monsters' thac0
    for r in range(runs):
        lm = lm_mod.LevelManager()
        kit = Kit()
        rings_seen = 0
        for floor in floors:
            dungeon, monsters, items = generate(lm, floor)
            rooms = _rooms_by_source(dungeon)
            P = per[floor]
            P['runs'] += 1
            for m in monsters:
                if not (getattr(m, 'is_boss', False) or getattr(m, 'is_mini_boss', False)
                        or getattr(m, 'is_seal_demon', False)):
                    thac0[floor].append(int(getattr(m, 'thac0', 20)))
            found = []      # (item, source)
            for it in items:
                src = _source_of(it, rooms)
                if isinstance(it, GoldPile):
                    P[f'gold:{src}'] += it.amount * share
                    continue
                if isinstance(it, Container):
                    P['chests'] += 1
                    P[f'chest_tpl:{getattr(it, "template_id", "?")}'] += 1
                    if getattr(it, 'is_mimic', False):
                        P['mimics'] += 1
                        continue
                    if random.random() >= share:
                        continue
                    loot = container_system._generate_loot_from_template(it, floor)
                    gold = container_system.chest_gold(it, floor, random)
                    gold += int(getattr(it, '_gold_bonus_accum', 0) or 0)
                    tval = sum(tr.total_value(x) for x in loot if tr.is_treasure(x))
                    if tval and gold:
                        gold = tr.coin_after_treasure(gold, tval)
                    P['gold:chest'] += gold
                    P['chest_items'] += len(loot)
                    P['chests_opened'] += 1
                    found += [(x, 'chest') for x in loot]
                    continue
                if random.random() < share:
                    found.append((it, src))
            stub = _DropStub(floor)
            for m in monsters:
                if random.random() >= share:
                    continue
                stub.ground_items = []
                stub._drop_treasure(m)
                for g in stub.ground_items:
                    if not keep_drop(g):
                        continue
                    if isinstance(g, GoldPile):
                        P['gold:drop'] += g.amount
                    else:
                        found.append((g, 'drop'))
            P['unique:drop'] += stub.uniques
            for it, src in found:
                for c in categories(it):
                    P[f'{c}:{src}'] += 1
                    P[f'{c}:all'] += 1
                if isinstance(it, Treasure):
                    P[f'tvalue:{src}'] += tr.total_value(it)
                if isinstance(it, Accessory) and getattr(it, 'slot', 'ring') == 'ring':
                    rings_seen += 1
                kit.add(it)
            kit_rows[floor].append((kit.ac(), kit.gear_ac(), kit.accessory_ac(),
                                    kit.stat_points(), rings_seen, kit.best_one_stat(),
                                    kit.best_one_stat_unstacked()))
    return per, kit_rows, thac0


def hit_chance(thac0: int, ac: int, min_hit: float = 0.30) -> float:
    """Monster.attack's roll: d20 >= thac0 - AC, natural 1 misses, natural
    20 hits, and a roll that falls short still lands min_hit of the time."""
    need = thac0 - ac
    p = 0.0
    for d in range(1, 21):
        if d == 1:
            continue
        if d == 20 or d >= need:
            p += 1 / 20
        else:
            p += min_hit / 20
    return p


def _avg(per, floor, key):
    P = per[floor]
    return P.get(key, 0.0) / max(1, P['runs'])


def report(per, kit_rows, thac0, floors, share, out=sys.stdout):
    w = out.write
    w(f"\nLOOT CENSUS  ({int(per[floors[0]]['runs'])} runs, share found {share:.2f})"
      + (f"  WHAT-IF {WHATIF}" if WHATIF else '') + "\n")
    w("Per floor, averaged over runs. 'gear' = weapons + armor + shields (common).\n\n")
    hdr = (f"{'F':>3} {'chests':>6} {'gear':>5} {'wpn':>4} {'arm':>4} {'shd':>4} {'ring':>5} "
           f"{'amul':>4} {'statA':>5} {'acA':>4} {'wand':>4} {'scrl':>4} {'book':>4} {'pot':>4} "
           f"{'uniq':>4} {'gold':>6} {'treas':>6}\n")
    w(hdr)
    cum = collections.Counter()
    for f in floors:
        g = lambda k: _avg(per, f, k)   # noqa: E731
        gear = g('weapon:all') + g('armor:all') + g('shield:all')
        gold = sum(g(f'gold:{s}') for s in SOURCES)
        tv = sum(g(f'tvalue:{s}') for s in SOURCES)
        uniq = g('unique:all') + g('unique:drop')
        row = dict(chests=g('chests'), gear=gear, wpn=g('weapon:all'), arm=g('armor:all'),
                   shd=g('shield:all'), ring=g('ring:all'), amul=g('amulet:all'),
                   statA=g('stat_acc:all'), acA=g('ac_acc:all'), wand=g('wand:all'),
                   scrl=g('scroll:all'), book=g('spellbook:all'), pot=g('potion:all'),
                   uniq=uniq, gold=gold, treas=tv)
        cum.update(row)
        w(f"{f:>3} {row['chests']:>6.2f} {gear:>5.1f} {row['wpn']:>4.1f} {row['arm']:>4.1f} "
          f"{row['shd']:>4.1f} {row['ring']:>5.2f} {row['amul']:>4.2f} {row['statA']:>5.2f} "
          f"{row['acA']:>4.2f} {row['wand']:>4.1f} {row['scrl']:>4.1f} {row['book']:>4.1f} "
          f"{row['pot']:>4.1f} {uniq:>4.2f} {gold:>6.0f} {tv:>6.0f}\n")
    w(f"{'sum':>3} {cum['chests']:>6.1f} {cum['gear']:>5.0f} {cum['wpn']:>4.0f} {cum['arm']:>4.0f} "
      f"{cum['shd']:>4.0f} {cum['ring']:>5.1f} {cum['amul']:>4.1f} {cum['statA']:>5.1f} "
      f"{cum['acA']:>4.1f} {cum['wand']:>4.0f} {cum['scrl']:>4.0f} {cum['book']:>4.0f} "
      f"{cum['pot']:>4.0f} {cum['uniq']:>4.1f} {cum['gold']:>6.0f} {cum['treas']:>6.0f}\n")

    w("\nWHERE IT COMES FROM (share of all finds over these floors)\n")
    for c in ('gear', 'ring', 'amulet', 'stat_acc', 'wand', 'scroll', 'potion'):
        keys = ('weapon', 'armor', 'shield') if c == 'gear' else (c,)
        tot = {s: sum(_avg(per, f, f'{k}:{s}') for f in floors for k in keys) for s in SOURCES}
        allv = sum(tot.values()) or 1
        w(f"  {c:<9}" + "  ".join(f"{s} {tot[s] / allv:4.0%}" for s in SOURCES)
          + f"   (total {allv:.1f})\n")
    gold_tot = {s: sum(_avg(per, f, f'gold:{s}') for f in floors) for s in SOURCES}
    allg = sum(gold_tot.values()) or 1
    w(f"  {'gold':<9}" + "  ".join(f"{s} {gold_tot[s] / allg:4.0%}" for s in SOURCES)
      + f"   (total {allg:,.0f})\n")

    w("\nCHESTS by template (per floor, all runs)\n")
    tpl = collections.Counter()
    for f in floors:
        for k, v in per[f].items():
            if k.startswith('chest_tpl:'):
                tpl[k[10:]] += v
    nruns = max(1, per[floors[0]]['runs'])
    for k, v in tpl.most_common():
        w(f"  {k:<20} {v / nruns / len(floors):5.2f} a floor\n")
    opened = sum(per[f]['chests_opened'] for f in floors)
    items_in = sum(per[f]['chest_items'] for f in floors)
    w(f"  items per opened chest: {items_in / max(1, opened):.2f}\n")

    w("\nTHE KIT  (best non-cursed common piece found so far, worn; DEX 10)\n")
    w(f"{'F':>3} {'AC':>5} {'gear':>5} {'acc':>4} {'ringStat':>8} {'oneStat':>7} {'1ring':>5} {'rings':>6} "
      f"{'thac0':>6} {'hit@10':>7} {'hit@kit':>8}\n")
    for f in floors:
        rows = kit_rows[f]
        ac = statistics.median(r[0] for r in rows)
        gear = statistics.mean(r[1] for r in rows)
        acc = statistics.mean(r[2] for r in rows)
        sp = statistics.mean(r[3] for r in rows)
        rs = statistics.mean(r[4] for r in rows)
        one = statistics.mean(r[5] for r in rows)
        one1 = statistics.mean(r[6] for r in rows)
        t0 = int(statistics.median(thac0[f])) if thac0[f] else 20
        w(f"{f:>3} {ac:>5.0f} {gear:>5.1f} {acc:>4.1f} {sp:>8.1f} {one:>7.1f} {one1:>5.1f} {rs:>6.1f} "
          f"{t0:>6d} {hit_chance(t0, 10):>7.0%} {hit_chance(t0, int(ac)):>8.0%}\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--runs', type=int, default=30)
    ap.add_argument('--floors', default='1-30')
    ap.add_argument('--share', type=float, default=1.0)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--whatif', default='', help='see the module docstring')
    a = ap.parse_args(argv)
    if a.whatif:
        apply_whatif(parse_whatif(a.whatif))
    lo, _, hi = a.floors.partition('-')
    floors = list(range(int(lo), int(hi or lo) + 1))
    per, kit_rows, thac0 = census(a.runs, floors, a.share, a.seed)
    report(per, kit_rows, thac0, floors, a.share)


if __name__ == '__main__':
    main()
