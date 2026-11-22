"""LoreFixturesMixin: Worth a Closer Look (Dungeon Alive slice 4, B1).

A lore fixture stands in a room (data/lore_fixtures.json): a copyist's desk,
an alchemist's bench, a surveyor's table, a memorial stone, a wayside
shrine, a clerk's ledger, a hunter's trophy board, a cooking fire, a brazen
head, a goblins' gaming table, a carved lintel over a hidden door. Stand on
or beside one and press D: ONE question of its subject, binary. A right
answer gives what it has, once; a wrong one spends it all the same.

What they give: information, consumables, coin and study progress, never
gear. No karma.
"""
from __future__ import annotations

import copy
import random

from game_states import STATE_PLAYER, STATE_QUIZ


class LoreFixturesMixin:

    def _lore_fixture_offer(self) -> bool:
        """D beside a lore fixture. The first press says what it is and asks
        for D again; the second begins its one question (audit G9: a hero
        who only meant to drop something got a question, and a wrong answer
        spent the fixture). True if one was there."""
        import decor
        hit = decor.lore_fixture_near(self.dungeon, self.player.x, self.player.y)
        if not hit:
            return False
        pos, fid = hit
        d = decor.lore_fixtures()['fixtures'].get(fid)
        if not d:
            return False
        armed = self.__dict__.get('_lore_armed')
        here = (self.dungeon_level, (self.player.x, self.player.y), pos)
        if armed != here:
            self._lore_armed = here
            self.add_message(f"{decor.fixture_def(fid).get('look', '')} "
                             f"Press D again to {d.get('verb', 'look closer')}; "
                             f"drop things from your Kit (K) instead.", 'info')
            return True
        self._lore_armed = None
        if not self._gate('work'):
            return True
        tier = int(((self.dungeon.__dict__.get('lore_fixtures') or {}).get(pos) or {}).get('tier', 1))
        subject = d['subject']
        self.add_message(f"You {d.get('verb', 'look closer')}...", 'info')
        self.quiz_title = f"{decor.fixture_def(fid).get('name', 'a fixture').upper()}  --  {subject.upper()}"
        self.state = STATE_QUIZ

        def on_complete(result):
            self._lore_fixture_resolve(pos, fid, d, bool(result.success))
            self.state = STATE_PLAYER
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold', subject=subject, tier=max(1, min(5, tier)),
            callback=on_complete, threshold=1, total_qs=1,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds(subject),
            base_seconds=self.player.get_quiz_timer(subject),
        )
        return True

    def _lore_fixture_hint(self, x: int, y: int) -> str:
        """The line a bump or a step beside it says: what it is, and D."""
        import decor
        pos = (x, y)
        state = self.dungeon.__dict__.get('lore_fixtures') or {}
        if pos not in state:
            return ''
        if (self.dungeon.__dict__.get('fixture_state') or {}).get(pos) == 'spent':
            return ''
        fid = decor.fixture_at(self.dungeon, x, y)
        d = decor.lore_fixtures()['fixtures'].get(fid or '')
        if not d:
            return ''
        return f"{decor.fixture_def(fid).get('look', '')} (D: {d.get('verb', 'look closer')}.)"

    def _lore_fixture_resolve(self, pos, fid: str, d: dict, ok: bool) -> None:
        state = self.dungeon.__dict__.setdefault('fixture_state', {})
        state[pos] = 'spent'
        if not ok:
            self.add_message(d.get('fail', 'Nothing comes of it.'), 'warning')
            if d.get('reward') == 'truth':
                # The brazen head laughs, loud enough to wake the floor.
                self._make_noise('alarm', pos[0], pos[1])
            elif d.get('reward') == 'pot':
                import economy
                # The purse is the Game's (player_gold); the Player has none.
                stake = min(int(self.player_gold or 0),
                            economy.roll_share(random, self.dungeon_level, economy.GRAVE_SMALL_SHARE))
                if stake > 0:
                    self.player_gold -= stake
                    self.add_message(f"You lose {stake:,} gold.", 'warning')
            return
        self.add_message(d.get('pass', 'It was worth a closer look.'), 'success')
        getattr(self, f"_lore_reward_{d.get('reward', 'none')}", lambda p, f: None)(pos, fid)
        try:
            self._chron('discovery', f"Looked closer at {self._fixture_name(fid)}, and it paid.",
                        once=f'lore_fixture:{fid}')
        except Exception:
            pass

    @staticmethod
    def _fixture_name(fid: str) -> str:
        import decor
        return decor.fixture_def(fid).get('name', 'something')

    # -- what each gives ------------------------------------------------------

    def _lore_drop(self, item) -> None:
        item.x, item.y = self.player.x, self.player.y
        self.ground_items.append(item)
        self.add_message(f"{self._display_name(item)} lies at your feet.", 'loot')

    def _lore_floor_item(self, cls_name: str):
        from items import load_items, is_random_loot
        from container_system import _weighted_common_pick
        lvl = max(1, min(100, self.dungeon_level))
        try:
            pool = [t for t in load_items(cls_name)
                    if getattr(t, 'min_level', 1) <= lvl and is_random_loot(t)
                    and not getattr(t, 'is_unique', False)]
        except FileNotFoundError:
            return None
        if not pool:
            return None
        return copy.copy(_weighted_common_pick(pool, lvl, random))

    def _lore_reward_scroll(self, pos, fid) -> None:
        item = self._lore_floor_item('scroll')
        if item is not None:
            self._lore_drop(item)

    def _lore_reward_potion(self, pos, fid) -> None:
        item = self._lore_floor_item('potion')
        if item is not None:
            self._lore_drop(item)

    def _lore_reward_map(self, pos, fid) -> None:
        for y in range(self.dungeon.height):
            for x in range(self.dungeon.width):
                self.dungeon.explored.add((x, y))

    def _lore_reward_reveal_store(self, pos, fid) -> None:
        """Where the garrison hid its stores: a hidden treasure chamber's door
        is shown (or, with none, the vault; or a little coin)."""
        from dungeon import SECRET_DOOR, DOOR
        for ch in self.dungeon.__dict__.get('hidden_chambers') or ():
            r = ch.get('room')
            if r is None or ch.get('type') != 'treasure':
                continue
            for y in range(r.y, r.y + r.height):
                for x in range(r.x, r.x + r.width):
                    if self.dungeon.tiles[y][x] == SECRET_DOOR:
                        self.dungeon.tiles[y][x] = DOOR
                        for yy in range(r.y, r.y + r.height):
                            for xx in range(r.x, r.x + r.width):
                                self.dungeon.explored.add((xx, yy))
                        self.add_message("A hidden door is marked on your map.", 'success')
                        return
        vault = self.dungeon.__dict__.get('vault')
        room = vault.get('room') if isinstance(vault, dict) else vault
        if room is not None:
            for yy in range(room.y, room.y + room.height):
                for xx in range(room.x, room.x + room.width):
                    self.dungeon.explored.add((xx, yy))
            self.add_message("A sealed vault is marked on your map.", 'success')
            return
        self._lore_reward_coin(pos, fid)

    def _lore_reward_blessing(self, pos, fid) -> None:
        for bad in ('petrifying', 'poisoned', 'diseased', 'bleeding', 'confused', 'blinded', 'weakened',
                    'hexed', 'charmed'):
            if self.player.has_effect(bad):
                self.player.status_effects.pop(bad, None)
                self.add_message(f"You are no longer {bad}.", 'success')
                return
        heal = max(1, self.player.max_hp // 4)
        before = self.player.hp
        self.player.hp = min(self.player.max_hp, self.player.hp + heal)
        if self.player.hp > before:
            self.add_message(f"You recover {self.player.hp - before} HP.", 'success')

    def _lore_reward_coin(self, pos, fid) -> None:
        import economy
        gold = economy.roll_share(random, self.dungeon_level, economy.THRONE_SHARE)
        self.add_message(f"You find {gold:,} gold.", 'success')
        self._gain_gold(gold)

    def _lore_reward_pot(self, pos, fid) -> None:
        import economy
        gold = economy.roll_share(random, self.dungeon_level, economy.GRAVE_SMALL_SHARE)
        self.add_message(f"You win {gold:,} gold.", 'success')
        self._gain_gold(gold)

    def _lore_reward_study(self, pos, fid) -> None:
        """The hunter's notes: one kind that hunts this floor, studied. The
        floor's clan first, so the board helps with what is really here."""
        import family_lore
        kinds = []
        clan = getattr(self.dungeon, 'clan', None)
        for m in self.monsters:
            if not m.alive or getattr(m, 'is_allied', False) or not getattr(m, 'family', None):
                continue
            if getattr(m, '_npc_encounter_tag', None) or getattr(m, '_flavor_encounter_tag', None):
                continue
            kinds.append((0 if m.family == clan else 1, m.kind))
        kinds.sort()
        for _rank, kind in kinds:
            if kind in family_lore.studied(self.player):
                continue
            if self._family_study(kind):
                self.add_message("Your Field Notes grow.", 'success')
                return
        self.add_message("You know every beast on this floor already.", 'info')

    def _lore_reward_meal(self, pos, fid) -> None:
        gain = max(1, self.player.max_sp // 2)
        before = self.player.sp
        self.player.sp = min(self.player.max_sp, self.player.sp + gain)
        self.add_message(f"You are fed. (+{self.player.sp - before} SP)", 'success')

    def _lore_reward_truth(self, pos, fid) -> None:
        """The brazen head's true thing: the vault, the floor's named foe, or
        its mystery altar, marked on the map."""
        for m in self.monsters:
            if m.alive and m._is_named_foe() and not getattr(m, 'is_allied', False):
                for yy in range(m.y - 2, m.y + 3):
                    for xx in range(m.x - 2, m.x + 3):
                        if self.dungeon.in_bounds(xx, yy):
                            self.dungeon.explored.add((xx, yy))
                self.add_message(f"\"{m.name} waits here,\" it says, and tells you where.", 'warning')
                return
        vault = self.dungeon.__dict__.get('vault')
        room = vault.get('room') if isinstance(vault, dict) else vault
        if room is not None:
            for yy in range(room.y, room.y + room.height):
                for xx in range(room.x, room.x + room.width):
                    self.dungeon.explored.add((xx, yy))
            self.add_message("\"There is a vault,\" it says, and tells you where.", 'success')
            return
        self._lore_reward_map(pos, fid)
        self.add_message("\"Then you shall have it all,\" it says, and names every room on the floor.", 'success')

    def _lore_reward_light_brazier(self, pos, fid) -> None:
        """Fenrir's hall: a lit brazier melts the ice round it. Fenrir slips
        on ice and so do you, so melt the patches you need and leave the ones
        that trip him."""
        import decor
        from dungeon import ICE, FLOOR
        decor.place(self.dungeon, pos, 'brazier_lit')
        (self.dungeon.__dict__.get('lore_fixtures') or {}).pop(pos, None)
        melted = 0
        x0, y0 = pos
        for y in range(y0 - 2, y0 + 3):
            for x in range(x0 - 2, x0 + 3):
                if self.dungeon.in_bounds(x, y) and self.dungeon.tiles[y][x] == ICE:
                    self.dungeon.tiles[y][x] = FLOOR
                    melted += 1
        if melted:
            self.add_message("The ice round the brazier melts to wet stone.", 'success')

    def _lore_reward_seal_vent(self, pos, fid) -> None:
        """The Pit: a vent sealed with a prayer lets no more locusts out
        (main._spawn_abaddon_locusts uses the vents still open). Only a
        right answer seals it: a wrong one spends the try, and the smoke
        goes on (audit G4)."""
        self.dungeon.__dict__.setdefault('sealed_vents', set()).add(tuple(pos))
        self.add_message("One way out of the Abyss is shut.", 'success')

    def _lore_reward_open_door(self, pos, fid) -> None:
        from dungeon import SECRET_DOOR, DOOR
        x, y = pos
        if self.dungeon.tiles[y][x] == SECRET_DOOR:
            self.dungeon.tiles[y][x] = DOOR
            self._refresh_fov()
