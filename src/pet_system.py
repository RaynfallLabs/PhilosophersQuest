"""
Pet companion system — Soul Sphere creatures that follow and fight alongside the player.
"""
import random

# ---------------------------------------------------------------------------
# Species data: 4 creature types × 3 evolution stages
# ---------------------------------------------------------------------------

_SPECIES = {
    'electric': {
        'element': 'electric',
        'damage_type': 'shock',
        'color': (255, 230, 50),
        'stages': [
            {'name': 'Zappik',       'symbol': 'z', 'msg': 'A tiny yellow rodent crackles to life!'},
            {'name': 'Voltpaw',      'symbol': 'Z', 'msg': '{old} surges with energy and evolves into Voltpaw!'},
            {'name': 'Thundertail',  'symbol': 'Z', 'msg': '{old} roars with lightning — it has become Thundertail!'},
        ],
        'special_name': 'Spark Bolt',
        'special_status': 'paralyzed',
        'special_status_chance': 0.25,
    },
    'water': {
        'element': 'water',
        'damage_type': 'cold',
        'color': (80, 160, 255),
        'stages': [
            {'name': 'Shellkit',     'symbol': 's', 'msg': 'A small blue turtle blinks into existence!'},
            {'name': 'Tideshell',    'symbol': 'S', 'msg': '{old} hardens its shell and evolves into Tideshell!'},
            {'name': 'Torrentoise',  'symbol': 'S', 'msg': '{old} unleashes a tidal surge — it has become Torrentoise!'},
        ],
        'special_name': 'Water Jet',
        'special_status': 'slowed',
        'special_status_chance': 0.30,
    },
    'plant': {
        'element': 'plant',
        'damage_type': 'poison',
        'color': (80, 200, 80),
        'stages': [
            {'name': 'Seedling',     'symbol': 'b', 'msg': 'A squat green creature with a bulb on its back appears!'},
            {'name': 'Thornback',    'symbol': 'B', 'msg': '{old} blooms with thorns and evolves into Thornback!'},
            {'name': 'Bloomsaur',    'symbol': 'B', 'msg': '{old} erupts in brilliant flowers — it has become Bloomsaur!'},
        ],
        'special_name': 'Vine Lash',
        'special_status': 'poisoned',
        'special_status_chance': 0.35,
    },
    'fire': {
        'element': 'fire',
        'damage_type': 'fire',
        'color': (255, 80, 40),
        'stages': [
            {'name': 'Emberpup',     'symbol': 'e', 'msg': 'A small red dragon-like creature bursts from the sphere!'},
            {'name': 'Flamescale',   'symbol': 'E', 'msg': '{old} spreads fiery wings and evolves into Flamescale!'},
            {'name': 'Infernodrake', 'symbol': 'E', 'msg': '{old} roars with infernal power — it has become Infernodrake!'},
        ],
        'special_name': 'Flame Breath',
        'special_status': 'burning',
        'special_status_chance': 0.30,
    },
}

# Evolution thresholds
_EVOLVE_1 = 33
_EVOLVE_2 = 66

# XP required to reach next level = current_level * 2
# Total XP to 100 ≈ 9900 turns; ~30 turns/floor × 100 floors = reasonable


