# Achievement badges

One PNG per achievement, named by its `art` field in `data/achievements.json` (`<art>.png`, 128 x 128, transparent outside the emblem). The game draws each badge's round rarity frame itself (bronze, silver, gold, violet), and makes the greyscale "not yet earned" version in code (`seeker_screen.badge_surface`), so only the full-colour emblem lives here.

The badges are made with the local pipeline in `tools/content/genart/` (the "Badges" section of its README) and installed by its badge installer. A badge with no PNG yet is drawn as a plain medallion, so a missing file never breaks a screen.

This README is kept out of the bundle (`bundle_excludes` in PhilosophersQuest.spec).
