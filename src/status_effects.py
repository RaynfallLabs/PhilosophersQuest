"""
Status effect registry and tick logic.

Effect durations are stored in player.status_effects as:
  n > 0  = active for n more turns
  -1     = permanent (intrinsic)
  absent / 0 = not active

All NetHack-style effects are registered here even if their
full mechanics are yet to be wired in -- the UI, tick, and
resistance systems are fully active for all of them.

What a debuff does to the hero's actions is not decided here: the one gate
(action_gate.py) and its data (data/effects.json) do that.
"""

import effect_rules
from lights import status_sight as _light_sight

MAX_EFFECT_DURATION = 60  # hard cap on status effect turns (prevents infinite stacking)

# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

# effect_id -> (display_name, rgb_color, short_description)
EFFECT_INFO: dict[str, tuple] = {
    # ---- Debuffs ----
    'paralyzed':          ('Paralyzed',         (220,  50,  50), 'Cannot move or act'),
    'sleeping':           ('Sleeping',           (100, 100, 210), 'Asleep; woken by damage'),
    'stunned':            ('Stunned',            (225, 155,  50), 'Double vision in quizzes. Your first step falls and your first fumble drops, unless in Guard'),
    'confused':           ('Confused',           (185, 100, 230), 'Steps go astray, but blows land where aimed; quiz words swim, then settle'),
    'blinded':            ('Blinded',            (165, 165, 178), 'Sight radius 1; quiz answers are dark but for a light you move'),
    'hallucinating':      ('Hallucinating',      (210,  85, 230), 'Monsters wear wrong faces; quizzes grow a false answer that fades'),
    'poisoned':           ('Poisoned',           ( 80, 210,  60), 'Losing 2% of max HP per turn'),
    'diseased':           ('Diseased',           (135, 205,  60), 'No rest healing; most heals halved; saps STR/CON'),
    'petrifying':         ('Petrifying',         (205, 205, 130), 'Turning to stone: stiff, then slow, then stone. Oil of Rue cures it'),
    'strangulation':      ('Strangled',          (200,  80,  80), 'Losing 4% of max HP per turn'),
    'fumbling':           ('Fumbling',           (220, 170,  80), 'You drop the first thing you handle, unless in Guard'),
    'slowed':             ('Slowed',             (155, 155, 230), 'Every action takes two turns'),
    'aggravated':         ('Aggravated',         (230, 100,  50), 'All monsters are alerted'),
    'teleportitis':       ('Teleportitis',       (100, 225, 225), 'May randomly teleport (4%/turn)'),
    'feared':             ('Feared',             (200,  80, 200), 'No going nearer or striking what frightens you, unless cornered. Shoot, cast or drink'),
    'charmed':            ('Charmed',            (255, 160, 200), 'You cannot harm your charmer, and walk toward it. Its first wound frees you'),
    'cursed':             ('Cursed',             (120,  40, 160), 'Misses more: -2 to hit'),
    'hexed':              ('Hexed',              (180, 120, 235), 'What you wear will not come off'),
    'knocked_down':       ('Knocked Down',       (215, 165,  90), 'Off your feet, no dodge: your next action is standing up'),
    'forgetting':         ('Mind-Bitten',        (190, 120, 220), 'Something ate a memory. Kill it on this floor to win it back'),
    'footing':            ('Footing',            (200, 220, 190), 'Sure-footed for a moment: cannot be slowed or knocked down'),
    'heal_blocked':       ('Wound Lingers',      (160,  30,  50), 'HP cannot be restored while active (Gae Dearg)'),
    'doom_dot':           ('Doom',               (140,  60, 200), 'Ticking damage as fraction of max HP per turn (Laevateinn)'),
    'weakened':           ('Weakened',           (150, 150,  80), 'Attack damage halved'),
    'bleeding':           ('Bleeding',           (200,  40,  40), 'Losing HP from wounds each turn'),
    'doomed':             ('Doomed',             (100,  20,  20), 'A death-curse; losing 1 HP per ~8 turns'),
    'draining':           ('Draining',           ( 80,  30, 100), 'Ring drains 1 HP per ~6 turns'),
    'burning':            ('Burning',            (245, 100,  20), 'On fire! Losing 2% of max HP per turn'),
    'frozen':             ('Frozen',             ( 80, 200, 245), 'Feet stuck, hands numb, melee halved. A lit torch thaws you'),
    'corroding':          ('Corroding',          (180, 200,  50), 'Acid eats at your gear: one piece at most'),
    'immobilized':        ('Immobilized',        (180, 130,  60), 'Feet held fast: you can still fight and use your hands'),
    'in_pit':             ('In Pit',             (140, 100,  60), 'Stuck in a pit; must climb out'),
    'silenced':           ('Silenced',           (120, 120, 160), 'No voice: no spell, no scroll, no song or call'),
    'empowered':          ('Empowered',          (255, 200,  80), 'Next melee attack deals 3x damage'),
    'berserk':            ('Berserk',            (220,  60,  40), 'Battle-fury: your blows land harder while it lasts'),
    'riposte_armed':      ('Riposte Armed',      (220, 220, 160), 'Next melee hit against you triggers a free counter'),
    'parry_armed':        ('Parry Armed',        (200, 210, 180), 'Quarterstaff defensive stance: +2 AC for 2 turns'),
    # ---- Chain combat v2 (v2.14.0): weapon chain-special statuses ----
    'armor_crack':        ('Armor Cracked',      (220, 180,  60), 'Target takes +25% damage from all sources'),
    # v2.15.0 doc fix: sundered code path is × 0.70 (-30%), not "halved".
    'sundered':           ('Sundered',           (200, 120,  80), 'Broken limb: outgoing damage reduced 30%'),
    'deep_wound':         ('Deep Wound',         (180,  60,  80), '+25% damage taken AND cannot regenerate'),
    'ruptured':           ('Ruptured',           (140,  30,  60), 'Losing 10% max HP per turn; cannot be healed'),
    'impaled':            ('Impaled',            (150, 100,  60), 'Pinned in place; cannot move (can still attack)'),
    'blade_flow':         ('Blade Flow',         (255, 240, 150), 'Next N attacks bypass damage reduction'),
    'melee_dmg_reduction':('Guarded Stance',     (180, 200, 220), 'Incoming melee damage reduced 30%'),
    # v2.15.0: register `reloading` so the status HUD stops rendering
    # "Reloading: N turns" via the raw fallback path. Crossbow-only.
    'reloading':          ('Reloading',          (200, 180, 130), 'Cranking the crossbow — cannot fire this turn'),
    'see_invisible':      ('See Invisible',      (200, 200, 255), 'You can perceive invisible creatures'),
    # ---- Hero special buffs (Phase 3B) ----
    'stand_ac':           ('Spartan Stand',      (255, 215, 80),  '+AC and counter-strike chance'),
    'crit_buff':          ('Rallied Strike',     (255, 100, 100), 'Next attack deals +50% damage'),
    'fear_immune':        ('Fearless',           (220, 60, 40),   'Immune to fear effects'),
    'boomstick_aoe_next': ('Boomstick Loaded',   (200, 90, 30),   'Next shot scatters'),
    'control_immune':     ('Recovering',         (200, 230, 255), 'Shaking it off -- briefly immune to being disabled'),
    # Cooked / power "ward" buffs — a timed bonus to a saving-throw category.
    'save_guard_CON':     ('Body Ward',          (150, 230, 170), 'Bonus to resisting paralysis / sleep / stun'),
    'save_guard_WIS':     ('Mind Ward',          (160, 200, 245), 'Bonus to resisting confusion / fear / charm'),
    'save_guard_DEX':     ('Reflex Ward',        (205, 230, 150), 'Bonus to resisting slow / immobilize'),
    'save_guard_all':     ('Warded',             (210, 230, 255), 'Bonus to all saving throws'),
    # ---- Buffs ----
    'hasted':             ('Hasted',             (245, 245,  60), 'Monsters act half as often'),
    'invisible':          ('Invisible',          (185, 235, 235), 'Harder to hit: 2 points of armor'),
    'levitating':         ('Levitating',         (185, 215, 245), 'Floating; immune to floor traps'),
    'regenerating':       ('Regenerating',       ( 80, 225, 105), 'Recovering 1 HP every 3 turns'),
    'telepathy':          ('Telepathy',          (205, 145, 245), 'All monsters visible on level'),
    'warning':            ('Warning',            (240, 210, 100), 'Sense monsters within 5 tiles'),
    'searching':          ('Searching',          (160, 200, 160), 'Auto-reveal adjacent tiles'),
    'clairvoyant':        ('Clairvoyant',        (245, 205, 105), 'Large area revealed around you; invisible creatures seen'),
    'displacement':       ('Displaced',          (200, 200, 200), 'Monsters may miss your true position'),
    'heroism':            ('Heroic',             (255, 200,  40), 'STR +2; surging with battle-strength'),
    'brilliance':         ('Brilliant',          (140, 180, 255), 'INT +1, WIS +1; mind razor-sharp'),
    'hallucinating_pot':  ('Hallucinating',      (210,  85, 230), 'Monsters wear wrong faces; quizzes grow a false answer that fades'),
    # ---- Accessory-granted permanent buffs ----
    'life_save':          ('Life Save',          (255, 215,  80), 'Survive one killing blow; effect is then spent'),
    'sustained':          ('Sustained',          (150, 230, 170), 'SP drains at half rate; need less food'),
    'truesight':          ('True Sight',         (200, 200, 255), 'See all monsters regardless of invisibility; +2 sight'),
    'dark_vision':        ('Dark Vision',        ( 60,  80, 160), 'Sight radius +4 even in deep darkness'),
    'identify_sight':     ('Identify Sight',     (220, 200, 150), 'Items auto-identified when picked up'),
    'spell_turning':      ('Spell Turning',      (210, 175, 255), 'Reflects 100% of monster-cast debuffs back at attacker'),
    # ---- Active buffs (wand/accessory-granted) ----
    'blessed':            ('Blessed',            (200, 240, 160), 'Combat quiz timer +25%; divine clarity'),
    'inspired':           ('Inspired',           (255, 215,  90), 'Wisdom lent from above: the combat clock runs long'),
    'shielded':          ('Shielded',           (120, 180, 245), '+2 AC; physical damage halved'),
    'fire_shield':        ('Fire Shield',        (245, 120,  40), 'Immune to fire; reflects fire attacks'),
    'cold_shield':        ('Cold Shield',        ( 80, 200, 245), 'Immune to cold; reflects cold attacks'),
    'reflecting':         ('Reflecting',         (220, 220, 180), '50% chance to reflect monster status attacks'),
    'phasing':            ('Phasing',            (180, 180, 220), 'Can walk through walls'),
    'time_stopped':       ('Time Stop',          (245, 220, 100), 'Time is frozen -- monsters cannot act'),
    'invulnerable':       ('Invulnerable',       (255, 240, 160), 'Divine grace — all incoming damage blocked'),
    # ---- Resistances (can be timed or permanent) ----
    'fire_resist':        ('Fire Resist',        (245, 130,  50), 'Halves fire damage; cannot be set alight'),
    'cold_resist':        ('Cold Resist',        (100, 195, 245), 'Halves cold damage; cannot be frozen'),
    'shock_resist':       ('Shock Resist',       (245, 245,  80), 'Halves lightning damage'),
    'poison_resist':      ('Poison Resist',      (100, 245,  80), 'Cannot be poisoned or diseased; halves poison damage'),
    'sleep_resist':       ('Sleep Resist',       (130, 130, 245), 'Immune to sleep and paralysis'),
    'magic_resist':       ('Magic Resist',       (200, 150, 245), 'Halves magic damage; turns aside mind magic'),
    'drain_resist':       ('Drain Resist',       (185,  80, 245), 'Immune to stat drain'),
    'disint_resist':      ('Disint. Resist',     (245, 185, 100), 'Immune to disintegration'),
    # ---- Trophy immunities (permanent; granted by boss-trophy recipes) ----
    'petrify_immune':     ('Stoneproof',         (205, 205, 130), 'Cannot be turned to stone'),
    'confuse_immune':     ('Clear-Headed',       (160, 220, 240), 'Cannot be confused or made to forget'),
    'acid_resist':        ('Acid Resist',        (170, 220,  90), 'Gear and flesh shrug off corrosion'),
    # ---- Story-encounter effects (ENCOUNTER_STORIES_DRAFT J3). Each lasts
    # whole floors or turns as its reward says; none changes a stat. ----
    'porter':             ('Porter',             (190, 160, 110), 'Someone carries part of your load: carry limit +50'),
    'light':              ('Light',              (255, 230, 140), f'A light burns about you: sight +{_light_sight()}, and you are seen from farther'),
    'sickly':             ('Sickly',             (160, 170,  90), 'A low fever: stamina drains twice as fast'),
}

