# The gold economy

Economy refactor, 2026-10-17 (ECONOMY_REFACTOR_PROPOSAL.md, built per
ECONOMY_REFACTOR_REPORT.md). Every gold rule is in `src/economy.py`; the
traders are `src/traders.py` (pure rules) and `src/game_traders.py` (the
Game side); the people and their lines are `data/traders.json`; what an item
is worth is `data/item_worth.json`.

## 1. The income line

`economy.floor_income(level) = 130 + 76 x level` (206 on floor 1, 1,650 on
floor 20, 7,730 on floor 100). Every price, share and written amount is
measured against it. Refit 2026-10-17 from `tools/balance/gold_sim.py`
(40 runs, 'prepared' at 90%): the generator pays within about 15% of the line
in every 10-floor band. (The old line, 150 + 90 x floor, had drifted: the
generator paid 1.35-1.55 times it from floor 40 down.)

LORE NOT FLOOR: the line sets PRICES and baked data; nothing multiplies a
creature's gold by the floor at runtime.

## 2. Where gold comes from (D1: gold by lore, not per kill)

| Source | Where | Rule |
|---|---|---|
| Monster purses | `data/monsters.json` `treasure.gold`, written by `tools/balance/gold_by_lore.py` | By what the creature IS (`treasure.purse`): beasts, vermin, oozes, plants, constructs, elementals, spirits and most demons carry **nothing**. People carry a purse (`purse`), thieves a fat one (`thief`), casters coin for ink (`scholar`), giants a sack, the buried dead grave goods, vampires and liches old money (`noble_dead`), fey trinkets, leprechauns a pot, dragons a hoard (by age), incubi and succubi bait (`tempter`); a leader word (king, chief, lord...) doubles it. Named one-offs, bosses and specials (`kept`) are left as written: a named beast's gold is its lair. Amounts are a share of the line at the creature's peak floor x a depth weight (deep floors hold far more people, so each carries less); hoards and pots take a fixed weight. |
| Room coin piles | `dungeon.spawn_items` | 25% of ordinary rooms hold a dropped purse (`COIN_PILE_SHARE` 1.5-4% of a floor). Drawn from a private generator keyed on the floor generator's state: no layout or roll after it moves. |
| Lairs | `dungeon.spawn_items` | A monster den or a barracks holds a heap (`LAIR_GOLD_SHARE` 8-20%). |
| Treasury, zoo, vault | `dungeon.spawn_items` | Unchanged (0.15-0.35, 0.5, 0.5 of a floor). |
| Chests | `container_system.chest_gold`, `data/chest_templates.json` `gold_share` | A share of the floor's income by chest (a wooden chest 7-14%, a gilded chest 7-14% deep, a dragon hoard 19-38%); a pass rolls the top 30% of the range. |
| Boss hoards | `boss_levels.py` | Fafnir's heaps and alcoves, Fenrir's side rooms: shares of the floor (`FAFNIR_HEAP_SHARE` ...), no longer written sums. |
| Graves, thrones, encounters, mysteries | unchanged | Encounter written gold x6 (`economy.written_gold`). |
| Selling | the traders (section 4) | New. |

Measured, 'prepared' at 90% (40 runs; see the report for every band):
floors 1-10 pay what they did (0.98x); floors 20-99 pay about 60% of what
they did. A 'casual' player (fights less) earns about what he did before,
because the coin is no longer inside the monsters.

## 3. Prices

`economy.merchant_price(item, level, markup=1.0)` = floor income x class
share (`MERCHANT_SHARE`: potion 0.15, food 0.10, ammo 0.10, scroll and wand
0.5, spellbook 0.8, gear 0.6, accessory 1.5; a named unique 3.0, rings and
amulets included, S4) x tier (0.6 + 0.2 x tier) x **worth**
(`economy.item_worth`, from `data/item_worth.json`: Full Healing 3, Healing
1, Sickness and every harmful potion or cursed ring "junk" 0.1, Ambrosia 12,
a Soul Sphere its own share of 2 floors) x the trader's markup.

Stock is sold unidentified, so a price that follows worth lets a sharp eye
price-identify (a NetHack-style discovery). `economy.unknown_price` is the
price of a thing as its unidentified class (tier 2, worth 1): what the hero is
offered for something he cannot name, never its true worth.

## 4. The traders (D4)

`data/traders.json` `traders`: six people, each with a name, a reason to be
down there, a stock list, a markup, a buying purse, what they buy, their
services and their lines.

