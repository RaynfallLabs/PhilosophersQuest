# Boss Class Ascension — design draft (2026-06-07)

## The pitch
Each of the **first four bosses** drops a unique **Legendary Cut**. Cooking it at the
cauldron isn't a meal — it's an **Ascension**: you commune with the slain boss's
essence and advance your **class**. Over a run you build a four-step identity:

```
Floor 20  Labyrinth boss  →  CALLING        (pick 1 of 4 base classes)
Floor 40  Temple boss     →  SPECIALIZATION (pick 1 of 4 subclasses on your path)
Floor 60  Lair boss       →  MASTERY        (pick 1 of 2 mastery paths)
Floor 80  Hall boss       →  CAPSTONE       (your subclass's signature power)
Floor 100 Abaddon         →  (no meal — the final fight tests the build you forged)
```

**Key framing: this REPLACES the boss trophy-meal reward, it doesn't add to it.**
Today those four bosses' trophy recipes grant a one-off `permanent_power`. We
repurpose that same power budget into a choice-driven class path — *more identity
and replayability, same total power.* That's the anti-power-creep anchor.

### Thematic hook (free synergy with the quiz subjects)
The four callings map onto the game's action-subjects, so a class leans into the
quizzes you're already good at:

| Calling | Leans on | Fantasy |
|---|---|---|
| **Fighter** | math (combat chains) | knight / warrior |
| **Mage** | science (wands/spells) | scholar-wizard |
| **Rogue** | economics (locks) + animal (harvest) | scout / cutpurse |
| **Cleric** | theology (prayer) | crusader-priest |

---

## The tree shape (content-scoped on purpose)
A literal 4→4→4→4 tree is 256 leaf paths and ~340 nodes — far too much content.
We honor the *branching* (each tier depends on the last) but bound it:

```
            Tier1: 4 base classes
              └─ Tier2: 4 subclasses each      = 16
                   └─ Tier3: 2 mastery paths    = 32   (binary, not 4-way)
                        └─ Tier4: 1 capstone     = 16   (one signature per subclass)
Total authored nodes ≈ 4 + 16 + 32 + 16 = 68
```

A single playthrough makes **4 choices**. The 68 nodes are the whole content
budget — comparable to one subject's worth of items, and reusing existing effect
plumbing (no new combat math).

---

## Tier 1 — the four CALLINGS (full detail)
Each is a small package: a couple of stat points, one **proficiency** (flat %),
and one **once-per-floor ability**. Roughly one good accessory's worth of power.

- **Fighter** — +1 STR, +1 CON. *Proficiency:* +10% melee damage. *Ability:*
  **Second Wind** (1×/floor: heal 15% max HP).
- **Mage** — +2 INT. *Proficiency:* +10% spell/wand damage. *Ability:*
  **Arcane Recovery** (1×/floor: restore 25% max MP).
- **Rogue** — +1 DEX, +1 PER. *Proficiency:* +15% backstab/crit damage; spot
  traps one tile farther. *Ability:* **Evasion** (auto-dodge the first trap each floor).
- **Cleric** — +1 WIS, +1 CON. *Proficiency:* +20% healing received; prayer
  cooldown −15%. *Ability:* **Divine Favor** (1×/floor: bless next action / minor smite).

---

## Tier 2 — the SUBCLASSES (16; Fighter branch worked, rest named)
At floor 40 you pick one of four subclasses *on your calling's branch*. Each adds
+1–2 stats, upgrades or adds a proficiency, and grants a second ability.

**Fighter →** worked example:
- **Berserker** — +2 STR; +15% damage while below 50% HP; *Ability:* **Rage**
  (1×/floor: +damage, −AC, a few turns).
- **Knight** — +2 CON; +2 AC while a shield is equipped; *Ability:* **Bulwark**
  (1×/floor: brace, halve next hit).
- **Weapon Master** — +1 STR/+1 DEX; pick a weapon class for +20% damage with it;
  *Ability:* **Riposte** (1×/floor: free counter on a dodged hit).
- **Warlord** — +1 STR/+1 WIS; your once-per-floor abilities recharge on a kill
  streak; *Ability:* **Battle Cry** (1×/floor: fear nearby weak foes).

**Mage →** Evoker · Necromancer · Enchanter · Battlemage
**Rogue →** Assassin · Trickster · Scout · Swashbuckler
**Cleric →** Crusader · Oracle · Druid · Inquisitor

