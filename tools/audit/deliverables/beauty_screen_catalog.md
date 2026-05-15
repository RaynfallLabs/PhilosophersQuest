# BEAUTY — Screen Catalog

**Audit date:** 2026-05-15
**Audit mode:** Code-only. The harness cannot run pygame. All visual outcomes are *inferred from draw code*, not from screenshots. Where a strong visual claim depends on rendered output, it is flagged "inferred".

**Game aesthetic identity** (target): *"high-fantasy medieval / arcane grimoire UI theme"* — `src/fantasy_ui.py:2`.

The theme is implemented in `src/fantasy_ui.py`:
- **Palette (`FP`)**: parchment / antique gold / midnight blue / burgundy / arcane purple. Semantic aliases (`PANEL_BG`, `PANEL_BORDER`, `BODY_TEXT`, `HINT_TEXT`, `DANGER_TEXT`, `SUCCESS_TEXT`, `WARNING_TEXT`, `LOOT_TEXT`).
- **Primitives**: `draw_panel` (parchment-textured, gold double border + corner flourishes + mid-edge diamonds), `draw_dark_panel` (midnight bg + gold border + same flourishes), `draw_header_bar` (two-tone midnight strip with mid-edge diamonds), `draw_divider` (gold line with center diamond), `draw_filigree_bar`, `draw_rune_circle`, `draw_candle_glow`, `draw_choice_button`, `draw_menu` (universal scrollable menu — used by 12+ screens).
- **Fonts (`get_font`)**: roles `title`/`heading` → Cinzel TTF; `body`/`small`/`mono` → Consolas SysFont (deliberately, per code comment); `gothic` → UnifrakturMaguntia TTF; `italic` → IM Fell English Italic TTF.

> **CRITICAL FONT ISSUE** — Found during catalog inspection: `assets/fonts/` directory **does not exist** in the repo (verified by directory listing). `fantasy_ui.py:140-147` silently falls back to `pygame.font.SysFont('garamond,palatino linotype,palatino,georgia,book antiqua,times new roman,consolas')` when the TTF is missing. Whether the title font is Cinzel (the intended display blackletter-flavored serif) or just Garamond/Times depends entirely on what's installed on the player's machine. The "arcane grimoire" type rendering is therefore unverifiable from code and likely under-realized. Flagged as `beauty-missing-fonts`.

> **MISSING PARCHMENT TEXTURE** — `fantasy_ui.py:208-219` tries to load `assets/textures/parchment.png` and falls back to the procedural `make_parchment`. The `assets/textures/` directory does not exist. So every parchment panel is the procedural variant — fine, but inferred.

---

## Screen inventory

Numbering for cross-reference in findings.

### 1. Welcome / title screen
- **File / class:** `src/welcome_screen.py:258` `WelcomeScreen`
- **Background:** procedural stone-block tilemap (`welcome_screen.py:306-321`), `(4,5,14)` fill + `48px` block grid with mortar lines — **inline EGA-style draw, NOT a grimoire primitive**.
- **Hero composition:** rotating 6-arm vortex (`_draw_vortex` line 554) + 12 domain icons arranged in a ring (`_draw_domain_ring` line 434) + central pulsing Octagon gem (`_draw_stone` line 584). Comment at line 599 explicitly calls this **"EGA diamond feel"** and line 450 calls the icon panel **"EGA-style bordered box"** with "classic 90s bevel".
- **Domain icon colors** (`_DOMAINS` line 266): pure EGA-bright palette — `(85,255,255)`, `(85,255,85)`, `(255,85,85)` etc. — **not** the FP grimoire palette.
- **Title banner:** uses grimoire primitives (`draw_panel` + `draw_filigree_bar` + `centered_text`) — line 633.
- **Name input:** uses grimoire primitives (`draw_panel` + `draw_header_bar`) — line 648.
- **Leaderboard panel** (right side, line 684): semi-transparent `(6,4,18,215)` fill with `GOLD_DARK` 1px border, `border_radius=6` — **rolled inline**, does not use `draw_dark_panel`.
- **All-time top-100 overlay** (line 766): same — raw `pygame.draw.rect` chrome, `border_radius=8`.
- **God-prompt popup** ("Did you mean, 'Dad'?", line 409): hardcoded `(12,10,25)` bg + `(200,170,80)` border — **rolled inline**, ignores `FP`/`draw_panel`.
- **Footer hint** (line 667): uses `FP.HINT_TEXT`. Version number renders in `(60,58,70)` — a near-invisible dark grey, *not* a `FP` color.
- **Fonts used:** `font_xl=title 52 bold`, `font_lg=heading 32`, `font_md=body 20`, `font_sm=body 15`, `font_icon=symbol 26`, `font_tiny=body 12`.
- **Tonal register:** "EGA / 90s adventure-game vortex" by self-admission. **Clashes with the rest of the game's grimoire theme.**

