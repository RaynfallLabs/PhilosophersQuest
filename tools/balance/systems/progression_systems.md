# Progression and Stats — Comprehensive Reference

Read-only map of every progression mechanic in Philosopher's Quest.
Every claim cites `file:line`. Question banks (`data/questions/`) are out of scope.

---

## 1. Resource tracks (HP, SP, MP)

### Base values & formulas

| Resource | Base | Formula at init | File:Line |
|---|---|---|---|
| max_hp | 20 | `BASE_HP (20) + CON` | `player.py:1, 42` |
| max_sp | 200 | `BASE_SP (200) + STR` | `player.py:2, 44` |
| max_mp | 10 | `BASE_MP (10) + INT` | `player.py:3, 46` |

`BASE_HP=20`, `BASE_SP=200`, `BASE_MP=10` declared at `player.py:1-3`. Stat-derived
maximums are recomputed in `apply_stat_bonus()` so each +1 CON gives +1 max_hp,
+1 STR gives +1 max_sp, +1 INT gives +1 max_mp (`player.py:383-397`).

### Sources of HP growth

| Source | Magnitude | Diminishing? | File:Line |
|---|---|---|---|
| CON gain via accessories/scrolls/quirks/altars | +1 max_hp per +1 CON | No | `player.py:390-392` |
| Single-ingredient cook (Q1–Q5) | `int(sqrt(min_level) × SINGLE_MULT[Q])` | Yes (cooking softcap) | `food_system.py:34-38` |
| Compound recipe (Q1–Q5, n≥2 ingredients) | `int(sqrt(max_min_level) × COMPOUND_MULT[Q] × (1 + 0.15×(n−2)))` | Yes | `food_system.py:41-46` |
| Throne mystery (chain 4) | +5..15 max_hp | One-shot | `game_divine.py:662-665` |
| Ragnarok quirk (L100 at ≤10 HP) | CON +5 → +5 max_hp | One-shot | `quirk_system.py:264-266` |
| Khopesh of Anubis (kill_max_hp_bonus) | +N per kill until `kill_max_hp_cap` | Hard-capped | `combat.py:220-228`, `items.py:93-94` |
| Hack Reality Tier 3 (XYZZY) | All stats +5 → CON +5 → +5 max_hp | Once per run | `main.py:2622-2627` |
| Hack Reality Tier 4 fallback | All stats +3 | Once per run | `main.py:2638-2641` |
| L100 altar fallback / Caesar quirk | CON +1..2 | Various | `quirk_system.py:530-532` (Caesar) |

### Sources of HP drain

| Source | Effect | File:Line |
|---|---|---|
| Monster attacks | dice damage minus AC roll | `monster.py:281-298` |
| Status DoTs: `poisoned` 1/turn, `bleeding` 1/turn, `strangulation` 2/turn, `burning` 1/turn, `doomed` ~12%/turn, `draining` ~17%/turn | various | `status_effects.py:320-364` |
| Berserk armor active | `berserk_hp_cost` per turn | `main.py:1619` |
| Cú Chulainn coat | hp cost per turn while berserk | `main.py:1601-1619` |
| Starvation (SP=0) | 1/turn | `main.py:2025` |
| `apply_stat_bonus('CON', -N)` | -N max_hp (drain potions, disease, mystery costs) | `player.py:390-392` |

### Regen mechanisms

| Source | Rate | File:Line |
|---|---|---|
| Passive HP regen | 1 HP every `max(10, 20 − max(0, CON − 12))` turns; blocked by bleeding/poisoned | `main.py:2037-2046` |
| Stair-rest (descending) | 0 HP (hardcoded `STAIR_REST_CAP_DESC = 0`) | `player.py:181, 196-197` |
| Stair-rest (ascending) | `min(22, max(0, max_hp × 0.04))` | `player.py:182, 192-194` |
| Stair-rest SP | +15 every stair | `player.py:199` |
| Stair-rest MP | `max(2, INT // 5)` | `player.py:200-201` |
| Passive MP regen (no adjacent monsters) | +1 MP per turn if not in combat | `game_input.py:243-244` |
| `regenerating` status | +1 HP/turn | `status_effects.py:337-339` |
| `on_hit_regen` weapon (Green Chapel Axe) | flat HP on being hit | `items.py:100` |
| Eye of Horus accessory `passive_regen` | +N every `passive_regen_interval` turns | `main.py:1593-1599`, `items.py:202-203` |
| Sustained accessory | SP drain halved (drain interval 4 vs 2) | `main.py:2017` |
| Prayer chain 5–8 | partial-to-full HP/SP restore | `game_divine.py:819-823` |
| Fountain mystery chain 2+ | partial-to-full HP, can cure | `game_divine.py:329-345` |

### Caps

* **`MAX_EFFECT_DURATION = 60`** (status effect turns hard cap) — `status_effects.py:14`.
* **Cooking 1000 softcap** — `COOKING_HP_SOFTCAP = 1000` at `player.py:203`; bonus
  scales `max(0.20, 1.0 − cooking_hp_gained/1000)` so contribution floors at 20% of
  raw, but never quite reaches the cap (asymptotic) — `player.py:211-216`.
* **HP/SP/MP have NO hard ceiling** — only floor 0; growth is unbounded but
  practically gated by ingredient pool and quirk/accessory inventory.

---

## 2. Stat scores (STR / CON / DEX / INT / WIS / PER)

### Starting values

Default new Player: **STR/CON/DEX/INT/WIS/PER all = 10** (`player.py:34-39`).
A "secret build" name typed at the welcome screen replaces these, e.g.:

