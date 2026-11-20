import random
from dice import roll, roll_duration
from combat import _line_of_sight
from status_effects import MAX_EFFECT_DURATION
from naming import ProperNameAttr
import packs
# Monster behaviour, first wave (AI-1, 2026-11-19): each in its own module.
import ai_blow
import breath
import faction
import gone_again
import grave_rot
import morale
import relurk
import summoning


# Ceiling on escalating rage (Fenrir, and the mini-bosses that borrow his
# pattern when wounded): each stack adds a die to every attack.
RAGE_STACK_CAP = 8
# Most locusts Abaddon keeps alive at once.
LOCUST_CAP = 12
# A monster whose roll misses still connects this often: armor turns blows,
# it does not make its wearer untouchable. These were 0.05 and 0.25, and a
# full kit's AC outran every THAC0 from floor 10 (measured hit chance 10 to
# 22 percent, 25 at floor 90), which is why the deep floors were SAFER than
# the middle ones.
# A gate boss left alone recovers. Nothing stopped a player walking off,
# resting to full and coming back to a boss still carrying every wound, as
# often as they liked: no gate boss could be lost to by anyone patient.
# After RECOVER_AFTER_TURNS without taking damage, a monster flagged
# `recovers_when_left` heals RECOVER_SHARE of its health each turn. (Asterion
# hides in the walls for 9 to 12 turns at a time: short of the threshold.)
RECOVER_AFTER_TURNS = 25
# What an attacker loses, as a share of its own health, for striking Tesla
# (every blow) or a Spartan in his stand (when the counter fires). Both were
# a third or a half of the MONSTER's damage: a point or two against thousands.
RESONANCE_SHARE = 0.04
SPARTAN_COUNTER_SHARE = 0.10

# A creature that weighs the heart (`weighs_heart`, Ammit's get) changes each
# blow by this much per point of the hero's karma: x1.4 at karma -10, x0.6 at
# +10. Karma is tight (karma.py), so a high score is earned.
HEART_WEIGHT_PER_KARMA = 0.04


def heart_weight(player) -> float:
    """The multiplier a heart-weighing blow carries against this hero."""
    game = getattr(player, '_combat_game_ref', None)
    try:
        karma = int(getattr(game, 'karma', 0) or 0)
    except (TypeError, ValueError):
        karma = 0
    return 1.0 - HEART_WEIGHT_PER_KARMA * max(-10, min(10, karma))
RECOVER_SHARE = 0.03

# The share of THAC0 misses that land anyway. With AC from body armour and
# shield only (gear.py) and every monster's THAC0 rebaked to the AC line
# (tools/balance/rebake_thac0.py), an ordinary monster needs no floor: the
# natural 20 is it, as in AD&D. At 0.30 every blow from floor 15 down was
# decided by this number, not by what the hero wore. Named foes keep some.
MIN_HIT_ORDINARY = 0.0
MIN_HIT_NAMED = 0.15
# Drain attacks: most CON one floor can cost, and the lowest drain can take it.
DRAIN_CON_PER_FLOOR = 1      # (2 until a point of CON became 3 hit points)
DRAIN_CON_FLOOR = 8
# Share of max HP a bleeding or burning monster loses each turn (1 / N).
# One in 15 took 267 a turn off Abaddon, more than any weapon in the game;
# named foes bleed far more slowly.
BLEED_DIVISOR = 15
BURN_DIVISOR = 20
POISON_DIVISOR = 40
NAMED_DOT_DIVISOR = 100
# Longest a hard control effect can hold a named foe, and what counts as one.
NAMED_FOE_CONTROL_CAP = 2
# After a hold on a named foe ends, it cannot be held again for this many
# turns (the player's own post-lock grace, status_effects.GRACE_TURNS, is the
# same idea). Without it a chain stun every turn held a boss for the whole
# fight (bug bash 4, call 12).
NAMED_FOE_CONTROL_GRACE = 3
# The lore pass (winning build slice 2) a monster's affinity lists come from;
# a saved monster without it takes its kind's lists on load.
AFFINITY_PASS = 1
_HARD_CONTROL = frozenset({'paralyzed', 'sleeping', 'stunned', 'frozen',
                           'confused', 'feared', 'charmed', 'petrifying',
                           'immobilized', 'time_stopped'})
# How far a petrifying gaze reaches, given a clear line of sight.
GAZE_RANGE = 8
# Dragon AI: reach of the breath, and turns between breaths (Fafnir's own
# clock; every other breather recharges by src/breath.py, the same 3 turns).
DRAGON_BREATH_RANGE = 7
DRAGON_BREATH_RECHARGE = breath.RECHARGE_DEFAULT['breath']


def the_name(monster, lower: bool = False) -> str:
    """A monster's name with the right article.

    Sentence start (default): "The giant rat", but "Arachne", "The Sphinx".
    Mid-sentence (lower=True): "the giant rat", "Arachne", "the Sphinx".

    Named foes (bosses, mini-bosses, scripted NPCs) are proper nouns, and
    four of them already begin with "The". Blindly prefixing "The " produced
    "The The Sphinx is slain!" and "The Baba Yaga misses!".
    """
    # An invisible creature the hero cannot see (src/unseen.py) is never named.
    if getattr(monster, '_unseen', False) is True:
        return 'something unseen' if lower else 'Something unseen'
    # Nor is one still lurking (bug bash 5 MON-04, PET-03): a mimic in its
    # disguise is named as the thing it poses as ("the iron chest", "the
    # staircase leading down"), an ambusher that has not sprung as "something".
    if (not getattr(monster, '_aware', False)
            and getattr(monster, 'ai_pattern', '') in ('ambush', 'mimic')):
        from unseen import disguise
        d = disguise(monster)
        if d:
            return f"{'the' if lower else 'The'} {d.get('name') or 'chest'}"
        return 'something' if lower else 'Something'
    name = getattr(monster, 'name', '') or 'something'
    low = name.lower()
    if low.startswith('the '):
        return ('t' if lower else 'T') + name[1:]
    if low.startswith(('a ', 'an ')):
        return name                     # already carries its own article
    if _is_proper(monster, low):
        return name
    return f"{'the' if lower else 'The'} {name}"


def _is_proper(monster, low: str) -> bool:
    """A named foe (a boss, a mini-boss, a seal demon, a story foe, the
    Bones ghost, Death): a proper noun, said with no article. So is a kind
    named for its master ("Fionn's Hound", "Set's Jackal"): "the Fionn's
    Hound" was said (round 3). Death himself is "Death"; a kind named for
    him is not ("Death Dog swings at you and misses!", "Death Mage is
    slain!" were said of seven ordinary kinds: bug bash 3.5.1 E)."""
    first = (getattr(monster, 'name', '') or '').split(' ', 1)[0]
    return bool(getattr(monster, 'is_boss', False) or getattr(monster, 'is_mini_boss', False)
                or getattr(monster, 'is_seal_demon', False)
                or getattr(monster, 'proper_noun', False)
                or getattr(monster, 'kind', '') in ('player_ghost', 'death')
                or low == 'death'
                or low.startswith(('ghost of ', "death's "))
                or (first[:1].isupper() and first.endswith(("'s", "s'"))))


def _hidden(monster) -> bool:
    """The hero cannot tell what it is: unseen, or a lurker not yet sprung."""
    if getattr(monster, '_unseen', False) is True:
        return True
    return (not getattr(monster, '_aware', False)
            and getattr(monster, 'ai_pattern', '') in ('ambush', 'mimic'))


def an_article(word: str) -> str:
    """'a' or 'an' for ``word`` by its sound: "an orc", "a unicorn", "an
    heir", "a one-eyed giant", "an Ushabti"."""
    w = str(word or '').lstrip('{').lstrip().lower()
    if not w:
        return 'a'
    if w.startswith(('heir', 'hour', 'honest', 'honou', 'honor')):
        return 'an'
    if w.startswith(('uni', 'use', 'usu', 'uti', 'eu', 'ewe', 'one', 'once')):
        return 'a'
    return 'an' if w[0] in 'aeiou' else 'a'


def kind_of_corpse(corpse):
    """A stand-in for the creature a corpse was, for the_name and a_name:
    its name and whether it was a named foe ("You understand the Asterion
    the Minotaur now." was said of a boss's corpse: bug bash 3.5.1 E)."""
    from types import SimpleNamespace
    md = dict(getattr(corpse, 'monster_def', None) or {})
    try:                    # the body keeps no flags: its kind's data does
        import affinity
        md = {**(affinity._monster_defs().get(getattr(corpse, 'monster_id', '')) or {}), **md}
    except (OSError, ValueError):
        pass
    return SimpleNamespace(
        name=str(getattr(corpse, 'monster_name', '') or md.get('name', '') or 'creature'),
        kind=getattr(corpse, 'monster_id', '') or md.get('id', ''),
        is_boss=bool(md.get('is_boss')), is_mini_boss=bool(md.get('is_mini_boss')),
        is_seal_demon=bool(md.get('is_seal_demon')), proper_noun=bool(md.get('proper_noun')),
        _aware=True, ai_pattern='')


def a_name(monster, lower: bool = True) -> str:
    """A monster's name with an indefinite article, as first seen: "a
    Skeleton", "an Orc Scout", but "Arachne", "The Sphinx" (a named foe is a
    proper noun). Mid-sentence by default ("You see a Skeleton."); at a
    sentence start (lower=False) "A Skeleton". An unseen creature is
    "something unseen", a lurker in disguise the thing it poses as."""
    if _hidden(monster):
        name = the_name(monster, lower=True)
        if name.startswith('the '):
            name = f"{an_article(name[4:])} {name[4:]}"
        return name if lower else name[:1].upper() + name[1:]
    name = getattr(monster, 'name', '') or 'something'
    low = name.lower()
    if low.startswith(('the ', 'a ', 'an ')):
        return (name[:1].lower() + name[1:]) if lower and low.startswith('the ') else name
    if _is_proper(monster, low):
        return name
    art = an_article(name)
    return f"{art if lower else art.capitalize()} {name}"


# ---------------------------------------------------------------------------
# A creature's pronouns (data/monsters.json `pronoun`; round 3, Brandon: "it
# unless clearly humanoid, then use appropriate: most will be he, but some,
# clearly feminine ... probably should be she"). Every individual is he, she
# or it, never "they". A creature the hero cannot see, or a lurker not yet
# sprung, is "it". A pickled monster from before the field takes its kind's.
# ---------------------------------------------------------------------------
PRONOUNS = {'it': ('it', 'it', 'its'), 'he': ('he', 'him', 'his'), 'she': ('she', 'her', 'her')}
_KIND_PRONOUNS = None


def kind_pronoun(kind) -> str:
    """The pronoun data/monsters.json gives ``kind`` ('it' for a kind it
    does not list)."""
    global _KIND_PRONOUNS
    if _KIND_PRONOUNS is None:
        import json
        from paths import data_path
        try:
            with open(data_path('data', 'monsters.json'), encoding='utf-8') as f:
                defs = json.load(f)
            _KIND_PRONOUNS = {k: str(v.get('pronoun') or 'it') for k, v in defs.items()
                              if isinstance(v, dict)}
        except (OSError, ValueError):
            _KIND_PRONOUNS = {}
    return _KIND_PRONOUNS.get(str(kind or ''), 'it')


def pronoun(monster) -> str:
    """'it', 'he' or 'she' for this creature as the hero sees it."""
    if monster is None or _hidden(monster):
        return 'it'
    own = getattr(monster, '__dict__', {}).get('pronoun') if hasattr(monster, '__dict__') else None
    if own is None:
        own = kind_pronoun(getattr(monster, 'kind', ''))
    word = str(own or 'it').lower()
    return word if word in PRONOUNS else 'it'


def pronouns(monster) -> tuple:
    """(subject, object, possessive): ('he', 'him', 'his'), ('she', 'her',
    'her') or ('it', 'it', 'its')."""
    return PRONOUNS[pronoun(monster)]


def pronoun_fill(monster) -> dict:
    """The pronoun slots a line can carry: {he} {He} {him} {his} {His}
    {himself} ('it', 'It', 'it', 'its', 'Its', 'itself' for an it)."""
    sub, obj, pos = pronouns(monster)
    return {'he': sub, 'He': sub.capitalize(), 'him': obj, 'his': pos, 'His': pos.capitalize(),
            'himself': obj + 'self'}


def fill(monster, text: str, **kw) -> str:
    """``text`` with the creature put in: {The} / {the} its name with the
    article, {A} / {a} with an indefinite one, the pronoun slots
    (pronoun_fill), and any ``kw`` ({kin}, {words}...). By plain
    replacement, so braces it does not know are left as they are."""
    t = str(text or '')
    if '{' not in t:
        return t
    if monster is not None:
        if '{The}' in t:
            t = t.replace('{The}', the_name(monster))
        if '{the}' in t:
            t = t.replace('{the}', the_name(monster, lower=True))
        if '{A}' in t:
            t = t.replace('{A}', a_name(monster, lower=False))
        if '{a}' in t:
            t = t.replace('{a}', a_name(monster))
    for k, v in pronoun_fill(monster).items():
        t = t.replace('{' + k + '}', v)
    for k, v in kw.items():
        t = t.replace('{' + k + '}', str(v))
    return t


# ---------------------------------------------------------------------------
# A monster's own attack in a line (data/combat_lines.json)
# ---------------------------------------------------------------------------
_COMBAT_LINES = None


def combat_lines() -> dict:
    global _COMBAT_LINES
    if _COMBAT_LINES is None:
        import json
        from paths import data_path
        try:
            with open(data_path('data', 'combat_lines.json'), encoding='utf-8') as f:
                _COMBAT_LINES = json.load(f)
        except (OSError, ValueError):
            _COMBAT_LINES = {}
    return _COMBAT_LINES


def attack_noun(atk) -> str:
    """The attack's name in a sentence: lower case ("rusty knife"), but a
    proper word keeps its capitals ("Euryale's wail", "words of Thoth")."""
    raw = str((atk or {}).get('name', 'attack') if isinstance(atk, dict) else atk or 'attack')
    proper = set(combat_lines().get('proper_words') or ())
    return ' '.join(w if w in proper else w.lower() for w in raw.replace('_', ' ').split())


def _attack_verb(atk) -> str:
    raw = str((atk or {}).get('name', '') if isinstance(atk, dict) else atk or '')
    return str((combat_lines().get('attack_verbs') or {}).get(raw.replace('_', ' '), '') or '')


def with_attack(monster, atk) -> str:
    """"his rusty knife", "her talons", "its bite"; "Euryale's wail" (a
    name that begins with a proper word takes no possessive)."""
    noun = attack_noun(atk)
    first = noun.split(' ', 1)[0] if noun else ''
    if first in set(combat_lines().get('proper_words') or ()):
        return noun
    return f"{pronouns(monster)[2]} {noun}"


def attack_line(monster, atk, actual: int) -> str:
    """The line for a blow that landed: "The Goblin hits you with his rusty
    knife for 3 damage!", "The Gelatinous Cube engulfs you for 4 damage!"."""
    who = the_name(monster)
    verb = _attack_verb(atk)
    if verb:
        pred = verb if ('you' in verb.split() or 'your' in verb.split()) else f"{verb} you"
        return f"{who} {pred} for {actual} damage!"
    return f"{who} hits you with {with_attack(monster, atk)} for {actual} damage!"


# Words in an attack's name that mark it as coming from a distance. Not
# 'spike': a Spiked Shield or a barbed devil's Tail Spike is a blow (the orc
# marauder "fired" his shield, bug bash 3.5.1 Q18). A creature that shoots
# its spikes says so in its data: the manticore's Tail Spike is `ranged`,
# its elder's is a Tail Spike Volley. One list, used everywhere.
_RANGED_WORDS = {'shoot', 'arrow', 'bolt', 'dart', 'spit', 'hurl',
                 'volley', 'ray', 'blast', 'breath', 'gaze',
                 'song', 'wail', 'charm', 'psionic', 'disintegrat',
                 'cast', 'bow', 'sling', 'javelin', 'spore', 'shock', 'hex'}
# Attacks that work on the mind or the eye: they do not fly, they fail to take.
# (A riddle is the Sphinx's: it either takes hold of your thoughts or it does not.)
_MIND_WORDS = ('gaze', 'song', 'wail', 'charm', 'psionic', 'hex', 'evil eye', 'riddle')

# Openers (2026-11-19, Brandon: "openers for sure"). A creature with a
# signature opening move (data `opener`: {"attack": <one of its attacks>,
# "range": N}) uses it before the hero can strike:
#   range 1  - a pounce, lunge or charge: on the turn it closes to the hero
#              it strikes with that attack at once;
#   range 2+ - from a distance, the hero in its sight: an archer's first
#              volley at once; a gaze, a voice or a breath is first drawn
#              up for a turn (OPENER_WIND_UP), a tell the hero can answer.
# Once a fight: it opens again only after it has lost the hero for
# OPENER_RESET_TURNS turns. The blow itself is an ordinary one (to-hit,
# saves, guards, wards and counters all apply).
OPENER_RESET_TURNS = 5
OPENER_WIND_UP = {
    'gaze': "{name} fixes {his} eyes on you.",
    'voice': "{name} draws a long breath.",
    'breath': "{name} rears back, and something kindles in {his} throat.",
}


# ---------------------------------------------------------------------------
# Who can bleed (data/monster_blood.json; Brandon, 3.3.3 play: "The Wraith is
# bleeding!"). A creature with no blood (bone and dust undead, spirits,
# golems, elementals, oozes, plants) never takes the bleeding status, never
# loses health to it and is never called bleeding; a vampire, or one of the
# fleshy dead, does. The rule is data: a family or a tag, and a short list of
# kinds that are the exception. Monster.can_bleed asks here.
# ---------------------------------------------------------------------------
_BLOOD_RULES = None


def blood_rules() -> dict:
    global _BLOOD_RULES
    if _BLOOD_RULES is None:
        import json
        from paths import data_path
        with open(data_path('data', 'monster_blood.json'), encoding='utf-8') as f:
            _BLOOD_RULES = json.load(f)
    return _BLOOD_RULES


def kind_can_bleed(kind: str, family, tags) -> bool:
    """The kind's own entry first, then a family that bleeds, then a family
    or a tag that has no blood; otherwise it bleeds."""
    r = blood_rules()
    kind = str(kind or '')
    if kind in (r.get('bleeds') or ()):
        return True
    if kind in (r.get('bloodless') or ()):
        return False
    if family and family in (r.get('bleeding_families') or ()):
        return True
    if family and family in (r.get('bloodless_families') or ()):
        return False
    if set(tags or ()) & set(r.get('bloodless_tags') or ()):
        return False
    return True


def _family_of_kind(kind):
    try:
        import family_lore
        return family_lore.family_of(str(kind or ''))
    except Exception:
        return None


# Family knowledge hooks (src/family_edges.py). Each is a no-op when the
# hero has earned nothing against this family.
def _edge_save(player, m, effect) -> int:
    """The family ward's bonus, quietly: its line waits for the save to
    hold (_edge_ward_held)."""
    try:
        import family_edges
        return family_edges.save_bonus(player, m, effect, quiet=True)
    except Exception:
        return 0


def _edge_ward_held(player, m, effect) -> None:
    try:
        import family_edges
        family_edges.ward_held(player, m, effect)
    except Exception:
        pass


def _edge_incoming(player, m, dmg: int, atk_type: str) -> int:
    try:
        import family_edges
        mult = family_edges.incoming_damage_mult(player, m, atk_type)
    except Exception:
        return dmg
    return max(1, int(round(dmg * mult))) if mult < 1.0 and dmg > 0 else dmg


def _edge_gaze_immune(player, m) -> bool:
    try:
        import family_edges
        return family_edges.gaze_immune(player, m)
    except Exception:
        return False


def _edge_no_ambush(player, m) -> bool:
    try:
        import family_edges
        return family_edges.no_ambush(player, m)
    except Exception:
        return False


def _edge_drain_block(player, m) -> bool:
    try:
        import family_edges
        return family_edges.drain_heal_blocked(player, m)
    except Exception:
        return False



# Told of every blow a monster takes: callable(monster, amount, dealt) or None.
# ``amount`` is the blow, ``dealt`` what it actually took off (no overkill).
# The Seeker's achievements listen (game_seeker.py); the game says whose blow
# it was (Game._damage_by).
DAMAGE_OBSERVER = None

