# Mastery Blessing Schema

A `mastery_blessing` is granted to the player when they identify a unique item
to chain depth 5 (escalator-chain philosophy quiz). The blessing is permanent
for the remainder of that run, tied to the item's id, and **only one
mastery per unique item-id can ever be claimed**.

All blessings have this shape:

```json
{
  "kind":  "<one of the allowed kinds>",
  "value": <kind-specific payload>,
  "scope": "item",
  "desc":  "<one-line player-facing description>"
}
```

`scope` is always `"item"` for now (the bonus is tied to the specific named
unique). Class-wide masteries are a future extension.

`desc` must be a single sentence that names the item explicitly and reads
fluidly inline — it's shown in the player's message log when the mastery
is gained.

## Allowed kinds

### Weapon masteries (use only on weapon entries)

| kind | value | what it does |
|------|-------|---|
| `weapon_chain_mult_bonus` | number (typ. 0.15-0.35) | Adds that flat amount to every chain multiplier for this weapon. |
| `weapon_base_damage_bonus` | int (typ. 2-5) | Adds flat damage to every hit. |
| `weapon_damage_vs_tag` | `{"tag": "<monster tag>", "pct": int 20-50}` | +pct% damage when target has that tag (e.g. `undead`, `demon`, `dragon`, `construct`, `beast`, `humanoid`, `fey`, `giant`, `evil`). |
| `weapon_first_hit_crit` | `true` | First swing of every chain auto-crits. |
| `weapon_lifesteal` | number 0.1-0.25 | Heals % of damage dealt. |
| `weapon_wound_lingers` | int 3-6 | Each hit extends bleeding by N turns. |
| `weapon_status_chance` | `{"status": "<id>", "pct": 15-30, "duration": 2-3}` | Chance per hit to apply status. Statuses: `stunned`, `paralyzed`, `frozen`, `burning`, `poisoned`, `slowed`, `confused`, `bleeding`. |

### Armor / Shield masteries (use only on armor or shield entries)

| kind | value | what it does |
|------|-------|---|
| `armor_ac_bonus` | int 1-2 | Extra -AC while worn (lower = better). |
| `armor_resist_bonus` | `{"type": "<element>", "pct": 20-50}` | Resist N% of incoming damage of type. Types: `fire`, `cold`, `lightning`, `acid`, `poison`, `psychic`, `holy`, `unholy`, or `all_elemental` for all 5 elements at once. |
| `armor_hp_bonus` | int 10-25 | Permanent max-HP bump applied once when mastered. |

### Accessory masteries (use only on accessory entries)

| kind | value | what it does |
|------|-------|---|
| `accessory_stat_bonus` | `{"stat": "<STR/CON/DEX/INT/WIS/PER>", "amount": 1-2}` | Permanent +N stat applied once when mastered. |
| `accessory_passive_strength` | one of the sub-shapes below | Augments an existing passive on the accessory. |

`accessory_passive_strength` sub-shapes:

- `{"kind": "passive_regen_bonus", "value": 1-3}` — adds N HP to each regen tick from this accessory.
- `{"kind": "gold_multiplier", "value": 2.5-3.0}` — final gold-pickup multiplier (replaces accessory's gold_multiplier if higher).
- `{"kind": "gold_finds_pct", "value": 25-50}` — gold piles on the floor are N% larger.
- `{"kind": "resurrect_to_full"}` — if the accessory grants a resurrect, restore full HP instead of partial.
- `{"kind": "buff_duration_bonus", "value": 5-10}` — buffs granted by this accessory last N turns longer.

### Wand / Scroll / Spellbook / Potion masteries

| kind | applies to | value | what it does |
|------|---|-------|---|
| `wand_extra_charge` | wand | int 1-3 | +N maximum charges, applied once on mastery. |
| `scroll_extra_read` | scroll | 1 | The first read after mastery does NOT consume the scroll. |
| `spellbook_mp_discount` | spellbook | int 1-3 | The book's spell costs N fewer MP, applied once on mastery if already learned. |
| `potion_potency_bonus` | potion | number 0.25-0.5 | Effects from this potion type are +N more potent. |

## Design rules

1. **Lore-faithful.** Match the mastery to the item's lore. The Sword of Michael deals +damage to demons because the saint slays demons; the Coat of Cú Chulainn boosts HP because Cú Chulainn was nigh-invincible; the Belt of Strength gives +STR because it literally is the belt of strength.
2. **Small but meaningful.** Stay within the value ranges in the tables. Mastery should feel like a tangible run-extending perk, not a build-defining game-changer.
3. **Pick the kind that fits the item.** Don't pick the same kind for every weapon. Spread variety across the catalog. Don't give 50 weapons +chain_mult_bonus — use the full kind palette.
4. **Pick monster tags from this set only:** `undead`, `demon`, `dragon`, `construct`, `beast`, `humanoid`, `fey`, `giant`, `evil`, `aberration`. Don't invent new tags.
5. **Don't reuse `desc` strings.** Each mastery's desc should reflect the specific named item.
6. **Output JSON only.** No commentary. Schema as documented above. One blessing per item_id.

## Exemplars

These 20 are already authored and represent the target quality / specificity:

| Item | Kind | Why this fits |
|------|------|---|
| Soul Reaver | weapon_wound_lingers (5) | Lore: wounds don't heal naturally |
| Dawnbreaker | weapon_damage_vs_tag (undead, 35%) | Lore: the dawnlight scatters the unliving |
| Excalibur | weapon_chain_mult_bonus (0.25) | The peerless blade; better in every swing |
| Mjolnir | weapon_status_chance (stunned, 25%/2) | The hammer of thunder, stuns its target |
| Hrunting | weapon_base_damage_bonus (4) | Beowulf's first ancient blade — raw heft |
| Gungnir | weapon_first_hit_crit (true) | Odin's spear NEVER misses its first throw |
| Khopesh of Anubis | weapon_lifesteal (0.2) | The death-god's blade drinks souls |
| Sword of Michael | weapon_damage_vs_tag (demon, 50%) | The archangel's blade undoes hellspawn |
| Babr-e Bayan | armor_resist_bonus (all_elemental, 20%) | Tiger-skin coat: elementally invulnerable |
| Coat of Cú Chulainn | armor_hp_bonus (20) | Cú Chulainn's vitality was legendary |
| Dragon-Sewn Mail of Sigurd | armor_resist_bonus (fire, 50%) | Dragon-slayer's mail: dragonfire-proof |
| Greater Aegis of Athena | armor_ac_bonus (2) | The peerless shield of the goddess |
| Andvaranaut | accessory_passive_strength (gold_finds_pct, 50) | The dwarf-gold ring summons more wealth |
| Draupnir | accessory_passive_strength (gold_multiplier, 3.0) | The self-replicating ring: every drop, eightfold |
| Megingjörð | accessory_stat_bonus (STR, 2) | Literally Thor's belt of strength |
| Ankh of Isis | accessory_passive_strength (resurrect_to_full) | Isis raised Osiris from the dead — wholly |
| Eye of Horus | accessory_passive_strength (passive_regen_bonus, 2) | The Eye is the symbol of perfect restoration |
| Aaron's Rod | wand_extra_charge (3) | The rod that never ran out of miracles |
| Scroll of Annihilation | scroll_extra_read (1) | The spoken word of unmaking, mastered |
| Necronomicon | spellbook_mp_discount (3) | The forbidden book whispers its words for free |