| Build | STR | CON | DEX | INT | WIS | PER | Special | File:Line |
|---|---|---|---|---|---|---|---|---|
| (default) | 10 | 10 | 10 | 10 | 10 | 10 | — | `player.py:34-39` |
| aristotle | 6 | 8 | 8 | 18 | 16 | 14 | ring_intellect_amethyst, lantern_of_diogenes | `welcome_screen.py:36-42` |
| socrates | 8 | 10 | 7 | 14 | 20 | 16 | cleanse_spell | `welcome_screen.py:43-49` |
| diogenes | 5 | 5 | 5 | 5 | 18 | 16 | no dagger, lantern | `welcome_screen.py:76-82` |
| achilles | 18 | 16 | 16 | 8 | 6 | 10 | achilles_spear, wooden_shield | `welcome_screen.py:84-91` |
| leonidas | 17 | 18 | 12 | 9 | 10 | 8 | romulus_spear, spartan shield | `welcome_screen.py:92-98` |
| merlin | 5 | 7 | 8 | 20 | 14 | 12 | wand of MM, spellbook MM, heal/shield | `welcome_screen.py:134-142` |
| **dad** | 20 | 20 | 20 | 20 | 20 | 20 | **immortal**, punch_in_the_face | `welcome_screen.py:187-194` |
| ash williams | 16 | 16 | 14 | 6 | 6 | 10 | boomstick + chainsaw + necronomicon | `welcome_screen.py:206-216` |

Build dict applied at `main.py:233-247`; `_immortal` flag at `player.py:77` prevents
death (HP rebounds to max in `is_dead()`). 30+ builds exist in `welcome_screen.py:34-322`.

### Stat → derived effects

| Stat | Effect | File:Line |
|---|---|---|
| STR | Carry capacity: `50 + STR × 5` lb | `player.py:4-5, 338-339` |
| STR | Per-attack damage factor: `1.0 + max(0, STR − 10) × 0.03` | `combat.py:140` |
| STR | max_sp = `BASE_SP + STR` | `player.py:44` |
| CON | max_hp = `BASE_HP + CON` | `player.py:42` |
| CON | Faster HP regen above 12 (shaves 1 turn / point) | `main.py:2043-2044` |
| DEX | AC modifier: `(DEX − 10) // 2` (lower AC = better) | `player.py:251` |
| INT | max_mp = `BASE_MP + INT` | `player.py:46` |
| INT | Magic-subject quiz bonus: `(INT − 10) // 2` extra seconds (philosophy identify) | `player.py:325-327` |
| WIS | Per-subject quiz timer: `base + WIS × scale` (table §9) | `player.py:300-305` |
| WIS | L30+ auto BUC-reveal on pickup if WIS ≥ 14 | `main.py:2166-2173` |
| PER | Sight radius: `max(3, PER // 2)` (+modifiers) | `player.py:285-298` |
| PER | Ranged weapon reach bonus: `+max(0, PER − 10) // 3` | `combat.py:290` |

### Permanent stat-gain sources

| Source | Stat | Magnitude | File:Line |
|---|---|---|---|
| Cooking compound `bonus_type` | varies (stat/two_stats/all_stats/combat_stat/random_stat) | +1/+2/+3 | `food_system.py:295-318`, `recipes.json` |
| Cooking single Q5 recipe `bonus_type` | per ingredient JSON | +1..+3 | `food_system.py:271-273`, `ingredient.json` |
| Scrolls — `boost_str` / `boost_con` / `boost_int` wand effects | +1 | once per zap | `game_magic.py:719-732` |
| Scroll — `great_power` (Tier 5) | all stats +1 | once per scroll | `game_magic.py:1870-1873` |
| Accessories — `effects.stat` and `effects.stat2` | varies (+1..+5) | permanent while worn | `player.py:526-532`, `accessory.json` |
| Heroism potion | STR +2 (while active) | timed | `food_system.py:446-454` |
| Brilliance potion | INT +1, WIS +1 | timed | `food_system.py:456-465` |
| Prayer chain ≥8 | WIS +1 (max 3× per run via `prayer_boon_count`) | diminishing | `game_divine.py:801-806` |
| Fountain chain 5 | random stat +1 | one-shot | `game_divine.py:346-350` |
| Throne mystery chain 5 | 2 distinct stats +1 | one-shot | `game_divine.py:666-670` |
| Mystery rewards | varies | one-shot | `mystery_system.py`, `game_encounters.py:765` |
| Quirk unlocks (see §5) | STR/CON/DEX/INT/WIS/PER +1..+5 | one-shot per quirk | `quirk_system.py` |
| Hack Reality Tier 3 | ALL stats +5 | once per run | `main.py:2622-2627` |

### Stat-decrease sources

| Source | Magnitude | Notes | File:Line |
|---|---|---|---|
| `drain_str` / `drain_con` / `drain_wis` / `drain_int` potions | -1 (cursed -2; blessed blocks) | `food_system.py:570-600` |
| Disease tick (`diseased`) | random STR or CON -1, 8% per turn | drain_resist or poison_resist blocks | `status_effects.py:325-330` |
| Mystery `stat_cost` | varies | one-shot per altar | `game_divine.py:114-117` |
| Necklace of Harmonia | WIS +4 but CON -2 (curse-pair) | permanent while worn | `accessory.json` |
| Berserk expiry | STR refund (no loss) | `status_effects.py:408-414` | |

### Restoration

* `restore_str` potion: refunds STR to `_base_STR` snapshot — `food_system.py:472-480`.
  No equivalents for CON/DEX/INT/WIS/PER restoration potions exist.
* Hack Reality always restores HP/SP/MP to max — `main.py:2586-2588`.
* Rand's Heart amulet: on death restores HP/SP/MP to max, clears debuffs, consumes amulet — `player.py:147-166`.

---

## 3. Cooking-as-leveling

The primary "level-up" track. Quiz is **always Tier 1** regardless of ingredient
(`food_system.py:166-175, 277-287`); only the chain length and ingredient potency
scale rewards.

### 3.1 Formulas (`food_system.py:25-65`)

