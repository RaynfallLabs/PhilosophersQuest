"""The four horns of legend: Robin Hood's Horn, Arthur's Bugle, Gjallarhorn and
the Olifant (data/horns.json; Brandon, 2026-11-16).

Each is a carried artifact (data/items/artifact.json) that only its story path
gives (data/flavor_encounters.json): Robin Hood's bridge (floors 12-18), the
sleepers under the hill (45-55), Heimdall's watch (70-78), all three placed
once a run by karma_rules.json run_start_schedule, and Roland's own chain for
the Olifant (86-92). While it is carried its power is in the V menu. Sounding
it is a HISTORY escalator chain; the chain sets how many answer the call
(``allies_by_chain``). Every horn sounds ONCE A RUN, and a failed quiz still
spends it. Those who answer stay ten turns (``turns``). The Olifant's host
rides from thirty leagues off and comes only ``delay_turns`` after the call:
blow it before the fight and give ground until it comes (Oliver's wisdom,
which Roland ignored at Roncevaux; the item's lore tells the legend).

The allies are monster kinds in data/monsters.json (``is_allied``,
``quest_only``, ``min_level`` 0: never found, never spawned), with their own
numbers from their lore at their horn's tier (LORE, NOT FLOOR). On the map
each is a :class:`CalledAlly`, a helper that comes and goes beside the hero
like a sketch (a Pet, never the one companion): it fights what is near, stays
its turns, then leaves with its line, and it stays on the floor it was called
to. It never strikes a gate's guardian (the five gate bosses,
data/domains.json): Fenrir is bound by Gleipnir and ended by the Sandal, and
no horn changes that.

Pure apart from the class: no pygame, no Game. game_horns.HornsMixin is the
Game's side.
"""
from __future__ import annotations

import json

from paths import data_path
from pet_system import Pet

_DATA: dict | None = None
_MONSTERS: dict | None = None
_GUARDIANS: frozenset | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        try:
            with open(data_path('data', 'horns.json'), encoding='utf-8') as f:
                _DATA = json.load(f)
        except (OSError, ValueError):
            _DATA = {'horns': {}}
    return _DATA


def reload() -> None:
    """Forget the cached tables (tests)."""
    global _DATA, _MONSTERS, _GUARDIANS
    _DATA = _MONSTERS = _GUARDIANS = None


def horns() -> dict:
    return data().get('horns') or {}


def horn_ids() -> list:
    return list(horns())


def horn(hid) -> dict:
    return horns().get(hid) or {}


def name(hid) -> str:
    """The horn's own name, as its item is called ("Robin Hood's Horn")."""
    return horn(hid).get('name') or str(hid).replace('_', ' ').title()


def power_id(hid) -> str:
    return horn(hid).get('power', '')


def horn_for_power(pid) -> str | None:
    for hid, h in horns().items():
        if h.get('power') == pid:
            return hid
    return None


def is_horn_power(pid) -> bool:
    return horn_for_power(pid) is not None


# ---------------------------------------------------------------- the hero

def carried(inventory) -> list:
    """The horns in the pack, in the data's order."""
    have = {getattr(i, 'id', '') for i in inventory or ()}
    return [hid for hid in horns() if hid in have]


def sounded(player) -> set:
    """The horns already sounded this run (each sounds once)."""
    return set(getattr(player, 'horns_sounded', None) or ())


def due(player) -> dict:
    """{horn id: [turns until the host arrives, chain]} for a host on its way."""
    d = getattr(player, 'horn_host_due', None)
    return d if isinstance(d, dict) else {}


def ready(player, hid) -> bool:
    return hid not in sounded(player) and hid not in due(player)


def spend(player, hid) -> None:
    player.horns_sounded = sounded(player) | {hid}


def menu_rows(player) -> list:
    """The V menu's rows for the carried horns not yet sounded:
    ``(power id, def, uses left, cooldown)``, as _open_power_menu builds them."""
    rows = []
    for hid in carried(getattr(player, 'inventory', ())):
        if not ready(player, hid):
            continue
        h = horn(hid)
        rows.append((h['power'], {'label': h.get('label', hid), 'desc': h.get('desc', ''),
                                  'cooldown': 0, 'uses': 1}, 1, 0))
    return rows


