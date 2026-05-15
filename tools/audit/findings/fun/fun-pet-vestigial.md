---
id: fun-pet-vestigial
dimension: fun
severity: P3
title: Pet system is mechanically present but emotionally vestigial — no dialog, no bonding loop, no narrative weight
status: open
systems: [pets, soul_spheres, npcs, chronicle]
when_it_hits: "Any run with a pet — feels like an extra DPS pool, not a companion"
evidence:
  - src/pet_system.py:1-80
  - src/game_combat.py:333-378
  - src/main.py:512-537
  - fun_pacing_trace.md#pets--npcs
discovered: 2026-05-15
---

## The friction or flatness
The pet system (`pet_system.py`) introduces 4 species × 3 evolution stages of creatures (Pokémon-flavored: Zappik→Voltpaw→Thundertail, etc.). Pets follow the player, attack adjacent monsters, evolve at XP 33 and 66, and have a damage type and signature attack with status effect chance.

What pets *don't* have:

1. **Names** — they're "Zappik" generically, not "Pikachu the Zappik."
2. **Dialog** — pets don't talk, ask, react, refuse. Compare to the unicorn (`game_encounters.py:251-300`) which has 5 distinct states (wary → relaxing → offered → eating → trusting) and a karma gate. The unicorn feels alive; pets do not.
3. **Bonding moments** — the only chronicle line a pet generates is the spawn message: "A soul sphere hatched. {pet.name} emerged. I'm not alone anymore." (`game_combat.py:378`). No further chronicle on evolution, no farewell on death.
4. **Loss consequence** — pets die in combat. There's no funeral beat, no chronicle entry, no "remember when…" The pet just stops being on the screen.
5. **Player-side investment**: the player throws a Soul Sphere at a tile. That's the whole bonding ritual. There's no choosing-by-affinity, no nurturing, no decision points that bind the player emotionally.

A pet is, mechanically, a small extra DPS pool that the player throws into combat as a wand-replacement. The Pokémon framing (named species, evolution stages) is *aesthetically* there but **mechanically** the pet is closer to a wand of fire bolt than a companion.

This is a missed opportunity given how much the rest of the game leans into named encounters with narrative texture (the Lost Girl, the Wandering Merchant, the Ethereal Unicorn, the Cow, the Fisher King, Asterion). The pet should be that level of texture, repeated; instead it's a fire-and-forget combat helper.

## When and how often it fires
- Any run that catches a Soul Sphere (~5% per floor + 15% chance from merchant). About half of full runs feature at least one pet.
- The pet is on screen for the rest of the run (unless it dies). Every floor walked features a pet doing pet things, with zero narrative engagement.

## Suggested redirect
- **Player names the pet on hatch**: simple text prompt. Suddenly the pet is *theirs*. The chronicle line incorporates the player-given name.
- **Pet states** mirroring the unicorn: hungry, content, trusting, scared. Pet-feeding (giving the pet a food item) raises trust and unlocks dialog snippets ("Voltpaw nuzzles your hand. You think it remembers the cave.")
- **Evolution chronicle**: when a pet evolves, write a chronicle entry. The first evolution especially is a wonder beat that currently passes by silently.
- **Pet-specific lore hints**: at chain 3+ on Recall Lore *while a pet is alive*, occasionally roll a hint that's specifically about the pet's species ("The yellow rodents of the deep are said to remember thunder.")
- **Pet farewell**: when a pet dies, a chronicle entry. ("Voltpaw fell. I covered the body with my cloak. The dungeon felt colder.")

## Notes
The pet system shares mechanical DNA with NPC encounters but completely lacks their narrative warmth. Spans pet_system + chronicle + npc_encounters paradigm. This is the kind of thing that turns a "good roguelike" into a "this is my favorite game" — the kid who names their pet and remembers them across runs is the player who comes back.
