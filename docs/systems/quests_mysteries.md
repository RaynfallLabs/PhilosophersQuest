# Quests & Mysteries

> Status: reference. Reflects v2.18.0 (`409e15d`, 2026-10-02).
> Scope: 9 named quest chains, 12 mystery altars, the altar/key spawn
> system, invert_result semantics, the Seven Seals judgment gate, and
> the v2.18 artifact `unidentified_name` sweep that stopped quest items
> from spoiling themselves on pickup.
>
> Related docs: [items](items.md) (quest items and the artifact pool),
> [progression](progression.md) (hero specials and quirks unlocked by
> mystery rewards), [world](world.md) (level generation + bones),
> [combat](combat.md) (Divine Intercession, seal-demon kills).
> Divine mechanics and karma scoring live in
> [karma_prayer](karma_prayer.md).

---

## 1. Design intent

Quests and mysteries sit above the normal dungeon loop. The normal
loop is "fight → loot → identify → cook → descend." A quest or
mystery is the moment the dungeon **points at a specific object or
place and dares the player to do something with it**. The player
rarely stumbles into a quest reward — the reward is withheld until a
specific item, altar, and action line up.

Four properties distinguish quests from mysteries:

| | Named quest chain | Mystery altar |
|---|-------------------|---------------|
| Spawn | Guaranteed on a fixed level | 60% roll per generated level, pool restricted by floor range |
| Trigger | Named key item (bronze bull, broken Gram, …) | Named key item or on-tile precondition (3 Food for Cauldron) |
| Challenge | Spatial / inventory puzzle (drop here, throw over altar, assemble 6 pieces) | Quiz challenge (threshold / chain / escalator) or physical (Sisyphus) |
| Reward | Named artifact or shrine door (Thread, Aegis, Shovel, Gleipnir, Sandal) | Stat bump, permanent status effect, or specific named item |

The quest chains tell small mythological stories: Theseus (Ariadne),
Perseus (Athena), Sigurd / Fafnir (Odin), the binding of the
World-Wolf (Gleipnir + Vidar), the Last Judgment (Michael), the
secret Diablo-2 cow level, Excalibur's single pull, and the Duck of
Doom slow-cook. Mysteries are standalone myth beats: Pandora,
Solomon, Grail, Sphinx, Mjolnir, Oracle, Fisher King, Mimir, Golden
Fleece, Black Cauldron, Crucible, Sisyphus.

---

## 2. The nine quest chains

Each chain is a two-, three-, or four-beat sequence. Steps run on
fixed floors so the trigger item is always findable before its
altar. Numbers are from `src/dungeon.py` + `src/main.py::_finish_drop`.

### 2.1 Ariadne — Bronze Bull → Fountain → Thread

| Beat | Floor | What happens |
|------|-------|--------------|
| 1 | L12 | `Bronze Bull Idol` (artifact id `bronze_bull`) spawns in a non-start room, guaranteed. `plot_role: asterion_quest_layer1` |
| 2 | L17 | `_create_ariadne_shrine` carves a sealed 3x3 shrine behind a wall adjacent to a fountain. Thread is placed inside. If the level has no fountain, one is forced into a random room. The shrine door tile stays as WALL. |
| 3 | L17 | Player **drops** the Bronze Bull on the FOUNTAIN tile → `_activate_ariadne_shrine` runs: bull is consumed, shrine door becomes DOOR, message "The water shimmers gold! ..." |
| 4 | L17 (shrine) | Player picks up `Ariadne's Thread` (artifact id `ariadnes_thread`). |

Chain reward: Ariadne's Thread anchors the L20 Asterion / Minotaur
boss. Its intended effect is "defangs Asterion's phasing" per
artifact `plot_role` metadata.

Trigger code: `main.py:6697-6701` → `game_divine._activate_ariadne_shrine`.
Shrine carver: `dungeon._create_ariadne_shrine` (L1989).

### 2.2 Athena — Eye of the Graeae → Altar → Aegis

| Beat | Floor | What happens |
|------|-------|--------------|
| 1 | L29 | `Eye of the Graeae` (artifact id `eye_of_graeae`) spawns in a non-start room, guaranteed. `plot_role: medusa_quest_layer1` |
| 2 | L37 | `_create_athena_shrine` finds an ALTAR on the floor (or forces one) and carves a sealed 3x3 shrine. `Aegis of Athena` (shield) is placed inside. |
| 3 | L37 | Player **drops** the Eye on an ALTAR tile → `_activate_athena_shrine`: eye dissolves, shrine door opens, "Athena speaks ..." |
| 4 | L37 (shrine) | Player picks up `Aegis of Athena` (mirror shield; weapon vs Medusa on L40). |

Trigger code: `main.py:6703-6707` → `game_divine._activate_athena_shrine`.
The Eye is pre-identified via `peak_floor=30 / peak_weight=0.4` so it
can also drop organically mid-twenties through the Gaussian pool, but
the guaranteed L29 spawn is the design-safe path.

### 2.3 Odin / Gram — Broken Gram → Altar (two paths) → Shovel + reforged Gram

This chain has **two** success paths, one obvious and one secret.