class Pet:
    """A companion creature that follows the player and fights enemies."""

    def __init__(self, species_key: str, x: int = 0, y: int = 0):
        self.species_key = species_key
        self.species = _SPECIES[species_key]
        self.level = 1
        self.xp = 0
        self.x = x
        self.y = y
        self.alive = True
        self._special_cooldown = 0  # turns until special attack ready
        self._regen_timer = 0       # ticks toward HP regen

        # Stats computed from level
        self.max_hp = self._calc_max_hp()
        self.hp = self.max_hp
        self.base_damage = self._calc_damage()

    # --- Stats ---------------------------------------------------------------

    def _calc_max_hp(self) -> int:
        """HP: 20 at L1, ~200 at L100."""
        return 20 + int(self.level * 1.8)

    def _calc_damage(self) -> int:
        """Base attack damage: 3 at L1, ~30 at L100."""
        return 3 + int(self.level * 0.27)

    def _refresh_stats(self):
        old_max = self.max_hp
        self.max_hp = self._calc_max_hp()
        self.hp += (self.max_hp - old_max)  # heal the difference
        self.hp = min(self.hp, self.max_hp)
        self.base_damage = self._calc_damage()

    # --- Identity ------------------------------------------------------------

    @property
    def stage(self) -> int:
        if self.level >= _EVOLVE_2:
            return 2
        if self.level >= _EVOLVE_1:
            return 1
        return 0

    @property
    def name(self) -> str:
        return self.species['stages'][self.stage]['name']

    @property
    def symbol(self) -> str:
        return self.species['stages'][self.stage]['symbol']

    @property
    def color(self) -> tuple:
        return self.species['color']

    # --- Leveling ------------------------------------------------------------

    def gain_xp(self, amount: int = 1) -> list[str]:
        """Add XP, check for level ups. Returns list of messages."""
        if not self.alive or self.level >= 100:
            return []
        self.xp += amount
        messages = []
        while self.xp >= self._xp_to_next() and self.level < 100:
            self.xp -= self._xp_to_next()
            old_stage = self.stage
            old_name = self.name
            self.level += 1
            self._refresh_stats()
            new_stage = self.stage
            if new_stage > old_stage:
                # Evolution!
                msg = self.species['stages'][new_stage]['msg'].format(old=old_name)
                messages.append(msg)
            elif self.level % 10 == 0:
                messages.append(f"{self.name} has reached level {self.level}!")
        return messages

    def _xp_to_next(self) -> int:
        return self.level * 2

    # --- Combat --------------------------------------------------------------

    def get_attack_damage(self, quiz_accuracy: float = 0.5) -> int:
        """Basic melee attack. Scaled by recent quiz accuracy (capped 0.5-1.2)."""
        mult = 0.5 + min(0.7, quiz_accuracy * 0.7)
        return max(1, int(self.base_damage * mult))

    def get_special_damage(self, quiz_accuracy: float = 0.5) -> int:
        """Special elemental attack — 1.5× base, same quiz scaling."""
        mult = 0.5 + min(0.7, quiz_accuracy * 0.7)
        return max(1, int(self.base_damage * 1.5 * mult))

    def can_use_special(self) -> bool:
        return self._special_cooldown <= 0

    def use_special(self):
        self._special_cooldown = 8

    def tick_cooldown(self):
        if self._special_cooldown > 0:
            self._special_cooldown -= 1

    # --- HP Regen ------------------------------------------------------------

    def tick_regen(self, bonus: int = 0):
        """Regen 1+bonus HP every 3 turns."""
        if not self.alive:
            return
        self._regen_timer += 1
        if self._regen_timer >= 3:
            self._regen_timer = 0
            if self.hp < self.max_hp:
                self.hp = min(self.max_hp, self.hp + 1 + bonus)

    # --- Take damage ---------------------------------------------------------

    def take_damage(self, amount: int) -> int:
        actual = min(self.hp, max(0, amount))
        self.hp -= actual
        if self.hp <= 0:
            self.alive = False
        return actual

    def is_dead(self) -> bool:
        return not self.alive

    # --- AI ------------------------------------------------------------------

    def take_turn(self, player, dungeon, monsters, pets, ground_items=None) -> tuple[str, object] | None:
        """
        Pet AI turn. Returns (action_type, target) or None.
        action_type: 'attack', 'special', or None (just moved/idle).
        """
        if not self.alive:
            return None

        # Find nearest alive enemy monster
        nearest = None
        nearest_dist = 999
        for m in monsters:
            if not m.alive:
                continue
            d = max(abs(m.x - self.x), abs(m.y - self.y))
            if d < nearest_dist:
                nearest = m
                nearest_dist = d

        # Adjacent enemy: attack
        if nearest and nearest_dist <= 1:
            if self.can_use_special():
                return ('special', nearest)
            return ('attack', nearest)

        # Enemy within 4 tiles: move toward it
        if nearest and nearest_dist <= 4:
            self._move_toward(nearest.x, nearest.y, dungeon, monsters, pets, player, ground_items)
            return None

        # Otherwise: follow player (stay within 2 tiles)
        pdist = max(abs(self.x - player.x), abs(self.y - player.y))
        if pdist > 2:
            self._move_toward(player.x, player.y, dungeon, monsters, pets, player, ground_items)

        return None

    def _move_toward(self, tx, ty, dungeon, monsters, pets, player, ground_items=None):
        """Move one step toward (tx, ty) if possible. Avoids cursed ground items."""
        dx = 0 if tx == self.x else (1 if tx > self.x else -1)
        dy = 0 if ty == self.y else (1 if ty > self.y else -1)
        # Build set of cursed-item tiles to avoid
        _cursed_tiles = set()
        if ground_items:
            for gi in ground_items:
                if getattr(gi, 'buc', 'uncursed') == 'cursed':
                    _cursed_tiles.add((gi.x, gi.y))
        # Try preferred direction, then each axis
        for mx, my in [(dx, dy), (dx, 0), (0, dy)]:
            if mx == 0 and my == 0:
                continue
            nx, ny = self.x + mx, self.y + my
            if not dungeon.is_walkable(nx, ny):
                continue
            if nx == player.x and ny == player.y:
                continue
            if any(m.alive and m.x == nx and m.y == ny for m in monsters):
                continue
            if any(p.alive and p is not self and p.x == nx and p.y == ny for p in pets):
                continue
            if (nx, ny) in _cursed_tiles:
                continue  # pets instinctively avoid cursed items
            self.x, self.y = nx, ny
            return


