# Magic system audit — v2.15.0 readiness

Scope: `src/spells.py`, `src/game_magic.py`, `src/chain_passives.py`, `data/items/{wand,scroll,spellbook}.json`, and cross-referenced code in `src/items.py` (`make_scroll_lake_of_fire`, `make_death_bane_scroll`).

Read-only audit — no code was changed.

---

## Severity summary

| Sev | Count | Notes |
|-----|-------|-------|
| P0  | 0     | No known crash paths in the cast / zap / read flows. |
| P1  | 2     | Two spells silently fizzle after successful cast (`blink_spell`, `elder_blink`). |
| P2  | 2     | Wand `magic_missile` bypasses MAGIC_TIER_MULT (T3-T5 wand-of-force line under-scaled ~2-3×); accessory `spell_crit` unit-mismatch neutralises the passive on the "Ruby" line. |
| P3  | 2     | Cosmetic `chain 5` echoes in code comments/messages; T5 utility spells at 20 MP vs 22-25 spec. |
| P4  | 3     | Dead handler branches (`identify_all`, ~30 unreferenced wand-effect branches), spellbook `mp_cost` overrides silently ignored on unique tomes. |

---

## Coverage matrix (top-line)

- **Spells → handlers.** Every effect in `LEARNABLE_SPELLS` has a matching branch in `_apply_spell_effect` **except** `teleport_self` when cast from a non-targeted spell (see P1-1). Witcher signs (`aard_blast`, `sign_yrden`'s `slow_monster`, `sign_axii`'s `confuse_monster`, `sign_quen`'s `shield_self`, `sign_igni`'s `fire_bolt`) all resolve to existing branches. Elder Blood's `elder_scream` (mass_ice) and `elder_charge` (empower_next) are wired.
- **Wands → handlers.** Every `effect` in `data/items/wand.json` (`heal`, `fire_bolt`, `cold_bolt`, `lightning_bolt`, `acid_spray`, `magic_missile`, `striking`, `sleep_monster`, `slow_monster`, `confuse_monster`, `paralyze_monster`, `blind_monster`, `fear_monster`, `polymorph_monster`, `charm_monster`, `turn_undead`, `poison_monster`, `disease_monster`, `curse_monster`, `weaken_monster`, `secret_door_detection`, `opening`, `probing`, `light`, `sunlight`, `wonder`, `digging`, `cancellation`, `drain_magic`, `dispel_magic`, `teleport_monster`, `death_ray`, `disintegrate`, `drain_life`, `iron_mortar`) has a branch in `_apply_wand_effect`. `philosophers_wrench` + `flux_capacitor` bypass the wand quiz in `_invoke_wand` and never reach `_apply_wand_effect`.
- **Scrolls → handlers.** Every `effect` in `data/items/scroll.json` + the two code-authored scrolls (`scroll_lake_of_fire`, `scroll_deaths_bane` — see `src/items.py:2115` / `:2187`) has a branch in `_apply_scroll_effect`. The `boss_reward` handler (line 2332) uses `scroll.power` as the code — matches all 20 quest reward scrolls.
- **Spellbooks → spells.** Every `spell_id` in `data/items/spellbook.json` resolves to an entry in `LEARNABLE_SPELLS`. `book_of_thoth` has `spell_id: ""` and is routed through `_read_book_of_thoth` (consumable-artifact branch in `_learn_from_spellbook:3361`) rather than a learn path — correct.
- **Character-build spells NOT in any book** (correct by design, per `spells.py:606` docstring — welcome-screen builds only): `sign_aard`, `sign_igni`, `sign_quen`, `sign_yrden`, `sign_axii`, `elder_blink`, `elder_charge`, `elder_scream`.

---

## P0 — Crash paths

None found. All damage handlers guard target/monster lookups, boss-resist helper returns tuples uniformly, and MAGIC_TIER_MULT.get uses a 1.5 default so an unknown tier can't KeyError.

---

## P1 — Silent-fizzle / broken effects

### P1-1  `blink_spell` and `elder_blink` silently do nothing after a successful cast
- **File:** `src/game_magic.py`, dispatch in `_apply_spell_effect` (line 1303).
- **Effect key:** `teleport_self`.
- **Registry:**
  - `blink_spell`: `effect='teleport_self'`, `needs_target=False`, `mp_cost=3` (`spells.py:437`).
  - `elder_blink`: `effect='teleport_self'`, `needs_target=False`, `mp_cost=2` (`spells.py:641`).
- **Problem:** the only `elif effect == 'teleport_self':` branch is at `game_magic.py:1979`, nested *inside* the `if target is not None:` block that starts at line 1874. `teleport_self` is not in `_SELF_BUFF_DURATIONS` (line 1850), not in `_MASS_STATUS` (line 1733), and has no top-level handler.
- **Flow:** `_invoke_spell` sees `needs_target=False`, deducts MP, calls `_start_spell_quiz(spell, spell_id, target=None)`. On correct answer, `_apply_spell_effect(spell, None)` runs, matches nothing, falls off the end. Player pays MP, sees a science quiz succeed, and gets no message and no teleport.
- **Fix sketch:** add `'teleport_self'` as a top-level handler that calls `self._teleport_player()` (mirroring the wand branch at `game_magic.py:359`) and emits a "You blink to a new location!" line, OR add `teleport_self` alongside `phase_self` / `levitation_self` inside `_SELF_BUFF_DURATIONS` with a dedicated code path. Either fix is one small block.
- **Severity:** P1 — advertised spell effect is silent. Not a crash, just no-op.