### 2. Character creation
- **Doesn't exist as a separate screen.** Name entry on the welcome screen *is* the build picker — typing a name in `SECRET_BUILDS` (`welcome_screen.py:34-255`) selects that build, otherwise default stats are used. A `[*] SECRET BUILD ACTIVE!` badge appears below the input (line 663). There's no stat-roll UI, no class picker.
- **Note:** Most `_sprite` entries in `SECRET_BUILDS` reference player sprites that **do not exist on disk**. Only `player.png`, `player_ash_ketchum.png`, `player_ash_williams.png`, `player_ciri.png`, `player_geralt.png`, `player_wizard_f.png` exist. Sprites referenced but missing include `player_aristotle`, `player_socrates`, `player_plato`, `player_nietzsche`, `player_pythagoras`, `player_prometheus`, `player_diogenes`, `player_achilles`, `player_leonidas`, `player_alexander`, `player_theseus`, `player_hermes`, `player_odysseus`, `player_merlin`, `player_ranger`, `player_dad`, `player_robyn`. `renderer.py:253` falls back silently to the default `player.png`. (Flagged as `beauty-missing-secret-sprites`.)

### 3. Dungeon main view — sidebar
- **File / class:** `src/ui.py:78` `Sidebar`
- **Background:** `FP.MIDNIGHT` rect + `FP.GOLD_DARK` left border, 2px wide (line 108-109). **Consistent.**
- **Section headers** (`_header` line 122): `FP.MIDNIGHT_MID` bg strip, 24px tall, `FP.GOLD_BRIGHT` text. **No flourish / no diamonds** — does NOT use `draw_header_bar` (which is the global header primitive for panels).
- **Bars** (HP/SP/MP, line 132): `(18,18,30)` dark slot + per-bar accent color (`(185,42,42)` HP red, `(50,85,205)` MP blue, dynamic SP). `border_radius=3`. **Raw inline draw — does NOT use FP semantic colors for the bars themselves**, just hardcoded RGB. Layout dimensions hardcoded.
- **Attribute grid** (line 175): 3-column with `FP.GOLD_BRIGHT/BODY_TEXT/DANGER_TEXT` based on stat value. Consistent.
- **Status section** (line 195): "AC / Level / Turns / Gold / Sight / Timer / Picks / Spells / Prayer / Lore / Hunger / Lockpick / passives / status effects". Each status line picks its own ad-hoc color. Examples of drift:
  - Prayer cooldown: `(140,100,200)` "arcane purple" inline (not `FP.ARCANE`).
  - Lore cooldown: `(80,160,200)` "teal" inline.
  - Lore ready: `(120,200,240)` (different from the cooldown teal).
  - "Fire Protect": `(245,150,60)` inline.
  - "Manifest": `(200,170,240)` inline.
  - "Death Ward": `(220,220,255)` inline.
- **Equipment slot list** (line 319): empty slot shown as `(52,52,70)` em-dash, equipped item as `FP.GOLD_PALE`. Consistent.
- **Inventory** (line 378): item colors from `ITEM_COLOR` dict (`fantasy_ui.py:525-539`). Consistent.
- **Visual hierarchy issue:** Death-pursuit state has NO sidebar indicator. The Death-chase is in the message-log only (see Screen 25). (Flagged as `beauty-death-chase-invisible`.)
- **Fonts:** `body 20` regular and bold, `heading 19` for section headers.

### 4. Dungeon main view — message log
- **File / class:** `src/ui.py:21` `MessageLog`
- **Background:** `FP.MIDNIGHT` rect + `FP.GOLD_DARK` 1px top border (line 53-54). Consistent.
- **Color mapping** (line 9-15): tag `'info'`→`FP.BODY_TEXT`, `'success'`→`FP.SUCCESS_TEXT`, `'warning'`→`FP.WARNING_TEXT`, `'danger'`→`FP.DANGER_TEXT`, `'loot'`→`FP.LOOT_TEXT`. **Centralized — the one location where the tag→color contract is correct.**
- **Fade behavior:** older messages fade toward zero with `fade = max(0.35, 1.0 - age*0.09)` — fine.
- **Font:** `body 20`. 60 max entries.