# What each story effect does, read by the systems named (no stat changes).
PORTER_CARRY_BONUS = 50      # Player.get_carry_limit
# The light status's sight (the Light spell, a wand of light, a story's
# lantern): data/lights.json status_sight. Lights do not add up: the
# brightest counts (lights.light_bonus, Player.get_sight_radius).
LIGHT_SIGHT_BONUS = _light_sight()

DEBUFFS: frozenset = frozenset({
    'paralyzed', 'sleeping', 'stunned', 'confused', 'blinded', 'hallucinating',
    'poisoned', 'diseased', 'petrifying', 'strangulation', 'fumbling',
    'slowed', 'aggravated', 'teleportitis',
    'feared', 'charmed', 'cursed', 'weakened', 'bleeding', 'doomed', 'draining',
    'burning', 'frozen', 'corroding', 'immobilized', 'in_pit', 'silenced',
    'hallucinating_pot', 'hexed', 'knocked_down', 'forgetting',
    # v2.15+ audit sync: berserk was double-classified (BUFFS + DEBUFFS).
    # It grants +STR damage but costs HP/turn — treated as a BUFF (below);
    # removed from DEBUFFS so `abjuration`/`cancellation`/`dispel_magic`
    # correctly strip it as an enchantment on the target.
    # Engine wave 3 (2026-05-30): heal_blocked debuff (Gae Dearg's wound).
    # Blocks restore_hp from working on target while active.
    'heal_blocked',
    # Story-encounter debuff (the plague bar lifted at the boundary stone).
    'sickly',
    # v2.15+ audit sync: Laevateinn's doom_dot was in EFFECT_INFO but missing
    # from DEBUFFS. Add so status HUD + strip-debuffs paths see it.
    'doom_dot',
    # Chain combat v2 (v2.14.0): weapon chain-special monster debuffs
    'armor_crack', 'sundered', 'deep_wound', 'ruptured', 'impaled',
    # v2.15.0: crossbow reload cooldown — player-side, not a debuff-buff really
    # but sits in the status_effects dict so tick_all decrements it.
    'reloading',
})

BUFFS: frozenset = frozenset({
    'hasted', 'invisible', 'levitating', 'regenerating', 'telepathy',
    'warning', 'searching', 'clairvoyant', 'displacement', 'heroism', 'brilliance', 'inspired',
    'shielded', 'fire_shield', 'cold_shield', 'reflecting', 'phasing', 'time_stopped', 'blessed',
    'invulnerable',
    'fire_resist', 'cold_resist', 'shock_resist', 'poison_resist',
    'sleep_resist', 'magic_resist', 'drain_resist', 'disint_resist',
    'life_save', 'sustained', 'truesight', 'dark_vision', 'identify_sight', 'spell_turning',
    'riposte_armed', 'parry_armed', 'see_invisible',
    # Hero special buffs (Phase 3B) — these are beneficial timed effects.
    'stand_ac', 'crit_buff', 'fear_immune', 'boomstick_aoe_next', 'berserk',
    # Chain combat v2 (v2.14.0): player-side chain buffs.
    'blade_flow', 'melee_dmg_reduction',
    # Post-lock grace buff (set when a hard-control effect expires).
    'control_immune',
    # The same grace after standing up from a knock-down.
    'footing',
    # Cooked / power "ward" buffs that grant a timed saving-throw bonus.
    'save_guard_CON', 'save_guard_WIS', 'save_guard_DEX', 'save_guard_all',
    # Story-encounter buffs that last whole floors (porter, a bright lantern).
    'porter', 'light',
})

# --- Control / disable effects + D&D-style saving-throw support ---------------
# HARD control = zero/near-zero player actions (the autokill risk): NEGATED on a
# successful save and followed by a grace window. SOFT control = degraded
# actions: HALVED on a save. Both REFRESH (max) instead of stacking, and are
# capped per single application so one failed save is never a death sentence.
#
# NOTE (v2.15+): `stunned` is a SOFT effect in semantics (player still acts:
# data/effects.json gate) but is deliberately kept in HARD_CONTROL
# so that a successful save fully negates it and cannot be re-applied within
# the post-lock grace window. This is an anti-stunlock guarantee — removing
# it would allow fast monsters to stunlock the player to death.
# NOTE (v2.15+): `petrifying` moved into HARD_CONTROL. Its val==1 tick sends
# the '_petrify_death' signal, and half-duration on a save could still kill;
# HARD_CONTROL means a successful CON save NEGATES it outright.
# NOTE (2026-10): `feared` moved into HARD_CONTROL. A feared player could not
# attack at all then (every move was flight), a save only halved it, every
# new hit refreshed it and there was no grace window after: one fear-caster
# was a lock with no answer. Now a save negates it and the usual grace
# window follows.
# Poison, bleeding and burning cost the player this share of max HP a turn
# (at least 1). They were a flat 1 at every depth, which is a third of a
# percent of a deep character's health: a status with no bite.
DOT_SHARE = 0.02
# Turns per point of the `regenerating` status.
REGEN_PERIOD = 3
REGEN_SHARE = 1 / 300          # of max health, each REGEN_PERIOD turns


