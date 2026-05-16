# Divine Systems — Karma, Altars, Prayer, Michael, Seals

A reference map of every divine / karma / altar / prayer mechanic in
Philosopher's Quest. Read-only audit; no fixes proposed. All claims cite
`file:line`.

---

## 1. Karma — the moral economy

### 1.1 Where karma is tracked

- **Field:** `self.karma: int` on the `Game` object, initialised to `0`
  (`src/main.py:181`).
- **Bounds:** clamped `-10..+10` at every update (`src/game_encounters.py:730`).
- **Persistence:** saved/loaded as `'karma'` (`src/save_system.py` via
  `state.get('karma', 0)` at `src/main.py:325`).
- **Display:**
  - Sidebar value in the L99 judgment overlay (`src/game_render.py:949`,
    border color shifts gold/red/grey by sign at `:932-937`).
  - Death-screen / chronicle summary line `f"Karma:{karma:+d}  Effects: ..."`
    (`src/game_render.py:3471-3474`).
  - **Karma is NOT shown in the normal HUD** — the player must infer their
    score from NPC encounter framing. (Confirmed: no other render path.)

### 1.2 The ONLY source of karma changes

Karma changes ONLY through NPC moral encounters (`game_encounters.py:728-730`):

```python
old_karma = self.karma
self.karma = max(-10, min(10, self.karma + karma_delta))
```

- **No karma from kills.** Grep across `src/`: `karma` never appears in
  `game_combat.py`. Killing pets, NPCs-as-monsters, or seal demons does
  nothing to karma.
- **No karma from item use, prayer, scroll reading, harvesting,** or any
  other mechanic. The grep coverage is exhaustive (one file, one delta path).
- **Flavor encounters explicitly skip karma** — `_npc_is_flavor = True` flag
  (`game_encounters.py:545`) routes them through `_apply_npc_choice` with
  `karma_delta = opt.get('karma', 0)` (default 0).

### 1.3 NPC encounter karma economy

- **10 encounters per run, one guaranteed per 10-level block** — blocks
  L3-9, L11-19, L21-29, ..., L91-98 (`src/npc_encounters.py:14-26`,
  `src/npc_encounters.py:1824-1858`).
- **Each encounter offers 3 options** with karma deltas of `+1`, `0`, `-1`
  respectively (~30 NPC encounters defined, lines 72-2027 in
  `npc_encounters.py`).
- **Theoretical karma range achievable: -10..+10** (one delta per block ×
  10 blocks). The clamp `max(-10, min(10, ...))` is precisely tuned to this
  range.
- **NPC encounters do not spawn on boss levels** (L20, L40, L60, L80, L100;
  `npc_encounters.py:12`).
- **Trigger-item encounters:** 3 of the 30 encounters require the player to
  be carrying a specific item (`silverlight_pendant`, `oathkeeper_sword`,
  `lionheart_shield` — `npc_encounters.py:82,417,1374`). The trigger item
  spawns 1-3 levels before the NPC (`get_trigger_item_levels`,
  `npc_encounters.py:1860-1872`).

### 1.4 Chronicle hooks at karma extremes

Hit `karma == 10` for the first time → chronicle entry
*"I feel... clean. Like everything I've done down here has mattered..."*
(`game_encounters.py:731-732`).

Hit `karma == -10` for the first time → chronicle entry
*"Something inside me has gone cold..."* (`:733-734`).

### 1.5 Karma read-gates (where karma actually matters)

Only 2 places in the codebase read karma to gate content:

1. **Unicorn trust quiz** (`game_encounters.py:328-335`): if `karma < 0`,
   the unicorn recoils, flees, and `unicorn.alive = False`. No second
   chance per run (unicorn is spawned at most once per run).
2. **L99 judgment altar** (`game_encounters.py:931`,
   `npc_encounters.py:2030-2045`): see Section 4 for tiers.

That's it. Karma is essentially a holdout variable that pays out at L99.

---

## 2. Altars

Altars use a single tile constant `ALTAR = 6` (`src/dungeon.py:31`). The
game distinguishes altar *roles* by position (`dungeon.judgment_altar_pos`,
`dungeon.odin_altar_pos`, `dungeon.vidar_altar_pos`, `dungeon.dwarven_forge_pos`)
and by floor number, not by tile type.

### 2.1 Generic altars (procedural)

- **Spawn rule:** in `_apply_terrain`, an altar is placed in a random
  non-start room when `level % 15 == 1` (`src/dungeon.py:326-336`).
  This means **L1, L16, L31, L46, L61, L76, L91**.
- **L76 collision:** L76 also gets the Dwarven Forge (`dungeon.py:1572-1574`)
  which reuses ALTAR tile (`dungeon.py:2140-2142`). One floor, potentially
  two altar tiles, both walkable, only the forge one has special semantics.
- **Special "shrine" rooms** can also place an altar tile
  (`dungeon.py:1368-1373`) when a room is generated with `room_type == 'shrine'`.

