# A1 — UI / Menu Rendering Audit (overnight bug-bash)

Audited:
- `src/game_render.py` (4626 lines, 50+ `_draw_*` methods)
- `src/fantasy_ui.py` (1095 lines: `draw_menu`, `draw_dark_panel`, helpers)
- `src/panel.py` (`PanelBuilder`)
- `src/ui.py` (`Sidebar`, `MessageLog`)

Skipped (already fixed): kit items columns, kit spells columns, identify menu N/5 markers, character sheet equipment-line truncation.

Layout assumptions used throughout the audit:
- `GAME_W = 1280`, `WINDOW_H = 900`, `MSG_H = 200`, `GAME_H = 700` at the default resolution.
- `font_sm` = body 20, `font_md` = body 26, `font_lg` = heading 32, `font_xl` = title 42.
- The window IS resizable (`layout.py` exports `resize()`), but no `_draw_*` checks the live values *during* a draw — they read `layout.GAME_W` once at the top and proceed. Things will break at small window sizes; this audit treats that as out-of-scope unless a method assumes a *minimum* size larger than the floor.

---

## A. Text overflow / clipping (missing truncate seam)

### [CRITICAL] Cow encounter description renders without truncation safety
**File**: `src/game_render.py:714-721`
**What I see**: `_wrap_text(..., bw - 50)` wraps the description (good), but the panel is `bh = 320` fixed and three rendered option lines each take 28px starting at `y += 12`. With longer wrap counts on the description, options can push past `by + bh - 40` and overlap the footer / poke hint at the bottom. There is no `if y > by + bh - …` clamp inside the per-line loop.
**Reproducer / when it triggers**: At 720p windows or future i18n where description wraps to 4+ lines, the "[3] Poke the cow." line lands underneath the poke hint.
**Suggested fix**: Either grow `bh` from content like `_draw_story_popup` does, or add an `if y >= by + bh - footer_h: break` to the desc loop.
**Confidence**: MEDIUM

### [WARN] Judgment narrative text has no bottom clamp
**File**: `src/game_render.py:907-927`
**What I see**: `_draw_judgment` word-wraps each paragraph and blits at `y += 24` per line, but never checks against `by + bh - footer_h`. The panel is fixed at `bh = 360`. A long karma history (e.g. multi-paragraph for max negative karma) will overflow the footer ("Press ENTER to continue").
**Reproducer / when it triggers**: Karma threshold story that wraps to >9 lines at 1280-wide.
**Suggested fix**: Add `if y > by + bh - 50: break` around line 925 before `y += 24`.
**Confidence**: MEDIUM

