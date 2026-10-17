"""The abandoned Emberpup: a random event, about one run in five.

On one floor from 3 to 8 a small fire lizard sits alone on a rock under a little
rain cloud, waiting for a trainer who said they would come back. Bumping it
opens its screen (``STATE_EMBERPUP``): the first time, its story; then four
choices.

  Give it something to eat   one identified food from the pack is eaten; it
                             warms up and trusts you a little (first feed only:
                             +1 karma). Nothing to give: it stays wary.
  Leave it be                it stays on its rock; come back any time.
  Attack it                  it flees into the dark, gone for the run; karma
                             drops. No fight, no loot.
  "I choose you!"            only once fed: an animal quiz, tier 2, two right
                             answers needed. Pass: it becomes your pet Emberpup
                             (the Soul Sphere pet path, naming popup included).
                             Fail: it shies away but stays; feed it again and
                             try again.

Run state lives in ``game._emberpup`` (saved): the floor it waits on (None in a
run without it), whether it has been placed, and how it ended ('fled' or
'adopted'). Its own state (story seen, fed) lives on the creature, which is
saved with the floor. All text and numbers are in data/abandoned_emberpup.json.
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
    """The floor this run's Emberpup waits on, or None (most runs)."""
    d = data()
    if rng.random() >= float(d['chance_per_run']):
        return None
    return rng.randint(int(d['first_floor']), int(d['last_floor']))


def roll_for_new_run() -> int | None:
    """roll_floor for a new run, drawn from its own generator so the shared
    random stream (dungeons, seeded tests, the capture harness) is untouched.
    The seed comes from that stream, so a seeded game is repeatable."""
    saved = random.getstate()
    try:
        seed = random.getrandbits(64)
    finally:
        random.setstate(saved)
    return roll_floor(random.Random(seed ^ 0x0E3BE6))


def new_run_state() -> dict:
    return {'floor': roll_for_new_run(), 'spawned': False, 'outcome': None}


def is_emberpup(thing) -> bool:
    return bool(getattr(thing, '_is_abandoned_emberpup', False))


def food_choices(inventory) -> list:
    """What the player could feed it: identified food and ordinary raw cuts
    (never a trophy)."""
    from items import Food, Ingredient
    return [i for i in inventory
            if isinstance(i, (Food, Ingredient))
            and getattr(i, 'identified', True)
            and getattr(i, 'tier_role', '') != 'trophy']


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

    def _maybe_spawn_emberpup(self, level: int):
        """Place the Emberpup on its floor, once per run, on first arrival."""
        st = self._emberpup_state()
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
        occupied.add((self.player.x, self.player.y))
        rooms = self.dungeon.rooms[1:] if len(self.dungeon.rooms) > 1 else self.dungeon.rooms
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
        pup._emberpup_met = False      # its story has been told
        pup._emberpup_fed = False      # fed since the last try: "I choose you" may be asked
        self.monsters.append(pup)
        st['spawned'] = True

    # ---- the screen -------------------------------------------------------

    def _start_emberpup_encounter(self, pup):
        """Bumping it: its story the first time, its choices after that."""
        self._emberpup_npc = pup
        self._emberpup_phase = 'options' if getattr(pup, '_emberpup_met', False) else 'story'
        pup._emberpup_met = True
        self._emberpup_text = ''
        self._emberpup_after = 'options'
        self._emberpup_food = []
        self._emberpup_food_scroll = 0
        self._emberpup_acted = False
        self.state = STATE_EMBERPUP

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
        elif key == pygame.K_ESCAPE:
            self._emberpup_ignore()

    # ---- the four choices ---------------------------------------------------

    def _emberpup_feed_start(self):
        d = data()
        pup = self._emberpup_npc
        if getattr(pup, '_emberpup_fed', False):
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
        """It eats one of `item` and trusts you a little."""
        d = data()
        pup = self._emberpup_npc
        if item not in self.player.inventory:
            self._emberpup_phase = 'options'
            return
        name = self._display_name(item)
        self.player.remove_from_inventory(item)
        pup._emberpup_fed = True
        self._emberpup_acted = True
        if not getattr(pup, '_emberpup_karma_given', False):
            pup._emberpup_karma_given = True
            self.karma = max(-10, min(10, self.karma + int(d['first_feed_karma'])))
        self.add_message(f"The Emberpup eats your {name}.", 'success')
        self._emberpup_outcome(d['fed'].format(food=name), 'options')

    def _emberpup_ignore(self):
        self.add_message(data()['ignore'], 'info')
        self._close_emberpup()

    def _emberpup_attack(self):
        d = data()
        pup = self._emberpup_npc
        pup.alive = False                 # it left: not a kill (see _reap_unnoticed_kills)
        try:
            self.monsters.remove(pup)
        except ValueError:
            pass
        self._emberpup_state()['outcome'] = 'fled'
        self.karma = max(-10, min(10, self.karma + int(d['attack_karma'])))
        self.add_message("The Emberpup flees into the dark.", 'danger')
        self._log_chronicle(d['attack_chronicle'])
        self._emberpup_acted = True
        self._emberpup_outcome(d['attack'], 'player')

    def _emberpup_choose(self):
        d = data()
        pup = self._emberpup_npc
        if not getattr(pup, '_emberpup_fed', False):
            self._emberpup_outcome(d['refused'], 'options')
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
                pup._emberpup_fed = False     # feed it again to try again
                self.add_message("The Emberpup shies away from you.", 'info')
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
        """It joins you, through the same path a Soul Sphere pet takes."""
        from pet_system import Pet
        d = data()
        x, y = pup.x, pup.y
        pup.alive = False
        try:
            self.monsters.remove(pup)
        except ValueError:
            pass
        self._emberpup_state()['outcome'] = 'adopted'
        pet = Pet(d['pet_species'], x, y)
        pet.apply_late_pickup_bonus(self.dungeon_level)
        self.pets.append(pet)
        self._emberpup_new_pet = pet
        self.add_message("The Emberpup comes down off its rock to you.", 'success')
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