**Effects at a generic altar:**

1. **BUC blessing** — drop an item on the altar to bless/uncurse it via a
   theology escalator_chain quiz; `chain >= 3` blesses, `chain >= 1`
   uncurses (`game_divine.py:184-233`).
2. **BUC identification** — stand on altar and use the "divine BUC" action
   (`_altar_buc_identify`, `game_divine.py:235-281`); threshold-1 theology
   quiz reveals BUC status of one inventory item.
3. **Prayer at altar** — kneeling on an altar tile gives `+1` to effective
   chain ("the altar amplifies your prayer", `game_divine.py:702-704`); see
   Section 3.

### 2.2 Boss-arena and quest altars

| Altar | Floor | How placed | Purpose |
|---|---|---|---|
| Medusa's nave altar | L40 | Hand-placed at nave center, `boss_levels.py:221` | Generic altar (prayer + BUC). No boss-quest hook. |
| Odin's altar | **L53** (not L80) | `dungeon.py:1538-1540` → `_create_odin_shrine` (`dungeon.py:1789-1808`) | Drop Broken Gram → Odin speaks + opens sealed shrine (Sigurd's Shovel). **Secret: throw Gram OVER altar to reforge.** See `game_divine.py:411-461` and `game_combat.py:287` (throw detection). |
| Asterion's labyrinth | L20 | None placed | No altar in `_level_20_labyrinth` (`boss_levels.py`). |
| Fafnir's hoard | L60 | None placed | No altar in `_level_60_lair`. |
| Fenrir's hall | L80 | One in central hall, `boss_levels.py:369` | Generic altar (works as normal prayer altar in boss room). |
| Abaddon's Abyss | L100 | **Ring of 6 altars** around the boss chamber, `boss_levels.py:468-478` | Holy-fire altars — single-use each, strip Abaddon's resistances. See Section 2.3. |
| Cow Level (L999) | — | None | |

### 2.3 L100 altar ring — the resist-strip burst mechanic

`boss_levels.py:468-478` places 6 altars at offsets
`(±8, 0), (0, ±8), (-6, -6), (+6, -6)` around the boss-room center
`(39, 28)`. (Comment says "6 altars for holy fire prayers".)

**Code path for L100 altar prayer** (`game_divine.py:750-777`):

- Check `self.dungeon_level == 100 and at_altar`.
- If `(p.x, p.y) in self._l100_altars_used`: already spent — message
  *"This altar's holy power has been spent."*
- Else if `chain > 0`:
  - `turns = chain * 2`
  - `self.abaddon_resist_removed_turns += turns` (additive! stacking from
    multiple altars accumulates the duration)
  - Find Abaddon, set `abaddon.resistances = []` (full strip).
  - Add `(p.x, p.y)` to `_l100_altars_used`.
  - **Returns immediately** — does NOT grant the standard prayer boon.
  - Cooldown set: `max(100, 80 + effective * 25)`.
