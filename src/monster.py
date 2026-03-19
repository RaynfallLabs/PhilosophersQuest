import random
from dice import roll


class Monster:
    def __init__(self, defn: dict, x: int, y: int):
        self.kind = defn['id']
        self.name = defn['name']
        self.symbol = defn['symbol']
        self.color = tuple(defn['color'])
        self.ai_pattern = defn.get('ai_pattern', 'aggressive')
        self.speed = defn.get('speed', 1)
        self.attacks = defn.get('attacks', [])

        hp_str = str(defn['hp'])
        self.max_hp = int(hp_str) if hp_str.isdigit() else roll(hp_str)
        self.hp = self.max_hp

        self.x = x
        self.y = y
        self.alive = True

        self.harvest_tier      = defn.get('harvest_tier', 1)
        self.harvest_threshold = defn.get('harvest_threshold', 2)
        self.ingredient_id     = defn.get('ingredient_id', None)
        self.min_level: int    = int(defn.get('min_level', 1))
        self.max_level         = defn.get('max_level', None)  # soft cap; None = no cap

        # THAC0: "To Hit Armor Class Zero". Lower = more accurate.
        self.thac0: int = int(defn.get('thac0', max(-10, 20 - defn.get('min_level', 1))))

        # Resistances and weaknesses (damage type strings)
        self.resistances: list[str] = defn.get('resistances', [])
        self.weaknesses:  list[str] = defn.get('weaknesses', [])

        # Treasure drop definition
        self.treasure: dict = defn.get('treasure', {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1})

        # Lore text revealed when corpse is identified
        self.lore: str = defn.get('lore', '')

        # Minimal status effects for wand interactions
        self.status_effects: dict[str, int] = {}  # effect_id -> turns remaining

    # --- Status effects ---

    def add_effect(self, name: str, duration: int):
        current = self.status_effects.get(name, 0)
        self.status_effects[name] = min(current + duration, 60)

    def has_effect(self, name: str) -> bool:
        return self.status_effects.get(name, 0) > 0

    def tick_effects(self):
        """Decrement all active effects by one turn. Apply damage-over-time effects."""
        bleeding_dmg = 0
        poison_dmg   = 0
        burning_dmg  = 0
        disease_tick = False
        for name in list(self.status_effects):
            val = self.status_effects[name]
            if val > 0:
                if name == 'bleeding':
                    bleeding_dmg = max(1, self.max_hp // 15)
                elif name == 'poisoned':
                    poison_dmg = 1
                elif name == 'diseased':
                    disease_tick = True
                elif name == 'burning':
                    burning_dmg = max(1, self.max_hp // 20)
            self.status_effects[name] -= 1
            if self.status_effects[name] <= 0:
                del self.status_effects[name]
                if name == 'petrifying':
                    self.hp = 0
                    self.alive = False
        if bleeding_dmg > 0:
            self.take_damage(bleeding_dmg)
        if poison_dmg > 0:
            self.take_damage(poison_dmg)
        if burning_dmg > 0:
            self.take_damage(burning_dmg)
        if disease_tick and random.random() < 0.08:
            self.take_damage(max(1, self.max_hp // 20))

    # --- Combat ---

    def take_damage(self, amount: int) -> int:
        actual = max(0, amount)
        self.hp = max(0, self.hp - actual)
        if self.hp == 0:
            self.alive = False
        if actual > 0:
            self.status_effects.pop('sleeping', None)
        return actual

    def is_dead(self) -> bool:
        return not self.alive

    def attack(self, player) -> tuple[int, str]:
        """Monster attacks player using THAC0 vs player AC. Returns (damage_dealt, message)."""
        if not self.attacks:
            # Floating eye: gaze-based paralysis (checks sleep_resist)
            if not player.has_effect('sleep_resist'):
                turns = max(player.status_effects.get('paralyzed', 0), 3)
                player.add_effect('paralyzed', turns)
                return 0, f"The {self.name}'s gaze paralyzes you for {turns} turns!"
            else:
                return 0, f"The {self.name} gazes at you harmlessly."

        atk = random.choice(self.attacks)

        # -- THAC0 Attack Roll ----------------------------------------------
        d20 = random.randint(1, 20)
        player_ac = player.get_ac()
        to_hit = self.thac0 - player_ac   # roll must be >= this to hit

        # Natural 1 always misses; natural 20 always hits
        if d20 == 1:
            return 0, f"The {self.name} swings at you and misses!"
        if d20 != 20 and d20 < to_hit:
            return 0, f"The {self.name} swings at you and misses! (AC {player_ac} deflects)"

        # Displacement: 30% miss chance even on successful attack roll
        if player.has_effect('displacement') and random.random() < 0.30:
            return 0, f"The {self.name} strikes at your displaced image and misses!"

        # -- Hit: roll damage -----------------------------------------------
        dmg = roll(atk['damage'])
        atk_type = atk.get('type', 'physical')

        # Weakened: this monster's attack deals half damage
        if self.has_effect('weakened'):
            dmg = max(1, dmg // 2)

        actual = player.take_damage(dmg, atk_type)

        msg = f"The {self.name} {atk['name']}s you for {actual} damage!"

        # Fire/cold shield: if attack was blocked (actual=0), reflect damage back
        if actual == 0 and atk_type == 'fire' and player.has_effect('fire_shield'):
            refl = max(1, dmg // 2)
            self.take_damage(refl)
            msg = f"The {self.name}'s fire reflects back! ({refl} dmg)"
        elif actual == 0 and atk_type == 'cold' and player.has_effect('cold_shield'):
            refl = max(1, dmg // 2)
            self.take_damage(refl)
            msg = f"The {self.name}'s cold reflects back! ({refl} dmg)"

        # Drain attack: reduce CON if not drain_resist
        if atk_type == 'drain' and not player.has_effect('drain_resist'):
            old_con = player.CON
            player.apply_stat_bonus('CON', -1)
            if player.CON < old_con:
                msg = f"The {self.name} drains your life force! ({actual} dmg, CON -1)"

        # Apply status effect from attack
        effect_id = atk.get('effect')
        if effect_id:
            chance   = atk.get('effect_chance', 0.30)
            duration = atk.get('effect_duration', 5)
            if random.random() < chance:
                # Reflecting: 50% chance to bounce effect back at attacker
                if player.has_effect('reflecting') and random.random() < 0.50:
                    self.add_effect(effect_id, duration)
                    msg += f" The effect reflects back -- the {self.name} is {effect_id}!"
                else:
                    applied = player.add_effect(effect_id, duration)
                    if applied:
                        msg += f" You are {effect_id}!"

        return actual, msg

    # --- AI ---

    def take_turn(self, player, dungeon, all_monsters) -> bool:
        """Execute this monster's turn. Returns True if it attacked the player."""
        if not self.alive:
            return False

        self.tick_effects()

        # Immobilised by sleep or paralysis
        if self.has_effect('sleeping') or self.has_effect('paralyzed'):
            return False

        # Slowed: skip every other turn
        if self.has_effect('slowed'):
            self._slow_skip = not getattr(self, '_slow_skip', False)
            if self._slow_skip:
                return False

        # Aggravated overrides passive/cowardly AI patterns
        effective_pattern = self.ai_pattern
        if player.has_effect('aggravated') and effective_pattern in ('sessile', 'cowardly'):
            effective_pattern = 'aggressive'

        if effective_pattern == 'sessile':
            return False

        if self._adjacent_to(player):
            return True  # caller triggers the attack

        dx, dy = self._preferred_dir(player, effective_pattern)
        candidates = self._move_candidates(dx, dy)

        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        player_pos = (player.x, player.y)

        for ddx, ddy in candidates:
            nx, ny = self.x + ddx, self.y + ddy
            if (nx, ny) in occupied or (nx, ny) == player_pos:
                continue
            tile = dungeon.tiles[ny][nx] if dungeon.in_bounds(nx, ny) else 0
            from dungeon import DOOR
            if tile == DOOR:
                dungeon.open_door(nx, ny)   # monsters open doors
                self.x, self.y = nx, ny
                break
            if dungeon.is_walkable(nx, ny):
                self.x, self.y = nx, ny
                break

        return False

    def _adjacent_to(self, player) -> bool:
        dx = abs(self.x - player.x)
        dy = abs(self.y - player.y)
        return dx <= 1 and dy <= 1 and not (dx == 0 and dy == 0)

    def _preferred_dir(self, player, effective_pattern: str) -> tuple[int, int]:
        # Confused or blinded monsters stumble randomly
        if self.has_effect('confused') or self.has_effect('blinded'):
            return random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
        dx = 0 if self.x == player.x else (1 if player.x > self.x else -1)
        dy = 0 if self.y == player.y else (1 if player.y > self.y else -1)
        if effective_pattern == 'cowardly':
            dx, dy = -dx, -dy
        return dx, dy

    def _move_candidates(self, dx: int, dy: int) -> list[tuple[int, int]]:
        if self.ai_pattern == 'grid_bug':
            opts = []
            if dx:
                opts.append((dx, 0))
            if dy:
                opts.append((0, dy))
            random.shuffle(opts)
            return opts

        if dx and dy:
            return [(dx, dy), (dx, 0), (0, dy)]
        if dx:
            return [(dx, 0), (0, 1), (0, -1)]
        if dy:
            return [(0, dy), (1, 0), (-1, 0)]
        return []


class DeathMonster(Monster):
    """The Grim Reaper -- invincible pursuer spawned when the player ascends from L100
    with the Philosopher's Stone.  Moves at half speed but always hits and deals
    heavy damage.  Cannot be killed, dispelled, or escaped -- only outrun."""

    _DEFN = {
        'id': 'death',
        'name': 'Death',
        'symbol': 'D',
        'color': [220, 220, 255],
        'ai_pattern': 'aggressive',
        'speed': 1,
        'hp': '1',          # irrelevant -- take_damage is overridden
        'attacks': [{'name': 'reap', 'damage': '3d20+50', 'type': 'physical'}],
        'thac0': -20,       # always hits
        'resistances': [],
        'weaknesses':  [],
        'treasure':    {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
        'lore': '',
        'min_level': 100,
    }

    def __init__(self, x: int = 0, y: int = 0):
        super().__init__(self._DEFN, x, y)
        self.hp      = 9999
        self.max_hp  = 9999
        self._half_speed_skip = False   # toggled each turn; True = skip this turn

    # Death cannot be harmed
    def take_damage(self, amount: int) -> int:
        return 0

    def is_dead(self) -> bool:
        return False

    # Effects don't stick to Death (no sleeping, paralysis, poison, etc.)
    def tick_effects(self):
        pass

    def add_effect(self, name: str, duration: int):
        pass

    def take_turn(self, player, dungeon, all_monsters) -> bool:
        """Half-speed: acts on alternating turns only."""
        self._half_speed_skip = not self._half_speed_skip
        if self._half_speed_skip:
            return False
        return super().take_turn(player, dungeon, all_monsters)

    def attack(self, player) -> tuple[int, str]:
        """Death always hits -- no THAC0 roll needed."""
        dmg = roll(self._DEFN['attacks'][0]['damage'])
        actual = player.take_damage(dmg, 'physical')
        return actual, f"Death's scythe tears through you for {actual} damage!"
