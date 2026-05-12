"""Spec document loader.

Loads moral_vision.md, per-subject spec docs, and taxonomy.yaml. Records
SHA-256 hash of each spec file so generated questions can be tagged with
the rubric version applied.

The deterministic regex patterns (anti-rote etc.) live in
`tools.quizgen.deterministic.anti_rote`, not here — they need to be
operational Python code. A test ensures they match what is documented
in moral_vision.md §6.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = _REPO_ROOT / "docs" / "quiz"
SUBJECTS_DIR = DOCS_DIR / "subjects"


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split YAML frontmatter from a markdown body. Returns (frontmatter, body)."""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    fm_text = text[4:end]
    body = text[end + 5 :]
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, body


@dataclass(frozen=True)
class MoralVision:
    path: Path
    sha256: str
    body: str
    version: int
    date: str


@dataclass(frozen=True)
class SubjectSpec:
    subject: str
    path: Path
    sha256: str
    body: str
    version: int
    style_verdict: str  # "WONDER-DRIVEN" or "SNAPPY-ROTE"
    in_game_action: str


@dataclass(frozen=True)
class TaxonomyCell:
    name: str
    description: str
    tier_quotas: dict[int, int]


@dataclass(frozen=True)
class SubjectTaxonomy:
    subject: str
    total_target: int
    cells: dict[str, TaxonomyCell]

    @property
    def actual_total(self) -> int:
        return sum(sum(c.tier_quotas.values()) for c in self.cells.values())

    @property
    def by_tier(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for cell in self.cells.values():
            for t, n in cell.tier_quotas.items():
                out[t] = out.get(t, 0) + n
        return out


@dataclass(frozen=True)
class Specs:
    moral_vision: MoralVision
    subjects: dict[str, SubjectSpec]
    taxonomy: dict[str, SubjectTaxonomy]


def load_moral_vision(path: Path | None = None) -> MoralVision:
    path = path or (DOCS_DIR / "moral_vision.md")
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    return MoralVision(
        path=path,
        sha256=_file_sha256(path),
        body=body,
        version=int(fm.get("version", 0)),
        date=str(fm.get("date", "")),
    )


def load_subject_spec(subject: str, path: Path | None = None) -> SubjectSpec:
    path = path or (SUBJECTS_DIR / f"{subject}.md")
    if not path.exists():
        raise FileNotFoundError(f"Subject spec not found: {path}")
    text = path.read_text(encoding="utf-8")
    fm, body = _parse_frontmatter(text)
    return SubjectSpec(
        subject=str(fm.get("subject", subject)),
        path=path,
        sha256=_file_sha256(path),
        body=body,
        version=int(fm.get("version", 0)),
        style_verdict=str(fm.get("style_verdict", "")),
        in_game_action=str(fm.get("in_game_action", "")),
    )


def load_taxonomy(path: Path | None = None) -> dict[str, SubjectTaxonomy]:
    path = path or (DOCS_DIR / "taxonomy.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    result: dict[str, SubjectTaxonomy] = {}
    for subject_name, subject_data in data.items():
        if subject_name in ("version", "date"):
            continue
        if not isinstance(subject_data, dict):
            continue
        total_target = int(subject_data.get("total_target", 0))
        cells: dict[str, TaxonomyCell] = {}
        for cell_name, cell_data in subject_data.items():
            if cell_name == "total_target":
                continue
            if not isinstance(cell_data, dict):
                continue
            tier_quotas_raw = cell_data.get("tier_quotas", {})
            tier_quotas = {int(k): int(v) for k, v in tier_quotas_raw.items()}
            cells[cell_name] = TaxonomyCell(
                name=cell_name,
                description=str(cell_data.get("description", "")),
                tier_quotas=tier_quotas,
            )
        result[subject_name] = SubjectTaxonomy(
            subject=subject_name,
            total_target=total_target,
            cells=cells,
        )
    return result


def available_subjects() -> list[str]:
    """Subjects with a spec doc on disk."""
    return sorted(p.stem for p in SUBJECTS_DIR.glob("*.md"))


def load_all(subject: str | None = None) -> Specs:
    """Load all spec docs.

    If subject is given, load only that subject's spec. Otherwise load all
    subject specs found on disk.
    """
    mv = load_moral_vision()
    if subject:
        subjects = {subject: load_subject_spec(subject)}
    else:
        subjects = {s: load_subject_spec(s) for s in available_subjects()}
    taxonomy = load_taxonomy()
    return Specs(moral_vision=mv, subjects=subjects, taxonomy=taxonomy)
