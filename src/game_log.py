"""
Central error/event logging for Philosopher's Quest.

Writes a verbose, human-readable log to a single, easy-to-find file:

    <Documents>/PhilosophersQuest/ERROR_LOG.txt   (rolling: 1 MB x 3 backups)

Playtesters can locate this one file and email it. Crash reports
(crash_handler.py) are written to the SAME folder AND appended here, so
ERROR_LOG.txt is a complete record of everything that went wrong in a session --
recovered (non-fatal) errors AND fatal crashes.

Design rules:
  * Logging must NEVER crash the game. Every public function swallows its own
    failures (falling back to stderr). A broken log is better than a dead game.
  * Identical behavior in dev (`python src/main.py`) and the frozen .exe.
  * No stdout reliance: the bundled exe is windowed, so print() goes nowhere --
    everything important goes to the file.
"""
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

_LOG_DIR = None
_LOGGER = None
_LOG_FILE = 'ERROR_LOG.txt'


def log_dir() -> str:
    """Resolve (and create) the directory for the error log + crash reports.

    First writable location wins, in this order:
      1. <Documents>/PhilosophersQuest  -- chosen so testers can find + email it
      2. the game's save directory        (paths.save_dir)
      3. the current working directory     (last resort)
    Cached after the first successful resolution.
    """
    global _LOG_DIR
    if _LOG_DIR:
        return _LOG_DIR
    candidates = []
    try:
        candidates.append(
            os.path.join(os.path.expanduser('~'), 'Documents', 'PhilosophersQuest'))
    except Exception:
        pass
    try:
        from paths import save_dir
        candidates.append(save_dir())
    except Exception:
        pass
    candidates.append(os.getcwd())
    for d in candidates:
        try:
            os.makedirs(d, exist_ok=True)
            probe = os.path.join(d, '.write_test')
            with open(probe, 'w', encoding='utf-8') as f:
                f.write('ok')
            os.remove(probe)
            _LOG_DIR = d
            return d
        except Exception:
            continue
    _LOG_DIR = os.getcwd()
    return _LOG_DIR


def log_path() -> str:
    """Full path to ERROR_LOG.txt -- the file testers should email."""
    return os.path.join(log_dir(), _LOG_FILE)


def get_logger():
    """Return the configured logger, building it on first use. Never raises."""
    global _LOGGER
    if _LOGGER is not None:
        return _LOGGER
    lg = logging.getLogger('philosophers_quest')
    lg.setLevel(logging.INFO)
    lg.propagate = False
    fmt = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
    try:
        fh = RotatingFileHandler(
            log_path(), maxBytes=1_000_000, backupCount=3, encoding='utf-8')
        fh.setFormatter(fmt)
        lg.addHandler(fh)
    except Exception as e:
        try:
            sys.stderr.write(f"[game_log] could not open log file: {e}\n")
        except Exception:
            pass
    # In dev, also echo to the console; harmless (and silent) when frozen.
    if not getattr(sys, 'frozen', False):
        try:
            sh = logging.StreamHandler(sys.stderr)
            sh.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
            lg.addHandler(sh)
        except Exception:
            pass
    if not lg.handlers:
        lg.addHandler(logging.NullHandler())
    _LOGGER = lg
    return lg


def log_info(msg: str) -> None:
    try:
        get_logger().info(msg)
    except Exception:
        pass


def log_warning(msg: str) -> None:
    try:
        get_logger().warning(msg)
    except Exception:
        pass


def log_error(msg: str, exc_info: bool = True) -> None:
    """Log an error message. By default captures the currently-handled
    exception's full traceback, so call this from inside an `except` block."""
    try:
        get_logger().error(msg, exc_info=exc_info)
    except Exception:
        # Absolute last resort -- never let logging take the game down.
        try:
            sys.stderr.write(f"[game_log] {msg}\n")
            if exc_info:
                import traceback
                traceback.print_exc()
        except Exception:
            pass


def log_crash_report(text: str) -> None:
    """Append a full crash-report block to ERROR_LOG.txt so the single file is a
    complete record. Called by crash_handler after it builds the report."""
    try:
        get_logger().critical("FATAL CRASH -- full report follows:\n" + text)
    except Exception:
        pass


def log_session_start(version: str = '?', player: str = '?', build=None) -> None:
    """Write a session banner so the log is segmented per launch."""
    try:
        lg = get_logger()
        lg.info("==================== SESSION START ====================")
        lg.info(f"version={version} player={player!r} build={build!r} "
                f"python={sys.version.split()[0]} "
                f"frozen={bool(getattr(sys, 'frozen', False))}")
        lg.info(f"log file: {log_path()}")
    except Exception:
        pass
