"""The cook menu's words and its list layout (pure: no pygame, no Game).

The kitchen rebuild, slice K2 (COOKING_REBUILD_PLAN_2026_11_14 section 2.4).
The rows come from ``kitchen.menu_rows``, read once per tab when the menu
opens (``Game._open_cook_menu``); this module turns them into what the screen
says, and picks the rows a long list shows:

- why the menu opened on its tab ("Opened on HP: you are hurt, 12 of 40 HP");
- a row's chip: the main thing a ready dish does ("+45 HP", "DEX +1"), or how
  close a dish being built toward is ("2 of 4");
- a row's second line: what a ready dish uses, with how many the pack holds,
  or what a dish still needs ("Needs: Wyvern Tail, Hard Cheese");
- where a missing part comes from ("Hunt it", "Forage or buy it");
- the list's sections (Ready to Cook, Building Toward, Legendary Feasts) and
  the line an empty tab shows, naming the tab that has something;
- ``window``: the slice of a long list in view, the selected row kept in it.
"""
import re

import kitchen
from naming import quantity

SECTION_TITLES = {'ready': 'Ready to Cook', 'building': 'Building Toward',
                  'legendary': 'Legendary Feasts'}

# What each tab's dishes are for (the empty tab's detail pane says it).
TAB_BLURBS = {
    'hp': "HP dishes heal you now and add to your maximum HP.",
    'sp': "SP dishes fill the belly far past a ration, and slow your hunger for a long while.",
    'mp': "MP dishes give back mana: a caster's meal before a hard fight.",
    'stat': "Stat dishes teach a stat: this floor's lesson, or a whole point from a rich dish.",
    'special': "Special dishes lend a power for a while: night sight, a resistance, a ward.",
}


def keep_together(text: str) -> str:
    """A number kept on one line with what it counts: "100 turns", "+2 Max
    HP", "1 of 4" are bound by no-break spaces, so a narrow pane wraps
    between facts, never inside one ("Sustained, 525 / turns")."""
    t = re.sub(r'(\d+) of (\d+)', '\\1\u00a0of\u00a0\\2', str(text))
    t = re.sub(r'(\d+) (turns?|HP|SP|MP|Max)\b', '\\1\u00a0\\2', t)
    return t.replace('Max HP', 'Max\u00a0HP').replace('Max MP', 'Max\u00a0MP')


def tab_name(tab: str) -> str:
    return kitchen.TAB_NAMES.get(tab, str(tab).title())


def reason_line(tab: str, why: str, player) -> str:
    """Why the menu opened on ``tab`` (kitchen.opening_choice), with the
    numbers that made it urgent."""
    def nums(cur, mx, label):
        return f"{int(cur or 0)} of {int(mx or 0)} {label}"
    p = player
    if why == 'hurt':
        what = f"you are hurt, {nums(getattr(p, 'hp', 0), getattr(p, 'max_hp', 0), 'HP')}"
    elif why == 'hungry':
        what = f"you are hungry, {nums(getattr(p, 'sp', 0), getattr(p, 'max_sp', 0), 'SP')}"
    elif why == 'mana':
        what = f"your mana is low, {nums(getattr(p, 'mp', 0), getattr(p, 'max_mp', 0), 'MP')}"
    elif why == 'lesson':
        what = "this floor's stat lesson is open"
    elif why == 'most_rows':
        what = "nothing is ready yet, but this is closest"
    elif why == 'nothing':
        what = "nothing to cook yet"
    else:
        what = "the most dishes ready"
    return f"Opened on {tab_name(tab)}: {what}"


def urgent(why: str) -> bool:
    """A reason that is about the hero's state right now (hurt, hungry, low
    on mana), drawn in the warning colour."""
    return why in ('hurt', 'hungry', 'mana')


