# Legendary Uniques: Magic Items, Accessories & Artifacts

Authoring 111 uniques across five categories. **Revised triage**: most accessories now stay flat-passive (threshold equip, static bonuses, single proc). Chain-equip (escalator OR chain mode, history subject) is reserved for pieces whose LORE specifically suggests a tier/chain mechanic: a ritual recognition, a sequence of bites, a generational curse, a multi-step bargain, a story told one night at a time. Re-equip is always FRESH — no sticky state.

Magic items (wands/scrolls/spellbooks) use escalator-chain natively as their cast mode — they keep their proposed mechanics. Artifacts keep their narrative-dominant quest role with light inventory-active overlays.

Quiz-subject mapping per the brief: accessories = history, scrolls/spellbooks = grammar, wands = science, artifacts = item-specific (often theology or history).

**Triage result: 9 chain-equip accessories survive. The rest are flat with a single proc.**

---

## 1. God-Touched Accessories

The flat-passive default for accessories. Chain-equip is reserved for the items where the LORE actually demands a ritual: Solomon's ring recognising its bearer, Isis reassembling the body, Ahriman's heart teaching unmaking in stages.

### Seal of Solomon (ring_of_solomon)

**Lore hook**: The ring given to Solomon from heaven that let him command demons and djinn and bind Asmodeus.

**Equip mode**: `escalator` (5 rungs)
**Why this mode**: The lore IS ritual recognition — the ring tests its bearer's wisdom before granting Solomon's authority. Each correct tier-question is the ring deciding you are Solomon.

**Tier bonuses**:
- T1: INT +1, WIS +1
- T2: INT +2, WIS +2, detect_magic (auto-reveals nearby wand/scroll/spellbook auras within sight)
- T3: INT +2, WIS +3, `pacify_chance` 0.15 on first sight of any demon/devil monster
- T4: INT +3, WIS +3, `pacify_chance` 0.20, telepathy, summoned creatures within sight fight at half STR
- T5: full Solomonic suite (see below)

**T-max named ability**: **Solomonic Key** — bypass any lock (chest, door) in line of sight 1/floor; once per floor, command an undead/demon you can see to fight for you for 20 turns.

**Why legendary**: at T5 you ARE Solomon for one floor. Locks open. Demons obey.

**Code needed**: tier_escalator infra (shared with armor proposal); lock-bypass action (moderate); summon-command flag on monster instance (moderate); pacify_on_sight already exists.

### Brisingamen (brisingamen) — FLAT (reverted from tier-escalator)

**Lore hook**: Freya's necklace, forged by four dwarves over four nights, paid for in four nights of her company.

**Passive bonus**: WIS +3, passive_regen 1/5t with +1 HP per tick, status `regenerating` active while worn, +2 to chain-bonus rolls vs giant/jotunn-tagged monsters.

**Proc**: **Tears of Freya** — when reduced below 25% HP, drop 2-3 gold pieces on the floor each turn until healed above 50%; this gold can be picked back up. Constant while the threshold is met.

**Why legendary**: a passive that bleeds gold when you bleed HP — costs nothing if you avoid danger, dramatic if you don't.

**Code needed**: low-HP gold drop tick (simple); jotunn tag check already in monsters.

### Aegis-pair Talisman / Palladium of Troy (talisman_of_troy) — FLAT (reverted from tier-escalator)

**Lore hook**: Athena's wooden image, said to have fallen from heaven. Troy was invincible while it stood within the walls.

**Passive bonus**: AC +2, `reflecting` status, fear_resist +2.

**Proc**: **Walls of Troy + Inviolate** — for 15 turns after entering each new floor, incoming spell damage is halved. Additionally, the first time per floor you would be reduced below 1 HP, you stop at 1 HP and gain 5 turns of `regenerating`.

**Why legendary**: Troy was invincible while the statue stood within the walls. The proc is "you cannot die on this floor without warning."

**Code needed**: floor-entry buff timer (simple); HP-floor save with attached regen (moderate).

### Eye of Horus (eye_of_horus) — FLAT (reverted from tier-escalator)

**Lore hook**: The wedjat — Horus's eye, torn out by Set, healed by Thoth. Oldest healing symbol in human history.

**Passive bonus**: PER +3, passive_regen 1/5t with +2 HP per tick, blindness_immune, see_invisible.

**Proc**: **Wedjat's Restoration** — once per floor, if you fall below 10% HP, regen ticks fire every turn for 10 turns.

**Why legendary**: the oldest healing symbol becomes an "I refuse to die" passive.

**Code needed**: low-HP burst-regen trigger (simple).

### Tyet of Isis (tyet_of_isis)

**Lore hook**: The Knot of Isis. From the Book of the Dead, Chapter 156: "You possess your blood, Isis; you possess your power." Always red jasper. Always.

**Equip mode**: `escalator` (5 rungs)
**Why this mode**: Isis reassembled Osiris from fourteen scattered pieces. Each tier rung IS another piece returning — the lore is sequential reassembly.

**Tier bonuses**:
- T1: WIS +2
- T2: WIS +2, `life_save` (first lethal blow per run reduces you to 1 HP)
- T3: WIS +2, life_save, +1 to all death-saves
- T4: WIS +3, life_save resets per floor (not per run)
- T5: WIS +3, full reassembly (see below)

**T-max named ability**: **Reassembly** — life_save now revives to FULL HP and grants 10 turns of `regenerating`; once per run only.

**Why legendary**: T5 is the Egyptian resurrection mythology compressed into one button, earned by reassembling the knot piece by piece in quiz form.

**Code needed**: per-floor life-save reset (simple); existing resurrect_to_full mechanic (already implemented for Ankh).

### Heart of Ahriman (heart_of_ahriman)

**Lore hook**: Ahriman is anti-being, the principle of unmaking. His heart, if extractable, holds complete knowledge of what can be destroyed.

**Equip mode**: `escalator` (5 rungs)
**Why this mode**: Zoroastrian dualism is staged — Ahriman's negation deepens with comprehension. Each rung is the bearer accepting another layer of what-can-be-destroyed.

**Tier bonuses**:
- T1: INT +2
- T2: INT +3, magic damage you deal +10%
- T3: INT +4, magic damage +15%, **Unmaking Sense** — your spell crits ignore magic resistance
- T4: INT +5, magic damage +20%
- T5: INT +5, magic damage +25%, Anti-Being (see below)

**T-max named ability**: **Anti-Being** — once per floor, your next destructive spell (fireball, cone of cold, magic missile, lightning bolt, annihilate) deals double damage; if it kills a unique monster, the heart pulses warmly for 50 turns and grants +2 INT.

**Why legendary**: Zoroastrian dualism as DPS curve. The flavor text matters — it should be warm. Players will check.

**Code needed**: spell-damage multiplier on item (simple); unique-kill trigger (moderate); spell-crit ignore-resist (moderate).

### Ankh of Isis (ankh_of_isis) — FLAT (reverted from tier-escalator)

**Lore hook**: Isis reassembled Osiris from fourteen pieces and breathed life back into him.

**Passive bonus**: CON +2, `resurrect_on_death: true`, +1 to all death/poison/magic saves. On revive, gain 30 turns of `regenerating` and 5 turns of damage reduction (`protected`).

**Proc**: **Resurrect to Full** — current mastery_blessing made baseline. The death revive restores FULL HP rather than 1 HP. Stays in mastery list for the legend tier but no longer gated.

**Why legendary**: a one-of-a-kind item built around its single resurrection moment.

**Code needed**: existing resurrect_to_full mechanic; baseline rather than mastery-gated.

### Pectoral of Amun (pectoral_of_amun) — FLAT (reverted from tier-escalator)

**Lore hook**: Amun was "the hidden one," invisible by definition; his cult image was sealed inside Karnak even from his own priests.

**Passive bonus**: WIS +4, +1 to identification quiz bonuses, +2 to theology-quiz timer (Amun was the patron of decisions).

**Proc**: **Hidden One** — once per floor, take a turn invisible to all enemies at the cost of 10 MP; if you attack while invisible you remain invisible until next turn.

**Why legendary**: a god of decisions extending the quiz timer plus a one-per-floor invisibility burst.

**Code needed**: subject-specific quiz-timer bonus (moderate — need item-driven timer adjust per quiz subject); invisible-attack-persistence (simple).

---

## 2. Heroic Personal Accessories

Items tied to a single named hero. Two pieces (Gawain, Scheherazade, Atalanta) earn chain-equip — their lore IS a sequence. The rest revert to flat with a per-floor or per-run proc.

### Ring of Sir Gawain (ring_of_gawain)

**Lore hook**: From the Alliterative Morte Arthure — Gawain's strength grew until noon, peaked till three, and diminished thereafter.

**Equip mode**: `chain` (5 rungs)
**Why this mode**: The dip-curve IS the lore. Each chain step is an hour of the day — morning-rise, noon-peak, three-o'clock-dip. Chain rather than escalator because chain-break maps directly to "the sun has passed."

