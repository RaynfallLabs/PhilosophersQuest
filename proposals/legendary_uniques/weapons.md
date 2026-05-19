# Weapons — Legendary Uniques Proposal

96 weapons. Re-imagined as fresh canvases. The 5-chain treatment is the BASELINE, not the ceiling. Long chains, skyrocket curves, dip curves, per-event procs, per-monster bonuses, failure modes — every weapon should make the player feel like they have the named thing from the myth/lit/history.

Grouped by archetype, not alphabetically. Mythic Exemptions and Code Required summarized at the bottom.

---

## 1. God-Touched

The mythic peaks. These are the named weapons of named gods. The chain caps and damage guardrails bend here — that's the point. A player who finds Mjolnir should feel the storm.

### Excalibur (`excalibur`)

**Lore hook**: Arthur's sword from the lake; the inscription "Take me up; cast me away."

**Mechanic**: Keep current 5-chain `[1.0, 1.5, 2.0, 3.0, 5.0]` — already perfect. Authorial restraint: this is the canonical example of a clean elevated curve. Add a `cast_me_away` proc: at HP ≤ 25%, the next attack drains the weapon's enchant by 1 and triggers `life_save`. Self-sacrificing. One-shot per descent.

**Why legendary**: The blade keeps Arthur alive once, then dims. Same as the myth — he had to give it back.

**Code needed**: `cast_me_away` proc (moderate).

### Mjolnir (`mjolnir`)

**Lore hook**: Thor's hammer; the handle came out short by Loki's sabotage.

**Mechanic**: 10-chain steady ascent `[1.0, 1.2, 1.5, 1.8, 2.2, 2.5, 3.0, 3.5, 4.0, 5.0]`. Stuns 40% per hit baseline. At chain 6+, each hit also chains lightning to a second adjacent foe for 50% damage. Thor doesn't warm up; he just keeps swinging until the storm arrives.

**Why legendary**: The player feels the storm gather. By chain 8 they're killing rooms.

**Code needed**: `chain_lightning_at_chain_n` (moderate).

### Gungnir (`gungnir`)

**Lore hook**: Odin's spear; an oath sworn on its tip is unbreakable; it has never missed.

**Mechanic**: 5-chain `[1.5, 1.8, 2.2, 2.8, 3.5]`, but EVERY hit is guaranteed (cannot miss; ignores miss-rolls and dodge entirely). First hit of chain auto-crits (keep existing blessing). No warm-up — the spear flies true on the first throw.

**Why legendary**: The math goes away. Quiz right, deal damage. No probability layer between the player and the kill.

**Code needed**: `cannot_miss` flag (simple).

### Heracles's Olive-Club (`heracles_club`)

**Lore hook**: Uprooted from Nemean olives, hardened in the lion's furnace.

**Mechanic**: Keep current `[1.0, 1.0, 1.5, 2.5, 4.0]` "Heracles never warms up; he finishes." Add: every chain-5 finisher knocks the target back AND a tile of "trampled earth" persists for 5 turns. Allies stepping there gain +2 STR. The grove regrows after the hero passes.

**Why legendary**: A myth-tier club leaves a mark on the floor.

**Code needed**: `terrain_buff_on_finisher` (complex — new floor-state).

### Sling of David (`sling_of_david`)

**Lore hook**: One stone. Five available. Goliath went down to the first.

**Mechanic**: Skyrocket `[0.2, 0.5, 1.0, 2.5, 8.0]` against any foe with the `giant` tag, or any monster ≥2x player level. Against ordinary mobs, normal `[0.5, 1.2, 2.0, 3.0, 4.5]`. The sling KNOWS who Goliath is.

**Why legendary**: The player picks fights they shouldn't win. The sling rewards it.

**Code needed**: `conditional_chain_curve_vs_tag` (moderate).

### Sword of Michael (`sword_of_michael`)

**Lore hook**: Archangel's flaming sword; cast Lucifer down; will be drawn again at the end of days.

**Mechanic**: Quest-only. Keep current 9-chain `[0.5, 1.2, 2.0, 3.2, 4.8, 6.5, 9.0, 12.0, 16.0]`. This is the only weapon whose chain 9 can one-shot Abaddon. Don't touch it. Add: at chain 7+, the blade ignites every demon in the dungeon (not just the target) — they get a permanent debuff (-25% damage they deal for the rest of the run). Once. Earned by reaching chain 7. The Host has noticed.

**Why legendary**: A chain 7 with Michael's sword *changes the run for every other monster.*

**Code needed**: `global_demon_debuff_proc` (complex). Already mostly hand-coded as quest item; the new piece is the run-wide event.

### Spear of Longinus (`spear_of_longinus`)

**Lore hook**: Pierced Christ's side; healed Longinus's eyes; Charlemagne carried it 47 battles.

**Mechanic**: 7-chain `[0.6, 0.9, 1.2, 1.7, 2.4, 3.2, 4.5]`. Keep +50% vs demons. Add: on any kill, the spear "weeps" — heals wielder 1 HP per remaining max-HP-tens of the slain (a Goliath-class kill heals huge). The relic's wounds heal.

**Why legendary**: Slaying the wicked makes the holy heal — the Charlemagne arc, ten battles long.

**Code needed**: `weep_heal_on_kill_scaled` (simple).

### Sudarshana Chakra (`sudarshana`)

**Lore hook**: Vishnu's spinning discus, forged from the sun's effulgence.

**Mechanic**: Keep `[1.0, 1.3, 1.7, 2.2, 3.4]` 10-chain. Add: the discus "returns" — on chain-5 finisher, the next melee attack on the player misses outright (one-shot ward, refreshes per chain reset). Vishnu's gift cuts the head AND comes back to the hand.

**Why legendary**: The chain-5 doesn't just hit hard; it pays out a free turn of safety.

**Code needed**: `return_to_hand_ward` (moderate).

### Trident of Poseidon (`trident_of_poseidon`)

**Lore hook**: Struck the Acropolis; tried to drown Odysseus for a decade.

**Mechanic**: 8-chain `[0.9, 1.1, 1.4, 1.8, 2.4, 3.0, 3.8, 5.0]`. Add: against any monster with `water` or `cold` tag, base damage is doubled. The sea-god knows his own. Chain-5+ knocks-back leaves a brine puddle (1 turn slow on traversal).

**Why legendary**: Aquatic/cold encounters become trivial. Everything else: still a great spear.

**Code needed**: `damage_double_vs_tag` (simple), `terrain_proc_brine` (moderate, can share with Amenonuhoko).

### Ruyi Jingu Bang (`ruyi_jingu_bang`)

**Lore hook**: 17,550 lb iron pillar; the As-You-Will Cudgel grows to fill heaven and earth.

**Mechanic**: 9-chain `[0.6, 1.0, 1.5, 2.5, 4.0, 4.5, 5.0, 5.5, 6.0]` — the staff GROWS each rung. Reach also expands: chain 1-3 reach 3, chain 4-6 reach 4, chain 7-9 reach 5. Sun Wukong's discipline: by chain 7 you are striking from across the room.

**Why legendary**: The stat sheet changes mid-chain. Players who hit chain 7 can keep distance forever.

**Code needed**: `chain_modulated_reach` (moderate).

### Amenonuhoko (`amenonuhoko`)

**Lore hook**: The Heavenly Jeweled Spear; brine from its tip became the first island of Japan.

**Mechanic**: Keep `[0.7, 1.0, 1.3, 1.6, 2.4]` 8-chain. Add: on kill, drips brine — leaves a 1-tile "primordial pool" that slows enemies entering by 50% for 4 turns and heals the player 1 HP if traversed. (Existing `aoe_slow_on_kill` flag is the seed.) Each kill builds the archipelago.

**Why legendary**: The floor literally fills with creation as the player works through it.

**Code needed**: Already partially via `aoe_slow_on_kill`; extend to terrain (moderate).

### Rod of Moses (`rod_of_moses`)

**Lore hook**: Became a serpent in Pharaoh's court; parted the Red Sea; struck the rock at Horeb.

**Mechanic**: 7-chain `[0.6, 0.9, 1.2, 1.7, 2.4, 3.2, 4.5]`. Each chain rung corresponds to one of the Ten Plagues — chain 3 inflicts boils (slow), chain 5 inflicts darkness (blinded), chain 7 inflicts firstborn (instant-execute if target HP ≤ 15%). Holy mode against evil-tagged.

**Why legendary**: Climbing the chain triggers narratively-named procs. Players quote plagues at the screen.

**Code needed**: `chain_tier_status_table` (moderate).

### Mjolnir Shard (`mjolnir_shard`)

**Lore hook**: A jagged fragment of the storm god's hammer; lightning arcs between its fractures.

**Mechanic**: 6-chain `[0.8, 1.0, 1.2, 1.6, 2.5, 4.5]`. At chain 5+, the static arc — adjacent enemies within 1 tile take 25% splash. The shard remembers being whole.

**Why legendary**: A mid-game tier-2 weapon that suddenly clears rooms once you hit chain 5.

**Code needed**: `adjacent_splash_at_chain_n` (moderate).

### Vel of Murugan (`vel_of_murugan`)

**Lore hook**: Parvati gave it to Murugan; split the demon Surapadman; half became a peacock, half a rooster.