# Stats a status lends while it lasts: granted when it begins, taken back
# when it ends, both inside this module.
TIMED_STAT_GRANTS: dict = {
    'heroism':    (('STR', 2),),
    'brilliance': (('INT', 1), ('WIS', 1)),
}


def sync_timed_grants(player) -> None:
    """Make the stats a status lends match the statuses actually present.

    The grant used to be made when a timed status began and taken back when
    it ran out. A status can also begin as permanent (an item that grants it)
    and can be removed by a plain pop (taking that item off), and neither of
    those paths granted or took back anything: the Pharaoh's Crook showed
    "Heroic" and gave nothing, and a heroism potion followed by wielding and
    unwielding the Crook left +2 Strength for good, once per potion."""
    held = getattr(player, '_timed_grants_held', None)
    if held is None:
        # first sight of this character (or an older save): whatever is
        # active now has already been granted
        held = {e for e in TIMED_STAT_GRANTS if player.status_effects.get(e, 0) != 0}
        player._timed_grants_held = held
        return
    for effect, grants in TIMED_STAT_GRANTS.items():
        active = player.status_effects.get(effect, 0) != 0
        if active and effect not in held:
            held.add(effect)
            for stat, amt in grants:
                player.apply_stat_bonus(stat, amt)
        elif not active and effect in held:
            held.discard(effect)
            for stat, amt in grants:
                player.apply_stat_bonus(stat, -amt)


def dot_tick(player) -> int:
    return max(1, int(round(getattr(player, 'max_hp', 1) * DOT_SHARE)))


HARD_CONTROL: frozenset = frozenset({
    'paralyzed', 'sleeping', 'immobilized', 'stunned', 'frozen',
    'petrifying', 'feared',
})
SOFT_CONTROL: frozenset = frozenset({'confused', 'charmed', 'slowed', 'weakened', 'forgetting'})
CONTROL: frozenset = HARD_CONTROL | SOFT_CONTROL

# Saving-throw stat per effect (D&D-style): body (CON) / mind (WIS) / reflex (DEX).
SAVE_STAT: dict = {
    'paralyzed': 'CON', 'sleeping': 'CON', 'stunned': 'CON', 'frozen': 'CON',
    'petrifying': 'CON',
    'confused': 'WIS', 'feared': 'WIS', 'charmed': 'WIS',
    'slowed': 'DEX', 'immobilized': 'DEX', 'knocked_down': 'DEX',
    'weakened': 'CON', 'forgetting': 'WIS',
}

# Hard cap on how long a SINGLE control application can last on the player —
# clamps egregious data durations so one failed save is never a death sentence.
CONTROL_CAP: dict = {
    'paralyzed': 4, 'sleeping': 5, 'stunned': 3, 'frozen': 4, 'immobilized': 4,
    'confused': 6, 'feared': 6, 'charmed': 6,
}
# Slowed, Weakened, the stone and a bitten mind (data/effects.json statuses);
# the caps of effects that are not control live there too (STATUS_CAP).
STATUS_CAP: dict = {k: int(v) for k, v in effect_rules.statuses()['caps'].items()}
CONTROL_CAP.update({k: v for k, v in STATUS_CAP.items()
                    if k in ('slowed', 'weakened', 'petrifying', 'forgetting')})
# A second dose runs to the longer of the two, never their sum: ten poison
# bites were 120% of max HP.
REFRESHES: frozenset = frozenset(effect_rules.statuses()['refresh'])
# Turns one action spends of a status (Slowed counts the world's turns).
TICK_STEPS: dict = {k: int(v) for k, v in effect_rules.statuses()['steps'].items()}
# A status that lasts until the hero does something about it.
UNTIL_ACTED: frozenset = frozenset({'knocked_down'})
FOOTING_TURNS: int = int(effect_rules.statuses()['footing_turns'])

GRACE_TURNS = 3  # turns of immunity to re-disable after a hard-control effect ends


def _load_soft_grace() -> dict:
    """Soft control with a recovery of its own, the shape of the hard-control
    grace: effect -> (grace status, turns). Confusion (Brandon 2026-11-19:
    the quiz scramble must never be an auto-kill): a running bout is never
    refreshed, and when it ends, or is cured, the hero is Clear-Headed
    (``confuse_immune``) for a few turns. data/confusion.json 'recovery'."""
    rec = {}
    try:
        import json
        from paths import data_path
        with open(data_path('data', 'confusion.json'), encoding='utf-8') as f:
            rec = json.load(f).get('recovery') or {}
    except (OSError, ValueError):
        rec = {}
    grace = (str(rec.get('status', 'confuse_immune')), max(1, int(rec.get('turns', 3))))
    # A bitten mind (2026-11-22) is a bout of the same shape: one memory a
    # bout, then Clear-Headed, which keeps the next bite off.
    # Slowed and Charmed are bouts too (2026-11-22, "no locks: a bout is
    # never refreshed, and recovery follows it"): after a slowing his
    # Footing, after a charm his Clear Sight.
    footing = max(1, int(effect_rules.statuses()['footing_turns']))
    return {'confused': grace, 'forgetting': grace,
            'slowed': ('footing', footing), 'charmed': ('clear_sight', footing)}


SOFT_GRACE: dict = _load_soft_grace()
CLEAR_HEADED_TURNS: int = SOFT_GRACE['confused'][1]


def _soft_bouts(player) -> set:
    """The soft-control bouts (SOFT_GRACE) running on the hero, so a bout
    ended outside the tick (a cure: a potion, a prayer, a trader) still
    earns its recovery. Kept on the hero; an older save has none yet."""
    bouts = player.__dict__.get('_soft_bouts')
    if not isinstance(bouts, set):
        bouts = set()
        player.__dict__['_soft_bouts'] = bouts
    return bouts


def _grant_recovery(player, effect: str) -> None:
    """``effect``'s bout is over: its grace status for its turns (a
    permanent one, a trophy's Clear-Headed, is left as it is)."""
    _soft_bouts(player).discard(effect)
    status, turns = SOFT_GRACE[effect]
    cur = player.status_effects.get(status, 0)
    if cur == -1:
        return
    player.status_effects[status] = max(int(cur or 0), turns)


def _recover_cured(player) -> None:
    """A bout that is marked running but is gone was cured: the recovery
    now, once."""
    bouts = player.__dict__.get('_soft_bouts')
    if not bouts:
        return
    for effect in list(bouts):
        if effect in SOFT_GRACE and player.status_effects.get(effect, 0) == 0:
            _grant_recovery(player, effect)

# Resistance effects that block specific debuffs from being applied
_RESIST_BLOCKS: dict[str, set] = {
    'poison_resist': {'poisoned', 'diseased'},
    'sleep_resist':  {'sleeping', 'paralyzed'},
    # v2.15+ audit sync: 'drain_resist' now also blocks the `draining` HP tick
    # so the display name (Drain Resist) matches behavior. The `diseased`
    # entry is retained for symmetry with poison_resist's coverage.
    'drain_resist':  {'diseased', 'draining'},
    'fire_resist':   {'burning'},
    'cold_resist':   {'frozen'},
    # The full shields keep off all the resists do, and laying one ends what
    # is there (_QUENCHES): a fire with no claim on him sets nothing alight.
    'fire_shield':   {'burning'},
    'cold_shield':   {'frozen'},
    # 2026: magic_resist now actively blocks mind-affecting / magical debuffs
    # so counterspell + Magic Resist amulets become meaningful.
    'magic_resist':  {'confused', 'charmed', 'silenced', 'feared',
                      'hallucinating', 'hallucinating_pot', 'forgetting'},
    # Boss-trophy immunities. These statuses were granted by trophy recipes
    # but nothing read them, so "permanent immunity" did nothing.
    'petrify_immune': {'petrifying'},
    'confuse_immune': {'confused', 'forgetting'},
    'acid_resist':    {'corroding'},
    'footing':        {'slowed', 'knocked_down'},
}

_QUENCHES = ('fire_shield', 'cold_shield')

# What wear (rust, acid, fire) can touch is read from the item's MATERIAL
# FILE where it has one (data/materials/armor and weapons): its
# material_class, and what it resists (a weapon material's `resistances`,
# an armour material's `protection` under 1: dragonhide does not scorch;
# `corrosion_immune` among its special properties). Rust is
# iron's: iron and steel rust, and so does every iron alloy of the metal and
# rare_metal classes; copper, bronze, tin, silver, gold, hematite (which is
# rust already) and mithril do not, and no leather, cloth, hide, wood or
# magical metal does. The hand-kept name sets below are only the fallback for
# a named piece whose material has no file ("hardwood", "divine bronze"); for
# rust its own `metal` word comes next (_can_rust).
# They used to be the whole rule, and missed most of the materials: canvas,
# cured, boiled and studded leather, spider silk, elven silk, oak and ash
# were all treated as rustable metal (winning-build plan section 2).
_RUST_CLASSES = frozenset({'metal', 'rare_metal'})
_NON_FERROUS = frozenset({
    'copper', 'bronze', 'tempered_bronze', 'tin', 'silver', 'elven_silver',
    'hardened_gold', 'gold', 'hematite', 'mithril',
})
_ACIDPROOF_CLASSES = frozenset({'magical_metal', 'dragon_material', 'exotic_metal'})
_FLAMMABLE_CLASSES = frozenset({'leather', 'studded_leather', 'hide', 'cloth', 'wood',
                                'rare_wood', 'exotic_organic'})