- Else (chain == 0): also adds to `_l100_altars_used` ("The heavens are
  silent"). **An altar is consumed even by a failed prayer at chain 0.**

**Resist restore:** `main.py:1542-1551` decrements the counter each turn
and, when it hits 0, restores `abaddon.resistances = list(base_resistances)`
with message *"The holy fire fades. Abaddon's dark armor reforms."*

**Max theoretical window:** 6 altars × chain 8 × 2 = 96 turns, but only if
all 6 prayers chain perfectly. Realistic: 6 × chain 4 × 2 = 48 turns.

### 2.4 Hidden / mystery altars (separate system)

The mystery system uses a completely separate object (`MysteryAltar`,
`mystery_system.py:215-234`) that sits in `ground_items` rather than as a
tile. These are **NOT** ALTAR tiles and don't intersect with prayer.

5 mystery altars defined (`mystery_system.py:MYSTERIES`):

| Mystery | Floors | Subject (challenge) | Key item | Reward |
|---|---|---|---|---|
| `pandora` | ? | (see mystery_system.py) | Sealed Box | inverted result |
| `mjolnir` | ? | history | Mjolnir hammer | unique |
| `oracle` | ? | philosophy | (varies) | reveals quirks |
| `fisher_king` | L58-72 | theology T4 (threshold 5/7) | Healing Herb | +30 max HP, **prayer cooldown halved forever** |
| `sisyphus` | L78-92 | physical (walk 25 tiles overloaded) | Boulder | STR+3, INT+1 |
| `cauldron` | L14-26 | cooking | (3 food) | permanent searching + warning |
| `solomon` | ? | philosophy | (see) | WIS+2, Ring of Command |

(Spawn: 60% chance per floor that has any eligible mystery,
`mystery_system.py:282-283`.)

**Mystery-altar cross-link to prayer:** the Fisher King mystery sets
`player.quirk_progress['fisher_king_mystery_active'] = True`
(`mystery_system.py:537-539`), which is checked at
`game_divine.py:784-785` to halve prayer cooldown a second time. See
Section 7.

### 2.5 L99 — The Altar of the Last Judgment

- Guaranteed single creation on L99 in the largest non-start room
  (`dungeon.py:1580-1582`, `_create_judgment_altar` at
  `dungeon.py:2157-2167`).
- Position stored at `dungeon.judgment_altar_pos`.
- **Triggered by praying while standing on it** (`game_divine.py:684-693`).
- **NOT cooldown-gated.** The judgment short-circuits cooldown check.
- **One-shot per run** — `self._judgment_resolved` flag prevents re-trigger.
- Routes to `_resolve_judgment` (`game_encounters.py:928-994`). See
  Section 4 for tier outcomes.

### 2.6 Other dungeon-specific quest altars (using ALTAR tile)

- **Dwarven Forge (L76)** — `dungeon.py:2133-2142`. Visually an altar; on
  bump or drop, checks if all 6 Gleipnir components are present
  (`game_divine.py:472-497`). Forges Gleipnir.
- **Vidar's Altar (L79)** — `dungeon.py:2145-2154`. Drop 10 leather scraps
  → Vidar's Sandal (`game_divine.py:499-521`).
- **Ariadne's shrine (L17)** — `dungeon.py:1501-1503`, but Ariadne is
  activated by dropping the Bronze Bull at a **fountain**, not an altar
  (`game_divine.py:362-385`).
- **Athena's shrine (L37)** — `dungeon.py:1522-1524`. Player drops Eye of
  the Graeae at the L37 altar → Athena opens shrine to Aegis
  (`game_divine.py:387-409`).

---

## 3. Prayer

### 3.1 The prayer quiz

- Action key: `\` (backslash).
- Mode: `escalator_chain`, subject: `theology`, tier 1, `max_chain=8`
  (`game_divine.py:718-728`).
- Timer: theology budget @ `46s @ WIS 10` (per CONTEXT.md table) + WIS
  bonus + extra seconds.
- Result.score = chain length 0..8.

### 3.2 Effective chain

`effective = chain + (1 if at_altar else 0)` (`game_divine.py:747`). With
chain 8 + altar bonus, effective can be 9 (used for verse lookup which
caps at 8).

### 3.3 Cooldown

`p.prayer_cooldown = max(100, 80 + effective * 25)` (`game_divine.py:780`).

| effective | cooldown (base) |
|---|---|
| 0 | 100 (the `max(100, 80)` floor) |
| 1 | 105 |
| 2 | 130 |
| 3 | 155 |
| 4 | 180 |
| 5 | 205 |
| 6 | 230 |
| 7 | 255 |
| 8 | 280 |
| 9 | 305 |

**Modifiers (stack multiplicatively, both halving):**
- Fisher King quirk: `// 2` if `quirk_progress['fisher_king_active']`
  (`game_divine.py:781-782`).
- Fisher King mystery reward: `// 2` again if
  `quirk_progress['fisher_king_mystery_active']` (`:783-785`).

**Combined effect with both active:** cooldown approximately **/4** → at
effective 8, 280/4 = 70 turns. At effective 0, `max(1, max(1, 100//2)//2)
= max(1, 50//2) = 25` turns.

**Cooldown ticks** at `main.py:1535-1536` (every turn).

### 3.4 Per-chain reward table (non-L100, non-L99-judgment)

For `effective` (chain + altar bonus) when **not on L100**:

| effective | Reward (`game_divine.py:799-900`) |
|---|---|
| 0 | "The heavens are silent." Nothing. |
| ≥1 | Remove one minor status (confused/bleeding/slowed/sleeping) **OR** +5% max SP. |
| ≥2 | Remove one major status (poisoned/paralyzed/blinded) **OR** uncurse all cursed equipped items + inventory **OR** remove one minor status **OR** +10% max SP. |
| ≥3 | Cleanse ALL negative status effects (poisoned/paralyzed/confused/bleeding/blinded/sleeping/slowed/weakened/cursed) **OR** +20% max SP. |
| ≥4 | +30% SP. |
| ≥5 | +60% SP, +20% HP. |
| ≥6 | Full SP, +50% HP. |
| ≥7 | Full HP **and** full SP. |
| ≥8 | First 3 times in run: **+1 WIS permanent** + full HP+SP. After 3 boons: full HP+SP only. |

The cascade is `if effective >= 8 ... elif effective >= 7 ...` — each
tier subsumes lower ones, only the highest applies.

**The `prayer_boon_count` cap** (`game_divine.py:803-806`,
`player.py:66`): only 3 permanent WIS gains from chain-8 prayers per run.

### 3.5 Bible verses on success

`_PRAYER_VERSES` table at `game_divine.py:735-745` maps `effective` 1-8 to
KJV citations (1 Peter 5:7, 1 John 1:9, Psalm 147:3, Isaiah 40:31, Psalm
23:1, Philippians 4:13, Isaiah 41:10, Matthew 25:23). At chain 0 verse is
`None`. Verse line is shown with `'loot'` color, citation in `'info'`
(`:905-911`).

For L100 altar prayer the verse is also displayed but only on success
(`:769-771`).

### 3.6 Death-chase prayer side effect

If `self.death_pursues and self.death_monster is not None`
(`game_divine.py:792-797`): set `self.death_monster._frozen_turns =
min(8, 3 + effective)`. **This runs in parallel with the boon — it does
NOT replace it.** Death freezes for 4-8 turns at effective 1-5+.

Chronicle is logged the first time this happens: *"Prayed while Death
hunted me. It froze in place. {N} turns. That's all I get."*

### 3.7 First-prayer chronicle

`_chronicle_first_prayer` is set when prayer happens at an altar
(`game_divine.py:732-734`): *"Prayed at an altar. Something listened. I
felt it."* Note: only triggers if `at_altar=True`. Praying off-altar on
the first prayer of the run does NOT trigger this entry.

### 3.8 Prayer's quirk-triggering payload

After a successful prayer (chain > 0), `quirk_system.on_prayer(hp_pct)` is
called (`game_divine.py:712-715`). See Section 7.1.

---

## 4. Michael's gift tiers

The Altar of the Last Judgment on L99 (Section 2.5) routes to
`_resolve_judgment` → `npc_encounters.judge_karma(self.karma)`
(`game_encounters.py:928-994`).

### 4.1 The 5 outcomes (`npc_encounters.py:1989-2027`)

| Karma | Outcome key | Reward |
|---|---|---|
| 10 | `sword_and_scales` | **Sword of Michael + Scales of Michael + Paladin title** |
| 1..9 | `scales_granted` | Scales of Michael only |
| 0 | `silence` | Nothing |
| -1..-5 | `locusts_strengthened` | **Abaddon's locust swarms grow +2..+3** |
| -6..-10 | `abaddon_empowered` | **Abaddon gets +50% HP** |

### 4.2 Tier-1 — Scales of Michael (karma 1..9)

- Item: `scales_of_michael` (`data/items/artifact.json:245-257`).
- Class: Artifact, weight 0.5, symbol `=`.
- **Lore:** *"In the final battle against the Destroyer, the Host answers
  the call of these scales. For every locust of the Abyss, an angel
  descends."*
- **Mechanic:** While in inventory, the Power menu shows "Summon the
  Heavenly Host" (`game_menus.py:697-705`). Activating sets
  `game.heavenly_host_active = True` and consumes the one-shot use
  (`:1010-1016`).
- **Effect:** in `_spawn_abaddon_locusts` (`main.py:3079-3094`), when
  Abaddon spawns locusts, an equal number of `heavenly_angel` monsters
  spawn near the player to counter them.

### 4.3 Tier-2 — Sword of Michael (karma == 10)

- Item: `sword_of_michael` (`data/items/weapon.json:8591-8640`).
- **Stats:**
  - baseDamage 45
  - mathTier 5, maxChainLength 9
  - chainMultipliers `[0.5, 1.2, 2.0, 3.2, 4.8, 6.5, 9.0, 12.0, 16.0]`
  - critMultiplier **4.0** (the numerical outlier flagged in
    `REVERSE_ENGINEERED.md`)
  - damageTypes `["holy", "slash"]`
  - `ignoreShield: true`
  - `ignore_resistances: true` (bypasses all monster resistances —
    `combat.py:84-85`)
  - `abaddon_bonus_damage: "6d10"` (bonus damage vs Abaddon only —
    `combat.py:157-160`)
  - stunChance 0.15, value 25000
- **min_level: 9999** — never spawns in normal loot, only awarded by
  judgment.

At karma 10 the player ALSO receives Scales of Michael
(`game_encounters.py:953-960`) and `player_title = 'Paladin'` is set
(`:938`).

### 4.4 Tier-3 (negative) — Abaddon empowered

When `_abaddon_empowered = True` is stored (`game_encounters.py:982`),
the next time the player enters L100 (`main.py:464-472`), Abaddon's
max_hp and current hp are increased by 50% (5000 → 7500 base; 8250 if
saved-and-loaded combine doesn't apply, but the `not saved` guard
prevents double-apply).

### 4.5 Tier-3.5 (negative) — Locusts strengthened

When `_locusts_strengthened = True` (`game_encounters.py:988`), every
locust spawn in `_spawn_abaddon_locusts` adds `lo += 2, hi += 3` to the
swarm count (`main.py:3036-3039`). Base locust_count is `[3, 5]` for
Abaddon (`monsters.json:19904-19907`), so penalized: `[5, 8]`.

### 4.6 Chronicle entries per outcome

Every judgment outcome writes a chronicle entry
(`game_encounters.py:961, 976, 983, 989`). Examples:

- Paladin: *"...a sword of white fire and the scales themselves were given
  to me. I've never felt so terrified."*
- Empowered: *"The altar judged me. I was found wanting. Something below
  grew stronger. I can feel it."*

### 4.7 Save persistence

All judgment flags persist (`save_system.py:42-50`,
`main.py:319-335`): `_abaddon_empowered`, `_locusts_strengthened`,
`heavenly_host_active`, `_l100_altars_used`, `abaddon_resist_removed_turns`,
`seals_broken`, `karma`, `player_title`, `_judgment_resolved`.

---

## 5. Seal-breaking gate

### 5.1 The 7 seal demons

Defined in `level_manager.py:152-160`:

| Floor | Demon ID | Name | Resist | Weak |
|---|---|---|---|---|
| 83 | seal_demon_wrath | Amon, Demon of Wrath | fire | cold, holy |
| 85 | seal_demon_pestilence | Buer, Demon of Pestilence | (see monsters.json) | (see) |
| 87 | seal_demon_famine | (Famine) | | |
| 89 | seal_demon_war | (War) | | |
| 91 | seal_demon_death | (Death) | | |
| 93 | seal_demon_earthquake | (Earthquake) | | |
| 97 | seal_demon_silence | (Silence) | | |

Common stats (`monsters.json:21084+`): hp ~1200 (Wrath, Pestilence
sometimes 850), thac0 -16, `is_seal_demon: true`, `is_mini_boss: true`,
`is_boss: true`, `frequency: 0`.

### 5.2 Spawn guarantee

`_try_spawn_seal_demon` (`level_manager.py:162-202`) is called from
`generate` (`:59`) on every level. Skips if `demon_id` already in
`_placed_mini_bosses`. Picks a non-start, non-end room and places it on a
free walkable tile. **Guaranteed spawn, idempotent across revisits.**

### 5.3 Seal break on kill

When a seal demon is killed (`game_combat.py:620-630`):

```
seal_id = 'seal_of_' + monster.kind.replace('seal_demon_', '')
self.seals_broken.add(seal_id)
count = len(self.seals_broken)
self.add_message(f"The {monster.name} falls! A seal is broken! ({count}/7)")
if count == 7:
    self.add_message("ALL SEVEN SEALS ARE BROKEN. The way to the Pit stands open.")
```

A chronicle entry is logged each break (`game_combat.py:626`) and a
special one at 7/7 (`:630`).

### 5.4 The seal artifact drop (separate from kill tracking)

Each seal demon's `treasure.unique_drop_id` (e.g. `"seal_of_wrath"`,
`monsters.json:21138`) spawns a tangible Seal artifact on death
(`game_combat.py:655-658` → `_spawn_unique_item`). These artifacts are
purely lore items — they have `min_level: 9999` so never spawn in normal
loot.

