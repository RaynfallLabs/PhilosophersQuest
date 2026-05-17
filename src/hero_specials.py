"""Hero-build specials: one active or passive ability per Secret Build.

DATA + RESOLVERS only. Wiring (V menu integration, passive hooks) lives in
the relevant mixins. All active specials use AI escalator_chain max_chain=5
with chain-tier-graded effects per the design spec.

Boss CC immunity: any special that applies a status effect (charm, fear,
confuse, paralyze, sleep, immobilize) checks `is_boss_or_huge(monster)`
and skips. Damage specials work on bosses but with 0.5x scaling.

Passives are stored on `player.hero_passives: set[str]` and checked at
hook sites in combat.py, player.py, game_menus.py, and main.py.
"""
from __future__ import annotations
import random


def is_boss_or_huge(monster) -> bool:
    """Standard boss-immunity check, mirroring game_magic.py."""
    if monster is None:
        return False
    return bool(getattr(monster, 'is_boss', False)) or getattr(monster, 'max_hp', 0) > 500


# ---------------------------------------------------------------------------
# Active specials — chain-escalator AI quiz with tier-graded effects
# ---------------------------------------------------------------------------
#
# Each entry shape:
#   id            unique power id (matches the V-menu pid dispatch)
#   name          display label
#   desc          short flavor line, shown in menu
#   cooldown      turns until reusable (~250-500 = once-per-floor)
#   effect        resolver key (see HERO_EFFECT_DISPATCH below)
#   boss_immune   True if status-application should skip bosses
#   tier_effects  dict mapping chain depth 0..5 to effect parameters
#                 (effect-specific shape; see resolver functions)

