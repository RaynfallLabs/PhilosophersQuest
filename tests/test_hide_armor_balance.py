"""Hide armor must not be strictly dominated (2026-06-07).

User: "Hide armor is the same AC as Cured Leather Padded Coat but weighs 10
units more." Light-body AC came ONLY from the template (hide/leather/padded were
all base_ac 1), so Hide gave no protection edge for its extra bulk. Hide is thick
beast-hide -- D&D medium armor -- so its template base_ac is now 2: it EARNS its
weight (same AC as studded leather, but available earlier). Data-layer test;
armor stats are data-driven.
"""
from items import instantiate_armor


def test_hide_template_is_ac2():
    hide = instantiate_armor('hide', 'hide')
    assert hide.ac_bonus == 2


def test_hide_not_dominated_by_lighter_cured_leather():
    hide = instantiate_armor('hide', 'hide')
    padded = instantiate_armor('padded', 'cured_leather_armor')
    # strictly MORE AC than the lighter coat -> the extra weight buys protection
    assert hide.ac_bonus > padded.ac_bonus
    assert hide.weight > padded.weight        # the deliberate heavy-option cost


def test_hide_matches_studded_leather_ac():
    hide = instantiate_armor('hide', 'hide')
    studded = instantiate_armor('studded_leather', 'studded_leather')
    assert hide.ac_bonus == studded.ac_bonus == 2