| Beat | Floor | What happens |
|------|-------|--------------|
| 1 | L48 | `Broken Blade of Gram` (`broken_gram`, weapon) spawns in a non-start room, guaranteed. |
| 2 | L53 | `_create_odin_shrine` places `odin_altar_pos` (ALTAR tile) in a non-start room and carves a sealed 3x3 shrine containing `sigurds_shovel`. |
| 3a | L53 (plain path) | Player **drops** Broken Gram on Odin's Altar tile → `_activate_odin_shrine(reforge=False)`: blade dissolves, shrine door opens, player goes in and picks up Sigurd's Shovel. **Gram is lost.** |
| 3b | L53 (secret path) | Player **throws** Broken Gram in a line that crosses the altar tile (`_throw_crosses_tile` in `game_combat._throw_weapon`, L293-315). → `_activate_odin_shrine(reforge=True)`: lightning strikes, Gram spawns on the altar **fully reforged** (3d6, +4 enchant, `is_unique`), and shrine door still opens. **Player gets both Gram and the Shovel.** |

The reforge gatekeeper is `_throw_crosses_tile(px, py, tx, ty, ax, ay)` —
the player stands on one side of the altar, the throw target is on the
other side, altar between them. Throwing any **other** weapon over the
altar triggers "A rumble of distant thunder... but nothing happens.
Odin will not reforge this." (`game_combat.py:311-314`).

Trigger code: `main.py:6709-6716` (drop path), `game_combat.py:293-315`
(throw path). Both call `game_divine._activate_odin_shrine`.

### 2.4 Gleipnir / Fenrir — 6 impossible ingredients → Dwarven Forge

| Beat | Floor | What happens |
|------|-------|--------------|
| 1 | L62 | `cats_footstep` ("Sound of a Cat's Footstep") spawns in a themed room ringed by silent-alarm traps. |
| 2 | L65 | `womans_beard` ("Roots of a Woman's Beard") spawns in a hidden alcove behind a SECRET_DOOR. |
| 3 | L68 | `mountain_root` ("Root of a Mountain") spawns surrounded by LAVA tiles. |
| 4 | L71 | `fish_breath` ("Breath of a Fish") spawns surrounded by WATER tiles. |
| 5 | L74 | `bird_spittle` ("Spittle of a Bird") spawns on an ALTAR tile. |
| 6 | L77 | `bear_sinew` ("Sinew of a Bear's Sensitivity") spawns next to a bear-trap ring. |
| 7 | L76 | `_create_dwarven_forge` places `dwarven_forge_pos` (visually an ALTAR tile) in a far room. |
| 8 | L76 | Player drops **all 6 components on the forge tile** → `_check_gleipnir_forge` fires on every drop; when all 6 ids are present, it consumes them and spawns `gleipnir` (artifact). |

The forge check is on every drop at the forge tile, so the player can
assemble pieces in any order. `_GLEIPNIR_COMPONENT_IDS` is a frozenset
in `game_divine.py:537`.

Reward: Gleipnir, the ribbon that binds the World-Wolf. Its gameplay
role is as the key item to immobilize Fenrir on the L80 boss floor.

Trigger code: `main.py:6718-6723` → `game_divine._check_gleipnir_forge`.

### 2.5 Vidar — 10 leather scraps → L79 altar

A parallel Norse-track quest that runs through the whole dungeon.

| Beat | Floor | What happens |
|------|-------|--------------|
| 1 | L5, L13, L21, L28, L35, L42, L50, L58, L66, L73 | One `leather_scrap` (artifact, 2.0 lb) spawns per level, guaranteed, in a non-start room. 10 total. |
| 2 | L79 | `_create_vidar_altar` places `vidar_altar_pos` (ALTAR tile) in a non-start room. |
| 3 | L79 | Player drops **10 leather scraps on the altar tile** → `_check_vidar_altar` consumes 10 scraps and spawns `vidars_sandal` (armor, `plot_role: fenrir_quest_layer2_instant_kill`). |

Reward: Vidar's Sandal, the Silent God's weapon. Per
`artifact.json::vidars_sandal.plot_role` it enables the instant-kill
line against Fenrir on L80.

Trigger code: `main.py:6725-6730` → `game_divine._check_vidar_altar`.
The 10-scrap set is hardcoded in `dungeon.py:1933` (`_LEATHER_SCRAP_LEVELS`).

### 2.6 Altar of the Last Judgment — Seven Seals → L99

The capstone divine chain. The "trigger items" here are **monsters**,
not objects.