HERO_SPECIALS: dict[str, dict] = {
    # ----- Philosophers -----
    "aristotle of stagira": {
        'id': 'hero_aristotles_catalogue',
        'name': "Aristotle's Catalogue",
        'desc': 'Identify a number of unidentified items in your pack (chain-scaled).',
        'cooldown': 400,
        'effect': 'identify_n',
        'tier_effects': {0: 0, 1: 1, 2: 2, 3: 3, 4: 5, 5: 999},
    },
    "socrates of athens": {
        'id': 'hero_maieutic_question',
        'name': 'Maieutic Question',
        'desc': 'Confuse visible humanoids; bosses untouched.',
        'cooldown': 300,
        'effect': 'confuse_visible',
        'boss_immune': True,
        'tier_effects': {
            0: {'count': 0, 'duration': 0, 'slow_too': False},
            1: {'count': 1, 'duration': 3, 'slow_too': False},
            2: {'count': 1, 'duration': 5, 'slow_too': False},
            3: {'count': 2, 'duration': 5, 'slow_too': False},
            4: {'count': 2, 'duration': 7, 'slow_too': False},
            5: {'count': 3, 'duration': 8, 'slow_too': True},
        },
    },
    "pythagoras of samos": {
        'id': 'hero_harmony_of_spheres',
        'name': 'Harmony of Spheres',
        'desc': 'Heal yourself by Nd6; deep chain cleanses debuffs.',
        'cooldown': 250,
        'effect': 'self_heal',
        'tier_effects': {
            0: {'dice': '0d0', 'cleanse': 0},
            1: {'dice': '1d6', 'cleanse': 0},
            2: {'dice': '2d6', 'cleanse': 0},
            3: {'dice': '3d6', 'cleanse': 0},
            4: {'dice': '4d6', 'cleanse': 1},
            5: {'dice': '5d6', 'cleanse': 2},
        },
    },
    "prometheus the firebearer": {
        'id': 'hero_liver_bound_fire',
        'name': 'Liver-Bound Fire',
        'desc': 'AoE fire burst around you. Costs 5 HP regardless.',
        'cooldown': 350,
        'effect': 'self_aoe_fire',
        'self_cost_hp': 5,
        'tier_effects': {
            0: {'radius': 0, 'dice': '0d0', 'burn_turns': 0},
            1: {'radius': 1, 'dice': '2d6', 'burn_turns': 0},
            2: {'radius': 1, 'dice': '3d6', 'burn_turns': 2},
            3: {'radius': 2, 'dice': '4d6', 'burn_turns': 2},
            4: {'radius': 2, 'dice': '5d6', 'burn_turns': 3},
            5: {'radius': 3, 'dice': '6d6', 'burn_turns': 4},
        },
    },
    # Plato, Nietzsche, Diogenes -> passives (see HERO_PASSIVES)

    # ----- Warriors -----
    # Achilles -> passive
    "leonidas of sparta": {
        'id': 'hero_spartan_stand',
        'name': 'Spartan Stand',
        'desc': 'Self AC buff + counter-strike chance for several turns.',
        'cooldown': 350,
        'effect': 'self_buff_stand',
        'tier_effects': {
            0: {'ac': 0, 'counter_pct': 0, 'duration': 0},
            1: {'ac': 2, 'counter_pct': 0, 'duration': 3},
            2: {'ac': 3, 'counter_pct': 0, 'duration': 5},
            3: {'ac': 3, 'counter_pct': 30, 'duration': 8},
            4: {'ac': 4, 'counter_pct': 50, 'duration': 10},
            5: {'ac': 5, 'counter_pct': 75, 'duration': 12},
        },
    },
    "alexander the great": {
        'id': 'hero_conquer_the_field',
        'name': 'Conquer the Field',
        'desc': 'Fear visible non-boss enemies; deep chain also immobilizes.',
        'cooldown': 400,
        'effect': 'fear_visible',
        'boss_immune': True,
        'tier_effects': {
            0: {'count': 0, 'duration': 0, 'immobilize_turns': 0},
            1: {'count': 1, 'duration': 2, 'immobilize_turns': 0},
            2: {'count': 2, 'duration': 3, 'immobilize_turns': 0},
            3: {'count': 3, 'duration': 4, 'immobilize_turns': 0},
            4: {'count': 99, 'duration': 5, 'immobilize_turns': 0},
            5: {'count': 99, 'duration': 7, 'immobilize_turns': 2},
        },
    },
    "theseus of athens": {
        'id': 'hero_labyrinth_sense',
        'name': 'Labyrinth Sense',
        'desc': 'Reveal traps, then walls, then everything (chain-scaled).',
        'cooldown': 500,
        'effect': 'reveal_floor',
        'tier_effects': {
            0: {'traps_near': False, 'full_map': False, 'all_traps': False,
                'stairs': False, 'items': False},
            1: {'traps_near': True,  'full_map': False, 'all_traps': False,
                'stairs': False, 'items': False},
            2: {'traps_near': True,  'full_map': True,  'all_traps': False,
                'stairs': False, 'items': False},
            3: {'traps_near': True,  'full_map': True,  'all_traps': True,
                'stairs': False, 'items': False},
            4: {'traps_near': True,  'full_map': True,  'all_traps': True,
                'stairs': True,  'items': False},
            5: {'traps_near': True,  'full_map': True,  'all_traps': True,
                'stairs': True,  'items': True},
        },
    },

    # ----- Rogues -----
    "hermes trismegistus": {
        'id': 'hero_hermetic_step',
        'name': 'Hermetic Step',
        'desc': 'Short-range teleport; deep chain extends range + grants haste.',
        'cooldown': 200,
        'effect': 'teleport_self',
        'tier_effects': {
            0: {'range': 0, 'haste': 0},
            1: {'range': 3, 'haste': 0},
            2: {'range': 5, 'haste': 0},
            3: {'range': 7, 'haste': 0},
            4: {'range': 99, 'haste': 0},
            5: {'range': 99, 'haste': 3},
        },
    },
    "odysseus of ithaca": {
        'id': 'hero_cunning_stratagem',
        'name': 'Cunning Stratagem',
        'desc': 'Charm visible non-boss monsters as temporary allies.',
        'cooldown': 400,
        'effect': 'charm_visible',
        'boss_immune': True,
        'tier_effects': {
            0: {'count': 0, 'duration': 0},
            1: {'count': 1, 'duration': 5},
            2: {'count': 1, 'duration': 10},
            3: {'count': 1, 'duration': 15},
            4: {'count': 2, 'duration': 10},
            5: {'count': 2, 'duration': 20},
        },
    },

    # ----- Mages -----
    "merlin ambrosius": {
        'id': 'hero_stardrop',
        'name': 'Stardrop',
        'desc': 'Falling-star single-target damage. Bosses take 0.5x.',
        'cooldown': 300,
        'effect': 'damage_single',
        'tier_effects': {
            0: {'dice': '0d0', 'range': 6},
            1: {'dice': '2d6', 'range': 6},
            2: {'dice': '4d6', 'range': 6},
            3: {'dice': '6d6', 'range': 6},
            4: {'dice': '8d6', 'range': 6},
            5: {'dice': '10d6', 'range': 6},
        },
    },

    # ----- Special / IP -----
    "ash williams": [
        {
            'id': 'hero_give_me_some_sugar',
            'name': 'Give Me Some Sugar',
            'desc': "Drain HP from an adjacent monster (must be... persuadable).",
            'cooldown': 300,
            'effect': 'drain_attractive',
            'tier_effects': {
                0: {'hp_drain': 0, 'charm_duration': 0},
                1: {'hp_drain': 5, 'charm_duration': 0},
                2: {'hp_drain': 10, 'charm_duration': 0},
                3: {'hp_drain': 15, 'charm_duration': 0},
                4: {'hp_drain': 25, 'charm_duration': 0},
                5: {'hp_drain': 40, 'charm_duration': 3},
            },
        },
        {
            'id': 'hero_she_bitch_lets_go',
            'name': "Yo, She-Bitch! Let's Go!",
            'desc': "Berserk fury for several turns; chain extends and deepens.",
            'cooldown': 350,
            'effect': 'self_buff_berserk',
            'tier_effects': {
                0: {'duration': 0, 'fear_immune': False, 'crit': False, 'str': 0},
                1: {'duration': 3, 'fear_immune': False, 'crit': False, 'str': 0},
                2: {'duration': 5, 'fear_immune': False, 'crit': False, 'str': 0},
                3: {'duration': 8, 'fear_immune': True, 'crit': False, 'str': 0},
                4: {'duration': 10, 'fear_immune': True, 'crit': True, 'str': 0},
                5: {'duration': 12, 'fear_immune': True, 'crit': True, 'str': 2},
            },
        },
        {
            'id': 'hero_this_is_my_boomstick',
            'name': "This... Is My BOOMSTICK!",
            'desc': "Materialise shotgun shells in your pack.",
            'cooldown': 400,
            'effect': 'gain_ammo',
            'ammo_id': 'shotgun_shell',
            'tier_effects': {
                0: {'count': 0, 'aoe_next': False},
                1: {'count': 5, 'aoe_next': False},
                2: {'count': 10, 'aoe_next': False},
                3: {'count': 15, 'aoe_next': False},
                4: {'count': 20, 'aoe_next': False},
                5: {'count': 30, 'aoe_next': True},
            },
        },
    ],
    "geralt of rivia": None,   # passive only — handled in HERO_PASSIVES
    "ciri riannon": None,
    "ash ketchum": {
        'id': 'hero_i_choose_you',
        'name': 'I Choose You!',
        'desc': 'Heal your active pet (chain-scaled).',
        'cooldown': 250,
        'effect': 'heal_pet',
        'tier_effects': {
            0: {'hp': 0, 'cleanse': False},
            1: {'hp': 10, 'cleanse': False},
            2: {'hp': 20, 'cleanse': False},
            3: {'hp': 35, 'cleanse': False},
            4: {'hp': 50, 'cleanse': False},
            5: {'hp': 99999, 'cleanse': True},
        },
    },
    # Dad: immortal flag, no special. Titivillus: qa_tools, no quiz special.

    # ----- New builds (Phase 3C) -----
    "ada augusta byron lovelace": {
        'id': 'hero_difference_engine',
        'name': 'Difference Engine',
        'desc': "Predict and disrupt: paralyse + slow a calculable foe.",
        'cooldown': 300,
        'effect': 'paralyze_target',
        'boss_immune': True,
        'tier_effects': {
            0: {'paralyze': 0, 'slow_too': 0},
            1: {'paralyze': 2, 'slow_too': 0},
            2: {'paralyze': 3, 'slow_too': 0},
            3: {'paralyze': 4, 'slow_too': 3},
            4: {'paralyze': 5, 'slow_too': 5},
            5: {'paralyze': 6, 'slow_too': 8},
        },
    },
    "leonardo di ser piero da vinci": {
        'id': 'hero_codex_sketch',
        'name': 'Codex Sketch',
        'desc': 'Sketch a mechanical helper to fight at your side (temporary).',
        'cooldown': 400,
        'effect': 'summon_sketch_helper',
        'tier_effects': {
            0: {'duration': 0, 'level': 0},
            1: {'duration': 15, 'level': 5},
            2: {'duration': 20, 'level': 10},
            3: {'duration': 25, 'level': 15},
            4: {'duration': 30, 'level': 25},
            5: {'duration': 40, 'level': 40},
        },
    },
    "boudicca queen of the iceni": None,   # passive
    "saint joan of arc maid of orleans": {
        'id': 'hero_standard_of_the_maid',
        'name': 'Standard of the Maid',
        'desc': "Rally: self-heal and crit-buff your next strike.",
        'cooldown': 350,
        'effect': 'heal_and_crit_buff',
        'tier_effects': {
            0: {'heal': 0, 'crit_turns': 0},
            1: {'heal': 8, 'crit_turns': 1},
            2: {'heal': 15, 'crit_turns': 2},
            3: {'heal': 25, 'crit_turns': 3},
            4: {'heal': 35, 'crit_turns': 4},
            5: {'heal': 50, 'crit_turns': 5},
        },
    },
    "sir arthur conan doyle's sherlock holmes": {
        'id': 'hero_deduction',
        'name': 'Deduction',
        'desc': 'Reveal traps + monster HP + identify items in a radius.',
        'cooldown': 400,
        'effect': 'reveal_radius',
        'tier_effects': {
            0: {'radius': 0, 'id_items': False},
            1: {'radius': 3, 'id_items': False},
            2: {'radius': 5, 'id_items': False},
            3: {'radius': 7, 'id_items': True},
            4: {'radius': 10, 'id_items': True},
            5: {'radius': 99, 'id_items': True},
        },
    },
    "miyamoto musashi the sword saint": None,   # passive dual-wield bonus
    "saint hildegard von bingen": {
        'id': 'hero_viriditas',
        'name': 'Viriditas',
        'desc': "Greenness — AoE heal + cleanse around you.",
        'cooldown': 350,
        'effect': 'aoe_heal_self',
        'tier_effects': {
            0: {'self_heal': 0, 'cleanse': 0},
            1: {'self_heal': 5, 'cleanse': 0},
            2: {'self_heal': 12, 'cleanse': 1},
            3: {'self_heal': 20, 'cleanse': 2},
            4: {'self_heal': 30, 'cleanse': 3},
            5: {'self_heal': 50, 'cleanse': 999},
        },
    },
    "nikola tesla the wizard of menlo park": None,   # passive shock counter
}