**Important:** the `seals_broken` set tracks the *kill event*, not the
*artifact pickup*. Even if the player abandons a seal corpse, the seal
counts as broken. The seal artifacts in inventory are flavor; the gate
check is on the set.

### 5.5 The L99→L100 gate

`_descend_stairs` (`main.py:1200-1217`):

```python
if self.dungeon_level == 99 and len(self.seals_broken) < 7:
    remaining = 7 - len(self.seals_broken)
    self.add_message(f"Seven seals hold the Pit closed. {remaining} remain unbroken.")
    self.add_message("You must slay the seven guardians before the way opens.")
    return
```

**The gate is descent-only.** Nothing prevents the player from going back
up from 99→98 etc. The Stairs Down on L99 is the only gated stair.

### 5.6 No altar/prayer involvement in seal-breaking

Pure kill-track. No theology check, no altar interaction.

### 5.7 Game-magic exclusion

Seal demons are excluded from some magic effects:
`game_magic.py:1924` — `and not getattr(m, 'is_seal_demon', False)` in
some spell targeting. (Likely teleport or area effects — not load-bearing
for divine mapping, but noted.)

---

## 6. Death-chase divine integration

### 6.1 Prayer as a death-freeze tool

Already covered in Section 3.6. Mechanism:
- Available any time the player has prayer cooldown ready during the
  ascent (death_pursues == True).