**Mechanic**: 8-chain `[0.6, 0.9, 1.2, 1.7, 2.4, 3.0, 3.8, 4.8]`. Keep +burn proc. Add: every chain-5+ kill against a demon-tagged foe summons a peacock OR rooster (alternating) — a temporary 5-turn ally with 8 HP, base dmg = floor/4. Two halves of the demon, on YOUR side now.

**Why legendary**: Boss fights become summoning rituals. Battlefield control on a divine weapon.

**Code needed**: `summon_on_demon_kill_alternating` (complex).

### Parashu (`parashu`)

**Lore hook**: Shiva gave it to Parashurama; he exterminated the Kshatriyas twenty-one times.

**Mechanic**: 7-chain `[0.9, 1.1, 1.3, 1.6, 2.0, 2.6, 3.4]`. Keep cleave_at_max and +40% vs humanoids. Add: when chain 5+ kill is a humanoid, the chain DOES NOT RESET. Parashurama's penance accumulates. Twenty-one Kshatriyas in a row, if you can answer.

**Why legendary**: A long humanoid-heavy floor becomes a sustained killing arc. No chain reset = unbounded climb.

**Code needed**: `chain_no_reset_on_tagged_kill` (moderate).

### Chandrahas (`chandrahas`)

**Lore hook**: Shiva's gift to Ravana; the Moon's Laughter; returns to Shiva if used for evil.

**Mechanic**: Keep current `[0.2, 0.4, 0.8, 1.4, 3.2]` finesse curve and +35% vs evil. Add: a karma hook. If player karma is negative (current `karma` system), the blade has 5% chance per equip-day to vanish back to Shiva. The myth, mechanized.

**Why legendary**: Evil players lose their best weapon. Players read the lore and feel it.

**Code needed**: `karma_disappear_proc` (moderate; reuses existing karma system).

### Gram (`gram`)

**Lore hook**: Sigurd's reforged blade; cut Fafnir; tasted dragon blood; understood birds.

**Mechanic**: Quest-only. Keep current 9-chain `[0.5, 1.0, 1.5, 2.2, 3.0, 4.0, 5.5, 7.0, 9.0]`. The blade is fine as-is. Add: after first dragon kill with Gram equipped, player gains permanent `understands_beasts` — animal subject quizzes give +5 second timer bonus for the rest of the run. Sigurd's bird-tongue gift, baked into the player.

**Why legendary**: A permanent run-wide buff earned by completing the myth. Players narrate the moment.

**Code needed**: `permanent_subject_timer_buff_after_milestone` (moderate).

### Vulcan's Brand (`vulcans_brand`)

**Lore hook**: Forged in Vulcan's furnace by Cacus; the blade never fully cools.

**Mechanic**: Quest-only. Keep `[0.6, 1.1, 1.6, 2.2, 2.9, 3.7, 4.5]` 7-chain. Add: weapon is permanently "burning" — wielder takes 1 fire damage per 100 turns (background tick). Heat resistance halves it. Mythological cost. The smith's curse is on the wielder, not the foe.

**Why legendary**: A weapon that costs HP to wield, but pays out devastatingly. Players accept the bargain.

**Code needed**: `passive_wielder_tick_damage` (moderate; can share with cursed-blade backlash if generalized).

---

## 2. Cursed / Ill-Omened

These wait. They open weak, hide their nature, and pay out in full when the player has earned the kill. Failure modes are FAIRLY MODEST — the curse expresses itself in design, not bricked runs.

### Tyrfing (`tyrfing`)

**Lore hook**: Forged under duress by Dvalinn and Durin; cursed to kill a man every unsheathing; three kings of the Hervarar line died by it.

**Mechanic**: Keep `[0.2, 0.4, 0.8, 1.4, 2.0]` 8-chain. Add: every TIME the player draws Tyrfing (sheath -> unsheath), the next attack auto-crits AND deals +50% damage. But ALSO: if the player puts Tyrfing away without a kill that combat, they suffer `cursed_miss_backlash` for 5 turns (already partially flagged). The blade demands blood per drawing.

**Why legendary**: The economy of unsheathing matters. Players plan their fights around when to draw.

**Code needed**: `unsheath_first_strike_proc` + extend existing `cursedMissBacklash` to trigger on sheath-without-kill (moderate).

### Stormbringer (`stormbringer`)

**Lore hook**: Black runesword forged by the Lords of Chaos; Elric of Melnibone leaned on it and lost everyone.

**Mechanic**: Keep current `[0.5, 0.85, 1.2, 1.7, 2.4]`, 25% lifesteal, berserk-on-equip. Add the `betrays_at_low_hp` flag (already in JSON): at player HP ≤ 15%, 25% chance per swing to instead strike the NEAREST ALLY (pet, summon, NPC) for full damage. The runesword chooses its meal. Existing `selects_wielder` becomes a real proc — the weapon refuses to be unequipped while attuned.

**Why legendary**: The cost is real. Pet-builds become risky with Stormbringer. Players read the Elric saga.

**Code needed**: `betray_at_low_hp_proc` (moderate), `refuse_unequip_while_attuned` (simple).

### Mistilteinn (`mistilteinn`)

**Lore hook**: The Mistletoe Sword — Frigg considered mistletoe too small to swear against, and Loki killed Baldur with a dart of it.

**Mechanic**: Keep `[0.2, 0.4, 0.8, 1.4, 2.4]`, ignore_resistances. Add: against any monster with ANY resistance, the chain values DOUBLE on the LAST hit only. The thing nobody guards against finds the gap. Plus: against monsters with NO resistances (low-tier mooks), Mistilteinn does -50% damage. The blade only cares about Baldurs.

**Why legendary**: The weapon picks its prey. Bosses with resistance-stacking are its true diet.

**Code needed**: `damage_double_vs_resistant_at_max_chain` + `damage_reduce_vs_unresistant` (moderate).

### Laevateinn (`laevateinn`)

**Lore hook**: Loki cut it at Hel's gates; will destroy Vidofnir, the rooster whose crow begins Ragnarok.

**Mechanic**: Keep `[0.2, 0.4, 0.8, 1.4, 2.4]`. Add: at chain 5 against a boss, a "doom rune" inscribes — boss takes 5% max-HP per turn as fire damage for the rest of the fight. Preventing Ragnarok is bureaucratically complicated. Slow-burn boss-killer.

**Why legendary**: Bosses don't survive 20 turns once the doom is written.

**Code needed**: `boss_doom_dot_at_chain_5` (moderate).

### Soul Reaver (`soul_reaver`)

**Lore hook**: Whispers between kills; grows heavier against the innocent.

**Mechanic**: Keep `[0.2, 0.55, 1.0, 1.8, 3.0]` and 30% lifesteal — these are good. Add: if player kills a non-hostile/non-monster NPC, the blade's `kills_to_grow` counter ACCELERATES — the next combat hit auto-crits. Reaver is fed by innocence; refusing to feed it is the choice. (No karma cost forced — the player picks.)

**Why legendary**: A genuine moral lever in combat. Players who pick the dark path feel it pay out. Players who don't, don't.

**Code needed**: `growth_on_innocent_kill` (moderate; reuses karma hook).

### Cronus's Scythe (`cronus_scythe`)

**Lore hook**: Gaia gave it to Cronus; he castrated his father with it; from the blood sprang the Giants and Aphrodite.

**Mechanic**: Keep `[0.2, 0.4, 0.8, 1.4, 1.9]` 7-chain finesse. Add: chain-5 kill against a humanoid male spawns a 1-HP "Giant" minion ally for 3 turns (chance 25%). The myth, in miniature. Lifesteal already present is fine.

**Why legendary**: Mythologically resonant proc. Players narrate.

**Code needed**: `spawn_giant_on_male_humanoid_kill` (complex — requires gender tags on humanoids, or just "humanoid + bipedal").

### Gae Dearg (`gae_dearg`)

**Lore hook**: The Red Spear of Diarmuid; wounds it deals cannot heal.

**Mechanic**: 8-chain `[0.2, 0.4, 0.8, 1.4, 2.4, 3.2, 4.2, 5.5]`. Keep the wound-lingers blessing. Add: targets damaged by Gae Dearg cannot be healed by spell, potion, or regen for 10 turns. Bosses unfairly hard? Strip their regen. The mercy that the yellow spear gave is here refused.

**Why legendary**: Healing-stacked bosses melt. Players read about Diarmuid's choice.

**Code needed**: `apply_heal_block_debuff` (moderate).

### Khopesh of Anubis (`khopesh_of_anubis`)

**Lore hook**: The priest's blade of the embalming rites — symbolic severance of what cannot be allowed onward.

**Mechanic**: Keep `[0.2, 0.4, 0.8, 1.4, 3.0]`. Add: chain-5 kill against an evil-aligned humanoid triggers a "weighing" — player gains 1 permanent max HP (cap +10, existing `kill_max_hp_cap`). Anubis's scale. Already mostly coded; just elevate the flavor with a screen message: "Your heart is lighter than the feather."

**Why legendary**: Run-spanning permanent growth tied to moral choice (killing evil = right).

**Code needed**: Already coded; add the flavor message (simple).

### Pelops Sword (`pelops_sword`)

**Lore hook**: Pelops took Pisa by chariot-race bribery; the curse passed to Atreus and Mycenae bled three generations.

**Mechanic**: Keep `[0.5, 0.85, 1.0, 1.45, 2.0]`. Add: the `cursed_lineage` flag (already in JSON) triggers on EQUIP — player loses 1 STR but gains 2 max HP. Every floor descent has 5% chance of "House of Atreus" event: a hostile NPC named after a Mycenaean spawns and attacks. The curse keeps coming.