```python
SINGLE_MULT   = {1: 0.3, 2: 0.6, 3: 0.9, 4: 1.5, 5: 2.2}
COMPOUND_MULT = {1: 0.6, 2: 1.1, 3: 1.8, 4: 3.0, 5: 4.5}
potency(min_level) = sqrt(max(1, min_level))      # L1=1.0 ; L100=10.0
single_max_hp(min_level, Q)   = max(1, int(potency(min_level) × SINGLE_MULT[Q]))
compound_max_hp(max_min_level, Q, n) = max(1, int(potency × COMPOUND_MULT[Q] × (1 + 0.15×(n−2))))
cooking_heal(min_level, Q)   = max(1, int(potency × Q × 1.5))
cooking_sp(min_level, Q, raw_sp=10) = max(int(5×potency×Q), int(raw_sp × (1 + 0.15×(Q−1))))
```

Diminishing returns: in `Player.increase_max_hp(from_cooking=True)` at
`player.py:205-216`, `cap_factor = max(0.20, 1.0 − cooking_hp_gained / 1000)`. So the
cooking track asymptotically approaches ~1000 max HP from cooking alone.

`max_chain` default = 5. **Persephone quirk** flips it to 6 — `main.py:2367-2370`.

### 3.2 Single recipes (per ingredient JSON)

`data/items/ingredient.json` has 296 ingredients. Each has up to 6 quality slots
(`recipes["0"]` through `recipes["5"]`), with fields `name`, `sp`, `bonus_type`,
`bonus_amount`, `bonus_stat`, `bonus_effect`.

* min_level distribution: 41 distinct levels, range 1..100 (one ingredient at each
  major tier band).
* Only **4 ingredients** carry `mp_restore > 0`: bone_shard (mp=2), warrior_bone (3),
  arcane_bone_dust (5), thrall_bone (8) — all undead/bone-themed. MP scales as
  `int(mp_base × quality / 5)` (`food_system.py:258-263`).
* **Status-effect single recipes** (Q3–Q5): 163 status-grant entries across 116
  ingredients. Effects: `fire_shield`, `cold_shield`, `lightning_resist`,
  `poison_resist`, `regenerating`, `haste`, `invisible`, `death_ward`, `blind_resist`,
  `cold_resist`, `arcane_shield`. Durations from 3 to 50 turns (clipped to
  MAX_EFFECT_DURATION = 60).

### 3.3 Compound recipes (`data/items/recipes.json`)

**Total: 335 compound recipes.** Aggregated breakdown:

| n_ingredients | count |
|---|---|
| 2 | 291 |
| 3 | 32 |
| 4 | 9 |
| 5 | 3 |

| bonus_type | count |
|---|---|
| stat (single named stat) | 189 |
| combat_stat (random of STR/CON) | 54 |
| random_stat (any stat) | 34 |
| two_stats (two random stats, same amount) | 24 |
| status (timed buff) | 18 |
| all_stats | 16 |

| (type, amount) tuples seen |
|---|
| stat: amounts 1 (137), 2 (36), 3 (16) |
| combat_stat: amounts 1 (50), 2 (1), 3 (3) |
| random_stat: amounts 1 (32), 2 (2) |
| two_stats: amounts 1 (6), 2 (12), 3 (6) |
| all_stats: amounts 1 (9), 2 (6), 3 (1) — note: one all_stats+3 exists, that's `philosophers_grand_banquet` |
| status: durations 6/8/10/12/15/25/30/40/50/60/80/150 (durations >60 clip on apply) |

Distinct notable compound recipes:

* `philosophers_grand_banquet` — 3 ingredients, all_stats +2 (the only Q5 super-cook with whole-bar effect)
* `serpent_king_culmination` — 5 ingredients, two_stats +2
* `abyssal_midnight_feast` — 5 ingredients, two_stats +3
* `chimera_heart_royale` — 4 ingredients, all_stats +1
* `medusa_bouillabaisse`, `basilisk_perpignan`, `frost_consomme_glace` — 4-ingredient compound (two_stats +2)
* `dragon_scale_pot_au_feu` — 4-ingredient, stat STR +3
* `eagle_eye_consomme` — 4-ingredient, stat PER +3

Compound consumption is in `cook_compound_recipe()` at `food_system.py:112-175`. All
ingredient instances are removed BEFORE the quiz starts (`food_system.py:127-131`) —
quality 0 (failed) still consumes the ingredients.

### 3.4 Special ingredient effects

Beyond mp_restore (§3.2) and status grants, ingredient `recipes[q].bonus_type`
options handled by `_apply_bonus()` at `food_system.py:290-325`:

* `random_stat` — random of 6 stats
* `combat_stat` — random of STR/CON
* `two_stats` — random 2 distinct stats, same amount each
* `all_stats` — every stat +N
* `stat` — fixed `bonus_stat`
* `status` — call `add_effect(bonus_effect, bonus_amount)` (clipped to 60 turns)

### 3.5 Quality scaling

Quality = `min(5, result.score)` from the chain quiz (`food_system.py:138, 237`).
Persephone caps at 6 (max_chain=6) but Q is still clipped at 5 (no Q6 in tables).
The mapping (potency × multiplier) yields ~7× spread (Q1 → Q5) and a ~10× spread
between L1 and L100 ingredients. Reference table from REVERSE_ENGINEERED.md:

| Cook type | L1 ingredient | L100 ingredient |
|---|---|---|
| Single Q1 | 1 HP | 3 HP |
| Single Q5 | 2 HP | 22 HP |
| Compound Q5 (2-ing) | 1 HP | 45 HP |
| Compound Q5 (4-ing) | 1 HP | 58 HP |

---

## 4. AC system + THAC0 ceiling

### Formula (`player.py:247-273`)

```
AC = 10
   − DEX_mod                    where DEX_mod = (DEX − 10) // 2
   − sum(armor.ac_bonus + armor.enchant_bonus for armor in armor_slots)
   − (shield.ac_bonus + shield.enchant_bonus) if shield equipped
   − blessed_bonus              +1 per blessed armor piece + shield
   − invisible_bonus            2 if invisible
   − shield_effect              2 if 'shielded' status
   − _accessory_ac_bonus        from rings (effects.stat == 'AC')
   − _surrounded_ac_bonus       Torc of Boudicca: +2 per adjacent enemy ≥3
```

