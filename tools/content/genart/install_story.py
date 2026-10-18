"""Install the reviewed story-content sprites (briefs story_s01/s02, story_items_s01/s02).

    <ComfyUI python> tools/content/genart/install_story.py [--dry]

Reads _genart/story_*/review.json. Monsters and NPC figures go to assets/tiles/monsters,
items to assets/tiles/items. A review entry may name an edited sprite in its note
("Install c1_sprite_edit.png"): when c<N>_sprite_edit.png exists it is used instead of
c<N>_sprite.png. Refuses to overwrite a file that already exists unless its id is one
of these runs' own (a re-install). Merges the ids into installed.json (monsters),
installed_rest.json (npc_*) and installed_items.json (items).
"""
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GEN = os.path.join(ROOT, '_genart')
RUNS = {'story_s01': 'monsters', 'story_s02': 'monsters', 'story_items_s01': 'items', 'story_items_s02': 'items'}
OURS = os.path.join(HERE, 'installed_story.json')


def main():
    dry = '--dry' in sys.argv
    ours = set(json.load(open(OURS, encoding='utf-8'))) if os.path.exists(OURS) else set()
    done = {'monsters': [], 'items': []}
    for run, folder in RUNS.items():
        rv = os.path.join(GEN, run, 'review.json')
        for sid, v in json.load(open(rv, encoding='utf-8')).items():
            if not v.get('pick'):
                print('no pick:', sid); continue
            base = os.path.join(GEN, run, sid, f"c{v['pick']}_sprite")
            src = base + '_edit.png' if os.path.exists(base + '_edit.png') else base + '.png'
            dst = os.path.join(ROOT, 'assets', 'tiles', folder, sid + '.png')
            if os.path.exists(dst) and sid not in ours:
                raise SystemExit(f'{dst} already exists and is not one of ours; not overwriting')
            if not dry:
                shutil.copyfile(src, dst)
            done[folder].append(sid)
            print(('would install' if dry else 'installed'), os.path.relpath(src, ROOT), '->', os.path.relpath(dst, ROOT))
    if dry:
        return
    json.dump(sorted(done['monsters'] + done['items']), open(OURS, 'w', encoding='utf-8'), indent=0)
    mons = [m for m in done['monsters'] if not m.startswith('npc_')]
    npcs = [m for m in done['monsters'] if m.startswith('npc_')]
    p = os.path.join(HERE, 'installed.json')
    json.dump(sorted(set(json.load(open(p, encoding='utf-8'))) | set(mons)), open(p, 'w', encoding='utf-8'), indent=0)
    p = os.path.join(HERE, 'installed_rest.json'); d = json.load(open(p, encoding='utf-8'))
    d['monsters'] = sorted(set(d['monsters']) | set(npcs)); json.dump(d, open(p, 'w', encoding='utf-8'), indent=0)
    p = os.path.join(HERE, 'installed_items.json'); d = json.load(open(p, encoding='utf-8'))
    d['items'] = sorted(set(d['items']) | set(done['items'])); json.dump(d, open(p, 'w', encoding='utf-8'), indent=0)


if __name__ == '__main__':
    main()
