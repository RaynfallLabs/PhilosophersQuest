"""HazardsMixin: the domain hazards at work (Dungeon Alive slice 3).

src/hazards.py says what each hazard is and does; this mixin applies it to
the hero and the monsters:

* ``_hazard_step_hero``: the hero stepped onto a tile (called with every
  floor-trap check);
* ``_hazard_step_monster``: a monster moved;
* ``_hazards_tick``: the fire vents breathe, glowing the turn before.

Damage is the written dice as a share of the victim's own health
(floor_curve), with fire resistance halving fire.
"""
from __future__ import annotations

import random

from game_states import STATE_DEAD


class HazardsMixin:

    def _hazard_hit_hero(self, h: dict) -> None:
        from dice import roll as _dice_roll
        from floor_curve import hazard as _hazard
        _thrown = getattr(self, '_riding_set_down', None)
        if _thrown is not None:
            _thrown('hazard')               # a rider is thrown (game_riding.py)
        dmg_str = h.get('damage')
        if dmg_str:
            raw = _hazard(_dice_roll(dmg_str), self.player.max_hp)
            dtype = h.get('type', 'physical')
            # Typed: fire resistance halves it in Player.take_damage (it was
            # also halved here first, so a resistant hero took a quarter).
            actual = self.player.take_damage(raw, dtype) if raw else 0
            if actual:
                self.add_message(f"You take {actual} damage!", 'danger')
        st = h.get('status')
        if st:
            name, lo, hi = st[0], int(st[1]), int(st[2])
            import gear as _gear
            _flame_ward = (_gear.ward_against(self.player, None, 'burning')
                           if name == 'burning' else None)
            if name == 'burning' and self.player.has_effect('fire_resist'):
                pass
            elif _flame_ward is not None:
                # Dragonscale will not catch (gear_rules wards, round 3).
                self.add_message(_gear.ward_line(self.player, *_flame_ward), 'success')
            elif h.get('save'):
                from status_effects import apply_debuff_with_save
                _ok, _msg = apply_debuff_with_save(self.player, name, random.randint(lo, hi), 14)
                if _msg:
                    self.add_message(_msg, 'danger' if _ok else 'success')
            else:
                self.player.add_effect(name, random.randint(lo, hi))
        mp = h.get('mp')
        if mp:
            from dice import roll as _r
            lost = min(int(getattr(self.player, 'mp', 0) or 0), _r(mp))
            if lost > 0:
                self.player.mp -= lost
                self.add_message(f"You lose {lost} MP.", 'danger')
        if h.get('pit'):
            if not hasattr(self.dungeon, 'pits'):
                self.dungeon.pits = set()
            self.dungeon.pits.add((self.player.x, self.player.y))
            self.player.add_effect('in_pit', -1)
            self.add_message("You land in a pit and must climb out.", 'danger')
        if self.player.is_dead() and self.state != STATE_DEAD:
            self.add_message("You have died!", 'danger')
            self.defeat_reason = 'died'
            self._on_game_over()
            self.state = STATE_DEAD

    def _hazard_step_hero(self, x: int, y: int) -> None:
        import hazards
        hit = hazards.hazard_at(self.dungeon, x, y)
        if not hit:
            return
        fid, h = hit
        # A "heavy pack" is a Heavy load or worse, over 70% of the limit
        # (the load's four tiers, Brandon 2026-11-16): the nearest line to
        # the three quarters it was from 2026-11-14, when Burdened began
        # there.
        heavy = False
        try:
            heavy = bool(self.player.is_heavy())
        except Exception:
            pass
        if not hazards.step_fires(h, heavy=heavy,
                                  levitating=self.player.has_effect('levitating'),
                                  rng=random):
            return
        if h.get('hero'):
            self.add_message(h['hero'], 'danger')
        self._hazard_hit_hero(h)
        hazards.spend(self.dungeon, (x, y), h)
        self._make_noise('struck', x, y)

    def _hazard_hit_monster(self, m, h: dict, line_key: str = 'monster') -> None:
        from dice import roll as _dice_roll
        from floor_curve import HAZARD_BAR, HAZARD_CAP, wound as _wound
        seen = self._sees_monster(m)
        line = h.get(line_key, '')
        if line and seen:
            from monster import the_name
            text = line.replace('{The}', the_name(m)).replace('{the}', the_name(m, lower=True))
            self.add_message(text[:1].upper() + text[1:], 'info')
        dmg_str = h.get('damage')
        if dmg_str:
            raw = _wound(min(HAZARD_CAP, _dice_roll(dmg_str) / HAZARD_BAR),
                         m.max_hp, m._is_named_foe())
            # The floor's blow, not the hero's (whatever turn it falls in):
            # no ward breaks and no peace ends for it (`_damage_by`).
            _by = getattr(self, '_damage_by', 'hero')
            self._damage_by = 'hazard'
            try:
                m.take_damage(raw, h.get('type', 'physical'))
            finally:
                self._damage_by = _by
        st = h.get('status')
        if st:
            m.add_effect(st[0], random.randint(int(st[1]), int(st[2])))
        if h.get('pit'):
            m.status_effects['stuck_in_pit'] = max(m.status_effects.get('stuck_in_pit', 0), 3)
        if not m.alive or m.is_dead():
            m.alive = False
            self._on_monster_killed(m)

    def _hazard_step_monster(self, m) -> None:
        import hazards
        if getattr(m, 'is_allied', False) or not m.alive:
            return
        hit = hazards.hazard_at(self.dungeon, m.x, m.y)
        if not hit:
            return
        fid, h = hit
        # A great beast is heavy (thin ice, crumbling floors); a bird, a bat
        # or a ghost does not touch the ground (audit G10).
        if not hazards.step_fires(h, heavy=hazards.is_heavy(m), levitating=hazards.floats(m),
                                  rng=random):
            return
        if not h.get('monster'):
            return
        self._hazard_hit_monster(m, h)
        hazards.spend(self.dungeon, (m.x, m.y), h)

    def _hazards_tick(self) -> None:
        """The fire vents breathe on their beat, glowing white the turn
        before; whatever stands on one when it fires is burned."""
        import hazards
        import decor
        if decor.expire(self.dungeon, self.turn_count) and hasattr(self, '_say_vines_wither'):
            self._say_vines_wither()          # a conjured vine's turns are up (game_wards.py)
        vents = hazards.cycle_hazards(self.dungeon)
        if not vents:
            return
        warned = fired = False
        state = self.dungeon.__dict__.setdefault('fixture_state', {})
        for pos in vents:
            phase = hazards.cycle_phase(self.dungeon, pos, self.turn_count)
            fid = decor.fixture_at(self.dungeon, *pos)
            h = hazards.hazard_def(fid)
            if phase == 'warn':
                state[pos] = 'glow'
                if pos in self.visible:
                    warned = True
            elif phase == 'fire':
                state[pos] = 'fire'
                if pos == (self.player.x, self.player.y):
                    if h.get('hero'):
                        self.add_message(h['hero'], 'danger')
                    self._hazard_hit_hero(h)
                    if self.state == STATE_DEAD:
                        return
                else:
                    from geom import occupied_tiles
                    for m in list(self.monsters):
                        if m.alive and not getattr(m, 'is_allied', False) and pos in occupied_tiles(m):
                            self._hazard_hit_monster(m, h)
                    if pos in self.visible:
                        fired = True
            else:
                state.pop(pos, None)
        if fired:
            self.add_message(hazards.hazard_def('fire_vent').get('seen', ''), 'warning')
        elif warned:
            self.add_message(hazards.hazard_def('fire_vent').get('warn', ''), 'warning')
