---
id: code-encyclopedia-item-id-lost
dimension: code
severity: P3
title: Encyclopedia item entries lose their `id` — `entry.get('id', '')` always returns empty
status: open
systems: [encyclopedia, ui]
evidence:
  - src/main.py:3962 — `item_list = list(all_items.values())` discards the dict keys (the id)
  - src/main.py:3964 — `iid = entry.get('id', '')` returns '' because the value dicts have no 'id' field
  - src/main.py:3965 — `if iid in known_ids:` — empty string is never in known_ids → no items added
  - data/items/potion.json:2-23 — example value dict: name, unidentified_name, symbol, etc., but no 'id' key (id is the outer dict key)
  - src/items.py:444-446 — `load_items` correctly injects `'id': item_id` because it iterates `raw.items()`. The encyclopedia code does not.
verified: true
discovered: 2026-05-15
---

## What's wrong
The encyclopedia item-category loader at `main.py:3953-3968` opens an item JSON file (e.g., `weapon.json`), which is a dict of `{id: defn}`. It then does:

```python
item_list = list(all_items.values()) if isinstance(all_items, dict) else all_items
for entry in item_list:
    iid = entry.get('id', '')
    if iid in known_ids:
        entries.append(entry)
```

`all_items.values()` discards the dict keys. The value dicts (definitions) do NOT include an `'id'` key — that's only the outer key. Therefore `entry.get('id', '')` returns `''` for every iteration, and **no items are ever added to the encyclopedia** for any item category.

The consensus baseline lists a very similar issue ("Encyclopedia item loader iterates dicts as lists") and the loader was partially patched to use `.values()` — but the patch addressed only the iteration mechanic and **did not preserve the keys**. Net effect: the bug from the prior audit is still present.

Compare to `items.load_items` (`items.py:444-446`) which correctly injects the id:

```python
return [cls({**defn, 'id': item_id, 'item_class': item_class})
        for item_id, defn in raw.items()]
```

## How to reproduce / where it fires
1. Identify a few items in the game (e.g., 5 different weapons via the Identify menu).
2. Open the Encyclopedia and switch to the Weapons category.
3. The list is empty — "Nothing discovered yet" — even though `known_item_ids` contains the IDs.

Call graph: open encyclopedia → category=weapon/armor/scroll/etc. → main.py:3954-3968 → entries always empty.

## Suggested fix
Iterate `all_items.items()` and project the key into the entry dict:

```python
entries = [
    {'id': iid, **defn}
    for iid, defn in all_items.items()
    if iid in known_ids
]
entries.sort(key=lambda e: e.get('name', e['id']))
self.encyclopedia_entries = entries
```

## Notes
The list-vs-dict guard at line 3962 (`if isinstance(all_items, dict)`) handles a defensive case, but no shipping item JSON file uses list format — they're all `{id: defn}` dicts. The fix above unifies the code path and matches the canonical pattern in `items.load_items`.