# The fallback (a material with no file): materials that cannot corrode or rust
_RUSTPROOF = frozenset({
    'diamond', 'mithril', 'adamantine', 'dragonbone', 'dragonscale', 'dragon scale',
    'crystal', 'obsidian', 'divine', 'divine silk', 'enchanted plate', 'spectral iron',
})
_ORGANIC = frozenset({
    'cloth', 'leather', 'hide', 'fur', 'silk', 'linen', 'wool', 'padded',
    'enchanted cloth', 'wood', 'hardwood', 'yew', 'ironwood', 'bone', 'fang',
})
# Organic materials don't rust but CAN be damaged by acid
# Rustproof materials are immune to both rust AND acid
_FLAMMABLE = frozenset({
    'cloth', 'leather', 'hide', 'fur', 'silk', 'linen', 'wool', 'padded',
    'enchanted cloth', 'wood', 'hardwood', 'yew', 'bone',
})
# Flammable materials degrade when burning. Ironwood and fang excluded (fire-resistant).


def material_wear(item):
    """(material_class, its own resistances) from the item's material
    file, or None when its material has no file (a named piece's
    "hardwood")."""
    mat = str(getattr(item, 'material', '') or '')
    if not mat:
        return None
    try:
        from items import get_material
        m = get_material('armor', mat) or get_material('weapons', mat)
    except Exception:
        m = None
    if not m:
        return None
    res = {str(r) for r in (m.get('resistances') or ())}
    # An armour material's profile (gear.material_protection, plan 3.3):
    # what it sheds, it does not wear from either.
    res |= {str(k) for k, v in (m.get('protection') or {}).items() if float(v) < 1.0}
    sp = m.get('special_properties') or ()
    if 'corrosion_immune' in sp:
        res.add('corrosion')
    if 'fire_resistant' in sp:
        res.add('fire')
    return str(m.get('material_class', '') or ''), res


def _can_corrode(item) -> bool:
    """Return True if an item can be damaged by acid/corrosion."""
    if _is_light(item):
        return False
    mat = getattr(item, 'material', '')
    wear = material_wear(item)
    if wear is not None:
        cls, res = wear
        return (cls not in _ACIDPROOF_CLASSES and mat not in _RUSTPROOF
                and not res & {'corrosion', 'acid'})
    return mat not in _RUSTPROOF


def is_legend(item) -> bool:
    """A unique or legendary piece: named in the data (``is_unique``) or made
    of the "legendary" stuff of the old named pieces."""
    return bool(getattr(item, 'is_unique', False)) or \
        str(getattr(item, 'material', '') or '').strip().lower() == 'legendary'


def _can_rust(item) -> bool:
    """Return True if an item can be damaged by rust (iron and its alloys).

    The one rust check: the rust trap's water, the rust monster's feelers,
    the Bloomleaf Cloak's ward and the card's "rusts" all ask it. A unique
    or legendary piece is magical and never rusts, whatever it is made of,
    unless its own lore says it does (``"rusts": true`` in its data, read by
    items.lore_rust_ids; Brandon 2026-11-14: "Legendary weapons don't need
    to rust, unless lore says so; they are magical")."""
    if is_legend(item):
        from items import lore_rust_ids
        return str(getattr(item, 'id', '') or '') in lore_rust_ids()
    if _is_light(item):
        return False
    mat = str(getattr(item, 'material', '') or '')
    wear = material_wear(item)
    if wear is not None:
        cls, res = wear
        return cls in _RUST_CLASSES and mat not in _NON_FERROUS and 'rust' not in res
    if mat in _RUSTPROOF or mat in _ORGANIC:
        return False                  # organic materials don't rust
    if any(w in mat for w in ('bronze', 'copper', 'tin', 'silver', 'gold', 'mithril')):
        return False                  # not iron
    # A named piece's own word on what it is made of (its ``metal``, which
    # gear.is_metal reads for the casting tax and the footsteps). A word
    # with no file ("legendary", "enchanted hide", "rubber") used to rust
    # whatever it named: the rust monster flaked the linen Linothorax of
    # Alexander and the Mantle of Elijah to red rust (bug bash WB-D05).
    own = getattr(item, 'metal', None)
    if own is not None:
        return bool(own)
    return any(w in mat for w in ('iron', 'steel'))     # iron, steel, "dark iron"...


def _is_light(item) -> bool:
    """A torch or lantern in the off hand: no plus for wear to take."""
    import lights
    return lights.is_light(item)


def _can_scorch(item) -> bool:
    """Return True if an item can be damaged by fire (flammable materials)."""
    if _is_light(item):
        return False
    mat = getattr(item, 'material', '')
    wear = material_wear(item)
    if wear is not None:
        cls, res = wear
        return cls in _FLAMMABLE_CLASSES and 'fire' not in res
    if mat in _RUSTPROOF:
        return False
    return mat in _FLAMMABLE


def rust_worn_gear(player, source=None, rng=None) -> tuple[str, str] | None:
    """Rust one piece of the hero's worn gear: THE way anything rusts (the
    rust trap's water, a rust monster's feelers; winning-build plan
    section 3.2).

    Nothing rusts on a hero who wears something that keeps rust off
    (Player.is_rustproof: a worn item whose special_properties has
    "rustproof_wearer": true). Otherwise one worn piece that can rust (iron
    and steel; see _can_rust) loses a point through items.wear_down: one
    plus off a weapon, a shield or body armour, one level off a minor piece;
    a smith's repair gives it back.

    `source`: the monster whose touch rusts (its feelers are named in the
    line), or None for water. Returns (message, kind), or None when nothing
    worn can rust."""
    import random as _random
    rng = rng or _random
    from hud_context import item_bare_name
    keeper = player.rustproof_item() if hasattr(player, 'rustproof_item') else None
    worn = [getattr(player, 'weapon', None), getattr(player, 'ranged_weapon', None),
            getattr(player, 'shield', None)] + list(getattr(player, 'armor_slots', None) or [])
    targets = []
    for it in worn:
        if it is not None and all(it is not t for t in targets) and _can_rust(it):
            targets.append(it)
    if not targets:
        return None
    if keeper is not None:
        return (f"Your {item_bare_name(player, keeper)} keeps the rust from your gear.", 'success')
    item = rng.choice(targets)
    name = item_bare_name(player, item)          # as the player knows it
    from items import wear_down
    import gear
    minor = getattr(item, 'item_class', '') == 'armor' and not gear.is_core(item)
    loss = '(-1 level)' if minor else '(-1 enchantment)'
    if source is not None:
        from monster import the_name
        who = the_name(source)
        if wear_down(item):
            return (f"{who}'s feelers brush your {name}, and good steel flakes to red rust! {loss}",
                    'danger')
        return (f"{who}'s feelers brush your {name}. It is pitted with rust, but it holds.",
                'warning')
    if wear_down(item):
        return (f"Your {name} rusts! {loss}", 'danger')
    return (f"Your {name} is corroded but holds together.", 'warning')


def _scorch_random_gear(player) -> tuple[str, str] | None:
    """Fire scorches one random equipped flammable item. Returns a message or None."""
    import random
    targets = []
    if player.weapon and _can_scorch(player.weapon):
        targets.append(('weapon', player.weapon))
    if player.shield and _can_scorch(player.shield):
        targets.append(('shield', player.shield))
    for i, slot in enumerate(player.armor_slots):
        if slot and _can_scorch(slot):
            targets.append((f'armor_{i}', slot))
    if not targets:
        return None
    if random.random() > 0.20:
        return None
    _, item = random.choice(targets)
    from hud_context import item_bare_name
    name = item_bare_name(player, item)      # as the player knows it
    from items import wear_down
    if wear_down(item):
        return (f'Fire scorches your {name}! (-1 enchantment)', 'danger')
    return (f'Fire licks at your {name}, but it holds.', 'warning')


def note_stat_drain(player, stat: str, amount: int = 1) -> None:
    """Remember a stat point a drain, a poison or a disease took, so a
    physician can give it back (the 'restore' service, game_traders.py).
    Strength lost this way is kept in ``_str_lost_to_disease``, which the
    Potion of Restore Strength reads; everything else in ``drained``."""
    if amount <= 0:
        return
    if stat == 'STR':
        player._str_lost_to_disease = int(getattr(player, '_str_lost_to_disease', 0) or 0) + amount
        return
    d = player.__dict__.setdefault('drained', {})
    d[stat] = int(d.get(stat, 0) or 0) + amount


