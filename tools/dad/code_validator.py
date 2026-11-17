"""Dad's Code Validator: a slot machine for the reward codes the kids bring.

    py tools/dad/code_validator.py        (or double-click "Code Validator.bat")

Choose the kid, then give the two things on the kid's Seeker page in the
game: the Seeker name the code was earned under (the kids play under names
that need not be their own, on more than one computer; the name last used
for the kid is filled in, and Up / Down or a click moves between the name
and the code) and the code. Press Enter (or pull the lever): the reels spin
while the code is checked with that name, and stop on three of the badge for
a real code. A code seen for the first time is given to the kid chosen,
recorded under the kid's name in the same ledger check_code.py keeps
(Documents\\PQ_Dad\\redeemed.csv), so it is marked complete, and the screen
says what the reward is. The Seeker name is remembered for the kid
(Documents\\PQ_Dad\\kids.json). A code already used for another kid lands
amber and says so: Enter gives it anyway, Esc goes back.

The Badge Library is each kid's badges, the one place that holds every
claim whichever machine the kid played on: every achievement by category as
the game's Seeker gallery shows it (claimed in colour with the date, the rest
grey, a deep secret only its name and "???"), the picked badge's page beside
it, and with L the badges earned, newest first.

M switches the sound off and on (F5 while a code is being typed, where M is a
letter); the choice is kept in Documents\\PQ_Dad\\validator.json.

The rules live in validator_core.py (no window); this file only draws and
listens. It borrows the game's look: the UI art kit (ui_theme), the fonts and
colours (fantasy_ui), the badges (seeker_screen) and the sounds (sound_system).
"""
from __future__ import annotations

import math
import os
import random
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import validator_core as core  # noqa: E402  (puts src/ on the path)
import dadlib  # noqa: E402

import pygame  # noqa: E402

import ui_scale  # noqa: E402
from ui_scale import px as S  # noqa: E402

SIZE = (1280, 800)
MIN_SIZE = (1024, 680)
FPS = 60

KIDS, CODE, SPIN, RESULT, PARTY, TRACKER = 'kids', 'code', 'spin', 'result', 'party', 'tracker'
NAME_ROW = 58                     # the Seeker name's row above the code boxes (unscaled px)
NAME_LABEL = "Seeker name (the name on the kid's Seeker page)"
NAME_LABELS = (NAME_LABEL, "Seeker name (on the kid's Seeker page)", "Seeker name")   # a narrow window
TABS = ((KIDS, 'Choose a Kid'), (CODE, 'Check a Code'), (TRACKER, 'Badge Library'))

# The kids' heroes (welcome_screen's Secret Builds: Fianna the Wizard, Corwin
# the Ranger): the art on their cards. Any other name gets its initial.
PORTRAITS = {'fianna': ('player_wizard_f', 'The Wizard'),
             'corwin': ('player_ranger', 'The Ranger')}


def _ui():
    """The game's UI helpers (imported once the window exists)."""
    import fantasy_ui
    return fantasy_ui


# -- sound -------------------------------------------------------------------------

class Sfx:
    """The machine's sounds, made the way src/sound_system.py makes the
    game's (its tone builders, and its achievement fanfare and secret
    chime), all short and soft. M (or F5) switches them off and on; the
    choice is kept in Documents\\PQ_Dad\\validator.json (the game's own
    sound setting is never read or written)."""

    # name: (builder, args) from sound_system; nothing over about a second.
    def __init__(self, enabled: bool = True, on: bool = True):
        self.sounds: dict = {}
        self.on = False
        self._last: dict = {}
        if not enabled:
            return
        try:
            import sound_system as snd
            snd.init()                            # opens the mixer at the rate the builders write for
            notes, noise = snd._make_notes, snd._make_noise_burst
            own = {
                # A key typed: a crisp little click.
                'key': lambda: noise(0.014, volume=0.16),
                # A key refused: a soft low blip.
                'refuse': lambda: notes([(233, 0.05)], wave='triangle', volume=0.14),
                # Enter: the lever's clunk, and the ratchet as it springs back.
                'lever': lambda: notes([(98, 0.05), (64, 0.13)], wave='triangle', volume=0.42),
                'ratchet': lambda: notes([(700, 0.012), (0, 0.035), (760, 0.012), (0, 0.035),
                                          (820, 0.012), (0, 0.035), (880, 0.012)], wave='triangle',
                                         volume=0.10),
                # The reels: a soft tick as each badge passes, a thunk as each stops.
                'tick': lambda: notes([(2100, 0.011)], wave='triangle', volume=0.09),
                'reel_stop': lambda: notes([(150, 0.05), (96, 0.11)], wave='triangle', volume=0.34),
                # The answers.
                'nope': lambda: notes([(415, 0.10), (0, 0.025), (311, 0.22)], wave='triangle', volume=0.22),
                'chime': lambda: notes([(784, 0.10), (988, 0.10), (784, 0.24)], wave='triangle', volume=0.22),
                'stamp': lambda: snd._make_sweep(170, 48, 0.24, volume=0.40, decay=0.12),
                'coins': lambda: notes([(1568, 0.05), (2093, 0.05), (1760, 0.05), (2349, 0.10)], volume=0.13),
                'toggle': lambda: notes([(660, 0.05), (880, 0.08)], volume=0.18),
            }
            for name, make in own.items():
                s = make()
                if s is not None:
                    self.sounds[name] = s
            for name in ('achievement', 'secret'):          # the game's own fanfare and chime
                if name in snd._sounds:
                    self.sounds[name] = snd._sounds[name]
            self.on = bool(self.sounds) and on
        except Exception:
            self.sounds, self.on = {}, False

    def play(self, name: str, volume: float = 1.0, *, gap: float = 0.0, now: float = 0.0):
        """Play ``name``; with ``gap``, not again until ``gap`` seconds after the last time."""
        if not self.on:
            return
        if gap and now - self._last.get(name, -99.0) < gap:
            return
        self._last[name] = now
        s = self.sounds.get(name)
        if s is None:
            return
        try:
            s.set_volume(max(0.0, min(1.0, volume)))
            s.play()
        except Exception:
            pass

    def toggle(self) -> bool:
        """Sound off or on, remembered for next time."""
        if not self.sounds:
            return False
        self.on = not self.on
        core.save_settings(sound=self.on)
        if self.on:
            self.play('toggle', 0.8)
        else:
            try:
                pygame.mixer.stop()
            except Exception:
                pass
        return self.on


# -- confetti and sparkles -------------------------------------------------------------

class Particles:
    def __init__(self, rng):
        self.rng = rng
        self.bits: list = []       # confetti: [x, y, vx, vy, angle, spin, w, h, colour, flip, flip speed]
        self.stars: list = []      # sparkles: [x, y, age, life, size, colour]

    def clear(self):
        self.bits.clear()
        self.stars.clear()

    def burst(self, x, y, n, colours, power=1.0):
        r = self.rng
        for _ in range(n):
            a = r.uniform(0, math.tau)
            v = r.uniform(180, 620) * power
            self.bits.append([x, y, math.cos(a) * v, math.sin(a) * v - 260 * power, r.uniform(0, 360),
                              r.uniform(-420, 420), r.uniform(7, 13), r.uniform(4, 8), r.choice(colours),
                              r.uniform(0, math.tau), r.uniform(5, 12)])

    def rain(self, width, n, colours):
        r = self.rng
        for _ in range(n):
            self.bits.append([r.uniform(0, width), r.uniform(-60, -10), r.uniform(-40, 40), r.uniform(60, 160),
                              r.uniform(0, 360), r.uniform(-300, 300), r.uniform(7, 12), r.uniform(4, 7),
                              r.choice(colours), r.uniform(0, math.tau), r.uniform(5, 11)])

    def sparkle(self, x, y, spread, n, colours):
        r = self.rng
        for _ in range(n):
            self.stars.append([x + r.uniform(-spread, spread), y + r.uniform(-spread, spread), 0.0,
                               r.uniform(0.5, 1.2), r.uniform(5, 13), r.choice(colours)])

    def update(self, dt, height):
        keep = []
        for b in self.bits:
            b[3] += 520 * dt                       # gravity
            b[2] *= (1 - 1.6 * dt)                 # air
            b[3] = min(b[3], 260 + 140 * abs(math.sin(b[9])))
            b[0] += b[2] * dt
            b[1] += b[3] * dt
            b[4] += b[5] * dt
            b[9] += b[10] * dt
            if b[1] < height + 30:
                keep.append(b)
        self.bits = keep[-700:]
        for s in self.stars:
            s[2] += dt
        self.stars = [s for s in self.stars if s[2] < s[3]]

    def draw(self, surf):
        for x, y, _vx, _vy, ang, _sp, w, h, col, flip, _fs in self.bits:
            fw = w * (0.25 + 0.75 * abs(math.cos(flip)))
            c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            pts = [(x + dx * c - dy * s, y + dx * s + dy * c)
                   for dx, dy in ((-fw / 2, -h / 2), (fw / 2, -h / 2), (fw / 2, h / 2), (-fw / 2, h / 2))]
            shade = 0.75 + 0.25 * math.cos(flip)
            pygame.draw.polygon(surf, tuple(int(v * shade) for v in col), pts)
        for x, y, age, life, size, col in self.stars:
            k = math.sin(math.pi * age / life)
            r = size * k
            if r < 1:
                continue
            pygame.draw.line(surf, col, (x - r, y), (x + r, y), 2)
            pygame.draw.line(surf, col, (x, y - r), (x, y + r), 2)
            pygame.draw.circle(surf, (255, 255, 240), (int(x), int(y)), max(1, int(r / 4)))


# -- the app -----------------------------------------------------------------------------

