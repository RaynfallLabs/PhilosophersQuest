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
the six Soul Spheres their own shares by tier: Soul 2, Greater 3.5,
Master 5, Hearth 3, Greater Hearth 5, Master Hearth 7 floors) x the trader's markup.

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
| generalist | Grindle, Deep Gnome Trader | 2-98, about 1 floor in 6 | potions, scrolls, rings, wands, ammo, common gear, sometimes a Soul Sphere (25% on 1-33) or a Greater Soul Sphere (from 34) | everything (a fence) | map |
| apothecary | Mother Wort | 2-35, 3 a run | a cure or healing for sure, potions, food | potions, food, ingredients | cure, restore, heal |
| armourer | Brannoc | 10-70, 3 a run | common gear, ammo | weapons, armour, shields, ammo | repair, sharpen, reinforce, cut a curse off |
| bookseller | Ambrose Vellum | 15-90, 2 a run | scrolls, one spellbook | scrolls, spellbooks | identify with the scribe, map |
| abyssal | Vesper, Dealer in the Deep | 61-98, 2 a run | named rings first, wands, potions (x1.5); rarely a Master Sphere (10%), a Greater Hearth Sphere (4%) or, from 67, a Master Hearth Sphere (3%) | everything, curses too | cut a curse off, restore |
| sutler (gate camp) | Old Mags Thorn | 19, 39, 59, 79, always | healing for sure, potions, food, a scroll, ammo, armour; sometimes a Soul Sphere (19, 39, 59) or a Greater Soul Sphere (39 on) | everything | repair, cure, heal, porter |

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
  things, every artifact but the six Soul Spheres, and a sphere that holds a
  bound companion), tools and keys, things outside
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
| `tools/balance/gold_sim.py` | The measured gold curve, floor by floor and source by source (wraps `difficulty_sim`); since 2026-10-18 also the treasure a floor pays (`t_value`, `t_weight`, by kind) and `wealth` (coin + treasure). |
| `tools/balance/purse_model.py` | The purse under hoarder / sensible / whale spending, with the real trader plan, stock, services and selling. It ignores weight: read it as "what was found", and weight_model.py as "what could be carried". |
| `tools/balance/weight_model.py` | What a careful hero CAN CARRY at each depth: coin under the Burdened line, gems and jewellery, art; the coin left behind; how often the dearest ware on a trader's table was within reach of coin plus treasure. |
| `tools/balance/gold_by_lore.py` | Writes every creature's purse into `data/monsters.json` (`--report` to preview), and its treasure chance and kinds. Re-run after adding monsters. |
| `py -m tools.encounters.validate --all --budget` | Checks `share` / `service` gold costs, `purse_pct`, `service` rewards, and the karma budget. |

Tests: `tests/test_economy.py`, `tests/test_traders.py`, `tests/test_treasure.py`.

## 11. Coin weight and treasure (Brandon's D2, 2026-10-18)

> "I think that's a very real lesson about cash and metals; they have value
> but are hard to move. Make sure player can DROP gold. ... make sure it's a
> realistic weight for coins. Let's say 1 gp is 1/10th an oz? ... Gems or
> TREASURE ... could be great way to capture wealth."

Rules in `src/treasure.py` (pure) and `src/game_purse.py` (the Game side).

- **A gold piece weighs a tenth of an ounce**: 160 to the pound
  (`treasure.COINS_PER_LB`). `Game.player_gold` mirrors the count onto
  `Player.purse_coins`, so the purse counts in `get_current_weight` with
  Burdened and the limit exactly as for any item. 16,000 gold is a full
  pack at STR 10; a fresh hero has room for about 13,900 coins, 10,000
  before he is Burdened.