Lower AC is better. Theoretical worst: 10 (naked, DEX 10, no statuses).

### Accessory AC

Three accessories grant `stat: AC` (`accessory.json`):
* `ring_protection_adamantine` — AC +3
* (two other AC-stat rings as confirmed by accessory aggregation; 3 total accessories carry the AC bonus)

`AC` is special-cased in `apply_stat_bonus()` at `player.py:385-388`: it doesn't
mutate the `DEX` value — it's accumulated in `_accessory_ac_bonus`.

### Damage-resistance from armor

`get_armor_resistance(damage_type)` multiplies per-slot `damage_resistances`
dicts (`player.py:275-283`). Shields too. Charmander Stuffie in inventory → fire ×0.5 (`player.py:130-133`).

### THAC0 mechanics & "floor"

Monster attack roll: `to_hit = thac0 − player_ac; d20 must be ≥ to_hit to hit`
(`monster.py:281-298`).

* **Natural 1 misses; natural 20 hits.** Even on math-miss, monsters can still
  hit via `min_hit_chance`: **0.25 for bosses, 0.05 for regulars** by default
  (`monster.py:288, 233`). So AC > thac0 by a wide margin caps benefit at ~95% miss
  (regular) / 75% miss (boss).
* **THAC0 floor in DATA, not code.** Lowest THAC0 in `monsters.json` = -16
  (Abaddon, Fenrir, all seal demons, several other late-game monsters). 70 monsters
  share thac0 = -16. **No monster has thac0 < -16.** Combat code does NOT hardcode
  a -16 floor; the data simply stops there. To make AC matter past -16 player AC,
  the data needs lower THAC0 values OR `min_hit_chance` must be raised — the
  `is_boss` 25% floor is what currently keeps Abaddon hitting at all once AC ≤ -16.

### AC progression (REVERSE_ENGINEERED.md §5 confirmed by item data)

| Tier | Player AC |
|---|---|
| Naked | 10 |
| Iron armor (early) | 5..8 |
| Diamond armor (L60s) | -10..-15 |
| Adamantine + uniques (L80+) | -20..-28 |
| Best-case stack (Tower shield, DEX max, blessed full) | ~-33 |

Effective AC ceiling: anything below -16 against a regular monster still allows
5% hits and 25% hits from bosses, so AC investment hits *diminishing* returns at
roughly -16 (against bosses) and at the d20 floor of `nat 1 always misses` for
regulars.

---

## 5. Quirks — exhaustive table

All 100 quirks (the file comment says "50 Bofuri-style traits" — that comment is
stale; current registry has 100). Source: `quirk_system.py:1097-1199` (progress
keys), `:1202-1254` (names), `:1260-1364` (trigger text), `:1474-1577` (effects).
Categories: **T**imer (subject quiz timer bonus), **S**tat (permanent stat ±),
**P**assive (intrinsic status effect or proc), **A**ctive Power (consumable
or cooldown-based ability; see `_ACTIVE_POWER_DEFS` at `quirk_system.py:1058-1089`).

