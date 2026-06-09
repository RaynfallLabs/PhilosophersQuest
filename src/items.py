import copy
import json
import os
from paths import data_path

_DATA_DIR = data_path('data', 'items')

# Armor slot index map (matches Player.armor_slots order)
ARMOR_SLOTS = ['head', 'body', 'arms', 'hands', 'legs', 'feet', 'cloak', 'shirt']


# Identify-system helpers — pure functions used by both item identify
# (game_magic.py:_identify_unique_item) and corpse identify
# (main.py:_start_corpse_identify). Extracted here so they're trivially
# unit-testable and the rule lives in ONE place.

def identify_resume_params(previous_level: int) -> tuple[int, int]:
    """Return (start_tier, max_chain) for an identify quiz that resumes
    from the failed tier.

    Rule: the chain starts at one tier ABOVE the last tier the kid passed,
    and only spans the remaining tiers. previous_level=0 -> (1, 5) — a
    fresh full identify. previous_level=2 -> (3, 3) — only T3+T4+T5 needed
    for mastery. previous_level=4 -> (5, 1) — last tier, mastery on the line.

    Clamped so previous_level >= 5 (already mastered) yields (5, 1) rather
    than crashing the quiz engine.
    """
    prev = max(0, min(int(previous_level), 5))
    start_tier = min(prev + 1, 5)
    max_chain = max(5 - prev, 1)
    return start_tier, max_chain


def id_progress_marker(id_level: int) -> str:
    """Return the menu marker that appears next to a partially-identified
    item's name (e.g. "  (2/5)"). The menu only contains items with
    id_level < 5; 5 is filtered out elsewhere.
    """
    lvl = max(0, min(int(id_level or 0), 5))
    return f"  ({lvl}/5)"

# Per-slot enchantment caps (max enchant_bonus allowed)
ENCHANT_CAP = {
    'head': 2, 'body': 3, 'arms': 1, 'hands': 1,
    'legs': 1, 'feet': 1, 'cloak': 2, 'shirt': 1,
    'shield': 2, 'weapon': 5,
}
# Random spawn enchant is capped at +1 for armor/shield; scrolls can push to slot cap
SPAWN_ENCHANT_CAP_ARMOR = 1


def effective_enchant_cap(player, slot_name: str) -> int:
    """ENCHANT_CAP lookup that respects Panoply of Hephaestus (divine_smithing).

    Panoply raises the weapon cap by `divine_smithing` (1 by default). Engine
    wave 5: the panoply at AC 8 was numerically mythic but mechanically generic.
    The forge-god's cross-slot bonus is what makes it legendary.
    """
    cap = ENCHANT_CAP.get(slot_name, 1)
    if player is None:
        return cap
    try:
        from armor_procs import proc_value
        bonus = int(proc_value(player, 'divine_smithing') or 0)
        if bonus > 0 and slot_name == 'weapon':
            cap += bonus
    except ImportError:
        pass
    return cap


class Item:
    # Item types where identical instances (same id) merge into a stack
    _STACKABLE_CLASSES: tuple = ()   # filled in after subclass definitions

    def __init__(self, defn: dict):
        self.id         = defn['id']
        self.name       = defn['name']
        self.symbol     = defn['symbol']
        self.color      = tuple(defn['color'])
        self.weight     = float(defn.get('weight', 1.0))
        self.item_class = defn.get('item_class', 'unknown')
        self.min_level  = int(defn.get('min_level', 1))
        self.x: int = 0
        self.y: int = 0
        self.count: int = 1          # stack size; >1 only for stackable types
        # Identification & BUC -- defaults on ALL items so no subclass can be missing them.
        # NOTE: `identified` is a property (defined below) reading id_level >= 4,
        # so it is NOT set as an instance attribute. id_level is the source of truth.
        self.unidentified_name: str = defn.get('unidentified_name', defn['name'])
        self.buc: str           = defn.get('buc', 'uncursed')
        self.buc_known: bool    = defn.get('buc_known', False)
        self.lore: str          = defn.get('lore', '')
        self.set_id: str        = defn.get('set_id', '')
        self.set_name: str      = defn.get('set_name', '')
        # Granular identification level (0-5) for the escalator-chain identify on uniques.
        # 0 = nothing known; 1 = real name; 2 = + BUC aura; 3 = + stats; 4 = + lore; 5 = + mastery.
        # For non-unique items going through threshold-mode identify, this jumps 0 -> 5 on success.
        # Default matches the legacy `identified` JSON field: known items start at 5, unknown at 0.
        self.id_level: int      = int(defn.get('id_level', 5 if defn.get('identified', True) else 0))
        # Mastery blessing data for is_unique items. Shape: {'kind': str, 'value': int|float|str, 'desc': str}
        # Granted to the player on chain-5 identify; lives on player.unlocked_masteries by item_id.
        self.mastery_blessing: dict | None = defn.get('mastery_blessing', None)
        # Permanent saving-throw bonus while equipped (the gradient defense; the
        # total is capped in Player.save_bonus_for). Shape: {'cat': 'CON'|'WIS'|
        # 'DEX'|'all', 'amount': int}. Read dynamically off equipped gear.
        self.save_bonus: dict | None = defn.get('save_bonus', None)
        # Named/legendary marker. Routes identify to escalator-chain mode and controls spawn-pool filtering.
        # Lives on base Item so accessories/wands/scrolls/spellbooks/etc. can mark uniques in JSON.
        self.is_unique: bool    = bool(defn.get('is_unique', False))
        # Bell-curve spawn fields — used by dungeon._item_eligible_weighted to
        # weight floor-relevance. peak_floor=0 means no bell weighting (fallback).
        self.peak_floor:  int   = int(defn.get('peak_floor', 0) or 0)
        self.spread:      int   = int(defn.get('spread', 10) or 10)
        self.peak_weight: float = float(defn.get('peak_weight', 0.0) or 0.0)

    # ------------------------------------------------------------------
    # Identified back-compat property (2026-05-29 bug-bash fix)
    # ------------------------------------------------------------------
    # Old code reads `item.identified` as a bool. The new model uses
    # `id_level: int` (0..5) as the source of truth. Treat `identified`
    # as True iff id_level >= 4 (lore tier reached).
    #
    # The setter is the critical part: many call sites write
    # `item.identified = True` and pre-2026-05-29 that was a no-op for
    # id_level — so the identify menu kept showing (0/5) even after a
    # scroll/wand identify revealed the name. Now the setter bumps
    # id_level to 4 minimum, keeping both representations in sync.
    #
    # Old pickled saves where `identified` was set as an instance
    # attribute (shadowing this property) are migrated on load — see
    # save_system.migrate_legacy_identified() / main.load_state.

    @property
    def identified(self) -> bool:
        return getattr(self, 'id_level', 0) >= 4

    @identified.setter
    def identified(self, value: bool) -> None:
        if value:
            self.id_level = max(getattr(self, 'id_level', 0), 4)
        else:
            self.id_level = 0


