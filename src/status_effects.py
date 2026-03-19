"""
Status effect registry and tick logic.

Effect durations are stored in player.status_effects as:
  n > 0  = active for n more turns
  -1     = permanent (intrinsic)
  absent / 0 = not active

All NetHack-style effects are registered here even if their
full mechanics are yet to be wired in -- the UI, tick, and
resistance systems are fully active for all of them.
"""

# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

# effect_id -> (display_name, rgb_color, short_description)
EFFECT_INFO: dict[str, tuple] = {
    # ---- Debuffs ----
    'paralyzed':          ('Paralyzed',         (220,  50,  50), 'Cannot move or act'),
    'sleeping':           ('Sleeping',           (100, 100, 210), 'Asleep; woken by damage'),
    'stunned':            ('Stunned',            (225, 155,  50), 'May stumble; quiz timer -25%'),
    'confused':           ('Confused',           (185, 100, 230), 'Random movement; choices shuffled'),
    'blinded':            ('Blinded',            ( 80,  80,  80), 'Sight radius 1; quiz timer -30%'),
    'hallucinating':      ('Hallucinating',      (210,  85, 230), 'Reality distorted; quiz timer -20%'),
    'poisoned':           ('Poisoned',           ( 80, 210,  60), 'Losing 1 HP per turn'),
    'diseased':           ('Diseased',           (135, 205,  60), 'Slowly drains STR/CON'),
    'petrifying':         ('Petrifying',         (205, 205, 130), 'Turning to stone -- find a cure!'),
    'strangulation':      ('Strangled',          (200,  80,  80), 'Losing 2 HP per turn'),
    'fumbling':           ('Fumbling',           (220, 170,  80), '20% chance actions fail'),
    'slowed':             ('Slowed',             (155, 155, 230), 'Every other action is skipped'),
    'aggravated':         ('Aggravated',         (230, 100,  50), 'All monsters are alerted'),
    'teleportitis':       ('Teleportitis',       (100, 225, 225), 'May randomly teleport (4%/turn)'),
    'feared':             ('Feared',             (200,  80, 200), 'Fleeing -- cannot approach enemies'),
    'charmed':            ('Charmed',            (255, 160, 200), 'Under enemy influence'),
    'cursed':             ('Cursed',             (120,  40, 160), 'Under a dark curse'),
    'weakened':           ('Weakened',           (150, 150,  80), 'Attack damage halved'),
    'bleeding':           ('Bleeding',           (200,  40,  40), 'Losing HP from wounds each turn'),
    'doomed':             ('Doomed',             (100,  20,  20), 'A death-curse; losing 1 HP per ~8 turns'),
    'draining':           ('Draining',           ( 80,  30, 100), 'Ring drains 1 HP per ~6 turns'),
    'burning':            ('Burning',            (245, 100,  20), 'On fire! Losing 1 HP per turn'),
    'frozen':             ('Frozen',             ( 80, 200, 245), 'Encased in ice; movement slowed'),
    'corroding':          ('Corroding',          (180, 200,  50), 'Acid eats at your gear; defense weakened'),
    # ---- Buffs ----
    'hasted':             ('Hasted',             (245, 245,  60), 'Extra action each turn'),
    'invisible':          ('Invisible',          (185, 235, 235), 'Monsters have 30% miss chance'),
    'levitating':         ('Levitating',         (185, 215, 245), 'Floating; immune to floor traps'),
    'regenerating':       ('Regenerating',       ( 80, 225, 105), 'Recovering 1 HP per turn'),
    'telepathy':          ('Telepathy',          (205, 145, 245), 'All monsters visible on level'),
    'warning':            ('Warning',            (240, 210, 100), 'Sense monsters within 5 tiles'),
    'searching':          ('Searching',          (160, 200, 160), 'Auto-reveal adjacent tiles'),
    'clairvoyant':        ('Clairvoyant',        (245, 205, 105), 'Large area revealed around you'),
    'displacement':       ('Displaced',          (200, 200, 200), 'Monsters may miss your true position'),
    'heroism':            ('Heroic',             (255, 200,  40), 'STR +2; surging with battle-strength'),
    'brilliance':         ('Brilliant',          (140, 180, 255), 'INT +1, WIS +1; mind razor-sharp'),
    'hallucinating_pot':  ('Hallucinating',      (210,  85, 230), 'Reality distorted; quiz timer -20%'),
    # ---- Accessory-granted permanent buffs ----
    'life_save':          ('Life Save',          (255, 215,  80), 'Survive one killing blow; effect is then spent'),
    'sustained':          ('Sustained',          (150, 230, 170), 'SP drains at half rate; need less food'),
    'truesight':          ('True Sight',         (200, 200, 255), 'See all monsters regardless of invisibility; +2 sight'),
    'dark_vision':        ('Dark Vision',        ( 60,  80, 160), 'Sight radius +4 even in deep darkness'),
    'identify_sight':     ('Identify Sight',     (220, 200, 150), 'Items auto-identified when picked up'),
    'spell_turning':      ('Spell Turning',      (210, 175, 255), 'Reflects 100% of monster-cast debuffs back at attacker'),
    # ---- Active buffs (wand/accessory-granted) ----
    'blessed':            ('Blessed',            (200, 240, 160), 'All quiz timers +25%; divine clarity'),
    'shielded':          ('Shielded',           (120, 180, 245), '+2 AC; physical damage halved'),
    'fire_shield':        ('Fire Shield',        (245, 120,  40), 'Immune to fire; reflects fire attacks'),
    'cold_shield':        ('Cold Shield',        ( 80, 200, 245), 'Immune to cold; reflects cold attacks'),
    'reflecting':         ('Reflecting',         (220, 220, 180), '50% chance to reflect monster status attacks'),
    'phasing':            ('Phasing',            (180, 180, 220), 'Can walk through walls'),
    'time_stopped':       ('Time Stop',          (245, 220, 100), 'Time is frozen -- monsters cannot act'),
    # ---- Resistances (can be timed or permanent) ----
    'fire_resist':        ('Fire Resist',        (245, 130,  50), 'Immune to fire damage'),
    'cold_resist':        ('Cold Resist',        (100, 195, 245), 'Immune to cold damage'),
    'shock_resist':       ('Shock Resist',       (245, 245,  80), 'Immune to electric damage'),
    'poison_resist':      ('Poison Resist',      (100, 245,  80), 'Immune to poison and disease'),
    'sleep_resist':       ('Sleep Resist',       (130, 130, 245), 'Immune to sleep and paralysis'),
    'magic_resist':       ('Magic Resist',       (200, 150, 245), 'Reduces magical effects'),
    'drain_resist':       ('Drain Resist',       (185,  80, 245), 'Immune to stat drain'),
    'disint_resist':      ('Disint. Resist',     (245, 185, 100), 'Immune to disintegration'),
}

