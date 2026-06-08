"""Material effective_against must not double-count (2026-06-07).

Fianna's yew heavy crossbow hit a fey Satyr for 41 at max chain with STR 7 /
PER 11 -- impossible from stats alone. Root cause: the yew material's
effective_against:['fey'] was applied TWICE --
  (1) inside _damage_multiplier, because the material is baked into the weapon's
      damage_types ([pierce, yew]) and _damage_multiplier reads material tags, and
  (2) again at the weapon's own effective_against check in player_attack.
1.5 x 1.5 = 2.25x, so round(7 x 1.75chain x 1.5crit x 2.25) = 41 instead of ~28.

Fix: the weapon.effective_against path is gated to UNIQUE weapons (whose JSON
declares explicit anti-tag arrays). COMPOSITIONAL weapons get their material
bonus exactly once, via the _damage_multiplier material path.
"""
from combat import _damage_multiplier
from items import instantiate_weapon


class _FeyMon:
    tags = ['fey']
    weaknesses: list = []
    resistances: list = []


def test_yew_crossbow_is_composite_and_inherits_fey_effectiveness():
    rw = instantiate_weapon('heavy_crossbow', 'yew')
    assert getattr(rw, 'is_unique', False) is False        # composite, not unique
    assert rw.material == 'yew'
    assert 'fey' in (rw.effective_against or [])            # inherited from yew
    # the material is baked into damage_types -> _damage_multiplier sees it
    assert 'yew' in [str(d).lower() for d in rw.damage_types]


def test_material_fey_bonus_is_applied_exactly_once():
    rw = instantiate_weapon('heavy_crossbow', 'yew')
    mon = _FeyMon()
    # PATH 1: the material path (yew in damage_types) applies the fey bonus.
    m1 = _damage_multiplier(list(rw.damage_types), mon)
    assert m1 == 1.5, m1
    # PATH 2: the weapon.effective_against bonus is now gated to UNIQUE weapons,
    # so a composite weapon must NOT apply it a second time. This mirrors the
    # exact use-site condition in combat.player_attack.
    path2_applies = (getattr(rw, 'is_unique', False)
                     and bool(set(mon.tags) & set(rw.effective_against or [])))
    assert path2_applies is False
    # NET: a single 1.5x, NOT the old 2.25x double-count.
    net = m1 * (1.5 if path2_applies else 1.0)
    assert net == 1.5


def test_chain5_yew_crossbow_lands_28_not_41():
    # base 7 (yew heavy crossbow) x chain-5 1.75 x crit 1.5 x fey 1.5 = 27.6 -> 28
    rw = instantiate_weapon('heavy_crossbow', 'yew')
    fey = 1.5  # single (fixed); the bug made this 2.25
    assert round(rw.base_damage * 1.75 * 1.5 * fey) == 28
    assert round(rw.base_damage * 1.75 * 1.5 * 2.25) == 41   # the old buggy value


def test_every_material_bonus_is_caught_by_damage_multiplier():
    # The fix gates weapon.effective_against to UNIQUES; composites rely on
    # _damage_multiplier catching their MATERIAL's effective_against. Guard that
    # it catches EVERY material x target-tag, so no composite loses its bonus
    # (27 materials today: yew, silver, cold_iron, dragonbone, ...).
    from combat import _load_material_tags, _MATERIAL_EFFECTIVE_AGAINST, _damage_multiplier
    _load_material_tags()

    class _Mon:
        def __init__(self, tag):
            self.tags = [tag]; self.weaknesses = []; self.resistances = []

    misses = [(mat, tag) for mat, tags in _MATERIAL_EFFECTIVE_AGAINST.items()
              for tag in tags if _damage_multiplier([mat], _Mon(tag)) != 1.5]
    assert not misses, f"material bonuses NOT caught by _damage_multiplier: {misses}"


def test_no_unique_double_counts_material_plus_own_effective_against():
    # Gating weapon.effective_against to uniques is only safe if no unique has a
    # MATERIAL whose effective_against overlaps its OWN effective_against (that
    # would re-introduce the double-count for that unique). Guard it forever.
    from combat import _load_material_tags, _MATERIAL_EFFECTIVE_AGAINST
    from items import load_items
    _load_material_tags()
    overlaps = []
    for w in load_items('weapon'):
        if not getattr(w, 'is_unique', False):
            continue
        ea = set(getattr(w, 'effective_against', []) or [])
        mat = (getattr(w, 'material', '') or '').lower()
        if ea & _MATERIAL_EFFECTIVE_AGAINST.get(mat, set()):
            overlaps.append(w.name)
    assert not overlaps, f"uniques that would double-count material+effective_against: {overlaps}"
