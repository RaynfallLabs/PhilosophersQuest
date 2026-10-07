# Monster scaling log

Every real run of `scale_monsters.py`. Earlier one-off passes are recorded in `apply_difficulty_schedule.py` and `apply_wisdom_rebalance.py`.

| When | HP schedule | Damage schedule | Named | Kept | Regen | Changed | Why |
|---|---|---|---|---|---|---|---|
| 2026-10-05 19:06 | hp 1:1:0.9:0.8:0.8:0.8 | dmg 0.55:0.8:1.1:1.15:1.1:1.05 | named: yes | keep-dmg: abaddon_destroyer | regen catch-up: yes | 210 hp, 959 attacks, 16 regen | Final tune for wisdom/3 floors + short Guide My Hand: ease floors 1-39 for a casual player, lighten deep HP (fewer sums per floor), calm floors 81-99 |
| 2026-10-05 19:21 | hp 1 | dmg 1.0:0.8:0.85:0.9:0.9:0.9 | named: yes | keep-dmg: abaddon_destroyer | regen catch-up: no | 0 hp, 473 attacks, 0 regen | Smooth the step at floor 20 (a casual player went from 0.3% to certain death per floor) and calm floors 61-99 (9% per floor for a prepared one at 81-99) |
| 2026-10-05 19:28 | hp 1 | dmg 1.0:0.72:1.0:1.0:1.0:1.0 | named: yes | keep-dmg: abaddon_destroyer, asterion_minotaur | regen catch-up: no | 0 hp, 171 attacks, 0 regen | Floors 20-35 eased so a casual player fades through the twenties instead of dying on floor 21 |
| 2026-10-05 | - | Medusa, Fafnir, Fenrir damage x1.25 (by hand) | named only | - | no | 3 bosses | With the quest layer they killed 0 to 3% of prepared players: no danger at all |
| 2026-10-05 19:36 | hp 1 | dmg 1.0:1.0:1.12:1.12:1.12:1.12 | named: yes | keep-dmg: asterion_minotaur | regen catch-up: no | 0 hp, 478 attacks, 0 regen | Floors 40+ a little sharper: a prepared good kid was winning one run in three; aim is nearer one in six |
| 2026-10-06 20:03 | hp 1 | dmg 0.9:0.85:1.0:1.2:1.3:1.38:1.45:1.52:1.6 | named: no | keep-dmg: - | regen catch-up: no | 0 hp, 350 attacks, 0 regen | Stat design step one (Constitution 3 HP + toughness, Dexterity dodge, cut-stat cooking, gate-boss gifts) made a prepared character about twice as durable deep down: ordinary monsters hit harder with depth to match; floors 1-19 eased a little for casual players. Named foes untouched. |
| 2026-10-06 21:06 | hp 1 | dmg 1:1:1:0.95:0.87:0.85:0.85:0.85:0.85 | named: no | keep-dmg: - | regen catch-up: no | 0 hp, 234 attacks, 0 regen | Second half of the same pass: with meditation limited to half a mana bar per floor (healing spells had been unlimited), floors 40+ came back 15% so a prepared player wins about 27% and a committed build about 41%. Net change from before this pass is roughly x1.1 at floor 50 rising to x1.35 at floor 100. Named foes untouched. |
