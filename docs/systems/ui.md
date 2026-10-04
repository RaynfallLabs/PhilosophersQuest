# UI — Rendering, Menus, HUD, Help, Welcome

**v2.18.0** (shipped 2026-10-02)

Covers everything the player sees after the dungeon tiles are blitted:
sidebar HUD, modal menus, quiz panel, combat HUD, help screen, kit /
discoveries / bestiary / lore dossier, cook / identify / drop menus,
and the welcome / name-entry flow.

**Sources:**
- `src/game_render.py` — `RenderMixin`, 8,444 LOC; every `_draw_*`
  method, the `_threshold_line` helper, the two `_identify_status_label`
  gates, and the full help-screen System-Rules card
- `src/ui.py` — `Sidebar`, `MessageLog`, left-rail / right-rail
  composition, effect chips, powers rows, in-sight rows
- `src/hud_context.py` — pure data helpers (`active_power_rows`,
  `visible_context_rows`, `hud_item_name`); True-Name identify-v3 rule
- `src/game_menus.py` — `MenuMixin`, menu input handlers, `_COOK_TABS`,
  `_open_identify_menu`, `_open_power_menu`, `_activate_gold_offering`
- `src/game_input.py` — `InputMixin.handle_event` state dispatch and
  `_player_input` key routing
- `src/fantasy_ui.py` — `FP` palette, font loader, chrome primitives
  (`draw_panel`, `draw_header_bar`, `draw_choice_button`,
  `draw_filigree_bar`, `draw_menu`)
- `src/panel.py` — `PanelBuilder`, the modal frame contract
- `src/text_layout.py` — `wrap_lines`, `truncate_label`, `fit_columns`
- `src/welcome_screen.py` — title vortex, name entry, leaderboard,
  `SECRET_BUILDS` dict

---

## 1. Architecture at a glance

Three sublayers sit between the Game loop and pygame:

```
   handle_event (game_input)
          ↓
   state-dispatch (STATE_* string → *_input handler)
          ↓
   render() (main.Game) → RenderMixin._draw_<state>()
          ↓
   PanelBuilder / fantasy_ui chrome / text_layout helpers
          ↓
   pygame surface blits
```

Rendering is driven by `Game.render()` which inspects `Game.state` and
calls the matching `_draw_<state>` method on `RenderMixin`. Input
mirrors this: `game_input.handle_event` holds a long `elif` chain
keyed on the same `STATE_*` strings; each branch delegates to a
`_*_input` method. Menu-input handlers live on `MenuMixin`;
free-input, confirm dialogs, and non-menu overlays live on
`InputMixin`.

**One rule the mixin split enforces:** no `_draw_*` method on
`RenderMixin` reads or mutates game state beyond what MRO exposes.
Rendering is a projection of state; input and action are the setters.

---

## 2. Layout + viewport

`src/layout.py`:

- `WINDOW_W = 1600`, `WINDOW_H = 900` — default; resized via
  `WINDOWRESIZED`, piped through `Game.on_resize`.
- `SIDEBAR_W = 330` (right rail), `LEFT_SIDEBAR_W = 248` (left rail).
- `GAME_W = WINDOW_W - SIDEBAR_W` — the main play area width (left
  rail does NOT reduce `GAME_W`; it overlays the far-left slice).
- `VERSION = "2.18.0"` — read by welcome screen, debug overlay, and
  the save-meta files.

The composite screen has three regions:

1. **Left sidebar** (`ui.py::Sidebar._pane` with `edge="right"`) —
   character identity, vitals, attributes, derived, effects.
2. **Center play area + message log + quiz / menu overlays** —
   `GAME_W` wide. Message log pins to the bottom with
   `MessageLog.draw`.
3. **Right sidebar** (`Sidebar._pane` with `edge="left"`) — powers,
   in-sight (enemies + items on the current visible set).

Overlays (quiz, menus, help, lore) draw a 185-alpha black
`draw_overlay` first, then a midnight-blue gold-bordered panel via
`PanelBuilder` or `draw_dark_panel`.

---

## 3. Theme — fantasy_ui.FP