def restore_drained(player) -> int:
    """Give back every stat point a drain, a poison or a disease took
    (note_stat_drain), and the life the dead drained (AI-1: left in
    ``_last_life_restored``): the physician's 'restore' service and the
    Water of Epidaurus both call this. Returns the stat points restored."""
    n = 0
    s = int(getattr(player, '_str_lost_to_disease', 0) or 0)
    if s:
        player.apply_stat_bonus('STR', s)
        player._str_lost_to_disease = 0
        n += s
    for stat, v in list((player.__dict__.get('drained') or {}).items()):
        if int(v or 0) > 0:
            player.apply_stat_bonus(stat, int(v))
            n += int(v)
    player.__dict__['drained'] = {}
    # The life the dead drained (src/life_drain.py, AI-1) comes back with
    # them, all of it; what came back is left for the caller's line.
    try:
        import life_drain
        player._last_life_restored = life_drain.restore(player)
    except ImportError:
        pass
    return n


def _corrode_random_gear(player) -> tuple[str, str] | None:
    """Acid eats at one random equipped item. Returns a message or None."""
    import random
    targets = []
    # Collect all equipped items that can corrode
    if player.weapon and _can_corrode(player.weapon):
        targets.append(('weapon', player.weapon))
    if player.shield and _can_corrode(player.shield):
        targets.append(('shield', player.shield))
    for i, slot in enumerate(player.armor_slots):
        if slot and _can_corrode(slot):
            targets.append((f'armor_{i}', slot))
    if not targets:
        return None
    # 25% chance per tick to actually degrade something
    if random.random() > 0.25:
        return None
    _, item = random.choice(targets)
    from hud_context import item_bare_name
    name = item_bare_name(player, item)      # as the player knows it
    from items import wear_down
    if wear_down(item):
        return (f'Acid eats at your {name}! (-1 enchantment)', 'danger')
    return (f'Acid sizzles on your {name}, but it holds.', 'warning')

# Damage type -> immunity status effect (first match wins; fire_shield overrides fire_resist)
# Fire is NOT here: fire_resist halves fire damage (DAMAGE_HALVED below). It
# used to be a full immunity, which made a floor-10 ring or one drink of
# Fafnir's Blood switch off every fire attack in the game, Amon's and
# Abaddon's included. The temporary fire_shield is still a full immunity.
#
# 2026-10 balance pass: cold, lightning, poison and magic followed fire. A
# resistance is half damage; only the temporary elemental shields and
# drain_resist are still complete. (poison_resist still stops the poisoned
# and diseased STATUSES outright; it is direct poison damage, a breath or a
# cloud, that is now halved.)
DAMAGE_IMMUNITY: dict[str, str] = {
    'drain':     'drain_resist',
}

# Damage type -> status that halves it (rounded up).
DAMAGE_HALVED: dict[str, str] = {
    'fire':      'fire_resist',
    'cold':      'cold_resist',
    'lightning': 'shock_resist',
    'poison':    'poison_resist',
    'magic':     'magic_resist',
}

# Additional damage-type immunities granted by shield effects (checked separately)
SHIELD_IMMUNITY: dict[str, str] = {
    'fire': 'fire_shield',
    'cold': 'cold_shield',
}

# Messages shown when a timed effect expires
_EXPIRE_MSGS: dict[str, tuple] = {
    'paralyzed':      ('You can move again.',                    'info'),
    'sleeping':       ('You wake up!',                           'info'),
    'stunned':        ('Your head clears -- no longer stunned.',  'info'),
    'confused':       ('Your mind sharpens. Confusion gone, and you are Clear-Headed for a moment.', 'info'),
    'blinded':        ('Your vision returns!',                   'success'),
    'hallucinating':  ('Reality snaps back into focus.',         'info'),
    'poisoned':       ('The poison leaves your body.',           'success'),
    'diseased':       ('You recover from the disease.',          'success'),
    'strangulation':  ('You gasp free -- strangulation ends.',    'success'),
    'fumbling':       ('Your hands are steady again.',            'info'),
    'slowed':         ('You are moving at normal speed.',        'info'),
    'aggravated':     ('The monsters calm down.',                'info'),
    'teleportitis':   ('The teleportation urge fades.',          'info'),
    'hasted':         ('You slow back to normal speed.',         'info'),
    'invisible':      ('You become visible again.',              'info'),
    'levitating':     ('You float back to the ground.',          'info'),
    'regenerating':   ('Your regeneration fades.',               'info'),
    'telepathy':      ('Your telepathy fades.',                  'info'),
    'warning':        ('Your danger sense fades.',               'info'),
    'searching':      ('You stop searching automatically.',      'info'),
    'clairvoyant':    ('Your clairvoyance fades.',               'info'),
    'displacement':   ('Your displacement aura fades.',          'info'),
    'shielded':       ('Your shield barrier dissipates.',        'info'),
    'fire_shield':    ('The flames around you die down.',        'info'),
    'cold_shield':    ('The frost shell around you melts.',      'info'),
    'reflecting':     ('Your reflective aura fades.',            'info'),
    'phasing':        ('You feel solid again.',                  'info'),
    'time_stopped':   ('Time resumes its flow.',                 'info'),
    'invulnerable':   ('The divine shield around you fades.',    'info'),
    'blessed':        ('The divine clarity fades.',              'info'),
    'inspired':       ('The Guiding Hand Lifts. Your Wisdom Is Your Own Again.', 'warning'),
    'feared':         ('Your fear subsides.',                    'info'),
    'charmed':        ('The charm over you breaks.',             'info'),
    'cursed':         ('The curse lifts.',                       'success'),
    'hexed':          ('The hex lifts. What you wear is yours to take off.', 'success'),
    'forgetting':     ('The thing is out of your head, and you are Clear-Headed for a moment.', 'info'),
    'weakened':       ('Your strength returns.',                 'info'),
    'bleeding':       ('Your wounds close.',                     'success'),
    'heroism':        ('The heroic surge fades. STR returns.',   'info'),
    'brilliance':     ('Your mind settles. INT and WIS return.', 'info'),
    'doomed':         ('The doom curse has lifted.',             'success'),
    'draining':       ('The ring stops draining your life.',     'success'),
    'burning':        ('The flames are extinguished.',           'success'),
    'frozen':         ('The ice cracks -- you can move freely!',  'success'),
    'sustained':      ('The deep fullness fades; hunger comes at its usual pace again.', 'info'),
    'truesight':      ('Your true sight fades.',                 'info'),
    'dark_vision':    ('Your dark vision fades.',                'info'),
    'spell_turning':  ('Your spell turning aura dissipates.',   'info'),
    'corroding':      ('The acid neutralizes.',                 'success'),
    'immobilized':    ('You wrench free!',                      'success'),
    'in_pit':         ('You climb out of the pit.',             'info'),
    'silenced':       ('You find your voice again.',            'success'),
    'hallucinating_pot': ('Reality snaps back into focus.',     'info'),
    'berserk':        ('The fury fades. You feel drained.',     'warning'),
    'porter':         ('Nobody is carrying your load any more.', 'info'),
    'light':          ('The light about you fades.',             'info'),
    'sickly':         ('The fever breaks.',                     'success'),
    # v2.15+ audit sync: fill in expire messages that had been missing.
    'doom_dot':          ('The doom-tick releases you.',              'success'),
    'petrifying':        ('You feel your flesh soften back to life.', 'success'),
    'armor_crack':       ('The armor cracks reseal.',                 'info'),
    'sundered':          ('The sundered limb steadies.',              'info'),
    'deep_wound':        ('The deep wound finally closes.',           'success'),
    'ruptured':          ('The rupture stems -- you can be healed again.', 'success'),
    'impaled':           ('You wrench free of the impalement!',       'success'),
    'heal_blocked':      ('Your wounds are willing to close once more.', 'success'),
    'blade_flow':        ('The blade-flow subsides.',                 'info'),
    'save_guard_CON':    ('Your Body Ward fades.',                    'info'),
    'save_guard_WIS':    ('Your Mind Ward fades.',                    'info'),
    'save_guard_DEX':    ('Your Reflex Ward fades.',                  'info'),
    'save_guard_all':    ('Your Warded aura fades.',                  'info'),
    'fear_immune':       ('Fear can find you again.',                 'info'),
    'control_immune':    ('Your footing steadies -- you are fully back in the fight.', 'info'),
    'parry_armed':       ('Your parry stance lowers.',                'info'),
    'riposte_armed':     ('Your riposte instinct settles.',           'info'),
    'see_invisible':     ('Invisible creatures fade from your sight.', 'info'),
    'identify_sight':    ('Your identify-sight fades.',               'info'),
    'life_save':         ('The life-save ward is spent.',             'warning'),
    'reloading':         ('The crossbow is cocked and ready.',        'info'),
    'boomstick_aoe_next':('The scatter charge dissipates.',           'info'),
    'crit_buff':         ('Your rallied strength fades.',             'info'),
    'stand_ac':          ('You break your Spartan Stand.',            'info'),
    'melee_dmg_reduction':('Your guarded stance drops.',              'info'),
}

