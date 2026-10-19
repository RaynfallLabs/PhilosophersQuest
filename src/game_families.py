"""FamilyMixin: the Game's side of monster family knowledge.

The rules live in src/family_lore.py (who is in which family, what the hero
has learned) and src/family_edges.py (what each tier's techniques do). This
mixin only says things to the player and touches the floor:

  * `_family_study`: a correct corpse study or a Scroll of Omnisight records
    the kind, then `_family_news` announces each tier, circle and title the
    first time it is reached (a gold line for tiers 1 and 2, a popup in the
    quirk popup's style for tiers 3 to 5, a circle or the Loremaster title,
    and a Journal line for each);
  * `_family_arrival`: the Forewarned lines when the hero reaches a floor, and
    the creatures that arrive calm (Beast-Friend, Entertaining Angels);
  * `_family_turn` / `_family_drain`: each turn, the families that flee on
    sight, the hidden things a family technique shows, and the queued
    technique lines;
  * `_family_surrender`: a foe that yields throws down its purse;
  * `_qa_family_tier`: the QA key (Titivillus, PQ_QA_MODE only).
"""
from __future__ import annotations

from game_states import STATE_STORY_POPUP

import family_edges
import family_lore
from naming import proper_name

# The accent of a tier popup: the quirk popup's look, in lore gold.
_POPUP_ACCENT = (232, 196, 110)


