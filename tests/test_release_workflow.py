"""Release pipeline guards (bug bash 2026-10-16, CQ-01..03).

The workflow itself only runs on GitHub, so these tests pin down the parts a
local edit could quietly undo: the tag/version check, exact dependency pins,
the test gate, the Python version, Node-24 action majors, a pinned Linux
runner and a pinned, checksummed appimagetool.
"""
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'release'))

import check_version  # noqa: E402


def _read(*parts):
    with open(os.path.join(ROOT, *parts), encoding='utf-8') as f:
        return f.read()


WORKFLOW = _read('.github', 'workflows', 'release.yml')
LAYOUT = 'VERSION    = "3.1.0"\nFPS = 60\n'
ISS = '#define AppName "x"\n#define AppVersion   "3.1.0"\n'


# ── tag == layout.VERSION == setup.iss AppVersion ────────────────────────────

def test_matching_tag_passes():
    assert check_version.problems('v3.1.0', LAYOUT, ISS) == []


def test_tag_ahead_of_layout_fails():
    errs = check_version.problems('v3.2.0', LAYOUT, ISS)
    assert any('layout.py' in e for e in errs)
    assert any('setup.iss' in e for e in errs)


def test_layout_and_installer_disagree_fails():
    errs = check_version.problems('v3.1.0', LAYOUT.replace('3.1.0', '3.1.1'), ISS)
    assert errs == ['src/layout.py VERSION is 3.1.1, tag is v3.1.0']


def test_malformed_tag_and_missing_lines_fail():
    errs = check_version.problems('v3.1', '', '')
    assert len(errs) == 3


def test_the_real_files_agree_with_each_other():
    layout_v, iss_v = check_version.read_versions(
        _read('src', 'layout.py'), _read('installer', 'setup.iss'))
    assert layout_v and layout_v == iss_v
    assert check_version.main(['x', f'v{layout_v}']) == 0
    assert check_version.main(['x', 'v0.0.0']) == 1


# ── pins ─────────────────────────────────────────────────────────────────────

def _requirement_lines(name):
    return [ln.strip() for ln in _read(name).splitlines()
            if ln.strip() and not ln.strip().startswith('#')]


def test_requirements_are_exact_pins():
    for name in ('requirements.txt', 'requirements-build.txt'):
        for ln in _requirement_lines(name):
            if ln.startswith('-r '):
                continue
            assert re.fullmatch(r'[A-Za-z0-9_.\-]+==[0-9][0-9A-Za-z.\-]*', ln), (name, ln)
    assert any(ln.startswith('pyinstaller==') for ln in _requirement_lines('requirements-build.txt'))


# ── workflow shape ───────────────────────────────────────────────────────────

def test_workflow_runs_version_check_and_tests_before_building():
    assert 'tools/release/check_version.py' in WORKFLOW
    assert re.search(r'python -m pytest tests/', WORKFLOW)
    assert 'SDL_VIDEODRIVER: dummy' in WORKFLOW and 'SDL_AUDIODRIVER: dummy' in WORKFLOW
    # both build jobs wait for the test job
    assert len(re.findall(r'^\s+needs: test\s*$', WORKFLOW, re.M)) == 2


def test_workflow_builds_with_python_314():
    assert "PYTHON_VERSION: '3.14'" in WORKFLOW
    versions = re.findall(r'python-version:\s*(.+)', WORKFLOW)
    assert len(versions) == 3
    assert all(v.strip() == '${{ env.PYTHON_VERSION }}' for v in versions)


NODE24_MAJORS = {
    'actions/checkout': 5,          # v5+ runs.using: node24
    'actions/setup-python': 6,
    'actions/upload-artifact': 6,
    'actions/download-artifact': 7,
    'softprops/action-gh-release': 3,
}


def test_every_action_is_on_a_node24_major():
    uses = re.findall(r'uses:\s*([\w\-]+/[\w\-]+)@v(\d+)', WORKFLOW)
    assert uses
    for action, major in uses:
        assert action in NODE24_MAJORS, f'unreviewed action {action}'
        assert int(major) >= NODE24_MAJORS[action], (action, major)


def test_linux_runner_is_pinned_and_apt_names_fit_it():
    assert not re.search(r'runs-on:\s*ubuntu-latest', WORKFLOW)
    assert 'runs-on: ubuntu-24.04' in WORKFLOW
    # libfuse2 does not exist on noble (it is libfuse2t64); we use
    # APPIMAGE_EXTRACT_AND_RUN instead of FUSE.
    assert not re.search(r'\blibfuse2\b', WORKFLOW)


def test_appimagetool_is_pinned_and_checksummed():
    assert '/continuous/' not in WORKFLOW
    assert 'AppImageKit/releases' not in WORKFLOW
    assert re.search(r"APPIMAGETOOL_VERSION: '\d+\.\d+\.\d+'", WORKFLOW)
    assert re.search(r"APPIMAGETOOL_SHA256: '[0-9a-f]{64}'", WORKFLOW)
    assert re.search(r"APPIMAGE_RUNTIME_SHA256: '[0-9a-f]{64}'", WORKFLOW)
    assert WORKFLOW.count('sha256sum -c') == 2
    assert '--runtime-file' in WORKFLOW


# ── installer upgrades (CQ-15) ───────────────────────────────────────────────

def test_installer_clears_the_old_bundle_before_copying_the_new_one():
    iss = _read('installer', 'setup.iss')
    m = re.search(r'^\[InstallDelete\]\s*$(.*?)^\[', iss, re.M | re.S)
    assert m, 'setup.iss needs an [InstallDelete] section'
    assert re.search(r'Type:\s*filesandordirs;\s*Name:\s*"\{app\}[\\/]_internal"', m.group(1))
    assert iss.index('[InstallDelete]') < iss.index('[Files]')


def test_frozen_player_files_live_outside_the_install_dir(monkeypatch, tmp_path):
    """[InstallDelete] wipes {app}/_internal, so nothing the player owns may
    be written there by the frozen build."""
    sys.path.insert(0, os.path.join(ROOT, 'src'))
    import paths
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, '_MEIPASS', str(tmp_path / 'install' / '_internal'), raising=False)
    monkeypatch.setenv('APPDATA', str(tmp_path / 'appdata'))
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'xdg'))
    sd = os.path.normpath(paths.save_dir())
    assert not sd.startswith(os.path.normpath(str(tmp_path / 'install')) + os.sep)
    assert sd.startswith(os.path.normpath(str(tmp_path / ('appdata' if sys.platform == 'win32' else 'xdg'))))