| Kind | Who | Floors | Stocks | Buys | Services |
|---|---|---|---|---|---|
| generalist | Grindle, Deep Gnome Trader | 2-98, about 1 floor in 6 | potions, scrolls, rings, wands, ammo, common gear, sometimes a Soul Sphere | everything (a fence) | map |
| apothecary | Mother Wort | 2-35, 3 a run | a cure or healing for sure, potions, food | potions, food, ingredients | cure, restore, heal |
| armourer | Brannoc | 10-70, 3 a run | common gear, ammo | weapons, armour, shields, ammo | repair, sharpen, reinforce, cut a curse off |
| bookseller | Ambrose Vellum | 15-90, 2 a run | scrolls, one spellbook | scrolls, spellbooks | identify with the scribe, map |
| abyssal | Vesper, Dealer in the Deep | 61-98, 2 a run | named rings first, wands, potions (x1.5) | everything, curses too | cut a curse off, restore |
| sutler (gate camp) | Old Mags Thorn | 19, 39, 59, 79, always | healing for sure, potions, food, a scroll, ammo, armour | everything | repair, cure, heal, porter |

**The plan** (`traders.roll_plan`): rolled once a run from the Road's seed
(`road.rng_for(seed, 'traders')`), never from the shared random stream.
Gate camps first; then the specialists inside their ranges, preferring floors
with no anchor, medium or high Road slot and never two specialists side by
side; then a generalist on some of the floors left (half as often on a busy
Road floor). Never on floor 1, 99, 100, a boss floor, the Cow Level, or the
Emberpup's or the Black Knight's floor. Saved as `Game._traders`.

**Placing** (`TraderMixin._maybe_spawn_trader`, called last in the arrival
spawns of `_change_level`): once per floor, on first arrival. Stock and spot
come from `road.rng_for(seed, 'trader:<floor>')`. The spot is a floor tile in
a room, reachable from the hero (`_reachable_tiles`), clear of the stairs,
every item and creature, the tiles around any encounter NPC, escort or ally,
and at least 3 tiles from the hero. Named uniques in stock are claimed for
the run. Floor generation no longer places a trader at all
(`spawn_merchant` is kept for tools and tests only).

**Stock** (`traders.build_stock`): guaranteed entries (`ids`) first, then
random picks weighted to the floor like other loot, deduplicated, dressed
(`dungeon.dress_spawn`, so wands come with rolled charges and arrows in
rolled bundles: S3), never cursed or enchanted, cut to `stock_size`. No
restock: a trader's goods are a one-time chance.

## 5. The shop (Y beside a trader)

`STATE_SHOP`; the model is `TraderMixin._trader_menu`, drawn by
`game_render._draw_shop` through `_draw_decision_menu` (the Midnight Codex
kit: the tab strip keeps the active tab in view via `tab_strip_window`; the
footer key hints replaced the removed `footer_regions` helper). Keys:
Left/Right/Tab change tab, Up/Down move, Enter buys / sells one / pays, H
haggles (Buy tab), Esc closes (or backs out of choosing a target).

- **Buy**: price x the deeds multiplier (section 7). Haggling (economics
  escalator chain, 10% a link, at most 50% off, once per ware, remembered on
  the ware). What was paid is remembered on the thing bought (`_bought_for`;
  a potion that joins a stack marks the stack).
- **Sell** (D5): the pack (worn things are never listed). The offer is
  `economy.sell_offer`: 20% of his own price, 25% when the copy is identified
  to the last detail; a thing whose type is unknown is priced as its
  unidentified class; capped by what is left in his purse
  (`purse` floors of income, spent as he buys, never refilled). Refused:
  quest pieces (`Game._QUEST_PIECE_IDS`, scripted-only ids, plot-locked
  things, every artifact but a Soul Sphere), tools and keys, things outside
  a specialist's line, and a curse the hero knows of (except to Vesper). A
  sold thing is gone: it never reappears in his stock (that would price-
  identify it).
