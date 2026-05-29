import random
from dice import roll
from geom import monster_at_tile, is_at_tile

# Fallback multipliers used when the player has no weapon equipped.
# Bare-hand chain table. Caps at the universal 5-chain like every common
# template; values are deliberately weaker than the weakest template
# (shortsword peak 2.0x) so unarmed combat is the LAST resort, not a
# stronger alternative. Was incorrectly 8-entry with 5.0x peak — caused
# unarmed players to out-chain wielded weapons. Fixed 2026-05-19.
_DEFAULT_MULTIPLIERS = [0.3, 0.5, 0.7, 0.9, 1.2]


def _weapon_mastery(player, weapon) -> dict | None:
    """Return the mastery blessing dict for this weapon if claimed, else None.

    Used to inject chain-5-earned bonuses (Excalibur +0.25 multipliers, etc.) at
    damage-calc time without touching the weapon's base stats.

    Checks BOTH per-id masteries (uniques) AND class masteries (commons —
    iron shortsword etc. get +1 damage via class blessing).
    """
    if weapon is None:
        return None
    # Per-id mastery first (uniques)
    masteries = getattr(player, 'unlocked_masteries', None) or {}
    m = masteries.get(getattr(weapon, 'id', None))
    if m:
        return m
    # Fall back to class mastery (commons)
    class_masteries = getattr(player, 'unlocked_class_masteries', None) or {}
    if class_masteries:
        try:
            from class_masteries import get_mastery_class
            return class_masteries.get(get_mastery_class(weapon))
        except Exception:
            return None
    return None


def _tag_match(monster, tag: str) -> bool:
    """True if `tag` is in the monster's tags (or matches its kind)."""
    if tag == 'all':
        return True
    mtags = set(getattr(monster, 'tags', []))
    if tag in mtags:
        return True
    return getattr(monster, 'kind', '') == tag


# --- Material effective_against / vulnerabilities lookup ---------------------
# Cached once. Populated lazily on first call. Generalizes the old hardcoded
# "silver vs undead, iron vs fey" rules into a data-driven system: every
# material in data/materials/weapons/*.json declares effective_against (tags
# the wielder hits +50%) and vulnerabilities (tags the wielder TAKES extra
# damage from). Gap 4.
_MATERIAL_EFFECTIVE_AGAINST: dict[str, set] = {}
_MATERIAL_VULNERABILITIES:   dict[str, set] = {}


def _load_material_tags() -> None:
    """Read all weapon-capable materials and build the effective/vulnerable maps."""
    if _MATERIAL_EFFECTIVE_AGAINST:
        return  # already loaded
    import json
    import os
    from paths import data_path
    mat_dir = data_path('data', 'materials', 'weapons')
    if not os.path.isdir(mat_dir):
        return
    for fn in os.listdir(mat_dir):
        if not fn.endswith('.json'):
            continue
        with open(os.path.join(mat_dir, fn), encoding='utf-8') as f:
            m = json.load(f)
        mid = m.get('id') or os.path.splitext(fn)[0]
        _MATERIAL_EFFECTIVE_AGAINST[mid] = set(m.get('effective_against', []))
        _MATERIAL_VULNERABILITIES[mid]   = set(m.get('vulnerabilities', []))


def _material_effective_multiplier(weapon, monster) -> float:
    """Return 1.5 if any of weapon's material/damage types target monster tags."""
    if weapon is None:
        return 1.0
    _load_material_tags()
    monster_tags = set(getattr(monster, 'tags', []))
    if not monster_tags:
        return 1.0
    # Check every damage type that's also a known material
    for dt in getattr(weapon, 'damage_types', []):
        eff = _MATERIAL_EFFECTIVE_AGAINST.get(dt)
        if eff and (eff & monster_tags):
            return 1.5
    # Also check explicit weapon.material if not in damage_types
    mat = getattr(weapon, 'material', None)
    if mat:
        eff = _MATERIAL_EFFECTIVE_AGAINST.get(mat)
        if eff and (eff & monster_tags):
            return 1.5
    return 1.0


def _material_wielder_vulnerable(player, monster_attack_tags: list) -> float:
    """Return >1.0 if the player's equipped weapon material is vulnerable to the
    incoming attack's tags. Used for cold-iron-vs-demon-attacks etc."""
    weapon = getattr(player, 'weapon', None)
    if not weapon:
        return 1.0
    _load_material_tags()
    mat = getattr(weapon, 'material', None)
    if not mat:
        return 1.0
    vuln = _MATERIAL_VULNERABILITIES.get(mat)
    if not vuln:
        return 1.0
    if any(t in vuln for t in monster_attack_tags):
        return 1.25  # +25% damage taken
    return 1.0