Every color used in the renderer MUST come from `FP` (the "Fantasy
Palette"). Raw `(R,G,B)` literals outside `fantasy_ui.py` are an
audit finding — the catalog `tools/audit/deliverables/
beauty_screen_catalog.md` calls this "beauty-palette-bypass".

**Palette families:**

| Family | Members | Usage |
|---|---|---|
| Parchment | PARCHMENT, PARCHMENT_DARK, PARCHMENT_LIGHT, VELLUM | body backgrounds, warm text |
| Gold | GOLD, GOLD_BRIGHT, GOLD_DARK, GOLD_PALE | panel borders, headings, loot |
| Ink | INK, INK_FADED, INK_LIGHT | dark text when on parchment |
| Burgundy | BURGUNDY, BURGUNDY_MID, BURGUNDY_DARK, BLOOD | HP, danger, cursed-item accent |
| Midnight | MIDNIGHT, MIDNIGHT_MID, MIDNIGHT_LIGHT | panel background, modal fill |
| Arcane | ARCANE, ARCANE_BRIGHT, ARCANE_DIM, ARCANE_ACCENT | magic (wand, spell, scroll, identify) |
| Status | HP_RED, SP_GREEN/AMBER/RED, MP_BLUE, MP_BLUE_TEXT | resource bars + their text readouts |
| Passive | PASSIVE_FIRE, PASSIVE_MANIFEST, PASSIVE_WARD | sidebar effect chips for passives |
| Lore | LORE_GOLD_* (corpse), LORE_BLUE_* (item) | lore dossier screen palettes |

**Semantic aliases** (use these in draw code, not the raw values):

| Alias | Role |
|---|---|
| `PANEL_BG` | modal background |
| `PANEL_BORDER` | panel outer border |
| `HEADER_TEXT` | header bar text |
| `BODY_TEXT` | normal body text on midnight |
| `FADED_TEXT` | secondary / disabled |
| `ACCENT_TEXT` | accented label |
| `HINT_TEXT` / `HINT_TEXT_DIM` | footer hint |
| `DANGER_TEXT` / `DANGER_TEXT_LIGHT` | DANGER_TEXT_LIGHT is for dark bgs (menu rows, choice cards) |
| `SUCCESS_TEXT` | positive outcomes |
| `WARNING_TEXT` | warnings |
| `LOOT_TEXT` | gold / loot |
| `SLOT_EMPTY` | the "no item" filler (4.7:1 contrast on midnight) |

**Border conventions per modal:**

| Modal | Border |
|---|---|
| Generic | `FP.GOLD` |
| Wand / Spell / Scroll / Identify | `FP.ARCANE_BRIGHT` |
| Cook / Eat (success) | `FP.SUCCESS_TEXT` |
| Danger / Death | `FP.BLOOD` / `FP.BURGUNDY_MID` |
| Corpse lore | `FP.LORE_GOLD_BORDER` |
| Item lore | `FP.LORE_BLUE_BORDER` |

**Subject accent colors** — one source of truth, used by the quiz
panel border and the welcome screen domain ring:

```python
FP.SUBJECT = {
    'math':       ( 40, 210, 245),  'geography':  ( 40, 190,  75),
    'history':    (215, 170,   0),  'animal':     (210, 105,  20),
    'cooking':    (215,  35, 170),  'science':    ( 75,  90, 245),
    'philosophy': (195, 190, 215),  'grammar':    (210,  45,  45),
    'economics':  (150, 210,   0),  'theology':   (195, 162,  70),
    'trivia':     (255, 200, 100),  'ai':         (  0, 220, 120),
}
```

Adding a subject? Add it HERE and only here. The quiz-engine lookup
is `self._SUBJECT_COLOR.get(qe.subject, (160, 130, 255))` with a lavender fallback.

---

## 4. Fonts

`fantasy_ui.get_font(role, size, bold=False)`:

| Role | Font (TTF) | Use |
|---|---|---|
| `title` | Cinzel-Variable.ttf (bold) | welcome banner |
| `heading` | Cinzel-Variable.ttf | section headers |
| `body` | IMFellEnglish-Regular.ttf | normal body |
| `small` | IMFellEnglish-Regular.ttf (small) | hint, status, dense tables |
| `gothic` | UnifrakturMaguntia.ttf | reserved for ornate accents |
| `italic` | IMFellEnglish-Italic.ttf | mystic / lore flavor |

Falls back through a Windows-first serif chain (`garamond,palatino
linotype,palatino,georgia,...,serif,consolas`) when the bundled TTF
fails to load. Monospace fallback is Consolas-first.
`_font_cache` is a module-level dict keyed on `(role, size, bold)`.

**Rule:** instantiate fonts through `get_font`, never `pygame.font.Font`
directly, so the cache and fallback chain stay consistent.

---

## 5. Panel + text helpers

### 5.1 `panel.PanelBuilder` — the modal frame contract

Every modal that follows the grimoire identity (header / tabs / body /
footer hint inside a midnight-blue gold-bordered panel) is built
through PanelBuilder. The audit at
`tools/audit/deliverables/beauty_screen_catalog.md` lists the ~10
screens that still hand-roll their chrome and silently drift.

**Size classes:** `SIZE_SM` 480px, `SIZE_MD` 760px, `SIZE_LG` 1000px,
`SIZE_XL` 1280px, `SIZE_FULL` viewport-minus-margin. Width is clamped
to the current viewport. Height is 75% of viewport by default, or an
explicit `max_height`.

**Order of operations:**

```python
p = PanelBuilder(screen, size=SIZE_LG, border_color=FP.GOLD)   # paints bg
p.set_title("YOUR PACK & WHAT LIES HERE")
p.set_tabs(["Weapons", "Armor", "Shields"], active=0)
p.set_footer_hint("Left/Right: tab   Up/Down: scroll   ESC: close")
rect = p.body_rect()                                            # inner draw area
# ... custom body draw inside `rect` ...
p.draw()                                                         # chrome on top
```

Background painting moved into `__init__` on 2026-05-18 to fix a bug
where calling `draw()` last would paint the 90%-opaque midnight panel
OVER the caller's body content ("DARK blue text in identify quiz /
Recall Lore" ghost text).

Chrome tokens: `PAD_TIGHT 4`, `PAD_NORMAL 8`, `PAD_LOOSE 16`,
`PAD_SECTION 24`. `HEADER_H 44`, `TAB_BAR_H 32`, `FOOTER_HINT_H 28`,
`SCROLLBAR_W 6`.

### 5.2 `text_layout` — three pure functions

| Function | Use for |
|---|---|
| `wrap_lines(text, max_width, font)` | CONTENT (prose, descriptions, hints). Never truncates. |
| `truncate_label(s, max_width, font, ellipsis='…')` | LABELS only (tab names, column headers, button text). |
| `fit_columns(columns, available_width)` | TABLES (kit panel, character sheet, equip menu). |

Rule: `wrap_lines` for content, `truncate_label` for chrome. Using
`truncate_label` on content loses information silently.

### 5.3 `fantasy_ui` chrome primitives

- `draw_panel` / `draw_dark_panel` — mid vs. midnight-blue panel fill,
  gold border, inner shadow.
- `draw_header_bar` — midnight strip + gold accent line + corner
  diamonds. The sidebar section headers reuse this helper (so the
  sidebar reads as a sibling of every modal).
- `draw_divider` — thin gold line.
- `draw_shadow_text`, `draw_glow_text` — the welcome banner uses
  these for the hum / vortex effect.
- `draw_choice_button` — the 2×2 quiz choice card with the
  `[N] text` layout; `correct=True` turns green, `incorrect=True`
  turns red.
- `draw_filigree_bar`, `draw_rune_circle`, `draw_candle_glow` —
  welcome screen flourishes.
- `draw_menu` — legacy menu renderer still used by `_draw_cook_menu`
  fallback path; most new menus go through
  `_draw_decision_menu_variant_a` or `_draw_fast_picker_variant_b` on
  `RenderMixin`.
- `draw_tab_bar` — tab strip used inside overlays (cook, equip, drop).

---

## 6. Sidebar (`ui.py::Sidebar`)

The left rail renders five sections top-to-bottom. The right rail
renders two. All headers use `fantasy_ui.draw_header_bar` so the
sidebar matches modal typography.

### 6.1 Left rail — CHARACTER / VITALS / ATTRIBUTES / DERIVED / EFFECTS

**CHARACTER** (`_identity`): player name (gold pale, truncated to
width), then `Floor N   Turn N` in faded text.

**VITALS** (`_vitals`): HP / MP / SP bars via `_bar`. SP color
transitions `SP_GREEN > SP_AMBER > SP_RED` at 50% / 25% ratios.

**ATTRIBUTES** (`_attributes`): STR / CON / DEX / INT / WIS / PER in a
2-column × 3-row grid (col 1 = STR / CON / DEX, col 2 = INT / WIS /
PER). Values are right-aligned inside each cell so 3-digit stats stay
on their own side of the midpoint. Value color: `GOLD_BRIGHT` > 12,
`BODY_TEXT` 10-12, `DANGER_TEXT` below 10.

**DERIVED** (`_derived`): 2-column grid of 6 metrics —
`AC`, `Gold`, `Sight`, `Timer`, `Wt`, `Spells`. Weight color
turns `WARNING_TEXT` above 75% of carry limit. The old `Depth` row
was removed in v2.22.0 — the CHARACTER identity section's `Floor N`
is the sole dungeon-level readout.

> **Audit finding (SYSTEMS_AUDIT §8 P1):** the Timer line reads
> `player.get_quiz_timer('math')`, which is correct. But the earlier
> `Picks N` row (removed in this version) and the Character Sheet's
> `economics timer` line (fixed in this version) used to lie. If you
> add a new metric here, verify its data source is live — the sidebar
> renders every frame.

**EFFECTS** (`_effects`): 2-column grid of 8 chip cells (max). Each
chip is a thin color stripe + bold label. Chip label format:
`"<name> <duration>"` or compact initial 5 letters when the full form
doesn't fit (`Poisoned → Pois`, `Paralyzed → Para`, etc.). Overflow
shows **`+N more`** at the bottom (mirroring the POWERS overflow
hint).

Passive effects added as chips before status effects: Fire Protect
(`charmander_stuffie`), Manifest (`dreamspun_sketchbook`), Death Ward
(`rands_heart` amulet). Palette: `FP.PASSIVE_FIRE`,
`FP.PASSIVE_MANIFEST`, `FP.PASSIVE_WARD`.

### 6.2 Right rail — POWERS / IN SIGHT

**POWERS** (`_powers`): rows built by `hud_context.active_power_rows`
(see §7). Each row shows a label + status badge (`ready`, `Nt`
cooldown, `N uses`). Max 8 rows + `+N more` overflow.

**IN SIGHT** (`_in_sight`): two subsections, `Enemies` and `Items`.
Rows built by `hud_context.visible_context_rows`. Each row shows a
name + distance (`"here"` or `"Nt"`) with color graded by
`spawn_fit_color(dungeon_level, peak_floor, spread, kind=...)` — red
means out-of-depth-dangerous (monster) or stale (item), green means
good fit. Max 6 enemies, 6 items.

Clipping guard: `if ay + 21 > bottom: break` — rows after the panel
bottom are dropped silently. (Audit note SYSTEMS_AUDIT §8 P5 flagged
this previously for EFFECTS without the overflow hint; now EFFECTS
has `+N more`, but IN SIGHT still clips silently. Add a hint if
monster count on a floor becomes routinely high.)

---

## 7. HUD data helpers (`hud_context.py`)

Pure functions, no pygame. Drawing stays boring; filtering stays
testable.

### 7.1 `hud_item_name(player, item, include_count=False)` — True Name rule

This is the identify-v3 fix (2026-08-06). The HUD + sidebar + menu
rows all go through this helper.

```
INSTANCE identified       → full name ("Rapier +2")
TYPE known + BUC known    → full name (BUC {blessed}/{cursed} prefix)
TYPE known + BUC unknown  → "unidentified <true name>"
TYPE unknown              → item.unidentified_name (appearance)
```

The `TYPE known + BUC unknown` branch is the key one — the player
knows what the item CLASS is, but THIS copy's BUC is still a mystery.
The HUD surfaces that explicitly so the player doesn't quaff a cursed
healing potion thinking it's identified.

BUC prefix is wrapped in braces (`{blessed}` / `{cursed}`); only
rendered when `buc_known`. Count suffix (`x3`) added if
`include_count` and count > 1.

### 7.2 `active_power_rows(player, secret_build, heavenly_host_active)`

Builds the POWERS list in a fixed order:

1. Prayer (always), with `prayer_cooldown`
2. Recall Lore (always), with `recall_lore_cooldown`
3. Hack Reality (conditional on unlocked)
4. Every unlocked quirk-power in `_ACTIVE_POWER_DEFS`
5. Charmander Fire Breath, Dreamspun Manifest, Gleipnir Bind
   Odinkiller, Michael Heavenly Host (inventory-conditional)
6. Elder Blood: Blink / Charge / Scream (secret-build conditional)
7. Every entry in `player.hero_specials` with its cooldown
8. Seven-League Step + Gilgamesh's Bribe (armor-slot conditional,
   once per floor)
