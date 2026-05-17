"""Game's magic-related action handlers, extracted from main.py (Phase 7).

This module defines :class:`MagicMixin`, which the real ``Game`` class
inherits alongside :class:`game_render.RenderMixin`,
:class:`game_menus.MenuMixin`, :class:`game_input.InputMixin`, and
:class:`game_encounters.EncountersMixin`.  The mixin owns:

  * Spell casting (learned spells via MP, science escalator-chain quiz):
    ``_invoke_spell``, ``_start_spell_quiz``, ``_spell_damage``, and the
    large dispatcher ``_apply_spell_effect``.
  * Scroll reading (grammar threshold quiz): ``_read_scroll`` and the
    large dispatcher ``_apply_scroll_effect``.
  * Spellbook learning, including the Necronomicon's stateful multi-question
    flow: ``_learn_from_spellbook``, ``_necronomicon_quiz``,
    ``_necro_ask_next``, ``_necro_answer``, ``_necro_update``,
    ``_necro_complete``, plus the side-effect spawns
    ``_spawn_necronomicon_undead``, ``_spawn_npc_deadite``, and
    ``_summon_undead_pets`` used by Army-of-Darkness.
  * Wand zapping (science threshold quiz): ``_invoke_wand``,
    ``_apply_wand_effect``, plus damage/duration scaling helpers
    ``_wand_tier_damage`` and ``_wand_tier_duration``.  ``_boss_resist_cc``
    is also magic-only and moves here.
  * Identification (philosophy threshold quiz): ``_identify_item``,
    ``_auto_identify_all`` (Philosopher's Stone), ``_propagate_identification``.
  * Recall Lore (trivia escalator-chain quiz): ``_start_recall_lore`` and
    ``_resolve_recall_lore``.

The corresponding render code (``_draw_spell_menu``, ``_draw_scroll_menu``,
``_draw_wand_menu``, ``_draw_identify_menu``) lives in RenderMixin, menu
input handlers (``_open_spell_menu``/``_spell_menu_input`` etc.) live in
MenuMixin, and the Necronomicon answer keypress is dispatched from
InputMixin.  MRO resolves all cross-mixin ``self._foo()`` calls.

``_int_scaled_damage`` stays on ``Game`` itself because it is also called
outside magic methods (Stuffie fire breath in main.py and elder_scream
power in MenuMixin); leaving it on Game keeps the dependency arrow
pointing the same direction as the other helpers.  Class-level constant
``_SCROLL_TABS`` stays on Game because MenuMixin and RenderMixin read it
directly.
"""
from __future__ import annotations

import random
from typing import TYPE_CHECKING

import pygame

import sound_system as _snd
from game_helpers import wand_tier_duration
from game_states import (
    STATE_PLAYER, STATE_QUIZ,
    STATE_TARGET, STATE_LORE,
    STATE_HINT,
)
from items import Container
from quiz_engine import QuizMode, QuizState
from spells import LEARNABLE_SPELLS

if TYPE_CHECKING:
    from items import Scroll, Spellbook, Wand