- **No buy/sell loop**: a thing bought from any trader never sells for more
  than half of what was paid (`RESALE_CAP_OF_PAID`). The least ever paid is
  40% of a list price (a full haggle and a friend's price), so every resale,
  on any floor, to any trader, at any markup, loses gold. Haggling never
  changes what he pays.
- **Services** (D3): see section 6.

A trader whose every ware was a unique the run already had is `sold_out`
(S10); a sold-out trader still buys and still works.

## 6. Services (D3: gold buys a second chance, never the answer)

`economy.service_price(sid, level, purse, points, markup)`; shares of the
floor's income (`SERVICE_SHARE`), the dearest also a share of the purse when
that is more (`SERVICE_PURSE_PCT`: restore 10%, cut a curse 5%). Rendered by
`TraderMixin._render_service`, shared with vendor encounters (a `service`
reward). Nothing is charged when there is nothing to do.

| Service | Price | What it does |
|---|---|---|
| repair | 0.15 a point | Gives back every point of enchantment rust, acid or fire took from worn gear (`items.wear_down` records `wear_loss`; never above what it had). |
| sharpen / reinforce | 0.6 | +1 to the wielded weapon / the body armour; at most +2 per piece from smiths (`_smith_bonus`). |
| cut_curse | 0.3 (or 5% of the purse) | Cuts off a worn piece whose curse the hero KNOWS of; the piece is destroyed. Never a quest piece or a part of the hero. |
| cure | 0.25 | Ends poison, disease, blindness, confusion, the shakes, petrification... (timed statuses only, never an item's). |
| restore | 0.8 (or 10% of the purse) | Every stat point a drain, a drain potion or a disease took (`status_effects.note_stat_drain`; Strength in `_str_lost_to_disease`). |
| heal | 0.3 | Back to full health. |
| id_retry | 0.3 | Identify one item with a scribe at your elbow: the same philosophy question (`_identify_item(item, backlash=False)`); a wrong answer costs the fee, not 10 turns stunned. |
| map | 0.3 | The floor's layout. |
| porter | 0.5 | `porter` for 3 floors (carry limit + `PORTER_CARRY_BONUS`). |

Vendor encounters that sell a service: Brunhild the smith (sharpen, and
mend), Doctor Finch (cure), the Medical Construct (restore, 15% of the purse).

## 7. Deeds and prices (D7)

`traders.price_mult(kind, ctx, friend)`; conditions are `deeds.check`
conditions in `data/traders.json`. No karma: it is the market, not God.

- **The traders talk** (`guild.wronged`): robbing Pomfrey Quill, Helena or
  Edric, selling Tansy or Sariel to Vell, burning the moneylender's markers:
  every trader's prices x1.25 for the rest of the run. The first trader to
  know says why, once a run (`_traders['told']`).
- **People repay** (`friend` per trader): Pomfrey Quill (saved) comes back as
  the generalist, Marta Venn as the apothecary, Corporal Pell (his company
  saved at the granary) as the armourer, Helena Marsh as the bookseller:
  their own art, their own line, a friend's price (-20%). Once a run each.
- **Kept oaths earn credit**: each `kept.*` deed is one thing on the house
  (up to a floor's income; above that, it comes off the price) at the next
  trader (`_traders['credits_used']`).
- **Charity has consequences, never karma** (`rumours.open_hand`: paying the
  widow's measure, Hanne, Charon's fare, the child's keep, the plague
  village, Berengar's rites, Hopkins, the Piper): Grindle and Vesper charge
  you 10% more ("Heard you pay other people's debts"), Mother Wort and Old
  Mags 10% less. Falling for Wren's con (`rumours.wrens_mark`) marks you with
  the fences: Grindle +15%.
- **Shoplifting**: not built (an open question for Brandon).

## 8. Purse shares (S1, D6)

- A `gold_pct` cost the hero CHOOSES has a floor: `economy.pct_cost` takes
  N% of the purse, never less than N% of two floors' income; an empty purse
  cannot pay it, and the option's label shows the figure
  (`npc_encounters.gold_pct_label`). (Dropping your gold first made every
  such choice free: the Golem Medic, Hopkins, the child, the slavers.)
  Losses that land on the hero (a thief, a delayed consequence) stay a plain
  share of what is there.
- Late temptations (floor 40 and down, plus the deep anchors: Vell's fee,
  selling Tansy, the red book, Andvari, the penitent's gold...) carry
  `purse_pct` on their gold reward: the written sum or that share of the
  purse, whichever is more (`economy.purse_scaled`).
- A `forgo` option's karma counts only when the gold turned down was real:
  at least 10% of the purse at the time (`economy.forgo_is_real`); a
  purse-relative temptation always is, and so is anything more than gold.

## 9. Other gold rules

- **Found gold vs the hero's own** (S2): `items.add_gold_to_tile(...,
  found=False)` for the hero's own coin (dropped, or given back by a thief);
  the two kinds never merge; a gold ring (Draupnir) multiplies found gold only
  (`items.is_found_gold`).
- **Gilgamesh's Bribe** (S9): priced once per monster (`_bribe_cost`); the
  monster stands aside (`charmed`, it will not raise a hand) for
  `BRIBE_TURNS`, and the deal is off the moment you strike it
  (`Monster.take_damage`). It was paralysed: three free turns of helpless
  hits.
- **Gold earned** (S7): `Game.player_gold` is a property; every rise is
  booked in `gold_earned` (found, rewarded, sold) except the hero's own coin
  coming back. The ending shows "Gold Earned" and "Gold Carried" (it read
  "Gold Collected" and showed the purse). Saved.

## 10. Tools

| Tool | What |
|---|---|
| `tools/balance/gold_sim.py` | The measured gold curve, floor by floor and source by source (wraps `difficulty_sim`). |
| `tools/balance/purse_model.py` | The purse under hoarder / sensible / whale spending, with the real trader plan, stock, services and selling. |
| `tools/balance/gold_by_lore.py` | Writes every creature's purse into `data/monsters.json` (`--report` to preview). Re-run after adding monsters. |
| `py -m tools.encounters.validate --all --budget` | Checks `share` / `service` gold costs, `purse_pct`, `service` rewards, and the karma budget. |

Tests: `tests/test_economy.py`, `tests/test_traders.py`.