9. Charged accessories (Lyre of Orpheus, Hand of Glory, etc.)

Each row is a `PowerRow(label, status, state)` with `state ∈ {ready,
cooldown, uses}`. The sidebar renders color by state (`SUCCESS_TEXT`,
`WARNING_TEXT`, `MP_BLUE_TEXT` respectively).

> **Gleipnir Bind Odinkiller** currently has no cooldown — the row
> always reads "ready". TODO comment in-code says: if a cooldown is
> ever added, thread it through `cooldowns.get("bind_odinkiller", 0)`.

### 7.3 `visible_context_rows(player, monsters, items, visible, dl)`

Filters to things in the player's visible-tile set, sorts by Manhattan
distance, caps at `max_monsters` / `max_items`. Items use
`hud_item_name` so the appearance / True-Name rule applies.

### 7.4 `spawn_fit_score / spawn_fit_color`

Returns -1..1 using `(peak_floor - dungeon_level) / max(4, spread)`.
Items: positive is good (above-depth loot). Monsters: positive is
good (stale weak enemies). Negative mixes with `NEUTRAL → RED`;
positive mixes with `NEUTRAL → GREEN`. The gradient makes it visible
at a glance whether an enemy or an item is "out of your weight class
(red)" or "comfortable (green)".

---

## 8. Message log (`ui.py::MessageLog`)

- `MAX = 60` entries kept in memory.
- `add(text, msg_type='info')` where `msg_type ∈ {info, success,
  warning, danger, loot}` — maps to `_MSG_COLORS`.
- `draw(screen, x, y, w, h)` word-wraps every entry via `_wrap` to
  fit `text_w = w - 16`, then renders bottom-up. Older lines fade by
  `max(0.35, 1.0 - age * 0.09)`.
- No overflow indicator — history before the top of the pane is
  implicit scrollback. Full message review on death is a separate
  state (`STATE_REVIEW_MISSED`).

**Message style:** terse, present-tense, player-perspective. Avoid
system jargon ("mastery", "chain break", "quality N") — see the
system-change-sweep rule in [conventions.md](conventions.md).

---

## 9. State → draw method → input handler table

Full dispatch map. Column 3 is the file that owns input for that
state; column 4 is the `_draw_<state>` method.

