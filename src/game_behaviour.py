"""BehaviourMixin: the Game's side of monster behaviour, first wave (AI-1,
2026-11-19).

The behaviours themselves are pure modules (breath, faction, summoning,
morale, life_drain, grave_rot, light_shy, gone_again, alarm, death_throes,
relurk, shove); this mixin is only what needs the Game: what the hero sees
and hears of them (the lines each leaves, src/ai_lines.py), and the few
things that touch the map, the kill handler or the hero's turn.

  _ai_turn_after(m)   after a monster's turn (CombatMixin._do_monster_turns):
                      its lines, said as the hero sees or hears them; the
                      purse a yielding bandit throws down (morale).
  _ai_on_kill(m)      from the kill handler (CombatMixin._on_monster_killed):
                      its side sees it fall (morale); it bursts (death
                      throes), one at a time.
  _ai_resolve_shove() after the monsters' turn (main._advance_turn, beside
                      the pull): a giant's blow threw the hero back.
"""
from __future__ import annotations

import ai_lines
import kind_data
import morale


class BehaviourMixin:

    def _ai_turn_after(self, m) -> None:
        """What a monster's behaviour left this turn for the hero to see or
        hear: the line he can see said as it is, a sound when he cannot (an
        unseen line never names the creature)."""
        self._ai_register_source()
        if m.__dict__.pop('_wants_purse_dropped', False):
            self._ai_drop_purse(m)
        if m.alive:
            import death_throes
            import light_shy
            light_shy.light_turn(m, self.player, getattr(self, 'dungeon', None))  # a troll in the light
            death_throes.warn(m)                      # it swells before it bursts
            if m.__dict__.get('_dark_hidden'):        # it may have run out of the dark
                import unseen
                m._unseen = unseen.unseen(m, self.player)
        lines = ai_lines.take(m)
        if not lines:
            return
        seen = self._sees_monster(m)
        for text_seen, text_unseen, colour in lines:
            text = text_seen if seen else text_unseen
            if text:
                self.add_message(text, colour or 'warning')

    def _ai_drop_purse(self, m) -> None:
        """A creature that yields (morale) throws down its purse, and what it
        stole: its gold falls on its tile now and is not dropped again when
        it dies."""
        import random as _rng
        from items import add_gold_to_tile
        import theft
        tre = dict(getattr(m, 'treasure', None) or {})
        lo, hi = (list(tre.get('gold') or [0, 0]) + [0, 0])[:2]
        gold = _rng.randint(int(lo), max(int(lo), int(hi))) if hi else 0
        if gold > 0:
            add_gold_to_tile(self.ground_items, gold, m.x, m.y)
        tre['gold'] = [0, 0]
        m.treasure = tre
        for text in theft.give_back(self, m):
            self.add_message(text, 'loot')
        # A war-band's captain who begs leads no one: his band answers as if
        # he had fallen (war_bands.on_death: the rout, the crumble...).
        if getattr(m, '_band_role', '') == 'leader':
            self._band_member_died(m)

    def _ai_register_source(self) -> None:
        """Tell summoning.py whose blows land now (a chant's line names
        who broke it)."""
        import summoning
        import weakref
        if getattr(summoning, '_READER_OWNER', None) is not self:
            summoning.set_source_reader(weakref.WeakMethod(self._ai_blow_source))
            summoning._READER_OWNER = self

    def _ai_blow_source(self, m) -> tuple:
        """('hero' | 'pet' | 'other', a pet's name): whose blow lands on
        ``m`` now, by the turn's part (main._advance_turn's _damage_by)."""
        by = getattr(self, '_damage_by', 'hero')
        if by == 'hero':
            return 'hero', ''
        if by == 'pet':
            pets = [p for p in (getattr(self, 'pets', None) or ()) if getattr(p, 'alive', False)]
            near = [p for p in pets if max(abs(p.x - m.x), abs(p.y - m.y)) <= 1] or pets
            if near:
                return 'pet', str(getattr(near[0], 'name', '') or 'companion')
        return 'other', ''

    def _ai_on_kill(self, m) -> None:
        """One of a side fell: its hurt kin that saw it may break (morale),
        and it may burst (death throes)."""
        try:
            morale.kin_fell(self.monsters, m, getattr(self, 'dungeon', None))
        except Exception as exc:          # never let a nerve check stop a kill
            from game_log import log_error
            log_error(f"morale.kin_fell: {exc!r}")
        self._ai_throes(m)

    # ------------------------------------------------------------------
    # Death Throes (src/death_throes.py)
    # ------------------------------------------------------------------

    def _ai_throes(self, m) -> None:
        """It bursts as it dies. A creature the blast kills bursts after it,
        one at a time (a queue: never one burst inside another)."""
        import death_throes
        if not death_throes.should_burst(m):
            return
        m._throes_done = True
        queue = self.__dict__.setdefault('_throes_queue', [])
        queue.append(m)
        if self.__dict__.get('_throes_running'):
            return
        self._throes_running = True
        # A blast is no one's blow (`_damage_by`): not the hero's, whoever
        # struck the one that burst, so no ward or sanctuary ends for it, no
        # peace breaks, no habit is taught and no damage badge counts it.
        by = getattr(self, '_damage_by', 'hero')
        self._damage_by = 'throes'
        try:
            while queue:
                self._ai_burst(queue.pop(0))
        finally:
            self._throes_running = False
            self._throes_queue = []
            self._damage_by = by

    def _ai_burst(self, m) -> None:
        import death_throes
        from status_effects import apply_debuff_with_save
        t = death_throes.spec(m) or {}
        kind = str(t.get('type', 'fire') or 'fire')
        eff = t.get('effect')
        dur = int(t.get('effect_duration', 3) or 3)
        if (m.x, m.y) in getattr(self, 'visible', ()) and t.get('line'):
            self.add_message(ai_lines.fill(m, t['line']), 'danger')
        p = self.player
        import holds
        # (Swallowed, the hero is inside another: no burst outside it reaches him. AI-3)
        if death_throes.in_blast(m, p.x, p.y, self.dungeon) and not holds.shields(p, m):
            import wards
            dmg = death_throes.blast(m, p.max_hp)
            if dmg > 0:
                # A ward against its family turns the blast as it turns its
                # blows (wards.py: Saint Martha's and the like).
                dmg = max(1, int(round(dmg * wards.damage_mult(p, m))))
                got = p.take_damage(dmg, kind)
                if got:
                    self.add_message(f"The blast catches you for {got} damage!", 'danger')
            if eff and p.hp > 0:
                import counters
                fake = {'name': 'Death Throes', 'delivery': str(t.get('delivery', '') or '')}
                blocked = counters.blocks_rider(p, m, fake, eff)
                warded = wards.rider_line(p, m, eff)
                if blocked is not None:
                    self.add_message(counters.line(p, blocked[0], blocked[1], m), 'info')
                elif warded:
                    self.add_message(warded, 'info')       # a family ward keeps it off
                else:
                    dc = min(18, 12 + int(getattr(m, 'min_level', 1) or 1) // 7)
                    _ok, text = apply_debuff_with_save(p, eff, dur, dc, source=m)
                    if text:
                        self.add_message(text, 'danger')
            if p.hp <= 0:
                self._answer_a_killing_blow()
                if p.is_dead():
                    from game_states import STATE_DEAD
                    if self.state != STATE_DEAD:
                        self.defeat_reason = 'died'
                        self._killed_by = getattr(m, 'kind', None)
                        self._on_game_over()
                        self.state = STATE_DEAD
                        self.add_message("You have died! Press Esc to return to the title.", 'danger')
                    return
        import summoning
        for o in list(self.monsters):
            if o is m or not o.alive or kind_data.outside_rules(o):
                continue
            if not death_throes.in_blast(m, o.x, o.y, self.dungeon):
                continue
            dmg = death_throes.blast(m, o.max_hp, o._is_named_foe())
            if dmg > 0:
                summoning.CONTEXT = 'throes'      # a chant it breaks says so
                try:
                    o.take_damage(dmg, kind)
                finally:
                    summoning.CONTEXT = None
            if eff and o.alive:
                o.add_effect(eff, dur)
            if not o.alive:
                self._on_monster_killed(o)
        # A death cry that carries (the mandrake's: `alarm_radius`): all that
        # hear it within reach are roused, through stone.
        if t.get('alarm_radius'):
            import alarm
            alarm.cry(m, self.monsters, self.player, int(t['alarm_radius']))

    # ------------------------------------------------------------------
    # Shove (src/shove.py)
    # ------------------------------------------------------------------

    def _ai_resolve_shove(self) -> None:
        """A blow this turn threw the hero back: one tile, never into
        danger the shover did not mean (water, lava, a pit, a wall)."""
        p = self.player
        sv = p.__dict__.pop('_pending_shove', None)
        if not sv or p.hp <= 0:
            return
        import shove
        from geom import all_occupied_tiles
        occ = set(all_occupied_tiles(self.monsters)) | set(self._occupants(hero=False))
        got = shove.landing(self.dungeon, (p.x, p.y), tuple(sv['from']), bool(sv.get('aim')), occ)
        if got is None:
            return
        (nx, ny), aimed = got
        p.x, p.y = nx, ny
        self.add_message(sv['aimed'] if aimed else sv['line'], 'danger')
        _hz = getattr(self, '_hazard_step_hero', None)
        if _hz is not None:
            _hz(nx, ny)
        self._refresh_fov()