class Weapon(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        # New structured fields (camelCase keys from JSON, fallback to legacy snake_case)
        self.weapon_class: str          = defn.get('class', defn.get('weapon_class', 'sword'))
        self.variant: str               = defn.get('variant', '1h')
        self.tier: int                  = int(defn.get('tier', 1))
        self.material: str              = defn.get('material', 'iron')
        self.base_damage: int           = int(defn.get('baseDamage', defn.get('base_damage', 5)))
        # Legacy dice damage kept for backward compat; new weapons use base_damage
        self.damage: str | None         = defn.get('damage', None)
        self.chain_multipliers: list[float] = defn.get(
            'chainMultipliers', defn.get('chain_multipliers', [0.5, 1.0, 1.5, 2.0, 2.5])
        )
        self.quiz_tier: int             = int(defn.get('mathTier', defn.get('quiz_tier', 1)))
        self.damage_types: list[str]    = defn.get('damageTypes', defn.get('damage_types', ['slash']))
        self.two_handed: bool           = bool(defn.get('twoHanded', defn.get('two_handed', False)))
        self.reach: int                 = int(defn.get('reach', 1))
        self.stun_chance: float         = float(defn.get('stunChance', defn.get('stun_chance', 0.0)))
        self.bleed_chance: float        = float(defn.get('bleedChance', defn.get('bleed_chance', 0.0)))
        self.knockback: bool            = bool(defn.get('knockback', False))
        self.ignore_shield: bool        = bool(defn.get('ignoreShield', defn.get('ignore_shield', False)))
        self.crit_multiplier: float     = float(defn.get('critMultiplier', defn.get('crit_multiplier', 1.0)))
        self.requires_ammo: str | None  = defn.get('requiresAmmo', defn.get('requires_ammo', None))
        self.infinite_ammo: bool        = bool(defn.get('infiniteAmmo', defn.get('infinite_ammo', False)))
        self.floor_spawn_weight: dict   = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.container_loot_tier: str   = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.value: int                 = int(defn.get('value', 50))
        self.enchant_bonus: int         = int(defn.get('enchant_bonus', defn.get('enchantBonus', 0)))
        self.id_level: int = int(defn.get("id_level", 5 if defn.get("identified", False) else 0))
        self.unidentified_name: str     = defn.get('unidentified_name', 'an unknown weapon')
        # On-hit effect properties
        self.poison_chance: float       = float(defn.get('poisonChance', defn.get('poison_chance', 0.0)))
        self.burn_chance: float         = float(defn.get('burnChance', defn.get('burn_chance', 0.0)))
        self.confuse_chance: float      = float(defn.get('confuseChance', defn.get('confuse_chance', 0.0)))
        self.lifesteal_percent: float   = float(defn.get('lifestealPercent', defn.get('lifesteal_percent', 0.0)))
        self.cursed_miss_backlash: int  = int(defn.get('cursedMissBacklash', defn.get('cursed_miss_backlash', 0)))
        self.petrify_on_crit: bool      = bool(defn.get('petrifyOnCrit', defn.get('petrify_on_crit', False)))
        self.counter_attack_chance: float = float(defn.get('counterAttackChance', defn.get('counter_attack_chance', 0.0)))
        self.kill_heal_amount: int      = int(defn.get('killHealAmount', defn.get('kill_heal_amount', 0)))
        self.growing_power: bool        = bool(defn.get('growingPower', defn.get('growing_power', False)))
        self.kills_to_grow: int         = int(defn.get('killsToGrow', defn.get('kills_to_grow', 10)))
        self.on_equip_status: str       = defn.get('onEquipStatus', defn.get('on_equip_status', ''))
        self.can_dig: bool              = bool(defn.get('can_dig', False))
        self.ignore_resistances: bool   = bool(defn.get('ignore_resistances', False))
        self.abaddon_bonus_damage: str  = defn.get('abaddon_bonus_damage', '')
        # Sword of Michael: dramatic flavor line when smiting evil (combat.py).
        self.holy_smite_message: bool   = bool(defn.get('holy_smite_message', False))
        # Khopesh of Anubis: +max_hp on kill
        self.kill_max_hp_bonus: int     = int(defn.get('kill_max_hp_bonus', 0))
        self.kill_max_hp_cap: int       = int(defn.get('kill_max_hp_cap', 0))
        # Chandrahasa: bonus damage when player HP is low
        self.low_hp_damage_bonus: bool  = bool(defn.get('low_hp_damage_bonus', False))
        # Amenonuhoko: slow adjacent monsters on kill
        self.aoe_slow_on_kill: bool     = bool(defn.get('aoe_slow_on_kill', False))
        # Template+material class mechanic tag (cleave_on_kill, bleed_on_chain3, etc.)
        # — combat.py reads this to fire heavy-class effects at max chain / on kill.
        self.class_mechanic: str        = defn.get('class_mechanic', '')
        # True for named/legendary weapons; controls spawn pool filtering.
        self.is_unique: bool            = bool(defn.get('is_unique', False))
        # Green Chapel Axe: heal when hit by enemy
        self.on_hit_regen: int          = int(defn.get('on_hit_regen', 0))
        # Runtime-only tracking for growing power
        self.kill_count: int            = 0
        # Runtime: accumulated max_hp bonus from kill_max_hp_bonus
        self._max_hp_granted: int       = 0

        # ------------------------------------------------------------------
        # Engine wave 2026-05-30: previously-inert Weapon JSON flags.
        # Each of these was declared on unique-weapon entries in
        # data/items/weapon.json but had no code consumer in src/. The
        # unique-audit (proposals/legendary_uniques/weapons.md vs current
        # JSON, 2026-05-30) flagged ~30 weapons whose lore-promised
        # mechanics were dead on the floor. These additions wake them up.
        # ------------------------------------------------------------------

        # effects: {status, effect_chance, effect_duration} — on-hit status
        # delivery for quest-mythic weapons (vulcans_brand, wendigo_fang,
        # echidna_fang, hunt_captains_sword). Previously loaded ONLY on
        # Accessory; now Weapon too.
        self.effects: dict              = defn.get('effects', {}) or {}
        # Per-weapon effective_against array — lore-tagged anti-X bonus.
        # Previously only material.effective_against was read at use-site,
        # leaving 10+ weapons (Zulfiqar, Vel of Murugan, Spear of Longinus,
        # Mjolnir, Dawnbreaker, Gungnir, Fragarach, Skofnung, Gilgamesh's
        # Axe, Shamshir...) with dead anti-tag declarations.
        self.effective_against: list[str] = list(defn.get('effective_against', []) or [])
        # Per-tag bonus damage dice. Each entry rolls a dice expression and
        # adds the result to damage when the target has the matching tag.
        # Built from the legacy *_bonus_damage keys (which were inert except
        # for abaddon_bonus_damage — left as-is for Sword of Michael).
        self.bonus_damage_vs_tag: dict[str, str] = {}
        for _tag in ('dragon', 'beast', 'undead', 'goblin', 'demon', 'fey', 'giant', 'troll'):
            _dice = defn.get(f'{_tag}_bonus_damage')
            if _dice:
                self.bonus_damage_vs_tag[_tag] = str(_dice)
        # Anduril-style multiplier flag: undead_bonus (numeric mult).
        # Converted at use-site into +50% damage vs undead if set above 1.0.
        self.undead_multiplier: float   = float(defn.get('undead_bonus', 1.0) or 1.0)
        # Aiglos: freeze proc on hit.
        self.freeze_chance: float       = float(defn.get('freezeChance', defn.get('freeze_chance', 0.0)) or 0.0)
        # Atalanta's Bow: at chain 1 against a full-HP target, 1.5x damage.
        self.first_blood_bonus: bool    = bool(defn.get('first_blood_bonus', False))
        # Gungnir: never misses — chain 0 promotes to chain 1 (like
        # guaranteed_hit class_mechanic but driven by data, not template).
        self.cannot_miss: bool          = bool(defn.get('cannot_miss', False))
        # Aiglos: while equipped, wielder takes no fire damage. ("Sauron's
        # flame did nothing.")
        self.wielder_fire_immunity: bool = bool(defn.get('wielder_fire_immunity', False))
        # Glamdring: Foe-Hammer's orc/goblin glow. While equipped against a
        # goblin/orc-tagged enemy, +1 chain rung head start.
        self.glows_near_orcs: bool      = bool(defn.get('glows_near_orcs', False))
        # Hofud: Heimdall's vigilance. While equipped, wielder gains +2 PER.
        self.vigilance_aware: bool      = bool(defn.get('vigilance_aware', False))
        # Stormbringer: the runesword betrays at low HP. At HP <= 15%, a
        # successful hit has 25% chance to also "feed" by draining the
        # nearest adjacent ally (pet) for half the damage dealt to the monster.
        self.betrays_at_low_hp: bool    = bool(defn.get('betrays_at_low_hp', False))
        # Stormbringer: the runesword selects its wielder. While equipped,
        # cannot be unequipped (refuses, same shape as cursed gear). Per
        # weapons.md design — the weapon "chooses you."
        self.selects_wielder: bool      = bool(defn.get('selects_wielder', False))
        # Excalibur: cast_me_away — at HP <= 25%, one-shot drain weapon
        # enchant -1 and grant life_save. One use per run.
        self.cast_me_away: bool         = bool(defn.get('cast_me_away', False))
        # Pelops Sword: cursed_lineage — on equip, -1 STR + 2 max HP
        # (cumulative ledger entry, see Player._apply_weapon_passives).
        # Per-descent 5% chance of "House of Atreus" hostile NPC spawn.
        self.cursed_lineage: bool       = bool(defn.get('cursed_lineage', False))
        # Akinakes of Acrisius: prophecy_blade — at first equip, the blade
        # declares a random monster tag/class. That tag takes +50% damage
        # from the Akinakes for the rest of the run.
        self.prophecy_blade: bool       = bool(defn.get('prophecy_blade', False))

        # ------------------------------------------------------------------
        # Engine wave 3 (2026-05-30) — finishes wiring the rest of the
        # audit-deferred unique mechanics. Each was flagged "code missing"
        # in the unique-weapons audit. Twenty-two flags added at once. Tests
        # cover loading + the consumer-code presence checks per flag.
        # ------------------------------------------------------------------

        # Chrysaor: weapon_immune_to_enchant_loss — enchant_bonus does not
        # decrease from corrosion / rust monsters / unenchant scrolls.
        self.weapon_immune_to_enchant_loss: bool = bool(
            defn.get('weapon_immune_to_enchant_loss', False))
        # Aiglos and successors: wielder_status_immunity — list of debuff
        # statuses the player is immune to while this weapon is equipped.
        # Generalizes wielder_fire_immunity into a flexible vocabulary.
        self.wielder_status_immunity: list[str] = list(
            defn.get('wielder_status_immunity', []) or [])
        # Robin Hood's Longbow: +X% damage when player is invisible or
        # stealthed. Stored as a fractional multiplier (0.50 = +50%).
        self.stealth_damage_bonus: float = float(
            defn.get('stealth_damage_bonus', 0.0) or 0.0)
        # Fail-not: cannot_miss_before_player_takes_damage — chain 0
        # promotes to chain 1 ONLY while the player hasn't taken any
        # damage in the current combat. Tristan's dutiful arrows.
        self.cannot_miss_before_hurt: bool = bool(
            defn.get('cannot_miss_before_player_takes_damage', False))
        # Mistilteinn: damage_double_vs_resistant_at_max — at max chain,
        # double damage if the target has ANY resistance (the gap nobody
        # guards against).
        self.damage_double_vs_resistant_at_max: bool = bool(
            defn.get('damage_double_vs_resistant_at_max', False))
        # Gae Dearg: apply_heal_block_chance — chance per hit to apply
        # heal_blocked status to the target. Diarmuid's wound.
        self.apply_heal_block_chance: float = float(
            defn.get('apply_heal_block_chance', 0.0) or 0.0)
        # Hrunting: one_shot_chain_save_per_floor — chain 0 promotes to
        # the PREVIOUS rung ONCE per floor. "Never failed any man."
        self.one_shot_chain_save_per_floor: bool = bool(
            defn.get('one_shot_chain_save_per_floor', False))
        # Sword of Damocles: damoclean_counter_auto_kill — after N chains
        # without breaking, the NEXT chain-1 attack auto-kills a non-boss.
        # The threshold is configurable; default 10.
        self.damoclean_counter_threshold: int = int(
            defn.get('damoclean_counter_threshold',
                     10 if defn.get('damoclean_counter_auto_kill') else 0)
            or 0)
        # Sharur: floor_start_reveal_chance — chance per floor entry to
        # reveal a random tile near a stair-down. The talking-mace scout.
        self.floor_start_reveal_chance: float = float(
            defn.get('floor_start_reveal_chance', 0.0) or 0.0)
        # Kusanagi: surrounded_proc_bonus — auto-crit when 3+ enemies are
        # adjacent to the player.
        self.surrounded_proc_bonus: bool = bool(
            defn.get('surrounded_proc_bonus', False))
        # Parashu: chain_no_reset_on_tag — list of tags. Killing a target
        # whose tags match keeps the chain going (no reset). Parashurama
        # accumulating his penance.
        self.chain_no_reset_on_tag: list[str] = list(
            defn.get('chain_no_reset_on_tag', []) or [])
        # Harpe: skip_chain_warmup_vs_tag — list of tags. Against matching
        # targets, the chain starts at rung 2 instead of rung 1.
        self.skip_chain_warmup_vs_tag: list[str] = list(
            defn.get('skip_chain_warmup_vs_tag', []) or [])
        # Prometheus Torch: equipped_light_aura — bonus to sight radius
        # while equipped (in addition to PER's natural radius).
        self.equipped_light_aura: int = int(
            defn.get('equipped_light_aura', 0) or 0)
        # Cain's Club: equipped_monster_aggro_radius — beasts seek the
        # player from an additional N tiles' distance.
        self.equipped_monster_aggro_radius: int = int(
            defn.get('equipped_monster_aggro_radius', 0) or 0)
        # Penitent's Blade: kill_count_karma_adjust — every N kills, the
        # weapon adjusts player karma by +1 toward 0 (caps at 0 — the
        # blade can balance the ledger but not make a wicked man holy).
        self.kill_count_karma_adjust: int = int(
            defn.get('kill_count_karma_adjust', 0) or 0)
        # Joyeuse: combat_start_aoe_confuse_chance — chance per combat
        # for nearby enemies to be confused for 1 turn.
        self.combat_start_aoe_confuse_chance: float = float(
            defn.get('combat_start_aoe_confuse_chance', 0.0) or 0.0)
        # Zireael: extra_action_after_kill — once per turn, the player
        # gets a bonus move action after killing.
        self.extra_action_after_kill: bool = bool(
            defn.get('extra_action_after_kill', False))
        # Oathkeeper: adjacent_pet_damage_bonus — fractional multiplier
        # applied to attacks when the player has at least one pet within
        # 1 tile. Lore: the young man's promise.
        self.adjacent_pet_damage_bonus: float = float(
            defn.get('adjacent_pet_damage_bonus', 0.0) or 0.0)
        # Pharaoh's Crook: equipped_ally_aura_buff_str — pets within 5
        # tiles gain +N STR while the weapon is equipped.
        self.equipped_ally_aura_buff_str: int = int(
            defn.get('equipped_ally_aura_buff_str', 0) or 0)
        # Whisperer: equipped_sound_radius_modifier — fractional change to
        # the player's sound radius (-0.5 = halve sound, etc.).
        self.equipped_sound_radius_modifier: float = float(
            defn.get('equipped_sound_radius_modifier', 0.0) or 0.0)
        # Meleager's Boar-Spear: reveal_tag_on_chain_5_kill — list of
        # tags. On chain-5 kill of any matching target, reveal all
        # other tag-matching monsters within sight for 5 turns.
        self.reveal_tag_on_chain_5_kill: list[str] = list(
            defn.get('reveal_tag_on_chain_5_kill', []) or [])
        # Skofnung: chain_bonus_on_low_hp_window — +N chain rungs on the
        # next attack when player drops below 50% HP. One of the twelve
        # berserkers takes over.
        self.chain_bonus_on_low_hp_window: int = int(
            defn.get('chain_bonus_on_low_hp_window', 0) or 0)
        # Runtime state for damoclean counter + one-shot per-floor saves.
        self._damoclean_consecutive: int = 0
        # Runtime kill_count tally for karma_adjust.
        self._karma_kill_tally: int = 0

        # ------------------------------------------------------------------
        # Engine wave 4 (2026-05-30) — the rest of the "complex" mechanics
        # the audit had flagged. Each wired through to behavior — no more
        # "deferred / will revisit." Field load + consumer code in this
        # commit; tests in tests/test_engine_wave4_unique_mechanics.py.
        # ------------------------------------------------------------------

        # Mjolnir: chain_lightning_at_chain_n = {"from_chain": 6,
        # "splash_pct": 0.5, "max_targets": 1}. At chain >= from_chain,
        # splash damage to adjacent enemies of the primary target.
        self.chain_lightning_at_chain_n: dict = defn.get(
            'chain_lightning_at_chain_n', {}) or {}
        # Sudarshana: return_to_hand_ward = True. On chain-5 kill, sets
        # player._return_to_hand_active so the NEXT monster attack misses
        # outright. Refreshes per chain reset (any new combat).
        self.return_to_hand_ward: bool = bool(
            defn.get('return_to_hand_ward', False))
        # Laevateinn: boss_doom_dot_at_chain_5 = {"pct_max_hp_per_turn":
        # 0.05, "duration": -1}. At chain 5 hit on a boss-tagged target,
        # apply a doom_dot status that ticks N% max-HP per turn.
        self.boss_doom_dot_at_chain_5: dict = defn.get(
            'boss_doom_dot_at_chain_5', {}) or {}
        # Spear of Longinus: weep_heal_on_kill_scaled = 0.1 (1 HP per
        # 10 max-HP of slain target). Charlemagne's spear weeps and
        # heals the wielder.
        self.weep_heal_on_kill_scaled: float = float(
            defn.get('weep_heal_on_kill_scaled', 0.0) or 0.0)
        # Rod of Moses: chain_tier_status_table = {"3": {"status":
        # "slowed", "duration": 3}, "5": ...}. The Ten Plagues by chain
        # rung.
        self.chain_tier_status_table: dict = defn.get(
            'chain_tier_status_table', {}) or {}
        # Zulfiqar: every_hit_secondary_target = {"splash_pct": 0.5,
        # "range_tiles": 1}. Every hit also deals splash damage to one
        # adjacent enemy of the primary target.
        self.every_hit_secondary_target: dict = defn.get(
            'every_hit_secondary_target', {}) or {}
        # Gandiva: multi_arrow_at_chain_5 = {"targets": 3, "damage_per":
        # 0.5}. At chain 5 ranged hit, hit up to N other visible monsters.
        self.multi_arrow_at_chain_5: dict = defn.get(
            'multi_arrow_at_chain_5', {}) or {}
        # Soul Reaver: growth_on_innocent_kill = True. Killing a
        # non-hostile NPC marks the next hit for auto-crit.
        self.growth_on_innocent_kill: bool = bool(
            defn.get('growth_on_innocent_kill', False))
        # Chandrahasa: karma_disappear_proc = 0.05 (chance per floor
        # change when karma is negative). Vanishes back to Shiva.
        self.karma_disappear_proc: float = float(
            defn.get('karma_disappear_proc', 0.0) or 0.0)
        # Ruyi Jingu Bang: chain_modulated_reach = {"4": 4, "7": 5}.
        # At chain >= key, reach is at least value.
        self.chain_modulated_reach: dict = defn.get(
            'chain_modulated_reach', {}) or {}
        # Curtana: spare_kill_chance = 0.25, spare_kill_hp_per_floor =
        # 5. On hit that WOULD kill, chance to spare instead. The
        # monster survives at 1 HP and the player gains +1 max HP up
        # to the floor cap.
        self.spare_kill_chance: float = float(
            defn.get('spare_kill_chance', 0.0) or 0.0)
        self.spare_kill_max_hp_per_floor: int = int(
            defn.get('spare_kill_max_hp_per_floor', 5) or 5)
        # Spear of Lugh: damage_bonus_vs_gaze = 2.0. Vs any monster with
        # a gaze/petrification mechanic, multiply damage. Killed Balor
        # through the eye.
        self.damage_bonus_vs_gaze: float = float(
            defn.get('damage_bonus_vs_gaze', 0.0) or 0.0)
        # Echidna's Fang: random_status_from_pool = {"pool": [...],
        # "chance": 0.4, "duration": 5}. On hit, roll chance and apply
        # a random status from the pool.
        self.random_status_from_pool: dict = defn.get(
            'random_status_from_pool', {}) or {}
        # Cadmus / Vel / Shamshir: summon_after_kill_with_tag = {"tag":
        # "demon", "duration_turns": 5, "max_hp_pct": 0.5, "chance": 1.0}.
        # On kill of matching tag, spawn an ally pet of similar level.
        self.summon_after_kill_with_tag: dict = defn.get(
            'summon_after_kill_with_tag', {}) or {}
        # Runtime: counter of spared monsters this floor for Curtana cap.
        self._spare_kill_floor_hp: int = 0
        # Runtime: per-floor karma_disappear roll already done flag.
        self._karma_disappear_rolled_this_floor: bool = False

    @property
    def max_chain_length(self) -> int:
        """Always derived from chain_multipliers so old pickled weapons stay correct."""
        return len(self.chain_multipliers)

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Armor(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.slot                = defn['slot']
        self.tier: int           = int(defn.get('tier', 1))
        self.material: str       = defn.get('material', 'leather')
        self.ac_bonus: int       = int(defn['ac_bonus'])
        self.enchant_bonus: int  = int(defn.get('enchant_bonus', 0))
        self.equip_threshold     = int(defn.get('equip_threshold', 2))
        self.quiz_tier: int      = int(defn.get('quiz_tier', 1))
        self.damage_resistances: dict = defn.get('damage_resistances', {})
        self.can_be_cursed: bool = bool(defn.get('can_be_cursed', False))
        self.id_level: int = int(defn.get("id_level", 5 if defn.get("identified", False) else 0))
        self.unidentified_name: str = defn.get('unidentified_name', 'unknown armor')
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.on_equip_status: str    = defn.get('onEquipStatus', defn.get('on_equip_status', ''))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.pet_regen_bonus: int    = int(defn.get('pet_regen_bonus', 0))
        self.chain_bonus: int        = int(defn.get('chain_bonus', 0))
        # Coat of Cú Chulainn: berserk at low HP
        self.berserk_trigger: bool   = bool(defn.get('berserk_trigger', False))
        self.berserk_hp_threshold: float = float(defn.get('berserk_hp_threshold', 0.25))
        self.berserk_str_bonus: int  = int(defn.get('berserk_str_bonus', 0))
        self.berserk_duration: int   = int(defn.get('berserk_duration', 0))
        self.berserk_hp_cost: int    = int(defn.get('berserk_hp_cost', 0))
        # Babr-e Bayan: absorb first hit per floor
        self.first_hit_absorb: bool  = bool(defn.get('first_hit_absorb', False))
        # Tarnhelm: activated invisibility
        self.invisibility_power: bool = bool(defn.get('invisibility_power', False))
        self.invisibility_duration: int = int(defn.get('invisibility_duration', 0))
        self.invisibility_cooldown: int = int(defn.get('invisibility_cooldown', 0))
        # ------- Engine wave 5 (armor procs) -------
        # AB band (early floors)
        self.weave_and_unweave: bool = bool(defn.get('weave_and_unweave', False))     # Penelope
        self.phalanx_recovery: int   = int(defn.get('phalanx_recovery', 0) or 0)       # Linothorax
        self.water_tile_ac_bonus: int = int(defn.get('water_tile_ac_bonus', 0) or 0)   # Dilmun
        self.water_tile_regen_bonus: int = int(defn.get('water_tile_regen_bonus', 0) or 0)
        self.unskinnable: bool       = bool(defn.get('unskinnable', False))           # Nemean Lion / Hide
        self.prophets_passing: bool  = bool(defn.get('prophets_passing', False))      # Elijah mantle
        self.webbed_strike: bool     = bool(defn.get('webbed_strike', False))         # Arachne cloak
        self.forest_hearing: int     = int(defn.get('forest_hearing', 0) or 0)        # Erlking mantle
        self.story_thread: bool      = bool(defn.get('story_thread', False))          # Anansi cloak
        self.monkey_king_dodge: int  = int(defn.get('monkey_king_dodge', 0) or 0)     # Sun Wukong cloak
        self.grendel_grip: bool      = bool(defn.get('grendel_grip', False))          # Beowulf coif
        self.gold_offering: bool     = bool(defn.get('gold_offering', False))         # Gilgamesh helm
        self.bond_check: bool        = bool(defn.get('bond_check', False))            # Trainer's cap
        self.bovine_fury: bool       = bool(defn.get('bovine_fury', False))           # Cow King horns
        self.dodge_first_arrow_per_floor: bool = bool(defn.get('dodge_first_arrow_per_floor', False))
        self.quest_humility: bool    = bool(defn.get('quest_humility', False))        # Perseus sandals
        self.their_own_methods: float = float(defn.get('their_own_methods', 0.0) or 0.0)  # Theseus
        self.royal_burial: bool      = bool(defn.get('royal_burial', False))          # Pharaoh kilt
        self.riastrad_echo: bool     = bool(defn.get('riastrad_echo', False))         # Cu Chulainn bracers

        # CD band (mid floors)
        self.cannae_encirclement: bool = bool(defn.get('cannae_encirclement', False))  # Hannibal
        self.last_stand_bonus: bool  = bool(defn.get('last_stand_bonus', False))      # Leonidas
        self.et_tu_charge: bool      = bool(defn.get('et_tu_charge', False))          # Caesar lorica
        self.guerrilla_terrain: bool = bool(defn.get('guerrilla_terrain', False))     # Wallace
        self.disguise_at_camp: bool  = bool(defn.get('disguise_at_camp', False))      # Mulan
        self.boundary_guardian: bool = bool(defn.get('boundary_guardian', False))     # Mars gauntlets
        self.wild_friend: float      = float(defn.get('wild_friend', 0.0) or 0.0)     # Enkidu (pet HP mult)
        self.gita_focus: bool        = bool(defn.get('gita_focus', False))            # Arjuna bracers
        self.seven_league_step: bool = bool(defn.get('seven_league_step', False))     # Boots of Seven Leagues
        self.descend_stairs_no_turn: bool = bool(defn.get('descend_stairs_no_turn', False))  # Hermes greaves
        self.tremor_sense: int       = int(defn.get('tremor_sense', 0) or 0)          # Blindfold radius
        self.peace_at_the_forge: int = int(defn.get('peace_at_the_forge', 0) or 0)    # Achilles vambraces
        self.amazon_charge: bool     = bool(defn.get('amazon_charge', False))         # Hippolyta girdle

        # EF band (deep floors)
        self.caustic_blood: float    = float(defn.get('caustic_blood', 0.0) or 0.0)   # Hydra carapace
        self.divine_smithing: int    = int(defn.get('divine_smithing', 0) or 0)       # Hephaestus panoply
        self.maid_does_not_fall: bool = bool(defn.get('maid_does_not_fall', False))   # Joan breastplate
        self.atlantean_resonance: int = int(defn.get('atlantean_resonance', 0) or 0)  # Orichalcum
        self.descent_haste: int      = int(defn.get('descent_haste', 0) or 0)         # Yoshitsune
        self.ringing_intimidation: int = int(defn.get('ringing_intimidation', 0) or 0)  # Achilles helm
        self.purity: bool            = bool(defn.get('purity', False))                # Galahad helm
        self.thors_step: float       = float(defn.get('thors_step', 0.0) or 0.0)      # Thor boots

        # True for named/legendary armors; controls spawn pool filtering.
        self.is_unique: bool         = bool(defn.get('is_unique', False))
        # Chain-equip fields (legendary uniques only). When equip_chain_mode is set
        # to 'escalator' or 'chain', equipping triggers that quiz mode instead of
        # threshold. tier_bonuses maps chain-rung (1-5) -> bonus dict.
        self.equip_chain_mode: str   = defn.get('equip_chain_mode', '')
        self.equip_chain_subject: str = defn.get('equip_chain_subject', '')
        self.tier_bonuses: dict      = defn.get('tier_bonuses', {})
        self.achieved_tier: int      = 0   # runtime — set after equip quiz

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Shield(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.tier: int           = int(defn.get('tier', 1))
        self.material: str       = defn.get('material', 'wood')
        self.ac_bonus: int       = int(defn['ac_bonus'])
        self.enchant_bonus: int  = int(defn.get('enchant_bonus', 0))
        self.equip_threshold     = int(defn.get('equip_threshold', 2))
        self.quiz_tier: int      = int(defn.get('quiz_tier', 1))
        self.damage_resistances: dict = defn.get('damage_resistances', {})
        self.can_be_cursed: bool = bool(defn.get('can_be_cursed', False))
        self.id_level: int = int(defn.get("id_level", 5 if defn.get("identified", False) else 0))
        self.unidentified_name: str = defn.get('unidentified_name', 'an unknown shield')
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        # Svalinn: reflect fire damage back at attacker
        self.fire_reflect: float     = float(defn.get('fire_reflect', 0.0))
        # Ancile: bonus seconds on quiz timers
        self.quiz_timer_bonus: int   = int(defn.get('quiz_timer_bonus', 0))
        # True for named/legendary shields; controls spawn pool filtering.
        self.is_unique: bool         = bool(defn.get('is_unique', False))
        # Chain-equip fields (see Armor)
        self.equip_chain_mode: str   = defn.get('equip_chain_mode', '')
        self.equip_chain_subject: str = defn.get('equip_chain_subject', '')
        self.tier_bonuses: dict      = defn.get('tier_bonuses', {})
        self.achieved_tier: int      = 0

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Accessory(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.slot             = defn['slot']
        self.effects          = defn.get('effects', {})
        self.equip_threshold  = int(defn.get('equip_threshold', 2))
        self.quiz_tier        = int(defn.get('quiz_tier', 1))
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.id_level: int = int(defn.get("id_level", 5 if defn.get("identified", False) else 0))
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        # Artifact mechanics (defaults match the getattr fallbacks used in main.py)
        self.passive_regen: int          = int(defn.get('passive_regen', 0))           # Eye of Horus
        self.passive_regen_interval: int = int(defn.get('passive_regen_interval', 5))
        self.gold_multiplier: float      = float(defn.get('gold_multiplier', 0.0))     # Draupnir
        self.surrounded_ac_bonus: int    = int(defn.get('surrounded_ac_bonus', 0))     # Torc of Boudicca
        self.pacify_chance: float        = float(defn.get('pacify_chance', 0.0))       # Seal of Solomon
        self.death_save: bool            = bool(defn.get('death_save', False))         # Jade Cicada
        self.resurrect_on_death: bool    = bool(defn.get('resurrect_on_death', False)) # Ankh of Isis
        self.can_be_cursed: bool         = bool(defn.get('can_be_cursed', False))
        # ----- Engine wave 6: charge-based accessories (Lyre of Orpheus,
        # Hand of Glory). `use_charged: true` exposes the item in the power
        # menu when equipped; `charges` / `max_charges` track remaining uses.
        self.use_charged: bool       = bool(defn.get('use_charged', False))
        self.charges: int            = int(defn.get('charges', 0))
        self.max_charges: int        = int(defn.get('max_charges', self.charges or 0))
        # Hand of Glory: passive flags + paralyze duration + expended-curse.
        # Use-sites: player.get_sight_radius (dark vision), monster detection
        # (silent walk), game_menus._activate_accessory_charge (paralyze + curse).
        self.passive_dark_vision: bool = bool(defn.get('passive_dark_vision', False))
        self.passive_silent_walk: bool = bool(defn.get('passive_silent_walk', False))
        self.expended_curse: bool      = bool(defn.get('expended_curse', False))
        self.paralyze_duration: int    = int(defn.get('paralyze_duration', 4) or 4)
        # Brisingamen (tears_of_freya): passive gold drip — main._advance_turn hook.
        self.tears_of_freya: bool      = bool(defn.get('tears_of_freya', False))
        self.tears_of_freya_gold: int  = int(defn.get('tears_of_freya_gold', 1) or 1)
        self.tears_of_freya_interval: int = int(defn.get('tears_of_freya_interval', 1) or 1)
        # ----- Engine wave 6: small per-item procs (audit follow-up) -----
        self.identify_timer_bonus: int = int(defn.get('identify_timer_bonus', 0) or 0)  # ring_of_pythia
        self.auto_invisible_at_low_hp: bool = bool(defn.get('auto_invisible_at_low_hp', False))  # ring_of_eluned
        self.protected_when_surrounded: bool = bool(defn.get('protected_when_surrounded', False))  # ring_of_hypatia
        self.gyges_invisible_attack_karma: bool = bool(defn.get('gyges_invisible_attack_karma', False))  # ring_of_gyges
        self.monster_tag_chain_bonus: dict = defn.get('monster_tag_chain_bonus', {})  # dragonslayer_ring
        self.rotating_subject_chain_cap: list = defn.get('rotating_subject_chain_cap', [])  # Lugh, Hamsa
        # Chain-equip fields (legendary uniques only). When equip_chain_mode is set
        # to 'escalator' or 'chain', equipping triggers that quiz mode. Default
        # subject for accessories is 'history' if equip_chain_subject is empty.
        self.equip_chain_mode: str   = defn.get('equip_chain_mode', '')
        self.equip_chain_subject: str = defn.get('equip_chain_subject', '')
        self.tier_bonuses: dict      = defn.get('tier_bonuses', {})
        self.achieved_tier: int      = 0

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Wand(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        # charges_min/max used at spawn time to roll a semi-random starting count
        self.charges_min      = int(defn.get('charges_min', defn.get('charges', 3)))
        self.charges_max      = int(defn.get('charges_max', self.charges_min))
        self.charges          = self.charges_min          # re-rolled when placed in dungeon
        self.max_charges      = int(defn.get('max_charges', self.charges_max))
        # BUC: blessed wands hold one extra charge, cursed wands one fewer
        # (floor 1). Charges are re-rolled at dungeon placement from
        # charges_min/charges_max, so shift those bounds too.
        _wbuc = getattr(self, 'buc', 'uncursed')
        if _wbuc == 'blessed':
            self.charges_min += 1
            self.charges_max += 1
            self.charges     += 1
            self.max_charges += 1
        elif _wbuc == 'cursed':
            self.charges_min = max(1, self.charges_min - 1)
            self.charges_max = max(1, self.charges_max - 1)
            self.charges     = max(1, self.charges - 1)
            self.max_charges = max(1, self.max_charges - 1)
        self.quiz_tier        = int(defn.get('quiz_tier', 1))
        self.quiz_threshold   = int(defn.get('quiz_threshold', 2))
        self.effect           = defn.get('effect', '')
        self.power            = defn.get('power', '')
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.id_level: int = int(defn.get("id_level", 5 if defn.get("identified", False) else 0))
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Scroll(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.quiz_tier        = int(defn.get('quiz_tier', 1))
        self.quiz_threshold   = int(defn.get('quiz_threshold', 2))
        # Quiz mode: default 'threshold' (pass/fail). Set to 'escalator_chain'
        # to scale the scroll's effect by chain (e.g. Scroll of Heal).
        self.quiz_mode        = defn.get('quiz_mode', 'threshold')
        # max_chain only used when quiz_mode == 'escalator_chain'.
        self.max_chain        = int(defn.get('max_chain', 5))
        self.effect           = defn.get('effect', '')
        self.power            = defn.get('power', '')
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.id_level: int = int(defn.get("id_level", 5 if defn.get("identified", False) else 0))
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        # Spawn-once quest scrolls: survive a failed read so the secret-victory
        # path is not bricked by a single bad grammar quiz.
        self.single_copy: bool = bool(defn.get('single_copy', False))

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class Spellbook(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.spell_id          = defn.get('spell_id', '')
        self.spell_name        = defn.get('spell_name', self.name)
        self.mp_cost           = int(defn.get('mp_cost', 5))
        self.quiz_tier         = int(defn.get('quiz_tier', 1))
        self.quiz_threshold    = int(defn.get('quiz_threshold', 1))
        self.unidentified_name = defn.get('unidentified_name', defn['name'])
        self.id_level: int = int(defn.get("id_level", 5 if defn.get("identified", False) else 0))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.container_loot_tier: str = defn.get('containerLootTier', defn.get('container_loot_tier', 'common'))


class Artifact(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)


class Lockpick(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.max_durability          = int(defn.get('max_durability', 5))
        self.durability              = int(defn.get('durability', 5))
        self.durability_loss_success = int(defn.get('durability_loss_success', 1))
        self.durability_loss_failure = int(defn.get('durability_loss_failure', 2))
        self.identified: bool        = True
        self.unidentified_name: str  = defn.get('unidentified_name', self.name)


class Container(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.tier           = int(defn.get('tier', 1))
        self.quiz_tier      = int(defn.get('quiz_tier', defn.get('tier', 1)))
        # Legacy threshold field kept for back-compat; new chests use chain mode
        # and gate on `chain` (0-5). quiz_threshold is unused by the new flow.
        self.quiz_threshold = int(defn.get('quiz_threshold', 2))
        self.trapped        = bool(defn.get('trapped', False))
        self.trap           = defn.get('trap', None)   # dict or None
        self.gold           = defn.get('gold', defn.get('gold_range', [0, 0])) # [min, max]
        self.extra_item_chance = float(defn.get('extra_item_chance', 0.40))
        # New: template_id ties the container to a chest_templates.json entry.
        # Set by dungeon.pick_container() at spawn time. Empty string = legacy
        # container (no template); container_system falls back to legacy loot.
        self.template_id: str = defn.get('template_id', '')
        # Runtime state (not from JSON)
        self.trap_triggered = False
        self.opened         = False
        self.is_mimic       = False


class Ingredient(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.source_monster = defn.get('source_monster', '')
        # recipes: str(quality 0-5) -> {name, sp, bonus_type, bonus_amount}
        self.recipes: dict  = defn.get('recipes', {})
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.identified: bool       = True   # raw ingredients are obvious
        self.unidentified_name: str = defn.get('unidentified_name', self.name)
        self.mp_restore: int        = int(defn.get('mp_restore', 0))
        # tier_role: 'universal' | 'family' | 'prime' | 'trophy' | 'dungeon'.
        # Where the ingredient comes from: only 'dungeon' (terrain-foraged --
        # cave mushroom, swamp moss, river salt...) may appear as floor or chest
        # loot. Monster-derived tiers (family/prime/trophy) come ONLY from
        # harvesting corpses. Consumed by dungeon.spawn_items, container_system
        # loot pools, and food_system raw-SP scaling -- all of which used
        # getattr(.., 'tier_role') and silently got '' until this was loaded.
        self.tier_role: str         = defn.get('tier_role', 'universal')
        # Cooking-overhaul 2026-06-07: `edible_safe` ingredients (jerky) are eaten
        # raw with NO food-poison roll; `raw_sp` data-drives the SP they restore
        # (overriding the tier_role map in food_system.eat_raw). Both default off
        # so the change is harmless to old saves / unflagged ingredients.
        self.edible_safe: bool      = bool(defn.get('edible_safe', False))
        self.raw_sp                 = defn.get('raw_sp', None)


class Corpse(Item):
    def __init__(self, monster_name: str, monster_id: str, x: int, y: int,
                 harvest_tier: int = 1, harvest_threshold: int = 2,
                 ingredient_id: str | None = None,
                 lore: str = '', monster_def: dict | None = None):
        defn = {
            'id':         f'corpse_{monster_id}',
            'name':       f'{monster_name} corpse',
            'symbol':     '%',
            'color':      [160, 60, 60],
            'weight':     5.0,
            'item_class': 'corpse',
            'min_level':  1,
        }
        super().__init__(defn)
        self.monster_id        = monster_id
        self.monster_name      = monster_name
        self.harvest_tier      = harvest_tier
        self.harvest_threshold = harvest_threshold
        self.ingredient_id     = ingredient_id
        self.lore              = lore
        self.monster_def       = monster_def or {}   # full definition for stat display
        # Escalator-chain identify level (0..5):
        #   0 nothing, 1 name+symbol, 2 basic stats, 3 weak/resist/tags,
        #   4 full lore, 5 family mastery unlocked. lore_identified is a
        #   property reflecting id_level >= 4 (backward compat).
        self.id_level: int     = 0
        self.x = x
        self.y = y

    @property
    def lore_identified(self) -> bool:
        """True once id_level >= 4 (lore tier achieved). Back-compat shim."""
        return int(getattr(self, 'id_level', 0)) >= 4

    @lore_identified.setter
    def lore_identified(self, value: bool):
        """Legacy setter: True bumps id_level to >=4; False resets to 0."""
        if value:
            self.id_level = max(int(getattr(self, 'id_level', 0)), 4)
        else:
            self.id_level = 0

    def __setstate__(self, state):
        """Migrate old pickled corpses to the new id_level field.

        Old saves stored `lore_identified` as a plain instance attribute that
        would shadow the new property. Drop it from __dict__ and translate to
        id_level >= 4 if it was set.
        """
        legacy = bool(state.pop('lore_identified', False))
        if 'id_level' not in state:
            state['id_level'] = 4 if legacy else 0
        elif legacy and int(state.get('id_level', 0)) < 4:
            state['id_level'] = max(int(state['id_level']), 4)
        self.__dict__.update(state)


class Ammo(Item):
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.ammo_type:    str = defn.get('ammo_type', 'arrow')
        self.tier:         int = int(defn.get('tier', 1))
        self.damage_bonus: int = int(defn.get('damage_bonus', 0))
        self.count_min:    int = int(defn.get('count_min', 10))
        self.count_max:    int = int(defn.get('count_max', 20))
        self.count:        int = self.count_min   # set at spawn; base class also has count=1 default
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        self.value:        int = int(defn.get('value', 1))
        # Ammo is always visually obvious -- identified by default
        self.identified: bool       = True
        self.unidentified_name: str = defn.get('unidentified_name', self.name)


class Food(Item):
    """Ready-to-eat food item. Restores SP and optionally HP; may grant a stat bonus."""
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.sp_restore:  int  = int(defn.get('sp_restore', 20))
        self.hp_restore:  int  = int(defn.get('hp_restore', 0))
        self.bonus_type:  str  = defn.get('bonus_type', 'none')
        self.bonus_stat:  str  = defn.get('bonus_stat', '')
        self.bonus_effect: str = defn.get('bonus_effect', '')
        self.bonus_amount: int = int(defn.get('bonus_amount', 0))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', defn.get('floor_spawn_weight', {}))
        # Food is recognizable by appearance -- identified by default
        self.identified: bool       = True
        self.unidentified_name: str = defn.get('unidentified_name', self.name)


class Potion(Item):
    """Drinkable potion. Instant or timed effect; no quiz required."""
    def __init__(self, defn: dict):
        super().__init__(defn)
        self.effect:   str = defn.get('effect', '')
        self.power:    str = defn.get('power', '')
        self.duration: int = int(defn.get('duration', 0))
        self.floor_spawn_weight: dict = defn.get('floorSpawnWeight', {})
        self.identified: bool       = False
        self.id_level: int          = int(defn.get('id_level', 0))
        self.unidentified_name: str = defn.get('unidentified_name', self.name)

    @property
    def cursed(self) -> bool:
        return getattr(self, 'buc', 'uncursed') == 'cursed'

    @cursed.setter
    def cursed(self, value: bool):
        self.buc = 'cursed' if value else 'uncursed'


class GoldPile:
    """Gold coins lying on the ground. Picked up to credit player_gold directly."""
    def __init__(self, amount: int, x: int = 0, y: int = 0):
        self.id     = 'gold_pile'
        self.amount = amount
        self.name   = f"{amount} gold coin{'s' if amount != 1 else ''}"
        self.symbol = '$'
        self.color  = (218, 165, 32)
        self.x      = x
        self.y      = y

    def _refresh_name(self):
        self.name = f"{self.amount} gold coin{'s' if self.amount != 1 else ''}"


def add_gold_to_tile(ground_items: list, amount: int, x: int, y: int) -> 'GoldPile':
    """Pool gold on a single tile instead of creating overlapping piles.
    If a GoldPile already exists at (x, y), add to it; otherwise create new.
    Returns the resulting GoldPile."""
    if amount <= 0:
        return None
    for it in ground_items:
        if isinstance(it, GoldPile) and it.x == x and it.y == y:
            it.amount += amount
            it._refresh_name()
            return it
    pile = GoldPile(amount, x, y)
    ground_items.append(pile)
    return pile


# Stackable item types: identical instances (same id) merge into one stack entry.
Item._STACKABLE_CLASSES = (Ingredient, Food, Potion, Scroll, Ammo)

# ------------------------------------------------------------------
# Loading
# ------------------------------------------------------------------

_CLASS_MAP: dict[str, type] = {
    'weapon':     Weapon,
    'armor':      Armor,
    'shield':     Shield,
    'accessory':  Accessory,
    'wand':       Wand,
    'scroll':     Scroll,
    'spellbook':  Spellbook,
    'ingredient': Ingredient,
    'artifact':   Artifact,
    'ammo':       Ammo,
    'food':       Food,
    'potion':     Potion,
    'lockpick':   Lockpick,
    'container':  Container,
}


def load_items(item_class: str) -> list:
    """Load and return a list of Item instances from data/items/{item_class}.json."""
    path = os.path.join(_DATA_DIR, f"{item_class}.json")
    with open(path, encoding='utf-8') as f:
        raw = json.load(f)
    cls = _CLASS_MAP[item_class]
    return [cls({**defn, 'id': item_id, 'item_class': item_class})
            for item_id, defn in raw.items()]


# ------------------------------------------------------------------
# Accessory appearance pool (one-cosmetic-per-item, 2026-06-07)
# ------------------------------------------------------------------
# Cosmetic ring/amulet groups were collapsed to ONE functional definition each
# (see data/items/_collapse_cosmetic_accessories.py + the design proposal). The
# survivor carries a NEUTRAL fallback look ("a ring" / "an amulet"); the real
# unidentified appearance is dealt ONCE PER RUN from this pool by
# Game._roll_appearance_map / Game.apply_appearance. Pooled per slot so a ring
# never wears an amulet's look.

_APPEARANCE_CACHE: dict | None = None


def load_accessory_appearances() -> dict:
    """Return {'ring': [{'name','color'}, ...], 'amulet': [...]}. Cached."""
    global _APPEARANCE_CACHE
    if _APPEARANCE_CACHE is None:
        path = os.path.join(_DATA_DIR, 'accessory_appearances.json')
        with open(path, encoding='utf-8') as f:
            _APPEARANCE_CACHE = json.load(f)
    return _APPEARANCE_CACHE


# Deleted/renamed-id remap (one-cosmetic-per-item migration). Old saves and any
# stale string-literal grant may hold a variant id that no longer exists in
# accessory.json; map it to the surviving canonical id so load doesn't crash and
# the item resolves to its (now single) functional type. Generated by
# data/items/_collapse_cosmetic_accessories.py --check; keep in sync with it.
LEGACY_ACCESSORY_ID_REMAP: dict[str, str] = {
    # -- cosmetic collapses --
    'ring_warning_oak': 'ring_of_warning',
    'ring_warning_runed_metal': 'ring_of_warning',
    'ring_warning_ancient_copper': 'ring_of_warning',
    'ring_warning_bone': 'ring_of_warning',
    'ring_warning_twisted_iron': 'ring_of_warning',
    'ring_warning_carved_jade': 'ring_of_warning',
    'ring_warning_rough_stone': 'ring_of_warning',
    'ring_warning_grey_granite': 'ring_of_warning',
    'ring_searching_silver': 'ring_of_searching',
    'ring_searching_polished_crystal': 'ring_of_searching',
    'ring_searching_malachite': 'ring_of_searching',
    'ring_searching_engraved_pewter': 'ring_of_searching',
    'ring_searching_gleaming_iron': 'ring_of_searching',
    'ring_searching_pale_ivory': 'ring_of_searching',
    'ring_searching_mossy_stone': 'ring_of_searching',
    'ring_telepathy_sapphire': 'ring_of_telepathy',
    'ring_telepathy_lapis_lazuli': 'ring_of_telepathy',
    'ring_telepathy_cobalt_blue': 'ring_of_telepathy',
    'ring_telepathy_dark_obsidian': 'ring_of_telepathy',
    'ring_telepathy_moonstone': 'ring_of_telepathy',
    'ring_telepathy_twilight_crystal': 'ring_of_telepathy',
    'ring_regen_emerald': 'ring_of_regeneration',
    'ring_regen_peridot': 'ring_of_regeneration',
    'ring_regen_serpentine': 'ring_of_regeneration',
    'ring_regen_verdant_jade': 'ring_of_regeneration',
    'ring_regen_living_wood': 'ring_of_regeneration',
    'ring_fire_res_a': 'ring_of_fire_resist',
    'ring_fire_res_b': 'ring_of_fire_resist',
    'ring_cold_res_a': 'ring_of_cold_resist',
    'ring_cold_res_b': 'ring_of_cold_resist',
    'ring_shock_res_a': 'ring_of_shock_resist',
    'ring_shock_res_b': 'ring_of_shock_resist',
    'ring_poison_res_a': 'ring_of_poison_resist',
    'ring_poison_res_b': 'ring_of_poison_resist',
    'ring_sleep_res_a': 'ring_of_sleep_resist',
    'ring_sleep_res_b': 'ring_of_sleep_resist',
    'amulet_warning_leather': 'amulet_of_warning',
    'amulet_warning_copper': 'amulet_of_warning',
    'amulet_searching_bone': 'amulet_of_searching',
    'amulet_searching_bronze': 'amulet_of_searching',
    'amulet_telepathy_silver': 'amulet_of_telepathy',
    'amulet_telepathy_jade': 'amulet_of_telepathy',
    # -- tiered stat-ring renames (+1 base / +2 greater / +3 master) --
    'ring_strength_iron': 'ring_of_strength',
    'ring_strength_steel': 'ring_of_greater_strength',
    'ring_strength_adamantine': 'ring_of_master_strength',
    'ring_strength_mithril': 'ring_of_master_strength',
    'ring_constitution_ruby': 'ring_of_constitution',
    'ring_constitution_coral': 'ring_of_greater_constitution',
    'ring_constitution_carnelian': 'ring_of_greater_constitution',
    'ring_constitution_garnet': 'ring_of_master_constitution',
    'ring_dexterity_quicksilver': 'ring_of_dexterity',
    'ring_dexterity_thin_wire': 'ring_of_greater_dexterity',
    'ring_dexterity_spun_glass': 'ring_of_greater_dexterity',
    'ring_dexterity_featherweight': 'ring_of_master_dexterity',
    'ring_intellect_amethyst': 'ring_of_intellect',
    'ring_intellect_purple_glass': 'ring_of_greater_intellect',
    'ring_intellect_arcane_pewter': 'ring_of_greater_intellect',
    'ring_intellect_prismatic': 'ring_of_master_intellect',
    'ring_wisdom_opal': 'ring_of_wisdom',
    'ring_wisdom_pearl': 'ring_of_greater_wisdom',
    'ring_wisdom_ivory': 'ring_of_greater_wisdom',
    'ring_wisdom_white_quartz': 'ring_of_master_wisdom',
    'ring_perception_topaz': 'ring_of_perception',
    'ring_perception_amber': 'ring_of_greater_perception',
    'ring_perception_citrine': 'ring_of_greater_perception',
    'ring_perception_hawks_eye': 'ring_of_master_perception',
    # -- tiered stat-amulet renames (+2 base / +3 greater; amulets have no +1) --
    'amulet_strength_iron_medallion': 'amulet_of_strength',
    'amulet_strength_titan_iron_pendant': 'amulet_of_greater_strength',
    'amulet_constitution_ruby_pendant': 'amulet_of_constitution',
    'amulet_constitution_guardian_ruby_locket': 'amulet_of_greater_constitution',
    'amulet_dexterity_quicksilver_charm': 'amulet_of_dexterity',
    'amulet_dexterity_air_light_locket': 'amulet_of_greater_dexterity',
    'amulet_intellect_amethyst_talisman': 'amulet_of_intellect',
    'amulet_intellect_brilliant_crystal_medallion': 'amulet_of_greater_intellect',
    'amulet_wisdom_opal_locket': 'amulet_of_wisdom',
    'amulet_wisdom_sage_ivory_locket': 'amulet_of_greater_wisdom',
    'amulet_perception_eagle_eye_pendant': 'amulet_of_perception',
    'amulet_perception_hawk_feather_talisman': 'amulet_of_greater_perception',
}


def remap_legacy_accessory_id(item_id: str) -> str:
    """Resolve a possibly-removed accessory id to its surviving canonical id."""
    return LEGACY_ACCESSORY_ID_REMAP.get(item_id, item_id)


_ACCESSORY_DEF_CACHE: dict | None = None


def get_accessory_def(item_id: str) -> dict | None:
    """Return the raw JSON definition for an accessory id (after legacy remap),
    or None if unknown. Cached. Used to heal save items whose old variant id was
    merged away: the loader rebuilds mechanical fields from the survivor."""
    global _ACCESSORY_DEF_CACHE
    if _ACCESSORY_DEF_CACHE is None:
        path = os.path.join(_DATA_DIR, 'accessory.json')
        with open(path, encoding='utf-8') as f:
            _ACCESSORY_DEF_CACHE = json.load(f)
    canon = remap_legacy_accessory_id(item_id)
    return _ACCESSORY_DEF_CACHE.get(canon)


# ------------------------------------------------------------------
# Chest templates -- 12 named chest archetypes with thematic loot
# (data/chest_templates.json). dungeon.spawn_items() picks a template by
# floor band and stamps `template_id` onto the Container instance. The
# container_system reads the template to drive escalator-chain loot.
# ------------------------------------------------------------------

_CHEST_TEMPLATE_CACHE: dict | None = None


def load_chest_templates() -> dict[str, dict]:
    """Return the dict of chest templates keyed by id. Cached on first load."""
    global _CHEST_TEMPLATE_CACHE
    if _CHEST_TEMPLATE_CACHE is None:
        path = data_path('data', 'chest_templates.json')
        with open(path, encoding='utf-8') as f:
            _CHEST_TEMPLATE_CACHE = json.load(f)
    return _CHEST_TEMPLATE_CACHE


def get_chest_template(template_id: str) -> dict | None:
    """Look up one chest template by id."""
    return load_chest_templates().get(template_id)


# ------------------------------------------------------------------
# Template + Material system (Phase 3.1 T3)
# Weapons, armor, and shields are now COMPOSITIONAL: a template defines the
# SHAPE (chain, slot, mechanics) and a material defines the STATS (damage
# multiplier, weight, max enchant, properties). Instances are produced on
# demand by instantiate_weapon / instantiate_armor / instantiate_shield.
# Uniques (Hrunting, Sword of Michael, etc.) keep their own JSON entries.
# ------------------------------------------------------------------

_TEMPLATES_DIR = data_path('data', 'templates')
_MATERIALS_DIR = data_path('data', 'materials')

# Cached on first load — these are read-only schema.
_TEMPLATE_CACHE: dict[str, dict[str, dict]] = {}
_MATERIAL_CACHE: dict[str, dict[str, dict]] = {}


def _load_category(root: str, category: str) -> dict[str, dict]:
    """Load every JSON file under {root}/{category}/ into a dict keyed by id."""
    cat_dir = os.path.join(root, category)
    if not os.path.isdir(cat_dir):
        return {}
    out = {}
    for fn in os.listdir(cat_dir):
        if not fn.endswith('.json'):
            continue
        with open(os.path.join(cat_dir, fn), encoding='utf-8') as f:
            defn = json.load(f)
        item_id = defn.get('id') or os.path.splitext(fn)[0]
        out[item_id] = defn
    return out


def load_templates(category: str) -> dict[str, dict]:
    """Return all templates for a category: 'weapons', 'armor', or 'shields'."""
    if category not in _TEMPLATE_CACHE:
        _TEMPLATE_CACHE[category] = _load_category(_TEMPLATES_DIR, category)
    return _TEMPLATE_CACHE[category]


def load_materials(category: str) -> dict[str, dict]:
    """Return all materials for a category: 'weapons' or 'armor'."""
    if category not in _MATERIAL_CACHE:
        _MATERIAL_CACHE[category] = _load_category(_MATERIALS_DIR, category)
    return _MATERIAL_CACHE[category]


def get_template(category: str, template_id: str) -> dict | None:
    """Look up one template by category + id."""
    return load_templates(category).get(template_id)


def get_material(category: str, material_id: str) -> dict | None:
    """Look up one material by category + id."""
    return load_materials(category).get(material_id)


# ----------------------------------------------------------------------
# Item-name composition (2026-05-28)
# ----------------------------------------------------------------------
# Many armor/shield templates carry a material word in their `name`
# field ("iron boots", "light wooden shield", "chain shirt"). Many
# material `unidentified_descriptor`s are written as noun phrases with
# leading articles and weapon-specific tail nouns ("a wooden plank",
# "a faintly blue blade"). The naive concat in the original compose
# logic produced "a wooden plank light wooden shield" — material word
# duplicated, ungrammatical, and overflowing the Kit menu.
#
# These helpers normalize both sides BEFORE concat so the result reads
# like a real noun phrase. No JSON edits required — they make existing
# data compose correctly.
#
# See proposals/v2_audit/IDENTIFY_SYSTEM.md §11 (Item-name composition).

GENERIC_MATERIAL_WORDS = frozenset({
    'wood', 'wooden', 'iron', 'steel', 'leather', 'plate',
    'chain', 'cloth', 'silk', 'linen', 'hide', 'padded',
    'studded', 'scale', 'bronze', 'silver', 'gold', 'mithril',
    'banded', 'ringmail', 'chainmail', 'splint',
})

# Tail nouns that appear at the END of material `unidentified_descriptor`
# values and don't compose as adjectives. "a wooden plank" -> strip
# "plank" leaves "wooden", which composes correctly with a template name.
DESCRIPTOR_TAIL_NOUNS = frozenset({
    # item-SHAPE / generic object nouns -- redundant before a template noun
    # ("a midnight-dark BLADE" -> "midnight-dark", "a heavy dark CLUB" ->
    # "heavy dark"). Material-class words (wood, metal, stone, bone, glass...)
    # are deliberately KEPT: for an unidentified item they hint what it might be
    # ("Pale Fibrous Wood Longbow", "Pale Silvery Metal Helm").
    'blade', 'haft', 'timber', 'plank', 'plate', 'board', 'hide', 'cloth',
    'fabric', 'leather', 'weapon', 'thing', 'club', 'wrap', 'length', 'piece',
    'bar', 'ingot', 'rod', 'shaft', 'stick', 'staff', 'sheen', 'sheet', 'suit',
    'wrought', 'armor', 'armour',
})

# Words that begin a relative/prepositional clause: everything from the first
# such word onward is flavor that must NOT leak into a composed item name
# ("a blade THAT shows no edge wear" -> "a blade"; "alloy, color SHIFTING in
# firelight" -> "alloy"). Leading participles like "gleaming"/"glowing" are
# deliberately absent -- they read fine as adjectives ("a gleaming silver ...").
_DESCRIPTOR_CLAUSE_CUT = frozenset({
    'that', 'which', 'who', 'whose', 'of', 'like', 'with', 'woven', 'shifting',
    'color', 'colour', 'set', 'etched', 'flecked', 'veined', 'traced', 'chased',
    'shot',
})

_LEADING_ARTICLES = frozenset({'a', 'an', 'the'})


def _strip_redundant_material_words(tpl_name: str) -> str:
    """Drop generic material words from a template name so they don't
    duplicate the material prefix.

    >>> _strip_redundant_material_words("light wooden shield")
    'light shield'
    >>> _strip_redundant_material_words("iron boots")
    'boots'
    >>> _strip_redundant_material_words("tower shield")  # no material word
    'tower shield'
    >>> _strip_redundant_material_words("leather")  # whole name is generic
    'leather'
    """
    if not tpl_name:
        return tpl_name
    cleaned = ' '.join(w for w in tpl_name.split()
                       if w.lower() not in GENERIC_MATERIAL_WORDS).strip()
    # If everything stripped (e.g. tpl_name was "leather"), keep original
    # so we don't end up with empty strings — the material prefix will
    # carry the meaning.
    return cleaned or tpl_name


def _normalize_descriptor(desc: str) -> str:
    """Reduce a flavor `unidentified_descriptor` to a SHORT visual adjective
    phrase fit to prefix a template noun. Strips a leading article, drops
    commas, truncates at the first clause word, then strips trailing object
    nouns:

    >>> _normalize_descriptor("a wooden plank")
    'wooden'
    >>> _normalize_descriptor("a faintly blue blade")
    'faintly blue'
    >>> _normalize_descriptor("a midnight-dark blade that shows no edge wear")
    'midnight-dark'
    >>> _normalize_descriptor("a heavy, dark club")
    'heavy dark'
    >>> _normalize_descriptor("an impossible alloy, color shifting in firelight")
    'impossible alloy'

    Falls back to 'strange' if nothing usable survives -- a descriptor that
    reduces to nothing should be rewritten in data, but a composed name must
    NEVER read as garbage ("Pale Fibrous Wood Longbow").
    """
    if not desc:
        return desc
    words = desc.replace(',', ' ').split()
    # Strip leading article (a / an / the).
    if words and words[0].lower() in _LEADING_ARTICLES:
        words = words[1:]
    # Truncate at the first relative/prepositional clause word.
    cut = next((i for i, w in enumerate(words)
                if w.lower().strip('.;') in _DESCRIPTOR_CLAUSE_CUT), None)
    if cut is not None:
        words = words[:cut]
    # Strip trailing object-nouns ('blade', 'wood', 'metal', ...).
    while words and words[-1].lower().strip('.;') in DESCRIPTOR_TAIL_NOUNS:
        words.pop()
    cleaned = ' '.join(words).strip(' ,.;')
    return cleaned or 'strange'


def _title_if_all_lower(s: str) -> str:
    """Title-case `s` ONLY if it's currently entirely lowercase. Mirrors
    game_helpers.fix_name_case so 'linen padded' becomes 'Linen Padded'
    without breaking 'STR+1'-style identifiers that already use case
    deliberately. Per user feedback 2026-05-29: identified item names
    were displaying as lowercase ('linen padded') in messages where
    fix_name_case wasn't applied at the call site. Title-casing at the
    composition source means every downstream consumer sees the
    correct form."""
    return s.title() if s and s == s.lower() else s


def _append_noun_if_missing(text: str, noun: str) -> str:
    """If `text` doesn't already end in `noun` (or contain it), append it.
    Used by compose_item_name / compose_unidentified_name to rescue names
    whose template is a bare adjective ('padded', 'leather', 'plate'),
    which would otherwise render as 'Linen Padded' with no noun. The
    template JSON supplies `noun` ('armor', 'mail', 'coat'); we only
    append the noun's words that aren't already present so 'padded shirt'
    + noun='shirt' doesn't become 'padded shirt shirt'.

    >>> _append_noun_if_missing('linen padded', 'coat')
    'linen padded coat'
    >>> _append_noun_if_missing('linen padded shirt', 'shirt')
    'linen padded shirt'
    >>> _append_noun_if_missing('leather armor', 'armor')
    'leather armor'
    >>> _append_noun_if_missing('damascus steel full', 'plate armor')
    'damascus steel full plate armor'
    >>> _append_noun_if_missing('damascus steel plate', 'plate armor')
    'damascus steel plate armor'
    """
    if not noun:
        return text
    words_lc = [w.lower() for w in text.split()]
    # Only append the noun-words that aren't already in the text. Preserves
    # word order in the noun phrase ("plate armor" not "armor plate").
    missing = [w for w in noun.split() if w.lower() not in words_lc]
    if not missing:
        return text
    return f"{text} {' '.join(missing)}".strip()


def _drop_words_present_in(phrase: str, *carriers: str) -> str:
    """Remove from `phrase` every word the material side already carries, so a
    template whose name IS a material word doesn't double up:
      'hide'   (material) + 'hide'    (template) -> 'Hide Armor'
      'leather'           + 'leather'            -> 'Leather Armor'
      'boiled leather'    + 'leather'            -> 'Boiled Leather Armor'
      'rawhide'/'dragonhide' + 'hide'            -> 'Rawhide/Dragonhide Armor'
    A template word is redundant if it matches a carrier word exactly, OR is the
    tail of a longer carrier word ('hide' inside 'rawhide'). The length guards
    keep short coincidental suffixes safe. Case-insensitive; preserves order +
    the kept words' original casing.
    """
    carrier = set()
    for c in carriers:
        carrier |= {w.lower() for w in c.split()}

    def redundant(w: str) -> bool:
        wl = w.lower()
        if wl in carrier:
            return True
        return len(wl) >= 4 and any(
            len(cw) > len(wl) and cw.endswith(wl) for cw in carrier)

    return ' '.join(w for w in phrase.split() if not redundant(w))


def _drop_generic_words_implied_by(material_name: str, *template_parts: str) -> str:
    """Drop a GENERIC material word already implied by a template word it is the
    tail of: 'dwarven plate' + 'breastplate' -> 'Dwarven Breastplate'. The word
    is KEPT when it still distinguishes ('dwarven plate' + 'gauntlets' stays
    'Dwarven Plate Gauntlets', since plate-gauntlets differ from leather ones).
    Only generic material words qualify, so real descriptors are never lost; the
    last surviving word is never stripped."""
    tpl = set()
    for p in template_parts:
        tpl |= {w.lower() for w in p.split()}

    def implied(w: str) -> bool:
        wl = w.lower()
        return (wl in GENERIC_MATERIAL_WORDS and len(wl) >= 4
                and any(tw != wl and tw.endswith(wl) for tw in tpl))

    kept = [w for w in material_name.split() if not implied(w)]
    return ' '.join(kept) or material_name


# Words that all mean "leather/hide armor". A leather-family MATERIAL meeting the
# OTHER family word as the TEMPLATE reads redundantly ('boiled leather' + 'hide'
# -> 'Boiled Leather Hide Armor'), so the template class-word is dropped.
_LEATHER_FAMILY = frozenset({'hide', 'leather', 'rawhide', 'skin'})


def _drop_leather_family_redundancy(cleaned: str, material_name: str) -> str:
    """If the cleaned template is a SINGLE leather/hide-family class word and the
    material is already a leather/hide material, drop the template word -- the
    appended noun carries the type: 'boiled leather' + 'hide' -> 'Boiled Leather
    Armor', 'dragonhide' + 'leather' -> 'Dragonhide Armor'."""
    words = cleaned.split()
    if len(words) != 1 or words[0].lower() not in _LEATHER_FAMILY:
        return cleaned
    mw = material_name.lower().split()
    if any(w in mw or material_name.lower().endswith(w) for w in _LEATHER_FAMILY):
        return ''
    return cleaned


def compose_item_name(material_name: str, template_name: str,
                      noun: str = '') -> str:
    """Identified-form item name. Strips redundant material words from
    the template so 'steel' + 'iron boots' renders as 'steel boots',
    not 'steel iron boots'. Also drops any template word the material name
    already carries, so 'hide' + 'hide' is 'Hide Armor', not 'Hide Hide
    Armor', and a cross-family leather/hide redundancy ('boiled leather' +
    'hide' -> 'Boiled Leather Armor'). Appends `noun` if provided and the cleaned
    phrase doesn't already contain it — this rescues bare-adjective template
    names ('padded' + 'linen' would otherwise be 'Linen Padded'). Title-cases."""
    cleaned = _strip_redundant_material_words(template_name)
    cleaned = _drop_words_present_in(cleaned, material_name)
    cleaned = _drop_leather_family_redundancy(cleaned, material_name)
    material_name = _drop_generic_words_implied_by(material_name, cleaned, noun)
    composed = f"{material_name} {cleaned}".strip()
    composed = _append_noun_if_missing(composed, noun)
    return _title_if_all_lower(composed)


def compose_unidentified_name(material_descriptor: str, template_name: str,
                              noun: str = '') -> str:
    """Unidentified-form item name. Normalizes both the descriptor
    (drop article, drop tail-noun) and the template (drop redundant
    material words, then any word the descriptor already carries) before
    composing. Appends `noun` if provided and the cleaned phrase lacks one.
    Title-cases the result."""
    cleaned_desc = _normalize_descriptor(material_descriptor)
    cleaned_tpl = _strip_redundant_material_words(template_name)
    cleaned_tpl = _drop_words_present_in(cleaned_tpl, cleaned_desc)
    composed = f"{cleaned_desc} {cleaned_tpl}".strip()
    composed = _append_noun_if_missing(composed, noun)
    return _title_if_all_lower(composed)


def instantiate_weapon(template_id: str, material_id: str, *,
                       enchant: int = 0, buc: str = 'uncursed',
                       x: int = 0, y: int = 0) -> Weapon:
    """Build a Weapon by combining a template (shape) with a material (stats).
    Damage is derived from curve.weapon_base_damage(material.peak_floor) × the
    material's damage_mult × the template's damage_modifier. Chain shape comes
    entirely from the template."""
    tpl = get_template('weapons', template_id)
    mat = get_material('weapons', material_id)
    if not tpl:
        raise ValueError(f"Unknown weapon template: {template_id}")
    if not mat:
        raise ValueError(f"Unknown weapon material: {material_id}")

    # Re-anchored 2026-05-18: weapon_base is chosen so that a chain-5 hit
    # at the material's peak floor equals one trash-mob HP. This makes the
    # chain ladder legible at every tier (no more 1,1,1,1,2 at iron level)
    # and gives an explicit, design-grounded relationship between weapon
    # damage and monster HP.
    #
    #   chain_5_mult = template.chain_multipliers[-1]
    #   weapon_base  = mob_hp(peak_floor) / chain_5_mult
    #
    # Then base_damage applies material's damage_mult + template's
    # damage_modifier as before, and round (not int-truncate) keeps the
    # chain-1..5 gradient visible at low tiers.
    peak_floor = int(mat.get('peak_floor', 1))
    if peak_floor <= 20:
        mob_hp = 4 * (1.10 ** (peak_floor - 1))
    else:
        early_cap = 4 * (1.10 ** 19)
        mob_hp = early_cap * (1.025 ** (peak_floor - 20))
    chain_mults = tpl.get('chain_multipliers') or [0.5, 0.85, 1.0, 1.45, 2.0]
    chain_5_mult = float(chain_mults[-1])
    weapon_base = max(1, round(mob_hp / chain_5_mult))
    # Floor of 2 (not 1) on final base damage. This is universal — it
    # guarantees a LEGIBLE chain-1..5 gradient at every weapon × material
    # combo, including weak materials (copper, oak rapier) where the math
    # would otherwise produce base 1 and a flat 1,1,1,1,2 chain. The 2-floor
    # doesn't break differentiation between materials because high-tier
    # materials produce base values 3+ naturally.
    base_damage = max(2, round(weapon_base
                               * float(mat.get('damage_mult', 1.0))
                               * float(tpl.get('damage_modifier', 1.0))))

    weight = max(0.1, tpl.get('base_weight_lb', 3.0) * mat.get('weight_mult', 1.0))
    name = compose_item_name(mat['name'], tpl['name'], tpl.get('noun', ''))
    lore = _compose_common_lore(tpl, mat, name, item_noun_for_weapon(tpl))

    defn = {
        'id': f"{material_id}_{template_id}",
        'name': name,
        'lore': lore,
        'symbol': '(',  # default weapon symbol; could vary by template
        'color': mat.get('color', [180, 180, 180]),
        'weight': weight,
        'item_class': 'weapon',
        'min_level': int(mat.get('peak_floor', 1) - mat.get('spread', 10)),
        'weapon_class': tpl.get('weapon_class', 'sword'),
        'class': tpl.get('weapon_class', 'sword'),
        'material': material_id,
        'tier': max(1, peak_floor // 20 + 1),
        'base_damage': base_damage,
        'chain_multipliers': tpl.get('chain_multipliers', [0.5, 1.0, 1.5, 2.5]),
        'damage_types': list(tpl.get('damage_types', ['slash'])),
        'two_handed': tpl.get('hands', 1) >= 2,
        'reach': int(tpl.get('reach', 1)),
        'crit_multiplier': float(tpl.get('crit_multiplier', 1.5)),
        'enchant_bonus': max(0, min(enchant, int(mat.get('max_enchant', 2)))),
        'identified': False,
        'unidentified_name': compose_unidentified_name(
            mat.get('unidentified_descriptor', mat['name']), tpl['name'],
            tpl.get('noun', '')),
        'buc': buc,
        'requires_ammo': tpl.get('requires_ammo', None),
        'infinite_ammo': bool(tpl.get('infinite_ammo', False)),
    }
    # Bring in material-flagged special properties (silver vs undead, etc.)
    for k in ('effective_against', 'vulnerabilities', 'special_properties'):
        if mat.get(k):
            defn[k] = mat[k]
    # Heavy-class mechanic flag (cleave / stun / etc. — code-side support pending)
    if tpl.get('class_mechanic'):
        defn['class_mechanic'] = tpl['class_mechanic']
        # Convert the 'ignores_shield' class mechanic into the explicit
        # ignore_shield weapon attribute. The bypass is checked at use-site
        # via weapon.ignore_shield, not via class_mechanic string.
        if tpl['class_mechanic'] == 'ignores_shield':
            defn['ignoreShield'] = True
    w = Weapon(defn)
    w.x, w.y = x, y
    # Material-specific damage type additions (e.g., silver adds 'silver' as a type)
    if material_id not in ('iron', 'steel'):
        if material_id not in w.damage_types:
            w.damage_types.append(material_id)
    return w


def _fix_article(text, material_name):
    """Fix 'A iron' -> 'An iron' if material name starts with a vowel."""
    import re as _re
    if material_name and material_name[0].lower() in 'aeiou':
        text = _re.sub(r'\bA\s+' + _re.escape(material_name),
                       f'An {material_name}', text)
    return text


def item_noun_for_weapon(tpl):
    return {
        'sword': 'blade', 'dagger': 'blade', 'rapier': 'blade',
        'scimitar': 'blade', 'axe': 'head', 'mace': 'head',
        'maul': 'head', 'hammer': 'head', 'club': 'shaft',
        'staff': 'shaft', 'flail': 'head', 'glaive': 'blade',
        'spear': 'point', 'bow': 'wood', 'crossbow': 'limb',
        'sling': 'leather', 'whip': 'cord',
    }.get(tpl.get('weapon_class', ''), 'weapon')


def _compose_common_lore(tpl, mat, name, item_noun):
    """Compose lore for a common item from template.lore_template +
    material.lore_descriptor. Returns a non-empty lore string.
    """
    lore_template = tpl.get('lore_template', '')
    material_descriptor = mat.get('lore_descriptor', '')
    lore = ''
    if lore_template:
        try:
            lore = lore_template.format(material_name=mat['name'])
        except (KeyError, IndexError):
            lore = lore_template
        lore = _fix_article(lore, mat['name'])
    if material_descriptor:
        if lore and not lore.endswith('.'):
            lore = lore + '.'
        if lore:
            lore = f"{lore} The {item_noun} is {material_descriptor}."
        else:
            lore = f"An everyday {name}. The {item_noun} is {material_descriptor}."
            lore = _fix_article(lore, mat['name'])
    if not lore:
        lore = f"A common {name} — reliable enough for the work."
        lore = _fix_article(lore, mat['name'])
    return lore


def instantiate_armor(template_id: str, material_id: str, *,
                     enchant: int = 0, buc: str = 'uncursed',
                     x: int = 0, y: int = 0) -> 'Armor':
    """Build an Armor instance from template + material."""
    tpl = get_template('armor', template_id)
    mat = get_material('armor', material_id)
    if not tpl:
        raise ValueError(f"Unknown armor template: {template_id}")
    if not mat:
        raise ValueError(f"Unknown armor material: {material_id}")

    base_ac = int(tpl.get('base_ac_value', 1))
    material_ac = int(mat.get('ac_bonus', mat.get('armor_ac_bonus', 0)))
    weight = max(0.1, tpl.get('base_weight_lb', 5.0) * mat.get('weight_mult', 1.0))
    name = compose_item_name(mat['name'], tpl['name'], tpl.get('noun', ''))

    defn = {
        'id': f"{material_id}_{template_id}",
        'name': name,
        'lore': _compose_common_lore(tpl, mat, name, 'plate' if 'plate' in template_id else 'piece'),
        'symbol': '[',
        'color': mat.get('color', [180, 180, 180]),
        'weight': weight,
        'item_class': 'armor',
        'min_level': int(mat.get('peak_floor', 1) - mat.get('spread', 10)),
        'slot': tpl.get('slot', 'body'),
        'tier': max(1, int(mat.get('peak_floor', 1)) // 20 + 1),
        'material': material_id,
        'ac_bonus': base_ac + material_ac,
        'enchant_bonus': max(0, min(enchant, int(mat.get('max_enchant', 2)))),
        'damage_resistances': mat.get('resistances', {}) if isinstance(mat.get('resistances'), dict) else {},
        'identified': False,
        'unidentified_name': compose_unidentified_name(
            mat.get('unidentified_descriptor', mat['name']), tpl['name'],
            tpl.get('noun', '')),
        'buc': buc,
        'quiz_tier': max(1, int(mat.get('peak_floor', 1)) // 20 + 1),
        # equip_threshold = complexity, driven by armor_class_tier:
        #   light = 1 (slip-on: cloak, leather, padded)
        #   medium = 2 (straps + lacing: chain shirt, scale, gauntlets)
        #   heavy = 3 (full kit + gambeson: plate, breastplate, banded)
        # Per-template `equip_threshold` overrides the class default if set.
        'equip_threshold': int(tpl.get('equip_threshold', 2)),
    }
    a = Armor(defn)
    a.x, a.y = x, y
    return a


def instantiate_shield(template_id: str, material_id: str, *,
                      enchant: int = 0, buc: str = 'uncursed',
                      x: int = 0, y: int = 0) -> 'Shield':
    """Build a Shield instance from template + material."""
    # Shields can pull material from either pool (weapons/armor) — try both.
    tpl = get_template('shields', template_id)
    mat = get_material('armor', material_id) or get_material('weapons', material_id)
    if not tpl:
        raise ValueError(f"Unknown shield template: {template_id}")
    if not mat:
        raise ValueError(f"Unknown shield material: {material_id}")
    base_ac = int(tpl.get('base_ac_value', 1))
    material_ac = int(mat.get('ac_bonus', mat.get('armor_ac_bonus', 0)))
    weight = max(0.1, tpl.get('base_weight_lb', 5.0) * mat.get('weight_mult', 1.0))
    name = compose_item_name(mat['name'], tpl['name'], tpl.get('noun', ''))
    defn = {
        'id': f"{material_id}_{template_id}",
        'name': name,
        'lore': _compose_common_lore(tpl, mat, name, 'face' if 'shield' in template_id.lower() or 'buckler' in template_id.lower() else 'shield'),
        'symbol': ')',
        'color': mat.get('color', [180, 180, 180]),
        'weight': weight,
        'item_class': 'shield',
        'min_level': int(mat.get('peak_floor', 1) - mat.get('spread', 10)),
        'tier': max(1, int(mat.get('peak_floor', 1)) // 20 + 1),
        'material': material_id,
        'ac_bonus': base_ac + material_ac,
        'enchant_bonus': max(0, min(enchant, int(mat.get('max_enchant', 2)))),
        'identified': False,
        'unidentified_name': compose_unidentified_name(
            mat.get('unidentified_descriptor', mat['name']), tpl['name'],
            tpl.get('noun', '')),
        'buc': buc,
        'quiz_tier': max(1, int(mat.get('peak_floor', 1)) // 20 + 1),
    }
    s = Shield(defn)
    s.x, s.y = x, y
    return s


def material_spawn_weight(material: dict, floor: int) -> float:
    """Bell-curve spawn weight for a material at the given floor."""
    import math
    peak_floor = int(material.get('peak_floor', 1))
    spread = max(1, int(material.get('spread', 10)))
    peak_weight = float(material.get('peak_weight', 1.0))
    if peak_weight <= 0:
        return 0.0
    distance = floor - peak_floor
    bell = math.exp(-(distance ** 2) / (2 * spread ** 2))
    if bell < 0.005:
        return 0.0
    return max(0.02, peak_weight * bell)


def pick_random_weapon_for_floor(floor: int, rng) -> Weapon | None:
    """Pick a random (template, material) pair appropriate for this floor
    and instantiate a Weapon. Returns None if no eligible material."""
    materials = load_materials('weapons')
    weighted = [(mid, m, material_spawn_weight(m, floor))
                for mid, m in materials.items()]
    weighted = [(mid, m, w) for mid, m, w in weighted if w > 0]
    if not weighted:
        return None
    total = sum(w for _, _, w in weighted)
    r = rng.random() * total
    cum = 0.0
    chosen_mid, chosen_mat = weighted[0][0], weighted[0][1]
    for mid, m, w in weighted:
        cum += w
        if r <= cum:
            chosen_mid, chosen_mat = mid, m
            break

    # Pick a compatible template
    templates = load_templates('weapons')
    mat_classes = set(chosen_mat.get('material_class', '').split(',')) | {chosen_mat.get('material_class', '')}
    compatible = []
    for tid, t in templates.items():
        accepts = set(t.get('compatible_material_classes', []))
        if not accepts or accepts & mat_classes or chosen_mat.get('material_class') in accepts:
            compatible.append((tid, t))
    if not compatible:
        compatible = list(templates.items())  # fallback
    tid, _ = rng.choice(compatible)
    return instantiate_weapon(tid, chosen_mid)


def pick_random_armor_for_floor(floor: int, rng, slot: str = 'body') -> 'Armor | None':
    """Pick a random armor template+material pair for this floor + slot.
    Filters templates to those that BOTH match the slot AND accept the
    chosen material's material_class — so e.g. 'ash' (wood) only goes to
    armor templates that accept wood, never to a steel breastplate."""
    materials = load_materials('armor')
    # Pre-filter materials: only those usable in at least one slot-matching template
    templates = load_templates('armor')
    slot_templates = [(tid, t) for tid, t in templates.items()
                      if t.get('slot', 'body') == slot]
    if not slot_templates:
        return None
    # Build set of material classes accepted by any slot-matching template
    accepted_classes: set[str] = set()
    for _, t in slot_templates:
        accepted_classes.update(t.get('compatible_material_classes', []))

    weighted = []
    for mid, m in materials.items():
        if m.get('material_class', '') not in accepted_classes and accepted_classes:
            continue
        w = material_spawn_weight(m, floor)
        if w > 0:
            weighted.append((mid, m, w))
    if not weighted:
        return None
    total = sum(w for _, _, w in weighted)
    r = rng.random() * total
    cum = 0.0
    chosen_mid, chosen_mat = weighted[0][0], weighted[0][1]
    for mid, m, w in weighted:
        cum += w
        if r <= cum:
            chosen_mid, chosen_mat = mid, m
            break
    # Now narrow templates to those that accept this specific material
    chosen_class = chosen_mat.get('material_class', '')
    compatible = [(tid, t) for tid, t in slot_templates
                  if chosen_class in t.get('compatible_material_classes', [])]
    if not compatible:
        compatible = slot_templates  # safety fallback
    tid, _ = rng.choice(compatible)
    try:
        return instantiate_armor(tid, chosen_mid)
    except ValueError:
        return None


def pick_random_shield_for_floor(floor: int, rng) -> 'Shield | None':
    """Pick a random shield template+material pair for this floor. Filters
    by template/material compatibility so e.g. 'linen' doesn't end up in a
    tower shield."""
    materials = load_materials('armor')
    templates = load_templates('shields')
    if not templates:
        return None
    # Set of material classes accepted by any shield template
    accepted_classes: set[str] = set()
    for t in templates.values():
        accepted_classes.update(t.get('compatible_material_classes', []))
    weighted = []
    for mid, m in materials.items():
        if m.get('material_class', '') not in accepted_classes and accepted_classes:
            continue
        w = material_spawn_weight(m, floor)
        if w > 0:
            weighted.append((mid, m, w))
    if not weighted:
        return None
    total = sum(w for _, _, w in weighted)
    r = rng.random() * total
    cum = 0.0
    chosen_mid, chosen_mat = weighted[0][0], weighted[0][1]
    for mid, m, w in weighted:
        cum += w
        if r <= cum:
            chosen_mid, chosen_mat = mid, m
            break
    chosen_class = chosen_mat.get('material_class', '')
    compatible = [tid for tid, t in templates.items()
                  if chosen_class in t.get('compatible_material_classes', [])]
    if not compatible:
        compatible = list(templates.keys())
    tid = rng.choice(compatible)
    try:
        return instantiate_shield(tid, chosen_mid)
    except ValueError:
        return None


def copy_at(item: Item, x: int, y: int) -> Item:
    """Return a shallow copy of item placed at (x, y)."""
    inst = copy.copy(item)
    inst.x = x
    inst.y = y
    return inst


# ------------------------------------------------------------------
# Deep-lore item factories  (not loaded from JSON)
# ------------------------------------------------------------------

def make_abyssal_shimmer(x: int, y: int) -> Item:
    """A fixed terrain feature -- the ground shimmers with ancient energy."""
    item = Item({
        'id': 'abyssal_shimmer',
        'name': 'Abyssal Shimmer',
        'symbol': '*',
        'color': [80, 20, 160],
        'weight': 9999.0,
        'item_class': 'terrain',
        'min_level': 1,
    })
    item.x = x
    item.y = y
    item.activated = False   # True once the Complete Tablet is placed here
    return item


def make_tablet_of_second_death(x: int, y: int) -> Item:
    """A stone tablet with a curious shaped slot -- unidentified until examined."""
    item = Artifact({
        'id': 'tablet_of_second_death',
        'name': 'Tablet of Second Death',
        'symbol': '=',
        'color': [150, 130, 80],
        'weight': 3.0,
        'item_class': 'artifact',
        'min_level': 80,
        'lore': "An ancient stone tablet, cold to the touch. A circular slot in its center is shaped to hold something luminous. Along the bottom edge, faint words are carved in a dead language. You can make out: 'The key to the Abyss. Place upon the threshold where the veil is thin.'",
    })
    item.x = x
    item.y = y
    item.unidentified_name = 'plain tablet'
    item.identified = False
    item.examine_text = "A plain tablet with a slot that looks like a small stone will fit."
    return item


def make_scroll_lake_of_fire(x: int, y: int) -> Scroll:
    """A worn scroll -- its contents unknown until read."""
    item = Scroll({
        'id': 'scroll_lake_of_fire',
        'name': 'Scroll of the Lake of Fire',
        'symbol': '?',
        'color': [220, 80, 20],
        'weight': 0.3,
        'item_class': 'scroll',
        'min_level': 50,
        'quiz_tier': 3,
        'quiz_threshold': 3,
        'effect': 'lake_of_fire',
        'power': '',
        'unidentified_name': 'worn scroll',
        'identified': False,
        'single_copy': True,
        'lore': "A scroll of terrible power, its words drawn from the final chapter of Revelation. The ink smells of ash and brimstone. The last line is underlined twice: 'This is the second death, the lake of fire.'",
    })
    item.x = x
    item.y = y
    return item


def make_philosophers_wrench(x: int, y: int) -> Wand:
    """An odd tool -- its purpose unclear until the right pieces are in hand."""
    item = Wand({
        'id': 'philosophers_wrench',
        'name': "Philosopher's Wrench",
        'symbol': '/',
        'color': [140, 130, 90],
        'weight': 2.0,
        'item_class': 'wand',
        'min_level': 21,
        'charges': 99,
        'charges_min': 99,
        'charges_max': 99,
        'max_charges': 99,
        'quiz_tier': 1,
        'quiz_threshold': 1,
        'effect': 'philosophers_wrench',
        'power': '',
        'unidentified_name': 'odd tool',
        'identified': False,
        'lore': "A tool of impossible craftsmanship. It does not tighten or loosen — it joins. Place it between two objects that were meant to become one, and the Wrench will fuse them. The alchemists who forged it understood that the greatest creation is not building something new, but completing something unfinished.",
    })
    item.x = x
    item.y = y
    return item


def make_complete_tablet(x: int, y: int) -> Item:
    """The Stone set perfectly into the Tablet -- ready."""
    item = Artifact({
        'id': 'complete_tablet_of_second_death',
        'name': 'Complete Tablet of Second Death',
        'symbol': '=',
        'color': [220, 180, 60],
        'weight': 4.0,
        'item_class': 'artifact',
        'min_level': 1,
        'lore': "The Philosopher's Stone sits perfectly in the tablet's slot. The cold stone is warm now, pulsing with deep golden light. The inscription along the bottom burns bright: 'The key to the Abyss.' It wants to be placed upon a threshold.",
    })
    item.x = x
    item.y = y
    item.identified = True
    item.examine_text = (
        "The Philosopher's Stone sits perfectly in the slot, glowing with deep energy."
    )
    return item


def make_death_bane_scroll(x: int, y: int) -> Scroll:
    """The sixth boss reward scroll -- dropped when Death itself is defeated."""
    item = Scroll({
        'id': 'scroll_deaths_bane',
        'name': "Scroll of Death's Bane",
        'symbol': '?',
        'color': [220, 220, 255],
        'weight': 0.1,
        'item_class': 'scroll',
        'min_level': 1,
        'quiz_tier': 1,
        'quiz_threshold': 1,
        'effect': 'boss_reward',
        'power': 'ABYSSAL-VICTOR',
        'unidentified_name': "Scroll of Death's Bane",
        'identified': True,
        'single_copy': True,
    })
    item.x = x
    item.y = y
    return item