class App:
    """The validator. ``screen``: the window's surface (a test may hand in
    any surface). Time moves only through ``update(dt)``."""

    def __init__(self, screen, *, sound: bool = True, rng=None, theme: bool = True):
        self.screen = screen
        self.rng = rng or random.Random()
        ui_scale.set_for_window(*screen.get_size())
        if theme:
            import ui_theme
            try:
                ui_theme.load()
            except Exception:
                ui_theme.unload()
        self.fx = Sfx(sound, on=core.load_settings()['sound'])
        self.parts = Particles(self.rng)
        self.achs = dadlib.achievements()
        self.by_id = {a['id']: a for a in self.achs}
        self.cats = dadlib.categories()
        self.words = core.code_words(self.achs)
        self.pool = [a['id'] for a in self.achs]
        self.key_ok = core.key_ready()
        self.kids = core.load_kids()
        self.kid = 0                       # the kid chosen (an index into kids)
        self.pick = 0                      # the card the arrows are on (len(kids): the "+" card)
        self.adding = None                 # the name being typed on the "+" card, or None
        self.removing = None               # the index of a name waiting for Y / N
        self.note = ''                     # a line under the kid cards
        self.note_t = -99.0
        self.esc_t = -99.0                 # the last Esc on the kid screen (two to quit)
        self.raw = ''                      # the code's keys as typed
        self.seeker_name = ''              # the Seeker name the code was earned under, as typed
        self.field = 'code'                # the field the keys go to: 'name' or 'code'
        self._name_for = None              # the kid (normalised) the Seeker name was filled in for
        self.entry = core.parse_entry('', self.words)
        self.line = ''                     # the hint under the slot
        self.shake_t = -99.0
        self.pop_t = -99.0
        self.strips = core.idle_strips(self.pool, self.rng)
        self.rest = [0] * core.REELS
        self.plan = None
        self.verdict = None
        self.spin_t = 0.0
        self.stops_heard: set = set()
        self.ticks = [0] * core.REELS
        self.track = None
        self.track_from = KIDS
        self.scroll = 0.0
        self.just = None                   # (kid, badge) claimed last in this window (marked New)
        self.view = 'grid'                 # the library: 'grid' (every badge) or 'list' (earned, newest first)
        self.sel = 0                       # the badge picked in the grid (an index into its entries)
        self.list_sel = 0                  # the row picked in the earned list
        self.list_scroll = 0.0
        self._reveal = False               # scroll the pick into view on the next frame
        self._grid_cols = 5
        self._stamp_heard = True
        self.state = KIDS
        self.t = 0.0                       # seconds since the window opened
        self.state_t = 0.0                 # seconds in this state
        self.hits: list = []               # (rect, action) of what can be clicked this frame
        self.quit = False
        self._badges: dict = {}
        self._sprites: dict = {}
        self._cache: dict = {}
        self._counts = {}
        self._refresh_counts()
        # Badges made a few a frame while the machine is idle, so the reels
        # and the tracker never wait for them (the reels' first).
        self._warm = [(self.by_id[i]['art'], 'reel', True) for s in self.strips for i in s]
        self._warm += [(a['art'], 'tile', won) for won in (True, False) for a in self.achs]

    # -- small helpers ---------------------------------------------------------
    @property
    def name(self) -> str:
        return self.kids[self.kid] if self.kids else ''

    def go(self, state):
        if state == TRACKER and self.state != TRACKER:
            self.track_from = self.state if self.state in (KIDS, CODE) else CODE
            # From a new claim, the library opens on that badge.
            self._open_library(self.just[1] if self.state == PARTY and self.just else None)
        if state == KIDS:
            self._refresh_counts()
            self.adding = self.removing = None
        if state == CODE:
            self._fill_name()
        if state != PARTY:
            self.parts.clear()
        self.state = state
        self.state_t = 0.0

    def _fill_name(self):
        """The Seeker name field, filled in for the kid chosen (the name last
        used for him or her, else the kid's own) when the kid has changed."""
        norm = core.normalise(self.name)
        if norm != self._name_for:
            self._name_for = norm
            self.seeker_name = core.prefill_name(self.name)
            self.field = 'code'

    def _open_library(self, focus=None):
        """Read the kid's library from the ledger, picking ``focus`` (a badge
        id) if given, else the first badge."""
        self.track = core.tracker(self.name)
        ids = [e['id'] for e in self.track['entries']]
        self.sel = ids.index(focus) if focus in ids else 0
        self.list_sel = 0
        self.scroll = self.list_scroll = 0.0
        self._reveal = True

    def _refresh_counts(self):
        rows = dadlib.ledger()
        ids = set(self.by_id)
        self._counts = {core.normalise(k): len(set(core.claims(k, rows)) & ids) for k in self.kids}
        self._plays_as = {core.normalise(k): (core.seeker_names(k) or [''])[0] for k in self.kids}

    def badge(self, art, px, earned=True):
        """A badge from seeker_screen, kept here for good (the tracker shows all of them)."""
        key = (art, int(px), bool(earned))
        got = self._badges.get(key)
        if got is None:
            import seeker_screen
            got = self._badges[key] = seeker_screen.badge_surface(art, px, earned)
        return got

    def _blurred(self, art, px):
        key = ('blur', art, int(px))
        got = self._badges.get(key)
        if got is None:
            b = self.badge(art, px)
            small = pygame.transform.smoothscale(b, (px, max(4, px // 7)))
            got = pygame.transform.smoothscale(small, (px, int(px * 1.35)))
            got.set_alpha(200)
            self._badges[key] = got
        return got

    def sprite(self, name, px):
        key = (name, int(px))
        got = self._sprites.get(key)
        if got is None:
            from paths import data_path
            from renderer import fit_sprite
            try:
                raw = pygame.image.load(data_path('assets', 'tiles', 'env', f'{name}.png'))
                got = fit_sprite(raw, int(px), int(px))
            except (pygame.error, OSError, FileNotFoundError):
                got = False
            self._sprites[key] = got
        return got or None

    def cached(self, key, make):
        got = self._cache.get(key)
        if got is None:
            got = self._cache[key] = make()
        return got

    def rarity_colour(self, rarity):
        import seeker_screen
        return seeker_screen.rarity_color(rarity)

    def _duplicate(self) -> bool:
        """The code on the reels is real but was used before for another kid."""
        return self.state in (SPIN, RESULT) and (self.verdict or {}).get('status') == 'duplicate'

    # -- events ------------------------------------------------------------------
    def handle(self, ev):
        if ev.type == pygame.QUIT:
            self.quit = True
        elif ev.type in (pygame.VIDEORESIZE, pygame.WINDOWSIZECHANGED):
            surf = pygame.display.get_surface()
            if surf is not None:
                self.screen = surf
            ui_scale.set_for_window(*self.screen.get_size())
            self._cache.clear()
        elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            for rect, action in reversed(self.hits):
                if rect.collidepoint(ev.pos):
                    self.click(action)
                    break
        elif ev.type == pygame.MOUSEWHEEL and self.state == TRACKER:
            if self.view == 'grid':
                self.scroll -= ev.y * S(60)
            else:
                self.list_scroll -= ev.y * S(60)
        elif ev.type == pygame.KEYDOWN:
            self.key(ev)

    def click(self, action):
        kind, arg = action
        if kind == 'tab' and self.state not in (SPIN,):
            self._tab(arg)
        elif kind == 'kid':
            self.pick = arg
            if arg == len(self.kids):
                self.adding = ''
            else:
                self._choose(arg)
        elif kind == 'lever' and self.state == CODE:
            self._pull()
        elif kind == 'field' and self.state == CODE:
            self._to_field(arg)
        elif kind == 'next':
            self._next()
        elif kind == 'track_kid' and self.kids:
            self.kid = (self.kid + arg) % len(self.kids)
            self._open_library()
        elif kind == 'view':
            self.view = arg
            self._reveal = True
        elif kind == 'badge':
            self.sel = arg
        elif kind == 'row':
            self.list_sel = arg

    def _tab(self, state):
        if state == CODE and (not self.kids):
            return
        if state == TRACKER and not self.kids:
            return
        self.go(state)

    def key(self, ev):
        k = ev.key
        if k == pygame.K_F5 or (k == pygame.K_m and not self._typing()):
            self.fx.toggle()
            return
        if k == pygame.K_F11:
            try:
                pygame.display.toggle_fullscreen()
            except pygame.error:
                pass
            return
        handler = {KIDS: self._key_kids, CODE: self._key_code, SPIN: self._key_spin,
                   RESULT: self._key_result, PARTY: self._key_party, TRACKER: self._key_tracker}[self.state]
        handler(ev)

    def _typing(self) -> bool:
        """True while the keys spell something (a code, a name): M is a letter then."""
        return self.state == CODE or (self.state == KIDS and self.adding is not None)

    def _sound_hint(self) -> str:
        key = 'F5' if self._typing() else 'M'
        return f"{key}: sound " + ("off" if self.fx.on else "on")

    def _cycle_tab(self, back=False):
        order = [s for s, _l in TABS]
        cur = self.state if self.state in order else CODE
        nxt = order[(order.index(cur) + (-1 if back else 1)) % len(order)]
        self._tab(nxt)

    # kid select
    def _key_kids(self, ev):
        k = ev.key
        n = len(self.kids)
        if self.removing is not None:
            if k in (pygame.K_y, pygame.K_RETURN, pygame.K_KP_ENTER):
                gone = self.kids[self.removing]
                self.kids = core.remove_kid(self.kids, self.removing)
                core.save_kids(self.kids)
                self.kid = min(self.kid, max(0, len(self.kids) - 1))
                self.pick = min(self.pick, len(self.kids))
                self._say(f"{gone} is off the list. Every code {gone} claimed is still in the Badge Library.")
                self._refresh_counts()
            self.removing = None
            return
        if self.adding is not None:
            if k == pygame.K_ESCAPE:
                self.adding = None
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                names, i, msg = core.add_kid(self.kids, self.adding)
                self._say(msg)
                if i >= 0:
                    if names != self.kids:
                        self.kids = names
                        core.save_kids(self.kids)
                        self._refresh_counts()
                    self.kid = self.pick = i
                    self.adding = None
            elif k == pygame.K_BACKSPACE:
                self.adding = self.adding[:-1]
            else:
                ch = getattr(ev, 'unicode', '') or ''
                import seeker_profile
                if len(ch) == 1 and ch.isprintable() and len(self.adding) < seeker_profile.NAME_MAX:
                    self.adding += ch
                    self.fx.play('key', 0.8)
            return
        if k == pygame.K_ESCAPE:
            if self.t - self.esc_t < 2.5:
                self.quit = True
            else:
                self.esc_t = self.t
                self._say("Press Esc again to close the validator.")
            return
        if k in (pygame.K_LEFT, pygame.K_a):
            self.pick = (self.pick - 1) % (n + 1)
        elif k in (pygame.K_RIGHT, pygame.K_d):
            self.pick = (self.pick + 1) % (n + 1)
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self.pick == n:
                self.adding = ''
            else:
                self._choose(self.pick)
        elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.pick = n
            self.adding = ''
        elif k in (pygame.K_DELETE,) and self.pick < n:
            self.removing = self.pick
        elif k == pygame.K_t and self.kids:
            self.kid = min(self.pick, n - 1)
            self.go(TRACKER)
        elif k == pygame.K_TAB:
            if self.pick < n:
                self.kid = self.pick
            self._cycle_tab(bool(ev.mod & pygame.KMOD_SHIFT))

    def _say(self, text):
        self.note, self.note_t = text, self.t

    def _choose(self, i):
        self.kid = self.pick = i
        if not self.key_ok:
            self._say("Codes can't be checked until the key is back: see the note below.")
            self.shake_t = self.t
            return
        self.go(CODE)

    # code entry
    def _key_code(self, ev):
        k = ev.key
        if k == pygame.K_ESCAPE:
            self.go(KIDS)
            return
        if k == pygame.K_TAB:
            self._cycle_tab(bool(ev.mod & pygame.KMOD_SHIFT))
            return
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self._pull()
            return
        if k in (pygame.K_UP, pygame.K_DOWN):
            self._to_field('name' if k == pygame.K_UP else 'code')
            return
        if self.field == 'name':
            self._key_name(ev)
            return
        if k == pygame.K_BACKSPACE:
            if ev.mod & pygame.KMOD_CTRL:
                self.raw = ''
            else:
                self.raw = core.backspace(self.raw, self.words)
            self._typed('')
            return
        if k == pygame.K_v and ev.mod & pygame.KMOD_CTRL:
            text = self._paste()
            if text:
                self.raw = core.entry_from_text(text, self.words)
                self._typed(core.hint(core.parse_entry(self.raw, self.words)))
            return
        ch = getattr(ev, 'unicode', '') or ''
        if not ch:
            return
        before = self.raw
        self.raw, line = core.type_key(self.raw, ch, self.words)
        if self.raw == before:
            if line:
                self.line = line
                self.shake_t = self.t
                self.fx.play('refuse')
            return
        self._typed(line)
        self.pop_t = self.t
        self.fx.play('key', 0.8)

    def _typed(self, line):
        self.entry = core.parse_entry(self.raw, self.words)
        self.line = line

    @staticmethod
    def _paste() -> str:
        try:
            return pygame.scrap.get_text() or ''
        except Exception:
            return ''

    def _to_field(self, field):
        """The keys go to the Seeker name ('name') or the code ('code') from now on."""
        if field in ('name', 'code') and field != self.field:
            self.field = field
            self.line = ''
            self.pop_t = self.t

    def _key_name(self, ev):
        """A key typed while the Seeker name field is active."""
        import seeker_profile
        k = ev.key
        if k == pygame.K_BACKSPACE:
            self.seeker_name = '' if ev.mod & pygame.KMOD_CTRL else self.seeker_name[:-1]
            self.line = ''
            return
        if k == pygame.K_v and ev.mod & pygame.KMOD_CTRL:
            text = ' '.join(self._paste().split())
            self.seeker_name = (self.seeker_name + text)[:seeker_profile.NAME_MAX]
            return
        ch = getattr(ev, 'unicode', '') or ''
        if len(ch) != 1 or not ch.isprintable():
            return
        if len(self.seeker_name) >= seeker_profile.NAME_MAX:
            self.line = "That's as long as a Seeker name can be."
            self.shake_t = self.t
            self.fx.play('refuse')
            return
        self.seeker_name += ch
        self.line = ''
        self.pop_t = self.t
        self.fx.play('key', 0.8)

    def _pull(self):
        """Enter or the lever: check the code with the Seeker name (and record a
        new one for the kid) now, then spin onto the answer."""
        if not core.clean_seeker_name(self.seeker_name):
            self._to_field('name')
            self.line = "Type the Seeker name first: the name on the kid's Seeker page in the game."
            self.shake_t = self.t
            self.fx.play('refuse')
            return
        e = self.entry
        if not e.dev and not e.complete:
            whole = core.complete_reading(self.raw, self.words)   # TABLE + T..., typed with no dash
            if whole:
                self.raw = whole
                self._typed('')
                e = self.entry
        if not e.dev and not e.complete:
            self._to_field('code')
            self.line = ("Type the whole code first: its word (any length), then eight letters and numbers."
                         if not e.empty else "Type the code the kid shows you, then press Enter.")
            self.shake_t = self.t
            self.fx.play('refuse')
            return
        self.seeker_name = core.clean_seeker_name(self.seeker_name)
        self.verdict = core.validate(self.name, e, self.seeker_name)
        self._spin()

    def _spin(self):
        """The lever comes down: the reels spin onto the answer already decided."""
        outcome = core.reel_outcome(self.verdict, self.pool, self.rng)
        self.plan = core.plan_reels(outcome, self.strips, self.rest)
        self.stops_heard = set()
        self.ticks = [int(math.floor(p + 0.5)) for p in self.plan.start]
        self.spin_t = 0.0
        self.go(SPIN)
        self.fx.play('lever')

    # spinning
    def _key_spin(self, ev):
        if ev.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
            if len(self.stops_heard) < core.REELS:
                self.fx.play('reel_stop', 0.9)
            self.spin_t = max(self.spin_t, core.ReelPlan.done_at())
            self.stops_heard = set(range(core.REELS))

    def _land(self):
        """The reels are still: the answer."""
        self.strips = self.plan.strips
        self.rest = list(self.plan.targets)
        v = self.verdict
        if v['status'] == 'new':
            self._celebrate()
        else:
            self.go(RESULT)
            if v['status'] == 'already':
                self.fx.play('chime', 0.9)
            elif v['status'] == 'duplicate':
                self.fx.play('chime', 0.6)
            elif v['status'] == 'dev':
                self.fx.play('secret', 0.8)
            else:
                self.fx.play('nope')

    def _celebrate(self):
        """A badge given: the kid's Seeker name is remembered (core.validate wrote it), then the party."""
        self.just = (core.normalise(self.name), self.verdict['achievement']['id'])
        self._refresh_counts()
        self.go(PARTY)
        self._party_start()

    def _give_anyway(self):
        """Enter on "Already Used": Dad gives the code to this kid too."""
        v = core.validate(self.name, self.entry, self.verdict.get('seeker') or self.seeker_name,
                          allow_duplicate=True)
        self.verdict = v
        if v['status'] == 'new':
            self._celebrate()

    def _party_start(self):
        a = self.verdict['achievement']
        col = self.rarity_colour(a['rarity'])
        _bpx, cx, cy = self._party_geom(self._body_rect())
        self.parts.clear()
        self.parts.burst(cx, cy, 220, self._confetti_colours(col), 1.1)
        self.fx.play('achievement', 0.9)
        self._stamp_heard = False

    def _confetti_colours(self, col):
        from fantasy_ui import FP
        return [col, col, FP.GOLD_BRIGHT, FP.VELLUM] + list(FP.SUBJECT.values())

    # results
    def _key_result(self, ev):
        k = ev.key
        dup = (self.verdict or {}).get('status') == 'duplicate'
        if k == pygame.K_TAB:
            self._cycle_tab(bool(ev.mod & pygame.KMOD_SHIFT))
        elif dup:
            # "Already Used": Enter gives it anyway; Esc (or Backspace, Space) goes back.
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self._give_anyway()
            elif k in (pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_SPACE):
                self._next(fresh=True)
        elif k == pygame.K_ESCAPE:
            self.go(KIDS)
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_BACKSPACE):
            self._next()
        elif k == pygame.K_SPACE:
            self._next(fresh=True)

    def _result_hint(self) -> str:
        v = self.verdict or {}
        if v.get('status') == 'duplicate':
            return f"Enter: give it to {self.name} anyway   Esc: back   Tab: Badge Library"
        if v.get('status') == 'fake':
            return ("Enter: fix the code or the name   Space: a new code   Tab: Badge Library   "
                    "Esc: choose a kid")
        return "Enter: next code   Tab: Badge Library   Esc: choose a kid"

    def _next(self, fresh=False):
        """Back to the slot for another code. A code that did not match stays,
        to be fixed (in its letters, or in the Seeker name above it)."""
        v = self.verdict or {}
        keep = v.get('status') == 'fake' and not fresh
        if keep and v.get('why') == 'name':
            self._to_field('name')
            self.line = "Type the Seeker name, then press Enter again."
        elif keep:
            self._to_field('code')
            self._typed("Fix the letters, or press Up to fix the Seeker name, then press Enter again.")
        else:
            self.raw = ''
            self._to_field('code')
            self._typed('')
        self.go(CODE)

    def _key_party(self, ev):
        k = ev.key
        if k == pygame.K_ESCAPE:
            self.go(KIDS)
        elif k == pygame.K_TAB:
            self._cycle_tab(bool(ev.mod & pygame.KMOD_SHIFT))
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
            if self.state_t < 0.6:
                return
            self._next(fresh=True)

    # the library
    def _key_tracker(self, ev):
        k = ev.key
        tr = self.track
        if k == pygame.K_ESCAPE:
            self.go(self.track_from if self.track_from in (KIDS, CODE) else KIDS)
        elif k == pygame.K_TAB:
            self._cycle_tab(bool(ev.mod & pygame.KMOD_SHIFT))
        elif k == pygame.K_l:
            self.click(('view', 'list' if self.view == 'grid' else 'grid'))
        elif k in (pygame.K_LEFTBRACKET, pygame.K_RIGHTBRACKET) and self.kids:
            self.click(('track_kid', -1 if k == pygame.K_LEFTBRACKET else 1))
        elif self.view == 'grid':
            rows = core.grid_rows(tr['sections'], self._grid_cols)
            moves = {pygame.K_LEFT: 'left', pygame.K_RIGHT: 'right', pygame.K_UP: 'up', pygame.K_DOWN: 'down',
                     pygame.K_a: 'left', pygame.K_d: 'right', pygame.K_w: 'up', pygame.K_s: 'down'}
            if k in moves:
                self.sel = core.grid_move(self.sel, moves[k], rows)
            elif k in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                self.sel = core.section_start(tr['sections'], self.sel, -1 if k == pygame.K_PAGEUP else 1)
            elif k == pygame.K_HOME:
                self.sel = 0
            elif k == pygame.K_END:
                self.sel = max(0, len(tr['entries']) - 1)
            else:
                return
            self._reveal = True
        else:
            n = len(tr['earned'])
            step = {pygame.K_UP: -1, pygame.K_w: -1, pygame.K_DOWN: 1, pygame.K_s: 1,
                    pygame.K_PAGEUP: -5, pygame.K_PAGEDOWN: 5, pygame.K_HOME: -n, pygame.K_END: n}.get(k)
            if step is None or not n:
                return
            self.list_sel = max(0, min(n - 1, self.list_sel + step))
            self._reveal = True

    # -- time ----------------------------------------------------------------------
    def update(self, dt):
        self.t += dt
        self.state_t += dt
        if self._warm and self.state in (KIDS, CODE, RESULT, TRACKER):
            reel_px = self._reel_px()
            for art, kind, won in self._warm[:4]:
                self.badge(art, reel_px if kind == 'reel' else S(64), won)
            del self._warm[:4]
        if self.state == SPIN:
            if self.spin_t < 0.30 <= self.spin_t + dt:
                self.fx.play('ratchet')                  # the handle springs back up
            self.spin_t += dt
            st = self.spin_t
            for k in range(core.REELS):
                if self.plan.stopped(k, st):
                    if k not in self.stops_heard:
                        self.stops_heard.add(k)
                        self.fx.play('reel_stop', 0.9)
                    continue
                cell = int(math.floor(self.plan.position(k, st) + 0.5))
                if cell != self.ticks[k]:
                    self.ticks[k] = cell
                    self.fx.play('tick', gap=0.045, now=self.t)
            if st >= core.ReelPlan.done_at() + core.HOLD:
                self._land()
        elif self.state == PARTY:
            W, _H = self.screen.get_size()
            a = self.verdict['achievement']
            col = self.rarity_colour(a['rarity'])
            if self.state_t < 6.0 and self.rng.random() < dt * 18:
                self.parts.rain(W, 2, self._confetti_colours(col))
            if self.rng.random() < dt * 10:
                bpx, cx, cy = self._party_geom(self._body_rect())
                self.parts.sparkle(cx, cy, bpx * 0.65, 1, [col, _ui().FP.VELLUM])
            if not self._stamp_heard and self.state_t >= 1.15:
                self._stamp_heard = True
                self.fx.play('stamp', 0.9)
                self.fx.play('coins', 0.7)
        self.parts.update(dt, self.screen.get_height())

    # -- drawing ----------------------------------------------------------------------
    def draw(self):
        self.hits = []
        self.screen.fill(_ui().KT.VOID)
        outer = self._outer()
        body = self._chrome(outer)
        if self.state == KIDS:
            self._draw_kids(body)
            hint = ("Left/Right: choose   Enter: check a code   T: Badge Library   +: add a name   "
                    "Del: take off the list   Esc: close")
            if self.adding is not None:
                hint = "Type a name   Enter: add   Esc: cancel"
            elif self.removing is not None:
                hint = "Y: yes, take it off   N: no"
        elif self.state in (CODE, SPIN, RESULT):
            self._draw_machine(body)
            hint = {CODE: "Up/Down: name or code   Enter: pull the lever   Backspace: fix   "
                          "Ctrl+V: paste   Tab: Badge Library   Esc: choose a kid",
                    SPIN: "Esc: skip the spin",
                    RESULT: self._result_hint()}[self.state]
            if self.state == RESULT:
                self._draw_result_card(body)
        elif self.state == PARTY:
            self._draw_party(body)
            hint = "Enter: check another code   Tab: Badge Library   Esc: choose a kid"
        else:
            self._draw_tracker(body)
            hint = ("Arrows: choose a badge   PgUp/PgDn: category   L: earned list   " if self.view == 'grid'
                    else "Up/Down: choose   L: all badges   ")
            hint += "[ / ]: another kid   Tab: switch   Esc: back"
        hint += "   " + self._sound_hint()
        self._footer(outer, hint)
        self.parts.draw(self.screen)

    def _outer(self):
        W, H = self.screen.get_size()
        return pygame.Rect(S(10), S(10), W - S(20), H - S(20))

    def _body_rect(self):
        """Where each screen draws: inside the window's panel, under the tabs, above the key hints."""
        ui = _ui()
        outer = self._outer()
        b = ui.panel_band('panel', outer)
        top = ui.header_rect(outer, S(48)).bottom + S(12) + S(30) + S(10)
        bottom = outer.bottom - b - S(8) - ui.key_hints_height() - S(28)
        side = b + S(22)
        return pygame.Rect(outer.x + side, top, outer.w - 2 * side, bottom - top)

    def _reel_px(self):
        _cab, _m, reels, _slot = self._machine_rects(self._body_rect())
        return min(int(self._reel_cell(reels[0]) * 0.84), reels[0].w - S(24))

    def _chrome(self, outer):
        """The window's panel, its title plaque and the tabs. Returns the body rect."""
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        ui.draw_dark_panel(self.screen, outer, border_color=FP.GOLD)
        hr = ui.draw_header_bar(self.screen, (outer.x, outer.y, outer.w, S(48)), text="Dad's Code Validator",
                                font=ui.get_font('heading', 28), accent=FP.GOLD, frame=(outer, FP.GOLD),
                                left_reserve=S(230), right_reserve=S(230))
        # The kid, on the plaque's left; the key's state on its right.
        f = ui.get_font('body', 16, bold=True)
        sy = hr.y + (hr.h - S(4) - f.get_height()) // 2
        if self.kids and self.state != KIDS:
            ts = f.render(f"For {self.name}", True, ui.readable(KT.TEXT_BODY, KT.PLAQUE))
            self.screen.blit(ts, (hr.x + S(40), sy))
        ks = f.render("Key Ready" if self.key_ok else "No Key", True,
                      ui.readable(KT.GOOD_TEXT if self.key_ok else KT.BAD_TEXT, KT.PLAQUE))
        self.screen.blit(ks, (hr.right - S(40) - ks.get_width(), sy))
        # Tabs.
        y = hr.bottom + S(12)
        cf = ui.get_font('body', 16, bold=True)
        labels = [(s, lab) for s, lab in TABS]
        widths = [cf.size(lab)[0] + S(34) for _s, lab in labels]
        gap = S(10)
        x = outer.centerx - (sum(widths) + gap * (len(widths) - 1)) // 2
        active = {RESULT: CODE, SPIN: CODE, PARTY: CODE}.get(self.state, self.state)
        import ui_theme
        for (s, lab), w in zip(labels, widths):
            r = pygame.Rect(x, y, w, S(30))
            on = s == active
            if ui_theme.draw_piece(self.screen, 'chip_active' if on else 'chip', r,
                                   accent=FP.GOLD if on else None):
                col = KT.TEXT_BODY if on else KT.TEXT_DIM
            else:
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID if on else FP.MIDNIGHT, r, border_radius=5)
                pygame.draw.rect(self.screen, FP.GOLD if on else FP.GOLD_DARK, r, 1, border_radius=5)
                col = FP.GOLD_BRIGHT if on else FP.FADED_TEXT
            ts = cf.render(lab, True, col)
            self.screen.blit(ts, (r.centerx - ts.get_width() // 2, r.centery - ts.get_height() // 2))
            self.hits.append((r, ('tab', s)))
            x += w + gap
        return self._body_rect()

    def _footer(self, outer, hint):
        ui = _ui()
        b = ui.panel_band('panel', outer)
        kh = ui.key_hints_height()
        keys = pygame.Rect(outer.x + b + S(20), outer.bottom - b - S(8) - kh, outer.w - 2 * (b + S(20)), kh)
        ui.draw_divider(self.screen, outer.x + b + S(28), keys.y - S(14), outer.w - 2 * (b + S(28)))
        ui.draw_key_hints(self.screen, keys, hint)

    def _text(self, text, font, colour, x, y, *, centre=False, shadow=False):
        ts = font.render(str(text), True, colour)
        if centre:
            x -= ts.get_width() // 2
        if shadow:
            from fantasy_ui import FP
            self.screen.blit(font.render(str(text), True, FP.INK), (x + S(2), y + S(2)))
        self.screen.blit(ts, (x, y))
        return ts

    def _wrap(self, text, font, width):
        from text_layout import wrap_lines
        return wrap_lines(str(text), max(1, int(width)), font)

    def _glow(self, colour, radius):
        """A soft round glow (cached per colour and size)."""
        def make():
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            for i in range(radius, 0, -max(1, radius // 14)):
                a = int(90 * (1 - i / radius) ** 1.6)
                pygame.draw.circle(s, (*colour[:3], a), (radius, radius), i)
            return s
        return self.cached(('glow', tuple(colour[:3]), radius), make)

    def _vgrad(self, w, h, top, bottom):
        def make():
            s = pygame.Surface((max(1, w), max(1, h)))
            for y in range(max(1, h)):
                k = y / max(1, h - 1)
                pygame.draw.line(s, tuple(int(top[i] + (bottom[i] - top[i]) * k) for i in range(3)),
                                 (0, y), (w, y))
            return s
        return self.cached(('vgrad', w, h, tuple(top), tuple(bottom)), make)

    # -- the kid cards -----------------------------------------------------------------
    def _draw_kids(self, body):
        ui = _ui()
        KT = ui.KT
        f_head = ui.get_font('title', 34)
        f_sub = ui.get_font('body', 18)
        y = body.y + S(6)
        self._text("Whose Code Is It?", f_head, KT.TEXT_HEAD, body.centerx, y, centre=True)
        y += f_head.get_height() + S(4)
        sub = "Choose the kid the badge is for, then type the Seeker name and the code he or she shows you."
        self._text(ui.fit_text(sub, f_sub, body.w - S(20)), f_sub, KT.TEXT_DIM, body.centerx, y, centre=True)
        y += f_sub.get_height() + S(18)
        notice_h = 0 if self.key_ok else S(132)
        area = pygame.Rect(body.x, y, body.w, body.bottom - y - notice_h - S(34))
        n = len(self.kids)
        gap = S(28)
        plus_w = S(170)
        card_w = min(S(300), (area.w - plus_w - gap * n) // max(1, n))
        card_h = min(area.h, S(420))
        total = n * card_w + plus_w + gap * n
        x = area.centerx - total // 2
        cy = area.y + (area.h - card_h) // 2
        for i, kid in enumerate(self.kids):
            r = pygame.Rect(x, cy, card_w, card_h)
            self._kid_card(r, kid, i == self.pick)
            self.hits.append((r, ('kid', i)))
            x += card_w + gap
        r = pygame.Rect(x, cy + (card_h - S(300)) // 2, plus_w, min(card_h, S(300)))
        self._plus_card(r, self.pick == n)
        self.hits.append((r, ('kid', n)))
        if self.note and self.t - self.note_t < 5:
            self._text(self.note, ui.get_font('body', 18, bold=True), KT.TEXT_QUIZ, body.centerx,
                       area.bottom + S(8), centre=True)
        if not self.key_ok:
            self._key_notice(pygame.Rect(body.x + S(40), body.bottom - notice_h, body.w - S(80), notice_h - S(6)))
        if self.removing is not None and self.removing < n:
            self._confirm_remove(self.kids[self.removing])

    def _kid_card(self, r, kid, sel):
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        import ui_theme
        lift = int(S(8) * (0.5 + 0.5 * math.sin(self.t * 3))) if sel else 0
        r = r.move(0, -lift)
        if sel:
            g = self._glow(FP.GOLD_BRIGHT, max(r.w, r.h) // 2 + S(30))
            self.screen.blit(g, (r.centerx - g.get_width() // 2, r.centery - g.get_height() // 2))
        if not ui_theme.draw_piece(self.screen, 'row_selected' if sel else 'card', r, body_color=KT.RAISED):
            pygame.draw.rect(self.screen, KT.SELECTED if sel else KT.RAISED, r, border_radius=10)
        pygame.draw.rect(self.screen, FP.GOLD_BRIGHT if sel else FP.GOLD_DARK, r, max(2, S(3)) if sel else 2,
                         border_radius=10)
        info = PORTRAITS.get(core.normalise(kid))
        well = pygame.Rect(r.x + S(18), r.y + S(18), r.w - S(36), r.w - S(36))
        well.h = min(well.h, r.h - S(162))
        pygame.draw.rect(self.screen, KT.WELL, well, border_radius=8)
        glow = self._glow(FP.ARCANE_BRIGHT if info and info[0] == 'player_wizard_f' else
                          FP.SUCCESS_TEXT if info else FP.GOLD, well.h // 2)
        self.screen.blit(glow, (well.centerx - glow.get_width() // 2, well.centery - glow.get_height() // 2))
        px = min(well.w, well.h) - S(16)
        spr = self.sprite(info[0], px) if info else None
        if spr is not None:
            self.screen.blit(spr, (well.centerx - px // 2, well.centery - px // 2))
        else:
            rad = px // 3
            pygame.draw.circle(self.screen, FP.GOLD_DARK, well.center, rad + S(4))
            pygame.draw.circle(self.screen, FP.MIDNIGHT_MID, well.center, rad)
            ft = ui.get_font('title', 64)
            ts = ft.render(kid[:1].upper(), True, FP.GOLD_BRIGHT)
            self.screen.blit(ts, (well.centerx - ts.get_width() // 2, well.centery - ts.get_height() // 2))
        pygame.draw.rect(self.screen, FP.GOLD_DARK, well, 1, border_radius=8)
        y = well.bottom + S(10)
        fn = ui.get_font('title', 32)
        self._text(ui.fit_text(kid, fn, r.w - S(20)), fn, KT.TEXT_HEAD, r.centerx, y, centre=True)
        y += fn.get_height() + S(2)
        fs = ui.get_font('body', 16)
        sub = info[1] if info else "Seeker"
        self._text(sub, ui.get_font('italic', 18), KT.TEXT_DIM, r.centerx, y, centre=True)
        y += ui.get_font('italic', 18).get_height() + S(4)
        got = self._counts.get(core.normalise(kid), 0)
        self._text(f"{got} of {len(self.achs)} badges claimed", fs, KT.TEXT_BODY, r.centerx, y, centre=True)
        plays = self._plays_as.get(core.normalise(kid))
        if plays and core.normalise(plays) != core.normalise(kid):
            y += fs.get_height() + S(4)
            fp = ui.get_font('italic', 16)
            self._text(ui.fit_text(f"Plays as: {plays}", fp, r.w - S(24)), fp, KT.TEXT_DIM, r.centerx, y,
                       centre=True)

    def _plus_card(self, r, sel):
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        import ui_theme
        if not ui_theme.draw_piece(self.screen, 'row_selected' if sel else 'row', r):
            pygame.draw.rect(self.screen, KT.SELECTED if sel else KT.RAISED, r, border_radius=10)
        pygame.draw.rect(self.screen, FP.GOLD_BRIGHT if sel else FP.GOLD_DARK, r, 2, border_radius=10)
        if self.adding is None:
            ft = ui.get_font('title', 64)
            self._text("+", ft, FP.GOLD_BRIGHT if sel else FP.GOLD, r.centerx, r.centery - ft.get_height() // 2 - S(14),
                       centre=True)
            fs = ui.get_font('body', 16, bold=True)
            self._text("Add a Name", fs, KT.TEXT_BODY, r.centerx, r.centery + S(30), centre=True)
            return
        fs = ui.get_font('body', 16, bold=True)
        self._text("New Name", fs, KT.TEXT_HEAD, r.centerx, r.y + S(26), centre=True)
        box = pygame.Rect(r.x + S(12), r.centery - S(22), r.w - S(24), S(44))
        fi = ui.get_font('body', 18, bold=True)
        shown = self.adding
        while shown and fi.size(shown)[0] > box.w - S(30):
            shown = shown[1:]
        ui.draw_input_box(self.screen, box, shown, fi, placeholder='Name')
        self._text("Enter: add", ui.get_font('body', 16), KT.TEXT_DIM, r.centerx, box.bottom + S(14), centre=True)

    def _key_notice(self, r):
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        shake = int(S(8) * math.sin((self.t - self.shake_t) * 40)) if self.t - self.shake_t < 0.35 else 0
        r = r.move(shake, 0)
        pygame.draw.rect(self.screen, FP.BURGUNDY_DARK, r, border_radius=8)
        pygame.draw.rect(self.screen, FP.DEATH_SUB, r, 2, border_radius=8)
        lines = core.key_help()
        fb = ui.get_font('body', 18, bold=True)
        f = ui.get_font('body', 16)
        y = r.y + S(12)
        self._text(lines[0], fb, KT.BAD_TEXT, r.centerx, y, centre=True)
        y += fb.get_height() + S(6)
        for line in lines[1:]:
            self._text(ui.fit_text(line, f, r.w - S(24)), f, KT.TEXT_BODY, r.centerx, y, centre=True)
            y += f.get_height() + S(4)

    def _confirm_remove(self, kid):
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        W, H = self.screen.get_size()
        ui.draw_overlay(self.screen, 170)
        r = pygame.Rect(0, 0, S(620), S(170))
        r.center = (W // 2, H // 2)
        ui.draw_dark_panel(self.screen, r, border_color=FP.GOLD)
        f = ui.get_font('heading', 24)
        self._text(f"Take {kid} off the list?", f, KT.TEXT_HEAD, r.centerx, r.y + S(30), centre=True)
        fs = ui.get_font('body', 16)
        self._text("The codes already claimed stay in the Badge Library.", fs, KT.TEXT_BODY, r.centerx,
                   r.y + S(78), centre=True)
        self._text("Y: Yes      N: No", ui.get_font('body', 18, bold=True), KT.TEXT_QUIZ, r.centerx,
                   r.y + S(114), centre=True)

    # -- the machine ---------------------------------------------------------------------
    def _machine_rects(self, body):
        lever_room = S(110)
        cw = min(body.w - lever_room - S(20), S(940))
        cab = pygame.Rect(body.centerx - (cw + lever_room) // 2, body.y + S(4), cw, body.h - S(8))
        marquee = pygame.Rect(cab.x + S(40), cab.y + S(30), cab.w - S(80), S(64))
        slot_h = S(150) + S(NAME_ROW)          # the Seeker name, then the code
        reels_top = marquee.bottom + S(20)
        reels_h = cab.bottom - S(30) - slot_h - S(16) - reels_top
        rw = (cab.w - S(110)) // 3
        reels = [pygame.Rect(cab.x + S(55) + k * rw + S(8), reels_top, rw - S(16), reels_h) for k in range(3)]
        slot = pygame.Rect(cab.x + S(40), cab.bottom - S(30) - slot_h, cab.w - S(80), slot_h)
        return cab, marquee, reels, slot

    def _draw_machine(self, body):
        ui = _ui()
        FP = ui.FP
        cab, marquee, reels, slot = self._machine_rects(body)
        st = self.spin_t if self.state in (SPIN, RESULT) else 0.0
        win = self.state in (SPIN, RESULT) and self.plan and self.plan.stopped(2, st) and \
            len(set(self.plan.outcome)) == 1
        # The lever, behind the cabinet's side.
        self._draw_lever(cab, reels)
        # The cabinet.
        body_s = self.cached(('cab', cab.size), lambda: self._cabinet_surface(cab.size))
        self.screen.blit(body_s, cab.topleft)
        self._draw_bulbs(cab, win)
        dup = win and self._duplicate()
        # The marquee.
        pygame.draw.rect(self.screen, FP.MIDNIGHT, marquee, border_radius=10)
        pygame.draw.rect(self.screen, FP.GOLD, marquee, 2, border_radius=10)
        ft = ui.get_font('title', 30)
        dots = ''
        if self.state == SPIN and not (self.plan and self.plan.stopped(2, st)):
            dots = '.' * (1 + int(self.t * 3) % 3)
            title = f"Checking {self.name}'s Code"
        elif self.state == RESULT and self.verdict:
            title = {'already': "A Real Code!", 'duplicate': "Already Used", 'dev': "A Practice Code",
                     'fake': "No Match"}.get(self.verdict['status'], "Checking")
        elif self.state == SPIN:
            title = "Already Used" if dup else "A Real Code!" if win else "Hmm..."
        else:
            title = f"{self.name}'s Code"
        title = ui.fit_text(title, ft, marquee.w - 2 * marquee.h - S(40))
        tx = marquee.centerx - ft.size(title)[0] // 2           # the dots never move the words
        ui.draw_glow_text(self.screen, ft, title + dots, FP.GOLD_BRIGHT,
                          (tx, marquee.centery - ft.get_height() // 2), glow_color=FP.GOLD_DARK, glow_r=2)
        info = PORTRAITS.get(core.normalise(self.name))
        spr = self.sprite(info[0], marquee.h - S(8)) if info else None
        if spr is not None:
            self.screen.blit(spr, (marquee.x + S(12), marquee.y + S(4)))
            self.screen.blit(pygame.transform.flip(spr, True, False),
                             (marquee.right - S(12) - spr.get_width(), marquee.y + S(4)))
        # The reels.
        for k, r in enumerate(reels):
            self._draw_reel(k, r, st)
        self._draw_payline(reels, win, st)
        # The code.
        self._draw_slot(slot)

    def _cabinet_surface(self, size):
        ui = _ui()
        FP = ui.FP
        w, h = size
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.blit(self._vgrad(w, h, FP.BURGUNDY, FP.BURGUNDY_DARK), (0, 0))
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=S(26))
        s.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        # A soft sheen down the middle (added light, so the edges stay dark), and the rims.
        sheen = pygame.Surface((w, h))
        for i in range(0, w // 2, 4):
            k = (1 - i / (w / 2)) ** 2
            col = (int(34 * k), int(22 * k), int(20 * k))
            pygame.draw.line(sheen, col, (w // 2 - i, 0), (w // 2 - i, h), 4)
            pygame.draw.line(sheen, col, (w // 2 + i, 0), (w // 2 + i, h), 4)
        s.blit(sheen, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        pygame.draw.rect(s, FP.GOLD, (0, 0, w, h), max(3, S(4)), border_radius=S(26))
        pygame.draw.rect(s, FP.GOLD_DARK, (S(9), S(9), w - S(18), h - S(18)), 2, border_radius=S(20))
        return s

    def _bulb_points(self, cab):
        def make():
            pts = []
            inset = S(16)
            r = cab.inflate(-2 * inset, -2 * inset)
            step = S(34)
            nx = max(2, r.w // step)
            ny = max(2, r.h // step)
            for i in range(nx):
                pts.append((r.x + r.w * i / nx, r.y))
            for i in range(ny):
                pts.append((r.right, r.y + r.h * i / ny))
            for i in range(nx):
                pts.append((r.right - r.w * i / nx, r.bottom))
            for i in range(ny):
                pts.append((r.x, r.bottom - r.h * i / ny))
            return [(int(x) - cab.x, int(y) - cab.y) for x, y in pts]
        return self.cached(('bulbs', cab.size), make)

    def _draw_bulbs(self, cab, win):
        ui = _ui()
        FP = ui.FP
        pts = self._bulb_points(cab)
        rad = S(5)
        status = self.verdict.get('status') if self.verdict and self.state in (SPIN, RESULT) else None
        if self.state == SPIN and not win:
            speed, colour = 14.0, FP.GOLD_BRIGHT
        elif win and self._duplicate():
            speed, colour = 2.5, FP.AMBER_ACCENT            # a real code used before: amber, slow
        elif win:
            colour = self.rarity_colour(self.verdict['achievement']['rarity']) if self.verdict.get(
                'achievement') else FP.GOLD_BRIGHT
            speed = None
        elif self.state == RESULT and status in ('fake', 'dev'):
            speed, colour = 1.5, FP.AMBER_ACCENT
        else:
            speed, colour = 4.0, FP.GOLD_BRIGHT
        on = (0, 1) if speed and speed > 10 else (0,)          # a fast chase lights two in four
        for i, (x, y) in enumerate(pts):
            if speed is None:
                lit = (int(self.t * 6) + i) % 2 == 0                # a win: every other bulb flashes
            else:
                lit = (i + int(self.t * speed)) % 4 in on
            X, Y = cab.x + x, cab.y + y
            pygame.draw.circle(self.screen, FP.INK, (X, Y), rad + S(2))
            if lit:
                g = self._glow(colour, rad * 4)
                self.screen.blit(g, (X - g.get_width() // 2, Y - g.get_height() // 2))
                pygame.draw.circle(self.screen, colour, (X, Y), rad)
                pygame.draw.circle(self.screen, (255, 255, 235), (X - rad // 3, Y - rad // 3), max(1, rad // 3))
            else:
                pygame.draw.circle(self.screen, tuple(int(c * 0.35) for c in colour), (X, Y), rad)

    def _lever_angle(self):
        """Degrees from straight up: 0 at rest, about 150 pulled right down."""
        if self.state != SPIN:
            return 0.0
        t = self.spin_t
        down, back = 0.22, 0.55
        if t < down:
            u = t / down
            return 150 * u * u
        if t < down + 0.08:
            return 150
        u = min(1.0, (t - down - 0.08) / back)
        u -= 1.0
        return 150 * (1 - (1 + 2.2 * u ** 3 + 1.2 * u ** 2))

    def _draw_lever(self, cab, reels):
        ui = _ui()
        FP = ui.FP
        pivot = (cab.right + S(26), reels[0].centery + S(20))
        L = S(150)
        th = math.radians(self._lever_angle())
        ball = (pivot[0] + int(S(18) * math.sin(th)), pivot[1] - int(L * math.cos(th)))
        rad = int(S(24) * (1 + 0.28 * math.sin(th)))
        # The housing on the cabinet's side.
        house = pygame.Rect(cab.right - S(6), pivot[1] - S(34), S(52), S(68))
        pygame.draw.rect(self.screen, FP.INK, house.inflate(S(4), S(4)), border_radius=S(10))
        pygame.draw.rect(self.screen, FP.GOLD_DARK, house, border_radius=S(10))
        pygame.draw.rect(self.screen, FP.GOLD, house, 2, border_radius=S(10))
        # The rod (lit on one side), then the ball.
        pygame.draw.line(self.screen, FP.INK, pivot, ball, S(14))
        pygame.draw.line(self.screen, (170, 170, 186), pivot, ball, S(10))
        pygame.draw.line(self.screen, (235, 235, 245), (pivot[0] - S(2), pivot[1]), (ball[0] - S(2), ball[1]), S(3))
        pygame.draw.circle(self.screen, FP.GOLD, pivot, S(14))
        pygame.draw.circle(self.screen, FP.GOLD_DARK, pivot, S(14), 2)
        hover = pygame.Rect(ball[0] - rad - S(10), ball[1] - rad - S(10), 2 * rad + S(20), 2 * rad + S(20))
        if self.state == CODE and self.entry.complete:
            g = self._glow(FP.DEATH_TITLE, rad * 2 + S(10))
            pulse = 0.6 + 0.4 * math.sin(self.t * 5)
            g2 = g.copy()
            g2.set_alpha(int(255 * pulse))
            self.screen.blit(g2, (ball[0] - g.get_width() // 2, ball[1] - g.get_height() // 2))
        pygame.draw.circle(self.screen, FP.INK, ball, rad + S(3))
        pygame.draw.circle(self.screen, FP.BLOOD, ball, rad)
        pygame.draw.circle(self.screen, FP.DEATH_TITLE, (ball[0] - rad // 4, ball[1] - rad // 4), rad // 2)
        pygame.draw.circle(self.screen, (255, 235, 230), (ball[0] - rad // 3, ball[1] - rad // 3), max(2, rad // 5))
        self.hits.append((hover, ('lever', None)))

    def _reel_cell(self, r):
        return max(S(60), int(r.h / 1.9))

    def _draw_reel(self, k, r, st):
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        cell = self._reel_cell(r)
        bpx = self._reel_px()
        plan = self.plan if self.state in (SPIN, RESULT) else None
        strip = plan.strips[k] if plan else self.strips[k]
        n = len(strip)
        if plan:
            p = plan.position(k, st)
            speed = (p - plan.position(k, st - 1 / 60)) * 60
        else:
            p, speed = float(self.rest[k]), 0.0
        self.screen.blit(self._vgrad(r.w, r.h, KT.WELL, KT.RAISED), r.topleft)
        mid = self._vgrad(r.w, r.h // 2, KT.RAISED, FP.MIDNIGHT_LIGHT)
        self.screen.blit(mid, (r.x, r.y))
        self.screen.blit(pygame.transform.flip(mid, False, True), (r.x, r.y + r.h // 2))
        old = self.screen.get_clip()
        self.screen.set_clip(r)
        cy = r.centery
        base = int(math.floor(p))
        blur = abs(speed) > 5
        for j in range(base - 2, base + 3):
            y = cy + (p - j) * cell
            if y < r.y - cell or y > r.bottom + cell:
                continue
            art = self.by_id.get(strip[j % n], {}).get('art', strip[j % n])
            if blur:
                b = self._blurred(art, bpx)
            else:
                b = self.badge(art, bpx)
            self.screen.blit(b, (r.centerx - b.get_width() // 2, int(y) - b.get_height() // 2))
        shade = self.cached(('reelshade', r.size), lambda: self._reel_shade(r.size))
        self.screen.blit(shade, r.topleft)
        self.screen.set_clip(old)
        pygame.draw.rect(self.screen, FP.INK, r.inflate(S(6), S(6)), S(4), border_radius=S(8))
        pygame.draw.rect(self.screen, FP.GOLD, r.inflate(S(2), S(2)), 2, border_radius=S(6))

    def _reel_shade(self, size):
        w, h = size
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        for y in range(h):
            d = abs(y - h / 2) / (h / 2)
            a = int(235 * max(0.0, d - 0.25) ** 1.4 / 0.75 ** 1.4)
            pygame.draw.line(s, (4, 4, 10, min(235, a)), (0, y), (w, y))
        return s

    def _draw_payline(self, reels, win, st):
        ui = _ui()
        FP = ui.FP
        cy = reels[0].centery
        left, right = reels[0].x - S(26), reels[-1].right + S(26)
        colour = FP.GOLD_BRIGHT
        if win:
            dup = self._duplicate()
            colour = FP.AMBER_ACCENT if dup else self.rarity_colour(self.verdict['achievement']['rarity'])
            cell = self._reel_cell(reels[0])
            pulse = 0.5 + 0.5 * math.sin(self.t * (3 if dup else 8))
            band = pygame.Rect(reels[0].x - S(8), cy - cell // 2, reels[-1].right - reels[0].x + S(16), cell)
            glow = pygame.Surface(band.size, pygame.SRCALPHA)
            pygame.draw.rect(glow, (*colour[:3], int(40 + 50 * pulse)), glow.get_rect(), border_radius=S(10))
            self.screen.blit(glow, band.topleft)
            pygame.draw.rect(self.screen, colour, band, max(2, S(3)), border_radius=S(10))
        for x, d in ((left, 1), (right, -1)):
            pts = [(x, cy - S(14)), (x + d * S(20), cy), (x, cy + S(14))]
            pygame.draw.polygon(self.screen, colour, pts)
            pygame.draw.polygon(self.screen, FP.INK, pts, 2)

    def _draw_slot(self, slot):
        """The two things Dad types: the Seeker name on top, then the code in
        its boxes, WORD - XXXX - XXXX. The field the keys go to is lit (a gold
        band and frame, its caret); a click on either one moves there."""
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        shake = int(S(10) * math.sin((self.t - self.shake_t) * 45)) if self.t - self.shake_t < 0.3 else 0
        slot = slot.move(shake, 0)
        pygame.draw.rect(self.screen, FP.INK, slot.inflate(S(6), S(6)), border_radius=S(12))
        pygame.draw.rect(self.screen, KT.WELL, slot, border_radius=S(12))
        pygame.draw.rect(self.screen, FP.GOLD_DARK, slot, 2, border_radius=S(12))
        typing = self.state == CODE
        name_area = pygame.Rect(slot.x, slot.y, slot.w, S(NAME_ROW))
        r = pygame.Rect(slot.x, name_area.bottom, slot.w, slot.bottom - name_area.bottom)
        active = self.field if typing else None
        for area, which in ((name_area, 'name'), (r, 'code')):
            band = area.inflate(-S(14), -S(10) if which == 'name' else -S(4))
            if active == which:
                glow = self.cached(('fieldband', band.size), lambda b=band: self._band_surface(b.size))
                self.screen.blit(glow, band.topleft)
                pygame.draw.rect(self.screen, FP.GOLD_BRIGHT, band, 2, border_radius=S(8))
            if typing:
                self.hits.append((band, ('field', which)))
        pygame.draw.line(self.screen, FP.GOLD_DARK, (slot.x + S(18), name_area.bottom),
                         (slot.right - S(18), name_area.bottom), 1)
        self._draw_name_field(name_area.inflate(-S(14), -S(10)), active == 'name')
        e = self.entry
        editing = typing                    # the code screen (either field)
        typing = active == 'code'           # the keys go to the code
        f_lab = ui.get_font('body', 16, bold=True)
        self._text("Type the Code", f_lab, KT.TEXT_HEAD if typing or not active else KT.TEXT_DIM,
                   r.centerx, r.y + S(8), centre=True)
        # The word's boxes: one per letter, one more for the next while it is
        # being typed. Before anything is typed, ONE wide box reading "any
        # length": code words run from 3 letters (MOO) to 12 (HUNDREDTRIPS),
        # and four ghost boxes spelling WORD read as "four letters" (Brandon,
        # 2026-11-17).
        empty_word = not e.word
        word_boxes = len(e.word) + (1 if editing and not e.in_chars and len(e.word) < core.WORD_MAX else 0)
        if empty_word:
            word_boxes = 6
        n = word_boxes + core.CHARS
        dash_w = S(26)
        dev_w = S(70) if e.dev else 0
        avail = r.w - S(40) - 2 * dash_w - dev_w
        bw = max(S(24), min(S(52), avail // n - S(4)))
        bh = int(bw * 1.3)
        gap = S(4)
        total = n * (bw + gap) - gap + 2 * dash_w + dev_w
        x = r.centerx - total // 2
        y = r.y + S(34)
        size = next((sz for sz in (36, 32, 28, 24, 20) if S(sz) <= bw * 0.78), 18)
        font = ui.get_font('mono', size, bold=True)
        if e.dev:
            chip = pygame.Rect(x, y + (bh - S(34)) // 2, dev_w - S(10), S(34))
            pygame.draw.rect(self.screen, FP.BURGUNDY, chip, border_radius=6)
            pygame.draw.rect(self.screen, FP.DEATH_SUB, chip, 2, border_radius=6)
            self._text("DEV", ui.get_font('body', 16, bold=True), KT.BAD_TEXT, chip.centerx,
                       chip.centery - S(9), centre=True)
            x += dev_w
        caret_on = typing and int(self.t * 2.2) % 2 == 0
        pop = max(0.0, 1 - (self.t - self.pop_t) / 0.15) if typing else 0.0
        last = (len(e.word) - 1) if not e.in_chars else word_boxes + len(e.chars) - 1
        word_col = FP.GOLD_BRIGHT if (e.known and e.in_chars) else \
            KT.TEXT_QUIZ if e.possible else KT.BAD_TEXT
        for i in range(n):
            if i == word_boxes or i == word_boxes + 4:
                pygame.draw.line(self.screen, FP.GOLD, (x + S(6), y + bh // 2), (x + dash_w - S(6), y + bh // 2),
                                 max(3, S(4)))
                x += dash_w
            if empty_word and i < word_boxes:
                if i == 0:
                    wide = pygame.Rect(x, y, word_boxes * (bw + gap) - gap, bh)
                    self._slot_box(wide, '', KT.TEXT_QUIZ, typing, caret_on, font, '', 0)
                    gf = ui.get_font('mono', max(16, size - 8), bold=True)
                    gs = gf.render("ANY LENGTH", True, KT.DIS_TEXT)
                    self.screen.blit(gs, (wide.centerx - gs.get_width() // 2, wide.centery - gs.get_height() // 2))
                x += bw + gap
                continue
            box = pygame.Rect(x, y, bw, bh)
            if i < word_boxes:
                ch = e.word[i] if i < len(e.word) else ''
                active = typing and not e.in_chars and i == len(e.word)
                col = word_col
            else:
                j = i - word_boxes
                ch = e.chars[j] if j < len(e.chars) else ''
                active = typing and e.in_chars and j == len(e.chars)
                col = KT.TEXT_QUIZ
            ghost = ''
            self._slot_box(box, ch, col, active, caret_on, font, ghost,
                           -int(S(6) * pop) if i == last else 0)
            x += bw + gap
        # The labels under the groups.
        fl = ui.get_font('body', 16)
        first = r.centerx - total // 2 + dev_w
        word_w = word_boxes * (bw + gap) - gap
        self._text("Word (any length)" if empty_word else "Word", fl, KT.TEXT_DIM,
                   first + word_w // 2, y + bh + S(4), centre=True)
        code_x = first + word_w + dash_w
        self._text("Eight Letters and Numbers", fl, KT.TEXT_DIM,
                   code_x + (8 * (bw + gap) + dash_w) // 2, y + bh + S(4), centre=True)
        line = self.line if editing else ''
        if typing and not line:
            line = core.hint(e) or ("Capitals and dashes are added for you. O counts as 0, I and L as 1."
                                    if not e.empty else "Type the code exactly as the kid shows it.")
        elif editing and not line:
            line = ("Type the name as the kid's Seeker page shows it, then press Down."
                    if not e.complete else "Press Enter to check the code with this name!")
        if line:
            lf = ui.get_font('body', 16, bold=True)
            col = KT.TEXT_QUIZ if e.complete else KT.TEXT_HINT
            self._text(ui.fit_text(line, lf, r.w - S(30)), lf, col, r.centerx, r.bottom - S(26), centre=True)

    def _band_surface(self, size):
        """The soft gold light behind the field the keys go to."""
        s = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(s, (*_ui().FP.GOLD_BRIGHT[:3], 34), s.get_rect(), border_radius=S(8))
        return s

    def _draw_name_field(self, r, active):
        """The Seeker name the code was earned under: its label, then the box."""
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        fl = ui.get_font('body', 16, bold=True)
        room = int(r.w * 0.56)
        label = next((lab for lab in NAME_LABELS if fl.size(lab)[0] <= room), NAME_LABELS[-1])
        lab_w = min(fl.size(label)[0], room)
        label = ui.fit_text(label, fl, lab_w)
        self._text(label, fl, KT.TEXT_HEAD if active or self.state != CODE else KT.TEXT_DIM,
                   r.x + S(12), r.centery - fl.get_height() // 2)
        bx = r.x + S(12) + lab_w + S(14)
        box = pygame.Rect(bx, r.y + S(5), r.right - S(10) - bx, r.h - S(10))
        self.screen.blit(self._vgrad(box.w, box.h, KT.RAISED, KT.WELL), box.topleft)
        pygame.draw.rect(self.screen, FP.GOLD_BRIGHT if active else FP.GOLD_DARK, box, 2 if active else 1,
                         border_radius=4)
        fi = ui.get_font('body', 20, bold=True)
        shown = self.seeker_name
        while shown and fi.size(shown)[0] > box.w - S(30):
            shown = shown[1:]
        tx = box.x + S(10)
        if shown:
            ts = fi.render(shown, True, KT.TEXT_QUIZ if active else KT.TEXT_BODY)
            dy = -int(S(4) * max(0.0, 1 - (self.t - self.pop_t) / 0.15)) if active else 0
            self.screen.blit(ts, (tx, box.centery - ts.get_height() // 2 + dy))
            cx = tx + ts.get_width() + S(3)
        else:
            ph = ui.get_font('italic', 18).render("The name the kid plays under", True, KT.DIS_TEXT)
            self.screen.blit(ph, (tx, box.centery - ph.get_height() // 2))
            cx = tx
        if active and int(self.t * 2.2) % 2 == 0:
            pygame.draw.rect(self.screen, FP.GOLD_BRIGHT, (cx, box.y + S(7), max(2, S(3)), box.h - S(14)))

    def _slot_box(self, box, ch, col, active, caret_on, font, ghost, dy):
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        self.screen.blit(self._vgrad(box.w, box.h, KT.RAISED, KT.WELL), box.topleft)
        pygame.draw.rect(self.screen, FP.GOLD_BRIGHT if active else FP.GOLD_DARK, box, 2 if active else 1,
                         border_radius=4)
        if ch:
            ts = font.render(ch, True, col)
            self.screen.blit(ts, (box.centerx - ts.get_width() // 2, box.centery - ts.get_height() // 2 + dy))
        elif ghost:
            ts = font.render(ghost, True, KT.DIS_TEXT)
            self.screen.blit(ts, (box.centerx - ts.get_width() // 2, box.centery - ts.get_height() // 2))
        if active and caret_on:
            pygame.draw.rect(self.screen, FP.GOLD_BRIGHT, (box.x + S(6), box.bottom - S(8), box.w - S(12), S(3)))

    # -- the result card ------------------------------------------------------------------
    def _draw_result_card(self, body):
        """The answer for a code that is not a new claim, laid over the code
        box at the foot of the machine (the reels stay in view above it)."""
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        v = self.verdict
        title, lines = core.result_lines(v)
        cab, _marquee, _reels, slot = self._machine_rects(body)
        k = min(1.0, self.state_t / 0.22)
        accent = {'already': FP.RARITY_RARE, 'dev': FP.ARCANE_BRIGHT}.get(v['status'], FP.AMBER_ACCENT)
        badge = v['status'] in ('already', 'duplicate')          # a real code: its badge and name
        fb = ui.get_font('body', 16)
        fn = ui.get_font('heading', 24)
        cw = min(S(920), body.w - S(20))
        probe = pygame.Rect(0, 0, cw, S(300))
        b = ui.panel_band('panel', probe)
        head = ui.header_rect(probe, S(44)).bottom
        well_px = S(120)
        text_x = b + S(22) + well_px + S(22)
        text_w = cw - text_x - b - S(22)
        wrapped = [part for line in lines for part in self._wrap(line, fb, text_w)]
        text_h = len(wrapped) * (fb.get_height() + S(4))
        if badge:
            text_h += fn.get_height() + S(26)
        ch = head + S(14) + max(well_px, text_h) + S(10) + fb.get_height() + S(12) + b
        ch = max(ch, slot.h + S(18))                    # covers the name and the code under it
        r = pygame.Rect(0, 0, cw, ch)
        r.midbottom = (cab.centerx, cab.bottom - S(12) + int(S(40) * (1 - k)))
        ui.draw_dark_panel(self.screen, r, border_color=accent)
        hr = ui.draw_header_bar(self.screen, (r.x, r.y, r.w, S(44)), text=title, font=ui.get_font('heading', 24),
                                accent=accent, frame=(r, accent))
        well = pygame.Rect(r.x + b + S(22), hr.bottom + S(14), well_px, well_px)
        pygame.draw.rect(self.screen, KT.WELL, well, border_radius=8)
        if badge:
            a = v['achievement']
            pygame.draw.rect(self.screen, accent if v['status'] == 'duplicate' else self.rarity_colour(a['rarity']),
                             well, 2, border_radius=8)
            bb = self.badge(a['art'], well_px - S(14))
            self.screen.blit(bb, (well.x + S(7), well.y + S(7)))
        else:
            pygame.draw.rect(self.screen, accent, well, 2, border_radius=8)
            fq = ui.get_font('title', 72 if v['status'] == 'fake' else 34)
            mark = fq.render("?" if v['status'] == 'fake' else "DEV", True, accent)
            self.screen.blit(mark, (well.centerx - mark.get_width() // 2, well.centery - mark.get_height() // 2))
        x = r.x + text_x
        y = hr.bottom + S(14)
        if badge:
            a = v['achievement']
            self._text(ui.fit_text(a['name'], fn, text_w), fn, KT.TEXT_HEAD, x, y)
            y += fn.get_height() + S(2)
            rr = f"{core.RARITY_NAMES.get(a['rarity'], '')}  ·  {core.FRAME_NAMES.get(a['rarity'], '')} Frame"
            self._text(rr, ui.get_font('body', 16, bold=True),
                       ui.readable(self.rarity_colour(a['rarity']), FP.MIDNIGHT), x, y)
            y += S(24)
        for part in wrapped:
            self._text(part, fb, KT.TEXT_BODY, x, y)
            y += fb.get_height() + S(4)
        checked = f"Code checked: {v.get('code', '')}"
        if v.get('seeker') and v['status'] != 'dev':
            checked += f"   Seeker name: {v['seeker']}"
        self._text(ui.fit_text(checked, fb, text_w), fb, KT.TEXT_DIM, x,
                   max(y + S(6), well.bottom - fb.get_height()))
        self.hits.append((r, ('next', None)))

    # -- the celebration --------------------------------------------------------------------
    def _party_geom(self, body):
        """(badge px, its centre x, y): the rings clear the tabs above it."""
        bpx = min(S(230), int(body.h * 0.38))
        return bpx, body.centerx, body.y + bpx // 2 + S(46)

    def _draw_party(self, body):
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        v = self.verdict
        a = v['achievement']
        col = self.rarity_colour(a['rarity'])
        t = self.state_t
        bpx, cx, cy = self._party_geom(body)
        # Rays turning behind the badge.
        R = int(max(body.w, body.h) * 0.75)
        layer = self.cached(('rays', body.size), lambda: pygame.Surface(body.size, pygame.SRCALPHA))
        layer.fill((0, 0, 0, 0))
        lx, ly = cx - body.x, cy - body.y
        for i in range(16):
            a0 = math.radians(i * 22.5 + t * 14)
            a1 = a0 + math.radians(9)
            pygame.draw.polygon(layer, (*col[:3], 30), [(lx, ly), (lx + R * math.cos(a0), ly + R * math.sin(a0)),
                                                        (lx + R * math.cos(a1), ly + R * math.sin(a1))])
        self.screen.blit(layer, body.topleft)
        g = self._glow(col, int(bpx * 0.95))
        self.screen.blit(g, (cx - g.get_width() // 2, cy - g.get_height() // 2))
        # Rings, then the badge popping in.
        for i in range(3):
            rr = bpx // 2 + S(14) + i * S(12) + int(S(4) * math.sin(t * 3 + i))
            pygame.draw.circle(self.screen, col, (cx, cy), rr, max(1, S(3) - i))
        pop = min(1.0, t / 0.45)
        scale = 1.0 + 0.18 * math.sin(math.pi * pop) if pop < 1 else 1.0
        size = max(8, int(bpx * (0.3 + 0.7 * pop) * scale))
        big = self.badge(a['art'], bpx)
        b = big if size == bpx else pygame.transform.smoothscale(big, (size, size))
        self.screen.blit(b, (cx - size // 2, cy - size // 2))
        # The words.
        y = cy + bpx // 2 + S(40)
        ft = ui.get_font('title', 40)
        line = f"{self.name} earned {a['name']}!"
        if ft.size(line)[0] > body.w - S(40):
            ft = ui.get_font('title', 30)
        line = ui.fit_text(line, ft, body.w - S(40))
        ui.draw_glow_text(self.screen, ft, line, FP.GOLD_BRIGHT,
                          (cx - ft.size(line)[0] // 2, y), glow_color=col, glow_r=3)
        y += ft.get_height() + S(6)
        rf = ui.get_font('heading', 22)
        rline = (f"{core.RARITY_NAMES.get(a['rarity'], '')}  ·  {core.FRAME_NAMES.get(a['rarity'], '')} Frame  ·  "
                 f"{v.get('category', '')}")
        self._text(rline, rf, ui.readable(col, KT.VOID), cx, y, centre=True)
        y += rf.get_height() + S(8)
        fi = ui.get_font('italic', 20)
        for part in self._wrap(a.get('unlocked_text', ''), fi, min(body.w - S(80), S(820)))[:2]:
            self._text(part, fi, KT.TEXT_BODY, cx, y, centre=True)
            y += fi.get_height() + S(2)
        y += S(10)
        # The reward.
        reward = core.reward_line(a)
        fr = ui.get_font('body', 20, bold=True)
        rw = min(body.w - S(120), max(S(520), fr.size(reward)[0] + S(60)))
        parts = self._wrap(reward, fr, rw - S(40))
        card = pygame.Rect(cx - rw // 2, y, rw, S(44) + len(parts) * (fr.get_height() + S(4)))
        import ui_theme
        if not ui_theme.draw_piece(self.screen, 'card', card, body_color=KT.RAISED):
            pygame.draw.rect(self.screen, KT.RAISED, card, border_radius=8)
        pygame.draw.rect(self.screen, col, card, 2, border_radius=8)
        self._text("Reward", ui.get_font('heading', 18, bold=True), KT.TEXT_HEAD, cx, card.y + S(8), centre=True)
        yy = card.y + S(34)
        for part in parts:
            self._text(part, fr, KT.TEXT_QUIZ, cx, yy, centre=True)
            yy += fr.get_height() + S(4)
        if body.bottom - card.bottom > S(30):
            self._text("Marked complete in the Badge Library.", ui.get_font('body', 16), KT.GOOD_TEXT, cx,
                       card.bottom + S(10), centre=True)
        # The stamp.
        if t >= 1.0:
            u = min(1.0, (t - 1.0) / 0.18)
            today = time.strftime('%Y-%m-%d')
            stamp = self.cached(('stamp', S(100), today), lambda: self._stamp_surface(today))
            z = 2.2 - 1.2 * u
            s2 = pygame.transform.rotozoom(stamp, 14, z)
            s2.set_alpha(int(255 * u))
            sx = cx + bpx // 2 + S(40)
            sy = cy + bpx // 2 - S(60)
            self.screen.blit(s2, (sx - s2.get_width() // 2, sy - s2.get_height() // 2))
        self.hits.append((body, ('next', None)))

    def _stamp_surface(self, today):
        ui = _ui()
        KT = ui.KT
        f1 = ui.get_font('title', 34)
        f2 = ui.get_font('heading', 17, bold=True)
        date = core.nice_date(today)
        w = max(f1.size("Claimed")[0], f2.size(date)[0]) + S(40)
        h = f1.get_height() + f2.get_height() + S(24)
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        ink = KT.GOOD_TEXT
        pygame.draw.rect(s, (*ink, 255), s.get_rect(), max(3, S(4)), border_radius=S(10))
        pygame.draw.rect(s, (*ink, 255), s.get_rect().inflate(-S(12), -S(12)), 1, border_radius=S(6))
        t1 = f1.render("Claimed", True, ink)
        t2 = f2.render(date, True, ink)
        s.blit(t1, (w // 2 - t1.get_width() // 2, S(10)))
        s.blit(t2, (w // 2 - t2.get_width() // 2, S(12) + t1.get_height()))
        return s

    # -- the library ------------------------------------------------------------------------
    def _draw_tracker(self, body):
        """The kid's badge library, as the game's Seeker gallery shows it:
        every badge by category (or, with L, the ones earned, newest first),
        and the picked badge's page beside them."""
        import seeker_screen
        tr = self.track or core.tracker(self.name)
        y = self._library_head(body, tr)
        left = pygame.Rect(body.x, y, int(body.w * 0.60), body.bottom - y)
        right = pygame.Rect(left.right + S(14), y, body.right - left.right - S(14), left.h)
        if self.view == 'grid':
            inner = seeker_screen._subpanel(self.screen, left,
                                            f"Every Badge: {tr['claimed']} of {tr['total']} Claimed")
            self._draw_grid(inner, tr)
            pick = tr['entries'][self.sel] if tr['entries'] else None
        else:
            inner = seeker_screen._subpanel(self.screen, left, f"Earned: {len(tr['earned'])}, Newest First")
            self._draw_earned(inner, tr)
            pick = tr['earned'][self.list_sel] if tr['earned'] else None
        self._draw_detail(seeker_screen._subpanel(self.screen, right, "Selected Badge"), pick)

    def _library_head(self, body, tr):
        """The kid (arrows to the others), the view chips and the counts. Returns the y below them."""
        import ui_theme
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        y = body.y
        fk = ui.get_font('title', 28)
        x = body.x
        many = len(self.kids) > 1
        af = ui.get_font('symbol', 20)

        def arrow(d, glyph, ax):
            r = pygame.Rect(ax, y + S(2), S(32), S(32))
            pygame.draw.rect(self.screen, KT.RAISED, r, border_radius=6)
            pygame.draw.rect(self.screen, FP.GOLD_DARK, r, 1, border_radius=6)
            self._text(glyph, af, KT.TEXT_HEAD, r.centerx, r.centery - af.get_height() // 2, centre=True)
            self.hits.append((r, ('track_kid', d)))
            return r.right + S(10)

        if many:
            x = arrow(-1, '◀', x)
        info = PORTRAITS.get(core.normalise(self.name))
        spr = self.sprite(info[0], S(40)) if info else None
        if spr is not None:
            self.screen.blit(spr, (x, y - S(2)))
            x += S(46)
        ts = self._text(f"{self.name}'s Badge Library", fk, KT.TEXT_HEAD, x, y)
        x += ts.get_width() + S(12)
        if many:
            arrow(1, '▶', x)
        # The two views.
        cf = ui.get_font('body', 16, bold=True)
        right = body.right
        for view, label in (('list', "Earned List"), ('grid', "All Badges")):     # from the right
            w = cf.size(label)[0] + S(30)
            r = pygame.Rect(right - w, y + S(2), w, S(30))
            on = self.view == view
            if ui_theme.draw_piece(self.screen, 'chip_active' if on else 'chip', r,
                                   accent=FP.GOLD if on else None):
                col = KT.TEXT_BODY if on else KT.TEXT_DIM
            else:
                pygame.draw.rect(self.screen, FP.MIDNIGHT_MID if on else FP.MIDNIGHT, r, border_radius=5)
                pygame.draw.rect(self.screen, FP.GOLD if on else FP.GOLD_DARK, r, 1, border_radius=5)
                col = FP.GOLD_BRIGHT if on else FP.FADED_TEXT
            self._text(label, cf, col, r.centerx, r.centery - cf.get_height() // 2, centre=True)
            self.hits.append((r, ('view', view)))
            right = r.x - S(8)
        y += max(fk.get_height(), S(36)) + S(6)
        # The counts, overall and by rarity.
        fc = ui.get_font('body', 16, bold=True)
        chips = [(f"Claimed {tr['claimed']} of {tr['total']}", FP.GOLD_BRIGHT, None)]
        for r_ in core.RARITIES:
            got, tot = tr['by_rarity'].get(r_, (0, 0))
            chips.append((f"{core.RARITY_NAMES[r_]} {got} / {tot}", self.rarity_colour(r_), r_))
        widths = [fc.size(c[0])[0] + S(38 if c[2] else 22) for c in chips]
        gap = S(10)
        x = body.centerx - (sum(widths) + gap * (len(widths) - 1)) // 2
        for (label, col, rar), w in zip(chips, widths):
            r = pygame.Rect(x, y, w, S(30))
            pygame.draw.rect(self.screen, KT.RAISED, r, border_radius=6)
            pygame.draw.rect(self.screen, col, r, 1, border_radius=6)
            tx = r.x + S(11)
            if rar:
                pygame.draw.circle(self.screen, col, (r.x + S(15), r.centery), S(6))
                pygame.draw.circle(self.screen, FP.INK, (r.x + S(15), r.centery), S(6), 1)
                tx = r.x + S(28)
            self._text(label, fc, ui.readable(col, KT.RAISED), tx, r.centery - fc.get_height() // 2)
            x += w + gap
        return y + S(30) + S(12)

    def _grid_layout(self, width, tr):
        """([(kind, rect, item, index, top of its section)], content height, columns).
        kind: 'head' (a category) or 'tile' (a badge)."""
        ui = _ui()
        fn = ui.get_font('body', 16)
        tile_w = max(S(118), fn.size('M')[0] * 12)        # a dozen letters a line, as the game sizes its tiles
        gap = S(8)
        cols = max(1, (width + gap) // (tile_w + gap))
        tile_w = (width - gap * (cols - 1)) // cols
        tile_h = S(8) + S(64) + S(6) + 2 * fn.get_height() + S(2) + fn.get_height() + S(6)
        head_h = S(32)
        out = []
        y = 0
        idx = 0
        for sec in tr['sections']:
            top = y
            out.append(('head', pygame.Rect(0, y, width, head_h), sec, -1, top))
            y += head_h + S(6)
            for i, e in enumerate(sec['entries']):
                rr, cc = divmod(i, cols)
                out.append(('tile', pygame.Rect(cc * (tile_w + gap), y + rr * (tile_h + gap), tile_w, tile_h),
                            e, idx, top if rr == 0 else None))
                idx += 1
            rows = -(-len(sec['entries']) // cols)
            y += rows * (tile_h + gap) + S(8)
        return out, y, cols

    def _new_here(self, tr):
        """The badge claimed last in this window, if it is this kid's."""
        return self.just[1] if self.just and self.just[0] == core.normalise(tr['seeker']) else None

    def _draw_grid(self, inner, tr):
        import seeker_screen
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        lane = S(14)
        width = inner.w - lane
        key = ('grid', width, ui_scale.get(), id(tr))
        lay = self._cache.get('gridlay')
        if not lay or lay[0] != key:
            lay = (key,) + self._grid_layout(width, tr)
            self._cache['gridlay'] = lay
        _k, items, content_h, self._grid_cols = lay
        max_scroll = max(0, content_h - inner.h)
        if self._reveal:
            self._reveal = False
            for kind, r, _item, idx, top in items:
                if kind == 'tile' and idx == self.sel:
                    want_top = top if top is not None else r.y - S(4)
                    if want_top < self.scroll:
                        self.scroll = want_top
                    elif r.bottom + S(4) > self.scroll + inner.h:
                        self.scroll = r.bottom + S(4) - inner.h
                    break
        self.scroll = max(0.0, min(float(self.scroll), float(max_scroll)))
        off = int(self.scroll)
        new = self._new_here(tr)
        old = self.screen.get_clip()
        self.screen.set_clip(inner.inflate(S(4), S(4)).clip(old))
        fh = ui.get_font('heading', 20)
        fc = ui.get_font('body', 16, bold=True)
        fn = ui.get_font('body', 16)
        built = 0
        for kind, r, item, idx, _top in items:
            rr = r.move(inner.x, inner.y - off)
            if rr.bottom < inner.y - S(4) or rr.y > inner.bottom + S(4):
                continue
            if kind == 'head':
                self._text(item['name'], fh, KT.TEXT_HEAD, rr.x, rr.y + S(2))
                cs = fc.render(f"{item['claimed']} of {item['total']} claimed", True, KT.TEXT_DIM)
                self.screen.blit(cs, (rr.right - cs.get_width(), rr.y + S(6)))
                pygame.draw.line(self.screen, FP.GOLD_DARK, (rr.x, rr.bottom - S(3)), (rr.right, rr.bottom - S(3)))
                continue
            claimed = item['claimed']
            if idx == self.sel:
                seeker_screen._row_bg(self.screen, rr, True)
                pygame.draw.rect(self.screen, FP.GOLD_BRIGHT, rr, 2, border_radius=6)
            else:
                pygame.draw.rect(self.screen, KT.SELECTED if claimed else KT.WELL, rr, border_radius=6)
                pygame.draw.rect(self.screen, self.rarity_colour(item['rarity']) if claimed else KT.LINE, rr,
                                 1, border_radius=6)
            bk = (item['art'], S(64), claimed)
            if bk in self._badges or built < 16:
                built += bk not in self._badges
                b = self.badge(item['art'], S(64), claimed)
                self.screen.blit(b, (rr.centerx - b.get_width() // 2, rr.y + S(8)))
            else:
                pygame.draw.circle(self.screen, KT.LINE, (rr.centerx, rr.y + S(8) + S(32)), S(30), 1)
            ty = rr.y + S(8) + S(64) + S(6)
            col = KT.TEXT_BODY if claimed else KT.TEXT_DIM
            for line in self._wrap(item['name'], fn, rr.w - S(10))[:2]:
                self._text(line, fn, col, rr.centerx, ty, centre=True)
                ty += fn.get_height()
            ty = rr.bottom - S(6) - fn.get_height()
            if claimed:
                self._text(core.nice_date(item['date'], short=True), fc, KT.GOOD_TEXT, rr.centerx, ty, centre=True)
            else:
                self._text("Not yet", fn, KT.DIS_TEXT, rr.centerx, ty, centre=True)
            if item['id'] == new:
                self._new_chip(rr)
            vis = rr.clip(inner)
            if vis.w and vis.h:
                self.hits.append((vis, ('badge', idx)))
        self.screen.set_clip(old)
        self._scrollbar(inner, off, content_h, max_scroll)

    def _new_chip(self, rr):
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        fc = ui.get_font('body', 16, bold=True)
        ns = fc.render("New", True, KT.TEXT_QUIZ)
        chip = pygame.Rect(0, 0, ns.get_width() + S(12), ns.get_height() + S(2))
        chip.topright = (rr.right - S(4), rr.y + S(4))
        pygame.draw.rect(self.screen, FP.BURGUNDY, chip, border_radius=5)
        pygame.draw.rect(self.screen, FP.ACHIEVEMENT, chip, 1, border_radius=5)
        self.screen.blit(ns, (chip.centerx - ns.get_width() // 2, chip.centery - ns.get_height() // 2))

    def _scrollbar(self, inner, off, content_h, max_scroll):
        if max_scroll <= 0:
            return
        FP = _ui().FP
        track = pygame.Rect(inner.right - S(6), inner.y, S(6), inner.h)
        pygame.draw.rect(self.screen, FP.MIDNIGHT, track, border_radius=3)
        th = max(S(30), int(track.h * inner.h / max(1, content_h)))
        ty = track.y + int((track.h - th) * (off / max_scroll))
        pygame.draw.rect(self.screen, FP.GOLD_DARK, (track.x, ty, track.w, th), border_radius=3)

    def _draw_earned(self, inner, tr):
        """The badges earned, newest first: badge, name, rarity and the day claimed."""
        import seeker_screen
        ui = _ui()
        FP, KT = ui.FP, ui.KT
        rows = tr['earned']
        if not rows:
            f = ui.get_font('heading', 22)
            fs = ui.get_font('body', 16)
            self._text("No badges claimed yet.", f, KT.TEXT_HEAD, inner.centerx, inner.centery - S(30), centre=True)
            self._text(f"When {self.name} shows you a code, the badge lands here.", fs, KT.TEXT_DIM,
                       inner.centerx, inner.centery + S(6), centre=True)
            return
        lane = S(14)
        row_h, gap = S(74), S(8)
        width = inner.w - lane
        content_h = len(rows) * (row_h + gap) - gap
        max_scroll = max(0, content_h - inner.h)
        self.list_sel = max(0, min(self.list_sel, len(rows) - 1))
        if self._reveal:
            self._reveal = False
            top = self.list_sel * (row_h + gap)
            if top < self.list_scroll:
                self.list_scroll = top
            elif top + row_h > self.list_scroll + inner.h:
                self.list_scroll = top + row_h - inner.h
        self.list_scroll = max(0.0, min(float(self.list_scroll), float(max_scroll)))
        off = int(self.list_scroll)
        new = self._new_here(tr)
        fn = ui.get_font('heading', 20)
        fr = ui.get_font('body', 16)
        fd = ui.get_font('body', 16, bold=True)
        bpx = S(58)
        old = self.screen.get_clip()
        self.screen.set_clip(inner.inflate(S(4), S(4)).clip(old))
        for i, e in enumerate(rows):
            rr = pygame.Rect(inner.x, inner.y + i * (row_h + gap) - off, width, row_h)
            if rr.bottom < inner.y or rr.y > inner.bottom:
                continue
            col = self.rarity_colour(e['rarity'])
            if i == self.list_sel:
                seeker_screen._row_bg(self.screen, rr, True)
                pygame.draw.rect(self.screen, FP.GOLD_BRIGHT, rr, 2, border_radius=6)
            else:
                pygame.draw.rect(self.screen, KT.SELECTED, rr, border_radius=6)
                pygame.draw.rect(self.screen, col, rr, 1, border_radius=6)
            b = self.badge(e['art'], bpx)
            self.screen.blit(b, (rr.x + S(10), rr.centery - bpx // 2))
            date = core.nice_date(e['date'], short=True)
            ds = fd.render(date, True, KT.GOOD_TEXT)
            dx = rr.right - S(14) - ds.get_width()
            tx = rr.x + S(10) + bpx + S(14)
            name = ui.fit_text(e['name'], fn, dx - tx - S(12))
            self._text(name, fn, KT.TEXT_HEAD, tx, rr.y + S(10))
            rline = f"{core.RARITY_NAMES.get(e['rarity'], '')}  ·  {e.get('category_name', '')}"
            self._text(ui.fit_text(rline, fr, dx - tx - S(12)), fr, ui.readable(col, KT.SELECTED), tx,
                       rr.y + S(14) + fn.get_height())
            self.screen.blit(ds, (dx, rr.centery - ds.get_height() // 2))
            if e['id'] == new:
                self._new_chip(pygame.Rect(rr.x, rr.y, bpx + S(30), row_h))
            vis = rr.clip(inner)
            if vis.w and vis.h:
                self.hits.append((vis, ('row', i)))
        self.screen.set_clip(old)
        self._scrollbar(inner, off, content_h, max_scroll)

    def _draw_detail(self, body, e):
        """The picked badge's page (the Seeker gallery's "Selected Achievement")."""
        ui = _ui()
        KT = ui.KT
        if e is None:
            self._text("Nothing to show yet.", ui.get_font('body', 16), KT.TEXT_DIM, body.centerx,
                       body.y + S(20), centre=True)
            return
        claimed = e['claimed']
        col = self.rarity_colour(e['rarity'])
        dp = max(S(64), min(S(128), int(body.w * 0.40)))
        pad = S(6)
        well = pygame.Rect(body.x, body.y, dp + 2 * pad, dp + 2 * pad)
        pygame.draw.rect(self.screen, KT.WELL, well)
        pygame.draw.rect(self.screen, col if claimed else KT.LINE, well, max(2, S(2)) if claimed else 1)
        self.screen.blit(self.badge(e['art'], dp, claimed), (well.x + pad, well.y + pad))
        bg = KT.RAISED
        fonts = {'name': ui.get_font('heading', 24), 'rarity': ui.get_font('body', 16),
                 'category': ui.get_font('body', 16),
                 'claimed': ui.get_font('body', 16, bold=True), 'locked': ui.get_font('body', 16),
                 'head': ui.get_font('body', 16, bold=True), 'hint': ui.get_font('body', 18),
                 'text': ui.get_font('body', 18)}
        colours = {'name': ui.readable(KT.TEXT_HEAD, bg), 'rarity': ui.readable(col, bg),
                   'category': ui.readable(KT.TEXT_DIM, bg),
                   'claimed': ui.readable(KT.OK_TEXT, bg), 'locked': ui.readable(KT.TEXT_DIM, bg),
                   'head': ui.readable(KT.TEXT_SUB, bg), 'hint': ui.readable(KT.TEXT_QUIZ, bg),
                   'text': ui.readable(KT.TEXT_BODY, bg)}
        lines = core.detail_lines(e)
        cx = well.right + S(16)
        col_w = body.right - cx - S(4)
        y = body.y + S(2)
        under = []
        prev = None
        for text, kind in lines:
            if kind in ('head', 'hint', 'text'):
                under.append((text, kind))
                continue
            if prev is not None and prev != kind:
                y += S(4)
            for part in self._wrap(text, fonts[kind], col_w):
                self._text(part, fonts[kind], colours[kind], cx, y)
                y += fonts[kind].get_height() + S(2)
            prev = kind
        y = max(y, well.bottom) + S(14)
        for text, kind in under:
            for part in self._wrap(text, fonts[kind], body.w - S(4)):
                if y + fonts[kind].get_height() > body.bottom:
                    return
                self._text(part, fonts[kind], colours[kind], body.x, y)
                y += fonts[kind].get_height() + S(3)
            y += S(4)
        # A ladder's rungs, as the game draws them.
        rungs = e.get('ladder') or []
        if len(rungs) > 1 and y + S(30) <= body.bottom:
            y += S(8)
            r = S(6)
            x = body.x + r
            fm = fonts['locked']
            mid = y + fm.get_height() // 2
            for t in rungs:
                c = self.rarity_colour(t['rarity'])
                if t['claimed']:
                    pygame.draw.circle(self.screen, c, (x, mid), r)
                else:
                    pygame.draw.circle(self.screen, KT.LINE, (x, mid), r, max(1, S(2)))
                if t['id'] == e['id']:
                    pygame.draw.circle(self.screen, KT.TEXT_HEAD, (x, mid), r + S(3), 1)
                x += 3 * r + S(2)
            self._text(f"Tier {e['tier']} of {len(rungs)}", fm, colours['locked'], x + S(6), y)

    # -- the loop ---------------------------------------------------------------------------
    def run(self):
        clock = pygame.time.Clock()
        while not self.quit:
            dt = min(0.05, clock.tick(FPS) / 1000.0)
            for ev in pygame.event.get():
                self.handle(ev)
            self.update(dt)
            self.draw()
            pygame.display.flip()


def open_window(size=SIZE):
    try:
        import display_setup
        display_setup.enable_dpi_awareness()
    except Exception:
        pass
    pygame.init()
    screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    pygame.display.set_caption("Dad's Code Validator")
    try:
        pygame.display.set_window_minimum_size(*MIN_SIZE)
    except Exception:
        pass
    try:
        from paths import data_path
        pygame.display.set_icon(pygame.image.load(data_path('assets', 'achievements', 'questions_100.png')))
    except Exception:
        pass
    return screen


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        app = App(open_window(), sound='--no-sound' not in argv)
        app.run()
    except Exception:
        text = traceback.format_exc()
        path = os.path.join(dadlib.dad_dir(), 'code_validator_error.txt')
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
        except OSError:
            path = ''
        try:
            pygame.display.message_box("Dad's Code Validator",
                                       "Something went wrong and the validator has to close.\n\n"
                                       + (f"The details are in {path}" if path else text[-800:]),
                                       message_type='error')
        except Exception:
            print(text, file=sys.stderr)
        return 1
    finally:
        pygame.quit()
    return 0


if __name__ == '__main__':
    sys.exit(main())