- Freeze duration: `min(8, 3 + effective)` turns. **4 turns minimum** for
  any successful prayer; 8-turn cap.
- **No special bonus for praying at an altar during chase** beyond the
  altar's normal +1 to effective chain.
- The boon (heal, cleanse, etc.) is granted as well — the freeze is *in
  addition* to the regular tier reward.

### 6.2 Scales of Michael during chase

`heavenly_host_active = True` persists across floors, so any locust
abilities from Abaddon (he is dead by this point — no effect during
chase). **Practically, the Scales' Heavenly Host mechanic has no
death-chase utility** since Abaddon is the only locust-summoning
monster.

### 6.3 Sword of Michael during chase

The Sword's `abaddon_bonus_damage` only triggers vs
`monster.kind == 'abaddon_destroyer'` (`combat.py:157`). Against
DeathMonster it gives no bonus. The base 45 + holy + ignore_resistances
combo is still powerful but Death cannot be killed by combat — only by
the Abyss ritual (Stone + Tablet of Second Death).

### 6.4 No altars during chase

The chase goes L100 → L1. Altars on L91, L76, L61, L46, L31, L16, L1 may
exist (level % 15 == 1 rule). Praying at them works normally. **No
special divine event during chase tied to specific altars.**

### 6.5 Lake of Fire / Abyssal Shimmer