**Why legendary**: Reading the lore reveals the events. Players make connections.

**Code needed**: `cursed_lineage_descent_event` (moderate).

### Cain's Club (`cain_club`)

**Lore hook**: The first murder weapon. Talmudic/Quranic tradition. The mark on Cain protected him but not from memory.

**Mechanic**: Keep `[0.5, 0.85, 1.0, 1.45, 2.0]`. Add: equipping Cain's Club marks the player — monsters of the `beast` tag actively SEEK the player from 2 tiles further than normal sight. The mark of Cain is on you. The cudgel is plain; the lore is the mechanic.

**Why legendary**: A weapon that changes monster AI passively. Lore-pure.

**Code needed**: `equipped_monster_aggro_radius_modifier` (moderate).

### Hrunting (`hrunting`)

**Lore hook**: Unferth lent it to Beowulf; it failed once, against Grendel's mother. Its single exception.

**Mechanic**: Keep `[0.7, 1.0, 1.3, 1.6, 2.2]`. Add: Hrunting CANNOT BREAK CHAIN — even on a wrong quiz answer, the chain holds at the previous rung instead of resetting. ONE TIME PER FLOOR. The poem's promise: never failed any man who grasped it. Then the one exception remembers, and the next failure resets normally.

**Why legendary**: A safety net that activates exactly once per descent. Players save it for the boss room.

**Code needed**: `one_shot_chain_save_per_floor` (moderate).

### Whisperer (`fragarach_the_whisperer`)

**Lore hook**: The silent companion to Fragarach. Present at seven significant deaths. Twice present at the survival of one.

