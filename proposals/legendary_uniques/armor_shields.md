# Legendary Uniques — Armor & Shields Proposal

**Scope**: All 59 unique body/head/cloak/feet/hands/arms/legs pieces in `data/items/armor.json` and all 37 unique shields in `data/items/shield.json`. Total: 96 pieces.

**Mandate**: Re-imagine each piece. Most armor stays flat-passive (threshold equip + static bonuses + per-event procs). Chain-equip — `escalator` or `chain` mode — is reserved for the small handful of pieces where the LORE specifically demands it: a recognition ritual, a building intensity, a race, a counted sequence.

**Equip quiz subject**: geography (armor + shields).

## Equip-mode conventions

- **Default (most pieces)**: threshold equip quiz; on success the piece grants its static bonuses and any always-on or per-floor proc. No tiered state on the item — equip is a binary pass/fail check, and the proc fires on whatever condition the proc itself defines.
- **`escalator` (tier-escalator) pieces**: an escalating quiz on equip determines which of 5 tiers the piece unlocks for the duration of equipped wear. Bonuses scale per tier; T5 unlocks a named ability. Re-equipping always re-runs a fresh quiz (no sticky state). The player may de-equip and re-attempt freely.
- **`chain` pieces**: a chain-mode quiz on equip; the chain length attained sets which rung's bonuses the piece grants. Re-equip is always fresh. Used where the lore is specifically a race or a counted sequence rather than a graded mastery curve.

Chain-equip is **rare**. The vast majority of armor — 81 of 96 pieces — is flat passive. Only the 15 pieces below use a chain-mode equip, because their lore is specifically what chain-equip captures.

---

## 1. Divine / God-Touched

The named gods' own gear. Several pieces here are the showcase chain-equip items — the recognition-ritual or building-intensity flavor is the whole point.

### Aegis of Athena (`aegis_of_athena`)

**Lore hook**: Athena's mirror-polished bronze shield, lent to Perseus to face the Gorgon by reflection rather than gaze.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: The Aegis is a recognition ritual — Athena tests the bearer's geographic mastery before lending the shield, and the deeper the mastery the more of the goddess's protection she extends.

**Tier bonuses**:
```
1: {"ac_bonus": 3}
2: {"ac_bonus": 4, "resistance": {"fear": 1}}
3: {"ac_bonus": 5, "resistance": {"fear": 2, "magic": 1}}
4: {"ac_bonus": 5, "resistance": {"fear": 2, "magic": 2}, "passive": "reflect_spell_10"}
5: {"ac_bonus": 6, "resistance": {"fear": 2, "magic": 2}, "passive": "reflect_spell_15_aura_of_awe"}
```
T5 named ability: **Aura of Awe** — every monster entering the player's FOV faces a fear check (saved against by monster will / level); failures lose 1 turn at start of next combat.

**Why legendary**: The shield Perseus used to behead Medusa now turns fear back on the dungeon. Geography mastery unlocks Athena herself.

**Code needed**: `reflect_spell_X` passive on incoming-spell hook; `aura_of_awe` fear check on FOV-entry (moderate).

### Greater Aegis of Athena (`greater_aegis_of_athena`)

**Lore hook**: The same Aegis at full Olympian expression — the goatskin storm-cloud Homer says Athena shakes to panic armies.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: The Greater Aegis is the deeper version of the same recognition ritual — the Gorgoneion fixed in the shield's center only answers to the bearer Athena fully approves.

**Tier bonuses**:
```
1: {"ac_bonus": 4, "resistance": {"petrify": 2}}
2: {"ac_bonus": 5, "resistance": {"petrify": 2, "fear": 1}}
3: {"ac_bonus": 5, "resistance": {"petrify": 2, "fear": 2, "magic": 1}}
4: {"ac_bonus": 6, "resistance": {"petrify": 2, "fear": 2, "magic": 2}, "passive": "reflect_spell_20"}
5: {"ac_bonus": 6, "resistance": {"petrify": 2, "fear": 2, "magic": 2}, "passive": "gorgoneion_petrify_on_hit"}
```
T5 named ability: **Gorgoneion** — the first monster to strike the bearer in melee each floor must save vs petrify or be turned to stone for 3 turns. Once per floor.

**Why legendary**: The Gorgon's severed head Athena mounted on the shield is finally a weapon, not just a decoration.

**Code needed**: `gorgoneion_petrify_on_hit` (per-floor flag + petrify status); resistance type `petrify` exists already (uses "petrifying" in existing items — reuse).

### Helm of Hades / Helm of Darkness (`helm_of_hades`)

**Lore hook**: Forged by the Cyclopes; prevents perception itself. Perseus, Hermes, and Athena all borrowed it.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: Hades' invisibility comes in layers — stealth in dark, unseen by undead, phase-step, finally "absence" itself. Each tier reveals a deeper register of being-unseen.

**Tier bonuses**:
```
1: {"ac_bonus": 2}
2: {"ac_bonus": 2, "passive": "stealth_in_dark"}
3: {"ac_bonus": 3, "passive": "invisible_to_undead"}
4: {"ac_bonus": 3, "passive": "phase_step_once_per_floor"}
5: {"ac_bonus": 4, "passive": "unseen_when_still"}
```
T5 named ability: **Unseen When Still** — if the player ends a turn without moving or attacking, all monsters lose the player from their target list until they move again. Re-acquires on next move/attack.

**Why legendary**: Hades' own helm doesn't grant invisibility — it grants absence. Standing still is now a tactical option.

**Code needed**: `phase_step` (one free walk through wall per floor — complex, reuse existing teleport plumbing); `unseen_when_still` (toggle target-clear on monster AI when player no-move; moderate).

### Sandals of Hermes (`winged_sandals_of_hermes`)

**Lore hook**: The talaria — the messenger god's wings between Olympus, Earth, and the Underworld.

**Equip mode**: `chain` (5 rungs)
**Why this mode**: The talaria are a race. Hermes runs and the wings unfurl one at a time as he picks up speed — chain-mode captures the build-up-or-fail rhythm of a flat-out sprint.

**Chain rung bonuses**:
```
1: {"ac_bonus": 1, "passive": "hasted"}
2: {"ac_bonus": 2, "passive": "hasted", "resistance": {"magic": 1}}
3: {"ac_bonus": 2, "passive": "hasted", "resistance": {"magic": 1}, "passive_2": "no_attack_of_opportunity"}
4: {"ac_bonus": 2, "passive": "hasted", "passive_2": "no_attack_of_opportunity", "passive_3": "free_escape_once_per_floor"}
5: {"ac_bonus": 2, "passive": "hasted", "passive_2": "no_attack_of_opportunity", "passive_3": "psychopomp_step"}
```
Max-rung named ability: **Psychopomp's Step** — on player death this floor, the sandals carry the soul one floor up instead, with 1 HP. Once per game.

**Why legendary**: Hermes guided the dead. The sandals refuse, once, to let their wearer be one of them.

**Code needed**: `no_attack_of_opportunity` (combat hook — simple); `psychopomp_step` death-save (complex — modifies death flow, save-system interaction).

### Hermes's Sandals (early game) (`hermes_sandals_early`)

**Lore hook**: A mortal smith's votive copy hung in a temple — wings of bronze, leather merely good.

**Mechanic**: Plain elevated. Keep `onEquipStatus: "hasted"` but add: `dodge_first_arrow_per_floor` (the bronze wings shed the first projectile in any encounter once per floor).

**Why legendary**: The votive carries one trick from the god. Just one. The flavor is: you found someone's prayer that worked.

**Code needed**: `dodge_first_arrow_per_floor` (encounter-scoped projectile evade flag — simple).

### Greaves of Hermes (`greaves_of_hermes`)

**Lore hook**: The Talaria's grounded sibling. Hermes wore both when he carried the dead.

**Mechanic**: Plain elevated. Static `+3 AC`, `magic 0.25`, `poison 0.15`, `onEquipStatus: hasted` (keep). Add: `descend_stairs_no_turn` — descending costs zero turns; rest restoration triggers immediately.

**Why legendary**: Sandals are speed; greaves are travel. Hermes walked between worlds; the greaves let the player skip the loading screen.

**Code needed**: Zero-cost descent (level_manager hook — simple).

### Cloak of the Morrigan (`cloak_of_the_morrigan`)

**Lore hook**: The Phantom Queen, who chose Cu Chulainn's deaths and the deaths of the men around him.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: The omen deepens. The Morrigan was a layered presence — first the raven appears, then the scout, then the death-mark; the escalator captures how her gaze sees further the more she's invited.

**Tier bonuses**:
```
1: {"ac_bonus": 2, "resistance": {"magic": 1}}
2: {"ac_bonus": 3, "resistance": {"magic": 1, "poison": 1}}
3: {"ac_bonus": 3, "resistance": {"magic": 1, "poison": 1}, "passive": "raven_scout"}
4: {"ac_bonus": 3, "resistance": {"magic": 2, "poison": 1}, "passive": "raven_scout_extended"}
5: {"ac_bonus": 4, "resistance": {"magic": 2, "poison": 1}, "passive": "death_omen_mark"}
```
T5 named ability: **Death Omen** — every kill marks the killing blow's monster type; for the next 50 turns the player deals +25% damage to monsters of that type. New mark replaces the old.

**Why legendary**: The Morrigan named the dead before they fell. Now the player does.

**Code needed**: `raven_scout` (reveal adjacent rooms — moderate); `death_omen_mark` (tracking monster-type damage bonus — moderate).

### Cloak of Odin / Wanderer's Cloak (`cloak_of_odin`)

**Lore hook**: Odin in disguise — the one-eyed wanderer who set saga-heroes their riddles.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: Odin hung on Yggdrasil for nine days to win the runes. The wisdom comes in stages — first identify-one, then the ravens, then the Faustian bargain. Each tier is another rung up the Allfather's tree.

**Tier bonuses**:
```
1: {"ac_bonus": 2, "resistance": {"magic": 1}}
2: {"ac_bonus": 2, "resistance": {"magic": 1, "cold": 1}, "passive": "identify_one_item_per_floor_free"}
3: {"ac_bonus": 3, "resistance": {"magic": 1, "cold": 1}, "passive": "identify_one_per_floor_free", "passive_2": "ravens_huginn_muninn"}
4: {"ac_bonus": 3, "resistance": {"magic": 2, "cold": 1}, "passive": "huginn_muninn", "passive_3": "wisdom_at_a_price"}
5: {"ac_bonus": 3, "resistance": {"magic": 2, "cold": 2}, "passive": "huginn_muninn", "passive_3": "wisdom_at_a_price_2"}
```
T5 named ability: **Wisdom At A Price** — once per floor the player may sacrifice 1 max HP permanently to fully identify any unidentified item in inventory. Odin hung on Yggdrasil. Wisdom is paid for.

