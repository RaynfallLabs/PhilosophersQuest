"""Press or Guard, and the two-hander's parry (winning-build plan 2026-11-13,
section 3.4, decision 7; slice 5).

**Press or Guard.** Brandon: "sacrificing defense for damage based on
monster". One key (Shift+S) steps through Neutral, Press and Guard; it takes
one turn, as swapping a weapon does, so the stance is chosen for a fight,
not for each blow. Press hits harder and opens the hero's guard; Guard is
the reverse. Every number is in data/arsenal.json ``stance``: ``damage``
multiplies every weapon blow and shot (combat.strike_damage), ``ac`` is the
armour points gained or given up (Player.get_ac). Neutral by default; kept
on the hero (``Player.stance``), so it is saved.

**The parry.** A two-handed melee weapon held with no shield turns blows
aside: the deep hero who gave up his shield for a greatsword was hit about
95% of the time. Its AC comes from the weapon's template (greatsword,
glaive, quarterstaff 2; bastard sword, great axe, maul, warhammer 1), a
named weapon's class when it has no template, plus one at tier 4 and 5
(data/arsenal.json ``parry``). Never from the floor. Player.get_ac adds it;
the weapon card says "Parry +2".

Pure: no pygame, no Game.
"""
from __future__ import annotations

NEUTRAL, PRESS, GUARD = 'neutral', 'press', 'guard'


def rules() -> dict:
    import coatings
    return coatings.data().get('stance') or {}


def parry_rules() -> dict:
    import coatings
    return coatings.data().get('parry') or {}


def order() -> list:
    return list(rules().get('order') or [NEUTRAL, PRESS, GUARD])


def of(player) -> str:
    """The hero's stance ('neutral' for one saved before stances)."""
    s = str(getattr(player, 'stance', NEUTRAL) or NEUTRAL)
    return s if s in order() else NEUTRAL


def _def(stance: str) -> dict:
    return rules().get(stance) or {}


def name(stance: str) -> str:
    return str(_def(stance).get('name', stance.title()))


def next_stance(stance: str) -> str:
    o = order()
    i = o.index(stance) if stance in o else 0
    return o[(i + 1) % len(o)]


def damage_mult(player) -> float:
    """What the stance does to a weapon blow or shot (Press 1.3, Guard 0.7).
    Fabius the Delayer (a trait) halves what Guard costs: 0.85."""
    s = of(player)
    m = float(_def(s).get('damage', 1.0) or 1.0)
    if s == GUARD and m < 1.0 and (getattr(player, 'quirk_progress', None) or {}).get('fabius_active'):
        m = 1.0 - (1.0 - m) / 2.0
    return m


def stance_ac(player) -> int:
    """Armour points the stance gives (Guard +2) or takes (Press -2)."""
    return int(_def(of(player)).get('ac', 0) or 0)


def change(player) -> str:
    """Step the hero to the next stance; the line that says so."""
    new = next_stance(of(player))
    player.stance = new
    return str(_def(new).get('line', f"Stance: {name(new)}."))


def detail(stance: str) -> str:
    """'+30% damage, 2 AC worse' for a stance's chip and card."""
    d = _def(stance)
    dmg = float(d.get('damage', 1.0) or 1.0)
    ac = int(d.get('ac', 0) or 0)
    bits = []
    if abs(dmg - 1.0) > 1e-9:
        bits.append(f"{round((dmg - 1.0) * 100):+d}% damage")
    if ac:
        bits.append(f"{abs(ac)} AC {'better' if ac > 0 else 'worse'}")
    return ', '.join(bits) or 'no change'


def hud_rows(player) -> list:
    """[(label, kind)] for the sidebar's effects: Press or Guard when held."""
    s = of(player)
    if s == NEUTRAL:
        return []
    return [(name(s), s)]


# ---------------------------------------------------------------------------
# The two-hander's parry
# ---------------------------------------------------------------------------

def _template_id(weapon) -> str:
    try:
        import smithing
        t = smithing.template_of(weapon)
        if t:
            return str(t)
    except Exception:
        pass
    return str(getattr(weapon, 'template_basis', '') or '')


def weapon_parry(weapon) -> int:
    """The parry a two-handed melee weapon gives held with no shield (0 for
    anything else): its template's, else its class's, plus its tier's."""
    if weapon is None or not getattr(weapon, 'two_handed', False):
        return 0
    if getattr(weapon, 'requires_ammo', None):
        return 0
    r = parry_rules()
    base = (r.get('by_template') or {}).get(_template_id(weapon))
    if base is None:
        base = (r.get('by_class') or {}).get(str(getattr(weapon, 'weapon_class', '') or ''), 0)
    base = int(base or 0)
    if base <= 0:
        return 0
    try:
        tier = int(getattr(weapon, 'tier', 1) or 1)
    except (TypeError, ValueError):
        tier = 1
    return base + int((r.get('tier_bonus') or {}).get(str(tier), 0) or 0)


def parry_ac(player) -> int:
    """AC the hero's two-hander gives him now: none with a shield on (a
    two-hander cannot take one, but a test or an old save can try)."""
    if getattr(player, 'shield', None) is not None:
        return 0
    p = weapon_parry(getattr(player, 'weapon', None))
    if p > 0 and (getattr(player, 'quirk_progress', None) or {}).get('wallace_active'):
        p += 1                              # the Wallace Sword (a trait)
    return p


def card_lines(weapon) -> list:
    """'Parry +2: ...' for a two-hander's card."""
    p = weapon_parry(weapon)
    if not p:
        return []
    return [str(parry_rules().get('card', 'Parry +{ac}.')).format(ac=p)]