# ---------------------------------------------------------------------------
# Passive abilities — set on player.hero_passives, checked at hook sites
# ---------------------------------------------------------------------------

HERO_PASSIVES: dict[str, list[str]] = {
    "plato of athens":             ['plato_no_shard'],
    "friedrich nietzsche":         ['will_to_power'],
    "diogenes of sinope":          ['cynic_detachment'],
    "achilles son of peleus":      ['demigod_hide_25'],
    "geralt of rivia":             ['witcher_mutations', 'witcher_resists'],
    "ciri riannon":                ['elder_blood_escape'],
    "boudicca queen of the iceni": ['vengeance_wakes'],
    "miyamoto musashi the sword saint": ['niten_ichi_ryu'],
    "nikola tesla the wizard of menlo park": ['resonant_frequency'],
}


# ---------------------------------------------------------------------------
# Journal entries — printed to chronicle on game start (per build)
# ---------------------------------------------------------------------------

HERO_JOURNAL: dict[str, str] = {
    "aristotle of stagira":
        "I am Aristotle, student of Plato and tutor of kings. The world is a "
        "catalogue waiting to be sorted; the dungeon is no different. With my "
        "amethyst ring and the Lantern of Diogenes I will categorise everything "
        "this place has to offer.",
    "socrates of athens":
        "Socrates of Athens — corrupter of youth, asker of questions. They poisoned "
        "me for impiety, but the dungeon does not know my name. I will question "
        "every guard until they confuse themselves to death.",
    "plato of athens":
        "Plato of Athens, philosopher-king-in-waiting. The forms are real; this "
        "dungeon is merely their shadow. I need no Shard to see the truth of "
        "an item — I see its idea.",
    "friedrich nietzsche":
        "I am Friedrich Nietzsche. God is dead, and the abyss before me is just "
        "a hole in the floor. When my blood runs low, my will runs higher.",
    "pythagoras of samos":
        "Pythagoras of Samos: number is the measure of all things. The world is "
        "tuned, and I can ring it. With the Quill of Aesop in my pocket, I'll "
        "find harmony even in this discord.",
    "prometheus the firebearer":
        "Prometheus, who stole the fire of the gods. The dungeon thinks itself "
        "dark; it has not yet met me. The torch in my hand is a promise, and the "
        "burning my own liver feels is the cost of every miracle.",
    "diogenes of sinope":
        "Diogenes the Cynic. I sleep in barrels, I bark at fools, and I need "
        "nothing. A cursed ring is still a ring; let the dungeon waste its "
        "curses on someone who cares.",
    "achilles son of peleus":
        "Achilles, son of Peleus, dipped in the river by my mother. My hide "
        "turns steel aside — except, perhaps, at the heel. My spear leads.",
    "leonidas of sparta":
        "Leonidas of Sparta. I lack the other 299; this hallway will have to "
        "narrow itself. Shield up, spear forward, stand.",
    "alexander the great":
        "I am Alexander, son of Philip, student of Aristotle. I have conquered "
        "from Macedon to the Indus. This dungeon is merely a Persia I have not "
        "yet seen — and its monsters have not yet learned to flee.",
    "theseus of athens":
        "Theseus of Athens, slayer of the Minotaur. I have done a labyrinth "
        "before. Ariadne is not here, but my Lyre is, and I remember the way "
        "a maze wants to be walked.",
    "hermes trismegistus":
        "Hermes Trismegistus — thrice-great, messenger, thief. I do not walk "
        "through a dungeon; I step around it. My sandals know shortcuts the "
        "stone has forgotten.",
    "odysseus of ithaca":
        "I am Odysseus, sacker of cities. The bow my Penelope wove cloth for "
        "is in my hand. The trick is never the strongest sword — it is the "
        "right word at the right moment, and a horse with a hollow belly.",
    "merlin ambrosius":
        "Merlin Ambrosius — half-incubus, fully magician. I trained Arthur "
        "before he was a king. The stars listen when I call them. The dungeon "
        "should worry.",
    "geralt of rivia":
        "Geralt of Rivia, witcher of the Wolf School. Mutated, augmented, "
        "preternaturally calm. Toss a coin to me; I'll do the rest.",
    "ciri riannon":
        "Cirilla Fiona Elen Riannon — Princess of Cintra, last of the Elder "
        "Blood. When the world closes around me I step sideways and arrive "
        "elsewhere, alive.",
    "ash williams":
        "Ash. S-Mart, housewares. Hail to the king, baby. Necronomicon's a "
        "real page-turner once you stop reading the words wrong.",
    "ash ketchum":
        "Ash Ketchum from Pallet Town. Going to be the very best, like no one "
        "ever was. The Trainer's Cap helps the pets level faster, and I never "
        "run out of friends.",
    "corwin":
        "Corwin the Ranger. The shortbow was a gift from Dad on my eleventh "
        "birthday. Charmander has been with me since the beginning. "  
	"Together, they make me brave.",
    "cain":
        "Cain the Hunter. My twin's bow is fine, but ash flexes farther than oak. "
        "I carry the same Stuffie because some traditions are worth keeping.",
    "fianna":
        "Fianna the Wizard, age Thirteen. I have a wand, a sketchbook, and a "
        "questionable plan. Magic missiles are the basis of a girl's education.",
    "fluffs":
        "Fluffs the Magnificent. Like Fianna but with a real spellbook. "
        "The dungeon should bow. (It will not.)",
    "robyn":
        "Robyn. Quiet feet, quick mind, quicker tongue. Sleep arrows for the rude "
        "and Rand's Heart against the worst day. We come back. We always come back.",
    "dad":
        "Dad has arrived. Everything will be fine.",
    "titivillus":
        "[QA] Titivillus the Scribe of Errors. Press Shift+I to toggle immortality, "
        "Shift+W to warp to any floor. Document well.",
    # New builds
    "ada augusta byron lovelace":
        "Ada Lovelace, Countess of Lovelace. The first programmer the world "
        "would name. Every monster's behaviour is a program; I can read it, "
        "and I can pause it.",
    "leonardo di ser piero da vinci":
        "Leonardo da Vinci, of the village of Vinci. Painter, anatomist, engineer. "
        "My codex is full of helpers I have not yet built. The dungeon will see "
        "a few of them.",
    "boudicca queen of the iceni":
        "Boudicca, Queen of the Iceni, scourged and crowned by Rome. When the "
        "blade falls on me I rise sharper. The dungeon has hurt the wrong woman.",
    "saint joan of arc maid of orleans":
        "Joan, of the village of Domrémy. The Voices told me to save France; "
        "I do not see why the dungeon should be exempt. My banner is white, and "
        "my faith is steel.",
    "sir arthur conan doyle's sherlock holmes":
        "Sherlock Holmes, of 221B Baker Street. The dungeon is a problem in "
        "want of attention. Every trap a fingerprint, every monster a chemical "
        "trace. Watson, the game is afoot.",
    "miyamoto musashi the sword saint":
        "Miyamoto Musashi, author of the Book of Five Rings. Two swords are "
        "better than one. Better still: see the duel before it begins.",
    "saint hildegard von bingen":
        "Hildegard of Bingen, abbess and visionary. Viriditas — the greening "
        "power of God — flows through everything that lives. I bring it down "
        "even here.",
    "nikola tesla the wizard of menlo park":
        "Nikola Tesla. I tuned the resonance of the earth; I split light at "
        "Colorado Springs. Whatever touches me, I touch back — with current.",
}


