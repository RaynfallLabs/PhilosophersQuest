"""The abandoned Emberpup: every run, earned.

Brandon, 2026-11-12: the one-in-N events happen every run, on a range of
floors, but winning one takes "a pattern of behavior AND the right items
(similar to unicorn)". Then, 2026-11-13 (winning-build plan 3.8 and 3.8b):

  "the reason the pup is in the rain is because he was abandoned, and
   mistreated by his former master... this pup has learned to be wary of
   those stronger than him"

So the pup (he) sits on a rock under a little rain cloud where a hard master
left him, and shies from anyone bigger than he is. Trust is earned the way
a beaten animal's is:

  * Leave him food THREE times (``visits_needed``), and let him eat in peace
    between: feeds at least ``feed_gap_turns`` apart. Leaving his floor
    counts as waiting. Come back too soon and he is still eating and pays
    you no attention (``too_soon``): that try does not count and costs
    nothing. Each feed has its own line, each a little warmer (``fed``):
    flinching, then watching, then lingering, then coming close. The
    choices screen says where he is now (``waiting``).
  * Keep the rain off him. Only one thing will: the Bloomleaf Cloak, broad
    leaves a Bloomsaur grew, that rain runs off. Old Nickel the kobold wears
    it (BloomleafMixin, below), on a floor at or above the pup's. Any other cloak
    or shield no longer does ("A cloak of leaves would turn this rain").
    Left over his rock, the cloak is his.
  * Only then will "I choose you!" be heard: the animal quiz, tier 2, two
    right answers. Pass, and he joins you, still wearing the cloak: this
    Emberpup wears it at every stage of his line (pet_system ``bloomleaf``:
    his own cloaked sprites, and no weakness to water for him).
    Fail, and he shies away but stays; feed him again and try again.

The other choices: leave him be (come back any time), or attack him (he
flees into the dark, gone for the run; karma drops). Feeding a starving pup
is kindness, not a weighed deed: with the karma gate on (the game's default)
it moves no karma; the deeds register still notes it. With the gate off,
the first feed pays first_feed_karma.

Run state lives in ``game._emberpup`` (saved): the floor he waits on (None
in a run without him), whether he has been placed, how it ended ('fled' or
'adopted'), the turn of the last feed and whether the hero has been away
since, and Old Nickel's floor ('cloak_floor', 'cloak_seed', 'cloak_spawned').
His own state (story told, feeds, fed since the last try, the cloak) lives
on the creature, which is saved with the floor. All text and numbers are in
data/abandoned_emberpup.json.
"""
from __future__ import annotations

import json
import random

from game_states import STATE_PLAYER, STATE_QUIZ, STATE_EMBERPUP, STATE_PET_NAME_INPUT

_DATA: dict | None = None


def data() -> dict:
    global _DATA
    if _DATA is None:
        from paths import data_path
        with open(data_path('data', 'abandoned_emberpup.json'), encoding='utf-8') as f:
            _DATA = json.load(f)
    return _DATA


def roll_floor(rng) -> int | None:
    """The floor this run's Emberpup waits on, or None (no run, with the data
    as it ships: chance_per_run is 1.0)."""
    d = data()
    if rng.random() >= float(d['chance_per_run']):
        return None
    return rng.randint(int(d['first_floor']), int(d['last_floor']))


def _run_rng() -> random.Random:
    """The run's own generator for the pup and the cloak, seeded from the
    shared stream without moving it, so seeded floors and captures are as
    they were before either existed."""
    saved = random.getstate()
    try:
        seed = random.getrandbits(64)
    finally:
        random.setstate(saved)
    return random.Random(seed ^ 0x0E3BE6)


def roll_for_new_run() -> int | None:
    """roll_floor for a new run, from the run's own generator."""
    return roll_floor(_run_rng())