**Chain bonuses** (cumulative as chain extends, dip-shaped per design brief's Damocles precedent):
- chain 1: STR +1 (morning)
- chain 2: STR +2, +1 to attack chain length (mid-morning)
- chain 3: **Noon-rise** — STR +4, hasted (current `hasted` status)
- chain 4: STR +5 (the peak — three hours past noon)
- chain 5: STR +3, hasted, Three O'Clock (see below)

**T-max named ability**: **Three O'Clock** — every 30 turns of combat, your STR bonus from this ring shrinks by 1 (min +2), then RESETS to +4 after resting two full turns out of combat.

**Why legendary**: a strength curve that breathes with the lore. Players must learn to time their pushes.

**Code needed**: per-turn STR decay counter + reset-on-rest (moderate); attack-chain-length item bonus (simple).

### Ring of Odysseus (ring_of_odysseus) — FLAT (reverted from tier-escalator)

**Lore hook**: Odysseus had no magic ring. He needed none. The ring is his in retrospect.

**Passive bonus**: PER +4, `searching` status, +1 to escalator-chain caps on any quiz (math, history, etc. — you "hear the next question coming"). Chest contents revealed before opening; +1 identify-quiz bonus.

**Proc**: **Wooden Horse** — once per floor, you can walk past one monster within sight without triggering combat; the monster must be at full HP and have no current target.

**Why legendary**: Odysseus's actual edge was cunning. The Wooden Horse proc is the named trick.

**Code needed**: chest-preview UI (moderate); chain-cap +1 item flag (moderate); pacify-walk-past action (moderate).

### Ring of Scheherazade (ring_of_scheherazade)

**Lore hook**: She told 1,001 stories to postpone execution. Survived by being more valuable alive than dead.

**Equip mode**: `chain` (5 rungs)
**Why this mode**: 1001 Nights is a frame story — each night is another tale told to delay the king's verdict. Each chain rung is a story. Chain-break IS the story she failed to tell, which is exactly the failure mode Scheherazade survives across.

**Chain bonuses**:
- chain 1: INT +2 (one tale told)
- chain 2: INT +3, +1 max chain on grammar-quizzes (reading scrolls)
- chain 3: INT +3, scrolls remain readable once after failing — chain breaks on first wrong answer, scroll doesn't burn
- chain 4: INT +4, +1 chain on all spellbook reads
- chain 5: INT +4, One Thousand and One (see below)

**T-max named ability**: **One Thousand and One** — after any unsuccessful quiz (any subject), one additional question is offered the next turn at no cost; if answered correctly, the original action succeeds at chain-1 effect.

**Why legendary**: T5 says failure is never final — at the cost of one more turn. Each tale she tells buys another night.

**Code needed**: "save scroll on fail" item flag (moderate); deferred-success retry queue (complex).

### Anklet of Atalanta (anklet_of_atalanta)

**Lore hook**: She could outrun any man alive. Hippomenes won by dropping golden apples; she stopped to pick them up because losing was more interesting than winning.

**Equip mode**: `chain` (5 rungs)
**Why this mode**: The lore is a race in stages — start, mid-stride, apple-stop, apple-stop, apple-stop. Each chain rung is another stride or another apple. Chain-break is the apple she chose to chase. Sequential by definition.

**Chain bonuses**:
- chain 1: DEX +2 (the starting line)
- chain 2: DEX +3, +1 movement speed (every 10th movement is free)
- chain 3: DEX +4 (mid-race stride)
- chain 4: DEX +5, **Three Apples** — once per floor when fleeing from combat (movement away from an enemy in sight), gain 3 free moves
- chain 5: DEX +5, three-apple proc, Atalanta's Choice (see below)

**T-max named ability**: **Atalanta's Choice** — you may pause your own action timer for 10 turns once per floor to wait for the right moment.

**Why legendary**: the apple-flee mechanic plays directly into "winning is boring" lore.

**Code needed**: free-move proc on flee (moderate); player action-pause for spectator turns (complex).

### Ring of Percival (ring_of_percival) — FLAT (reverted from tier-escalator)

**Lore hook**: The knight who failed the Grail question because he was too polite to ask "Who does the Grail serve?"

**Passive bonus**: WIS +4, +1 to theology-quiz bonus (Grail wisdom).

**Proc**: **Right Question + Healed King** — once per floor when faced with an NPC encounter, view the encounter's outcome paths before choosing. Additionally, once per run, you may fully heal one allied creature in sight (pet, charmed monster, NPC); if used on a unique NPC, that NPC offers a one-time service (information, item, training).

**Why legendary**: turns courtesy into a strategic asset.

**Code needed**: NPC-encounter outcome preview (complex — needs to read encounter trees); allied-heal cast (simple).

### Ring of Lancelot (ring_of_lancelot) — FLAT (reverted from tier-escalator)

**Lore hook**: The greatest knight in the world, destroyed the Round Table by being exactly that.

**Passive bonus**: STR +5, hasted, +1 attack chain length, **Joyous Gard** (passive) — when below 50% HP, gain +1 to-hit and +1 damage per attack.

**Proc**: **Best Knight** — at the start of every floor, if you have killed at least one named unique monster on the previous floor, gain 30 turns of `hasted` + `protected`.

**Why legendary**: rewards a player who keeps killing the named monsters. The buff cascade reads as Lancelot's reputation preceding him.

**Code needed**: floor-entry buff conditional on previous-floor unique kill (moderate).

---

## 3. Cursed Accessories

The items where the price is intrinsic. Most curses are CONSTANT (the gold-curse, the ring-of-power dread), not escalating. Only Harmonia earns chain-equip — its lore is the generational deepening of catastrophe. Nibelung's curse is the ring itself, not a ritual.

### Ring of the Nibelung (ring_of_the_nibelung) — FLAT (reverted from tier-escalator)

**Lore hook**: Andvari's gold, cursed to destroy every owner. Hreidmar killed by his son, Fafnir killed his brother for it, Sigurd killed Fafnir, Gudrun murdered Sigurd. Wagner needed four operas.

**Passive bonus**: STR +5, `gold_multiplier 4.0`. Powerful and constant — the ring's gift is real.

**Proc / curse**: **Andvari's Curse** — every time a pet or named ally dies while you wear the ring, you take 5 unavoidable HP damage (the ring drinks death). Cannot be removed in town (cursed); requires a remove-curse scroll or theology rite to take off.

**Why legendary**: the curse isn't a debuff. The curse is "people die around you, and you feel it."

**Code needed**: pet/ally-death-deals-HP-to-bearer hook (moderate); cursed flag with remove conditions (already exists).

### Necklace of Harmonia (necklace_of_harmonia)

**Lore hook**: Hephaestus's wedding gift for Harmonia and Cadmus — and he cursed it because Harmonia's mother was Aphrodite, who'd cuckolded him with Ares. Every owner suffered catastrophe.

**Equip mode**: `escalator` (5 rungs)
**Why this mode**: The lore IS generational deepening — each subsequent owner across centuries suffered worse than the last. Each tier rung is another generation accepting the bargain.

**Tier bonuses**:
- T1: WIS +2, CON -1 (the first generation)
- T2: WIS +3, CON -1 (the second)
- T3: WIS +4, CON -1, +1 max MP (the third — Argia, Eriphyle's daughter)
- T4: WIS +4, CON -2, +2 max MP
- T5: WIS +5, CON -2, Beautiful Ruin (see below)

**T-max named ability**: **Beautiful Ruin** — at the start of each floor, the highest-level monster on the floor is revealed and seeks you; the necklace pulses warmer when it dies. Every 5 named monsters killed while wearing the necklace, your WIS goes up by 1 permanently (max +3 from this passive).

**Why legendary**: the WIS bonus is real and permanent. The CON penalty never goes away. The bargain itself is what's legendary.

**Code needed**: monster-pulled-toward-player flag (moderate); permanent stat-gain counter (simple).

### Andvaranaut (andvaranaut)

**Lore hook**: Andvari's gold-finding ring, cursed alongside the rest of his hoard.

**Mechanic**: keep current static (INT +3, `searching`, gold-finds +50%). **Add `can_be_cursed: true` curse mode**: when cursed, gold piles found on the floor are still +50%, but every fifth gold pickup teleports the player to a random location on the floor. The bonus is real. The teleport is real.

**Why legendary**: the chaos is the curse. Players will weigh greed against geography.

**Code needed**: cursed-side-effect proc on gold pickup (moderate); existing teleport infra.

### Crown of Croesus / Diadem of Croesus (crown_of_croesus)

**Lore hook**: The richest man in the world tested the Delphic Oracle, then misinterpreted it and attacked Persia. The error wasn't the Oracle.

**Mechanic**: keep current (INT +3, `searching`, +50% gold finds). **Add a curse-mode variant** that spawns alongside the normal: when cursed, gold-finds is still +50%, but each time you check your gold total in inventory, one random unidentified item in your inventory becomes "misidentified" (its true identity hidden for 50 turns).

**Why legendary**: greed-blindness made into a mechanic.

**Code needed**: temporary mis-identification overlay (moderate); inventory-view trigger (simple).

### Hand of Glory (hand_of_glory) — NEW

**Lore hook**: A medieval grimoire fixture from Petit Albert — the dried, pickled hand of a hanged murderer holding a candle made of his own fat. Said to render its bearer invisible and paralyse anyone in the household.

**Slot**: amulet (cursed)

**Base stats**: PER -1 (the hand is unsettling to wear); cannot be removed without remove-curse (`can_be_cursed: true`, starts cursed).

**Charges**: 3 uses per run, never recharges. Each use targets one monster in line of sight — that monster is `paralysed` for 10 turns.

**Passive while charges remain**: `silent_walk` (no chase aggro from sound), `dark_vision` (low-light sight extended by 1 tile).

**Passive after charges expended**: the hand goes inert; PER -1 remains, no silent_walk, no further use. The amulet still cannot be removed without remove-curse — and now there's no upside.

**Why legendary**: the rare proper grimoire item — directly from Petit Albert. The cost is real: spend all three charges and you're carrying a dead hand around your neck until you can find a scroll of remove curse.

**Code needed**: targeted paralysis use (simple, reuse Aaron's Rod logic); silent_walk flag (already used); charge-exhausted passive state (moderate).

### Pandora's Box (NEW unique to add — see Section 8)

Treated as artifact below.

---

## 4. Quirky Trinkets

Flavor-first. Power level moderate. All flat-passive (their lore doesn't carry the weight of a ritual).

### Lyre of Orpheus (lyre_of_orpheus)

**Lore hook**: Orpheus charmed Cerberus and Persephone with this. Rocks wept. He failed only because he looked back.

**Passive bonus**: `sleep_resist`.

**Charges**: 3 per floor (refill on descend). Each use: one enemy in line of sight who is not a boss/unique is `charmed` for 10 turns — they fight at your side and gain `pacified` toward you.

**Proc / curse**: **Don't Look Back** — if you attack the charmed monster yourself within the 10 turns, ALL nearby monsters become enraged for 10 turns.

**Why legendary**: the failure mode is canonical to the myth.

**Code needed**: charm-status on monster (moderate, may already exist for some encounters); enrage-on-betrayal proc (moderate).

### Jade Cicada (jade_cicada) — FLAT (overlay removed)

**Lore hook**: Placed on the tongues of Han dynasty dead to guarantee resurrection.

**Passive bonus**: `death_save: true`, `poison_immune`, PER +2, +1 to all saves.

**Proc**: **Reborn** — death_save resets per floor not per run. The first death_save per floor leaves you at 50% HP. If a SECOND death_save fires that floor, the cicada shatters (item consumed) and you revive at full HP.

**Why legendary**: an item that gives its own life for yours.

**Code needed**: per-floor save-reset (simple); item-consumed-on-trigger flag (simple).

### Aesop's Quill (aesops_quill)

**Lore hook**: Aesop, the freed Greek slave who taught morality through animals.

**Passive bonus**: WIS +2.

**Proc**: every 100 turns of wearing, a random fable-relevant flavour message appears in the message log (no mechanical effect — the quill is "writing"). Every 500 turns, gain +1 to a single random quiz-subject bonus for 50 turns (rotating through subjects).

**Why legendary**: a passive that simply makes the world more textured.

**Code needed**: timed flavour message system (already exists for hints); rotating-subject-bonus tick (simple).

### Charmander Stuffie (charmander_stuffie)

**Lore hook**: A child's first beloved toy, full of love that became real magic.

**Passive bonus**: CON +2 on mastery (current).

**Proc**: while in inventory (no slot needed), if the player has 0 pets, the stuffie counts as a half-pet — passive +1 CON, and once per floor at 0% HP it warms in your hand and grants +3 turns of `protected`. Cannot stack with active pet.

**Why legendary**: the soft-mode pet for solo runs.

**Code needed**: inventory-passive item (need new pattern); zero-HP proc (simple, reuse life_save infrastructure).

### Dreamspun Sketchbook (dreamspun_sketchbook)

**Lore hook**: A young lady's sketchbook of dreams.

**Passive bonus**: once per floor, when entering a new floor, the dungeon generates one extra non-hostile flavor encounter (NPC, mystery, or low-stake event). The sketchbook is "drawing the day."

**Why legendary**: changes the texture of the entire dungeon. Makes runs feel less procedural.

**Code needed**: floor-entry extra-encounter spawn (moderate — integrates with flavor_encounters).

### Hamsa Hand / Hand of Fatima (hamsa_hand) — FLAT (reverted from tier-escalator)

**Lore hook**: A shared symbol of three Abrahamic faiths. The painted eye deflects the evil eye.

**Passive bonus**: CON +3, `warning` status, immune to evil-eye / gaze attacks (basilisk, medusa, beholder), reflect_gaze (any gaze attack hits the attacker for half damage), +1 to theology-quiz, +1 to history-quiz, +1 to grammar-quiz timer (one bonus per Abrahamic tradition the hand is shared by).

**Proc**: none — the multi-subject bonus is the proc. The ward is constant, not ritualistic.

**Why legendary**: the multi-subject bonus is unique to this item — Hamsa Hand is the only accessory that hands out three quiz bonuses at once. Constant ward, no escalation needed.

**Code needed**: per-subject quiz bonus flag (moderate); gaze-reflect (already exists as `reflecting`).

### Ariadne's Thread accessory (ariadnes_thread, amulet)

**Lore hook**: She gave the thread to Theseus to navigate the Labyrinth. She was abandoned on Naxos.

**Mechanic**: keep current (`searching`, +WIS 2). **Add passive**: while worn, the auto-map remembers explored tiles in greater detail; pressing the map key shows visited stairs from previous floors as ghost-icons (purely informational, no teleport). After mastery, the thread reveals stairs on each new floor as soon as you enter it.

**Why legendary**: a navigation passive worthy of the myth, not a stat block.

**Code needed**: floor-entry stair reveal (already exists for Palladium artifact); ghost-icon map UI (moderate).

---

## 5. Unique Wands

Three to author (plus Wand of Wonder as a 4th — see Section 8). Wands use escalator-chain (subject = science) natively. Uniques can push chain-length or per-tier different effects.

### Aaron's Rod (aarons_rod)

**Lore hook**: Aaron's almond-wood rod that became a serpent and swallowed Pharaoh's serpents, then budded almonds overnight.

**Mechanic**: chain mode (8 entries, longer than standard 5). Per-chain effect tiers:
- chain 1-2: paralyze monster for 5 turns (current)
- chain 3-4: paralyze monster for 10 turns
- chain 5-6: paralyze + summon a serpent ally for 30 turns (counts as pet)
- chain 7: paralyze + summon 2 serpent allies
- chain 8: **The Almonds Bud** — paralyze, summon 2 serpents, AND refund all charges spent; the rod fully recharges itself once per run on chain 8

**Why legendary**: chain 8 is the budding of the rod — the actual scene from Numbers 17.

**Code needed**: per-chain-step branching effect (moderate); rod self-recharge on chain-max (simple); summon-as-pet (already exists for some monsters).

### Circe's Wand (circes_wand)

**Lore hook**: Circe turned Odysseus's crew into pigs on Aeaea. Their minds knew the whole time.

**Mechanic**: chain mode (6 entries). Per-chain skyrocket:
- chain 1: polymorph target into a pig for 5 turns (current — half STR, can attack but weakly)
- chain 2: polymorph into pig for 15 turns
- chain 3: polymorph + the pig is `pacified` toward you for the duration
- chain 4: polymorph + pacified + the pig drops a piece of bacon when killed
- chain 5: **Aeaean Sty** — polymorph target AND all monsters within 3 tiles of the target into pigs for 20 turns
- chain 6: Aeaean Sty + once per run, you may instead make the polymorph permanent (the monster becomes a permanent pig pet — your "swineherd")

**Why legendary**: chain 6 builds a literal sty of charmed pigs over the course of a long run.

**Code needed**: AoE polymorph (moderate); permanent-pet conversion (moderate); bacon item drop (simple, food_system).

### Indra's Vajra (indras_vajra)

**Lore hook**: Made by Tvastr from the bones of the sage Dadhichi, who gave his body for it. Indra struck Vritra the world-drought serpent and freed the seven rivers.

**Mechanic**: chain mode (5 entries, sharp skyrocket per design brief's `[0.1, 0.1, 0.2, 0.5, 5.0]` precedent). Per-chain damage scaling on lightning_bolt (6d6 base):
- chain 1: 1d6 lightning (terrible — Indra is testing you)
- chain 2: 2d6 lightning
- chain 3: 4d6 lightning
- chain 4: 8d6 lightning chain-arc (jumps to 2 nearby enemies for half)
- chain 5: **Strike Against Vritra** — 12d6 lightning to the primary target, 6d6 chain-arc to ALL enemies in sight; if the primary target is a unique serpent/dragon-tagged monster, the damage is doubled

**Why legendary**: 12d6 + chain to all visible enemies is genuinely world-altering. The early chains are punishingly weak — Indra demands competence.

**Code needed**: chain-arc lightning (moderate); per-monster-tag damage doubler (moderate, already exists for some weapons).

---

## 6. Unique Scrolls

Two to author. Scrolls use escalator-chain or escalator-threshold (subject = grammar).

### Scroll of Annihilation (scroll_of_annihilation)

**Lore hook**: First spoken on the day the great library of Carthage burned.

**Mechanic**: keep current as escalator-threshold (read_threshold 3, quiz_tier 5). **Stretch the chain to 5 tiers with per-tier different effects**:
- threshold 1: damage = 4d4 to nearest visible enemy (failed annihilation — the scroll is angry)
- threshold 2: damage = 8d4 to nearest visible enemy
- threshold 3: original `annihilate` (every visible creature dissolves — 12d4)
- threshold 4: annihilate + the scroll does not burn on this use (effective +1 use)
- threshold 5: **Library of Carthage** — annihilate all visible creatures AND identify every unidentified item in your inventory; the scroll does not burn

**Why legendary**: threshold 5 is the entire library of Carthage burning around you, briefly, to your benefit.

**Code needed**: scroll-non-consumed-on-threshold flag (simple); bulk-identify proc (already exists for Book of Thoth).

### Book of Thoth (book_of_thoth)

**Lore hook**: Pharaoh Neferkaptah stole it from its serpent guardian in the Nile. His family drowned for his audacity, and the book was buried with him. From the Setna cycle.

**Mechanic**: keep current `identify_all` at read_threshold 4. **Extend to threshold 5**:
- threshold 1-3: nothing happens, scroll burns
- threshold 4: identify_all (current) — every unidentified item in your inventory becomes identified
- threshold 5: **Speech of the Dead** — identify_all + reveal all unique items currently on the entire dungeon (mini-map markers placed on stair-up tiles indicating which floor each unique is on)

**Why legendary**: threshold 5 turns "find the legendary items" from a roll into a treasure hunt with directions.

**Code needed**: cross-floor item-location markers in map UI (complex).

---

## 7. Unique Spellbooks

Four to author. Spellbooks use escalator-chain (subject = grammar).

### The Necronomicon (necronomicon)

**Lore hook**: Naturom Demonto. Bound in human flesh, inked in blood. Sumerian funeral incantations and demon resurrection passages. Don't read aloud. Seriously.

**Mechanic**: chain mode (6 entries — long for early-game item at min_level 18). Per-chain effect:
- chain 1: Army of Darkness summons 1 skeleton ally for 30 turns (current at chain 1 effectively)
- chain 2: 2 skeletons
- chain 3: 3 skeletons + zombie (heavier)
- chain 4: 4 undead + you take 2 HP damage (the book is reading you back)
- chain 5: 5 undead + you take 4 HP + gain `terrified` for 10 turns (the player faces what they raised)
- chain 6: **Klaatu Verata Nictu (mumble)** — summon 8 undead BUT the army has a 25% chance to be hostile to YOU (Ash's classic mispronunciation; the book wants you to read it perfectly or pay the comedy price). Players should remember the line.

**Why legendary**: chain 6 is a roll of the dice with the book's sense of humor.

**Code needed**: summon-N-allies chain effect (moderate); hostile-summon roll (simple); HP/status cost on cast (simple).

### Sefer Yetzirah (sefer_yetzirah)

**Lore hook**: Attributed to Abraham. The oldest extant Jewish mystical text. The Maharal of Prague used a copy to shape a golem of clay; the golem walked Prague's Jewish quarter until the Maharal removed the Name from its forehead.

**Mechanic**: chain mode (5 entries). Per-chain "letter of the Name" added to the golem:
- chain 1: summon Guardian (clay golem) — current `summon_guardian_spell`. Lasts 50 turns, AC 4, weak attacks. (The golem is incomplete — one letter on its forehead.)
- chain 2: golem is +2 STR, lasts 75 turns
- chain 3: golem is +4 STR, +2 AC, lasts 100 turns
- chain 4: golem is heavy — pierce/slash damage reduction 0.3
- chain 5: **The Name Complete** — golem is permanent until killed (no expiry timer), STR +5, AC +4, immune to fire and shock; when the golem is reduced to 0 HP, the book offers you a quiz to "erase the Name and lay it to rest" (chain quiz to peacefully end the golem rather than have it die ugly)

**Why legendary**: chain 5 builds the Maharal's golem. The "lay it to rest" beat is the actual Maharal story.

**Code needed**: permanent-until-killed summon flag (moderate); on-summon-death quiz hook (complex).

### Picatrix (picatrix)

**Lore hook**: Ghayat al-Hakim, the Aim of the Sage. Tenth-century al-Andalus. Talismanic magic and planetary hours. Dee owned a copy. Ficino pretended he hadn't.

**Mechanic**: chain mode (7 entries — Picatrix is dense). Per-chain "planetary hour" determines damage type:
- chain 1: Sun — 3d6 fire to one target
- chain 2: Moon — 3d6 cold to one target
- chain 3: Mars — 4d6 fire to all visible enemies in cone (current fireball, base case)
- chain 4: Mercury — 4d6 force; pushes targets 2 tiles
- chain 5: Jupiter — 5d6 lightning to all enemies in 5-tile radius
- chain 6: Saturn — 5d6 cold + 30% chance to slow each target for 10 turns
- chain 7: **The Empyrean Hour** — all seven planetary effects fire in sequence at one target; total damage approximately 25d6 mixed elemental

**Why legendary**: chain 7 is the planetary cascade Picatrix actually describes — the player has to study which damage type at which chain.

**Code needed**: chain-step damage-type lookup (moderate); per-element status proc (simple).

### Lemegeton (lemegeton)

**Lore hook**: Five books bound as one. The Ars Goetia lists seventy-two demons King Solomon bound to his service. Bael teaches invisibility, Asmodeus answers questions truthfully, Vassago finds lost things. Crowley translated it in 1904.

**Mechanic**: chain mode (5 entries) — per-chain summon a DIFFERENT demon:
- chain 1: summon imp (Bael, lesser form) — 1 ally for 30 turns
- chain 2: summon shadow-fiend (Vassago) — also reveals 3 nearest hidden items on floor
- chain 3: summon hellhound pack (Marbas) — 2 fire-aspect hounds
- chain 4: summon Asmodeus's herald — one heavy demon ally + once per floor you may ask it a true/false question about the dungeon state ("is there a unique on this floor?")
- chain 5: **Ars Goetia** — summon the original army-of-darkness equivalent (3-5 demons of varying form) AND gain `truesight` for 50 turns

**Why legendary**: chain 4's "ask a question" is unique among spellbooks. Lemegeton becomes a research tool.

**Code needed**: per-chain different summon (moderate); demon-asks-question UI hook (complex).

---

## 8. Quest Artifacts

Most of these are plot-flag carriers today — they exist to be picked up and trigger a downstream event. The brief asks us to consider what each SHOULD do. Below I classify each artifact: **quest-only** (leave the mechanic alone), **inventory-active** (passive while held), or **use-active** (charged/consumed). Many keep their current plot role and gain a small inventory-active passive that doesn't interfere with the quest beat.

### Philosopher's Stone (philosophers_stone)

**Classification**: quest-only (death_kill_ritual_component, score_bonus_50000). The Stone is the endgame anchor.

**Mechanic addition**: while held, all unidentified items in inventory auto-identify on floor descent. This was always thematically present (Hermes Trismegistus etc) but unimplemented. The auto-identify makes carrying the Stone feel like the Great Work is actively happening.

**Why legendary**: alchemy at the cosmic level should make small alchemy trivial.

**Code needed**: per-floor descent identify hook (simple); auto-identify already in special_properties.

### Bronze Bull Idol (bronze_bull)

**Classification**: quest-only (Asterion quest layer 1 — pour on Ariadne fountain to defang phasing). Leave mechanics alone.

**Add narrative**: while held, the player smells faintly of sea-foam (flavor message every 100 turns). The bull is "alive" in your pack.

**Why legendary**: pure narrative. Reinforces that the quest item is participating in the journey.

### Ariadne's Thread (artifact, ariadnes_thread)

**Classification**: quest-only currently. Reveals_hidden_paths flag exists but is consumed at the fountain.

**Mechanic addition (inventory-active)**: while held, see hidden corridors within sight radius (existing `reveal_hidden_paths` interpreted as constant while held, not just at fountain). Consumed at fountain ends this benefit. Player choice: keep for navigation or spend on quest.

**Why legendary**: the player faces an actual choice about timing of the quest beat.

**Code needed**: passive reveal-hidden-tile-within-sight (already exists for some items, just gate on possession).

### Eye of the Graeae (eye_of_graeae)

**Classification**: quest-only (Medusa quest layer 1 — drop on Athena altar produces Aegis).

**Mechanic addition (inventory-active)**: while held, the player can see through walls at 2-tile range (rendered as a faded eye-icon overlay). The Grey Sisters are looking for you. When dropped on the altar, the wall-vision ends.

**Why legendary**: the eye that lets Perseus extort the Graeae now lets the player extort the dungeon.

**Code needed**: limited wall-vision overlay (moderate).

### Cat's Footstep / Woman's Beard / Mountain Root / Fish Breath / Bird Spittle / Bear Sinew (6 Gleipnir components)

**Classification**: quest-only (forge_with_5_others_at_dwarven_forge_to_make_gleipnir). Leave mechanics alone.

**Mechanic addition (per item, inventory-active flavor only)**: while held, each adds one small flavour tic:
- Cat's Footstep: player movement is silent (`silent_walk`, no sound aggro)
- Woman's Beard: NPCs in encounters are slightly more confused (one extra dialogue option flavor-text)
- Mountain Root: +1 to STR-based encumbrance checks
- Fish Breath: hold breath underwater longer (no current mechanic, but reserve for water-floor content)
- Bird Spittle: messages from the world log are slightly more cryptic (flavor only)
- Bear Sinew: warns you of off-screen monsters within 4 tiles (subtle ping in sidebar)

**Why legendary**: each impossible thing IS impossible-in-microcosm.

**Code needed**: minor flag-based passives (each simple individually).

### Gleipnir (assembled, gleipnir)

**Classification**: use-active. Currently `bind_fenrir_with_stat_tax_during_fight` (existing mechanic).

**Mechanic addition**: while held outside Fenrir fight, the player gains +1 to escalator chain caps on any binding-themed action (lockpicking, identify-quizzes). The thinnest ribbon in the world strengthens every binding you attempt.

**Why legendary**: even outside its single use, it does its lore.

**Code needed**: chain-cap +1 flag on specific subjects while item held (moderate).

### Leather Scrap (leather_scrap)

**Classification**: quest-only (10 assembled = Vidar's Sandal). Leave alone.

### Seal of Wrath / Pestilence / Famine / War / Death / Earthquake / Silence (7 seals)

**Classification**: quest-only currently (shatter_on_pickup_with_chronicle). The seals trigger plot beats.

**Mechanic addition (inventory-active overlay) — only if held between pickup and the Pit-opening trigger**: each seal grants a passive aligned with its name while held in inventory:
- Wrath: +5% damage dealt, +5% damage taken (cannot be reduced)
- Pestilence: poison resistance +1, but the player smells of plague (intimidate-flavor)
- Famine: hunger ticks 25% slower, but max HP -10%
- War: +1 chain on combat math attacks, but no first-strike
- Death: undead one tile away pacify, but living humans avoid you
- Earthquake: doors and walls within 1 tile have 5% chance per turn to crack (slow demolition), but you bleed dust (flavor)
- Silence: silent_walk + spell-cast cannot fail to mis-pronounce (no comedy backfire), but you cannot read aloud (scrolls cost +1 chain)

The seals are temporary — they shatter at the Pit. The passives end with them.

**Why legendary**: holding a seal CHANGES YOU until you give it up. The Apocalypse rides with you for as long as you carry it.

**Code needed**: per-seal status flags (each simple); seal-shatter-removes-status hook (simple).

### Scales of Michael (scales_of_michael)

**Classification**: quest-only (v_power_summon_angel_per_locust during Abaddon fight).

**Mechanic addition (inventory-active outside Abaddon)**: while held and your karma is in 1-9 range (the spawn condition), once per floor when you kill a monster, the scales weigh its soul — if the kill was "righteous" (creature was hostile, attacked you first this floor), karma +1; else neutral. Caps at +10 (your existing karma clamp). Players who carry the Scales become accountable to them.

**Why legendary**: Michael continues to weigh souls even outside the final battle.

**Code needed**: on-kill karma-judgment hook (moderate — reuse existing karma adjustment system).

### Cursed Lodestone (cursed_lodestone)

**Classification**: use-active negative — currently `heavy_20lb_cannot_drop_until_remove_curse`. Leave as is. The weight IS the point.

**Mechanic addition (narrative only)**: every 50 turns of carrying, the player hears the knight's wife murmur (flavor message). Make the burden feel inhabited.

### Sealed Dispatch (sealed_dispatch)

**Classification**: use-active — `deliver_to_surface_for_karma_or_score`. Leave as is.

**Mechanic addition**: while carried, NPC encounters have one extra dialogue option ("Have you heard about the siege?") that returns useful information (hint, rumor, or small reward) once per floor.

**Why legendary**: the dispatch is alive in the player's pack. People notice you carrying it.

**Code needed**: encounter dialogue conditional on inventory item (moderate).

### Palladium (palladium, artifact)

**Classification**: inventory-active (current — `stair_reveal_while_carried`). Leave as is. This is the gold standard for "passive while held."

### Tablet of Destinies (tablet_of_destinies)

**Classification**: use-active — `one_quiz_reroll_per_floor_when_wrong`. Excellent mechanic; preserve.

**Mechanic addition (inventory-active overlay)**: while held, the next floor's boss/unique-monster type is revealed in the message log as you descend ("the air thickens with dragon-musk" / "a faint scent of brimstone"). Tablet readers know what's coming.

**Why legendary**: the Tablet predicts. That's the whole point.

**Code needed**: floor-descent flavor message based on next-floor spawn list (moderate).

### Bracers of Cu Chulainn / Leggings of Enkidu / Vambraces of Achilles / Vidar's Sandal (4 armor-tagged artifacts)

**Classification**: these are actually armor pieces filed under artifact. They have full armor mechanics already (warp-spasm, wild-man-tread, hephaestus-forged, instant-kill-on-fenrir).

**Recommendation**: leave mechanically as-is — these were sized in the armor pass. Do NOT add tier-escalator to Vidar's Sandal (its quest role is sacrosanct — the instant-kill IS the legendary thing).

**Possible polish only**: Vambraces of Achilles could get a small inventory-active "Scenes of Peace" flavor — every 100 turns of equip, a brief flavor message about a farmer or dancer engraved on the bronze. Pure narrative.

### Pandora's Box (pandoras_box) — NEW

**Lore hook**: Pandora opened the jar (mistranslated as "box") given to her by the gods. Plagues, sorrows, and ills flew out. Only Hope remained inside.

**JSON-ready fields**:
```json
{
  "id": "pandoras_box",
  "name": "Pandora's Box",
  "category": "artifact",
  "slot": "carried",
  "weight": 5,
  "min_level": 30,
  "rarity": "unique",
  "tags": ["greek", "chaos", "one_shot"],
  "use_charged": true,
  "charges": 1,
  "consumed_on_use": true,
  "special_properties": {
    "rolls_on_chaos_table": "pandora",
    "score_bonus_on_use": 5000
  }
}
```

**Mechanic**: use-active, single-shot, consumed on use. On use, roll 1d20 on the Pandora chaos table below. No quiz gate — opening the box is the act, and you cannot un-open it.

**Chaos table** (50% buffs, 50% debuffs; most effects MINOR per user guidance):

| Roll | Effect |
|---|---|
| 1 | **Plague released** — gain `poisoned` for 30 turns + all enemies within sight gain `poisoned` for 30 turns. |
| 2 | **Toil released** — all enemies in sight gain +1 attack chain capacity for 50 turns. Yours: -1 for the same duration. |
| 3 | **Strife released** — random monster in sight becomes hostile to ALL other monsters (including you) for 50 turns. |
| 4 | **Famine released** — hunger meter drops 25% (you become Hungry if not already). Cosmetic if already Starving. |
| 5 | **Madness released** — one random stat -1 for 100 turns. |
| 6 | **Lies released** — one random unidentified item in your inventory gains a false flavor description for 100 turns. |
| 7 | **Old Age released** — DEX -2 for 50 turns. |
| 8 | **Despair released** — lose 5 SP. Cannot SP-cast for 20 turns. |
| 9 | **Tempest released** — random lightning bolt strikes a random tile in sight (4d6 to whatever stands there — could be you). |
| 10 | **Polymorph one** — one random hostile monster in sight is polymorphed into a small harmless creature (mouse, rat, sparrow) for 30 turns. (User-clarified example.) |
| 11 | **Foresight kept** — gain `clairvoyant` for 50 turns. |
| 12 | **Toil-mastery** — gain +1 chain capacity on all quizzes for 50 turns. |
| 13 | **Memory of Eden** — gain +1 to a random stat for 50 turns. (User-clarified: minor stat change.) |
| 14 | **Friendship** — one nearest hostile monster becomes `charmed` for 30 turns. (User-clarified example.) |
| 15 | **Curiosity rewarded** — identify all unidentified items in inventory. |
| 16 | **Beauty unleashed** — gain `pacified` aura: monsters within 2 tiles cannot attack you for 5 turns. |
| 17 | **Health restored** — full HP and SP. |
| 18 | **Foreknowledge** — full mini-map for current floor revealed. |
| 19 | **Strength of will** — gain +3 turns of `protected` and 50 turns of `hasted`. |
| 20 | **Hope** — permanent +1 to a random stat. (The single big-payoff roll; weighted at 5% of rolls.) |

**Why legendary**: a one-shot consumable that the player will agonize over. Most rolls are minor temp shifts. Roll 20 is the legend payoff.

**Code needed**: chaos table lookup (moderate); temp-stat-shift status (already exists for many statuses); polymorph-monster proc (reuse Circe's Wand chain 1).

### Aladdin's Lamp (aladdins_lamp) — NEW

**Lore hook**: From the One Thousand and One Nights. The djinn bound to the lamp grants a wish to whoever rubs the lamp and proves themselves worthy. One wish — not three. Make it count.

**JSON-ready fields**:
```json
{
  "id": "aladdins_lamp",
  "name": "Aladdin's Lamp",
  "category": "artifact",
  "slot": "carried",
  "weight": 8,
  "min_level": 35,
  "rarity": "unique",
  "tags": ["arabian", "wish", "one_shot"],
  "use_charged": true,
  "charges": 1,
  "consumed_on_use": true,
  "quiz_gate": {
    "subject": "theology",
    "mode": "escalator_threshold",
    "tier": 5,
    "required_correct": 4
  },
  "special_properties": {
    "djinn_wish_menu": true,
    "fallback_on_failure": "half_potency_random_wish"
  }
}
```

**Mechanic**: use-active, single-use, consumed on use. On use, the lamp prompts a tier-5 theology escalator quiz (5 tier-5 questions, must answer 4 of 5 correctly). On success, the player chooses ONE wish from a menu of three categories. On failure, the djinn answers a different prayer ("I cannot grant that, but...") and a RANDOM wish fires at HALF potency.

**Wish menu** (player chooses one on success):

| Wish | Effect |
|---|---|
| **Wish for an item** | Player names an item category (weapon / armor / shield / accessory / artifact / wand / scroll / spellbook / potion). The djinn generates a random item of that category appropriate to the current floor's loot tier (one tier above normal). For artifact, the djinn produces a random non-quest artifact not currently in the player's inventory. |
| **Wish for a power** | Choose ONE: permanent +1 to any single stat (STR/CON/DEX/INT/WIS/PER, no cap override), OR a permanent status immunity (player picks from: poison, paralysis, fear, sleep, blindness, confusion). |
| **Wish for a named entity** | Choose ONE: summon a powerful ally for 50 turns (paladin, archmage, or holy warrior — equivalent to a tier-5 charmed monster), OR reveal the location, name, and weakness of the next boss/unique-monster on a future floor. |

**Failure fallback** (random pick, half potency):
- Random item from the player's chosen category but ONE tier BELOW current floor's loot tier
- Permanent +1 to a RANDOM stat (not player's choice)
- Random status immunity (50% chance) OR 100 turns of the same immunity (50% chance)
- Ally summon for 25 turns instead of 50
- Boss-location reveal but no weakness, no name

**Why legendary**: the highest-quiz-tier item in the game. Theology fluency required. The wish menu makes "I can have anything" a real strategic choice. One wish, bounded but meaningful.

**Code needed**: tier-5 escalator-threshold quiz UI (already exists for current scrolls); wish-menu selection UI (moderate); appropriate-tier item generator (already exists for loot tables); permanent stat +1 (simple); status-immunity flag (simple); ally summon (already exists); boss-reveal UI (moderate).

### Wand of Wonder (wand_of_wonder) — NEW

**Lore hook**: Old tabletop RPG fixture, going back to AD&D. A wand whose effect is rolled fresh each cast. Wonder is mostly positive but bounded — the wand wants to please.

**JSON-ready fields**:
```json
{
  "id": "wand_of_wonder",
  "name": "Wand of Wonder",
  "category": "wand",
  "slot": "hand",
  "weight": 3,
  "min_level": 22,
  "rarity": "unique",
  "tags": ["chaos", "wonder", "tabletop"],
  "quiz_subject": "science",
  "quiz_mode": "chain",
  "chain_length": 5,
  "charges": 10,
  "max_charges": 10,
  "special_properties": {
    "rolls_on_wonder_table_per_chain": true,
    "wonder_bias_positive": true
  }
}
```

**Mechanic**: chain mode (5 entries, science subject). Each chain rung rolls FRESH on an escalating Wonder table. The table biases POSITIVE (per user guidance — Wonder is bounded for balance but mostly good).

**Wonder tables** (each chain step rolls fresh on its tier's table; ~70% positive, ~20% neutral/silly, ~10% minor negative):

**Chain 1 — 1d6**:
| Roll | Effect |
|---|---|
| 1 | Heal target 2d6 (if hostile, this is a downside — but the wand wanted to help) |
| 2 | Heal SELF 1d6 |
| 3 | Identify ONE random unidentified item in inventory |
| 4 | Polymorph target to mouse for 10 turns |
| 5 | Teleport target to a random tile within sight |
| 6 | Nothing happens (silly — the wand giggles) |

**Chain 2 — 1d8** (chain 1 entries + 2 new):
| Roll | Effect |
|---|---|
| 1-6 | as chain 1 |
| 7 | Charm target for 10 turns |
| 8 | Heal SELF 2d6 |

**Chain 3 — 1d10** (chain 2 entries + 2 new):
| Roll | Effect |
|---|---|
| 1-8 | as chain 2 |
| 9 | AoE 3d6 damage in 3-tile radius (mixed elemental, friendly fire — chaos is real here) |
| 10 | Find item — a random common item appears on the tile next to the target |

**Chain 4 — 1d12** (chain 3 entries + 2 new):
| Roll | Effect |
|---|---|
| 1-10 | as chain 3 |
| 11 | Lightning 6d6 to target |
| 12 | Summon friendly imp for 50 turns (counts as pet temporarily) |

**Chain 5 — 1d20** (chain 4 entries + 8 new wonder effects):
| Roll | Effect |
|---|---|
| 1-12 | as chain 4 |
| 13 | **Mass-charm** — all hostile monsters in sight `charmed` for 10 turns |
| 14 | **Heal to full** — caster restored to full HP and SP |
| 15 | **Identify all** — every unidentified item in inventory identified |
| 16 | **Levitation** — caster gains 30 turns of `levitating` (ignore traps and water tiles) |
| 17 | **Future preview** — reveal next floor's mini-map (one-time vision) |
| 18 | **Stat-color** — one of the caster's stats glows a random color for 50 turns (purely cosmetic; sidebar shows stat in different hue). Pure silliness. |
| 19 | **Open all chests** — every unopened chest on the current floor opens at once (lockpicks unnecessary; trapped chests still trap-trigger) |
| 20 | **Wonder unbounded** — caster loses 5 HP (the wand is overextending itself) BUT gains a random rolling buff: pick one of `hasted`, `protected`, `clairvoyant`, `regenerating`, `truesight` for 50 turns. The 5 HP loss is the only consistent negative on the chain 5 table. |

**Mechanic note**: each chain step rolls a FRESH table. Chain 5 can roll a small effect (1-4) or a giant one (13-20). The wand is swingy but bounded — the worst chain 5 outcome is "lose 5 HP and get a 50-turn buff" or "miscast at chain 1." There are no game-breaking outcomes.

**Why legendary**: the chaos engine done RIGHT — mostly positive, occasionally silly, never catastrophic. The player learns to lean into chain-extension because higher chains have better wonder odds.

**Code needed**: chain-step roll-on-table mechanic (moderate); per-effect dispatch (each effect is a known mechanic or trivial — simple-to-moderate per effect); stat-color cosmetic (simple, sidebar render hook).

---

## 9. Plain Elevated Accessories

The smaller pieces. Good lore, clean treatment. All flat-passive — they don't have the lore weight to justify chain-equip. Static bonuses elevated slightly.

### Dragonslayer's Ring (dragonslayer_ring)

**Lore hook**: Forged from a wyrm's hoard-gold, quenched in dragon's blood.

**Mechanic**: keep current (STR +2, fire_resist). **Add**: +1 damage chain bonus vs dragon-tagged monsters.

**Why legendary**: the Western Reach hunters had a specific edge. It should still cut.

### Shadow Walker's Ring (shadow_walker_ring)

**Lore hook**: Thieves' guild grandmaster's signet. Stripped from a dead king alongside the venom-glands that flavor the band.

**Mechanic**: keep current (poison_resist). **Add**: +1 to all DEX-based saves + 5% chance per backstab-position attack to apply 10 turns of bleed.

### Philosopher's Ring (philosophers_ring) / Philosopher's Ring of Mastery (philosophers_ring_legendary)

**Lore hook**: The original dungeon philosopher's ring. Mastery version found at the Academy.

**Mechanic** (base): keep current (WIS +2, INT +1). **Add**: +1 to philosophy-quiz timer.

**Mechanic** (Mastery): keep current (WIS +3, truesight). **Add**: +2 to philosophy-quiz timer and +1 chain max on identify-quizzes.

**Why legendary**: identification-themed accessory rewards the philosopher's mode of play.

### Ring of Gyges (ring_of_gyges)

**Lore hook**: Plato's thought experiment. Would a just man behave differently if he could act unseen?

**Mechanic**: keep current (invisible). **Add**: while invisible from this ring, gold from chests counts double — but also if the player attacks an NPC while invisible from the ring, karma -2 (the moral question is no longer hypothetical).

**Why legendary**: the ring asks the question Plato asked.

**Code needed**: invisibility-source tracking on attack hook (moderate).

### Andvaranaut (andvaranaut)

Static. Already strong. See Section 3 for cursed-mode addition.

### Draupnir (draupnir)

**Lore hook**: Drips eight new rings every ninth night.

**Mechanic**: keep current (STR +3, gold_multiplier 2.0). **Add**: every 9 floors descended while wearing Draupnir, a random ring item appears in your inventory (a "child ring" of Draupnir — common-tier random ring with one minor effect).

**Why legendary**: literal lore-mechanic. Eight rings every ninth night.

**Code needed**: floor-counter spawn-ring proc (moderate); random common-ring picker (simple).

### Ring of Eluned (ring_of_eluned)

**Lore hook**: Welsh Arthurian. Saved Owain at the portcullis. Luned retrieved it afterward.

**Mechanic**: keep current (invisible, DEX +2). **Add**: when you go below 25% HP, gain `invisible` for 5 turns automatically (the ring intervenes once per floor).

**Why legendary**: the portcullis save in mechanical form.

### Menat of Hathor (menat_of_hathor)

**Lore hook**: Hathor's sacred rattle-necklace, sound of "everything being well."

**Mechanic**: keep current (CON +4). **Add**: +2 turns of `regenerating` on every successful chain of 5+ on any quiz (Hathor approves of perseverance).

**Why legendary**: a chain-success reward unique to this item.

### Idunn's Apple (idunn_apple_charm)

**Lore hook**: The golden apples that kept the Aesir young. Each bite is another year stripped away.

**Equip mode**: `chain` (5 rungs)
**Why this mode**: An apple is eaten in bites, not all at once. Each chain rung is a bite of Idunn's apple — youth restored one mouthful at a time. The lore is literal sequence.

**Chain bonuses**:
- chain 1: CON +2 (first bite — slight rejuvenation)
- chain 2: CON +3, hunger ticks 33% slower (the apple sustains)
- chain 3: CON +4, hunger ticks 50% slower
- chain 4: CON +5, hunger ticks 50% slower, +1 to all death-saves (youth shrugs off death)
- chain 5: CON +5, hunger ticks 66% slower, **Aesir-Young** (see below)

**T-max named ability**: **Aesir-Young** — once per floor, if you would suffer any age-related debuff (decay, slow, weariness from over-encumbrance), it is negated. Additionally, the charm gives +5 turns of `protected` immediately after reaching chain 5 on re-equip (the final bite is sweet).

**Why legendary**: a charm whose lore is consumption. Each bite earns you another year.

**Code needed**: chain_escalator on charm slot (shared infra); hunger-tick rate modifier (simple); negate-age-debuffs hook (simple — flag-based).

### Caduceus of Hermes (caduceus_charm)

**Lore hook**: Hermes traded the lyre to Apollo for it. Confused with Asclepius's staff in medical iconography.

**Mechanic**: keep current (regenerating, WIS +2). **Add**: +1 to grammar-quiz (Hermes is patron of messengers and language).

### Torque of Lugh (torque_of_lugh)

**Lore hook**: Lugh of the Long Arm, god of every skill simultaneously.

**Mechanic**: keep current (STR +4). **Add**: +1 to a SINGLE randomly chosen quiz-subject bonus each floor descent (rotates — Lugh is good at one new thing each day).

### Sea-Collar of Njord (collar_of_njord)

**Lore hook**: Njord, god of winds and sea, married Skadi who chose him by his feet.

**Mechanic**: keep current (CON +3, warning). **Add**: +2 to cold and water resistances (no current shock_resist conflict).

### Seal of Agrippa (seal_of_agrippa)

**Lore hook**: Heinrich Cornelius Agrippa systematised all of Renaissance magic. Died in debt.

**Mechanic**: keep current (INT +3, clairvoyant). **Add**: +1 to science-quiz timer (Agrippa's three worlds: elemental, celestial, intellectual).

### Tetractys Amulet / Amulet of Pythagoras (amulet_of_pythagoras)

**Lore hook**: Pythagoras's sacred ten-point triangle. Hippasus drowned for proving √2 irrational.

**Mechanic**: keep current (INT +3, searching). **Add**: +1 to math-quiz chain cap (Pythagoras is the math god).

### Ring of Hypatia (ring_of_hypatia)

**Lore hook**: Hypatia of Alexandria. Killed by a mob in 415 CE.

**Mechanic**: keep current (INT +3, truesight). **Add**: when surrounded by 3+ enemies, gain `protected` for 3 turns once per floor (the mob takes her — the ring is sorry, and tries).

**Why legendary**: the mechanic apologizes for history.

### Sphinx Crown (sphinx_crown) — plot-locked

Keep current (WIS +2). **Polish**: +5 seconds to quiz timer on philosophy and grammar (riddles are language puzzles).

### Sailor's Amulet (sailors_amulet) — plot-locked

Keep current (PER +1, cold_resist). **Polish**: warning status (sailors see weather coming).

### Anubis's Scales (anubis_scales) — plot-locked

Keep current (CON +1). **Polish**: undead's first attack each floor against the bearer misses (Anubis weighs the strike).

### Ring of Iron Grip (ring_of_iron_grip) — plot-locked

Keep current (STR +2). **Polish**: cannot be disarmed; weapons cannot be stolen from inventory.

### Obsidian Talisman (obsidian_talisman) — plot-locked

Keep current (dark_vision). **Polish**: fear-resist (Xibalba taught it).

### Saint's Reliquary (saints_reliquary) — plot-locked

Keep current (WIS+1, CON+1). **Polish**: undead damage reduced by 10% to the bearer.

### Officer's Signet (officers_signet) — plot-locked

Keep current (STR+1, DEX+1). **Polish**: +1 to all combat-math chain caps when below 25% HP (you remember your training).

### Prophet's Amulet (prophets_amulet) — plot-locked

Keep current (WIS+2, PER+1). **Polish**: once per floor, when you would walk into an unseen trap, the amulet warns you (the trap is revealed, you do not trigger it).

### Epona's Charm (eponas_charm)

Keep current (searching, PER+1). **Polish**: stairs-up tile is always visible on map once any tile adjacent to it has been seen (Epona ensures you find the way home).

### Anansi's Thread (anansis_thread)

Keep current (INT+2). **Polish**: +1 to any single subject after answering 10 questions in that subject correctly across the run (Anansi remembers every story).

### Rope of Izanagi (rope_of_izanagi)

Keep current (CON+2, searching). **Polish**: undead and demons within 3 tiles take 1 damage per turn (the rope divides life from death — they cannot stand near the threshold).

### Girdle of Hippolyta (girdle_of_hippolyta)

Keep current (STR+3). **Polish**: when fighting Amazon/female-tagged monsters, +1 chain (mutual recognition).

### Silverlight Pendant (silverlight_pendant) — plot-locked

Keep current (WIS+2, PER+1). **Polish**: child's-name flavor — once per run, a child NPC in a flavor encounter offers an unexpected gift. (Elara is remembered.)

### Rand's Heart (rands_heart) — secret/end-game (min_level 999)

Keep current (warning). **No polish.** This is a personal-promise item; mechanical embellishment would diminish it.

### Megingjörð (megingjord) — FLAT (reverted from tier-escalator)

**Lore hook**: Thor's belt of strength. Doubled his power.

**Passive bonus**: STR +5 (doubled — Thor's lore is the belt doubles you, not phases you up).

**Proc**: **Thor's Catch** — once per floor, your next melee attack has +2 chain capacity and ignores armor resistance (Thor would have hauled Jormungandr aboard).

**Why legendary**: the belt's lore is INSTANT doubling, not staged ascent. Flat is correct here.

**Code needed**: chain-capacity-buff on next-attack proc (moderate); armor-ignore flag (already exists for some weapons).

### Kavacha and Kundala (kavacha_kundala)

**Lore hook**: Karna born wearing them. Gave them as alms because a Brahmin's request cannot be refused.

**Equip mode**: `escalator` (5 rungs)
**Why this mode**: Karna's life with the kavacha was a slow burden of obligation — each generation of warriors who came begging tightened the lore around him. The T5 voluntary sacrifice IS the Mahabharata climax. Chain-equip lets the player feel the weight of the obligation accumulating across rungs before they reach the moment of choice.

**Tier bonuses**:
- T1: CON +3, fire_resist (current)
- T2: CON +4 (the armor grows with the warrior)
- T3: CON +4, fire_resist +2 (heavy)
- T4: CON +5, **Surya's Gift** — once per floor, when you receive a Brahmin/scholar NPC's request, you may answer "yes" and the encounter grants double its normal reward (but you cannot say no)
- T5: CON +5, Surya's Gift, Cut and Given (see below)

**T-max named ability**: **Cut and Given** — once per run, you may sacrifice the Kavacha (item permanently removed from inventory) to instantly gain full HP, +2 permanent CON, and +5 karma. This is Karna's final scene as a permanent option.

**Why legendary**: the mechanic IS the Mahabharata. You can give them up. You should not. You will.

**Code needed**: NPC-encounter forced-yes flag (moderate); permanent item-sacrifice with stat reward (moderate).

### Ring of Thunder / Ring of the Deep / Amulet of the Titan / Amulet of Insight / Ring of the Assassin / Amulet of Fortitude / Ring of Far Sight / Amulet of the Archmage / Ring of Displacement / Amulet of Protection (10 sub-unique workhorse items)

These are the "elevated commons" of the unique tier. They sit at min_level 16-28, fill out the mid-game. Keep mechanics as currently authored — they're already clean, single-stat-and-status, balanced. **No chain-equip** for any of these (their lore-weight is too thin to justify the ritual). **Optional polish** per item:

- **Ring of Thunder**: thunder-themed monsters (storm elementals, sky-serpents) hit for -10% damage.
- **Ring of the Deep**: cold immunity (not just resist) when at full CON.
- **Amulet of the Titan**: weight you can carry is +20% (Titanic frame).
- **Amulet of Insight**: +1 turn of effect on any beneficial scroll.
- **Ring of the Assassin**: backstab attacks gain +1 chain capacity.
- **Amulet of Fortitude**: poison and disease durations halved.
- **Ring of Far Sight**: detect any trap within 3 tiles (passive sense).
- **Amulet of the Archmage**: fire and shock resistances stack additively for +2 each.
- **Ring of Displacement**: 5% miss chance against you on all incoming attacks.
- **Amulet of Protection**: incoming spell damage reduced by 1 (flat).

### Ring of the Oracle / Ring of Pythia (ring_of_pythia)

Keep current (clairvoyant, PER+2). **Polish**: identify-quiz timer +2 seconds (laurel-smoke helps the seer focus).

### Diadem of Croesus (crown_of_croesus)

See Section 3 for cursed variant. Base version keeps current.

### Torc of Boudicca (torc_of_boudicca)

Keep current (STR+2, surrounded_ac_bonus +2). **Polish**: when 3+ enemies surround you, +1 chain on next combat attack (Boudicca's fury).

### Tablet of Gilgamesh (tablet_of_gilgamesh) / Tablet of Hammurabi (tablet_of_hammurabi) / Scales of Ma'at (scales_of_maat)

These three are early-mid-game lore tablets that grant small stat bumps. Each gets one thematic polish:

- **Tablet of Gilgamesh**: +1 to grammar-quiz when reading the FIRST scroll of each floor (the original literacy).
- **Tablet of Hammurabi**: NPC encounters where you offer/refuse mercy resolve at +1 karma (the first written law had specific penalties — the player benefits from acting deliberately).
- **Scales of Ma'at**: +1 chain on theology-quiz when at karma 0 (perfect balance).

### Amulet of Merlin (amulet_of_merlin)

Keep current (INT+5). **Polish**: identify-quiz +1 chain (Merlin advised three kings on what they could not see).

---

## Chain-Equip Accessory Summary

The accessories that survived the lore-test as chain-equip pieces. Subject = history for all. Each picks `escalator` or `chain` based on whether the lore is staged-deepening (escalator) or sequential-narrative (chain). 9 items total.

| Item | Mode | Rungs | T-max named ability | Lore reason |
|---|---|---|---|---|
| Seal of Solomon | escalator | 5 | Solomonic Key | The ring's ritual recognition of Solomon |
| Tyet of Isis | escalator | 5 | Reassembly | Isis assembling Osiris from 14 pieces |
| Heart of Ahriman | escalator | 5 | Anti-Being | Zoroastrian dualism deepening |
| Ring of Sir Gawain | chain | 5 | Three O'Clock | Hour-by-hour strength curve (morning/noon/3pm) |
| Ring of Scheherazade | chain | 5 | One Thousand and One | 1001 tales told one night at a time |
| Anklet of Atalanta | chain | 5 | Atalanta's Choice | Race-strides interrupted by apples |
| Necklace of Harmonia | escalator | 5 | Beautiful Ruin | Generational curse deepening across owners |
| Kavacha and Kundala | escalator | 5 | Cut and Given | Karna's growing obligation, climactic sacrifice |
| Idunn's Apple Charm | chain | 5 | Aesir-Young | Bites of the apple, each restoring youth |

**Re-equip behavior**: every chain-equip piece begins with a FRESH quiz when re-equipped. No sticky state. Player can hot-swap by accepting the quiz cost each time.

---

## Reverted to Flat (with proc)

These pieces were tier-escalator in the original draft and have been reverted to flat-passive with a single proc, preserving the proposed T5 named ability as always-on or per-floor:

| Item | Old T5 → New proc |
|---|---|
| Brisingamen | Tears of Freya (always-on at low-HP threshold) |
| Palladium of Troy | Walls of Troy + Inviolate (floor-entry buff + per-floor lethal-save) |
| Eye of Horus | Wedjat's Restoration (per-floor low-HP regen burst) |
| Ankh of Isis | Resurrect-to-full (baseline, was mastery-gated) |
| Pectoral of Amun | Hidden One (per-floor invisible-turn) |
| Ring of Odysseus | Wooden Horse (per-floor pacify-walk) |
| Ring of Percival | Right Question + Healed King (per-floor preview + per-run heal) |
| Ring of Lancelot | Best Knight (floor-entry buff conditional on previous-floor unique kill) |
| Ring of the Nibelung | Andvari's Curse (constant — pet/ally deaths damage you) |
| Hand of Fatima | 3-subject quiz bonus (constant ward) |
| Jade Cicada | Reborn (per-floor death_save + item-consumed second activation) |
| Megingjörð | Thor's Catch (per-floor armor-ignore attack) |

---

## Code Required

Hooks required to implement the above proposals, deduplicated. Complexity tagged.

### Simple (drop-in flags, reuse existing systems)
- `tier_escalator` and `chain_equip` infrastructure for accessory slot (shared with armor proposal)
- Per-floor-reset on death_save / life_save (jade_cicada, tyet_of_isis)
- Item-grants-quiz-subject-timer-bonus (most chain-equips; per-subject)
- Permanent stat-gain counter (Necklace of Harmonia named-kill)
- Pet-ally-death-deals-HP-to-bearer (Ring of the Nibelung)
- Free-move proc on flee (Anklet of Atalanta T4)
- HP-floor save (Palladium proc)
- Scroll-non-consumed-on-threshold (Scroll of Annihilation T4)
- Floor-counter spawn-ring (Draupnir)
- Per-seal status flag overlay (7 seals)
- Per-100-turn flavor messages (multiple)
- Item-grants-chain-cap-bonus (multiple)
- Resurrect_to_full as baseline (Ankh of Isis)
- Hunger-tick rate modifier (Idunn's Apple Charm)
- Negate-age-debuffs flag (Idunn's Apple Charm T5)
- Charge-exhausted passive state transition (Hand of Glory)

### Moderate (new mechanics; modest code)
- Lock-bypass action (Seal of Solomon T5)
- Summon-command via item (Seal of Solomon)
- Spell-damage multiplier on item (Heart of Ahriman)
- Spell-crit ignores resistance (Heart of Ahriman)
- Floor-entry buff conditional on prev-floor unique kill (Lancelot proc)
- Subject-specific quiz-timer bonus (Pectoral of Amun, Hamsa Hand, etc.)
- Pacify-walk-past action (Ring of Odysseus proc)
- Invisible-attack-persistence (Pectoral of Amun)
- AoE polymorph (Circe's Wand)
- Permanent-pet conversion (Circe's Wand)
- Hostile-summon-roll on chain effect (Necronomicon)
- HP/status cost on cast (Necronomicon)
- Per-chain damage-type lookup (Picatrix)
- Per-chain summon different monster (Lemegeton)
- Chain-arc lightning (Indra's Vajra)
- Per-monster-tag damage doubler (Indra's Vajra, several others)
- Cursed-side-effect proc on gold pickup (Andvaranaut cursed variant)
- Encounter dialogue conditional on inventory (Sealed Dispatch)
- Wall-vision overlay 2 tiles (Eye of Graeae)
- On-kill karma-judgment hook (Scales of Michael)
- Floor-descent flavor based on next-floor spawn (Tablet of Destinies)
- Chaos table lookup (Pandora's Box, Wand of Wonder)
- Chain-step branching effects (Aaron's Rod, Circe's Wand, Necronomicon, Sefer Yetzirah, Picatrix, Lemegeton, Wand of Wonder)
- Inventory-passive items without slot (Charmander Stuffie)
- Stair-reveal on floor entry (Ariadne's Thread, Epona's Charm)
- Permanent item-sacrifice with stat reward (Kavacha and Kundala T5)
- Allied-heal cast (Ring of Percival proc)
- Per-turn STR decay counter + reset-on-rest (Sir Gawain T5)
- Chain-capacity-buff on next-attack proc (Megingjörð proc)
- Wish-menu selection UI (Aladdin's Lamp)
- Appropriate-tier item generator (Aladdin's Lamp wish-for-item)
- Boss-location preview UI (Aladdin's Lamp wish-for-entity)
- Per-chain roll-on-table dispatch (Wand of Wonder)
- Wonder-effect grab-bag (stat-color cosmetic, levitation, future-preview, open-all-chests)

### Complex (substantial new systems; may need refactor)
- Player action-pause for spectator turns (Anklet of Atalanta T5)
- Deferred-success retry queue (Ring of Scheherazade T5)
- NPC-encounter outcome preview (Ring of Percival proc — needs to read encounter trees)
- Cross-floor item-location markers (Book of Thoth T5)
- On-summon-death quiz hook (Sefer Yetzirah T5)
- Demon-asks-question UI hook (Lemegeton chain 4)

### NEW uniques recommended to author
- **Hand of Glory** (accessory, amulet slot, cursed-charged): grimoire item from Petit Albert
- **Pandora's Box** (artifact, single-shot consumable): chaos table (1d20, mostly minor)
- **Aladdin's Lamp** (artifact, single-wish, theology-gated): three-category wish menu
- **Wand of Wonder** (wand, chain mode, science-gated): per-chain Wonder table

These bring totals to: 75 accessories, 30 artifacts, 4 unique wands.

---

## Power-Guardrail Audit

- Largest tier/chain-5 stat bonus: STR/INT/CON +5 (Heart of Ahriman, Idunn's Apple, Anklet of Atalanta, Kavacha and Kundala T4-T5, Megingjörð, Ring of the Nibelung, Ring of Lancelot) — within +5 single-stat cap.
- Flat-passive bonuses kept in roughly the same envelope (typically +3 to +5 on one stat plus a status flag or proc).
- Wild magic tables (Pandora, Wonder) biased per user guidance — Pandora 50/50 buff-debuff and MOSTLY MINOR, Wonder biased POSITIVE with occasional silly/neutral and very minor negatives.
- Aladdin's Lamp is single-use, quiz-gated at tier 5 theology; the wish is meaningful but bounded (one stat point, one item one tier above current, one ally summon).
- Quest artifacts: narrative dominates power. Use-charged artifacts (Pandora, Aladdin's Lamp) have meaningful costs (single-use, quiz-gated).
- Chain-equip named abilities are mostly once-per-floor or once-per-run — they reward the ritual without trivializing dungeon traversal.
- Cursed items (Nibelung, Harmonia, Hand of Glory) have permanent or charge-exhausted downsides — the trade is real.
- The Mahabharata-themed Kavacha and Kundala T5 (Cut and Given) is the only proposed mechanic where a unique item can be voluntarily sacrificed for a permanent stat gain. This is intentional — it is THE moment from the epic, and it should be available exactly once per run.
- Hand of Glory's charge-exhaustion permanently cursed state is a genuine cost — players who burn all three charges carry a dead hand on their neck until a remove-curse appears.

---

## Ambiguous / Flagged for Review

- **Hamsa Hand**: I reverted to flat. The 3-subject bonus is the legend mechanic and feels constant rather than ritualistic. If you want Hamsa to be chain-equip (three Abrahamic traditions = three rungs in a ritual recognition), it's a defensible read — let me know and I'll restore tier-escalator with the 3-subject bonus appearing at T3 and the reflect_gaze at T5.
- **Jade Cicada**: original had a "minimal escalator overlay" — I stripped it entirely and put Reborn (two-activation per floor with item-consumed on second) in as a flat proc. If you preferred the gentle staged overlay, it can come back.
- **Idunn's Apple**: PROMOTED from Section 9 flat to Section 9 chain-equip. The user's intuition list said "chain (bites of the apple)" but Idunn's Apple was already flat in Section 9, not in the original tier-escalator pool. I treated this as an authorial promotion to chain-equip. If the intent was "leave it flat," it's a one-edit revert.
- **Cloaks (Eyes/Eldritch/Charlemagne)**: these are armor pieces and live in the armor proposal, not this doc. The user's intuition list mentioned them, but no action was required here.
- **Eye of Graeae**: this is an artifact (already flat / inventory-active in Section 8). The user's intuition list mentioned it; no triage action required.
- **"Ring of Solomon (duplicate?)"**: there is only one Solomon item — Seal of Solomon, whose `id` is `ring_of_solomon`. No duplicate exists.
- **Wand of Wonder chain 5 row 18 "stat-color"**: purely cosmetic. If the engine doesn't support per-stat-render hue, drop it for "free identify of one item" and renumber.
- **Wand of Wonder chain 5 row 19 "open all chests"**: if traps on those chests trigger when opened by Wonder (the proposal says yes), this could damage the caster. Calling out explicitly so it can be toned down if needed.