### 5. Dungeon main view — map / tile renderer
- **File / class:** `src/renderer.py:68` `Renderer`
- **Background:** black `_UNEXPLORED=(0,0,0)`. Visible/explored tiles use sprite from `assets/tiles/env/{name}.png` if present, else fall back to `_VISIBLE`/`_EXPLORED` color tables (line 31-62) with raw `pygame.draw.rect`.
- **Tile colors** are hardcoded RGBs **completely outside the FP palette system**. Floor `(60,55,50)` is brown-grey; wall `(130,130,140)` is cool blue-grey. These are independent of any grimoire palette decision.
- **Special-tile effects** (line 194-210): lava red-channel pulse, water blue shimmer. **Hardcoded magic numbers.**
- **Player draw** (line 249): tries `player_{name}.png` from secret build; falls back to `player.png`, then to a white square.
- **Entity draw** (line 261): monster sprite or color fallback square. Optional `tint` overlay for pets / sketches.
- **Death special-case** (`game_render.py:1044-1052`): pale spectral pulse `(200+55*pulse, 200+55*pulse, 255)` only on Death's tile, when in FOV. **The only Death-chase-specific visual.**
- **Abyssal Shimmer** (`game_render.py:1029-1042`): pulsing violet glow — brighter when activated. The visual cue for the secret victory ritual.
- **Inferred:** Tile aesthetic depends entirely on the 516 monster sprites and 1550 item sprites. Style coherence across that asset base is not audited from code alone — sprites are generated artwork.

### 6. Quiz panel (centerpiece)
- **File:** `src/game_render.py:1382` `_draw_quiz`
- **Overlay:** `(0,0,0,190)` SRCALPHA fill.
- **Panel:** `draw_dark_panel(border_color=accent)` where `accent` is `_SUBJECT_COLOR[subject]` — uses the FP subject palette. **Consistent grimoire chrome.**
- **Header:** `draw_header_bar` with accent-tinted bottom separator. Consistent.
- **Tier pips** (line 1469-1481): 5 small circles, filled if `i < qe.tier`. Subject-color fill / dim outline.
- **Timer bar** (line 1483-1503): `(28,10,10)` dark slot + green/amber/red fill with hardcoded thresholds, `border_radius=4`, 5 black tick marks. **Inline raw bar — not a shared primitive.**
- **Question text** (line 1505-1510): `(255,245,210)` parchment-ish but NOT `FP.PARCHMENT_LIGHT (242,222,182)` or `FP.VELLUM (250,235,200)`. Close but ad-hoc.
- **Choice cards (2×2 grid, line 1521-1570):** completely custom chrome — `pygame.draw.rect` with `border_radius=7`, dark `(0,0,0)` shadow rect, bevel highlights via `min(255, v+40)` on top/left edges. **This is a different visual language from `draw_dark_panel`** — modern-button bevels vs. medieval ornamental flourishes.
- **Important:** `fantasy_ui.py:546` defines `draw_choice_button` — an "ornate answer-choice button" with rune-stone styling. **The quiz does NOT use it.** It rolls its own card style.
- **Result feedback** (line 1575-1582): "* CORRECT!" / "* WRONG!" using `font_lg`. The asterisk-asterisk decoration is a placeholder for what was presumably meant to be a symbol/glyph.
- **Status hint** "Press 1 2 3 4 to answer" uses `(90,85,130)` inline (not `FP.HINT_TEXT (170,165,215)`).
- **Combat HUD** (line 1618 `_draw_combat_hud`): inline HP bars, chain damage table, weakness/resist labels with heat-colored numeric output. Uses lots of hardcoded colors `(220,185,140)`, `(60,40,40)`, etc.
- **Padding/sizing:** `bw = min(1060, GAME_W - 40)`, `PAD = 24`. Header 42, timer 28, status 36, combat 110.
- **Tonal register:** mostly grimoire, but **the choice cards and timer bar are visually closer to modern flashcard apps** than to medieval grimoire.