- **Receiving gold** (`_gain_gold`): he keeps what he can carry. Found gold
  (a grave, a throne, a cache) that will not fit is set down at his feet as
  his own pile, booked once in Gold Earned. A PERSON paying him (a trader
  buying, an encounter's reward, change) makes up what will not fit in gems
  (`treasure.gems_for`, the dearest gem kinds found by that floor), valued.
  Brisingamen's tears stop when the purse is full.
- **Piles** (`_pickup_gold`): picked up only as far as he can carry: "You
  can only carry 340 of the 1,200 gold. The rest stays on the floor." A full
  pack takes nothing and spends no turn. Draupnir (and every
  `gold_multiplier` ring) doubles a FOUND pile once, where it lies, the first
  time it is touched; the hero's own pile never.
- **Dropping gold**: `D` lists **Drop Gold** first, with an amount prompt
  that shows the weight. The pile is the hero's own (`found=False`) and joins
  his own pile on the tile, never a find.
- **Thieves** cut the coin purse (the hero is lighter by it) and snatch a
  piece of treasure most of all (`theft.BRIGHT_KINDS`). What a dead thief
  drops is the hero's own, picked up by weight as any pile.
- **The bribe** (Gilgamesh's helm) is tossed coin, never gems.

### Treasure

17 kinds in `data/items/treasure.json` (class `items.Treasure`), each with
a real weight and a lore-fixed value. LORE NOT FLOOR: a kind is worth the
same on every floor; deep floors hold the dear kinds by spawn bell.

| Kind | Name | Weight (lb) | Value | Floors (min, peak) |
|---|---|---|---|---|
| gem | Bohemian Garnet Cluster | 0.02 | 60 | 1, 6 |
| gem | Lump of Baltic Amber | 0.03 | 150 | 3, 14 |
| gem | Badakhshan Lapis Stone | 0.05 | 450 | 10, 26 |
| gem | Burmese Ruby | 0.01 | 2,500 | 30, 50 |
| gem | Kashmir Sapphire | 0.01 | 4,000 | 42, 66 |
| gem | Golconda Diamond | 0.01 | 8,000 | 60, 84 |
| gem | Eye of a Temple Idol | 0.05 | 15,000 | 75, 95 |
| jewellery | Viking Silver Arm-Ring | 0.5 | 90 | 1, 8 |
| jewellery | Saxon Garnet Brooch | 0.2 | 350 | 6, 20 |
| coins | Byzantine Solidus Purse | 0.5 | 700 | 12, 30 |
| jewellery | Celtic Gold Torc | 1.0 | 1,800 | 20, 40 |
| jewellery | String of Gulf Pearls | 0.1 | 3,000 | 36, 58 |
| art | Silver Candelabra | 6 | 600 | 8, 24 |
| art | Liangzhu Jade Disc | 2 | 2,000 | 26, 46 |
| art | Arras Tapestry | 20 | 3,500 | 24, 48 |
| art | Gold Idol | 10 | 5,000 | 38, 64 |
| art | Persian Gold Rhyton | 4 | 12,000 | 68, 88 |

- **Known by sight, valued by a trader**: no identify question; the art and
  the name are the same before and after. The exact worth of a KIND is known
  once a trader has valued it (`Player.appraised_treasure`; every trader
  values the pack when his shop opens, and the gems on his table carry their
  price). Before that the hero sees its band (`treasure.VALUE_BANDS`: "tens /
  hundreds / thousands of gold", "a fortune"), and what he can count on for
  paying is the band's low end, so an unvalued piece never says more than he
  knows.
- **Score**: the true value of the treasure carried when the run ends, a
  point a gold (`treasure.SCORE_PER_GOLD`). Coin does not score. The ending
  screens show "Treasure" beside Gold Earned and Gold Carried; the
  high-score row keeps `treasure` (0 for older rows).
- **Where it lies** (`treasure.py` constants; what is found is weighted to
  the floor like any loot):

  | Place | Rule |
  |---|---|
  | Chests | a `treasure` loot weight in `data/chest_templates.json`: jewel box 8, dragon hoard 4, merchant's strongbox and crypt chest 2, gilded chest, ornate chest and iron lockbox 1 |
  | Treasury room | a piece half the time (`TREASURY_PIECES`) |
  | Vault | one piece (`VAULT_PIECES`) |
  | Den, barracks | one piece one time in ten (`LAIR_CHANCE`) |
  | Gate bosses | Asterion 1, Medusa 1, Fafnir 3, Fenrir 2 (`BOSS_HOARD_PIECES`) |
  | Rich grave | grave goods: jewellery or old coin (`GRAVE_KINDS`) |
  | Throne | a loose stone half the time (`THRONE_GEM_CHANCE`) |
  | Creatures | `treasure.treasure_chance` / `treasure_kinds` in monsters.json, written by `gold_by_lore.py`: dragons 0.03-0.09 by age, vampires and liches 0.025, thieves 0.02 (leaders x2); grave goods are in the graves, dug |
  | Traders | a few gems for sale (below) |
  | Bones | a dead hero's dearest pieces, at most a floor's income all told |

  A hoard's coin shrinks by the worth of the treasure laid beside it, never
  below a quarter (`treasure.coin_after_treasure`): deep, a hoard is gems and
  plate more than heavy coin. Treasure is placed from a generator of its own
  (`treasure.private_rng`), so no other floor roll moves.

### Trading in treasure (data/traders.json `treasure`)

- **Every trader buys treasure** at `buy_rate` (0.9) of its value, capped by
  his purse, whatever he otherwise deals in. No resale cap: he sells a gem at
  `sell_markup` (1.1) and buys it at 0.9, so no loop is possible.
- **The exchange**: each trader has a few gems for sale (`gem_stock`: Vesper
  3, Grindle and Mags 2, the others 1), priced at value x 1.1, never haggled,
  never given a friend's or a charity discount (a wronged guild's rise still
  applies). Heavy coin becomes light gems at a tenth's cost.
- **Paying with treasure** (`game_purse._pay_gold`, the design choice that
  keeps deep prices payable): coin first; if it falls short, the
  fewest-gold set of pieces that covers the rest (`treasure.plan_payment`),
  taken at `buy_rate`, change in coin from his purse (and gems for change
  that will not fit). The Buy tab says so before Enter: "Pays with a Gold
  Idol; 1,890 gold back." Services are paid the same way, after they are
  done. Buying pays first, so the coin paid lightens the pack before the ware
  goes in; a ware still too heavy is set down at the hero's feet.
- **Encounters** take treasure too: a gold cost is coin first, then treasure
  at the same rate, change in coin (`EncountersMixin._npc_pay_gold`). An
  altar's tribute gives no change. "Can you afford it" counts treasure at
  what the hero can count on (`_purse_wealth`).
- **"Your purse"** for every share of it (a chosen "N% of your purse" cost,
  a temptation of "a quarter of what you carry", restore and cut-curse
  prices, the forgo-karma test) is coin plus treasure at the trader's rate
  (`_purse_wealth`). A loss that lands on the hero (a quick hand in the
  night) is a share of the coin.

### Stock that builds a character (2026-10-18)

Brandon: "merchants should be an excellent way for kids to find or CHOOSE
items they haven't yet encountered, helps to BUILD the character."

- **The lean** (`stock_bias`): every random pick of a trader's stock weighs
  a kind the hero has already held (`Player.seen_item_ids`, filled by
  `add_to_inventory`, plus the known types) at `seen_weight` (0.3) against 1
  for one he has not. A gear pick draws `gear_candidates` (3) pieces for the
  floor and keeps one by the same weights. The lean picks KINDS only: wares
  are still sold unidentified, and their power is their own.
- **The spread** (`spread` per trader): his stall always holds at least one
  ware from each group, by role. Grindle: an accessory; a weapon, armour or
  shield; a scroll or book; a potion, wand or ammo. Mother Wort: a potion;
  food. Brannoc: a weapon; armour; a shield or ammo. Ambrose: a scroll; a
  spellbook. Vesper: an accessory; a wand; a potion; a scroll or book. Mags:
  a potion; food; armour or a weapon; a scroll or book.

### The Draught of Mimir's Well (D8)

Brandon: "No WIS purchase, possible rare shop appearance?" There is no
regular WIS purchase. One `rare_stock` ware: `draught_of_mimir`, about 1
trader stock in 30 (`chance` 0.034), floor 40 and down, priced at 5 floors of
income x 0.8 (4 floors: about 12,700 gold on floor 40, 21,800 on floor 70).
Gold buys the flask, never the wisdom: drinking it asks one philosophy or
theology question at tier 4 (the potion's `quiz` block); right, +1 WIS for
good; wrong, the water runs through and the draught is wasted. It is never
random loot (min_level 9999, no spawn weight) and arrives known.

### Measured (2026-10-18)

`gold_sim.py` (40 runs, 'prepared' at 90%), per floor in each band:

| Floors | Income line | Coin | Treasure | Treasure / income |
|---|---|---|---|---|
| 1-5 | 358 | 310 | 24 | 0.07 |
| 6-10 | 738 | 728 | 48 | 0.07 |
| 11-19 | 1,270 | 1,344 | 203 | 0.16 |
| 21-29 | 2,030 | 1,804 | 424 | 0.21 |
| 31-39 | 2,790 | 2,318 | 1,104 | 0.40 |
| 41-49 | 3,550 | 3,184 | 1,910 | 0.54 |
| 51-59 | 4,310 | 4,022 | 2,274 | 0.53 |
| 61-69 | 5,070 | 5,185 | 2,872 | 0.57 |
| 71-79 | 5,830 | 5,393 | 3,769 | 0.65 |
| 81-89 | 6,590 | 5,913 | 4,416 | 0.67 |
| 90-99 | 7,312 | 6,857 | 5,559 | 0.76 |

`weight_model.py` (120 runs; a careful hero, STR 10 rising to 18, a 40-60
lb kit, never Burdened), medians:

| Floor | Room for wealth | Coin carried | Gems and jewellery | Wealth (floors of income) | Coin left behind (all run) | Dearest ware within reach |
|---|---|---|---|---|---|---|
| 5 | 34 lb | 1,382 (9 lb) | 120 | 2.9 | 0 | 92% |
| 10 | 39 lb | 4,464 (28 lb) | 493 | 5.6 | 0 | 99% |
| 19 | 37 lb | 3,393 (21 lb) | 3,393 | 4.3 | 8,354 | 100% |
| 30 | 47 lb | 6,631 (41 lb) | 7,660 | 6.0 | 18,387 | 100% |
| 50 | 55 lb | 6,273 (39 lb) | 35,468 | 10.6 | 52,274 | 100% |
| 70 | 63 lb | 4,823 (30 lb) | 76,345 | 14.9 | 119,569 | 100% |
| 99 | 63 lb | 0 | 141,715 | 18.5 | 278,749 | 100% |

From floor 15 on he cannot carry what a floor pays in coin, leaves about
half of all coin behind by the end, and carries his wealth as gems (most of
it bought at a trader at a tenth's cost). Every trader's dearest ware stays
within reach of coin plus treasure. (purse_model.py, which ignores weight,
still shows what was FOUND: a sensible buyer 26x a floor's income at 99.)
Two dials set how hard coin weighs: `treasure.gem_stock` and
`sell_markup` (how easily coin becomes gems), and the treasure counts above.

### QA

The Titivillus QA build's `$` key (`_qa_treasure_sampler`) lays a found pile
of 20,000 gold under the hero, one of every treasure kind round him, and a
trader with gems and the draught beside him.
