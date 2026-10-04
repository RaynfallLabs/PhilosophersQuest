"""Load / save a JSON data file without disturbing its formatting.

Offline tooling. The data files in this repo were written by several
generators with different indents, newline styles and ASCII escaping; a
content patch should produce a diff of the fields it touched and nothing
else. `load` works out which combination reproduces the file byte for byte
and `save` writes it back the same way.
"""
from __future__ import annotations

import json
from pathlib import Path


def _candidates(data):
    for indent in (2, 4, 1, None):
        for ascii_ in (False, True):
            for seps in (None, (',', ': '), (',', ':')):
                try:
                    text = json.dumps(data, indent=indent, ensure_ascii=ascii_, separators=seps)
                except (TypeError, ValueError):
                    continue
                for nl in ('\n', '\r\n'):
                    for tail in ('', '\n'):
                        yield (indent, ascii_, seps, nl, tail), (text.replace('\n', nl) + tail.replace('\n', nl))


def load(path):
    """Return (data, fmt). fmt is None when no exact round trip was found."""
    raw = Path(path).read_bytes()
    bom = raw.startswith(b'\xef\xbb\xbf')
    text = raw.decode('utf-8-sig')
    data = json.loads(text)
    for fmt, out in _candidates(data):
        if out == text:
            return data, fmt + (bom,)
    nl = '\r\n' if '\r\n' in text else '\n'
    return data, (2, False, None, nl, '\n' if text.endswith('\n') else '', bom)


def save(path, data, fmt) -> None:
    indent, ascii_, seps, nl, tail, bom = fmt
    text = json.dumps(data, indent=indent, ensure_ascii=ascii_, separators=seps)
    text = text.replace('\n', nl) + tail.replace('\n', nl)
    Path(path).write_bytes((b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8'))


def roundtrips(path) -> bool:
    raw = Path(path).read_bytes()
    data = json.loads(raw.decode('utf-8-sig'))
    return any(out == raw.decode('utf-8-sig') for _f, out in _candidates(data))