*(Each of the other 12 gets the same shape as the Fighter four — Phase-2 work.)*

---

## Tiers 3 & 4 — MASTERY + CAPSTONE (Berserker worked)
**Tier 3 = a binary mastery path** (an offense vs. utility fork), keeping the
branch alive without a content explosion:
- **Berserker → Bloodrager** (offense): Rage also lifesteals 10%; +1 STR.
- **Berserker → Juggernaut** (utility/defense): Rage no longer lowers AC; +1 CON.

**Tier 4 = one signature CAPSTONE per subclass** — strong, build-defining, late
(floor 80), and singular:
- **Berserker capstone — Undying Fury:** the first time you would die each floor,
  survive at 1 HP and enter Rage for free. (One charge per floor.)

Capstones are the payoff; by floor 80 the enemies justify one defining power.

---

## Balance — "fun but not overpowering"
The guard-rails, concretely:

1. **It's the boss reward, not a bonus on top of one.** Replaces the trophy meal's
   `permanent_power`. Net power budget unchanged; we're spending it better.
2. **Small per tier.** Whole-run total ≈ **+6–8 stats**, 3–4 *once-per-floor*
   abilities, 1–2 flat proficiencies, 1 capstone. (For scale: a stat ring is +1–2.)
3. **Separate, capped stat pool.** Class stat grants count against their own cap
   (suggest **+10 total**), independent of cooking's per-floor cap — no stacking loophole.
4. **Additive, not multiplicative.** Proficiencies are flat % adds; abilities are
   floor-gated (not spammable). No infinite loops with masteries/quirks/builds.
5. **Late capstone.** The one genuinely strong effect arrives at floor 80, against
   deep-dungeon difficulty — earned, not early-game snowball.
6. **Permanent choices (proposed).** No respec → each pick has weight and the build
   is a story, which also drives replayability.

---

## Gating options (your "make it harder" idea)
- **(A) Ungated** — all four callings always offered. Simplest; pure player choice.
- **(B) Soft-gated (recommended)** — each calling has an *earned* sign: Mage wants
  INT ≥ 14 *or* a wand/spellbook carried; Rogue wants N backstabs *or* traps found;
  Cleric wants N prayers; Fighter is always open (the default path). All remain
  *pickable*, but the ones you've played toward are highlighted as "answered." Fun,
  rewards playstyle, no hard walls.
- **(C) Hard-gated** — you must collect a **class token** (drops from themed
  monsters) to even see a calling. More friction, more build-planning; risk of a
  player getting locked out of every option on an unlucky run.

---

## Integration sketch (reuses existing plumbing)
- **Data:** new `data/classes.json` — nodes keyed by id: `{tier, parent, name,
  flavor, stat_bonuses, proficiency, ability, requirements}`.
- **Cooking hook:** give each of the 4 bosses a **Legendary Cut** recipe whose
  cook, instead of `_apply_tier_outcome`, emits a `_class_ascension` signal (same
  pattern as `_gain_level` / `_teleport` / the new `_preserve`). The game opens the
  **Ascension screen** filtered to the player's current tier + path + met requirements.
- **Selection UI:** a new screen modeled on the welcome-screen build picker — shows
  each available node with its bonuses; pick one.
- **Applying a node:** reuse what exists — `apply_stat_bonus` for stats; a new
  `player.class_features` set that combat/magic read for proficiencies; the existing
  per-floor charge system (`armor_procs` / `chain_passives`) for once-per-floor abilities.
- **Persistence:** `player.class_path = [node_id, …]`; features re-derived on load.
- **Combat/magic:** proficiency reads sit beside the existing weapon-class/INT
  scaling; abilities surface in the power (`p`) menu.

## Phasing (each phase independently playable)
1. **Framework + Tier 1** — data model, cooking hook, Ascension UI, 4 callings.
   Playable end-to-end with just the base classes.
2. **Tier 2** — the 16 subclasses.
3. **Tiers 3–4** — mastery paths + capstones.

## Open questions for you
1. **Tree shape:** OK with 4 → 16 → 32 → 16 (binary Tier 3, single capstone Tier 4)?
2. **Gating:** A (ungated), B (soft, recommended), or C (hard class-tokens)?
3. **Archetypes:** Fighter / Mage / Rogue / Cleric — or reskin to the Crusader
   theme (Knight / Scholar / Outrider / Chaplain)?
4. **Permanent vs. respec:** lock choices in (recommended) or allow re-cooking to swap?