**Why legendary**: A geographically-mastered Odin disguise that turns the identify system into a Faustian bargain.

**Code needed**: `huginn_muninn` (reveal monster intents — moderate); `wisdom_at_a_price` (HP-cost identify menu, complex).

### Crown of Brahma (`crown_of_brahma`)

**Lore hook**: The creator's four-faced crown — Brahma kept looking in every direction when Saraswati appeared.

**Equip mode**: `chain` (4 rungs)
**Why this mode**: Four faces. Four rungs. The lore is literally counted, not graded — Brahma turns one face at a time until all four are watching the player.

**Chain rung bonuses**:
```
1: {"ac_bonus": 3, "int_bonus": 1}
2: {"ac_bonus": 4, "int_bonus": 2, "mp_bonus": 10}
3: {"ac_bonus": 5, "int_bonus": 2, "mp_bonus": 15, "passive": "regenerating", "resistance": {"magic": 1}}
4: {"ac_bonus": 6, "int_bonus": 3, "mp_bonus": 25, "passive": "regenerating", "resistance": {"magic": 2, "fire": 1, "lightning": 1}, "passive_2": "four_faces_360_fov"}
```
Max-rung named ability: **Four Faces** — full 360-degree FOV regardless of facing, no blind spots. The player sees what Brahma sees.

**Why legendary**: Pure caster's crown. INT, MP, and complete spatial awareness — the late-game wizard's culmination.

**Code needed**: `four_faces_360_fov` (FOV-mode override — moderate; fov.py already supports radius modes).

### Helm of Awe / Aegishjalmr (`aegishjalmr`)

**Lore hook**: Fafnir's deathbed boast — while he wore it, no man dared meet his eye. Later Icelandic grimoires paint the rune on the forehead in blood.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: The grimoires describe a layered painting — first stroke, second stroke, the rune deepening in blood until it's complete. The escalator literalizes the rune-drawing.

**Tier bonuses**:
```
1: {"ac_bonus": 2, "resistance": {"fear": 1}}
2: {"ac_bonus": 3, "resistance": {"fear": 2}}
3: {"ac_bonus": 3, "resistance": {"fear": 2, "magic": 1}, "passive": "fafnirs_glare"}
4: {"ac_bonus": 3, "resistance": {"fear": 2, "magic": 1, "fire": 1}, "passive": "fafnirs_glare"}
5: {"ac_bonus": 4, "resistance": {"fear": 2, "magic": 2, "fire": 1}, "passive": "no_man_dares"}
```
T5 named ability: **No Man Dares Meet Your Eye** — first attacker each combat must save vs fear (will check) or lose its action. Resets per combat encounter.

**Why legendary**: The same helm the dragon hoarded. Worn correctly, it turns combat into a test of intimidation before steel.

**Code needed**: Fear save on first-attacker (combat hook — moderate).

### Svalinn (`svalinn`)

**Lore hook**: The Norse shield that stands before the sun itself — without it the mountains and the sea would burn.

**Mechanic**: Plain elevated with proc. Static `+4 AC`, `fire 1.0`, `fire_reflect 0.25` (keep). Add: when struck by fire damage, heal `floor(damage * 0.25)` HP. The shield drinks fire.

**Why legendary**: Fire mages become the player's healer.

**Code needed**: Fire-damage-as-heal proc (combat hook — simple).

### Skidbladnir Aegis (`skidbladnir_aegis`)

**Lore hook**: Freyr's ship folded into pouch-sized cloth, carved here as a shield-image.

**Mechanic**: Plain elevated with quirky proc. Keep static `+4 AC`, `cold 1.0`, `magic 0.3`. Add: `pack_capacity_bonus: 30` — the shield folds like the ship; carry weight rises by 30 lbs while equipped. The folding is the magic.

**Why legendary**: A shield that solves the inventory crisis. Lore-perfect.

**Code needed**: Pack-capacity equip bonus (player.py STR-derived cap modifier — simple).

---

## 2. Heroic / Mythic Heroes

The named hero's personal gear. A handful here are chain-equip (Sigurd's dragon-blood bath, Aragorn's paths walked); most are flat passive with a proc that captures the hero's signature moment.

### Hide of the Nemean Lion (`hide_of_nemean_lion`) + Nemean Pelt (`nemean_pelt`) — FLAT (reverted from tier-escalator)

**Lore hook**: The hide no weapon could cut — only the lion's own claws skinned it.

**Passive bonus**: Static `+6 AC`, `slash 0.3`, `blunt 0.3`, `pierce 0.3` resistance.

**Proc**: **Unskinnable** — always-on. Any monster attack with a non-magical weapon deals 1 damage minimum / 0 if the attacker has no magical attribute. Magical weapons, spells, breath, poison still bite.

**Why legendary**: The Nemean hide is a static property — Heracles' lion was born invulnerable, and the hide is invulnerable forever after the kill. There's no ritual to escalate. The mythic effect IS the always-on proc: only divine arms can hurt you.

**Code needed**: Damage-floor override based on attacker's magical flag (combat hook — moderate; existing `magical_creature` or attack-type field).

**Mechanic** (`nemean_pelt`, plot-locked quest version): Keep current — auto-grants the same Unskinnable proc on quest spawn (already powerful, plot-locked).

### Helm of Achilles (`helm_of_achilles`)

**Lore hook**: Hephaestus' last commission — the helmet that rang like a bell for the last weeks of Achilles' life.

**Mechanic**: Plain elevated with proc. Static `+4 AC`, `slash 0.2`, `fire 0.1`, `magic 0.15`. Add: `ringing_intimidation` — at start of each combat, monsters within 3 tiles roll vs morale (HP-based); failures lose 1 turn. The helm rings.

**Why legendary**: Achilles' helmet announces him. The proc is the sound itself.

**Code needed**: Combat-start morale check in radius (moderate).

### Vambraces of Achilles (`vambraces_of_achilles`)

**Lore hook**: The vambraces from the same panoply — engraved with farmers and dancers, ordinary lives the war was fought for.

**Mechanic**: Plain elevated. Keep `+4 AC`, slash/pierce/fire. Add: `peace_at_the_forge` — when the player rests (full sleep cycle), the vambraces' scenes restore +5 MP and +5 SP in addition to normal recovery.

**Why legendary**: A smith-god's reminder that war is fought over peace. Rest mechanic gets richer.

**Code needed**: Rest-cycle bonus regen tied to item (simple — extend existing rest hook).

### Coif of Beowulf (`coif_of_beowulf`)

**Lore hook**: "Wound with wires by a weapon-smith of cunning" — the Sutton Hoo helmet matches almost exactly.

**Mechanic**: Plain elevated. Static `+2 AC`, `slash 0.3`. Add: `grendel_grip` — when grappled, paralyzed, or held, the coif lets the wearer break free on the next turn without cost. Beowulf killed Grendel bare-handed; the helm remembers grip.

**Why legendary**: A free escape from the worst status effects. Anti-paralysis.

**Code needed**: Status-clear hook on paralyze/grapple/hold (moderate — interacts with status_effects.py).

### Lendings of Beowulf (`lendings_of_beowulf`, shield) — FLAT (reverted from tier-escalator)

**Lore hook**: The iron shield Beowulf ordered for the dragon — he knew wood would burn.

**Passive bonus**: Static `+3 AC`, `fire 2` resistance, `fire_reflect 0.25`.

**Proc**: **Dragon-Boss-Killer** — always-on. +50% damage dealt to creatures with the `dragon` tag while equipped. Wiglaf was there. So is the player.

**Why legendary**: The shield was made for one purpose: the dragon. It's a loaned, single-task tool, not a ritual mastery — Beowulf ordered it the morning of the fight. The mechanic should be a static dragon-killer, not a graded reveal.

**Code needed**: `fire_reflect_X` (existing field, simple value); dragon-tag damage bonus (combat hook — simple, monster.tags exists).

### Bracers of Cu Chulainn (`bracers_of_cu_chulainn`)

**Lore hook**: The Hound of Ulster's bracers — stained by the warp-spasm's hundred battles.

**Mechanic**: Plain elevated proc. Static `+2 AC`, `slash 0.1`, `enchant_bonus 1`. Add: `riastrad_echo` — every third melee hit causes the bracers to inflict bleed (1 HP/turn for 5 turns, non-stacking).

**Why legendary**: The warp-spasm bleeds enemies. Light bleed proc, thematic.

**Code needed**: Bleed status (may already exist as poison-variant); attack-count tracking (simple).

### Coat of Cu Chulainn (`coat_of_cu_chulainn`)

**Lore hook**: The war-harness — when his blood was up, his body twisted into the riastrad.

