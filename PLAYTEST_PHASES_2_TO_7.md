# Play-test list: rebalance Phases 2 to 7

Date: 2026-10-06. Six local commits since v3.0.0's play-test fixes (`586cefc` to the Phase 7 commit). Nothing here has been played. Tests (2,100) prove the rules do what they say; they do not prove the game feels right.

Run from source: `python src/main.py`

## Reachable in the first twenty minutes

| What to do | What should happen |
|---|---|
| Look at the sidebar | It says **Clock Ns**, not Timer. Drink a haste potion or pray to Michael: the number rises and turns gold. Get confused or stunned: it falls and turns red. |
| Open the character sheet | Two new readouts, **Dodge** and **Tough**, both 0% for a starting character. Check they fit: I added a row and could not see the screen. |
| Look at any weapon's card | It starts with **Tier N Sums**. |
| Kill something, harvest it, cook the prime cut properly | "You feel it doing you good. (Strength: 1 of 2 meals toward +1)". Cook the same stat's cut on the next floor: "Your Strength increases by 1!". A second proper meal on the same floor teaches nothing. |
| Stand still hurt (hold `.`) | Health climbs to 60% and stops. Only food, potions, spells or prayer take it higher. |
| Meditate (hold `.` with mana missing) | After half a mana bar on one floor: "This floor's quiet has no more to give; the next will." |
| Fight on floors 1 to 13 | Ordinary monsters hit for three quarters of what they did. Floor 1 should feel safe for a careful child. |
| Start as a hero with a named weapon (Achilles, Leonidas, Prometheus, Geralt, Ciri, Ash Williams) and reach floor 12 to 20 | "Achilles' Spear Grows With You: Base Damage 8 Becomes 10." At floor 20 it also says it now asks tier 2 sums. |
| Cast any damage spell or zap a wand | It does roughly half of what one good chain does. It should feel like a useful extra, not the main event. |
| Hatch a pet | Its bite is about a quarter of your own attack; it should survive several hits. |

## Asterion (floor 20): the one fight worth playing on purpose

- He should feel like a wall for a character who has cooked little and has no Thread, and a hard but fair fight otherwise. Measured: he beats about half the casual players who reach him.
- Every blow he swings is 2% heavier than the last. The log tells you ("...his blows come heavier. Every moment this lasts favours the bull.").
- Walk away for 25 turns and come back: "Asterion has had time to mend. Wounds you gave have closed."
- When he dies a panel opens: **Three Things Lie Where The Bull-Man Fell**. Press 1, 2 or 3. Escape does nothing on purpose. With the Thread each gift shows one more point.

## Cannot be play-tested in reasonable time (covered by tests and the simulator)

Gifts from Medusa, Fafnir and Fenrir; Fenrir's heavier blows and the Sandal; Abaddon's lighter ones; Death's scythe on the climb out (8% of full health a blow); trait points being held and paid out as you descend; lucky stat points running out; pets and hero weapons at depth.

## The one thing I could not measure at all

The climb out with the Stone. The simulator has no map, and Death's chase is a race across a map. If you ever get there, tell me whether it was tense or lethal.

## What the numbers say now

For a child who is 95% right on simple sums, 480 simulated runs each (a "win" is Abaddon dead):

| Player | Reaches floor 20 | Wins |
|---|---|---|
| Casual: cooks a little, skips quests | 93% (about half then beat Asterion) | 0 |
| Prepared: cooks, does the quests | 98% | 32% |
| Committed stat build | 100% | 35% |
| Committed build with a pet | 100% | 55% |
| Committed, found the four secrets | 100% | 45% |
| Everything: build, secrets, pet, magic | 99% | 59% |

Full account, phase by phase: `REBALANCE_MASTER_PLAN.md` (each phase has an "As built" note).