DEBUFFS: frozenset = frozenset({
    'paralyzed', 'sleeping', 'stunned', 'confused', 'blinded', 'hallucinating',
    'poisoned', 'diseased', 'petrifying', 'strangulation', 'fumbling',
    'slowed', 'aggravated', 'teleportitis',
    'feared', 'charmed', 'cursed', 'weakened', 'bleeding', 'doomed', 'draining',
    'burning', 'frozen', 'corroding',
})

BUFFS: frozenset = frozenset({
    'hasted', 'invisible', 'levitating', 'regenerating', 'telepathy',
    'warning', 'searching', 'clairvoyant', 'displacement', 'heroism', 'brilliance',
    'shielded', 'fire_shield', 'cold_shield', 'reflecting', 'phasing', 'time_stopped', 'blessed',
    'fire_resist', 'cold_resist', 'shock_resist', 'poison_resist',
    'sleep_resist', 'magic_resist', 'drain_resist', 'disint_resist',
    'life_save', 'sustained', 'truesight', 'dark_vision', 'identify_sight', 'spell_turning',
})

# Resistance effects that block specific debuffs from being applied
_RESIST_BLOCKS: dict[str, set] = {
    'poison_resist': {'poisoned', 'diseased'},
    'sleep_resist':  {'sleeping', 'paralyzed'},
    'drain_resist':  {'diseased'},
    'fire_resist':   {'burning'},
    'cold_resist':   {'frozen'},
}

# Damage type -> immunity status effect (first match wins; fire_shield overrides fire_resist)
DAMAGE_IMMUNITY: dict[str, str] = {
    'fire':    'fire_resist',
    'cold':    'cold_resist',
    'lightning':'shock_resist',
    'poison':  'poison_resist',
    'drain':   'drain_resist',
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
    'confused':       ('Your mind sharpens. Confusion gone.',    'info'),
    'blinded':        ('Your vision returns!',                   'success'),
    'hallucinating':  ('Reality snaps back into focus.',         'info'),
    'poisoned':       ('The poison leaves your body.',           'success'),
    'diseased':       ('You recover from the disease.',          'success'),
    'strangulation':  ('You gasp free -- strangulation ends.',    'success'),
    'fumbling':       ('You regain your footing.',               'info'),
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
    'blessed':        ('The divine clarity fades.',              'info'),
    'feared':         ('Your fear subsides.',                    'info'),
    'charmed':        ('The charm over you breaks.',             'info'),
    'cursed':         ('The curse lifts.',                       'success'),
    'weakened':       ('Your strength returns.',                 'info'),
    'bleeding':       ('Your wounds close.',                     'success'),
    'heroism':        ('The heroic surge fades. STR returns.',   'info'),
    'brilliance':     ('Your mind settles. INT and WIS return.', 'info'),
    'doomed':         ('The doom curse has lifted.',             'success'),
    'draining':       ('The ring stops draining your life.',     'success'),
    'burning':        ('The flames are extinguished.',           'success'),
    'frozen':         ('The ice cracks -- you can move freely!',  'success'),
    'sustained':      ('Your ring of sustenance crumbles.',      'info'),
    'truesight':      ('Your true sight fades.',                 'info'),
    'dark_vision':    ('Your dark vision fades.',                'info'),
    'spell_turning':  ('Your spell turning aura dissipates.',   'info'),
}


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------