**Mechanic**: Keep current berserk system mostly as-is (it's already a special proc). Light polish: when berserk triggers, all monsters in sight roll vs fear; failures lose 1 turn. The warp-spasm panics armies.

**Why legendary**: Already lore-rich. The fear-on-trigger makes the trigger feel like a moment.

**Code needed**: Fear-on-berserk-trigger (extends existing berserk hook — simple).

### Breastplate of Joan of Arc (`breastplate_of_joan`) — FLAT (reverted from tier-escalator)

**Lore hook**: White-painted steel made for her by command. "It could not protect against what God willed."

**Passive bonus**: Static `+5 AC`, `slash 2`, `pierce 1`, `fire 1` resistance, `blessed`.

**Proc**: **The Maid Does Not Fall** — always-on. First lethal hit per floor heals to 1 HP instead. She fought on through every wound. (Joan was steady, not escalating — she fought wounded at Orléans, at Patay, at Reims. The miracle is constant.)

**Why legendary**: A second life every floor. Joan's whole career is the proc — the steadiness, not the build-up. She was the same Maid the day she met the Dauphin and the day she burned.

**Code needed**: Per-floor death-save with HP-set to 1 (complex — shared plumbing with Psychopomp's Step and Green Knight; reuse).

### Tower Shield of Ajax (`tower_shield_of_ajax`) — FLAT (reverted from tier-escalator)

**Lore hook**: Seven ox-hides laminated with bronze. Ajax stood before the Greek ships and could not be moved.

**Passive bonus**: Static `+3 AC`, `slash 2`, `pierce 2` resistance, `block 0.25`, `knockback_immune`.

**Proc**: **Before The Ships** — always-on. When an adjacent ally (pet, friendly NPC) would take a killing blow, redirect the damage to the player (up to player's remaining HP). Ajax died protecting the line.

**Why legendary**: Ajax stood unmoving. He didn't escalate, didn't transform, didn't grow into the role — he was *already* the immovable man when Achilles fell. The protection of the line is a single constant act, not a graded ritual. Flat passive captures the immovability the myth is about.

**Code needed**: Damage-redirect hook (moderate — pet_system + combat).

### Pridwen (`pridwen`) — FLAT (reverted from tier-escalator)

**Lore hook**: Arthur's shield, the Virgin Mary painted on its **inner** face — for the bearer to look at, not the enemy.

**Passive bonus**: Static `+3 AC`, `magic 2`, `unholy 2` resistance.

**Proc**: **Facing Her Alone** — always-on. When player HP drops below 25%, gain +2 AC, +1 to all saves, and prayer cooldown resets. Once per floor. The inner face is what gets you home.

**Why legendary**: The Lady-of-the-Lake's painted face is a passive ward — it doesn't deepen with mastery, it watches. Arthur didn't earn her gaze in stages; she was there the whole time, waiting for him to look. The crisis trigger is the moment the bearer remembers to look.

**Code needed**: Low-HP trigger (moderate); prayer-cooldown reset (simple).

### Spartan Aspis of Leonidas (`spartan_aspis_of_leonidas`)

**Lore hook**: Gold-chased lambda. Held the Hot Gates with three hundred Spartans, seven hundred Thespians, four hundred Theban hostages.

**Mechanic**: Plain elevated with phalanx proc. Static `+3 AC`, `pierce 0.35`, `slash 0.3`, `block 0.15`. Add: `phalanx_bonus` — for each adjacent ally (pet, NPC), +1 AC. The Spartan shield protected the man on its left.

**Why legendary**: Mechanically rewards keeping a pet adjacent. The wall-of-shields flavor lands.

**Code needed**: Adjacent-ally AC scan (simple).

### Shield of the Spartans (`shield_of_the_spartans`)

**Lore hook**: The aspis with the lambda — "Return with your shield, or on it."

**Mechanic**: Plain elevated proc. Static `+3 AC`, `pierce 0.15`. Add: `dropped_shield_curse` — if the player drops or unequips this shield while at <50% HP, gain `coward_curse` for 100 turns (-2 to all saves). Pick it up to clear.

**Why legendary**: The mother's farewell weaponized. Drop-it-and-you-shame-it.

**Code needed**: Unequip-while-wounded curse hook (moderate — interacts with status_effects).

### Helm of Leonidas (`helm_of_leonidas`)

**Lore hook**: The Corinthian helm with the transverse crest. Spartans combed their hair before the last day.

**Mechanic**: Plain elevated. Static `+3 AC`, `slash 0.2`, `pierce 0.2`. Add: `last_stand_bonus` — when player HP < 20%, +3 damage on all attacks and +20% accuracy.

**Why legendary**: Late-fight comeback potential. The Spartans were preparing for death the way their custom required.

**Code needed**: Low-HP combat bonus (simple).

### Helm of Gilgamesh (`helm_of_gilgamesh`)

**Lore hook**: Beaten gold-and-electrum from the royal tombs at Ur. Ornamental enough that real fighting would dent it.

**Mechanic**: Plain elevated. Static `+2 AC`, `blunt 0.3`. Add: `gold_offering` — once per floor, equipped helm grants the player the option to bribe a non-boss monster to skip its attack turn (costs 1d100 gold; success only on monsters with INT >= 5).

**Why legendary**: Bribery as a mechanic. Quirky, lore-faithful — Gilgamesh was a king first.

**Code needed**: Monster-bribe interaction menu (moderate — flavor_encounters has analog).

### Sandals of Perseus (`sandals_of_perseus`)

**Lore hook**: Ordinary bronze-buckled Mycenaean sandals — what Perseus had before Hermes lent him the talaria.

**Mechanic**: Plain elevated. Static `+1 AC`, `pierce 0.15`. Add: `quest_humility` — the player has +10% encounter-rate with friendly/NPC flavor events. Athena visited him in these sandals.

**Why legendary**: Lore-light proc: more NPCs find you. The pre-myth flavor.

**Code needed**: NPC encounter weighting (simple — flavor_encounters.py spawn weight).

### Sandals of Theseus (`sandals_of_theseus`)

**Lore hook**: Aegeus left them under a rock. Theseus took them and killed Sinis, Sciron, and Procrustes by their own methods.

**Mechanic**: Plain elevated proc. Static `+2 AC`, `pierce 0.2`. Add: `their_own_methods` — when a monster uses a status effect (poison, paralyze, fear, etc.), the player has a 20% chance to apply that same status to the monster on the next successful melee hit.

**Why legendary**: Tactical, lore-perfect. The bandits' methods turned on them.

**Code needed**: Status-mirror hook (moderate — status_effects.py).

### Bracers of Arjuna (`bracers_of_arjuna`)

**Lore hook**: The Mahabharata's third Pandava and greatest archer. Krishna sang him the Gita before Kurukshetra.

**Mechanic**: Plain elevated. Static `+2 AC`, `slash 0.2`, `magic 0.15`. Add: `gita_focus` — first ranged attack each floor cannot miss. Arjuna lowered his bow before the song. He raised it after.

**Why legendary**: Guaranteed first arrow, lore-faithful. Crucial for bow-builds.

**Code needed**: First-projectile-per-floor auto-hit (simple — encounter flag).

### Girdle of Hippolyta (`girdle_of_hippolyta`)

**Lore hook**: Ares' gift to the Amazon queen. Heracles' ninth Labour, paid for in Hippolyta's blood through Hera's lie.

**Mechanic**: Plain elevated. Keep STR +2 mastery blessing. Add: `amazon_charge` — when the player moves more than 3 tiles in a straight line, the next melee attack deals +50% damage. Once per encounter.

**Why legendary**: A charge mechanic for the run-and-strike player.

**Code needed**: Movement-direction tracking + bonus-attack flag (moderate — combat.py).

### Sigurd's Handshield (`sigurds_handshield`)

**Lore hook**: Sigurd painted his shields with the Fafnir story. He used the small buckler because he trusted his sword Gram more.

**Mechanic**: Plain elevated. Static `+3 AC`, `pierce 0.5`, `magic 0.2`, `block 0.15`. Add: `gram_trust` — while a unique weapon is equipped, +1 weapon damage chain bonus. The shield trusts the sword.

**Why legendary**: Weapon-pairing synergy — flavor-rich for the player who carries Gram or any other unique blade.

**Code needed**: Equipment-set check for chain-bonus (simple).

### Dragon-Sewn Mail of Sigurd (`dragon_mail_of_sigurd`)

**Lore hook**: Sigurd bathed in Fafnir's blood and became invulnerable — except for a leaf that fell between his shoulders.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: The dragon-blood bath is a stepwise ritual — Sigurd lowered himself into the blood by degrees, and at the moment of full immersion a leaf fell on his shoulder. The escalator literalizes the immersion, leaf-flaw and all.

**Tier bonuses**:
```
1: {"ac_bonus": 4, "resistance": {"fire": 1, "slash": 1}}
2: {"ac_bonus": 5, "resistance": {"fire": 2, "slash": 1, "pierce": 1}}
3: {"ac_bonus": 5, "resistance": {"fire": 2, "slash": 1, "pierce": 1}, "weakness": {"back_attack": 1.5}}
4: {"ac_bonus": 6, "resistance": {"fire": 2, "slash": 2, "pierce": 1}, "weakness": {"back_attack": 1.5}, "passive": "fire_resist"}
5: {"ac_bonus": 6, "resistance": {"fire": 2, "slash": 2, "pierce": 2}, "weakness": {"back_attack": 1.5}, "passive": "fire_resist", "passive_2": "dragon_blood_bath"}
```
T5 named ability: **Dragon-Blood Bath** — once per floor when struck by a dragon's breath, fully absorb the damage and heal for 25% of it. The leaf-weakness remains: back-attacks always deal 1.5x damage. Flavor-trade.

**Why legendary**: Sigurd's myth is the armor's mechanic — the leaf is the price.

**Code needed**: Directional-attack damage modifier (back-attack = monster behind player — moderate, needs facing logic); dragon-breath absorb (moderate, reuses Svalinn proc).

### Hittite Chariot-Guard (`hittite_chariot_guard`)

**Lore hook**: Figure-eight shield — the shield-bearer at Kadesh stood behind to protect the whole crew.

**Mechanic**: Plain elevated. Static `+2 AC`, `pierce 0.3`, `block 0.08`. Add: `crew_shield` — adjacent pets gain +1 AC. The chariot-guard's job was the others.

**Why legendary**: Pet-defensive secondary. Lore-perfect.

**Code needed**: Adjacent-pet AC pass-through (simple).

### Bronze Aegis (`bronze_aegis`) - quest-locked early aegis

**Lore hook**: The ceremonial bronze shield carved with Hephaestus' eye — the early-game stand-in for the divine Aegis.

**Mechanic**: Plain elevated, quest-spawn. Keep current `+3 AC`, blunt/slash. Add: `apprentice_aegis` — counts as the Aegis for any Aegis-themed quest or check, even though it isn't the real article. Story-tag.

**Why legendary**: Quest item; doesn't need power. Iconic for the early arc.

**Code needed**: Tag system already supports this (simple).

---

## 3. Royal / Crown

The crowns and helms of kings. Mostly plain elevated with a single thematic ability — Aragorn is the exception, because his lore IS the journey.

### Helm of the King Returned / Helm of Aragorn (`helm_of_aragorn`)

**Lore hook**: Aragorn went by Strider for most of his life. The willing exile is the rightful king.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: Aragorn's kingship is a sequence of paths walked — Strider, Dúnadan, Captain of the West, the King returned. Each tier is another path completed; T5 is the descent into the Paths of the Dead, the most lore-specific tier-5 trigger in the proposal.

**Tier bonuses**:
```
1: {"ac_bonus": 3, "resistance": {"magic": 1, "fear": 1}}
2: {"ac_bonus": 4, "resistance": {"magic": 1, "fear": 2}}
3: {"ac_bonus": 4, "resistance": {"magic": 1, "fear": 2, "slash": 1}, "passive": "blessed"}
4: {"ac_bonus": 5, "resistance": {"magic": 2, "fear": 2, "slash": 1}, "passive": "blessed", "passive_2": "command_undead"}
5: {"ac_bonus": 5, "resistance": {"magic": 2, "fear": 2, "slash": 1}, "passive": "blessed", "passive_2": "command_undead", "passive_3": "paths_of_the_dead"}
```
T5 named ability: **Paths of the Dead** — once per floor, any undead in FOV must save vs charm; failures attack their original allies for 5 turns. The Dead Men of Dunharrow answered.

**Why legendary**: Mass undead-charm — devastating in the cathedral floors.

**Code needed**: Mass-charm-undead (moderate — pet_system has charm plumbing).

### Crown of Brahma

*Already in Divine section above.*

### Cuirass of Hannibal (`cuirass_of_hannibal`)

**Lore hook**: He crossed the Alps with elephants. Won every battle. Lost the war. Military academies still teach Cannae.

**Mechanic**: Plain elevated. Static `+6 AC`, slash/blunt/pierce. Add: `cannae_encirclement` — when surrounded by 3+ enemies, gain +2 AC and +1 damage per surrounding enemy. The encircled became the encircler.

**Why legendary**: Rewards being mobbed — the worst situation becomes the best one.

**Code needed**: Adjacency-count AC/damage bonus (simple).

### Lorica of Caesar (`lorica_hamata_of_caesar`)

**Lore hook**: He refused the bodyguard. He understood warnings as challenges. He was stabbed twenty-three times.

**Mechanic**: Plain elevated. Static `+5 AC`, slash/pierce. Add: `et_tu_charge` — first attacker each combat deals +1 damage to the player but is then marked; player deals +50% damage to that monster until it dies. The first knife is the loudest.

**Why legendary**: A revenge mechanic. Caesar fell, but he marked the conspirators.

**Code needed**: First-attacker mark + damage bonus (moderate).

### Iron Boots of Thor (`boots_of_thor`)

**Lore hook**: Thor's working kit — iron gloves, belt, boots — listed in the Eddas as ordinary gear. The thunder came from the work.

**Mechanic**: Plain elevated. Static `+5 AC`, `lightning 0.5`, `blunt 0.25`. Add: `thors_step` — every step on stone floor has a 5% chance to discharge 1d6 lightning damage to a random adjacent enemy. The boots are heavy. They land.

**Why legendary**: Passive damage just from walking. Pure flavor proc.

**Code needed**: Step-trigger random-adjacent damage (simple).

### Haramaki of Yoshitsune (`haramaki_of_yoshitsune`)

**Lore hook**: The Genpei War's great general. Won Ichi-no-Tani by cavalry tactics nobody expected. His brother turned on him.

**Mechanic**: Plain elevated. Static `+5 AC`, slash/pierce/fire, `blessed`. Add: `tactical_descent` — descending stairs grants `hasted` for 5 turns. Yoshitsune won by speed.

**Why legendary**: Speed-on-stairs synergy. New-floor advantage.

**Code needed**: On-descent status (simple — level_manager hook).

### Cloak of Mulan (`cloak_of_mulan`)

**Lore hook**: Twelve years of war. The Ballad uses sixty-two lines. She came home and her comrades did not recognize her.

**Mechanic**: Plain elevated. Static `+3 AC`, cold/magic. Add: `disguise_at_camp` — at rest sites, the cloak fully restores HP, MP, and SP rather than partially. The years of war turn invisible at the hearth.

**Why legendary**: Rest amplifier. Lore: the homecoming is the point.

**Code needed**: Full-restore on rest (simple).

### Linothorax of Alexander (`linothorax_of_alexander`)

**Lore hook**: Layers of linen glued and quilted, stiff enough to stop arrows. Lighter than bronze, cheaper, copied by Rome.

**Mechanic**: Plain elevated. Static `+2 AC`, `pierce 0.4`. Add: `phalanx_recovery` — when fully resting, +5 HP regen rate per turn until next move. The Macedonian column rested when it stopped.

**Why legendary**: Rest-buff. Practical, lore-true.

**Code needed**: Rest-rate modifier (simple).

### Kilt of the Pharaoh (`kilt_of_the_pharaoh`)

**Lore hook**: The shendyt — pleated linen, sometimes gold-threaded. Tutankhamun was buried with several.

**Mechanic**: Plain elevated. Static `+1 AC`, `fire 0.4`. Add: `royal_burial` — on player death, drop one preserved possession on bones (highest-value item) intact and uncursed. Pharaonic afterlife rules.

**Why legendary**: Bones-aware. The dynasty preserves what mattered.

**Code needed**: Bones-system item-preserve override (moderate — bones.py).

### Helm of the Black Prince / Heater of the Black Prince (`heater_of_the_black_prince`)

**Lore hook**: Edward of Woodstock won Crécy at sixteen and Poitiers at twenty-six. Ich dien — I serve. He died before he reigned.

**Mechanic**: Plain elevated. Static `+3 AC`, `slash 0.6`, `magic 0.2`. Add: `ich_dien` — while equipped, mastery_blessing effects across all items count for +1 (compound mastery bonus).

**Why legendary**: Mastery synergy — rewards the player who masters multiple items. The Prince serves; the items serve in turn.

**Code needed**: Mastery-stacking modifier (moderate — interacts with mastery_blessing system).

### Lionheart Shield (`lionheart_shield`)

**Lore hook**: Marten of the Iron Vale promised his wife he would be back for supper. Four months ago.

**Mechanic**: Plain elevated. Keep `+4 AC`. Add: `martens_promise` — first time the player descends to a new floor each day, gain +20 HP and +20 SP for 50 turns. The shield wants to go home.

**Why legendary**: The shield finds its end of the story through the player.

**Code needed**: Per-day per-floor trigger (moderate — interacts with save-system day tracking).

---

## 4. Magical / Arcane

The robes and mantles of casters. Two showcase chain-equip pieces (Magus, Solomon, Smoking Mirror) — each is a recognizable mage-ritual sequence. Most cloaks are flat passive.

### Robe of the Magus (`robe_of_the_magus`)

**Lore hook**: The Magi were scholars of stars and dreams. They followed a conjunction, brought gold, frankincense, myrrh; went home another way.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: The Magi were scholars whose mastery accumulated by degree — the robe records what its wearer has studied. Each tier is another text learned, another spell stabilized, until at T5 the wearer can cast at the conjunction's peak.

**Tier bonuses**:
```
1: {"ac_bonus": 1, "mp_bonus": 5, "int_bonus": 1, "resistance": {"magic": 1}}
2: {"ac_bonus": 2, "mp_bonus": 10, "int_bonus": 1, "resistance": {"magic": 1}}
3: {"ac_bonus": 2, "mp_bonus": 15, "int_bonus": 2, "resistance": {"magic": 2}, "passive": "free_cast_once_per_floor"}
4: {"ac_bonus": 2, "mp_bonus": 15, "int_bonus": 2, "resistance": {"magic": 2}, "passive": "free_cast_once_per_floor", "passive_2": "spell_crit_10"}
5: {"ac_bonus": 2, "mp_bonus": 20, "int_bonus": 3, "resistance": {"magic": 2}, "passive": "free_cast_once_per_floor", "passive_2": "spell_crit_10", "passive_3": "double_cast_at_max_chain"}
```
T5 named ability: **Double-Cast at Max Chain** — when the player's grammar-quiz chain reaches max while reading from this robe, the next spell casts twice.

**Why legendary**: The full Archmage build. Geography is the equip; grammar is the cast.

**Code needed**: `free_cast` flag (moderate — magic mixin); `spell_crit` damage modifier (simple); `double_cast` chain trigger (moderate).

### Robes of Solomon (`robes_of_solomon`)

**Lore hook**: His wisdom was the gift he asked for. The seventy-two names on the robe were the bound demons.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: Solomon's mastery was learning the demons' true names one at a time. Each tier is another seal bound, another name remembered. T5 is the full court of seventy-two assembled — the demon-true-name instakill is the lore's literal mechanic.

**Tier bonuses**:
```
1: {"ac_bonus": 3, "int_bonus": 1, "resistance": {"magic": 1, "fire": 1}}
2: {"ac_bonus": 4, "int_bonus": 2, "resistance": {"magic": 1, "fire": 1, "cold": 1}}
3: {"ac_bonus": 5, "int_bonus": 2, "resistance": {"magic": 2, "fire": 1, "cold": 1, "poison": 1}, "passive": "blessed"}
4: {"ac_bonus": 5, "int_bonus": 3, "resistance": {"magic": 2, "fire": 1, "cold": 1, "poison": 1}, "passive": "blessed", "passive_2": "demon_command_one_per_floor"}
5: {"ac_bonus": 5, "int_bonus": 3, "resistance": {"magic": 2, "fire": 1, "cold": 1, "poison": 1}, "passive": "blessed", "passive_2": "demon_command_one_per_floor", "passive_3": "seventy_two_seals"}
```
T5 named ability: **Seventy-Two Seals** — once per floor, the player may speak the true name of a demon-tagged monster, instantly defeating it. Charges per floor.

**Why legendary**: A late-game demon-kill button. Lore-perfect.

**Code needed**: Demon-tag instakill on demand (moderate — monster.tags + UI prompt).

### Mantle of Elijah (`mantle_of_elijah`)

**Lore hook**: Elijah's mantle, taken up by Elisha. The mantle is the office, not the man. Elisha finished plowing the field first.

**Mechanic**: Plain elevated. Static `+2 AC`, `fire 0.3`, `magic 0.2`. Add: `prophets_passing` — when the player levels up while wearing this, gain +1 max MP permanently (stacking). The mantle is inherited.

**Why legendary**: A slow-growth MP item — flavor-perfect for the inherited office.

**Code needed**: Level-up MP bonus per-level-while-equipped (moderate — needs persistent counter).

### Tarnhelm (`tarnhelm`)

**Lore hook**: Forged by Mime for Alberich. Siegfried took it after Fafnir. Renders the wearer absent from perception entirely.

**Mechanic**: Plain elevated. Keep current `+3 AC` and invisibility power but extend: once-per-floor invisibility lasts 8 turns (was 5), and during it the player may pickpocket up to one item from any non-boss monster's loot table without combat.

**Why legendary**: The Nibelung's invisibility plus theft. Lore-tight — Alberich stole the Rhine gold.

**Code needed**: Pickpocket-from-monster-loot during invisibility (moderate — needs item-pull from monster's lootable inventory).

### Anansi's Web Cloak (`anansi_web_cloak`)

**Lore hook**: Spun from the thread of a thousand stories. Attacks miss; traps fail.

**Mechanic**: Plain elevated. Keep `+3 AC`, poison/physical resists. Add: `story_thread` — when struck by a critical hit, the cloak retells it as a near-miss and reduces the damage to 1. Once per floor. The story changes the ending.

**Why legendary**: Trickster crit-protection. One-per-floor saver.

**Code needed**: Per-floor crit-reduction flag (moderate — combat.py crit hook).

### Erlking's Mantle (`erlking_mantle`)

**Lore hook**: Woven from the living branches of the Erlking's forest. Sound and sight carry further.

**Mechanic**: Plain elevated. Keep current `per_plus_2`. Add: `forest_hearing` — reveal all monsters within 6 tiles on the map (silhouettes), even through walls.

**Why legendary**: Full sensory advantage. The forest tells the mantle who is coming.

**Code needed**: Map silhouette reveal in radius (moderate — fov.py + renderer).

### Arachne's Silk Cloak (`arachne_silk_cloak`)

**Lore hook**: Woven by Arachne before her transformation. Catches arrows, slows blades.

**Mechanic**: Plain elevated. Keep `+2 AC`, `pierce 0.7`. Add: `webbed_strike` — when struck in melee, attacker is slowed (-1 speed) for 3 turns. Non-stacking.

**Why legendary**: Defensive slow on every melee hit. Crowd-control through being hit.

**Code needed**: Slow-on-being-hit (moderate — status_effects).

### Cloak of Sun Wukong (`cloak_of_sun_wukong`)

**Lore hook**: Born from a stone egg. Stole the peaches of immortality. Seventy-two transformations.

**Mechanic**: Plain elevated. Keep `+2 AC` and `displacement`. Add: `monkey_king_dodge` — every 10 turns, the next incoming attack auto-misses. The seventy-two transformations include "not where you thought."

**Why legendary**: Predictable dodge. Player can count turns and bait.

**Code needed**: Turn-counter dodge proc (simple).

### Ancile (`ancile`, shield)

**Lore hook**: Fell from heaven during Numa's reign. Eleven copies made so no thief could find the real one.

**Mechanic**: Plain elevated. Keep `+3 AC`, `blunt 0.7`, `quiz_timer_bonus 2`. Add: `numas_eleven` — when destroyed, dropped, or stolen, has a 90% chance to be one of the copies (an `Ancile Replica` with half the bonuses materializes in inventory). The real one is preserved somewhere.

**Why legendary**: The shield refuses to be lost. Save-system flavor.

**Code needed**: On-destroy/drop replacement item spawn (moderate — items.py + save_system).

### Battersea Votive Shield (`battersea_votive_shield`)

**Lore hook**: Found in the Thames in 1857. La Tene style. Too thin to fight with. Thrown in the river as a gift.

**Mechanic**: Plain elevated. Keep `+2 AC`, `magic 0.5`, `spell_block 0.15`. Add: `river_offering` — sacrificing this shield to a fountain or altar grants the player +1 INT permanently. The shield was meant to be given up.

**Why legendary**: One-shot stat bump if the player commits. Lore-perfect — votive offerings worked by destruction.

**Code needed**: Altar/fountain sacrifice interaction (moderate — flavor_encounters extension).

### Smoking Mirror of Tezcatlipoca (`smoking_mirror_of_tezcatlipoca`)

**Lore hook**: Tezcatlipoca's obsidian mirror showed souls, not futures. Quetzalcoatl saw his own face and fled.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: The smoking-mirror divinations were a graded ritual — first the smoke clears, then the obsidian reflects, then the soul appears. Each tier is another step in Tezcatlipoca's gaze; the deeper the mastery, the more the mirror sees.

**Tier bonuses**:
```
1: {"ac_bonus": 2, "resistance": {"magic": 1}}
2: {"ac_bonus": 3, "resistance": {"magic": 2}}
3: {"ac_bonus": 3, "resistance": {"magic": 2, "fire": 1}, "passive": "spell_reflect_20"}
4: {"ac_bonus": 4, "resistance": {"magic": 2, "fire": 1}, "passive": "spell_reflect_30"}
5: {"ac_bonus": 4, "resistance": {"magic": 2, "fire": 1}, "passive": "mirror_of_souls"}
```
T5 named ability: **Mirror of Souls** — when a monster casts a spell at the player, the caster sees its own karma and is stunned for 1 turn (in addition to spell-reflect). The lesson lands.

**Why legendary**: Anti-mage utility. Caster-killer.

**Code needed**: Stun-on-spell-cast at caster (moderate — spell hook).

### Vajra Paramita (`vajra_paramita`)

**Lore hook**: The vajra is lightning and diamond. Indra carries one. Vajrapani carries one. Six perfections to cross to the far shore.

**Mechanic**: Plain elevated. Keep `+4 AC`, magic/pierce/cold resists, lightning resist bonus. Add: `six_perfections` — for each unique mastery_blessing the player has earned, gain +1 max MP. The paramitas accumulate.

**Why legendary**: Stacks with mastery system. Late-game caster reward.

**Code needed**: Mastery-count MP bonus (moderate — needs mastery counter).

### Scarab of Apophis-Binding (`scarab_of_apophis_binding`)

**Lore hook**: Apophis tries to swallow Ra's barge every night. Khepri pushes the sun across. The scarab pushes back.

**Mechanic**: Plain elevated. Keep `+5 AC`, multiple resists, spell_reflect 0.5. Add: `dawn_of_ra` — at the start of every fifth turn, all undead and demon-tagged monsters in FOV take 1d8 holy damage. Apophis hisses.

**Why legendary**: A pulse of holy damage on a timer. The barge crosses the sky.

**Code needed**: Periodic FOV-scan damage to tagged enemies (moderate — turn-counter + tag-check).

### Yama's Dharma-Watch (`yamas_dharma_watch`)

**Lore hook**: Yama, first man and king of the dead. Buffalo-headed judge with the Mirror of Karma. Spells, having been measured, decline to land.

**Mechanic**: Plain elevated. Keep `+5 AC`, magic 1.0, petrify 1.0, cold 0.8, all reflect/block stats. Add: `mirror_of_karma` — for each negative karma point the player has, +1 damage on melee attacks (up to +10 at karma -10). The judge's account-keeping cuts both ways.

**Why legendary**: Late-game evil-build amplifier — the bad-karma player has been keeping score, and Yama agrees.

**Code needed**: Karma-tied damage bonus (simple — karma int already in player).

### Horse-Armor of the Norns (`horse_armor_of_the_norns`)

**Lore hook**: Urd, Verdandi, Skuld — past, becoming, what-should-be. They weave fate; Odin obeys.

**Mechanic**: Plain elevated. Keep `+4 AC`, cold/magic, block, knockback, spell_reflect. Add: `weave_of_three` — every third turn, choose: heal 5 HP, restore 5 MP, or restore 5 SP. Cycles through choices automatically if not selected.

**Why legendary**: Predictable triple regen. The Norns weave on schedule.

**Code needed**: Periodic regen-choice menu (moderate — UI hook).

---

## 5. Cursed / Sinister

The pieces with cost-to-power. Most are flat passive — the curse IS the constant — except for Ragnarok, where the doom genuinely builds.

### Coat of Cu Chulainn

*Already in Heroic section above — the berserk system is the cost.*

### Babr-e Bayan (`babr_e_bayan`)

**Lore hook**: Rostam's tiger-skin armor. Worn through the Seven Labors. Each monster absorbed remembers.

**Mechanic**: Plain elevated. Keep current `first_hit_absorb` and resistances. Add: `seven_labors` — for each non-trivial monster (CR >= floor average) the player kills, the coat permanently gains +1 HP up to +50. Slow grind, lore-true.

**Why legendary**: A progress-tracking armor. Rostam earned his hide by labors; the player earns theirs by kills.

**Code needed**: Kill-tracking HP accrual capped (moderate — items can persist kill counter).

### Blindfold (`blindfold`)

**Lore hook**: Heavy black cloth. Total darkness. Sometimes not seeing is the only way to survive.

**Mechanic**: Quirky. Keep current `blinded` on equip and `psychic 0.5` mastery. Add: `closed_eyes_open_mind` — while blinded by this item, gain `tremor_sense` (perceive all adjacent monsters and walls within 3 tiles regardless of light/FOV). Outside that radius, blind.

**Why legendary**: A real tradeoff — trade sight for tremor-sense. Anti-psychic build niche.

**Code needed**: Tremor-sense FOV mode (moderate — fov.py).

### Cow King's Horns (`cow_kings_horns`)

**Lore hook**: Ripped from the Cow King's crowned skull. Left horn inscribed: "Moo."

**Mechanic**: Quirky proc. Keep `+1 AC`, `chain_bonus 1`. Add: `bovine_fury` — first miss in a combat chain becomes a free re-roll once per encounter. The Cow King had infinite patience.

**Why legendary**: Easter-egg item; quirky mechanical relief in chain-mode.

**Code needed**: Per-encounter chain-reroll flag (simple — quiz_engine integration).

### Armor of Ragnarök (`armor_of_ragnarok`)

**Lore hook**: The harness for the day the gods knew was coming and went out to meet anyway.

**Equip mode**: `escalator` (5 tiers)
**Why this mode**: Ragnarok is a doom that builds. The Eddas tell it as a sequence — Fimbulwinter, the wolves swallowing sun and moon, the world-tree shaking, the final battle. Each tier is another stage of the doom; T5 is the gods walking out to meet the end. The escalator literalizes the buildup.

**Tier bonuses**:
```
1: {"ac_bonus": 4, "resistance": {"fire": 1, "cold": 1}}
2: {"ac_bonus": 5, "resistance": {"fire": 2, "cold": 1, "slash": 1}}
3: {"ac_bonus": 6, "resistance": {"fire": 2, "cold": 2, "slash": 1, "pierce": 1}}
4: {"ac_bonus": 6, "resistance": {"fire": 2, "cold": 2, "slash": 2, "pierce": 1, "blunt": 1}, "passive": "first_hit_absorb"}
5: {"ac_bonus": 6, "resistance": {"fire": 2, "cold": 2, "slash": 2, "pierce": 1, "blunt": 1}, "passive": "first_hit_absorb", "passive_2": "doom_of_the_gods"}
```
T5 named ability: **Doom of the Gods** — when player HP drops to 1 (lethal hit not killed by other saves), the armor explodes for 5d10 damage to all monsters in FOV and is destroyed. The Ragnarok was the gods' choice.

**Why legendary**: A nuclear option. Lose the armor; clear the floor.

**Code needed**: Self-destruct on near-death with AOE (complex — combat + items + bones, but high-impact).

---

## 6. Quirky / Flavor

Power-neutral or low-power; the effect is the point. All flat passive.

### Trainer's Cap (`trainers_cap`)

**Lore hook**: Brim reads: "I choose you."

**Mechanic**: Keep `pet_regen_bonus: 2` (already perfect). Add: `bond_check` — the player's first pet of the run levels up an additional time on each new floor entered while this cap is worn. The Trainer raises the bond.

**Why legendary**: Pet-build amplifier. Easter-egg lore, real mechanical depth.

**Code needed**: Per-floor pet XP grant (moderate — pet_system).

### Vidar's Sandal (`vidars_sandal`)

**Lore hook**: Reinforced with leather scraps from a lifetime. Vidar planted his foot on the World-Wolf's lower jaw.

**Mechanic**: Quirky. Keep `+3 AC`, slash/blunt resist. Add: `world_wolfs_jaw` — first time the player kicks/melees a wolf-tagged monster per floor, instant-kill that monster. The sandal remembers.

**Why legendary**: Wolf-tag instakill, once per floor. Lore-perfect.

**Code needed**: Wolf-tag first-hit instakill (simple — monster.tags + combat).

### Cloth of Penelope (`cloth_of_penelope`)

**Lore hook**: Wove and unwove for twenty years. The thread refused to stay finished.

**Mechanic**: Quirky. Keep `+1 AC`, `regenerating`. Add: `weave_and_unweave` — when the player's HP drops below 25%, the cloth begins regenerating at +2 HP/turn until back to full. The thread re-knits the body.

**Why legendary**: Crisis-tier emergency healing. Penelope's pace.

**Code needed**: Low-HP regen boost (simple — extends status_effects).

### Khopesh-Breaker of Thebes (`khopesh_breaker_of_thebes`)

**Lore hook**: Egyptian tall shield specifically designed to deny the khopesh's hooking edge.

**Mechanic**: Plain elevated. Keep `+1 AC`, `slash 0.3`, all-elemental mastery. Add: `khopesh_denier` — slashing attacks from monsters with curved blades (saber, scimitar, khopesh, falchion) deal -50% damage. Specific anti-counter.

**Why legendary**: Specific defense against specific weapon types. Lore-true: armor evolves as an answer.

**Code needed**: Weapon-shape damage modifier (moderate — needs weapon-type tags on monster attacks).

### Pelte of the Thracian (`pelte_of_the_thracian`)

**Lore hook**: The crescent shield doesn't have to be heavy to win. Iphicrates' peltasts broke a Spartan regiment.

**Mechanic**: Plain elevated. Keep `+1 AC`, `slash 0.25`, `block 0.1`. Add: `peltast_retreat` — when the player moves away from an adjacent enemy, that enemy does not get an attack of opportunity. Skirmish mechanic.

**Why legendary**: Pure tactical flavor. Hit-and-run becomes a real strategy.

**Code needed**: Conditional disable-of-attack-of-opportunity (moderate — combat.py).

### Buckler of the Sumerian Lugal (`buckler_of_the_sumerian_lugal`)

**Lore hook**: The Stele of the Vultures. "I am the man whom Ningirsu loves." Four thousand years later, the god is gone, the shield works.

**Mechanic**: Plain elevated. Keep `+1 AC`, `fire 0.25`. Add: `phalanx_oldest` — when adjacent to any other shield-wielding entity (NPC or pet with shield), +1 AC. The first phalanx.

**Why legendary**: Shield-line synergy. Lore-archaic.

**Code needed**: Adjacent-shield-wielder check (simple).

### Mycenaean Tower of Telamon (`mycenaean_tower_of_telamon`)

**Lore hook**: Eight layers of ox-hide. Heavier than the bearer's torso. The body learned to lean into it.

**Mechanic**: Plain elevated. Keep `+1 AC`, `pierce 0.25`, `block 0.08`. Add: `lean_into_it` — while equipped, the player's encumbrance cap rises by 20 lbs. The shield doubles as a back-brace.

**Why legendary**: Inventory utility. The shield wins by being heavy in the right way.

**Code needed**: Encumbrance cap modifier (simple — STR-derived cap).

### Etruscan Round Shield (`etruscan_round_shield`)

**Lore hook**: Italy before Rome. Their language is mostly undeciphered. We do not know what they called the shield.

**Mechanic**: Plain elevated. Keep `+2 AC`, `blunt 0.3`, `block 0.12`. Add: `the_old_name_forgotten` — first cursed item the player picks up each floor identifies as `cursed` automatically. The Etruscan shield knows lost truth.

**Why legendary**: Auto-curse-detection. Lore-true: the shield outlasted those who named it.

**Code needed**: Per-floor curse-reveal hook (simple — identify system).

### Saxon Round Shield (`saxon_round_shield`)

**Lore hook**: Sutton Hoo. Limewood, iron boss, dragon of the Wuffingas. Beowulf was written in this kingdom in this century.

**Mechanic**: Plain elevated. Keep `+3 AC`, slash/blunt, `block 0.12`, `knockback_on_block 0.15`. Add: `wyrm_painted` — gain +20% damage with shield-bash (existing block mechanic) against dragon-tagged enemies. The shield knows its enemy.

**Why legendary**: Anti-dragon shield-bash specialization.

**Code needed**: Tag-modified shield-bash damage (simple — block mechanic + tag).

### Sarmatian Lamellar Targe (`sarmatian_lamellar_targe`)

**Lore hook**: Sarmatian cavalry. Garrisoned Hadrian's Wall. Some say King Arthur's cavalry was Sarmatian.

**Mechanic**: Plain elevated. Keep `+3 AC`, `pierce 0.5`, `block 0.12`. Add: `mounted_blood` — when riding a pet (if pet-riding ever ships), +2 AC. Otherwise: when adjacent to a pet that has just attacked, +1 damage on next melee. Cavalry doctrine.

**Why legendary**: Pet synergy. Lore-perfect.

**Code needed**: Pet-just-attacked flag (moderate — pet_system tracking).

### Carolingian Kite (`carolingian_kite`)

**Lore hook**: Charlemagne's heavy horse. Long point covers the left leg. Empire fell apart inside his grandsons' lifetimes.

**Mechanic**: Plain elevated. Keep `+3 AC`, `pierce 0.6`, `block 0.15`, `projectile_block 0.4`. Add: `crown_of_christmas_day` — first prayer per floor has its cooldown halved. The Pope crowned him on Christmas.

**Why legendary**: Theology synergy. Faster prayers, lore-anchored.

**Code needed**: Prayer cooldown modifier first-cast (simple — divine mixin).

### Mameluke Targe (`mameluke_targe`)

**Lore hook**: Slave-soldiers who became rulers of Egypt and broke the Mongols at Ain Jalut. Useless against missiles but perfect for the saber-duel.

**Mechanic**: Plain elevated. Keep `+3 AC`, `slash 0.5`, `block 0.18`, `knockback_on_block 0.2`. Add: `ain_jalut` — vs creatures with the `mongol` or `horde` or `swarm` tag, +2 AC. The targe was made for the specific battle.

**Why legendary**: Anti-swarm specialization.

**Code needed**: Tag-based AC modifier (simple).

### O-Tate of the Samurai (`o_tate_of_the_samurai`)

**Lore hook**: Not held. A wooden screen propped on the ground. At Nagashino, three thousand arquebusiers behind a palisade of o-tate broke the Takeda cavalry.

**Mechanic**: Plain elevated. Keep `+4 AC`, `pierce 0.7`, `projectile_block 0.5`. Add: `set_in_place` — when the player has not moved for the previous turn, +2 AC and projectiles auto-miss for the current turn. The shield wins when it is not being held.

**Why legendary**: Stand-still bonus. Pure lore-mechanic.

**Code needed**: No-move-last-turn AC + projectile evade (moderate — turn tracking).

### Scutum of Aeneas (`scutum_of_aeneas`)

**Lore hook**: Hephaestus forged it with all of Rome's future inscribed. Aeneas carried it without understanding.

**Mechanic**: Plain elevated. Keep `+5 AC`, slash/blunt/fire. Add: `unwritten_future` — when entering a new floor, reveal the floor's boss-tag and one random encounter event from its event pool. The shield's bearer was preinformed.

**Why legendary**: Strategic intel from the shield. Lore-perfect — the shield's images foretold Rome.

**Code needed**: Floor-reveal partial info on descent (moderate — level_manager + flavor_encounters).

### Scutum of the Legio (`scutum_of_the_legio`)

**Lore hook**: Legio XII Fulminata. Plywood, cowhide, iron-edged. Light to march. Strong to testudo.

**Mechanic**: Plain elevated. Keep `+2 AC`, pierce/slash, block/projectile-block. Add: `testudo` — when adjacent to two or more allies or shield-wielders, +1 AC and projectile damage is reduced 50%. The tortoise formation.

**Why legendary**: Multi-ally formation bonus. Pure cohort flavor.

**Code needed**: Multi-adjacent shield-check (simple — extends Sumerian Lugal's hook).

### Macedonian Aspis of Philip (`macedonian_aspis_of_philip`)

**Lore hook**: Philip shrank the shield so both hands could grip the sarissa. Alexander conquered the world before thirty-three.

**Mechanic**: Plain elevated. Keep `+2 AC`, `pierce 0.3`, `block 0.1`, `fire_reflect 0.1`. Add: `two_handed_sarissa` — while equipped, two-handed weapons can be used with this shield (it straps to the arm). Effective +1 damage with any two-handed weapon while equipped.

**Why legendary**: Breaks the shield/two-handed mutual exclusion. Lore-faithful, mechanically novel.

**Code needed**: Equipment-rule override (moderate — items.py equip checks).

### Celtic Oval Shield (`celtic_oval_shield`)

**Lore hook**: Caesar's commentaries. The Gauls lost. The shield does not know it lost.

**Mechanic**: Plain elevated. Keep `+2 AC`, `slash 0.5`, `block 0.12`. Add: `obstinate` — first time per floor the player would lose a quiz chain at 1, the chain holds at 1 instead. The shield refuses to break.

**Why legendary**: Chain-mode safety net. Lore-true: lost the war, kept the shield.

**Code needed**: Per-floor chain-save (moderate — quiz_engine).

### Germanic Kriegsschild (`germanic_kriegsschild`)

**Lore hook**: Arminius and the Teutoburg Forest. Three legions annihilated in three days. Rome never put eagles east of the Rhine again.

**Mechanic**: Plain elevated. Keep `+3 AC`, `cold 0.5`, `block 0.1`. Add: `teutoburg` — in dark or forest-tagged floors, +2 AC. The shield knows the trees.

**Why legendary**: Terrain-specific bonus. Lore-perfect.

**Code needed**: Floor-tag AC modifier (simple — dungeon.py floor.tags).

### Assyrian Siege-Pavise (`assyrian_siege_pavise`)

**Lore hook**: Sennacherib at Lachish. Man-high wickerwork shields. The relief is in the British Museum.

**Mechanic**: Plain elevated. Keep `+2 AC`, `pierce 0.4`, `block 0.05`, `projectile_block 0.3`. Add: `sennacherib_set` — when standing still, projectile_block rises to 0.6. The pavise is meant to be planted.

**Why legendary**: Static defender. Anti-archer.

**Code needed**: Conditional projectile-block (simple — turn-stationary flag).

---

## 7. Plain Elevated

The lore-rich pieces that don't need a wild mechanic. Clean static bonuses, single proc. The Green Knight's Plate is the one exception — a quest-spawn auto-T5 escalator piece.

### Panoply of Hephaestus (`panoply_of_hephaestus`)

**Lore hook**: Hephaestus' masterwork. Achilles' armor. The smith god limped; his works walked.

**Mechanic**: Static `+8 AC`, slash/pierce/blunt/fire (keep). Add: `divine_smithing` — all currently-equipped weapons gain +1 to their max enchant cap while this is worn. The smith god raises every weapon.

**Why legendary**: Cross-slot synergy with weapon enchants. A smith's armor blesses the smith's work.

**Code needed**: Equipped-weapon enchant-cap override (moderate — items.py).

### Carapace of the Hydra (`carapace_of_the_hydra`)

**Lore hook**: The Hydra's outer scale was immune to its own venom. Heracles used the blood to poison his arrows.

**Mechanic**: Static `+6 AC`, `poison 0.65`, cold/fire (keep). Add: `caustic_blood` — when the wearer takes a poison or acid attack, the attacker also suffers 1 turn of `poisoned` (no save). The venom answers.

**Why legendary**: Poison-reflective. Late-game venomous-mob killer.

**Code needed**: Poison-on-receive-poison reflect (simple — status_effects).

### Orichalcum Breastplate (`orichalcum_breastplate`)

**Lore hook**: Plato's lost metal. Brass-red and resonant.

**Mechanic**: Static `+7 AC`, magic/fire/cold (keep). Add: `atlantean_resonance` — every fifth turn, the resonance grants the wearer +1 to all saves for 1 turn. The metal hums.

**Why legendary**: Periodic save-buff. Quiet utility.

**Code needed**: Periodic save-buff trigger (simple — turn counter).

### Brigandine of Wallace (`brigandine_of_william_wallace`)

**Lore hook**: Real William Wallace. Stirling Bridge. Executed by a method designed for dishonor. The speeches were invented later.

**Mechanic**: Plain elevated. Static `+5 AC`, slash/pierce. Add: `guerrilla_terrain` — in narrow corridors (1-tile-wide), +2 AC. Wallace won at the bridge by terrain.

**Why legendary**: Terrain-aware. Stirling Bridge proper.

**Code needed**: Corridor-detection AC (moderate — dungeon-tile context).

### Boots of Seven Leagues (`boots_of_seven_leagues`)

**Lore hook**: Seven leagues per step. Stolen from an ogre. Disproportionately large on every original owner, perfectly fitting the hero.

**Mechanic**: Plain elevated. Keep `+2 AC`, `magic 0.2`, `hasted` on equip. Add: `seven_league_step` — once per floor, the player may dash up to 7 tiles in a straight line (ending in a known-revealed tile). The boots' name is literal.

**Why legendary**: Tactical reposition. Lore-perfect, mechanically distinct from hasted.

**Code needed**: 7-tile dash ability (moderate — dungeon traversal + UI).

### Gauntlets of Mars (`gauntlets_of_mars`)

**Lore hook**: Mars defends boundaries. His priests danced with sacred shields. Tuesday is named for him through Tiwaz/Tyr.

**Mechanic**: Plain elevated. Static `+3 AC`, blunt/slash. Add: `boundary_guardian` — when the player is in a room with a door, +1 AC. Defending the threshold.

**Why legendary**: Room-defense flavor. Mars protects boundaries.

**Code needed**: Door-adjacency AC check (moderate — dungeon).

### Great Helm of Galahad (`great_helm_of_galahad`)

**Lore hook**: Galahad sat in the Siege Perilous and nothing happened. The Grail works through irony.

**Mechanic**: Plain elevated. Static `+4 AC`, magic/slash, `unholy 0.4`. Add: `purity` — the helm cannot be cursed, and while worn, no other equipped item can become cursed by drinking/random events.

**Why legendary**: Anti-curse insurance. Galahad cannot be tempted.

**Code needed**: Curse-immunity passthrough (moderate — items.py curse system).

### Leggings of Enkidu (`leggings_of_enkidu`)

**Lore hook**: Enkidu was made wild and made friend. Gilgamesh's grief is the oldest written grief.

**Mechanic**: Plain elevated. Static `+2 AC`, slash/blunt/pierce. Add: `wild_friend` — pets' max HP is +20% while these are worn. The friend stands taller.

**Why legendary**: Pet-defense. Lore-faithful.

**Code needed**: Pet max-HP multiplier (simple — pet_system).

### Scale of Dilmun (`scale_of_dilmun`)

**Lore hook**: Sumerian paradise. The flood survivor lived there. The scale-armor predates the Hittite by centuries.

**Mechanic**: Plain elevated. Static `+3 AC`, slash/pierce. Add: `paradise_water` — when standing on water or fountain tile, +2 AC and +1 HP regen/turn. Dilmun was a paradise of water.

**Why legendary**: Terrain-bonus. Lore-perfect.

**Code needed**: Water-tile bonus (simple).

### Greaves of Qin (`greaves_of_qin`)

**Lore hook**: Terracotta Army. Lacquered leather scales laced with cord. Qin engineers understood materials.

**Mechanic**: Plain elevated. Static `+2 AC`, pierce/slash. Add: `lacquered` — `acid 0.3` resistance added. The lacquer waterproofs.

**Why legendary**: Quiet acid-resistance. Lore-true: lacquer is anti-corrosion.

**Code needed**: None (acid is an existing resistance type in Nidhoggr).

### Green Knight's Plate (`green_knights_plate`, plot-locked)

**Lore hook**: Enchanted iron that grows with the wearer. Sir Gawain's beheading-game.

**Equip mode**: `escalator` (5 tiers) — quest-spawn variant: T5 awarded directly on quest completion (no equip-quiz). Player may also unequip and re-attempt the escalator at the cost of losing the auto-T5 bonus, then re-equip at whatever tier they reach.

**Why this mode**: The Green Knight's covenant has stages — the first beheading (Gawain's swing), the year's delay, the journey to the Green Chapel, the second beheading mediated by the girdle, the survival. Each tier is another beat of the bargain. T5 is the survival.

**Tier bonuses**:
```
1: {"ac_bonus": 5, "passive": "regen_2"}
2: {"ac_bonus": 6, "passive": "regen_2", "resistance": {"slash": 2}}
3: {"ac_bonus": 7, "passive": "regen_2", "resistance": {"slash": 2, "physical": 2}}
4: {"ac_bonus": 7, "passive": "regen_2", "resistance": {"slash": 2, "physical": 2}, "passive_2": "life_save"}
5: {"ac_bonus": 8, "passive": "regen_2", "resistance": {"slash": 2, "physical": 2}, "passive_2": "life_save", "passive_3": "second_beheading_returns"}
```
T5 named ability: **The Second Beheading Returns** — on death, the player automatically returns to life at full HP one floor above the death floor. Once per game. The Green Knight's covenant.

**Why legendary**: The hardest extra-life mechanic in the game. Lore-perfect: Gawain survived the second beheading.

**Code needed**: Death-bypass with floor-up (complex — same plumbing as Joan's flat-proc death-save and Psychopomp's Step, but full HP).

### Serpent Scale Mail (`serpent_scale_mail`, plot-locked)

**Lore hook**: Jormungandr's juvenile scales. Poison neutralized but still repellent.

**Mechanic**: Plain elevated. Keep `+6 AC`, `poison 0` (full immunity), `cold 0.7`. Add: `world_serpent_scale` — when struck by any monster with the `serpent` tag, that monster takes 1d8 damage and is `marked` (revealed on the map for the next 20 turns). Serpents recognize the World-Serpent.

**Why legendary**: Anti-serpent specialization. Quest item earned via serpent fight.

**Code needed**: Serpent-tag damage-and-mark on receive-hit (moderate — combat + map).

---

## Chain-Equip Pieces

The 15 pieces using chain-equip — `escalator` or `chain` mode — and their named abilities. Every other unique uses flat-passive threshold equip.

### Escalator (5-tier) — 13 pieces

1. **Aegis of Athena** — Aura of Awe (FOV-entry fear check) *(recognition ritual)*
2. **Greater Aegis of Athena** — Gorgoneion (first-hit petrify, once per floor) *(recognition ritual, deeper)*
3. **Helm of Hades** — Unseen When Still (no-move target-clear) *(layered absence)*
4. **Cloak of the Morrigan** — Death Omen (kill-marks +25% dmg vs type for 50t) *(omen deepens)*
5. **Cloak of Odin** — Wisdom At A Price (1 max HP for free identify) *(Yggdrasil-tree mastery)*
6. **Aegishjalmr** — No Man Dares (first-attacker fear save) *(rune painted in blood, stroke by stroke)*
7. **Helm of Aragorn** — Paths of the Dead (mass undead-charm) *(paths walked: Strider → King)*
8. **Dragon-Sewn Mail of Sigurd** — Dragon-Blood Bath (breath absorb + heal) *(stepwise dragon-blood immersion)*
9. **Robe of the Magus** — Double-Cast at Max Chain *(scholar's accumulated study)*
10. **Robes of Solomon** — Seventy-Two Seals (demon true-name instakill) *(seals bound one at a time)*
11. **Smoking Mirror of Tezcatlipoca** — Mirror of Souls (spell-cast stun) *(Tezcatlipoca's graded gaze)*
12. **Armor of Ragnarök** — Doom of the Gods (1-HP self-destruct AOE) *(Ragnarok builds: Fimbulwinter → wolves → battle)*
13. **Green Knight's Plate** — The Second Beheading Returns (full-HP death-save) *(beheading-game's stages)*

### Chain — 2 pieces

1. **Sandals of Hermes** — Psychopomp's Step (one-shot death-evade). 5 rungs. *(the race the messenger runs)*
2. **Crown of Brahma** — Four Faces (360-degree FOV). 4 rungs. *(four literal faces of Brahma)*

### Pieces reverted to flat passive (originally proposed as escalator)

These pieces keep their named proc as an always-on or per-floor effect — no equip-quiz tier:

- **Hide of the Nemean Lion** — Unskinnable (always-on). The hide IS uncuttable; no ritual to escalate.
- **Breastplate of Joan of Arc** — The Maid Does Not Fall (per-floor death-save). Joan was steady, not escalating.
- **Tower Shield of Ajax** — Before the Ships (pet-protect always-on). Ajax was immovable from the moment he showed up.
- **Pridwen** — Facing Her Alone (per-floor low-HP buff). Mary's passive ward, not a graded ritual.
- **Lendings of Beowulf** — Dragon-Boss-Killer (+50% vs dragon always-on). A loaned single-task tool, not a mastery curve.

---

## New Resistance / Status Types

Required engine additions, deduplicated:

| Type | Used by | Status |
|---|---|---|
| `fear` (resistance) | Aegis, Greater Aegis, Aegishjalmr, Helm of Aragorn | NEW resistance type |
| `petrify` / `petrifying` | Greater Aegis | exists (`petrifying` in Greater Aegis already) — alias |
| `unholy` (resistance) | Pridwen, Helm of Aragorn, Great Helm of Galahad | exists (mastery_blessings use it) |
| `psychic` | many | exists |
| `back_attack` (weakness multiplier) | Dragon-Sewn Mail | NEW directional damage type |
| `tremor_sense` (status) | Blindfold | NEW perception status |
| `bleed` | Bracers of Cu Chulainn | exists or use poison variant |
| `webbed_slow` | Arachne's Silk | use existing slow |
| `mark` (debuff) | Cloak of the Morrigan, Serpent Scale | NEW monster-mark status (probably exists in mystery_system or similar) |
| `coward_curse` | Shield of the Spartans | NEW |
| `blessed` | many | exists |
| `regenerating` | Cloth of Penelope, Crown of Brahma, Mantle of Elijah | exists |
| `displacement` | Cloak of Sun Wukong | exists |
| `invisible_to_undead` | Helm of Hades T3 | NEW (extension of invisibility flagged by faction) |
| `dragon_tag`, `serpent_tag`, `wolf_tag`, `mongol/horde/swarm_tag` | Lendings, Serpent Scale, Vidar, Mameluke | likely exist in monster.tags |
| `demon_tag` | Robes of Solomon | exists |

---

## Code Required

Every engine hook needed by these proposals, deduplicated, with complexity markers.

### Equip & Chain-Equip Plumbing

- **Tier-escalator equip flow for armor/shields** (complex) — extension of existing tier-escalator pattern; must persist tier on item instance for the duration of equipped wear; re-equip is always a fresh quiz (no sticky state). Used by 13 pieces.
- **Chain-mode equip flow for armor/shields** (moderate) — chain-quiz on equip selecting which rung's bonuses the piece grants. Re-equip is always fresh. Used by 2 pieces (Sandals of Hermes, Crown of Brahma).
- **Geography equip-quiz integration** (simple) — already exists for threshold; need escalator + chain subject hooks

### Defensive / Damage Resistance

- **`fear` resistance type** (simple) — add to damage_resistances dict resolution in combat.py
- **`back_attack` directional damage multiplier** (moderate) — needs player-facing logic; player.py would need a facing field, or use last-move-direction
- **Damage-floor based on attacker magical flag** (moderate) — for Nemean Unskinnable; combat.py
- **Curse-immunity passthrough** (moderate) — Galahad's helm protects other slots
- **Coward-curse status** (moderate) — status_effects.py + items.py drop-trigger

### Reflect / Reflect-Like Passives

- **`reflect_spell_X`** at scaling tiers (moderate) — extends existing spell_reflect field
- **`fire_reflect_X`** scaling (simple) — exists, just a value
- **Fire-damage-as-heal proc** (simple) — Svalinn polish

### On-Hit & On-Receive Procs

- **Status-mirror on receive-status** (moderate) — Sandals of Theseus
- **Stun-on-spell-cast at caster** (moderate) — Smoking Mirror T5
- **Poison-on-receive-poison reflect** (simple) — Hydra
- **Slow-on-being-melee'd** (moderate) — Arachne
- **Per-floor crit-reduction** (moderate) — Anansi
- **First-attacker fear save** (moderate) — Aegishjalmr T5
- **First-attacker mark + damage bonus** (moderate) — Lorica of Caesar

### Per-Floor / Per-Encounter Triggers

- **Per-floor death-save with HP-set** (complex) — Joan (flat proc), Green Knight (escalator T5), Hermes (chain max), Ragnarok (escalator T5). Different effects, same plumbing — reuse.
- **Per-floor invisibility timer** (already exists — Tarnhelm)
- **Per-encounter chain-reroll** (simple) — Cow King
- **Per-floor projectile-evade flag** (simple) — Hermes early
- **Per-floor demon-true-name instakill prompt** (moderate) — Solomon T5
- **Per-floor wolf-tag instakill** (simple) — Vidar
- **Per-floor curse-detection** (simple) — Etruscan
- **Per-floor chain-save at 1** (moderate) — Celtic Oval

### Spatial / Adjacency

- **Adjacent-ally AC bonus** (simple) — Spartan Aspis, Hittite, Sumerian Lugal, Scutum Legio
- **Adjacent-shield-wielder synergy** (simple)
- **Surrounded-by-N AC/damage bonus** (simple) — Hannibal
- **No-move-last-turn AC** (moderate) — O-Tate
- **Corridor-tile detection AC** (moderate) — Wallace
- **Door-adjacency AC** (moderate) — Mars
- **Water-tile AC + regen** (simple) — Dilmun
- **Floor-tag AC modifier** (simple) — Kriegsschild (forest tag)

### Magical / Cast Hooks

- **Free-cast once per floor flag** (moderate) — Robe of the Magus T3
- **Double-cast at max chain** (moderate) — Robe T5
- **Spell-crit damage modifier** (simple) — Robe T4
- **MP/INT scaling per tier** (simple — additive to existing equip-stat hooks)
- **Mastery-count MP bonus** (moderate) — Vajra
- **Level-up MP-while-equipped bonus** (moderate) — Elijah

### Movement / Action Economy

- **No-attack-of-opportunity passive** (simple) — Hermes Sandals, Pelte
- **Zero-cost stairs descent** (simple) — Greaves of Hermes
- **Status-on-descent** (simple) — Yoshitsune
- **7-tile dash ability** (moderate) — Boots of Seven Leagues
- **Phase-step (walk through wall)** (complex) — Helm of Hades T4
- **Unseen-when-still target-clear** (moderate) — Helm of Hades T5
- **Movement-direction tracking for charge** (moderate) — Girdle of Hippolyta
- **Pack-capacity bonus** (simple) — Skidbladnir, Telamon

### Pet / Ally

- **Pet AC pass-through** (simple) — Hittite, Sarmatian
- **Pet max-HP multiplier** (simple) — Enkidu
- **Damage-redirect from pet to player** (moderate) — Ajax (now flat proc)
- **Pet XP grant per floor** (moderate) — Trainer's Cap

### Tag-Based Damage Modifiers

- **Dragon-tag damage bonus** (simple) — Lendings (now flat proc), Saxon Round
- **Wolf-tag instakill** (simple) — Vidar
- **Mongol/swarm-tag AC** (simple) — Mameluke
- **Curved-blade attack type modifier** (moderate) — Khopesh-Breaker
- **Serpent-tag on-receive damage + mark** (moderate) — Serpent Scale

### Quiz / Identify Synergy

- **HP-cost identify prompt** (complex) — Odin T5
- **Per-floor full-identify free** (moderate) — Odin T2

### Mastery / Item Synergy

- **Mastery-stacking modifier** (moderate) — Black Prince
- **Equipped-set damage bonus** (simple) — Sigurd's Handshield

### FOV / Perception

- **360-degree FOV mode** (moderate) — Brahma max-rung; fov.py already has radius modes
- **Tremor-sense FOV mode** (moderate) — Blindfold
- **Map silhouette reveal in radius** (moderate) — Erlking
- **Floor-preview on descent** (moderate) — Scutum of Aeneas
- **Raven-scout (reveal adjacent rooms)** (moderate) — Morrigan T3
- **Huginn-Muninn (reveal monster intents)** (moderate) — Odin T3

### Prayer / Karma / Divine

- **Karma-tied melee damage bonus** (simple) — Yama
- **Prayer cooldown first-cast halved** (simple) — Carolingian
- **Prayer-reset trigger at low HP** (simple) — Pridwen flat proc

### Periodic / Timed Effects

- **Periodic FOV-scan damage to tagged enemies** (moderate) — Apophis
- **Periodic regen-choice menu** (moderate) — Norns
- **Periodic save-buff trigger** (simple) — Orichalcum
- **Turn-counter dodge proc** (simple) — Sun Wukong
- **Step-trigger random-adjacent lightning** (simple) — Thor's Boots

### Other / Quirky

- **Encounter-rate NPC weighting** (simple) — Sandals of Perseus
- **Altar/fountain sacrifice +INT** (moderate) — Battersea
- **Bones preserved-item override** (moderate) — Kilt of the Pharaoh
- **Per-day per-floor trigger** (moderate) — Lionheart
- **Per-encounter first-projectile auto-hit** (simple) — Arjuna
- **Rest-bonus regen tied to item** (simple) — Vambraces of Achilles
- **Full-rest restore** (simple) — Mulan
- **Combat-start morale radius check** (moderate) — Helm of Achilles ringing
- **Kill-tracking item HP accrual** (moderate) — Babr-e Bayan
- **Equipment-rule override (shield+two-handed)** (moderate) — Macedonian Aspis
- **On-destroy replacement item spawn** (moderate) — Ancile
- **Self-destruct AOE on near-death** (complex) — Armor of Ragnarok T5
- **Monster-bribe interaction** (moderate) — Helm of Gilgamesh
- **Pet-just-attacked flag** (moderate) — Sarmatian
- **Conditional projectile-block** (simple) — Assyrian
- **Equipped-weapon enchant-cap override** (moderate) — Panoply of Hephaestus
- **Berserk-trigger fear AOE** (simple — extends existing) — Coat of Cu Chulainn
- **Pickpocket-from-monster-loot during invisibility** (moderate) — Tarnhelm

### Estimated Total New / Modified Hooks

- **Simple**: 28 hooks (small additive changes, often single combat or items.py lines)
- **Moderate**: 40 hooks (new flags, status types, per-system integration)
- **Complex**: 6 hooks (death-save plumbing, phase-walk, Solomon true-name, Ragnarok self-destruct, identify-cost-HP, tier-escalator armor flow itself)

The reverted-to-flat pieces (Nemean Hide, Joan, Ajax, Pridwen, Lendings) cut roughly 5 tier-state-tracking integrations off the original 20-piece count; their procs all become always-on or per-floor flags using infra already needed elsewhere (e.g., Joan's death-save reuses the Green Knight / Hermes death-save plumbing).

---

## Implementation Order Suggestion

If accepted, a phased rollout that aligns with the existing identify-rebuild work:

1. **Phase 1 (foundation)**: tier-escalator equip flow + chain-equip flow + `fear` resistance + a single tier-escalator pilot piece (Aegis of Athena) and a single chain pilot piece (Sandals of Hermes). Validates both modes before broad rollout.
2. **Phase 2 (mythic showcase)**: implement the remaining 13 chain-equip pieces with their named abilities.
3. **Phase 3 (procs & quirks)**: implement plain-elevated procs grouped by complexity — simple flags first, then moderate hooks, then complex (death-saves, Ragnarok self-destruct, Solomon true-name). The 5 reverted pieces ship here as always-on procs.
4. **Phase 4 (synergy)**: implement cross-slot synergies (mastery-stacking, equipped-set, pet pass-throughs) — these touch existing systems and benefit from being last.

Stays compatible with the existing mastery_blessing system, identify rebuild (393d34d), and the engine caps documented in `reference_engine_caps.md`.