def new_run_state(exclude=()) -> dict:
    """A new run's pup and cloak. `exclude`: floors a planned mini-boss
    holds, which Old Nickel keeps off where he can (draw_floor)."""
    rng = _run_rng()
    floor = roll_floor(rng)
    return {'floor': floor, 'spawned': False, 'outcome': None,
            'cloak_floor': draw_floor(rng, floor, exclude),
            'cloak_seed': rng.getrandbits(32), 'cloak_spawned': False}


def is_emberpup(thing) -> bool:
    return bool(getattr(thing, '_is_abandoned_emberpup', False))


def food_choices(inventory) -> list:
    """What the player could feed him: identified food and ordinary raw cuts
    (never a trophy)."""
    from items import Food, Ingredient
    return [i for i in inventory
            if isinstance(i, (Food, Ingredient))
            and getattr(i, 'identified', True)
            and getattr(i, 'tier_role', '') != 'trophy']


def _is_leaf_cloak(it) -> bool:
    return is_cloak(it)


def _is_other_cover(it) -> bool:
    """A cloak or a shield that is not the leaf cloak: it no longer turns
    his rain (winning-build plan 3.8)."""
    from items import Armor, Shield
    if it is None or _is_leaf_cloak(it):
        return False
    return isinstance(it, Shield) or (isinstance(it, Armor) and getattr(it, 'slot', '') == 'cloak')


def shelter_choices(player) -> list:
    """What would keep the rain off him: the Bloomleaf Cloak in the pack
    (a worn one has to come off first)."""
    return [it for it in player.inventory if _is_leaf_cloak(it)]


def _worn(player) -> list:
    return [getattr(player, 'shield', None)] + list(getattr(player, 'armor_slots', None) or ())


def wears_cover(player) -> bool:
    """Is the Bloomleaf Cloak on the hero's own back?"""
    return any(it is not None and _is_leaf_cloak(it) for it in _worn(player))


def other_cover(player):
    """A cloak or shield the hero has that would NOT do, or None."""
    for it in list(player.inventory) + _worn(player):
        if _is_other_cover(it):
            return it
    return None


def feeds(pup) -> int:
    """How many times he has been fed, on the way to trusting the hero.
    (A pup saved before feeds were counted kept 'visits'.)"""
    n = getattr(pup, '_emberpup_feeds', None)
    if n is None:
        n = getattr(pup, '_emberpup_visits', 0)
    return int(n or 0)


def needed() -> int:
    return int(data().get('visits_needed', 3))


def stage(pup) -> int:
    """0 never fed; 1 and 2 on the way; 3 (needed) he trusts you."""
    return min(feeds(pup), needed())


def waiting_text(pup) -> str:
    """The choices screen's words: where his trust stands, and the cloak."""
    d = data()
    lines = d.get('waiting') or ['']
    text = lines[min(stage(pup), len(lines) - 1)]
    if getattr(pup, '_emberpup_sheltered', False) and d.get('waiting_sheltered'):
        text = f"{text} {d['waiting_sheltered']}"
    return text


def sprite_of(pup) -> str:
    """His picture: on his rock in the rain, or with the leaf cloak over him."""
    d = data()
    if pup is not None and getattr(pup, '_emberpup_sheltered', False):
        return d.get('sprite_sheltered') or d['sprite_id']
    return d['sprite_id']


FOOD_PAGE = 9


