"""A Seeker's profile: the real person playing, what he or she has won, and
the lifetime counters behind the achievement ladders
(PLAN_SEEKER_PROFILE_ACHIEVEMENTS_2026_10_25.md section 1).

Pure module: no pygame and no Game import. A hero lives one run; a Seeker
keeps every hero's achievements, across deaths, new games and new versions.

Files, in ``save_dir()/seekers/`` (``%APPDATA%\\PhilosophersQuest`` when
installed, which no upgrade or uninstall touches)::

    index.json                    the active Seeker and the list of Seekers
    seeker_<encoded>.json         one profile per Seeker
    seeker_<encoded>.json.bak     the last good copy, kept on every write

A profile is JSON, never pickle (it has to outlive every version of the code),
and sealed (``seeker_codes.seal``): the codes a child shows Dad come from what
it says is unlocked, so an edited file is set aside and the backup restored.
A file that will not read is kept, never overwritten, as the save system does.

Shape (schema 1)::

    {"format": "PQSEEKER", "schema": 1, "seeker": "Robyn", "created": "...",
     "written_by": "3.3.0",
     "stats": {name: int},          lifetime sums
     "best": {name: int},           lifetime maxima
     "sets": {name: [str]},         distinct things (Secret Builds, endings)
     "live": {name: int},           current values (a running streak)
     "unlocked": {id: {"at", "version", "hero"}},
     "seen": [id],                  unlocks the gallery has shown
     "seal_key": "pq1", "seal": hex}

Unknown keys are kept: an older game never drops what a newer one wrote.
Counters only go up. Two copies of the game write without losing each
other's progress: each keeps only what changed since it last read the file,
and a write re-reads the file and adds those changes to it (``flush``).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import time

import seeker_codes

FORMAT = 'PQSEEKER'
SCHEMA = 1
NAME_MAX = 24
_SECTIONS = ('stats', 'best', 'sets', 'live', 'unlocked')

# Tests point this at a temp dir; otherwise the profiles live in save_dir().
_DIR_OVERRIDE: str | None = None


def seekers_dir() -> str:
    if _DIR_OVERRIDE is not None:
        base = _DIR_OVERRIDE
    else:
        from paths import save_dir
        base = os.path.join(save_dir(), 'seekers')
    os.makedirs(base, exist_ok=True)
    return base


def clean_name(text) -> str | None:
    """A typed Seeker name made tidy (spaces collapsed, at most NAME_MAX
    characters), or None if it has no letter or digit in it."""
    s = re.sub(r'\s+', ' ', str(text or '')).strip()[:NAME_MAX].strip()
    if not s or not seeker_codes.normalise_name(s) or not s.isprintable():
        return None
    return s


def profile_path(name: str) -> str:
    """One file per Seeker as codes see the name: "Robyn" and "robyn" are the
    same Seeker, with the same codes, so they share a file."""
    from save_system import _encode_name
    return os.path.join(seekers_dir(),
                        f'seeker_{_encode_name(seeker_codes.normalise_name(name))}.json')


def _today() -> str:
    return time.strftime('%Y-%m-%d')


def _version() -> str:
    try:
        from layout import VERSION
        return VERSION
    except Exception:
        return '?'


def new_doc(name: str) -> dict:
    return {'format': FORMAT, 'schema': SCHEMA, 'seeker': name, 'created': _today(),
            'written_by': _version(), 'stats': {}, 'best': {}, 'sets': {}, 'live': {},
            'unlocked': {}, 'seen': []}


def canonical(doc: dict) -> bytes:
    """The bytes the seal covers: everything but the seal itself."""
    body = {k: v for k, v in doc.items() if k not in ('seal', 'seal_key')}
    return json.dumps(body, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=True).encode('ascii')


def _seal(doc: dict) -> dict:
    doc['seal_key'] = seeker_codes.current_label()
    doc['seal'] = seeker_codes.seal(canonical(doc), doc['seal_key'])
    return doc


# Schema migrations: {from_schema: function(doc) -> doc at from_schema + 1}.
_MIGRATIONS: dict = {}


def migrate(doc: dict) -> dict:
    """Bring a profile up to SCHEMA, one tested step at a time, and fill any
    missing section (never dropping an unknown one)."""
    n = int(doc.get('schema', 1) or 1)
    while n < SCHEMA:
        doc = _MIGRATIONS[n](doc)
        n += 1
    doc['schema'] = max(n, int(doc.get('schema', 1) or 1))
    for key in _SECTIONS:
        if not isinstance(doc.get(key), dict):
            doc[key] = {}
    if not isinstance(doc.get('seen'), list):
        doc['seen'] = []
    return doc


def _shape_ok(doc) -> bool:
    return (isinstance(doc, dict) and doc.get('format') == FORMAT
            and isinstance(doc.get('schema'), int) and isinstance(doc.get('seeker'), str))


def read(path: str) -> tuple[dict | None, str]:
    """(profile, status). Status: 'ok', 'missing', 'corrupt' (will not read),
    'edited' (reads, but the seal is wrong) or 'newer' (a later schema than
    this game knows: returned, to be shown but never written)."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            doc = json.load(f)
    except FileNotFoundError:
        return None, 'missing'
    except (OSError, ValueError):
        return None, 'corrupt'
    if not _shape_ok(doc):
        return None, 'corrupt'
    if not seeker_codes.seal_ok(canonical(doc), doc.get('seal_key'), doc.get('seal')):
        return None, 'edited'
    if doc['schema'] > SCHEMA:
        return doc, 'newer'
    return migrate(doc), 'ok'