`_trigger_abyss()` (referenced in CONTEXT.md, lives in `main.py` near
ascent) — the ritual that "swallows Death" and grants the **Scroll of
Death's Bane**. This is a Stone+Tablet+Shimmer interaction, not strictly
divine (no theology quiz, no altar). But it is the canonical "Death and
Hades were thrown into the lake of fire" outcome.

---

## 7. Divine-aligned quirks

### 7.1 Fisher King (#18) — `quirk_system.py:785-792`

- **Trigger:** call `on_prayer(hp_pct)` with `hp_pct <= 0.15` six times.
- **Effect:** sets `quirk_progress['fisher_king_active'] = True` →
  halves prayer cooldown (`game_divine.py:781-782`).
- Description: *"You prayed 6 times at 15% HP or below."*
- Reward text: *"Prayer cooldown permanently halved."*

### 7.2 Fisher King mystery — `mystery_system.py:145-157, 537-539`

- **Trigger:** activate the Fisher King mystery altar (theology T4 quiz,
  threshold 5/7) on L58-72.
- **Effect:** +30 max HP, sets
  `quirk_progress['fisher_king_mystery_active'] = True` → halves prayer
  cooldown a **second time** (`game_divine.py:783-785`).
- **STACKS with the quirk.** Combined: cooldown ÷ 4.

### 7.3 Zoroaster (#62) — `quirk_system.py:794-797`

- **Trigger:** pray successfully on 15 distinct dungeon floors (the
  floor number is added to a set on `on_prayer`, regardless of HP%).
- **Effect:** all quiz timers +1 second (`_all_timer_bonus(1)`).

### 7.4 Confucius (#61) — `quirk_system.py:411-415`

- **Trigger:** answer 50 philosophy questions correctly **while
  Blessed**. (Bless status, not BUC.)
- **Effect:** philosophy quiz timer +4 seconds.
- Theology-adjacent: requires the Bless effect, which can come from
  altar BUC blessings, scrolls of bless, or other holy sources.

### 7.5 Solomon (#64) — `quirk_system.py:380-385`

- **Trigger:** 100 correct philosophy answers in a run.
- **Effect:** WIS +2 permanent.
- Not strictly divine, but lore-tied (the ring lore of Solomon and
  Michael at `accessory.json` solomon ring).

### 7.6 Cassandra (#12) — `quirk_system.py:456-461`

- **Trigger:** pass a threshold quiz with ≥2 wrong answers, 10 times.
- **Effect:** WIS +1 permanent.
- Not divine-locked, but WIS feeds prayer (longer timer, +1s per WIS
  above 10).

### 7.7 Norns (#28) — `quirk_system.py:799-805`

- **Trigger:** use recall_lore 20 times in a run.
- **Effect:** sets `norns_active` flag.
- Listed here because of CONTEXT.md cross-link to halved recall_lore
  cooldown (not prayer-related but lore-adjacent to divine knowledge).

### 7.8 Apollo (#23), Hypatia, Galileo, etc.

Subject-mastery quirks (`philosophy_correct_total`, `science_correct_total`,
etc.) are not divine-gated, but theology mastery is conspicuously absent —
there is no "Theology master" quirk in `quirk_system.py`. **Theology
correct totals are not tracked.** (Grep `theology_correct` returns
nothing in `quirk_system.py`.) This is a potentially noteworthy gap.

### 7.9 The "anointed Paladin" title

`self.player_title = 'Paladin'` is set at karma 10 judgment
(`game_encounters.py:938`). Grep across `src/` shows the title is read
only by the **highscore** and **chronicle/death** displays — it has no
mechanical effect (no AC bonus, no aggro change, no item lock-out).

---

## 8. Cross-system interactions

The divine system has at least these threads into other subsystems:

### 8.1 → Boss fights

- **L20 (Asterion):** No divine hook. Quest layer is Ariadne's Thread.
- **L40 (Medusa):** Generic altar in the nave (`boss_levels.py:221`). No
  combat resist-strip. Quest layer is the Athena/Aegis shrine on L37
  (altar-mediated, but pre-L40, `dungeon.py:1522-1524`).
- **L60 (Fafnir):** No altar in the lair. Odin's altar on L53 (`dungeon.py:1538-1540`)
  is the divine quest layer (drop Broken Gram → Sigurd's Shovel or
  reforged Gram via the throw-over secret, `game_divine.py:411-461`).