def main_effect(row: dict) -> str:
    """The short main thing a dish does, for its chip: "+45 HP", "+150 SP",
    "+12 MP", "DEX +1" (a whole point, or the meal that completes one),
    "Teaches DEX" (half a point), "No DEX Lesson" (used or capped), a
    timed power's name ("Dark Vision", "Body Ward +3")."""
    rec = row['recipe']
    tab = kitchen.dish_tab(rec)
    first = (row.get('effects') or [''])[0]
    if tab == 'stat':
        stat = kitchen.dish_stat(rec) or ''
        if not first.startswith('Teaches'):
            return f"No {stat} Lesson"
        if 'full point' in first or 'completes' in first:
            return f"{stat} +1"
        return f"Teaches {stat}"
    if kitchen.makes(rec):
        return "To Carry"                 # cooked to carry (the Starnut Tart)
    if kitchen.song_of(rec):
        return f"{kitchen.song_share(rec)} Damage"   # its song's power (songs.py)
    if tab == 'special':
        out = kitchen.dish_outcome(rec)
        label = kitchen.power_label(out['power'])
        return f"{label} +{out['ward']}" if out['ward'] else label
    return first


def chip_text(row: dict) -> str:
    """The chip at a row's right: what a ready dish does, or "2 of 4"."""
    return main_effect(row) if row['ready'] else row['progress']


def _part_label(name: str, n: int) -> str:
    return f"{name} x{n}" if n > 1 else name


def uses_parts(row: dict, counts) -> list:
    """What a ready dish uses, with how many the pack holds where it holds
    more than the dish takes (what is left to cook again, or to save):
    "Goblin Gristle (2 in pack)", "River Salt x2 (3 in pack)", "Wild
    Mushroom" (exactly enough: the detail pane says "Have 1")."""
    out = []
    for part in row['have'] + row['missing']:
        held = int(counts.get(part['id'], 0) or 0)
        label = _part_label(part['name'], part['need'])
        out.append(f"{label} ({held} in pack)" if held > part['need'] else label)
    return out


def missing_parts(row: dict) -> list:
    """What a dish still needs, by name: "Wyvern Tail", "Hard Cheese x2"."""
    return [_part_label(m['name'], m['need'] - m['have']) for m in row['missing']]


def fit_list(lead: str, names: list, fits) -> str:
    """``lead`` + the names, as many as ``fits(text)`` allows, the rest
    counted ("Needs: Wyvern Tail and 2 more") rather than cut off."""
    names = list(names)
    full = lead + ', '.join(names)
    if fits(full) or len(names) <= 1:
        return full
    for k in range(len(names) - 1, 0, -1):
        text = f"{lead}{', '.join(names[:k])} and {len(names) - k} more"
        if fits(text):
            return text
    return f"{lead}{names[0]} and {len(names) - 1} more"


def row_line(row: dict, counts, fits=lambda _t: True) -> str:
    """A row's second line: a ready dish's ingredients and what the pack
    holds of each; else "Needs: " and what is missing."""
    if row['ready']:
        return fit_list('', uses_parts(row, counts), fits)
    return fit_list('Needs: ', missing_parts(row), fits)


def part_source(part_id: str) -> str:
    """What to do about a missing part, for a kid deciding what to hunt:
    a monster part is hunted, a trophy is won from a boss, a foraged find
    or a ration is found (or bought: traders stock both)."""
    kind = kitchen.part_kind(part_id)
    if kind == 'monster':
        return "Hunt"
    if kind == 'trophy':
        return "Boss trophy:"
    if kind == 'forage':
        return "Forage or buy"
    return "Find or buy"


def part_words(part: dict, held: int) -> tuple:
    """One ingredient in the detail pane, as (left, right): a part the pack
    holds enough of is its name and "Have 2"; a missing one says what to do
    ("Hunt Wyvern Tail", "Find or buy Hard Cheese") and how many of how
    many the pack holds ("0 of 1")."""
    if held >= part['need']:
        return part['name'], f"Have {held}"
    return f"{part_source(part['id'])} {part['name']}", f"{held} of {part['need']}"


