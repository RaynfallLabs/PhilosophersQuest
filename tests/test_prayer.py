"""Tests for the v2.13.0 prayer + altar simplification (2026-09-06).

v2.13.0 REPLACED the 9-prayer picker + drop-on-altar BUC quiz with:
  * Simple Prayer (\\) -- ONE theology escalator_chain quiz, max 5.
    Bonuses stack per chain tier (SP, HP, MP, uncurse-or-bless, shielded).
    Karma modifies magnitudes; altar DOUBLES the karma delta.
  * Divine Intercession (Shift+\\) -- once-per-run "big ask" gated by
    ``player.divine_intercession_used``. On-altar = escalator_chain(1);
    off-altar = threshold=5 T5. Success = full heal + invulnerable +
    random artifact. Failure = every worn item cursed + blinded 100t.
  * Altar drop-reveal -- passive, no quiz. Positive karma = truthful
    reveal (cursed items consumed); negative karma = deceptive reveal;
    zero karma = silent.

This file locks in the mechanics that survived the redesign:
  * karma-tier verse buckets (moral_vision voice, unchanged)
  * _iter_equipped helper covers every equip slot
  * _altar_drop_reveal karma-branching + consumption semantics
  * _resolve_simple_prayer chain-tier stacking (SP -> HP -> MP -> ...)
  * Divine Intercession quiz-mode selection + once-per-run gate
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import game_divine


# ---------------------------------------------------------------------------
# karma_tier mapping (verse voice; unchanged from v2.12)
# ---------------------------------------------------------------------------

def test_karma_tier_buckets():
    f = game_divine._karma_tier
    assert f(10) == 'saintly'
    assert f(6)  == 'saintly'
    assert f(5)  == 'righteous'
    assert f(1)  == 'righteous'
    assert f(0)  == 'neutral'
    assert f(-1) == 'slipping'
    assert f(-5) == 'slipping'
    assert f(-6) == 'fallen'
    assert f(-10) == 'fallen'


def test_karma_verses_have_full_chains():
    """escalator_chain caps at tier 5 -- verses indexed 1-5 (plus 0 for
    fallen 'examine your conscience' silence)."""
    for tier in ('saintly', 'righteous', 'neutral', 'slipping'):
        for chain in range(1, 6):
            assert chain in game_divine._KARMA_VERSES[tier], (
                f"{tier} missing chain {chain} verse")
    assert 0 in game_divine._KARMA_VERSES['fallen']
    for chain in range(1, 6):
        assert chain in game_divine._KARMA_VERSES['fallen'], (
            f"fallen missing chain {chain} verse")


# ---------------------------------------------------------------------------
# v2.13.0: the retired-content lockdown. If any of these ever pass True
# something is dragging the old code back.
# ---------------------------------------------------------------------------

def test_prayers_registry_is_gone():
    """The 9-prayer PRAYERS list was retired in v2.13.0."""
    assert not hasattr(game_divine, 'PRAYERS')


def test_per_prayer_handlers_are_gone():
    """The 9 per-prayer _prayer_* handlers were retired in v2.13.0."""
    for pid in ('pater_noster', 'ave_maria', 'memorare', 'saint_michael',
                'saint_raphael', 'saint_anthony', 'anima_christi',
                'confiteor', 'benedictio'):
        assert not hasattr(game_divine.DivineMixin, f'_prayer_{pid}'), (
            f"stale _prayer_{pid} handler must not be re-added"
        )


def test_altar_buc_upgrade_and_identify_are_gone():
    assert not hasattr(game_divine.DivineMixin, '_altar_buc_upgrade')
    assert not hasattr(game_divine.DivineMixin, '_altar_buc_identify')


def test_state_pray_is_gone():
    import game_states
    assert not hasattr(game_states, 'STATE_PRAY')
    # And the replacement Y/N state is registered.
    assert hasattr(game_states, 'STATE_INTERCESSION_PROMPT')


# ---------------------------------------------------------------------------
# _iter_equipped helper (v2.13.0)
# ---------------------------------------------------------------------------

class _StubItem:
    def __init__(self, buc='uncursed', name='stub'):
        self.buc = buc
        self.name = name


class _StubPlayer:
    def __init__(self):
        self.weapon = None
        self.ranged_weapon = None
        self.shield = None
        self.armor_slots = [None] * 8
        self.accessory_slots = [None] * 4
        self.amulet_slot = None
        self.belt_slot = None
        self.inventory = []


def test_iter_equipped_yields_every_slot():
    p = _StubPlayer()
    w  = _StubItem(name='sword');    p.weapon = w
    r  = _StubItem(name='bow');      p.ranged_weapon = r
    s  = _StubItem(name='shield');   p.shield = s
    a1 = _StubItem(name='helm');     p.armor_slots[0] = a1
    a2 = _StubItem(name='boots');    p.armor_slots[5] = a2
    ac = _StubItem(name='ring');     p.accessory_slots[1] = ac
    am = _StubItem(name='amulet');   p.amulet_slot = am
    be = _StubItem(name='belt');     p.belt_slot = be
    got = list(game_divine._iter_equipped(p))
    for it in (w, r, s, a1, a2, ac, am, be):
        assert it in got, f"{it.name} missing from _iter_equipped"


def test_iter_equipped_empty_when_no_gear():
    p = _StubPlayer()
    assert list(game_divine._iter_equipped(p)) == []


# ---------------------------------------------------------------------------
# _altar_drop_reveal — karma-branched drop-on-altar behaviour
# ---------------------------------------------------------------------------

class _Msg:
    def __init__(self, text, kind='info'):
        self.text = text
        self.kind = kind


class _RevealGame:
    """Minimal Game stub for _altar_drop_reveal calls."""
    def __init__(self, karma=0):
        self.karma = karma
        self.messages = []
        # Give it a display_name that just returns the item's name.

    def add_message(self, text, kind='info'):
        self.messages.append(_Msg(text, kind))

    def _display_name(self, item):
        return getattr(item, 'name', 'item')


def _reveal(g, item):
    return game_divine.DivineMixin._altar_drop_reveal(g, item)


def test_altar_drop_reveal_positive_karma_cursed_consumed():
    g = _RevealGame(karma=5)
    it = _StubItem(buc='cursed', name='shortsword')
    consumed = _reveal(g, it)
    assert consumed is True, "positive-karma cursed item must be consumed"
    assert any('altar consumes' in m.text for m in g.messages)


def test_altar_drop_reveal_positive_karma_blessed_shown():
    g = _RevealGame(karma=3)
    it = _StubItem(buc='blessed', name='helm')
    consumed = _reveal(g, it)
    assert consumed is False
    assert getattr(it, 'buc_known', False) is True, (
        "positive-karma reveal on blessed item must set buc_known"
    )
    assert any('truly blessed' in m.text for m in g.messages)


def test_altar_drop_reveal_positive_karma_uncursed_silent():
    g = _RevealGame(karma=5)
    it = _StubItem(buc='uncursed', name='cloak')
    consumed = _reveal(g, it)
    assert consumed is False
    assert g.messages == []
    assert getattr(it, 'buc_known', False) is False


def test_altar_drop_reveal_negative_karma_cursed_lies_blessed():
    g = _RevealGame(karma=-5)
    it = _StubItem(buc='cursed', name='amulet')
    consumed = _reveal(g, it)
    assert consumed is False
    # LIE: it says the item is blessed, but the actual buc stays cursed
    # and buc_known stays False so the player can't tell.
    assert it.buc == 'cursed'
    assert getattr(it, 'buc_known', False) is False
    assert any('holy light' in m.text and 'blessed' in m.text
               for m in g.messages)


def test_altar_drop_reveal_negative_karma_blessed_lies_consumed():
    g = _RevealGame(karma=-3)
    it = _StubItem(buc='blessed', name='ring')
    consumed = _reveal(g, it)
    # LIE: message claims consumed but item stays on the ground.
    assert consumed is False
    assert it.buc == 'blessed'
    assert any('altar consumes' in m.text for m in g.messages)


def test_altar_drop_reveal_neutral_karma_silent():
    for buc in ('cursed', 'blessed', 'uncursed'):
        g = _RevealGame(karma=0)
        it = _StubItem(buc=buc, name='thing')
        consumed = _reveal(g, it)
        assert consumed is False
        assert g.messages == [], (
            f"karma=0 must produce no message; got {[m.text for m in g.messages]}"
        )


def test_altar_drop_reveal_no_buc_field_is_silent():
    g = _RevealGame(karma=5)

    class _NoBUC:
        name = 'gold pile'

    consumed = _reveal(g, _NoBUC())
    assert consumed is False
    assert g.messages == []


# ---------------------------------------------------------------------------
# _resolve_simple_prayer — chain-tier stacking + karma modifiers
# ---------------------------------------------------------------------------
#
# We build a lightweight game-with-real-player stub. The Player class is
# the real one (so restore_hp / restore_sp / restore_mp / add_effect all
# work); the Game stub only supplies the fields _resolve_simple_prayer
# reads (dungeon_level, dungeon.tiles for the L100 branch, _log_chronicle,
# _l100_altars_used, add_message, _apply_prayer_cooldown_quirks, karma).
#
# We call _resolve_simple_prayer AS AN UNBOUND METHOD via the DivineMixin
# to avoid needing the Game's __init__ + all the pygame surfaces.


def _make_prayer_game(*, karma=0, at_altar=False):
    import player as _player_mod
    p = _player_mod.Player()
    # Take some damage / spend some resources so restores have room.
    p.hp = max(1, p.max_hp // 4)
    p.mp = max(0, p.max_mp // 4)
    p.sp = max(0, p.max_sp // 4)

    from dungeon import FLOOR, ALTAR

    class _D:
        pass

    d = _D()
    center = ALTAR if at_altar else FLOOR
    # Player sits at (1, 1); build a 3x3 tile grid.
    d.tiles = [
        [FLOOR, FLOOR, FLOOR],
        [FLOOR, center, FLOOR],
        [FLOOR, FLOOR, FLOOR],
    ]
    p.x, p.y = 1, 1

    g = types.SimpleNamespace()
    g.player = p
    g.dungeon = d
    g.dungeon_level = 5  # not L100; avoid the holy-fire branch
    g.karma = karma
    g.messages = []
    g._l100_altars_used = set()
    g.abaddon_resist_removed_turns = 0
    g.monsters = []
    g.ground_items = []

    def _add(text, kind='info'):
        g.messages.append((text, kind))

    def _log(_text):
        pass

    def _apply_cooldown_quirks():
        # Real one lives on DivineMixin — call it against g so it can see
        # the (real) player.quirk_progress. Quirks default to {} so no
        # halving fires in tests.
        game_divine.DivineMixin._apply_prayer_cooldown_quirks(g)

    def _show_verse(_karma_tier, _key):
        pass

    g.add_message = _add
    g._log_chronicle = _log
    g._apply_prayer_cooldown_quirks = _apply_cooldown_quirks
    g._show_prayer_verse = _show_verse
    return g


def test_simple_prayer_chain0_silent_heavens_no_restore():
    g = _make_prayer_game(karma=0, at_altar=False)
    hp0, sp0, mp0 = g.player.hp, g.player.sp, g.player.mp
    game_divine.DivineMixin._resolve_simple_prayer(g, 0, False)
    assert g.player.hp == hp0
    assert g.player.sp == sp0
    assert g.player.mp == mp0
    assert g.player.prayer_cooldown > 0


def test_simple_prayer_chain1_restores_sp_only():
    g = _make_prayer_game(karma=0, at_altar=False)
    hp0, sp0, mp0 = g.player.hp, g.player.sp, g.player.mp
    game_divine.DivineMixin._resolve_simple_prayer(g, 1, False)
    assert g.player.sp > sp0, "chain 1 must restore SP"
    assert g.player.hp == hp0, "chain 1 must NOT restore HP"
    assert g.player.mp == mp0, "chain 1 must NOT restore MP"


def test_simple_prayer_chain2_also_restores_hp():
    g = _make_prayer_game(karma=0, at_altar=False)
    hp0, sp0, mp0 = g.player.hp, g.player.sp, g.player.mp
    game_divine.DivineMixin._resolve_simple_prayer(g, 2, False)
    assert g.player.sp > sp0
    assert g.player.hp > hp0
    assert g.player.mp == mp0


def test_simple_prayer_chain3_also_restores_mp():
    g = _make_prayer_game(karma=0, at_altar=False)
    hp0, sp0, mp0 = g.player.hp, g.player.sp, g.player.mp
    game_divine.DivineMixin._resolve_simple_prayer(g, 3, False)
    assert g.player.sp > sp0
    assert g.player.hp > hp0
    assert g.player.mp > mp0


def test_simple_prayer_chain4_uncurses_first_worn_cursed_item():
    g = _make_prayer_game(karma=0, at_altar=False)
    # Give the player a cursed worn weapon.
    cursed = _StubItem(buc='cursed', name='iron_sword')
    g.player.weapon = cursed
    game_divine.DivineMixin._resolve_simple_prayer(g, 4, False)
    assert cursed.buc == 'uncursed', "chain 4 must uncurse a worn cursed item"
    assert cursed.buc_known is True


def test_simple_prayer_chain4_blesses_inventory_when_nothing_cursed():
    g = _make_prayer_game(karma=0, at_altar=False)
    # No cursed worn items. Two unblessed inventory items.
    it1 = _StubItem(buc='uncursed', name='scroll')
    it2 = _StubItem(buc='uncursed', name='potion')
    g.player.inventory = [it1, it2]
    game_divine.DivineMixin._resolve_simple_prayer(g, 4, False)
    # At karma=0, blessing count is 1.
    blessed_count = sum(1 for it in (it1, it2) if it.buc == 'blessed')
    assert blessed_count == 1, (
        f"karma=0 chain=4 must bless exactly 1 item; blessed={blessed_count}"
    )


def test_simple_prayer_chain4_bless_scales_with_positive_karma():
    g = _make_prayer_game(karma=6, at_altar=False)
    items = [_StubItem(buc='uncursed', name=f'x{i}') for i in range(5)]
    g.player.inventory = list(items)
    game_divine.DivineMixin._resolve_simple_prayer(g, 4, False)
    # karma=6 -> 1 + karma//3 = 3 blessings.
    blessed = sum(1 for it in items if it.buc == 'blessed')
    assert blessed == 3, f"expected 3 blessings at karma=6; got {blessed}"


def test_simple_prayer_chain4_bless_refused_at_karma_neg5():
    g = _make_prayer_game(karma=-5, at_altar=False)
    items = [_StubItem(buc='uncursed', name=f'x{i}') for i in range(3)]
    g.player.inventory = list(items)
    game_divine.DivineMixin._resolve_simple_prayer(g, 4, False)
    # God turns away -- no items should be blessed.
    assert all(it.buc == 'uncursed' for it in items), (
        "at karma <= -5, chain-4 gift must be refused"
    )


def test_simple_prayer_chain5_adds_shielded():
    g = _make_prayer_game(karma=0, at_altar=False)
    game_divine.DivineMixin._resolve_simple_prayer(g, 5, False)
    assert g.player.has_effect('shielded'), (
        "chain 5 must grant the 'shielded' status effect"
    )


def test_simple_prayer_negative_karma_reduces_sp_gain():
    g_pos = _make_prayer_game(karma=5, at_altar=False)
    g_neg = _make_prayer_game(karma=-5, at_altar=False)
    sp_start_pos = g_pos.player.sp
    sp_start_neg = g_neg.player.sp
    game_divine.DivineMixin._resolve_simple_prayer(g_pos, 1, False)
    game_divine.DivineMixin._resolve_simple_prayer(g_neg, 1, False)
    gained_pos = g_pos.player.sp - sp_start_pos
    gained_neg = g_neg.player.sp - sp_start_neg
    assert gained_pos > gained_neg, (
        f"positive karma must yield more SP than negative "
        f"({gained_pos} vs {gained_neg})"
    )


def test_simple_prayer_altar_doubles_positive_karma_magnitude():
    g_no_altar = _make_prayer_game(karma=5, at_altar=False)
    g_altar    = _make_prayer_game(karma=5, at_altar=True)
    sp_start = g_no_altar.player.sp
    game_divine.DivineMixin._resolve_simple_prayer(g_no_altar, 1, False)
    game_divine.DivineMixin._resolve_simple_prayer(g_altar,    1, True)
    gain_flat  = g_no_altar.player.sp - sp_start
    gain_altar = g_altar.player.sp - sp_start
    # Altar-with-positive-karma must gain MORE SP than the same prayer
    # without an altar (karma is doubled at altars).
    assert gain_altar > gain_flat, (
        f"altar must amplify karma bonus (altar {gain_altar} vs flat {gain_flat})"
    )


# ---------------------------------------------------------------------------
# Divine Intercession — once-per-run gate + success / failure branches
# ---------------------------------------------------------------------------

def _make_intercession_game(*, at_altar=False, karma=0):
    """Build a stub for Divine Intercession success/failure paths.
    We stub the quiz engine so we can drive result manually."""
    import player as _player_mod
    p = _player_mod.Player()
    p.hp = 5
    p.mp = 2
    p.sp = 3
    from dungeon import FLOOR, ALTAR

    class _D:
        pass

    d = _D()
    center = ALTAR if at_altar else FLOOR
    d.tiles = [
        [FLOOR, FLOOR, FLOOR],
        [FLOOR, center, FLOOR],
        [FLOOR, FLOOR, FLOOR],
    ]
    p.x, p.y = 1, 1

    g = types.SimpleNamespace()
    g.player = p
    g.dungeon = d
    g.dungeon_level = 20
    g.karma = karma
    g.messages = []
    g.ground_items = []
    g.monsters = []
    g.state = 'player'
    g.quiz_title = ''
    g._advance_turn_count = 0

    def _add(text, kind='info'):
        g.messages.append((text, kind))

    def _log(_text):
        pass

    def _advance_turn():
        g._advance_turn_count += 1

    g.add_message = _add
    g._log_chronicle = _log
    g._advance_turn = _advance_turn

    class _StubQuiz:
        def __init__(self):
            self.started = None

        def start_quiz(self, **kw):
            self.started = kw

    g.quiz_engine = _StubQuiz()
    # Bind the intercession helpers as methods so success-branch code that
    # calls ``self._spawn_intercession_artifact`` works against the stub.
    g._spawn_intercession_artifact = (
        lambda px, py: game_divine.DivineMixin._spawn_intercession_artifact(
            g, px, py))
    return g


def test_divine_intercession_once_per_run_gate():
    g = _make_intercession_game()
    g.player.divine_intercession_used = True
    game_divine.DivineMixin._start_divine_intercession(g)
    # The state must NOT have changed to prompt (nothing to prompt for).
    assert g.state != 'intercession_prompt'
    assert any('already sought' in m for m, _ in g.messages)


def test_divine_intercession_prompt_transitions_state():
    g = _make_intercession_game()
    game_divine.DivineMixin._start_divine_intercession(g)
    assert g.state == 'intercession_prompt'


def test_divine_intercession_off_altar_uses_threshold_5_at_T5():
    g = _make_intercession_game(at_altar=False)
    game_divine.DivineMixin._confirm_divine_intercession(g, True)
    kw = g.quiz_engine.started
    assert kw['mode'] == 'threshold'
    assert kw['tier'] == 5
    assert kw['threshold'] == 5
    assert kw['total_qs'] == 5
    assert kw['subject'] == 'theology'
    assert g.player.divine_intercession_used is True


def test_divine_intercession_on_altar_uses_escalator_chain():
    g = _make_intercession_game(at_altar=True)
    game_divine.DivineMixin._confirm_divine_intercession(g, True)
    kw = g.quiz_engine.started
    assert kw['mode'] == 'escalator_chain'
    assert kw['tier'] == 1
    assert kw['max_chain'] == 5


def test_divine_intercession_decline_does_not_lock_run():
    g = _make_intercession_game()
    game_divine.DivineMixin._confirm_divine_intercession(g, False)
    assert g.player.divine_intercession_used is False
    assert g.quiz_engine.started is None


def test_intercession_success_full_restore_and_invulnerable():
    g = _make_intercession_game(at_altar=True)
    game_divine.DivineMixin._resolve_intercession_success(g)
    assert g.player.hp == g.player.max_hp
    assert g.player.mp == g.player.max_mp
    assert g.player.sp == g.player.max_sp
    assert g.player.has_effect('invulnerable'), (
        "success must grant the invulnerable status"
    )


def test_intercession_success_clears_debuffs():
    g = _make_intercession_game(at_altar=True)
    g.player.add_effect('poisoned', 5)
    g.player.add_effect('blinded',  5)
    g.player.add_effect('bleeding', 5)
    game_divine.DivineMixin._resolve_intercession_success(g)
    for eff in ('poisoned', 'blinded', 'bleeding'):
        assert not g.player.has_effect(eff), (
            f"success must clear debuff {eff}"
        )


def test_intercession_success_spawns_artifact_or_falls_back():
    g = _make_intercession_game(at_altar=True)
    game_divine.DivineMixin._resolve_intercession_success(g)
    # Should either drop an item on the ground OR log a "no relic" chronicle;
    # the artifact pool is nontrivial so we expect at least one ground item.
    assert len(g.ground_items) >= 1, (
        "intercession success should place a relic at the player's feet"
    )


def test_intercession_failure_curses_all_equipped_and_blinds():
    g = _make_intercession_game(at_altar=False)
    # Load up equipment slots.
    from items import Weapon, Shield
    w = Weapon({'id': 'testblade', 'name': 'blade', 'symbol': ')',
                'color': [200, 200, 200], 'item_class': 'weapon',
                'weight': 3, 'weapon_class': 'sword'})
    s = Shield({'id': 'testshield', 'name': 'buckler', 'symbol': '[',
                'color': [180, 180, 180], 'item_class': 'shield',
                'weight': 5, 'ac_bonus': 1})
    g.player.weapon = w
    g.player.shield = s
    game_divine.DivineMixin._resolve_intercession_failure(g)
    for it in (w, s):
        assert it.buc == 'cursed', f"{it.name} must be cursed after smite"
        assert it.buc_known is True
    assert g.player.has_effect('blinded')
    assert g.player.status_effects.get('blinded', 0) >= 50


# ---------------------------------------------------------------------------
# invulnerable status blocks damage
# ---------------------------------------------------------------------------

def test_invulnerable_blocks_all_damage():
    import player as _player_mod
    p = _player_mod.Player()
    hp0 = p.hp
    p.add_effect('invulnerable', 5)
    actual = p.take_damage(50, 'physical')
    assert actual == 0
    assert p.hp == hp0
    # Also blocks other damage types.
    p.take_damage(50, 'fire')
    p.take_damage(50, 'poison')
    assert p.hp == hp0


# ---------------------------------------------------------------------------
# Player field bootstrap
# ---------------------------------------------------------------------------

def test_player_has_divine_intercession_flag():
    import player as _player_mod
    p = _player_mod.Player()
    assert hasattr(p, 'divine_intercession_used')
    assert p.divine_intercession_used is False
