"""Busy for N turns: an action that takes several turns (winning-build plan
3.4, 2026-11-13). The first user is dressing (src/game_dressing.py): plate
takes five turns to buckle on, a whole kit the sum of its pieces.

An action is a list of STEPS. Each step takes some turns and happens on its
last one: a piece being put on counts (its AC, its guards) only once it is
fully on, and until then its slot is empty. The turns pass through the
game's normal turn advance, one at a time, so the monsters act on every one
of them.

The action stops when a hostile comes into view or the hero is struck, and
the game asks whether to go on ("Keep dressing? (Y/N)"). Going on picks up
where it stopped; stopping drops what is left (the step under way is not
done: the piece stays in the pack, or stays on).

Pure bookkeeping: what to do next and when to stop. The caller (the game)
advances the turns and does each step.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Step:
    """One piece of the action. ``kind`` and ``item`` say what the caller
    does when the step is done ('off', 'on', 'wield', 'ready'); ``turns`` is
    how long it takes (0: done at once, no turn of its own)."""
    kind: str
    item: object
    turns: int
    slot: str = ''
    tier: int = 0                   # a chain-equip legend's tier on 'on'
    extra: dict = field(default_factory=dict)


@dataclass
class BusyAction:
    """A multi-turn action in progress."""
    steps: list
    label: str = ''                 # "the plate", "Kit One"
    prompt: str = 'Keep dressing?'
    index: int = 0                  # the step under way
    spent: int = 0                  # turns already spent on it
    seen: set = field(default_factory=set)   # ids of monsters in view when it (re)started
    struck: int = 0                 # the blows-landed counter when it (re)started
    done_line: str = ''             # said when the whole action is done

    @property
    def total_turns(self) -> int:
        return sum(max(0, int(s.turns)) for s in self.steps)

    @property
    def turns_left(self) -> int:
        if self.done:
            return 0
        here = max(0, int(self.steps[self.index].turns) - self.spent)
        return here + sum(max(0, int(s.turns)) for s in self.steps[self.index + 1:])

    @property
    def done(self) -> bool:
        return self.index >= len(self.steps)

    @property
    def current(self):
        return None if self.done else self.steps[self.index]

    def step_due(self) -> bool:
        """Is the step under way finished by the turn about to pass (or
        does it take no turn at all)? The caller then does the step before
        advancing that turn, so the piece counts on it (a one-turn equip is
        what it always was: on, then the monsters act)."""
        s = self.current
        if s is None:
            return False
        return self.spent + 1 >= int(s.turns) or int(s.turns) <= 0

    def advance(self) -> None:
        """One turn of the step under way has passed."""
        if self.done:
            return
        self.spent += 1

    def finish_step(self) -> None:
        """The step under way is done: on to the next."""
        if self.done:
            return
        self.index += 1
        self.spent = 0


def new_sightings(before: set, now: set) -> set:
    """Monsters in view now that were not when the action (re)started."""
    return set(now) - set(before)


def interrupt_reason(action: BusyAction, seen_now: set, struck_now: int) -> str:
    """'struck', 'seen' or '' (go on)."""
    if int(struck_now) > int(action.struck):
        return 'struck'
    if new_sightings(action.seen, seen_now):
        return 'seen'
    return ''