_FENRIR_SPECIES = {
    'element': 'holy',
    'damage_type': 'holy',
    'color': (180, 200, 255),
    'stages': [
        {'name': 'Fenrir',   'symbol': 'F', 'msg': 'A colossal wolf materializes from the rift in reality — Fenrir has answered the call!'},
        {'name': 'Fenrir',   'symbol': 'F', 'msg': 'Fenrir grows stronger!'},
        {'name': 'Fenrir',   'symbol': 'F', 'msg': 'Fenrir howls with world-shaking power!'},
    ],
    'special_name': 'Ragnarok Bite',
    'special_status': 'bleeding',
    'special_status_chance': 0.50,
}


class FenrirPet(Pet):
    """Fenrir — the legendary wolf summoned by XYZZY tier 5.
    Extremely powerful, no leveling needed, fast regen, high damage."""

    def __init__(self, x: int = 0, y: int = 0):
        # Bypass normal Pet.__init__ to set custom stats
        self.species_key = 'fenrir'
        self.species = _FENRIR_SPECIES
        self.level = 100           # max level immediately
        self.xp = 0
        self.x = x
        self.y = y
        self.alive = True
        self._special_cooldown = 0
        self._regen_timer = 0

        self.max_hp = 500
        self.hp = 500
        self.base_damage = 45      # ~1.5× a max-level normal pet

    def _calc_max_hp(self) -> int:
        return 500

    def _calc_damage(self) -> int:
        return 45

    def gain_xp(self, amount: int = 1) -> list[str]:
        return []   # Fenrir doesn't level

    def tick_regen(self, bonus: int = 0):
        """Regen 3+bonus HP every turn (very fast)."""
        if not self.alive:
            return
        if self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + 3 + bonus)

    def take_turn(self, player, dungeon, monsters, pets, ground_items=None) -> tuple[str, object] | None:
        """Fenrir moves at double speed — gets two attempts to move/attack per turn."""
        if not self.alive:
            return None
        result = super().take_turn(player, dungeon, monsters, pets, ground_items)
        if result:
            return result
        # Second move attempt (fast wolf)
        return super().take_turn(player, dungeon, monsters, pets, ground_items)