def set_aside(path: str, why: str) -> str | None:
    """Move a profile that will not load out of the way, keeping it."""
    dst = f"{path}.{why}-{time.strftime('%Y%m%d-%H%M%S')}"
    try:
        os.replace(path, dst)
        return dst
    except OSError:
        return None


def write(path: str, doc: dict) -> bool:
    """Seal and write atomically: temp file, fsync, rename. The file being
    replaced is copied to .bak first, so a good copy always survives."""
    tmp = f'{path}.{os.getpid()}.tmp'
    bak_tmp = f'{path}.bak.{os.getpid()}.tmp'
    try:
        _seal(doc)
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=1, sort_keys=True, ensure_ascii=True)
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(path) and read(path)[1] == 'ok':
            shutil.copyfile(path, bak_tmp)
            os.replace(bak_tmp, path + '.bak')
        os.replace(tmp, path)
        return True
    except Exception:
        try:
            from game_log import log_error
            log_error(f'seeker profile could not be written: {path}')
        except Exception:
            pass
        for leftover in (tmp, bak_tmp):
            try:
                if os.path.exists(leftover):
                    os.remove(leftover)
            except OSError:
                pass
        return False


class Profile:
    """One Seeker's profile while the game runs.

    ``_base`` is the profile as last read or written; the ``_d*`` dicts are
    what changed since. Reads combine the two. ``flush`` re-reads the file,
    adds the changes to whatever is on disk now, and writes it back.
    """

    def __init__(self, name: str, doc: dict, *, readonly: bool = False,
                 edited: bool = False, notice: str | None = None):
        self.name = name
        self._base = doc
        self.readonly = readonly
        self.notice = notice           # one-shot line for the title screen
        self.edited_found = edited     # someone edited the file (the hidden achievement)
        self._clear()

    def _clear(self):
        self._dadd: dict[str, int] = {}
        self._dbest: dict[str, int] = {}
        self._dsets: dict[str, set] = {}
        self._dlive: dict[str, int] = {}
        self._dunlock: dict[str, dict] = {}
        self._dseen: set = set()

    # -- reading --------------------------------------------------------
    def stat(self, key: str) -> int:
        return int(self._base['stats'].get(key, 0)) + self._dadd.get(key, 0)

    def best(self, key: str) -> int:
        return max(int(self._base['best'].get(key, 0)), self._dbest.get(key, 0))

    def members(self, key: str) -> set:
        return set(self._base['sets'].get(key, ())) | self._dsets.get(key, set())

    def live(self, key: str) -> int:
        if key in self._dlive:
            return self._dlive[key]
        return int(self._base['live'].get(key, 0))

    def is_unlocked(self, aid: str) -> bool:
        return aid in self._dunlock or aid in self._base['unlocked']

    def unlocked(self) -> dict:
        out = dict(self._base['unlocked'])
        out.update(self._dunlock)
        return out

    def is_seen(self, aid: str) -> bool:
        return aid in self._dseen or aid in self._base.get('seen', ())

    # -- changing --------------------------------------------------------
    def add(self, key: str, n: int = 1):
        if n > 0:
            self._dadd[key] = self._dadd.get(key, 0) + int(n)

    def raise_best(self, key: str, v: int):
        if int(v) > self.best(key):
            self._dbest[key] = int(v)

    def include(self, key: str, member) -> bool:
        """Add ``member`` to a set; True if it was new."""
        member = str(member)
        if member in self.members(key):
            return False
        self._dsets.setdefault(key, set()).add(member)
        return True

    def set_live(self, key: str, v: int):
        self._dlive[key] = int(v)

    def unlock(self, aid: str, *, hero: str = '') -> bool:
        if self.is_unlocked(aid):
            return False
        self._dunlock[aid] = {'at': time.strftime('%Y-%m-%dT%H:%M'),
                              'version': _version(), 'hero': str(hero or '')}
        return True

    def mark_seen(self, aids):
        self._dseen.update(str(a) for a in aids)

    def dirty(self) -> bool:
        return bool(self._dadd or self._dbest or self._dsets or self._dlive
                    or self._dunlock or self._dseen)

    # -- writing ---------------------------------------------------------
    def _apply(self, doc: dict) -> dict:
        for k, n in self._dadd.items():
            doc['stats'][k] = int(doc['stats'].get(k, 0)) + n
        for k, v in self._dbest.items():
            doc['best'][k] = max(int(doc['best'].get(k, 0)), v)
        for k, members in self._dsets.items():
            doc['sets'][k] = sorted(set(doc['sets'].get(k, ())) | members)
        doc['live'].update(self._dlive)
        for aid, info in self._dunlock.items():
            doc['unlocked'].setdefault(aid, info)
        doc['seen'] = sorted(set(doc.get('seen', ())) | self._dseen)
        doc['written_by'] = _version()
        return doc

    def flush(self) -> bool:
        """Write what changed. Re-reads the file first, so another copy of
        the game's progress is kept. A file found edited or damaged since it
        was read is set aside, and this copy's view is written instead."""
        if self.readonly:
            return False
        if not self.dirty() and os.path.exists(profile_path(self.name)):
            return True
        path = profile_path(self.name)
        disk, status = read(path)
        if status == 'ok':
            doc = disk
        else:
            if status in ('corrupt', 'edited'):
                set_aside(path, 'unreadable' if status == 'corrupt' else 'edited')
                if status == 'edited':
                    self.edited_found = True
            if status == 'newer':           # a newer game wrote it meanwhile
                self.readonly = True
                return False
            doc = json.loads(json.dumps(self._base))
        doc = self._apply(doc)
        if not write(path, doc):
            return False
        self._base = migrate(json.loads(json.dumps(doc)))
        self._clear()
        return True


