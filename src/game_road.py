"""Game's side of the Road, the pending queue and the oath lifecycle
(DEEDS_KARMA_DESIGN.md sections 4.7, 4.8, 5 and 6.3).

:class:`RoadMixin` owns:

* ``_road``: the run's Road state (``road.py``). Behind
  ``data/karma_rules.json: road_enabled``, for new runs only; an old save
  keeps its legacy ``_npc_encounter_levels`` / ``_flavor_encounter_levels``
  for that run. With the Road off those two dicts are still the views every
  spawner and the bump dispatch read.
* The pending queue in the deeds register: callbacks (an encounter placed N
  floors after a deed) and delayed rewards.
* ``_road_arrive(level)``: runs on the first visit of a floor, before the
  ``_maybe_spawn_*`` calls. It returns at once on the Cow Level (999), and
  every "deeper than" test uses ``deepest_floor_reached``, which never
  counts the Cow Level. In order: open oaths past their due floor lapse;
  pending rewards that are due are delivered; pending callbacks for this
  floor are placed (or carried, or dropped); the Road binds this floor's
  slot; a triggered anchor whose item is not held gives way to its fallback.

Karma never moves here: a lapse is 0 (Brandon, decision 3), delayed rewards
never carry karma (P5).
"""
from __future__ import annotations

import copy

from boss_levels import COW_LEVEL


def _encounter_by_tag(tag: str):
    """(source, definition) for an encounter tag: 'flavor' or 'npc'."""
    import flavor_encounters
    import npc_encounters
    for e in flavor_encounters.FLAVOR_ENCOUNTERS:
        if e.get('tag') == tag:
            return 'flavor', e
    for e in npc_encounters.ENCOUNTERS:
        if e.get('tag') == tag:
            return 'npc', e
    return None, None


_KEEPERS: dict | None = None


def _oath_refs(enc) -> dict:
    """{key: set(oath ids)} for each oath_* key in an encounter's options
    and their quiz branches."""
    out = {}

    def walk(o):
        if isinstance(o, dict):
            for k in ('oath_keep', 'oath_lapse', 'oath_break', 'oath_release'):
                if isinstance(o.get(k), str):
                    out.setdefault(k, set()).add(o[k])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk((enc or {}).get('options') or [])
    return out


def _oaths_kept_by(enc) -> set:
    return set(_oath_refs(enc).get('oath_keep', ()))


def _keepers_index() -> dict:
    """{oath id: {'keep': tags, 'settle': tags}} over the encounter data."""
    global _KEEPERS
    if _KEEPERS is None:
        import flavor_encounters
        import npc_encounters
        idx = {}
        for e in list(flavor_encounters.FLAVOR_ENCOUNTERS) + list(npc_encounters.ENCOUNTERS):
            for k, ids in _oath_refs(e).items():
                for oid in ids:
                    row = idx.setdefault(oid, {'keep': set(), 'settle': set()})
                    row['settle'].add(e['tag'])
                    if k == 'oath_keep':
                        row['keep'].add(e['tag'])
        _KEEPERS = idx
    return _KEEPERS


def _keepers_of(oath_id: str) -> set:
    """The encounters that can keep this oath."""
    return set((_keepers_index().get(oath_id) or {}).get('keep', ()))


def _settlers_of(oath_id: str) -> set:
    """The encounters that keep, lapse or break this oath."""
    return set((_keepers_index().get(oath_id) or {}).get('settle', ()))