| ID | Display Name | Cat | Trigger | Reward |
|---|---|---|---|---|
| mithridates | The Mithridates Protocol | P | Eat 5 monster types that poisoned you | Perm poison_resist (`quirk_system.py:658-659`) |
| tiresias | Tiresias' Gift | S | 25 correct while blinded | PER +2 |
| odin | Odin's Vigil | P | Wait 12,960 turns | Perm telepathy |
| scheherazade | Scheherazade's Tongue | T | Read 12 unidentified scrolls | Grammar +5s |
| paracelsus | Paracelsus' Doctrine | P | Disease drains 5+ stat | Perm drain_resist |
| siegfried | Siegfried's Bath | P | Eat 5 distinct attack-effect monsters | Perm magic_resist |
| musashi | Musashi's Empty Strike | P | 30 kills at chain==1 | Chain-1 dmg uses 2nd multiplier |
| rasputin | Rasputin's Constitution | S | 5× survive ≤5% HP | CON +2 |
| merlin | Merlin's Apprenticeship | T | 10 unidentified wand types | Science +4s |
| buddha | The Buddha's Stillness | P | 500 waits near hostile monsters | Perm displacement |
| hephaestus | Hephaestus' Obsession | P | Equip same armor 15× | Equip threshold -1 for that slot (`main.py:2898-2900`) |
| cassandra | Cassandra's Persistence | S | Pass threshold quizzes with ≥2 wrong, 10× | WIS +1 |
| sisyphus | Sisyphus' Mastery | T | Fail lockpick on 10 distinct trapped chests | Economics +5s |
| job | Job's Endurance | P | Trigger 5 distinct trap types | Perm levitating |
| orpheus | Orpheus' Lyre | P | 5× pacifist sessions (10 turns adj enemies, no combat) | Monsters slowed 5t on floor entry |
| tantalus | Tantalus' Resolve | S | 15 quality-0 ruined meals | STR +1 |
| asclepius | Asclepius' Serpent | T | Harvest 15 distinct poison species | Animal +4s |
| fisher_king | The Fisher King's Vigil | P | Pray 6× at ≤15% HP | Prayer cooldown halved |
| anansi | Anansi's Clarity | S | 20 correct while confused | INT +1 |
| prometheus | Prometheus Unbound | P | 10 bleed episodes ≥5 turns | Perm regenerating |
| penelope | Penelope's Mastery | T | 100 armor (un)equip actions | Geography +3s |
| dionysus | Dionysus' Vision | T | 10 potions while hallucinating | Philosophy +3s |
| apollo | Apollo's Perfection | T | 10 max-chain hits | Math +3s |
| athena | Athena's Owl | T | See 50 distinct monsters | History +4s |
| loki | Loki's Gambit | S | Wear 5 cursed items ≥10 turns each | WIS +2 |
| thor | Thor's Oath | P | 30 combats with same weapon | That weapon enchant +2 |
| beowulf | Beowulf's Vow | P | 10 unarmed wins | Unarmed +5 base dmg |
| norns | The Norns' Thread | P | 20 recall_lore uses | Recall cooldown -50% |
| jormungandr | Jormungandr's Cycle | P | 20 (un)equips same weapon | Max chain +1 (that weapon) |
| shiva | Shiva's Third Eye | T | 100 turns hallucinating | Philosophy +5s |
| enkidu | Enkidu's Wildness | S | Harvest 20 distinct species | STR +1 |
| perseus | Perseus' Reflection | P | Reflect 5 status effects back | Debuffs on you 50% shorter |
| theseus | Theseus in the Labyrinth | S | Fully explore 5 floors | PER +1 |
| persephone | Persephone's Descent | P | Q5 meals from 5 distinct ings | Cooking max chain → 6 |
| hermes | Hermes' Wings | P | 8 teleports | Hasted duration ×2 |
| sibyl | The Sibyl of Cumae | T | 500 correct before L20 | ALL timers +2s |
| valkyrie | The Valkyrie's Eye | S | 25 ranged kills | DEX +1 |
| ahasverus | Ahasverus | P | 15,000 tile moves | Perm searching |
| circe | Circe's Cauldron | T | Cook 5 distinct bonus-type categories | Cooking +4s |
| gawain | Gawain's Bargain | S | 6 wins starting ≤40% HP | CON +1 |
| ariadne | Ariadne's Thread | S | 10 floor escapes within 30 turns | INT +1 |
| morgan | Morgan le Fay | S | 6 spells at ≤20% HP | INT +2 |
| cuchulainn | Cu Chulainn's Riastrad | S | 5 kills while feared | STR +1 |
| fenrir | Fenrir's Chains | S | 150 turns under debuff | CON +1 |
| kali | Kali's Dance | T | 100 kills same monster type | Theology +3s |
| medusa | Medusa's Gaze | S | 5 blinded-episode correct answers | DEX +2 |
| green_knight | The Green Knight | S | 5× survive single 30%+ max_hp hit | CON +1 |
| narcissus | Narcissus | S | 30 examine uses | PER +1 |
| cerberus | Cerberus | P | 300 stair uses | Perm warning |
| ragnarok | Ragnarok's Survivor | S | Reach L100 with ≤10 HP | CON +5 |
| spartacus | The Gladiator's Defiance | S | 20 kills with debuff active | STR +1, CON +1 |
| ramanujan | The Infinite Sum | T | 500 math correct in run | Math +5s |
| ibn_battuta | Ibn Battuta's Road | T | Fully explore 30 floors | Geography +4s |
| tesla | Tesla's Circuit | T | 50 wand zaps | Science +5s |
| de_medici | De Medici's Treasury | T | 20 lockpicks | Economics +4s |
| leonidas | The Last Stand | S | Kill on 30 distinct floors | CON +2 |
| confucius | The Analects | T | 50 philosophy correct while Blessed | Philosophy +4s |
| zoroaster | The Prophet's Vigil | T | Pray on 15 distinct floors | ALL timers +1s |
| boudicca | Boudicca's Fury | S | 50 kills missing >60% HP | STR +2 |
| solomon_q | Wisdom of Solomon | S | 100 philosophy correct | WIS +2 |
| atalanta | Winged Feet | S | 10 floors in ≤25 turns | DEX +2 |
| galileo | Galileo's Heresy | T | 100 science correct | Science +3s |
| caesar | Veni Vidi Vici | S | 300 kills in one run | ALL stats +1 |
| shakespeare | The Bard's Tongue | T | Read 50 scrolls | Grammar +5s |
| wanderlust_q | The Endless Wanderer | P | 20,000 tile moves | SP drain halved |
| nostradamus | The Prophet's Eye | S | Recall 10× while mental-debuffed | WIS +3 |
| archimedes | Give Me a Lever | S | 50 science AND 50 economics correct | INT +1 |
| machiavelli | The Prince | T | 500 correct in run | ALL timers +1s |
| darwin | Survival of the Fittest | S | 8 distinct debuff types survived | CON +3 |
| hypatia | Hypatia's Legacy | S | 50 math AND 50 science correct | INT +2 |
| diogenes | Diogenes' Lantern | S | Drop Shard, survive 10 levels without it | WIS +2 |

### Power quirks (active abilities) — `_ACTIVE_POWER_DEFS` at `quirk_system.py:1058-1089`

Triggered via the powers screen; uses-based unless `cooldown > 0`.

| ID | Trigger | Effect | Uses |
|---|---|---|---|
| philosophers_stone | Identify 200 items | Blessed + Brilliance 10t | ×1 |
| atlas_burden | Carry 90%+ wt for 100 turns | Heroism 20t | ×2 |
| zeus_bolt | Hasted 15× in run | Shock Resist + Hasted 15t | ×3 |
| gorgon_ward | Petrify survived 3× | Sleep Resist + Displacement 15t | ×2 |
| phoenix_rising | Survive ≤5% HP 10× | Fully restore HP | ×1 |
| eye_storm | 5 damage-free floors | Invisible + Blessed 10t | ×3 |
| iron_will | 10 hits while paralyzed | Shielded + Reflecting 10t | ×2 |
| battle_trance | 200 kills | Heroism 15t | ×3 |
| second_sight | Recall 5× while blinded | Telepathy + Clairvoyance 15t | ×3 |
| iron_ration | 15k tile moves | Restore 100 SP | ×5 |
| shadow_step | 2,500 invisible moves | Invisible + Phasing 5t | ×3 |
| focused_scholar | 500 correct | Brilliance 10t | ×2 |
| arcane_surge | 20 spells in run | Brilliance 10t + full MP | ×2 |
| death_wish | 10 wins at ≤10% HP | Heroism + Hasted 10t | ×3 |
| wandering_star | 15 teleports | Teleport (CD 50) | CD 50 |
| time_dilation | 25 consecutive correct | Time Stop 10t | ×1 |
| mirror_mind | Identify 100 | Reflecting + Magic Resist 10t | ×2 |
| metabolic | 5k tile moves | Restore 100 SP | ×3 |
| venom_lore | 5 turns poisoned+diseased | Poison Resist 20t + cure poison | ×3 |
| war_cry | 15 kills while feared | Hasted 8t | ×3 |
| mind_fortress | 30 correct while mental-debuffed | Clear all mental debuffs | ×3 |
| temporal_shield | Take 50 hits | Shielded 25t | ×2 |
| ancestral_q | Fully explore 10 floors | Clairvoyance 20t | ×2 |
| mystic_eye | Telepathy on 10 distinct floors | Telepathy+Clairvoyance+Warning 15t | ×3 |
| life_drain | 25 kills at ≤15% HP | Restore 25% max HP | ×3 |
| reality_anchor | 5 turns confused+hallucinating | Clear all debuffs | ×2 |
| runic_armor | All 3 resists active 10t | Fire+Cold Shield + Shock Resist 10t | ×2 |
| astral_form | 100 turns invisible | Levitate+Invisible+Phasing 8t | ×2 |
| sage_counsel | 50 history correct | Blessed 15t | ×3 |
| ouroboros | 1,000 correct in one run | Hasted+Shielded+Regen 20t | ×1 |

