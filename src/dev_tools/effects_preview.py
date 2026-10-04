"""Effects preview harness -- standalone pygame window.

Phase 2 of CHAIN_EFFECTS_PLAN.md (2026-10-03). Lets a developer drive
the actual ``EffectsRuntime`` (not a mock) with keyboard controls so
the chain-aura ranks + milestone bursts + fullscreen takeovers can be
tuned visually without running a full combat loop.

Run interactively:

    python src/dev_tools/effects_preview.py

Keyboard controls:

    [ / ]   chain down / up
    R       simulate correct answer (bumps asked_count + last_correct=True)
    W       simulate wrong answer
    T       simulate timeout
    N       new session (increments session_id, resets handler state)
    M       toggle reduced motion (reload runtime)
    C       toggle context-pause (sets paused=True on runtime.update)
    D       fire divine_intercession_takeover
    U       fire unicorn_bond_takeover
    I       fire identify_success_orb (Phase 3 handler, if registered)
    ESC     quit

Capture mode (headless-ish, cycles states and saves PNGs):

    python src/dev_tools/effects_preview.py --capture

Captures land in ``docs/audits/effects_preview_YYYY-MM-DD/`` with a
``reduced/`` subfolder for the ``PQ_REDUCED_MOTION=1`` pass and a
dedicated set for the two takeovers.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import os
import sys
from pathlib import Path
from typing import Optional


# Make src/ importable when running from the project root as a script.
_SRC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SRC))


def _lazy_imports():
    """Imports deferred so the module file is importable without pygame
    (e.g. for lint tooling). Returns the handful of names we need."""
    import pygame  # noqa: WPS433 -- deliberate lazy import
    import layout
    from effects_runtime import build_default_runtime
    from fantasy_ui import get_font, make_parchment
    return pygame, layout, build_default_runtime, get_font, make_parchment


# ---------------------------------------------------------------------------
# Preview state
# ---------------------------------------------------------------------------

class PreviewState:
    """Mutable harness state. Mirrors the fields ``main.Game.update``
    builds into a quiz snapshot every frame."""

    def __init__(self) -> None:
        self.chain: int = 0
        self.asked_count: int = 0
        self.correct_count: int = 0
        self.last_correct: Optional[bool] = None
        self.quiz_state: str = 'ASKING'
        self.subject: str = 'math'
        self.mode: str = 'chain'
        self.has_combat_target: bool = True
        self.session_id: int = 1
        self.paused: bool = False

    # -- transitions mirroring real quiz events ---------------------
    def answer_correct(self) -> None:
        self.chain += 1
        self.asked_count += 1
        self.correct_count += 1
        self.last_correct = True

    def answer_wrong(self) -> None:
        self.chain = 0
        self.asked_count += 1
        self.last_correct = False

    def answer_timeout(self) -> None:
        self.asked_count += 1
        self.last_correct = None  # engine convention for timeout

    def new_session(self) -> None:
        self.chain = 0
        self.asked_count = 0
        self.correct_count = 0
        self.last_correct = None
        self.session_id += 1

    def snapshot(self) -> dict:
        return {
            'subject': self.subject,
            'mode': self.mode,
            'chain': self.chain,
            'asked_count': self.asked_count,
            'correct_count': self.correct_count,
            'last_correct': self.last_correct,
            'quiz_state': self.quiz_state,
            'has_combat_target': self.has_combat_target,
            'state': 'STATE_QUIZ',
        }


# ---------------------------------------------------------------------------
# Drawing helpers (preview chrome -- NOT part of the real game UI)
# ---------------------------------------------------------------------------

def _draw_quiz_panel(pygame, surface, layout, panel_rect, state: PreviewState,
                     font_heading, font_body, font_small) -> list:
    """Paint a representative quiz panel so the aura has something to
    hug. Returns a list of 'protected' rects (text / counters) that
    the effect runtime should NOT paint into."""
    # Opaque panel background -- the game uses parchment; we use a
    # muted dark fill so the aura reads clearly in captures.
    pygame.draw.rect(surface, (28, 24, 36), panel_rect, border_radius=14)
    pygame.draw.rect(surface, (120, 110, 90), panel_rect, width=2,
                     border_radius=14)

    protected: list = []
    pad = 24

    # Header: subject + chain
    header = font_heading.render(
        f'{state.subject.upper()} CHAIN QUIZ',
        True, (240, 230, 200))
    header_pos = (panel_rect.x + pad, panel_rect.y + pad)
    surface.blit(header, header_pos)
    protected.append(pygame.Rect(header_pos[0], header_pos[1],
                                 header.get_width(), header.get_height()))

    # Chain counter (top-right)
    counter_text = f'{state.chain}'
    counter = font_heading.render(counter_text, True, (255, 220, 120))
    counter_pos = (panel_rect.right - pad - counter.get_width(),
                   panel_rect.y + pad)
    surface.blit(counter, counter_pos)
    protected.append(pygame.Rect(counter_pos[0], counter_pos[1],
                                 counter.get_width(),
                                 counter.get_height()))

    # Faux question text
    qline = font_body.render('What is 7 x 8?', True, (240, 230, 220))
    qpos = (panel_rect.x + pad, panel_rect.y + 90)
    surface.blit(qline, qpos)
    protected.append(pygame.Rect(qpos[0], qpos[1],
                                 qline.get_width(), qline.get_height()))

    # Four faux choice cards
    choice_rows = [('A', '54'), ('B', '56'), ('C', '48'), ('D', '63')]
    cy = panel_rect.y + 150
    for i, (letter, val) in enumerate(choice_rows):
        row_rect = pygame.Rect(panel_rect.x + pad, cy + i * 36,
                               panel_rect.w - pad * 2, 30)
        pygame.draw.rect(surface, (46, 40, 60), row_rect,
                         border_radius=6)
        label = font_small.render(f'{letter}) {val}', True, (220, 215, 200))
        surface.blit(label, (row_rect.x + 10, row_rect.y + 4))
        protected.append(row_rect)

    # Timer bar at the bottom
    tbar = pygame.Rect(panel_rect.x + pad,
                       panel_rect.bottom - 24,
                       panel_rect.w - pad * 2, 10)
    pygame.draw.rect(surface, (90, 80, 60), tbar, border_radius=4)
    pygame.draw.rect(surface, (240, 220, 110),
                     pygame.Rect(tbar.x, tbar.y,
                                 int(tbar.w * 0.6), tbar.h),
                     border_radius=4)
    protected.append(tbar)

    return protected


def _rank_name(chain: int) -> str:
    """Mirror the effects_config.json rank thresholds for the preview
    overlay text."""
    for threshold, name in (
        (20, 'Mythic'),
        (15, 'Prodigy'),
        (10, 'Genius'),
        (8, 'Brilliant'),
        (5, 'Sharp'),
        (3, 'Solid'),
        (1, ''),
        (0, ''),
    ):
        if chain >= threshold:
            return name
    return ''


def _draw_hud(pygame, surface, state: PreviewState, runtime,
              font_small) -> None:
    """Bottom-left state readout + top controls hint."""
    lines = [
        '[ / ]  chain down/up    R correct    W wrong    T timeout    '
        'N new-session',
        'M reduced-motion    C pause    D divine takeover    '
        'U unicorn takeover    I identify orb    ESC quit',
    ]
    y = 10
    for line in lines:
        surf = font_small.render(line, True, (180, 180, 160))
        surface.blit(surf, (10, y))
        y += surf.get_height() + 2

    status = (f'session={state.session_id} chain={state.chain} '
              f'rank={_rank_name(state.chain) or "-"} '
              f'reduced_motion={runtime.reduced_motion} '
              f'paused={state.paused}')
    status_surf = font_small.render(status, True, (210, 210, 180))
    surface.blit(status_surf,
                 (10, surface.get_height() - status_surf.get_height() - 10))


# ---------------------------------------------------------------------------
# Interactive main loop
# ---------------------------------------------------------------------------

def run_interactive() -> int:
    pygame, layout, build_default_runtime, get_font, _make = _lazy_imports()
    pygame.init()
    pygame.display.set_caption('Effects Preview -- Chain Aura + Takeovers')
    screen = pygame.display.set_mode((layout.WINDOW_W, layout.WINDOW_H))
    clock = pygame.time.Clock()

    runtime = build_default_runtime()
    state = PreviewState()

    font_heading = get_font('heading', 28)
    font_body = get_font('body', 22)
    font_small = get_font('small', 16)

    # Representative panel rect (center of screen, generous size).
    panel_rect = pygame.Rect(0, 0, 760, 360)
    panel_rect.center = (layout.WINDOW_W // 2, layout.WINDOW_H // 2 + 20)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_LEFTBRACKET:
                    state.chain = max(0, state.chain - 1)
                elif event.key == pygame.K_RIGHTBRACKET:
                    state.chain += 1
                    state.asked_count += 1
                    state.correct_count += 1
                    state.last_correct = True
                elif event.key == pygame.K_r:
                    state.answer_correct()
                elif event.key == pygame.K_w:
                    state.answer_wrong()
                elif event.key == pygame.K_t:
                    state.answer_timeout()
                elif event.key == pygame.K_n:
                    state.new_session()
                    runtime.reset_scope(state.session_id - 1)
                elif event.key == pygame.K_m:
                    # Flip env var + rebuild runtime so the new mode
                    # takes effect this frame.
                    new_val = '0' if runtime.reduced_motion else '1'
                    if new_val == '1':
                        os.environ['PQ_REDUCED_MOTION'] = '1'
                    else:
                        os.environ.pop('PQ_REDUCED_MOTION', None)
                    runtime = build_default_runtime()
                elif event.key == pygame.K_c:
                    state.paused = not state.paused
                elif event.key == pygame.K_d:
                    runtime.fire('divine_intercession_takeover', {})
                elif event.key == pygame.K_u:
                    runtime.fire('unicorn_bond_takeover', {})
                elif event.key == pygame.K_i:
                    if 'identify_success_orb' in runtime.handlers:
                        runtime.fire('identify_success_orb', {})
                    else:
                        print('[preview] identify_success_orb not '
                              'registered (Phase 3 handler missing)',
                              file=sys.stderr)

        # Pipe current state into the runtime.
        runtime.observe(state.session_id, state.snapshot())
        runtime.update(dt, paused=state.paused)

        # Paint frame.
        screen.fill((16, 14, 24))
        runtime.draw_background(screen, panel_rect)
        protected = _draw_quiz_panel(pygame, screen, layout, panel_rect,
                                     state, font_heading, font_body,
                                     font_small)
        runtime.draw_foreground(screen, protected)
        runtime.draw_top_overlay(screen)
        _draw_hud(pygame, screen, state, runtime, font_small)

        pygame.display.flip()

    pygame.quit()
    return 0


# ---------------------------------------------------------------------------
# Capture mode
# ---------------------------------------------------------------------------

_CAPTURE_CHAINS = (0, 1, 3, 5, 10, 15, 20, 25)
_TAKEOVER_SAMPLES_MS = (300, 900, 1500)


def _settle_frames(pygame, runtime, state, surface, panel_rect,
                   fonts, settle_ms: int = 300) -> list:
    """Advance the runtime for ``settle_ms`` of real time so pulses +
    bursts land where they should before the frame is captured. Returns
    the final frame's protected rects."""
    font_heading, font_body, font_small = fonts
    frames = max(1, settle_ms // 16)
    protected: list = []
    for _ in range(frames):
        runtime.observe(state.session_id, state.snapshot())
        runtime.update(0.016, paused=state.paused)
        surface.fill((16, 14, 24))
        runtime.draw_background(surface, panel_rect)
        protected = _draw_quiz_panel(pygame, surface, None, panel_rect, state,
                                     font_heading, font_body, font_small)
        runtime.draw_foreground(surface, protected)
        runtime.draw_top_overlay(surface)
        _draw_hud(pygame, surface, state, runtime, font_small)
    return protected


def _capture_set(pygame, build_default_runtime, layout, get_font, out_dir: Path,
                 reduced: bool) -> int:
    """Capture one full set of chain-state PNGs plus the two takeovers.

    Returns the number of frames written.
    """
    if reduced:
        os.environ['PQ_REDUCED_MOTION'] = '1'
    else:
        os.environ.pop('PQ_REDUCED_MOTION', None)
    runtime = build_default_runtime()
    state = PreviewState()
    out_dir.mkdir(parents=True, exist_ok=True)

    font_heading = get_font('heading', 28)
    font_body = get_font('body', 22)
    font_small = get_font('small', 16)
    fonts = (font_heading, font_body, font_small)

    surface = pygame.Surface((layout.WINDOW_W, layout.WINDOW_H),
                             pygame.SRCALPHA)
    panel_rect = pygame.Rect(0, 0, 760, 360)
    panel_rect.center = (layout.WINDOW_W // 2, layout.WINDOW_H // 2 + 20)

    written = 0

    # Climbing chains -- feed the runtime cumulative asked_counts so
    # per-answer pulses + milestone bursts land as they would in play.
    state.new_session()
    runtime.reset_scope(state.session_id)
    for target in _CAPTURE_CHAINS:
        delta = target - state.chain
        if delta < 0:
            # Rolling back is unrealistic -- start a fresh session.
            state.new_session()
            runtime.reset_scope(state.session_id)
            delta = target
        for _ in range(delta):
            state.answer_correct()
        _settle_frames(pygame, runtime, state, surface, panel_rect, fonts,
                       settle_ms=300)
        path = out_dir / f'chain_{target:02d}_correct.png'
        pygame.image.save(surface, str(path))
        written += 1

    # Wrong-answer frame: last state had chain=25. Answer wrong resets
    # the chain to 0 but we want to see the frame RIGHT after the miss.
    state.answer_wrong()
    _settle_frames(pygame, runtime, state, surface, panel_rect, fonts,
                   settle_ms=300)
    pygame.image.save(surface, str(out_dir / 'chain_wrong.png'))
    written += 1

    # Timeout frame: build a mid-chain, then timeout.
    state.new_session()
    runtime.reset_scope(state.session_id)
    for _ in range(10):
        state.answer_correct()
    state.answer_timeout()
    _settle_frames(pygame, runtime, state, surface, panel_rect, fonts,
                   settle_ms=300)
    pygame.image.save(surface, str(out_dir / 'chain_timeout.png'))
    written += 1

    # Fullscreen takeovers (divine + unicorn + identify-orb if Phase 3 is
    # live), sampled at 300/900/1500 ms elapsed from trigger. Any
    # effect that is not registered gets quietly skipped.
    takeover_names = ['divine_intercession_takeover', 'unicorn_bond_takeover']
    if 'identify_success_orb' in runtime.handlers:
        takeover_names.append('identify_success_orb')
    for name in takeover_names:
        runtime.fire(name, {'item_name': 'Wand of Fire'})
        elapsed = 0
        for target_ms in _TAKEOVER_SAMPLES_MS:
            # Advance to the target elapsed_ms.
            step_ms = max(0, target_ms - elapsed)
            frames = max(1, step_ms // 16)
            for _ in range(frames):
                runtime.update(0.016, paused=False)
                surface.fill((16, 14, 24))
                # Draw a muted scene behind the takeover so captures
                # resemble the in-game feel.
                runtime.draw_background(surface, panel_rect)
                _draw_quiz_panel(pygame, surface, None, panel_rect, state,
                                 font_heading, font_body, font_small)
                runtime.draw_top_overlay(surface)
                _draw_hud(pygame, surface, state, runtime, font_small)
            elapsed = target_ms
            # Prefix the file by the kind of effect: fullscreen takeovers
            # share the "takeover_" prefix, identify_orb gets its own.
            if name.endswith('_takeover'):
                short = name.split('_takeover')[0]
                path = out_dir / f'takeover_{short}_{target_ms}ms.png'
            else:
                path = out_dir / f'oneshot_{name}_{target_ms}ms.png'
            pygame.image.save(surface, str(path))
            written += 1

    return written


def run_capture() -> int:
    pygame, layout, build_default_runtime, get_font, _make = _lazy_imports()
    # Headless-safe: use a dummy video driver so we don't need a visible
    # window to render into surfaces.
    os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
    pygame.init()
    pygame.display.set_mode((1, 1))  # satisfies some init paths

    today = _dt.date.today().isoformat()
    root = Path(__file__).resolve().parent.parent.parent
    base = root / 'docs' / 'audits' / f'effects_preview_{today}'
    reduced_dir = base / 'reduced'

    total = 0
    print(f'[preview] capturing full-motion set -> {base}', file=sys.stderr)
    total += _capture_set(pygame, build_default_runtime, layout, get_font,
                          base, reduced=False)
    print(f'[preview] capturing reduced-motion set -> {reduced_dir}',
          file=sys.stderr)
    total += _capture_set(pygame, build_default_runtime, layout, get_font,
                          reduced_dir, reduced=True)
    print(f'[preview] wrote {total} frames.', file=sys.stderr)
    pygame.quit()
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args(argv: list) -> argparse.Namespace:
    p = argparse.ArgumentParser(description='Effects preview harness.')
    p.add_argument('--capture', action='store_true',
                   help='Programmatic capture: cycle through chain '
                   'states + takeovers and save PNGs under '
                   'docs/audits/effects_preview_YYYY-MM-DD/. Exits '
                   'without opening an interactive window.')
    return p.parse_args(argv)


def main(argv: Optional[list] = None) -> int:
    args = _parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.capture:
        return run_capture()
    return run_interactive()


if __name__ == '__main__':
    raise SystemExit(main())