| State | Trigger | Input handler | Draw method |
|---|---|---|---|
| `STATE_PLAYER` | default | `game_input._player_input` | main render |
| `STATE_QUIZ` | quiz starts | `_quiz_input` | `game_render._draw_quiz` |
| `STATE_EQUIP_MENU` | `E` | `_equip_menu_input` | `_draw_equip_menu` |
| `STATE_KIT` | `K` | `_kit_input` | `_draw_kit_panel` → `_draw_kit_browser` |
| `STATE_DISCOVERIES` | `J` | `_discoveries_input` | `_draw_discoveries_panel` |
| `STATE_WAND_MENU` | `Z` | `_wand_menu_input` | `_draw_wand_menu` |
| `STATE_SCROLL_MENU` | `R` | `_scroll_menu_input` | `_draw_scroll_menu` |
| `STATE_IDENTIFY_MENU` | `I` | `_identify_menu_input` | `_draw_identify_menu` |
| `STATE_COOK_MENU` | `C` | `_cook_menu_input` | `_draw_cook_menu` |
| `STATE_EAT_MENU` | `U` | `_eat_menu_input` | `_draw_eat_menu` |
| `STATE_QUAFF_MENU` | `Q` | `_quaff_menu_input` | `_draw_quaff_menu` |
| `STATE_THROW_MENU` | `T` | `_throw_menu_input` | `_draw_throw_menu` |
| `STATE_SPELL_MENU` | `M` | `_spell_menu_input` | `_draw_spell_menu` |
| `STATE_POWER_MENU` | `V` | `_power_menu_input` | `_draw_power_menu` |
| `STATE_DROP_MENU` | `D` | `_drop_menu_input` | `_draw_drop_menu` |
| `STATE_DROP_GOLD_INPUT` | drop gold | `_drop_gold_input` | `_draw_drop_gold_input` |
| `STATE_DROP_QTY_INPUT` | drop stack | `_drop_qty_input` | `_draw_drop_qty_input` |
| `STATE_HELP` | `?` | `_help_input` | `_draw_help_screen` |
| `STATE_LORE` | lore trigger | `_lore_input` | `_draw_lore_dossier_screen` |
| `STATE_HINT` | Recall Lore | any-key dismiss | `_draw_hint_screen` |
| `STATE_EXAMINE` | `X` | `_examine_menu_input` | `_draw_examine_menu` |
| `STATE_ENCYCLOPEDIA` | `B` | `_encyclopedia_input` | `_draw_encyclopedia_browser` |
| `STATE_HACK_REALITY` | hack unlock | any-key | `_draw_hack_reality_screen` |
| `STATE_XYZZY_INPUT` / `_CONFIRM` | backquote | `_xyzzy_input` / `_xyzzy_confirm_input` | `_draw_xyzzy_input` / `_draw_xyzzy_confirm` |
| `STATE_QUIRKS` | `W` | `_quirks_input` | `_draw_quirks_screen` |
| `STATE_CHARACTER_SHEET` | `@` | `_character_sheet_input` | `_draw_character_sheet` → `_draw_character_pack_sheet` |
| `STATE_NPC_ENCOUNTER` | NPC trigger | `_npc_encounter_input` | `_draw_npc_encounter` |
| `STATE_COW_ENCOUNTER` | cow spawn | `_cow_encounter_input` | `_draw_cow_encounter` |
| `STATE_JUDGMENT` | L99 altar | `_judgment_input` | `_draw_judgment` |
| `STATE_STUDY` | `;` | `_study_input` | `_draw_study_journal` |
| `STATE_MYSTERY_APPROACH` | mystery altar | `_mystery_approach_input` | `_draw_mystery_approach` |
| `STATE_INTERCESSION_PROMPT` | `Shift+\` | `_intercession_prompt_input` | `_draw_intercession_prompt` |
| `STATE_SHOP` | `Y` | `_shop_input` | `_draw_shop` |
| `STATE_PET_MENU` | `Shift+P` | `_pet_menu_input` | `_draw_pet_menu` |
| `STATE_PET_FEED` / `_HEAL` / `_SPECIALS` | pet sub-menu | `_pet_*_input` | `_draw_pet_feed_submenu` etc. |
| `STATE_PET_NAME_INPUT` | hatch | `_pet_name_input` | `_draw_pet_name_popup` |
| `STATE_TARGET` | `A`/`F`/`O`/throw/wand/spell | `_target_input` | `_draw_targeting` / `_melee_targeting` / `_throw_targeting` / `_ranged_targeting` |
| `STATE_QA_WARP_INPUT` | Titivillus `W` | `_qa_warp_input_handler` | `_draw_qa_warp_popup` |
| `STATE_STORY_POPUP` | narrative | any-key | `_draw_story_popup` |
| `STATE_CONFIRM_EXIT` | ESC on player | `_confirm_exit_input` | `_draw_confirm_exit` |
| `STATE_EXIT_QUEST` | has Stone + stairs<1 | `_exit_quest_input` | `_draw_exit_quest` |
| `STATE_ABANDON_QUEST` | no Stone + stairs<1 | `_abandon_quest_input` | `_draw_abandon_quest` |
| `STATE_CHICKEN` | McFly | `_chicken_input` | `_draw_chicken` |
| `STATE_VICTORY` | has Stone + L0 | hard exit | `_draw_victory_screen` |
| `STATE_DEAD` | HP ≤ 0 | `R` → review | `_draw_death_screen` |
| `STATE_REVIEW_MISSED` | post-death `R` | arrow nav | `_draw_review_missed` |

**Global keys that override state dispatch:**

| Key | Effect | File |
|---|---|---|
| `F11` | toggle fullscreen | `handle_event` |
| `F2` | toggle debug overlay | `handle_event` |
| `ESC` | state-dependent dismiss (see table in `handle_event` L88-174) | `handle_event` |
| `Shift+I` | immortal toggle (QA only, `qa_tools` build) | `handle_event` |
| `Shift+W` | floor warp (QA only, `qa_tools` build) | `handle_event` |
| `TAB` | cycle zoom `full → medium → close → full` | `_player_input` |

ESC behavior is critical: it dismisses almost every modal cleanly,
with special handling for `STATE_QUIZ` (end as chain-0 failure),
`STATE_TARGET` (refund MP for pending spell), `STATE_NPC_ENCOUNTER`
(call `_close_npc_encounter(resolved=False)` so NPC stays reachable),
`STATE_PLAYER` (open confirm-exit), `STATE_REVIEW_MISSED` (back to
`STATE_DEAD`), `STATE_PET_FEED/HEAL/SPECIALS` (back to pet menu).

**Spurious QUIT guard:** `handle_event` for `pygame.QUIT` logs the
event, routes to `STATE_CONFIRM_EXIT` unless `_quit_confirmed` is
set — defends against OS sleep / RDP / focus-loss events closing the
run silently.

---

## 10. Key dispatch (`_player_input`)

The main input routing lives in `game_input.InputMixin._player_input`.
Returns early on `sleeping` / `paralyzed` (turn passes).

| Key | Action |
|---|---|
| `.` | wait / meditate (+1 MP if no adjacent monsters) |
| `g` / `,` | pickup |
| `e` | equip menu |
| `r` | scroll menu |
| `z` | wand menu |
| `u` | eat menu |
| `q` | quaff menu |
| `m` | spell menu |
| `i` | identify menu |
| `h` | harvest |
| `c` | cook menu |
| `p` | disarm trap, then lockpick |
| `a` | melee targeting |
| `f` | fire ranged weapon |
| `t` | throw menu |
| `\` | pray (plain) / `Shift+\` divine intercession |
| `n` | recall lore |
| `?` / `/` | help |
| `x` | examine known items |
| `b` | encyclopedia |
| `d` | drop menu (altar / fountain / grave interact special-case) |
| `y` | merchant shop |
| `v` | active powers menu |
| `` ` `` | xyzzy input |
| `w` | quirks progress |
| `o` | observe cursor |
| `k` | kit comparison |
| `j` | discoveries |
| `;` | study journal (missed questions in-run) |
| `TAB` | cycle zoom |
| Arrows | move / attack |