# ---------------------------------------------------------------------------
# Effect resolvers — invoked when the player triggers an active special.
# Each takes (game, special_dict, tier_data, chain) and applies the effect.
# Bosses (is_boss_or_huge) are skipped by status effects when boss_immune=True.
# ---------------------------------------------------------------------------

def resolve_active_special(game, special: dict, chain: int) -> None:
    """Dispatch a successful chain quiz to the right effect handler."""
    tier_effects = special.get('tier_effects', {})
    # Clamp chain to 0..5 and pick the tier-effect entry
    chain = max(0, min(5, int(chain)))
    tier = tier_effects.get(chain, tier_effects.get(0))
    if tier is None:
        return
    eff = special.get('effect', '')
    handler = _DISPATCH.get(eff)
    if handler is None:
        game.add_message(f"({eff} effect not yet implemented)", 'warning')
        return
    handler(game, special, tier, chain)


def _eff_identify_n(game, special, tier, chain):
    """Aristotle's Catalogue. tier is an int = how many items to identify."""
    n = int(tier) if isinstance(tier, int) else int(tier.get('count', 0))
    if n <= 0:
        game.add_message("Your mind is empty; nothing comes into focus.", 'info')
        return
    unknown = [i for i in game.player.inventory
               if hasattr(i, 'identified') and not i.identified]
    if not unknown:
        game.add_message("Everything in your pack is already known.", 'info')
        return
    random.shuffle(unknown)
    for it in unknown[:n]:
        it.identified = True
        it.id_level = 5
        it.buc_known = True
        game.player.known_item_ids.add(it.id)
        game.add_message(f"Catalogued: {it.name}.", 'success')