class MagicMixin:
    """Spell, scroll, spellbook, wand, identification, and recall-lore actions.

    Class-level state (``_SPELL_CHAIN_MULTS``, ``_NECRONOMICON_QUESTIONS``,
    and the staticmethod alias ``_wand_tier_duration``) lives on the mixin
    so it stays co-located with the methods that consume it.
    """

    # ------------------------------------------------------------------
    # Recall Lore (trivia escalator chain quiz)
    # ------------------------------------------------------------------

    def _start_recall_lore(self):
        """Begin a Recall Lore session -- escalator chain trivia quiz. Cooldown-gated."""
        if self.player.recall_lore_cooldown > 0:
            self.add_message(
                f"Your mind needs rest before recalling more lore. "
                f"({self.player.recall_lore_cooldown} turns remain)", 'warning'
            )
            return
        self.add_message("You close your eyes and search your memory...", 'info')
        self.quiz_title = "RECALL LORE -- TRIVIA"
        self.state = STATE_QUIZ

        def on_complete(result):
            chain = result.score
            self._resolve_recall_lore(chain)
            self.state = STATE_HINT
            _qs_lore = getattr(self, 'quirk_system', None)
            if _qs_lore:
                _qs_lore.on_recall_lore()
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='trivia',
            tier=1,
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_quiz_extra_seconds('trivia'),
            base_seconds=self.player.get_quiz_timer('trivia'),
        )

    def _resolve_recall_lore(self, chain: int):
        """Pick a hint based on chain quality and display it. Set cooldown."""
        import json as _json
        import random as _rng

        # Cooldown: longer for better knowledge (takes time to absorb)
        if chain == 0:
            self.player.recall_lore_cooldown = 40
            self.add_message("Your thoughts scatter. Nothing surfaces.", 'warning')
            self._lore_hint_text = None
            return

        self.player.recall_lore_cooldown = 50 + chain * 15   # 65 .. 125 turns
        if getattr(self.player, 'quirk_progress', {}).get('norns_active'):
            self.player.recall_lore_cooldown = max(5, self.player.recall_lore_cooldown // 2)

        from paths import data_path
        hints_path = data_path('data', 'hints.json')
        try:
            with open(hints_path, encoding='utf-8') as f:
                all_hints = _json.load(f)
        except Exception:
            self.add_message("A lore scroll crumbles in your memory.", 'warning')
            self._lore_hint_text = None
            return

        tier_key = str(min(chain, 5))
        pool = all_hints.get(tier_key, [])
        if not pool:
            self.add_message("Nothing comes to mind.", 'info')
            self._lore_hint_text = None
            return

        hint = _rng.choice(pool)
        self._lore_hint_text = hint
        self._lore_hint_chain = chain
        # Save to lore hints journal (avoid duplicates)
        if hint not in self._recalled_hints:
            self._recalled_hints.append(hint)

    # ------------------------------------------------------------------
    # Wand menu  (u key -- science quiz)
    # ------------------------------------------------------------------

    def _invoke_wand(self, wand: 'Wand'):
        # Philosopher's Wrench: no quiz -- it's a tool, not magic
        if wand.id == 'philosophers_wrench':
            wand.identified = True
            self.player.known_item_ids.add(wand.id)
            self._use_philosophers_wrench()
            self._advance_turn()
            return

        # Flux Capacitor: no quiz -- it's a gift from the universe
        if wand.id == 'flux_capacitor':
            wand.charges -= 1
            self.player.add_effect('time_stopped', 10)
            self.add_message("The Flux Capacitor ignites! Time freezes around you -- 10 turns!", 'success')
            if wand.charges <= 0:
                self.add_message("The Flux Capacitor burns out in a shower of sparks.", 'warning')
                self.player.remove_from_inventory(wand)
            self._advance_turn()
            return

        if wand.charges <= 0:
            self.add_message("The wand is empty -- it crumbles to dust.", 'warning')
            self.player.remove_from_inventory(wand)
            self._advance_turn()
            return

        # Combat wands: open targeting cursor first (like ranged weapons)
        _TARGETED_EFFECTS = {
            'sleep_monster', 'slow_monster', 'confuse_monster', 'paralyze_monster',
            'blind_monster', 'stoning', 'fire_bolt', 'cold_bolt', 'lightning_bolt',
            'acid_spray', 'magic_missile', 'striking', 'death_ray', 'cancellation',
            'polymorph_monster', 'fear_monster', 'charm_monster', 'poison_monster',
            'disease_monster', 'curse_monster', 'teleport_monster', 'drain_life',
            'disintegrate', 'weaken_monster', 'drain_magic', 'dispel_magic',
        }
        if wand.effect in _TARGETED_EFFECTS:
            self._pending_wand = wand
            self._wand_targeting = True
            self._melee_targeting = False
            self._throw_targeting = False
            self._observe_targeting = False
            px, py = self.player.x, self.player.y
            candidates = [
                m for m in self.monsters
                if m.alive and (m.x, m.y) in self.visible
            ]
            candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))
            self._target_candidates = candidates
            self._target_idx = 0
            if candidates:
                self.target_cursor_x = candidates[0].x
                self.target_cursor_y = candidates[0].y
            else:
                self.target_cursor_x = px
                self.target_cursor_y = py
            self.state = STATE_TARGET
            self.add_message(
                "Aim wand -- arrow keys to target, TAB to cycle, ENTER to fire, ESC to cancel.",
                'info'
            )
            return

        display = self._display_name(wand)
        self.quiz_title = f"INVOKING {display.upper()}  --  SCIENCE"
        self.state = STATE_QUIZ
        _was_identified_before = getattr(wand, 'identified', False) or \
            wand.id in self.player.known_item_ids

        def on_complete(result):
            self.state = STATE_PLAYER
            wand.identified = True
            self.player.known_item_ids.add(wand.id)
            _qs_wand = getattr(self, 'quirk_system', None)
            if _qs_wand:
                _qs_wand.on_wand_zapped(wand.id, was_identified=_was_identified_before)

            if not result.success:
                self.add_message("The wand fizzes and fails to fire.", 'warning')
                self._advance_turn()
                return

            wand.charges -= 1
            # Cursed wands: 3% chance to misfire (wastes charge, no effect)
            import random as _rng_wand
            if getattr(wand, 'buc', 'uncursed') == 'cursed' and _rng_wand.random() < 0.03:
                self.add_message("The cursed wand misfires! The charge is wasted.", 'warning')
                if wand.charges <= 0:
                    self.add_message("The wand crumbles to dust -- it is spent.", 'warning')
                    self.player.remove_from_inventory(wand)
                self._advance_turn()
                return
            self._apply_wand_effect(wand)
            if wand.charges <= 0:
                self.add_message("The wand crumbles to dust -- it is spent.", 'warning')
                self.player.remove_from_inventory(wand)
            else:
                self.add_message(
                    f"({wand.charges}/{wand.max_charges} charges remain)", 'info'
                )
            self._advance_turn()

        # All wands use threshold quiz — power is baked into the wand's tier
        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='science',
            tier=wand.quiz_tier,
            callback=on_complete,
            threshold=wand.quiz_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('science'),
            base_seconds=self.player.get_quiz_timer('science'),
        )

    def _boss_resist_cc(self, target, duration: int) -> tuple:
        """Boss CC resistance: 50% chance to resist; if it lands, half duration.
        Returns (adjusted_duration, resisted_bool)."""
        import random as _rng
        is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
        if not is_boss:
            return duration, False
        if _rng.random() < 0.50:
            return 0, True
        return max(1, duration // 2), False

    _wand_tier_duration = staticmethod(wand_tier_duration)

    def _wand_tier_damage(self, base_dmg: int, tier: int) -> int:
        """Scale wand damage by tier AND player INT."""
        tier_mult = 0.5 + tier * 0.5  # T1=1.0, T3=2.0, T5=3.0
        return max(1, int(base_dmg * tier_mult * (1.0 + self.player.INT * 0.1)))

    def _apply_wand_effect(self, wand: 'Wand'):
        import random as _rng
        from dice import roll
        effect = wand.effect

        # -- CHARACTER EFFECTS ------------------------------------------------
        if effect == 'heal':
            amount = roll(wand.power) if wand.power else 8
            self.player.restore_hp(amount)
            self.add_message(f"The wand heals you for {amount} HP!", 'success')

        elif effect == 'extra_heal':
            amount = (roll(wand.power) if wand.power else 20) + 10
            self.player.restore_hp(amount)
            self.add_message(f"Intense healing washes over you -- {amount} HP restored!", 'success')

        elif effect == 'restore_body':
            self.player.hp = self.player.max_hp
            self.player.sp = self.player.max_sp
            self.player.mp = self.player.max_mp
            self.add_message("Your body is fully restored!", 'success')

        elif effect == 'haste_self':
            dur = self._wand_tier_duration(12, wand.quiz_tier)
            self.player.add_effect('hasted', dur)
            self.add_message(f"You feel supernaturally swift! ({dur} turns)", 'success')

        elif effect == 'invisibility_self':
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('invisible', dur)
            self.add_message(f"You fade from sight! ({dur} turns)", 'success')

        elif effect == 'levitation_self':
            dur = self._wand_tier_duration(12, wand.quiz_tier)
            self.player.add_effect('levitating', dur)
            self.add_message(f"You rise gently off the ground! ({dur} turns)", 'success')

        elif effect == 'teleport_self':
            self._teleport_player()

        # -- WORLD EFFECTS ----------------------------------------------------
        elif effect == 'digging':
            px, py = self.player.x, self.player.y
            opened = 0
            from dungeon import DOOR, SECRET_DOOR, WALL, FLOOR
            for dx, dy in [(0,-1),(0,1),(-1,0),(1,0),(-1,-1),(-1,1),(1,-1),(1,1)]:
                nx, ny = px + dx, py + dy
                if self.dungeon.in_bounds(nx, ny):
                    t = self.dungeon.tiles[ny][nx]
                    if t in (DOOR, SECRET_DOOR, WALL):
                        self.dungeon.tiles[ny][nx] = FLOOR
                        opened += 1
            self._refresh_fov()
            self.add_message(
                f"The wand blasts open {opened} wall{'s' if opened != 1 else ''} around you!" if opened
                else "The wand hums -- nothing to dig here.", 'success' if opened else 'info'
            )

        elif effect == 'light':
            radius = 15
            px, py = self.player.x, self.player.y
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx*dx + dy*dy <= radius*radius:
                        nx, ny = px + dx, py + dy
                        if self.dungeon.in_bounds(nx, ny):
                            self.dungeon.explored.add((nx, ny))
            self.add_message("Brilliant light floods the area!", 'success')

        elif effect == 'create_monster':
            import json
            from monster import Monster
            from paths import data_path
            mp = data_path('data', 'monsters.json')
            try:
                with open(mp, encoding='utf-8') as f:
                    all_defs = json.load(f)
                eligible = {k: v for k, v in all_defs.items()
                            if v.get('min_level', 1) <= self.dungeon_level and v.get('frequency', 1) > 0}
                if eligible:
                    kind = _rng.choice(list(eligible.keys()))
                    defn = {**eligible[kind], 'id': kind}
                    floors = [
                        (x, y) for y in range(self.dungeon.height)
                        for x in range(self.dungeon.width)
                        if self.dungeon.is_walkable(x, y)
                        and abs(x - self.player.x) <= 6 and abs(y - self.player.y) <= 6
                        and not any(m.alive and m.x == x and m.y == y for m in self.monsters)
                        and (x, y) != (self.player.x, self.player.y)
                    ]
                    if floors:
                        mx, my = _rng.choice(floors)
                        self.monsters.append(Monster(defn, mx, my))
                        self.add_message(f"{self._a_or_an(defn['name']).capitalize()} materialises from the ether!", 'danger')
                    else:
                        self.add_message("The wand sputters -- no room for a monster nearby.", 'info')
            except Exception:
                self.add_message("The wand misfires!", 'warning')

        # -- STATUS EFFECTS ON TARGET -----------------------------------------
        elif effect in ('sleep_monster', 'slow_monster', 'confuse_monster',
                        'paralyze_monster', 'blind_monster', 'stoning',
                        'fire_bolt', 'cold_bolt', 'lightning_bolt',
                        'acid_spray', 'magic_missile', 'striking',
                        'death_ray', 'cancellation', 'polymorph_monster',
                        'fear_monster', 'charm_monster', 'poison_monster',
                        'disease_monster', 'curse_monster', 'teleport_monster',
                        'drain_life', 'disintegrate', 'weaken_monster',
                        'drain_magic', 'dispel_magic'):
            target = getattr(self, '_wand_override_target', None) or self._nearest_visible_monster()
            if target is None:
                self.add_message("The wand hums but finds no target.", 'info')
                return

            if effect == 'sleep_monster':
                dur = self._wand_tier_duration(8, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the sleep!", 'warning')
                else:
                    target.add_effect('sleeping', dur)
                    self.add_message(f"The {target.name} slumps into a deep sleep! ({dur} turns)", 'success')

            elif effect == 'slow_monster':
                dur = self._wand_tier_duration(8, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the slowing magic!", 'warning')
                else:
                    target.add_effect('slowed', dur)
                    self.add_message(f"The {target.name} slows to a crawl! ({dur} turns)", 'success')

            elif effect == 'confuse_monster':
                dur = self._wand_tier_duration(10, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the confusion!", 'warning')
                else:
                    target.add_effect('confused', dur)
                    self.add_message(f"The {target.name} staggers in confusion! ({dur} turns)", 'success')

            elif effect == 'paralyze_monster':
                dur = self._wand_tier_duration(6, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} resists the paralysis!", 'warning')
                else:
                    target.add_effect('paralyzed', dur)
                    self.add_message(f"The {target.name} is locked in place! ({dur} turns)", 'success')

            elif effect == 'blind_monster':
                dur = self._wand_tier_duration(8, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the blindness!", 'warning')
                else:
                    target.add_effect('blinded', dur)
                    self.add_message(f"The {target.name} claws at its eyes, blinded! ({dur} turns)", 'success')

            elif effect == 'stoning':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} is far too powerful to petrify!", 'warning')
                else:
                    dur = self._wand_tier_duration(5, wand.quiz_tier)
                    target.add_effect('petrifying', dur)
                    self.add_message(f"The {target.name} begins to turn to stone! ({dur} turns)", 'success')

            elif effect == 'cancellation':
                target.status_effects.clear()
                self.add_message(
                    f"The {target.name}'s abilities and effects are cancelled!", 'success'
                )

            elif effect == 'fire_bolt':
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 6, wand.quiz_tier)
                actual = target.take_damage(dmg, 'fire')
                self.add_message(
                    f"A bolt of fire strikes the {target.name} for {actual} damage!", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'cold_bolt':
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 4, wand.quiz_tier)
                actual = target.take_damage(dmg, 'cold')
                dur = self._wand_tier_duration(4, wand.quiz_tier)
                dur, sr = self._boss_resist_cc(target, dur)
                if not sr:
                    target.add_effect('slowed', dur)
                self.add_message(
                    f"A bolt of cold strikes the {target.name} for {actual} damage"
                    + (f" and slows it! ({dur} turns)" if not sr else "!"), 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'lightning_bolt':
                from combat import get_line_tiles
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 10, wand.quiz_tier)
                px, py = self.player.x, self.player.y
                line = get_line_tiles(px, py, target.x, target.y)
                line_set = set(line)
                line_hits = [m for m in self.monsters
                             if m.alive and (m.x, m.y) in line_set and (m.x, m.y) in self.visible]
                for lm in line_hits:
                    actual = lm.take_damage(dmg, 'lightning')
                    if actual > 0:
                        sd, sr = self._boss_resist_cc(lm, 3)
                        if not sr:
                            lm.add_effect('stunned', sd)
                    if not lm.alive:
                        self._on_monster_killed(lm)
                if len(line_hits) > 1:
                    self.add_message(
                        f"Lightning arcs through {len(line_hits)} creatures for {dmg} damage each!", 'success')
                elif line_hits:
                    self.add_message(
                        f"Lightning strikes the {line_hits[0].name} for {dmg} damage!", 'success')
                else:
                    self.add_message("The lightning dissipates harmlessly.", 'info')

            elif effect == 'acid_spray':
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 4, wand.quiz_tier)
                actual = target.take_damage(dmg, 'acid')
                dur = self._wand_tier_duration(6, wand.quiz_tier)
                dur, sr = self._boss_resist_cc(target, dur)
                if not sr:
                    target.add_effect('diseased', dur)
                self.add_message(
                    f"Acid dissolves the {target.name} for {actual} damage"
                    + (f" -- diseased for {dur} turns!" if not sr else "!"), 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'magic_missile':
                # Irresistible: bypasses all resistances. Missile count = wand tier.
                missiles = max(1, wand.quiz_tier)
                total_dmg = 0
                for _ in range(missiles):
                    if not target.alive:
                        break
                    dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 5, wand.quiz_tier)
                    target.hp = max(0, target.hp - dmg)
                    if target.hp == 0:
                        target.alive = False
                    total_dmg += dmg
                self.add_message(
                    f"{missiles} magic missile{'s' if missiles > 1 else ''} "
                    f"unerringly strike{'s' if missiles == 1 else ''} the "
                    f"{target.name} for {total_dmg} total damage!", 'success')
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'striking':
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else 10, wand.quiz_tier)
                actual = target.take_damage(dmg)
                self.add_message(
                    f"The wand slams into the {target.name} for {actual} physical damage!", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'death_ray':
                # 70% chance instant kill; remaining HP otherwise. Bosses immune to instant kill.
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if not is_boss and _rng.random() < 0.70:
                    target.hp = 0
                    target.alive = False
                    self.add_message(f"The {target.name} is slain instantly by the death ray!", 'success')
                    self._on_monster_killed(target)
                else:
                    dmg = max(1, target.max_hp // 2)
                    actual = target.take_damage(dmg)
                    if is_boss:
                        self.add_message(
                            f"The death ray strikes the {target.name} for {actual} damage! "
                            f"The creature is too powerful for an instant kill.", 'success')
                    else:
                        self.add_message(
                            f"The death ray grazes the {target.name} for {actual} damage!", 'success')
                    if not target.alive:
                        self._on_monster_killed(target)

            elif effect == 'polymorph_monster':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} resists the transformation!", 'warning')
                else:
                    import json
                    from monster import Monster
                    from paths import data_path
                    mp = data_path('data', 'monsters.json')
                    try:
                        with open(mp, encoding='utf-8') as f:
                            all_defs = json.load(f)
                        eligible = [k for k, v in all_defs.items()
                                    if v.get('min_level', 1) <= self.dungeon_level
                                    and k != target.kind and v.get('frequency', 1) > 0]
                        if eligible:
                            old_name = target.name
                            kind = _rng.choice(eligible)
                            defn = {**all_defs[kind], 'id': kind}
                            new_m = Monster(defn, target.x, target.y)
                            idx = self.monsters.index(target)
                            self.monsters[idx] = new_m
                            self.add_message(
                                f"The {old_name} warps into {self._a_or_an(new_m.name)}!", 'success'
                            )
                        else:
                            self.add_message("The polymorph wand finds no suitable form.", 'info')
                    except Exception:
                        self.add_message("The wand misfires!", 'warning')

            elif effect == 'fear_monster':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} resists the fear!", 'warning')
                else:
                    dur = self._wand_tier_duration(8, wand.quiz_tier)
                    target.add_effect('feared', dur)
                    target.ai_pattern = 'cowardly'
                    self.add_message(f"The {target.name} turns and flees in terror! ({dur} turns)", 'success')

            elif effect == 'charm_monster':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} is far too willful to charm!", 'warning')
                else:
                    dur = self._wand_tier_duration(20, wand.quiz_tier)
                    target.add_effect('charmed', dur)
                    target.ai_pattern = 'sessile'
                    self.add_message(f"The {target.name} gazes at you with adoration. ({dur} turns)", 'success')

            elif effect == 'poison_monster':
                dur = self._wand_tier_duration(12, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the poison!", 'warning')
                else:
                    target.add_effect('poisoned', dur)
                    self.add_message(f"The {target.name} writhes as poison courses through it! ({dur} turns)", 'success')

            elif effect == 'disease_monster':
                dur = self._wand_tier_duration(15, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the disease!", 'warning')
                else:
                    target.add_effect('diseased', dur)
                    actual = target.take_damage(max(1, target.max_hp // 5))
                    self.add_message(f"The {target.name} is wracked by disease! ({actual} dmg, {dur} turns)", 'success')
                    if not target.alive:
                        self._on_monster_killed(target)

            elif effect == 'curse_monster':
                dur = self._wand_tier_duration(20, wand.quiz_tier)
                sdur = self._wand_tier_duration(8, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the curse!", 'warning')
                else:
                    sdur = max(1, sdur // 2) if (getattr(target, 'is_boss', False) or target.max_hp > 500) else sdur
                    target.add_effect('cursed', dur)
                    target.add_effect('slowed', sdur)
                    self.add_message(f"Dark energy envelops the {target.name}! Cursed ({dur}t) and slowed ({sdur}t).", 'success')

            elif effect == 'teleport_monster':
                open_tiles = [(x, y)
                              for y in range(len(self.dungeon.tiles))
                              for x in range(len(self.dungeon.tiles[y]))
                              if self.dungeon.is_walkable(x, y)
                              and not any(m.alive and m.x == x and m.y == y for m in self.monsters)
                              and not any(p.alive and p.x == x and p.y == y for p in self.pets)
                              and (x, y) != (self.player.x, self.player.y)]
                if open_tiles:
                    tx, ty = _rng.choice(open_tiles)
                    old_name = target.name
                    target.x, target.y = tx, ty
                    self.add_message(f"The {old_name} vanishes in a flash of light!", 'success')

            elif effect == 'drain_life':
                from dice import roll
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else _rng.randint(3, 10), wand.quiz_tier)
                actual = target.take_damage(dmg)
                heal = min(actual, self.player.max_hp - self.player.hp)
                self.player.hp += heal
                self.add_message(
                    f"You drain {actual} life from the {target.name}! (+{heal} HP)", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

            elif effect == 'disintegrate':
                # 85% instant kill. Bosses immune to instant kill, take max_hp/3 instead.
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if not is_boss and _rng.random() < 0.85:
                    target.hp = 0
                    target.alive = False
                    self.add_message(f"The {target.name} is disintegrated!", 'success')
                    self._on_monster_killed(target)
                else:
                    actual = target.take_damage(target.max_hp // 3)
                    if is_boss:
                        self.add_message(
                            f"The {target.name} resists disintegration but takes {actual} damage!", 'success')
                    else:
                        self.add_message(
                            f"The {target.name} is partially disintegrated! ({actual} dmg)", 'success')
                    if not target.alive:
                        self._on_monster_killed(target)

            elif effect == 'weaken_monster':
                dur = self._wand_tier_duration(15, wand.quiz_tier)
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the weakening magic!", 'warning')
                elif target.attacks:
                    target.add_effect('weakened', dur)
                    self.add_message(f"The {target.name} looks visibly weaker! ({dur} turns)", 'success')
                else:
                    target.add_effect('weakened', dur)
                    self.add_message(f"The {target.name} seems diminished. ({dur} turns)", 'success')

            elif effect == 'drain_magic':
                target.status_effects.clear()
                self.add_message(f"The {target.name}'s magical effects are drained away!", 'success')

            elif effect == 'dispel_magic':
                target.status_effects.clear()
                self.add_message(f"All enchantments on the {target.name} are dispelled!", 'success')

        # ---- Effects that don't require a target OR handle mass effects ----
        if effect == 'boost_str':
            old = self.player.STR
            self.player.apply_stat_bonus('STR', 1)
            self.add_message(f"You feel powerful! STR: {old} -> {self.player.STR}", 'success')

        elif effect == 'boost_con':
            old = self.player.CON
            self.player.apply_stat_bonus('CON', 1)
            self.add_message(f"You feel hardy! CON: {old} -> {self.player.CON}", 'success')

        elif effect == 'boost_int':
            old = self.player.INT
            self.player.apply_stat_bonus('INT', 1)
            self.add_message(f"Your mind sharpens! INT: {old} -> {self.player.INT}", 'success')

        elif effect == 'shield_self':
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('shielded', dur)
            self.add_message(f"A shimmering barrier surrounds you! ({dur} turns)", 'success')

        elif effect == 'fire_shield':
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('fire_shield', dur)
            self.add_message(f"Flames swirl around you! Fire protection for {dur} turns.", 'success')

        elif effect == 'cold_shield':
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('cold_shield', dur)
            self.add_message(f"Frost encases you! Cold protection for {dur} turns.", 'success')

        elif effect == 'regeneration_self':
            dur = self._wand_tier_duration(30, wand.quiz_tier)
            self.player.add_effect('regenerating', dur)
            self.add_message(f"You feel your wounds slowly closing. ({dur} turns)", 'success')

        elif effect == 'reflect_self':
            dur = self._wand_tier_duration(20, wand.quiz_tier)
            self.player.add_effect('reflecting', dur)
            self.add_message(f"A reflective aura surrounds you! ({dur} turns)", 'success')

        elif effect == 'phase_self':
            dur = self._wand_tier_duration(15, wand.quiz_tier)
            self.player.add_effect('phasing', dur)
            self.add_message(f"You feel briefly incorporeal -- walls seem thin. ({dur} turns)", 'success')

        elif effect == 'detect_monsters':
            for m in self.monsters:
                if m.alive:
                    self.visible.add((m.x, m.y))
            self.add_message("You sense the presence of all nearby creatures!", 'success')

        elif effect == 'detect_treasure':
            for item in self.ground_items:
                self.dungeon.explored.add((item.x, item.y))
            self.add_message("A golden shimmer reveals hidden treasures!", 'success')

        elif effect == 'mapping':
            for y in range(self.dungeon.height):
                for x in range(self.dungeon.width):
                    self.dungeon.explored.add((x, y))
            self.add_message("The wand maps the entire dungeon level into your mind!", 'success')

        elif effect == 'clairvoyance':
            for y in range(len(self.dungeon.tiles)):
                for x in range(len(self.dungeon.tiles[y])):
                    self.dungeon.explored.add((x, y))
            self.add_message("Your mind expands -- you perceive the entire level!", 'success')

        elif effect == 'identify_item':
            unknown = [i for i in self.player.inventory if hasattr(i, 'identified') and not i.identified]
            if unknown:
                item = unknown[0]
                item.identified = True
                self.player.known_item_ids.add(item.id)
                self.add_message(f"The wand identifies: {item.name}!", 'success')
            else:
                self.add_message("Everything you carry is already known.", 'info')

        elif effect == 'enchant_weapon':
            from items import ENCHANT_CAP
            w = self.player.weapon or self.player.ranged_weapon
            if w:
                cap = ENCHANT_CAP.get('weapon', 5)
                if w.enchant_bonus < cap:
                    w.enchant_bonus += 1
                    self.add_message(f"Your {w.name} glows! Enchantment +{w.enchant_bonus}.", 'success')
                else:
                    self.add_message(f"Your {w.name} shudders but can hold no more enchantment.", 'info')
            else:
                self.add_message("You wield no weapon to enchant.", 'warning')

        elif effect == 'earthquake':
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            total_dmg = 0
            for m in visible_monsters:
                dmg = self._wand_tier_damage(_rng.randint(5, 20), wand.quiz_tier)
                actual = m.take_damage(dmg)
                total_dmg += actual
                if not m.alive:
                    self._on_monster_killed(m)
            self.add_message(f"The earth shakes! {len(visible_monsters)} creatures are battered. ({total_dmg} total dmg)", 'success')

        elif effect == 'explosion':
            from dice import roll
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                dmg = self._wand_tier_damage(roll(wand.power) if wand.power else _rng.randint(8, 24), wand.quiz_tier)
                actual = m.take_damage(dmg)
                if not m.alive:
                    self._on_monster_killed(m)
            self.add_message(f"A massive explosion engulfs the area! ({len(visible_monsters)} creatures hit)", 'success')

        elif effect == 'mass_confuse':
            dur = self._wand_tier_duration(12, wand.quiz_tier)
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                m.add_effect('confused', dur)
            self.add_message(f"A wave of confusion washes over {len(visible_monsters)} creatures! ({dur} turns)", 'success')

        elif effect == 'mass_sleep':
            dur = self._wand_tier_duration(10, wand.quiz_tier)
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                m.add_effect('sleeping', dur)
            self.add_message(f"All visible creatures slump into slumber! ({len(visible_monsters)} affected, {dur} turns)", 'success')

        elif effect == 'mass_slow':
            dur = self._wand_tier_duration(10, wand.quiz_tier)
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in visible_monsters:
                m.add_effect('slowed', dur)
            self.add_message(f"{len(visible_monsters)} creatures are slowed! ({dur} turns)", 'success')

        elif effect == 'time_stop':
            dur = self._wand_tier_duration(5, wand.quiz_tier)
            self.player.add_effect('time_stopped', dur)
            self.add_message(f"Time freezes! You have {dur} turns of free movement.", 'success')

        elif effect == 'wish':
            self.add_message("The wand glows brilliantly... but you cannot yet speak your wish.", 'info')

        elif effect == 'iron_mortar':
            # Baba Yaga's Iron Mortar: the effect is never the same twice
            _chaos = _rng.choice([
                ('heal',       lambda: (self.player.restore_hp(25),
                                        self.add_message("Chaotic healing washes over you! (+25 HP)", 'success'))),
                ('teleport',   lambda: (self._teleport_player(),
                                        self.add_message("The mortar warps you across the level!", 'warning'))),
                ('haste',      lambda: (self.player.add_effect('hasted', 10),
                                        self.add_message("Baba Yaga's magic hastens your step!", 'success'))),
                ('confusion',  lambda: (self.player.add_effect('confused', 8),
                                        self.add_message("The mortar's chaos clouds your mind!", 'danger'))),
                ('mass_sleep', lambda: (
                    [m.add_effect('sleeping', 12) for m in self.monsters if m.alive and (m.x, m.y) in self.visible],
                    self.add_message("The mortar grinds out a sleep-fog over the room!", 'success'))),
                ('regen',      lambda: (self.player.add_effect('regenerating', 20),
                                        self.add_message("Ground-up hero bones restore your vitality!", 'success'))),
                ('blast',      lambda: [
                    (m.take_damage(_rng.randint(5, 15)), self._on_monster_killed(m) if not m.alive else None)
                    for m in list(self.monsters) if m.alive and (m.x, m.y) in self.visible
                ] or self.add_message("Chaotic energy blasts all visible enemies!", 'success')),
            ])
            _chaos[1]()
            self.add_message("Baba Yaga's Iron Mortar churns with unpredictable magic!", 'warning')

        # -- Tier 5 wand effects -------------------------------------------
        elif effect == 'nova':
            from dice import roll as _roll
            all_monsters = [m for m in self.monsters if m.alive]
            if not all_monsters:
                self.add_message("The wand fires but no creatures are present!", 'info')
            else:
                total = 0
                for m in all_monsters:
                    dmg = self._wand_tier_damage(_roll(wand.power) if wand.power else _rng.randint(15, 30), wand.quiz_tier)
                    actual = m.take_damage(dmg)
                    total += actual
                    if not m.alive:
                        self._on_monster_killed(m)
                self.add_message(
                    f"A nova of stellar fire engulfs the entire level! "
                    f"({len(all_monsters)} creatures hit, {total} total damage)", 'success'
                )

        elif effect == 'life_transfer':
            target = self._nearest_visible_monster()
            if not target:
                self.add_message("No visible target for life transfer.", 'warning')
            else:
                drain = max(1, target.hp // 2)
                actual = target.take_damage(drain)
                self.player.restore_hp(actual)
                self.add_message(
                    f"Life force drains from the {target.name}! "
                    f"({actual} drained, +{actual} HP to you)", 'success'
                )
                if not target.alive:
                    self._on_monster_killed(target)

        elif effect == 'abjuration':
            target = self._nearest_visible_monster()
            # Strip all effects from target
            cleared_monster = 0
            if target:
                cleared_monster = len(target.status_effects)
                target.status_effects.clear()
            # Purge player debuffs
            from status_effects import DEBUFFS
            cleared_player = [e for e in list(self.player.status_effects) if e in DEBUFFS]
            for e in cleared_player:
                del self.player.status_effects[e]
            if target and cleared_monster:
                self.add_message(
                    f"Abjuration strips {cleared_monster} effect(s) from the {target.name}!", 'success'
                )
            if cleared_player:
                self.add_message(
                    f"Your afflictions dissolve: {', '.join(cleared_player)}.", 'success'
                )
            if not target and not cleared_player:
                self.add_message("Nothing to abjure.", 'info')

        elif effect == 'knock':
            # Open nearest locked container within 5 tiles
            px, py = self.player.x, self.player.y
            best, best_d = None, 999
            for item in self.ground_items:
                if isinstance(item, Container) and getattr(item, 'locked', False):
                    d = abs(item.x - px) + abs(item.y - py)
                    if d <= 5 and d < best_d:
                        best, best_d = item, d
            if best:
                best.locked = False
                self.add_message(f"Click! The {best.name} unlocks!", 'success')
            else:
                self.add_message("The wand hums but finds nothing locked nearby.", 'info')

        elif effect == 'turn_undead':
            from dice import roll as _roll_tu
            base_dmg = self._wand_tier_damage(_roll_tu(wand.power) if wand.power else 8, wand.quiz_tier)
            _UNDEAD_WORDS = {'skeleton', 'zombie', 'ghost', 'wraith', 'lich', 'wight',
                             'spectre', 'vampire', 'mummy', 'revenant', 'death', 'undead',
                             'ghoul', 'ghast', 'shade', 'banshee', 'draugr', 'barrow',
                             'bone', 'corpse', 'vrykolakas', 'strigoi', 'mohrg', 'demi_lich'}
            undead = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible
                      and any(w in m.kind.lower() for w in _UNDEAD_WORDS)]
            if undead:
                for m in undead:
                    actual = m.take_damage(base_dmg, 'holy')
                    m.add_effect('feared', self._wand_tier_duration(8, wand.quiz_tier))
                    if not m.alive:
                        self._on_monster_killed(m)
                self.add_message(
                    f"Holy light blazes! {len(undead)} undead take {base_dmg} holy damage and flee!",
                    'success')
            else:
                # Minor effect on non-undead: flash of light
                self.add_message("Holy light flares but no undead are present.", 'info')

        elif effect == 'wonder':
            _WONDER_EFFECTS = [
                ('heal', lambda: (self.player.restore_hp(15),
                    self.add_message("The wand heals you for 15 HP!", 'success'))),
                ('haste', lambda: (self.player.add_effect('hasted', 8),
                    self.add_message("The wand makes you supernaturally fast!", 'success'))),
                ('confuse', lambda: (
                    [m.add_effect('confused', 8) for m in self.monsters
                     if m.alive and (m.x, m.y) in self.visible],
                    self.add_message("A wave of confusion erupts!", 'success'))),
                ('fireball', lambda: (
                    [m.take_damage(self._wand_tier_damage(_rng.randint(8, 20), wand.quiz_tier), 'fire')
                     for m in self.monsters if m.alive and (m.x, m.y) in self.visible],
                    self.add_message("A burst of flame erupts from the wand!", 'success'))),
                ('teleport', lambda: (self._teleport_player(),
                    self.add_message("The wand teleports you randomly!", 'warning'))),
                ('shield', lambda: (self.player.add_effect('shielded', 10),
                    self.add_message("A protective barrier appears!", 'success'))),
                ('sleep', lambda: (
                    [m.add_effect('sleeping', 8) for m in self.monsters
                     if m.alive and (m.x, m.y) in self.visible],
                    self.add_message("A wave of slumber washes out!", 'success'))),
                ('invisible', lambda: (self.player.add_effect('invisible', 10),
                    self.add_message("You vanish from sight!", 'success'))),
                ('lightning', lambda: (
                    (lambda t: (t.take_damage(self._wand_tier_damage(_rng.randint(10, 25), wand.quiz_tier), 'lightning'),
                     self.add_message(f"Lightning zaps the {t.name}!", 'success'),
                     None if t.alive else self._on_monster_killed(t))
                    )(self._nearest_visible_monster()) if self._nearest_visible_monster() else
                    self.add_message("Lightning crackles harmlessly.", 'info'))),
                ('regen', lambda: (self.player.add_effect('regenerating', 15),
                    self.add_message("Your wounds begin to close on their own!", 'success'))),
            ]
            _, fn = _rng.choice(_WONDER_EFFECTS)
            fn()
            self.add_message("The wand of wonder crackles with chaotic energy!", 'warning')

    # ------------------------------------------------------------------
    # Spell menu  (m key -- learned spells, cast with science chain quiz)
    # ------------------------------------------------------------------

    def _invoke_spell(self, spell_id: str):
        spell = LEARNABLE_SPELLS.get(spell_id)
        if not spell:
            return
        mp_cost = spell['mp_cost']
        if self.player.mp < mp_cost:
            self.add_message(
                f"Not enough MP to cast {spell['name']}! "
                f"(need {mp_cost}, have {self.player.mp})", 'warning')
            self.state = STATE_PLAYER
            return

        # For targeted spells, enter targeting mode
        if spell.get('needs_target'):
            self._pending_spell = spell
            self._pending_spell_id = spell_id
            px, py = self.player.x, self.player.y
            candidates = [
                m for m in self.monsters
                if m.alive and (m.x, m.y) in self.visible
            ]
            candidates.sort(key=lambda m: abs(m.x - px) + abs(m.y - py))
            if not candidates:
                self.add_message("No visible target for this spell.", 'warning')
                self.state = STATE_PLAYER
                return
            self.player.mp -= mp_cost
            self._power_targeting = True
            self._pending_power = f'spell_{spell_id}'
            self._target_candidates = candidates
            self._target_idx = 0
            self.target_cursor_x = candidates[0].x
            self.target_cursor_y = candidates[0].y
            self.state = STATE_TARGET
            self.add_message(
                f"Casting {spell['name']}... select target! Arrows to aim, ENTER to cast.",
                'info')
            return

        # Non-targeted spells: go straight to quiz
        self.player.mp -= mp_cost
        self._start_spell_quiz(spell, spell_id, target=None)

    def _start_spell_quiz(self, spell, spell_id, target):
        """Start the science escalator chain quiz for a spell."""
        self.state = STATE_QUIZ
        self.quiz_title = f"CAST {spell['name'].upper()} -- SCIENCE"

        def on_complete(result):
            chain = result.score
            self.state = STATE_PLAYER
            if chain == 0:
                self.add_message(f"The {spell['name']} fizzles... (MP wasted)", 'warning')
            else:
                _snd.play('spell_cast')
                self._apply_spell_effect(spell, chain, target)
                _qs_spell = getattr(self, 'quirk_system', None)
                if _qs_spell:
                    hp_pct = self.player.hp / max(1, self.player.max_hp)
                    _qs_spell.on_spell_cast(hp_pct)
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='escalator_chain',
            subject='science',
            tier=spell['quiz_tier'],
            callback=on_complete,
            max_chain=5,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('science'),
            base_seconds=self.player.get_quiz_timer('science'),
        )

    # Spell chain multipliers — same philosophy as weapon chain multipliers
    _SPELL_CHAIN_MULTS = [0.5, 1.0, 1.8, 2.8, 4.0]

    def _spell_damage(self, base_dmg: int, chain: int) -> int:
        """Scale spell damage by chain multiplier AND INT."""
        mult = self._SPELL_CHAIN_MULTS[min(chain - 1, len(self._SPELL_CHAIN_MULTS) - 1)]
        return max(1, int(base_dmg * mult * (1.0 + self.player.INT * 0.1)))

    def _apply_spell_effect(self, spell: dict, chain: int, target=None):
        """Apply a learned spell's effect. Chain 1-5 scales damage/duration."""
        effect = spell['effect']
        power  = spell.get('power', '')

        # Scale duration with chain (utility/buff spells)
        chain_scale = chain / 5.0   # 0.2 .. 1.0

        # Handle the two spell-specific effects not in wand system
        if effect == 'displacement_self':
            dur = max(5, int(20 * chain_scale))
            self.player.add_effect('displacement', dur)
            self.add_message(f"Your image displaces! ({dur} turns)", 'success')
            return

        if effect == 'mass_ice':
            from dice import roll
            base_dmg = roll(power) if power else 10
            scaled   = self._spell_damage(base_dmg, chain)
            hit = 0
            for m in list(self.monsters):
                if m.alive and (m.x, m.y) in self.visible:
                    m.take_damage(scaled, 'cold')
                    if not m.alive:
                        self._on_monster_killed(m)
                    hit += 1
            self.add_message(
                f"Ice Storm! {hit} monsters take {scaled} cold dmg (chain {chain})", 'success')
            return

        if effect == 'mass_fire':
            from dice import roll
            base_dmg = roll(power) if power else 10
            scaled   = self._spell_damage(base_dmg, chain)
            hit = 0
            for m in list(self.monsters):
                if m.alive and (m.x, m.y) in self.visible:
                    actual = m.take_damage(scaled, 'fire')
                    if not m.alive:
                        self._on_monster_killed(m)
                    hit += 1
            self.add_message(
                f"Fireball! {hit} monsters take {scaled} fire dmg (chain {chain})", 'success')
            return

        if effect == 'knock_spell':
            # Find nearest locked container within 3 tiles
            px, py = self.player.x, self.player.y
            best, best_d = None, 999
            for item in self.ground_items:
                if isinstance(item, Container) and getattr(item, 'locked', False):
                    d = abs(item.x - px) + abs(item.y - py)
                    if d <= 3 and d < best_d:
                        best, best_d = item, d
            if best:
                best.locked = False
                self.add_message(f"Click! The {best.name} unlocks magically! (chain {chain})", 'success')
            else:
                self.add_message("No locked containers nearby to open.", 'info')
            return

        if effect == 'detect_monsters_spell':
            dur = max(5, int(20 * chain_scale))
            self.player.add_effect('clairvoyant', dur)
            count = sum(1 for m in self.monsters if m.alive)
            self.add_message(
                f"Your senses expand -- {count} creatures revealed for {dur} turns! (chain {chain})", 'success')
            return

        if effect == 'teleport_away_spell':
            # Target nearest visible monster, or self-teleport if none
            # Bosses CAN be teleported — they stay aggro'd and come back
            target_m = self._nearest_visible_monster()
            if target_m:
                floors = [(x, y) for y in range(self.dungeon.height)
                          for x in range(self.dungeon.width)
                          if self.dungeon.is_walkable(x, y)
                          and (x, y) != (self.player.x, self.player.y)
                          and not any(m.alive and m.x == x and m.y == y for m in self.monsters)]
                if floors:
                    nx, ny = random.choice(floors)
                    target_m.x, target_m.y = nx, ny
                    self.add_message(
                        f"The {target_m.name} vanishes in a flash of light! (chain {chain})", 'success')
                else:
                    self.add_message("The spell fizzles -- no safe destination found.", 'warning')
            else:
                # No visible monsters — teleport self
                self._teleport_player()
                self.add_message(f"You teleport to a new location! (chain {chain})", 'success')
            return

        # Scale extra_heal duration/amount
        if effect == 'extra_heal':
            from dice import roll
            base = roll(power) if power else 8
            healed = self._spell_damage(base, chain)
            self.player.restore_hp(healed)
            self.add_message(f"You are healed for {healed} HP! (chain {chain})", 'success')
            return

        # Army of Darkness: summon undead pet horde
        if effect == 'summon_undead_horde':
            count = max(3, int(5 * chain_scale))
            self._summon_undead_pets(count)
            self.add_message(
                f"The dead rise to serve you! {count} undead minions summoned! (chain {chain})",
                'success')
            return

        # Cleanse: remove one negative status effect
        if effect == 'cleanse_self':
            from status_effects import DEBUFFS
            active = [e for e in self.player.status_effects if e in DEBUFFS]
            if active:
                removed = active[0]
                self.player.status_effects.pop(removed, None)
                self.add_message(f"Cleansed! {removed.title()} removed.", 'success')
            else:
                self.add_message("You have no ailments to cleanse.", 'info')
            return

        # Empower: next melee attack deals 3x damage
        if effect == 'empower_next':
            self.player.status_effects['empowered'] = 1
            self.add_message("Arcane power surges through your weapon! Next attack deals 3x damage!", 'success')
            return

        # Summon Guardian: temporary pet ally
        if effect == 'summon_guardian':
            from pet_system import Pet, random_species
            px, py = self.player.x, self.player.y
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    nx, ny = px + dx, py + dy
                    if (nx, ny) == (px, py):
                        continue
                    if not self.dungeon.is_walkable(nx, ny):
                        continue
                    if any(m.alive and m.x == nx and m.y == ny for m in self.monsters):
                        continue
                    species = random_species()
                    pet = Pet(species, nx, ny)
                    pet.level = max(1, self.dungeon_level // 3)
                    pet._refresh_stats()
                    self.pets.append(pet)
                    self.add_message(
                        f"{self._a_or_an(pet.name).capitalize()} materializes to guard you! (chain {chain})", 'success')
                    return
            self.add_message("No room to summon a guardian.", 'warning')
            return

        # Meteor: massive AoE fire damage
        if effect == 'meteor':
            from dice import roll as _roll_m
            base_dmg = _roll_m(power) if power else 20
            scaled = self._spell_damage(base_dmg, chain)
            visible_monsters = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            kills = 0
            for m in visible_monsters:
                actual = m.take_damage(scaled, 'fire')
                if not m.alive:
                    self._on_monster_killed(m)
                    kills += 1
            self.add_message(
                f"A meteor crashes down! {len(visible_monsters)} creatures take {scaled} fire damage! "
                f"({kills} slain, chain {chain})", 'success')
            return

        # Time Freeze: freeze all monsters
        if effect == 'time_freeze':
            dur = max(3, int(5 * chain_scale))
            count = 0
            for m in self.monsters:
                if m.alive:
                    m.add_effect('paralyzed', dur)
                    count += 1
            self.add_message(
                f"TIME FREEZES! {count} creatures locked in place for {dur} turns! (chain {chain})", 'success')
            return

        # Light spell: reveal tiles in a radius (chain scales radius)
        if effect == 'light':
            base_radius = 15
            radius = max(5, int(base_radius * chain_scale))
            px, py = self.player.x, self.player.y
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx*dx + dy*dy <= radius*radius:
                        nx, ny = px + dx, py + dy
                        if self.dungeon.in_bounds(nx, ny):
                            self.dungeon.explored.add((nx, ny))
            self.add_message(
                f"Brilliant light floods the area! (radius {radius}, chain {chain})", 'success')
            return

        # --- 2026 SPELL EXPANSION: new self/AOE handlers --------------------

        # Cone of Cold — AOE cold damage to all visible monsters within 5 tiles
        if effect == 'cone_of_cold':
            from dice import roll as _roll_co
            base_dmg = _roll_co(power) if power else 14
            scaled = self._spell_damage(base_dmg, chain)
            px, py = self.player.x, self.player.y
            hit = 0
            for m in list(self.monsters):
                if not m.alive: continue
                if (m.x, m.y) not in self.visible: continue
                if max(abs(m.x - px), abs(m.y - py)) > 5: continue
                m.take_damage(scaled, 'cold')
                # Apply frozen briefly
                dur = max(2, int(4 * chain_scale))
                m.add_effect('frozen', dur)
                if not m.alive:
                    self._on_monster_killed(m)
                hit += 1
            self.add_message(
                f"A cone of cold blasts outward! {hit} creatures take {scaled} cold dmg + frozen! (chain {chain})", 'success')
            return

        # Mass Polymorph — polymorph every visible monster
        if effect == 'mass_polymorph':
            count = 0
            for m in list(self.monsters):
                if not m.alive: continue
                if (m.x, m.y) not in self.visible: continue
                if getattr(m, 'is_boss', False): continue   # bosses immune
                # Crude polymorph: weaken HP + AC + speed to a "small animal"
                m.max_hp = max(1, m.max_hp // 4)
                m.hp = min(m.hp, m.max_hp)
                m.thac0 = min(20, m.thac0 + 8)
                m.speed = min(m.speed, 6)
                count += 1
            self.add_message(
                f"Mass Polymorph! {count} creatures become small animals! (chain {chain})", 'success')
            return

        # Meteor Swarm — multiple meteors, each hitting all visible
        if effect == 'meteor_swarm':
            from dice import roll as _roll_ms
            shots = max(2, chain)   # chain 1 = 2 meteors, chain 5 = 5 meteors
            base_dmg = _roll_ms(power) if power else 18
            scaled_per = self._spell_damage(base_dmg, chain)
            total = 0
            for _ in range(shots):
                hit = 0
                for m in list(self.monsters):
                    if not m.alive: continue
                    if (m.x, m.y) not in self.visible: continue
                    m.take_damage(scaled_per, 'fire')
                    if not m.alive:
                        self._on_monster_killed(m)
                    hit += 1
                total += hit
            self.add_message(
                f"Meteor Swarm! {shots} meteors fall — {total} hits, {scaled_per} fire dmg each! (chain {chain})", 'success')
            return

        # Storm of Vengeance — chain lightning to ALL visible monsters
        if effect == 'storm_of_vengeance':
            from dice import roll as _roll_sv
            base_dmg = _roll_sv(power) if power else 20
            scaled = self._spell_damage(base_dmg, chain)
            hit = 0
            for m in list(self.monsters):
                if not m.alive: continue
                if (m.x, m.y) not in self.visible: continue
                m.take_damage(scaled, 'lightning')
                # Stun chance from the thunder
                if random.random() < 0.40:
                    m.add_effect('stunned', max(2, int(4 * chain_scale)))
                if not m.alive:
                    self._on_monster_killed(m)
                hit += 1
            self.add_message(
                f"Storm of Vengeance breaks overhead! {hit} creatures take {scaled} lightning + stun! (chain {chain})", 'success')
            return

        # Gate — summon a higher-tier guardian pet (boosted vs summon_guardian)
        if effect == 'gate':
            from pet_system import Pet, random_species
            px, py = self.player.x, self.player.y
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    nx, ny = px + dx, py + dy
                    if (nx, ny) == (px, py): continue
                    if not self.dungeon.is_walkable(nx, ny): continue
                    if any(m.alive and m.x == nx and m.y == ny for m in self.monsters): continue
                    species = random_species()
                    pet = Pet(species, nx, ny)
                    pet.level = max(3, self.dungeon_level // 2)   # ~2x summon_guardian level
                    pet._refresh_stats()
                    pet.hp = pet.max_hp
                    self.pets.append(pet)
                    self.add_message(
                        f"A gate opens! {self._a_or_an(pet.name).capitalize()} (lv {pet.level}) "
                        f"steps through to serve you! (chain {chain})", 'success')
                    return
            self.add_message("The gate flickers — no room nearby to manifest.", 'warning')
            return

        # Scale status durations for self-buff spells
        _SELF_BUFF_DURATIONS = {
            'shield_self':       ('shielded',    12),
            'haste_self':        ('hasted',      10),
            'invisibility_self': ('invisible',   15),
            'reflect_self':      ('reflecting',  15),
            # 2026 spell expansion — self buffs that re-use existing statuses
            'stoneskin_self':    ('shielded',    25),    # longer shielded; "skin of stone"
            'counterspell_self': ('magic_resist', 12),   # anti-spell shield
            'foresight_self':    ('clairvoyant', 30),    # long detect-all
            'resurrection_self': ('life_save',   50),    # one-shot revive
            'greater_invis_self': ('invisible',  25),    # longer invis
        }
        if effect in _SELF_BUFF_DURATIONS:
            eff_name, base_dur = _SELF_BUFF_DURATIONS[effect]
            dur = max(2, int(base_dur * chain_scale))
            self.player.add_effect(eff_name, dur)
            self.add_message(
                f"{spell['name']} -- {eff_name} for {dur} turns! (chain {chain})", 'success')
            return

        # Targeted spells -- handle directly so we use the pre-found target
        if target is not None:
            from dice import roll as _roll
            if effect == 'magic_missile':
                # Fire one missile per chain link (1-5 missiles)
                missiles = max(1, chain)
                total_dmg = 0
                for _ in range(missiles):
                    if not target.alive:
                        break
                    base_dmg = _roll(power) if power else 4
                    per_missile = self._int_scaled_damage(base_dmg)
                    target.hp = max(0, target.hp - per_missile)
                    if target.hp == 0:
                        target.alive = False
                    total_dmg += per_missile
                self.add_message(
                    f"{missiles} magic missile{'s' if missiles > 1 else ''} "
                    f"strike{'s' if missiles == 1 else ''} the {target.name} "
                    f"for {total_dmg} total damage! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'fire_bolt':
                base_dmg = _roll(power) if power else 8
                scaled = self._spell_damage(base_dmg, chain)
                actual = target.take_damage(scaled, 'fire')
                self.add_message(
                    f"A bolt of fire strikes the {target.name} for {actual} damage! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'lightning_bolt':
                from combat import get_line_tiles
                base_dmg = _roll(power) if power else 10
                scaled = self._spell_damage(base_dmg, chain)
                px, py = self.player.x, self.player.y
                line = get_line_tiles(px, py, target.x, target.y)
                line_set = set(line)
                line_hits = [m for m in self.monsters
                             if m.alive and (m.x, m.y) in line_set and (m.x, m.y) in self.visible]
                stun_dur = max(1, int(3 * chain_scale))
                for lm in line_hits:
                    actual = lm.take_damage(scaled, 'lightning')
                    if actual > 0:
                        sd, sr = self._boss_resist_cc(lm, stun_dur)
                        if not sr:
                            lm.add_effect('stunned', sd)
                    if not lm.alive:
                        self._on_monster_killed(lm)
                if len(line_hits) > 1:
                    self.add_message(
                        f"Lightning arcs through {len(line_hits)} creatures for {scaled} damage! (chain {chain})", 'success')
                elif line_hits:
                    self.add_message(
                        f"Lightning strikes the {line_hits[0].name} for {scaled} damage! (chain {chain})", 'success')
                else:
                    self.add_message("The lightning dissipates harmlessly.", 'info')
            elif effect == 'sleep_monster':
                dur = max(2, int(6 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the sleep! (chain {chain})", 'warning')
                else:
                    target.add_effect('sleeping', dur)
                    self.add_message(f"The {target.name} falls asleep for {dur} turns! (chain {chain})", 'success')
            elif effect == 'confuse_monster':
                dur = max(2, int(10 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the confusion! (chain {chain})", 'warning')
                else:
                    target.add_effect('confused', dur)
                    self.add_message(f"The {target.name} is confused for {dur} turns! (chain {chain})", 'success')
            elif effect == 'paralyze_monster':
                dur = max(2, int(8 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} resists the paralysis! (chain {chain})", 'warning')
                else:
                    target.add_effect('paralyzed', dur)
                    self.add_message(f"The {target.name} is paralyzed for {dur} turns! (chain {chain})", 'success')
            elif effect == 'aard_blast':
                base_dmg = _roll(power) if power else 10
                scaled = self._spell_damage(base_dmg, chain)
                actual = target.take_damage(scaled)
                stun = max(1, int(3 * chain_scale))
                stun, sr = self._boss_resist_cc(target, stun)
                if not sr:
                    target.add_effect('stunned', stun)
                self.add_message(
                    f"Aard! A telekinetic blast strikes the {target.name} for {actual} damage"
                    + (" and stuns it!" if not sr else "!") + f" (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'slow_monster':
                dur = max(2, int(8 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the slowing magic! (chain {chain})", 'warning')
                else:
                    target.add_effect('slowed', dur)
                    self.add_message(f"The {target.name} is slowed for {dur} turns! (chain {chain})", 'success')
            elif effect == 'teleport_self':
                self._teleport_player()
                self.add_message("The Elder Blood bends space around you!", 'success')
            elif effect == 'smite':
                base_dmg = _roll(power) if power else 20
                scaled = self._spell_damage(base_dmg, chain)
                target.hp = max(0, target.hp - scaled)  # holy — bypasses resistances
                if target.hp == 0:
                    target.alive = False
                self.add_message(
                    f"Holy fire smites the {target.name} for {scaled} damage! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'slow_monster_spell':
                dur = max(4, int(10 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(f"The {target.name} shrugs off the slowing magic! (chain {chain})", 'warning')
                else:
                    target.add_effect('slowed', dur)
                    self.add_message(f"The {target.name} is slowed for {dur} turns! (chain {chain})", 'success')
            elif effect == 'acid_arrow':
                base_dmg = _roll(power) if power else 8
                scaled = self._spell_damage(base_dmg, chain)
                actual = target.take_damage(scaled, 'acid')
                dot_dur = max(2, int(5 * chain_scale))
                dot_dur, dot_resisted = self._boss_resist_cc(target, dot_dur)
                if not dot_resisted:
                    target.add_effect('poisoned', dot_dur)
                self.add_message(
                    f"An acid arrow strikes the {target.name} for {actual} damage!"
                    + (f" Acid burns for {dot_dur} turns!" if not dot_resisted else " It resists the acid burn!")
                    + f" (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'drain_life_spell':
                base_dmg = _roll(power) if power else 10
                scaled = self._spell_damage(base_dmg, chain)
                actual = target.take_damage(scaled)
                healed = self.player.restore_hp(actual)
                self.add_message(
                    f"You drain {actual} life from the {target.name} and heal {healed} HP! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'fear_monster_spell':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} is too powerful to frighten!", 'warning')
                else:
                    dur = max(3, int(10 * chain_scale))
                    target.add_effect('feared', dur)
                    target.ai_pattern = 'cowardly'
                    self.add_message(
                        f"The {target.name} turns and flees in terror for {dur} turns! (chain {chain})", 'success')
            elif effect == 'polymorph_spell':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if is_boss:
                    self.add_message(f"The {target.name} resists the polymorph!", 'warning')
                else:
                    import json as _pjson
                    from monster import Monster as _PMon
                    from paths import data_path as _pdp
                    try:
                        with open(_pdp('data', 'monsters.json'), encoding='utf-8') as _pf:
                            _all_defs = _pjson.load(_pf)
                        # High chain biases toward weaker result
                        max_ml = max(1, target.min_level + 10 - chain * 3)
                        eligible = [k for k, v in _all_defs.items()
                                    if v.get('min_level', 1) <= max_ml
                                    and k != target.kind and v.get('frequency', 1) > 0]
                        if not eligible:
                            eligible = [k for k, v in _all_defs.items()
                                        if k != target.kind and v.get('frequency', 1) > 0]
                        old_name = target.name
                        kind = random.choice(eligible)
                        defn = {**_all_defs[kind], 'id': kind}
                        new_m = _PMon(defn, target.x, target.y)
                        idx = self.monsters.index(target)
                        self.monsters[idx] = new_m
                        self.add_message(
                            f"The {old_name} warps into {self._a_or_an(new_m.name)}! (chain {chain})", 'success')
                    except Exception:
                        self.add_message("The polymorph spell fizzles!", 'warning')
            elif effect == 'disintegrate_spell':
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                # Chain-scaling kill chance: 30/45/60/75/90%
                kill_chance = 0.15 + chain * 0.15  # 0.30 at chain 1 .. 0.90 at chain 5
                if not is_boss and random.random() < kill_chance:
                    target.hp = 0
                    target.alive = False
                    self.add_message(
                        f"The {target.name} is disintegrated! (chain {chain}, {int(kill_chance*100)}%)", 'success')
                    self._on_monster_killed(target)
                else:
                    base_dmg = _roll(power) if power else 20
                    scaled = self._spell_damage(base_dmg, chain)
                    actual = target.take_damage(scaled)
                    if is_boss:
                        self.add_message(
                            f"The {target.name} resists disintegration but takes {actual} damage! (chain {chain})", 'success')
                    else:
                        self.add_message(
                            f"The {target.name} partially resists! {actual} damage! (chain {chain}, {int(kill_chance*100)}% missed)", 'warning')
                    if not target.alive:
                        self._on_monster_killed(target)
            # --- 2026 SPELL EXPANSION: new targeted handlers --------------
            elif effect == 'frost_touch':
                base_dmg = _roll(power) if power else 4
                scaled = self._spell_damage(base_dmg, chain)
                actual = target.take_damage(scaled, 'cold')
                # Slow chance from the frost
                if random.random() < 0.50:
                    dur = max(2, int(5 * chain_scale))
                    dur, _ = self._boss_resist_cc(target, dur)
                    target.add_effect('slowed', dur)
                self.add_message(
                    f"Frost touch chills the {target.name} for {actual} cold dmg! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)
            elif effect == 'chain_lightning_jump':
                # Initial hit + jumps to nearest 2 monsters within 3 tiles at reduced dmg
                base_dmg = _roll(power) if power else 12
                scaled = self._spell_damage(base_dmg, chain)
                hit_targets = [target]
                target.take_damage(scaled, 'lightning')
                if not target.alive:
                    self._on_monster_killed(target)
                # Find nearest 2 monsters within 3 tiles of ANY already-hit
                remaining = [m for m in self.monsters
                             if m.alive and m not in hit_targets
                             and any(abs(m.x - h.x) + abs(m.y - h.y) <= 3
                                     for h in hit_targets)]
                remaining.sort(key=lambda m: abs(m.x - target.x) + abs(m.y - target.y))
                for jump_n, jm in enumerate(remaining[:2], start=1):
                    arc_dmg = max(1, int(scaled * (0.75 if jump_n == 1 else 0.50)))
                    jm.take_damage(arc_dmg, 'lightning')
                    if not jm.alive:
                        self._on_monster_killed(jm)
                    hit_targets.append(jm)
                self.add_message(
                    f"Chain Lightning arcs through {len(hit_targets)} targets! (chain {chain})", 'success')
            elif effect == 'banishment':
                # Returns summoned/extraplanar entities — fey, demon, celestial, elemental
                tags = set(getattr(target, 'tags', []))
                BANISHABLE = {'fey', 'demon', 'celestial', 'elemental'}
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                if (tags & BANISHABLE) and not is_boss:
                    target.alive = False
                    target.hp = 0
                    # No treasure / on_killed callback — banished, not slain
                    self.add_message(
                        f"The {target.name} is banished back to its home plane! (chain {chain})", 'success')
                elif is_boss:
                    self.add_message(
                        f"The {target.name} is too anchored to this plane to banish.", 'warning')
                else:
                    # Non-extraplanar: brief paralyze as a consolation
                    dur = max(2, int(4 * chain_scale))
                    target.add_effect('paralyzed', dur)
                    self.add_message(
                        f"The {target.name} is a creature of this world — frozen in dread for {dur} turns instead. (chain {chain})", 'warning')
            elif effect == 'power_word_kill':
                # Instakill if target HP at or below threshold; threshold scales
                # with player INT and chain. Bosses immune.
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                threshold = self.player.INT * chain * 4
                if not is_boss and target.hp <= threshold:
                    target.alive = False
                    target.hp = 0
                    self.add_message(
                        f"POWER WORD: KILL! The {target.name} drops dead. (chain {chain}, threshold {threshold} HP)", 'success')
                    self._on_monster_killed(target)
                elif is_boss:
                    self.add_message(
                        f"The {target.name} resists the death-word but staggers!", 'warning')
                    target.take_damage(self.player.INT * chain)
                else:
                    self.add_message(
                        f"The {target.name} ({target.hp} HP) is too strong for the death-word "
                        f"(threshold {threshold}). (chain {chain})", 'warning')
            elif effect == 'imprisonment':
                # Very long paralyze — effectively removes target from combat
                is_boss = getattr(target, 'is_boss', False) or target.max_hp > 500
                dur = max(15, int(60 * chain_scale))
                dur, resisted = self._boss_resist_cc(target, dur)
                if resisted:
                    self.add_message(
                        f"The {target.name} resists imprisonment! (chain {chain})", 'warning')
                else:
                    target.add_effect('paralyzed', dur)
                    self.add_message(
                        f"The {target.name} is sealed in arcane stone for {dur} turns! (chain {chain})", 'success')
            else:
                # Fallback: generic targeted damage
                from dice import roll as _r
                scaled = max(1, int((_r(power) if power else 6) * chain_scale))
                actual = target.take_damage(scaled)
                self.add_message(f"The {effect.replace('_', ' ')} hits the {target.name} for {actual} dmg! (chain {chain})", 'success')
                if not target.alive:
                    self._on_monster_killed(target)

    # ------------------------------------------------------------------
    # Scroll reading  (s key -- grammar quiz; see ``Game._SCROLL_TABS``)
    # ------------------------------------------------------------------

    def _read_scroll(self, scroll: 'Scroll'):
        display = self._display_name(scroll)
        self.quiz_title = f"READING {display.upper()}  --  GRAMMAR"
        self.state = STATE_QUIZ
        _was_identified_before = getattr(scroll, 'identified', False) or \
            scroll.id in self.player.known_item_ids

        def on_complete(result):
            self.state = STATE_PLAYER

            if not result.success:
                # Quest scrolls (single-copy) survive a bad read AND keep their
                # mystery — the scroll's purpose is too heavy to be uncovered
                # by a half-read. Each one gets its own lore-flavored refusal.
                if getattr(scroll, 'single_copy', False):
                    if scroll.id == 'scroll_lake_of_fire':
                        self.add_message(
                            "The words swim across the page. They are not for this hour, "
                            "not for this place. The scroll's heat fades back to stillness.",
                            'warning')
                    elif scroll.id == 'scroll_deaths_bane':
                        self.add_message(
                            "The names of Death grow heavy on the page. Steady your breath. "
                            "Try again when the words will hold.", 'warning')
                    else:
                        self.add_message(
                            "The page resists you. Its time is not now.", 'warning')
                    self._advance_turn()
                    return
                scroll.identified = True
                self.player.known_item_ids.add(scroll.id)
                self.player.remove_from_inventory(scroll)
                self.add_message(
                    "You stumble over the words -- the scroll crumbles unread.", 'warning'
                )
                self._advance_turn()
                return

            scroll.identified = True
            self.player.known_item_ids.add(scroll.id)
            self.player.remove_from_inventory(scroll)
            self.add_message(f"You read the {display}!", 'success')
            _qs_scroll = getattr(self, 'quirk_system', None)
            if _qs_scroll:
                _qs_scroll.on_scroll_read(scroll.id, was_identified=_was_identified_before)
            self._apply_scroll_effect(scroll)
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='grammar',
            tier=scroll.quiz_tier,
            callback=on_complete,
            threshold=scroll.quiz_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus() +
                          self.player.get_quiz_extra_seconds('grammar'),
            base_seconds=self.player.get_quiz_timer('grammar'),
        )

    def _apply_scroll_effect(self, scroll: 'Scroll'):
        from dice import roll
        effect = scroll.effect
        _scroll_buc = getattr(scroll, 'buc', 'uncursed')

        if effect == 'heal':
            amount = roll(scroll.power) if scroll.power else 10
            self.player.restore_hp(amount)
            self.add_message(f"Healing light washes over you -- {amount} HP restored!", 'success')

        elif effect == 'boss_reward':
            code = scroll.power or '???'
            self.add_message(f"[REWARD CODE: {code}]", 'loot')
            self.add_message("Show this code to Dad in real life for a reward!", 'success')
            self.add_message("You can re-read this scroll at any time to see the code again.", 'info')
            # Put the scroll back in inventory so the player can re-read it
            self.player.inventory.append(scroll)
            return  # skip the remove that the caller does

        elif effect == 'mapping':
            for y in range(self.dungeon.height):
                for x in range(self.dungeon.width):
                    self.dungeon.explored.add((x, y))
            self.add_message("The dungeon layout floods your mind!", 'success')

        elif effect == 'identify':
            if _scroll_buc == 'cursed':
                self.add_message("The scroll's words dissolve into nonsense.", 'warning')
            elif _scroll_buc == 'blessed':
                # Blessed: identify ALL unknown items
                unknowns = [i for i in self.player.inventory
                            if hasattr(i, 'identified') and not i.identified
                            and i.id not in self.player.known_item_ids]
                if unknowns:
                    for u in unknowns:
                        u.identified = True
                        u.buc_known = True
                        self.player.known_item_ids.add(u.id)
                        self._propagate_identification(u.id)
                    self.add_message(f"Brilliant light reveals all {len(unknowns)} items!", 'success')
                else:
                    self.add_message("All your items are already identified.", 'info')
            else:
                # Uncursed: identify one item
                unknown = next(
                    (i for i in self.player.inventory
                     if hasattr(i, 'identified') and not i.identified
                        and i.id not in self.player.known_item_ids),
                    None
                )
                if unknown:
                    unknown.identified = True
                    unknown.buc_known = True
                    self.player.known_item_ids.add(unknown.id)
                    self._propagate_identification(unknown.id)
                    self.add_message(f"The {unknown.unidentified_name} is revealed: {unknown.name}!", 'success')
                    if unknown.lore:
                        self._lore_subject = unknown
                        self.state = STATE_LORE
                else:
                    self.add_message("All your items are already identified.", 'info')

        elif effect == 'enchant_weapon':
            from items import ENCHANT_CAP
            w = self.player.weapon or self.player.ranged_weapon
            if w:
                cap = ENCHANT_CAP.get('weapon', 5)
                delta = 2 if _scroll_buc == 'blessed' else (-1 if _scroll_buc == 'cursed' else 1)
                old_val = w.enchant_bonus
                w.enchant_bonus = max(-3, min(cap, w.enchant_bonus + delta))
                actual = w.enchant_bonus - old_val
                if actual > 0:
                    self.add_message(
                        f"Your {w.name} glows -- enchant +{w.enchant_bonus}!",
                        'success'
                    )
                elif actual < 0:
                    self.add_message(
                        f"Your {w.name} dims -- enchant {w.enchant_bonus:+d}!",
                        'warning'
                    )
                else:
                    self.add_message(
                        f"Your {w.name} shudders but can hold no more enchantment.",
                        'info'
                    )
            else:
                self.add_message("You have no weapon to enchant.", 'info')

        elif effect == 'remove_curse':
            if _scroll_buc == 'cursed':
                self.add_message("The scroll's power fizzles. Nothing happens.", 'warning')
            else:
                from status_effects import DEBUFFS
                removed = [e for e in list(self.player.status_effects) if e in DEBUFFS]
                for e in removed:
                    del self.player.status_effects[e]
                cursed_items = []
                if _scroll_buc == 'blessed':
                    # Blessed: uncurse ALL inventory items too
                    all_items = list(self.player.inventory)
                    if self.player.weapon:
                        all_items.append(self.player.weapon)
                    if self.player.ranged_weapon:
                        all_items.append(self.player.ranged_weapon)
                    all_items.extend(s for s in self.player.armor_slots if s)
                    if self.player.shield:
                        all_items.append(self.player.shield)
                    all_items.extend(s for s in getattr(self.player, 'accessory_slots', []) if s)
                    amulet = getattr(self.player, 'amulet_slot', None)
                    if amulet:
                        all_items.append(amulet)
                else:
                    # Uncursed: equipped items only
                    all_items = []
                    if self.player.weapon:
                        all_items.append(self.player.weapon)
                    if self.player.ranged_weapon:
                        all_items.append(self.player.ranged_weapon)
                    all_items.extend(s for s in self.player.armor_slots if s)
                    if self.player.shield:
                        all_items.append(self.player.shield)
                    all_items.extend(s for s in getattr(self.player, 'accessory_slots', []) if s)
                for eq in all_items:
                    if getattr(eq, 'buc', 'uncursed') == 'cursed':
                        eq.buc = 'uncursed'
                        eq.buc_known = True
                        cursed_items.append(eq.name)
                if removed or cursed_items:
                    parts = []
                    if removed:
                        parts.append(f"status effects: {', '.join(removed)}")
                    if cursed_items:
                        parts.append(f"cursed items: {', '.join(cursed_items)}")
                    self.add_message(f"A cleansing light removes {' and '.join(parts)}.", 'success')
                else:
                    self.add_message("You feel purified (no curses to remove).", 'info')

        elif effect == 'confuse_monsters':
            count = 0
            for m in self.monsters:
                if m.alive and (m.x, m.y) in self.visible:
                    m.add_effect('confused', 8)
                    count += 1
            if count:
                self.add_message(f"{count} monster(s) reel in confusion!", 'success')
            else:
                self.add_message("No monsters are in sight to confuse.", 'info')

        # -- Tier 3 scroll effects ------------------------------------------
        elif effect == 'sleep_monsters':
            targets = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in targets:
                m.add_effect('sleeping', 8)
            if targets:
                self.add_message(f"A wave of slumber washes out -- {len(targets)} creature(s) fall asleep!", 'success')
            else:
                self.add_message("No creatures are in sight to affect.", 'info')

        elif effect == 'haste_self':
            duration = int(scroll.power) if scroll.power else 15
            self.player.add_effect('hasted', duration)
            self.add_message(f"Energy surges through you -- hasted for {duration} turns!", 'success')

        elif effect == 'enchant_armor':
            from items import ENCHANT_CAP, ARMOR_SLOTS
            equipped = [(s, ARMOR_SLOTS[i]) for i, s in enumerate(self.player.armor_slots) if s is not None]
            if equipped:
                target, slot_name = equipped[0]
                cap = ENCHANT_CAP.get(slot_name, 1)
                delta = 2 if _scroll_buc == 'blessed' else (-1 if _scroll_buc == 'cursed' else 1)
                old_val = getattr(target, 'enchant_bonus', 0)
                target.enchant_bonus = max(-3, min(cap, old_val + delta))
                actual = target.enchant_bonus - old_val
                if actual > 0:
                    self.add_message(
                        f"Your {target.name} shines -- enchant +{target.enchant_bonus}!", 'success'
                    )
                elif actual < 0:
                    self.add_message(
                        f"Your {target.name} tarnishes -- enchant {target.enchant_bonus:+d}!", 'warning'
                    )
                else:
                    self.add_message(
                        f"Your {target.name} shudders but can hold no more enchantment.", 'info'
                    )
            else:
                self.add_message("You wear no armor to enchant.", 'info')

        elif effect == 'enchant_item':
            from items import ENCHANT_CAP, ARMOR_SLOTS
            candidates = []
            if self.player.weapon:
                candidates.append((self.player.weapon, 'weapon'))
            if self.player.ranged_weapon:
                candidates.append((self.player.ranged_weapon, 'weapon'))
            for i, s in enumerate(self.player.armor_slots):
                if s:
                    candidates.append((s, ARMOR_SLOTS[i]))
            if self.player.shield:
                candidates.append((self.player.shield, 'shield'))
            for s in getattr(self.player, 'accessory_slots', []):
                if s:
                    candidates.append((s, 'accessory'))
            if candidates:
                target, slot_key = candidates[0]
                cap = ENCHANT_CAP.get(slot_key, 1)
                delta = 2 if _scroll_buc == 'blessed' else (-1 if _scroll_buc == 'cursed' else 1)
                old_val = getattr(target, 'enchant_bonus', 0)
                target.enchant_bonus = max(-3, min(cap, old_val + delta))
                actual = target.enchant_bonus - old_val
                if actual > 0:
                    self.add_message(
                        f"A golden light infuses your {target.name} -- enchant +{target.enchant_bonus}!",
                        'success'
                    )
                elif actual < 0:
                    self.add_message(
                        f"A dark energy corrupts your {target.name} -- enchant {target.enchant_bonus:+d}!",
                        'warning'
                    )
                else:
                    self.add_message(
                        f"Your {target.name} shudders but can hold no more enchantment.",
                        'info'
                    )
            else:
                self.add_message("You have no equipped items to enchant.", 'info')

        # -- Tier 4 scroll effects ------------------------------------------
        elif effect == 'teleport_self':
            self._teleport_player()

        elif effect == 'charging':
            from items import Wand
            wands = [i for i in self.player.inventory if isinstance(i, Wand)]
            if wands:
                for w in wands:
                    w.charges = min(w.max_charges, w.charges + 1)
                self.add_message(
                    f"Magical energy crackles into {len(wands)} wand(s) -- each recharged by 1!", 'success'
                )
            else:
                self.add_message("You carry no wands to charge.", 'info')

        elif effect == 'identify_all':
            unknown = [i for i in self.player.inventory
                       if hasattr(i, 'identified') and not i.identified]
            if unknown:
                for item in unknown:
                    item.identified = True
                    self.player.known_item_ids.add(item.id)
                self.add_message(
                    f"A flash of revelation -- {len(unknown)} item(s) identified!", 'success'
                )
            else:
                self.add_message("All your items are already identified.", 'info')

        # -- Tier 5 scroll effects ------------------------------------------
        elif effect == 'annihilate':
            victims = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in victims:
                m.hp = 0
                m.alive = False
                self._on_monster_killed(m)
            if victims:
                self.add_message(
                    f"A blinding flash of white energy obliterates {len(victims)} creature(s)!", 'success'
                )
            else:
                self.add_message("No creatures are visible to annihilate.", 'info')

        elif effect == 'time_stop_scroll':
            duration = int(scroll.power) if scroll.power else 10
            self.player.add_effect('time_stopped', duration)
            self.add_message(f"Time itself halts -- {duration} turns of absolute stillness!", 'success')

        elif effect == 'great_power':
            for stat in ('STR', 'CON', 'DEX', 'INT', 'WIS', 'PER'):
                self.player.apply_stat_bonus(stat, 1)
            self.add_message("Every faculty within you is elevated! All stats permanently +1!", 'success')

        elif effect == 'earth':
            from dice import roll as _roll_e
            base_dmg = _roll_e(scroll.power) if scroll.power else 12
            scaled = self._int_scaled_damage(base_dmg)
            victims = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            for m in victims:
                m.take_damage(scaled)
                if not m.alive:
                    self._on_monster_killed(m)
            if victims:
                self.add_message(
                    f"Boulders crash from the ceiling! {len(victims)} creature(s) take {scaled} damage!", 'success')
            else:
                self.add_message("Rocks tumble from above, but nothing is in the way.", 'info')

        elif effect == 'protection':
            _buc = getattr(scroll, 'buc', 'uncursed')
            bonus = 5 if _buc == 'blessed' else (1 if _buc == 'cursed' else 3)
            dur = 30
            self.player.add_effect('shielded', dur)
            self.add_message(f"A protective ward envelops you! +{bonus} AC for {dur} turns!", 'success')

        elif effect == 'enchant_accessory':
            _buc = getattr(scroll, 'buc', 'uncursed')
            bonus = 2 if _buc == 'blessed' else (-1 if _buc == 'cursed' else 1)
            acc = next((s for s in self.player.accessory_slots if s is not None), None)
            if acc:
                fx = acc.effects
                if 'amount' in fx:
                    fx['amount'] = max(0, fx['amount'] + bonus)
                    self.add_message(
                        f"The {acc.name} glows! Bonus {'increased' if bonus > 0 else 'decreased'} by {abs(bonus)}!", 'success')
                else:
                    self.add_message(f"The {acc.name} shimmers briefly but nothing happens.", 'info')
            else:
                self.add_message("You have no accessory equipped to enchant.", 'warning')

        elif effect == 'genocide':
            # Kill all monsters of the most common visible type. Bosses/quest immune.
            visible = [m for m in self.monsters if m.alive and (m.x, m.y) in self.visible]
            if not visible:
                self.add_message("No creatures are visible to target.", 'info')
            else:
                # Count by kind, excluding bosses and seal demons
                from collections import Counter
                kind_counts = Counter(
                    m.kind for m in visible
                    if not getattr(m, 'is_boss', False)
                    and m.max_hp <= 500
                    and not getattr(m, 'is_seal_demon', False)
                )
                if not kind_counts:
                    self.add_message("The scroll finds no suitable targets among these creatures.", 'warning')
                else:
                    target_kind = kind_counts.most_common(1)[0][0]
                    killed = 0
                    for m in list(self.monsters):
                        if m.alive and m.kind == target_kind:
                            m.hp = 0
                            m.alive = False
                            self._on_monster_killed(m)
                            killed += 1
                    target_name = next((m.name for m in self.monsters if m.kind == target_kind), target_kind)
                    self.add_message(
                        f"A wave of annihilation sweeps the level -- {killed} {target_name}(s) erased from existence!",
                        'success')

        elif effect == 'full_light':
            _buc = getattr(scroll, 'buc', 'uncursed')
            # Reveal entire level layout
            for y in range(self.dungeon.height):
                for x in range(self.dungeon.width):
                    self.dungeon.explored[y][x] = True
            self.add_message("Brilliant light floods every corner of the level!", 'success')
            if _buc == 'blessed':
                self.player.add_effect('clairvoyant', 30)
                self.add_message("Your vision extends to sense all creatures!", 'success')

        elif effect == 'lake_of_fire':
            # The inscription is always revealed
            self.add_message(
                '"Then Death and Hades were thrown into the lake of fire."', 'info'
            )
            # Keep the scroll in inventory -- it may need to be read again
            self.player.inventory.append(scroll)

            # Check if the Abyss conditions are met
            shimmer = next(
                (g for g in self.ground_items if g.id == 'abyssal_shimmer' and g.activated),
                None
            )
            complete_on_shimmer = shimmer and any(
                g.id == 'complete_tablet_of_second_death'
                and g.x == shimmer.x and g.y == shimmer.y
                for g in self.ground_items
            )
            death_on_shimmer = (
                self.death_pursues
                and self.death_monster is not None
                and shimmer is not None
                and self.death_monster.x == shimmer.x
                and self.death_monster.y == shimmer.y
            )
            if shimmer and complete_on_shimmer and death_on_shimmer:
                self._trigger_abyss(shimmer)

    # ------------------------------------------------------------------
    # Identify menu  (i key -- philosophy quiz)
    # ------------------------------------------------------------------

    def _identify_item(self, item):
        display = self._display_name(item)
        self.quiz_title = f"IDENTIFYING {display.upper()}  --  PHILOSOPHY"
        self.state = STATE_QUIZ

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                item.identified = True
                item.buc_known = True  # BUC revealed on identification
                self.player.known_item_ids.add(item.id)
                # Propagate to ALL items: inventory, ground, and every stored level
                self._propagate_identification(item.id)
                self.add_message(
                    f"The {display} is revealed: {item.name}!", 'success'
                )
                # Show BUC status if non-uncursed
                _buc = getattr(item, 'buc', 'uncursed')
                if _buc == 'blessed':
                    self.add_message("It radiates a holy aura.", 'success')
                elif _buc == 'cursed':
                    self.add_message("A dark aura clings to it.", 'warning')
                _qs_id = getattr(self, 'quirk_system', None)
                if _qs_id:
                    _qs_id.on_item_identified(item.id)
                # Chronicle legendary identifies
                itier = getattr(item, 'quiz_tier', getattr(item, 'tier', 1))
                if itier >= 4:
                    self._log_chronicle(f"Identified something remarkable: {item.name}. The lore runs deep.")
                # Show lore screen for the identified item
                if item.lore:
                    self._lore_subject = item
                    self.state = STATE_LORE
            else:
                self.add_message(
                    f"You ponder the {display} but gain no insight.", 'warning'
                )
            self._advance_turn()

        # Identification threshold scales with item tier: tier 1 -> 2/3 qs, tier 5 -> 6/9 qs
        id_tier = getattr(item, 'quiz_tier', 1)
        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='philosophy',
            tier=id_tier,
            callback=on_complete,
            threshold=id_tier + 1,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus(),
            base_seconds=self.player.get_quiz_timer('philosophy'),
        )

    # -- Necronomicon custom quiz data -----------------------------------------
    _NECRONOMICON_QUESTIONS = [
        {
            'question': 'What is the first word?',
            'choices': ['Klaatu', 'Kla-tu', 'Clawtoo?'],
            'answer': 'Klaatu',
        },
        {
            'question': 'What is the second word?',
            'choices': ['Barada', 'Barracuda', 'Barba'],
            'answer': 'Barada',
        },
        {
            'question': 'What is the final word?',
            'choices': ['N-cnghnhhnh', 'Nicotine', 'Nada'],
            'answer': 'Nikto',           # hidden 4th option via key "4"
            '_hidden_4': 'Nikto',         # marker for the draw code
        },
    ]

    def _learn_from_spellbook(self, book: 'Spellbook'):
        """Try to learn the spell in a spellbook via grammar threshold quiz."""
        spell_id = book.spell_id
        if spell_id in self.player.known_spells:
            self.add_message(f"You already know {book.spell_name}.", 'info')
            return

        # Necronomicon: custom "Say The Words" quiz
        if book.id == 'necronomicon':
            self._necronomicon_quiz(book)
            return

        self.state = STATE_QUIZ
        self.quiz_title = "DECIPHER SPELLBOOK -- GRAMMAR"

        def on_complete(result):
            self.state = STATE_PLAYER
            if result.success:
                mp_cost = book.mp_cost
                self.player.known_spells[spell_id] = mp_cost
                book.identified = True
                self.player.remove_from_inventory(book)
                self.add_message(
                    f"You master the arcane text! {book.spell_name} learned! (costs {mp_cost} MP)", 'success')
                self._log_chronicle(f"Learned a new spell: {book.spell_name}. The words burned into my memory.")
            else:
                self.add_message(
                    "The text resists your understanding. Try again.", 'warning')
            self._advance_turn()

        self.quiz_engine.start_quiz(
            mode='threshold',
            subject='grammar',
            tier=book.quiz_tier,
            callback=on_complete,
            threshold=book.quiz_threshold,
            wisdom=self.player.WIS,
            timer_modifier=self.player.get_quiz_timer_modifier(),
            extra_seconds=self.player.get_int_quiz_bonus(),
            base_seconds=self.player.get_quiz_timer('grammar'),
        )

    def _necronomicon_quiz(self, book: 'Spellbook'):
        """The Necronomicon: recite The Words (Klaatu Barada Nikto).
        Three threshold questions with a hidden correct answer on Q3.
        Success: learn Army of Darkness. Failure: undead horde spawns."""
        import copy
        qs = [copy.deepcopy(q) for q in self._NECRONOMICON_QUESTIONS]
        # Inject into quiz engine as a custom pool
        qe = self.quiz_engine
        qe.state = QuizState.IDLE
        self.state = STATE_QUIZ
        self.quiz_title = "RECITE THE WORDS -- NECRONOMICON"
        self._necro_book = book
        self._necro_qs = qs
        self._necro_idx = 0
        self._necro_correct = 0
        self._necro_show_result = False
        self._necro_result_timer = 0.0
        self._necro_last_correct = None
        self._necro_ask_next()

    def _necro_ask_next(self):
        """Load the next Necronomicon question into the quiz engine display."""
        qe = self.quiz_engine
        q = self._necro_qs[self._necro_idx]
        qe.current_question = q
        qe.confused_order = None  # don't shuffle these
        qe.state = QuizState.ASKING
        qe.mode = QuizMode.THRESHOLD
        qe.subject = 'grammar'
        # Timer set once on first question, runs continuously (like all quizzes)
        if self._necro_idx == 0:
            _necro_timer = 10 + self.player.WIS
            qe.time_remaining = float(_necro_timer)
            qe.timer_seconds = _necro_timer
        qe.last_answer = ''
        qe.last_correct = False
        qe.correct_count = self._necro_correct
        qe.required = 3
        qe.tier = 1
        self._necro_show_result = False

    def _necro_answer(self, key: int):
        """Handle answer input for the Necronomicon quiz."""
        if self._necro_show_result:
            return  # waiting for result display to clear

        key_map = {
            pygame.K_1: 0, pygame.K_KP1: 0,
            pygame.K_2: 1, pygame.K_KP2: 1,
            pygame.K_3: 2, pygame.K_KP3: 2,
            pygame.K_4: 3, pygame.K_KP4: 3,
        }
        idx = key_map.get(key)
        if idx is None:
            return

        q = self._necro_qs[self._necro_idx]
        choices = q['choices']
        correct_answer = q['answer']

        # Hidden 4th option: "Nikto" on Q3 — only way to get it right
        if idx == 3 and '_hidden_4' in q:
            chosen = q['_hidden_4']
        elif idx < len(choices):
            chosen = choices[idx]
        else:
            return

        is_correct = chosen.strip().lower() == correct_answer.strip().lower()
        if is_correct:
            self._necro_correct += 1
            self.quiz_engine.correct_count = self._necro_correct

        # Show result briefly
        self._necro_last_correct = is_correct
        self._necro_show_result = True
        self._necro_result_timer = 0.6

        # Update quiz engine display for result feedback
        qe = self.quiz_engine
        qe.last_correct = is_correct
        qe.last_answer = chosen
        qe.state = QuizState.RESULT
        qe.result_timer = 0.6

        # If hidden 4th option was picked, add it to visible choices for result display
        if idx == 3 and '_hidden_4' in q:
            q['choices'].append(chosen)

    def _necro_update(self, dt: float):
        """Tick the Necronomicon result display timer."""
        if not self._necro_show_result:
            return
        self._necro_result_timer -= dt
        if self._necro_result_timer <= 0:
            self._necro_show_result = False
            self._necro_idx += 1
            if self._necro_idx >= len(self._necro_qs):
                self._necro_complete()
            else:
                self._necro_ask_next()

    def _necro_complete(self):
        """Resolve the Necronomicon quiz."""
        book = self._necro_book
        self.quiz_engine.state = QuizState.IDLE
        self.quiz_engine.current_question = None
        self.state = STATE_PLAYER

        if self._necro_correct == 3:
            # Perfect: learn Army of Darkness
            spell_id = book.spell_id
            mp_cost = book.mp_cost
            self.player.known_spells[spell_id] = mp_cost
            book.identified = True
            self.player.remove_from_inventory(book)
            self.add_message(
                "The words echo through the dungeon. The dead hear you. "
                "Army of Darkness learned!", 'success')
            _snd.play('spell_cast')
        else:
            # Failure: spawn hostile undead
            self.add_message(
                "Hey, I said the words! Maybe not every single little tiny "
                "syllable, but I said them!", 'danger')
            self._spawn_necronomicon_undead()
        self._necro_qs = None
        self._advance_turn()

    def _spawn_necronomicon_undead(self):
        """Spawn hostile Deadites when the Necronomicon quiz is failed."""
        import random
        from monster import Monster
        count = random.randint(4, 7)
        px, py = self.player.x, self.player.y
        occupied = {(m.x, m.y) for m in self.monsters if m.alive}
        lvl = max(1, self.dungeon_level)
        spawned = 0
        for _ in range(count):
            for _attempt in range(20):
                dx = random.randint(-3, 3)
                dy = random.randint(-3, 3)
                nx, ny = px + dx, py + dy
                if (nx, ny) in occupied or (nx, ny) == (px, py):
                    continue
                if not self.dungeon.in_bounds(nx, ny):
                    continue
                if self.dungeon.tiles[ny][nx] not in (1, 4):  # FLOOR or DOOR
                    continue
                defn = {
                    'id': 'deadite',
                    'name': 'Deadite',
                    'symbol': 'z',
                    'color': [160, 160, 210],
                    'ai_pattern': 'aggressive',
                    'hp': str(10 + lvl * 2),
                    'min_level': lvl,
                    'thac0': max(0, 18 - lvl // 5),
                    'attacks': [
                        {'name': 'claw', 'damage': f'1d4+{lvl // 10}', 'type': 'slash'},
                        {'name': 'bite', 'damage': f'1d3+{lvl // 15}', 'type': 'pierce'},
                    ],
                    'resistances': ['drain'],
                    'weaknesses': ['fire', 'holy'],
                    'lore': 'A shambling corpse raised by the Necronomicon. It knows only hunger.',
                }
                m = Monster(defn, nx, ny)
                self.monsters.append(m)
                occupied.add((nx, ny))
                spawned += 1
                break
        if spawned:
            self.add_message(
                f"{spawned} Deadites claw their way out of the ground!", 'danger')

    def _spawn_npc_deadite(self):
        """Spawn a single hostile Deadite where the NPC encounter was."""
        from monster import Monster
        npc_m = self._npc_encounter_monster
        if npc_m is None:
            return
        nx, ny = npc_m.x, npc_m.y
        lvl = max(1, self.dungeon_level)
        defn = {
            'id': 'deadite',
            'name': 'Deadite',
            'symbol': 'z',
            'color': [160, 160, 210],
            'ai_pattern': 'aggressive',
            'hp': str(20 + lvl * 3),
            'min_level': lvl,
            'thac0': max(0, 16 - lvl // 4),
            'attacks': [
                {'name': 'claw', 'damage': f'1d6+{lvl // 8}', 'type': 'slash'},
                {'name': 'bite', 'damage': f'1d4+{lvl // 10}', 'type': 'pierce'},
            ],
            'resistances': ['drain'],
            'weaknesses': ['fire', 'holy'],
            'lore': 'A shambling corpse raised by dark forces. It knows only hunger.',
        }
        m = Monster(defn, nx, ny)
        self.monsters.append(m)
        # Remove the NPC monster so it doesn't remain
        if npc_m in self.monsters:
            self.monsters.remove(npc_m)

    def _summon_undead_pets(self, count: int):
        """Summon friendly undead minions (pets) from Army of Darkness spell."""
        from pet_system import Pet
        px, py = self.player.x, self.player.y
        occupied = {(m.x, m.y) for m in self.monsters if m.alive}
        if hasattr(self, 'pets'):
            occupied |= {(p.x, p.y) for p in self.pets if p.alive}
        else:
            self.pets = []
        import random
        spawned = 0
        for _ in range(count):
            for _attempt in range(20):
                dx = random.randint(-3, 3)
                dy = random.randint(-3, 3)
                nx, ny = px + dx, py + dy
                if (nx, ny) in occupied or (nx, ny) == (px, py):
                    continue
                if not self.dungeon.in_bounds(nx, ny):
                    continue
                if self.dungeon.tiles[ny][nx] not in (1, 4):
                    continue
                # Create an undead pet using the existing Pet class
                pet = Pet('fire', nx, ny)  # reuse fire type as base
                pet.species = {
                    'element': 'shadow', 'damage_type': 'drain',
                    'color': (160, 160, 210),
                    'stages': [
                        {'name': 'Deadite', 'symbol': 'z',
                         'msg': 'A shambling deadite claws its way from the earth!'},
                        {'name': 'Deadite', 'symbol': 'z', 'msg': ''},
                        {'name': 'Deadite', 'symbol': 'z', 'msg': ''},
                    ],
                    'special_name': 'Drain Touch',
                    'special_status': 'slowed',
                    'special_status_chance': 0.3,
                }
                pet.level = max(1, self.dungeon_level // 10)
                pet.max_hp = 15 + self.dungeon_level
                pet.hp = pet.max_hp
                pet._refresh_stats()
                self.pets.append(pet)
                occupied.add((nx, ny))
                spawned += 1
                break

    def _propagate_identification(self, item_id: str):
        """Record that the player now recognises this item type by ID.

        We do NOT set item.identified = True on other instances -- that flag
        means 'this specific copy has been examined and modifiers are known'.
        Type recognition is tracked solely via player.known_item_ids.
        Also propagate buc_known to all same-id items in inventory.
        """
        self.player.known_item_ids.add(item_id)
        for inv_item in self.player.inventory:
            if inv_item.id == item_id and hasattr(inv_item, 'buc_known'):
                inv_item.buc_known = True

    def _auto_identify_all(self):
        """Identify every item in inventory and on the ground (Philosopher's Stone)."""
        for item in self.player.inventory:
            item.identified = True
            self.player.known_item_ids.add(item.id)
        for item in self.ground_items:
            item.identified = True
            self.player.known_item_ids.add(getattr(item, 'id', ''))
        # Equipped items too
        for slot_item in self.player.get_equipped_items().values():
            if slot_item:
                slot_item.identified = True
                self.player.known_item_ids.add(slot_item.id)