### 7. Quiz celebration screen (MAX CHAIN)
- **File:** `src/game_render.py:1588` `_draw_celebration`
- **Background:** pure black `(0,0,0)` full screen + warm `(80,55,0)` SRCALPHA pulsing wash.
- **Text:** `font_xl` headline with shadow + sub-line "PERFECT COMBO!" in `(180,255,180)`.
- **No grimoire chrome.** No rune circles, no candle glow, no filigree. Just text on black with a yellow wash. **Visually orphaned from the rest of the game.**
- **Tonal register:** arcade victory ("PERFECT COMBO!") — clashes with the Cormac-McCarthy chronicle voice.

### 8. Equip / Unequip menu
- **File:** `src/game_render.py:1701` `_draw_equip_menu`
- Uses `draw_menu` (universal). `border_color=FP.GOLD`. Tabs from `_EQUIP_TABS`. Icon rows with item sprites.
- Consistent grimoire chrome.

### 9. Accessory equip menu — `_draw_accessory_menu` (line 1777). `draw_menu`, `border_color=FP.GOLD`. Subtitle shows `4/4` slot count. Consistent.

### 10. Wand zap menu — `_draw_wand_menu` (line 1807). `draw_menu`, `border_color=FP.ARCANE_BRIGHT` (signals magic). Charge counts color-coded. Consistent.

### 11. Spell cast menu — `_draw_spell_menu` (line 1840). `draw_menu`, `border_color=FP.ARCANE_BRIGHT`. Tier-colored detail text. Inline `_SpellIcon` proxy class for icon. Badges show MP cost. Consistent.

### 12. Scroll / spellbook read menu — `_draw_scroll_menu` (line 1883). `draw_menu`, `border_color=FP.GOLD`. Tabs for scrolls vs. spellbooks. Consistent.

### 13. Identify menu — `_draw_identify_menu` (line 1927). `draw_menu`, `border_color=FP.ARCANE_BRIGHT`. Section headers split Inventory / Ground / Corpses. Subtitle "Requires Philosopher's Shard". Consistent.

### 14. Cook menu — `_draw_cook_menu` (line 1977). `draw_menu`, tabs for single-ingredient vs. compound. Recipe icon proxy. Consistent.

### 15. Drop menu — `_draw_drop_menu` (line 2063). `draw_menu`, text rows. Tab counts. Consistent.

### 16. Eat menu — `_draw_eat_menu` (line 2099). `draw_menu`, `border_color=FP.SUCCESS_TEXT` (green). SP subtitle color-coded. Consistent.

### 17. Quaff potion menu — `_draw_quaff_menu` (line 2140). `draw_menu`, `border_color=FP.ARCANE_BRIGHT`. "Unknown potions may harm" subtitle in `(200,150,80)` inline. Consistent.

### 18. Throw menu — `_draw_throw_menu` (line 2177). `draw_menu`. Consistent.

### 19. Quirk power menu — `_draw_power_menu` (line 2221). `draw_menu`. Cooldown indicators.

### 20. Save & exit / abandon / chicken confirmation popups
- **File:** `_draw_confirm_exit` (line 2259), `_draw_exit_quest` (line 2291), `_draw_abandon_quest` (line 2318), `_draw_chicken` (line 2345).
- All use `draw_overlay` + `draw_dark_panel` + `draw_header_bar` + `draw_divider`. **Highly consistent grimoire family.**
- Hint colors: `FP.GOLD_BRIGHT` for affirmative, `FP.WARNING_TEXT` for negative, `FP.HINT_TEXT` for "Keep playing".

### 21. Story popup (boss-defeat / dungeon-entrance / exit-with-stone / exit-without-stone)
- **File:** `src/game_render.py:2368` `_draw_story_popup`. Content in `main.py:_STORY_CONTENT` (line ~3300+).
- Uses `draw_overlay` + `draw_dark_panel` + accent border.
- Has an "accent bar" SRCALPHA strip below title (line 2417), reward-code block (line 2438-2449) shown with `FP.GOLD_BRIGHT` code text and accent-tinted background.
- Title is `font_lg` in accent color, body is `font_md` in `FP.PARCHMENT_LIGHT`, quoted lines `(200,195,160)`.
- Footer: "-- Press any key to continue --" in `FP.HINT_TEXT`.
- **Most consistent grimoire example.** Both Stone-exit AND secret-Abyss-exit run through the SAME `exit_with_stone` story popup (`main.py:1458`) — the secret victory has no unique visual treatment.