def _eff_confuse_visible(game, special, tier, chain):
    cnt = int(tier['count'])
    dur = int(tier['duration'])
    if cnt == 0:
        game.add_message("Your question rings hollow.", 'warning')
        return
    targets = [m for m in game.monsters if m.alive
               and (m.x, m.y) in game.visible
               and 'humanoid' in getattr(m, 'tags', [])
               and not is_boss_or_huge(m)]
    random.shuffle(targets)
    for m in targets[:cnt]:
        cur = m.status_effects.get('confused', 0)
        m.status_effects['confused'] = max(cur, dur)
        if tier.get('slow_too'):
            cur = m.status_effects.get('slowed', 0)
            m.status_effects['slowed'] = max(cur, dur)
        game.add_message(f"{m.name} questions everything it knows.", 'success')


def _eff_self_heal(game, special, tier, chain):
    from dice import roll
    dice = tier.get('dice', '0d0')
    cleanse_n = int(tier.get('cleanse', 0))
    if dice == '0d0':
        game.add_message("The music falters; nothing happens.", 'warning')
        return
    heal = roll(dice)
    game.player.restore_hp(heal) if hasattr(game.player, 'restore_hp') else None
    if not hasattr(game.player, 'restore_hp'):
        game.player.hp = min(game.player.max_hp, game.player.hp + heal)
    game.add_message(f"Harmony — you recover {heal} HP.", 'success')
    if cleanse_n > 0:
        from status_effects import DEBUFFS
        debuffs = [e for e in list(game.player.status_effects) if e in DEBUFFS]
        random.shuffle(debuffs)
        for d in debuffs[:cleanse_n]:
            game.player.status_effects.pop(d, None)
            game.add_message(f"  ...{d} clears from you.", 'success')