class EmberpupMixin:
    """Spawn, screen state and outcomes. Drawing is game_render
    ``_draw_emberpup_encounter``; keys come through ``_emberpup_input``."""

    # ---- spawn ------------------------------------------------------------

    def _emberpup_state(self) -> dict:
        st = getattr(self, '_emberpup', None)
        if not isinstance(st, dict):
            st = {'floor': None, 'spawned': False, 'outcome': None}
            self._emberpup = st
        return st

    def _emberpup_left(self, from_level: int, to_level: int | None = None):
        """The hero leaves a floor: leaving the pup's floor after a feed is
        waiting, as good as the turns (Game._change_level)."""
        st = self._emberpup_state()
        if st.get('fed_once') and from_level == st.get('floor') and to_level != from_level:
            st['away'] = True

    def _maybe_spawn_emberpup(self, level: int):
        """Place the Emberpup on his floor, once per run, on first arrival."""
        st = self._emberpup_state()
        # Being on another floor after feeding him is waiting.
        if st.get('fed_once') and level != st.get('floor'):
            st['away'] = True
        if st.get('spawned') or st.get('outcome') or st.get('floor') != level:
            return
        if any(is_emberpup(m) for m in self.monsters):
            return
        from monster import Monster
        from geom import all_occupied_tiles
        d = data()
        defn = {
            'id': d['sprite_id'], 'name': d['name'], 'symbol': 'e',
            'color': [255, 80, 40], 'hp': 1, 'thac0': 20, 'speed': 0,
            'attacks': [], 'ai_pattern': 'sessile', 'resistances': [],
            'weaknesses': [], 'min_level': level, 'is_allied': True,
            'harvest_tier': 0, 'harvest_threshold': 99, 'ingredient_id': None,
        }
        occupied = all_occupied_tiles(self.monsters)
        occupied |= self._occupants()     # the hero, pets and escorts
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
        # Never in Old Nickel's room (BloomleafMixin, below).
        taken = [_room_of(self.dungeon.rooms, m.x, m.y)
                 for m in self.monsters if is_wearer(m)]
        rooms = [r for r in rooms if r not in taken] or rooms
        spot = None
        for room in random.sample(rooms, min(len(rooms), 5)):
            tiles = list(room.inner_tiles())
            random.shuffle(tiles)
            spot = next(((x, y) for x, y in tiles
                         if self.dungeon.is_walkable(x, y) and (x, y) not in occupied), None)
            if spot:
                break
        if spot is None:
            spot = self._free_spawn_tile(occupied)
        if spot is None:
            return
        pup = Monster(defn, *spot)
        pup._is_abandoned_emberpup = True
        pup._emberpup_met = False      # his story has been told
        pup._emberpup_fed = False      # fed since the last try: "I choose you" may be asked
        pup._emberpup_feeds = 0        # feeds on the way to trust (visits_needed)
        self.monsters.append(pup)
        st['spawned'] = True

    # ---- the screen -------------------------------------------------------

    def _emberpup_too_soon(self, pup) -> bool:
        """Fed less than feed_gap_turns ago, the hero never away since, and
        trust still building: he is still eating and pays no attention."""
        st = self._emberpup_state()
        if not st.get('fed_once') or st.get('away') or feeds(pup) >= needed():
            return False
        gap = int(data().get('feed_gap_turns', 25))
        return int(getattr(self, 'turn_count', 0)) - int(st.get('fed_turn', 0) or 0) < gap

    def _start_emberpup_encounter(self, pup):
        """Bumping him: his story the first time; his choices after that,
        unless he is still eating his last meal."""
        d = data()
        self._emberpup_npc = pup
        first = not getattr(pup, '_emberpup_met', False)
        self._emberpup_phase = 'story' if first else 'options'
        pup._emberpup_met = True
        self._emberpup_text = ''
        self._emberpup_after = 'options'
        self._emberpup_food = []
        self._emberpup_food_scroll = 0
        self._emberpup_acted = False
        self.state = STATE_EMBERPUP
        if not first and self._emberpup_too_soon(pup):
            # Too soon: no choices, no turn spent. Come back in a while.
            self._emberpup_outcome(d['too_soon'], 'player')

    def _emberpup_outcome(self, text: str, after: str):
        self._emberpup_text = text
        self._emberpup_after = after
        self._emberpup_phase = 'outcome'

    def _close_emberpup(self):
        acted = getattr(self, '_emberpup_acted', False)
        self._emberpup_npc = None
        self._emberpup_phase = 'story'
        self._emberpup_food = []
        self._emberpup_acted = False
        self.state = STATE_PLAYER
        if acted:
            self._advance_turn()

    def _emberpup_input(self, key: int):
        import pygame
        phase = getattr(self, '_emberpup_phase', 'options')
        pup = getattr(self, '_emberpup_npc', None)
        if pup is None:
            self.state = STATE_PLAYER
            return
        if phase == 'story':
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self._emberpup_phase = 'options'
            elif key == pygame.K_ESCAPE:
                self._close_emberpup()
            return
        if phase == 'outcome':
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE, pygame.K_ESCAPE):
                after = self._emberpup_after
                if after == 'options':
                    self._emberpup_phase = 'options'
                elif after == 'name':
                    self._emberpup_open_naming()
                else:
                    self._close_emberpup()
            return
        if phase == 'select_food':
            self._emberpup_food_input(key)
            return
        # options
        if key in (pygame.K_1, pygame.K_KP1):
            self._emberpup_feed_start()
        elif key in (pygame.K_2, pygame.K_KP2):
            self._emberpup_ignore()
        elif key in (pygame.K_3, pygame.K_KP3):
            self._emberpup_attack()
        elif key in (pygame.K_4, pygame.K_KP4):
            self._emberpup_choose()
        elif key in (pygame.K_5, pygame.K_KP5):
            self._emberpup_shelter()
        elif key == pygame.K_ESCAPE:
            self._emberpup_ignore()

    # ---- the five choices ---------------------------------------------------

    def _emberpup_feed_start(self):
        d = data()
        pup = self._emberpup_npc
        if self._emberpup_too_soon(pup):
            self._emberpup_outcome(d['too_soon'], 'options')
            return
        if getattr(pup, '_emberpup_fed', False) and feeds(pup) >= needed():
            self._emberpup_outcome(d['already_fed'], 'options')
            return
        food = food_choices(self.player.inventory)
        if not food:
            self._emberpup_outcome(d['no_food'], 'options')
            return
        self._emberpup_food = food
        self._emberpup_food_scroll = 0
        self._emberpup_phase = 'select_food'

    def _emberpup_food_input(self, key: int):
        import pygame
        food = self._emberpup_food
        if key == pygame.K_ESCAPE:
            self._emberpup_phase = 'options'
            return
        if key == pygame.K_DOWN:
            self._emberpup_food_scroll = min(max(0, len(food) - FOOD_PAGE),
                                             self._emberpup_food_scroll + 1)
            return
        if key == pygame.K_UP:
            self._emberpup_food_scroll = max(0, self._emberpup_food_scroll - 1)
            return
        if pygame.K_a <= key <= pygame.K_z:
            i = self._emberpup_food_scroll + (key - pygame.K_a)
            if key - pygame.K_a < FOOD_PAGE and 0 <= i < len(food):
                self._emberpup_feed(food[i])

    def _emberpup_feed(self, item):
        """He eats one of `item`. While his trust is building, each feed is a
        step (feeds), and each step has its own line."""
        d = data()
        pup = self._emberpup_npc
        if item not in self.player.inventory:
            self._emberpup_phase = 'options'
            return
        name = self._display_name(item)
        self.player.remove_from_inventory(item)
        pup._emberpup_fed = True
        self._emberpup_acted = True
        st = self._emberpup_state()
        before = feeds(pup)
        if before < needed():
            pup._emberpup_feeds = before + 1
        st['fed_once'] = True
        st['fed_turn'] = int(getattr(self, 'turn_count', 0))
        st['away'] = False
        if not getattr(pup, '_emberpup_karma_given', False):
            pup._emberpup_karma_given = True
            import karma
            # Feeding a starving pup is kindness, not a weighed deed: with
            # the karma gate on it moves nothing (DEEDS_KARMA_DESIGN 3.1;
            # Brandon, decision 9). Off, it pays as it always did.
            if not karma.gate_enabled():
                karma.adjust(self, int(d['first_feed_karma']), kind='legacy',
                             source='emberpup_feed')
            import deeds
            deeds.note(self, 'aid.emberpup', source='emberpup', unique=True)
        self.add_message(d['log']['fed'].format(food=name), 'success')
        if before < needed():
            lines = d['fed']
            text = lines[min(before, len(lines) - 1)]
        else:
            text = d['fed_again']
        self._emberpup_outcome(text.format(food=name), 'options')

    def _emberpup_ignore(self):
        self.add_message(data()['ignore'], 'info')
        self._close_emberpup()

    def _emberpup_attack(self):
        d = data()
        pup = self._emberpup_npc
        pup.alive = False                 # he left: not a kill (see _reap_unnoticed_kills)
        try:
            self.monsters.remove(pup)
        except ValueError:
            pass
        self._emberpup_state()['outcome'] = 'fled'
        import karma
        karma.adjust(self, int(d['attack_karma']), kind='cruelty', source='emberpup_attack')
        import deeds
        deeds.note(self, 'wrong.emberpup', source='emberpup', tags=['vice:cruelty'])
        self.add_message(d['log']['fled'], 'danger')
        self._chron('deed', d['attack_chronicle'], source='emberpup')
        self._emberpup_acted = True
        self._emberpup_outcome(d['attack'], 'player')

    def _emberpup_shelter(self):
        """Leave him the Bloomleaf Cloak against the rain: it is his now."""
        d = data()
        pup = self._emberpup_npc
        if getattr(pup, '_emberpup_sheltered', False):
            self._emberpup_outcome(d['already_sheltered'], 'options')
            return
        cover = shelter_choices(self.player)
        if not cover:
            if wears_cover(self.player):
                self._emberpup_outcome(d['take_off'], 'options')
                return
            other = other_cover(self.player)
            if other is not None:
                self._emberpup_outcome(d['not_leaves'].format(item=self._bare_name(other)), 'options')
                return
            self._emberpup_outcome(d['no_shelter'], 'options')
            return
        item = cover[0]
        name = self._display_name(item)
        self._emberpup_give_cover(item)
        pup._emberpup_sheltered = True
        pup.sprite_id = sprite_of(pup)
        self._emberpup_acted = True
        import deeds
        deeds.note(self, 'aid.emberpup_sheltered', source='emberpup', unique=True)
        self.add_message(d['log']['sheltered'].format(item=name), 'success')
        self._emberpup_outcome(d['sheltered'].format(item=name), 'options')

    def _emberpup_give_cover(self, item) -> None:
        """The cloak stays with the pup: it is his from now on."""
        if item in self.player.inventory:
            self.player.remove_from_inventory(item)
        pup = getattr(self, '_emberpup_npc', None)
        if pup is not None:
            pup._emberpup_cloak = item

    def _emberpup_choose(self):
        d = data()
        pup = self._emberpup_npc
        if feeds(pup) <= 0:
            self._emberpup_outcome(d['refused'], 'options')
            return
        if feeds(pup) < needed():
            self._emberpup_outcome(d['refused_trust'], 'options')
            return
        if not getattr(pup, '_emberpup_fed', False):
            self._emberpup_outcome(d['refused_hungry'], 'options')
            return
        if not getattr(pup, '_emberpup_sheltered', False):
            self._emberpup_outcome(d['refused_cold'], 'options')
            return
        q = d['quiz']
        subject, tier, need = q['subject'], int(q['tier']), int(q['threshold'])
        self.quiz_title = d['quiz_title']
        self.state = STATE_QUIZ

        def on_complete(result):
            self._emberpup_npc = pup
            if result.success:
                self._emberpup_adopt(pup)
            else:
                pup._emberpup_fed = False     # feed him again to try again
                self.add_message(d['log']['shied'], 'info')
                self._emberpup_acted = True
                self._emberpup_outcome(d['fail'], 'player')
                self.state = STATE_EMBERPUP

        self.quiz_engine.start_quiz(
            mode='threshold', subject=subject, tier=tier, callback=on_complete,
            threshold=need,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds(subject),
            base_seconds=self.player.get_quiz_timer(subject),
        )

    def _emberpup_adopt(self, pup):
        """He joins you, through the same path a Soul Sphere pet takes, still
        wearing the Bloomleaf Cloak (pet_system ``bloomleaf``)."""
        from pet_system import Pet
        d = data()
        x, y = pup.x, pup.y
        pup.alive = False
        try:
            self.monsters.remove(pup)
        except ValueError:
            pass
        self._emberpup_state()['outcome'] = 'adopted'
        import deeds
        deeds.note(self, 'saved.emberpup', source='emberpup', unique=True)
        # A pup: he starts as a newborn does (level 1), whatever the floor.
        pet = Pet(d['pet_species'], x, y)
        pet.bloomleaf = bool(getattr(pup, '_emberpup_sheltered', False))
        self._companions_to_stasis()          # one companion at a time
        self.pets.append(pet)
        self._emberpup_new_pet = pet
        self.add_message(d['log']['joined'], 'success')
        self._emberpup_outcome(d['pass'], 'name')
        self.state = STATE_EMBERPUP

    def _emberpup_open_naming(self):
        """The Soul Sphere naming popup, with the Emberpup's own words."""
        d = data()
        pet = getattr(self, '_emberpup_new_pet', None)
        self._emberpup_npc = None
        self._emberpup_new_pet = None
        if pet is None:
            self.state = STATE_PLAYER
            return
        self._naming_pet = pet
        self._pet_name_input_buffer = pet.species_name
        self._naming_story = {
            'title': d['name_title'], 'prompt': d['name_prompt'],
            'named_message': d['named_message'], 'unnamed_message': d['unnamed_message'],
            'named_chronicle': d['named_chronicle'], 'unnamed_chronicle': d['unnamed_chronicle'],
        }
        self.state = STATE_PET_NAME_INPUT