### 22. Victory screen (Stone exit)
- **File:** `src/game_render.py:2456` `_draw_victory_screen`
- `draw_overlay(190, (12,10,0))` + `draw_rune_circle` (gold, big and small, counter-rotating) + `draw_candle_glow`.
- Title "VICTORY!" with `draw_glow_text`, sub "You retrieved the Philosopher's Stone!", filigree bars above + below title.
- Grade badge `font_xl`, score `font_lg`, stats table, breakdown line, high-score list.
- Hint `FP.HINT_TEXT` "Press ESC to close".
- **NO `draw_dark_panel`** — the screen is a free-form composition over `draw_overlay`. This is in the "draw_filigree_bar" family along with the welcome title and the shop.
- Consistent grimoire visual identity.

### 23. Death screen
- **File:** `src/game_render.py:2551` `_draw_death_screen`
- `draw_overlay(180, (50,0,0))` (red-tinted) + two counter-rotating `draw_rune_circle` (BURGUNDY + BLOOD).
- Title "YOU HAVE DIED" / "YOU FLED THE DUNGEON" / "YOU HAVE STARVED" depending on `defeat_reason`.
- `draw_glow_text(BLOOD, glow_color=BURGUNDY)` for the title.
- Filigree bars in `FP.BURGUNDY_MID`.
- Stats table same as victory.
- Mirrors victory's structure — visually a "dark twin" of the victory screen. **Highly consistent — the best sibling-screen relationship in the game.**

### 24. Review missed questions
- **File:** `src/game_render.py:2741` `_draw_review_missed`
- `draw_dark_panel(border_color=FP.GOLD)` + `draw_header_bar`. Consistent.

### 25. Study journal (in-game `;` key, post-death review)
- **File:** `src/game_render.py:2656` `_draw_study_journal`
- `draw_dark_panel(border_color=FP.GOLD)` + `draw_header_bar`. Consistent.

### 26. Standalone Study Mode (F3 from welcome screen)
- **File:** `src/study_mode.py:15` `StudyMode`
- **Background:** plain `FP.MIDNIGHT` fill — full screen.
- **No `draw_dark_panel`, no `draw_header_bar`, no `draw_overlay`, no flourishes.**
- Subject/tier picker rows: raw `pygame.Rect` + `pygame.draw.rect(... border_radius=4)`. Highlight is `FP.MIDNIGHT_MID` + subject-color 2px border.
- Question text rendered as bare `font_md` lines on midnight.
- Hint: `FP.HINT_TEXT` at bottom — only consistent element.
- **Tonal register:** completely orphaned from the rest of the game's chrome. Looks like a quick prototype.

### 27. Recall Lore / hint display
- **File:** `src/game_render.py:3336` `_draw_hint_screen`
- **Background:** raw `pygame.draw.rect(screen, (24,18,8), ..., border_radius=10)` + `(160,130,60)` 2px border + `(80,65,25)` inner 1px stroke, all rounded.
- **Does NOT use `draw_dark_panel`, `draw_header_bar`, or `draw_filigree_bar`.** Despite being a parchment-colored panel (close to `FP.PARCHMENT_DARK / GOLD_DARK / INK`), it's hand-rolled rounded chrome.
- Title `"RECALL LORE -- {label}"` in `(220,180,80)` heading 20.
- "Stars" indicator: `'[*] ' * chain + '[ ] ' * (5-chain)` — ASCII bracket+asterisk shimmer.
- Body text `(230,210,160)` body 19.
- Cooldown notice + close prompt in `(100,85,45)` body 16.
- **Visually orphaned from the rest of the grimoire chrome despite being the centerpiece of the game's discovery loop.** Compare against `_draw_story_popup` (Screen 21) which uses `draw_dark_panel` for nearly identical needs.

### 28. Lore screen (item identify / bestiary corpse-lore, `_lore_subject`)
- **File:** `src/game_render.py:2808` `_draw_lore_screen`
- **Background:** raw `pygame.draw.rect(screen, (8,6,20), ..., border_radius=10)` + dynamic border color (gold-amber for corpse, blue-grey for item) + inner 1px stroke.
- **Does NOT use `draw_dark_panel`, `draw_header_bar`.**
- Section divider lines are plain `pygame.draw.line` — no `draw_divider` (which has the center diamond).
- Color scheme is **completely different** between corpse-lore (warm gold) and item-lore (cool blue): `border_col`, `inner_col`, `title_col`, `stat_col`, `lore_col` all switch on `is_corpse`. This is a deliberate decision but the colors used `(80,120,200)` etc. are **not in FP**.
- "-- LORE --" header rendered in `border_col` — fine.
- Hint: `(80,80,100)` — not `FP.HINT_TEXT`.

