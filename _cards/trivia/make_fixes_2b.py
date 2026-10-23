"""Round two of the trivia b002-b003 fixes, from the judge (2026-10-23)."""
import json
from pathlib import Path

F = []


def fx(h, field, old, new):
    F.append({'subject': 'trivia', 'hash': h, 'field': field, 'old': old, 'new': new})


Q, A, C = 'question', 'answer', 'choices'
# The question asked for a pair while the key now lists all five enemy pairs.
fx('a57cb77c57', Q, 'Which two colors sit diametrically', 'Which colors sit diametrically')
# The key named five men by counting Triple H and Hunter Hearst Helmsley twice.
fx('09504165ff', Q, 'five real-life best friends who worked for the company', 'a group of real-life best friends who worked for the company')
fx('09504165ff', A, 'Shawn Michaels, Triple H, Razor Ramon, Diesel, and Hunter Hearst Helmsley',
   'Shawn Michaels, Razor Ramon, Diesel and Hunter Hearst Helmsley, who is Triple H')
# The card and a sibling rung say he was fired three weeks into shooting.
fx('a40bae20a4', Q, 'The original director who was fired before filming began', 'The original director who was fired three weeks into shooting')
# NOT fixed here: 2:40 is the real DK Mode requirement, so the CARD was wrong.
# The Marlboro campaign ran from 1965.
fx('162fe4bcfe', Q, 'In the 1980s, a famous TV ad campaign reused the theme', 'From the mid-1960s, a famous ad campaign reused the theme')
# The key is the 1978 Donner film, which the stem's own 1975 date excludes.
fx('e4dcb20b0e', Q, 'What 1975 development finally got DC', 'What development finally got DC')
# Sadamoto began the manga in 1994, before the series was broadcast, and
# 1994 to 2013 is nineteen years (fourteen is the volume count).
fx('661ccce8be', Q, 'When the anime series ended in 1996, he began drawing his own manga version of the same story.',
   'He had begun his own manga version in 1994, before the series was even broadcast.')
fx('661ccce8be', A, 'Roughly seventeen years, finishing in June 2013', 'Roughly nineteen years, finishing in June 2013')
# Miyazaki drew the chase himself, so nobody drew it "under" him.
fx('23c95d46fd', Q, 'Which animator drew that scene, working under Miyazaki?', 'Who drew that scene?')
# Routh's Superman predates Scott Pilgrim, so "went on to" is wrong.
fx('b94801ed58', Q, 'Two of those cast members went on to play other comic-book', 'Two of those cast members have also played other comic-book')
# This stem prints the answer to its own sibling rung c251c200d0.
fx('fd147f33bb', Q, " — the others by Philip Humber (April 21) and Matt Cain (June 13)", '')
# Spike TV did not exist in 1997, and the card says only that it was held off air.
fx('3c995b939e', Q, ' on Spike TV in 1997', ' years later')
# Hanako's haunt is the old girls' lavatory, per the card and three siblings.
fx('3b5cb92577', Q, "boys' bathroom stall", "girls' lavatory")
# Nicol Bolas is blue-black-red.
fx('54d5fa2637', Q, 'this red 7/7', 'this blue-black-red 7/7')
# A sibling rung and the card say twenty-three.
fx('515eebd133', Q, 'a movie about a 22-year-old bass player', 'a movie about a 23-year-old bass player')
# A sibling rung says twenty-three, which is the figure usually given.
fx('2a0647255b', Q, 'with music by 24-year-old Yasunori Mitsuda', 'with music by 23-year-old Yasunori Mitsuda')
# The card and the key both make it a promotional videotape, not a print ad.
fx('9e6cce3975', Q, 'commercial that opens th', 'advert that opens th')

Path(__file__).with_name('fixes_trivia_2b.json').write_text(json.dumps(F, ensure_ascii=False, indent=1), encoding='utf-8')
print(len(F), 'fixes')