class RoadMixin:
    # ------------------------------------------------------------------
    # State
    # ------------------------------------------------------------------

    def _road_state(self) -> dict:
        import road
        st = getattr(self, '_road', None)
        if not isinstance(st, dict):
            st = self._road = road.ensure_state(None)
        return road.ensure_state(st)

    def _init_road(self):
        """A new run's Road. With ``road_enabled`` the anchors bind now (their
        trigger items are laid 1-3 floors earlier) and every other slot binds
        on arrival; the legacy scheduler's picks are replaced. Off, only the
        seed is kept (callback and delayed-reward targets use it)."""
        import karma
        import road
        enabled = bool(karma.rules().get('road_enabled', False))
        self._road = road.new_state(road.roll_seed(), enabled=enabled,
                                    secret_floors=self._secret_floors())
        if enabled:
            self._setne_off_anchor()
        self._schedule_run_start()
        if not enabled:
            return
        import economy
        import npc_encounters
        anchors = road.bind_anchors(self._road, npc_encounters.ENCOUNTERS)
        self._npc_encounter_levels = {f: economy.price_encounter(e) for f, e in anchors.items()}
        self._npc_trigger_item_levels = npc_encounters.get_trigger_item_levels(
            self._npc_encounter_levels)
        self._flavor_encounter_levels = {}

    def _schedule_run_start(self):
        """Callbacks placed when the run begins, whatever the hero does
        (``karma_rules.json: run_start_schedule``): The Gate on one floor in
        94-98, which reads the people met on the way down. An entry whose
        encounter is not in the data yet is skipped silently."""
        import deeds
        import karma
        import road
        reg = self._deeds_reg()
        st = self._road_state()
        for spec in karma.rules().get('run_start_schedule') or ():
            if not isinstance(spec, dict) or not spec.get('encounter'):
                continue
            tag = spec['encounter']
            _src, enc = _encounter_by_tag(tag)
            if enc is None:
                continue
            lo, hi = (spec.get('floors') or [94, 98])[:2]
            seq = deeds.next_seq(reg)
            target = road.pick_target(st['seed'], f'start:{tag}', int(lo), int(hi), deepest=1,
                                      blocked=self._callback_blocked_floors(),
                                      band=enc.get('band'))
            if target is None:
                continue
            deeds.schedule(reg, {
                'kind': 'encounter', 'id': f'start:{tag}:{seq}', 'source': 'engine:run_start',
                'made_floor': 1, 'earliest': int(lo), 'latest': int(hi), 'target': target,
                'spec': {'encounter': tag, 'if_missed': spec.get('if_missed', 'carry')},
                'requires': spec.get('requires'), 'cause': seq,
            })

    def _secret_floors(self) -> list:
        """The floors a system scene owns (the Emberpup, the Black Knight,
        Setne's Tomb): no medium or high Road slot and no callback lands
        there, so a floor never holds two big scenes (CON-04, INT-12)."""
        out = []
        for attr in ('_emberpup', '_black_knight', '_setne'):
            f = (getattr(self, attr, None) or {}).get('floor')
            if f:
                out.append(int(f))
        return out

    def _setne_off_anchor(self):
        """The Road never refuses an anchor a floor, so the anchor of the
        tomb's band can fall on the tomb's floor. Then the tomb moves: to
        another of its candidate floors that holds no anchor, medium or high
        slot and no other secret, picked from the road seed. The tomb is
        rolled before the Road and placed only on arrival, so nothing is
        lost by moving it. (Were no such floor free it would stay put; with
        its 17 candidate floors and at most six busy ones in its bands, one
        always is.)"""
        import road
        st = getattr(self, '_setne', None)
        if not isinstance(st, dict) or not st.get('floor') or st.get('spawned'):
            return
        slot = self._road['slots'].get(int(st['floor']))
        if not slot or slot.get('role') != 'anchor':
            return
        try:
            import setne_tomb
            cands = setne_tomb.candidate_floors()
        except Exception:
            return
        busy = road.busy_floors(self._road) | set(self._secret_floors())
        free = [c for c in cands if c not in busy]
        if free:
            st['floor'] = road.rng_for(self._road['seed'], 'setne:move').choice(free)

    def _road_enabled(self) -> bool:
        return bool(self._road_state().get('enabled'))

    def _callback_blocked_floors(self) -> set:
        """Floors a callback may not take: an anchor, a medium or high Road
        slot, or another pending callback's floor."""
        import road
        blocked = set(getattr(self, '_npc_encounter_levels', {}) or {})
        blocked |= road.busy_floors(self._road_state())
        blocked |= set(self._secret_floors())
        for p in self._deeds_reg().get('pending', ()):
            if p.get('kind') == 'encounter' and p.get('target') is not None:
                blocked.add(int(p['target']))
        return blocked

    # ------------------------------------------------------------------
    # Scheduling (called from an outcome)
    # ------------------------------------------------------------------

    def _schedule_callbacks(self, specs, source: str, *, thread=None):
        """An outcome's ``schedule`` list: place each encounter N floors on
        (4.7). The target is chosen now, from the road seed; if no floor
        qualifies the thread is lost and the callback dropped.

        ``thread`` is the thread the outcome opened: it rides with each
        callback (unless the spec names its own), so a callback that is lost
        closes it with its wistful line (JNL-02).

        A callback that keeps an oath with a due floor lands on or before
        that floor (ENG-01): the two used to be rolled apart, and in a third
        of runs Wat's oath ran out before the Seventh Lamp could come."""
        import deeds
        import road
        reg = self._deeds_reg()
        floor, d, block, turn = self._deed_where()
        st = self._road_state()
        for spec in specs or ():
            if not isinstance(spec, dict) or not spec.get('encounter'):
                continue
            tag = spec['encounter']
            _src, enc = _encounter_by_tag(tag)
            if thread and not spec.get('thread'):
                spec = dict(spec, thread=thread)
            span = spec.get('after_floors') or [1, 10]
            base = d
            # 'after_oath_due': counted from an oath's due floor, not from
            # here (the dead come 1-3 floors after the Book of Thoth was due).
            # The oath must be sworn in this same outcome, before 'schedule'.
            linked = spec.get('after_oath_due')
            if linked:
                due = (reg['oaths'].get(linked) or {}).get('due_floor')
                if due is not None:
                    base = max(d, int(due))
            earliest, latest = base + int(span[0]), base + int(span[1])
            full_latest = latest
            kept = [reg['oaths'][k] for k in sorted(_oaths_kept_by(enc))
                    if (reg['oaths'].get(k) or {}).get('status') == 'open'
                    and reg['oaths'][k].get('due_floor') is not None
                    and reg['oaths'][k].get('lapse_mode') != 'callback']
            for o in kept:
                if earliest <= int(o['due_floor']):
                    latest = min(latest, int(o['due_floor']))
            seq = deeds.next_seq(reg)
            target = road.pick_target(
                st['seed'], f'cb:{tag}:{seq}', earliest, latest, deepest=d,
                blocked=self._callback_blocked_floors(),
                band=(enc or {}).get('band'))
            if target is None and kept and latest < full_latest:
                # Every floor up to the due floor is taken: the whole span,
                # and the oath's due floor moves with it (below).
                target = road.pick_target(
                    st['seed'], f'cb:{tag}:{seq}:late', earliest, full_latest, deepest=d,
                    blocked=self._callback_blocked_floors(),
                    band=(enc or {}).get('band'))
            if target is None or enc is None:
                self._callback_lost(tag, spec, source)
                continue
            for o in kept:
                # No free floor at or before the due floor: the oath waits
                # for its callback rather than running out first.
                if int(o['due_floor']) < target:
                    o['due_floor'] = target
            deeds.schedule(reg, {
                'kind': 'encounter', 'id': f'cb:{tag}:{seq}', 'source': source,
                'made_floor': floor, 'earliest': earliest, 'latest': latest,
                'target': target, 'spec': copy.deepcopy(spec),
                'requires': spec.get('requires'), 'cause': seq,
                'oath': linked or None,
            })

    def _schedule_delayed(self, specs, source: str):
        """An outcome's ``delayed`` list: a reward waiting N floors on (4.8).
        It may land on a boss floor, never on 99 or 100."""
        import deeds
        import road
        reg = self._deeds_reg()
        floor, d, block, turn = self._deed_where()
        st = self._road_state()
        for spec in specs or ():
            if not isinstance(spec, dict) or not (spec.get('reward') or spec.get('cost')):
                continue
            span = spec.get('after_floors') or [1, 5]
            earliest, latest = d + int(span[0]), d + int(span[1])
            seq = deeds.next_seq(reg)
            target = road.pick_target(st['seed'], f'dl:{source}:{seq}', earliest, latest,
                                      deepest=d, allow_boss=True)
            if target is None:
                continue
            deeds.schedule(reg, {
                'kind': 'reward', 'id': f'dl:{source}:{seq}', 'source': source,
                'made_floor': floor, 'earliest': earliest, 'latest': latest,
                'target': target, 'spec': copy.deepcopy(spec),
                'requires': spec.get('requires'), 'cause': seq,
            })

    def _callback_lost(self, tag: str, spec: dict, source: str):
        """A callback that can never happen: record ``flag.thread_lost.<tag>``
        and close its thread with a wistful line."""
        import chronicle
        import deeds
        deeds.note(self, f'flag.thread_lost.{deeds.slug(tag)}', source=source)
        # An oath left open for this callback to settle (lapse_mode
        # 'callback') lapses now: the callback that would have come for it
        # never can.
        linked = (spec or {}).get('after_oath_due')
        if linked:
            o = self._deeds_reg()['oaths'].get(linked) or {}
            if o.get('status') == 'open' and o.get('lapse_mode') == 'callback':
                floor, _d, block, turn = self._deed_where()
                deeds.lapse_oath(self._deeds_reg(), linked, floor=floor, block=block, turn=turn)
        tid = (spec or {}).get('thread')
        if tid and any((p.get('spec') or {}).get('thread') == tid
                       for p in self._deeds_reg().get('pending', ())
                       if p.get('kind') == 'encounter'):
            tid = None          # another callback of the same thread is still to come
        if tid and deeds.close_thread(self._deeds_reg(), tid, line=spec.get('lost_line')):
            line = spec.get('lost_line')
            if not line:
                _src, enc = _encounter_by_tag(tag)
                who = ((enc or {}).get('person') or {}).get('name') or (enc or {}).get('name')
                if who:
                    from naming import proper_name
                    line = f"I never did find out what became of {proper_name(who)}."
            if line:
                chronicle.chron(self, 'consequence', line, thread=tid)
        self._lapse_orphan_oaths()

    def _lapse_orphan_oaths(self):
        """ENG-08 (owner call, 2026-10-17): an open oath with no due floor
        lapses (0 karma, tag vice:lapsed) once every callback that could
        keep it is gone: met and closed without a keep, lost, or left
        behind (the hero more than three floors deeper than its floor
        without meeting it, the carry window missed callbacks get). An oath
        no encounter keeps (Sir Aldric's lodestone: any altar keeps it)
        never lapses this way."""
        import deeds
        reg = self._deeds_reg()
        for o in list(deeds.open_oaths(reg)):
            if o.get('due_floor') is not None or o.get('lapse_mode') == 'callback':
                continue
            keepers = _keepers_of(o['id'])
            if not keepers:
                continue
            if any((p.get('spec') or {}).get('encounter') in keepers
                   for p in reg.get('pending', ()) if p.get('kind') == 'encounter'):
                continue
            if self._keeper_waiting(keepers):
                continue
            self._lapse_oath_now(o)

    def _keeper_waiting(self, keepers) -> bool:
        """Is one of these encounters on a floor, not met yet, and not left
        behind? (The one open on screen right now counts as waiting.)"""
        active = (getattr(self, '_npc_encounter_active', None) or {}).get('tag')
        if active in keepers:
            return True
        d = int(getattr(self.player, 'deepest_floor_reached', 1) or 1)
        spent = set(getattr(self, '_encountered_flavor_npcs', None) or ()) | \
            set(getattr(self, '_encountered_npcs', None) or ())
        for view in (getattr(self, '_flavor_encounter_levels', None) or {},
                     getattr(self, '_npc_encounter_levels', None) or {}):
            for f, e in view.items():
                tag = (e or {}).get('tag')
                if tag in keepers and tag not in spent and int(f) + 3 >= d:
                    return True
        return False

    def _lapse_oath_now(self, o: dict):
        """Lapse one open oath, with its Journal line (as at a due floor)."""
        import chronicle
        import deeds
        reg = self._deeds_reg()
        floor, _d, block, turn = self._deed_where()
        if not deeds.lapse_oath(reg, o['id'], floor=floor, block=block, turn=turn):
            return
        line = o.get('lapse_chronicle')
        if not line and o.get('to'):
            from naming import proper_name
            line = f"I let my promise to {proper_name(o['to'])} run out. Nobody came to collect it."
        if line:
            chronicle.chron(self, 'oath', line, deed=f"lapsed.{o['id']}",
                            thread=o.get('thread'))
        if o.get('thread'):
            deeds.close_thread(reg, o['thread'], line=line)

    # ------------------------------------------------------------------
    # Arrival (6.3)
    # ------------------------------------------------------------------

    def _road_arrive(self, new_level: int):
        """First visit of ``new_level``: oaths, pending rewards, callbacks,
        the Road slot and the anchor fallback. Never on the Cow Level."""
        if new_level == COW_LEVEL:
            return
        d = int(getattr(self.player, 'deepest_floor_reached', new_level) or new_level)
        self._lapse_due_oaths(d)
        self._lapse_hostile_left_behind(new_level)
        self._deliver_due_rewards(d)
        placed = self._resolve_callbacks(new_level, d)
        if not placed:
            self._bind_road_slot(new_level)
        self._anchor_fallback(new_level)
        self._lapse_orphan_oaths()

    def _lapse_hostile_left_behind(self, new_level: int):
        """ENG-07: a 'callback'-mode oath (the Book of Thoth) is settled by
        its hostile scene. If the hero reaches a new, deeper floor while that
        scene still waits unmet on a floor above, the oath lapses: walking
        away is not a way to keep the book with a clean slate."""
        spent = set(getattr(self, '_encountered_flavor_npcs', None) or ()) | \
            set(getattr(self, '_encountered_npcs', None) or ())
        waiting = set()
        for view in (getattr(self, '_flavor_encounter_levels', None) or {},
                     getattr(self, '_npc_encounter_levels', None) or {}):
            for f, e in view.items():
                if ((e or {}).get('hostile') and e.get('tag') not in spent
                        and int(f) < int(new_level)):
                    waiting.add(e['tag'])
        if not waiting:
            return
        import deeds
        for o in list(deeds.open_oaths(self._deeds_reg())):
            if o.get('lapse_mode') == 'callback' and _settlers_of(o['id']) & waiting:
                self._lapse_oath_now(o)

    def _lapse_due_oaths(self, d: int):
        """An open oath whose due floor is behind the deepest floor lapses:
        0 karma, tag vice:lapsed (blocks 'faithful')."""
        import chronicle
        import deeds
        reg = self._deeds_reg()
        floor, _d, block, turn = self._deed_where()
        for o in list(deeds.open_oaths(reg)):
            due = o.get('due_floor')
            if due is None or int(due) >= d:
                continue
            if o.get('lapse_mode') == 'callback':
                continue        # its callback, or a late keep, settles it
            if deeds.lapse_oath(reg, o['id'], floor=floor, block=block, turn=turn):
                line = o.get('lapse_chronicle')
                if not line and o.get('to'):
                    from naming import proper_name
                    line = f"I let my promise to {proper_name(o['to'])} run out. Nobody came to collect it."
                if line:
                    chronicle.chron(self, 'oath', line, deed=f"lapsed.{o['id']}",
                                    thread=o.get('thread'))
                if o.get('thread'):
                    deeds.close_thread(reg, o['thread'], line=line)

    def _deliver_due_rewards(self, d: int):
        import chronicle
        import deeds
        reg = self._deeds_reg()
        for p in list(deeds.due_on_arrival(reg, d)):
            if p.get('kind') != 'reward':
                continue
            deeds.pop(reg, p['id'])
            if p.get('requires') and not deeds.check(p['requires'], self._deed_ctx()):
                continue
            spec = p.get('spec') or {}
            if spec.get('text'):
                self.add_message(spec['text'], 'warning' if spec.get('cost') else 'loot')
            if spec.get('cost'):
                # A loss that lands later (a knife missed a few floors on):
                # paid from the pack, no pick, never more than is there.
                from npc_encounters import can_pay_cost
                if can_pay_cost(self.player, spec['cost'], self.player_gold)[0]:
                    self._npc_pay_cost(spec['cost'], None)
            if spec.get('reward'):
                self._apply_npc_reward(spec['reward'])
            if spec.get('chronicle'):
                chronicle.chron(self, 'consequence', spec['chronicle'], cause=p.get('cause'),
                                source=p.get('source') or None)

    def _resolve_callbacks(self, new_level: int, d: int) -> bool:
        """Place this floor's callbacks; carry or drop the missed ones.
        Returns True if a callback took this floor."""
        import deeds
        reg = self._deeds_reg()
        placed = False
        for p in sorted([p for p in reg.get('pending', ()) if p.get('kind') == 'encounter'],
                        key=lambda p: (int(p.get('target') or 0), p.get('id', ''))):
            target = int(p.get('target') or 0)
            spec = p.get('spec') or {}
            tag = spec.get('encounter', '')
            if target > new_level and target > d:
                continue                        # still ahead
            if target != new_level:
                # Missed: the hero went past its floor without visiting it
                # (a level warp, a potion, a trapdoor).
                if (spec.get('if_missed', 'carry') == 'carry'
                        and d <= int(p.get('latest') or 0) + 3):
                    if placed or not self._floor_free_for_callback(new_level):
                        p['target'] = d + 1     # try the next new floor
                        continue
                else:
                    deeds.pop(reg, p['id'])
                    self._callback_lost(tag, spec, p.get('source', ''))
                    continue
            if placed or not self._floor_free_for_callback(new_level):
                # Another callback took the floor, or a carried callback
                # reached a busy one (an anchor, a medium or high slot, a
                # secret floor): it waits for the next new floor, within its
                # carry window.
                if placed or (spec.get('if_missed', 'carry') == 'carry'
                              and d <= int(p.get('latest') or 0) + 3):
                    p['target'] = d + 1
                    continue
                deeds.pop(reg, p['id'])
                self._callback_lost(tag, spec, p.get('source', ''))
                continue
            deeds.pop(reg, p['id'])
            _src, _cb = _encounter_by_tag(tag)
            # The encounter's own requires / forbids too (ENG-02): one that
            # cannot appear is lost, not placed to bind the floor and never
            # spawn.
            if ((p.get('requires') and not deeds.check(p['requires'], self._deed_ctx()))
                    or (_cb is not None and not self._encounter_allowed(_cb))):
                self._callback_lost(tag, spec, p.get('source', ''))
                continue
            if self._place_callback(new_level, tag):
                placed = True
                # The Journal files the callback's line under the deed
                # that caused it (chronicle.deed_rows).
                if p.get('source'):
                    reg.setdefault('causes', {})[tag] = p['source']
            else:
                self._callback_lost(tag, spec, p.get('source', ''))
        return placed

    def _floor_free_for_callback(self, level: int) -> bool:
        import road
        if level in (getattr(self, '_npc_encounter_levels', {}) or {}):
            return False
        if level in self._secret_floors():
            return False
        return level not in road.busy_floors(self._road_state())

    def _place_callback(self, level: int, tag: str) -> bool:
        """Put the callback encounter on this floor through the compatibility
        views; the ordinary spawners then place the NPC. A light encounter
        already there is cancelled (``replace: light``)."""
        import economy
        src, enc = _encounter_by_tag(tag)
        if enc is None:
            return False
        spent = (getattr(self, '_encountered_flavor_npcs', None) or set()) if src == 'flavor' \
            else (getattr(self, '_encountered_npcs', None) or set())
        if tag in spent:
            return False
        priced = economy.price_encounter(enc)
        if src == 'flavor':
            self._flavor_encounter_levels[level] = priced
        else:
            self._npc_encounter_levels[level] = priced
        st = self._road_state()
        if tag not in st['used_tags']:
            st['used_tags'].append(tag)
        s = st['slots'].get(level)
        if s is not None and s.get('role') == 'light':
            s['bound'] = tag
        return True

    def _bind_road_slot(self, level: int):
        """Late binding of a light, medium or high slot (5.3)."""
        if not self._road_enabled():
            return
        if (getattr(self, '_flavor_encounter_levels', None) or {}).get(level):
            return      # the floor already holds an encounter: one a floor
        import economy
        import flavor_encounters
        import npc_encounters
        import road
        st = self._road_state()
        pool = list(flavor_encounters.FLAVOR_ENCOUNTERS) + [
            e for e in npc_encounters.ENCOUNTERS if e.get('road_ok')]
        spent = set(getattr(self, '_encountered_flavor_npcs', None) or ())
        enc = road.bind_slot(st, level, pool,
                             allowed=lambda e: e['tag'] not in spent and self._encounter_allowed(e))
        if enc is not None:
            self._flavor_encounter_levels[level] = economy.price_encounter(enc)

    def _anchor_fallback(self, level: int):
        """A triggered anchor whose item the hero does not hold gives way to
        the fallback bound with it (bug 4: the block used to lose its anchor)."""
        if not self._road_enabled():
            return
        s = self._road_state()['slots'].get(level)
        enc = (getattr(self, '_npc_encounter_levels', {}) or {}).get(level)
        if not s or s.get('role') != 'anchor' or not s.get('fallback') or enc is None:
            return
        trig = enc.get('trigger_item')
        if not trig or trig in getattr(self, '_npc_triggered_items', set()):
            return
        _src, fb = _encounter_by_tag(s['fallback'])
        if fb is not None:
            import economy
            self._npc_encounter_levels[level] = economy.price_encounter(fb)
            s['bound'], s['fallback'] = s['fallback'], None