class SketchedPet(Pet):
    """Temporary pet manifested from the Dreamspun Sketchbook.

    Inherits a monster's appearance and scaled-down stats.
    Lasts for a fixed number of turns, then dissolves.
    """

    SCALE = 0.40  # 40% of monster stats

    def __init__(self, monster, px: int, py: int, duration: int):
        # Build a fake species dict so the Pet base class can function
        sketch_species = {
            'element': 'sketch',
            'damage_type': 'physical',
            'color': (160, 140, 230),  # lavender tint
            'stages': [
                {'name': f'Sketched {monster.name}', 'symbol': monster.symbol, 'msg': ''},
                {'name': f'Sketched {monster.name}', 'symbol': monster.symbol, 'msg': ''},
                {'name': f'Sketched {monster.name}', 'symbol': monster.symbol, 'msg': ''},
            ],
            'special_name': '',
            'special_status': '',
            'special_status_chance': 0,
        }
        # Bypass normal __init__ species lookup
        self.species_key = 'sketch'
        self.species = sketch_species
        self.level = max(1, min(100, getattr(monster, 'min_level', 1)))
        self.xp = 0
        self.x = px
        self.y = py
        self.alive = True
        self._special_cooldown = 999  # no special attack
        self._regen_timer = 0

        # Scale from monster stats
        self.max_hp = max(10, int(monster.max_hp * self.SCALE))
        self.hp = self.max_hp
        # Compute base_damage from monster's first attack dice
        self._attack_dice = '1d4'
        if hasattr(monster, 'attacks') and monster.attacks:
            self._attack_dice = monster.attacks[0].get('damage', '1d4')
        self.base_damage = max(3, int(self._calc_dice_avg(self._attack_dice) * self.SCALE))

        # Monster identity (for sprite rendering and messages)
        self.monster_kind = monster.kind
        self.monster_name = monster.name
        self.is_sketch = True

        # Duration tracking
        self.turns_remaining = duration

    @staticmethod
    def _calc_dice_avg(dice_str: str) -> float:
        """Parse 'NdM+B' and return average roll."""
        import re
        m = re.match(r'(\d+)d(\d+)([+-]\d+)?', str(dice_str))
        if not m:
            return 5.0
        n, sides = int(m.group(1)), int(m.group(2))
        bonus = int(m.group(3)) if m.group(3) else 0
        return n * (sides + 1) / 2 + bonus

    @property
    def name(self) -> str:
        return f'Sketched {self.monster_name}'

    def get_attack_damage(self, quiz_accuracy: float = 0.5) -> int:
        """Roll the monster's attack dice at 40% power."""
        from dice import roll
        raw = roll(self._attack_dice)
        return max(1, int(raw * self.SCALE))

    def get_special_damage(self, quiz_accuracy: float = 0.5) -> int:
        return self.get_attack_damage(quiz_accuracy)

    def can_use_special(self) -> bool:
        return False

    def gain_xp(self, amount: int = 1) -> list[str]:
        return []  # sketched pets don't level

    def tick_duration(self) -> bool:
        """Decrement timer. Returns True if expired (pet should dissolve)."""
        self.turns_remaining -= 1
        if self.turns_remaining <= 0:
            self.alive = False
            return True
        return False


class DadPet(Pet):
    """Dad. Invincible. 9999 damage. 5 turns. Everything will be fine."""

    def __init__(self, x: int, y: int, duration: int = 5):
        dad_species = {
            'element': 'dad',
            'damage_type': 'physical',
            'color': (255, 220, 100),
            'stages': [
                {'name': 'Dad', 'symbol': '@', 'msg': ''},
                {'name': 'Dad', 'symbol': '@', 'msg': ''},
                {'name': 'Dad', 'symbol': '@', 'msg': ''},
            ],
            'special_name': '',
            'special_status': '',
            'special_status_chance': 0,
        }
        self.species_key = 'dad'
        self.species = dad_species
        self.level = 100
        self.xp = 0
        self.x = x
        self.y = y
        self.alive = True
        self._special_cooldown = 999
        self._regen_timer = 0

        self.max_hp = 99999
        self.hp = 99999
        self.base_damage = 9999

        self.is_dad = True
        self.turns_remaining = duration

    @property
    def name(self) -> str:
        return 'Dad'

    def get_attack_damage(self, quiz_accuracy: float = 0.5) -> int:
        return 9999

    def get_special_damage(self, quiz_accuracy: float = 0.5) -> int:
        return 9999

    def can_use_special(self) -> bool:
        return False

    def take_damage(self, amount: int) -> int:
        return 0  # invincible

    def gain_xp(self, amount: int = 1) -> list[str]:
        return []

    def tick_duration(self) -> bool:
        """Decrement timer. Returns True if Dad is leaving."""
        self.turns_remaining -= 1
        if self.turns_remaining <= 0:
            self.alive = False
            return True
        return False


def random_species() -> str:
    """Pick a random species key with equal probability."""
    return random.choice(list(_SPECIES.keys()))
