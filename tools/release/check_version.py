"""Release guard: the pushed tag must match the version written in the game.

The version lives in two places (src/layout.py VERSION, shown on the title
screen and in the error log, and installer/setup.iss AppVersion, which Inno
Setup stamps on the installer). Bumping one and forgetting the other, or
pushing a tag before bumping either, used to produce a release whose title
screen named the previous version. The release workflow runs this before it
builds anything:

    python tools/release/check_version.py v3.1.0

Exit code 0 when the tag, layout.VERSION and AppVersion agree; 1 otherwise,
with every mismatch printed. It reads the files as text so it needs no game
imports (layout.py imports pygame).
"""
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', '..'))

_LAYOUT_RE = re.compile(r'^VERSION\s*=\s*["\']([^"\']+)["\']', re.M)
_ISS_RE = re.compile(r'^#define\s+AppVersion\s+"([^"]+)"', re.M)


def _read(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        return f.read()


def read_versions(layout_text: str, iss_text: str):
    """Return (layout VERSION, setup.iss AppVersion); None for a missing one."""
    m1 = _LAYOUT_RE.search(layout_text)
    m2 = _ISS_RE.search(iss_text)
    return (m1.group(1) if m1 else None, m2.group(1) if m2 else None)


def problems(tag: str, layout_text: str, iss_text: str) -> list:
    """Every reason the tag cannot be released, as readable lines."""
    out = []
    version = tag[1:] if tag.startswith('v') else tag
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        out.append(f"tag {tag!r} is not of the form vX.Y.Z")
    layout_v, iss_v = read_versions(layout_text, iss_text)
    if layout_v is None:
        out.append("src/layout.py has no VERSION = \"X.Y.Z\" line")
    elif layout_v != version:
        out.append(f"src/layout.py VERSION is {layout_v}, tag is {tag}")
    if iss_v is None:
        out.append("installer/setup.iss has no #define AppVersion line")
    elif iss_v != version:
        out.append(f"installer/setup.iss AppVersion is {iss_v}, tag is {tag}")
    return out


def main(argv) -> int:
    tag = argv[1] if len(argv) > 1 else os.environ.get('GITHUB_REF_NAME', '')
    if not tag:
        print("usage: check_version.py vX.Y.Z  (or set GITHUB_REF_NAME)")
        return 1
    errs = problems(tag, _read(os.path.join('src', 'layout.py')),
                    _read(os.path.join('installer', 'setup.iss')))
    for e in errs:
        print(f"::error::{e}")
    if errs:
        print("Bump the version in BOTH files, commit, and re-tag.")
        return 1
    print(f"version check OK: {tag}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