**Mechanic**: Keep `[0.2, 0.4, 0.8, 1.4, 3.2]` 10-chain. Add: the wielder takes -50% sound radius (monsters don't hear footsteps as far). The Whisperer doesn't ring — neither do you. Stealth synergy.

**Why legendary**: A stealth weapon that actually changes stealth. Player builds around it.

**Code needed**: `equipped_sound_radius_modifier` (simple if sound radius exists; moderate if it doesn't).

### Chandrahasa (`chandrahasa`)

**Lore hook**: The Laughing Moon — Shiva's gift to Ravana; grows more dangerous as wielder's life fades.

**Mechanic**: Keep `[0.2, 0.4, 0.8, 1.4, 2.4]`. Add (refining existing `low_hp_damage_bonus`): at player HP ≤ 50%, all chain multipliers +50%. At HP ≤ 25%, all multipliers +100%. The blade laughs louder. Cap at +100% so it doesn't trivialize.

**Why legendary**: Desperation-build players make Chandrahasa their main weapon and intentionally walk wounded.

**Code needed**: Extend existing `low_hp_damage_bonus` to tiered (simple).

### Sword of Damocles (`sword_of_damocles`)

**Lore hook**: A blade suspended above a tyrant's throne by a single horsehair.

**Mechanic**: Keep current `[0.3, 0.9, 1.4, 0.6, 2.4]` 7-chain dip curve (chain-4 = 0.6 is the horsehair almost snapping). Add: every chain BUILDS toward "the fall" — after 10 successful chains without ever breaking, the NEXT chain-1 attack is an auto-kill on any non-boss. The sword finally falls. Counter resets on use. The Damoclean payoff is rare but devastating.

**Why legendary**: Players track the counter mentally. The kill, when it comes, feels earned.

**Code needed**: `damoclean_counter_auto_kill` (moderate).

---

## 3. Royal / Inheritance

Steady, noble, reliable. These don't bend the rules — they raise the floor. The chain is a king's progress: dignified, measured, undeniable.

### Anduril (`anduril`)

**Lore hook**: The Flame of the West, reforged from Narsil's shards; the blade that cut the Ring from Sauron's hand.

**Mechanic**: Keep current `[0.7, 1.0, 1.3, 1.8, 2.5]` — perfect signature curve. Authorial restraint applies. Keep undead_bonus 2.5x, fear_aura on equip, ignore_resistances. Add: against any evil-tagged monster at HP ≤ 30%, the next strike auto-executes. The Heir of Elendil finishes what he started.

**Why legendary**: The fear aura already exists. The execute is the moment the Paths of the Dead remember.

**Code needed**: `execute_low_hp_tagged` (simple).

### Joyeuse (`joyeuse`)

**Lore hook**: Charlemagne's coronation sword; changed colour thirty times a day; dazzled enemies before the first blow.

**Mechanic**: Keep `[0.4, 0.7, 1.0, 1.6, 2.4]` 10-chain. Keep confuse proc. Add: at the START of every combat, Joyeuse shines — all enemies within 3 tiles must save vs WIS or be confused for 1 turn (one-shot per combat). The dazzle before the duel.

**Why legendary**: Initiative matters. Joyeuse-wielders are always the ones moving first.

**Code needed**: `combat_start_aoe_confuse` (moderate).

### Curtana (`curtana`)

**Lore hook**: The Sword of Mercy; the angel broke the tip before Ogier could kill Charlemagne's son. Mercy is the lesser blade.

**Mechanic**: Keep `[1.0, 1.2, 1.4, 1.6, 1.8]` 8-chain. Add: on any kill, the player may CHOOSE to spare instead — the monster flees and the player gets +1 max HP (cap +5 per floor). The mercy mechanic. Reading the lore unlocks the choice; using it grants the bonus. Lore-as-tutorial.

**Why legendary**: A weapon that rewards NOT killing. Players who read the inscription understand.

**Code needed**: `spare_kill_choice` (moderate).

### Durendal (`durendal`)

**Lore hook**: Roland's sword; saint-relics in the hilt; he struck the stone three times rather than let it fall to the Saracens.

**Mechanic**: Keep `[0.7, 1.0, 1.3, 1.6, 2.0]` 9-chain, ignore_shield, +35% vs evil, blessed-on-equip. Add: Durendal CANNOT BE BROKEN. Other weapons can be sundered (existing or planned mechanic); Durendal is exempt. The stone broke; the sword did not.

**Why legendary**: The phrasing matters. Players reading the description say "of course."

**Code needed**: `weapon_indestructible` flag (simple — even if sundering isn't yet in, the flag is future-proofing).

### Caliburn (`caliburn`)

**Lore hook**: The sword in the stone — distinct from the lake-gift Excalibur; earned, not given.

**Mechanic**: Keep `[1.0, 1.3, 1.7, 2.1, 2.4]` 9-chain. Keep `growingPower`/`killsToGrow`. Add: every 10 kills, base damage +1 PERMANENT (cap +5). The sword earns its edge as the wielder does. Already partially designed; just commit to the cap.

**Why legendary**: Run-length progression on a single weapon. Players root in.

**Code needed**: Already designed; just cap at +5 and persist (simple).

### Caladbolg (`caladbolg`)

**Lore hook**: Fergus mac Roich's greatsword; cut the tops off three hills with one sweep.

**Mechanic**: Keep `[0.9, 1.1, 1.3, 1.6, 2.0]` 8-chain. Add: chain-5 cleaves — hits all 3 tiles in front of the wielder, full damage to primary, 50% to secondary, 50% to tertiary. Three hills, one sweep. The class_mechanic for cleave already exists; this is the specific implementation.

**Why legendary**: Crowd control payoff for the chain. Hallway cleaving.

**Code needed**: `cleave_3_tile_at_chain_5` (moderate; reuses cleave logic).

### Zulfiqar (`zulfiqar`)

**Lore hook**: Bifurcated tip; "There is no sword but Zulfiqar, no hero but Ali."

**Mechanic**: Keep `[1.0, 1.3, 1.7, 2.1, 2.5]`, +35% vs demon+undead, ignoreShield. Add: every hit strikes TWO targets if available within 1 tile of primary (50% damage to secondary). Two lives, one thrust. Permanent twin-cut.

**Why legendary**: A perpetual cleave on every swing, not just chain-max. Crowd weapon.

**Code needed**: `every_hit_secondary_target` (moderate).

### Pharaoh's Crook (`pharaohs_crook`)

**Lore hook**: The symbol of pharaonic authority — the shepherd's duty to guide and protect.

**Mechanic**: Keep `[1.0, 1.3, 1.6, 1.9, 2.3]`. Keep heroism-on-equip and stun chance. Add: when wielded, friendly NPCs and pets within 5 tiles gain +1 STR (encouraging the flock). The crook leads.

**Why legendary**: Pet-build players adopt the crook. The shepherd metaphor delivers.

**Code needed**: `equipped_ally_aura_buff` (moderate; reusable for other "command" weapons).

### Shamshir-e Zomorrodnegar (`shamshir_e_zomorrodnegar`)

**Lore hook**: Solomon's emerald scimitar; used to command djinn in building the Temple; an administrative tool.

**Mechanic**: Keep `[0.7, 1.0, 1.4, 2.0, 3.2]`. Keep +40% vs demon. Add: chance to BIND on chain-5 kill of a demon — the slain demon becomes a 5-turn ally (50% chance). Solomon's labor management. Reuses the Vel of Murugan summon proc.

**Why legendary**: Building a demon army on a holy weapon. Players quote Ecclesiastes.

**Code needed**: Shared with Vel — `summon_demon_ally_on_kill` (complex; one of the shared mechanics).

### Chrysaor (`chrysaor`)

**Lore hook**: Sprang from Medusa's neck with Pegasus; founded a western kingdom under Geryones; never tarnishes.

**Mechanic**: Keep `[1.0, 1.3, 1.7, 2.1, 2.4]` 9-chain. Add: Chrysaor cannot tarnish — its enchant level never decreases (potions of unenchantment, rust monsters, etc. don't work on it). Permanently +max_enchant. Authorial restraint on the chain; the mechanic is durability.

**Why legendary**: A small but real promise. The gold sword stays gold.

**Code needed**: `weapon_immune_to_enchant_loss` (simple).

### Glamdring (`glamdring`)

**Lore hook**: Foe-Hammer, the orc-cleaver, forged in Gondolin; glows blue when orcs are near.

**Mechanic**: Keep `[0.7, 1.0, 1.3, 1.8, 2.5]`, +40% vs humanoid, burn_chance. Keep `glows_near_orcs` (already in JSON). Add: when glow is active (orcs in sight), the sword preempts — the wielder gets +2 initiative for the combat. Gandalf in Moria.

**Why legendary**: The glow tells the player something AND does something. Lore-pure.

**Code needed**: `glow_initiative_buff` (moderate; the glow is already flagged).

### Aiglos (`aiglos`)

**Lore hook**: Snow-point, the spear of Gil-galad; pierced even Sauron's hand at the Last Alliance; the wielder burned to ash but the spear endured.

**Mechanic**: Keep `[0.8, 1.1, 1.4, 1.8, 2.4]`. Keep freeze_chance 25%. Add: Aiglos never warms in the hand — total immunity to fire/burn-status on the WIELDER while equipped. Sauron's flame did nothing.

**Why legendary**: Hard counter to fire enemies. Dragon floors become viable for melee.

**Code needed**: `wielder_status_immunity` (simple; reusable).

### Hofud (`hofud`)

**Lore hook**: Heimdall's sword; the watcher who hears wool growing.

**Mechanic**: Keep `[0.5, 0.85, 1.0, 1.45, 2.0]` clean curve. Keep first-hit auto-crit. Add: wielder gets +2 PER while equipped. The watcher's gift. Hofud is the only "stat-passive" weapon; this is the player-emotional moment when they realize equipping it gives them sight.

**Why legendary**: Stat boost on a weapon is rare — and Hofud's lore demands sight.

**Code needed**: `wielder_per_passive` (simple; reusable for similar items).

---

## 4. Hero's Personal

The named blade of a specific hero. These curves often follow the hero's character — Cu Chulainn's confidence, Robin Hood's patience, Achilles's grief.

### Gae Bolg (`gae_bulg`)

**Lore hook**: Cu Chulainn's spear, thrown with the foot; thirty barbs opened in the wound.

**Mechanic**: Keep `[1.0, 1.3, 1.6, 2.0, 2.5]` 8-chain. Confidence opener (1.0x already a kill). Add: chain-3 kill triggers the "foot-throw" — the spear flies to a second target up to 5 tiles away for 50% damage. Cu Chulainn's signature move. Cannot be removed without killing the spear's target (existing wound-lingers blessing covers this).

**Why legendary**: A ranged option on a melee spear, lore-justified.

**Code needed**: `secondary_target_thrown_at_chain_3` (moderate).

### Fragarach (`fragarach`)

**Lore hook**: The Answerer; Manannan mac Lir's blade; Lugh carried it; no armor could stop it; no man could move once it was held to his throat.

**Mechanic**: Keep `[1.0, 1.3, 1.7, 2.1, 2.5]` 9-chain. Keep first-hit auto-crit and ignore_shield. Add: held in front of any humanoid for 1 turn (rest action while wielding Fragarach toward target), the target FREEZES for 3 turns. The Answerer compels truth. Once per combat.

**Why legendary**: Non-combat utility. The blade resolves encounters without violence.

**Code needed**: `compel_humanoid_freeze_action` (moderate).

### Achilles's Spear (`achilles_spear`)

**Lore hook**: Hephaestus forged it; the rust from its tip cured the very wound it made (Telephus).

**Mechanic**: Keep `[0.7, 1.0, 1.3, 1.6, 2.3]` 8-chain, kill_heal 15. Add: every chain-5 kill, the spear's rust grows — once per floor, can be "scraped" (rest action) to produce a healing potion (heals 25% max HP). The Telephus myth made into a mechanic.

**Why legendary**: A weapon that PRODUCES consumables. Long-runs benefit hugely.

**Code needed**: `weapon_produces_potion_on_threshold` (moderate).

### Hunt Captain's Sword (`hunt_captains_sword`)

**Lore hook**: Taken from the captain of the Wild Hunt; phases between this world and the spectral realm.

**Mechanic**: Quest-only. Keep current 8-chain `[0.5, 1.0, 1.8, 2.8, 4.0, 5.5, 7.5, 10.0]` — strong skyrocket. Add: at chain 6+, attacks bypass terrain (can hit through walls one tile thick). The blade phases. The Wild Hunt rides through stone.

**Why legendary**: The chain-6 unlocks a tactical option no other weapon has.

**Code needed**: `chain_phase_through_wall` (complex).

### Oathkeeper (`oathkeeper_sword`)

**Lore hook**: A young man carried it down, "VALE" on the crossguard. He didn't come back. The blade is still sharp — someone maintained it with love.

**Mechanic**: Quest-only. Keep `[0.5, 1.0, 1.8, 2.8, 4.0, 5.5]` 6-chain. Add: when the player's pet is alive and adjacent, +1 chain multiplier at every rung. The young man's promise to whoever inherited the blade. The lore is the mechanic — care for what walks beside you.

**Why legendary**: Pet-builds get a clear best-weapon. The flavor demands it.

**Code needed**: `adjacent_pet_buff` (moderate).

### Penitent's Blade (`penitents_blade`)

**Lore hook**: A dark iron dagger carried for twenty years by a man who used it to kill. The blade drinks blood as though balancing a ledger.

**Mechanic**: Quest-only. Keep current `[0.5, 1.2, 2.0, 3.5, 5.0, 7.0]` 6-chain finesse skyrocket. Keep 15-25% lifesteal. Add: every 100 kills with the Penitent's Blade, the player's karma improves by +1 (caps at 0 — the blade can't make a wicked man righteous, only balance the ledger). The myth, mechanized.

**Why legendary**: A weapon as moral practice. Players engaged with the karma system reward themselves through use.

**Code needed**: `kill_count_karma_adjust` (moderate; reuses existing karma).

### Atalanta's Bow (`atalanta_bow`)

**Lore hook**: The huntress raised by bears; drew first blood on the Calydonian Boar.

**Mechanic**: Keep `[0.2, 0.55, 1.0, 1.8, 3.0]` finesse skyrocket. Keep first-blood/first-hit auto-crit. Add: against any enemy at full HP (untouched this combat), all chain multipliers +50%. First blood. Same as the myth.

**Why legendary**: Open-combat play. Rewards the first arrow before the rest.

**Code needed**: `damage_bonus_vs_full_hp` (simple).

### Bellerophon's Lance (`bellerophon_lance`)

**Lore hook**: Tipped with lead; melted in the Chimera's throat; the molten metal did the killing.

**Mechanic**: Keep `[0.75, 0.9, 1.0, 1.3, 1.75]`. Keep burn_chance + beast_bonus. Add: against any FIRE-DAMAGING enemy (basilisks, dragons, fire imps), Bellerophon's Lance does +100% damage. The lead melts in their fire and chokes them. Self-defeating elemental weapon.

**Why legendary**: Anti-dragon spec. Players save Bellerophon for the moment.

**Code needed**: `damage_bonus_vs_fire_dealer` (moderate; needs fire-damage-source tag on monsters).

### Hector's Javelin (`hector_javelin`)

**Lore hook**: The bronze-headed javelin of Hector, breaker of horses; bent on Ajax's shield-boss; felled Patroclus.

**Mechanic**: Keep `[0.75, 0.9, 1.0, 1.3, 1.75]`. Keep bleed_chance 0.25. Add: throws — once per combat, the javelin can be thrown (consumes 1 chain rung, ranged 4 tiles, full damage). Returns at end of combat unless the throw missed (then must be retrieved from the floor tile). The Iliad's spear-throwing duel.

**Why legendary**: Range option on a melee spear. Tactical variety.

**Code needed**: `throwable_weapon_proc` (complex — spawning weapon on floor, retrieval).

### Meleager's Boar-Spear (`meleager_spear`)

**Lore hook**: Ash-shafted; pinned the Calydonian Boar that Artemis sent.

**Mechanic**: Keep `[0.75, 0.9, 1.0, 1.3, 1.75]`. Keep +35% vs beast, bleed 0.3. Add: chain-5 kill of a beast triggers "the hunt" — for 5 turns, all beast-tagged monsters in sight are revealed (mini-map). The Calydonian Hunt assembled at Meleager's word.

**Why legendary**: Information advantage. A scout-weapon for beast levels.

**Code needed**: `reveal_tag_on_chain_5_kill` (moderate).

### Setanta's Hurley (`cuchulainn_hurley`)

**Lore hook**: Before he was Cu Chulainn, he was Setanta who killed Culann's hound with a hurling ball and a stick.

**Mechanic**: Keep `[0.5, 0.85, 1.0, 1.45, 2.0]`. Keep +damage and knockback. Add: against any monster with `dog` or `hound` subtype, base damage is doubled AND chain values +0.5. The myth's specificity rewarded.

**Why legendary**: A starter weapon with a hyper-specific killing edge. Player remembers Setanta.

**Code needed**: `damage_double_vs_subtype` (simple; reuses existing tag system).

### Mwindo's Conga-Scepter (`mwindo_axe`)

**Lore hook**: Hero of the Banyanga epic; born speaking; born with this in his hand; brought his uncles back from the dead.

**Mechanic**: Keep `[0.5, 0.85, 1.0, 1.45, 2.0]`. Keep `kill_heal_amount` 2. Add: once per floor, can resurrect a dead pet (consumes the floor's "Mwindo's blessing" charge). The conga-scepter healed and woke and worked as a flyswatter; let it wake the dead.

**Why legendary**: Pet-build players have a panic button. African mythology represented.

**Code needed**: `resurrect_pet_proc` (complex).

### Cadmus Sword (`cadmus_sword`)

**Lore hook**: Cadmus slew Ares's water-dragon at Thebes; sowed the dragon's teeth and the Sown Men sprang up armed.

**Mechanic**: Keep `[0.5, 0.85, 1.0, 1.45, 2.0]`. Keep +35% vs dragon, dragon_bonus 1d8. Add: after every dragon kill with Cadmus, the next combat starts with a "Sown Man" ally (5 HP, dies in 5 turns). The teeth in the furrow.

**Why legendary**: Dragon kills produce summons. The myth, faithful.

**Code needed**: `summon_after_specific_kill_tag` (moderate; shared with Vel/Shamshir).

### Theseus's Club (`theseus_club`)

**Lore hook**: Bronze club taken from Periphetes the brigand; Theseus carried it through the labyrinth.

**Mechanic**: Keep `[0.5, 0.85, 1.0, 1.45, 2.0]`. Keep stun_chance 0.3. Add: while wielding Theseus's Club, the player can never be lost — the dungeon map auto-reveals adjacent unexplored tiles. The thread of Ariadne, mechanized as wayfinding.

**Why legendary**: Navigation aid. Players unconsciously feel safer.

**Code needed**: `equipped_auto_reveal_adjacent` (simple).

### Akinakes of Acrisius (`akinakes_acrisius`)

**Lore hook**: Acrisius locked his daughter in a bronze tower; Perseus killed him anyway by accidental discus throw.

**Mechanic**: Keep `[0.2, 0.55, 1.0, 1.8, 3.0]` finesse skyrocket. Keep `prophecy_blade` flag (already in JSON). Add: at start of every run, "the prophecy" — a randomly-chosen enemy class is declared by the blade. That class's monsters take +50% damage from the Akinakes for the run. The blade outlasted its king's prophecy.

**Why legendary**: Personalized run-modifier on a low-tier weapon. Roll-dependent build.

**Code needed**: `run_start_prophecy_buff` (moderate).

### Bow of Rama (`bow_of_rama`)

**Lore hook**: Rama bent Shiva's bow to win Sita's hand; his dharma-guided arrows killed Ravana.

**Mechanic**: Keep `[0.5, 1.0, 1.8, 2.8, 4.0]` skyrocket. Keep +40% vs evil, +demon effectiveness. Add: at chain 5 against an evil-tagged target, the arrow is "dharma-guided" — auto-hits, ignores all defense. The arrow that found Ravana.

**Why legendary**: The skyrocket payoff hits, period. Players save the chain-5 for bosses.

**Code needed**: `dharma_guided_chain_5_vs_tag` (moderate).

### Robin Hood's Longbow (`robin_hoods_longbow`)

**Lore hook**: Robin of Loxley; split an arrow at two hundred paces; struck from the shadows.

**Mechanic**: Keep `[0.5, 0.7, 0.9, 1.1, 2.3]` 6-chain dip-then-climb. Keep auto-crit first hit. Add: if the player is `invisible`, `stealthed`, or shooting from outside the target's sight cone, base damage +100%. Robin's specialty.

**Why legendary**: Stealth-build players have an answer. Rangers build around it.

**Code needed**: `stealth_damage_bonus` (moderate; needs stealth detection logic).

### Fail-not (`fail_not`)

**Lore hook**: Tristan's bow, gift of Morgain le Fay; arrows in duty fly true, in anger miss.

**Mechanic**: Keep `[0.5, 0.7, 0.9, 1.1, 2.2]` 10-chain. Keep guaranteed_hit class_mechanic. Add: cannot miss against any enemy that has not yet attacked the player this combat. Tristan's dutiful arrows. After enemy attacks (player has taken damage = "anger"), miss rolls return.

**Why legendary**: Opener weapon. Strike before the strike, and you cannot fail.

**Code needed**: `cannot_miss_before_player_takes_damage` (moderate).

### Kusanagi-no-Tsurugi (`kusanagi`)

**Lore hook**: Cut the grass and redirected the wind when Yamato Takeru was surrounded by flame.

**Mechanic**: Keep `[0.4, 0.7, 1.0, 1.6, 2.4]` 9-chain finesse. Keep 25% slow on hit. Add: when player is surrounded (3+ adjacent enemies), Kusanagi auto-crits and knockback is doubled. The grass-cutter's escape.

**Why legendary**: A panic button on a finesse blade. Player feels Yamato Takeru's moment.

**Code needed**: `surrounded_proc_bonus` (moderate; needs adjacency check).

### Spear of Lugh (`spear_of_lugh`)

**Lore hook**: Four Treasures of the Tuatha De; submerged in poison to keep it from igniting; Lugh killed Balor of the Evil Eye through the eye.

**Mechanic**: Keep `[0.9, 1.1, 1.4, 1.8, 2.4]` 9-chain heavy. Keep burn_chance 0.3, ignoreShield. Add: against any monster with `eye` or `gaze` attack type (basilisks, beholders, evil-eye archetype), the Spear of Lugh deals +200% damage and ignores any reflection/gaze mechanic. The myth, point-for-point.

**Why legendary**: Hard counter to gaze-based monsters. Cataloged specificity.

**Code needed**: `damage_bonus_vs_attack_type` (moderate; needs gaze tagging on monsters).

### Gandiva (`gandiva`)

**Lore hook**: Arjuna's divine bow; one hundred strings; killed 100,000 in the Kurukshetra War; Krishna delivered 18 chapters to make him pick it up.

**Mechanic**: Keep `[0.9, 1.1, 1.4, 1.8, 2.4]` 9-chain. Add: at chain 5, Gandiva fires the "hundred strings" — splits into 3 arrows hitting up to 3 targets in line of sight. Long bow, mass-target. The bow doesn't tire.

**Why legendary**: A volley weapon on chain-5. The myth's scope reflected.

**Code needed**: `multi_arrow_at_chain_5` (moderate).

### Brisingr (`brisingr`)

**Lore hook**: Old Norse for "fire"; sword in a Gotland mound, blade still warm centuries later; metallurgists who examined it published a paper that vanished.

**Mechanic**: Keep `[0.6, 0.9, 1.2, 1.7, 2.4]`. Keep burn_chance 0.35. Add: at chain 5 against a cold-tagged enemy, instant kill if target HP ≤ 40%. Brisingr's preferred meal. Otherwise just a strong burning sword.

**Why legendary**: Cold-floor specialist. Players carry it down to the ice levels.

**Code needed**: `execute_at_chain_5_vs_tag_low_hp` (moderate; reusable execute logic).

### Zireael (`zireael`)

**Lore hook**: Swallow, the witcher's blade — Esterhazy of Mahakam made it for a girl with Elder Blood.

**Mechanic**: Quest-only. Keep `[0.4, 0.7, 1.0, 1.6, 2.8]` 6-chain. Add: the wielder can take one extra move action per turn if they killed something the previous turn. Speed-of-Ciri. Limited to once per turn.

**Why legendary**: An action-economy weapon. Speed-build payoff.

**Code needed**: `extra_action_after_kill` (complex).

### Gae Bolg Fragment (`gae_bolg_fragment`)

**Lore hook**: A splinter of Cu Chulainn's spear — bone-barbed, lesser, but still remembers.

**Mechanic**: Keep `[0.2, 0.4, 0.8, 1.4, 2.3]` 6-chain. Keep first-hit auto-crit. Add: every wound dealt by the Fragment counts as TWO wounds for the purposes of stacking poison/bleed. The original's thirty-barbs, in echo.

**Why legendary**: A mid-game version of Gae Bolg with its own identity. Stack-cheese.

**Code needed**: `wound_count_multiplier` (moderate).

### Witcher's Silver Blade (`witcher_silver_blade`)

**Lore hook**: Forged for monsters; carried by a white-haired witcher through a hundred contracts.

**Mechanic**: Quest-only. Keep `[0.6, 1.0, 1.6, 2.4, 3.2, 4.2]` 6-chain. Keep +40% vs undead. Add: at chain 4+, the runes hum — the player gets +25% magic resistance for 3 turns after the strike. Witcher Signs, mechanized.

**Why legendary**: A defensive payoff on an offensive chain. The witcher's school of caution.

**Code needed**: `temporary_resistance_at_chain_n` (moderate; reuses status system).

### Romulus Spear (`romulus_spear`)

**Lore hook**: Hurled from the Aventine into the Palatine; took root; grew into a tree; founded Rome.

**Mechanic**: Keep `[0.5, 1.0, 1.8, 2.8, 4.0]` skyrocket. Add: every chain-5 kill lets the player drop a "Spear-Tree" — a 1-tile obstacle that lasts 10 turns and blocks enemy movement. Founding small fortresses in the dungeon. Cap 3 active.

**Why legendary**: A weapon that shapes the floor. Tactical and resonant.

**Code needed**: `place_terrain_on_chain_5` (complex; new terrain type).

---

## 5. Trickster / Wild

Chaotic curves, mid-chain dips, unpredictable. These weapons have personalities.

### Kladenets / Samosek (`kladenets`)

**Lore hook**: The Self-Swinger; fights on its own; heroes survive while it does the killing.

**Mechanic**: Keep current `[0.3, 0.9, 1.4, 0.6, 2.3]` dip curve (the sword's autonomy creating a momentum hiccup). Keep counterAttackChance 0.25. Add: every 5th turn (free of player input), Kladenets attacks the nearest enemy in reach for 50% damage. The sword acts on its own. Cannot be turned off — that's the point.

**Why legendary**: A weapon that takes turns from the player AND for the player. Russian fairy-tale.

**Code needed**: `autonomous_attack_proc` (moderate).

### Thyrsus of Dionysus (`thyrsus`)

**Lore hook**: Maenad's staff; Agave killed Pentheus believing him a lion; Dionysus watched.

**Mechanic**: Keep `[0.3, 0.9, 1.4, 0.6, 2.4]` 10-chain dip. Keep confuse 0.25. Add: at chain 3 (Maenad rhythm), the wielder enters `frenzied` for 3 turns — +50% damage, -50% defense. Self-imposed berserk on a chain. Dionysian.

**Why legendary**: A weapon that hurts the wielder for power. Drunk-mode build.

**Code needed**: `self_status_at_chain_n` (moderate).

### Sharur (`sharur`)

**Lore hook**: Ninurta's talking mace; flew and spoke; reported enemy positions before battle.

**Mechanic**: Keep `[0.4, 0.7, 1.0, 1.6, 2.3]` 6-chain. Keep confuse 0.25 + 0.3. Add: at the start of each new floor, Sharur "speaks" — reveals a random uncovered tile near a stair-down. The scout-mace.

**Why legendary**: Map information. A weapon that gives the player info before combat.

**Code needed**: `floor_start_reveal_proc` (moderate).

### Carnwennan (`carnwennan`)

**Lore hook**: Arthur's dagger; shrouded its wielder in shadow; killed the Very Black Witch in the Valley of Grief.

**Mechanic**: Keep `[0.4, 0.7, 1.0, 1.6, 3.2]` 10-chain finesse skyrocket. Keep invisible_on_equip. Add: while invisible, all of Carnwennan's chain values +0.5. The shadow rewards the shadow-walker.

**Why legendary**: Stealth synergy mechanically baked in. Players unify build.

**Code needed**: `chain_bonus_while_status` (moderate).

### Net of Hephaestus (`net_of_hephaestus`)

**Lore hook**: The smith-god forged it to catch Ares and Aphrodite; nothing escapes it.

**Mechanic**: Keep `[0.4, 0.7, 1.0, 1.6, 2.0]` 4-chain. Keep stunChance 0.8, paralyze 30%. Add: any monster hit by the Net cannot teleport, blink, phase, or be summoned away for 5 turns. The bonds Ares could not break.

**Why legendary**: Hard counter to evasive bosses. The net traps.

**Code needed**: `apply_anti_evasion_debuff` (moderate).

### Harpe (`harpe`)

**Lore hook**: Hermes's gift to Perseus; petrified gaze, the blade severed Medusa's head; Cronus used its ancestor to castrate Uranus.

**Mechanic**: Keep `[0.4, 0.7, 1.0, 1.6, 3.2]` 9-chain skyrocket. Keep petrify_on_crit. Add: against any monster with `gaze`, `petrification`, or `aberration` tag, the Harpe's chain auto-completes from rung-2 onward (skip the warm-up). The weapon that knows the monster.

**Why legendary**: Aberration-killer. Players save Harpe for the Medusa floors.

**Code needed**: `skip_chain_warmup_vs_tag` (moderate).

### Skofnung (`skofnung`)

**Lore hook**: Taken from King Hrolf Kraki's barrow; the twelve berserkers in the steel; wounds heal only at the Skofnung Stone.

**Mechanic**: Keep current `[0.8, 1.2, 0.9, 1.4, 2.3]` 9-chain dip curve (each rung a different berserker finding rhythm). Keep wound_lingers. Add: when player health drops below 50%, the next 3 attacks have +1 chain multiplier each. One of the twelve berserkers takes over.

**Why legendary**: A self-rescuing weapon. The twelve berserkers, one per panic.

**Code needed**: `chain_bonus_on_low_hp_window` (moderate).

---

## 6. Bestial / Primal

Weapons of monsters and the primordial.

### Wendigo's Fang (`wendigo_fang`)

**Lore hook**: Torn from the Wendigo's maw; leaches warmth on contact.

**Mechanic**: Quest-only. Keep current 7-chain `[0.5, 1.0, 2.0, 3.0, 4.5, 6.5, 9.0]` skyrocket. Add: every hit chills the target — stacks `frostbite`; at 5 stacks, target's max HP is reduced by 10% for the combat. The cold gets in and stays. Existing slow proc kept.

**Why legendary**: A stacking debuff alongside the skyrocket damage. Long fights vs bosses become slow drains.

**Code needed**: `frostbite_stack_max_hp_reduction` (moderate).

### Echidna's Fang (`echidna_fang`)

**Lore hook**: Tooth of the mother of monsters; venom mimics her many children's poisons.

**Mechanic**: Quest-only. Keep `[0.3, 0.5, 0.8, 1.3, 2.2, 3.5, 5.0, 6.5]` 8-chain skyrocket. Keep poison 25%/40%. Add: the poison inflicted is RANDOM each hit — could be paralytic (Gorgon), petrifying (basilisk), hallucinatory (Sphinx-child), etc. Each of Echidna's children's poisons is in the venom. Pick one each strike.

**Why legendary**: Unpredictable status payouts. Players catalog Echidna's children.

**Code needed**: `random_status_from_pool` (simple; reuses status system).

### Gilgamesh's Axe (`gilgamesh_axe`)

**Lore hook**: Enkidu dreamed of an axe that fell from the sky; the bond hardens it after the first wound.

**Mechanic**: Keep `[0.8, 1.2, 0.9, 1.4, 1.9]` 7-chain. Keep +construct effectiveness. Add: once the player takes damage in a combat, all subsequent chain values +25%. The bond hardens. Enkidu's principle.

**Why legendary**: A weapon that pays out for taking damage. Tank-builds love it.

**Code needed**: `chain_bonus_after_player_damaged` (moderate).

### Naegling (`naegling`)

**Lore hook**: Beowulf's sword that broke against the dragon; iron could not help him; his grip was too strong.

**Mechanic**: Keep `[0.9, 1.1, 1.3, 1.6, 1.9]` 8-chain. Add: every time Naegling deals damage above its base*2.0, the weapon takes 1 "stress." At 10 stress, the next swing is the LAST — auto-kill on any non-boss, then Naegling breaks (becomes unusable for the rest of the run). The Beowulf moment, faithful.

**Why legendary**: A one-shot legendary climax. Players save it for the worst foe and feel the myth.

**Code needed**: `weapon_stress_counter_break` (complex).

### Talos Sickle (`talos_sickle`)

**Lore hook**: Ground from a drop of molten bronze ichor Talos bled when Medea pulled the brass pin.

**Mechanic**: Keep `[0.2, 0.55, 1.0, 1.8, 3.0]` finesse skyrocket. Keep bleed 0.3, ignore_armor 1. Add: against any construct or mechanical-tagged enemy, ignore_armor doubles to 2. Talos was bronze; this knows bronze.

**Why legendary**: Construct floor specialist. Niche but real.

**Code needed**: `ignore_armor_vs_tag_bonus` (simple; reuses existing ignore_armor).

### Green Chapel Axe (`green_chapel_axe`)

**Lore hook**: The Green Knight's axe from Gawain's tale; strike then take then strike.

**Mechanic**: Keep `[0.8, 1.2, 0.9, 1.4, 1.9]` 6-chain. Keep `returning_blow` class_mechanic + on_hit_regen 3. Add: whenever the player kills a monster with the Green Chapel Axe, the same monster's NEXT spawn this run has -25% HP. The Knight remembers what was struck.

**Why legendary**: A run-spanning memory mechanic. Bosses fought once and again are weaker the second time.

**Code needed**: `monster_class_hp_debuff_persistent` (complex; needs per-run monster memory).

### Dawnbreaker (`dawnbreaker`)

**Lore hook**: Hammer that ended the First Darkness; sliver of preserved dawn in the head.

**Mechanic**: Keep `[0.6, 0.9, 1.2, 1.7, 2.0]` 9-chain. Keep +35% vs undead, ignore_resistances, burn 0.3. Add: chain-5 kill against an undead creates a "dawn-shaft" — a 3-tile light cone from player position lasting 5 turns; undead in the cone take 5 damage/turn and cannot enter darkness. The sun, slowed.

**Why legendary**: Light/dark mechanic. Undead levels become survivable.

**Code needed**: `dawn_shaft_terrain_proc` (complex; reuses Romulus Spear terrain logic).

### Venomfang (`venomfang`)

**Lore hook**: A master poisoner's morningstar; spikes weep ichor; the bleed corrupts.

**Mechanic**: Keep `[0.2, 0.4, 0.8, 1.4, 2.0]` 9-chain. Keep poisonChance 0.6. Add: against any already-poisoned target, Venomfang's damage is +50%. The corruption deepens. Stack-friendly.

**Why legendary**: Self-synergizing. Players ramp Venomfang into bigger Venomfang.

**Code needed**: `damage_bonus_vs_poisoned` (simple).

### Labrys (`labrys`)

**Lore hook**: The double-headed axe of Minoan Crete; appears in every palace fresco held by women.

**Mechanic**: Keep `[0.7, 1.0, 1.3, 1.6, 1.8]` 9-chain. Keep cleave_at_max, +30% vs beast. Add: in any room with multiple beast-tagged enemies (≥3), Labrys's chain values +0.25. The priestess's ritual rhythm assumes the herd.

**Why legendary**: A weapon that rewards the labyrinth-encounter density.

**Code needed**: `chain_bonus_in_high_density_tagged_room` (moderate).

---

## 7. Quirky / Flavor-First

Power-neutral or character-flavor weapons. Each is its own joke or wink.

### Punch in the Face (`punch_in_the_face`)

**Lore hook**: Dad's fist. Legendary. Has never missed. Has never needed to miss twice.

**Mechanic**: Quest-only. Keep current single-chain `[1.0]` × 9999 base damage, stun 100%. AUTHORIAL RESTRAINT: this is perfect as-is. The joke is the joke. Don't elaborate.

**Why legendary**: It already is.

**Code needed**: None.

### Sigurd's Shovel (`sigurds_shovel`)

**Lore hook**: It's a shovel. Sigurd dug a pit, stabbed a dragon from below.

**Mechanic**: Quest-only. Keep `[0.5, 1.0, 1.5, 2.0]` 4-chain. Keep `can_dig`. Keep +25% vs dragon. Add: the shovel can dig DOWN through a floor (creates a one-way pit to the next floor below the player). Cost: full chain reset. Skip the staircase. The humble tool.

**Why legendary**: Mechanically: skip floors. Lore: it's a shovel. The juxtaposition IS the legend.

**Code needed**: `weapon_dig_floor_traversal` (complex; new movement type).

### Broken Gram (`broken_gram`)

**Lore hook**: The hilt of Sigurd's father's blade; Odin broke it; still hums with dormant power.

**Mechanic**: Quest-only. Keep `[0.5, 1.0, 1.5]` 3-chain. Authorial restraint: this is the broken sword stage of the player's narrative arc. Don't elevate it. The dormancy is the point. Carrying it earns Gram later.

**Why legendary**: A weapon that exists to be replaced. The narrative is the legend.

**Code needed**: None — keep flavor.

### Narthex of Prometheus (`prometheus_torch`)

**Lore hook**: Hesiod's hollow fennel stalk; smolders for three thousand years.

**Mechanic**: Keep `[0.5, 1.0, 1.7, 2.5, 3.5]` 5-chain skyrocket. Keep burn 0.4, +undead. Add: the Narthex provides LIGHT — a 5-tile light radius around the player while equipped. Stolen fire. Functional in dark dungeons (overrides darkness-status floors).

**Why legendary**: A weapon that doubles as a torch. Practical lore.

**Code needed**: `equipped_light_aura` (simple; reuses light/dark system).

### Boomstick (`boomstick`)

**Lore hook**: Twelve-gauge double-barreled Remington. S-Mart's top of the line.

**Mechanic**: Quest-only. Keep `[0.5, 0.9, 1.2, 1.8, 3.5]` 4-chain. AUTHORIAL RESTRAINT: this is Ash's joke. Don't over-engineer. Add: AOE on chain-5 (already flagged in design_notes) — 3-tile cone, all targets take chain-5 damage. Shotgun spread.

**Why legendary**: Shop smart. Shop S-Mart.

**Code needed**: `cone_aoe_at_chain_5` (moderate; share with Bow of Apollo/Gandiva).

### Chainsaw Prosthetic (`chainsaw_prosthetic`)

**Lore hook**: Homelite XL bolted to a stump in Tennessee. Has carved through deadites.

**Mechanic**: Quest-only. Keep `[0.7, 1.2, 2.0, 3.0, 4.0]` 5-chain. Keep bleed 0.35. Add: against any undead-tagged target, the chain LOOPS — chain-5 finisher resets to chain-3 instead of chain-1 (one-shot per combat). Groovy.

**Why legendary**: Deadite specialist. The chain extends in deadite-rich rooms.

**Code needed**: `chain_loop_on_kill_vs_tag` (complex).

---

## 8. Quest-Only (already noted above)

These are scripted/hand-set items and have been folded into their archetype groups above. Listing for reference:
- Gram (God-Touched), Broken Gram (Quirky), Sigurd's Shovel (Quirky), Punch in the Face (Quirky)
- Hunt Captain's Sword (Hero's Personal), Wendigo's Fang (Bestial), Echidna's Fang (Bestial), Vulcan's Brand (God-Touched)
- Sword of Michael (God-Touched), Oathkeeper (Hero's Personal), Penitent's Blade (Hero's Personal)
- Boomstick (Quirky), Chainsaw Prosthetic (Quirky), Witcher's Silver Blade (Hero's Personal), Zireael (Hero's Personal)

All quest items keep their hand-set baseDamage and chain shape. Flavor edits noted in their entries are OPTIONAL elevations, not required changes.

---

## 9. Plain Elevated (clean 5-chain treatments where lore doesn't demand exotic mechanic)

A few weapons whose current curves are already great signature work. Authorial restraint applies — don't break what isn't broken.

### Sword of Cadmus, Akinakes of Acrisius, Hector's Javelin, Meleager's Boar-Spear, Setanta's Hurley, Cain's Club, Wepwawet Mace, Mwindo's Conga-Scepter, Theseus's Club, Atalanta's Bow, Bellerophon's Lance, Romulus Spear, Pelops Sword

These are all noted under their archetypes above; the proposed mechanic additions are SMALL elevations on top of the existing clean curves. None of them gets a radical curve rewrite — they get one flavor proc each.

### Mace of Wepwawet (`wepwawet_mace`)

**Lore hook**: Wepwawet, Opener of the Ways; predynastic Egyptian war-god, jackal-headed, scout-and-standard-bearer.

**Mechanic**: Keep `[0.5, 0.85, 1.0, 1.45, 2.0]`, stun 20%. Keep `can_dig`. Add: while wielding Wepwawet, on entering a new floor, the player learns the location of the stair-down (revealed on map). Opener of the Ways, literally.

**Why legendary**: Early-game navigation. Players adopt it for the utility.

**Code needed**: `floor_start_reveal_stair` (simple; share with Sharur).

### Staff of Moses (`staff_of_moses`)

**Lore hook**: Parted the Red Sea; struck the rock at Horeb.

**Mechanic**: Keep `[0.6, 0.9, 1.2, 1.7, 2.3]` 6-chain. Keep +40% vs undead, knockback. Add: once per floor, can be used to "part" — clears a 5-tile line of any non-boss enemies (they're pushed to the sides). The miracle, with a cooldown.

**Why legendary**: A get-out-of-hallway-free card. Crowd control on a holy weapon.

**Code needed**: `part_line_proc` (moderate).

---

## Mythic Exemptions

These weapons exceed the 3.0x mob_hp non-mythic peak guardrail. Listed with justification:

1. **Excalibur** — 5.0x peak. Mythic god-touched (lake-gift). The canonical example of the mythic exemption.
2. **Mjolnir** — proposed 5.0x peak with chain-lightning. God-touched (Thor). Justified.
3. **Gungnir** — proposed 3.5x peak with cannot-miss. God-touched (Odin). The peak is mid-mythic but the cannot-miss is the real ceiling.
4. **Heracles's Olive-Club** — 4.0x peak. Demigod-hero. Within the spirit of mythic.
5. **Sling of David** — conditional 8.0x vs giants (and conditional). The Goliath payoff. Mythic.
6. **Sword of Michael** — 16.0x peak. Quest-only, archangelic. The supreme exemption. Already in code.
7. **Sudarshana Chakra** — 3.4x peak, plus return-ward. Vishnu's discus. Mythic.
8. **Trident of Poseidon** — proposed 5.0x peak with brine puddle. God-touched (Poseidon). Justified.
9. **Ruyi Jingu Bang** — proposed 6.0x peak with growing reach. Sun Wukong's pillar. Mythic.
10. **Rod of Moses** — proposed 4.5x peak with Plagues cascade. Prophetic relic. Justified.
11. **Mjolnir Shard** — proposed 4.5x peak (chain-6 lightning splash). Shard of mythic. Reduced from full Mjolnir.
12. **Sudarshana Chakra** — listed.
13. **Vel of Murugan** — proposed 4.8x peak with peacock/rooster summon. Murugan/Parvati. Mythic.
14. **Spear of Longinus** — proposed 4.5x peak with weep-heal. Christ-relic. Justified.
15. **Wendigo's Fang** — 9.0x peak (existing). Quest-only mythic monster-bone. Justified.
16. **Echidna's Fang** — 6.5x peak (existing). Quest-only mythic monster-bone. Justified.
17. **Hunt Captain's Sword** — 10.0x peak (existing). Quest-only. Justified.
18. **Penitent's Blade** — 7.0x peak (existing). Quest-only. Justified.
19. **Gram** — 9.0x peak (existing). Quest-only Sigurd's blade. Justified.
20. **Ruyi Jingu Bang** — listed.

Total mythic exemptions: ~17 weapons (down from 96). All have lore basis as god-touched, archangelic, or hand-set quest items.

---

## Code Required

Deduplicated list of new mechanics needed in `combat.py` or `instantiate.py` hooks. Marked simple/moderate/complex.

### Simple (~12 entries)

1. `cannot_miss` flag — Gungnir. (Just a no-miss check on attack roll.)
2. `weep_heal_on_kill_scaled` — Spear of Longinus. (Heal scales with slain max HP.)
3. `damage_double_vs_tag` — Trident of Poseidon, Setanta's Hurley. (Existing `effective_against` is close; extend to multiplier.)
4. `weapon_immune_to_enchant_loss` — Chrysaor. (Skip the unenchant routine.)
5. `wielder_status_immunity` — Aiglos (fire). (Block status by tag on the wielder.)
6. `wielder_per_passive` — Hofud. (Static stat boost on equip; reusable.)
7. `random_status_from_pool` — Echidna's Fang. (Existing statuses; pick randomly.)
8. `ignore_armor_vs_tag_bonus` — Talos Sickle. (Existing ignore_armor; double vs tag.)
9. `damage_bonus_vs_poisoned` — Venomfang. (Check target poison status.)
10. `damage_bonus_vs_full_hp` — Atalanta's Bow. (Check target HP == max.)
11. `equipped_light_aura` — Narthex of Prometheus. (Reuse light radius system.)
12. `equipped_auto_reveal_adjacent` — Theseus's Club. (Tile reveal on movement.)
13. `equipped_sound_radius_modifier` — Whisperer. (If sound radius exists; simple.)

### Moderate (~30 entries)

14. `cast_me_away` proc — Excalibur. (One-shot life save on equipping/HP low; existing life_save status.)
15. `chain_lightning_at_chain_n` — Mjolnir. (Adjacent splash at chain rung n+.)
16. `damage_bonus_vs_resistant_at_max_chain` (+ inverse penalty) — Mistilteinn.
17. `boss_doom_dot_at_chain_5` — Laevateinn.
18. `chain_tier_status_table` — Rod of Moses.
19. `chain_no_reset_on_tagged_kill` — Parashu.
20. `unsheath_first_strike_proc` — Tyrfing.
21. `betray_at_low_hp_proc` — Stormbringer.
22. `apply_heal_block_debuff` — Gae Dearg.
23. `equipped_monster_aggro_radius_modifier` — Cain's Club.
24. `one_shot_chain_save_per_floor` — Hrunting.
25. `damoclean_counter_auto_kill` — Sword of Damocles.
26. `karma_disappear_proc` — Chandrahas (reuses karma).
27. `conditional_chain_curve_vs_tag` — Sling of David.
28. `weapon_produces_potion_on_threshold` — Achilles's Spear.
29. `combat_start_aoe_confuse` — Joyeuse.
30. `spare_kill_choice` — Curtana.
31. `cleave_3_tile_at_chain_5` — Caladbolg.
32. `every_hit_secondary_target` — Zulfiqar.
33. `equipped_ally_aura_buff` — Pharaoh's Crook (reusable).
34. `compel_humanoid_freeze_action` — Fragarach.
35. `adjacent_pet_buff` — Oathkeeper.
36. `kill_count_karma_adjust` — Penitent's Blade.
37. `stealth_damage_bonus` — Robin Hood's Longbow.
38. `cannot_miss_before_player_takes_damage` — Fail-not.
39. `surrounded_proc_bonus` — Kusanagi.
40. `damage_bonus_vs_attack_type` — Spear of Lugh. (Needs gaze-tagging on monsters.)
41. `multi_arrow_at_chain_5` — Gandiva.
42. `execute_at_chain_5_vs_tag_low_hp` — Brisingr.
43. `wound_count_multiplier` — Gae Bolg Fragment.
44. `temporary_resistance_at_chain_n` — Witcher's Silver Blade.
45. `chain_bonus_after_player_damaged` — Gilgamesh's Axe.
46. `chain_bonus_while_status` — Carnwennan.
47. `apply_anti_evasion_debuff` — Net of Hephaestus.
48. `skip_chain_warmup_vs_tag` — Harpe.
49. `chain_bonus_on_low_hp_window` — Skofnung.
50. `autonomous_attack_proc` — Kladenets.
51. `self_status_at_chain_n` — Thyrsus.
52. `floor_start_reveal_proc` (+ stair variant) — Sharur, Wepwawet Mace.
53. `frostbite_stack_max_hp_reduction` — Wendigo's Fang.
54. `secondary_target_thrown_at_chain_3` — Gae Bolg.
55. `chain_bonus_in_high_density_tagged_room` — Labrys.
56. `passive_wielder_tick_damage` — Vulcan's Brand.
57. `permanent_subject_timer_buff_after_milestone` — Gram.
58. `glow_initiative_buff` — Glamdring.
59. `dharma_guided_chain_5_vs_tag` — Bow of Rama.
60. `run_start_prophecy_buff` — Akinakes of Acrisius.
61. `part_line_proc` — Staff of Moses.
62. `execute_low_hp_tagged` — Anduril.
63. `terrain_proc_brine` — Trident of Poseidon, Amenonuhoko.
64. `return_to_hand_ward` — Sudarshana Chakra.
65. `adjacent_splash_at_chain_n` — Mjolnir Shard.
66. `cone_aoe_at_chain_5` — Boomstick (and could share with future ranged).
67. `damage_bonus_vs_fire_dealer` — Bellerophon's Lance. (Needs fire-source tag.)
68. `damage_double_vs_subtype` — Setanta's Hurley.
69. `chain_modulated_reach` — Ruyi Jingu Bang.
70. `weapon_indestructible` flag — Durendal. (Future-proof; current code might not need.)

### Complex (~14 entries)

71. `terrain_buff_on_finisher` — Heracles's Olive-Club. (New floor terrain that buffs allies.)
72. `global_demon_debuff_proc` — Sword of Michael. (Run-wide debuff for tagged monsters.)
73. `spawn_giant_on_male_humanoid_kill` — Cronus's Scythe. (Allied summon.)
74. `cursed_lineage_descent_event` — Pelops Sword. (Random hostile NPC spawn per descent.)
75. `summon_on_demon_kill_alternating` / `summon_after_specific_kill_tag` / `summon_demon_ally_on_kill` — Vel of Murugan, Shamshir-e Zomorrodnegar, Cadmus Sword. (Three weapons; ONE shared summon system. Allied summon with timer.)
76. `throwable_weapon_proc` — Hector's Javelin. (Weapon-on-floor pickup retrieval.)
77. `resurrect_pet_proc` — Mwindo's Conga-Scepter. (Pet death-revive system.)
78. `chain_phase_through_wall` — Hunt Captain's Sword. (Attack through walls.)
79. `extra_action_after_kill` — Zireael. (Action economy / turn system mod.)
80. `place_terrain_on_chain_5` — Romulus Spear. (Placeable obstacle terrain.)
81. `weapon_stress_counter_break` — Naegling. (Weapon-breaks-permanently mechanic.)
82. `monster_class_hp_debuff_persistent` — Green Chapel Axe. (Per-run monster memory.)
83. `dawn_shaft_terrain_proc` — Dawnbreaker. (Light-cone terrain.)
84. `weapon_dig_floor_traversal` — Sigurd's Shovel. (New movement type — dig down.)
85. `chain_loop_on_kill_vs_tag` — Chainsaw Prosthetic. (Chain-on-kill reset to mid-chain.)
86. `growth_on_innocent_kill` — Soul Reaver. (Karma+counter hook.)
87. `refuse_unequip_while_attuned` — Stormbringer. (Equip-lock; can share with future cursed gear.)

### Count Summary

- **Simple**: 13 mechanics (small flags/checks; mostly extend existing systems)
- **Moderate**: 57 mechanics (most new proc hooks; reuse where possible)
- **Complex**: 17 mechanics (new floor-state, persistent run-memory, action-economy mods)

**Total new mechanics**: ~87, but with significant sharing — the summon system is one engine serving 4-5 weapons, the terrain-proc system is shared across 5+ weapons, the chain-conditional-bonus generic could cover 10+ weapons.

Realistic implementation pass: probably 25-35 distinct engine systems with weapon-specific data.

---

## Author's notes on what to skip

If the user wants to ship a smaller scope:
- **Skip the complex shared summon system** → cut Vel, Shamshir, Cadmus, Cronus to simpler procs (just damage bonus + status).
- **Skip terrain-state procs** → cut Heracles trample, Amenonuhoko brine, Romulus tree, Dawnbreaker shaft. Replace with on-hit AoE statuses.
- **Skip monster memory** → cut Green Chapel Axe persistence; replace with on-kill heal escalator.

What MUST stay (these are the ones the user values, per the brief):
- Excalibur, Mjolnir, Gungnir, Anduril, Sword of Michael — the spine.
- Punch in the Face, Sigurd's Shovel, Boomstick, Chainsaw Prosthetic — the jokes that ARE the legend.
- Soul Reaver, Stormbringer, Tyrfing — the cursed blades.
- Hunt Captain's Sword, Penitent's Blade, Oathkeeper — the player's emotional companions.

Everything else is the wide canvas. Spend creative energy where the user's heart is.