# ===========================================================================
# The Bloomleaf Cloak and Old Nickel, who wears it (winning-build plan 3.8)
# ===========================================================================
#
# The Bloomleaf Cloak and Old Nickel, the kobold who wears it (winning-build
# plan 2026-11-13, section 3.8).
#
# The abandoned Emberpup sits in the rain, and only a cloak of leaves will turn
# it (EmberpupMixin, above). There is one such cloak in the run: broad
# leaves torn off a young Bloomsaur's back, which nothing rusts under while it
# is worn (special_properties.rustproof_wearer, read by Player.is_rustproof).
# It is not lying about. Old Nickel wears it: a greedy, spiteful kobold of the
# upper shafts who hoards stolen iron (data/monsters.json ``old_nickel``).
#
#   * His floor is drawn once a run, with the run's own seeded generator (the
#     Emberpup's), from floor 1 to the Emberpup's floor, away from a planned
#     mini-boss where it can be (``draw_floor``; kept in ``game._emberpup`` as
#     'cloak_floor', so it is saved with the pup's).
#   * He is set down when that floor is first reached, in a room of his own:
#     never the pup's room, never the room the hero stands in. That room is
#     his home (Monster._wary_home): he does not leave it.
#   * He does not start the fight (Monster.wary, monster.py): he watches, warns
#     once, keeps his distance, and fights when the hero comes beside him,
#     corners him or strikes first. Then he is a real fight for his floor.
#   * He drops the cloak, identified (treasure.unique_drop_id, and
#     special_properties.arrives_known in Game._spawn_unique_item); if a kill
#     path gave nothing (a banishment takes his goods with him), the cloak is
#     set down where he fell all the same (``_cloak_wearer_slain``).
#   * Killing him moves no karma: he is nobody's innocent. The deeds register
#     notes ``slew.old_nickel``.
#
# The choice the run then asks: keep a cloak that guards your iron all run, or
# give it to a pup who has been waiting in the rain. Recall Lore carries the
# hint (data/hints.json).

