"""MagicWardsMixin: the Game's side of the MONSTERS AND MAGIC magic (2026-11-19).

The rules are pure modules and data: the hero's wards (src/wards.py), the gates
on a monster (src/attack_gates.py), data/wards.json; the spells in src/spells.py,
the items in data/items/{spellbook,scroll,potion,wand,weapon}.json. This mixin
casts, reads and zaps them, and says what happened, one plain line each.

Hooks into the old dispatchers, one line each:
  * MagicMixin._cast_spell_effect -> ``_mm_cast`` (the new spells);
  * MagicMixin._invoke_spell -> ``_begin_tile_spell`` (a spell aimed at a tile:
    Shrink the Earth), CombatMixin._confirm_power_target -> ``_confirm_tile_spell``;
  * MagicMixin._apply_scroll_effect -> ``_mm_scroll`` (family wards, the Piper's
    tune) and its 'protection' branch -> ``_protection_also`` (what each warding
    rite also keeps off);
  * MagicMixin._apply_wand_effect -> ``_mm_wand`` (Unstringing, the Krotala);
  * the 'detect_treasure' wand and the Fern-Flower Tincture -> ``_treasure_sight``;
  * DivineMixin._resolve_simple_prayer -> ``_answer_deliver_us``;
  * the V menu -> ``_sceptre_power_rows`` / ``_activate_sceptre`` (the Sceptre of
    Agamemnon's Call the Assembly);
  * monster.HERO_STRUCK -> ``_ward_hero_struck`` (the wards a blow breaks).

New state is per instance and defaults by getattr (old saves read as none):
the player's ``_ward_gen`` and ``_sceptre_floor``; a monster's ``_wards_broken``,
``_strife_peace``; the dungeon's ``fixture_expiry`` (decor.place_for).
"""
from __future__ import annotations

from naming import quantity
from game_states import STATE_PLAYER, STATE_QUIZ, STATE_TARGET
from geom import monster_at_tile

SCEPTRE_ID = 'sceptre_of_agamemnon'
SCEPTRE_POWER = 'sceptre_assembly'
# What the QA sampler (Shift+B, Titivillus) hands over.
QA_SPELLS = frozenset((
    'galdr_of_loosing_spell', 'cockcrow_spell', 'sanctuary_spell', 'elf_shot_spell',
    'stayed_spear_spell', 'tacitas_seal_spell', 'dionysus_vine_spell', 'shrink_the_earth_spell',
    'bough_of_somnus_spell', 'dulled_blades_spell', 'confusion_of_tongues_spell',
    'darkness_of_egypt_spell', 'pans_panic_spell', 'settled_strife_spell',
    'mist_of_manannan_spell', 'hush_of_the_feralia_spell'))
QA_SCROLLS = ('scroll_of_the_lemuria', 'scroll_of_the_hamelin_piper', 'scroll_of_daniel',
              'scroll_of_the_psylli', 'scroll_of_the_heart_sutra', 'scroll_of_saint_martha',
              'scroll_of_the_udug_hul')
QA_POTIONS = ('goatherds_coffee', 'nepenthe', 'oil_of_rue', 'fern_flower_tincture', 'moly',
              'theriac', 'water_of_epidaurus', 'charm_of_prometheus', 'water_of_the_styx')


def _the(m, lower: bool = False) -> str:
    from monster import the_name
    return the_name(m, lower=lower)


def _cheb(ax, ay, bx, by) -> int:
    return max(abs(ax - bx), abs(ay - by))