def load(name: str) -> Profile:
    """The profile for ``name``: read, restored from its backup, or new.
    Never raises, never deletes, never overwrites a file it could not read."""
    name = clean_name(name) or 'Seeker'
    path = profile_path(name)
    doc, status = read(path)
    if status == 'ok':
        return Profile(doc.get('seeker') or name, doc)
    if status == 'newer':
        return Profile(doc.get('seeker') or name, migrate(doc), readonly=True,
                       notice=(f"{doc.get('seeker') or name}'s profile was saved by a newer "
                               "version of the game. Progress will not be recorded until "
                               "you update."))
    # Damaged or edited: keep the file, out of the way, and try the backup.
    # An edited file gets no notice at all: finding that out is the secret.
    kept = None
    if status in ('corrupt', 'edited'):
        kept = set_aside(path, 'unreadable' if status == 'corrupt' else 'edited')
    bak, bstatus = read(path + '.bak')
    if bstatus == 'ok':
        notice = None
        if status == 'corrupt':
            notice = (f"{name}'s profile could not be read. The backup was restored"
                      + (f", and the damaged file was kept as {os.path.basename(kept)}."
                         if kept else "."))
        write(path, json.loads(json.dumps(bak)))   # the backup becomes the profile again
        return Profile(bak.get('seeker') or name, bak, edited=(status == 'edited'),
                       notice=notice)
    notice = None
    if status == 'corrupt' or bstatus == 'corrupt':
        notice = (f"{name}'s profile could not be read, so a new one was started. "
                  "Nothing was deleted" + (f": the old file was kept as {os.path.basename(kept)}."
                                           if kept else "."))
    return Profile(name, new_doc(name), edited=(status == 'edited' or bstatus == 'edited'),
                   notice=notice)


# -- the index: who is playing -------------------------------------------

def _index_path() -> str:
    return os.path.join(seekers_dir(), 'index.json')


def _read_index() -> dict:
    try:
        with open(_index_path(), 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return {}


def _write_index(data: dict):
    path = _index_path()
    tmp = f'{path}.{os.getpid()}.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=1, ensure_ascii=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass


def active_name() -> str | None:
    """The Seeker who stays active until someone deliberately changes it."""
    name = _read_index().get('active')
    return clean_name(name) if name else None


def set_active(name: str) -> str | None:
    """Make ``name`` the active Seeker (creating the profile if new)."""
    name = clean_name(name)
    if name is None:
        return None
    if not os.path.exists(profile_path(name)):
        write(profile_path(name), new_doc(name))
    data = _read_index()
    data['active'] = name
    names = [n for n in data.get('seekers', []) if isinstance(n, str)
             and seeker_codes.normalise_name(n) != seeker_codes.normalise_name(name)]
    data['seekers'] = sorted(names + [name], key=str.casefold)
    _write_index(data)
    return name


def all_names() -> list[str]:
    """Every Seeker on this machine: the index, plus any profile file the
    index does not list (a damaged index is rebuilt from the files)."""
    seen: dict[str, str] = {}
    for n in _read_index().get('seekers', []):
        if isinstance(n, str) and clean_name(n):
            seen[seeker_codes.normalise_name(n)] = clean_name(n)
    try:
        for fn in os.listdir(seekers_dir()):
            if fn.startswith('seeker_') and fn.endswith('.json'):
                doc, st = read(os.path.join(seekers_dir(), fn))
                if doc and st in ('ok', 'newer'):
                    seen.setdefault(seeker_codes.normalise_name(doc['seeker']), doc['seeker'])
    except OSError:
        pass
    return sorted(seen.values(), key=str.casefold)
