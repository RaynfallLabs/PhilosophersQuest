"""Restore-MP/HP potions must ROLL their magnitude, not serve a flat value
(2026-06-08).

'potion of mana' displayed "Magnitude: 15 (rolled when quaffed)" but its power
was the flat string "15", so the quaff did int("15")=15 and it ALWAYS restored
exactly 15 -- never rolled, contradicting the UI. restore_mp/brilliance_mp now
roll_dice(power) like the HP heals already did, and the data carries dice
notation (mana 2d8+6, brilliance 4d8+22).
"""
import json
import os
import random
from pathlib import Path

os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

from food_system import drink_potion
from items import Potion

_ROOT = Path(__file__).resolve().parents[1]
_POTIONS = json.loads((_ROOT / 'data' / 'items' / 'potion.json').read_text(encoding='utf-8'))

# Effects whose `power` is a numeric magnitude applied per quaff. The UI labels
# these "(rolled when quaffed)", so the data MUST be dice notation -- a flat
# value here is exactly the mana-potion bug.
_ROLLED_MAGNITUDE = {'heal', 'extra_heal', 'restore_sp', 'restore_mp', 'brilliance_mp'}


class _P:
    def __init__(self):
        self.mp = 0
        self.max_mp = 500
        self.hp = 1
        self.max_hp = 500
        self.sp = 0
        self.max_sp = 500
        self.status_effects = {}
        self.unlocked_class_masteries = {}

    def restore_mp(self, a):
        self.mp = min(self.max_mp, self.mp + a)

    def restore_hp(self, a):
        self.hp = min(self.max_hp, self.hp + a)

    def restore_sp(self, a):
        self.sp = min(self.max_sp, self.sp + a)


def _potion(pid):
    dd = dict(_POTIONS[pid])
    dd['id'] = pid
    p = Potion(dd)
    p.identified = True
    return p


def test_every_rolled_magnitude_potion_has_dice_power():
    """No flat-magnitude potion may claim '(rolled when quaffed)'."""
    bad = []
    for pid, v in _POTIONS.items():
        if v.get('effect') in _ROLLED_MAGNITUDE:
            p = str(v.get('power', ''))
            if 'd' not in p.lower():
                bad.append(f"{pid} ({v.get('effect')}) power={p!r}")
    assert not bad, "rolled-magnitude potions with FLAT power:\n  " + "\n  ".join(bad)


def test_mana_and_brilliance_actually_vary():
    random.seed(1)
    for pid in ('potion_of_mana', 'potion_of_brilliance'):
        seen = set()
        for _ in range(60):
            pl = _P()
            drink_potion(pl, _potion(pid))
            seen.add(pl.mp)
        assert len(seen) > 1, f"{pid} restored a constant amount (not rolled)"


def test_mana_rolls_within_its_dice_band():
    random.seed(2)
    vals = []
    for _ in range(200):
        pl = _P()
        drink_potion(pl, _potion('potion_of_mana'))
        vals.append(pl.mp)
    # 2d8+6 -> [8, 22]
    assert min(vals) >= 8 and max(vals) <= 22, f"mana out of 2d8+6 band: {min(vals)}-{max(vals)}"