### P1-2  Wand `magic_missile` skips MAGIC_TIER_MULT
- **File:** `src/game_magic.py:648-663`.
- **Symptom:** wand `magic_missile` handler uses `dmg = max(1, base + self.player.INT // 5)`, deliberately *not* calling `_wand_tier_damage`. Explicit comment at line 649-653 says this is intentional ("baked into wand.power per tier").
- **Impact vs T-line:** at INT 10 default, sample outputs:
  - T1 `wand_of_force_dart` (power 2d4, avg 5) → 5+2 = 7 dmg.
  - T3 `wand_of_force_barrage` (power 6d6, avg 21) → 21+2 = 23 dmg.
  - T5 `wand_of_force_cataclysm` (power 12d8, avg 54) → 54+2 = 56 dmg.
  - Sister T5 wands going through `_wand_tier_damage` (fire/cold/lightning at 12d10, avg 66): `66 × 1.5 × 2.0 = 198 dmg`.
  So the force line's T5 lands at ~28% the damage of the other T5 damage lines. Also 56 vs a chain-5 2h-warhammer's 72 dmg from `chain_combat_v2.md`.
- **Was this intended?** The comment "baked into wand.power per tier" was correct BEFORE MAGIC_TIER_MULT (v2.14.0) added the tier boost. Post-boost, magic_missile is now the *only* damage-wand effect without the tier multiplier, so the entire force-wand line reads as under-tuned vs cataclysm/absolute-zero/zeus's-wrath/dissolution/devastation.
- **Severity:** P2 — advertised as an unerring high-tier tool; users comparing wand-of-force-cataclysm to wand-of-cataclysm (both T5 12d10-class) will feel the gap sharply.

---

## P2 — Under-scaled / broken passives

### P2-1  Accessory `passive_spell_crit` unit-mismatch (Ruby-of-Nogitsune line silent)
- **Files:** `src/chain_passives.py:210` (`get_spell_crit_chance`), `data/items/accessory.json:1922-1938`, `data/items/armor.json:792/800`.
- **Formula:** `get_spell_crit_chance` returns `sum_passive_values(...) / 100.0`.
- **Armor authoring (correct):** Robe of the Magus T4/T5 → `passive_spell_crit: 10` → resolves to 0.10 (10%). Reasonable.
- **Accessory authoring (broken):** the amulet at T3-T5 uses `passive_spell_crit: 0.05 / 0.08 / 0.12`. Divided by 100 those give **0.05% / 0.08% / 0.12%** — effectively silent. Presumably the author intended 5%/8%/12%.
- **Downstream:** `apply_spell_damage_passives` (chain_passives.py:379) rolls `random.random() < crit_chance`. With crit_chance ≈ 0.0005, players never see the Ruby crit fire.
- **Fix:** either rewrite the accessory values (0.05 → 5, 0.08 → 8, 0.12 → 12) OR change the formula to a max/min-clamp that treats both fraction and integer inputs sensibly. The former is a one-line JSON change per line; the latter avoids future confusion.
- **Severity:** P2 — advertised spell-crit passive doesn't fire in normal play from the amulet slot.

### P2-2  (No standalone P2-2 — scaling comparison covered under P1-2.)

---

## P3 — Cosmetic / balance drift

### P3-1  T5 utility spells authored at 20 MP vs 22-25 MP spec
- **File:** `src/spells.py`.
- Ten T5 non-damage utility spells are 20 MP instead of the 22-25 band: `deep_slumber_spell` (20), `mass_paralyze_spell` (20), `terror_spell` (20), `madness_spell` (20), `greater_haste_spell` (20), `greater_invisibility_spell` (20), `reflect_spell` (20), `omnisight_spell` (20), `foresight_spell` (20). All damage/summoning T5 spells (22-25) are in-band.
- **Severity:** P3 — likely a deliberate concession that CC-only utilities are worth less than damage AoEs; either accept as-is or nudge to 22.

### P3-2  Dead `chain` echoes in comments and one code path
- **File:** `src/game_magic.py`.
- Line 1315 comment: `now just says "(chain 5)" -- harmless echo`. Confirmed harmless.
- Line 1557 (`meteor_swarm`): `shots = max(2, chain)` still consults the retired `chain` variable (constant 5); comment reads "chain 1 = 2 meteors, chain 5 = 5 meteors" but the ladder is dead — always 5 shots. Same at line 1667 (`annihilate` threshold_pct = 0.35 always) and 2150 (`power_word_kill` threshold = INT×20 always).
- Not bugs (behaviour is intentional at chain=5), but the comments still describe the retired chain-scaling contract. **Severity:** P3 cosmetic.