**Total quirks cataloged: 100** (71 passive/stat/timer + 29 active powers — `len(_QUIRK_PROGRESS) = 100`).

### Quirk-driven runtime flags (cross-references)

* `musashi_active` — combat damage at chain==1 uses 2nd multiplier instead of 1st (`combat.py:78-79`)
* `beowulf_unarmed_bonus = 5` — unarmed base damage +5 (`combat.py:117-118`)
* `persephone_active` — cooking max_chain = 6 (`main.py:2367-2370`)
* `wanderlust_active` — checked at SP-drain points (`main.py:2017` and quirk effect `wanderlust_q`)
* `hermes_active` — hasted duration doubled when applied (`player.py:231-233`)
* `perseus_active` — debuff durations halved on apply (`player.py:235-237`)
* `orpheus_active` — monsters slowed 5t on floor entry (`main.py:492`)
* `hephaestus_slot` — equip threshold -1 for that slot (`main.py:2898-2902`)
* `thor_qualifying_weapon` / `thor_enchant_pending` — +2 enchant on that weapon (`quirk_system.py:513-519`)
* `jormungandr_weapon_id` — max chain +1 (`combat.py:241-243`)
* `fisher_king_active` — prayer cooldown halved (`game_divine.py:781-782`)
* `fisher_king_mystery_active` — stacks with quirk (`game_divine.py:784-785`)
* `levels_without_shard` — Diogenes quirk progress key

---

## 6. Hack Reality (XYZZY)

The hidden debug terminal. Hinted at in T2 lore: *"a hidden terminal that accepts
a spoken word ... beside the number 1, quiet and overlooked"* (the backtick key).

* Player state: `hack_reality_cooldown`, `hack_reality_count`, `hack_tiers_claimed: set[int]` — `player.py:71-74`.
* Input flow: backtick → `_open_xyzzy_input()` (`main.py:2521-2525`) → user types "xyzzy" → confirm Y/N dialog → `_start_hack_reality()`. Backtick keybinding registered at `game_input.py:344`.
* Quiz: escalator_chain on subject `ai`, max_chain 5, tier 1 — `main.py:2543-2553`.
  Uses AI question bank.
* Cooldown:
  * chain 0 → 100 turn cooldown, SEGFAULT message (`main.py:2561-2566`)
  * chain ≥ 1 → `150 + chain × 30` turns = 180..300 (`main.py:2568`)
* Each tier 2–5 is **once per run** via `hack_tiers_claimed.add(tier)` (`main.py:2604, 2622, 2630, 2644`).

### Tier rewards (`main.py:2585-2655`)

| Tier | Chain | Reward | Repeatable? |
|---|---|---|---|
| 1 | ≥1 | Full HP/SP/MP restore + purge all negative status effects | Every successful XYZZY |
| 2 | ≥2 | Permanent random positive status: regenerating / hasted / see_invisible / fire_shield / cold_shield / reflecting / displacement / drain_resist | Once per run |
| 3 | ≥3 | All 6 stats permanently +5 | Once per run |
| 4 | ≥4 | Random legendary item from `container_loot_tier == 'legendary'` pool (fallback: all stats +3) | Once per run |
| 5 | ≥5 | Spawn Fenrir wolf pet (`pet_system.FenrirPet` at `pet_system.py:287`; fallback: all stats +3) | Once per run |

Tier labels in UI: ECHO / RESONANCE / CONVERGENCE / TRANSCENDENCE / SINGULARITY (`main.py:2576-2583`).

A first-XYZZY chronicle line is logged once: *"Spoke an old word of power. XYZZY. Reality flickered..."* (`main.py:2569-2571`).

---

## 7. Score economy

### Formula (`main.py:1479-1490`)

```python
score = turn_count * 10
      + max_level_reached * 1000
      + monsters_killed * 100
      + (50000 if has_stone else 0)
```

`has_stone` is True if the player carries `philosophers_stone` OR the completed
tablet (`complete_tablet_of_second_death`) — both qualify.

**Open question:** the formula awards 10 points per turn. This rewards survival
duration; against the difficulty contract this is fine but unmoored to skill.
No turn-count CAP is applied — a slow patient run scores linearly.

### Grade thresholds (`main.py:1492-1508`)

| Score | Grade |
|---|---|
| ≥ 200,000 | S |
| ≥ 100,000 | A+ |
| ≥ 60,000 | A |
| ≥ 30,000 | B+ |
| ≥ 15,000 | B |
| ≥ 7,000 | C |
| ≥ 3,000 | D |
| < 3,000 | F |

---

## 8. Sight / perception

`Player.get_sight_radius()` at `player.py:285-298`:

```
if head slot == 'blindfold':           return 0      # total darkness
if has_effect('blinded'):              return 1
radius = max(3, PER // 2)
if has_effect('dark_vision'):          radius += 4
if has_effect('truesight'):            radius += 2
```