Arrows: `_MOVE_KEYS` maps `K_UP/DOWN/LEFT/RIGHT` to deltas; movement
routes through `_do_move`. (`A`/`F`/`T` open targeting cursors;
targeting arrows are a separate `_TARGET_MOVE_KEYS` constant on Game,
not here.)

---

## 11. Quiz panel (`_draw_quiz` L2071-2306)

**Modal geometry:** 1060px wide max, centered. Chrome: header
(42px) → tier pips + timer bar (28px) → question (variable, capped
to half-viewport minus `_reserved = 240 + (110 if combat)`) → 2×2
choice-card grid → status feedback (36px) → combat HUD (110px, if
chain-mode combat).

**Header right-side:**
- CHAIN modes render `Chain x{N} — {rank_name}` with font upgraded to
  `font_lg` at chain ≥ 10 and color recolored at each rank milestone
  via `_chain_rank`.
- THRESHOLD / ESCALATOR_THRESHOLD modes render `{correct_count} /
  {required}` **AND the "any wrong = fail" subtitle** below it
  (DANGER_TEXT, L2170-2189). This is the player-facing zero-tolerance
  cue.
- Header `right_reserve` sized to the wider of counter / subtitle so
  the quiz title never overlaps.

**Tier pips:** 5 small circles left of the timer bar — filled at
`i < qe.tier`, hollow otherwise. Shows escalator-mode progression.

**Timer bar:** rendered only when `qe.timed = True`. Non-math quizzes
drop the bar entirely (L2220 branch). Color gates: green > 55%,
amber > 28%, red below. Tick marks every 20%. Seconds label on the
right end.

**Choice cards:** 2×2 grid via `draw_choice_button`. Each card has a
`[N]` key badge and wrapped text. Case-EXACT comparison for correct
match (not `.lower()`) — pre-2026-06-01 the lowered comparison would
mark all four grammar-capitalization choices green. In the RESULT
phase: correct = green border, player's wrong pick = red border.

**Status bar:**
- RESULT phase: `*  CORRECT!` or `*  WRONG!` centered in `font_lg`.
- ASKING phase: `Press  1  2  3  4  to answer` in HINT_TEXT.

**Combat HUD** (`_draw_combat_hud` L2391-2470, when chain + combat
target):
- LEFT: monster name + HP bar + status effects row. Name truncated
  via `truncate_label` to not bleed into the right column.
- RIGHT: damage-type banner (`WEAKNESS!` dm ≥ 1.5, `RESISTED` dm ≤
  0.5, else damage-type names). Chain-rung preview table showing
  current / next / peak damage; the ranged variant uses
  `player.ranged_weapon` for its base.

---

## 12. Threshold copy — the 12 sites that use `_threshold_line`

`game_render._threshold_line(label, n)` at line 53 is the single
source of truth for threshold-line copy. Format:
`"{label}: {n} correct (any wrong = fail)"`.

**Call sites (post-v2.18 unification):**

| Line | Context | Call |
|---|---|---|
| 6500 | `_lore_item_mechanic_lines` Armor | `_threshold_line("Equip", item.equip_threshold)` |
| 6514 | `_lore_item_mechanic_lines` Shield | `_threshold_line("Equip", item.equip_threshold)` |
| 6537 | `_lore_item_mechanic_lines` Accessory | `_threshold_line("Equip", item.equip_threshold)` |
| 6547 | `_lore_item_mechanic_lines` Wand | `_threshold_line("Science", item.quiz_threshold)` |
| 6556 | `_lore_item_mechanic_lines` Scroll | `_threshold_line("Grammar", item.quiz_threshold)` |
| 6566 | `_lore_item_mechanic_lines` Spellbook | `_threshold_line("Grammar", item.quiz_threshold)` |
| 7274 | `_draw_lore_dossier_screen` Armor | same |
| 7285 | `_draw_lore_dossier_screen` Shield | same |
| 7296 | `_draw_lore_dossier_screen` Accessory | same |
| 7301 | `_draw_lore_dossier_screen` Wand | `Quiz` label |
| 7305 | `_draw_lore_dossier_screen` Scroll | `Quiz` label |
| 7344 | `_draw_lore_dossier_screen` Spellbook | `Quiz` label |

**Rule:** if you add a new threshold-displaying item class or a new
item card, call `_threshold_line` — never `f"Equip: {n} correct"`
hand-rolled. The lie-by-omission regression is a sticky one.

