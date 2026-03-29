import random
from dice import roll
from combat import _line_of_sight


class Monster:
    def __init__(self, defn: dict, x: int, y: int):
        self.kind = defn['id']
        self.name = defn['name']
        self.symbol = defn['symbol']
        self.color = tuple(defn['color'])
        self.ai_pattern = defn.get('ai_pattern', 'aggressive')
        self.speed = defn.get('speed', 10)
        self.attacks = defn.get('attacks', [])

        hp_str = str(defn['hp'])
        self.max_hp = int(hp_str) if hp_str.isdigit() else roll(hp_str)
        self.hp = self.max_hp

        self.x = x
        self.y = y
        self.alive = True

        # --- NetHack-inspired AI state ---
        self._flee_timer: int = 0       # turns remaining in flee mode
        self._alerted: bool = False     # woken by a nearby ally's call for help
        self._slow_skip: bool = False   # used by variable-speed skip logic

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

        # --- Hit-and-run AI state (Asterion) ---
        self.can_phase_walls: bool = defn.get('can_phase_walls', False)
        self._hit_run_state: str = 'hunting'   # hunting / retreating / hiding
        self._hit_run_timer: int = 0            # turns in current state
        self._hit_run_attacks: int = 0          # attacks landed this engagement

        # --- Gaze attack (Medusa) ---
        self.gaze_paralyze: int = defn.get('gaze_paralyze', 0)      # paralyze duration (0 = no gaze)
        self.gaze_cooldown_max: int = defn.get('gaze_cooldown', 4)   # turns between gazes
        self._gaze_cooldown: int = 0                                  # current cooldown remaining

        # --- Dragon scales (Fafnir): fraction of damage absorbed (0.0-1.0) ---
        self.dragon_scales: float = float(defn.get('dragon_scales', 0))

        # --- Fenrir rage mechanic ---
        self.rage_interval: int = int(defn.get('rage_interval', 0))    # 0 = no rage
        self.rage_damage_bonus: str = defn.get('rage_damage_bonus', '')
        self.rage_stacks: int = 0
        self._rage_turn_counter: int = 0
        self._rage_message: str = ''  # set each turn for caller to read

        # --- Abaddon locust swarm mechanic ---
        self.locust_interval: int = int(defn.get('locust_interval', 0))
        self.locust_count: list = defn.get('locust_count', [0, 0])
        self._locust_turn_counter: int = 0
        self._wants_locust_spawn: bool = False
        self.base_resistances: list = defn.get('base_resistances', [])

        # --- Allied monster (angels) ---
        self.is_allied: bool = defn.get('is_allied', False)
        self.sp_drain: int = int(defn.get('sp_drain', 0))
        self.is_seal_demon: bool = defn.get('is_seal_demon', False)
        self._annihilate_target = None  # set by seek_locust AI

        # --- Piercing ranged state (set by _ranged_turn for caller to process) ---
        self._piercing_collateral: list = []   # monsters in projectile path
        self._force_piercing: bool = False      # next attack must use piercing

    # Backward compat: old pickled monsters may lack newer attributes
    _DEFAULTS = {
        '_flee_timer': 0, '_alerted': False, '_aware': False, '_slow_skip': False,
        'speed': 10, 'resistances': [], 'weaknesses': [],
        'treasure': {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
        'lore': '', 'status_effects': {}, 'thac0': 20,
        'harvest_tier': 1, 'harvest_threshold': 2, 'ingredient_id': None,
        'min_level': 1, 'max_level': None,
        'can_phase_walls': False,
        '_hit_run_state': 'hunting', '_hit_run_timer': 0, '_hit_run_attacks': 0,
        'gaze_paralyze': 0, 'gaze_cooldown_max': 4, '_gaze_cooldown': 0,
        'is_boss': False, 'dragon_scales': 0.0,
        'rage_interval': 0, 'rage_damage_bonus': '', 'rage_stacks': 0,
        '_rage_turn_counter': 0, '_rage_message': '',
        'locust_interval': 0, 'locust_count': [0, 0],
        '_locust_turn_counter': 0, '_wants_locust_spawn': False,
        'base_resistances': [],
        'is_allied': False, 'sp_drain': 0, 'is_seal_demon': False,
        '_annihilate_target': None,
    }

    def __getattr__(self, name):
        if name in Monster._DEFAULTS:
            return Monster._DEFAULTS[name]
        raise AttributeError(f"'Monster' object has no attribute {name!r}")

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
            # Floating eye: gaze-based paralysis (checks sleep_resist or total blindness)
            if player.get_sight_radius() == 0:
                return 0, f"The {self.name} gazes at you, but you cannot see its eyes!"
            if not player.has_effect('sleep_resist'):
                turns = max(player.status_effects.get('paralyzed', 0), 3)
                player.add_effect('paralyzed', turns)
                return 0, f"The {self.name}'s gaze paralyzes you for {turns} turns!"
            else:
                return 0, f"The {self.name} gazes at you harmlessly."

        # --- Gaze attack (Medusa): petrifying gaze before normal attack ---
        if self.gaze_paralyze > 0 and self._gaze_cooldown <= 0:
            self._gaze_cooldown = self.gaze_cooldown_max
            # Check player's sight: total blindness negates gaze
            if player.get_sight_radius() == 0:
                gaze_msg = f"The {self.name} locks eyes on you, but you are blind to her gaze!"
            # Check mirror shield (Aegis): reflects gaze back
            elif getattr(player.shield, 'id', '') in ('aegis_of_athena', 'greater_aegis_of_athena'):
                self.status_effects['paralyzed'] = 1
                gaze_msg = (f"The {self.name} meets her own reflection in your shield "
                            f"and is turned to stone for a moment!")
            else:
                player.add_effect('paralyzed', self.gaze_paralyze)
                gaze_msg = (f"The {self.name}'s terrible gaze freezes you in place! "
                            f"Paralyzed for {self.gaze_paralyze} turns!")
                return 0, gaze_msg  # gaze turn: no damage, just paralyze
            # Gaze was blocked or reflected — continue to normal attack
            # (but append the gaze message below)
            atk = random.choice(self.attacks)
            # Fall through to normal damage with gaze_msg prepended
            d20 = random.randint(1, 20)
            player_ac = player.get_ac()
            to_hit = self.thac0 - player_ac
            is_boss = getattr(self, 'is_boss', False)
            min_hit = getattr(self, 'min_hit_chance', 0.25 if is_boss else 0.05)
            if d20 == 1:
                return 0, gaze_msg + f" The {self.name} swings but misses!"
            if d20 != 20 and d20 < to_hit:
                if random.random() >= min_hit:
                    return 0, gaze_msg + f" The {self.name} swings but misses!"
            dmg = roll(atk['damage'])
            atk_type = atk.get('type', 'physical')
            if self.has_effect('weakened'):
                dmg = max(1, dmg // 2)
            actual = player.take_damage(dmg, atk_type)
            return actual, gaze_msg + f" The {self.name} hits you with {atk['name'].replace('_', ' ')} for {actual} damage!"

        # Fenrir rage: at 3+ stacks, use ALL attacks instead of random choice
        if self.rage_stacks >= 3 and len(self.attacks) > 1:
            return self._fenrir_multi_attack(player)

        # Ranged monsters at distance: prefer ranged attacks over melee
        _RANGED_WORDS = {'shoot', 'arrow', 'bolt', 'dart', 'spit', 'hurl',
                         'volley', 'ray', 'blast', 'breath', 'spike', 'gaze',
                         'song', 'wail', 'charm', 'psionic', 'disintegrat'}
        if not self.attacks:
            return 0, f"The {self.name} flails helplessly!"
        if getattr(self, '_force_piercing', False):
            # Piercing turn: must use a piercing ranged attack
            self._force_piercing = False
            piercing_atks = [a for a in self.attacks
                             if a.get('piercing') and any(w in a.get('name', '').lower() for w in _RANGED_WORDS)]
            atk = random.choice(piercing_atks) if piercing_atks else random.choice(self.attacks)
        elif self.ai_pattern == 'ranged' and not self._adjacent_to(player) and len(self.attacks) > 1:
            ranged_atks = [a for a in self.attacks
                          if any(w in a.get('name', '').lower() for w in _RANGED_WORDS)]
            atk = random.choice(ranged_atks) if ranged_atks else random.choice(self.attacks)
        else:
            atk = random.choice(self.attacks)
        atk_name = atk.get('name', 'attack').lower()
        atk_type = atk.get('type', 'physical')

        # Gaze attacks: blocked by blindness (player can't see the gaze)
        is_gaze = 'gaze' in atk_name or 'evil eye' in atk_name
        if is_gaze and player.get_sight_radius() == 0:
            return 0, f"The {self.name} tries to lock eyes with you, but you cannot see!"

        # Breath/spit/hurl attacks miss player hiding in a pit
        is_breath = any(w in atk_name for w in ('breath', 'spit', 'hurl', 'volley'))
        if is_breath and player.has_effect('in_pit'):
            return 0, f"The {self.name}'s {atk['name'].replace('_', ' ')} passes harmlessly over your pit!"

        # -- THAC0 Attack Roll ----------------------------------------------
        d20 = random.randint(1, 20)
        player_ac = player.get_ac()
        to_hit = self.thac0 - player_ac   # roll must be >= this to hit

        # Minimum hit chance: intrinsic to the monster (bosses 25%, regular 5%)
        is_boss = getattr(self, 'is_boss', False)
        min_hit = getattr(self, 'min_hit_chance', 0.25 if is_boss else 0.05)

        # Natural 1 always misses; natural 20 always hits
        if d20 == 1:
            return 0, f"The {self.name} swings at you and misses!"
        if d20 != 20 and d20 < to_hit:
            # Depth minimum hit: even if THAC0 says miss, deep monsters can still connect
            if random.random() < min_hit:
                pass  # hit anyway — fall through to damage
            else:
                return 0, f"The {self.name} swings at you and misses! (AC {player_ac} deflects)"

        # Confused: 30% chance to swing at nothing
        if self.has_effect('confused') and random.random() < 0.30:
            return 0, f"The {self.name} swings wildly in confusion and misses!"

        # Blinded: 40% chance to miss (can't see target)
        if self.has_effect('blinded') and random.random() < 0.40:
            return 0, f"The {self.name} flails blindly and misses!"

        # Displacement: 30% miss chance even on successful attack roll
        if player.has_effect('displacement') and random.random() < 0.30:
            return 0, f"The {self.name} strikes at your displaced image and misses!"

        # -- Hit: roll damage -----------------------------------------------
        dmg = roll(atk['damage'])
        atk_type = atk.get('type', 'physical')

        # Rage damage bonus (Fenrir)
        if self.rage_stacks > 0 and self.rage_damage_bonus:
            for _ in range(self.rage_stacks):
                dmg += roll(self.rage_damage_bonus)

        # Weakened: this monster's attack deals half damage
        if self.has_effect('weakened'):
            dmg = max(1, dmg // 2)

        actual = player.take_damage(dmg, atk_type)

        msg = f"The {self.name} hits you with {atk['name'].replace('_', ' ')} for {actual} damage!"

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
                    msg += f" The effect reflects back -- the {self.name} is {effect_id.replace('_', ' ')}!"
                else:
                    applied = player.add_effect(effect_id, duration)
                    if applied:
                        msg += f" You are {effect_id.replace('_', ' ')}!"

        return actual, msg

    # --- AI ---

    def take_turn(self, player, dungeon, all_monsters, extra_occupied=None) -> bool:
        """Execute this monster's turn. Returns True if it attacked the player.
        extra_occupied: optional set of (x,y) positions to avoid (e.g. pet tiles)."""
        if not self.alive:
            return False

        self.tick_effects()

        # Immobilised by sleep or paralysis
        if self.has_effect('sleeping') or self.has_effect('paralyzed'):
            return False

        # Stuck in a pit: can attack if adjacent, but cannot move
        if self.has_effect('stuck_in_pit'):
            if self._adjacent_to(player):
                return True  # attack from the pit
            return False  # can't move, can't reach

        # --- Variable speed: slow monsters skip turns ---
        if self.speed < 8 and self.speed > 0:
            # speed 6 => skip 40% of turns, speed 4 => skip 60%, etc.
            if random.random() < (8 - self.speed) / 10.0:
                return False

        # Slowed: skip every other turn
        if self.has_effect('slowed'):
            self._slow_skip = not self._slow_skip
            if self._slow_skip:
                return False

        # --- Flee when hurt (non-boss aggressive monsters) ---
        is_boss = self.max_hp > 500
        if not is_boss and self.ai_pattern == 'aggressive':
            if self._flee_timer > 0:
                self._flee_timer -= 1
                # Regain courage if healed above 50%
                if self.hp > self.max_hp * 0.5:
                    self._flee_timer = 0
            elif self.hp < self.max_hp * 0.25 and self.hp > 0:
                self._flee_timer = 8

        # --- Hit-and-run AI (Asterion): attack then vanish through walls ---
        if self.ai_pattern == 'hit_and_run':
            return self._hit_and_run_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Dancer AI (Medusa): sidestep then strike ---
        if self.ai_pattern == 'dancer':
            return self._dancer_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Fenrir rage AI: aggressive + escalating rage ---
        if self.ai_pattern == 'fenrir_rage':
            return self._fenrir_rage_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Abaddon AI: aggressive + locust swarm spawning ---
        if self.ai_pattern == 'abaddon':
            return self._abaddon_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Seek-locust AI (angels): move toward nearest locust ---
        if self.ai_pattern == 'seek_locust':
            return self._seek_locust_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Ranged AI: shoot from distance, maintain range ---
        if self.ai_pattern == 'ranged':
            dist_r = abs(self.x - player.x) + abs(self.y - player.y)
            if dist_r <= 8 or player.has_effect('aggravated'):
                self._aware = True
            if not getattr(self, '_aware', False) and not self._alerted:
                self._wander(dungeon, all_monsters, extra_occupied, player)
                return False
            return self._ranged_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Ambush AI: stay still until player is within 5 tiles ---
        if self.ai_pattern == 'ambush':
            dist = abs(self.x - player.x) + abs(self.y - player.y)
            if dist > 5:
                return False  # lurk silently
            # Player spotted -- switch to aggressive permanently
            self.ai_pattern = 'aggressive'

        # --- Detection range: monsters only hunt within 8 tiles ---
        # Once a monster spots the player, it stays aware permanently.
        # Aggravated status makes ALL monsters aware immediately.
        dist_to_player = abs(self.x - player.x) + abs(self.y - player.y)
        detection_range = 8
        if dist_to_player <= detection_range or player.has_effect('aggravated'):
            self._aware = True
        if not getattr(self, '_aware', False) and not self._alerted:
            # Beyond detection range and never spotted the player.
            # Behavior depends on base AI: sessile/ambush wait, others wander.
            if self.ai_pattern not in ('sessile', 'ambush', 'cowardly'):
                self._wander(dungeon, all_monsters, extra_occupied, player)
            return False

        # --- Call for help: alert same-kind allies within 5 tiles ---
        if self._adjacent_to(player):
            self.alert_nearby(all_monsters)

        # Aggravated overrides passive/cowardly AI patterns
        effective_pattern = self.ai_pattern
        if player.has_effect('aggravated') and effective_pattern in ('sessile', 'cowardly'):
            effective_pattern = 'aggressive'

        # Alerted monsters act aggressive
        if self._alerted and effective_pattern in ('sessile', 'cowardly'):
            effective_pattern = 'aggressive'

        # Flee when hurt overrides to cowardly
        if self._flee_timer > 0 and effective_pattern == 'aggressive':
            effective_pattern = 'cowardly'

        if effective_pattern == 'sessile':
            return False

        # Confused monsters: 40% chance to stumble randomly instead of acting
        if self.has_effect('confused') and random.random() < 0.40:
            self._stumble_random(dungeon, all_monsters, extra_occupied, player)
            return False

        # Blinded monsters: 30% chance to stumble, and miss more in combat
        if self.has_effect('blinded') and random.random() < 0.30:
            self._stumble_random(dungeon, all_monsters, extra_occupied, player)
            return False

        # Feared monsters: flee from player instead of attacking
        if self.has_effect('feared'):
            self._flee_from(player, dungeon, all_monsters, extra_occupied)
            return False

        if self._adjacent_to(player):
            return True  # caller triggers the attack

        # --- Standard movement ---
        if self._standard_move(player, dungeon, all_monsters, extra_occupied, effective_pattern):
            return True  # reached player during double-move

        return False

    def _standard_move(self, player, dungeon, all_monsters, extra_occupied, effective_pattern):
        """Standard movement logic used by aggressive/cowardly AI."""
        move_steps = 2 if self.speed >= 14 else 1

        dx, dy = self._preferred_dir(player, effective_pattern)
        candidates = self._move_candidates(dx, dy)

        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        if extra_occupied:
            occupied |= extra_occupied
        player_pos = (player.x, player.y)

        for _step in range(move_steps):
            moved = False
            for ddx, ddy in candidates:
                nx, ny = self.x + ddx, self.y + ddy
                if (nx, ny) in occupied or (nx, ny) == player_pos:
                    continue
                tile = dungeon.tiles[ny][nx] if dungeon.in_bounds(nx, ny) else 0
                from dungeon import DOOR
                if tile == DOOR:
                    dungeon.open_door(nx, ny)   # monsters open doors
                    self.x, self.y = nx, ny
                    moved = True
                    break
                if self._can_move_to(dungeon, nx, ny):
                    self.x, self.y = nx, ny
                    moved = True
                    break
            if not moved:
                break
            # After first step of a double-move, check adjacency again
            if _step == 0 and move_steps > 1 and self._adjacent_to(player):
                return True
            # Recalculate direction for second step
            if _step == 0 and move_steps > 1:
                dx, dy = self._preferred_dir(player, effective_pattern)
                candidates = self._move_candidates(dx, dy)
                occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
                if extra_occupied:
                    occupied |= extra_occupied

        return False

    def _wander(self, dungeon, all_monsters, extra_occupied, player):
        """Random wandering when the monster hasn't detected the player."""
        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        if extra_occupied:
            occupied |= extra_occupied
        occupied.add((player.x, player.y))
        dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        random.shuffle(dirs)
        for ddx, ddy in dirs:
            nx, ny = self.x + ddx, self.y + ddy
            if (nx, ny) not in occupied and self._can_move_to(dungeon, nx, ny):
                self.x, self.y = nx, ny
                return

    def alert_nearby(self, all_monsters):
        """Wake up same-kind monsters within 5 tiles (call for help)."""
        for m in all_monsters:
            if m is self or not m.alive or m._alerted:
                continue
            if m.kind != self.kind:
                continue
            dist = abs(m.x - self.x) + abs(m.y - self.y)
            if dist <= 5:
                m._alerted = True
                m._aware = True
                # Wake sleeping allies
                m.status_effects.pop('sleeping', None)

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

    def _can_move_to(self, dungeon, nx: int, ny: int) -> bool:
        """Check if this monster can move to (nx, ny), including wall-phasing."""
        if not dungeon.in_bounds(nx, ny):
            return False
        if dungeon.is_walkable(nx, ny):
            return True
        # Wall-phasing: Asterion can move through phasing walls
        if self.can_phase_walls:
            from dungeon import WALL
            phasing = getattr(dungeon, 'phasing_walls', set())
            if dungeon.tiles[ny][nx] == WALL and (nx, ny) in phasing:
                return True
        return False

    def _stumble_random(self, dungeon, all_monsters, extra_occupied, player):
        """Move in a random direction (confused/blinded stumble)."""
        dirs = [(0,-1),(0,1),(-1,0),(1,0)]
        random.shuffle(dirs)
        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        if extra_occupied:
            occupied |= extra_occupied
        for ddx, ddy in dirs:
            nx, ny = self.x + ddx, self.y + ddy
            if ((nx, ny) not in occupied and (nx, ny) != (player.x, player.y)
                    and self._can_move_to(dungeon, nx, ny)):
                self.x, self.y = nx, ny
                return

    def _flee_from(self, player, dungeon, all_monsters, extra_occupied):
        """Move away from player (feared)."""
        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        if extra_occupied:
            occupied |= extra_occupied
        away_dx = 0 if self.x == player.x else (1 if self.x > player.x else -1)
        away_dy = 0 if self.y == player.y else (1 if self.y > player.y else -1)
        for ddx, ddy in [(away_dx, away_dy), (away_dx, 0), (0, away_dy),
                         (-away_dy, away_dx), (away_dy, -away_dx)]:
            if ddx == 0 and ddy == 0:
                continue
            nx, ny = self.x + ddx, self.y + ddy
            if ((nx, ny) not in occupied and (nx, ny) != (player.x, player.y)
                    and self._can_move_to(dungeon, nx, ny)):
                self.x, self.y = nx, ny
                return

    # --- Ranged AI -----------------------------------------------------------
    _RANGED_MAX = 6   # max shooting range (tiles)
    _RANGED_IDEAL = 4  # preferred distance to maintain

    def _has_los(self, px, py, dungeon) -> bool:
        return _line_of_sight(self.x, self.y, px, py, dungeon)

    def _has_clear_shot(self, px, py, dungeon, all_monsters) -> bool:
        """True if LOS is clear of walls AND no allied monster blocks the path."""
        if not _line_of_sight(self.x, self.y, px, py, dungeon):
            return False
        # Bresenham walk to check for monsters in the way
        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        dx, dy = abs(px - self.x), abs(py - self.y)
        sx = 1 if px > self.x else -1
        sy = 1 if py > self.y else -1
        err = dx - dy
        cx, cy = self.x, self.y
        while True:
            if cx == px and cy == py:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy
            if (cx, cy) != (px, py) and (cx, cy) in occupied:
                return False
        return True

    def _monsters_in_path(self, px, py, all_monsters) -> list:
        """Return monsters standing on tiles between self and (px, py)."""
        occupied = {}
        for m in all_monsters:
            if m is not self and m.alive:
                occupied[(m.x, m.y)] = m
        result = []
        dx, dy = abs(px - self.x), abs(py - self.y)
        sx = 1 if px > self.x else -1
        sy = 1 if py > self.y else -1
        err = dx - dy
        cx, cy = self.x, self.y
        while True:
            if cx == px and cy == py:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy
            if (cx, cy) != (px, py) and (cx, cy) in occupied:
                result.append(occupied[(cx, cy)])
        return result

    def _has_piercing_ranged(self) -> bool:
        """True if this monster has at least one piercing ranged attack."""
        _RANGED_WORDS = {'shoot', 'arrow', 'bolt', 'dart', 'spit', 'hurl',
                         'volley', 'ray', 'blast', 'breath', 'spike', 'gaze',
                         'song', 'wail', 'charm', 'psionic', 'disintegrat'}
        for a in self.attacks:
            if a.get('piercing') and any(w in a.get('name', '').lower() for w in _RANGED_WORDS):
                return True
        return False

    def _ranged_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Ranged AI: shoot when player is in LOS within range.
        If too close, try to back away. If too far or no LOS, approach."""
        self._piercing_collateral = []  # reset each turn
        dist = max(abs(self.x - player.x), abs(self.y - player.y))  # Chebyshev
        has_los = self._has_los(player.x, player.y, dungeon)

        # In range with LOS — check for clear shot or piercing override
        if has_los and 2 <= dist <= self._RANGED_MAX:
            if self._has_clear_shot(player.x, player.y, dungeon, all_monsters):
                return True
            # Shot blocked by ally — piercing monsters fire anyway
            if self._has_piercing_ranged():
                self._piercing_collateral = self._monsters_in_path(
                    player.x, player.y, all_monsters)
                self._force_piercing = True
                return True
            # No piercing — try to reposition
            has_los = False  # fall through to approach/reposition

        # Adjacent — still attack (melee fallback) but try to retreat next turn
        if self._adjacent_to(player):
            return True

        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        if extra_occupied:
            occupied |= extra_occupied
        player_pos = (player.x, player.y)

        # Too close (dist 1 and not adjacent shouldn't happen, but dist < 2 with LOS):
        # try to back away from the player
        if has_los and dist < 2:
            away_dx = 0 if self.x == player.x else (1 if self.x > player.x else -1)
            away_dy = 0 if self.y == player.y else (1 if self.y > player.y else -1)
            for ddx, ddy in [(away_dx, away_dy), (away_dx, 0), (0, away_dy),
                             (-away_dx, away_dy), (away_dx, -away_dy)]:
                nx, ny = self.x + ddx, self.y + ddy
                if (ddx == 0 and ddy == 0):
                    continue
                if (nx, ny) not in occupied and (nx, ny) != player_pos and self._can_move_to(dungeon, nx, ny):
                    self.x, self.y = nx, ny
                    # After retreating, check if we can now shoot
                    new_dist = max(abs(self.x - player.x), abs(self.y - player.y))
                    if new_dist >= 2 and self._has_clear_shot(player.x, player.y, dungeon, all_monsters):
                        return True  # retreat + shoot
                    return False
            # Can't retreat — fight in melee
            return True if self._adjacent_to(player) else False

        # Out of range or no LOS — approach (same as aggressive)
        if self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive'):
            return True
        return False

    def _hit_and_run_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Hit-and-run AI for Asterion: hunt, strike, vanish through walls, repeat.

        States:
          hunting   - move toward player aggressively (through phasing walls)
          retreating - flee through phasing walls after attacking (3 turns)
          hiding    - wait hidden in the walls (4-6 turns), then hunt again
        """
        self._hit_run_timer -= 1

        if self._hit_run_state == 'retreating':
            if self._hit_run_timer <= 0:
                self._hit_run_state = 'hiding'
                self._hit_run_timer = random.randint(4, 6)
            # Move away from player, prefer phasing walls for escape
            self._phase_move(player, dungeon, all_monsters, extra_occupied, away=True)
            return False

        if self._hit_run_state == 'hiding':
            if self._hit_run_timer <= 0:
                self._hit_run_state = 'hunting'
                self._hit_run_attacks = 0
            return False  # lurking in the walls

        # --- hunting state ---
        if self._adjacent_to(player):
            self._hit_run_attacks += 1
            # After 1-2 attacks, retreat through walls
            if self._hit_run_attacks >= random.randint(1, 2):
                self._hit_run_state = 'retreating'
                self._hit_run_timer = 3
            return True  # signal attack

        # Move toward player (can phase through walls)
        self._phase_move(player, dungeon, all_monsters, extra_occupied, away=False)

        # Check if we reached adjacency after moving
        if self._adjacent_to(player):
            return True

        return False

    def _phase_move(self, player, dungeon, all_monsters, extra_occupied, away: bool):
        """Move through the labyrinth, phasing through walls if possible."""
        if away:
            dx = 0 if self.x == player.x else (-1 if player.x > self.x else 1)
            dy = 0 if self.y == player.y else (-1 if player.y > self.y else 1)
        else:
            dx = 0 if self.x == player.x else (1 if player.x > self.x else -1)
            dy = 0 if self.y == player.y else (1 if player.y > self.y else -1)

        candidates = self._move_candidates(dx, dy)
        # When retreating, also try random directions to find phasing walls
        if away:
            all_dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            random.shuffle(all_dirs)
            for d in all_dirs:
                if d not in candidates:
                    candidates.append(d)

        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        if extra_occupied:
            occupied |= extra_occupied
        player_pos = (player.x, player.y)

        for ddx, ddy in candidates:
            nx, ny = self.x + ddx, self.y + ddy
            if (nx, ny) in occupied or (nx, ny) == player_pos:
                continue
            if self._can_move_to(dungeon, nx, ny):
                self.x, self.y = nx, ny
                return True
        return False


    def _fenrir_rage_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Fenrir rage AI: aggressive movement + escalating rage stacks.
        Every rage_interval turns, gains a rage stack with increasing damage/speed."""
        self._rage_message = ''
        self._rage_turn_counter += 1

        if self.rage_interval > 0 and self._rage_turn_counter % self.rage_interval == 0:
            self.rage_stacks += 1
            _RAGE_MSGS = [
                "Fenrir snarls and grows larger!",
                "Fenrir's hackles rise -- frost crackles around his jaws!",
                "Fenrir HOWLS! The ground shakes!",
                "Fenrir is consumed by Ragnarok fury! His form fills the chamber!",
                "The World-Wolf's shadow swallows the light! Ragnarok is upon you!",
            ]
            idx = min(self.rage_stacks - 1, len(_RAGE_MSGS) - 1)
            self._rage_message = _RAGE_MSGS[idx]

        if self._adjacent_to(player):
            self.alert_nearby(all_monsters)
            return True

        # At high rage (3+), Fenrir gets double movement speed
        effective_pattern = 'aggressive'
        old_speed = self.speed
        if self.rage_stacks >= 3:
            self.speed = max(self.speed, 14)  # ensures double-move
        result = self._standard_move(player, dungeon, all_monsters, extra_occupied, effective_pattern)
        self.speed = old_speed
        return result

    def reset_rage(self):
        """Reset Fenrir's rage (called by Gleipnir binding)."""
        self.rage_stacks = 0
        self._rage_turn_counter = 0

    def _abaddon_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Abaddon AI: aggressive movement + periodic locust swarm spawning.
        Sets _wants_locust_spawn flag for main.py to handle actual spawning."""
        self._wants_locust_spawn = False
        self._locust_turn_counter += 1

        if self.locust_interval > 0 and self._locust_turn_counter % self.locust_interval == 0:
            self._wants_locust_spawn = True

        if self._adjacent_to(player):
            self.alert_nearby(all_monsters)
            return True

        return self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive')

    def _seek_locust_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Angel AI: move toward nearest locust. Sets _annihilate_target if adjacent."""
        self._annihilate_target = None

        # Find nearest locust
        locusts = [m for m in all_monsters if m.alive and m.kind == 'abyssal_locust']
        if not locusts:
            return False  # nothing to seek

        # Check if already adjacent to a locust
        for loc in locusts:
            if abs(self.x - loc.x) <= 1 and abs(self.y - loc.y) <= 1:
                self._annihilate_target = loc
                return False  # no attack on player

        # Move toward nearest locust
        nearest = min(locusts, key=lambda l: abs(l.x - self.x) + abs(l.y - self.y))
        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        if extra_occupied:
            occupied |= extra_occupied
        occupied.add((player.x, player.y))

        dx = 1 if nearest.x > self.x else (-1 if nearest.x < self.x else 0)
        dy = 1 if nearest.y > self.y else (-1 if nearest.y < self.y else 0)
        candidates = self._move_candidates(dx, dy)

        for ddx, ddy in candidates:
            nx, ny = self.x + ddx, self.y + ddy
            if (nx, ny) in occupied:
                continue
            if dungeon.in_bounds(nx, ny) and self._can_move_to(dungeon, nx, ny):
                self.x, self.y = nx, ny
                # Check if now adjacent to a locust
                for loc in locusts:
                    if abs(self.x - loc.x) <= 1 and abs(self.y - loc.y) <= 1:
                        self._annihilate_target = loc
                break

        return False  # angels never attack the player

    def _fenrir_multi_attack(self, player) -> tuple[int, str]:
        """Fenrir at 3+ rage: use ALL attacks in one turn. Returns (total_dmg, combined_msg)."""
        total = 0
        parts = []
        is_boss = getattr(self, 'is_boss', False)
        min_hit = getattr(self, 'min_hit_chance', 0.25 if is_boss else 0.05)
        for atk in self.attacks:
            d20 = random.randint(1, 20)
            player_ac = player.get_ac()
            to_hit = self.thac0 - player_ac
            if d20 == 1:
                parts.append("miss")
                continue
            if d20 != 20 and d20 < to_hit:
                if random.random() >= min_hit:
                    parts.append("miss")
                    continue
            dmg = roll(atk['damage'])
            if self.rage_stacks > 0 and self.rage_damage_bonus:
                for _ in range(self.rage_stacks):
                    dmg += roll(self.rage_damage_bonus)
            if self.has_effect('weakened'):
                dmg = max(1, dmg // 2)
            actual = player.take_damage(dmg, atk.get('type', 'physical'))
            total += actual
            parts.append(f"{atk['name'].replace('_', ' ')} {actual}")
        hit_str = ", ".join(parts)
        msg = f"The {self.name} attacks in a frenzy! [{hit_str}] ({total} total)"
        return total, msg

    def _dancer_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Dancer AI (Medusa): sidestep to a new position adjacent to player, then attack.
        If not adjacent, approach normally. The constant repositioning makes her
        hard to pin down unless the player uses chokepoints."""
        # Tick gaze cooldown
        if self._gaze_cooldown > 0:
            self._gaze_cooldown -= 1

        px, py = player.x, player.y
        if not self._adjacent_to(player):
            self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive')
            return False

        # Adjacent: reposition to a different adjacent-to-player tile, then attack
        occupied = {(m.x, m.y) for m in all_monsters if m is not self and m.alive}
        if extra_occupied:
            occupied |= extra_occupied
        occupied.add((px, py))

        candidates = []
        for ddx in [-1, 0, 1]:
            for ddy in [-1, 0, 1]:
                if ddx == 0 and ddy == 0:
                    continue
                nx, ny = px + ddx, py + ddy
                if (nx, ny) == (self.x, self.y):
                    continue
                if (nx, ny) not in occupied and dungeon.is_walkable(nx, ny):
                    candidates.append((nx, ny))

        if candidates:
            self.x, self.y = random.choice(candidates)

        return True  # signal attack


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
        'speed': 10,
        'hp': '1',          # irrelevant -- take_damage is overridden
        'attacks': [{'name': 'reap', 'damage': '2d12+15', 'type': 'physical'}],
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

    def take_turn(self, player, dungeon, all_monsters, extra_occupied=None) -> bool:
        """Half-speed: acts on alternating turns only."""
        self._half_speed_skip = not self._half_speed_skip
        if self._half_speed_skip:
            return False
        return super().take_turn(player, dungeon, all_monsters, extra_occupied)

    def attack(self, player) -> tuple[int, str]:
        """Death always hits -- no THAC0 roll needed."""
        dmg = roll(self._DEFN['attacks'][0]['damage'])
        actual = player.take_damage(dmg, 'physical')
        return actual, f"Death's scythe tears through you for {actual} damage!"
