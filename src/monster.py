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

    # --- Combat ---

    def take_damage(self, amount: int) -> int:
        actual = max(0, amount)
        self.hp = max(0, self.hp - actual)
        if self.hp == 0:
            self.alive = False
        return actual

    def is_dead(self) -> bool:
        return not self.alive

    def attack(self, player) -> tuple[int, str]:
        """Monster attacks player. Returns (damage_dealt, message)."""
        if not self.attacks:
            # Floating eye: gaze-based paralysis (checks sleep_resist)
            if not player.has_effect('sleep_resist'):
                turns = max(player.status_effects.get('paralyzed', 0), 3)
                player.add_effect('paralyzed', turns)
                return 0, f"The {self.name}'s gaze paralyzes you for {turns} turns!"
            else:
                return 0, f"The {self.name} gazes at you harmlessly."

        atk = random.choice(self.attacks)

        # Invisible player: 30% miss chance
        if player.has_effect('invisible') and random.random() < 0.30:
            return 0, f"The {self.name} swings at you and misses!"

        dmg = roll(atk['damage'])
        actual = player.take_damage(dmg, atk.get('type', 'physical'))

        msg = f"The {self.name} {atk['name']}s you for {actual} damage!"

        # Drain attack: reduce CON if not drain_resist
        if atk.get('type') == 'drain' and not player.has_effect('drain_resist'):
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
                applied = player.add_effect(effect_id, duration)
                if applied:
                    msg += f" You are {effect_id}!"

        return actual, msg

    # --- AI ---

    def take_turn(self, player, dungeon, all_monsters) -> bool:
        """Execute this monster's turn. Returns True if it attacked the player."""
        if not self.alive:
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
            if dungeon.is_walkable(nx, ny) and (nx, ny) not in occupied and (nx, ny) != player_pos:
                self.x, self.y = nx, ny
                break

        return False

    def _adjacent_to(self, player) -> bool:
        dx = abs(self.x - player.x)
        dy = abs(self.y - player.y)
        return dx <= 1 and dy <= 1 and not (dx == 0 and dy == 0)

    def _preferred_dir(self, player, effective_pattern: str) -> tuple[int, int]:
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