# The wards (MONSTERS AND MAGIC 2026-11-19: data/wards.json, src/wards.py):
# each is a buff the HUD shows, the tick runs down and Dispel strips; and
# what Loosed (free_action), Wakeful and Clear Sight keep off. The monster
# gates (attack_gates.py) are named here for the Look screen.
import wards as _wards                                   # noqa: E402
for _k, _v in _wards.status_registry().items():
    EFFECT_INFO.setdefault(_k, _v)
for _k, _v in _wards.expire_messages().items():
    _EXPIRE_MSGS.setdefault(_k, _v)
for _k, _v in _wards.resist_blocks().items():
    _RESIST_BLOCKS.setdefault(_k, set(_v))
BUFFS = BUFFS | frozenset(_wards.status_registry())
EFFECT_INFO.setdefault('unstrung', ('Unstrung', (170, 150, 120), 'No bow, sling or thrown weapon will answer it'))
EFFECT_INFO.setdefault('babbled', ('Babbling', (190, 150, 210), 'Its pack or band cannot fight together'))
EFFECT_INFO.setdefault('gate_grace', ('Steadying', (200, 200, 200), 'Shakes off the next silence or unstringing'))


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------

def _gall_saves_sight(player) -> bool:
    """Raphael's Gall (Book of Tobit): the first time the eyes would go
    dark, the gall in the pack is used up instead, and they do not."""
    inv = list(getattr(player, 'inventory', None) or ())
    gall = next((i for i in inv if getattr(i, 'cures_blindness_once', False)
                 or getattr(i, 'id', '') == 'raphaels_gall'), None)
    if gall is None:
        return False
    try:
        player.remove_from_inventory(gall)
    except Exception:
        try:
            player.inventory.remove(gall)
        except ValueError:
            return False
    game = getattr(player, '_combat_game_ref', None)
    if game is not None and hasattr(game, 'add_message'):
        game.add_message("The dark comes over your eyes, and the fish's gall in your pack "
                         "goes cold and is gone. The dark goes with it.", 'success')
    return True


def apply_effect(player, effect: str, duration: int, cap: int | None = None) -> bool:
    """
    Try to apply *effect* for *duration* turns (-1 = permanent) to *player*.
    Returns True if applied, False if blocked by resistance or already permanent.
    ``cap`` lets a buff run past MAX_EFFECT_DURATION, up to ``cap`` turns: a
    cooked meal's power lasts as long as its rules say (cooking_rules.json),
    not the 60 turns that stop a potion or a wand stacking forever.
    """
    if effect == 'cursed':
        effect = 'hexed'               # on the hero a curse is a hex; Cursed is a monster's
    if effect in SOFT_GRACE and duration != 0:
        # A bout cured since the last tick earns its Clear-Headed turns
        # before anything can lay a new one on (confusion's recovery).
        _recover_cured(player)
    for resist, blocked in _RESIST_BLOCKS.items():
        if effect in blocked and player.has_effect(resist):
            return False
    if effect == 'blinded' and duration != 0 and _gall_saves_sight(player):
        return False
    if effect == 'burning' and duration != 0:
        # Body armour that will not catch (dragonscale: gear_rules wards
        # 'flame') never lets the hero burn, whatever set the fire: a
        # monster's blow (Monster._apply_attack_effect says its line), a
        # trap, a vent, a chest (round 3, "it's fire, make it so").
        try:
            import gear as _gear
            if _gear.ward_against(player, None, 'burning') is not None:
                return False
        except Exception:
            pass

    sync_timed_grants(player)
    current = player.status_effects.get(effect, 0)
    if current == -1:
        return False  # permanent -- can't be changed

    if effect in UNTIL_ACTED:
        # Down until he stands: never twice, and not again while he has his
        # footing back.
        if duration == 0 or current > 0 or player.status_effects.get('footing', 0):
            return False
        player.status_effects[effect] = 1
        return True
    if duration == -1:
        player.status_effects[effect] = -1
        sync_timed_grants(player)
    elif effect in CONTROL:
        # (A price the game sets may pass the cap: its caller gives ``cap``.)
        most = cap or CONTROL_CAP.get(effect)
        if most is not None:
            duration = min(duration, most)
        if effect in HARD_CONTROL:
            # Hard control cannot be re-applied OR refreshed while you are already
            # locked, nor within the post-lock grace window. This GUARANTEES that
            # every bout of hard control is followed by free turns — no permalock
            # no matter how reliably a monster re-applies. Core autokill fix.
            if current > 0 or player.status_effects.get('control_immune', 0) > 0:
                return False
            player.status_effects[effect] = min(duration, MAX_EFFECT_DURATION)
        elif effect in SOFT_GRACE:
            # Confusion (the quiz scramble) is a bout, like hard control: it
            # is not refreshed while it runs, and its recovery (Clear-Headed,
            # which blocks it above) follows it, so a confusing monster cannot
            # keep the hero scrambled back to back.
            if current > 0:
                return False
            if duration <= 0:
                return False
            player.status_effects[effect] = min(duration, MAX_EFFECT_DURATION)
            _soft_bouts(player).add(effect)
        else:
            # Soft control (you still act): refresh to the larger value, never stack.
            player.status_effects[effect] = min(max(current, duration), MAX_EFFECT_DURATION)
    else:
        # Statuses that lend a stat for their duration grant it HERE, once,
        # when the status begins, so that the grant and the removal at expiry
        # can never come apart. They used to be granted by each caller, and
        # the cooking path did not: every "Heroic" or "Brilliant" meal ended
        # by taking away two STR, or a point each of INT and WIS, for good.
        limit = max(MAX_EFFECT_DURATION, int(cap)) if cap else MAX_EFFECT_DURATION
        if effect in STATUS_CAP:
            # One dose lasts this long at most, unless its caller sets the price.
            limit = int(cap) if cap else STATUS_CAP[effect]
        if effect in REFRESHES:
            player.status_effects[effect] = max(current, min(duration, limit))
        else:
            player.status_effects[effect] = min(current + duration, limit)
        sync_timed_grants(player)
    if not current and player.status_effects.get(effect, 0):
        effect_rules.opened(player, effect)
    if effect in _QUENCHES and player.status_effects.get(effect, 0):
        for put_out in _RESIST_BLOCKS[effect]:
            player.status_effects.pop(put_out, None)
    return True


# What a cure lifts: every debuff but the crossbow's crank and the pit he
# stands in.
AILMENTS: frozenset = DEBUFFS - {'reloading', 'in_pit'}
# Which one a cure of ONE lifts first (Cleanse): what kills, then what
# stops him, then the rest.
_URGENT = ('petrifying', 'strangulation', 'ruptured', 'doom_dot', 'paralyzed', 'sleeping',
           'poisoned', 'bleeding', 'burning', 'frozen', 'knocked_down', 'hexed', 'charmed',
           'feared', 'stunned', 'slowed', 'weakened', 'silenced', 'forgetting')


def ailments_on(player) -> list:
    """The ailments a cure can lift, the most urgent first. One with no end
    (-1: the gear he wears holds it on him) goes with the gear, not a cure."""
    on = [e for e, v in player.status_effects.items() if v > 0 and e in AILMENTS]
    return sorted(on, key=lambda e: (_URGENT.index(e) if e in _URGENT else len(_URGENT), e))


# What the hero's own statuses become on a monster they are turned back on.
# A countdown would kill it outright; the others are the hero's alone.
_REFLECTS_AS = {'petrifying': ('paralyzed', 2), 'forgetting': ('confused', None),
                'knocked_down': ('stunned', 2), 'hexed': ('cursed', None)}


def reflected(effect: str, turns: int) -> tuple:
    """``(status, turns)`` for an effect thrown back at the monster that
    laid it."""
    to, fixed = _REFLECTS_AS.get(effect, (effect, None))
    return to, (fixed if fixed is not None else turns)


def end_bout(player, effect: str) -> None:
    """``effect`` is over early for a reason of the world's (its owner died,
    his wound broke its charm, the hero thawed): gone, with the recovery
    that follows it at the tick."""
    if not player.status_effects.pop(effect, None):
        return
    effect_rules.ended(player, effect)
    if effect in HARD_CONTROL:
        player.status_effects['control_immune'] = GRACE_TURNS
    if effect in SOFT_GRACE:
        _grant_recovery(player, effect)


def turns_now(player, effect: str, asked: int) -> int:
    """The turns of ``effect`` the hero has now, for the line that lays it:
    the cap, what was left already and a doubled haste all show, so what is
    said is what he has (``asked`` when it has no count: it is for good)."""
    now = int((getattr(player, 'status_effects', None) or {}).get(effect, 0) or 0)
    return now if now > 0 else asked