class Monster:
    # Always title case, however monsters.json (or an old save) spelled it.
    name = ProperNameAttr('name')

    def _roll_rage_bonus(self) -> int:
        """Damage added per rage stack. Data may give dice ("1d6") or a flat
        number; a bare int used to crash dice.roll() (grave_knight)."""
        bonus = self.rage_damage_bonus
        if isinstance(bonus, (int, float)):
            return int(bonus)
        text = str(bonus).strip()
        return int(text) if text.lstrip('-').isdigit() else roll(text)

    def __init__(self, defn: dict, x: int, y: int):
        self.kind = defn['id']
        self.name = defn['name']
        self.symbol = defn['symbol']
        self.color = tuple(defn['color'])
        self.ai_pattern = defn.get('ai_pattern', 'aggressive')
        self.speed = defn.get('speed', 10)
        self.attacks = defn.get('attacks', [])

        hp_str = str(defn['hp'])
        self.max_hp = int(hp_str) if hp_str.isdigit() else roll(hp_str)
        self.hp = self.max_hp

        self.x = x
        self.y = y
        self.alive = True

        # --- NetHack-inspired AI state ---
        self._flee_timer: int = 0       # turns remaining in flee mode
        self._alerted: bool = False     # woken by a nearby ally's call for help
        self._slow_skip: bool = False   # used by variable-speed skip logic

        self.harvest_tier      = defn.get('harvest_tier', 1)
        # harvest_threshold: dead JSON field as of harvest v4 (2026-08-06);
        # harvest is a single-question flow now — read kept for old-pickle
        # compat but defaults gracefully.
        self.harvest_threshold = defn.get('harvest_threshold', 2)
        # ingredient_id: dead JSON field: the harvest resolves the drop via
        # data/items/harvest_map.json (by monster.kind), not this field.
        # Read kept for old-pickle compat.
        self.ingredient_id     = defn.get('ingredient_id', None)
        self.min_level: int    = int(defn.get('min_level', 1))
        self.max_level         = defn.get('max_level', None)  # soft cap; None = no cap
        self.peak_floor: int   = int(defn.get('peak_floor', self.min_level) or self.min_level)
        self.spread: int       = int(defn.get('spread', 10) or 10)

        # THAC0: "To Hit Armor Class Zero". Lower = more accurate.
        self.thac0: int = int(defn.get('thac0', max(-10, 20 - defn.get('min_level', 1))))

        # Resistances and weaknesses (damage type strings)
        self.resistances: list[str] = defn.get('resistances', [])
        self.weaknesses:  list[str] = defn.get('weaknesses', [])
        # What it shrugs off (a quarter of the blow gets through), what its
        # nature refuses (no "It is Feared!" said of a golem) and what it
        # falls to easily: written from its lore (data/family_affinity.json,
        # tools/content/affinity_pass.py; the steps in data/affinity_rules.json).
        self.shrugs_off: list[str] = list(defn.get('shrugs_off', []) or [])
        self.status_immune: list[str] = list(defn.get('status_immune', []) or [])
        self.status_weak: list[str] = list(defn.get('status_weak', []) or [])
        # A monster saved before the lore pass has no mark and takes its
        # kind's lists on load (Game._migrate_monster_affinities).
        self._affinity_pass: int = AFFINITY_PASS
        # Tags for systemic material interactions (undead, demon, fey, etc.)
        self.tags: list[str] = defn.get('tags', [])
        # Its ONE monster family (monsters.json `family`, src/family_lore.py):
        # what the hero's family knowledge works on. Built-in creatures look
        # theirs up by kind (the Bones ghost is a Ghost; Death has none).
        self.family = defn.get('family') or _family_of_kind(self.kind)

        # Treasure drop definition
        self.treasure: dict = defn.get('treasure', {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1})

        # Lore text revealed when corpse is identified
        self.lore: str = defn.get('lore', '')

        # Minimal status effects for wand interactions
        self.status_effects: dict[str, int] = {}  # effect_id -> turns remaining

        # Regeneration: HP per turn (trolls, hydras; fire stops it)
        self.regeneration: int = int(defn.get('regeneration', 0))
        self.recovers_when_left: bool = bool(defn.get('recovers_when_left', False))
        self._unhurt_turns: int = 0
        # Fury: every blow this monster swings adds `fury_per_attack` to its
        # damage, up to +`fury_cap`. A fight against it is a race, won by
        # long chains rather than by a deep pack of potions. It cools when
        # the monster is left alone (see _recover_when_left).
        self.fury_per_attack: float = float(defn.get('fury_per_attack', 0.0))
        self.fury_cap: float = float(defn.get('fury_cap', 1.0))
        self.fury_message: str = str(defn.get('fury_message', '') or '')
        # A monster's own chance to land a blow that failed its roll (four
        # carry one). `_min_hit` read this attribute and nothing set it.
        self.min_hit_chance = defn.get('min_hit_chance')
        self._fury_swings: int = 0
        self._fury_told: int = 0

        # --- Hit-and-run AI state (Asterion) ---
        self.can_phase_walls: bool = defn.get('can_phase_walls', False)
        self._hit_run_state: str = 'hunting'   # hunting / retreating / hiding
        self._hit_run_timer: int = 0            # turns in current state
        self._hit_run_attacks: int = 0          # attacks landed this engagement

        # --- Gaze attack (Medusa) ---
        self.gaze_paralyze: int = defn.get('gaze_paralyze', 0)      # paralyze duration (0 = no gaze)
        self.gaze_cooldown_max: int = defn.get('gaze_cooldown', 4)   # turns between gazes
        self._gaze_cooldown: int = 0                                  # current cooldown remaining
        # Gazers that share one gaze (Stheno and Euryale): when any of the
        # group looks, every living gazer of the group waits out the cooldown,
        # so the player is never paralysed twice by the pair in one turn.
        self.gaze_group: str = defn.get('gaze_group', '') or ''

        # --- Dragon scales (Fafnir): fraction of damage absorbed (0.0-1.0) ---
        self.dragon_scales: float = float(defn.get('dragon_scales', 0))

        # --- Fenrir rage mechanic ---
        self.rage_interval: int = int(defn.get('rage_interval', 0))    # 0 = no rage
        self.rage_damage_bonus: str = defn.get('rage_damage_bonus', '')
        self.rage_stacks: int = 0
        self._rage_turn_counter: int = 0
        self._rage_message: str = ''  # set each turn for caller to read

        # --- Abaddon locust swarm mechanic ---
        self.locust_interval: int = int(defn.get('locust_interval', 0))
        self.locust_count: list = defn.get('locust_count', [0, 0])
        self._locust_turn_counter: int = 0
        self._wants_locust_spawn: bool = False
        self.base_resistances: list = defn.get('base_resistances', [])

        # --- Allied monster (angels) ---
        self.is_allied: bool = defn.get('is_allied', False)
        self.sp_drain: int = int(defn.get('sp_drain', 0))
        self.is_seal_demon: bool = defn.get('is_seal_demon', False)
        self._annihilate_target = None  # set by seek_locust AI

        # --- Boss flag (mini-bosses, seal demons, etc.) ---
        # Read from JSON so boss-immunity in hero_specials/game_magic actually
        # applies to blood_archon, iron_patriarch, whispering_crone, and the
        # 7 seal_demon_* monsters. Falls back to False if the JSON omits it;
        # _DEFAULTS also carries is_boss=False for old pickles.
        self.is_boss: bool = bool(defn.get('is_boss', False))
        self.is_mini_boss: bool = bool(defn.get('is_mini_boss', False))

        # --- Footprint (multi-tile monsters) ---
        # NW-anchored rectangle. (1, 1) = single-tile (the default for
        # every existing monster). (2, 2) = 4-tile boss (currently
        # Fafnir only). See src/geom.py for the helpers that consume
        # this; new code should never compare (m.x, m.y) directly to a
        # tile coordinate — use `geom.monster_at_tile(...)` etc.
        _fp = defn.get('footprint', [1, 1])
        self.footprint: tuple[int, int] = (int(_fp[0]), int(_fp[1]))

        # --- Piercing ranged state (set by _ranged_turn for caller to process) ---
        self._piercing_collateral: list = []   # monsters in projectile path
        self._force_piercing: bool = False      # next attack must use piercing

        # --- Detection / alert overrides (default 8-tile sight, 5-tile alert) ---
        self.perception_range: int = int(defn.get('perception_range', 8))
        self.alert_radius:     int = int(defn.get('alert_radius', 5))
        self.alert_all_tag:    bool = bool(defn.get('alert_all_tag', False))

        # --- HP-threshold phase change (boss behaviour) ---
        # When hp drops below enrage_at_hp_pct, ai_pattern flips to enraged_pattern
        # (one-way; the swap is permanent for the encounter).
        self.enrage_at_hp_pct: float = float(defn.get('enrage_at_hp_pct', 0.0))
        self.enraged_pattern:  str   = defn.get('enraged_pattern', '')
        # Optional per-monster lines (data-driven; all fall back to a generic
        # line when absent): the enrage switch, each rage stack, standing back
        # up after a fatal blow, and the Journal entry for its death.
        self.enrage_message: str   = defn.get('enrage_message', '') or ''
        self.rage_messages:  list  = list(defn.get('rage_messages', []) or [])
        self.revive_message: str   = defn.get('revive_message', '') or ''
        self.kill_chronicle: str   = defn.get('kill_chronicle', '') or ''
        # A named pair (Stheno and Euryale): the partner's kind, and the line
        # written only when the second of the two falls (MON-10).
        self.kill_pair: str           = defn.get('kill_pair', '') or ''
        self.kill_pair_chronicle: str = defn.get('kill_pair_chronicle', '') or ''
        # Loses its footing when it attacks from an ICE tile (Fenrir's hall).
        self.slips_on_ice: bool    = bool(defn.get('slips_on_ice', False))
        # Fraction of every blow absorbed (Abaddon). base_ keeps the authored
        # value so it can be restored after an altar strips it.
        self.damage_ward: float      = float(defn.get('damage_ward', 0.0) or 0.0)
        self.base_damage_ward: float = self.damage_ward
        self._enraged: bool = False
        self._enrage_message: str = ''

        # --- Healer AI fields ---
        self.heal_amount_pct: float = float(defn.get('heal_amount_pct', 0.25))
        self._heal_target = None              # set when this monster healed someone
        self._heal_amount: int = 0

        # --- Summoner AI fields ---
        # summon_kind: str id, or list of str ids (random pick). Empty = no summon.
        self.summon_kind = defn.get('summon_kind', '')
        self.summon_cooldown: int = int(defn.get('summon_cooldown', 5))
        self.summon_max:      int = int(defn.get('summon_max', 4))
        self._summon_turn_counter: int = 0
        self._summons_made:        int = 0
        self._wants_summon: bool = False      # game loop polls this each turn

        # --- Charge (passive damage boost on straight-line approach) ---
        self.can_charge:        bool  = bool(defn.get('can_charge', False))
        self.charge_bonus_mult: float = float(defn.get('charge_bonus_mult', 1.5))
        self._charge_ready: bool = False      # set by movement when conditions met

        # --- Pack-dependent (aggressive with allies, cowardly alone) ---
        self.pack_dependent: bool = bool(defn.get('pack_dependent', False))
        self.pack_min_allies: int = int(defn.get('pack_min_allies', 1))

        # --- Flanker (prefer perpendicular approach when allies pressure player) ---
        self.prefers_flank: bool = bool(defn.get('prefers_flank', False))

        # --- Phase blink (teleport adjacent at distance) ---
        self.can_phase_blink:     bool  = bool(defn.get('can_phase_blink', False))
        self.phase_blink_chance:  float = float(defn.get('phase_blink_chance', 0.30))

        # --- Mimic surprise flag (set when mimic springs from disguise) ---
        self._mimic_surprise: bool = False
        # What an un-sprung mimic-AI creature is drawn as ({'item', 'name'}).
        self.disguise = defn.get('disguise') or None

        # --- Invisible by nature (src/unseen.py holds every rule) ---
        # Not seen without see invisible / true sight / telepathy. `_unseen`
        # is kept by the Game (it depends on the hero's senses) and turns
        # this creature's name into "something unseen" in every message;
        # `_felt_at` is the tile where the hero bumped into it.
        self.invisible: bool = bool(defn.get('invisible', False))
        self._unseen: bool = False
        self._felt_at = None

        # --- Boss multi-attack: fires all attacks per turn like Fenrir at
        # rage 3+. Currently used by Abaddon. Wired in act().
        self.multi_attack_always: bool = bool(defn.get('multi_attack_always', False))
        # Granular multi-attack: fire only the first N attacks per turn
        # (0 = all). Lets bosses ramp up — phase 1 fires 2, enraged phase
        # fires all 5. Tiamat/Asmodeus/Abaddon all use this for phase
        # escalation alongside enrage_at_hp_pct.
        self.multi_attack_count: int = int(defn.get('multi_attack_count', 0) or 0)
        self.enraged_multi_attack_count: int = int(defn.get('enraged_multi_attack_count', 0) or 0)
        # Its opening move (OPENER_WIND_UP above), the attack itself, or None.
        self.opener = None
        self._opener_attack = None
        _op = defn.get('opener')
        if isinstance(_op, dict) and _op.get('attack'):
            _oa = next((a for a in (defn.get('attacks') or [])
                        if isinstance(a, dict) and a.get('name') == _op['attack']), None)
            if _oa is not None:
                self.opener = {'attack': str(_op['attack']),
                               'range': max(1, int(_op.get('range', 1) or 1)),
                               'wind_up': str(_op.get('wind_up') or '')}
                self._opener_attack = _oa
        self._opened = False                # used this fight
        self._winding = False               # drawn up, to fire on its next turn
        # Chain-disrupt-on-hit: chance the strike disrupts the player's
        # chain meter for the next attack. Stored on player as
        # _chain_disrupt_pending; consumed by next chain-mode quiz start
        # if the quiz engine wires it. Currently JSON-stored, partial wire.
        self.chain_break_on_hit: float = float(defn.get('chain_break_on_hit', 0.0) or 0.0)
        # Drain heals self: vampires and life-drainers regain HP when their
        # drain attacks deal damage. Default 1.0 = full heal, 0.5 = half.
        self.drain_heals_self: float = float(defn.get('drain_heals_self', 0.0) or 0.0)
        # Revive-once-on-death: green_knight signature — first death drops
        # to 0 HP but the corpse pops back up to revive_hp_pct.
        self.revive_once_on_death: bool = bool(defn.get('revive_once_on_death', False))
        self.revive_hp_pct: float = float(defn.get('revive_hp_pct', 0.5) or 0.5)
        self._has_revived: bool = False
        # Pull-on-hit: chance the strike drags the player 2 tiles toward
        # the monster (charybdis / kraken / grappler family).
        self.pull_chance: float = float(defn.get('pull_chance', 0.0) or 0.0)
        # A named story foe (Neferkaptah, Azarael, Morrow): no article.
        self.proper_noun: bool = bool(defn.get('proper_noun', False))

        # --- 2026-10 late-game mechanics (all data-driven) ---
        # Thieves (src/theft.py): an attack with `steal` takes gold or an
        # item; `after_theft` says what the thief does then ('flee', or
        # 'teleport' somewhere else on the floor). What it carries falls out
        # when it dies. `_wants_steal` is polled by the game after the blow.
        self.after_theft: str = str(defn.get('after_theft', 'flee') or 'flee')
        self.stolen_gold: int = 0
        self.stolen_items: list = []
        self._wants_steal = None
        # Splitting (src/splitting.py): {'by': 'weak_blow' | [forms],
        # 'share', 'max', 'into'}. take_damage counts the splits a blow
        # earned in `_pending_splits`; the game spawns them.
        self.splits = defn.get('splits') or None
        self._pending_splits: int = 0
        self._incoming_forms = None
        # Weighs the hero's heart: its blows land harder on a low karma and
        # softer on a high one (Ammit's get).
        self.weighs_heart: bool = bool(defn.get('weighs_heart', False))
        # Never flees when hurt and cannot be frightened (the galla).
        self.fearless: bool = bool(defn.get('fearless', False))
        # Confused, it strikes the creature beside it instead (the Sown Men);
        # a thing thrown into the middle of them confuses the one it hits.
        self.quarrelsome: bool = bool(defn.get('quarrelsome', False))
        self.quarrels_when_struck_by_thrown: int = int(
            defn.get('quarrels_when_struck_by_thrown', 0) or 0)
        # The stalking coward (ai_pattern 'stalker_coward', data 'stalker':
        # Old Nickel, who wears the Bloomleaf Cloak; _stalker_turn). A false
        # friend until `_revealed`: he comes up to the hero and never
        # strikes. The act drops (for good) when the hero rests or lies
        # helpless near him, and his sneak attack follows (`_sneak_ready`),
        # or when the hero strikes him first; `_stalk_reveal` is why, for
        # the game's line. Revealed, he strikes only a hero beside him he
        # cannot back away from, backs off from a hero who comes at him,
        # follows one who walks away a few tiles off, and darts in on a hero
        # at rest. `_wary_home` is his own room (his hoard: set where he is
        # placed), `_hoard` the tile he keeps there; `_provoked` that he has
        # been in a fight (he struck the hero, or was struck); `_stalk_event`
        # what his turn did, for the game's lines (game: _old_nickel_turn).
        self.stalker = defn.get('stalker') or None
        self._revealed: bool = False
        self._sneak_ready: bool = False
        self._stalk_reveal: str = ''
        # 'it', 'he' or 'she' (data/monsters.json; see pronoun() above).
        self.pronoun: str = str(defn.get('pronoun') or kind_pronoun(self.kind))
        self._provoked: bool = False
        self._wary_home = None
        self._hoard = None
        self._stalk_lost: int = 0
        self._stalk_seen_at = None
        self._stalk_event: str = ''
        self._stalk_prey: str = ''
        # What the eye sees of him at first sight, whatever the hero knows of
        # the kind ("It wears a cloak of broad green leaves..."): a sight, not
        # lore (Game._maybe_tell, Observe).
        self.sight_sign: str = str(defn.get('sight_sign', '') or '')

    # Backward compat: old pickled monsters may lack newer attributes
    _DEFAULTS = {
        '_flee_timer': 0, '_alerted': False, '_aware': False, '_slow_skip': False,
        'speed': 10, 'resistances': [], 'weaknesses': [],
        'shrugs_off': (), 'status_immune': (), 'status_weak': (),
        'treasure': {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
        'peak_floor': 0, 'spread': 10,
        'lore': '', 'status_effects': {}, 'thac0': 20,
        'harvest_tier': 1, 'harvest_threshold': 2, 'ingredient_id': None,
        'min_level': 1, 'max_level': None,
        'can_phase_walls': False,
        '_hit_run_state': 'hunting', '_hit_run_timer': 0, '_hit_run_attacks': 0,
        'gaze_paralyze': 0, 'gaze_cooldown_max': 4, '_gaze_cooldown': 0, 'gaze_group': '',
        'kill_pair': '',
        'is_boss': False, 'dragon_scales': 0.0,
        'rage_interval': 0, 'rage_damage_bonus': '', 'rage_stacks': 0,
        '_rage_turn_counter': 0, '_rage_message': '',
        'locust_interval': 0, 'locust_count': [0, 0],
        '_locust_turn_counter': 0, '_wants_locust_spawn': False,
        'base_resistances': [],
        'is_allied': False, 'sp_drain': 0, 'is_seal_demon': False, 'is_mini_boss': False,
        # Senses (src/senses.py): knows where the hero is now; the place it is
        # going to look; its own business before it notices him.
        '_tracking': False, '_goal': None, '_searching': False, '_job': 'wander',
        '_home': None, '_path': None, '_lead_used': False,
        '_sense_how': '', '_sense_message': '', '_lost_line': '',
        '_annihilate_target': None,
        # New AI fields (2026 dungeon-depth pass)
        'perception_range': 8, 'alert_radius': 5, 'alert_all_tag': False,
        'enrage_at_hp_pct': 0.0, 'enraged_pattern': '',
        '_enraged': False, '_enrage_message': '',
        'heal_amount_pct': 0.25,
        '_heal_target': None, '_heal_amount': 0,
        'summon_kind': '', 'summon_cooldown': 5, 'summon_max': 4,
        '_summon_turn_counter': 0, '_summons_made': 0, '_wants_summon': False,
        'can_charge': False, 'charge_bonus_mult': 1.5, '_charge_ready': False,
        'recovers_when_left': False, '_unhurt_turns': 0, '_recovered_note': False, '_left_at_turn': None,
        'fury_per_attack': 0.0, 'fury_cap': 1.0, '_fury_swings': 0, '_fury_told': 0,
        'fury_message': '', 'min_hit_chance': None,
        'pack_dependent': False, 'pack_min_allies': 1,
        'prefers_flank': False,
        'can_phase_blink': False, 'phase_blink_chance': 0.30,
        '_mimic_surprise': False,
        'disguise': None, 'invisible': False, '_unseen': False, '_felt_at': None,
        # 2026-10 late-game mechanics. (stolen_items is read through
        # theft.carried(), which copes with this shared None.)
        'after_theft': 'flee', 'stolen_gold': 0, 'stolen_items': None, '_wants_steal': None,
        'splits': None, '_pending_splits': 0, '_incoming_forms': None,
        'weighs_heart': False, 'fearless': False,
        'quarrelsome': False, 'quarrels_when_struck_by_thrown': 0,
        # ('wary', '_wary_warned', '_wary_line': the old wary engine's, on a
        # Nickel saved before he became a stalker; the game makes him one.)
        'wary': None, '_provoked': False, '_wary_warned': False, '_wary_home': None,
        '_wary_line': '', 'sight_sign': '',
        'stalker': None, '_hoard': None, '_stalk_lost': 0, '_stalk_seen_at': None,
        '_stalk_event': '', '_stalk_prey': '', '_revealed': False, '_sneak_ready': False,
        '_stalk_reveal': '', '_help_wait': 0, '_help_hit': None,
        # Footprint default — every saved Monster from before the
        # multi-tile feature gets (1, 1) automatically. Live Monster
        # instances set this in __init__; pickled instances inherit it
        # through __getattr__ via this dict.
        'footprint': (1, 1),
    }

    def __getattr__(self, name):
        if name in Monster._DEFAULTS:
            return Monster._DEFAULTS[name]
        if name == 'family':
            # A monster saved before families looks its family up by kind.
            return _family_of_kind(self.__dict__.get('kind', ''))
        if name == 'pronoun':
            # A monster saved before pronouns takes its kind's (round 3).
            return kind_pronoun(self.__dict__.get('kind', ''))
        raise AttributeError(f"'Monster' object has no attribute {name!r}")

    # --- Status effects ---

    def add_effect(self, name: str, duration: int) -> int:
        """Put an effect on this monster for `duration` turns. Returns the
        turns it now has, or 0 when it did not take hold: its nature refuses
        it (status_immune, resists_control; `_refused_effect` remembers which,
        for the line that says why: affinity.status_line), or a named foe is
        steadying after a hold. What it falls to easily (status_weak) lasts
        half again as long (data/affinity_rules.json)."""
        if name == 'bleeding' and not self.can_bleed():
            return 0                        # nothing in it to bleed (kind_can_bleed)
        if self.resists_control(name):
            self.__dict__['_refused_effect'] = name
            return 0
        if name in (getattr(self, 'status_weak', None) or ()):
            import affinity as _aff
            duration = _aff.status_weak_duration(duration)
        # Named foes cannot be locked down. Whatever the source, a hard
        # control effect on a boss, mini-boss or seal demon lasts at most
        # NAMED_FOE_CONTROL_CAP turns and does not stack. Before this there
        # was no check on the monster's side at all: a sleep scroll put
        # Abaddon out for 25 turns, a time-freeze spell held every boss on
        # the level, and imprisonment was 30 to 60 turns of free hits.
        # (Quest effects that set the status directly, such as Gleipnir and
        # the Aegis, are deliberate and do not pass through here.)
        # A hold already running is not refreshed (a fresh stun every turn
        # kept the old one from ever running out), and once a hold ends a
        # named foe shakes off the next for NAMED_FOE_CONTROL_GRACE turns
        # ('control_immune', set in tick_effects).
        if name in _HARD_CONTROL and self._is_named_foe():
            if self.status_effects.get('control_immune', 0) > 0:
                return 0
            if self.status_effects.get(name, 0) > 0:
                return int(self.status_effects[name])   # held already: not refreshed
            self.status_effects[name] = max(
                self.status_effects.get(name, 0),
                min(int(duration), NAMED_FOE_CONTROL_CAP))
            return int(self.status_effects[name])
        current = self.status_effects.get(name, 0)
        self.status_effects[name] = min(current + duration, MAX_EFFECT_DURATION)
        return int(self.status_effects[name])

    def hold(self, name: str, duration: int):
        """Apply an effect keeping the longer of the old and new duration
        (the chain specials' rule: a second stun does not stack). A hard
        control effect on a named foe goes through add_effect's cap and
        grace instead; the chain specials used to write the status straight
        in and skip both, so a maul at chain 10 every turn stunned Asterion
        for the whole fight. What its nature refuses never takes hold, and
        what it falls to easily lasts half again as long (add_effect)."""
        if not self.alive:
            return
        if name == 'bleeding' and not self.can_bleed():
            return                          # nothing in it to bleed (kind_can_bleed)
        if name in _HARD_CONTROL and self._is_named_foe():
            self.add_effect(name, duration)
            return
        if self.resists_control(name):
            self.__dict__['_refused_effect'] = name
            return
        if name in (getattr(self, 'status_weak', None) or ()):
            import affinity as _aff
            duration = _aff.status_weak_duration(duration)
        cur = int(self.status_effects.get(name, 0) or 0)
        self.status_effects[name] = max(cur, int(duration))

    def can_bleed(self) -> bool:
        """It has blood to lose (data/monster_blood.json: a skeleton, a
        wraith, a golem, an ooze or a plant has none; a vampire and a ghoul
        do). "The Wraith is bleeding!" was said, and it lost health to it."""
        try:
            import family_lore
            return kind_can_bleed(getattr(self, 'kind', ''), family_lore.family_of(self),
                                  getattr(self, 'tags', None) or ())
        except Exception:
            return True

    # Which creatures shrug off which control effects. Lore, not balance:
    #   constructs and plants have no mind to frighten, charm or confuse;
    #   the undead feel no affection (charm) but CAN be turned (feared);
    #   plants have no eyes to blind;
    #   named foes (bosses, mini-bosses, seal demons) are too wilful to be
    #   charmed or routed, and true bosses cannot be pinned in place.
    _MINDLESS_TAGS = frozenset({'construct', 'plant'})

    def _is_named_foe(self) -> bool:
        return bool(getattr(self, 'is_boss', False)
                    or getattr(self, 'is_mini_boss', False)
                    or getattr(self, 'is_seal_demon', False))

    def resists_control(self, effect: str) -> bool:
        """True if this creature is immune to an effect by nature: its
        kind's `status_immune` (written from its lore: the mindless know no
        fear, the dead do not sleep or choke on poison), and the older tag
        rules below for a creature with no such list."""
        # Isildur's heir binds the Dead (Helm of Aragorn): the oath lifts the
        # dead's own immunity to charm, never a named foe's will (below).
        oath = effect == 'charmed' and bool(self.__dict__.get('_oathbound'))
        if effect in (getattr(self, 'status_immune', None) or ()) and not oath:
            return True
        if effect == 'burning':
            # Fire is fire (round 3, Brandon: "it's fire, make it so"): what
            # fire hardly touches does not catch fire at all. A fire
            # elemental never burns; a creature that only resists fire
            # burns, at half the rate (tick_effects: the burn is typed).
            return 'fire' in (getattr(self, 'shrugs_off', None) or ())
        tags = set(self.tags or ())
        mindless = bool(tags & self._MINDLESS_TAGS)
        if effect == 'feared':
            # The galla never give up the chase, and nothing frightens them
            # (`fearless`): a flask, a mass spell or a fright from fire
            # never says one is Feared (bug bash WB-B02).
            return mindless or self._is_named_foe() or bool(getattr(self, 'fearless', False))
        if effect == 'charmed':
            # The undead take no charm, except from Isildur's heir: the Helm of
            # Aragorn's command (_oathbound, set with its charm and gone when
            # the charm ends) binds the Dead to the oath they broke.
            undead_bars = 'undead' in tags and not self.__dict__.get('_oathbound')
            return mindless or undead_bars or self._is_named_foe()
        if effect == 'confused':
            return mindless
        if effect == 'blinded':
            return 'plant' in tags
        if effect == 'immobilized':
            return bool(getattr(self, 'is_boss', False))
        return False

    def _under(self, effect: str) -> bool:
        """Has the effect AND is not immune to it by nature."""
        return self.has_effect(effect) and not self.resists_control(effect)

    def has_effect(self, name: str) -> bool:
        return self.status_effects.get(name, 0) > 0

    def _drain_takes_hold(self, player) -> bool:
        """A drain hit costs a point of CON for good, so it gets a saving
        throw and a limit. It used to land on every hit with neither, and
        every point is also a point of max HP: a few wraiths took more off a
        character than a floor of cooking put on."""
        if int(getattr(player, 'CON', 10)) <= DRAIN_CON_FLOOR:
            return False
        if int(getattr(player, '_con_drained_this_floor', 0)) >= DRAIN_CON_PER_FLOOR:
            return False
        mod = (int(player.CON) - 10) // 2
        bonus = player.save_bonus_for('CON') if hasattr(player, 'save_bonus_for') else 0
        # A ward against this family's draining (Grave-Salt, Iron and Salt):
        # outside the +5 cap, earned against one family only.
        ward = _edge_save(player, self, 'drain')
        bonus += ward
        dc = min(18, 12 + self.min_level // 7)
        if random.randint(1, 20) + mod + bonus < dc:
            return True
        if ward > 0:
            # The save held: only now does the ward say so (it was said
            # before the roll, above a "drains your life force! (CON -1)").
            _edge_ward_held(player, self, 'drain')
        return False

    def _dot_divisor(self, ordinary: int) -> int:
        return NAMED_DOT_DIVISOR if self._is_named_foe() else ordinary

    def _min_hit(self) -> float:
        """Chance a blow that failed its roll lands anyway."""
        own = getattr(self, 'min_hit_chance', None)
        if own is not None:
            return float(own)
        return MIN_HIT_NAMED if self._is_named_foe() else MIN_HIT_ORDINARY

    def tick_effects(self):
        """Decrement all active effects by one turn. Apply damage-over-time effects."""
        bleeding_dmg = 0
        poison_dmg   = 0
        burning_dmg  = 0
        doom_dmg     = 0
        rupture_dmg  = 0
        disease_tick = False
        # A bleed written straight into the statuses (a weapon's or a pet's
        # proc, an old save) on a creature with no blood: gone, unfelt. So
        # is a burn on a creature that fire cannot set alight.
        if self.status_effects.get('bleeding') and not self.can_bleed():
            self.status_effects.pop('bleeding', None)
        if self.status_effects.get('burning') and self.resists_control('burning'):
            self.status_effects.pop('burning', None)
        for name in list(self.status_effects):
            val = self.status_effects[name]
            if val > 0:
                if name == 'bleeding':
                    bleeding_dmg = max(1, self.max_hp // self._dot_divisor(BLEED_DIVISOR))
                elif name == 'poisoned':
                    # A share of max HP like bleed and burn (it was a flat 1,
                    # which stopped meaning anything once HP was sized to depth).
                    poison_dmg = max(1, self.max_hp // self._dot_divisor(POISON_DIVISOR))
                elif name == 'diseased':
                    disease_tick = True
                elif name == 'burning':
                    burning_dmg = max(1, self.max_hp // self._dot_divisor(BURN_DIVISOR))
                elif name == 'doom_dot':
                    # Laevateinn (engine wave 4): doom_dot ticks N% of
                    # max_hp per turn. The % is stashed on the monster
                    # by the application code in combat.py.
                    _pct = float(getattr(self, '_doom_dot_pct', 0.05) or 0.05)
                    doom_dmg = max(1, int(self.max_hp * _pct))
                elif name == 'ruptured':
                    # Chain combat v2 (v2.14.0): dagger chain-20 signature.
                    # 10% max HP per turn AND cannot be healed (heal-block
                    # handled by the healing paths that check has_effect).
                    rupture_dmg = max(1, int(self.max_hp * 0.10))
            # Permanent effects (duration == -1) do NOT tick down or expire.
            if self.status_effects[name] < 0:
                continue
            self.status_effects[name] -= 1
            if self.status_effects[name] <= 0:
                del self.status_effects[name]
                if name == 'charmed':
                    self.__dict__.pop('_oathbound', None)   # the Helm of Aragorn's hold ends
                if name == 'petrifying':
                    self.hp = 0
                    self.alive = False
                # A named foe that comes out of a hold is briefly steady on
                # its feet (see add_effect). Set after the loop's snapshot,
                # so it is not ticked this turn: it lasts the full grace.
                elif (name in _HARD_CONTROL and self._is_named_foe()
                      and not any(self.status_effects.get(e, 0) > 0
                                  for e in _HARD_CONTROL)):
                    self.status_effects['control_immune'] = NAMED_FOE_CONTROL_GRACE
        # A wound that keeps bleeding is not a new blow: it never splits a
        # creature that splits (src/splitting.py).
        self._dot_tick = True
        try:
            if bleeding_dmg > 0:
                self.take_damage(bleeding_dmg)
            if poison_dmg > 0:
                # Typed: a creature that resists or shrugs off poison takes
                # less of it, one weak to it more (it was untyped, so the
                # poison wand ignored poison resistance).
                self.take_damage(poison_dmg, 'poison')
            if burning_dmg > 0:
                # Typed (round 3): a burn ticks as fire, so a creature weak
                # to fire burns twice as fast and one that resists it at
                # half the rate (data/affinity_rules.json). It was untyped,
                # and a fire-resistant creature burned at the full rate.
                self.take_damage(burning_dmg, 'fire')
            if doom_dmg > 0:
                self.take_damage(doom_dmg, 'fire')
            if rupture_dmg > 0:
                self.take_damage(rupture_dmg)
            if disease_tick:
                # Grave Rot (src/grave_rot.py, AI-1): a share of its health
                # every turn, poison's rate (it was 8% a turn of a twentieth).
                grave_rot.monster_tick(self, POISON_DIVISOR)
        finally:
            self._dot_tick = False

        # The behaviour clocks (AI-1): a gaze is ready again in its own time
        # for every gazer (it was counted down only by the dancer AI, so the
        # floating eye looked once in its life), a healer gathers its voice
        # (src/faction.py), a breath is drawn up again (src/breath.py).
        if self._gaze_cooldown > 0:
            self._gaze_cooldown -= 1
        faction.tick(self)
        breath.tick(self)

        # Regeneration: heal HP each turn (trolls, hydras).
        # Chain combat v2: `deep_wound` and `ruptured` block regen (heal-lock).
        regen = getattr(self, 'regeneration', 0)
        # A hero who knows the family's fire-and-dawn trick has stopped the
        # wound closing for a few turns (family_edges block_regen).
        _blocked = int(self.__dict__.get('_regen_blocked', 0) or 0)
        if _blocked > 0:
            self.__dict__['_regen_blocked'] = _blocked - 1
        if regen and self.alive and self.hp < self.max_hp:
            # Don't regenerate while burning (fire stops troll regen), or
            # while a heal-blocking wound (deep_wound / ruptured) is active.
            # A sick creature does not mend either (Grave Rot).
            if (not self.has_effect('burning') and self.can_heal() and _blocked <= 0
                    and not grave_rot.blocks_monster_regen(self)):
                self.hp = min(self.max_hp, self.hp + regen)
        self._unhurt_turns = int(getattr(self, '_unhurt_turns', 0)) + 1
        self._tick_fury()
        self._recover_when_left()

    def can_heal(self) -> bool:
        """False while a heal-blocking wound is on it: Gae Dearg's
        heal_blocked, the dagger's ruptured, deep_wound. Every way a monster
        regains health asks this (C10: only regeneration did, and only for
        two of the three)."""
        return not (self.has_effect('heal_blocked') or self.has_effect('deep_wound')
                    or self.has_effect('ruptured'))

    def _tick_fury(self):
        if (getattr(self, 'fury_per_attack', 0.0) and self.alive
                and self._unhurt_turns >= RECOVER_AFTER_TURNS):
            self._fury_swings = 0                 # left alone: it cools
            self._fury_told = 0

    def fury_mult(self) -> float:
        """Damage multiplier from fury (1.0 for almost every monster)."""
        per = getattr(self, 'fury_per_attack', 0.0)
        if not per:
            return 1.0
        return 1.0 + min(self.fury_cap, per * int(getattr(self, '_fury_swings', 0)))

    def fury_line(self) -> str:
        """Said once each time fury passes another quarter: the player
        should be able to see the race they are in."""
        step = int((self.fury_mult() - 1.0) / 0.25)
        if step <= int(getattr(self, '_fury_told', 0)):
            return ''
        self._fury_told = step
        return (getattr(self, 'fury_message', '')
                or f"{the_name(self)} grows more furious the longer this lasts.")

    def mend_for_absence(self, turns: int) -> int:
        """The player was on another floor for `turns` turns: recover as if
        those turns had passed here (see _recover_when_left). Returns the HP
        regained."""
        if not getattr(self, 'recovers_when_left', False) or not self.alive or turns <= 0:
            return 0
        self._unhurt_turns = int(getattr(self, '_unhurt_turns', 0)) + int(turns)
        mending = self._unhurt_turns - RECOVER_AFTER_TURNS + 1
        if mending <= 0:
            return 0
        self._fury_swings = 0
        self._fury_told = 0
        before = self.hp
        self.hp = min(self.max_hp,
                      self.hp + max(1, int(self.max_hp * RECOVER_SHARE)) * min(mending, int(turns)))
        if self.hp > before:
            self._recovered_note = True
        return self.hp - before

    _UNDODGEABLE = ('breath', 'spit', 'hurl', 'volley', 'gaze', 'stare', 'glare', 'howl',
                    'scream', 'wail', 'song', 'curse')

    def _slipped(self, player, atk) -> bool:
        """Dexterity: did the player slip this blow? Only a blow from beside
        them, and only something that can be sidestepped (not a breath, a
        gaze or a sound). Used on every melee path, single or multi-attack."""
        dodge = getattr(player, 'dodge_chance', None)
        if dodge is None or not self._adjacent_to(player):
            return False
        name = str((atk or {}).get('name', '')).lower()
        if any(w in name for w in self._UNDODGEABLE):
            return False
        return random.random() < dodge()

    def _recover_when_left(self):
        """Gate bosses: heal once the challenger has backed off (see
        RECOVER_AFTER_TURNS). Returns the HP regained this turn."""
        if not getattr(self, 'recovers_when_left', False) or not self.alive:
            return 0
        if self._unhurt_turns < RECOVER_AFTER_TURNS or self.hp >= self.max_hp:
            return 0
        if not self.can_heal():
            return 0
        before = self.hp
        self.hp = min(self.max_hp, self.hp + max(1, int(self.max_hp * RECOVER_SHARE)))
        if self.hp > before:
            self._recovered_note = True
        return self.hp - before

    # --- Combat ---

    def spring(self) -> bool:
        """A blow on an unaware lurker springs it (bug bash 5 MON-03, MON-05,
        PET-04: Brandon chose "any blow springs it"). An ambusher that has not
        sprung, or a mimic still in its disguise, struck by the hero, a pet,
        a wand or a spell, or dragged by a pet's pull, gives itself away and
        turns on whoever is near. Returns True when it was lurking.

        The reveal line is left in `_spring_note`, written while the
        disguise still holds; the game prints it (Game._say_springs)."""
        if getattr(self, '_aware', False) or getattr(self, 'ai_pattern', '') not in ('ambush', 'mimic'):
            return False
        was = the_name(self)
        disguised = was.lower() != 'something'
        self._aware = True
        self.ai_pattern = 'aggressive'
        if getattr(self, '_unseen', False):
            note = "Something unseen stirs!"
        else:
            what = a_name(self)        # aware now: its own name, "an Orc", "Arachne"
            if disguised:
                note = f"{was} springs to life -- it's {what}!"
            else:
                note = f"{what[:1].upper()}{what[1:]} springs from hiding!"
        self.__dict__['_spring_note'] = note
        return True

    def take_damage(self, amount: int, damage_type: str = 'physical',
                    ignore_resistance: bool = False) -> int:
        """Apply damage to this monster, consulting resistances/weaknesses for non-physical types.

        Melee callers (combat.player_attack) pre-scale damage with dragon_scales and the
        full weapon-type multiplier, then call take_damage(amount) — the default
        damage_type='physical' yields a 1.0 multiplier here, so no double-apply.

        Spell/wand callers pass the elemental type (fire/cold/lightning/acid/holy/...)
        and let take_damage apply the resistance lookup.

        ignore_resistance: when True, weaknesses still apply but resistances do not.
        Used by chain-equip unmaking_sense passive (Heart of Ahriman) on spell crits.

        Encounter NPCs (the cow, the karma and flavor NPCs, the unicorn) take
        no damage at all. They have 1 HP and stand among the monsters, and
        area spells do not skip them: one blast could delete a quest.
        """
        if (getattr(self, '_npc_encounter_tag', None) or getattr(self, '_flavor_encounter_tag', None)
                or getattr(self, '_is_unicorn', False) or getattr(self, 'is_allied', False)):
            return 0
        if amount > 0:
            self._unhurt_turns = 0           # see _recover_when_left
            self._struck = True              # a calmed locust remembers (Locust Charm)
            self.spring()                    # a struck lurker gives itself away
            if self.__dict__.get('_chanting') and not self.__dict__.get('_dot_tick'):
                summoning.spoil(self)        # a blow breaks a chant (src/summoning.py)
            if self.__dict__.pop('_bribed', False):
                # A bribed monster struck: the deal is off (Gilgamesh's Bribe).
                self.status_effects.pop('charmed', None)
        if damage_type and damage_type != 'physical':
            from combat import _damage_multiplier
            mult = _damage_multiplier([damage_type], self)
            if ignore_resistance and mult < 1.0:
                mult = 1.0
            amount = int(amount * mult)
            # A spell, wand or breath of a kind it is weak to, or resists:
            # said at the end of the action (affinity.py). A burn ticking is
            # not a hit.
            if amount >= 0 and not self.__dict__.get('_dot_tick'):
                import affinity
                affinity.note(self, affinity.kind_of(mult), damage_type)
        actual = max(0, amount)
        hp_before = self.hp
        self.hp = max(0, self.hp - actual)
        if actual > 0 and DAMAGE_OBSERVER is not None:
            try:
                DAMAGE_OBSERVER(self, actual, min(actual, hp_before))
            except Exception:
                pass
        # A creature that splits (src/splitting.py) notes the split this blow
        # earned; the game sets the new body down at the end of the action.
        if (actual > 0 and self.hp > 0 and getattr(self, 'splits', None)
                and not self.__dict__.get('_dot_tick')):
            from splitting import blow_splits
            if blow_splits(self, actual, damage_type):
                self._pending_splits = int(getattr(self, '_pending_splits', 0) or 0) + 1
        self._incoming_forms = None
        if self.hp == 0:
            # Green Knight (revive_once_on_death): the beheading-game pact.
            # First death pops back up at revive_hp_pct (default 0.5). Only
            # fires once per encounter.
            if getattr(self, 'revive_once_on_death', False) and not getattr(self, '_has_revived', False):
                self._has_revived = True
                self.hp = max(1, int(self.max_hp * float(getattr(self, 'revive_hp_pct', 0.5) or 0.5)))
                # Append a flag so the killing-blow path can announce it.
                self._just_revived = True
            else:
                self.alive = False
        if actual > 0:
            self.status_effects.pop('sleeping', None)
            self._after_typed_hit(damage_type, actual)
        return actual

    def _after_typed_hit(self, damage_type: str, actual: int) -> None:
        """What a hit of a kind the creature is weak to sets off besides the
        damage (data/affinity_rules.json):

        * a regenerating creature weak to fire or acid (the trolls, the
          hydra) cannot close the wound for regen_stop_turns turns: fire and
          acid stop a troll's healing, as Iolaus' torch stopped the Hydra's;
        * a beast or troll that fears fire (status_weak `fear_of_fire`)
          flees a fire hit for fear_of_fire_turns turns."""
        if damage_type not in ('fire', 'acid') or self.__dict__.get('_dot_tick') or not self.alive:
            return
        import affinity as _aff
        if (int(getattr(self, 'regeneration', 0) or 0) > 0
                and damage_type in (getattr(self, 'weaknesses', None) or ())):
            turns = int(_aff.rules().get('regen_stop_turns', 3))
            self.__dict__['_regen_blocked'] = max(int(self.__dict__.get('_regen_blocked', 0) or 0), turns)
        if (damage_type == 'fire'
                and _aff.FEAR_OF_FIRE in (getattr(self, 'status_weak', None) or ())
                and not getattr(self, 'fearless', False) and not self._is_named_foe()
                and not self.resists_control('feared')):
            self.hold('feared', int(_aff.rules().get('fear_of_fire_turns', 3)))
            if self.has_effect('feared'):
                _aff.note(self, _aff.FIRE_FRIGHT, 'fire')

    def is_dead(self) -> bool:
        return not self.alive

    def _through_material_weakness(self, player, dmg: int, atk_type: str):
        """(damage, note): a blow lands harder on a player whose weapon's
        material cannot bear it (cold iron and demons, wood and fire...);
        see combat.material_vulnerability (call 14)."""
        from combat import material_vulnerability
        mult, note = material_vulnerability(
            player, set(self.tags or ()) | {atk_type or 'physical'})
        if mult == 1.0:
            return dmg, ''
        return max(1, int(round(dmg * mult))), note

    def attack(self, player) -> tuple[int, str]:
        """Monster attacks player using THAC0 vs player AC. Returns (damage_dealt, message)."""
        # A monster that is swinging has not been left alone: it neither
        # mends nor cools (see _recover_when_left). Fury used to reset in the
        # middle of a fight whenever the player went 25 turns without a hit.
        self._unhurt_turns = 0
        # Sudarshana (engine wave 4): return_to_hand_ward. The previous
        # chain-5 kill set this flag — this attack misses outright and the
        # ward is consumed.
        if getattr(player, '_return_to_hand_active', False):
            player._return_to_hand_active = False
            return 0, f"{the_name(self)}'s strike is deflected — a discus spins between you!"
        if not self.attacks:
            # Floating eye: gaze-based paralysis (checks sleep_resist or total blindness)
            if player.get_sight_radius() == 0:
                return 0, f"{the_name(self)} gazes at you, but you cannot see {pronouns(self)[2]} eyes!"
            if _edge_gaze_immune(player, self):
                return 0, f"{the_name(self)} gazes at you, and you do not meet {pronouns(self)[2]} eyes."
            # A mirror shield (counters.py): the gaze slides off it.
            import counters as _counters
            _mirror = _counters.blocks_gaze(player, self)
            if _mirror is not None:
                return 0, _counters.line(player, _mirror, _counters.GAZE, self)
            if not player.has_effect('sleep_resist'):
                from status_effects import apply_debuff_with_save
                dc = min(18, 12 + self.min_level // 7)
                applied, _ = apply_debuff_with_save(player, 'paralyzed', 3, dc,
                                                    source=self, gaze=True)
                if applied:
                    return 0, f"{the_name(self)}'s gaze paralyzes you!"
                return 0, f"You wrench your gaze away from {the_name(self, lower=True)} just in time!"
            else:
                return 0, f"{the_name(self)} gazes at you harmlessly."

        # --- Gaze attack (Medusa): petrifying gaze before normal attack ---
        if self.gaze_paralyze > 0 and self._gaze_cooldown <= 0:
            self._gaze_cooldown = self.gaze_cooldown_max
            self._share_gaze_cooldown()
            # The gaze reaches across a room (see _dancer_turn): she may be
            # several tiles away. At range the gaze is her whole turn; next
            # to the player a gaze that fails still leaves her fangs.
            _at_range = not self._adjacent_to(player)
            import counters as _counters
            _mirror = _counters.blocks_gaze(player, self)
            _his = pronouns(self)[2]
            # Check player's sight: total blindness negates gaze
            if player.get_sight_radius() == 0:
                gaze_msg = f"{the_name(self)} locks eyes on you, but you are blind to {_his} gaze!"
                if _at_range:
                    return 0, (f"{the_name(self)} turns {_his} face full on you. "
                               f"You see nothing, and nothing happens.")
            # Proof against petrification (Medusa's trophy, the Greater
            # Aegis). The status existed but nothing consulted it: every gaze
            # paralyses, so the reward protected against nothing.
            elif player.has_effect('petrify_immune'):
                gaze_msg = (f"{the_name(self)}'s gaze slides off you. "
                            f"Stone has no claim on you now.")
                if _at_range:
                    return 0, gaze_msg
            # Perseus' Shield (family knowledge): watched in a shield, the
            # gaze of this family cannot take the hero at all.
            elif _edge_gaze_immune(player, self):
                _counters.fired(_counters.GAZE, self)
                gaze_msg = (f"You watch {the_name(self, lower=True)} in the bright metal "
                            f"of your shield, and the gaze slides off.")
                if _at_range:
                    return 0, gaze_msg
            # Check mirror shield (Aegis): reflects gaze back
            elif getattr(player.shield, 'id', '') in ('aegis_of_athena', 'greater_aegis_of_athena'):
                _counters.fired(_counters.GAZE, self)
                player._reflected_back = True      # read by game_combat for Perseus's trait
                # She loses this turn and the next, and does NOT also attack.
                # (It used to set 1 turn, which the next status tick removed
                # before she ever lost an action, and then she hit anyway.)
                # With a gaze every gaze_cooldown turns this is about half
                # her actions, which is what CURVE.md asks of the Aegis.
                self.status_effects['paralyzed'] = max(
                    self.status_effects.get('paralyzed', 0), 2)
                return 0, (f"{the_name(self)} meets {_his} own eyes in the bronze "
                           f"and stands rigid, snakes and all.")
            # Any other mirror shield (counters.py): watched in its face, the
            # gaze cannot take the hero (it is not the Aegis: no reflection).
            elif _mirror is not None:
                gaze_msg = _counters.line(player, _mirror, _counters.GAZE, self)
                if _at_range:
                    return 0, gaze_msg
            else:
                from status_effects import apply_debuff_with_save
                dc = min(18, 12 + self.min_level // 7)
                applied, _ = apply_debuff_with_save(player, 'paralyzed', self.gaze_paralyze, dc,
                                                    source=self, gaze=True)
                if applied:
                    return 0, (f"{the_name(self)}'s terrible gaze freezes you in place!")
                return 0, (f"You meet {the_name(self, lower=True)}'s gaze but tear your eyes away "
                           f"before the stone takes hold!")  # gaze turn: no damage
            # Gaze was blocked or reflected — continue to normal attack
            # (but append the gaze message below)
            atk = random.choice(self.attacks)
            # Behind a mirror shield a second gaze is no blow either (a
            # floating eye has nothing but its stare): nothing lands.
            if _mirror is not None and ('gaze' in str(atk.get('name', '')).lower()
                                        or atk.get('delivery') == 'gaze'):
                return 0, gaze_msg
            # Fall through to normal damage with gaze_msg prepended.
            # Bug-bash fix aac-#2: this inline path was bypassing all
            # damage-mitigation procs (unskinnable, weakened, summon-weaken,
            # back_attack_weakness). Re-route through the same mitigations.
            d20 = random.randint(1, 20)
            player_ac = player.get_ac()
            to_hit = self.thac0 - player_ac
            min_hit = self._min_hit()
            if d20 == 1:
                return 0, gaze_msg + " " + self._miss_text(atk)
            if d20 != 20 and d20 < to_hit:
                if random.random() >= min_hit:
                    return 0, gaze_msg + " " + self._miss_text(atk)
            if self._slipped(player, atk):
                return 0, gaze_msg + f" You slip {the_name(self, lower=True)}'s blow."
            dmg = roll(atk['damage'])
            # What was swung and how hard, before any armor: read by the
            # armor that answers a blow (Hydra carapace, Svalinn).
            self._last_attack_type = atk.get('type', 'physical')
            self._last_attack_roll = dmg
            atk_type = atk.get('type', 'physical')
            if self.has_effect('weakened'):
                dmg = max(1, dmg // 2)
            if self.has_effect('sundered'):
                # Chain combat v2: sundered halves outgoing monster damage.
                dmg = max(1, int(dmg * 0.70))
            # Hide of the Nemean Lion (unskinnable): physical/slash/pierce/blunt
            # attackers do half damage. Same condition as the main path.
            try:
                from armor_procs import player_has_armor_proc
                if player_has_armor_proc(player, 'unskinnable') and \
                        atk_type in ('physical', 'pierce', 'slash', 'blunt') and \
                        not getattr(self, 'magical', False) and \
                        'magic' not in (getattr(self, 'tags', []) or []) and \
                        'divine' not in (getattr(self, 'tags', []) or []):
                    if dmg > 1:
                        dmg = max(1, dmg // 2)
            except ImportError:
                pass
            dmg, _vuln_note = self._through_material_weakness(player, dmg, atk_type)
            dmg = _edge_incoming(player, self, dmg, atk_type)
            actual = player.take_damage(dmg, atk_type)
            return actual, (gaze_msg + " " + attack_line(self, atk, actual)
                            + (f" {_vuln_note}" if _vuln_note and actual > 0 else ''))

        # Attacking from ice: half the lunges go wide, and there is no
        # flurry. (The game loop sets _on_ice before calling attack. The ice
        # in Fenrir's hall used to slide the player and do nothing else, so
        # the arena was scenery.)
        _slipping = (getattr(self, 'slips_on_ice', False)
                     and getattr(self, '_on_ice', False))
        if _slipping and random.random() < 0.5:
            return 0, (f"{the_name(self)}'s claws find no purchase on the ice. "
                       f"The lunge goes wide.")

        # Its opening move (take_turn armed it): that attack, alone.
        _op_atk = self.__dict__.pop('_opener_now', None)
        if _op_atk is not None:
            self.__dict__.pop('_pack_blow', None)
            return self._resolve_blow(_op_atk, player)
        # The blow its pack's trick chose (src/packs.py): a goblin's sling
        # stone at range, its knife beside the hero.
        _pk_atk = self.__dict__.pop('_pack_blow', None)
        if _pk_atk is not None and not (self.multi_attack_count or self.multi_attack_always):
            return self._resolve_blow(_pk_atk, player)

        # Fenrir rage: at 3+ stacks, use ALL attacks instead of random choice
        if self.rage_stacks >= 3 and len(self.attacks) > 1 and not _slipping:
            return self._fenrir_multi_attack(player)

        # Tiered multi-attack (Tiamat, Asmodeus, Abaddon):
        #   multi_attack_count=N → fire first N attacks per turn
        #   enraged_multi_attack_count=M → swap to M when enraged
        #   multi_attack_always=True → fire ALL attacks (legacy Abaddon path)
        # Phase escalation via enrage_at_hp_pct gives the boss-fight rhythm.
        _macnt = int(getattr(self, 'multi_attack_count', 0) or 0)
        _emacnt = int(getattr(self, 'enraged_multi_attack_count', 0) or 0)
        if self._enraged and _emacnt > 0:
            _macnt = _emacnt
        if _macnt > 0 and _macnt < len(self.attacks):
            return self._fenrir_multi_attack(player, attack_limit=_macnt)
        if (getattr(self, 'multi_attack_always', False) or _macnt >= len(self.attacks)) \
                and len(self.attacks) > 1:
            return self._fenrir_multi_attack(player)

        # Ranged monsters at distance: prefer ranged attacks over melee
        if not self.attacks:
            return 0, f"{the_name(self)} flails helplessly!"
        if getattr(self, '_force_piercing', False):
            # Piercing turn: must use a piercing ranged attack
            self._force_piercing = False
            piercing_atks = [a for a in self.attacks
                             if a.get('piercing') and any(w in a.get('name', '').lower() for w in _RANGED_WORDS)]
            atk = random.choice(piercing_atks) if piercing_atks else random.choice(self.attacks)
        elif (self.ai_pattern == 'sessile' and not self._adjacent_to(player)
              and any(a.get('ranged') for a in self.attacks)):
            atk = random.choice([a for a in self.attacks if a.get('ranged')])
        elif (self.ai_pattern in ('healer', 'summoner') and not self._adjacent_to(player)
              and self._distance_attacks()):
            # C09: a caster at range uses its prayer or bolt, never its mace.
            atk = random.choice(self._distance_attacks())
        elif (self.ai_pattern in ('ranged', 'dragon') and not self._adjacent_to(player)
              and len(self.attacks) > 1):
            ranged_atks = [a for a in self.attacks
                          if a.get('ranged') or any(w in a.get('name', '').lower() for w in _RANGED_WORDS)]
            atk = random.choice(ranged_atks) if ranged_atks else random.choice(self.attacks)
        elif self.ai_pattern == 'dragon':
            # Adjacent: tooth and claw. The breath is for the approach.
            close_atks = [a for a in self.attacks if 'breath' not in a.get('name', '').lower()]
            atk = random.choice(close_atks or self.attacks)
        elif self.__dict__.get('_sneak_ready') and self.stalker:
            # The sneak attack comes with his first, best blow (Old Nickel's
            # stolen spear), not a kick.
            atk = self.attacks[0]
        else:
            atk = random.choice(self.attacks)
        # Draws Breath (src/breath.py): a breath still drawing is never used;
        # another blow ready is (never one from afar), else the turn is spent.
        atk = breath.choose(self, atk, player)
        if atk is None:
            return 0, breath.drawing_line(self)
        return self._resolve_blow(atk, player)

    def _pack_company(self) -> list:
        """The creatures about it this turn (take_turn keeps the list): its
        pack's tricks count the packmates beside the hero."""
        return [m for m in (self.__dict__.get('_cached_all_monsters') or ())
                if getattr(m, 'alive', False)]

    def _miss_text(self, atk: dict, *, confused: bool = False, note: str = '') -> str:
        """The line for a blow that misses. Only a blow that swings swings: an
        archer's arrow or a dragon's breath misses by name (playtest
        2026-10-24, "monsters that fire ranged attacks say they swing")."""
        low = str(atk.get('name', 'attack')).replace('_', ' ').lower()
        name = attack_noun(atk)
        who = the_name(self)
        tail = f" {note}" if note else ''
        # A shot or spell named by a verb misses as one ("The Skeleton
        # Archer shoots at you and misses!", not "...'s shoot misses you!").
        miss = (combat_lines().get('attack_misses') or {}).get(
            str(atk.get('name', '')).replace('_', ' '))
        if miss and not confused:
            return f"{who} {miss}!{tail}"
        if any(w in low for w in _MIND_WORDS):
            return f"{who}'s {name} fails to take hold of you!"
        if atk.get('ranged') or any(w in low for w in _RANGED_WORDS):
            if confused:
                return f"{who}'s {name} goes wild in {pronouns(self)[2]} confusion and misses!"
            return f"{who}'s {name} misses you!{tail}"
        if confused:
            return f"{who} swings wildly in confusion and misses!"
        return f"{who} swings at you and misses!{tail}"

    def _resolve_blow(self, atk: dict, player, in_flurry: bool = False) -> tuple[int, str]:
        """One blow with one attack, start to finish: the rules that can stop
        it, the roll to hit, the damage and everything that changes it, and
        everything that follows from it landing. Returns (damage, message).

        Both a single attack and each blow of a flurry come through here.
        The flurry used to have its own short copy (roll, damage, one status)
        and so 41 monsters, every mini-boss, seal demon and end boss among
        them, skipped the rest: no drain that heals, no Constitution drain,
        no pull, no charge, no rule about breath and a pit, no gaze immunity,
        no reflection, no Nemean hide."""
        atk_name = atk.get('name', 'attack').lower()
        atk_type = atk.get('type', 'physical')
        breath.spend(self, atk)              # a breath must be drawn again (src/breath.py)

        # Gaze attacks: blocked by blindness (player can't see the gaze)
        is_gaze = 'gaze' in atk_name or 'evil eye' in atk_name
        if is_gaze and player.get_sight_radius() == 0:
            return 0, f"{the_name(self)} tries to lock eyes with you, but you cannot see!"
        # Any paralysing gaze (the ordinary medusas' "Stony Gaze" as well as a
        # boss's): proof against petrification stops it, and so does a
        # mirror-bright shield held between you.
        if is_gaze and atk.get('effect') == 'paralyzed':
            if player.has_effect('petrify_immune'):
                return 0, f"{the_name(self)}'s gaze finds nothing in you to turn to stone."
            if _edge_gaze_immune(player, self):
                import counters as _counters
                _counters.fired(_counters.GAZE, self)
                return 0, (f"You watch {the_name(self, lower=True)} in the bright metal of "
                           f"your shield, and the gaze slides off.")
            if getattr(player.shield, 'id', '') in ('aegis_of_athena', 'greater_aegis_of_athena'):
                import counters as _counters
                _counters.fired(_counters.GAZE, self)
                return 0, (f"{the_name(self)} catches {pronouns(self)[2]} own eyes in the bronze "
                           f"and flinches away.")
        # A named counter turns any gaze aside, whatever it carries: no
        # damage and no rider (counters.py: the mirror shield, as Perseus's).
        if is_gaze or atk.get('delivery') == 'gaze':
            import counters as _counters
            _mirror = _counters.blocks_gaze(player, self)
            if _mirror is not None:
                return 0, _counters.line(player, _mirror, _counters.GAZE, self)

        # Breath/spit/hurl attacks miss player hiding in a pit
        is_breath = any(w in atk_name for w in ('breath', 'spit', 'hurl', 'volley'))
        if is_breath and player.has_effect('in_pit'):
            return 0, f"{the_name(self)}'s {attack_noun(atk)} passes harmlessly over your pit!"

        # The false friend's sneak attack (data 'stalker', Old Nickel): the
        # blow as the act drops on a hero at rest never misses its roll, and
        # lands 'sneak_mult' times as hard (sneak_blow; it can kill).
        _sneak = bool(self.__dict__.pop('_sneak_ready', False)) and bool(self.stalker)
        if _sneak:
            self._last_sneak = True          # (the game's line after it: none)

        # -- THAC0 Attack Roll ----------------------------------------------
        d20 = random.randint(1, 20)
        if _sneak:
            d20 = 20
        # A touch ignores body armour and shield (bug bash 3.3.2, 3e "touch
        # AC"): the gloves guard against it instead (guards.py).
        import guards as _guards
        if _guards.delivery(atk) == 'touch':
            player_ac = _guards.touch_ac(player)
        else:
            player_ac = player.get_ac()
        to_hit = self.thac0 - player_ac   # roll must be >= this to hit
        # Chain-equip passive: no_attack_of_opportunity (Sandals of Hermes T3+)
        # re-purposed as "free disengage" — if the player stepped away from
        # this monster's adjacent tile last turn, the monster's next attack
        # is at -2 to hit (effectively +2 player AC for this swing).
        if getattr(self, '_aoo_disengage_pending', False):
            to_hit += 2
            self._aoo_disengage_pending = False
        # AI-1 (src/ai_blow.py): at bay it strikes truer; a light-shy creature
        # flinches from a bright light.
        to_hit += ai_blow.to_hit_shift(self, player, atk)

        # Minimum hit chance (MIN_HIT_ORDINARY / MIN_HIT_NAMED)
        min_hit = self._min_hit()

        # Natural 1 always misses; natural 20 always hits
        if d20 == 1:
            return 0, self._miss_text(atk)
        if d20 != 20 and d20 < to_hit:
            # Depth minimum hit: even if THAC0 says miss, deep monsters can still connect
            if random.random() < min_hit:
                pass  # hit anyway — fall through to damage
            else:
                return 0, self._miss_text(atk, note=f"(AC {player_ac} deflects)")

        # Confused: 30% chance to swing at nothing
        if self.has_effect('confused') and random.random() < 0.30:
            return 0, self._miss_text(atk, confused=True)

        # Blinded: 40% chance to miss (can't see target)
        if self.has_effect('blinded') and random.random() < 0.40:
            return 0, f"{the_name(self)} flails blindly and misses!"

        # Dodge (Dexterity): a blow from beside you can be slipped. Breath,
        # spit and thrown things cannot, and nor can a gaze (handled above),
        # nor a friend's knife you never saw coming.
        if not is_breath and not _sneak and self._slipped(player, atk):
            return 0, f"You slip {the_name(self, lower=True)}'s blow."

        # Displacement's 30% miss is rolled once, by the caller in game_combat
        # (it used to be rolled here as well, for a combined 51% miss).

        # Bracers of Parrying (enchantments.py): a blow from beside you that
        # would land is parried. Not a breath, a missile, a gaze or a voice.
        if _guards.delivery(atk) in ('blow', 'bite', 'sting', 'trample', 'grapple', 'touch') and not _sneak:
            try:
                import enchantments as _ench
                _parry = _ench.might(player, 'parrying')
            except ImportError:
                _parry = 0.0
            if _parry > 0 and random.random() < _parry:
                return 0, f"You parry {the_name(self, lower=True)}'s blow."

        # Cloak of Sun Wukong (monkey_king_dodge): every Nth attack against the
        # player auto-misses. Counter is on the player; resets when armor unequipped.
        try:
            from armor_procs import proc_value
            mkd_n = int(proc_value(player, 'monkey_king_dodge') or 0)
            if mkd_n > 0:
                player._monkey_king_counter = int(getattr(player, '_monkey_king_counter', 0)) + 1
                if player._monkey_king_counter >= mkd_n:
                    player._monkey_king_counter = 0
                    return 0, f"You shimmer like the Monkey King — {the_name(self, lower=True)}'s strike finds nothing!"
        except ImportError:
            pass

        # Hermes votive sandals (dodge_first_arrow_per_floor): first ranged attack
        # per floor auto-misses. _RANGED_WORDS already computed above.
        _is_ranged_atk = bool(atk.get('ranged')) or any(w in atk_name for w in _RANGED_WORDS)
        if _is_ranged_atk:
            try:
                from armor_procs import consume_floor_charge
                if consume_floor_charge(player, 'dodge_first_arrow_per_floor'):
                    return 0, f"{the_name(self)}'s shot whistles past — the votive sandals carry you a hair's-breadth aside!"
            except ImportError:
                pass

        # -- Hit: roll damage -----------------------------------------------
        dmg = roll(atk['damage'])
        # What was swung and how hard, before any armor: read by the
        # armor that answers a blow (Hydra carapace, Svalinn).
        self._last_attack_type = atk.get('type', 'physical')
        self._last_attack_roll = dmg
        atk_type = atk.get('type', 'physical')

        # Rage damage bonus (Fenrir)
        if self.rage_stacks > 0 and self.rage_damage_bonus:
            for _ in range(self.rage_stacks):
                dmg += self._roll_rage_bonus()

        if getattr(self, 'fury_per_attack', 0.0):
            dmg = max(1, int(round(dmg * self.fury_mult())))
            self._fury_swings = int(getattr(self, '_fury_swings', 0)) + 1

        # Charge bonus: armed by movement when monster approached along a straight
        # line and is now adjacent. Consume one-shot.
        charged = False
        if self.can_charge and self._charge_ready:
            self._charge_ready = False
            dmg = max(1, int(dmg * self.charge_bonus_mult))
            charged = True

        # Mimic surprise: first hit after springing from disguise crits.
        mimic_strike = False
        if self._mimic_surprise:
            self._mimic_surprise = False
            # A hero who knows this family's ambushers is not caught
            # unawares (family_edges no_ambush): no surprise blow.
            if not _edge_no_ambush(player, self):
                dmg = int(dmg * 1.75)
                mimic_strike = True

        # Weakened: this monster's attack deals half damage
        if self.has_effect('weakened'):
            dmg = max(1, dmg // 2)

        # Chain combat v2 (v2.14.0): sundered = broken limb, -30% outgoing.
        if self.has_effect('sundered'):
            dmg = max(1, int(dmg * 0.70))

        # Chain-equip passive: weaken_summoned (Ring of Solomon).
        # Summoned monsters (marked _is_summoned=True at spawn) deal half damage.
        if getattr(self, '_is_summoned', False):
            try:
                from chain_passives import player_has_passive
                if player_has_passive(player, 'weaken_summoned'):
                    dmg = max(1, dmg // 2)
            except ImportError:
                pass

        # Hide of the Nemean Lion (unskinnable): non-magical blows do HALF
        # damage. (They used to do 1: from floor 53 that zeroed four or five
        # of every ten attacks in the game.) "Only divine arms scratch it" —
        # Heracles used the lion's own claws. Magic/holy/fire/cold/lightning/acid/poison/radiant all bypass
        # since they are not "blade hits hide." Pure physical/slash/pierce/blunt
        # gets clamped.
        try:
            from armor_procs import player_has_armor_proc
            if player_has_armor_proc(player, 'unskinnable') and \
                    atk_type in ('physical', 'pierce', 'slash', 'blunt') and \
                    not getattr(self, 'magical', False) and \
                    'magic' not in (getattr(self, 'tags', []) or []) and \
                    'divine' not in (getattr(self, 'tags', []) or []):
                if dmg > 1:
                    dmg = max(1, dmg // 2)
        except ImportError:
            pass

        # Chain-equip passive: back_attack_weakness (dragon_mail_of_sigurd).
        # Multiplier on incoming damage when monster is in the player's "rear arc"
        # (opposite to the player's facing). Treated as 1.5x by default.
        try:
            from chain_passives import get_back_attack_multiplier
            back_mult = get_back_attack_multiplier(player)
            if back_mult > 1.0:
                fx = getattr(player, '_facing_dx', 0)
                fy = getattr(player, '_facing_dy', 0)
                if fx or fy:
                    # Vector from player to attacker
                    rx = self.x - player.x
                    ry = self.y - player.y
                    # "Behind" if the dot product of facing and monster-direction
                    # is negative (monster lies opposite to where we're facing).
                    if (fx * rx + fy * ry) < 0:
                        dmg = max(1, int(dmg * back_mult))
        except ImportError:
            pass

        # A blow that is worse on a held hero (the mara's trample on a
        # sleeper): {"bonus_vs": {"sleeping": 1.5}} on the attack.
        _held_note = ''
        for _eff, _mult in ((atk.get('bonus_vs') or {}).items() if not _sneak else ()):
            if player.has_effect(_eff):
                dmg = max(1, int(round(dmg * float(_mult))))
                _held_note = f" It comes down on you while you are {_eff.replace('_', ' ')}!"
                break

        # Ammit's get weigh the heart: a blow lands harder on a low karma and
        # softer on a high one (Game.karma, -10..+10).
        if getattr(self, 'weighs_heart', False):
            dmg = max(1, int(round(dmg * heart_weight(player))))

        # Its pack's trick (src/packs.py): a rat's bite is worth more for every
        # other rat on the hero; hyenas harry a wounded hero; ghouls feed on a
        # held one.
        _pack_note = ''
        if packs.pack_of(self.kind) and not _sneak:
            _pm, _pack_note = packs.blow_mult(self, player, atk, self._pack_company())
            if _pm != 1.0:
                dmg = max(1, int(dmg * _pm + 0.5))

        dmg, _vuln_note = self._through_material_weakness(player, dmg, atk_type)
        # Family knowledge that turns this family's fire, cold or holy
        # light aside (Dragon-Ward, Ward of the Elements, Angel's Due).
        dmg = _edge_incoming(player, self, dmg, atk_type)
        # The minor slots' guards (guards.py): the helm against voice and
        # gaze, the gloves against touch, the cloak against breath and the
        # elements... turn aside a share of a matching attack's damage.
        _keep_d, _keep_r, _guard_piece = _guards.guard_keep(player, atk)
        if _keep_d < 1.0 and dmg > 0:
            dmg = max(1, int(round(dmg * _keep_d)))
        if _sneak:
            dmg = self.sneak_blow(dmg, player)
            _held_note = " A friend's blow: you never saw it coming!"
        actual = player.take_damage(dmg, atk_type)

        if getattr(self, '_unseen', False) is True:
            # Nothing to name and nothing seen swinging (src/unseen.py).
            msg = f"Something unseen strikes you for {actual} damage!"
        else:
            msg = attack_line(self, atk, actual)
        if _vuln_note and actual > 0:
            msg += f" {_vuln_note}"
        if _held_note and actual > 0:
            msg += _held_note
        if packs.pack_of(self.kind):
            if _pack_note and actual > 0:
                msg += ' ' + _pack_note
            # A wolf's hamstring with a packmate beside the hero; a harpy's
            # snatch.
            msg += packs.after_blow(self, player, atk, actual, self._pack_company())
        # A thief's blow (src/theft.py): the game takes the gold or the item
        # right after this blow, because the purse belongs to the Game.
        if atk.get('steal') and random.random() < float(atk.get('steal_chance', 1.0)):
            self._wants_steal = atk['steal']
        if charged:
            msg = f"{the_name(self)} CHARGES! " + msg
        if mimic_strike:
            msg = f"{the_name(self)} ERUPTS from {pronouns(self)[2]} disguise! " + msg

        # Fire/cold shield: if attack was blocked (actual=0), reflect damage back
        # Typed (round 3): its own fire turned back burns as fire, so a
        # creature that resists fire takes less of it.
        if actual == 0 and atk_type == 'fire' and player.has_effect('fire_shield'):
            refl = self.take_damage(max(1, dmg // 2), 'fire')
            msg = f"{the_name(self)}'s fire reflects back! ({refl} dmg)"
        elif actual == 0 and atk_type == 'cold' and player.has_effect('cold_shield'):
            refl = self.take_damage(max(1, dmg // 2), 'cold')
            msg = f"{the_name(self)}'s cold reflects back! ({refl} dmg)"

        # Chain-equip passive: reflect_spell / spell_reflect (Aegis of Athena,
        # Smoking Mirror). Magical/elemental damage rolls % chance to reflect
        # full damage back at the attacker.
        if atk_type in ('fire', 'cold', 'lightning', 'magic', 'acid', 'poison',
                        'force', 'necrotic', 'radiant', 'psychic') and actual > 0:
            try:
                from chain_passives import get_reflect_spell_chance
                chance = get_reflect_spell_chance(player)
                if chance > 0 and random.random() < chance:
                    refl = self.take_damage(max(1, dmg), atk_type)   # typed (round 3)
                    msg += f" The {atk_type} damage reflects back! ({refl} dmg)"
            except ImportError:
                pass

        # Chain-equip passive: mirror_of_souls (Smoking Mirror of Tezcatlipoca).
        # 20% chance an incoming melee attacker takes the same damage they dealt.
        if atk_type in ('physical', 'pierce', 'slash', 'blunt') and actual > 0:
            try:
                from chain_passives import roll_mirror_of_souls
                refl = roll_mirror_of_souls(player, self, actual)
                if refl:
                    self.take_damage(refl)
                    msg += f" The Mirror of Souls turns the blow against you! ({refl} dmg)"
            except ImportError:
                pass

        # Chain-equip passive: gorgoneion_petrify_on_hit (Greater Aegis of Athena).
        # First melee striker each floor saves vs petrification (paralyzed proxy).
        if atk_type in ('physical', 'pierce', 'slash', 'blunt') and actual > 0:
            try:
                from chain_passives import roll_gorgoneion_petrify
                if roll_gorgoneion_petrify(player, self):
                    msg += f" The Gorgoneion meets {the_name(self, lower=True)}'s eyes! Petrified!"
            except ImportError:
                pass

        # Hero passive: Tesla's Resonant Frequency — shock-counter on melee hits.
        if actual > 0 and atk_type in ('physical', 'pierce', 'slash', 'blunt') and \
                'resonant_frequency' in getattr(player, 'hero_passives', set()):
            from floor_curve import wound
            shock = wound(RESONANCE_SHARE, self.max_hp, self._is_named_foe())
            self.take_damage(shock)
            msg += f" (Resonance arcs back: {shock} shock!)"

        # Hero buff: Leonidas Spartan Stand counter-strike
        if actual > 0 and player.status_effects.get('stand_ac', 0) > 0:
            import random as _ssr
            cpct = getattr(player, '_stand_counter_pct', 0)
            if cpct > 0 and _ssr.randint(1, 100) <= cpct:
                from floor_curve import wound
                cstrike = wound(SPARTAN_COUNTER_SHARE, self.max_hp, self._is_named_foe())
                self.take_damage(cstrike)
                msg += f" (Counter-strike: {cstrike} dmg!)"

        # AI-1 (src/ai_blow.py): what follows a landed blow (a nerve broken
        # by blows that do nothing, a light put out, a shove), and a drain
        # blow's life taken (src/life_drain.py: lasting max HP; the old CON
        # point for the liches and the death lord, and for named foes).
        msg = ai_blow.after_blow(self, player, atk, actual, msg)

        # Drain heals self (vampire lord, life-drainer family): when a
        # drain attack lands, regain a fraction of the damage dealt.
        # JSON: drain_heals_self = 1.0 → full heal, 0.5 → half. Audit fix
        # for ancient_vampire_lord: "drain attack causes CON -1 but doesn't
        # heal the vampire — not a vampire."
        _dhs = float(getattr(self, 'drain_heals_self', 0.0) or 0.0)
        if (atk_type == 'drain' and _dhs > 0 and actual > 0 and self.alive and self.can_heal()
                and not _edge_drain_block(player, self)):
            heal = max(1, int(actual * _dhs))
            self.hp = min(self.max_hp, self.hp + heal)
            msg += f" {the_name(self)}'s wounds close as {pronouns(self)[0]} feeds ({heal} HP regained)."

        # Chain-disrupt: chance the strike interrupts the player's chain
        # build for the next attack. Sets a flag the quiz engine can read
        # (currently stored; consumer pending).
        _cbh = float(getattr(self, 'chain_break_on_hit', 0.0) or 0.0)
        if _cbh > 0 and actual > 0 and random.random() < _cbh:
            player._chain_disrupt_pending = True

        # Pull-on-hit (Charybdis, kraken, grappler family): drag the player
        # 1-2 tiles toward this monster. Storms request via a flag the
        # game loop honors when it can resolve movement.
        _pc = float(getattr(self, 'pull_chance', 0.0) or 0.0)
        if _pc > 0 and actual > 0 and random.random() < _pc:
            player._pending_pull_toward = (self.x, self.y)
            msg += f" {the_name(self)} drags you closer!"

        # Apply status effect from attack (gated by a D&D-style saving throw).
        # In a flurry at most one lands, so a five-attack boss cannot stack a
        # stun, a freeze and a slow in one turn.
        if not (in_flurry and getattr(self, '_flurry_effect_done', False)):
            _eff = ''
            if actual > 0 or not in_flurry:
                # (gaze only when it is one: the ward against a killing gaze)
                _eff = (self._apply_attack_effect(atk, player, gaze=True) if is_gaze
                        else self._apply_attack_effect(atk, player))
            if in_flurry and _eff:
                self._flurry_effect_done = True
            msg += _eff

        return actual, msg

    def _apply_attack_effect(self, atk: dict, player, gaze: bool = False) -> str:
        """Roll an attack's on-hit status effect against the player.

        Returns the text to append to the attack message ('' if nothing
        happened). Shared by the single-attack path and the multi-attack
        path; the latter used to skip effects entirely, so Asmodeus,
        Surtur, Ymir and Hrungnir never applied theirs.
        """
        effect_id = atk.get('effect')
        if not effect_id:
            return ''
        chance   = atk.get('effect_chance', 0.30)
        duration = roll_duration(atk.get('effect_duration', 5))
        if effect_id == 'diseased':
            duration = grave_rot.linger(duration)    # it lingers (Grave Rot, AI-1)
        # The minor slots' guards shrug off a matching rider (guards.py):
        # the helm a stare's paralysis, the boots a slowing, the shirt a
        # poisoning... The roll that would have landed and did not is told.
        import guards as _guards
        _keep_d, keep_r, piece = _guards.guard_keep(player, atk)
        roll = random.random()
        if roll >= chance:
            return ''
        # A named counter stops it outright (counters.py): wax in the ears
        # against a voice, cold iron against the Fair Folk's glamour.
        import counters as _counters
        _blocked = _counters.blocks_rider(player, self, atk, effect_id)
        if _blocked is not None:
            return " " + _counters.line(player, _blocked[0], _blocked[1], self)
        if roll >= chance * keep_r:
            if piece is not None:
                from hud_context import item_bare_name
                return (f" Your {item_bare_name(player, piece)} turns the "
                        f"{effect_id.replace('_', ' ')} aside.")
            return ''
        # What the body armour's material stops outright (gear.ward_against,
        # data/gear_rules.json wards): cold iron turns the fair folk's
        # glamour, dragonscale will not catch fire. Told, so a kid who
        # chose the iron sees it work.
        import gear as _ap
        _ward = _ap.ward_against(player, self, effect_id)
        if _ward is not None:
            return " " + _ap.ward_line(player, _ward[0], _ward[1])
        if effect_id == 'rust':
            # A rust monster's feelers (no saving throw: one brush and good
            # steel flakes to red dust). The one rust rule:
            # status_effects.rust_worn_gear.
            from status_effects import rust_worn_gear
            got = rust_worn_gear(player, self)
            return (" " + got[0]) if got else ''
        # Reflecting: 50% chance to bounce effect back at attacker
        if player.has_effect('reflecting') and random.random() < 0.50:
            self.add_effect(effect_id, duration)
            player._reflected_back = True          # read by game_combat for Perseus's trait
            return f" The effect reflects back -- {the_name(self, lower=True)} is {effect_id.replace('_', ' ')}!"
        from status_effects import apply_debuff_with_save
        # DC scales gently with monster depth; data may override.
        dc = min(18, int(atk.get('effect_save_dc', 12 + self.min_level // 7)))
        # source=self: the hero's ward against this family (family_edges)
        # adds to the save, or shortens an effect that has none.
        _applied, _emsg = apply_debuff_with_save(player, effect_id, duration, dc,
                                                 source=self, gaze=gaze)
        return (" " + _emsg) if _emsg else ''

    # --- AI ---

    def take_turn(self, player, dungeon, all_monsters, extra_occupied=None) -> bool:
        """Execute this monster's turn. Returns True if it attacked the player.
        extra_occupied: optional set of (x,y) positions to avoid (e.g. pet tiles).

        Status-effect ticking happens once per game turn in Game._advance_turn, not
        here — ticking in both places would halve effect durations and double DOTs.
        """
        # Cache the monster list so AI helpers (flanker, etc.) can inspect allies
        # without passing it through every internal helper.
        self._cached_all_monsters = all_monsters

        if not self.alive:
            return False
        if tuple(self.footprint) != (1, 1):
            from geom import all_occupied_tiles
            self._turn_occupied = (all_occupied_tiles(all_monsters, exclude=self)
                                   | set(extra_occupied or ()) | {(player.x, player.y)})

        # Held: asleep, paralysed, stunned or frozen. The last two were
        # applied by thirteen weapon specials and four spells, announced
        # ("is stunned!") and then read by nothing.
        if (self.has_effect('sleeping') or self.has_effect('paralyzed')
                or self.has_effect('stunned') or self.has_effect('frozen')):
            return False

        # A hound of a pack that bayed keeps the hero's scent (src/packs.py).
        if self.__dict__.get('_scent_left'):
            packs.keep_scent(self, player)

        # Stuck in a pit: can attack if adjacent, but cannot move
        if self.has_effect('stuck_in_pit'):
            if self._adjacent_to(player):
                return True  # attack from the pit
            return False  # can't move, can't reach

        # Chain combat v2 (v2.14.0): impaled by a spear. Same shape as
        # stuck_in_pit — can still attack the adjacent player, but the pinning
        # weapon holds the monster in place for the duration.
        if self.has_effect('impaled') or self._under('immobilized'):
            if self._adjacent_to(player):
                return True
            return False

        # --- Variable speed: slow monsters skip turns ---
        if self.speed < 8 and self.speed > 0:
            # speed 6 => skip 40% of turns, speed 4 => skip 60%, etc.
            if random.random() < (8 - self.speed) / 10.0:
                return False

        # Slowed: skip every other turn
        if self.has_effect('slowed'):
            self._slow_skip = not self._slow_skip
            if self._slow_skip:
                return False

        # --- HP-threshold phase change (boss "second phase" mechanic) ---
        # A foe with summon data but another AI pattern (Tiamat, Asmodeus)
        # still calls its minions: the timer used to run only inside the
        # 'summoner' pattern, so theirs never appeared.
        if (self.summon_kind and self.ai_pattern != 'summoner'
                and getattr(self, '_aware', False)
                and self._summons_made < self.summon_max):
            if self._is_named_foe():
                # Tiamat and Asmodeus keep their own tuned timers.
                self._summon_turn_counter += 1
                if self._summon_turn_counter >= self.summon_cooldown:
                    self._wants_summon = True
                    self._summon_turn_counter = 0
                    self._summons_made += 1
            elif (self.__dict__.get('_tracking')
                  and summoning.step(self, player, all_monsters, dungeon)):
                # An ordinary lich or skeleton mage calls as a summoner does
                # (src/summoning.py): it chants, then its dead come.
                return False

        # One-way swap to enraged_pattern when HP drops below threshold.
        if (not self._enraged
                and self.enraged_pattern
                and self.enrage_at_hp_pct > 0
                and self.hp <= self.max_hp * self.enrage_at_hp_pct
                and self.hp > 0):
            self._enraged = True
            old_pat = self.ai_pattern
            self.ai_pattern = self.enraged_pattern
            del old_pat
            self._enrage_message = (
                getattr(self, 'enrage_message', '')
                or f"{the_name(self)} fights like a thing with nothing left to lose.")

        # --- Pack-dependent: aggressive with allies nearby, cowardly alone ---
        # Re-evaluates each turn so the pattern tracks the immediate situation.
        if self.pack_dependent and self.ai_pattern in ('aggressive', 'cowardly'):
            allies_near = sum(
                1 for m in all_monsters
                if m is not self and m.alive
                and (m.kind == self.kind or (set(self.tags) & set(getattr(m, 'tags', []))))
                and abs(m.x - self.x) + abs(m.y - self.y) <= 5
            )
            self.ai_pattern = 'aggressive' if allies_near >= self.pack_min_allies else 'cowardly'

        # --- Morale by Nature (src/morale.py, AI-1) ---
        # Each creature breaks the way its nature says: the mindless never, a
        # beast bolts, a goblin runs for its friends, a giant falls back. One
        # check a trigger, never re-armed; named foes never break (this was
        # `max_hp > 500` as well, which kept half of every ordinary kind from
        # floor 21 down from ever breaking). The galla are fearless; a
        # war-band follower holds while his leader lives; a hyena that smells
        # a wounded hero never runs (all in morale.turn).
        morale.turn(self, player, all_monsters)

        # --- Mind-affecting statuses: apply to EVERY AI pattern ---
        # These used to sit below the pattern dispatch, so ranged, healer,
        # summoner, hit-and-run, dancer and boss patterns (about 136
        # monsters) ignored fear / confusion / blindness entirely, and
        # charm had no monster-side effect at all. Rooted monsters
        # (sessile, a mimic still in disguise) cannot flee or stumble.
        if self.ai_pattern not in ('sessile', 'mimic'):
            if self._under('feared'):
                self._flee_from(player, dungeon, all_monsters, extra_occupied)
                return False
            if self._under('charmed'):
                # A charmed creature will not raise a hand against the player.
                self._wander(dungeon, all_monsters, extra_occupied, player)
                return False
            if self.quarrelsome and self._under('confused'):
                # The Sown Men: confused, each blames the man beside him.
                if self._strike_a_brother(all_monsters):
                    return False
            if self._under('confused') and random.random() < 0.40:
                self._stumble_random(dungeon, all_monsters, extra_occupied, player)
                return False
            if self._under('blinded') and random.random() < 0.30:
                self._stumble_random(dungeon, all_monsters, extra_occupied, player)
                return False
        elif self._under('charmed'):
            # Rooted, so it cannot wander off; charmed, it still holds its blow.
            return False

        # --- The stalking coward (data 'stalker': Old Nickel) ---------------
        if self.ai_pattern == 'stalker_coward':
            return self._stalker_turn(player, dungeon, all_monsters, extra_occupied)

        # --- A thief with a haul runs (src/theft.py); cornered, it fights ---
        if self.__dict__.get('stolen_gold') or self.__dict__.get('stolen_items'):
            self._aware = True
            before = (self.x, self.y)
            self._flee_from(player, dungeon, all_monsters, extra_occupied)
            if (self.x, self.y) == before and self._adjacent_to(player):
                return True
            return False

        # --- A broken creature runs (src/morale.py): to its friends or away
        # along a real path; cornered beside the hero it turns at bay. A beast
        # that bolted keeps away for good; one that yielded never strikes.
        _run = morale.run(self, player, dungeon, all_monsters, extra_occupied)
        if _run is not None:
            return _run

        # --- Phase-blink for the patterns that never reached it (G7): an
        # archer or a summoner that can blink steps out to a clear shot four
        # tiles off; a hit-and-run one (Lyssa) blinks in beside the hero.
        if (self.can_phase_blink and self.ai_pattern in ('ranged', 'summoner', 'hit_and_run')
                and self.__dict__.get('_tracking')
                and random.random() < self.phase_blink_chance):
            if self.ai_pattern == 'hit_and_run':
                if (max(abs(self.x - player.x), abs(self.y - player.y)) >= 3
                        and self._phase_blink_to_player(player, dungeon, all_monsters, extra_occupied)):
                    return True
            elif self._blink_to_standoff(player, dungeon, all_monsters, extra_occupied):
                return False

        # --- Healer AI: heal a damaged adjacent ally; fall back to ranged/aggressive ---
        if self.ai_pattern == 'healer':
            return self._healer_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Summoner AI: spawn minions on cooldown; otherwise behave as ranged ---
        if self.ai_pattern == 'summoner':
            return self._summoner_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Mimic AI: silent until player steps adjacent, then spring with surprise ---
        if self.ai_pattern == 'mimic':
            return self._mimic_turn(player, dungeon, all_monsters, extra_occupied)

        # The hunters below used to skip noticing altogether and hunt the hero
        # from anywhere on the floor (G6): they notice him like anything else
        # now. Asterion and Abaddon are masters of their own houses and Fenrir
        # has a wolf's nose (data/senses.json), so their fights begin as
        # before; an imp or a brigand has to find you first.
        if self.ai_pattern in ('hit_and_run', 'dancer', 'fenrir_rage', 'abaddon'):
            if (self.ai_pattern != 'hit_and_run' or self._hit_run_state == 'hunting'):
                if not self._spots_player(player, dungeon, all_monsters, extra_occupied):
                    return False

        # --- Hit-and-run AI (Asterion): attack then vanish through walls ---
        if self.ai_pattern == 'hit_and_run':
            return self._hit_and_run_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Dancer AI (Medusa): sidestep then strike ---
        if self.ai_pattern == 'dancer':
            return self._dancer_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Fenrir rage AI: aggressive + escalating rage ---
        if self.ai_pattern == 'fenrir_rage':
            return self._fenrir_rage_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Abaddon AI: aggressive + locust swarm spawning ---
        if self.ai_pattern == 'abaddon':
            return self._abaddon_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Seek-locust AI (angels): move toward nearest locust ---
        if self.ai_pattern == 'seek_locust':
            return self._seek_locust_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Dragon AI (Fafnir): breathe on the way in, then close ---
        if self.ai_pattern == 'dragon':
            # A dragon's nose finds a thief across its hoard (Smaug, Fafnir;
            # data/senses.json gives the dragons scent 10). Until then it lies
            # coiled where it is.
            if not self._spots_player(player, dungeon, all_monsters, extra_occupied):
                return False
            return self._dragon_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Ranged AI: shoot from distance, maintain range ---
        if self.ai_pattern == 'ranged':
            if not self._spots_player(player, dungeon, all_monsters, extra_occupied):
                return False
            _op = self._opener_from_range(player, dungeon)
            if _op is not None:
                return _op
            return self._ranged_turn(player, dungeon, all_monsters, extra_occupied)

        # --- Ambush AI: stay still until player is within 5 tiles ---
        if self.ai_pattern == 'ambush':
            if getattr(self, '_aware', False):
                # Already detected by PER check — switch to aggressive
                self.ai_pattern = 'aggressive'
            else:
                dist = abs(self.x - player.x) + abs(self.y - player.y)
                if dist > 5:
                    return False  # lurk silently, invisible
                # It springs on what it can see (or touch), not through stone.
                import senses as _senses
                if (not self._adjacent_to(player)
                        and not _senses.clear_view(self.x, self.y, player.x, player.y, dungeon)):
                    return False
                # Sprung! Switch to aggressive and become visible
                self.ai_pattern = 'aggressive'
                self._aware = True

        # --- Detection range: per-monster perception_range (default 8) ---
        if not self._spots_player(player, dungeon, all_monsters, extra_occupied):
            # Back to the Web (src/relurk.py): a hurt ambusher out of his
            # sight goes back into hiding.
            relurk.consider(self, player)
            return False
        dist_to_player = abs(self.x - player.x) + abs(self.y - player.y)
        # Its opener from a distance (a gaze, a song, a first arrow), before
        # it closes or the hero can strike.
        if self.ai_pattern not in ('sessile', 'cowardly') and self._flee_timer <= 0:
            _op = self._opener_from_range(player, dungeon)
            if _op is not None:
                return _op

        # --- Phase-blink: chance to teleport adjacent to player when at distance ---
        # Applied AFTER detection/awareness so unaware monsters don't teleport.
        if self.can_phase_blink and dist_to_player >= 3:
            if random.random() < self.phase_blink_chance:
                if self._phase_blink_to_player(player, dungeon, all_monsters, extra_occupied):
                    return True  # adjacent now — attack this turn

        # --- Call for help: alert same-kind allies within 5 tiles ---
        if self._adjacent_to(player):
            self.alert_nearby(all_monsters)

        # Aggravated overrides passive/cowardly AI patterns
        effective_pattern = self.ai_pattern
        if player.has_effect('aggravated') and effective_pattern == 'cowardly':
            effective_pattern = 'aggressive'

        # Alerted monsters act aggressive. A rooted thing stays rooted (G8:
        # an alerted mold or floating eye used to walk the floor).
        if self._alerted and effective_pattern == 'cowardly':
            effective_pattern = 'aggressive'

        # A broken creature (morale) that run() did not move flees as a coward
        if self._flee_timer > 0 and effective_pattern == 'aggressive':
            effective_pattern = 'cowardly'

        if effective_pattern == 'sessile':
            # Rooted things do not chase, but they do strike what comes
            # within reach. This returned False before the adjacency check,
            # so a lone plant, mold, ooze or statue never attacked at all
            # (measured: 0 attacks in 200 turns standing next to one).
            if self._adjacent_to(player):
                return True
            if any(a.get('ranged') for a in self.attacks):
                dist = max(abs(self.x - player.x), abs(self.y - player.y))
                if (dist <= self._RANGED_MAX
                        and self._has_los(player.x, player.y, dungeon)):
                    return True
            return False

        # (Fear / charm / confusion / blindness are handled near the top of
        # take_turn so every AI pattern honours them.)

        # --- Charge: arm a damage bonus if approaching player on a clean straight ---
        # Conditions: can_charge flag, distance 2-5, AND player is on a cardinal or
        # diagonal axis (dx == 0, dy == 0, or |dx| == |dy|). Sets _charge_ready;
        # the attack() method consumes it when the monster reaches the player.
        if self.can_charge and not self._charge_ready:
            dist = max(abs(self.x - player.x), abs(self.y - player.y))
            if 2 <= dist <= 5:
                dxp = player.x - self.x
                dyp = player.y - self.y
                if dxp == 0 or dyp == 0 or abs(dxp) == abs(dyp):
                    self._charge_ready = True

        # A pack hunts together (src/packs.py, data/packs.json).
        _pack = packs.pack_of(self.kind) if effective_pattern == 'aggressive' else None

        if self._adjacent_to(player):
            if effective_pattern != 'cowardly':
                # Its pack's trick beside the hero: a jackal darts back out,
                # a kobold backs off over a trap it lays.
                if _pack and packs.adjacent_turn(self, player, dungeon, all_monsters,
                                                 extra_occupied) == 'moved':
                    return False
                self._pounce_now()       # its first blow is its opener
            return True  # caller triggers the attack

        # A pack hunter: it spreads round the hero in the open, holds a
        # corridor's mouth or goes round, slings from range, darts in.
        if _pack:
            _pk = packs.hunt_turn(self, player, dungeon, all_monsters, extra_occupied)
            if _pk == 'attack':
                return True
            if _pk == 'held':
                return False
            if _pk == 'moved':
                return bool(self._adjacent_to(player) and self._pounce_now())

        # --- Standard movement ---
        if self._standard_move(player, dungeon, all_monsters, extra_occupied, effective_pattern):
            if effective_pattern != 'cowardly':
                self._pounce_now()
            return True  # reached player during double-move
        # A pounce: it closes and strikes in the same turn (its opener).
        if (effective_pattern != 'cowardly' and self._adjacent_to(player)
                and self._pounce_now()):
            return True

        return False

    def _spots_player(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """The one detection check for a monster that hunts the hero: True
        when it knows where he is and goes after him this turn, False when it
        has spent the turn on its own business or on looking for him.

        It used to be distance alone, 8 tiles through solid stone, and a
        monster that had noticed him once knew where he was for ever. Now it
        is sight, sound and the lore senses of data/senses.json, with a
        search when the trail goes cold (src/senses.py)."""
        import senses as _senses
        seen = _senses.notice(self, player, dungeon, all_monsters, extra_occupied)
        # A fight ends when it has lost the hero a while: its opener is
        # ready again (OPENER_RESET_TURNS).
        if seen:
            self._lost_turns = 0
        else:
            self._lost_turns = int(self.__dict__.get('_lost_turns', 0) or 0) + 1
            if self._lost_turns >= OPENER_RESET_TURNS:
                self._opened = False
                self._winding = False
        return seen

    def _opener_from_range(self, player, dungeon):
        """Its opener from a distance, this turn: None when it has none to
        use (no opener, already used, out of range or sight, a pounce), else
        True (it fires now: attack() takes the opener) or False (it spent
        the turn drawing a gaze, a voice or a breath up; the line is in
        _wind_up_message for the game to say)."""
        op = self.__dict__.get('opener')
        if not op or self.__dict__.get('_opened') or op['range'] < 2:
            return None
        dist = max(abs(self.x - player.x), abs(self.y - player.y))
        if dist > op['range'] or not self._has_los(player.x, player.y, dungeon):
            return None
        delivery = str(self._opener_attack.get('delivery', '') or '')
        if delivery in OPENER_WIND_UP and not self.__dict__.get('_winding'):
            self._winding = True
            his = pronouns(self)[2]
            line = op.get('wind_up') or OPENER_WIND_UP[delivery]
            self._wind_up_message = line.format(name=the_name(self), his=his)
            return False
        self._winding = False
        self._opened = True
        self._opener_now = self._opener_attack
        return True

    def _pounce_now(self) -> bool:
        """It has just closed to the hero (or stands beside him) with a
        pounce unused: arm it, so its blow this turn is the opener."""
        op = self.__dict__.get('opener')
        if not op or self.__dict__.get('_opened') or op['range'] != 1:
            return False
        self._opened = True
        self._opener_now = self._opener_attack
        return True

    def _standard_move(self, player, dungeon, all_monsters, extra_occupied, effective_pattern):
        """Standard movement logic used by aggressive/cowardly AI."""
        move_steps = 2 if self.speed >= 14 else 1
        # A hunter with no clear view of the hero (it has his scent, hears
        # him, feels his steps) follows a real path round the walls; one that
        # sees him charges straight in, and takes the path only when the
        # straight way is blocked.
        if (effective_pattern != 'cowardly'
                and not self.has_effect('confused') and not self.has_effect('blinded')):
            import senses as _senses
            if not _senses.clear_view(self.x, self.y, player.x, player.y, dungeon):
                for _step in range(move_steps):
                    if not _senses.step_toward(self, dungeon, (player.x, player.y),
                                               all_monsters, extra_occupied, player):
                        break
                    if move_steps > 1 and self._adjacent_to(player):
                        return _step == 0
                return False

        dx, dy = self._preferred_dir(player, effective_pattern)
        candidates = self._move_candidates(dx, dy)

        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        player_pos = (player.x, player.y)

        for _step in range(move_steps):
            moved = False
            for ddx, ddy in candidates:
                nx, ny = self.x + ddx, self.y + ddy
                if (nx, ny) in occupied or (nx, ny) == player_pos:
                    continue
                tile = dungeon.tiles[ny][nx] if dungeon.in_bounds(nx, ny) else 0
                from dungeon import DOOR
                if tile == DOOR:
                    dungeon.open_door(nx, ny)   # monsters open doors
                    # MK-03: the whole body must fit through, not only the
                    # anchor tile: Fafnir (2x2) stepped half into the wall.
                    # One that cannot leaves the door shut.
                    if not self._can_move_to(dungeon, nx, ny):
                        dungeon.tiles[ny][nx] = DOOR
                        continue
                    self.x, self.y = nx, ny
                    moved = True
                    break
                if self._can_move_to(dungeon, nx, ny):
                    self.x, self.y = nx, ny
                    moved = True
                    break
            if not moved:
                if _step == 0 and effective_pattern != 'cowardly':
                    # Something stands in the straight way (a pillar, a
                    # statue, another creature): go round it.
                    import senses as _senses
                    _senses.step_toward(self, dungeon, (player.x, player.y),
                                        all_monsters, extra_occupied, player)
                break
            # After first step of a double-move, check adjacency again
            if _step == 0 and move_steps > 1 and self._adjacent_to(player):
                return True
            # Recalculate direction for second step
            if _step == 0 and move_steps > 1:
                dx, dy = self._preferred_dir(player, effective_pattern)
                candidates = self._move_candidates(dx, dy)
                from geom import all_occupied_tiles
                occupied = all_occupied_tiles(all_monsters, exclude=self)
                if extra_occupied:
                    occupied |= extra_occupied

        return False

    def _wander(self, dungeon, all_monsters, extra_occupied, player):
        """Random wandering when the monster hasn't detected the player."""
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        occupied.add((player.x, player.y))
        dirs = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        random.shuffle(dirs)
        for ddx, ddy in dirs:
            nx, ny = self.x + ddx, self.y + ddy
            if (nx, ny) not in occupied and self._can_move_to(dungeon, nx, ny):
                self.x, self.y = nx, ny
                return

    def alert_nearby(self, all_monsters):
        """Wake up nearby allies. Default: same-kind within 5 tiles.
        alert_radius and alert_all_tag fields let warlord/horn-blower types alert
        all same-tag allies in a wider radius."""
        radius = getattr(self, 'alert_radius', 5)
        use_tags = getattr(self, 'alert_all_tag', False)
        my_tags = set(getattr(self, 'tags', []))
        for m in all_monsters:
            if m is self or not m.alive or m._alerted:
                continue
            if use_tags:
                if not (my_tags & set(getattr(m, 'tags', []))):
                    continue
            else:
                if m.kind != self.kind:
                    continue
            dist = abs(m.x - self.x) + abs(m.y - self.y)
            if dist <= radius:
                # Woken and called to the fight (src/senses.py rouse).
                import senses as _senses
                _senses.rouse(m, self.x, self.y)

    def _adjacent_to(self, player) -> bool:
        """True if the player is Chebyshev-1 adjacent to ANY tile of
        this monster's footprint (and not standing on the monster).
        For 1×1 monsters this is the classic 8-neighbour adjacency;
        for 2×2 monsters the player counts as adjacent if they're
        next to any of the 4 occupied tiles."""
        from geom import is_adjacent
        return is_adjacent(player.x, player.y, self)

    def _preferred_dir(self, player, effective_pattern: str) -> tuple[int, int]:
        # Confused or blinded monsters stumble randomly
        if self.has_effect('confused') or self.has_effect('blinded'):
            return random.choice([(0, -1), (0, 1), (-1, 0), (1, 0)])
        dx = 0 if self.x == player.x else (1 if player.x > self.x else -1)
        dy = 0 if self.y == player.y else (1 if player.y > self.y else -1)
        if effective_pattern == 'cowardly':
            dx, dy = -dx, -dy
        # Flanker: when an ally is already pressuring the player from one axis,
        # this monster prefers the perpendicular axis. Surrounds instead of
        # stacking on the same approach line.
        elif self.prefers_flank and (dx != 0 or dy != 0):
            # Are we still 2+ tiles from the player? Only flank during approach.
            if max(abs(self.x - player.x), abs(self.y - player.y)) >= 2:
                dx, dy = self._flanker_dir(player, dx, dy)
        return dx, dy

    def _flanker_dir(self, player, dx: int, dy: int) -> tuple[int, int]:
        """Rotate the approach direction 90° if another same-kind/tag ally
        is already approaching on the original axis."""
        my_tags = set(getattr(self, 'tags', []))
        # Vectors from a few same-faction monsters to player
        for m in getattr(self, '_cached_all_monsters', []) or []:
            if m is self or not getattr(m, 'alive', False):
                continue
            if m.kind != self.kind and not (my_tags & set(getattr(m, 'tags', []))):
                continue
            mdx = 0 if m.x == player.x else (1 if player.x > m.x else -1)
            mdy = 0 if m.y == player.y else (1 if player.y > m.y else -1)
            if (mdx, mdy) == (dx, dy):
                # Same approach line — rotate 90° (preserving axis sign as we can)
                if dx and dy:
                    return (dx, -dy)   # diagonal flip the y axis
                if dx:
                    return (0, 1 if random.random() < 0.5 else -1)
                if dy:
                    return (1 if random.random() < 0.5 else -1, 0)
        return dx, dy

    def _move_candidates(self, dx: int, dy: int) -> list[tuple[int, int]]:
        if self.ai_pattern == 'grid_bug':
            opts = []
            if dx:
                opts.append((dx, 0))
            if dy:
                opts.append((0, dy))
            random.shuffle(opts)
            return opts

        if dx and dy:
            return [(dx, dy), (dx, 0), (0, dy)]
        if dx:
            return [(dx, 0), (0, 1), (0, -1)]
        if dy:
            return [(0, dy), (1, 0), (-1, 0)]
        return []

    def _can_move_to(self, dungeon, nx: int, ny: int) -> bool:
        """Check if this monster can move to anchor position (nx, ny),
        including wall-phasing. For multi-tile monsters, ALL footprint
        tiles at the new position must be walkable — a 2×2 dragon
        can't step into a 1-tile gap."""
        fw, fh = self.footprint
        # A creature larger than one tile must find every tile it would cover
        # free of other creatures; only its corner tile was ever compared.
        _busy = getattr(self, '_turn_occupied', None) if (fw, fh) != (1, 1) else None
        # Validate every footprint tile at the proposed new position
        for dy in range(fh):
            for dx in range(fw):
                tx, ty = nx + dx, ny + dy
                if not dungeon.in_bounds(tx, ty):
                    return False
                if _busy and (tx, ty) in _busy:
                    return False
                if dungeon.is_walkable(tx, ty):
                    continue
                # Wall-phasing: Asterion can move through phasing walls.
                # (Asterion is 1×1, but we keep the check general.)
                if self.can_phase_walls:
                    from dungeon import WALL
                    phasing = getattr(dungeon, 'phasing_walls', set())
                    if (dungeon.tiles[ty][tx] == WALL
                            and (tx, ty) in phasing):
                        continue
                return False
        return True

    def _strike_a_brother(self, all_monsters) -> bool:
        """Quarrelsome and confused: strike a creature beside this one, its
        own kind first (Cadmus's stone among the Sown Men). True if it did.
        The game reports it through `_confused_hit`."""
        from geom import occupied_tiles as _ot
        near = []
        for m in all_monsters:
            if m is self or not getattr(m, 'alive', False) or getattr(m, 'is_allied', False):
                continue
            if any(max(abs(tx - self.x), abs(ty - self.y)) == 1 for tx, ty in _ot(m)):
                near.append(m)
        if not near or not self.attacks:
            return False
        kin = [m for m in near if m.kind == self.kind]
        victim = random.choice(kin or near)
        atk = random.choice(self.attacks)
        dmg = roll(atk.get('damage', '1d4'))
        victim.take_damage(dmg)
        self._confused_hit = (victim, dmg)
        return True

    def _stumble_random(self, dungeon, all_monsters, extra_occupied, player):
        """Move in a random direction (confused/blinded stumble).
        If stumble would bump another monster, attack it (friendly fire)."""
        dirs = [(0,-1),(0,1),(-1,0),(1,0)]
        random.shuffle(dirs)
        from geom import occupied_tiles as _ot
        occupied = {}
        for _m in all_monsters:
            if _m is not self and _m.alive:
                for _t in _ot(_m):
                    occupied[_t] = _m
        for ddx, ddy in dirs:
            nx, ny = self.x + ddx, self.y + ddy
            # Confused friendly fire: bump into another monster = attack it
            if (nx, ny) in occupied and self.has_effect('confused'):
                victim = occupied[(nx, ny)]
                if self.attacks:
                    atk = random.choice(self.attacks)
                    dmg = roll(atk.get('damage', '1d4'))
                    victim.take_damage(dmg)
                    self._confused_hit = (victim, dmg)  # main.py reads this for messages
                return
            if ((nx, ny) not in occupied and (nx, ny) != (player.x, player.y)
                    and self._can_move_to(dungeon, nx, ny)):
                self.x, self.y = nx, ny
                return

    # --- The stalking coward (ai_pattern 'stalker_coward') ---------------------

    def _stalker_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """The stalking coward's turn (data 'stalker': Old Nickel; Brandon,
        2026-11-17). True when he strikes the hero this turn.

        The FALSE FRIEND, until `_revealed` (Brandon: "he initially
        approaches the player and tells him he'll protect him and watch his
        back"): he comes up to the hero and keeps 'friend_keep' tiles off, a
        step back when the hero comes beside him (never more), and never
        strikes, cornered or not.

        The REVEAL, for good: a hero at rest (the wait key this turn:
        senses.TURN.rested) or held by one of his 'prey_on' statuses
        (asleep, paralysed, confused, stunned), that he sees or hears within
        'hears_prey' tiles (a sleeper's breath carries). He darts in at
        'dash_steps' steps a turn, still smiling, and drops the act only the
        moment he reaches him: his blow that same moment is the sneak attack
        (`_sneak_ready`, Monster._resolve_blow), sudden and vicious. Struck
        first, he drops it too, with no sneak attack. Until then the friend
        also helps where it is safe (_stalker_help): one stab at a wounded
        monster busy with the hero.

        Revealed (rules 1-5):
        1. He strikes only a hero beside him, and only when he cannot back
           away from him (a wall or a corner at his back).
        3. A hero at rest or helpless he darts in on again, and strikes him
           the turn he reaches him.
        4. A hero walking away he follows, 'keep' to keep + 'slack' tiles off.
        5. A hero coming at him he backs away from, toward his hoard.
        Out of sight 'lose_after' turns, he goes back to his hoard.

        `_stalk_event` says what the turn did, for the game's lines: 'dash',
        'creep' (the friend closing on a hero at rest, still smiling), 'prey'
        (the blow on a hero at rest), 'help' (the friend's stab), 'cornered',
        'backs', 'follows', 'home' or ''; `_stalk_reveal` ('prey' or
        'struck') that the act has just dropped."""
        s = self.stalker or {}
        import senses as _senses
        self._stalk_event = ''
        revealed = bool(self.__dict__.get('_revealed', False))
        if self.__dict__.get('_struck'):
            self._provoked = True                # he has been in a fight
            if not revealed:
                self._stalker_reveal('struck')   # struck first: the act drops
                revealed = True
        keep = int(s.get('keep', 3)) if revealed else int(s.get('friend_keep', 2))
        slack = int(s.get('slack', 1)) if revealed else 0
        lose_after = int(s.get('lose_after', 12))
        # He watches with his eyes, as every creature does (senses.sees: an
        # invisible hero, or one in the Boots of Elvenkind past half his
        # reach, is not seen; nor one a worn legend hides; bug bash WB-C05).
        hidden = _senses._hidden(self, player, dungeon)
        seen = not hidden and _senses.sees(self, player, dungeon)
        here = (player.x, player.y)
        dist = max(abs(self.x - player.x), abs(self.y - player.y))
        if seen:
            self._aware = True
            self._tracking = True
            self._stalk_lost = 0
            self._stalk_seen_at = here
        else:
            self._stalk_lost = int(self.__dict__.get('_stalk_lost', 0) or 0) + 1

        # 3. A hero at rest or helpless: he darts in. The friend, still
        # smiling, drops the act only the moment he reaches him, and strikes
        # that same moment (Brandon: "sudden and vicious, never slow").
        prey = '' if hidden else self._prey_of(player, s)
        if prey and (seen or dist <= int(s.get('hears_prey', 6))):
            self._stalk_prey = prey
            self._tracking = True
            if not self._adjacent_to(player):
                self._stalk_event = 'dash' if revealed else 'creep'
                for _ in range(max(1, int(s.get('dash_steps', 2)))):
                    if not _senses.step_toward(self, dungeon, here, all_monsters,
                                               extra_occupied, player):
                        break
                    if self._adjacent_to(player):
                        break
            if self._adjacent_to(player):
                if not revealed:
                    self._stalker_reveal('prey')
                    self._sneak_ready = True     # this blow: the sneak attack
                self._provoked = True
                self._stalk_event = 'prey'
                return True
            return False
        self._stalk_prey = ''
        self._sneak_ready = False                # he got up first: no sneak attack

        # The friend helps, where it is safe: a stab at a wounded monster
        # busy with the hero, and back again.
        if not revealed and seen and self._stalker_help(player, dungeon, all_monsters,
                                                        extra_occupied, s):
            return False

        # 1 and 5. Beside him: he backs off if he can; cornered, he strikes
        # (the friend never does: he steps back, or stays and smiles).
        if self._adjacent_to(player):
            if self._stalker_step_away(player, dungeon, all_monsters, extra_occupied):
                self._stalk_event = 'backs'
                return False
            if not revealed:
                return False
            self._provoked = True
            self._tracking = True
            self._stalk_event = 'cornered'
            return True

        if not seen:
            last = self.__dict__.get('_stalk_seen_at')
            if last is None or self._stalk_lost > lose_after:
                # Lost him for good (or never saw him): back to his hoard.
                self._tracking = False
                if self._stalker_go_home(player, dungeon, all_monsters, extra_occupied):
                    self._stalk_event = 'home'
                return False
            # Lost him a moment ago: to where he saw him last, no nearer than
            # he keeps.
            if max(abs(self.x - last[0]), abs(self.y - last[1])) > keep:
                if _senses.step_toward(self, dungeon, last, all_monsters, extra_occupied, player):
                    self._stalk_event = 'follows'
            return False

        # 5. Too close: he backs away (cornered, he holds and waits).
        if dist < keep:
            if self._stalker_step_away(player, dungeon, all_monsters, extra_occupied):
                self._stalk_event = 'backs'
            return False
        # 4. Too far: he follows (the friend comes up to the hero).
        if dist > keep + slack:
            if _senses.step_toward(self, dungeon, here, all_monsters, extra_occupied, player):
                self._stalk_event = 'follows'
        return False

    def _stalker_reveal(self, why: str) -> None:
        """The act drops, for good: 'prey' (the hero at rest or helpless) or
        'struck' (the hero struck him first). The game says the line."""
        self._revealed = True
        self._stalk_reveal = str(why)
        self._tracking = True

    def sneak_blow(self, dmg: int, player=None) -> int:
        """The sneak attack's damage: 'sneak_mult' times the blow (data
        'stalker'). No cap: it can kill (Brandon, 2026-11-17: "We're not
        running a charity here")."""
        s = self.stalker or {}
        return max(1, int(round(dmg * float(s.get('sneak_mult', 3.0)))))

    def _safe_to_stab(self, m, player, spec) -> bool:
        """Will the friend dare strike this monster? Only a hostile, ordinary
        one, at or under 'help_below' of its health, that will not be hitting
        him: busy with the hero (beside him) or held fast. Never one at full
        health, never one free to hit him back, never a story creature."""
        if m is self or not getattr(m, 'alive', False):
            return False
        if (getattr(m, 'is_allied', False) or getattr(m, 'is_escort', False)
                or getattr(m, '_npc_encounter_tag', None) or getattr(m, '_flavor_encounter_tag', None)
                or getattr(m, '_is_unicorn', False) or getattr(m, 'stationary', False)
                or m._is_named_foe() or getattr(m, 'ai_pattern', '') == 'stalker_coward'):
            return False
        if not m.__dict__.get('_aware') or getattr(m, '_unseen', False):
            return False                          # not in the hero's fight
        max_hp = max(1, int(getattr(m, 'max_hp', 1) or 1))
        if m.hp >= max_hp or m.hp > max_hp * float(spec.get('help_below', 0.5)):
            return False
        held = any(m.has_effect(e) for e in ('sleeping', 'paralyzed', 'stunned', 'frozen',
                                             'stuck_in_pit', 'impaled', 'immobilized'))
        return m._adjacent_to(player) or held or getattr(m, 'ai_pattern', '') == 'sessile'

    def _stalker_help(self, player, dungeon, all_monsters, extra_occupied, spec) -> bool:
        """The friend's stab (Brandon: "he attacks monsters too, during the
        friendly act, but only when it's SAFE"): a monster _safe_to_stab within
        his dart, at most once in 'help_gap' turns. He darts in, strikes it
        once with his first attack, and darts back a step. The game says the
        helper line and the blow (`_help_hit`: (victim, damage)). True if he
        struck."""
        import senses as _senses
        gap = int(spec.get('help_gap', 4))
        self._help_wait = int(self.__dict__.get('_help_wait', 0) or 0) - 1
        if self._help_wait > 0 or not self.attacks:
            return False
        steps = max(1, int(spec.get('dash_steps', 2)))
        near = [m for m in all_monsters or ()
                if max(abs(m.x - self.x), abs(m.y - self.y)) <= steps + 1
                and self._safe_to_stab(m, player, spec)]
        if not near:
            return False
        target = min(near, key=lambda m: (m.hp / max(1, m.max_hp),
                                          max(abs(m.x - self.x), abs(m.y - self.y))))
        used = 0
        while not target._adjacent_to(self) and used < steps:
            if not _senses.step_toward(self, dungeon, (target.x, target.y), all_monsters,
                                       extra_occupied, player):
                break
            used += 1
        if not target._adjacent_to(self):
            return False
        from dice import roll
        dmg = target.take_damage(roll(self.attacks[0].get('damage', '1d3')),
                                 self.attacks[0].get('type', 'physical'))
        self._help_hit = (target, dmg)
        self._help_wait = gap
        self._stalk_event = 'help'
        if used < steps:
            # (back a step from it, never onto the hero)
            self._stalker_step_away(target, dungeon, all_monsters,
                                    set(extra_occupied or ()) | {(player.x, player.y)})
        return True

    @staticmethod
    def _prey_of(player, spec) -> str:
        """The state that makes the hero his prey this turn, or ''. 'resting'
        is the wait key this turn (senses.TURN.rested); the others are the
        hero's statuses."""
        import senses as _senses
        for state in (spec or {}).get('prey_on') or ():
            if state == 'resting':
                if getattr(_senses.TURN, 'rested', False):
                    return 'resting'
            elif player.has_effect(state):
                return str(state)
        return ''

    def _hoard_tile(self):
        """The tile he keeps by his hoard: where he was set down, else the
        middle of his room, else None."""
        h = self.__dict__.get('_hoard')
        if h:
            return tuple(h)
        home = self.__dict__.get('_wary_home')
        if home:
            return ((home[0] + home[2]) // 2, (home[1] + home[3]) // 2)
        return None

    def _stalker_step_away(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """One step that takes him farther from the hero, the one nearest his
        hoard of those (a coward backs off toward his iron). A shut door is
        opened on the way. False when there is none: he is cornered."""
        from geom import all_occupied_tiles
        from dungeon import DOOR
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        now = max(abs(self.x - player.x), abs(self.y - player.y))
        hoard = self._hoard_tile()
        best, best_key = None, None
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                if not ddx and not ddy:
                    continue
                nx, ny = self.x + ddx, self.y + ddy
                if (nx, ny) in occupied or (nx, ny) == (player.x, player.y):
                    continue
                d = max(abs(nx - player.x), abs(ny - player.y))
                if d <= now:
                    continue
                door = dungeon.in_bounds(nx, ny) and dungeon.tiles[ny][nx] == DOOR
                if not door and not self._can_move_to(dungeon, nx, ny):
                    continue
                to_hoard = max(abs(nx - hoard[0]), abs(ny - hoard[1])) if hoard else 0
                key = (to_hoard, -d)
                if best_key is None or key < best_key:
                    best, best_key = (nx, ny), key
        if best is None:
            return False
        nx, ny = best
        if dungeon.tiles[ny][nx] == DOOR:
            dungeon.open_door(nx, ny)
            if not self._can_move_to(dungeon, nx, ny):
                dungeon.tiles[ny][nx] = DOOR
                return False
        self.x, self.y = best
        return True

    def _stalker_go_home(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """A step back toward his hoard. True if he moved."""
        hoard = self._hoard_tile()
        if hoard is None or (self.x, self.y) == hoard:
            return False
        import senses as _senses
        return _senses.step_toward(self, dungeon, hoard, all_monsters, extra_occupied, player)

    def _flee_from(self, player, dungeon, all_monsters, extra_occupied):
        """Move away from player (feared)."""
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        away_dx = 0 if self.x == player.x else (1 if self.x > player.x else -1)
        away_dy = 0 if self.y == player.y else (1 if self.y > player.y else -1)
        for ddx, ddy in [(away_dx, away_dy), (away_dx, 0), (0, away_dy),
                         (-away_dy, away_dx), (away_dy, -away_dx)]:
            if ddx == 0 and ddy == 0:
                continue
            nx, ny = self.x + ddx, self.y + ddy
            if ((nx, ny) not in occupied and (nx, ny) != (player.x, player.y)
                    and self._can_move_to(dungeon, nx, ny)):
                self.x, self.y = nx, ny
                return

    # --- Ranged AI -----------------------------------------------------------
    _RANGED_MAX = 6   # max shooting range (tiles)
    _RANGED_IDEAL = 4  # preferred distance to maintain

    def _has_los(self, px, py, dungeon) -> bool:
        return _line_of_sight(self.x, self.y, px, py, dungeon)

    def _has_clear_shot(self, px, py, dungeon, all_monsters) -> bool:
        """True if LOS is clear of walls AND no allied monster blocks the path."""
        if not _line_of_sight(self.x, self.y, px, py, dungeon):
            return False
        # Bresenham walk to check for monsters in the way
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        dx, dy = abs(px - self.x), abs(py - self.y)
        sx = 1 if px > self.x else -1
        sy = 1 if py > self.y else -1
        err = dx - dy
        cx, cy = self.x, self.y
        while True:
            if cx == px and cy == py:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy
            if (cx, cy) != (px, py) and (cx, cy) in occupied:
                return False
        return True

    def _monsters_in_path(self, px, py, all_monsters) -> list:
        """Return monsters standing on tiles between self and (px, py)."""
        from geom import occupied_tiles as _ot
        occupied = {}
        for m in all_monsters:
            if m is not self and m.alive:
                for _t in _ot(m):
                    occupied[_t] = m
        result = []
        dx, dy = abs(px - self.x), abs(py - self.y)
        sx = 1 if px > self.x else -1
        sy = 1 if py > self.y else -1
        err = dx - dy
        cx, cy = self.x, self.y
        while True:
            if cx == px and cy == py:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                cx += sx
            if e2 < dx:
                err += dx
                cy += sy
            if (cx, cy) != (px, py) and (cx, cy) in occupied:
                result.append(occupied[(cx, cy)])
        return result

    def _has_piercing_ranged(self) -> bool:
        """True if this monster has at least one piercing ranged attack
        (the module's _RANGED_WORDS)."""
        for a in self.attacks:
            if a.get('piercing') and any(w in a.get('name', '').lower() for w in _RANGED_WORDS):
                return True
        return False

    def _dragon_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Dragon AI: breathe while closing, then fight with tooth and claw.

        The plain `ranged` pattern stands off at 2 to 8 tiles and fires for
        ever, and backs away when the player comes close. For Fafnir that
        meant he never came to the pit, which is the whole of Sigurd's plan.

          * Adjacent: attack (attack() picks claw or bite, not the breath).
          * In sight, 2 to DRAGON_BREATH_RANGE tiles, breath recharged, and
            the player is NOT down a pit: breathe. The breath then needs
            DRAGON_BREATH_RECHARGE turns, during which he advances.
          * Otherwise advance. A player crouched in a pit is out of the
            breath's path, so he does not waste it: he comes on.
        """
        self._piercing_collateral = []
        cd = int(getattr(self, '_breath_cd', 0) or 0)
        if cd > 0:
            self._breath_cd = cd - 1
        if self._adjacent_to(player):
            return True
        dist = max(abs(self.x - player.x), abs(self.y - player.y))
        if (cd <= 0 and 2 <= dist <= DRAGON_BREATH_RANGE
                and not player.has_effect('in_pit')
                and self._has_los(player.x, player.y, dungeon)):
            self._breath_cd = DRAGON_BREATH_RECHARGE
            return True
        if self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive'):
            return True
        return self._adjacent_to(player)

    def _ranged_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Ranged AI: shoot when player is in LOS within range.
        If too close, try to back away. If too far or no LOS, approach."""
        self._piercing_collateral = []  # reset each turn
        # Draws Breath (src/breath.py): its only shot is a breath still being
        # drawn up, so it comes in with tooth and claw (it used to breathe
        # every turn it had a shot and back away from a hero who closed); a
        # creature with no blow of its own keeps its distance.
        if breath.drawing(self):
            if breath.has_close(self):
                if self._adjacent_to(player):
                    return True
                return self._standard_move(player, dungeon, all_monsters, extra_occupied,
                                           'aggressive')
            if self._adjacent_to(player):
                self._step_back(player, dungeon, all_monsters, extra_occupied)
            return False
        dist = max(abs(self.x - player.x), abs(self.y - player.y))  # Chebyshev
        has_los = self._has_los(player.x, player.y, dungeon)

        # In range with LOS — check for clear shot or piercing override
        if has_los and 2 <= dist <= self._RANGED_MAX:
            if self._has_clear_shot(player.x, player.y, dungeon, all_monsters):
                return True
            # Shot blocked by ally — piercing monsters fire anyway
            if self._has_piercing_ranged():
                self._piercing_collateral = self._monsters_in_path(
                    player.x, player.y, all_monsters)
                self._force_piercing = True
                return True
            # No piercing — try to reposition
            has_los = False  # fall through to approach/reposition

        # Adjacent: an archer keeps its distance when it can (G5: this used
        # to be unreachable, so archers stood and clubbed you). Half the time
        # it steps back to a tile two away that still sees you, and shoots
        # on its next turn; cornered, it fights in melee.
        if self._adjacent_to(player):
            if random.random() < 0.5 and self._step_back(player, dungeon, all_monsters,
                                                          extra_occupied):
                return False
            return True

        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        player_pos = (player.x, player.y)

        # Too close (dist 1 and not adjacent shouldn't happen, but dist < 2 with LOS):
        # try to back away from the player
        if has_los and dist < 2:
            away_dx = 0 if self.x == player.x else (1 if self.x > player.x else -1)
            away_dy = 0 if self.y == player.y else (1 if self.y > player.y else -1)
            for ddx, ddy in [(away_dx, away_dy), (away_dx, 0), (0, away_dy),
                             (-away_dx, away_dy), (away_dx, -away_dy)]:
                nx, ny = self.x + ddx, self.y + ddy
                if (ddx == 0 and ddy == 0):
                    continue
                if (nx, ny) not in occupied and (nx, ny) != player_pos and self._can_move_to(dungeon, nx, ny):
                    self.x, self.y = nx, ny
                    # After retreating, check if we can now shoot
                    new_dist = max(abs(self.x - player.x), abs(self.y - player.y))
                    if new_dist >= 2 and self._has_clear_shot(player.x, player.y, dungeon, all_monsters):
                        return True  # retreat + shoot
                    return False
            # Can't retreat — fight in melee
            return True if self._adjacent_to(player) else False

        # Out of range or no LOS — approach (same as aggressive)
        if self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive'):
            return True
        return False

    def _step_back(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Step to a free tile two from the hero that still has a clear shot
        at him. True if it moved."""
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        options = []
        for ddx in (-1, 0, 1):
            for ddy in (-1, 0, 1):
                if not ddx and not ddy:
                    continue
                nx, ny = self.x + ddx, self.y + ddy
                if (nx, ny) in occupied or (nx, ny) == (player.x, player.y):
                    continue
                if max(abs(nx - player.x), abs(ny - player.y)) < 2:
                    continue
                if not self._can_move_to(dungeon, nx, ny):
                    continue
                if not _line_of_sight(nx, ny, player.x, player.y, dungeon):
                    continue
                options.append((nx, ny))
        if not options:
            return False
        self.x, self.y = random.choice(options)
        return True

    def _hit_and_run_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Hit-and-run AI for Asterion: hunt, strike, vanish through walls, repeat.

        States:
          hunting   - move toward player aggressively (through phasing walls)
          retreating - flee through phasing walls after attacking (3 turns)
          hiding    - wait hidden in the walls (4-6 turns), then hunt again
        """
        self._hit_run_timer -= 1

        # Gone Again (src/gone_again.py, AI-1): one that cannot walk through
        # walls breaks off to cover, out of the hero's sight, and hides there
        # until he finds it or strikes it (it used to stand in plain sight).
        if self._hit_run_state == 'retreating' and gone_again.applies(self):
            if gone_again.retreat(self, player, dungeon, all_monsters, extra_occupied):
                return False
        if self._hit_run_state == 'hiding' and gone_again.applies(self):
            if gone_again.hiding_turn(self, player, dungeon):
                return self._adjacent_to(player)        # found: it fights
            if self._hit_run_timer <= 0:
                self._hit_run_state = 'hunting'
                self._hit_run_attacks = 0
                gone_again.end_dark(self)
            return False

        if self._hit_run_state == 'retreating':
            if self._hit_run_timer <= 0:
                self._hit_run_state = 'hiding'
                self._hit_run_timer = random.randint(4, 6)
            # Move away from player, prefer phasing walls for escape
            self._phase_move(player, dungeon, all_monsters, extra_occupied, away=True)
            return False

        if self._hit_run_state == 'hiding':
            if self._hit_run_timer <= 0:
                self._hit_run_state = 'hunting'
                self._hit_run_attacks = 0
            return False  # lurking in the walls

        # --- hunting state ---
        if self._adjacent_to(player):
            self._hit_run_attacks += 1
            # After 1-2 attacks, retreat through walls
            if self._hit_run_attacks >= random.randint(1, 2):
                self._hit_run_state = 'retreating'
                self._hit_run_timer = 3
            return True  # signal attack

        # A bull lowers his horns on a clean straight run (G7: Asterion's
        # charge was armed only in the plain path, so it waited for his rage).
        if self.can_charge and not self._charge_ready:
            _cd = max(abs(self.x - player.x), abs(self.y - player.y))
            _dxp, _dyp = player.x - self.x, player.y - self.y
            if 2 <= _cd <= 5 and (_dxp == 0 or _dyp == 0 or abs(_dxp) == abs(_dyp)):
                self._charge_ready = True

        # Move toward player (can phase through walls)
        self._phase_move(player, dungeon, all_monsters, extra_occupied, away=False)

        # Check if we reached adjacency after moving
        if self._adjacent_to(player):
            return True

        return False

    def _phase_move(self, player, dungeon, all_monsters, extra_occupied, away: bool):
        """Move through the labyrinth, phasing through walls if possible."""
        if away:
            dx = 0 if self.x == player.x else (-1 if player.x > self.x else 1)
            dy = 0 if self.y == player.y else (-1 if player.y > self.y else 1)
        else:
            dx = 0 if self.x == player.x else (1 if player.x > self.x else -1)
            dy = 0 if self.y == player.y else (1 if player.y > self.y else -1)

        candidates = self._move_candidates(dx, dy)
        # When retreating, also try random directions to find phasing walls
        if away:
            all_dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            random.shuffle(all_dirs)
            for d in all_dirs:
                if d not in candidates:
                    candidates.append(d)

        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        player_pos = (player.x, player.y)

        for ddx, ddy in candidates:
            nx, ny = self.x + ddx, self.y + ddy
            if (nx, ny) in occupied or (nx, ny) == player_pos:
                continue
            if self._can_move_to(dungeon, nx, ny):
                self.x, self.y = nx, ny
                return True
        return False


    def _fenrir_rage_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Fenrir rage AI: aggressive movement + escalating rage stacks.
        Every rage_interval turns, gains a rage stack with increasing damage/speed."""
        self._rage_message = ''
        # Rage builds only once the foe has noticed the player, and stops at
        # RAGE_STACK_CAP. It used to tick from the moment the floor was
        # entered with no ceiling: Fenrir had about nine stacks by the time
        # the player crossed his hall, and forty if they explored first.
        engaged = (getattr(self, '_aware', False) or self._alerted
                   or self._adjacent_to(player))
        if engaged:
            self._rage_turn_counter += 1

        if (engaged and self.rage_interval > 0
                and self._rage_turn_counter % self.rage_interval == 0
                and self.rage_stacks < RAGE_STACK_CAP):
            self.rage_stacks += 1
            if self.kind == 'fenrir_wolf':
                _RAGE_MSGS = [
                    "Fenrir's back rises toward the roof beams.",
                    "Fenrir's hackles lift. Frost cracks along his jaws.",
                    "Fenrir howls, and the floor answers.",
                    "Fenrir fills the hall. This is the wolf the gods were afraid of.",
                    "The wolf's shadow takes the last of the light.",
                ]
                idx = min(self.rage_stacks - 1, len(_RAGE_MSGS) - 1)
                self._rage_message = _RAGE_MSGS[idx]
            else:
                _own = getattr(self, 'rage_messages', None) or []
                if _own:
                    self._rage_message = _own[min(self.rage_stacks - 1, len(_own) - 1)]
                else:
                    self._rage_message = f"{the_name(self)} presses harder."

        if self._adjacent_to(player):
            self.alert_nearby(all_monsters)
            return True

        # At high rage (3+), Fenrir gets double movement speed
        effective_pattern = 'aggressive'
        old_speed = self.speed
        if self.rage_stacks >= 3:
            self.speed = max(self.speed, 14)  # ensures double-move
        result = self._standard_move(player, dungeon, all_monsters, extra_occupied, effective_pattern)
        self.speed = old_speed
        return result

    def reset_rage(self):
        """Reset Fenrir's rage (called by Gleipnir binding)."""
        self.rage_stacks = 0
        self._rage_turn_counter = 0

    def _abaddon_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Abaddon AI: aggressive movement + periodic locust swarm spawning.
        Sets _wants_locust_spawn flag for main.py to handle actual spawning."""
        self._wants_locust_spawn = False
        # Swarms come only once Abaddon has noticed the player (they used to
        # pile up, unseen and uncapped, from the moment floor 100 was entered).
        engaged = (getattr(self, '_aware', False) or self._alerted
                   or self._adjacent_to(player))
        if engaged:
            self._locust_turn_counter += 1

        if (engaged and self.locust_interval > 0
                and self._locust_turn_counter % self.locust_interval == 0):
            _live = sum(1 for m in all_monsters
                        if m.alive and getattr(m, 'kind', '') == 'abyssal_locust')
            if _live < LOCUST_CAP + int(getattr(self, 'locust_cap_bonus', 0) or 0):
                self._wants_locust_spawn = True

        if self._adjacent_to(player):
            self.alert_nearby(all_monsters)
            return True

        return self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive')

    def _seek_locust_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Angel AI: move toward nearest locust. Sets _annihilate_target if adjacent."""
        self._annihilate_target = None

        # Find nearest locust
        locusts = [m for m in all_monsters if m.alive and m.kind == 'abyssal_locust']
        if not locusts:
            return False  # nothing to seek

        # Check if already adjacent to a locust
        for loc in locusts:
            if abs(self.x - loc.x) <= 1 and abs(self.y - loc.y) <= 1:
                self._annihilate_target = loc
                return False  # no attack on player

        # Move toward nearest locust
        nearest = min(locusts, key=lambda m: abs(m.x - self.x) + abs(m.y - self.y))
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        occupied.add((player.x, player.y))

        dx = 1 if nearest.x > self.x else (-1 if nearest.x < self.x else 0)
        dy = 1 if nearest.y > self.y else (-1 if nearest.y < self.y else 0)
        candidates = self._move_candidates(dx, dy)

        for ddx, ddy in candidates:
            nx, ny = self.x + ddx, self.y + ddy
            if (nx, ny) in occupied:
                continue
            if dungeon.in_bounds(nx, ny) and self._can_move_to(dungeon, nx, ny):
                self.x, self.y = nx, ny
                # Check if now adjacent to a locust
                for loc in locusts:
                    if abs(self.x - loc.x) <= 1 and abs(self.y - loc.y) <= 1:
                        self._annihilate_target = loc
                break

        return False  # angels never attack the player

    def _fenrir_multi_attack(self, player, attack_limit: int = 0) -> tuple[int, str]:
        """Fire multiple attacks in one turn. Returns (total_dmg, combined_msg).

        attack_limit > 0: use only the first N attacks (for tiered bosses
        like Tiamat phase 1 / Asmodeus phase 1 — see the multi_attack_count
        JSON field). attack_limit == 0: use ALL attacks (Fenrir / Abaddon
        multi_attack_always).
        """
        total = 0
        parts = []
        extras: list[str] = []
        self._flurry_effect_done = False
        # Only what is ready: a breath still drawing waits, and the next
        # attack in its routine comes instead (src/breath.py).
        atks_to_fire = breath.flurry(self, self.attacks, attack_limit)
        for atk in atks_to_fire:
            if not self.alive or player.hp <= 0:
                break               # a blow turned back killed it, or the player is already down
            actual, m = self._resolve_blow(atk, player, in_flurry=True)
            low = m.lower()
            label = attack_noun(atk)
            tail = ''
            if actual > 0:
                total += actual
                parts.append(f"{label} {actual}")
                if 'drains your life force' in low:
                    tail = "Your life force drains away! (CON -1)"
                elif 'damage!' in m:
                    tail = m.split('damage!', 1)[1].strip()
            elif 'you slip' in low:
                parts.append("slipped")
            elif 'miss' in low:
                parts.append("miss")
            else:
                parts.append(f"{label} 0")
                tail = m            # turned aside by something worth saying
            if tail and tail not in extras:
                extras.append(tail)
        self._flurry_effect_done = False
        hit_str = ", ".join(parts)
        msg = f"{the_name(self)} attacks in a frenzy! [{hit_str}] ({total} total)"
        if extras:
            msg += " " + " ".join(extras)
        return total, msg

    # ------------------------------------------------------------------
    # New 2026 AI patterns: healer, summoner, mimic, phase_blink, charge
    # ------------------------------------------------------------------

    def _distance_attacks(self) -> list:
        """The attacks that reach from a distance: flagged `ranged` or named
        with a ranged word."""
        return [a for a in self.attacks
                if a.get('ranged') or any(w in a.get('name', '').lower() for w in _RANGED_WORDS)]

    def _healer_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Heal a badly hurt friend beside it instead of attacking: its own
        side only, the one fighting the hero first, then a rest before the
        next prayer (src/faction.py). Falls back to ranged_turn (if it has a
        distance attack) or standard aggressive movement otherwise."""
        self._heal_target = None
        self._heal_amount = 0
        target = faction.heal_choice(self, all_monsters, player, reach=1)
        if target is not None:
            faction.heal(self, target)
            return False  # no attack — used the turn to heal

        # Mending a friend needs no sight of the hero; going after him does.
        if not self._spots_player(player, dungeon, all_monsters, extra_occupied):
            return False

        # No wounded ally to heal — behave as ranged if possible, else aggressive.
        # C09: "possible" means it HAS a distance attack; a healer whose two
        # attacks are both melee used to club the player from 2-6 tiles.
        if len(self.attacks) > 1 and self._distance_attacks():
            return self._ranged_turn(player, dungeon, all_monsters, extra_occupied)
        if self._adjacent_to(player):
            return True
        return self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive')

    def _summoner_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Call its dead when it counts (src/summoning.py): its timer runs only
        while it hunts the hero; it calls with him in reach and sight and
        fewer than its live cap standing, after a one-turn chant a blow
        breaks. Game loop polls self._wants_summon and calls
        _spawn_summoner_minion() — the actual JSON lookup + placement happens
        caller-side, mirroring the existing Abaddon locust-spawn pattern."""
        self._wants_summon = False
        # It summons only once it has spotted the hero (this sets _aware;
        # nothing did for a summoner, so none ever summoned).
        if not self._spots_player(player, dungeon, all_monsters, extra_occupied):
            self.__dict__.pop('_chanting', None)     # lost him: the chant is let go
            return False
        if summoning.step(self, player, all_monsters, dungeon):
            return False                             # it chants, or its dead come
        # While not summoning, behave as ranged caster (or melee if no ranged)
        if len(self.attacks) > 1 and self._distance_attacks():
            return self._ranged_turn(player, dungeon, all_monsters, extra_occupied)
        if self._adjacent_to(player):
            return True
        return self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive')

    def _mimic_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Mimic AI: appear as terrain until player steps adjacent, then spring.
        On reveal, switch ai_pattern to aggressive permanently and flag a
        surprise crit for the first attack."""
        if self._adjacent_to(player):
            # Spring! Flag surprise so the next attack lands with a crit bonus.
            self._mimic_surprise = True
            self._aware = True
            self.ai_pattern = 'aggressive'
            return True  # attack now
        if self.__dict__.get('_given_away', False):
            # Already given away (a chest that turned out to be it): no
            # disguise left to keep, so it hunts like anything else.
            self.ai_pattern = 'aggressive'
            return self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive')
        # Still hidden — completely inert until player walks into range
        return False

    def _phase_blink_to_player(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Teleport to an empty walkable tile adjacent to the player.
        Returns True if teleport succeeded (caller treats as attack)."""
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        occupied.add((player.x, player.y))
        # Try adjacent tiles in shuffled order
        candidates = [(player.x + dx, player.y + dy)
                      for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                      if not (dx == 0 and dy == 0)]
        random.shuffle(candidates)
        for nx, ny in candidates:
            if (nx, ny) in occupied:
                continue
            if dungeon.in_bounds(nx, ny) and self._can_move_to(dungeon, nx, ny):
                self.x, self.y = nx, ny
                return True
        return False

    def _blink_to_standoff(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Blink to a free tile four from the hero with a clear shot at him."""
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        occupied.add((player.x, player.y))
        if max(abs(self.x - player.x), abs(self.y - player.y)) == 4:
            return False
        spots = [(player.x + dx, player.y + dy) for dx in range(-4, 5) for dy in range(-4, 5)
                 if max(abs(dx), abs(dy)) == 4]
        random.shuffle(spots)
        for nx, ny in spots:
            if ((nx, ny) not in occupied and dungeon.in_bounds(nx, ny)
                    and self._can_move_to(dungeon, nx, ny)
                    and _line_of_sight(nx, ny, player.x, player.y, dungeon)):
                self.x, self.y = nx, ny
                return True
        return False

    def _share_gaze_cooldown(self) -> None:
        """This monster has just used its gaze: put every other living gazer of
        its `gaze_group` on the cooldown too. One shared gaze between them, so
        two of them never paralyse the player in the same turn."""
        if not self.gaze_group:
            return
        for m in getattr(self, '_cached_all_monsters', None) or ():
            if (m is not self and getattr(m, 'alive', False)
                    and getattr(m, 'gaze_group', '') == self.gaze_group):
                m._gaze_cooldown = max(int(getattr(m, '_gaze_cooldown', 0) or 0),
                                       self.gaze_cooldown_max)

    def _dancer_turn(self, player, dungeon, all_monsters, extra_occupied) -> bool:
        """Dancer AI (Medusa): sidestep to a new position adjacent to player, then attack.
        If not adjacent, approach normally. The constant repositioning makes her
        hard to pin down unless the player uses chokepoints. (Her gaze's
        cooldown is counted down in tick_effects, for every gazer.)"""
        px, py = player.x, player.y
        if not self._adjacent_to(player):
            # The gaze works across open floor: within GAZE_RANGE and with a
            # clear line of sight she looks instead of stepping. A pillar
            # between you breaks it. (The gaze used to fire only when she
            # was already adjacent, so the temple's pillars blocked nothing.)
            if (self.gaze_paralyze > 0 and self._gaze_cooldown <= 0
                    and max(abs(self.x - px), abs(self.y - py)) <= GAZE_RANGE
                    and self._has_los(px, py, dungeon)):
                return True     # attack() resolves the gaze
            self._standard_move(player, dungeon, all_monsters, extra_occupied, 'aggressive')
            return False

        # Adjacent: reposition to a different adjacent-to-player tile, then attack
        from geom import all_occupied_tiles
        occupied = all_occupied_tiles(all_monsters, exclude=self)
        if extra_occupied:
            occupied |= extra_occupied
        occupied.add((px, py))

        candidates = []
        for ddx in [-1, 0, 1]:
            for ddy in [-1, 0, 1]:
                if ddx == 0 and ddy == 0:
                    continue
                nx, ny = px + ddx, py + ddy
                if (nx, ny) == (self.x, self.y):
                    continue
                if (nx, ny) not in occupied and dungeon.is_walkable(nx, ny):
                    candidates.append((nx, ny))

        if candidates:
            self.x, self.y = random.choice(candidates)

        return True  # signal attack


class DeathMonster(Monster):
    """The Grim Reaper -- invincible pursuer spawned when the player ascends from L100
    with the Philosopher's Stone.  Moves at half speed but always hits and deals
    heavy damage.  Cannot be killed, dispelled, or escaped -- only outrun."""

    _DEFN = {
        'id': 'death',
        'name': 'Death',
        'pronoun': 'he',
        'symbol': 'D',
        'color': [220, 220, 255],
        'ai_pattern': 'aggressive',
        'speed': 10,
        'hp': '1',          # irrelevant -- take_damage is overridden
        'attacks': [{'name': 'reap', 'damage': '2d12+15', 'type': 'physical'}],
        'thac0': -20,       # always hits
        'resistances': [],
        'weaknesses':  [],
        'treasure':    {'gold': [0, 0], 'item_chance': 0.0, 'item_tier': 1},
        'lore': '',
        'min_level': 100,
    }

    def __init__(self, x: int = 0, y: int = 0):
        super().__init__(self._DEFN, x, y)
        self.hp      = 9999
        self.max_hp  = 9999
        self._speed_pct = 50           # % chance to act each turn (50=half, 75, 100, 125)
        self._frozen_turns = 0         # prayer freeze countdown

    # Death cannot be harmed. Accept and discard the same kwargs as
    # Monster.take_damage (damage_type, ignore_resistance) so callers that
    # pass them through — spell/wand paths, chain-passive procs — don't
    # raise TypeError on Death.
    def take_damage(self, amount: int, damage_type: str = 'physical',
                    ignore_resistance: bool = False) -> int:
        return 0

    def is_dead(self) -> bool:
        return False

    # Effects don't stick to Death (no sleeping, paralysis, poison, etc.)
    def tick_effects(self):
        pass

    def add_effect(self, name: str, duration: int) -> int:
        return 0

    def hold(self, name: str, duration: int):
        # The chain specials apply through here. (They used to write the
        # status straight in, and with tick_effects a no-op a chain stun
        # would have held Death for good.)
        pass

    def take_turn(self, player, dungeon, all_monsters, extra_occupied=None) -> bool:
        """Speed-scaled movement. 50%=half, 100%=normal, 125%=faster than player."""
        # Backwards compat: old pickled DeathMonsters lack new fields
        if not hasattr(self, '_speed_pct'):
            self._speed_pct = 50
        if not hasattr(self, '_frozen_turns'):
            self._frozen_turns = 0
        # Prayer freeze: skip turn, decrement counter
        if self._frozen_turns > 0:
            self._frozen_turns -= 1
            return False
        # Speed check: roll against _speed_pct to decide if Death acts
        if self._speed_pct < 100:
            if random.randint(1, 100) > self._speed_pct:
                return False
        result = super().take_turn(player, dungeon, all_monsters, extra_occupied)
        # 125% speed: 25% chance of a bonus STEP. It closes distance; it is
        # never a second attack. (It could be: at the top of the dungeon a
        # fleeing player took a free scythe blow on a quarter of all turns,
        # which nobody can outlast over twenty-five floors.)
        if (self._speed_pct > 100 and self._frozen_turns == 0 and not result
                and not self._adjacent_to(player)):
            bonus_chance = self._speed_pct - 100
            if random.randint(1, 100) <= bonus_chance:
                super().take_turn(player, dungeon, all_monsters, extra_occupied)
        return result

    def attack(self, player) -> tuple[int, str]:
        """Death always hits -- no THAC0 roll needed. The scythe takes a
        share of the player's own health (floor_curve.DEATH_REAP_SHARE): the
        written 2d12+15 was nearly half of a 60-point health bar when it was
        set, and a scratch on the 450-point one a winner carries now."""
        from floor_curve import DEATH_REAP_SHARE
        dmg = max(roll(self._DEFN['attacks'][0]['damage']),
                  int(round(DEATH_REAP_SHARE * max(1, int(player.max_hp)))))
        actual = player.take_damage(dmg, 'physical')
        return actual, f"Death's scythe tears through you for {actual} damage!"
