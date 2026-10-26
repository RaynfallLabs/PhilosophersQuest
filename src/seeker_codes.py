"""Reward codes for Dad, and the seal on a Seeker's profile
(PLAN_SEEKER_PROFILE_ACHIEVEMENTS_2026_10_25.md section 4).

Pure module: no pygame and no Game import. ``tools/dad/`` imports it too, so
Dad's checker and the game make codes the same way.

A code reads ``WORD-XXXX-XXXX``: the achievement's code word, then 40 bits of
HMAC-SHA256(code key, "<key label>|<achievement id>|<normalised Seeker name>")
in Crockford base32 (no I, L, O or U, so nothing reads as anything else when a
child copies it out). The same Seeker always gets the same code for an
achievement, and a sibling's name gives a different one.

The key is never in the repo (the repo is public). It lives in ``_dad_key.py``
beside this file: gitignored on Brandon's machine (``tools/dad/make_key.py``
writes it) and written from the ``PQ_DAD_KEY`` secret by the release build.
Without it (a fork, the CI test job) the game uses ``DEV_KEY``, which is public,
and every code starts ``DEV-``: Dad's checker never accepts one.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import unicodedata

ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ'      # Crockford base32
CODE_CHARS = 8                                       # 40 bits
DEV_LABEL = 'dev'
DEV_KEY = b'philosophers-quest-public-development-key-not-secret'
DEV_PREFIX = 'DEV-'

# Typed in place of a code character, read as the character meant.
_TYPO = {'O': '0', 'I': '1', 'L': '1'}

# Tests set this to {'label': ..., 'keys': {label: bytes}} so they never
# depend on whether a real key is installed.
_KEYS_OVERRIDE: dict | None = None


def _installed() -> tuple[str, dict[str, bytes]]:
    """(current label, {label: master key}) from _dad_key.py, or the dev key."""
    if _KEYS_OVERRIDE is not None:
        return _KEYS_OVERRIDE['label'], dict(_KEYS_OVERRIDE['keys'])
    try:
        import _dad_key                                  # noqa: PLC0415
        keys = {str(k): bytes.fromhex(v) for k, v in dict(_dad_key.KEYS).items()}
        current = str(_dad_key.CURRENT)
        if current in keys and all(len(v) >= 16 for v in keys.values()):
            return current, keys
    except Exception:
        pass
    return DEV_LABEL, {DEV_LABEL: DEV_KEY}


def is_dev() -> bool:
    """True when no real key is installed: codes are DEV codes."""
    return _installed()[0] == DEV_LABEL


def current_label() -> str:
    return _installed()[0]


def known_labels() -> set[str]:
    """Every key label this build can check a seal with. A real build never
    trusts the public dev key."""
    label, keys = _installed()
    if label != DEV_LABEL:
        keys.pop(DEV_LABEL, None)
    return set(keys)


def _derived(master: bytes, purpose: str) -> bytes:
    return hmac.new(master, f'pq-{purpose}'.encode('ascii'), hashlib.sha256).digest()


def normalise_name(name) -> str:
    """The Seeker name as codes see it: NFKC, case-folded, letters and digits
    only. "Robyn", " robyn " and "ROBYN" are one Seeker."""
    s = unicodedata.normalize('NFKC', str(name or '')).casefold()
    return re.sub(r'[\W_]+', '', s)


def _base32(raw: bytes, n: int = CODE_CHARS) -> str:
    v = int.from_bytes(raw, 'big')
    bits = len(raw) * 8
    return ''.join(ALPHABET[(v >> (bits - 5 * (i + 1))) & 31] for i in range(n))


def _mac(master: bytes, label: str, achievement_id: str, seeker: str) -> str:
    msg = f'{label}|{achievement_id}|{normalise_name(seeker)}'.encode('utf-8')
    raw = hmac.new(_derived(master, 'code'), msg, hashlib.sha256).digest()[:5]
    return _base32(raw)


def make_code(achievement_id: str, code_word: str, seeker: str) -> str:
    """The code a Seeker shows Dad for an achievement, with this build's key."""
    label, keys = _installed()
    chars = _mac(keys[label], label, achievement_id, seeker)
    code = f'{code_word.upper()}-{chars[:4]}-{chars[4:]}'
    return DEV_PREFIX + code if label == DEV_LABEL else code


def split_code(text) -> tuple[str, str] | None:
    """(code word, the 8 code characters) from a code as typed, forgiving case,
    spaces, missing dashes and O/I/L typed in the code part (never in the
    word: GORGON has an O). None if it cannot be a code, and None for every
    DEV code (no code word may start with DEV: achievements.validate)."""
    s = re.sub(r'[\s\-_.]+', '', str(text or '').upper())
    if s.startswith('DEV'):
        return None
    if len(s) <= CODE_CHARS:
        return None
    word, chars = s[:-CODE_CHARS], s[-CODE_CHARS:]
    if not word.isalpha():
        return None
    chars = ''.join(_TYPO.get(c, c) for c in chars)
    if any(c not in ALPHABET for c in chars):
        return None
    return word, chars


def check_code(text, seeker: str, achievements, keys: dict[str, bytes] | None = None):
    """Which achievement a code is for, or None if it is not a real code for
    this Seeker. ``achievements``: iterable of (id, code word). ``keys``:
    {label: master key}; by default every key this build holds (the dev key is
    never accepted). Returns (achievement id, key label) or None."""
    parts = split_code(text)
    if parts is None:
        return None
    word, chars = parts
    if keys is None:
        _label, keys = _installed()
        keys.pop(DEV_LABEL, None)
    for aid, aword in achievements:
        if str(aword).upper() != word:
            continue
        for label, master in keys.items():
            if hmac.compare_digest(_mac(master, label, aid, seeker), chars):
                return aid, label
    return None


def seal(payload: bytes, label: str | None = None) -> str:
    """The profile seal: HMAC of the profile's canonical bytes with ``label``'s
    key (this build's current key by default). Hex."""
    cur, keys = _installed()
    label = label or cur
    return hmac.new(_derived(keys[label], 'seal'), payload, hashlib.sha256).hexdigest()


def seal_ok(payload: bytes, label, value) -> bool:
    """Is ``value`` the seal of ``payload`` under a key this build trusts?"""
    if not isinstance(label, str) or label not in known_labels() or not isinstance(value, str):
        return False
    return hmac.compare_digest(seal(payload, label), value)