class FamilyMixin:

    # ------------------------------------------------------------------
    # Studying
    # ------------------------------------------------------------------
    def _family_study(self, kind) -> bool:
        """One study of `kind`: recorded, then any news announced. True when
        the kind was new to the hero (only a new kind is progress)."""
        new = family_lore.record_study(self.player, kind)
        self._family_news()
        return new

    def _family_has_page(self, kind) -> bool:
        """Ruling 1: the full Bestiary page opens only for an identified kind
        (studied, opened by the Book of Thoth or Omnisight, or its family at
        tier 1 or more)."""
        return family_lore.has_page(self.player, kind)

    def _family_news(self) -> None:
        """Announce, once each, every tier, circle and title newly reached."""
        news = family_lore.news(self.player)
        if not news:
            return
        popup_title, popup_lines = '', []
        for what, key, tier in news:
            if what == 'tier':
                fid = key
                line = family_lore.tier_chronicle(fid, tier)
                if line:
                    self._chron('discovery', line, once=f'family:{fid}:{tier}')
                msg = family_lore.tier_message(fid, tier)
                if msg:
                    self.add_message(msg, 'loot')
                title = family_lore.popup_title(fid, tier)
                if title:
                    popup_title = popup_title or title
                    if popup_lines:
                        popup_lines += ['', title]
                    popup_lines += self._family_tier_popup_lines(fid, tier)
                    self.add_message(f"{proper_name(title.lower())}: "
                                     + ', '.join(a.get('name', '') for a in
                                                 family_lore.tier_entry(fid, tier).get('abilities', ())),
                                     'loot')
            elif what == 'circle':
                c = family_lore.circles().get(key) or {}
                boon = c.get('boon') or {}
                line = c.get('chronicle', '')
                if line:
                    self._chron('discovery', line, once=f'circle:{key}')
                head = family_lore.data().get('circle_title', 'CIRCLE COMPLETE')
                popup_title = popup_title or head
                if popup_lines:
                    popup_lines += ['', head]
                popup_lines += [c.get('name', ''), '',
                                f"{boon.get('name', '')}: {boon.get('text', '')}"]
                self.add_message(f"{c.get('name', '')} is complete: {boon.get('name', '')}.", 'loot')
            elif what == 'loremaster':
                lm = family_lore.data().get('loremaster') or {}
                line = lm.get('chronicle', '')
                if line:
                    self._chron('discovery', line, once='loremaster')
                title = str(lm.get('title', 'Loremaster')).upper()
                popup_title = popup_title or title
                if popup_lines:
                    popup_lines += ['', title]
                popup_lines += ["Five families of monster, known down to the last weakness.",
                                "", "You have earned the title of Loremaster."]
                self.add_message("You are a Loremaster now.", 'loot')
        if popup_lines:
            self._family_popup(popup_title, popup_lines)

    def _family_tier_popup_lines(self, fid, tier) -> list:
        """A tier popup's body: its lead line, each technique as "Name: what
        it does" (a blank line between: the popup joins touching lines into
        one paragraph), and the tier's Field Note when it is written."""
        entry = family_lore.tier_entry(fid, tier)
        lines = []
        lead = family_lore.popup_lead(fid, tier)
        if lead:
            lines += [lead, '']
        for a in entry.get('abilities', ()) or ():
            lines += [f"{a.get('name', '')}: {a.get('text', '')}", '']
        note = str(entry.get('field_note', '') or '').strip()
        if note:
            lines += [f'"{note}"']
        while lines and lines[-1] == '':
            lines.pop()
        return lines

    def _family_popup(self, title: str, lines: list) -> None:
        """A tier, circle or title popup in the quirk popup's style. A
        second one raised while one is up joins it rather than replacing it,
        and it returns to wherever the hero was (the lore page after a
        study)."""
        if self.state == STATE_STORY_POPUP and isinstance(getattr(self, 'popup_data', None), dict) \
                and self.popup_data.get('_family'):
            self.popup_data['lines'] += [''] + [title] + list(lines)
            return
        self.popup_data = {'title': title, 'accent': _POPUP_ACCENT, 'lines': list(lines),
                           'code': None, '_family': True}
        if self.state != STATE_STORY_POPUP:
            self.popup_next_state = self.state
        self.state = STATE_STORY_POPUP

    # ------------------------------------------------------------------
    # The Bestiary's Families view (B, then Tab)
    # ------------------------------------------------------------------
    def _bestiary_family_entries(self) -> list:
        """One entry per family the hero has met (a member seen or studied)
        or holds a tier in. Unmet families, unseen members and a family's
        size are never shown."""
        out = []
        tiers = family_lore.tiers(self.player)
        for fid in family_lore.families():
            seen = family_lore.members_seen(self.player, fid)
            if not seen and not tiers.get(fid):
                continue
            out.append({'_family': fid, 'name': family_lore.family_name(fid)})
        out.sort(key=lambda e: e['name'].lower().removeprefix('the '))
        return out

    # ------------------------------------------------------------------
    # Arriving on a floor
    # ------------------------------------------------------------------
    def _family_arrival(self, first_visit: bool = True) -> None:
        """Forewarned: one line per family at tier 2 or more with a member
        on this floor that the hero could see (never a concealed one, the
        Hellmouth's stair or an ally); at most three lines. And on a first
        visit, the lesser creatures that arrive calm."""
        import unseen
        player = self.player
        mons = [m for m in (self.monsters or ()) if getattr(m, 'alive', False)]

        def _ally(m):
            return bool(getattr(m, 'is_allied', False) or getattr(m, '_npc_encounter_tag', None)
                        or getattr(m, '_flavor_encounter_tag', None)
                        or getattr(m, '_is_unicorn', False))

        def _hidden(m):
            # Whether or not it is in sight, ask what it would look like:
            # an invisible creature, an un-sprung ambusher and a disguised
            # mimic (the Hellmouth's false stair) are never counted.
            return (unseen.is_invisible(m) and not unseen.sees_invisible(player)) or (
                getattr(m, 'ai_pattern', '') in ('ambush', 'mimic') and not getattr(m, '_aware', False))

        for line in family_lore.arrival_lines(player, mons, concealed=_hidden, is_ally=_ally):
            self.add_message(line, 'warning')
        if first_visit:
            fired = family_edges.calm_arrivals(player, [m for m in mons if not _ally(m)])
            for ab in fired:
                if ab and ab.get('trigger_msg'):
                    self.add_message(ab['trigger_msg'], 'info')

    # ------------------------------------------------------------------
    # Every turn
    # ------------------------------------------------------------------
    def _family_turn(self) -> None:
        """Before the monsters act: the families that flee from the hero on
        sight do (Your Name Is Known), and a hidden creature a family
        technique now shows him is announced, once."""
        player = self.player
        vis = getattr(self, 'visible', None) or set()
        if not family_lore.tiers(player):
            return
        fired = family_edges.on_sight_turns(player, self.monsters, vis)
        told = self.__dict__.setdefault('_family_floor_told', set())
        for ab in fired:
            key = (self.dungeon_level, ab.get('id'))
            if key not in told and ab.get('trigger_msg'):
                told.add(key)
                self.add_message(ab['trigger_msg'], 'info')
        for m in self.monsters or ():
            if (getattr(m, 'alive', False) and (m.x, m.y) in vis
                    and family_edges.senses(player, m)):
                ab = family_edges.sense_ability(player, m)
                if ab is not None:
                    family_edges.tell(player, m, ab)
        self._family_drain()

    def _family_drain(self) -> None:
        """Print the technique lines queued since the last call."""
        for line in family_edges.drain(self.player):
            self.add_message(line, 'success')

    # ------------------------------------------------------------------
    # Yield!
    # ------------------------------------------------------------------
    def _family_surrender(self, monster) -> None:
        """A lesser foe yields (Mortal Foes' Yield!): it throws down its purse
        on its own tile, as a gold pile the hero picks up by the usual rules
        of coin weight, and has nothing left to drop if it dies later."""
        import random as _rng
        from items import add_gold_to_tile
        treasure = dict(getattr(monster, 'treasure', {}) or {})
        lo, hi = (list(treasure.get('gold', [0, 0])) + [0, 0])[:2]
        gold = _rng.randint(int(lo), max(int(lo), int(hi)))
        stolen = int(getattr(monster, 'stolen_gold', 0) or 0)
        total = gold + stolen
        if total > 0:
            add_gold_to_tile(self.ground_items, total, monster.x, monster.y)
            self.add_message(f"{self._the_monster_name(monster)} throws down {total:,} gold "
                             f"and runs.", 'loot')
        treasure['gold'] = [0, 0]
        monster.treasure = treasure
        monster.stolen_gold = 0

    def _the_monster_name(self, monster) -> str:
        from monster import the_name
        return the_name(monster)

    # ------------------------------------------------------------------
    # QA (Titivillus, PQ_QA_MODE only)
    # ------------------------------------------------------------------
    def _qa_family_tier(self) -> None:
        """Shift+F with the QA build: one tier more (5 wraps to 0) in the
        family of the nearest creature in sight, or in every family when
        none is. News and popups fire as in play."""
        if not getattr(self.player, 'qa_tools', False):
            return
        target = None
        vis = getattr(self, 'visible', None) or set()
        best = None
        for m in self.monsters or ():
            if getattr(m, 'alive', False) and (m.x, m.y) in vis and family_lore.family_of(m):
                d = max(abs(m.x - self.player.x), abs(m.y - self.player.y))
                if best is None or d < best:
                    best, target = d, m
        fids = [family_lore.family_of(target)] if target is not None else list(family_lore.families())
        g = self.player.family_lore_grants = dict(getattr(self.player, 'family_lore_grants', {}) or {})
        for fid in fids:
            t = (family_lore.tier(self.player, fid) + 1) % (family_lore.max_tier(fid) + 1)
            g[fid] = t
            if t == 0:
                g.pop(fid, None)
                told = getattr(self.player, 'family_tiers_told', {}) or {}
                told[fid] = 0
        names = ', '.join(family_lore.short_name(f) for f in fids[:3]) + ('...' if len(fids) > 3 else '')
        self.add_message(f"[QA] Family tier now {family_lore.tier(self.player, fids[0])}: {names}.",
                         'info')
        self._family_news()