def _eff_self_aoe_fire(game, special, tier, chain):
    from dice import roll
    cost = int(special.get('self_cost_hp', 0))
    if cost > 0:
        game.player.hp -= cost
        game.add_message(f"Your liver burns: -{cost} HP.", 'warning')
    radius = int(tier.get('radius', 0))
    if radius == 0:
        game.add_message("The flame gutters.", 'warning')
        return
    dice = tier.get('dice', '0d0')
    burn = int(tier.get('burn_turns', 0))
    px, py = game.player.x, game.player.y
    hits = 0
    for m in list(game.monsters):
        if not m.alive:
            continue
        if max(abs(m.x - px), abs(m.y - py)) <= radius:
            dmg = roll(dice)
            if is_boss_or_huge(m):
                dmg = max(1, dmg // 2)
            m.take_damage(dmg)
            hits += 1
            if m.alive and burn and not is_boss_or_huge(m):
                cur = m.status_effects.get('burning', 0)
                m.status_effects['burning'] = max(cur, burn)
            if not m.alive:
                game._on_monster_killed(m)
    game.add_message(
        f"Stolen flame erupts! {hits} foe(s) caught.", 'success' if hits else 'info')


def _eff_self_buff_stand(game, special, tier, chain):
    """Leonidas. Apply a stand_ac (custom) effect for `duration` turns.
    Also stores counter_pct on the player's status_effects via a sentinel."""
    dur = int(tier.get('duration', 0))
    if dur == 0:
        game.add_message("You waver and step back.", 'warning')
        return
    ac_bonus = int(tier.get('ac', 0))
    counter_pct = int(tier.get('counter_pct', 0))
    # Reuse existing 'shielded' status (-2 AC) by stacking; plus our own marker
    game.player.status_effects['stand_ac'] = max(
        game.player.status_effects.get('stand_ac', 0), dur)
    game.player._stand_ac_bonus = ac_bonus
    game.player._stand_counter_pct = counter_pct
    game.add_message(
        f"Spartan Stand! AC -{ac_bonus} and {counter_pct}% counter, {dur} turns.",
        'success')


def _eff_fear_visible(game, special, tier, chain):
    cnt = int(tier['count'])
    dur = int(tier['duration'])
    immob = int(tier.get('immobilize_turns', 0))
    if cnt == 0:
        game.add_message("No one cowers.", 'warning')
        return
    targets = [m for m in game.monsters if m.alive
               and (m.x, m.y) in game.visible
               and not is_boss_or_huge(m)]
    random.shuffle(targets)
    for m in targets[:cnt]:
        cur = m.status_effects.get('feared', 0)
        m.status_effects['feared'] = max(cur, dur)
        if immob:
            cur = m.status_effects.get('immobilized', 0)
            m.status_effects['immobilized'] = max(cur, immob)
        game.add_message(f"{m.name} breaks before you.", 'success')


def _eff_reveal_floor(game, special, tier, chain):
    revealed = 0
    if tier.get('full_map'):
        for y in range(game.dungeon.height):
            for x in range(game.dungeon.width):
                if game.dungeon.is_walkable(x, y) or game.dungeon.is_door(x, y):
                    game.explored.add((x, y))
                    revealed += 1
    elif tier.get('traps_near'):
        for (tx, ty) in list(game.dungeon.traps):
            if max(abs(tx - game.player.x), abs(ty - game.player.y)) <= 8:
                game.dungeon.traps[(tx, ty)]['revealed'] = True
                revealed += 1
    if tier.get('all_traps'):
        for (tx, ty), trap in game.dungeon.traps.items():
            trap['revealed'] = True
    if tier.get('items'):
        for it in game.ground_items:
            if hasattr(it, 'identified'):
                it.identified = True
                game.player.known_item_ids.add(getattr(it, 'id', ''))
    game.add_message("The labyrinth opens to you.", 'success')


def _eff_teleport_self(game, special, tier, chain):
    rng = int(tier.get('range', 0))
    haste = int(tier.get('haste', 0))
    if rng <= 0:
        game.add_message("Your step falters; you go nowhere.", 'warning')
        return
    candidates = []
    for y in range(game.dungeon.height):
        for x in range(game.dungeon.width):
            if not game.dungeon.is_walkable(x, y):
                continue
            d = max(abs(x - game.player.x), abs(y - game.player.y))
            if d <= rng and (x, y) != (game.player.x, game.player.y):
                if not any(m.alive and m.x == x and m.y == y for m in game.monsters):
                    candidates.append((x, y))
    if candidates:
        x, y = random.choice(candidates)
        game.player.x, game.player.y = x, y
        game._refresh_fov()
        game.add_message("Hermes' step — the dungeon blinks past.", 'success')
        if haste:
            cur = game.player.status_effects.get('hasted', 0)
            game.player.status_effects['hasted'] = max(cur, haste)
    else:
        game.add_message("Nowhere to step.", 'warning')


def _eff_charm_visible(game, special, tier, chain):
    cnt = int(tier['count'])
    dur = int(tier['duration'])
    if cnt == 0:
        game.add_message("None are persuaded.", 'warning')
        return
    targets = [m for m in game.monsters if m.alive
               and (m.x, m.y) in game.visible
               and not is_boss_or_huge(m)]
    random.shuffle(targets)
    for m in targets[:cnt]:
        cur = m.status_effects.get('charmed', 0)
        m.status_effects['charmed'] = max(cur, dur)
        game.add_message(f"{m.name} turns to your side.", 'success')


def _eff_damage_single(game, special, tier, chain):
    from dice import roll
    dice = tier.get('dice', '0d0')
    if dice == '0d0':
        game.add_message("The star fizzles.", 'warning')
        return
    # Damage the cursor-target monster if any (player targets via cursor),
    # otherwise nearest visible enemy. For simplicity in v1, pick nearest visible.
    targets = [m for m in game.monsters if m.alive and (m.x, m.y) in game.visible]
    if not targets:
        game.add_message("No target in sight.", 'warning')
        return
    targets.sort(key=lambda m: max(abs(m.x - game.player.x), abs(m.y - game.player.y)))
    target = targets[0]
    dmg = roll(dice)
    if is_boss_or_huge(target):
        dmg = max(1, dmg // 2)
    target.take_damage(dmg)
    game.add_message(f"A star falls on {target.name} for {dmg} damage.", 'success')
    if not target.alive:
        game._on_monster_killed(target)


def _eff_drain_attractive(game, special, tier, chain):
    """Ash Williams: Give Me Some Sugar. Only works on monsters with
    `female_attractive` tag (nymph, lamia, succubus, dryad, harpy, banshee)."""
    hp_drain = int(tier['hp_drain'])
    charm_dur = int(tier['charm_duration'])
    if hp_drain <= 0:
        game.add_message("She isn't having it.", 'warning')
        return
    px, py = game.player.x, game.player.y
    adj = [m for m in game.monsters if m.alive
           and max(abs(m.x - px), abs(m.y - py)) <= 1
           and 'female_attractive' in getattr(m, 'tags', [])]
    if not adj:
        game.add_message("No suitably... persuadable... target nearby.", 'info')
        return
    target = adj[0]
    drained = min(hp_drain, target.hp)
    target.take_damage(drained)
    game.player.hp = min(game.player.max_hp, game.player.hp + drained)
    game.add_message(
        f"Ash drains {drained} HP from {target.name}. \"Groovy.\"", 'success')
    if charm_dur and target.alive and not is_boss_or_huge(target):
        cur = target.status_effects.get('charmed', 0)
        target.status_effects['charmed'] = max(cur, charm_dur)
    if not target.alive:
        game._on_monster_killed(target)


def _eff_self_buff_berserk(game, special, tier, chain):
    dur = int(tier['duration'])
    if dur == 0:
        game.add_message("You can't muster the rage.", 'warning')
        return
    cur = game.player.status_effects.get('berserk', 0)
    game.player.status_effects['berserk'] = max(cur, dur)
    if tier.get('fear_immune'):
        cur = game.player.status_effects.get('fear_immune', 0)
        game.player.status_effects['fear_immune'] = max(cur, dur)
    if tier.get('crit'):
        cur = game.player.status_effects.get('crit_buff', 0)
        game.player.status_effects['crit_buff'] = max(cur, dur)
    str_bonus = int(tier.get('str', 0))
    if str_bonus > 0:
        game.player.apply_stat_bonus('STR', str_bonus)
        # Auto-revert when buff expires would need an event hook; for now,
        # permanent +STR as the chain-5 reward (matches buff scaling).
    game.add_message(f"Ash roars: \"Le's GO!\" Berserk for {dur} turns.", 'success')


def _eff_gain_ammo(game, special, tier, chain):
    cnt = int(tier['count'])
    if cnt == 0:
        game.add_message("Click.", 'warning')
        return
    from items import load_items
    ammo_id = special.get('ammo_id', 'shotgun_shell')
    proto = next((i for i in load_items('ammo') if i.id == ammo_id), None)
    if proto is None:
        game.add_message(f"({ammo_id} not in ammo registry)", 'warning')
        return
    import copy
    stack = copy.copy(proto)
    stack.count = cnt
    game.player.add_to_inventory(stack)
    game.add_message(f"BOOM. {cnt} {ammo_id.replace('_', ' ')} shells appear.",
                     'success')
    if tier.get('aoe_next'):
        cur = game.player.status_effects.get('boomstick_aoe_next', 0)
        game.player.status_effects['boomstick_aoe_next'] = max(cur, 1)
        game.add_message("Your next shot will scatter.", 'success')


def _eff_heal_pet(game, special, tier, chain):
    pets = [p for p in getattr(game, 'pets', []) if p.alive]
    if not pets:
        game.add_message("No pet to heal.", 'warning')
        return
    pet = pets[0]   # first alive pet
    hp = int(tier['hp'])
    if hp == 0:
        game.add_message("The cry doesn't reach.", 'warning')
        return
    before = pet.hp
    pet.hp = min(pet.max_hp, pet.hp + hp)
    gained = pet.hp - before
    game.add_message(f"{pet.name} is healed! (+{gained} HP)", 'success')
    if tier.get('cleanse'):
        from status_effects import DEBUFFS
        debs = [e for e in list(pet.status_effects) if e in DEBUFFS]
        for d in debs:
            pet.status_effects.pop(d, None)
        if debs:
            game.add_message(f"  ...all debuffs cleared from {pet.name}.", 'success')


def _eff_paralyze_target(game, special, tier, chain):
    """Ada Lovelace's Difference Engine: paralyse + slow nearest non-boss."""
    par = int(tier['paralyze'])
    slow = int(tier['slow_too'])
    if par == 0:
        game.add_message("The calculation diverges.", 'warning')
        return
    targets = [m for m in game.monsters if m.alive
               and (m.x, m.y) in game.visible
               and not is_boss_or_huge(m)]
    if not targets:
        game.add_message("No tractable target.", 'warning')
        return
    targets.sort(key=lambda m: max(abs(m.x - game.player.x), abs(m.y - game.player.y)))
    target = targets[0]
    cur = target.status_effects.get('paralyzed', 0)
    target.status_effects['paralyzed'] = max(cur, par)
    if slow:
        cur = target.status_effects.get('slowed', 0)
        target.status_effects['slowed'] = max(cur, slow)
    game.add_message(f"{target.name} freezes in its loop.", 'success')


def _eff_summon_sketch_helper(game, special, tier, chain):
    """Leonardo's Codex Sketch: summon a sketched-pet helper (uses pet_system)."""
    dur = int(tier['duration'])
    lvl = int(tier['level'])
    if dur == 0:
        game.add_message("Your sketch is just lines.", 'warning')
        return
    # Use a mock 'monster' shape that SketchedPet can ingest
    class _Helper:
        kind = 'sketched_helper'
        name = "Mechanical Helper"
        symbol = 'h'
        min_level = lvl
        max_hp = 30 + lvl * 4
        attacks = [{'damage': '1d8+2'}]
    from pet_system import SketchedPet
    px, py = game.player.x, game.player.y
    pet = SketchedPet(_Helper(), px, py, dur)
    game.pets.append(pet)
    game.add_message(
        f"From the page leaps a Mechanical Helper! ({dur} turns)", 'success')


def _eff_heal_and_crit_buff(game, special, tier, chain):
    heal = int(tier['heal'])
    crit_turns = int(tier['crit_turns'])
    if heal == 0 and crit_turns == 0:
        game.add_message("The Voices are silent.", 'warning')
        return
    game.player.hp = min(game.player.max_hp, game.player.hp + heal)
    if crit_turns:
        cur = game.player.status_effects.get('crit_buff', 0)
        game.player.status_effects['crit_buff'] = max(cur, crit_turns)
    game.add_message(
        f"The Maid's Standard! +{heal} HP; next {crit_turns} hits will crit.",
        'success')


def _eff_reveal_radius(game, special, tier, chain):
    radius = int(tier['radius'])
    id_items = bool(tier.get('id_items'))
    if radius == 0:
        game.add_message("Insufficient data.", 'info')
        return
    px, py = game.player.x, game.player.y
    revealed_traps = 0
    for (tx, ty), trap in list(game.dungeon.traps.items()):
        if max(abs(tx - px), abs(ty - py)) <= radius and not trap.get('revealed'):
            trap['revealed'] = True
            revealed_traps += 1
    if id_items:
        for it in game.ground_items:
            if not hasattr(it, 'identified'):
                continue
            if max(abs(it.x - px), abs(it.y - py)) <= radius and not it.identified:
                it.identified = True
                it.id_level = 5
                game.player.known_item_ids.add(getattr(it, 'id', ''))
    game.add_message(
        f"Sherlock deduces. ({revealed_traps} traps revealed in radius {radius}).",
        'success')


def _eff_aoe_heal_self(game, special, tier, chain):
    """Hildegard Viriditas: self-heal + cleanse N debuffs."""
    heal = int(tier['self_heal'])
    cleanse_n = int(tier['cleanse'])
    if heal == 0 and cleanse_n == 0:
        game.add_message("The green light does not bloom.", 'warning')
        return
    if heal:
        game.player.hp = min(game.player.max_hp, game.player.hp + heal)
        game.add_message(f"Viriditas — green life. +{heal} HP.", 'success')
    if cleanse_n > 0:
        from status_effects import DEBUFFS
        debs = [e for e in list(game.player.status_effects) if e in DEBUFFS]
        random.shuffle(debs)
        for d in debs[:cleanse_n]:
            game.player.status_effects.pop(d, None)
            game.add_message(f"  ...{d} fades.", 'success')


_DISPATCH = {
    'identify_n':       _eff_identify_n,
    'confuse_visible':  _eff_confuse_visible,
    'self_heal':        _eff_self_heal,
    'self_aoe_fire':    _eff_self_aoe_fire,
    'self_buff_stand':  _eff_self_buff_stand,
    'fear_visible':     _eff_fear_visible,
    'reveal_floor':     _eff_reveal_floor,
    'teleport_self':    _eff_teleport_self,
    'charm_visible':    _eff_charm_visible,
    'damage_single':    _eff_damage_single,
    'drain_attractive': _eff_drain_attractive,
    'self_buff_berserk':_eff_self_buff_berserk,
    'gain_ammo':        _eff_gain_ammo,
    'heal_pet':         _eff_heal_pet,
    'paralyze_target':  _eff_paralyze_target,
    'summon_sketch_helper': _eff_summon_sketch_helper,
    'heal_and_crit_buff':   _eff_heal_and_crit_buff,
    'reveal_radius':    _eff_reveal_radius,
    'aoe_heal_self':    _eff_aoe_heal_self,
}


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_specials_for_build(build_name: str) -> list[dict]:
    """Return a list of active-special dicts for the build (may be empty).

    Ash Williams has 3; most heroes have 1 or 0. Result is always a list
    for uniform downstream handling.
    """
    sp = HERO_SPECIALS.get(build_name)
    if sp is None:
        return []
    if isinstance(sp, list):
        return [s for s in sp if isinstance(s, dict)]
    return [sp]


def get_passives_for_build(build_name: str) -> list[str]:
    return list(HERO_PASSIVES.get(build_name, []))


def get_journal_for_build(build_name: str) -> str:
    return HERO_JOURNAL.get(build_name, '') or ''