Subject labels: use the subject the quiz actually uses — `Science`
for wands, `Grammar` for scrolls / spellbooks, `Equip` for armor /
shield / accessory (which doesn't fire a subject-specific quiz).

---

## 13. Cook menu (`_draw_cook_menu` L4454-4530)

**Tabs:** `_COOK_TABS = (('Recipes', 'compound'),)` — ONE tab. The
single-cook tab was removed on 2026-06-07; the `'single'` branch
remains as dead code in the fallback below `return` (safe to delete).

**Entries:** compound recipes from `self.cook_compound_recipes`,
rendered through `_draw_decision_menu_variant_a` with a `_RecipeIcon`
proxy that sprites to `recipe_{id}` then falls back to the first
ingredient's sprite.

**Context lines:**
- `COOKING` title (GOLD_BRIGHT)
- `SP {sp}/{max_sp}` (color-coded: green > 30, amber > 10, red
  below)
- `Recipes available: {N}`
- **v2.15.0 UI-rot fix line:** `"Cooking uses one cooking question.
  Right = full meal; wrong = ruined."` (FADED_TEXT) — matches cook v2
  flow.

**Open:** `game_menus._open_cook_menu` filters compound recipes to
those the player has ingredients for; sets `self._cook_tab`,
`_cook_sel`, `_cook_scroll`.

**Input:** `_cook_menu_input` — LEFT/RIGHT cycles tabs via
`_cycle_tab(..., _cook_tab_has_items)` (empty tabs skip); UP/DOWN
scrolls; ENTER or a-z fires `_cook_compound`.

**Dead code to clean (SYSTEMS_AUDIT §5):** below the explicit `return`
at L4531 is the legacy `_cook_item` path with two `_format_tier_preview`
branches (one v2.6.4, one legacy `tier_outcomes`). Marked unreachable.
Removing it is a straight delete.

---

## 14. Identify menu (`_draw_identify_menu` L4397-4452)

Post-identify-v3 (2026-08-06) model. One philosophy Q, no masteries.

**Entries:** every candidate item from `self.identify_menu_items`
(prepared by `_open_identify_menu`, see §15). Each entry carries:
- `name`: display name (via `_display_name`)
- `detail`: `"{Type label} | ID tier {tier}"` where `tier` is
  `items.item_id_tier(item)` — corpses get `"Corpse lore | ID tier
  {tier}"` instead
- `badge`: `GROUND` / `PACK` / `CORPSE`
- `details` lines: one-line prompt — `"Reveal this item directly."`
  if a Scroll of Identify is pending, else `"Answer ONE philosophy
  question at the item's tier."`

**Context lines:**
- `IDENTIFICATION`
- Shard row: `"Shard: carried"` if carrying Philosopher's Shard,
  `"Shard: not needed (Plato's Form of Ideas active)"` if
  `plato_no_shard` passive, else `"Shard: needed (or use a Scroll of
  Identify to bypass)"`
- `Targets: {N}`
- `"One question. Right: fully identified. Wrong: the Shard stuns
  you."`

Border: `FP.ARCANE_BRIGHT`.

**Open:** `game_menus._open_identify_menu` collects (a) ground items
on current tile, (b) unknown pack items (`id_level < 5`), (c)
corpses — ingredients are flattened into their corpse source. Guards
against calling the menu with zero candidates.

---

## 15. Bestiary (bestiary flows through `_draw_lore_dossier_screen` for corpse subjects)

The bestiary lives in two places: the Encyclopedia browser
(`STATE_ENCYCLOPEDIA` → `_draw_encyclopedia_browser` L7782) under the
`bestiary` category, AND the dossier `_draw_lore_dossier_screen` /
`_draw_lore_screen` for the per-corpse case.

**Corpse rendering** (`_draw_lore_screen` L7065-7395, corpse branch):

Per the identify-v3 model, a corpse is either unstudied (`id_level
< 5`, name + symbol only) or fully studied (`id_level >= 5`, stats +
resistances + family + lore all at once). The `>= 2 / >= 3 / >= 4`
intermediate gates below are preserved for old-save corpses stuck at
partial levels; new corpses only use 0 and 5.

**Ingredient reroute (v2.18 bestiary fix, SYSTEMS_AUDIT §10 P2):**

The old path was `load_ingredient_for(subject.ingredient_id)` where
`subject.ingredient_id` is a dead field written to 525/527 monsters
in the OLD scheme (`rat_meat`, `goblin_flesh`, …). Those ids don't
exist in `ingredient.json`, so the Bestiary "Ingredient:" / "Solo
cook:" / recipe hint lines never rendered.

The current path (L7144-7156) routes through `prime_cuts.json` keyed
by the monster's `kind`:

```python
monster_id = getattr(subject, 'kind', '') or getattr(subject, 'id', '')
prime_info = _load_prime_cuts().get(monster_id) if monster_id else None
if prime_info:
    ing_id = (f"{monster_id}_trophy"
              if prime_info.get('is_trophy')
              else f"{monster_id}_prime")
```

This is the same rule `food_system._harvest_outcome_for_tier` uses,
so the bestiary preview matches what harvest actually drops.

---

## 16. Lore dossier (`_draw_lore_dossier_screen` L6706)

The dossier is the "detail view" for a selected item or corpse. Owns
the paired "lore + mechanics" presentation.

**Identity lines** (`_lore_item_identity_lines`):
- Display name (GOLD_BRIGHT, heading)
- `Identification: {_identify_status_label(id_level)}` where the
  label maps:
  - `>= 5` → `"Identified"`
  - `>= 4` → `"Type known (BUC / enchant hidden)"`
  - `>= 1` → `"Partial (legacy save)"`
  - else → `"Unknown"`
- If `id_level < 1` and `unidentified_name` present: show the
  appearance.
- `True name` (if `id_level >= 1` else `"Unknown"`)
- `Class: {item_class}`, `Slot: {slot}`, `Weight: {w}`
- `Aura: {buc}` (when `id_level >= 2` or `buc_known` else "unknown")
- `Source: Equipped | Pack | Record`

**Mechanic lines** (`_lore_item_mechanic_lines`, L6468-6568):
- Hidden entirely at `id_level < 3`: `"Mechanics unrevealed"`
- Weapon: type, material, tier, damage dice + average + types,
  reach, 1h/2h, special (stun / bleed / knockback / ignore_shield),
  ammo requirement
- Armor / Shield: AC, enchant, resistances, `_threshold_line("Equip",
  n)` — see §12
- Accessory: slot + effects + `_threshold_line("Equip", n)`
- Wand: effect, power, charges, `_threshold_line("Science", n)`
- Scroll: effect, power, `_threshold_line("Grammar", n)`
- Spellbook: teaches, mp_cost, `_threshold_line("Grammar", n)`

**v2.15.0 UI-rot fix** (preserved here): the Weapon branch dropped
the stale "Perfect Chain Crit" label — crit was retired in v2.14.0
("chain IS the crit"), and `crit_multiplier` was stripped from all
99 uniques. The chain-identity display is now honest: polynomial
weapons show `Chain: n^{exp}` with example rungs; array weapons show
the chain-multiplier array.

Palettes: `LORE_BLUE_*` for items, `LORE_GOLD_*` for corpses — gives
item vs biology lore distinct visual families.

---

## 17. Help screen (`_draw_help_screen`)

Panel: `COMMAND REFERENCE`, max 1380×620, GOLD border. **Pure
keybind reference** — every row is a key → action pair, no prose, no
parentheticals. Every listing must map to a real dispatch in
`game_input.py`; test by pressing the key.

**Six key-group columns:**

1. **Movement** — Arrows, `.`, `< >`, `Tab`
2. **Combat** — `A`, `F`, `T`, `M / Z`, `V`
3. **Items** — `E`, `X`, `I`, `H`, `C`, `D`, `U / Q`, `R`
4. **Knowledge** — `@`, `B`, `J`, `K`, `W`, `;`, `N`
5. **World** — `G / ,`, `P`, `Y`, `\`, `Shift+\`, `O`, `Shift+P`
6. **System** — `1-4`, `SPACE`, `?`, `ESC`

Rendered in a 3-column (if wide ≥ 780) or 2-column grid. Each key
tile is a midnight-mid pill with gold border; the description is a
single line.

**Footer hint:** `"? / ESC: close"`.

Earlier (v2.18) revisions carried a "System Rules" prose subpanel at
the bottom covering zero-tolerance / chain-v2 / math-only / subject-
action-map. That card was removed on 2026-10-03 — it was unrequested
clutter and the extra height squeezed the grid rows enough to
truncate the last entry of the Knowledge column (Recall Lore).
The zero-tolerance/chain-v2 rules live in the quiz modal subtitle
and in `conventions.md` instead.

If you add a new keybind, add it to the group that fits AND verify
the dispatch exists in `game_input.py`. Do **not** attach
parentheticals ("1 philosophy Q", "mid-chain", "theology chain",
"compound recipes" etc.) — the help screen is a key map, not a
tutorial.

---

## 18. Welcome screen (`src/welcome_screen.py`)

### 18.1 Flow

`WelcomeScreen(screen, version, notice=None).run(clock)` is the pre-
game loop. Returns `(name, build_dict | None)`. Rotates between the
primary panel (title vortex + name entry) and the leaderboard panel
on `F2`.

**Primary panel elements:**

- Title banner (Cinzel bold, drop-shadow)
- Vortex (`_draw_vortex`) — animated runes behind the entry panel
- Candle glow + domain ring (`_draw_domain_ring`) — the per-subject
  gradient circling the entry
- Name input box (`_draw_name_input`) — pygame key capture, Delete
  deletes the save, Enter submits
- Footer hints (F2 leaderboard, F11 fullscreen, Delete save)

**Leaderboard panel:**

- Top-N `highscore_system.get_top` list
- "All-Time Best" summary strip (`_draw_alltime`)

### 18.2 Secret builds

`SECRET_BUILDS: dict[str, dict]` maps lowercased names to override
dicts. 30+ entries: philosophers, warriors, mythic figures. The
build dict carries stat overrides (STR/CON/DEX/INT/WIS/PER) and
`_`-prefixed metadata:

| Key | Role |
|---|---|
| `_sprite` | env sprite replacing default player tile |
| `_start_weapon` | start weapon id (or `(class, material)` tuple) |
| `_start_wand` | start wand id |
| `_start_book` | start spellbook id |
| `_start_accessory` | start accessory id |
| `_start_shield` | start shield id |
| `_start_armor` | start armor id |
| `_start_soul_spheres` | number of Soul Spheres |
| `_start_spells` | list of spell ids learned at start |
| `_no_dagger` | skip the default iron dagger |
| `_immortal` | player cannot die (dad build) |
| `_qa_tools` | enable Shift+I immortal, Shift+W warp (gated) |
| `_greeting` | custom welcome line |

**QA gate:** `_qa_tools: True` builds (titivillus) are only honored
when `PQ_QA_MODE=1` or `--qa` is on the CLI (L472-476). If neither
is set, the build is returned as None — the player gets a plain run
instead of dev cheats.

See [progression.md](progression.md) for the full secret-build
inventory and [conventions.md](conventions.md) §11 for the design
rule (secret builds are intentional surprises, don't demystify them).

---

## 19. Menu primitives on RenderMixin

Not every menu is a bespoke `_draw_<name>_menu`. Two generic
primitives handle most lists:

### 19.1 `_draw_decision_menu_variant_a(...)` L2883-3007

Used by: cook, identify, scroll, equip (new path), wand, pet feed,
pet heal, pet specials.

Takes `entries` (name, detail, key, icon, name_color, detail_color,
badge, badge_color, details), `selected` index, `context_lines`
(list of (text, color, font)), optional `tabs`, optional
`active_tab`, `tab_counts`, `hint`, `border_color`, `scroll_attr`.

Layout: tabs (if given) → entries list with sprite + 1-line detail
→ selected-entry "details" subpanel on the right (3-4 lines) →
footer hint.

### 19.2 `_draw_fast_picker_variant_b(...)` L3008-3122

Used by: power menu, discoveries, hero-special pickers.

Simpler — no sprite, no detail subpanel. Compact badge + description.
Good for terse `[READY | CD 5t | x3 USES]` lists.

### 19.3 Helpers

- `_menu_letter(i)` — maps index 0-25 to a-z key label
- `_menu_clamp_selection('_name_sel', len(entries))` — persistent
  per-menu cursor
- `_menu_item_detail_lines(item, action)` — standard "action phrase +
  mechanic preview" subpanel content
- `_menu_recipe_detail_lines(recipe)` — recipe-specific preview
  (tier, SP/HP, buff / permanent power)
- `_menu_base_context([lines])` — builds the standard subtitle block
  used by the context panel

If you add a new modal list, use variant_a unless the content is a
pure selector; new menus going into variant_a inherit the chrome, the
scroll handling, and the detail subpanel for free.

---

## 20. `_activate_gold_offering` (format-bug fix, v2.18)

`game_menus._activate_gold_offering` (L1561-1605) powers the
Gilgamesh's Bribe passive on armor. It picks the closest visible,
non-boss, INT ≥ 5 monster, rolls `1d100` gold cost, and (if the
player can pay) paralyzes the target for 1 turn.

**v2.18 bug fix (SYSTEMS_AUDIT §7 P1):** the pre-fix message was
`.format(tname=target.name)` only — `{cost}` and `{target.name}`
reached the log unsubstituted. Current code uses an f-string:

```python
f"You toss {cost} gold at the {target.name}'s feet. "
f"The {target.name} bows and steps aside."
```

The symmetric "no bribeable mortals" message is now:
`"No bribeable mortals in sight — only dumb beasts or kings."`

If you add a similar hero-special with a per-target message, use an
f-string, not `.format` — the audit was explicit about this pattern.

---

## 21. Discoveries panel (`_draw_discoveries_panel` + `_discoveries_sections`)

`J` opens a six-section summary:

| Section | Rows |
|---|---|
| QUIZ PERFORMANCE | total answered, right/wrong, acc%; per-subject grid with per-tier `T{N} CLEARED` or `T{N} r/t` |
| IDENTIFICATION | total identifies performed, item types learned, Mantle of the Philosopher |
| BESTIARY | monsters encountered, monsters studied |
| FAITH & KARMA | prayer boons, karma (clamped −10..+10) |
| MAGIC | spells learned, reality hacks claimed |
| JOURNEY | current floor, deepest floor reached |
| QUIRKS | unlocked count (NAMES hidden to avoid spoilers) |

**v2.18 vocabulary fix (SYSTEMS_AUDIT §8 P4):** the per-tier badge is
now `T{ti} CLEARED` — pre-fix it was `T{ti} MASTERED`, sharing
vocabulary with the removed class / family / identify masteries. Per-
run tier-clear (the badge the player earns for clearing an entire
tier) is retained as a mechanic; only the word changed.

The Quirks section intentionally shows only the count. Secret-build
rule: unlocked-quirk NAMES would spoil hidden mechanics; keep them
hidden until the player triggers them.

---

## 22. Character sheet (`_draw_character_pack_sheet`)

`@` opens the full character sheet. `_draw_character_sheet` is a thin
wrapper that forwards to `_draw_character_pack_sheet` (which lives
further up `game_render.py`). The code below `return` in
`_draw_character_sheet` (L978-1232) is the LEGACY sheet retained for
reference; the live sheet uses the pack layout.

**v2.18 timer-line fix** (even in the dead branch, L1045, so a grep
hit is still honest):

```python
f"Quiz timer: {math_t}s (math combat only). Other subjects untimed."
```

Pre-fix: `"Quiz timer: {math_t}s (combat) to {econ_t}s (text-heavy)
x{timer_mod}"` — asserted a text-heavy timer that doesn't exist. The
new line is honest about math-only timing. Also deleted: the
`"+{int_bonus}s on magic subjects (INT bonus)"` row.

**Rule:** sheet rows must be live-data-driven. If a feature is
retired, remove its row entirely, don't leave a `0` or `−`
placeholder — that reads as "worth earning" to a new player.

---

## 23. Rendering invariants (what to not break)

1. **Every modal paints bg BEFORE body.** `PanelBuilder.__init__`
   does this; hand-rolled modals that call `draw_dark_panel` at the
   end create the "ghost text" bug. Use PanelBuilder for new modals.
2. **Every `_draw_*` method handles the empty / zero case.** Example:
   `_draw_identify_menu` guards zero candidates upstream in
   `_open_identify_menu`; `_draw_cook_menu` renders an empty list
   gracefully.
3. **Every list has a scroll attr.** `scroll_attr='_name_scroll'` on
   `_draw_decision_menu_variant_a` keeps the scroll position across
   frames; losing it resets scroll on every redraw.
4. **ESC dismisses or confirms-exit — never silent.** See
   `handle_event` L88-174 for the full dismiss table.
5. **Color never means more than one thing.** HP red is burgundy;
   DANGER_TEXT is blood red; DANGER_TEXT_LIGHT is the salmon used on
   dark backgrounds. Pick the one that matches the background's
   contrast class.
6. **No raw RGB literals outside `fantasy_ui.py`.** Add a `FP`
   constant and reference it.
7. **No hand-rolled threshold copy.** Use `_threshold_line`.
8. **No "mastery" vocabulary.** The three stores were removed on
   2026-08-06; see [conventions.md](conventions.md) §6.
9. **No fictitious timers.** If a non-math subject gains "N seconds",
   that's dead copy — rewrite the reward.

---

## 24. Known UI-rot debt (SYSTEMS_AUDIT findings not yet fully resolved)

Documented for traceability. Fixes land in follow-up commits.

- **Sidebar `Picks 0` row** (`ui.py::_derived` pre-fix). Deleted in
  this version — `player.lockpick_charges` was always 0 and never
  incremented.
- **Character sheet timer line** — fixed in this version.
- **11 threshold-copy strings** — unified under `_threshold_line`.
- **Help screen System Rules card** — added in v2.18, removed 2026-10-03 (unrequested clutter, truncated Knowledge group).
- **Discoveries `MASTERED` → `CLEARED`** — renamed.
- **`MASTERY!` toast → `TIER N CLEARED`** — renamed.
- **Mimir's Well reward text** — still promises timers; replace with
  a stat-bump or save-bonus reward (open item).
- **`sage_counsel` and 16 timer-quirk parentheticals** — "if X ever
  becomes timed" tails still in copy; retargeted to stat bumps, but
  the parenthetical is noise now.
- **Effect chip overflow** — added `+N more` hint; IN SIGHT panel
  still clips silently.
- **Quiz "1 wrong = fail" cue** — added as subtitle in the header
  right slot (L2170-2189) for threshold modes.

---

## 25. Adding a new menu / overlay — checklist

1. Add `STATE_<NAME>` to `src/game_states.py`.
2. Add the ESC branch to `game_input.handle_event` so ESC dismisses
   cleanly.
3. Add a dispatch arm in `handle_event` (`elif self.state ==
   STATE_<NAME>: self._<name>_input(key)`).
4. Add `_<name>_input` handler on `InputMixin` (free input) or
   `MenuMixin` (menu-style).
5. Add `_draw_<name>` method on `RenderMixin`. Use `PanelBuilder` or
   `_draw_decision_menu_variant_a`.
6. Add an `_open_<name>` method on `MenuMixin` that sets state,
   builds the entry list, resets `_<name>_sel` / `_<name>_scroll`.
7. Wire the trigger key in `_player_input` (or in an existing menu's
   action handler if it chains from another menu).
8. If the menu renders a quiz threshold, use `_threshold_line`.
9. If the menu displays item names, use `hud_item_name` so the
   True-Name identify-v3 rule is honored.
10. Add context lines explaining the mechanic in one line (follow the
    cook / identify menu pattern: `COOKING / SP x/y / Recipes
    available / Cooking uses one cooking question...`).

**Do not:**
- Instantiate pygame.font.Font directly — use `get_font`.
- Use raw RGB literals — add to `FP` first.
- Hand-roll threshold copy.
- Say "mastery" anywhere.
- Promise timers on non-math subjects.