def apply_effect(player, effect: str, duration: int) -> bool:
    """
    Try to apply *effect* for *duration* turns (-1 = permanent) to *player*.
    Returns True if applied, False if blocked by resistance or already permanent.
    """
    for resist, blocked in _RESIST_BLOCKS.items():
        if effect in blocked and player.has_effect(resist):
            return False

    current = player.status_effects.get(effect, 0)
    if current == -1:
        return False  # permanent -- can't be changed

    if duration == -1:
        player.status_effects[effect] = -1
    else:
        player.status_effects[effect] = min(current + duration, 60)
    return True


def tick_all(player, dungeon=None) -> list[tuple[str, str]]:
    """
    Advance one turn for every active effect on *player*.
    Returns list of (message_text, message_type) tuples.
    May mutate player.hp, player stats, and player.status_effects.
    Special signals prefixed with '_' are meant for main.py:
        '_teleport'      -- teleport the player to a random tile
        '_petrify_death' -- player has fully turned to stone (death)
    """
    import random
    messages: list[tuple[str, str]] = []
    to_expire: list[str] = []

    for effect, val in list(player.status_effects.items()):
        if val == 0:
            to_expire.append(effect)
            continue

        # ---- Per-turn side effects ----
        if effect == 'poisoned' and not player.has_effect('poison_resist'):
            dmg = player.take_damage(1, 'poison')
            if dmg:
                messages.append(('The poison burns through you!', 'danger'))

        elif effect == 'diseased':
            if not player.has_effect('poison_resist') and not player.has_effect('drain_resist'):
                if random.random() < 0.08:
                    stat = random.choice(['STR', 'CON'])
                    player.apply_stat_bonus(stat, -1)
                    messages.append((f'The disease saps your strength! {stat} -1.', 'danger'))

        elif effect == 'strangulation':
            dmg = player.take_damage(2, 'physical')
            if dmg:
                messages.append(('You are being strangled!', 'danger'))

        elif effect == 'regenerating':
            if player.hp < player.max_hp:
                player.restore_hp(1)

        elif effect == 'petrifying':
            if val <= 3:
                messages.append(('Your limbs are rigid -- death is moments away!', 'danger'))
                if val == 1:
                    messages.append(('_petrify_death', 'danger'))
            elif val <= 6:
                messages.append(('Your skin is hardening into stone!', 'danger'))
            elif val <= 10:
                messages.append(('You feel yourself stiffening...', 'warning'))

        elif effect == 'bleeding':
            dmg = player.take_damage(1, 'physical')
            if dmg:
                messages.append(('You are bleeding!', 'danger'))

        elif effect == 'doomed':
            if random.random() < 0.12:
                player.hp = max(0, player.hp - 1)
                messages.append(('The doom curse gnaws at your life force!', 'danger'))

        elif effect == 'draining':
            if random.random() < 0.17:
                player.hp = max(0, player.hp - 1)
                messages.append(('The ring drains your life force!', 'danger'))

        elif effect == 'burning':
            if not player.has_effect('fire_resist') and not player.has_effect('fire_shield'):
                dmg = player.take_damage(1, 'fire')
                if dmg:
                    messages.append(('You are on fire!', 'danger'))

        elif effect == 'frozen':
            pass  # slowing mechanic handled by caller; cold DOT negligible

        elif effect == 'weakened':
            pass  # damage halving is checked at combat time via has_effect('weakened')

        elif effect == 'teleportitis':
            if random.random() < 0.04:
                messages.append(('_teleport', 'info'))

        # ---- Decrement timed effects ----
        if val > 0:
            new_val = val - 1
            if new_val <= 0:
                to_expire.append(effect)
            else:
                player.status_effects[effect] = new_val

    # Expire finished effects
    for effect in to_expire:
        player.status_effects.pop(effect, None)
        # Reverse stat bonuses granted by timed effects
        if effect == 'heroism':
            player.apply_stat_bonus('STR', -2)
        elif effect == 'brilliance':
            player.apply_stat_bonus('INT', -1)
            player.apply_stat_bonus('WIS', -1)
        msg_pair = _EXPIRE_MSGS.get(effect)
        if msg_pair:
            messages.append(msg_pair)

    return messages