---

## P4 — Nits

### P4-1  Dead `identify_all` scroll effect handler
- `game_magic.py:2722` (`elif effect == 'identify_all':`) is dead — no scroll in `data/items/scroll.json` uses `identify_all` (all use `identify`). Only an old `tools/balance/generated/data/scroll.json` and `add_iconic_items.py` script reference it. Safe to leave, but flagging as removable.

### P4-2  Large family of dead wand-effect branches
- `_apply_wand_effect` contains handler blocks for ~30 effects not currently authored in `data/items/wand.json`, e.g. `extra_heal`, `restore_body`, `create_monster`, `fire_shield`, `cold_shield`, `regeneration_self`, `phase_self`, `detect_treasure`, `mapping`, `clairvoyance`, `identify_item`, `enchant_weapon`, `earthquake`, `explosion`, `mass_confuse`, `mass_sleep`, `mass_slow`, `time_stop`, `wish`, `boost_str/con/int`, `nova`, `life_transfer`, `abjuration`, `knock`, `haste_self`, `invisibility_self`, `levitation_self`, `teleport_self`, `shield_self`, `reflect_self`, `detect_monsters`. Handler space kept for extensibility — not bugs.

### P4-3  Unique-tome `mp_cost` overrides silently ignored
- `_learn_from_spellbook:3415` stores `mp_cost = book.mp_cost` into `player.known_spells`, but `_invoke_spell:1170` reads `mp_cost = spell['mp_cost']` from `LEARNABLE_SPELLS` at cast time, so the stored per-book override never gets used.
- Concrete impact:
  - `picatrix` (T4 unique) advertises `mp_cost: 12` for `fireball_spell` (base 10) — cast still costs 10 MP.
  - `sefer_yetzirah` (T4 unique) advertises `mp_cost: 18` for `summon_guardian_spell` (base 10) — cast still costs 10 MP.
- Since the "cheaper via base spell" outcome favours the player and no book advertises a *lower* cost than the base, this is only a data-file wart — but consider either honouring the stored cost or stripping the mp_cost overrides from the artefact books.

---

## Sanity checks that passed cleanly

- Every `LEARNABLE_SPELLS` `tier` matches `quiz_tier` (asserted by inspection of all 62 entries).
- Every book `tier` matches `quiz_tier`.
- Every wand `tier` matches `quiz_tier`.
- Every scroll `tier` matches `quiz_tier`, except the 20 quest reward scrolls + `scroll_of_the_labyrinth` etc. which are all `quiz_tier: 1, quiz_threshold: 2` — intentional (see `boss_reward` handler).
- MAGIC_TIER_MULT map matches spec `{1:3.0, 2:2.5, 3:2.0, 4:1.75, 5:1.5}`.
- `_spell_damage` and `_wand_tier_damage` both pull from MAGIC_TIER_MULT correctly; INT scaling identical (`1.0 + INT*0.1`).
- Every damage handler in `_apply_spell_effect` routes through `_spell_damage` (`mass_ice`, `mass_fire`, `meteor`, `cone_of_cold`, `meteor_swarm`, `storm_of_vengeance`, `turn_undead`, `fire_bolt`, `lightning_bolt`, `aard_blast`, `smite`, `acid_arrow`, `drain_life_spell`, `disintegrate_spell`, `frost_touch`, `chain_lightning_jump`) — no direct-multiply bypasses.
- Every damage handler in `_apply_wand_effect` routes through `_wand_tier_damage` EXCEPT wand `magic_missile` (see P1-2). HP-percent-based handlers (`death_ray`, `disintegrate`, `life_transfer`) correctly bypass MAGIC_TIER_MULT since they scale by target HP.
- Scroll `earth` uses `self._int_scaled_damage(int(base_dmg * _chain_mult))` at line 2806 — that's the pre-magic INT scaler, not MAGIC_TIER_MULT. Scrolls are grammar-quizzed and were not part of the v2.14.0 magic-tier boost, so this is correct.
- Chain-equip passives that affect magic and fire in code:
  - `spellbook_chain_bonus` — `_start_spell_quiz` reads it at line 1269-1272 to reduce effective cast tier. Wired.
  - `grammar_chain_cap_bonus` — `_read_scroll:2286-2289` and `_learn_from_spellbook:3431-3435` both reduce read tier. Wired.
  - `scroll_save_on_fail` — `_read_scroll:2231-2255` and `_learn_from_spellbook:3387-3402` both preserve the item on quiz-fail. Wired.
  - `free_cast_once_per_floor` — `_invoke_spell:1181-1184` (Robe of the Magus). Wired.
  - `double_cast_at_peak_tier` — `_start_spell_quiz:1249-1256` (T5 spells, Robe of the Magus T5). Wired.
  - `spell_damage_bonus` + `spell_crit` — `apply_spell_damage_passives` (chain_passives.py:379); called by `_spell_damage`. Wired (but see P2-1 for the unit-mismatch on accessory-side crit).
  - No `wand_chain_bonus` passive exists in code or data — retired term.