def hud_rows(player) -> list:
    """(label, value, kind) for the HUD's powers panel: a horn ready to blow,
    and a host still on the road."""
    out = []
    for hid in carried(getattr(player, 'inventory', ())):
        if ready(player, hid):
            out.append((name(hid), '1 Use', 'uses'))
    for hid, (left, _chain) in due(player).items():
        out.append((name(hid), f"Coming ({int(left)})", 'cooldown'))
    return out


# ---------------------------------------------------------------- the call

def ally_count(hid, chain) -> int:
    """How many answer a chain of ``chain`` (0 to 5)."""
    table = list(horn(hid).get('allies_by_chain') or [0])
    c = max(0, min(int(chain or 0), len(table) - 1))
    return int(table[c])


def allies_for(hid, chain) -> list:
    """The kinds that answer, first in the roster first."""
    roster = list(horn(hid).get('roster') or ())
    return roster[:max(0, ally_count(hid, chain))]


def turns(hid) -> int:
    """How long those who answer stay: ten turns for every horn (Brandon,
    2026-11-16, down from 25 and 30)."""
    return int(horn(hid).get('turns', 10) or 10)


def delay(hid) -> int:
    return int(horn(hid).get('delay_turns', 0) or 0)


def line(hid, key, **kw) -> str:
    text = (horn(hid).get('lines') or {}).get(key, '')
    try:
        return text.format(**kw) if kw else text
    except (KeyError, IndexError, ValueError):
        return text


def chronicle_line(hid, who: str = '', failed: bool = False) -> str:
    """The Journal's line for a sounding (data/horns.json lines, linted by
    tests/test_chronicle_voice.py)."""
    return line(hid, 'chronicle_fail' if failed else 'chronicle', who=who)


def monster_defs() -> dict:
    global _MONSTERS
    if _MONSTERS is None:
        try:
            with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
                _MONSTERS = json.load(f)
        except (OSError, ValueError):
            _MONSTERS = {}
    return _MONSTERS


def ally_defn(kind) -> dict | None:
    d = monster_defs().get(kind)
    return d if isinstance(d, dict) else None


def ally_kinds() -> list:
    """Every kind any horn calls (each once)."""
    out = []
    for h in horns().values():
        for k in h.get('roster') or ():
            if k not in out:
                out.append(k)
    return out


def gate_guardians() -> frozenset:
    """The five gate bosses (data/domains.json): never a called ally's target."""
    global _GUARDIANS
    if _GUARDIANS is None:
        try:
            import decor
            _GUARDIANS = frozenset(d['boss'] for d in decor.domains() if d.get('boss'))
        except Exception:
            _GUARDIANS = frozenset({'asterion_minotaur', 'medusa_gorgon', 'fafnir_dragon',
                                    'fenrir_wolf', 'abaddon_destroyer'})
    return _GUARDIANS


def strikes(monster) -> bool:
    """May a called ally strike this creature? Never a gate's guardian."""
    return getattr(monster, 'kind', None) not in gate_guardians()


_NUMBERS = ('no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight',
            'nine', 'ten', 'eleven', 'twelve')


def who_line(kinds) -> str:
    """"Little John, Will Scarlet and two Yeoman Archers": the named first,
    in roster order, then the rest counted in words."""
    from naming import proper_name
    plurals = data().get('plurals') or {}
    order, counts = [], {}
    for k in kinds:
        if k not in counts:
            order.append(k)
        counts[k] = counts.get(k, 0) + 1
    named, rest = [], []
    for k in order:
        d = ally_defn(k) or {}
        name = proper_name(d.get('name') or k)
        if d.get('proper_noun'):
            named.append(name)
        else:
            n = counts[k]
            if n == 1:
                art = 'an' if name[:1].lower() in 'aeiou' else 'a'
                rest.append(f"{art} {name}")
            else:
                word = _NUMBERS[n] if n < len(_NUMBERS) else 'many'
                rest.append(f"{word} {plurals.get(k, name + 's')}")
    parts = named + rest
    if not parts:
        return ''
    if len(parts) == 1:
        return parts[0]
    return ', '.join(parts[:-1]) + ' and ' + parts[-1]


# ---------------------------------------------------------------- the ally