class MagicWardsMixin:
    # ------------------------------------------------------------------
    # Shared
    # ------------------------------------------------------------------

    def _mm_foes_in_sight(self) -> list:
        """The hostile creatures an area spell of this kind catches: alive,
        in a clear line from the hero, not a friend."""
        return [m for m in self.monsters
                if self._in_spell_sight(m) and not getattr(m, 'is_allied', False)]

    def _mm_seen(self, m) -> bool:
        from game_magic import _hero_sees
        return _hero_sees(self, m)

    def _mm_mass(self, foes, status: str, turns: int, landed: str, none: str,
                 gate: bool = False) -> int:
        """Lay ``status`` on each of ``foes`` (through _inflict, or the gate
        rules for silenced / unstrung / babbled), and say how many of those
        the hero sees took it. Returns that count."""
        import attack_gates
        took = 0
        seen = 0
        for m in foes:
            vis = self._mm_seen(m)
            seen += 1 if vis else 0
            got = attack_gates.inflict(m, status, turns) if gate else self._inflict(m, status, turns)[0]
            if got and vis:
                took += 1
        if seen:
            self.add_message(landed.format(n=took, of=seen, dur=quantity(turns, 'turn')),
                             'success' if took else 'warning')
        else:
            self.add_message(none, 'info')
        return took

    def _family_rout(self, family: str, status: str, turns: int, landed: str, none: str) -> int:
        """Every creature of ``family`` in sight takes ``status`` (the Piper's
        tune on vermin, the Krotala's clash on birds). Named foes stand."""
        import family_lore
        foes = [m for m in self._mm_foes_in_sight() if family_lore.family_of(m) == family]
        if not foes:
            self.add_message(none, 'info')
            return 0
        return self._mm_mass(foes, status, turns, landed, none)

    def _treasure_sight(self, line: str = '') -> int:
        """Every treasure, coin and chest on the floor is marked on the map
        (the Fern-Flower Tincture; the wand of treasure finding). Returns how
        many places."""
        from items import Container, GoldPile, Treasure
        spots = set()
        for it in getattr(self, 'ground_items', None) or ():
            if isinstance(it, (Treasure, GoldPile, Container)) or \
                    getattr(it, 'item_class', '') in ('treasure', 'gold', 'container'):
                x, y = getattr(it, 'x', None), getattr(it, 'y', None)
                if x is not None and y is not None:
                    spots.add((int(x), int(y)))
        for p in spots:
            self.dungeon.explored.add(p)
        self.__dict__.setdefault('_treasure_seen', set()).update(spots)
        if spots:
            self.add_message(line or (f"The fern flower's sight opens in you: "
                                      f"{quantity(len(spots), 'place')} where treasure lies "
                                      f"are marked on your map."), 'success')
        else:
            self.add_message("The fern flower's sight opens in you, and finds no treasure "
                             "on this floor.", 'info')
        return len(spots)

    # ------------------------------------------------------------------
    # The hero strikes (monster.HERO_STRUCK)
    # ------------------------------------------------------------------

    def _ward_hero_struck(self, m) -> None:
        """One of the hero's own blows landed on ``m``: the wards it breaks
        and sanctuary end (wards.hero_struck); Settled Strife ends for it."""
        if getattr(self, '_damage_by', 'hero') != 'hero':
            return
        if m not in (getattr(self, 'monsters', None) or ()):
            return
        import wards
        for line in wards.hero_struck(self.player, m, getattr(self, 'turn_count', None)):
            self.add_message(line, 'info')
        if m.__dict__.get('_strife_peace') and m.status_effects.get('charmed', 0) > 0:
            m.status_effects.pop('charmed', None)
            m._strife_peace = False
            self.add_message(f"You struck {_the(m, lower=True)}: the peace is broken, "
                             f"and {_the(m, lower=True)} takes up arms again.", 'warning')

    def _say_vines_wither(self) -> None:
        self.add_message("The god's vines wither back into the stone.", 'info')

    # ------------------------------------------------------------------
    # The spells
    # ------------------------------------------------------------------

    def _mm_cast(self, spell: dict, target, cs: float) -> bool:
        """The MONSTERS AND MAGIC spells. True when ``spell`` was one of them."""
        import attack_gates
        import wards
        effect = spell.get('effect')
        base = int(spell.get('duration', 0) or 0)
        from status_effects import MAX_EFFECT_DURATION as _MAXD
        dur = min(_MAXD, max(2, int(base * cs))) if base else 0
        p = self.player

        if effect == 'stayed_spear_self':
            wards.grant(p, 'stayed_spear', dur)
            self.add_message(f"You sing the fifth charm and keep your eyes open: arrows, stones "
                             f"and spears from any foe you can see will drop short of you "
                             f"({quantity(dur, 'turn')}).", 'success')
            return True

        if effect == 'loosing_self':
            freed = [s for s in ('immobilized', 'impaled', 'in_pit', 'strangulation')
                     if p.status_effects.pop(s, None) is not None]
            if 'in_pit' in freed and hasattr(self.dungeon, 'pits'):
                self.dungeon.pits.discard((p.x, p.y))
            wards.grant(p, 'free_action', dur)
            if freed:
                self.add_message(f"You sing the charm for a man in chains, and whatever held you "
                                 f"springs off. Nothing can grab or pin you "
                                 f"({quantity(dur, 'turn')}).", 'success')
            else:
                self.add_message(f"You sing the charm for a man in chains. Nothing can grab or "
                                 f"pin you ({quantity(dur, 'turn')}).", 'success')
            return True

        if effect == 'sanctuary_self':
            wards.grant(p, 'sanctuary', dur)
            self.add_message(f"The old law of the church door closes round you: ordinary foes "
                             f"will not strike you until you strike ({quantity(dur, 'turn')}).",
                             'success')
            return True

        if effect == 'veil_self':
            wards.grant(p, 'veiled', dur)
            self.add_message(f"Manannan's cloak of mist comes down round you: nothing more than "
                             f"two steps off can see you ({quantity(dur, 'turn')}).", 'success')
            return True

        if effect == 'silence_monster':
            if target is None:
                return False
            got = attack_gates.inflict(target, 'silenced', dur)
            if got:
                self.add_message(f"{_the(target)}'s mouth is sealed: no wail, no song, no call, "
                                 f"no spell ({quantity(got, 'turn')}).", 'success')
            elif attack_gates.mouthless(target):
                self.add_message(f"{_the(target)} has no voice to take.", 'warning')
            else:
                self.add_message(f"{_the(target)} shakes off the seal.", 'warning')
            return True

        if effect == 'entangle':
            if target is None:
                return False
            self._cast_entangle(target, dur)
            return True

        if effect == 'aimed_step':
            spot = self.__dict__.pop('_aimed_tile', None)
            why = self._aimed_step_refused(*spot) if spot else "There is nowhere to step to."
            if why:
                self.add_message(why, 'warning')
                return True
            p.x, p.y = spot
            self._refresh_fov()
            self.add_message("You fold the veins of the earth and take one stride. You stand "
                             "where you looked.", 'success')
            _qs = getattr(self, 'quirk_system', None)
            if _qs:
                _qs.on_teleport()
            return True

        if effect == 'sleep_area':
            if target is None:
                return False
            from geom import chebyshev_distance
            near = [m for m in self.monsters if m.alive and not getattr(m, 'is_allied', False)
                    and (m is target or chebyshev_distance(target.x, target.y, m) <= 1)]
            took = sum(1 for m in near if self._inflict(m, 'sleeping', dur)[0])
            if took:
                self.add_message(f"You shake the bough of Lethe over them: "
                                 f"{quantity(took, 'creature')} fall asleep "
                                 f"({quantity(dur, 'turn')}).", 'success')
            else:
                self.add_message("The dew of Lethe falls, and no one sleeps.", 'warning')
            return True

        if effect == 'mass_weaken':
            self._mm_mass(self._mm_foes_in_sight(), 'weakened', dur,
                          "You sing the war-song at them and their edges go blunt: "
                          "{n} of {of} Weakened ({dur}).",
                          "You sing the war-song, and there is no foe in sight to hear it.")
            return True

        if effect == 'mass_blind':
            self._mm_mass(self._mm_foes_in_sight(), 'blinded', dur,
                          "A darkness that can be felt falls on them, and your own eyes stay "
                          "clear: {n} of {of} Blinded ({dur}).",
                          "The darkness falls, and there is no foe in sight under it.")
            return True

        if effect == 'mass_silence':
            self._mm_mass(self._mm_foes_in_sight(), 'silenced', dur,
                          "The hush of the Feralia falls on the room: {n} of {of} Silenced ({dur}).",
                          "The hush falls, and there is no foe in sight to keep quiet.",
                          gate=True)
            return True

        if effect == 'pan_panic':
            from geom import chebyshev_distance
            foes = [m for m in self._mm_foes_in_sight()
                    if chebyshev_distance(p.x, p.y, m) <= 4]
            self._mm_mass(foes, 'feared', dur,
                          "Pan's sudden terror goes through everything near you: "
                          "{n} of {of} run ({dur}).",
                          "Pan's terror goes out from you, and nothing is near enough to feel it.")
            return True

        if effect == 'tongues':
            foes = [m for m in self._mm_foes_in_sight() if attack_gates.speaks(m)]
            if not foes:
                self.add_message("Their speech is confounded, but nothing in sight has a "
                                 "language to lose.", 'info')
                return True
            band = max(2, int(12 * cs))
            took = 0
            for m in foes:
                if self._inflict(m, 'confused', dur)[0] and self._mm_seen(m):
                    took += 1
                attack_gates.inflict(m, 'babbled', band)
            self.add_message(f"Their speech is confounded: each hears his fellows babble. "
                             f"{took} of {sum(1 for m in foes if self._mm_seen(m))} Confused "
                             f"({quantity(dur, 'turn')}), and no pack or band among them fights "
                             f"as one ({quantity(band, 'turn')}).", 'success')
            return True

        if effect == 'settled_strife':
            foes = [m for m in self._mm_foes_in_sight() if attack_gates.is_person(m)]
            if not foes:
                self.add_message("You sing the song that settles hatred, and no man, goblin or "
                                 "giant is here to hear it.", 'info')
                return True
            took = 0
            for m in foes:
                if self._inflict(m, 'charmed', dur)[0]:
                    m._strife_peace = True
                    took += 1 if self._mm_seen(m) else 0
            self.add_message(f"You sing the song that settles hatred: {took} of "
                             f"{sum(1 for m in foes if self._mm_seen(m))} lay down arms "
                             f"({quantity(dur, 'turn')}). Strike one, and it is over for that one.",
                             'success' if took else 'warning')
            return True

        return False

    def _cast_entangle(self, target, dur: int) -> None:
        """Dionysus's Vine: everything on the target's tile and the eight
        round it is held fast; the vines stay and catch whoever steps in."""
        import decor
        import hazards
        from dungeon import FLOOR
        tx, ty = target.x, target.y
        tiles = [(tx + dx, ty + dy) for dy in (-1, 0, 1) for dx in (-1, 0, 1)]
        caught = 0
        for m in list(self.monsters):
            if not m.alive or getattr(m, 'is_allied', False):
                continue
            from geom import occupied_tiles
            if not any(t in tiles for t in occupied_tiles(m)):
                continue
            if hazards.floats(m):
                continue
            if self._inflict(m, 'immobilized', dur)[0] and self._mm_seen(m):
                caught += 1
        until = int(getattr(self, 'turn_count', 0)) + 12
        grown = 0
        try:
            from dungeon import STAIRS_DOWN, STAIRS_UP, DOOR
            bad = {STAIRS_DOWN, STAIRS_UP, DOOR}
        except ImportError:
            bad = set()
        for (x, y) in tiles:
            if not self.dungeon.in_bounds(x, y):
                continue
            if self.dungeon.tiles[y][x] != FLOOR or self.dungeon.tiles[y][x] in bad:
                continue
            if (x, y) == (self.player.x, self.player.y):
                continue
            if decor.place_for(self.dungeon, (x, y), 'conjured_vine', until):
                grown += 1
        if caught:
            self.add_message(f"Vines burst up out of the stones and wind round "
                             f"{quantity(caught, 'creature')}: held fast ({quantity(dur, 'turn')}). "
                             f"The vines stay a while, and catch whatever steps in.", 'success')
        elif grown:
            self.add_message("Vines burst up out of the stones. They stay a while, and catch "
                             "whatever steps in.", 'success')
        else:
            self.add_message("Vines stir under the stones, but nothing here will hold them.", 'warning')

    # ------------------------------------------------------------------
    # A spell aimed at a tile: Shrink the Earth
    # ------------------------------------------------------------------

    def _begin_tile_spell(self, spell, spell_id, mp_cost, free) -> None:
        """Open the aim for a tile spell: the cursor starts on the hero, the
        arrows move it as far as the spell reaches."""
        self.player.mp -= mp_cost
        self._pending_spell = spell
        self._pending_spell_id = spell_id
        self._pending_spell_paid = mp_cost
        self._pending_spell_free = bool(free)
        self._power_targeting = True
        self._pending_power = f'spell_{spell_id}'
        self._target_candidates = []
        self._target_idx = 0
        self.target_cursor_x, self.target_cursor_y = self.player.x, self.player.y
        self.state = STATE_TARGET
        from spells import spell_reach
        self.add_message(f"Casting {spell['name']}... move the cursor to a spot you can see, "
                         f"up to {quantity(spell_reach(spell) or 6, 'step')} away, and press "
                         f"ENTER.", 'info')

    def _aimed_step_refused(self, x: int, y: int) -> str:
        """'' when the hero may stand on (x, y) now, else why not."""
        from spells import LEARNABLE_SPELLS, spell_reach
        reach = spell_reach(LEARNABLE_SPELLS.get('shrink_the_earth_spell')) or 6
        p = self.player
        if (x, y) == (p.x, p.y):
            return "You are standing there already."
        if _cheb(p.x, p.y, x, y) > reach:
            return f"That is too far: the earth folds only {quantity(reach, 'step')}."
        if (x, y) not in self.visible:
            return "You can only step to a spot you can see."
        if not self.dungeon.is_walkable(x, y):
            return "There is no footing there."
        if monster_at_tile(self.monsters, x, y) is not None or \
                (x, y) in self._occupants(hero=False):
            return "Someone is standing there."
        return ''

    def _confirm_tile_spell(self, cx: int, cy: int) -> None:
        """ENTER on the tile spell's aim: the quiz, then the step."""
        spell = getattr(self, '_pending_spell', None)
        spell_id = getattr(self, '_pending_spell_id', None)
        why = self._aimed_step_refused(cx, cy)
        if why:
            self.add_message(why, 'warning')
            self._refund_pending_spell()
            self.state = STATE_PLAYER
            return
        self._pending_spell = None
        self._pending_spell_id = None
        self._pending_spell_paid = None
        self._pending_spell_free = False
        self._aimed_tile = (cx, cy)
        if spell:
            self._start_spell_quiz(spell, spell_id, None)

    # ------------------------------------------------------------------
    # The scrolls
    # ------------------------------------------------------------------

    def _mm_scroll(self, scroll) -> bool:
        """Family wards and the Piper's tune. True when handled."""
        import wards
        effect = getattr(scroll, 'effect', '')
        if effect not in ('family_ward', 'family_rout'):
            return False
        d = wards.item_def('scroll', getattr(scroll, 'id', ''))
        buc = getattr(scroll, 'buc', 'uncursed')
        mult = 1.5 if buc == 'blessed' else (0.5 if buc == 'cursed' else 1.0)
        turns = max(1, int(int(d.get('turns', 10)) * mult))
        if effect == 'family_ward':
            wid = d.get('ward', '')
            if not wards.ward_spec(wid):
                self.add_message("The words fade from the page before you can finish them.", 'warning')
                return True
            got = wards.grant(self.player, wid, turns)
            self.add_message(f"{d.get('read_line', 'The rite takes hold.')} "
                             f"({quantity(got, 'turn')}).", 'success')
            return True
        self._family_rout(d.get('family', ''), d.get('status', 'feared'), turns,
                          d.get('read_line', '') + " {n} of {of} go ({dur}).",
                          d.get('none_line', 'The tune plays, and nothing in sight follows it.'))
        return True

    def _protection_also(self, scroll) -> None:
        """What each warding rite keeps off besides the blow (data
        'ward_also': [[status, turns], ...]; a cursed scroll gives only its
        Shielded)."""
        import wards
        if getattr(scroll, 'buc', 'uncursed') == 'cursed':
            return
        d = wards.item_def('scroll', getattr(scroll, 'id', ''))
        also = d.get('ward_also') or []
        if not also:
            return
        names = []
        from status_effects import EFFECT_INFO
        for st, turns in also:
            wards.grant(self.player, st, int(turns), cap=max(60, int(turns)))
            names.append((EFFECT_INFO.get(st) or (st.replace('_', ' ').title(),))[0])
        if d.get('ward_line'):
            self.add_message(f"{d['ward_line']} ({', '.join(names)}.)", 'success')

    # ------------------------------------------------------------------
    # The wands
    # ------------------------------------------------------------------

    def _mm_wand(self, wand) -> bool:
        import attack_gates
        import wards
        effect = getattr(wand, 'effect', '')
        if effect == 'unstring_monster':
            target = getattr(self, '_wand_override_target', None) or self._nearest_visible_monster()
            if target is None:
                self.add_message("The wand hums but finds no target.", 'info')
                return True
            from game_magic import _spring_at
            _spring_at(self, target)
            turns = self._wand_effect_duration(wand, 8)
            got = attack_gates.inflict(target, 'unstrung', turns)
            if got:
                self.add_message(f"The singer's song goes into {_the(target, lower=True)}'s long "
                                 f"weapons: bow, breath and gaze will not answer "
                                 f"{_the(target, lower=True)} ({quantity(got, 'turn')}). "
                                 f"It has to come to you.", 'success')
            else:
                self.add_message(f"{_the(target)} shakes off the song.", 'warning')
            return True
        if effect == 'family_rout':
            d = wards.item_def('wand', getattr(wand, 'id', ''))
            turns = self._wand_effect_duration(wand, 10)
            self._family_rout(d.get('family', 'birds'), d.get('status', 'feared'), turns,
                              d.get('zap_line', '') + " {n} of {of} take fright ({dur}).",
                              d.get('none_line', 'The bronze clashes, and no bird is in sight.'))
            if hasattr(self, '_make_noise'):
                self._make_noise('shout')       # an honest price: every sleeper hears it
            return True
        return False

    # ------------------------------------------------------------------
    # The prayer: Deliver Us From Evil
    # ------------------------------------------------------------------

    def _answer_deliver_us(self, chain: int, effective: int, hp_pct: float) -> None:
        import prayers
        import wards
        turns = prayers.deliver_us(effective, hp_pct <= prayers.DESPERATE_HP)
        if turns <= 0:
            return
        got = wards.grant(self.player, 'ward_deliver_us', turns)
        self.add_message(f"A ring of light stands round you that the fiends and the evil dead "
                         f"cannot cross to lay hands on you ({quantity(got, 'turn')}). "
                         f"Strike one, and it is open to that one.", 'success')
        if chain >= 5:
            self._chron('soul', "I prayed to be delivered from evil, and the dead stood off "
                                "from me as if from fire.", once='deliver_us')

    # ------------------------------------------------------------------
    # QA (Titivillus build, Shift+B)
    # ------------------------------------------------------------------

    def _qa_magic_sampler(self) -> None:
        """Every new spell learned, two of each new scroll, potion and oil,
        the two wands and the Sceptre in the pack, MP full: the whole of the
        MONSTERS AND MAGIC magic to try in a few minutes."""
        if not getattr(self.player, 'qa_tools', False):
            return
        from items import make_item_by_id
        from spells import LEARNABLE_SPELLS
        p = self.player
        learned = 0
        for sid in sorted(QA_SPELLS):
            if sid not in p.known_spells:
                p.known_spells[sid] = int(LEARNABLE_SPELLS[sid]['mp_cost'])
                learned += 1
        given = 0
        for cls, ids, n in (('scroll', QA_SCROLLS, 2), ('potion', QA_POTIONS, 2),
                            ('wand', ('wand_of_unstringing', 'krotala_of_athena'), 1),
                            ('weapon', (SCEPTRE_ID,), 1)):
            for iid in ids:
                it = make_item_by_id(cls, iid)
                if it is None:
                    continue
                it.identified = True
                p.known_item_ids.add(iid)
                if n > 1:
                    it.count = n
                p.inventory.append(it)
                given += 1
        p.mp = p.max_mp
        self.add_message(f"[QA] The new magic: {learned} spells learned, {given} kinds of scroll, "
                         f"potion, oil, wand and the Sceptre in your pack. MP full.", 'info')

    # ------------------------------------------------------------------
    # The Sceptre of Agamemnon: Call the Assembly (V)
    # ------------------------------------------------------------------

    def _sceptre_ready(self) -> bool:
        p = self.player
        w = getattr(p, 'weapon', None)
        if getattr(w, 'id', '') != SCEPTRE_ID:
            return False
        return p.__dict__.get('_sceptre_floor') != getattr(self, 'dungeon_level', None)

    def _sceptre_power_rows(self) -> list:
        """The V menu's row for the sceptre in the hand, once a floor."""
        w = getattr(self.player, 'weapon', None)
        if getattr(w, 'id', '') != SCEPTRE_ID:
            return []
        ready = self._sceptre_ready()
        return [(SCEPTRE_POWER, {'label': 'Call the Assembly',
                                 'desc': ('Raise the sceptre as Odysseus did: every man and '
                                          'goblin in sight loses heart and runs, a war band '
                                          'loses its leader\'s hold. A history chain; once a floor.'),
                                 'cooldown': 0, 'uses': 1}, 1 if ready else 0, 0)]

    def _activate_sceptre(self) -> bool:
        p = self.player
        if not self._sceptre_ready():
            self.add_message("The sceptre has called the assembly once on this floor. It will "
                             "not be heard again here.", 'warning')
            return True
        p._sceptre_floor = getattr(self, 'dungeon_level', None)
        self.add_message("You raise the sceptre of Zeus's own making, as Odysseus did when the "
                         "army broke for the ships.", 'info')
        self.quiz_title = "CALL THE ASSEMBLY  --  HISTORY"
        self.state = STATE_QUIZ
        self.quiz_engine.start_quiz(
            mode='escalator_chain', subject='history', tier=3,
            callback=self._sceptre_quiz_done, max_chain=6,
            wisdom=p.WIS, timer_modifier=p.get_quiz_timer_modifier(),
            extra_seconds=p.get_quiz_extra_seconds('history'),
            base_seconds=p.get_quiz_timer('history'),
        )
        return True

    def _sceptre_quiz_done(self, result) -> None:
        self.state = STATE_PLAYER
        chain = int(getattr(result, 'score', 0) or 0)
        if chain <= 0:
            self.add_message("You raise the sceptre, and no one heeds it.", 'warning')
            self._advance_turn()
            return
        import attack_gates
        import war_bands
        turns = min(12, 2 * chain)
        foes = [m for m in self._mm_foes_in_sight() if attack_gates.is_person(m)]
        bands = {getattr(m, '_band', None) for m in foes} - {None}
        for uid in bands:
            war_bands.break_hold(self.monsters, uid)
        took = 0
        for m in foes:
            if self._inflict(m, 'feared', turns)[0] and self._mm_seen(m):
                took += 1
        if took:
            self.add_message(f"The sceptre comes down, and the will goes out of them: "
                             f"{quantity(took, 'foe')} turn and run ({quantity(turns, 'turn')})."
                             + (" The war band's leader has lost his hold on it." if bands else ''),
                             'success')
        else:
            self.add_message("The sceptre comes down, and no man or goblin in sight gives way.",
                             'warning')
        self._advance_turn()