- **L80 (Fenrir):** Altar in the boss hall (`boss_levels.py:369`).
  Generic prayer altar. **The divine quest layer for Fenrir is the
  Dwarven Forge (L76) + Vidar's Altar (L79)** producing Gleipnir and
  Vidar's Sandal — both use ALTAR tile but their semantics are checked
  by position, not tile type.
- **L100 (Abaddon):** Full integration. 6-altar resist-strip ring
  (Section 2.3) + karma-gated Sword/Scales/empowerment (Section 4) + seal
  gate at L99→L100 (Section 5.5).

### 8.2 → Items

- **Sword of Michael** (`weapon.json:8591`): tied to karma == 10.
  `ignore_resistances` + `abaddon_bonus_damage` are coded in `combat.py:84,157`.
- **Scales of Michael** (`artifact.json:245`): tied to karma >= 1.
  Spawn-locked via `min_level: 9999`; only the judgment encounter
  introduces them.
- **Seal artifacts** (seal_of_wrath/pestilence/famine/war/death/earthquake/silence
  in `artifact.json:230+`): `min_level: 9999`; only seal-demon drops.
  Pure flavor — no mechanical use beyond carrying weight (~0.1 each).
- **Scroll of the Abyss** (`scroll.json:230-249`): reward scroll from
  Abaddon, carries a reward code (`power: "ABYSS-MMXXV-V"`). Not
  divine-mechanical but ties to the Boss Reward economy.

### 8.3 → Quirks

(Already covered in Section 7.) Two quirk-trigger paths into the divine
system: `quirk_system.on_prayer` (Fisher King, Zoroaster) and
`mystery_system.apply_mystery_reward` (Fisher King mystery, fountain-
based cooldown halving).

### 8.4 → Hidden / secret systems

- **Throw-over secret at Odin's altar** (`game_divine.py:411-461`,
  detection at `game_combat.py:287`): if the player *throws* (not drops)
  the Broken Gram across the altar, Gram is reforged. Pure divine secret.
- **Unicorn karma gate** (`game_encounters.py:328-335`): the unicorn
  refuses negative-karma players. The unicorn itself is a magical
  encounter tracked via `_is_unicorn` flag (`game_encounters.py:372`).
- **Mystery altars** (Section 2.4): the Fisher King mystery is the only
  one with a divine cross-link to prayer cooldown.

### 8.5 → Lore / hints

- CONTEXT.md identifies T2 hint about altars in `data/hints.json`:
  *"Strange altars sometimes appear in the dungeon. Those who approach
  and kneel before them discover ancient challenges — and ancient
  rewards."*
- **No T5 hint specifically about the L100 resist-strip mechanic**
  (called out as a question in `REVERSE_ENGINEERED.md` Q12).
- The seal-gate L99 message is in-game spoken (not a hint).
- Sword of Michael lore (`weapon.json:8639`) and Scales lore
  (`artifact.json:256`) are entirely in-item-lore. The player only sees
  these strings if the item is identified.

### 8.6 → Chronicle voice

The divine system contributes ~7 distinct chronicle hooks:
- First prayer at altar (Section 3.7)
- First fountain drink
- First grave dig
- First throne
- First mystery altar
- Karma extremes ±10 (Section 1.4)
- Each of 4 judgment outcomes (paladin, scales-granted, empowered,
  locusts-strengthened)
- Each of 7 seal breaks + the 7/7 message
- Praying during Death chase
- Various boss kills (Asterion, Medusa, Fafnir, Fenrir, Abaddon)

---

## 9. Open questions / incomplete implementations

### 9.1 The L99 judgment altar bypasses the prayer cooldown check

`game_divine.py:684-693` runs the judgment branch *before* the
`prayer_cooldown > 0` check at `:695`. This is intentional (the
judgment is a one-shot per-run event), but worth flagging — a player
mid-cooldown can still get judged.

### 9.2 Failed L100 prayers consume an altar

