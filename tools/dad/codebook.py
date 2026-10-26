"""Dad's Codebook: every achievement and its code for one Seeker, as a page
to print.

    py tools/dad/codebook.py Robyn [Corwin ...]

Writes Documents\\PQ_Dad\\Codebook_<name>.html (outside the repo: it lists
every code). Open it in a browser and print it. Codes already redeemed (see
check_code.py) are ticked with their date. Secret achievements are listed
too, with how they unlock, so you can tick them off: keep the page away from
the children.
"""
import html
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dadlib  # noqa: E402
from dadlib import seeker_codes  # noqa: E402

_CSS = """
body { font-family: Georgia, 'Times New Roman', serif; color: #111; background: #fff;
       margin: 24px; font-size: 12px; }
h1 { font-size: 22px; margin: 0 0 4px; }
h2 { font-size: 15px; margin: 18px 0 6px; border-bottom: 1px solid #999; }
p.meta { color: #444; margin: 0 0 12px; }
table { border-collapse: collapse; width: 100%; }
td, th { border: 1px solid #bbb; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #eee; }
tr { page-break-inside: avoid; }
td.code { font-family: Consolas, 'Courier New', monospace; font-size: 13px; white-space: nowrap; }
td.box { width: 18px; text-align: center; }
td.done { color: #555; }
@media print { body { margin: 10mm; } }
"""


def build(seeker: str, data_path: str | None = None) -> str:
    """The Codebook page for one Seeker, as HTML text."""
    achs = dadlib.achievements(data_path)
    cats = dadlib.categories(data_path)
    notes = dadlib.notes()
    out = [f'<!doctype html><html><head><meta charset="utf-8"><title>Codebook: '
           f'{html.escape(seeker)}</title><style>{_CSS}</style></head><body>',
           f"<h1>Dad's Codebook: {html.escape(seeker)}</h1>",
           f'<p class="meta">Made {time.strftime("%Y-%m-%d")} with key '
           f'{html.escape(seeker_codes.current_label())}. {len(achs)} achievements. '
           'A code is good only for this name. Keep this page away from the children.</p>']
    for cat_id, cat_name in cats.items():
        rows = [a for a in achs if a['category'] == cat_id]
        if not rows:
            continue
        out.append(f'<h2>{html.escape(cat_name)}</h2><table><tr><th></th><th>Achievement</th>'
                   '<th>How it unlocks</th><th>Rarity</th><th>Code</th></tr>')
        for a in rows:
            code = seeker_codes.make_code(a['id'], a['code_word'], seeker)
            done = dadlib.redeemed(seeker, a['id'])
            box = '&#10003;' if done else '&#9744;'
            how = notes.get(a['id']) or a.get('hint', '')
            if done:
                how += f' (redeemed {done["date"]})'
            out.append(f'<tr><td class="box">{box}</td><td>{html.escape(a["name"])}</td>'
                       f'<td{" class=done" if done else ""}>{html.escape(how)}</td>'
                       f'<td>{html.escape(a["rarity"])}</td>'
                       f'<td class="code">{html.escape(code)}</td></tr>')
        out.append('</table>')
    out.append('</body></html>')
    return '\n'.join(out)


def write(seeker: str, data_path: str | None = None) -> str:
    safe = ''.join(c if c.isalnum() else '_' for c in seeker) or 'Seeker'
    path = os.path.join(dadlib.dad_dir(), f'Codebook_{safe}.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(build(seeker, data_path))
    return path


def main(argv):
    names = [a for a in argv if not a.startswith('--')]
    if not names:
        sys.exit('Give one or more Seeker names:  py tools/dad/codebook.py Robyn')
    dadlib.require_real_key()
    for n in names:
        print('Written:', write(n))


if __name__ == '__main__':
    main(sys.argv[1:])