### 29. Encyclopedia (category picker + list + entry detail)
- **File:** `src/game_render.py:3140` `_draw_encyclopedia`
- **Category picker** (line 3159): uses `draw_menu` with `border_color=FP.GOLD`. Consistent.
- **Entry list** (line 3293): uses `draw_menu` with `border_color=FP.ARCANE_BRIGHT`. Consistent.
- **Entry detail** (line 3198): `draw_dark_panel(border_color=FP.ARCANE_BRIGHT)` + `draw_header_bar` + `draw_divider`. Consistent grimoire chrome.
- **BUT** the lore color inside the detail view is `(200,215,240)` cool-blue with `(80,120,200)` "LORE" header — same blue palette as `_draw_lore_screen` item-lore branch. **Two separate render functions both bypass `FP` and roll their own blue-lore color identity.** They agree with each other by coincidence; refactoring either could desync them.
- **Tonal register:** the encyclopedia detail and `_draw_lore_screen` look like siblings of *each other* but neither sibling of the rest of the game.

### 30. Mystery approach prompt
- **File:** `src/game_render.py:50` `_draw_mystery_approach`
- **Background:** raw `pygame.draw.rect(screen, (18,12,6), ..., border_radius=10)` + `altar.color` 2px border + dimmed inner 1px stroke. **Hand-rolled rounded chrome — same family as `_draw_hint_screen` and `_draw_lore_screen`.**
- Title bar with `altar.symbol` flanking, divider line is plain `pygame.draw.line`.
- Requirements text in `(180,170,130)`, description in `(230,215,180)`, prompt in `(120,180,120)` — all inline, not FP.
- Y/N prompt at bottom.
- **Inconsistent with story-popup and confirm-exit popups**, which use `draw_dark_panel`.

### 31. NPC encounter dialog (moral encounters)
- **File:** `src/game_render.py:792` `_draw_npc_encounter`
- `draw_overlay(190)` + `draw_dark_panel(border_color=enc['color'])` + `draw_header_bar`. **Consistent grimoire chrome.**
- Multi-phase: text → options → select_item → outcome.
- Footer hints in `(120,120,120)` — should be `FP.HINT_TEXT`.

### 32. Cow encounter
- **File:** `src/game_render.py:744` `_draw_cow_encounter`
- `draw_overlay(190)` + `draw_dark_panel(border_color=(180,140,80))` + `draw_header_bar` + `draw_divider`. Consistent.

### 33. Altar of Judgment outcome
- **File:** `src/game_render.py:921` `_draw_judgment`
- `draw_overlay(190)` + `draw_dark_panel(border_color=<karma-driven>)` + `draw_header_bar`. Consistent grimoire chrome.

### 34. Container open / lockpick
- **No standalone container-open screen exists.** Inventory contents of containers are listed via `add_message` calls in `container_system.py` and the lockpicking interaction reuses the standard `STATE_QUIZ` quiz panel. The "container open" experience is purely message-log.
- This is consistent with the game's text-roguelike-with-tiles aesthetic, but **the act of opening a chest has no dedicated visual emphasis** — flagged in `beauty-no-container-emphasis`.

### 35. Quirk unlock notification / Quirks browse screen
- **Browse screen (`W` key, `_draw_quirks_screen` line 393):** raw `pygame.draw.rect(screen, (16,12,24), ..., border_radius=8)` + `(140,100,200)` border + `(70,50,100)` inner 1px stroke. **Hand-rolled — does not use `draw_dark_panel`.**
- Title `(200,170,255)` heading 20. Footer `(90,80,120)` body 13.
- Progress bars: `(40,30,60)` slot + `(140,100,200)` or `(100,255,120)` (full) fill. All inline RGB, not FP.
- "UNLOCKED" badge in `(100,255,120)` (close to but not `FP.SUCCESS_TEXT (110,220,100)`).
- **Quirk unlock notification:** not a screen — handled via `add_message` ("You feel the spark of..." style) in `quirk_system.py`. **The big-moment first-quirk discovery has no special UI.**