CLOAK_ID = 'bloomleaf_cloak'
WEARER_ID = 'old_nickel'


def cfg() -> dict:
    """The cloak's block in data/abandoned_emberpup.json."""
    return data().get('cloak') or {}


def cloak_id() -> str:
    return str(cfg().get('item_id', CLOAK_ID))


def wearer_id() -> str:
    return str(cfg().get('wearer_id', WEARER_ID))


def draw_floor(rng, pup_floor, exclude=()) -> int | None:
    """The floor Old Nickel waits on: one from ``first_floor`` (1) to the
    Emberpup's own, drawn with `rng`. Floors in `exclude` (a planned
    mini-boss's) are skipped while any other is left. None in a run with no
    Emberpup."""
    if not pup_floor:
        return None
    lo = int(cfg().get('first_floor', 1))
    floors = list(range(lo, int(pup_floor) + 1)) or [int(pup_floor)]
    free = [f for f in floors if f not in set(exclude or ())]
    return rng.choice(free or floors)


def is_cloak(item) -> bool:
    return getattr(item, 'id', None) == cloak_id()


def is_wearer(m) -> bool:
    return getattr(m, 'kind', None) == wearer_id()


def wearer_defn() -> dict:
    from paths import data_path
    with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
        d = json.load(f)[wearer_id()]
    return {**d, 'id': wearer_id()}