| Source | Effect on sight | File:Line |
|---|---|---|
| PER stat | radius = `max(3, PER // 2)`, floor 3 | `player.py:293` |
| `blindfold` head armor | radius 0 | `player.py:288-290` |
| `blinded` debuff | radius 1, timer ×0.70 | `player.py:291, 315-316` |
| `dark_vision` permanent | +4 radius | `player.py:294-295` |
| `truesight` permanent | +2 radius, see invisible | `player.py:296-297` |
| `hallucinating` | timer ×0.80 (no sight effect) | `player.py:317-318` |
| `clairvoyant` | reveal 10-tile radius each turn (`main.py:1629-1635`); doesn't modify get_sight_radius |
| `searching` | auto-reveal adjacent tiles each turn |
| `warning` | sense monsters within 5 tiles |
| `telepathy` | all monsters visible regardless of FOV |

FOV is shadowcasting (`fov.py` — not read here). Hint: the system is in `_refresh_fov()`.

---

## 9. Quiz timer system

### Base table (`player.py:12-30`)

```python
SUBJECT_TIMER = {
    'math':       (8,  0.8),    # combat — snappy
    'science':    (24, 1.2),
    'grammar':    (20, 1.0),
    'trivia':     (26, 1.2),
    'geography':  (28, 1.2),
    'history':    (32, 1.6),
    'animal':     (32, 1.6),
    'ai':         (40, 1.5),
    'philosophy': (40, 1.5),
    'cooking':    (44, 1.6),
    'theology':   (48, 1.7),
    'economics':  (48, 1.7),
}
```

`get_quiz_timer(subject) = round(base + WIS × scale)` — `player.py:300-305`.

At WIS 10: math 16s, science 36s, grammar 30s, trivia 38s, geography 40s,
history 48s, animal 48s, ai 55s, philosophy 55s, cooking 60s, theology 65s,
economics 65s.

### Multiplicative modifiers (`player.py:307-323`)

```
mod = 1.0
× 0.55 if confused
× 0.75 if stunned
× 0.70 if blinded
× 0.80 if hallucinating
× 1.25 if hasted
× 1.25 if blessed
floor: max(0.40, mod)        # hard floor at 40% of base
```

Stacked debuffs can floor the timer at 0.40× regardless of how many apply.

### Per-subject WIS bonuses (`player.quiz_timer_bonuses` dict)

Filled by quirks (see §5 table): math +3s (apollo) + 5s (ramanujan); grammar +5s
(scheherazade) + 5s (shakespeare); science +4s (merlin) + 3s (galileo) + 5s
(tesla); geography +3s (penelope) + 4s (ibn_battuta); history +4s (athena);
animal +4s (asclepius); cooking +4s (circe); philosophy +3s (dionysus) + 5s
(shiva) + 4s (confucius); theology +3s (kali); economics +5s (sisyphus) + 4s
(de_medici).

Plus **ALL subjects** bonuses: sibyl +2s, zoroaster +1s, machiavelli +1s, caesar
implicitly via WIS gain.

Equipment-granted: **Ancile shield** (`shield.quiz_timer_bonus`) adds to every
subject (`player.py:333-336`).

### INT bonus (`player.py:325-327`)

`get_int_quiz_bonus() = max(0, INT − 10) // 2` extra seconds — applied to
**identify-philosophy quizzes only** (`game_magic.py:2034`). Not currently applied
to science or grammar despite the docstring claim.

---

## 10. Identification

### Auto-ID

* **Philosopher's Stone**: on pickup, grants permanent `identify_sight` status AND
  calls `_auto_identify_all()` on existing inventory/ground/equipped items
  (`main.py:2151-2160`, `game_magic.py:2365-2377`).
* **`identify_sight` status** (`status_effects.py:70`): future pickups are auto-ID'd
  (`main.py:2107-2110`).
* **Accessories with `identify_sight` effect** (none in current data: only the
  Stone grants this).
* **`buc_known` auto-reveal**: at floor ≥ 30 with WIS ≥ 14, every pickup's BUC is
  revealed (`main.py:2166-2173`).

### Manual identify

`_identify_item()` at `game_magic.py:1985-2036`:
* Subject: **philosophy**, mode: **threshold**.
* Tier scales: `id_tier = item.quiz_tier` (defaults to 1 if missing).
* Threshold: `id_tier + 1` — Tier 1 needs 2 correct, Tier 5 needs 6 correct.
* Extra seconds: `get_int_quiz_bonus()` (INT-based).
* On success: `item.identified = True`, `item.buc_known = True`,
  `known_item_ids.add(item.id)`, `_propagate_identification(item.id)` marks all
  same-id items in inventory as buc_known, then triggers
  `quirk_system.on_item_identified()` (counts toward mirror_mind / philosophers_stone power quirks).

### Persistent tracking

* `player.known_item_ids: set[str]` — set of item IDs identified in this run
  (`player.py:84`).
* `player.known_monster_ids: set[str]` — monsters seen in FOV (`player.py:86`).
* `player.lore_known_monster_ids: set[str]` — monsters whose corpse has been
  studied (`player.py:87`).
* **Cross-run persistence**: NO. Bones (`bones.py`) preserve a ghost monster but
  not identification state. Each run starts fresh.

### Other identify sources

* Wand `identify_item` effect — ID first unidentified inventory item
  (`game_magic.py:787-795`).
* Scroll `identify_all` (Tier 4) — ID all unknown inventory (`game_magic.py:1838-1849`).
* Mystery throne chain 3 — ID all unknown inventory (`game_divine.py:650-660`).
* Reading or zapping an unidentified scroll/wand identifies it on first use
  (`game_magic.py:156, 223, 1562, 1571`).

---

## 11. Cross-system interactions (top picks)