### 36. Hack Reality / XYZZY result
- **File:** `src/game_render.py:330` `_draw_hack_reality_screen`
- Raw `pygame.draw.rect(screen, (8,16,8), ..., border_radius=6)` + `(0,200,80)` border + `(0,100,40)` inner 1px stroke. **Hand-rolled "green terminal" chrome — deliberate stylistic exception.** (The hidden backtick terminal references "a reality beneath reality" in Tier 2 hints, so this is *intentionally* off-theme.)
- Tonal register: cyberpunk/terminal — explicit thematic break for the meta secret.
- **The XYZZY input screen** (`_draw_xyzzy_input` line 234) and **confirm screen** (`_draw_xyzzy_confirm` line 278) likely also use this terminal aesthetic — not re-read but inferred.

### 37. Character sheet (`@` key)
- **File:** `src/game_render.py:496` `_draw_character_sheet`
- `draw_dark_panel(border_color=FP.GOLD)` + `draw_header_bar` + `draw_divider`. Consistent grimoire chrome.
- Sections rendered as `(text, color, font, is_header)` tuples — heavy use of FP colors but a few inline `CYAN = (120,210,240)` / `PURPLE = (200,170,255)` constants.

### 38. Shop (merchant)
- **File:** `src/game_render.py:3093` `_draw_shop`
- `draw_overlay(190, (10,8,2))` + `draw_filigree_bar` (top + bottom). **NO `draw_dark_panel` chrome at all** — just filigree bars and centered text on the overlay.
- Item rows shown with manual highlight `(60,50,20,180)` SRCALPHA rect for the selection.
- Hint at bottom in `FP.HINT_TEXT`.
- **Visually anaemic** — every other modal in the game has at least a panel; the shop has only filigree.

### 39. Drop-gold input
- **File:** `src/game_render.py:3037` `_draw_drop_gold_input`
- `draw_overlay(190)` + `draw_dark_panel`. Consistent.

### 40. Examine menu — `_draw_examine_menu` (line 3063). Uses `draw_menu`. Consistent.

### 41. Help screen / Command reference (`?` key)
- **File:** `src/game_render.py:3496` `_draw_help_screen`
- `draw_dark_panel(border_color=FP.GOLD)` + `draw_header_bar` + `draw_divider`. Consistent.
- Two-column key/desc layout.

### 42. Debug overlay (F2 in-game)
- **File:** `src/game_render.py:3406` `_draw_debug_overlay`
- Plain `(0,0,0,180)` SRCALPHA rect, no border. Green `(0,255,100)` title, `(200,220,200)` body. Intentionally raw — developer-only.

### 43. Targeting overlays (melee/throw/ranged)
- **Files:** `_draw_targeting` (1147), `_draw_melee_targeting` (1156), `_draw_throw_targeting` (1198), `_draw_ranged_targeting` (1283).
- Tile-overlay reticles + path lines, drawn directly on the dungeon. Inline colors. Not panels; not catalog material.

---

## Consistency matrix — clashes between screens

| Cluster A (consistent grimoire) | Cluster B (rolled inline) |
|---|---|
| Story popup (21), confirm-exit (20), abandon (20), chicken (20), help (41), char sheet (37), review-missed (24), study journal (25), NPC dialog (31), cow (32), judgment (33), drop-gold (39), all `draw_menu` menus (8–19, 29, 40), encyclopedia detail (29), victory (22), death (23). All use `draw_dark_panel` / `draw_header_bar` / `draw_filigree_bar` / `draw_divider` / FP palette. | **Hint screen (27), lore screen (28), mystery approach (30), quirks browse (35), welcome title-bg + leaderboard (1), god-prompt popup (1), hack-reality (36 — intentional exception), study mode (26 — no chrome at all), shop (38 — only filigree, no panel), all-time top-100 (1), celebration (7)** |

**Cluster B summary:** ~9–10 screens roll their own `pygame.draw.rect(..., border_radius=…)` chrome instead of using `draw_dark_panel`. Most of these are **high-emotional-stakes screens** (Recall Lore hints, mystery prompts, quirk unlock progress) — the moments when the grimoire identity matters most.

### Specific clashes

1. **Hint screen vs. Story popup.** Both deliver atmospheric mythological narrative text in the same lifecycle position. Story popup uses `draw_dark_panel` with corner flourishes + diamond mid-edge ornaments. Hint screen uses rounded `border_radius=10` raw rects with no flourishes. They look like they're from different games. (See `beauty-hint-screen-orphan`.)