class CalledAlly(Pet):
    """One who answered a horn: Little John, Sir Gawain, one of the einherjar,
    Charlemagne. Built from the kind's own entry in data/monsters.json (its
    mean health, its first attack's dice and type); a helper that comes and
    goes, never the one companion (pet_system.is_companion). It follows the
    hero and fights what is near, never a gate's guardian; it does not heal or
    grow; after ``turns_remaining`` turns it leaves with its horn's line."""

    is_called = True
    # A class default, so a pickled ally from an older build reads these.
    bite_type = 'physical'
    attack_name = ''
    called_floor = None

    def __init__(self, kind: str, x: int, y: int, *, horn_id: str, turns: int):
        from naming import proper_name
        from sketch_manifest import mean_hp
        d = ally_defn(kind) or {}
        name = proper_name(d.get('name') or kind)
        atk = (d.get('attacks') or [{}])[0] or {}
        self.species_key = 'called'
        self.species = {
            'element': 'none', 'damage_type': atk.get('type', 'physical'),
            'color': tuple(d.get('color') or (200, 200, 200)),
            'stages': [{'name': name, 'symbol': d.get('symbol', '@'), 'msg': ''}] * 3,
            'specials': [], 'pronoun': d.get('pronoun', 'he'),
        }
        self.level = 1
        self.xp = 0
        self.x, self.y = int(x), int(y)
        self.alive = True
        self._regen_timer = 0
        self._passive_xp_timer = 0
        self.nickname = ''
        self.kills_count = 0
        self._special_cooldowns = {}
        self.command = 'return'
        self.last_pet_floor = -1
        self.rescue_spent_at = 0
        self.ally_kind = kind
        self.sprite_id = kind
        self.horn_id = horn_id
        self.display_name = name
        self.max_hp = self.hp = max(1, mean_hp(d))
        self._bite_dice = str(atk.get('damage') or '1d6')
        self.bite_type = atk.get('type') or 'physical'
        self.attack_name = atk.get('name', '')
        self.base_damage = max(1, mean_hp({'hp': self._bite_dice}))
        self.turns_remaining = max(1, int(turns))

    # A person (or one of the einherjar), not a species.
    @property
    def name(self) -> str:
        return self.display_name

    @property
    def species_name(self) -> str:
        return self.display_name

    @property
    def symbol(self) -> str:
        return self.species['stages'][0]['symbol']

    def get_attack_damage(self, quiz_accuracy: float = 0.5) -> int:
        """A blow by its own dice (monsters.json): what he is, not how the
        hero has been answering."""
        from dice import roll
        try:
            return max(1, roll(self._bite_dice))
        except Exception:
            return max(1, int(self.base_damage))

    def get_special_damage(self, quiz_accuracy: float = 0.5) -> int:
        return self.get_attack_damage(quiz_accuracy)

    def available_specials(self) -> list:
        return []

    def can_use_special(self, special_id=None) -> bool:
        return False

    def gain_xp(self, amount: int = 1) -> list:
        return []

    def gain_xp_passive(self) -> list:
        return []

    def tick_regen(self, bonus: int = 0):
        return None                      # one fight's help: no healing between

    def tick_duration(self) -> bool:
        """One turn of his stay gone. True when it is over (he leaves)."""
        self.turns_remaining -= 1
        if self.turns_remaining <= 0:
            self.alive = False
            return True
        return False

    def take_turn(self, player, dungeon, monsters, pets, ground_items=None):
        """Strike the nearest foe beside him, go for one within four tiles, or
        keep near the hero. A gate's guardian is never his to fight; a friend,
        or a lurker nobody has seen spring, is not a foe; nor is one at peace."""
        if not self.alive:
            return None
        import lore_powers
        from geom import chebyshev_distance
        nearest, best = None, 999
        for m in monsters:
            if not getattr(m, 'alive', False) or getattr(m, 'is_allied', False):
                continue
            if not strikes(m) or lore_powers.at_peace(m):
                continue
            if not getattr(m, '_aware', False) and getattr(m, 'ai_pattern', '') in ('ambush', 'mimic'):
                continue
            d = chebyshev_distance(self.x, self.y, m)
            if d < best:
                nearest, best = m, d
        if nearest is not None and best <= 1:
            return ('attack', nearest)
        if nearest is not None and best <= 4:
            self._move_toward(nearest.x, nearest.y, dungeon, monsters, pets, player, ground_items)
            return None
        if max(abs(self.x - player.x), abs(self.y - player.y)) > 2:
            self._move_toward(player.x, player.y, dungeon, monsters, pets, player, ground_items)
        return None

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__dict__.setdefault('turns_remaining', 0)
        self.__dict__.setdefault('horn_id', '')