`game_divine.py:776-777`: even at chain 0 ("the heavens are silent"),
the altar is added to `_l100_altars_used`. The player can burn all 6
altars without ever stripping Abaddon if they whiff every theology quiz.
Possibly intentional (preserves stakes); possibly a bug (an off-altar
practice or a brain-fart shouldn't waste a resource). **Flagged, not
fixed.**

### 9.3 No "theology mastery" quirk

`quirk_system.py` has subject-mastery quirks for math (Ramanujan),
philosophy (Solomon), science (Galileo, Hypatia), economics (Archimedes),
history (Sage's Counsel) — but **none for theology correct totals**. The
trigger statistic (`theology_correct_total`) isn't tracked. Likely a
gap, given that theology is the prayer subject and the L99 judgment is
gated by a separate karma score (not skill).

### 9.4 prayer_boon_count interaction with Fisher King

`prayer_boon_count` (`player.py:66`) caps WIS-+1 prayers at 3 per run.
With Fisher King's halved cooldown the player can pray ~2x more often,
but they still hit the 3-WIS cap. So the quirk doesn't accelerate stat
gain — only timing/healing access. This appears intentional but unsigned.

### 9.5 `heavenly_host_active` flag is monotonic-true

Once set to True, the flag never resets (`game_menus.py:1010-1011`). The
"uses: 1" check (`game_menus.py:702-705`) prevents re-summon. If the
player saves after activating Heavenly Host and reloads, the angels keep
spawning. Verified as intended via `save_system.py:41`.

### 9.6 Scales of Michael power is hidden until inventoried

The "Summon the Heavenly Host" power only appears in the Power menu when
the Scales are in inventory (`game_menus.py:698-705`). There is no
in-game tutorial for this — the player must discover it. CONTEXT.md
treats this as a feature (hidden systems are features).

### 9.7 Karma is invisible during play

`game_render.py:932` and `:949` reference karma in the **judgment
overlay** and **death chronicle screen** only. The HUD does not display
karma during normal play. The player must infer their score from NPC
encounter context. This is consistent with the "hint, don't explain"
philosophy but means a player who accidentally chose -1 options is
heading toward `abaddon_empowered` with no warning.

### 9.8 No "praying breaks vow" mechanic

Nothing penalizes the player for praying constantly. The cooldown is
the only soft-limit. There is no "your prayer becomes hollow" or
"piety" track. This is in line with the design that prayer is a recall
mechanic, not a separate stat.

### 9.9 Cassandra unicorn loophole

The unicorn check is `karma < 0` (`game_encounters.py:329`). A player at
karma 0 (perfectly neutral) can still get the unicorn. This means the
player can take +0 NPC options early, ride a unicorn quest reward, then
take +1s later. No exploit per se, but worth noting that the unicorn
gate is *not* "good karma only" — it's "not actively wicked."

### 9.10 Boss-altar count mismatch with REVERSE_ENGINEERED.md prediction

`REVERSE_ENGINEERED.md` Section 2 speculates "If the arena has 4-6
altars, the design supports sustained burst phases." **Confirmed: 6
altars** (`boss_levels.py:468-478`). This was an open question; now
closed.

### 9.11 Mystery system altars do not stack with Fisher King quirk

The Fisher King quirk + Fisher King mystery both halve the cooldown.
The REVERSE_ENGINEERED audit noted this as a potential bug. Reading the
code: both halvings apply unconditionally in sequence
(`game_divine.py:781-785`). Likely **intentional** — the player must
both (a) survive low-HP prayers 6 times AND (b) solve the L58-72
mystery — to combine them. Two distinct skill paths, both rewarded.

---

## Cross-link summary (top 5)

1. **Seal gate ↔ L99 judgment ↔ L100 altars ↔ Abaddon stats.** Three
   separate divine systems converge on the final boss fight: the player
   must (a) break 7 seals to descend, (b) be judged at the L99 altar
   (karma decides Abaddon's HP and weapon), (c) use the L100 altar ring
   to open resist windows. This is the densest cross-system convergence
   in the game.
2. **Fisher King quirk + Fisher King mystery → Prayer cooldown ÷ 4.**
   Two independently earned bonuses stack multiplicatively. Touches:
   quirks, mystery system, prayer, death-chase utility.
3. **Karma gate on unicorn pet.** A divine-system variable (karma) gates
   a pet-system reward (UnicornPet, `pet_system.py`).
4. **Athena/Aegis shrine on L37 → Aegis vs Medusa (L40).** Generic altar
   tile + item drop (`eye_of_graeae` on L29) → shrine opens →
   Medusa-fight-critical loot. Same pattern with Ariadne's bull, Odin's
   Gram, Vidar's scraps + Gleipnir.
5. **Scales of Michael → Heavenly Host → counters Abaddon's locust
   summon.** Karma 1-9 (NPC encounter system) → judgment outcome
   (divine) → power-menu unlock (UI/item system) → spawn balance during
   boss combat. Five subsystems for one mechanic.

---

## Files cited (absolute paths)

- `C:\Users\brand\Documents\PhilosophersQuest\src\game_divine.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\game_encounters.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\game_combat.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\game_menus.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\game_render.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\game_magic.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\main.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\dungeon.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\boss_levels.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\level_manager.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\quirk_system.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\mystery_system.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\monster.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\combat.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\items.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\npc_encounters.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\player.py`
- `C:\Users\brand\Documents\PhilosophersQuest\src\save_system.py`
- `C:\Users\brand\Documents\PhilosophersQuest\data\items\weapon.json`
- `C:\Users\brand\Documents\PhilosophersQuest\data\items\artifact.json`
- `C:\Users\brand\Documents\PhilosophersQuest\data\items\scroll.json`
- `C:\Users\brand\Documents\PhilosophersQuest\data\monsters.json`
