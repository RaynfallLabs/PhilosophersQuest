# Theology bank v2.7.0 — READY TO SHIP

**Status:** built, audited, merged, gated, promoted, frozen. Awaiting your `ISCC` rebuild + `git commit/push` + live play-test.

---

## Numbers

- **345 topics / 2,739 questions** live in `data/questions/theology.json` (replaces 1,320-Q v1)
- Tier distribution: T1 529 (19.3%) · T2 543 (19.8%) · T3 618 (22.6%) · T4 569 (20.8%) · T5 480 (17.5%) — healthy curve

## Pillar shares (target vs actual)

| Pillar          | Topics | Q     | Share  | Target |
|-----------------|-------:|------:|-------:|-------:|
| Christian       | 138    | 999   | 36.5%  | 36%    |
| Greek           | 72     | 613   | 22.4%  | 22%    |
| Norse           | 54     | 443   | 16.2%  | 17%    |
| Western myth    | 81     | 684   | 25.0%  | 25%    |

Held perfectly against the queue-review projection.

## Audits

- **Moral:** 1 / 345 flagged (0.3%) — one `low` on Belshazzar's feast, essentially clean.
- **Tone:** 14 / 345 flagged (12 low, 2 medium) — both mediums fixed inline (Blandina "roast her" → "burn her"; Becket "scattered his brains" → "drove the sword-tip into his skull"). Lows shipped as-is.
- **Deterministic gate:** 4 / 2,739 (0.15%) — safe to ship.

## What's committed vs local vs pending

**Local, not committed:**
- `data/questions/theology.json` (the shipped bank)
- `src/layout.py` (VERSION 2.6.6 → 2.7.0)
- `installer/setup.iss` (AppVersion 2.6.6 → 2.7.0)
- `bankbuild/theology/` (the whole rebuild workspace: queue, strand specs, ladders, manifest, harness)
- `bankbuild/subjects/theology.json` (the subject config)
- `THEOLOGY_QUEUE_REVIEW.md` (post-trim/dedup queue review)
- `_archive/theology_v2_ship/` (backup + staging JSONs, kept for rollback)

**Bundle validated:** `dist/PhilosophersQuest/_internal/data/questions/theology.json` has 2,739 Q. Pytest full suite: **1,570 pass**. PyInstaller freeze clean.

## Pending for you

1. **Rebuild installer:**
   ```
   ISCC installer/setup.iss
   ```
   (produces `installer/PhilosophersQuest_Setup.exe`)

2. **Commit + push:**
   ```
   git add data/questions/theology.json src/layout.py installer/setup.iss \
           bankbuild/theology/ bankbuild/subjects/theology.json \
           THEOLOGY_QUEUE_REVIEW.md THEOLOGY_SHIP_READY.md \
           _archive/theology_v2_ship/
   git commit -m "theology bank v2.7.0: 4-pillar wonder bank, 345 topics / 2,739 Q"
   git push origin main
   ```

3. **Live play-test:**
   ```
   python src/main.py
   ```
   Pray at an altar (theology mechanic) to see the new bank in the wild.

## Rollback

If anything goes wrong: `_archive/theology_v2_ship/theology_pre_v2_backup.json` is the v1 bank (1,320 Q). Restore with:
```
copy _archive\theology_v2_ship\theology_pre_v2_backup.json data\questions\theology.json
```

## Design notes worth remembering

- **Symmetric voice** (bank-wide rule): Christian rungs read plainly, no reverence bonus; Norse/Greek rungs read plainly, no sneer discount.
- **Two ladder shapes:** deep character-anchored (12-rung wonder ladders) + shallow supporting-cast (5-8 rung mini-ladders).
- **Grokipedia-first sourcing** followed throughout research.
- **Sharded dedup pass** ran before build (Norse Loki-tricks vs Aesir-gods overlap surfaced 7 dups; kept the Loki-tricks placements).
- **~1,150+ Opus agent messages** invested (author + adv-judge R1 + revise + adv-judge R2 per topic; ~30 tool calls per batch × 115 batches).