2. **Welcome screen vs. every other screen.** The vortex/EGA-domain-ring is acknowledged in code as "EGA-style" / "90s adventure-game style". The title banner and name input use grimoire primitives, but the giant rotating animation underneath is a different aesthetic generation. The leaderboard panel is also hand-rolled.

3. **Quiz choice cards vs. menu rows.** `draw_menu` (used by 12+ menus) has medieval-styled rows: solid bg, border, optional gold key label. Quiz choice cards use **modern button bevels** (`border_radius=7`, `min(255, v+40)` highlight on top/left). The two systems disagree about what a "selectable answer rectangle" looks like.

4. **Lore screen (corpse) vs. Lore screen (item) vs. Encyclopedia detail.** Three places that display the same kind of content (stats + LORE section). Corpse-lore uses warm-amber `(160,120,40)` palette; item-lore uses cool-blue `(80,120,200)`; encyclopedia detail (which CAN show both) uses the cool-blue `(80,120,200)` for everything. The book the player consults (encyclopedia) and the in-the-moment lore overlay (`_draw_lore_screen`) tell the same kind of stories with two different visual voices.

5. **Sidebar headers vs. panel headers.** Sidebar section headers are a flat `MIDNIGHT_MID` strip with no flourish. Panel headers use `draw_header_bar` — two-tone midnight + accent line + mid-edge diamonds. The sidebar feels lighter-weight than every modal.

6. **Celebration screen vs. everything.** MAX CHAIN celebration is pure black + warm yellow wash + arcade text. No rune circle, no candle glow, no filigree — the only "win moment" screen without grimoire treatment.

7. **Shop vs. every other modal.** The shop has *only* filigree bars and centered text. No panel, no header bar, no divider. It looks like an unfinished mockup compared to (e.g.) the cow encounter.

8. **Study mode vs. main-game study journal.** The standalone study mode (F3 from welcome) and the in-game `;` study journal cover the same gameplay function. The in-game version uses `draw_dark_panel` + `draw_header_bar`; the standalone version uses bare `FP.MIDNIGHT` fill + rounded rects.

9. **Death-chase atmosphere.** When `death_pursues = True`, the only visual change is Death's tile pulse. The sidebar, message log, map vignette, color palette are unchanged. The chase is a textual experience. (See `beauty-death-chase-invisible`.)

10. **Secret Abyss victory vs. Stone-exit victory.** Both flow through `_show_story_popup('exit_with_stone')` → `STATE_VICTORY` → `_draw_victory_screen`. The "maximum-difficulty hidden ending" gets the **identical screen** as the regular ending. (See `beauty-no-secret-victory-distinction`.)

11. **Inline hex literals vs. FP palette.** Far too many screens drop in raw `(220,180,80)` / `(140,100,200)` / `(0,200,80)` rather than referencing `FP.GOLD_BRIGHT` / `FP.ARCANE` / etc. Refactoring a palette value in `fantasy_ui.py` will not affect any of these inline colors — they will silently drift away from the centralized palette. (See `beauty-palette-bypass`.)

12. **Hint text color is inconsistently used.** `FP.HINT_TEXT (170,165,215)` is used in some screens, but many screens use `(120,120,120)`, `(80,80,100)`, `(100,85,45)`, `(90,80,120)` for the "press X to close" hint. Five different hint colors across the game.

---

## Top-of-mind structural fixes (not findings — for the architect)

These are the systemic refactors that would resolve most of the catalog clashes at once:

1. **Adopt `draw_dark_panel` everywhere a modal exists.** Then *re-style* the hint screen, lore screen, mystery approach, quirks browse, all-time top-100 — they all become siblings of the story popup.
2. **Adopt `draw_choice_button` (`fantasy_ui.py:546`) in the quiz panel.** It exists, it's the right aesthetic, but the quiz rolls its own card.
3. **Add FP entries for the inline colors that recur** (e.g., the lore-blue family, the quirk-arcane family, the cooldown teal). Then ban raw RGB literals outside `fantasy_ui.py`.
4. **Ship the TTF fonts.** Without `assets/fonts/Cinzel-*.ttf` and `UnifrakturMaguntia.ttf`, the grimoire type identity is invisible on machines without Garamond.
5. **Generate the missing player sprites** referenced in `SECRET_BUILDS` — or pare the build list to those with art.
6. **Build a dedicated secret-Abyss-victory screen** that is visually distinct from the Stone-exit victory. Reuse rune circles in arcane-purple instead of gold.

---

*End of catalog.*