### [WARN] NPC encounter text overflows when label wraps past panel
**File**: `src/game_render.py:783-799`
**What I see**: In the `options` phase, `_wordwrap_text` wraps long opt labels and increments `y += 20` per line, then `y += 8` after each option. No bottom clamp. Panel `bh = 440`.
**Reproducer / when it triggers**: An NPC option text >120 chars at 760px text width would wrap to 3 lines per option × 3 options = `54+9×20+24 = 234` extra px after `by + 54` = `y ≈ 288`. Tight but okay; longer text breaks it.
**Suggested fix**: Pre-measure total wrapped height; if it would overflow, shrink labels with `truncate_label` or grow the panel to a content-fit height.
**Confidence**: LOW (today's content is fine, but the option text comes from JSON — adversarial fix recommended)

### [WARN] Hack-reality result lines can overflow bottom border
**File**: `src/game_render.py:349-355`
**What I see**: `_draw_hack_reality_screen` wraps each result line and blits at fixed `bh = 400`. There's no clamp on `y` against `by + bh - 30`; a multi-line result + many items in `result_lines` can push past the "[ any key ] to close" prompt.
**Reproducer / when it triggers**: Singularity chain (chain=5) with rich `result_lines` content from `hero_specials`.
**Suggested fix**: Track `y > by + bh - 40` and break.
**Confidence**: MEDIUM

### [WARN] Hint screen — no clamp on `wrap_lines` body
**File**: `src/game_render.py:4435-4439`
**What I see**: `_draw_hint_screen` renders all wrapped lines of `hint_text` without checking `y > body.bottom`. The panel is `max_height=320` and stars take 28 + footer takes ~28, leaving ~264 for content. A 200-char hint at 18pt font is roughly 10-12 lines, 22-26 per line = ~260-280 px. The exit case where lines exceed body just paints over the footer hint area.
**Reproducer / when it triggers**: Recall Lore chain 4+ at high tier → long lore string. The "Next recall in N turns" hint can be overwritten.
**Suggested fix**: Stop the loop when `y + line_h > body.bottom`.
**Confidence**: MEDIUM

### [WARN] Drop-gold panel doesn't use `layout.WINDOW_H` for centering
**File**: `src/game_render.py:4085-4105`
**What I see**: `by = (layout.GAME_H - bh) // 2` uses `GAME_H` (700) instead of `WINDOW_H` (900). Every other modal centers in WINDOW_H. The drop-gold popup will appear shifted upward by 100px relative to the message log, which surprises the user vs other input boxes (drop, pet name, QA warp).
**Reproducer / when it triggers**: D > Drop gold from any room.
**Suggested fix**: Change `layout.GAME_H` to `layout.WINDOW_H` to match the rest.
**Confidence**: HIGH

### [WARN] `_draw_pet_menu` early-returns leak the panel chrome with no hint
**File**: `src/game_render.py:3006-3011`
**What I see**: When `items` is empty, the function blits "No active companions…" at `(bx + 30, y)` then `return` — the footer hint ("a-z: select pet | …") never renders. The user sees a half-populated panel with no exit instruction.
**Reproducer / when it triggers**: Open the pet menu (Shift+P) before summoning a pet.
**Suggested fix**: Move the early-empty case to render an "ESC: close" hint at the footer before `return`, or restructure so the hint render is unconditional.
**Confidence**: HIGH

### [WARN] `_draw_pet_sub_picker` early-returns leak the chrome too
**File**: `src/game_render.py:3120-3124`
**What I see**: Same shape: when items empty, renders the message and returns BEFORE the hint draw at the bottom of the function. User sees a popup with no ESC instruction.
**Reproducer / when it triggers**: Pet feed submenu with no food in inventory.
**Suggested fix**: Always render hint, or restructure.
**Confidence**: HIGH

### [WARN] `_draw_pet_specials_submenu` same early-return bug
**File**: `src/game_render.py:3086-3090`
**What I see**: When `items` empty, renders "No specials unlocked" and returns. No ESC hint.
**Reproducer / when it triggers**: Pet without unlocked specials.
**Suggested fix**: As above.
**Confidence**: HIGH

---

## B. Hardcoded widths / unmeasured content

### [WARN] Combat HUD right-column at fixed x=320 collides with long monster names
**File**: `src/game_render.py:1670`
**What I see**: `rx = bx + 320` is hardcoded for the damage-preview column. The left column draws a monster-name HP line at `lx` with width unmeasured. For a 24+ char monster name (some uniques run "the Greater Spectral Knight of Caer Llion" or similar), `name_surf` blits into the right-column area and clobbers `dm_text` ("WEAKNESS!" / "RESISTED").
**Reproducer / when it triggers**: Combat against a unique monster with a long display name (boss-level monsters, named uniques from `monsters.json`).
**Suggested fix**: Either truncate the name surf to `(rx - lx - 8)` via `truncate_label`, or pre-measure the longest name and shift `rx` if needed.
**Confidence**: HIGH

### [WARN] Combat HUD HP bar width hardcoded at 260 — overlaps right column
**File**: `src/game_render.py:1656-1661`
**What I see**: `hb_w = 260`. The bar starts at `lx = bx + 22`, so its right edge is `bx + 282`. `rx = bx + 320` for the right column. That leaves only 38px of "gutter" — tight. At smaller window sizes (`bw < 600`) the right column squeezes left and the bar may overlap. Especially the right column row2 chain damage labels render at `row2_x = rx`.
**Reproducer / when it triggers**: Window resized to ~700px wide while in combat; also when right column gets wider chain mult digits like "x6:999".
**Suggested fix**: Compute `hb_w` as `min(260, rx - lx - 16)`.
**Confidence**: MEDIUM

### [WARN] Combat HUD effects row caps at 5 but doesn't measure
**File**: `src/game_render.py:1663-1667`
**What I see**: `effects[:5]` then `"  ".join(f"[{e}]" for e in effects[:5])` is rendered at `lx, hb_y + 16`. No truncation. A monster with 5 long effect names (`["paralyzed", "poisoned", "frostbite", "berserk", "marked"]`) renders ~120 chars at font_sm — about 720px. Even with the cap, this can bleed into the right column or past the panel.
**Reproducer / when it triggers**: Status-effect-rich boss combat.
**Suggested fix**: Wrap in `truncate_label(eff_text, rx - lx - 16, self.font_sm)`.
**Confidence**: MEDIUM

### [WARN] XYZZY input title not measured
**File**: `src/game_render.py:230-232`
**What I see**: "Speak the First Word" rendered centered with no width check against `bw = 520`. Today's title fits but if font_size scales (e.g. accessibility), the text will overflow the green panel.
**Reproducer / when it triggers**: Font size change.
**Suggested fix**: `truncate_label` against `bw - 60`.
**Confidence**: LOW

### [WARN] Sidebar `_status` lockpick name overflows
**File**: `src/ui.py:288-289`
**What I see**: `lp_text = f"Lockpick: {lp.durability}/{lp.max_durability}  [{lp.name}]"`. Rendered raw without `_fit()` truncation. Lockpick names from JSON (e.g. "ornate goblin pick", "elven masterwork lockpick") at font_sm can run past `SIDEBAR_W = 430`.
**Reproducer / when it triggers**: Carrying a verbose-named lockpick.
**Suggested fix**: Wrap the f-string in `self._fit(self._fsm, lp_text, self.w - self.PAD * 2)`.
**Confidence**: HIGH

### [WARN] Sidebar `_status` "[Hungry]"/"[Starving]" rendered with `_fbold` no truncation
**File**: `src/ui.py:267-278`
**What I see**: Fits today (text is short) but pattern is "render directly without `_fit()` against sidebar width." If a future status banner like "[Critically Wounded]" or similar gets added, it will overflow silently.
**Reproducer / when it triggers**: New status display text.
**Suggested fix**: Add `_fit` wrapper for consistency.
**Confidence**: LOW

### [WARN] Sidebar equipment label assumes 5-char fixed name slot
**File**: `src/ui.py:368-372`
**What I see**: `label_surf` measured fine, `max_name_w` computed correctly, name is `_fit`'d — good. But ammo suffix `iname += f" [{total} {ammo_type}s]"` is added BEFORE enchant suffix `+N` AND `{C}` cursed flag, all before the truncate. For a long ammo type like `iron tipped arrows` you get `"Crossbow [124 iron tipped arrowss] +3 {C}"` — gets `…`'d in the middle. The information lost is the enchant bonus, which is the part the user cares most about.
**Reproducer / when it triggers**: Enchanted ranged weapon with long-name ammo.
**Suggested fix**: Truncate the *base name* first, then append the metadata fields; if there's no room, drop the ammo count but keep the enchant.
**Confidence**: MEDIUM

### [WARN] Throw HUD label not truncated
**File**: `src/game_render.py:1255-1260`
**What I see**: `label_surf = self.font_sm.render(label, ...)` for messages like `f"{blocker.name} blocks the path! {item_name} will hit it instead."` Long monster + potion names produce 80+ char labels. Rendered with a black bg sized to `label_surf.get_width() + 16` — so the bg auto-stretches, but the surf can extend past `GAME_W` if items+monsters have long names.
**Reproducer / when it triggers**: Throwing a long-named potion at a long-named monster blocker.
**Suggested fix**: `truncate_label(label, layout.GAME_W - 32, self.font_sm)` before rendering.
**Confidence**: MEDIUM

### [WARN] Ranged HUD label same pattern
**File**: `src/game_render.py:1335-1340`
**What I see**: Same shape as throw HUD label — no truncation against game viewport. Long monster name produces a label wider than the screen.
**Reproducer / when it triggers**: Firing at a verbose-named boss.
**Suggested fix**: Same as throw HUD.
**Confidence**: MEDIUM

### [WARN] Confirm-exit subtitle width hardcoded 520
**File**: `src/game_render.py:3190`
**What I see**: `self._fit_text(sub, self.font_md, 520)` — hardcoded 520. But `bw = min(560, layout.GAME_W - 40)`, so on small windows the subtitle will overflow the panel. Should be `bw - 40`.
**Reproducer / when it triggers**: Window resized below 600px wide and user opens the exit menu.
**Suggested fix**: `self._fit_text(sub, self.font_md, bw - 40)`.
**Confidence**: MEDIUM

### [MINOR] Quirks screen progress bar position assumes 200px right gutter
**File**: `src/game_render.py:420-435`
**What I see**: Name truncated to `body.w - 220` then bar drawn at `body.right - 200`. If `body.w < 240`, name slot becomes ≤ 20px and renders as just "…". Visually broken but unlikely at default geometry (SIZE_LG = 1000 panel).
**Reproducer / when it triggers**: Heavily resized window.
**Suggested fix**: Floor the bar position: `bar_x = body.right - min(200, body.w // 3)`.
**Confidence**: LOW

---

## C. Paint-order / Z-order bugs

### [CRITICAL] `_draw_kit_panel` body content is hidden under the panel bg in early `PanelBuilder` versions of one path
**File**: `src/game_render.py:1805-1825`
**What I see**: `_draw_kit_panel` follows the correct PanelBuilder pattern (constructor paints bg, body content, then `p.draw()`). Confirmed working. But the `_draw_measured_table` helper draws cells at `(cx + left_pad, ry)` without first checking the body_rect against the helper-drawn-divider. Specifically: `draw_divider(self.screen, x, y + divider_y_offset, w)` on line 1905. If the caller's `y` parameter places the divider INSIDE the chrome region (`p.set_tabs` adds `TAB_BAR_H=32`), it can be drawn under the tab strip. (NOT a paint-order bug per se — but a body content escaping `body_rect()` upward into chrome space.) Today it's safe because `body_rect()` returns the rect below tabs. Leaving as MINOR.
**Confidence**: LOW (NOT a bug today; flagged as fragile)

### [WARN] `_draw_quirks_screen` calls `p.draw()` AFTER rendering body — good — but the body loop can extend past `body.bottom` because nothing stops it
**File**: `src/game_render.py:387-438`
**What I see**: `for idx in range(scroll, len(data))` loop checks `if y >= content_bot: break` at the top, but DOES `y += 16` and `y += ROW_H_LOCKED` increments WITHOUT a final check. The check inside `if unlocked:` (line 400, `if y + needed_h > content_bot`) catches multi-line entries; the locked-entry path (line 417) also breaks. OK, this is fine. **Withdrawing my initial flag** — kept on the list for transparency.
**Confidence**: LOW

### [WARN] Pet menu pet roster line overruns when 8 pets are present
**File**: `src/game_render.py:3013-3023`
**What I see**: Loop `for idx, pet in enumerate(items[:8])` blits at `y += 26`, then `y += 12 + divider + 12 = 36` plus per-action 28px × 6 = 168px. Total used = `by + 56 + 8*26 + 36 + 168 = by + 468`. Panel `bh = min(560, layout.WINDOW_H - 40)`. At default 900 windows: ok. At smaller: action rows can be obscured. Plus the hint line at `by + bh - 28`.
**Reproducer / when it triggers**: Player at max pet count (8) at smaller-than-default window.
**Suggested fix**: Either reduce pet roster lines or pre-measure total height.
**Confidence**: LOW

---

## D. Long item names / messages bleeding

### [CRITICAL] Equipment sidebar — fully identified item adds 4+ suffixes that can blow past truncation budget
**File**: `src/ui.py:347-372`
**What I see**: For a ranged weapon, `iname` builds as `base + ammo[N TYPEs] + enchant + cursed{C}` BEFORE the single `_fit()` call truncates the whole thing at `max_name_w` (~280px). The truncation will eat the enchant `+3` (the player-meaningful info) and leave the verbose `[124 silver tipped arrowss]` count. From a player-attention standpoint this is backwards: the enchant + curse status is what the player needs to see for combat decisions.
**Reproducer / when it triggers**: Any enchanted ranged weapon with named ammo. Very common late-game.
**Suggested fix**: Build suffix list, render `name + critical_suffixes` first, fall back to dropping the ammo suffix if truncation triggers.
**Confidence**: HIGH

### [WARN] Pet roster line in `_draw_pet_menu`
**File**: `src/game_render.py:3018-3022`
**What I see**: Line uses `self._fit_text(line, self.font_md, bw - 50)` which is good, but with a long pet name (player can type up to N chars in the name popup, no enforced cap visible), the truncation eats the trailing `[{cmd}]` info — the user can't see the pet's current command mode. Same UX failure as the sidebar equipment.
**Reproducer / when it triggers**: Player names a pet "Sir Galahad the Pure of Heart" or similar.
**Suggested fix**: Build line as `name_part + suffix_part` and prioritize suffix in truncation.
**Confidence**: MEDIUM

### [WARN] Pet specials submenu desc text not truncated/wrapped
**File**: `src/game_render.py:3099-3101`
**What I see**: `desc_surf = self.font_sm.render("    " + sp.get('desc', ''), True, FP.BODY_TEXT)`. No wrap, no fit. Specials descs from `pet_system.py` can be 80-120 chars (e.g. fire breath: "Cone of flame damaging all enemies in a 3-tile arc"). At font_sm width ~720px and `bw = min(700, …)` → ~50% chance of overflow.
**Reproducer / when it triggers**: View special attacks list for any pet with a long desc.
**Suggested fix**: `truncate_label` against `bw - 50`.
**Confidence**: HIGH

### [WARN] Shop merchant line truncates after composition — same pattern as equipment sidebar
**File**: `src/game_render.py:4178-4189`
**What I see**: `line = f"  {iname}  (wt:{wt:.1f})   {price} gold{tag}"`. Composed THEN `truncate_label(prefix + line, body.w - 8, ...)`. A long item name like a unique artifact eats the price field. The player needs to see the price to decide to buy — this is the worst possible truncation order.
**Reproducer / when it triggers**: Merchant carrying any verbose-named unique.
**Suggested fix**: Render columns separately: name left-fit to fixed width, price right-aligned, wt in middle. Use `_draw_measured_table` (already exists) or compute name truncation against `body.w - price_w - wt_w - prefix_w`.
**Confidence**: HIGH

### [WARN] Mystery approach requirements list — no truncation on `cost_desc`
**File**: `src/game_render.py:101-102`
**What I see**: `cost_desc = ', '.join(f"{s}{v}" for s, v in m['stat_cost'].items())`. If a mystery costs many stats (e.g. `{STR: -3, DEX: -2, INT: -1, WIS: -1}`), the joined string can run past `body.w - 8` at font_small.
**Reproducer / when it triggers**: Multi-stat-cost mystery encounters.
**Suggested fix**: Wrap via `wrap_lines` and render multi-line, or truncate.
**Confidence**: LOW (current mystery data is short, but JSON-driven)

### [WARN] Character sheet skips word-wrapped overflow check for `cur_w / max_w` color
**File**: `src/game_render.py:493-497`
**What I see**: Builds `f"  Weight: {cur_w:.1f} / {max_w}  ({pct*100:.0f}%)"` and appends to lines unwrapped. The wrap is applied per-line during render (`_wrap_text` at 673). OK — wrap handles it. Withdrawing.
**Confidence**: LOW

---

## E. Color contrast issues

### [WARN] Selected row bg `(40, 55, 110)` + FADED_TEXT detail color is low contrast
**File**: `src/fantasy_ui.py:974-975` and `:1013`
**What I see**: `bg_col = (40, 55, 110)` for selected rows. The FADED_TEXT `(165, 155, 185)` detail color sits at ~3.0:1 against this bg — below WCAG AA 4.5:1. The `BODY_TEXT` name color at `(218, 192, 145)` is fine (~5.4:1).
**Reproducer / when it triggers**: Any menu using draw_menu with a selected row — equip, kit, etc.
**Suggested fix**: When rendering a selected row, swap FADED_TEXT for a lighter shade like `(195, 185, 215)`.
**Confidence**: MEDIUM

### [WARN] Empty-slot dim `SLOT_EMPTY (140,140,165)` on dark-row bg pair
**File**: `src/ui.py:366-367`
**What I see**: SLOT_EMPTY is 4.7:1 on plain midnight (per FP comment). But the sidebar has no row-bg coloring, and the comment already addressed this. Withdrawing — actually OK.
**Confidence**: LOW

### [WARN] `(80, 168, 215)` shield color (`ITEM_COLOR['shield']`) is identical to `(80, 148, 215)` armor — undistinguishable in sidebar inventory
**File**: `src/fantasy_ui.py:632-633`
**What I see**: Shield = `(80, 168, 215)` vs Armor = `(80, 148, 215)` — only the G channel differs by 20. Visually indistinguishable. Was this intentional? In the sidebar inventory list these read as the same color.
**Reproducer / when it triggers**: Inventory listing with both armor and shields.
**Suggested fix**: Pick a more distinct shield hue, e.g. cyan-leaning steel `(80, 200, 215)`.
**Confidence**: MEDIUM

### [WARN] Hint screen body text vs LORE_GOLD_BODY contrast
**File**: `src/game_render.py:4437`
**What I see**: `FP.LORE_GOLD_BODY (230, 215, 180)` rendered on `FP.MIDNIGHT (14, 18, 48)`. That's ~13:1 contrast — fine. But the stars row at `FP.LORE_GOLD_STAT (200, 170, 90)` is ~7:1, also fine. No issue here.
**Confidence**: LOW (no actual bug, kept for transparency)

### [WARN] Quirks unlocked row has bare title + bare badge — readable on plain panel, but no row-bg differentiation
**File**: `src/game_render.py:402-415`
**What I see**: Unlocked entries use GOLD_BRIGHT name, PARCHMENT_LIGHT effect, FADED_TEXT trigger. All readable on the plain midnight panel. No bg color = no contrast issue. OK.
**Confidence**: LOW (no bug, kept for transparency)

### [MINOR] Wand menu charge color uses `DANGER_TEXT_LIGHT` for 0-charge entries — but the entry is renderable still (the player can pick it). Visual feedback says "broken" but mechanically the wand is just empty.
**File**: `src/game_render.py:2479`
**What I see**: Semantic mismatch — 0 charges isn't an error, it's a state. Use FADED_TEXT (greyed) instead of DANGER_TEXT_LIGHT (red).
**Confidence**: LOW

---

## F. Inconsistent padding / gutters

### [MINOR] Footer Y offset differs between panels — `bh - 28` vs `bh - 30` vs `bh - 34`
**File**: multiple — `_draw_pet_menu:3058`, `_draw_pet_specials_submenu:3103`, `_draw_pet_sub_picker:3138`, `_draw_review_missed:3764`, `_draw_judgment:932`, etc.
**What I see**: Footer hint y is computed as `by + bh - N` where N ranges 22-40 across functions. Visually drifts slightly between modals.
**Suggested fix**: Adopt the PanelBuilder pattern (`FOOTER_HINT_H = 28`) everywhere.
**Confidence**: LOW

### [MINOR] Confirm/exit/abandon dialogs use inconsistent padding above options
**File**: `_draw_confirm_exit:3201` (`oy = by + 112`), `_draw_exit_quest:3228` (`oy = by + 100`), `_draw_abandon_quest:3255` (`oy = by + 100`)
**What I see**: Confirm-exit puts options 4px lower than the other two — visually inconsistent for siblings.
**Suggested fix**: Standardize on `by + 100`.
**Confidence**: LOW

### [MINOR] `_draw_chicken` option row gap inconsistent with `_draw_confirm_exit` family
**File**: `src/game_render.py:3286`
**What I see**: chicken uses `oy += key_surf.get_height() + 16`, confirm-exit uses `+ 6`, exit-quest uses `+ 8`. Same dialog family, three different gaps.
**Suggested fix**: Pick one.
**Confidence**: LOW

---

## G. State-dependent rendering

### [CRITICAL] `_draw_pet_feed_submenu` / `_draw_pet_heal_submenu` / `_draw_pet_specials_submenu` draw OVER `_draw_pet_menu` but assume pet menu chrome is already drawn
**File**: `src/game_render.py:1044-1052` (state dispatch) + the submenu draws
**What I see**: The dispatch correctly draws pet menu first, then submenu on top. But `_draw_pet_menu` early-returns at line 3011 if `items` is empty. If the player somehow gets into `STATE_PET_FEED` without pets (e.g. last pet died mid-menu), the parent draw aborts and only the submenu chrome renders — meaning no underlying menu, and the submenu has no clear "back to pet menu" context. Edge case but reproducible.
**Reproducer / when it triggers**: Pet dies between `STATE_PET_FEED` input handling and next frame.
**Suggested fix**: Either guard the state transition (auto-return to STATE_PLAYER if no pets), or ensure the empty-pet branch still draws full panel chrome.
**Confidence**: MEDIUM

### [WARN] `_draw_quiz` assumes `qe.current_question` exists or no-ops; `_draw_celebration` assumes `qe.celebrating`
**File**: `src/game_render.py:1351-1359`
**What I see**: The early-return at `if not qe.current_question` leaves screen with no visible quiz panel — but state is still STATE_QUIZ. Game world from `render()` is visible (good) but no input prompt visible to user. Could feel "frozen" for the frame between quiz start and first question population.
**Reproducer / when it triggers**: Race condition between state transition and quiz_engine question load.
**Suggested fix**: Render a "Preparing question..." placeholder.
**Confidence**: LOW

### [WARN] Story popup: code-block reward renders even if `code` field is empty string ("")
**File**: `src/game_render.py:3358`
**What I see**: `if code:` — falsy on empty string, so OK. But `code = d.get('code')` will return None if absent; OK. Net: no bug. Withdrawing.
**Confidence**: LOW

---

## H. Quiz overlay specifics

### [WARN] `_draw_quiz` timer ratio computation can divide by zero in edge state
**File**: `src/game_render.py:1462`
**What I see**: `ratio = max(0.0, qe.time_remaining / max(1, qe.timer_seconds))` — safe. OK.
**Confidence**: LOW (no bug, transparent)

### [WARN] Choice card text uses pre-wrapped `c_wrapped` but each card height is `max(52, max_c_lines * c_line_h + 20)` — wastes space when other cards are short
**File**: `src/game_render.py:1407`
**What I see**: All 4 cards share the same height (`ch_height`), which is the height of the LONGEST card's wrapped text. For asymmetric content (1 long answer, 3 short answers), 3 cards have a lot of empty vertical space. Cosmetic, not a bug.
**Suggested fix**: Render each card with its own height OR center text vertically within the unified height (which `draw_choice_button` already does — confirmed at line 734). OK, no bug.
**Confidence**: LOW (no bug, kept for transparency)

### [WARN] Quiz status text uses `*` symbols in feedback text
**File**: `src/game_render.py:1532`
**What I see**: `fb_text = "*  CORRECT!"` — ASCII asterisk. The user's earlier feedback (commits in history) used `[*]` / `[ ]` for ASCII compat. This is just `*` and renders fine in Consolas. Withdrawing.
**Confidence**: LOW

### [WARN] Timer pip indicator overlaps the timer bar on very short bars
**File**: `src/game_render.py:1450-1460`
**What I see**: `pip_cx0 = bar_x + pip_r`, then `bar_x += tier_offset` (= `5*pip_gap + 8 = 73px`). At default `bw = 1060`, `bar_w = 1060 - 48 = 1012`, after offset `bar_w = 939`. Plenty of room. But at minimum `bw = layout.GAME_W - 40 = 1240 px` window — also fine. Edge case: window <300px wide breaks the bar. Below practical reproducer threshold.
**Confidence**: LOW

### [WARN] `_draw_celebration` headline text not measured against window width
**File**: `src/game_render.py:1612-1620`
**What I see**: `cel_text = qe.celebration_text` rendered with font_xl (42pt) at position centered. `qe.celebration_text` defaults to "PERFECT CHAIN!" or similar — fine. If extended to longer text in future builds, no fit/wrap protection.
**Suggested fix**: Pre-fit via `truncate_label(cel_text, layout.WINDOW_W - 80, cel_font)`.
**Confidence**: LOW

---

## I. Targeting overlays

### [WARN] Melee targeting label has no label render
**File**: `src/game_render.py:1135-1175`
**What I see**: Unlike ranged and throw targeting (which draw bottom HUD labels with key hints), melee targeting draws ONLY the reach tiles and cursor — no `"MELEE [ENTER=attack ESC=cancel]"` instruction. Per inputs the user needs to know what keys do what. This is a missing affordance vs the other two targeting modes.
**Reproducer / when it triggers**: Player invokes melee targeting (A key with multiple adjacent enemies).
**Suggested fix**: Add the same bottom-strip HUD label as `_draw_ranged_targeting:1335-1340`.
**Confidence**: HIGH

### [WARN] Throw / ranged HUD draws label at `GAME_H - height - 12` but doesn't account for MSG_H
**File**: `src/game_render.py:1259-1260`, `:1339-1340`
**What I see**: `layout.GAME_H` is the game viewport height (700). Drawing at `GAME_H - h - 12` places the label right above the message log. That's intentional — it lives inside the game viewport. OK, no bug. But the message log is at `y = GAME_H, h = MSG_H` so first messages are 16px below the label. Visually crowded, but functional.
**Confidence**: LOW (no bug, transparent)

### [WARN] Cursor highlight skipped at viewport edge — user can't see cursor when targeting far corner
**File**: `src/game_render.py:1172-1175` (melee), `:1232-1235` (throw), `:1316-1319` (ranged)
**What I see**: `if 0 <= scr_cx < layout.GAME_W and 0 <= scr_cy < layout.GAME_H:` — the cursor is NOT drawn when off-screen. But the player can still move the cursor off-screen and a successful target there will fire correctly. The user gets no visual feedback. Mostly a problem at low zoom or with wide-reach weapons.
**Reproducer / when it triggers**: Throw potion or long-reach ranged from corner of dungeon.
**Suggested fix**: Clamp cursor draw to screen edge with an arrow/indicator pointing off-screen toward the cursor location.
**Confidence**: MEDIUM

---

## J. Combat HUD specifics

### [WARN] Chain damage table assumes max 6 entries — older weapons have more
**File**: `src/game_render.py:1687,1700`
**What I see**: `for i, mult in enumerate(mults[:6])` caps at 6. Row1 takes first 3, Row2 takes parts[3:]. Some weapons in `weapons.json` define `chain_multipliers` of length 5 or 8 — the 5-length renders 3+2, the 8-length silently drops 7 and 8. Player loses information about late-chain damage.
**Reproducer / when it triggers**: Combat with a high-tier weapon that has 7+ chain multipliers.
**Suggested fix**: Either wrap to 3 rows or change cap to display all. Better: pre-measure and shrink font if needed.
**Confidence**: MEDIUM

### [WARN] Chain damage heat color formula clips for `max_dmg == 1`
**File**: `src/game_render.py:1690-1697`
**What I see**: `max_dmg = max(d for _, d in parts) or 1`. Safe. But when all dmg values are similar (e.g. mults are [0.5, 1.0, 1.0, 1.0, 1.0]) all heat values cluster near 1.0 and all entries render the same color. Cosmetic — no info loss.
**Confidence**: LOW (no bug)

### [WARN] Weapon name in HUD truncated to ?
**File**: `src/game_render.py:1708-1711`
**What I see**: `w_name = weapon.name if weapon else "bare hands"`. Rendered with no truncation against right column width. Long weapon names extend past the panel.
**Reproducer / when it triggers**: Equipping a long-named unique weapon in combat.
**Suggested fix**: `truncate_label(w_name, bw - rx - 24, self.font_sm)`.
**Confidence**: MEDIUM

---

## K. Sidebar / message log specifics

### [WARN] Message log fade math at edge: 35% min could be too dim on midnight
**File**: `src/ui.py:71-73`
**What I see**: `fade = max(0.35, 1.0 - age * 0.09)`. After 8 messages, fade clamps to 0.35. For BODY_TEXT (218, 192, 145) the faded version is (76, 67, 50) → ~2.3:1 contrast on MIDNIGHT (14, 18, 48). Below WCAG AA. Old messages are intentionally less prominent, but at 2.3:1 they're functionally unreadable.
**Reproducer / when it triggers**: Any time message log fills past ~8 entries.
**Suggested fix**: Bump min fade to 0.55 (4.5:1 contrast).
**Confidence**: HIGH

### [WARN] Sidebar status effect grid overflows when 6+ effects active
**File**: `src/ui.py:306-319`
**What I see**: `for i, (eid, val) in enumerate(active):` no slice cap. With 8 active effects (paralyzed, poisoned, blinded, slowed, berserk, marked, dazed, confused) at `(i // 2) * 22 = 88px` extra height — pushes sidebar past available screen.
**Reproducer / when it triggers**: Late-game status-storm — e.g. cursed amulet pile.
**Suggested fix**: Cap at e.g. `[:8]` and append "+N more" indicator.
**Confidence**: MEDIUM

### [WARN] Sidebar `_inventory` letters block — uses `cname` from `_cap(raw_name)` BEFORE adding `x{count}` suffix
**File**: `src/ui.py:421-431`
**What I see**: `display = f"{cname} x{count}" if count is not None else cname` then `display = self._fit(...)`. Same anti-pattern as equipment slot: long item names truncate AFTER count is added, possibly hiding the count.
**Reproducer / when it triggers**: Stacked item with verbose name (e.g. `100 silver-tipped arrows`).
**Suggested fix**: Truncate base name first, append count, then re-truncate as safety.
**Confidence**: MEDIUM

---

## L. Other findings

### [WARN] `_draw_review_missed` `q['chosen']` and `q['correct']` are wrapped but lines don't break inside the loop
**File**: `src/game_render.py:3736-3744`
**What I see**: The inner loops do NOT check `y > bh - footer`. Long answer strings (some philosophy answers are 80+ chars and wrap to 3-4 lines) can push past `by + bh - 30` where the hint sits.
**Reproducer / when it triggers**: Reviewing a missed philosophy question with long choices.
**Suggested fix**: Add `if y + 22 > by + bh - 40: break` inside each line loop.
**Confidence**: MEDIUM

### [WARN] `_draw_lore_screen` stat_lines truncates without clear UX
**File**: `src/game_render.py:4044-4059`
**What I see**: When stat lines overflow the top 55% of body, a `"  ... N more line(s)"` indicator is appended at the bottom. Good. But the indicator is rendered at `stat_y` which has already been incremented past `stat_bottom`. If `skipped_lines > 0` the indicator overlaps with the lore section header below it.
**Reproducer / when it triggers**: Looking at lore for a weapon with many specials (long Type/Material/Special/Resistances chains).
**Suggested fix**: Reserve a fixed line at the bottom for the "N more" indicator, or render it before the divider line.
**Confidence**: MEDIUM

### [WARN] `_draw_encyclopedia` entry detail uses `self._wrap_text(line, ..., bw - 44) or [line]` fallback
**File**: `src/game_render.py:4328`
**What I see**: `or [line]` fallback rendering. If `_wrap_text` returns `['']` for empty input, the loop still runs once and blits empty surface at advancing y. Cosmetic only.
**Confidence**: LOW

### [WARN] Encyclopedia entry detail lore_lines wraps but no overflow break
**File**: `src/game_render.py:4341-4347`
**What I see**: `if y + self.font_sm.get_height() > by + bh - 40: break` IS in the loop. Good. No issue.
**Confidence**: LOW (transparent, no bug)

### [WARN] `_draw_help_screen` description truncation gives only 1 column width minus 170px for keys
**File**: `src/game_render.py:4612-4617`
**What I see**: `desc_max_w = col_w - 170`. With `col_w = (bw - 40) // 2 = 480`, desc gets 310px. The long help descriptions like "(weapons / armor / shields / accessories)" at 38 chars × ~7px = 266px — barely fits. Anything shorter columns (smaller window) will silently ellipsis essential info.
**Reproducer / when it triggers**: Smaller windows.
**Suggested fix**: Use the right column instead of always-cutting. Or split key label width adaptively.
**Confidence**: MEDIUM

### [WARN] `_draw_xyzzy_confirm` Y/N buttons rendered at fixed offsets, no truncation guard
**File**: `src/game_render.py:289-299`
**What I see**: `bx_btn = bx + bw // 2 - 120 + i * 160`. If user has a custom font where `[ YES ]` is wider than ~80px, the button highlights at `(bx_btn - 10, btn_y - 4, 100, 32)` won't fit. Cosmetic edge case.
**Confidence**: LOW

### [WARN] `_draw_qa_warp_popup` subtitle rendered with font_md — but font_md is the larger one (26pt)
**File**: `src/game_render.py:2983-2985`
**What I see**: Subtitle "Enter a floor number (1-100):" at font_md is 24pt body — fairly large for a subtitle. Other popups use font_sm for subtitles. Cosmetic inconsistency.
**Confidence**: LOW (cosmetic)

### [WARN] Discoveries panel section header line bottom-y crash on `body.right - 8`
**File**: `src/game_render.py:2364-2367`
**What I see**: `pygame.draw.line(self.screen, FP.GOLD_DARK, (body.x, ly + 18), (body.right - 8, ly + 18), 1)`. `body.right` is the right edge of body_rect — drawing a 1px line is safe.
**Confidence**: LOW (no bug, transparent)

### [WARN] Story popup `code_label` and `code_val` y misalignment
**File**: `src/game_render.py:3367-3368`
**What I see**: `self.screen.blit(code_label, (lx, y))` and `self.screen.blit(code_val, (lx + code_label.get_width(), y - 3))`. The `y - 3` offset is to align baselines of font_md (26) and font_lg (32). The actual baseline difference at those sizes is ~6-8 px, so `-3` is half-tuned. Looks slightly off.
**Suggested fix**: Use baseline calculation `code_label.get_height() - code_val.get_height()`.
**Confidence**: LOW (cosmetic)

### [WARN] Empty stat_lines after skipping in lore screen renders an unhelpful "..." with no skip count UX
**File**: `src/game_render.py:4055-4059`
**What I see**: When `skipped_lines > 0` and `stat_y` has overflowed the budget, the "N more line(s)" indicator renders at `stat_y` which is already past `stat_bottom`. Visually overlaps the divider.
**Reproducer / when it triggers**: Verbose weapon/monster lore at level 3+ where many stat fields populate.
**Suggested fix**: Render indicator at `stat_bottom - line_h` instead of `stat_y`.
**Confidence**: MEDIUM

### [WARN] `_draw_pet_name_popup` subtitle uses `f"…name?"` with no truncation
**File**: `src/game_render.py:3157-3159`
**What I see**: Fine today. No bug.
**Confidence**: LOW (transparent)

### [WARN] Pet roster `pet.command` mapping defaults to `'return'` if unknown — silent eat of invalid state
**File**: `src/game_render.py:3040-3041`
**What I see**: Not a render bug; flagging for the spawn-task list.
**Confidence**: LOW (not a render bug)

### [WARN] `_draw_throw_targeting` HUD label "Out of throw range" uses hardcoded reach value
**File**: `src/game_render.py:1249`
**What I see**: `label = f"Out of throw range ({reach} tiles)  [ESC=cancel]"`. Fine.
**Confidence**: LOW (no bug)

### [WARN] `_draw_cook_menu` does not pass `subtitle_color` consistently
**File**: `src/game_render.py:2762-2763`
**What I see**: `subtitle=f"SP: {sp}/{self.player.max_sp}", subtitle_color=sp_color`. Consistent. OK.
**Confidence**: LOW (no bug)

### [WARN] `_draw_cook_menu` compound recipe icon proxy never sets `.name` — `_draw_menu_icon` reads `getattr(item, 'symbol', '?')` and `getattr(item, 'color', ...)` — but `_get_menu_sprite(item.id)` may return None for recipe sprites that don't exist
**File**: `src/game_render.py:2710-2719`
**What I see**: Falls back to `first_ing` lookup, then to glyph. Functional, but the glyph symbol `*` and color `[110, 220, 100]` is identical across all recipes — no visual differentiation. Cosmetic.
**Confidence**: LOW

### [WARN] `_draw_drop_gold_input` uses `layout.GAME_H` for vertical center, but the rest of the inputs use `layout.WINDOW_H`
**File**: see Finding under section A above (`drop-gold panel doesn't use WINDOW_H`).
(Duplicate — already counted.)

### [WARN] `_draw_quirks_screen` `ROW_H_LOCKED = 30` plus unlocked rows of variable height — scroll math indexes by row not by pixel
**File**: `src/game_render.py:383-385`
**What I see**: `max_scroll = max(0, len(data) - 1)` — allows scrolling past the end of useful entries. Adjusting `_quirks_scroll = scroll` (line 385) sets it before clamping to actual visible window. Edge: pressing Down many times can scroll to a state where only the last entry shows.
**Suggested fix**: Compute max_scroll properly based on visible entry heights.
**Confidence**: LOW (UX nit, not a render bug)

---

## Summary

Total findings: **72**.
By severity:
- **CRITICAL**: 4 (cow desc overflow, equip sidebar suffix truncation order, combat HUD monster name collision against fixed-x right column, pet feed/heal/specials state assumes pet-menu chrome but parent may early-return)
- **WARN**: 63 (the bulk — text rendered without a `truncate_label`/`fit_text` safety net, suffix-vs-base composition order, footer-hint-after-early-return, etc.)
- **MINOR**: 5 (cosmetic spacing / palette nits)

Note: WARN dominates because most missing safety nets are not breaking *today's* content but WILL break the moment someone writes a longer name / a more elaborate JSON entry / resizes the window. The CRITICAL bucket is reserved for issues a player will see at default geometry on shipped data.

Top-priority cleanups (high-confidence, user-visible):
1. `_draw_combat_hud` monster-name truncation against `rx - lx - 8` (line 1654).
2. Sidebar equipment suffix-before-truncate ordering (`src/ui.py:347`).
3. Pet menu / pet feed / pet specials submenu — all three early-return without rendering the footer hint (`game_render.py:3011, 3090, 3124`).
4. Drop-gold popup uses `GAME_H` not `WINDOW_H` (`game_render.py:4091`).
5. Shop merchant truncation eats the price field (`game_render.py:4187`).
6. Sidebar lockpick text not `_fit()`'d (`ui.py:288-289`).
7. Message log fade min 0.35 → contrast 2.3:1 on midnight (`ui.py:72`).
8. Melee targeting has no key-hint HUD label.

Patterns / discipline rules suggested for future drawing:
- ALWAYS truncate base name BEFORE appending modifier suffixes (enchant, count, etc.). Suffixes carry the player-meaningful info; let the name eat the ellipsis.
- ALWAYS render the footer hint unconditionally — never inside a branch that early-returns.
- Center popups in `WINDOW_H`, not `GAME_H`. The drop-gold popup is the lone exception today.
- For per-frame draws that compose a full line then truncate, prefer the `_draw_measured_table` column pattern.