def make_cloak(x: int = 0, y: int = 0):
    """A fresh Bloomleaf Cloak from data/items/armor.json, or None."""
    from items import load_items, copy_at
    tpl = next((a for a in load_items('armor') if getattr(a, 'id', '') == cloak_id()), None)
    return copy_at(tpl, x, y) if tpl is not None else None


def _room_of(rooms, x: int, y: int):
    for r in rooms:
        if r.x <= x < r.x + r.width and r.y <= y < r.y + r.height:
            return r
    return None


def home_of(room) -> tuple:
    """The floor tiles inside a room, as (x0, y0, x1, y1) inclusive."""
    return (room.x + 1, room.y + 1, room.x + room.width - 2, room.y + room.height - 2)


class BloomleafMixin:
    """Old Nickel's place in the run. The pup's side is EmberpupMixin."""

    def _cloak_floor(self):
        """This run's floor for Old Nickel. A save from before him draws
        nothing new: he waits on the pup's own floor, met the next time the
        hero comes there (only while the pup still waits)."""
        st = self._emberpup_state()
        if 'cloak_floor' not in st:
            st['cloak_floor'] = st.get('floor') if not st.get('outcome') else None
            st.setdefault('cloak_spawned', False)
        return st.get('cloak_floor')

    def _maybe_spawn_cloak_wearer(self, level: int):
        """Set Old Nickel down on his floor, once a run, in a room that is
        neither the pup's nor the hero's."""
        st = self._emberpup_state()
        if self._cloak_floor() != level or st.get('cloak_spawned'):
            return
        if any(is_wearer(m) and getattr(m, 'alive', False) for m in self.monsters):
            st['cloak_spawned'] = True
            return
        from monster import Monster
        from geom import all_occupied_tiles
        rng = random.Random(int(st.get('cloak_seed', 0) or 0) * 131 + int(level))
        rooms = list(self.dungeon.rooms)
        pup_rooms = {id(r) for m in self.monsters if is_emberpup(m)
                     for r in [_room_of(rooms, m.x, m.y)] if r is not None}
        here = _room_of(rooms, self.player.x, self.player.y)
        start = rooms[0] if rooms else None
        # Nor a room with a trader's stall in it (a save from before him
        # meets him on a floor whose stall is already set out): his room is
        # his, and the hero would have to corner him to trade.
        from mystery_system import MerchantNPC
        stall_rooms = {id(r) for g in (getattr(self, 'ground_items', None) or ())
                       if isinstance(g, MerchantNPC)
                       for r in [_room_of(rooms, g.x, g.y)] if r is not None}
        picks = [r for r in rooms if id(r) not in pup_rooms and id(r) not in stall_rooms
                 and r is not here and r is not start]
        if not picks:
            picks = [r for r in rooms if id(r) not in pup_rooms and r is not here]
        rng.shuffle(picks)
        picks.sort(key=lambda r: -(max(0, r.width - 2) * max(0, r.height - 2) >= 9))
        occupied = all_occupied_tiles(self.monsters) | self._occupants()
        spot, home = None, None
        for room in picks:
            tiles = [t for t in room.inner_tiles()
                     if self.dungeon.is_walkable(*t) and t not in occupied
                     and max(abs(t[0] - self.player.x), abs(t[1] - self.player.y)) > 2]
            if tiles:
                spot, home = rng.choice(tiles), home_of(room)
                break
        if spot is None:
            spot = self._free_spawn_tile(occupied)
        if spot is None:
            return
        m = Monster(wearer_defn(), *spot)
        m._wary_home = home
        self.monsters.append(m)
        st['cloak_spawned'] = True

    def _cloak_wearer_slain(self, monster):
        """Old Nickel is dead: the deed, and the cloak where he fell if no
        kill path set it down (a banished foe takes his goods with him)."""
        if not is_wearer(monster):
            return
        import deeds
        deeds.note(self, 'slew.old_nickel', source='engine:bloomleaf', unique=True)
        st = self._emberpup_state()
        st['cloak_outcome'] = 'slain'
        if self._cloak_in_play():
            return
        cloak = make_cloak(monster.x, monster.y)
        if cloak is None:
            return
        from items import grant_identified, claim_unique
        grant_identified(self, cloak)
        claim_unique(cloak)
        self.ground_items.append(cloak)
        self.add_message(f"{monster.name}'s cloak of leaves falls where he fell.", 'loot')

    def _cloak_in_play(self) -> bool:
        """Is there a Bloomleaf Cloak in the run already: on this floor's
        ground, carried or worn, or over the Emberpup's rock?"""
        if any(is_cloak(i) for i in self.ground_items):
            return True
        p = self.player
        if any(is_cloak(i) for i in list(p.inventory) + list(p.worn_items())):
            return True
        if any(is_emberpup(m) and getattr(m, '_emberpup_sheltered', False) for m in self.monsters):
            return True
        return self._emberpup_state().get('outcome') == 'adopted'

    # ---- QA (Titivillus, Shift+L) -----------------------------------------

    def _qa_bloomleaf(self):
        """Titivillus QA build only: Old Nickel set down in this room, a few
        steps off; pressed again with him already here, the Bloomleaf Cloak
        straight into the pack (to test the rust and the pup without the
        fight)."""
        if not getattr(self.player, 'qa_tools', False):
            return
        here = [m for m in self.monsters if is_wearer(m) and m.alive]
        if here:
            cloak = make_cloak(self.player.x, self.player.y)
            if cloak is not None:
                from items import grant_identified
                grant_identified(self, cloak)
                self.player.inventory.append(cloak)
                self.add_message("[QA] A Bloomleaf Cloak is in your pack.", 'info')
            return
        from monster import Monster
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(self.monsters) | self._occupants()
        ring = [(self.player.x + dx, self.player.y + dy) for r in (4, 3, 5, 2)
                for dx in range(-r, r + 1) for dy in range(-r, r + 1) if max(abs(dx), abs(dy)) == r]
        spot = next((t for t in ring if self.dungeon.in_bounds(*t) and self.dungeon.is_walkable(*t)
                     and t not in occupied), None)
        if spot is None:
            self.add_message("[QA] No room for Old Nickel here.", 'info')
            return
        m = Monster(wearer_defn(), *spot)
        m._wary_home = None
        room = _room_of(self.dungeon.rooms, *spot)
        if room is not None:
            m._wary_home = home_of(room)
        self.monsters.append(m)
        st = self._emberpup_state()
        self.add_message(f"[QA] Old Nickel set down {max(abs(spot[0] - self.player.x), abs(spot[1] - self.player.y))} "
                         f"steps off. His floor this run: {self._cloak_floor()}; the pup's: {st.get('floor')}. "
                         "Shift+L again: the cloak into your pack.", 'info')
