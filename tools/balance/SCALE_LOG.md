# Monster scaling log

Every real run of `scale_monsters.py`. Earlier one-off passes are recorded in `apply_difficulty_schedule.py` and `apply_wisdom_rebalance.py`.

| When | HP schedule | Damage schedule | Named | Kept | Regen | Changed | Why |
|---|---|---|---|---|---|---|---|
| 2026-10-05 19:06 | hp 1:1:0.9:0.8:0.8:0.8 | dmg 0.55:0.8:1.1:1.15:1.1:1.05 | named: yes | keep-dmg: abaddon_destroyer | regen catch-up: yes | 210 hp, 959 attacks, 16 regen | Final tune for wisdom/3 floors + short Guide My Hand: ease floors 1-39 for a casual player, lighten deep HP (fewer sums per floor), calm floors 81-99 |
| 2026-10-05 19:21 | hp 1 | dmg 1.0:0.8:0.85:0.9:0.9:0.9 | named: yes | keep-dmg: abaddon_destroyer | regen catch-up: no | 0 hp, 473 attacks, 0 regen | Smooth the step at floor 20 (a casual player went from 0.3% to certain death per floor) and calm floors 61-99 (9% per floor for a prepared one at 81-99) |
| 2026-10-05 19:28 | hp 1 | dmg 1.0:0.72:1.0:1.0:1.0:1.0 | named: yes | keep-dmg: abaddon_destroyer, asterion_minotaur | regen catch-up: no | 0 hp, 171 attacks, 0 regen | Floors 20-35 eased so a casual player fades through the twenties instead of dying on floor 21 |
| 2026-10-05 | - | Medusa, Fafnir, Fenrir damage x1.25 (by hand) | named only | - | no | 3 bosses | With the quest layer they killed 0 to 3% of prepared players: no danger at all |
| 2026-10-05 19:36 | hp 1 | dmg 1.0:1.0:1.12:1.12:1.12:1.12 | named: yes | keep-dmg: asterion_minotaur | regen catch-up: no | 0 hp, 478 attacks, 0 regen | Floors 40+ a little sharper: a prepared good kid was winning one run in three; aim is nearer one in six |
