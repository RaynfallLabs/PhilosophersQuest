"""
Pet companion system — Soul Sphere creatures that follow and fight alongside the player.
"""
import random
from geom import monster_at_tile, is_at_tile

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
        'specials': [
            {
                'id': 'spark_bolt', 'name': 'Spark Bolt', 'unlock_stage': 1,
                'damage_mult': 1.5, 'damage_type': 'shock',
                'targeting': 'single', 'range': 5,
                'status': 'paralyzed', 'status_chance': 0.50, 'status_duration': 2,
                'cooldown': 250,
                'desc': "Range 5 single target; 1.5x damage; 50% paralyze (2 turns).",
            },
            {
                'id': 'thunder_strike', 'name': 'Thunder Strike', 'unlock_stage': 2,
                'damage_mult': 2.0, 'damage_type': 'shock',
                'targeting': 'aoe', 'range': 4, 'aoe_radius': 1,
                'status': 'paralyzed', 'status_chance': 0.40, 'status_duration': 1,
                'cooldown': 400,
                'desc': "Range 4; AoE 3x3; 2x damage; 40% paralyze all hit.",
            },
        ],
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
        'specials': [
            {
                'id': 'water_jet', 'name': 'Water Jet', 'unlock_stage': 1,
                'damage_mult': 1.5, 'damage_type': 'cold',
                'targeting': 'single', 'range': 4,
                'status': 'slowed', 'status_chance': 0.60, 'status_duration': 3,
                'knockback': 1,
                'cooldown': 250,
                'desc': "Range 4 single target; 1.5x damage; knockback; 60% slow.",
            },
            {
                'id': 'tidal_crash', 'name': 'Tidal Crash', 'unlock_stage': 2,
                'damage_mult': 1.8, 'damage_type': 'cold',
                'targeting': 'line', 'range': 4,
                'status': 'slowed', 'status_chance': 0.50, 'status_duration': 4,
                'knockback': 1,
                'cooldown': 400,
                'desc': "Line 4 tiles; 1.8x damage; knockback + 50% slow all hit.",
            },
        ],
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
        'specials': [
            {
                'id': 'vine_lash', 'name': 'Vine Lash', 'unlock_stage': 1,
                'damage_mult': 1.5, 'damage_type': 'poison',
                'targeting': 'single', 'range': 3,
                'status': 'immobilized', 'status_chance': 0.70, 'status_duration': 2,
                'cooldown': 250,
                'desc': "Range 3 single target; 1.5x damage; 70% root (2 turns).",
            },
            {
                'id': 'bloomburst', 'name': 'Bloomburst', 'unlock_stage': 2,
                'damage_mult': 0.4, 'damage_type': 'poison',
                'targeting': 'aoe', 'range': 0, 'aoe_radius': 2,
                'status': 'poisoned', 'status_chance': 1.0, 'status_duration': 5,
                'cooldown': 400,
                'desc': "Pet-centered AoE radius 2; small damage; ALWAYS poisons (5 turns).",
            },
        ],
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
        'specials': [
            {
                'id': 'flame_breath', 'name': 'Flame Breath', 'unlock_stage': 1,
                'damage_mult': 1.5, 'damage_type': 'fire',
                'targeting': 'cone', 'range': 3,
                'status': 'burning', 'status_chance': 0.50, 'status_duration': 3,
                'cooldown': 250,
                'desc': "Cone 3 tiles forward; 1.5x damage; 50% burn (3 turns).",
            },
            {
                'id': 'inferno_pillar', 'name': 'Inferno Pillar', 'unlock_stage': 2,
                'damage_mult': 2.5, 'damage_type': 'fire',
                'targeting': 'aoe', 'range': 5, 'aoe_radius': 1,
                'status': 'burning', 'status_chance': 0.75, 'status_duration': 4,
                'cooldown': 400,
                'desc': "Range 5; AoE 3x3; 2.5x damage center; 75% burn (4 turns).",
            },
        ],
    },
}

# Evolution thresholds — major Pokémon-style milestones.
# Stage 1 (L25): ~20 floors of dedicated bonding to achieve.
# Stage 2 (L55): late-run / endgame achievement; rare for casual runs.
_EVOLVE_1 = 25
_EVOLVE_2 = 55