def apply_penalty(player, effect: str, turns: int) -> None:
    """Apply an effect the player has EARNED as the stated cost of their own
    action (a failed identification, a botched spellbook), for exactly
    `turns` turns.

    apply_effect caps control effects (stunned at 3 turns) and refuses them
    during the grace window. Those rules stop monsters from locking a player
    down; they are not meant to shorten a price the game has just announced.
    The identify backlash said "Stunned (10 turns)" and lasted two.
    """
    had = int(player.status_effects.get(effect, 0) or 0)
    player.status_effects[effect] = max(int(turns), had)
    if not had:
        effect_rules.opened(player, effect)
        # His own doing: the double vision only, never a fall or a drop
        # (Brandon, 2026-11-22: a failed identification is not a chore).
        effect_rules.self_inflicted(player, effect)


# Save-feedback flavor: the player should FEEL which stat saved them (body /
# will / reflexes) without seeing dice or DCs. Keyed by the save stat.
_SAVE_FLAVOR: dict = {
    'CON': 'Your hardy constitution',
    'WIS': 'Your strong will',
    'DEX': 'Your quick footwork',
}
# Natural-language noun per effect so messages read as flavor, not effect ids.
# v2.15+ audit sync: 'stunned' noun changed from 'daze' to 'stun' so apply/expire
# messages match the effect id (expire says "no longer stunned").
_EFFECT_NOUN: dict = {
    'paralyzed': 'paralysis', 'sleeping': 'drowsiness', 'stunned': 'stun',
    'frozen': 'creeping frost', 'immobilized': 'grip', 'petrifying': 'petrification',
    'confused': 'confusion', 'feared': 'dread', 'charmed': 'charm',
    'slowed': 'sluggishness',
    # Effects with no save, named for the family-ward line ('The poison
    # cannot take hold of you.').
    'poisoned': 'poison', 'diseased': 'disease', 'burning': 'fire',
    'blinded': 'blindness', 'weakened': 'weakness', 'hallucinating': 'false sight',
    'silenced': 'silence', 'teleportitis': 'slipping',
    'knocked_down': 'blow', 'forgetting': 'feeding', 'hexed': 'hex',
}

# Held Fast (AI-3, src/holds.py): a coil, a gullet or a drowning grip. HARD
# control, so a DEX save slips it, it lasts at most CONTROL_CAP turns and the
# grace follows it; not a DEBUFF (it is a grip, not a curse a cure lifts: the
# holder's death, the hero's blow or his struggle ends it).
EFFECT_INFO.setdefault('held', ('Held', (190, 120, 80),
                                'In its grip: you cannot walk away. Strike the holder hard, or struggle free'))
_EXPIRE_MSGS.setdefault('held', ('The grip slackens, and you tear yourself free.', 'success'))
_EFFECT_NOUN.setdefault('held', 'grip')
HARD_CONTROL = HARD_CONTROL | frozenset({'held'})
CONTROL = HARD_CONTROL | SOFT_CONTROL
CONTROL_CAP.setdefault('held', 4)
SAVE_STAT.setdefault('held', 'DEX')
NEGATED_BY_SAVE: frozenset = HARD_CONTROL | frozenset({'knocked_down', 'forgetting'})
# The Caster's Book (AI-3, src/caster_ai.py): a ward raised about a caster.
EFFECT_INFO.setdefault('spell_ward', ('Warded', (170, 170, 230),
                                      'A ward turns weapons aside: blows land weak; spells pass it'))


def _family_ward(player, source, effect: str, gaze: bool) -> tuple[int, float]:
    """(save bonus, duration share) the hero's monster-family knowledge
    gives against `effect` from `source` (src/family_edges.py): a ward of
    +N on the save, outside the +5 cap of Player.save_bonus_for because it
    is earned against one family only, and a share of the duration (0.5:
    wears off twice as fast; 0: it never takes hold). A gaze also counts
    the ward against the killing gaze. No source, no family ward; a
    circle's boon (the Hellward Gate's Unbent Mind: "from anything") still
    counts, so a confusion or fear with no monster behind it (a bad meal)
    meets it too. family_edges.save_bonus gives only the circle part when
    `source` is None."""
    try:
        import family_edges
    except ImportError:
        return 0, 1.0
    # Quiet: the ward's line is said only once the save has held
    # (_say_ward_held), never before the roll.
    bonus = family_edges.save_bonus(player, source, effect, quiet=True)
    bonus += (family_edges.save_bonus(player, source, 'gaze', quiet=True)
              if (gaze and source is not None) else 0)
    share = family_edges.duration_mult(player, source, effect) if source is not None else 1.0
    return bonus, share


def _say_ward_held(player, source, effect: str, gaze: bool) -> None:
    """The family ward against `effect` (and a gaze's ward) held: its line
    ("Grave-Salt: ...") is queued, once per creature. Never on a failed
    save: "The paralysis takes hold!" was followed by "Grave-Salt: the salt
    in your pocket keeps the grave's grip off you." (3.3.3 lore audit)."""
    if source is None:
        return
    try:
        import family_edges
    except ImportError:
        return
    family_edges.ward_held(player, source, effect)
    if gaze:
        family_edges.ward_held(player, source, 'gaze')


