"""Regression tests for the PyInstaller bundle spec.

These tests caught the v2.0.0 launch crash where the spec was missing
`data/chest_templates.json` (and `data/materials/`, `data/templates/`,
`data/flavor_encounters.json`, `assets/icon.ico`). Every one of those
silently passed unit tests because pytest ran from source — only the
frozen exe surfaced the missing-file errors.

The general invariant the tests enforce:

  For every literal `data_path('data', ...)` or `data_path('assets',
  ...)` call site in src/, the target path must be covered by the
  spec's `added_files` list — either as an exact file or as a parent
  directory.

This means future contributors can't add a `data_path(...)` to game
code without also touching the spec; the test fails loudly during
CI/pytest before anyone tries to ship a broken exe.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
SPEC = ROOT / "PhilosophersQuest.spec"

sys.path.insert(0, str(SRC))


# ---------------------------------------------------------------------------
# Parse the spec to extract `added_files`
# ---------------------------------------------------------------------------

def _parse_added_files() -> list[tuple[str, str]]:
    """Return the list of (source, dest) tuples from the spec's
    `added_files = [...]` literal. Parses the .spec file as Python."""
    spec_src = SPEC.read_text(encoding="utf-8")
    tree = ast.parse(spec_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "added_files":
                    if isinstance(node.value, ast.List):
                        out = []
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Tuple) and len(elt.elts) == 2:
                                src_node, _dst_node = elt.elts
                                if isinstance(src_node, ast.Constant):
                                    out.append(src_node.value)
                        return out
    raise RuntimeError("Could not find `added_files = [...]` in the spec")


# ---------------------------------------------------------------------------
# Scan src/ for `data_path('data', ...)` and `data_path('assets', ...)`
# call sites
# ---------------------------------------------------------------------------

_DATA_PATH_RX = re.compile(
    r"data_path\(\s*['\"](data|assets)['\"]\s*(?:,\s*([^)]*))?\)"
)


def _walk_data_path_calls() -> list[tuple[Path, int, list[str]]]:
    """Yield (file, line_no, ['data', 'chest_templates.json']) for every
    matched call site. Only string-literal arguments are extracted;
    dynamic f-string suffixes (`f'{subject}.json'`) yield the parent
    directory only."""
    out = []
    for py in sorted(SRC.glob("**/*.py")):
        text = py.read_text(encoding="utf-8")
        for m in _DATA_PATH_RX.finditer(text):
            line_no = text[: m.start()].count("\n") + 1
            head = m.group(1)
            rest = (m.group(2) or "").strip()
            # Extract any string-literal arguments after the head
            parts = [head]
            for s in re.finditer(r"['\"]([^'\"]+)['\"]", rest):
                parts.append(s.group(1))
            out.append((py, line_no, parts))
    return out


# ---------------------------------------------------------------------------
# Path coverage logic
# ---------------------------------------------------------------------------

def _is_covered(parts: list[str], spec_sources: set[str]) -> bool:
    """True if a `data_path(*parts)` target is bundled.

    A path `data/chest_templates.json` is covered if:
      - the exact string is in `spec_sources`, OR
      - any prefix directory (e.g., `data/`) is in `spec_sources`.

    Trailing f-string segments (which yield only the parent dirs) are
    handled by walking up the path."""
    target = "/".join(parts)
    # Strip any trailing empty segment
    target = target.rstrip("/")
    while target:
        if target in spec_sources:
            return True
        # Walk up
        if "/" not in target:
            break
        target = target.rsplit("/", 1)[0]
    return False


# ---------------------------------------------------------------------------
# The actual tests
# ---------------------------------------------------------------------------

def test_spec_added_files_parses():
    """Sanity: the spec is a parseable file with a literal added_files."""
    sources = _parse_added_files()
    assert sources, "added_files in spec must not be empty"
    # Every entry must exist on disk in the repo
    for s in sources:
        p = ROOT / s
        assert p.exists(), (
            f"spec added_files lists '{s}' but it does not exist in repo"
        )


# Each entry: (filename, joined_parts) — exempt because the call site
# either (a) bundles nothing because the result is just a parent dir
# the spec already populates, or (b) handles missing files gracefully
# via an explicit os.path.exists() check.
_EXEMPT = {
    # data_path('data') returns the bundled `data/` directory root.
    # That directory exists in the bundle because of all the child
    # entries (monsters.json, items/, etc.). The call site just uses
    # it as a join base.
    ("flavor_encounters.py", "data"),
    ("main.py", "data"),
    # Parchment background is loaded once at startup with an isfile()
    # fallback; the bundle is fine without it (the welcome name box paints
    # its procedural parchment). See src/ui_theme.py:_load_textures.
    ("ui_theme.py", "assets/textures/parchment.png"),
}


def test_every_data_path_call_is_bundled():
    """For every `data_path('data', ...)` and `data_path('assets',
    ...)` literal in src/, the target must be reachable via the spec's
    added_files. Catches the bundle bug that crashed v2.0.0 on launch.

    Exemptions live in `_EXEMPT` with a comment explaining why."""
    sources = set(_parse_added_files())
    # Normalize separators — the spec uses forward slashes consistently
    sources = {s.replace("\\", "/") for s in sources}

    call_sites = _walk_data_path_calls()
    assert call_sites, "expected to find at least one data_path() call"

    missing = []
    for py, line_no, parts in call_sites:
        key = (py.name, "/".join(parts))
        if key in _EXEMPT:
            continue
        if not _is_covered(parts, sources):
            missing.append(
                f"  {py.relative_to(ROOT)}:{line_no}  data_path"
                f"({', '.join(repr(p) for p in parts)})"
            )

    assert not missing, (
        "The following data_path() targets are NOT covered by the spec's "
        "added_files — the frozen exe will FileNotFoundError when these "
        "are read. Add the source to PhilosophersQuest.spec, OR add an "
        "entry to `_EXEMPT` if the call site has a graceful fallback.\n\n"
        + "\n".join(missing)
    )


# ---------------------------------------------------------------------------
# Guard: whole-directory bundle entries must contain ONLY runtime files.
# The spec bundles data/items, data/materials, data/questions, data/templates,
# assets/fonts and assets/tiles *wholesale*, so any generator script,
# __pycache__, *.backup, or *_v2/_pre_v2_backup/_tellgate staging JSON dropped
# inside them SHIPS in the exe. This test fails loudly if that happens.
# (Added with the 2026-07-18 distro cleanup that removed ~50 MB of such cruft.)
# ---------------------------------------------------------------------------

_BUNDLED_DIR_ALLOWED = {
    "data/items":              {".json"},
    "data/materials":          {".json"},
    "data/questions":          {".json"},
    "data/question_contexts":  {".json"},
    "data/templates":          {".json"},
    "assets/fonts":            {".ttf", ".otf"},
    "assets/tiles":            {".png"},
    # The UI art kit ships runtime art + its manifest only. Its README
    # (the asset contract) stays in the repo but is in the spec's
    # bundle_excludes. Never .psd/.kra sources, ComfyUI workflows or
    # drafts: those live in _genart/.
    "assets/ui":               {".png", ".json"},
}
_ARTIFACT_MARKERS = ("_v2", "_pre_v2", "_tellgate", "_backup", "_staging")


def _spec_is_excluded():
    """Return the spec's `_is_excluded(dest)` function, built from its
    literal `bundle_excludes` list and its own source, so the test runs the
    exact filter the spec applies to a.datas."""
    import os
    tree = ast.parse(SPEC.read_text(encoding="utf-8"))
    keep = [n for n in tree.body
            if (isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "bundle_excludes"
                        for t in n.targets))
            or (isinstance(n, ast.FunctionDef) and n.name == "_is_excluded")]
    assert len(keep) == 2, "spec must define bundle_excludes and _is_excluded"
    ns = {"os": os}
    exec(compile(ast.Module(body=keep, type_ignores=[]), str(SPEC), "exec"), ns)
    return ns["_is_excluded"]


def _shipped_files(rel):
    """Files the bundle ships from the whole-dir entry `rel` (PyInstaller
    dest names use the OS separator, as the spec's filter sees them)."""
    import os
    excluded = _spec_is_excluded()
    for f in (ROOT / rel).rglob("*"):
        if f.is_file() and not excluded(
                os.path.join(*f.relative_to(ROOT).parts)):
            yield f


def test_spec_compiles_without_warnings():
    """The spec's docstring once held a bare backslash-P escape (a
    SyntaxWarning on every build, an error in a future Python)."""
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        compile(SPEC.read_text(encoding="utf-8"), str(SPEC), "exec")


def test_spec_excludes_the_prune_archive_and_ui_readme():
    import os
    excluded = _spec_is_excluded()
    j = os.path.join
    assert excluded(j("data", "questions", "_pruned", "x", "cooking.json"))
    assert excluded(j("assets", "ui", "README.md"))
    assert not excluded(j("data", "questions", "cooking.json"))
    assert not excluded(j("data", "questions_pruned.json"))
    assert not excluded(j("assets", "ui", "manifest.json"))


def test_bundled_dirs_contain_only_runtime_files():
    """Whole-directory `added_files` entries ship every file inside them
    (minus the spec's bundle_excludes), so those dirs must stay pristine —
    only runtime data/assets, never generator scripts, __pycache__,
    backups, *_v2 staging banks, or _underscore archive folders."""
    offenders = []
    for rel, allowed in _BUNDLED_DIR_ALLOWED.items():
        d = ROOT / rel
        if not d.is_dir():
            offenders.append(f"  MISSING bundled dir: {rel}")
            continue
        for f in _shipped_files(rel):
            if any(p.startswith("_") for p in f.relative_to(d).parts[:-1]):
                offenders.append(
                    f"  {f.relative_to(ROOT).as_posix()}  "
                    f"(archive folder — add it to the spec's bundle_excludes)")
            elif f.suffix.lower() not in allowed:
                offenders.append(
                    f"  {f.relative_to(ROOT).as_posix()}  "
                    f"(bundle ships only {sorted(allowed)} here)")
            elif rel == "data/questions" and any(m in f.stem for m in _ARTIFACT_MARKERS):
                offenders.append(
                    f"  {f.relative_to(ROOT).as_posix()}  "
                    f"(bank-build artifact — must not ship in the exe)")
    assert not offenders, (
        "Non-runtime files found inside whole-dir bundle entries — these "
        "would ship in the frozen exe. Move them out of the bundled dir "
        "(e.g. to _archive/ or a non-bundled tools/ path):\n\n"
        + "\n".join(offenders)
    )