1. **Cooking-as-leveling is the ONLY scalable max-HP track outside of CON gain**
   (`player.py:180` says `HP_PER_LEVEL = 0`; `STAIR_REST_CAP_DESC = 0` means
   descending stairs do not grant max HP). The `cooking_hp_gained` softcap (1000)
   is fixed regardless of dungeon level, creating the central balance tension
   surfaced in REVERSE_ENGINEERED.md (a patient L30 cook over-levels for L30
   monsters, while a non-cook at L100 has ~44 HP).
2. **Fisher King double-stack**: the FK quirk halves prayer cooldown AND the FK
   mystery sets `fisher_king_mystery_active`, halving AGAIN — both at
   `game_divine.py:781-785`. Effective cooldown can drop to ~25% of base.
3. **Stone → identify_sight → power quirk identifies**: picking up the Stone
   ID's everything in inventory (`main.py:2157`), which can trigger Mirror Mind
   (100 items) and Philosopher's Stone (200 items) power quirks in one frame.
   Each individual ID also counts toward `items_identified` via
   `quirk_system.on_item_identified()` (`game_magic.py:2007-2009`).
4. **Persephone × Cooking quality**: Persephone bumps cooking max_chain to 6
   (`main.py:2370`) but `quality = min(5, score)` (`food_system.py:138, 237`) caps
   reward at Q5 — the 6th chain step has NO direct cooking payoff. Suspicious;
   may be intentional (one "free" answer / failure buffer) or oversight. **Open
   question:** is the 6th step meant to add a bonus that's missing in code?
5. **L100 altar interaction with quirks**: prayer at L99 altar with chain > 0
   strips Abaddon resistances for `chain × 2` turns AND counts toward Zoroaster
   (15 distinct prayer-floors), Fisher King prayer count, and prayer_boon_count
   (WIS gain). One altar prayer can advance four progression tracks at once
   (`game_divine.py:750-777`, `quirk_system.on_prayer:785-797`).

Other notable cross-system links:

* **Caesar quirk** (`+1 all stats`) interacts with cooking softcap: triggers
  CON +1 → +1 max_hp ALONGSIDE cooking gains; doesn't consume the cooking budget.
* **Hack Reality Tier 3** (+5 all stats) is the single biggest single-event stat
  gain in the game (+30 stat points → +5 max_hp, +5 max_sp, +5 max_mp).
* **Khopesh of Anubis** (`kill_max_hp_bonus` with `kill_max_hp_cap`) is an
  *independent* permanent max_hp track that doesn't touch `cooking_hp_gained`
  (`combat.py:220-228`). Capped per-weapon-instance.
* **Coat of Cú Chulainn** triggers berserk at low HP via `armor.berserk_trigger`,
  granting `berserk_str_bonus` directly to `player.STR` (not via apply_stat_bonus,
  so NO max_sp side-effect) and an HP cost per turn (`main.py:1601-1619`,
  `status_effects.py:408-414` for refund).
* **Lockpick charges** are stored as a player-level pool (`player.lockpick_charges`)
  rather than per-item, picked up from Lockpick items (`main.py:2095-2102`).

---

## 12. Open questions / suspected gaps

1. **Persephone quirk's 6th chain has no reward** — Q is clipped at 5 in the
   quality lookup. Either the formula tables should extend to Q6 (Q6 → ~3.0× SINGLE,
   ~6.0× COMPOUND extrapolated) or the 6th chain is "free padding" (you can fail
   one without dropping quality). Should be ratified.
2. **INT bonus claim mismatch** — `get_int_quiz_bonus()` docstring says
   "science/grammar/philosophy" (`player.py:326`), but it is only applied at
   `game_magic.py:2034` (identify philosophy quiz). Science wand/scroll quizzes
   use `get_quiz_extra_seconds()` instead. Documentation says one thing, code does
   another.
3. **Cooking 1000 softcap not floor-aware** — known issue from REVERSE_ENGINEERED.md;
   ceiling is asymptotic to ~1000 regardless of dungeon level reached.
4. **Score formula rewards turn_count** — a survive-and-camp run scores linearly.
   No cap; no efficiency multiplier. Open question whether the formula should
   include a turn-per-floor efficiency factor.
5. **THAC0 floor only in data, not code** — the audit consensus flag of "hardcoded
   THAC0 floor at -16" appears to be DATA-floor, not code-floor. No `combat.py`
   line clamps thac0 — every monster in `monsters.json` simply has thac0 ≥ -16.
   Lowering values below -16 is allowed by the code; this is a content gap, not
   a code bug.
6. **Hack Reality cooldown re-claim** — `hack_tiers_claimed` persists across saves
   (set on player). Once a player claims tiers 2-5, they can never claim them
   again in the same run — correct. But on a NEW run, the `hack_tiers_claimed`
   set is reset (new `Player()` initializes it as `set()` at `player.py:74`). So
   each run has independent XYZZY tier claims. **No cross-run XYZZY persistence.**
7. **The `gain_level` potion effect** signals via `messages.append("_gain_level")`
   at `food_system.py:483` and is intercepted in `game_menus.py:181-182` to ascend
   one floor — bypassing the dungeon's exploration / stair-rest costs. Identified
   as `boost` effect type but has no other power.
8. **Quirk file header comment is stale** — says "50 Bofuri-style traits" but the
   actual registry has 100 entries (71 passive/stat/timer + 29 active powers).
9. **The `_QUIRK_NAMES` dict's quirk count: 100; `_QUIRK_TRIGGER`: 100; `_QUIRK_EFFECTS`: 100** — all aligned.
   `_QUIRK_PROGRESS` is 100. The `_ACTIVE_POWER_DEFS` is 29 (one less than the 30 power-tier quirks listed in
   the table above — sage_counsel & some others) — sage_counsel IS in `_ACTIVE_POWER_DEFS` at line 1064.
   **Verified: 100 quirks total, 29 active power definitions.**
10. **Diogenes' Lantern progress**: requires player to drop the Philosopher's Shard
    and survive 10 dungeon levels without it. The `levels_without_shard` counter
    has no obvious increment site visible from grep — needs verification of where
    it's incremented (likely in level_manager or game_input on stair use).