def apply_debuff_with_save(player, effect: str, duration: int, dc: int,
                           source=None, gaze: bool = False,
                           lethal: bool = False) -> tuple[bool, str]:
    """Apply a MONSTER-inflicted debuff gated by a D&D-style saving throw.

    Two-gate model: the caller already passed the monster's to-apply check
    (effect_chance — its skill at landing the blow). Here the player rolls
    d20 + stat-modifier vs ``dc``:
      - HARD control (paralyze/sleep/immobilize/stun/freeze): a save NEGATES it.
      - SOFT control (confuse/charm/slow/weaken): a save HALVES the duration.
      - a knock-down and a bitten mind: a save NEGATES it (there is no half).
      - effects with no SAVE_STAT entry (poison, bleed, etc.): applied directly.

    Returns (applied, message). The message is FLAVOR, not math — on a save the
    player hears their constitution/will/reflexes hold; on a failure they hear
    the effect take hold. Always routes application through ``player.add_effect``
    so existing defenses + refresh/cap/grace still apply on top.
    """
    import random as _r
    stat = SAVE_STAT.get(effect)
    noun = _EFFECT_NOUN.get(effect, effect.replace('_', ' '))
    # ``source`` is the monster inflicting it (when known): the hero's ward
    # against that monster's family (Grave-Salt, Antivenom...) applies.
    _ward, _share = _family_ward(player, source, effect, gaze)
    if stat is None and _ward > 0:
        # A ward against an effect with no save (poison, burning, blinding)
        # shortens it instead (family_edges.no_save_ward_share: a share off
        # a point, at most half). A duration technique for the same effect
        # does not stack with it: the stronger of the two counts.
        import family_edges
        _share = min(_share, family_edges.no_save_ward_share(_ward))
        _ward = 0
        _say_ward_held(player, source, effect, gaze)     # it did shorten it
    if _share <= 0.0:
        return False, f"The {noun} cannot take hold of you."
    if _share < 1.0:
        duration = max(1, int(round(int(duration) * _share)))
    if stat is None:
        # v2.15+ audit sync: effects without a SAVE_STAT entry (poison, bleed,
        # burn, disease, etc.) previously bypassed save_bonus entirely. Now the
        # CON save_bonus reduces the applied duration by a flat amount (min 1),
        # so gear/quirks/ward gradients still soften body afflictions. This
        # preserves the "resource loss IS the penalty" rule (DoTs still land)
        # but rewards a built-out CON save profile with shorter-lived DoTs.
        _sb = int(player.save_bonus_for('CON')) if hasattr(player, 'save_bonus_for') else 0
        _dur = max(1, int(duration) - _sb)
        applied = player.add_effect(effect, _dur)
        return applied, (f"You are {effect.replace('_', ' ')}!" if applied else "")
    mod = (int(getattr(player, stat, 10)) - 10) // 2
    bonus = player.save_bonus_for(stat) if hasattr(player, 'save_bonus_for') else 0
    roll = _r.randint(1, 20) + mod + bonus + _ward
    was_on = bool(player.status_effects.get(effect, 0)) if effect in effect_rules.BOUTED else True
    flavor = _SAVE_FLAVOR.get(stat, 'You')
    if roll >= dc:
        if _ward > 0:
            _say_ward_held(player, source, effect, gaze)
        if effect in NEGATED_BY_SAVE:
            # Full save on hard control — negated, and you feel your stat earn it.
            return False, f"{flavor} throws off the {noun}!"
        applied = player.add_effect(effect, max(1, duration // 2))
        if applied and not was_on:
            effect_rules.laid_by(player, effect, source)
        return applied, (f"{flavor} blunts the {noun} — it barely takes hold." if applied else "")
    # Failed save — the effect lands.
    applied = player.add_effect(effect, duration)
    if applied and not was_on:
        effect_rules.laid_by(player, effect, source, lethal=lethal)
    if applied and effect == 'knocked_down':
        return applied, effect_rules.line('floored')
    return applied, (f"The {noun} takes hold!" if applied else "")


def tick_all(player, dungeon=None) -> list[tuple[str, str]]:
    """
    Advance one turn for every active effect on *player*.
    Returns list of (message_text, message_type) tuples.
    May mutate player.hp, player stats, and player.status_effects.
    Special signals prefixed with '_' are meant for main.py:
        '_teleport'      -- teleport the player to a random tile
        '_petrify_death' -- player has fully turned to stone (death)
    The world's own count of a slowed action is main's (Player.get_speed);
    here such an action spends two of Slowed's turns (TICK_STEPS).
    """
    sync_timed_grants(player)
    import random
    messages: list[tuple[str, str]] = []
    to_expire: list[str] = []
    # A confusion running on the hero is a bout whose recovery is owed
    # however it ends (an older save's confusion is marked here).
    for _sg in SOFT_GRACE:
        if int(player.status_effects.get(_sg, 0) or 0) > 0:
            _soft_bouts(player).add(_sg)

    # Coif of Beowulf (grendel_grip): the wearer cannot be held. Clears any
    # paralyzed/strangulation/sleeping status at the START of the tick. The
    # grip that strangled Grendel keeps you free.
    try:
        from armor_procs import player_has_armor_proc
        if player_has_armor_proc(player, 'grendel_grip'):
            for _gg_eff in ('paralyzed', 'strangulation', 'sleeping',
                            'immobilized', 'stunned', 'frozen'):
                if player.status_effects.get(_gg_eff, 0) > 0:
                    player.status_effects[_gg_eff] = 0
                    messages.append((f'Grendel-grip — you wrench free of {_gg_eff.replace("_", " ")}!', 'success'))
    except ImportError:
        pass

    for effect, val in list(player.status_effects.items()):
        if val == 0:
            to_expire.append(effect)
            continue

        # ---- Per-turn side effects ----
        if effect == 'poisoned' and not player.has_effect('poison_resist'):
            dmg = player.take_damage(dot_tick(player), 'poison')
            if dmg:
                messages.append(('The poison burns through you!', 'danger'))

        elif effect == 'diseased':
            if not player.has_effect('poison_resist') and not player.has_effect('drain_resist'):
                stat = random.choice(['STR', 'CON']) if random.random() < 0.08 else None
                # The disease never drains a stat below 1 (MNK-08: STR reached
                # 0 and went on down), the floor player.py keeps for STR.
                if stat and getattr(player, stat, 0) > 1:
                    player.apply_stat_bonus(stat, -1)
                    # Signal for main.py to dispatch the Paracelsus quirk hook.
                    messages.append((f'_disease_drain:{stat}:1', 'info'))
                    # what a potion of restore strength (STR) or a physician
                    # (any stat) gives back
                    note_stat_drain(player, stat, 1)
                    _what = 'strength' if stat == 'STR' else 'health'
                    messages.append((f'The disease saps your {_what}! {stat} -1.', 'danger'))

        elif effect == 'strangulation':
            dmg = player.take_damage(dot_tick(player) * 2, 'physical')
            if dmg:
                messages.append(('You are being strangled!', 'danger'))

        elif effect == 'regenerating':
            # One point every REGEN_PERIOD turns (it was every turn: a ring
            # found by floor 12 refilled the whole bar every minute of play).
            player._regen_phase = (int(getattr(player, '_regen_phase', 0)) + 1) % REGEN_PERIOD
            if player._regen_phase == 0 and player.hp < player.max_hp:
                # A share of the body it mends: one point for a small one, and
                # REGEN_SHARE of a large one (one flat point was nothing at
                # 1,500 health, where the Crown of Brahma grants this).
                # A Ring of Regeneration mends more by its tier (rings.py).
                try:
                    import rings
                    share = max(REGEN_SHARE, rings.regen_share(player))
                except ImportError:
                    share = REGEN_SHARE
                player.restore_hp(max(1, int(player.max_hp * share)))

        elif effect == 'petrifying' and val > 0:
            lethal = effect_rules.is_lethal(player)
            if val == 1 and lethal:
                messages.append(('_petrify_death', 'danger'))
            elif val > 1:
                # The count he watches: how it stands with a turn less.
                left = val - 1
                stage = effect_rules.stone_stage(player, left)
                key = {'stiff': 'stiff', 'slow': 'stiff_slow',
                       'rigid': 'rigid_lethal' if lethal else 'rigid_lesser'}[stage]
                messages.append((f"{effect_rules.line(key)} ({left})",
                                 'warning' if stage == 'stiff' else 'danger'))

        elif effect == 'bleeding':
            dmg = player.take_damage(dot_tick(player), 'physical')
            if dmg:
                messages.append(('You are bleeding!', 'danger'))

        elif effect == 'doomed':
            if random.random() < 0.12:
                player.hp = max(0, player.hp - max(1, dot_tick(player) // 2))
                messages.append(('The doom curse gnaws at your life force!', 'danger'))

        elif effect == 'draining':
            if random.random() < 0.17:
                player.hp = max(0, player.hp - max(1, dot_tick(player) // 2))
                messages.append(('The ring drains your life force!', 'danger'))

        elif effect == 'burning':
            if not player.has_effect('fire_resist') and not player.has_effect('fire_shield'):
                dmg = player.take_damage(dot_tick(player), 'fire')
                if dmg:
                    messages.append(('You are on fire!', 'danger'))
                if effect_rules.may_wear(player, 'burning'):
                    scorch = _scorch_random_gear(player)
                    if scorch:
                        messages.append(scorch)
                        if '(-1' in scorch[0]:
                            effect_rules.wore(player, 'burning')

        elif effect == 'corroding':
            # Acid eats at a random equipped metal item each turn
            result = _corrode_random_gear(player) if effect_rules.may_wear(player, 'corroding') else None
            if result:
                messages.append(result)
                if '(-1' in result[0]:
                    effect_rules.wore(player, 'corroding')

        elif effect == 'frozen':
            pass  # feet, hands and the thaw are the gate's (action_gate.py)

        elif effect == 'weakened':
            pass  # damage halving is checked at combat time via has_effect('weakened')

        elif effect == 'teleportitis':
            if random.random() < 0.04:
                messages.append(('_teleport', 'info'))

        # ---- Decrement timed effects ----
        # A side effect above can remove an effect mid-tick (poison damage
        # wakes a sleeper); writing the snapshot value back would re-add it.
        if effect not in player.status_effects:
            continue
        if val > 0 and effect not in UNTIL_ACTED:
            new_val = val - TICK_STEPS.get(effect, 1)
            if new_val <= 0:
                to_expire.append(effect)
            else:
                player.status_effects[effect] = new_val

    # Expire finished effects
    for effect in to_expire:
        _lesser_stone = effect == 'petrifying' and not effect_rules.is_lethal(player)
        player.status_effects.pop(effect, None)
        effect_rules.ended(player, effect)
        if _lesser_stone:
            # A cockatrice's stone ends in a short paralysis, never death. It
            # is set outright: the save was made when the countdown began.
            if not player.has_effect('sleep_resist'):
                player.status_effects['paralyzed'] = int(
                    effect_rules.data()['petrify']['lesser']['end_paralyzed'])
                messages.append((effect_rules.line('lesser_end'), 'danger'))
                continue                     # its grace follows the paralysis
        # Post-lock grace: after a hard-control effect ends, grant brief immunity
        # to being re-disabled so the player ALWAYS gets free turns to act/flee.
        if effect in HARD_CONTROL:
            player.status_effects['control_immune'] = GRACE_TURNS
        # Confusion's own recovery: Clear-Headed for a few turns (SOFT_GRACE).
        if effect in SOFT_GRACE:
            _grant_recovery(player, effect)
        # When a cooked/power "ward" expires, drop its magnitude companion.
        if effect.startswith('save_guard_'):
            _g = getattr(player, '_save_guard', None)
            if isinstance(_g, dict):
                _g.pop(effect[len('save_guard_'):], None)
        # Reverse stat bonuses granted by timed effects (see apply_effect)
        if effect == 'inspired':
            player.insight_wis = 0
        if effect in TIMED_STAT_GRANTS:
            sync_timed_grants(player)        # the status is gone: its stats go with it
        elif effect == 'stand_ac':
            # Leonidas Spartan Stand expiry — clear the AC + counter bonuses.
            player._stand_ac_bonus = 0
            player._stand_counter_pct = 0
        elif effect == 'berserk':
            # Berserk uses direct STR write (not apply_stat_bonus) because
            # it's a combat damage bonus, not a full stat buff — no max_sp gain.
            bonus = getattr(player, '_berserk_str_bonus', 0)
            if bonus:
                player.STR -= bonus
                player._berserk_str_bonus = 0
        if effect == 'petrifying' and ('_petrify_death', 'danger') in messages:
            continue                         # no softening: he is stone
        msg_pair = _EXPIRE_MSGS.get(effect)
        if msg_pair:
            messages.append(msg_pair)

    # A confusion cured this turn (outside the tick) is followed by its
    # Clear-Headed turns all the same.
    _recover_cured(player)
    return messages