# Tag/name heuristics used by warhammer's anti_heavy_at_max bonus.
_HEAVY_ARMORED_TAGS = {'construct', 'dragon'}
_HEAVY_ARMORED_NAME_HINTS = (
    'knight', 'paladin', 'samurai', 'cataphract', 'sentinel',
    'guard', 'plate', 'golem', 'juggernaut',
)


def _is_heavy_armored(monster) -> bool:
    """True for monsters whose defining trait is heavy plate / hide armor.
    Used by anti_heavy_at_max (warhammer) and as a proxy where no AC stat exists."""
    tags = set(getattr(monster, 'tags', []))
    if tags & _HEAVY_ARMORED_TAGS:
        return True
    name = (getattr(monster, 'name', '') or '').lower()
    return any(hint in name for hint in _HEAVY_ARMORED_NAME_HINTS)


# Damage type advantage/disadvantage vs monster flags.
# Monster defn can set 'resistances': ['slash'] or 'weaknesses': ['pierce']
def _damage_multiplier(damage_types: list[str], monster) -> float:
    """Return 0.5 for resistance, 1.5 for weakness, 1.0 otherwise.
    If weapon has multiple types, pick the best result across all types.

    Material effective_against now drives this via data (see _load_material_tags).
    The legacy hardcoded silver/iron rules are kept as a safety net for monsters
    whose data files predate the material system."""
    _load_material_tags()
    resistances = getattr(monster, 'resistances', [])
    weaknesses  = list(getattr(monster, 'weaknesses', []))
    tags = set(getattr(monster, 'tags', []))
    # Data-driven material bonuses (silver vs undead, cold_iron vs fey, etc.)
    for dt in damage_types:
        eff = _MATERIAL_EFFECTIVE_AGAINST.get(dt)
        if eff and (eff & tags) and dt not in weaknesses:
            weaknesses.append(dt)
    # Legacy hardcoded fallbacks (kept for safety while the new data lands)
    if 'undead' in tags or 'demon' in tags:
        if 'silver' not in weaknesses:
            weaknesses.append('silver')
    if 'fey' in tags:
        if 'iron' not in weaknesses:
            weaknesses.append('iron')
    mults = []
    for dt in damage_types:
        if dt in weaknesses:
            mults.append(1.5)
        elif dt in resistances:
            mults.append(0.5)
        else:
            mults.append(1.0)
    return max(mults) if mults else 1.0