# XP curve: xp_to_next = level * _XP_PER_LEVEL. Total to L25 ≈ 6,000 XP,
# total to L55 ≈ 30,000 XP. Combined with passive (1/3 turns) + kill XP
# scaling with monster max_hp, stage 1 lands around floor 20-25 of
# pet's life, stage 2 only with deep play.
_XP_PER_LEVEL = 20


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
        self._regen_timer = 0       # ticks toward HP regen
        self._passive_xp_timer = 0  # ticks toward next passive XP grain
        # Player-given nickname (set via the naming popup on hatch). Empty
        # string means use the species name directly.
        self.nickname: str = ''
        # Lifetime kill counter (chronicle / future achievements).
        self.kills_count: int = 0
        # Per-special cooldown tracking; key = special_id, value = turns remaining.
        # Initialized empty; populated as specials unlock + are used.
        self._special_cooldowns: dict[str, int] = {}
        # AI command: 'return' (default — follow player + attack), 'stay' (hold
        # position, attack adjacent only), 'wander' (roam aggressively within
        # 8 tiles; don't auto-follow player).
        self.command: str = 'return'
        # Floor on which this pet last received a "pet" interaction (once-per-floor cooldown).
        self.last_pet_floor: int = -1

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
    def species_name(self) -> str:
        """The species' name at the current evolution stage."""
        return self.species['stages'][self.stage]['name']

    @property
    def name(self) -> str:
        """Display name. If the player has given a nickname, shows
        'Nickname the Species'; otherwise just the species name."""
        sp = self.species_name
        if self.nickname:
            return f"{self.nickname} the {sp}"
        return sp

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
            old_species = self.species_name
            self.level += 1
            self._refresh_stats()
            new_stage = self.stage
            if new_stage > old_stage:
                # Evolution! Use species-name placeholder; the message
                # template has {old} for the prior form.
                new_species = self.species_name
                if self.nickname:
                    msg = (f"{self.nickname} the {old_species} grows brighter — "
                           f"it has evolved into {new_species}!")
                else:
                    msg = self.species['stages'][new_stage]['msg'].format(old=old_species)
                messages.append(msg)
            elif self.level % 10 == 0:
                messages.append(f"{self.name} has reached level {self.level}!")
        return messages

    def gain_xp_passive(self) -> list[str]:
        """Passive XP — call once per pet turn. Awards 1 XP every 3rd call."""
        if not self.alive:
            return []
        self._passive_xp_timer += 1
        if self._passive_xp_timer >= 3:
            self._passive_xp_timer = 0
            return self.gain_xp(1)
        return []

    def gain_xp_from_kill(self, monster_max_hp: int) -> list[str]:
        """Award XP for a kill, scaled by monster strength.

        Formula: 3 + max_hp // 10 (so a 10-HP F1 monster grants 4 XP; a
        200-HP F90 monster grants 23 XP). Combined with passive ticks and
        late-pickup catch-up, pets level steadily through normal play.
        """
        self.kills_count += 1
        xp = 3 + max(0, int(monster_max_hp)) // 10
        return self.gain_xp(xp)

    def apply_late_pickup_bonus(self, floor: int) -> None:
        """One-time XP grant for pets hatched on deeper floors so they
        don't start uselessly underpowered. Capped just below stage 1
        evolution (level 25) so the late pet still has to EARN its first
        big milestone — but it won't take 20 floors of catch-up to do so.
        """
        bonus = min(max(0, int(floor)) * 50, 4000)
        if bonus > 0:
            self.gain_xp(bonus)

    def _xp_to_next(self) -> int:
        return self.level * _XP_PER_LEVEL

    # --- Combat --------------------------------------------------------------

    def get_attack_damage(self, quiz_accuracy: float = 0.5) -> int:
        """Basic melee attack. Scaled by recent quiz accuracy (capped 0.5-1.2)."""
        mult = 0.5 + min(0.7, quiz_accuracy * 0.7)
        return max(1, int(self.base_damage * mult))

    def get_special_damage(self, quiz_accuracy: float = 0.5) -> int:
        """Special elemental attack — 1.5× base, same quiz scaling."""
        mult = 0.5 + min(0.7, quiz_accuracy * 0.7)
        return max(1, int(self.base_damage * 1.5 * mult))

    def available_specials(self) -> list[dict]:
        """Return the specials unlocked at the pet's current evolution stage.

        unlock_stage 1 = available at stage 1 (level >= _EVOLVE_1);
        unlock_stage 2 = available at stage 2 (level >= _EVOLVE_2).
        Stage 0 pets (pre-evolution) have no specials.
        """
        specials = self.species.get('specials', [])
        return [s for s in specials if s.get('unlock_stage', 1) <= self.stage]

    def special_cooldown(self, special_id: str) -> int:
        """Turns remaining until the named special is ready (0 = ready)."""
        return self._special_cooldowns.get(special_id, 0)

    def can_use_special(self, special_id: str | None = None) -> bool:
        """True if `special_id` is unlocked AND its cooldown is 0.

        Legacy compatibility: calling without an id returns True iff ANY
        unlocked special is ready (used by Phase-1 AI code that didn't
        target a specific attack).
        """
        avail = self.available_specials()
        if not avail:
            return False
        if special_id is None:
            return any(self.special_cooldown(s['id']) == 0 for s in avail)
        return (any(s['id'] == special_id for s in avail)
                and self.special_cooldown(special_id) == 0)

    def use_special(self, special_id: str | None = None):
        """Mark a special as just-used; sets its cooldown from the species data.

        If `special_id` is None, applies to the first available special.
        """
        avail = self.available_specials()
        if not avail:
            return
        target = None
        if special_id is None:
            target = avail[0]
        else:
            for s in avail:
                if s['id'] == special_id:
                    target = s
                    break
        if target is None:
            return
        self._special_cooldowns[target['id']] = int(target.get('cooldown', 250))

    def tick_cooldown(self):
        """Decrement every active cooldown by 1; remove zero/negative entries."""
        if not self._special_cooldowns:
            return
        for sid in list(self._special_cooldowns):
            self._special_cooldowns[sid] -= 1
            if self._special_cooldowns[sid] <= 0:
                del self._special_cooldowns[sid]

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
        """Pet AI turn. Returns (action_type, target) or None.

        action_type is only ever 'attack' here; specials are player-triggered
        via the pet menu (Shift+P) post-2026-05-17. The command field
        controls movement behavior:
          'return' - follow player; engage enemies within 4 tiles (default)
          'stay'   - hold position; only attack adjacent enemies
          'wander' - aggressive: engage enemies within 8 tiles; don't auto-follow
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

        # Adjacent enemy: always melee-attack regardless of command.
        if nearest and nearest_dist <= 1:
            return ('attack', nearest)

        cmd = getattr(self, 'command', 'return')

        # Stay: don't move from current tile. Only attack adjacent (handled above).
        if cmd == 'stay':
            return None

        # Wander: engage within 8 tiles, don't auto-follow player.
        if cmd == 'wander':
            if nearest and nearest_dist <= 8:
                self._move_toward(nearest.x, nearest.y, dungeon, monsters, pets, player, ground_items)
            return None

        # Default 'return': enemy within 4 tiles → engage; otherwise follow player.
        if nearest and nearest_dist <= 4:
            self._move_toward(nearest.x, nearest.y, dungeon, monsters, pets, player, ground_items)
            return None
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
            if monster_at_tile(monsters, nx, ny) is not None:
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
        # Required by base Pet methods called every turn from game_combat
        # (gain_xp_passive, tick_cooldown, name property, command-aware AI).
        self._passive_xp_timer = 0
        self._special_cooldowns: dict[str, int] = {}
        self.nickname: str = ''
        self.kills_count: int = 0
        self.command: str = 'return'
        self.last_pet_floor: int = -1

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
        # Required by base Pet methods called every turn from game_combat.
        self._passive_xp_timer = 0
        self._special_cooldowns: dict[str, int] = {}
        self.nickname: str = ''
        self.kills_count: int = 0
        self.command: str = 'return'
        self.last_pet_floor: int = -1

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
        # Required by base Pet methods called every turn from game_combat.
        self._passive_xp_timer = 0
        self._special_cooldowns: dict[str, int] = {}
        self.nickname: str = ''
        self.kills_count: int = 0
        self.command: str = 'return'
        self.last_pet_floor: int = -1

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


class UnicornPet(Pet):
    """Ethereal Unicorn — healer companion obtained through the unicorn encounter.

    Does NOT attack enemies. Instead:
    - Heals player 3-5 HP every 4 turns
    - Removes one negative status effect every 8 turns
    - Detects traps within 3 tiles (sets trap.detected = True)
    - Not targeted by enemies (but AoE/traps can still hit her)
    - Follows the player between levels
    """

    def __init__(self, x: int = 0, y: int = 0):
        unicorn_species = {
            'element': 'holy',
            'damage_type': 'holy',
            'color': (255, 255, 240),
            'stages': [
                {'name': 'Ethereal Unicorn', 'symbol': 'u', 'msg': ''},
                {'name': 'Ethereal Unicorn', 'symbol': 'u', 'msg': ''},
                {'name': 'Ethereal Unicorn', 'symbol': 'u', 'msg': ''},
            ],
            'special_name': 'Purify',
            'special_status': '',
            'special_status_chance': 0,
        }
        self.species_key = 'unicorn'
        self.species = unicorn_species
        self.level = 30
        self.xp = 0
        self.x = x
        self.y = y
        self.alive = True
        self._special_cooldown = 0
        self._regen_timer = 0
        self._heal_timer = 0
        self._cleanse_timer = 0
        self.is_unicorn = True
        # Required by base Pet methods called every turn from game_combat.
        self._passive_xp_timer = 0
        self._special_cooldowns: dict[str, int] = {}
        self.nickname: str = ''
        self.kills_count: int = 0
        self.command: str = 'return'
        self.last_pet_floor: int = -1

        self.max_hp = 120
        self.hp = 120
        self.base_damage = 0  # unicorn does not attack

    @property
    def name(self) -> str:
        return 'Ethereal Unicorn'

    @property
    def symbol(self) -> str:
        return 'u'

    @property
    def color(self) -> tuple:
        return (255, 255, 240)

    def get_attack_damage(self, quiz_accuracy: float = 0.5) -> int:
        return 0  # unicorn does not attack

    def get_special_damage(self, quiz_accuracy: float = 0.5) -> int:
        return 0

    def can_use_special(self) -> bool:
        return False

    def gain_xp(self, amount: int = 1) -> list[str]:
        return []  # unicorn doesn't level

    def tick_regen(self, bonus: int = 0):
        """Unicorn regens 2 HP every 3 turns."""
        if not self.alive:
            return
        self._regen_timer += 1
        if self._regen_timer >= 3:
            self._regen_timer = 0
            if self.hp < self.max_hp:
                self.hp = min(self.max_hp, self.hp + 2)

    def take_turn(self, player, dungeon, monsters, pets, ground_items=None) -> tuple | None:
        """Unicorn AI: follow player, heal, cleanse, detect traps. Never attacks."""
        if not self.alive:
            return None

        messages = []

        # Heal player every 4 turns
        self._heal_timer += 1
        if self._heal_timer >= 4:
            self._heal_timer = 0
            if player.hp < player.max_hp:
                heal = random.randint(3, 5)
                player.hp = min(player.max_hp, player.hp + heal)
                messages.append(('heal', heal))

        # Cleanse one negative status every 8 turns
        self._cleanse_timer += 1
        if self._cleanse_timer >= 8:
            self._cleanse_timer = 0
            from status_effects import DEBUFFS
            active_debuffs = [e for e in player.status_effects if e in DEBUFFS]
            if active_debuffs:
                removed = active_debuffs[0]
                player.status_effects.pop(removed, None)
                messages.append(('cleanse', removed))

        # Detect traps within 3 tiles. Setting `revealed=True` is what the
        # rest of the engine uses (renderer, _check_floor_trap, _try_disarm_trap).
        # Pre-2026-05-17 this set `detected` which was unused — silent no-op bug.
        if hasattr(dungeon, 'traps'):
            for (tx, ty), trap in dungeon.traps.items():
                if abs(tx - self.x) <= 3 and abs(ty - self.y) <= 3:
                    if not trap.get('revealed', False):
                        trap['revealed'] = True
                        messages.append(('trap', tx, ty))

        # Follow player — stay within 2 tiles
        pdist = max(abs(self.x - player.x), abs(self.y - player.y))
        if pdist > 2:
            self._move_toward(player.x, player.y, dungeon, monsters, pets, player, ground_items)

        if messages:
            return ('unicorn_actions', messages)
        return None


def random_species() -> str:
    """Pick a random species key with equal probability."""
    return random.choice(list(_SPECIES.keys()))
