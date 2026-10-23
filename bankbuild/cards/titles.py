"""Stamp a display title on every topic card.

    py -m bankbuild.cards.titles [--check]

The Lore Codex (Encyclopedia m), Study Mode's By Topic list and the card
reader show a topic by name, and the topic ids are slugs, some cut off at 60
characters ("welfare-cliffs-the-effective-marginal-tax-rate-that-traps-lo").
So every entry in data/question_contexts/<subject>.json carries a `title`:
  * the topic's `name` in bankbuild/<subject>/_queue.json, where it has one;
  * else bankbuild/cards/topic_titles.json (ai, trivia, and ladders added
    after their queue was written);
  * math's skill classes are already named, so a math title is its id.
Titles pass through naming.proper_name (Title Case at source). `merge` and
`stage apply` keep an entry's other keys, so a title survives a card rewrite;
a NEW topic (a split ladder) needs its title added to topic_titles.json and
this run again. --check lists topics with no title and changes nothing.
"""
from __future__ import annotations

import json
import re
import sys

from bankbuild.cards.common import CDIR, ROOT


def _proper(text: str) -> str:
    sys.path.insert(0, str(ROOT / 'src'))
    from naming import proper_name
    # The queues write a dash as "--" or "  -  "; a title shows one em dash.
    text = re.sub(r'\s*(?:--|\s-\s)\s*', ' — ', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    # A subtitle starts with a capital: "Jekyll Island: The Secret Meeting".
    titled = re.sub(r'([:—]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(),
                    proper_name(text))
    return re.sub(r'(?<=\w) Vs\.? ', lambda m: m.group(0).lower(), titled)   # "Athens vs. Sparta"


def titles_for(subject: str) -> dict[str, str]:
    out: dict[str, str] = {}
    queue = ROOT / 'bankbuild' / subject / '_queue.json'
    if queue.exists():
        for t in json.loads(queue.read_text(encoding='utf-8')):
            if t.get('id') and t.get('name'):
                out[t['id']] = t['name']
    extra = json.loads((ROOT / 'bankbuild' / 'cards' / 'topic_titles.json').read_text(encoding='utf-8'))
    out.update(extra.get(subject, {}))
    return out


def main() -> None:
    check = '--check' in sys.argv
    missing_all = {}
    for path in sorted(CDIR.glob('*.json')):
        subject = path.stem
        cards = json.loads(path.read_text(encoding='utf-8'))
        names = titles_for(subject)
        missing, changed = [], 0
        for topic, entry in cards.items():
            if not isinstance(entry, dict):
                continue
            title = topic if subject == 'math' else names.get(topic)
            if not title:
                missing.append(topic)
                continue
            title = _proper(title.strip())
            if entry.get('title') != title:
                entry['title'] = title
                changed += 1
        if missing:
            missing_all[subject] = missing
        if changed and not check:
            path.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(f'{subject}: {len(cards)} cards, {changed} titles {"to set" if check else "set"}, '
              f'{len(missing)} without one')
    for subject, missing in missing_all.items():
        print(f'  {subject} needs titles in topic_titles.json: {missing[:10]}')
    sys.exit(1 if missing_all and check else 0)


if __name__ == '__main__':
    main()