def player_attack(player, monster, quiz_engine, on_complete, ammo=None):
    """
    Start a math chain quiz for the player attacking a monster.

    on_complete(damage: int, killed: bool, chain: int) is called when the quiz ends.
    Chain 0 (first answer wrong) = MISS (0 damage).
    Uses weapon's base_damage (int) or falls back to rolling weapon.damage (dice string).
    Applies enchant_bonus, ammo damage_bonus, damage type multipliers, and stun chance on hit.
    ammo: optional Ammo item whose damage_bonus is added to base damage.
    """
    weapon = player.ranged_weapon if ammo else player.weapon

    def _callback(result):
        chain = result.score

        # Cow King's Horns (or any armor with chain_bonus): free chain head start
        for slot in getattr(player, 'armor_slots', []):
            if slot and getattr(slot, 'chain_bonus', 0):
                chain += slot.chain_bonus

        # Monster-family tohit_vs_tag mastery (humanoid Anatomist): +N chain
        # rungs when striking a matching-family target. This is the chain
        # equivalent of "+1 to-hit" in a system that has no separate to-hit roll.
        fam_masteries_pre = getattr(player, 'unlocked_monster_class_masteries', {}) or {}
        for _fb_pre in fam_masteries_pre.values():
            if _fb_pre.get('kind') == 'tohit_vs_tag':
                _tag_pre = _fb_pre.get('tag', '')
                _val_pre = int(_fb_pre.get('value', 0) or 0)
                if _tag_pre and _val_pre and _tag_match(monster, _tag_pre):
                    chain += _val_pre

        # Fail-not: Tristan's bow given by Morgan le Fay — never misses.
        # Chain 0 is promoted to chain 1 (minimum hit) so a missed quiz still lands.
        if chain == 0 and weapon and getattr(weapon, 'class_mechanic', '') == 'guaranteed_hit':
            chain = 1

        # Cursed weapon backlash on miss (Tyrfing).
        # Floor at 0 so the player.hp value stays non-negative — downstream
        # code (HUD bars, low-HP buff triggers, is_dead checks) all assume
        # hp >= 0. See bug-bash A7-6.
        if chain == 0:
            if weapon and getattr(weapon, 'cursed_miss_backlash', 0) > 0:
                player.hp = max(0, player.hp - weapon.cursed_miss_backlash)
            on_complete(0, monster.is_dead(), chain)
            return

        if monster.is_dead():
            on_complete(0, True, chain)
            return

        # Base damage: new integer field preferred over legacy dice string
        if weapon and weapon.base_damage:
            base = weapon.base_damage
        elif weapon and weapon.damage:
            base = roll(weapon.damage)
        else:
            base = roll('1d4')

        # Weakened / frozen: halve player attack damage. Both effects
        # describe "attack damage halved" / "encased in ice." Previously
        # NEITHER was wired for the player — applied by 30+ monsters but
        # did nothing.
        if player.has_effect('weakened') or player.has_effect('frozen'):
            base = max(1, base // 2)

        # Mastery hooks (chain-5 unlocks on uniques)
        _mastery = _weapon_mastery(player, weapon)

        # weapon_base_damage_bonus: flat damage add
        if _mastery and _mastery.get('kind') == 'weapon_base_damage_bonus':
            base += int(_mastery.get('value', 0))

        # Ammo damage bonus (ranged shots only)
        ammo_bonus  = ammo.damage_bonus if ammo else 0
        enchant     = weapon.enchant_bonus if weapon else 0
        multipliers = weapon.chain_multipliers if weapon else _DEFAULT_MULTIPLIERS
        mult        = multipliers[min(chain - 1, len(multipliers) - 1)]

        # weapon_chain_mult_bonus: flat add to every chain multiplier
        if _mastery and _mastery.get('kind') == 'weapon_chain_mult_bonus':
            mult += float(_mastery.get('value', 0.0))
        # Musashi quirk: chain-1 uses 2nd multiplier instead of weakest
        if chain == 1 and getattr(player, 'quirk_progress', {}).get('musashi_active'):
            mult = multipliers[min(1, len(multipliers) - 1)]

        # Damage type advantage vs monster resistances/weaknesses
        # Gram (reforged) ignores all resistances
        dtype_mult = 1.0
        if weapon and getattr(weapon, 'ignore_resistances', False):
            dtype_mult = 1.0  # bypass all resistance/weakness checks
        elif weapon:
            # Include weapon material as a damage type so iron weapons
            # trigger "iron" weakness on fey creatures, etc.
            dtypes = list(weapon.damage_types)
            mat = getattr(weapon, 'material', '').lower()
            if mat and mat not in dtypes:
                dtypes.append(mat)
            # Blessed weapons deal holy damage (effective vs undead/demons)
            if getattr(weapon, 'buc', 'uncursed') == 'blessed' and 'holy' not in dtypes:
                dtypes.append('holy')
            dtype_mult = _damage_multiplier(dtypes, monster)

        # Shield bypass: ignore_shield weapons deal full damage through monster's shielded effect
        if not (weapon and weapon.ignore_shield):
            if monster.has_effect('shielded'):
                dtype_mult *= 0.5

        # Critical hit: if weapon has crit_multiplier and chain hits max, apply bonus
        crit = False
        if weapon and weapon.crit_multiplier > 1.0:
            max_c = weapon.max_chain_length or len(weapon.chain_multipliers)
            if chain >= max_c:
                mult *= weapon.crit_multiplier
                crit = True
                # Petrify on crit (Harpe)
                if weapon.petrify_on_crit:
                    current_pet = monster.status_effects.get('petrifying', 0)
                    monster.status_effects['petrifying'] = max(current_pet, 3)

        # weapon_first_hit_crit mastery: guarantee crit on the FIRST hit of a chain
        if chain == 1 and _mastery and _mastery.get('kind') == 'weapon_first_hit_crit' \
                and _mastery.get('value') and weapon:
            mult *= max(1.5, weapon.crit_multiplier)
            crit = True

        # Pre-damage class-mechanic multipliers. Apply to mult before damage
        # is rolled. Several mechanics fire ONLY at max chain (the chain-5
        # payoff identity); some fire on every hit (versatile, master_strike).
        _pre_mech = getattr(weapon, 'class_mechanic', None) if weapon else None
        if _pre_mech and weapon:
            _max_c = weapon.max_chain_length or len(weapon.chain_multipliers)
            _at_max = chain >= _max_c

            # versatile (bastard_sword) — +20% damage when wielded 2H (no shield).
            # Fires on EVERY hit, not just max chain.
            if _pre_mech == 'versatile' and player.shield is None:
                mult *= 1.20

            # master_strike (longsword) — the Meisterhau. At chain 3+, +15%
            # damage representing the diagonal cut that defeats defensive guards.
            if _pre_mech == 'master_strike' and chain >= 3:
                mult *= 1.15

            # AT-MAX-CHAIN damage multipliers
            if _at_max:
                if _pre_mech == 'anti_heavy_at_max' and _is_heavy_armored(monster):
                    mult *= 1.5
                elif _pre_mech == 'armor_pierce_at_max':
                    mult *= 1.35
                elif _pre_mech == 'ignores_all_armor':
                    # heavy_crossbow signature — bypass all resistance.
                    # Sets dtype_mult to 1.0 if resisted, but boosts via mult.
                    if dtype_mult < 1.0:
                        mult *= (1.0 / dtype_mult)
                        dtype_mult = 1.0
                elif _pre_mech == 'ignores_half_armor':
                    # light_crossbow — halve the resistance penalty
                    if dtype_mult < 1.0:
                        dtype_mult = (dtype_mult + 1.0) / 2.0

        # Beowulf quirk: unarmed attacks deal +5 base damage
        if weapon is None:
            unarmed_bonus = getattr(player, 'quirk_progress', {}).get('beowulf_unarmed_bonus', 0)
            base += unarmed_bonus

        # Weakened status: halve base damage before multipliers
        if getattr(player, 'status_effects', {}).get('weakened', 0):
            base = max(1, base // 2)

        # Hero passive: Will to Power — +30% damage when below 30% HP.
        hero_passives = getattr(player, 'hero_passives', set())
        if 'will_to_power' in hero_passives and player.max_hp > 0 and \
                player.hp <= player.max_hp * 0.3:
            mult *= 1.3
        # Hero passive: Witcher Mutations — +20% damage vs monsters (all).
        if 'witcher_mutations' in hero_passives:
            mult *= 1.2
        # Hero passive: Niten Ichi-Ryū (Musashi) — +15% damage when dual-wielding.
        if 'niten_ichi_ryu' in hero_passives and \
                getattr(player, 'ranged_weapon', None) is not None and \
                getattr(player, 'weapon', None) is not None:
            mult *= 1.15
        # Hero buff: crit_buff (Joan of Arc's Standard / Ash's She-Bitch) — next attack crits
        if getattr(player, 'status_effects', {}).get('crit_buff', 0) > 0:
            mult *= 1.5
            # consume one charge by reducing duration; if it reaches 0, status fades naturally
            player.status_effects['crit_buff'] = max(0, player.status_effects['crit_buff'] - 1)
        # Hero buff: berserk — flat +30% damage while active
        if getattr(player, 'status_effects', {}).get('berserk', 0) > 0:
            mult *= 1.3

        # BUC weapon bonus: blessed +1, cursed -1
        buc_bonus = 0
        if weapon:
            wbuc = getattr(weapon, 'buc', 'uncursed')
            if wbuc == 'blessed':
                buc_bonus = 1
            elif wbuc == 'cursed':
                # Hero passive: Diogenes' Cynic Detachment — cursed items don't penalize.
                if 'cynic_detachment' not in getattr(player, 'hero_passives', set()):
                    buc_bonus = -1

        # Chandrahasa: bonus damage when player HP is low
        low_hp_mult = 1.0
        if weapon and getattr(weapon, 'low_hp_damage_bonus', False) and player.max_hp > 0:
            hp_pct = player.hp / player.max_hp
            if hp_pct < 0.5:
                low_hp_mult = 1.0 + (0.5 - hp_pct) * 2.0  # up to 2x at 0% HP

        str_factor = 1.0 + max(0, player.STR - 10) * 0.03

        # weapon_damage_vs_tag mastery: +X% damage when target matches tag
        tag_mult = 1.0
        if _mastery and _mastery.get('kind') == 'weapon_damage_vs_tag':
            tag_val = _mastery.get('value') or {}
            if isinstance(tag_val, dict) and _tag_match(monster, tag_val.get('tag', '')):
                tag_mult = 1.0 + (float(tag_val.get('pct', 0)) / 100.0)

        # Monster-family mastery (chain-5 corpse-id):
        #   damage_vs_tag (dragon/demon/undead/construct/plant/reptile): +N flat
        #   tohit_vs_tag  (humanoid): +N chain bonus (acts as a guaranteed-hit
        #     promotion when chain == 0; otherwise irrelevant — chain length
        #     already drives accuracy via the chain mechanic).
        family_dmg_bonus = 0
        fam_masteries = getattr(player, 'unlocked_monster_class_masteries', {}) or {}
        for _fb in fam_masteries.values():
            _kind = _fb.get('kind')
            _tag = _fb.get('tag', '')
            _val = int(_fb.get('value', 0) or 0)
            if not _tag or not _val:
                continue
            if _kind == 'damage_vs_tag' and _tag_match(monster, _tag):
                family_dmg_bonus += _val

        # round (not int-truncate): chain damage gradient must survive at
        # low base values. With int(), iron sword base=1 gave 1,1,1,1,2
        # across chain levels — invisible progression. round() preserves
        # the half-step damage differences that the chain ladder is designed
        # to deliver.
        damage = max(1, round((base + enchant + ammo_bonus + buc_bonus) * mult * dtype_mult * str_factor * low_hp_mult * tag_mult) + family_dmg_bonus)

        # Empower spell: 3x damage on next hit, then clears
        if player.has_effect('empowered'):
            damage *= 3
            player.status_effects.pop('empowered', None)

        # Dragon scales: massive damage reduction (bypassed by ignore_resistances or player in pit)
        dragon_scales = getattr(monster, 'dragon_scales', 0)
        if dragon_scales > 0 and not getattr(weapon, 'ignore_resistances', False):
            if player.has_effect('in_pit'):
                damage = damage * 4  # devastating underbelly strike from below!
            else:
                damage = max(1, int(damage * (1.0 - dragon_scales)))

        # Sword of Michael vs Abaddon: bonus holy damage
        if weapon and getattr(weapon, 'abaddon_bonus_damage', '') and monster.kind == 'abaddon_destroyer':
            from dice import roll as _ab_roll
            bonus = _ab_roll(weapon.abaddon_bonus_damage)
            damage += bonus

        # Chain-equip passive: death_omen_mark (Cloak of the Morrigan T5).
        # +25% damage against the floor's highest-level monster.
        if getattr(player, '_death_omen_target', None) == id(monster):
            damage = int(damage * 1.25)

        actual = monster.take_damage(damage)

        # Stun mechanic (staves only, or any weapon with stunChance > 0)
        stunned = False
        if weapon and weapon.stun_chance > 0 and actual > 0:
            if random.random() < weapon.stun_chance:
                # Monster makes a resistance roll: bigger monsters resist more.
                # threshold = hp/300 clamped [0.05, 0.95]; roll must BEAT threshold to stun.
                # e.g. 30 HP -> 90% chance, 150 HP -> 50%, 300 HP+ -> 5%
                resist_threshold = min(0.95, max(0.05, monster.max_hp / 300.0))
                if random.random() > resist_threshold:
                    monster.add_effect('paralyzed', 2)
                    stunned = True

        # Bleed mechanic
        if weapon and weapon.bleed_chance > 0 and actual > 0:
            if random.random() < weapon.bleed_chance:
                monster.add_effect('bleeding', 3)

        # Poison mechanic
        poisoned = False
        if weapon and getattr(weapon, 'poison_chance', 0) > 0 and actual > 0:
            if random.random() < weapon.poison_chance:
                monster.add_effect('poisoned', 5)
                poisoned = True

        # Burn mechanic
        burned = False
        if weapon and getattr(weapon, 'burn_chance', 0) > 0 and actual > 0:
            if random.random() < weapon.burn_chance:
                monster.add_effect('burning', 4)
                burned = True

        # Confuse mechanic (Thyrsus-style)
        confused = False
        if weapon and getattr(weapon, 'confuse_chance', 0) > 0 and actual > 0:
            if random.random() < weapon.confuse_chance:
                monster.add_effect('confused', 4)
                confused = True

        # Lifesteal mechanic (Soul Reaver). Mastery: weapon_lifesteal adds % on top.
        healed = False
        lifesteal_pct = float(getattr(weapon, 'lifesteal_percent', 0) or 0)
        if _mastery and _mastery.get('kind') == 'weapon_lifesteal':
            lifesteal_pct += float(_mastery.get('value', 0.0))
        if weapon and lifesteal_pct > 0 and actual > 0:
            heal = max(1, int(actual * lifesteal_pct))
            player.hp = min(player.max_hp, player.hp + heal)
            healed = True

        # weapon_wound_lingers mastery: extend bleeding duration on hit.
        if _mastery and _mastery.get('kind') == 'weapon_wound_lingers' and actual > 0:
            extra = int(_mastery.get('value', 0))
            if extra > 0:
                current = monster.status_effects.get('bleeding', 0)
                monster.status_effects['bleeding'] = max(current, 3) + extra

        # weapon_status_chance mastery: apply an additional on-hit status (e.g. stun)
        if _mastery and _mastery.get('kind') == 'weapon_status_chance' and actual > 0:
            st = _mastery.get('value') or {}
            status = st.get('status')
            chance_pct = float(st.get('pct', 0)) / 100.0
            dur = int(st.get('duration', 2))
            if status and chance_pct > 0 and random.random() < chance_pct:
                current = monster.status_effects.get(status, 0)
                monster.status_effects[status] = max(current, dur)

        # Kill heal mechanic (Excalibur, Achilles's Spear)
        if monster.is_dead() and weapon and getattr(weapon, 'kill_heal_amount', 0) > 0:
            player.hp = min(player.max_hp, player.hp + weapon.kill_heal_amount)
            healed = True

        # Growing power mechanic (Caliburn)
        if monster.is_dead() and weapon and getattr(weapon, 'growing_power', False):
            weapon.kill_count = getattr(weapon, 'kill_count', 0) + 1
            if weapon.kill_count % weapon.kills_to_grow == 0:
                weapon.base_damage += 1

        # Kill max HP bonus (Khopesh of Anubis)
        if monster.is_dead() and weapon and getattr(weapon, 'kill_max_hp_bonus', 0) > 0:
            granted = getattr(weapon, '_max_hp_granted', 0)
            cap = getattr(weapon, 'kill_max_hp_cap', 10)
            if granted < cap:
                bonus = min(weapon.kill_max_hp_bonus, cap - granted)
                player.max_hp += bonus
                player.hp += bonus
                weapon._max_hp_granted = granted + bonus

        # Knockback mechanic (handled by caller via return value; flag via on_complete extra)
        knocked = False
        if weapon and weapon.knockback and actual > 0:
            knocked = True

        petrified = crit and weapon and getattr(weapon, 'petrify_on_crit', False)

        # ---------------------------------------------------------------
        # Class mechanics — fire from template-driven class_mechanic tags
        # (Gap 3). Most check on a successful hit; some on kill or max chain.
        # Heavy weapons rely on these for their "max chain payoff" identity.
        # ---------------------------------------------------------------
        class_mech = getattr(weapon, 'class_mechanic', None) if weapon else None
        if class_mech and actual > 0:
            max_c = (weapon.max_chain_length
                     or len(weapon.chain_multipliers)) if weapon else 5
            at_max = chain >= max_c
            # ---- ALL class-mechanic specials fire at MAX CHAIN ONLY ----
            # (Per developer design call: chain length uniform at 5, all specials
            # gated on max chain regardless of weapon class.)

            # Bleed at max (battleaxe, great_axe via cleave_at_max_plus_bleed)
            if class_mech in ('bleed_at_max', 'cleave_at_max_plus_bleed') and at_max:
                monster.add_effect('bleeding', 4)

            # Stun at max (mace, warhammer-anti-heavy variant, maul)
            if class_mech in ('stun_at_max', 'stun_knockdown_at_max') and at_max:
                # Maul's stun-knockdown is the harder variant (more powerful stun)
                if class_mech == 'stun_knockdown_at_max':
                    resist_thr = min(0.90, max(0.10, monster.max_hp / 250.0))
                    if random.random() > resist_thr:
                        monster.add_effect('paralyzed', 3)
                        stunned = True
                    knocked = True
                else:
                    resist_thr = min(0.95, max(0.05, monster.max_hp / 300.0))
                    if random.random() > resist_thr:
                        monster.add_effect('paralyzed', 2)
                        stunned = True

            # Backstab (dagger) — now requires max chain AND unaware monster
            if class_mech == 'backstab' and at_max:
                _unaware = (monster.has_effect('sleeping')
                            or (getattr(monster, 'ai_pattern', '') == 'ambush'
                                and not getattr(monster, '_aware', False)))
                if _unaware:
                    extra = monster.take_damage(actual)  # apply the same damage AGAIN
                    actual += extra

            # Disarm at max (scimitar, quarterstaff's reach_disarm)
            if class_mech in ('disarm_at_max', 'reach_disarm') and at_max:
                if random.random() < 0.30:
                    monster.add_effect('paralyzed', 1)

            # Concussion at max (club) — heavy skull blow rattles the brain
            if class_mech == 'concussion_at_max' and at_max:
                if random.random() < 0.35:
                    monster.add_effect('confused', 2)
                    confused = True

            # Quick riposte (shortsword) — arms a counter-attack for next turn
            if class_mech == 'quick_riposte' and at_max:
                player.add_effect('riposte_armed', 2)

            # Returning blow (Green Chapel Axe) — beheading-game contract: max-chain
            # blows return to the wielder for half damage. The Green Knight survives
            # decapitation; the bearer pays the price for swinging too hard.
            if class_mech == 'returning_blow' and at_max:
                backlash = max(1, actual // 2)
                player.hp = max(0, player.hp - backlash)

            # Defensive parry (quarterstaff) — at max chain, gain +2 AC for 2
            # turns. The quarterstaff's defensive identity: master fighters
            # used it to time strikes from a position of safety.
            if class_mech == 'defensive_parry' and at_max:
                cur = player.status_effects.get('parry_armed', 0)
                player.status_effects['parry_armed'] = max(cur, 2)

            # Rapid shot (shortbow) — at max chain, fire a second arrow at the
            # same target for half damage. Mongol horse-archer signature speed.
            if class_mech == 'rapid_shot_at_max' and at_max and not monster.is_dead():
                followup = max(1, actual // 2)
                extra = monster.take_damage(followup)
                actual += extra

        # Cleave: max-chain kill triggers AOE to adjacent monsters
        # (greatsword cleave_at_max / great_axe cleave_at_max_plus_bleed)
        _cleave_mech = class_mech in ('cleave_at_max', 'cleave_at_max_plus_bleed')
        _cleave_eligible = _cleave_mech and weapon and chain >= (
            weapon.max_chain_length or len(weapon.chain_multipliers))
        if monster.is_dead() and _cleave_eligible:
            cleave_dmg = max(1, int(actual * 0.5))
            # The adjacent-monster lookup happens at the caller's level (game_combat
            # has the monster list); signal via on_complete kwarg.
            # Caller checks 'cleave_dmg' to apply AoE.
            on_complete(actual, monster.is_dead(), chain, stunned=stunned, knocked=knocked,
                        crit=crit, poisoned=poisoned, burned=burned, confused=confused,
                        petrified=petrified, healed=healed, cleave_dmg=cleave_dmg)
            return

        # Sling ricochet: at max chain, 25% chance to bounce for second hit
        # on a monster adjacent to the original target. Caller handles adjacency.
        _ricochet_dmg = 0
        if class_mech == 'free_stones' and weapon and chain >= (
                weapon.max_chain_length or len(weapon.chain_multipliers)):
            if random.random() < 0.25 and actual > 0:
                _ricochet_dmg = max(1, int(actual * 0.6))
        if _ricochet_dmg:
            on_complete(actual, monster.is_dead(), chain, stunned=stunned, knocked=knocked,
                        crit=crit, poisoned=poisoned, burned=burned, confused=confused,
                        petrified=petrified, healed=healed, ricochet_dmg=_ricochet_dmg)
            return

        on_complete(actual, monster.is_dead(), chain, stunned=stunned, knocked=knocked, crit=crit,
                    poisoned=poisoned, burned=burned, confused=confused, petrified=petrified, healed=healed)

    # Jormungandr quirk: +1 max chain for repeatedly-equipped weapon
    _max_chain = weapon.max_chain_length if weapon else len(_DEFAULT_MULTIPLIERS)
    if _max_chain and weapon:
        if getattr(player, 'quirk_progress', {}).get('jormungandr_weapon_id') == weapon.id:
            _max_chain += 1
    # Chain-equip passive: attack_chain_cap_bonus (Ring of Gawain etc.)
    try:
        from chain_passives import get_attack_chain_cap_bonus
        _max_chain += get_attack_chain_cap_bonus(player)
    except ImportError:
        pass

    quiz_engine.start_quiz(
        mode='chain',
        subject='math',
        tier=weapon.quiz_tier if weapon else 1,
        callback=_callback,
        max_chain=_max_chain,
        wisdom=player.WIS,
        timer_modifier=player.get_quiz_timer_modifier(),
        extra_seconds=getattr(player, 'get_quiz_extra_seconds', lambda s: 0)('math'),
        base_seconds=player.get_quiz_timer('math'),
    )


def apply_knockback(player, monster, dungeon, monsters=None):
    """Push monster one tile away from the player. No-ops if tile is blocked or occupied."""
    dx = monster.x - player.x
    dy = monster.y - player.y
    # Normalize to direction
    nx = (1 if dx > 0 else -1) if dx != 0 else 0
    ny = (1 if dy > 0 else -1) if dy != 0 else 0
    tx, ty = monster.x + nx, monster.y + ny
    if not dungeon.is_walkable(tx, ty):
        return
    if monsters and any(m is not monster and m.alive and is_at_tile(m, tx, ty)
                        for m in monsters):
        return
    monster.x, monster.y = tx, ty


def can_melee_attack(player, monster) -> bool:
    """Return True if the player's equipped weapon can reach the monster."""
    weapon = player.weapon
    reach = weapon.reach if weapon else 1
    if reach < 15:  # melee or polearm
        dx = abs(player.x - monster.x)
        dy = abs(player.y - monster.y)
        return dx <= reach and dy <= reach and not (dx == 0 and dy == 0)
    return False  # ranged weapons handled separately


def can_ranged_attack(player, monster, dungeon) -> bool:
    """Return True if the player has a ranged weapon, ammo, and line of sight."""
    weapon = player.ranged_weapon
    if not weapon or not weapon.requires_ammo:
        return False
    reach = weapon.reach + max(0, player.PER - 10) // 3
    dx = abs(player.x - monster.x)
    dy = abs(player.y - monster.y)
    dist = max(dx, dy)
    if dist > reach:
        return False
    # Check ammo in inventory (skip for infinite-ammo weapons — sling/stones)
    if not getattr(weapon, 'infinite_ammo', False):
        ammo_type = weapon.requires_ammo
        has_ammo = any(
            getattr(i, 'ammo_type', None) == ammo_type
            for i in player.inventory
        )
        if not has_ammo:
            return False
    # Line of sight: check no solid tiles block the path (Bresenham)
    return _line_of_sight(player.x, player.y, monster.x, monster.y, dungeon)


def _line_of_sight(x0, y0, x1, y1, dungeon) -> bool:
    """Bresenham line-of-sight check with corner-cutting prevention.
    Returns True if path is clear (no walls, doors, or obstacles)."""
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy
    cx, cy = x0, y0
    while True:
        if cx == x1 and cy == y1:
            break
        e2 = 2 * err
        step_x = e2 > -dy
        step_y = e2 < dx
        if step_x and step_y:
            # Diagonal step: check BOTH adjacent tiles to prevent corner-cutting.
            # An arrow can't pass through a diagonal gap between two walls.
            adj_x_blocked = not dungeon.is_walkable(cx + sx, cy)
            adj_y_blocked = not dungeon.is_walkable(cx, cy + sy)
            if adj_x_blocked and adj_y_blocked:
                return False  # both corners blocked — no passage
        if step_x:
            err -= dy
            cx += sx
        if step_y:
            err += dx
            cy += sy
        # Check the tile we moved to (skip origin and target)
        if (cx, cy) != (x1, y1):
            if not dungeon.is_walkable(cx, cy):
                return False
    return True


def get_line_tiles(x0, y0, x1, y1) -> list[tuple[int, int]]:
    """Return all tiles on the Bresenham line from (x0,y0) to (x1,y1), excluding origin."""
    tiles = []
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1
    err = dx - dy
    cx, cy = x0, y0
    while True:
        if cx == x1 and cy == y1:
            if (cx, cy) not in tiles:
                tiles.append((cx, cy))
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            cx += sx
        if e2 < dx:
            err += dx
            cy += sy
        if (cx, cy) != (x0, y0) and (cx, cy) not in tiles:
            tiles.append((cx, cy))
    return tiles


def get_cone_tiles(x0, y0, x1, y1, max_range=6) -> set[tuple[int, int]]:
    """Return tiles in a cone from (x0,y0) in the direction of (x1,y1).

    The cone EXTENDS PAST the target to max_range — fire doesn't stop at
    the first thing it hits. The direction is determined by the target, but
    the cone continues through and beyond it.

    Widening with distance:
      - Distance 1-2: just the center line (width 1)
      - Distance 3-4: center + 1 perpendicular on each side (width 3)
      - Distance 5+:  center + 2 perpendicular on each side (width 5)
    Origin tile is excluded.
    """
    dx, dy = x1 - x0, y1 - y0
    dist = max(abs(dx), abs(dy))
    if dist == 0:
        return set()

    # Calculate direction and perpendicular vectors
    length = (dx * dx + dy * dy) ** 0.5
    if length == 0:
        return set()
    dir_x = dx / length
    dir_y = dy / length
    perp_x = -dir_y
    perp_y = dir_x

    # Extend the line PAST the target to max_range by projecting further
    # along the same direction
    far_x = x0 + round(dir_x * max_range)
    far_y = y0 + round(dir_y * max_range)
    line = get_line_tiles(x0, y0, far_x, far_y)

    result = set()
    for i, (tx, ty) in enumerate(line):
        tile_dist = i + 1
        if tile_dist > max_range:
            break
        result.add((tx, ty))

        # Determine spread at this distance
        if tile_dist >= 5:
            spread = 2
        elif tile_dist >= 3:
            spread = 1
        else:
            spread = 0

        for s in range(1, spread + 1):
            result.add((tx + round(perp_x * s), ty + round(perp_y * s)))
            result.add((tx - round(perp_x * s), ty - round(perp_y * s)))

    return result