| Beat | Floor | What happens |
|------|-------|--------------|
| 1 | L83, L85, L87, L89, L91, L93, L97 | A seal demon force-spawns on each level: Wrath, Pestilence, Famine, War, Death, Earthquake, Silence. Monsters are flagged `is_seal_demon=True`. See `level_manager._SEAL_DEMON_LEVELS`. |
| 2 | varies | Kill the seal demon → it drops a `seal_of_<kind>` artifact. Picking the seal up adds it to `game.seals_broken` (set of 7 ids). Seals shatter in hand on pickup (`main.py:4218-4228`). |
| 3 | L99 | `_create_judgment_altar` places `judgment_altar_pos` (ALTAR tile) in the largest non-start room. |
| 4 | L99 | **Descent to L100 is gated**: `_descend_stairs` (`main.py:2715-2722`) refuses with "Seven seals hold the Pit closed. N remain unbroken." until `len(seals_broken) == 7`. |
| 5 | L99 (altar) | Player prays (`\`) on the altar tile → `_start_pray` short-circuits into `_resolve_judgment` (`game_divine.py:772-780`). Prayer is replaced by the karma judgment. |
| 6 | L99 | `_resolve_judgment` reads `self.karma`, routes through `npc_encounters.judge_karma` → one of five outcomes (see §2.6 below and [karma_prayer §8](karma_prayer.md)). The altar then flips `_judgment_resolved = True` and stays silent on repeat tries. |

Judgment outcome summary (karma clamp -10..+10):

| Karma | Outcome key | Effect |
|-------|-------------|--------|
| 10 | `sword_and_scales` | Player receives **Sword of Michael** + **Scales of Michael**, title set to "Paladin", chronicle entry logged. |
| +1..+9 | `scales_granted` | Player receives Scales of Michael. |
| 0 | `silence` | Nothing. "You have done nothing worthy of praise or condemnation." |
| -1..-5 | `locusts_strengthened` | `_locusts_strengthened = True` → larger locust swarms on L100. |
| -6..-10 | `abaddon_empowered` | `_abaddon_empowered = True` → Abaddon on L100 gets +50% HP and an extra attack. |

Seal demon list (`level_manager.py:236-244`):

```python
_SEAL_DEMON_LEVELS = {
    83: 'seal_demon_wrath',
    85: 'seal_demon_pestilence',
    87: 'seal_demon_famine',
    89: 'seal_demon_war',
    91: 'seal_demon_death',
    93: 'seal_demon_earthquake',
    97: 'seal_demon_silence',
}
```

### 2.7 Duck of Doom — the slow-cook

A joke chain and secret pet unlock. One floor L1-10 drops a Duck of
Doom (armor id `duck_of_doom`). Pickup force-equips to the head
slot (bypasses cursed-helm guards), displaces whatever was there,
and locks on because the Duck is itself cursed.

| Beat | Floor | What happens |
|------|-------|--------------|
| 1 | L1-10 (one chosen at game start, `_duck_of_doom_floor`) | One Duck of Doom placed, guaranteed. |
| 2 | pickup | `_duck_of_doom_pickup` force-equips to head slot, kicks the old head to inventory (or ground), starts `quirk_progress['duck_of_doom_turns'] = 0`. |
| 3 | +2026 turns | `_duck_of_doom_tick` ticks the counter every player turn. At 2026 → `_duck_of_doom_transform`. |
| 4 | transform | Duck leaves head slot (consumed), spawns a `Pet('duck_of_doom', px, py)` — the **Waddlekind** celestial duckling — at the player's tile. Late-pickup XP applies so a duck hatched at F40 isn't L1-weak (`pet.apply_late_pickup_bonus(dungeon_level)`). The `duck_of_doom` quirk is awarded. |

Constant: `Game.DUCK_OF_DOOM_TURNS_REQUIRED = 2026` (release-year
joke). Transform code: `main.py:4455-4493`.

Known leak (see SYSTEMS_AUDIT §3 P2): Soul Sphere throws, Summon
Guardian, and Gate spells pull from `pet_system.random_species`,
which **includes `duck_of_doom`**, so Waddlekind can appear outside
the 2026-turn chain.

### 2.8 Excalibur — the one-shot pull

Not a multi-beat chain, but a quest-shaped unique: it fires once per
run and consumes itself.

| Beat | Floor | What happens |
|------|-------|--------------|
| 1 | varies | `excalibur` (weapon, `is_unique`) spawns through the normal Gaussian unique pool (`peak_floor` + `peak_weight`). |
| 2 | combat | While equipped, each kill restores `kill_heal_amount` HP (purity signature). |
| 3 | HP ≤ 25% | **`cast_me_away` fires once per run**: the next attack drains the weapon's enchantment / effect for a one-shot burst, after which Excalibur is spent. |

Flag: `cast_me_away` in `items.py:425-427`. Doc/data mismatch logged
in SYSTEMS_AUDIT §3 (`chainMultipliers` peak 2.0 vs `design_notes`
claim of 5.0x at chain-5 — treat 2.0 as truth).

### 2.9 Cow Level — the Diablo-2 nod

A secret chain triggered by **not** combat. The cow is an allied NPC
with 1 HP, flagged `_npc_encounter_tag = '_cow_dialog'`; bumping it
opens a dialog instead of attacking.

| Beat | Floor | What happens |
|------|-------|--------------|
| 1 | one floor L30-39 (chosen at game start, `_cow_level: int = _lore_rng.randint(30, 39)`) | `_maybe_spawn_cow` places a sessile cow NPC in a non-start room. |
| 2 | bump | `_start_cow_encounter` opens `STATE_COW_ENCOUNTER`. Player can MOO (random `_COW_MOO_MESSAGES`) or POKE (`_COW_POKE_MESSAGES`, counter `_cow_poke_count`). |
| 3 | 10th poke | `_enter_cow_level` fires: "The cow's eyes glow red. The ground splits open beneath you! MOO MOO MOO MOO MOO!" `_cow_return_level` is stashed, player teleports to `COW_LEVEL = 999` (`boss_levels.py:16`). |
| 4 | Moo Moo Farm | `_level_999_moo_moo_farm` (`boss_levels.py:562`) carves a 35x20 pasture ringed by fence-post walls, with a 6x4 **Cow King's Pen** sealed by a DOOR. Hell Bovines scatter across the pasture. Entry tile is a STAIRS_DOWN that is actually the **portal home**. |
| 5 | exit | Stepping on the portal → `_exit_cow_level` sets `_cow_level_done=True`, teleports back to `_cow_return_level`. Cow is gone (consumed), portal closes. |

### 2.10 Chain summary table

| Chain | Trigger items | Spawn floors | Altar / meeting floor | Reward |
|-------|---------------|--------------|-----------------------|--------|
| Ariadne | Bronze Bull | L12 | L17 fountain | Ariadne's Thread |
| Athena | Eye of the Graeae | L29 | L37 altar | Aegis of Athena |
| Odin / Gram | Broken Blade of Gram | L48 | L53 Odin's Altar | Sigurd's Shovel (+Gram if thrown over) |
| Gleipnir / Fenrir | 6 impossible components | L62, L65, L68, L71, L74, L77 | L76 Dwarven Forge | Gleipnir |
| Vidar | 10 leather scraps | L5-73 (10 fixed floors) | L79 Vidar's Altar | Vidar's Sandal |
| Judgment | 7 seals (seal-demon drops) | L83-97 (7 fixed floors) | L99 Altar of Judgment | 5 karma-tiered outcomes |
| Duck of Doom | Duck of Doom (armor) | L1-10 (one random) | n/a (2026 turns worn) | Waddlekind pet |
| Excalibur | Excalibur (weapon pool) | Gaussian unique spawn | n/a (HP ≤ 25% trigger) | kill_heal + 1-shot nova |
| Cow Level | — (NPC bump + 10 pokes) | L30-39 (one random) | L999 Moo Moo Farm | Hell Bovine loot pool |

### 2.11 Chain-equip tier bonuses

The nine chains do not currently stack a dedicated set-bonus
mechanic — the rewards are standalone items that each slot into the
normal equipment system. The one chain-aware mechanic in game is
`chain_passives.suryas_gift` (Kavacha-Kundala), which doubles
positive-karma NPC rewards (`game_encounters.py:741-750`). It is a
karma hook, not a quest-chain hook. See
[progression.md](progression.md) for the full chain-passive table.

---

## 3. The twelve mystery altars

Each mystery is an altar tile with a one-shot quiz challenge
attached. Spawn is probabilistic (see §4). All thresholds below are
the **v2.18 retuned values** — the pre-v2.18 numbers assumed the
old "mis-answer survives" semantics and were brutal under
zero-tolerance (one wrong = fail).

### 3.1 Common schema

Every entry in `mystery_system.MYSTERIES` carries:

| Field | Meaning |
|-------|---------|
| `name` | Display string |
| `floor_range` | `(lo, hi)` inclusive. The mystery is eligible iff the generating floor is inside this range. |
| `symbol` + `color` | Tile glyph for the altar (and for the key item, if any) |
| `description` | Flavor shown when the player approaches |
| `key_item` | None, or a dict `{name, symbol, color, weight}` describing the physical key the player must find on-floor. `None` means on-tile precondition (gold or Food) |
| `gold_cost` | Gold deducted on activation (only Oracle: 50) |
| `stat_cost` | Permanent stat delta applied **before** the quiz starts (only Mimir: `PER: -1`) |
| `challenge` | `{mode, subject, tier, threshold, total | max_chain | tiles}` |
| `reward` | Stats, max_hp bump, permanent `effects`, `gold`, or a `special` tag |
| `reward_text`, `fail_text`, `fail_reward` | Narrative on success / failure, plus Pandora's consolation |
| `invert_result` | Boolean. True ONLY for Pandora. See §3.4. |

Activation flow (`game_divine._begin_mystery_challenge`):

1. Apply `stat_cost` and `gold_cost` up front.
2. Consume the key item (except for Cauldron and Sisyphus).
3. For Cauldron, additionally consume 3 Food items.
4. Launch the quiz.
5. On completion, flip the altar to `activated=True` and remove it
   from `ground_items` so it can't be used twice.
6. Call `apply_mystery_reward` which routes stats / effects / gold /
   `special` tags. Pandora inverts the quiz result before this.

### 3.2 Mystery table (v2.18 thresholds)

| Mystery | Floor | Subject | Mode | Threshold | Pre-v2.18 | Key item (sym) | Reward |
|---------|-------|---------|------|-----------|-----------|-----------------|--------|
| **Solomon** | 30-42 | history T3 | threshold | **3** / 4 | 6 / 8 | Seal of Solomon (`*`) | WIS +2, Ring of Command |
| **Grail** | 45-55 | theology T3 | threshold | **2** / 7 | 5 / 7 | A Chalice (`U`) | max_hp +30, CON +2 |
| **Pandora** | 20-30 | economics T2 | threshold (inverted) | **2** / 5 | 4 / 5 | Pandora's Key (`P`) | magic_resist, displacement, +300 gold |
| **Sphinx** | 22-35 | philosophy T3 | escalator_threshold | **2** / 6 | 4 / 6 | — | WIS +2, INT +1 |
| **Mjolnir** | 33-45 | math T3 | escalator_threshold | **2** / 6 | 4 / 6 | Mjolnir (unfinished) (`^`) | Forge Mjolnir + STR +2 |
| **Oracle** | 25-35 | theology T3 | threshold | **2** / 7 | 5 / 7 | — (50 gold tribute) | Reveal 3 locked quirks |
| **Fisher King** | 58-72 | theology T4 | threshold | **2** / 7 | 5 / 7 | Healing Herb (`+`) | max_hp +30, `fisher_cooldown` (prayer cd halved) |
| **Mimir** | 42-55 | philosophy T4 | chain | **3** chain | 6 chain | — (PER -1 cost) | **WIS +1, INT +1** (v2.18) |
| **Fleece** | 38-50 | animal T3 | chain | 2 chain | 2 chain | Golden Fleece (`+`) | regenerating, poison_resist |
| **Crucible** | 10-22 | philosophy T1 | threshold | **3** / 4 | ~4 / 5 | Lead Ingot (`V`) | +400 gold |
| **Cauldron** | 14-26 | cooking T2 | threshold | **1** / 1 | 5 / 5 | — (3 Food) | searching, warning |
| **Sisyphus** | 78-92 | — | physical | **15 tiles** | 25 tiles | The Boulder (`*`, **20 lb**) | STR +3, INT +1 |

**v2.18 retune principle**: zero-tolerance semantics mean one wrong
answer ends a threshold quiz immediately, so pre-retune numbers like
"6 correct out of 8" were effectively "answer six philosophy T3
questions in a row perfectly." All thresholds were **halved** (or
reframed as 1-Q where appropriate) so the mysteries remain reachable
without feeling punitive to a competent player. Sisyphus boulder
weight also reduced from 30 lb → 20 lb, and the carry-tile count from
25 → 15.

Mimir's reward is the other v2.18 change: it was previously
`{'all_timer_bonus': 1}`, which populated `player.quiz_timer_bonuses`
for all 10 subjects — but **only math is actually timed in combat
chain mode**, so 9/10 of the bonus was dead and the reward text
("all quiz timers +1s") lied. v2.18 replaced it with a concrete
`{'WIS': 1, 'INT': 1}` stat bump that pairs honestly with the PER -1
up-front cost (net: WIS +1, INT +1, PER -1).

### 3.3 Challenge mode semantics

- **threshold** (`solomon`, `grail`, `pandora`, `oracle`, `fisher_king`,
  `crucible`, `cauldron`): must get `threshold` correct out of `total`.
  Under zero-tolerance, in practice the player must get the first
  `threshold` right (one wrong fails).
- **escalator_threshold** (`sphinx`, `mjolnir`): same bookkeeping as
  threshold, but questions escalate in tier each round (T1 → T2 → ...),
  capping at T5.
- **chain** (`fleece`, `mimir`): build a correct-answer chain; score
  is the chain length. Success is `result.score >= threshold`
  (`game_divine.py:258` adds this check manually because
  `QuizResult.success` is False for chain mode).
- **physical** (`sisyphus`): no quiz. The player must walk `tiles`
  tiles while over the carry limit, holding The Boulder (20 lb).
  State is tracked via `quirk_progress['sisyphus_boulder_active']`
  and `quirk_progress['sisyphus_boulder_tiles']`. On success, the
  boulder vanishes and the reward applies.

### 3.4 Pandora's inversion (`invert_result: True`)

Pandora is the only mystery with inverted quiz semantics. The design
beat: "Do not open the box. You'll want to open it." The quiz is
economics T2 threshold 2/5. The player's incentive is to **fail**.

Flow (`game_divine._begin_mystery_challenge` on_complete, L255-262):

```python
success = result.success
if ch['mode'] in ('chain', 'escalator_chain') and 'threshold' in ch:
    success = result.score >= ch['threshold']
if m.get('invert_result'):
    success = not success
apply_mystery_reward(..., success)
```

- Quiz success (player answered correctly) → `success = False`
  → `fail_reward: {gold: 100}` runs and `fail_text` plays:
  "You open it 'correctly' — but nothing is inside. Only gold."
- Quiz failure (player got one wrong) → `success = True`
  → full `reward` runs: `effects: ['magic_resist', 'displacement']`
  + 300 gold + `reward_text` ("The box opens wrong — chaos
  floods out... and so does Hope.").

The on-screen quiz UI does not telegraph the inversion. Discovery is
part of the mystery; the description "Do not open. The keyhole glows
red" is the only clue.

### 3.5 Per-mystery detail

**Solomon's Tribunal** (`solomon`) — "A throne room with two doors."
`history T3 threshold 3/4` with Seal of Solomon in-hand. Reward:
WIS +2 **and** a Ring of Command (accessory, +1 WIS, `quiz_tier: 5`)
auto-identified into inventory. `special: 'ring_of_command'`.

**Chapel of the Grail** (`grail`) — "A ruined chapel. A chalice rests
on the altar, glowing faintly." `theology T3 threshold 2/7`. Reward:
max_hp +30, CON +2. Narrative: "You are found worthy."

**Pandora's Coffer** (`pandora`) — See §3.4. Inverted. Reward on
intentional "failure": permanent magic_resist, permanent displacement,
+300 gold.

**The Sphinx** (`sphinx`) — "A towering stone sphinx fixes you with
ancient eyes." `philosophy T3 escalator_threshold 2/6`. No key item.
Reward: WIS +2, INT +1.

**The Dwarven Forge** (`mjolnir`) — "A dwarven forge, still hot."
`math T3 escalator_threshold 2/6`. Key: Mjolnir (unfinished), 8.0 lb.
Reward on success: `special: 'forge_mjolnir'` → a brand-new Mjolnir
weapon (3d6, +4 enchant, baseDamage 18, blunt, chainMultipliers
[0.5, 1.0, 1.5, 2.0, 2.5, 3.0]) is created and placed in inventory,
and STR +2 applies. The unfinished key is removed first to avoid
dupes.

**The Oracle's Rift** (`oracle`) — "A smoking rift in the stone,
tended by a stone priestess." `theology T3 threshold 2/7` with
**50-gold tribute** up front (`gold_cost: 50`). No key item. Reward
on success: `special: 'oracle_reveal'` → `_oracle_reveal_quirks`
picks up to 3 of the player's locked quirks and reveals a cryptic
one-line hint for each (odin, mithridates, tiresias, penelope,
orpheus, hermes, atalanta, musashi, scheherazade, merlin, prometheus,
ragnarok). On total unlock the Oracle says "You have walked all
paths. Remarkable."

**The Fisher King's Hall** (`fisher_king`) — "A desolate hall. A
wounded king lies motionless." `theology T4 threshold 2/7` with
Healing Herb in-hand. Reward: max_hp +30, **plus
`special: 'fisher_cooldown'`** which sets
`player.quirk_progress['fisher_king_mystery_active'] = True`. See
[karma_prayer §7](karma_prayer.md) for how
`_apply_prayer_cooldown_quirks` consumes this flag to halve prayer
cooldown permanently (and stacks with the Fisher King **quirk** for
quartered cooldown).

**Mimir's Well** (`mimir`) — "A dark well with runes carved around
its rim. The water below holds all wisdom. A price is implied."
`philosophy T4 chain, threshold 3`. **Up-front cost: PER -1** (applied
before the quiz launches, with message "You feel a part of yourself
drain away as payment..."). Reward: WIS +1, INT +1 (v2.18 — see §3.2).

**The Fleece Altar** (`fleece`) — "An altar carved with the image of
a ram." `animal T3 chain, threshold 2`. Key: Golden Fleece, 2.0 lb.
Reward: permanent regenerating and poison_resist.

**Alchemist's Crucible** (`crucible`) — "An alchemist's crucible.
'From base matter, golden truth.'" `philosophy T1 threshold 3/4`.
Key: Lead Ingot, 5.0 lb. Reward: +400 gold.

**The Black Cauldron** (`cauldron`) — "A bubbling cauldron of Celtic
make." No key item; **requires 3 Food items in inventory** at
activation time. `cooking T2 threshold 1/1` — a single one-question
gate. Reward: permanent searching + warning.

**Sisyphus' Hill** (`sisyphus`) — "A steep slope carved into the
stone." Physical challenge: walk 15 tiles while over the carry limit,
holding The Boulder (20 lb). No quiz. Reward: STR +3, INT +1. See
also [progression.md](progression.md) for the `sisyphus` quirk, which
is a parallel 100-floor-at-STR-5 achievement, not this mystery.

### 3.6 Mystery key item inventory

The physical key items for mysteries use their own class
(`MysteryKeyItem`, `mystery_system.py:194`) that is not an Item but
walks and talks like one for inventory/display purposes.

| Mystery | Key name | Symbol | Weight | Color |
|---------|----------|--------|--------|-------|
| solomon | Seal of Solomon | `*` | 0.5 | gold (255, 220, 50) |
| pandora | Pandora's Key | **`P`** | 0.5 | dark red (180, 30, 30) |
| grail | A Chalice | `U` | 1.0 | silver-blue (200, 200, 255) |
| fleece | Golden Fleece | `+` | 2.0 | golden (218, 165, 32) |
| mjolnir | Mjolnir (unfinished) | `^` | 8.0 | orange (255, 140, 0) |
| crucible | Lead Ingot | `V` | 5.0 | gray (150, 150, 160) |
| fisher_king | Healing Herb | `+` | 0.5 | light green (100, 220, 100) |
| sisyphus | The Boulder | `*` | **20.0** | stone gray (140, 140, 140) |

> **Known collision: Pandora's Key uses symbol `P`, which is also the
> player's default tile character.** On a floor with Pandora
> eligible, a dropped Pandora Key renders identically to the player
> on the map. The dungeon generator currently places both symbols
> through separate paths, so visual confusion is possible but not a
> functional bug. Flagged for future replacement.

Mysteries without a `key_item` entry (`sphinx`, `mimir`, `oracle`,
`cauldron`, `sisyphus`) either use an on-tile precondition (gold
tribute, 3 Food, boulder) or require no physical token. The boulder
for Sisyphus is spawned on-level and is counted as a key item for
inventory-check purposes but is **not consumed** on activation (it is
dropped as part of the physical challenge instead).

---

## 4. Mystery spawn pipeline

### 4.1 Per-level roll

Every generated level runs `spawn_mystery_for_level`
(`mystery_system.py:266`):

```python
eligible = [mid for mid, m in MYSTERIES.items()
            if m['floor_range'][0] <= level <= m['floor_range'][1]]
if not eligible:
    return None
if rng.random() > 0.60:
    return None
mystery_id = rng.choice(eligible)
```

Six observations:

1. **60% spawn rate per generated level** (`rng.random() > 0.60`
   gate). Not per-run — per-generation.
2. **No lifetime cap**: nothing tracks "this mystery already fired."
   The same mystery can regenerate on a save/reload (or on a later
   visit if the dungeon regenerates the floor) because the gate is
   purely RNG. SYSTEMS_AUDIT §3 flags this as "spawn_mystery_for_level —
   60% per generation, no lifetime cap. Same mystery
   re-generatable on save/reload if never triggered."
3. **Altar placement**: picked `altar_room` is any room except
   `rooms[0]` (start room). Any walkable tile not already holding a
   ground item is used.
4. **Key placement**: if the mystery has a key item, the key is
   placed in a **different** room from the altar when possible
   (`key_rooms = [r for r in non_start_rooms if r is not altar_room]`).
   Fallback: same non-start pool.
5. **Mysteries don't block regular items** — they stack cleanly with
   the normal floor loot generation.
6. **Floor ranges overlap**: a floor in L22-26 is eligible for
   sphinx, oracle, mjolnir, pandora, cauldron, and crucible. One is
   chosen uniformly at random when the 60% roll succeeds.

### 4.2 Activation requirements

`can_activate(mystery_id, player, player_gold)` (`mystery_system.py:333`)
runs when the player presses `o` adjacent to the altar:

- Gold cost check: fails if `player_gold < gold_cost`.
- Key item check: fails if the mystery has a `key_item` and the
  player's inventory doesn't contain a `MysteryKeyItem` with
  `mystery_id` matching (skipped for Sisyphus and Cauldron).
- Sisyphus: must have The Boulder in inventory.
- Cauldron: must have ≥3 Food items (ingredients count too, via the
  `cauldron` branch in `get_cauldron_food_items`).

Failure returns `(False, reason_string)` which is surfaced to the
player as a yellow warning line.

### 4.3 Reward routing

`apply_mystery_reward` (`mystery_system.py:438`) handles:

| Reward dict key | Effect |
|-----------------|--------|
| `STR`, `CON`, `DEX`, `INT`, `WIS`, `PER` | `player.apply_stat_bonus(stat, amount)` |
| `max_hp: N` | `player.max_hp += N`; current HP topped up by same amount |
| `effects: [name, ...]` | Each effect added with duration -1 (permanent) |
| `gold: N` | `game.player_gold += N` |
| `all_timer_bonus: N` | (legacy, pre-v2.18 Mimir) populates `player.quiz_timer_bonuses` for all 10 subjects — only math is read in practice. |
| `special: 'forge_mjolnir'` | Spawns the fully-forged Mjolnir weapon in inventory (plus STR +2 from the parallel `STR` key). |
| `special: 'ring_of_command'` | Spawns the Ring of Command accessory in inventory. |
| `special: 'oracle_reveal'` | Runs `_oracle_reveal_quirks` for up to 3 cryptic locked-quirk hints. |
| `special: 'fisher_cooldown'` | Sets `player.quirk_progress['fisher_king_mystery_active'] = True` for permanent prayer-cd halving. |

Failure path: `fail_reward` is applied if present (currently only
Pandora's gold-100 consolation), then `fail_text` prints as a warning.

---

## 5. v2.18 artifact `unidentified_name` sweep

Before v2.18, pickup of a quest artifact rendered its **true name**
on the message log — "You pick up the Scales of Michael." — because
24 artifacts in `data/items/artifact.json` were missing the
`unidentified_name` field. This spoiled the plot and made the identify
pipeline cosmetic for these items. v2.18 added `unidentified_name`
to all 24.

Counts (from `grep unidentified_name data/items/artifact.json`): 26
artifacts in artifact.json carry an `unidentified_name`, of which the
24 added in v2.18 cover every quest / plot item.

Representative additions:

| Artifact id | True name | `unidentified_name` |
|-------------|-----------|---------------------|
| `philosophers_stone` | Philosopher's Stone | "smooth red stone" |
| `bronze_bull` | Bronze Bull Idol | "bronze figurine" |
| `eye_of_graeae` | Eye of the Graeae | "cloudy glass eye" |
| `cats_footstep` | Sound of a Cat's Footstep | "silvery whisper in a bottle" |
| `womans_beard` | Roots of a Woman's Beard | "wisps of fine hair" |
| `mountain_root` | Root of a Mountain | "chunk of dark stone" |
| `fish_breath` | Breath of a Fish | "sealed vial of mist" |
| `bird_spittle` | Spittle of a Bird | "tiny sealed vial" |
| `bear_sinew` | Sinew of a Bear's Sensitivity | "coiled thread" |
| `gleipnir` | Gleipnir | "impossibly thin ribbon" |
| `leather_scrap` | leather scrap | "leather scrap" (identified on spawn — no spoiler risk) |
| `seal_of_wrath` ... `seal_of_silence` | Seal of X | "sealed metal disc (red/green/black/rust/pale/grey/silver)" (7 seals, one per color) |
| `scales_of_michael` | Scales of Michael | "ornate golden scales" |
| `cursed_lodestone` | Cursed Lodestone | "dark magnetic stone" |
| `sealed_dispatch` | Sealed Dispatch | "wax-sealed letter" |
| `palladium` | Palladium | "ancient wooden idol" |
| `tablet_of_destinies` | Tablet of Destinies | "obsidian tablet" |
| `vidars_sandal` | Vidar's Sandal | "old leather sandal" |

Combined with `_meta: { plot_locked: true }` on the deepest plot
items (Philosopher's Stone, Bronze Bull), the identify-tier pipeline
now treats these like any other artifact: the player sees "pick up a
smooth red stone", and only philosophy-quiz identification (identify
v3) resolves the true name — unless an `identified: true` override
exists on `special_properties`, which is the case for every Gleipnir
component (they're identified on pickup so the player can act on them
immediately).

Related v2.18 SYSTEMS_AUDIT P2 fix flagged but not yet applied:
`palladium` and `tablet_of_destinies` have `id_level: null`, which
flows through `int(defn.get("id_level", 5 if identified else 0))` and
could raise `TypeError` on `int(None)` unless coerced upstream.

---

## 6. State flags cheat-sheet

Quest and mystery state spread across `Game` and `Player`:

| Flag | Owner | Purpose |
|------|-------|---------|
| `game.seals_broken: set[str]` | Game | 7-seal pickup tracker; descent to L100 gated on `len() == 7` |
| `game._judgment_resolved: bool` | Game | L99 altar one-shot flag |
| `game._abaddon_empowered: bool` | Game | Judgment outcome `abaddon_empowered` — read on L100 spawn |
| `game._locusts_strengthened: bool` | Game | Judgment outcome `locusts_strengthened` — read on L100 spawn |
| `game._cow_level: int` | Game | Chosen L30-39, where the cow lives |
| `game._cow_spawned`, `_cow_level_done` | Game | Cow placement + farm-visited flags |
| `game._cow_poke_count: int` | Game | 10-poke trigger for cow dimension |
| `game._cow_return_level: int` | Game | Where to return from the farm |
| `game._duck_of_doom_floor: int` | Game | Chosen L1-10, where the Duck drops |
| `game._duck_of_doom_placed: bool` | Game | Prevents double-spawn |
| `player.quirk_progress['duck_of_doom_turns']: int` | Player | Counts up to 2026 |
| `player.quirk_progress['sisyphus_boulder_active']: bool` | Player | Sisyphus physical challenge arming |
| `player.quirk_progress['sisyphus_boulder_tiles']: int` | Player | Progress toward 15-tile goal |
| `player.quirk_progress['fisher_king_mystery_active']: bool` | Player | Permanent prayer-cd halving (mystery branch) |
| `game.player.divine_intercession_used: bool` | Player | 1/run gate for Shift+\ |
| `game._active_mystery_altar` | Game | Mystery currently being approached (STATE_MYSTERY_APPROACH) |
| `game._chronicle_first_mystery: bool` | Game | One-shot chronicle entry on first mystery discovery |
| `MysteryAltar.activated: bool` | item | Set to True on challenge completion; also removed from `ground_items` |

Save/load: `seals_broken`, `_cow_*`, `_cow_poke_count`, `_duck_*`,
`karma` are all round-tripped by `save_system.save_game` /
`main.py:_load_game`. The Mystery altars themselves are serialized as
part of `ground_items`. `quirk_progress` is on `Player` and persists
via the normal save path.

---

## 7. Audit-flagged open items

From SYSTEMS_AUDIT.md §3 (Quest systems + secret builds), these are
the P1/P2 items that affect this doc's scope and remain open as of
v2.18.0:

- **Mystery spawn has no lifetime cap** — the 60% roll can
  regenerate the same altar across save/load cycles. Pre-v2.18 this
  was less visible because mysteries fired less often; post-threshold-halve
  they fire more. Design decision pending: add a run-scoped
  `game._mysteries_fired: set` and gate against it.
- **`mimir_reward` `all_timer_bonus` was dead-code** — fixed in v2.18
  by swapping to `{WIS: 1, INT: 1}`.
- **Pandora's Key uses symbol `P`** — collision with player glyph.
  Non-blocking visually (different render pass), but a UX smell.
- **Judgment karma=10 is reachable but fragile** — ten "+1" blocks
  must all land. See [karma_prayer §2](karma_prayer.md) for how
  karma is accumulated.
- **`judge_karma` fallback branch is unreachable** per docstring; the
  karma-clamp invariant makes the loop complete. Dead code; keep
  as belt-and-braces.
- **24 artifacts needed `unidentified_name`** — fixed in v2.18.
- **`palladium.id_level` and `tablet_of_destinies.id_level` are
  `null`** — pending; probably `int(None)` → TypeError risk on an
  identify pipeline that uses them without the `or 0` guard.

---

## 8. Where things live (file index)

```
src/mystery_system.py        -- MYSTERIES dict, MysteryAltar/MysteryKeyItem
                                classes, spawn_mystery_for_level,
                                can_activate, apply_mystery_reward,
                                _oracle_reveal_quirks, MerchantNPC
src/game_divine.py           -- _start_mystery, _begin_mystery_challenge,
                                _activate_ariadne_shrine, _activate_athena_shrine,
                                _activate_odin_shrine, _check_gleipnir_forge,
                                _check_vidar_altar
src/game_combat.py:293       -- _throw_weapon (Odin reforge path)
src/game_encounters.py       -- _resolve_judgment, cow level handlers,
                                unicorn state machine, Magic Carrot spawn
src/main.py:4357             -- Duck of Doom lifecycle (place, pickup,
                                tick, transform)
src/main.py:6697-6730        -- Drop-based trigger routing (Ariadne/Athena/
                                Odin/Gleipnir/Vidar)
src/main.py:2715-2722        -- Seven Seals descent gate on L99→L100
src/boss_levels.py:16-554    -- COW_LEVEL constant + Moo Moo Farm generator
src/dungeon.py:1873-2587     -- Quest-floor spawns (bull, eye, gram, scraps,
                                Gleipnir components) and shrine carvers
                                (Ariadne, Athena, Odin, Gleipnir forge,
                                Vidar altar, Judgment altar)
src/level_manager.py:236-287 -- _SEAL_DEMON_LEVELS + forced-spawn
data/items/artifact.json     -- 24 quest artifacts, all with v2.18
                                unidentified_name entries
```

---

## 9. Related reading

- [karma_prayer](karma_prayer.md) — Prayer v2, Divine Intercession,
  Fisher-King-mystery cooldown halving, Judgment outcome details,
  karma scale and 30 karma NPCs.
- [items](items.md) — Full artifact pool, BUC rolls, identify
  pipeline, unique drop rates.
- [progression](progression.md) — Quirks (odin, mithridates, tiresias,
  …), hero specials, chain passives like `suryas_gift`.
- [world](world.md) — Dungeon generation, bones/ghost pipeline, boss
  level framework.
- [combat](combat.md) — Chain-mode scoring, Divine Intercession
  invulnerable buff, seal-demon kill routing.