def status_line(row: dict) -> str:
    """The detail pane's status: ready, or how close."""
    if row['group'] == 'legendary':
        kind = 'Trophy Dish' if row.get('trophy') and not row.get('legendary') \
            else 'Legendary Feast'
        return f"{kind}: Ready" if row['ready'] else f"{kind}: {row['progress']}"
    if row['ready']:
        return "Ready to Cook"
    return f"Building Toward: {row['progress']}"


def not_ready_line(row: dict) -> str:
    """What Enter on a dish that is not ready says."""
    names = missing_parts(row)
    if not names:
        return f"{row['name']} is not ready yet."
    if len(names) == 1:
        need = names[0]
    else:
        need = ', '.join(names[:-1]) + ' and ' + names[-1]
    return f"{row['name']} is not ready: you still need {need}."


def tier_line(row: dict) -> str:
    """The cooking question's tier (the band of the dish's deepest part)."""
    return f"Question: Tier {row['tier']}"


def list_items(rows: list, note: str = '') -> list:
    """The list as drawn: an optional note, then each group's header and its
    rows, in ``kitchen.GROUPS`` order (``menu_rows`` already sorts them so).
    Items are dicts: ``{'kind': 'note', 'text'}``, ``{'kind': 'head',
    'group', 'count'}`` or ``{'kind': 'row', 'index'}`` (into ``rows``)."""
    items = []
    if note:
        items.append({'kind': 'note', 'text': note})
    for group in kitchen.GROUPS:
        idx = [i for i, r in enumerate(rows) if r['group'] == group]
        if not idx:
            continue
        items.append({'kind': 'head', 'group': group, 'count': len(idx)})
        items.extend({'kind': 'row', 'index': i} for i in idx)
    return items


def section_title(group: str, count: int) -> str:
    return f"{SECTION_TITLES.get(group, group.title())} ({count})"


def window(heights: list, focus: int, avail: int, heads=()) -> tuple:
    """``(start, end)``: the items drawn in ``avail`` px, item ``focus`` in
    view. The list shows from the top while the focus fits there, else it
    ends at the focus; when the focus is a section's first row, its header
    comes into view with it. ``heads``: the indexes of section headers; a
    header is never left alone at the foot of the view, its rows below."""
    n = len(heights)
    if n == 0:
        return 0, 0
    focus = max(0, min(focus, n - 1))
    start = 0
    while start < focus and sum(heights[start:focus + 1]) > avail:
        start += 1
    end, used = start, 0
    while end < n and used + heights[end] <= avail:
        used += heights[end]
        end += 1
    end = max(end, focus + 1)
    while end < n and end - 1 > focus and (end - 1) in heads:
        end -= 1
    return start, end


def best_other_tab(tab: str, ready_n: dict, rows_n: dict):
    """The tab to suggest from ``tab``: the most dishes ready, else the most
    being built toward; None when every other tab is empty."""
    others = [t for t in kitchen.MENU_TABS if t != tab]
    best = max(others, key=lambda t: (ready_n.get(t, 0), rows_n.get(t, 0),
                                      -kitchen.MENU_TABS.index(t)))
    return best if (ready_n.get(best, 0) or rows_n.get(best, 0)) else None


def _try(best: str, ready_n: dict) -> str:
    n = ready_n.get(best, 0)
    if n:
        return f"Try {tab_name(best)}: {quantity(n, 'dish', 'dishes')} ready."
    return f"Try {tab_name(best)}: dishes to build toward."


def empty_line(tab: str, ready_n: dict, rows_n: dict) -> str:
    """One line for a tab with nothing ready or being built toward."""
    head = f"No dish in the {tab_name(tab)} tab uses what you carry yet."
    best = best_other_tab(tab, ready_n, rows_n)
    return f"{head} {_try(best, ready_n)}" if best else head


def nothing_ready_note(tab: str, ready_n: dict) -> str:
    """The note over a tab that has dishes to build toward but none ready,
    when another tab has one ready ('' otherwise)."""
    if ready_n.get(tab, 0):
        return ''
    best = best_other_tab(tab, ready_n, {})
    if not best or not ready_n.get(best, 0):
        return ''
    return f"Nothing ready in {tab_name(tab)} yet. {_try(best, ready_n)}"
