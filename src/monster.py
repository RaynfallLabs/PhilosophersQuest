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

        hp_str = defn['hp']
        self.max_hp = int(hp_str) if hp_str.isdigit() else roll(hp_str)
        self.hp = self.max_hp

        self.x = x
        self.y = y
        self.alive = True

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
            # No damage attack — floating eye paralyzes
            turns = max(player.status_effects.get('paralyzed', 0), 3)
            player.status_effects['paralyzed'] = turns
            return 0, f"The {self.name}'s gaze paralyzes you for {turns} turns!"

        atk = random.choice(self.attacks)
        dmg = roll(atk['damage'])
        actual = player.take_damage(dmg, atk.get('type', 'physical'))
        return actual, f"The {self.name} {atk['name']}s you for {actual} damage!"

    # --- AI ---

    def take_turn(self, player, dungeon, all_monsters) -> bool:
        """Execute this monster's turn. Returns True if it attacked the player."""
        if self.ai_pattern == 'sessile' or not self.alive:
            return False

        if self._adjacent_to(player):
            return True  # caller triggers the attack

        dx, dy = self._preferred_dir(player)
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

    def _preferred_dir(self, player) -> tuple[int, int]:
        dx = 0 if self.x == player.x else (1 if player.x > self.x else -1)
        dy = 0 if self.y == player.y else (1 if player.y > self.y else -1)
        if self.ai_pattern == 'cowardly':
            dx, dy = -dx, -dy
        return dx, dy

    def _move_candidates(self, dx: int, dy: int) -> list[tuple[int, int]]:
        if self.ai_pattern == 'grid_bug':
            # Orthogonal only, pick a random axis
            opts = []
            if dx:
                opts.append((dx, 0))
            if dy:
                opts.append((0, dy))
            random.shuffle(opts)
            return opts

        # Diagonal first, then orthogonal fallbacks
        if dx and dy:
            return [(dx, dy), (dx, 0), (0, dy)]
        if dx:
            return [(dx, 0), (0, 1), (0, -1)]
        if dy:
            return [(0, dy), (1, 0), (-1, 0)]
        return []
