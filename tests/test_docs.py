"""Every relative link in the documentation points at something that exists, and every document the
index lists is there. Docs that rot silently are worse than none."""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DOCS = sorted(
    path
    for path in REPO.rglob("*.md")
    if not any(part in {".venv", "node_modules", ".pytest_cache"} for part in path.parts)
)
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


@pytest.mark.parametrize("document", DOCS, ids=[str(path.relative_to(REPO)) for path in DOCS])
def test_relative_links_resolve(document: Path) -> None:
    text = re.sub(r"```.*?```", "", document.read_text(encoding="utf-8"), flags=re.DOTALL)
    for target in LINK.findall(text):
        if re.match(r"^[a-z]+:", target) or target.startswith("#"):
            continue
        path = target.split("#", 1)[0]
        assert (document.parent / path).exists(), f"{document.relative_to(REPO)} → {target}"


def test_the_index_lists_every_document_in_docs() -> None:
    index = (REPO / "docs" / "INDEX.md").read_text(encoding="utf-8")
    for path in (REPO / "docs").rglob("*.md"):
        relative = path.relative_to(REPO / "docs").as_posix()
        if relative == "INDEX.md" or (relative.startswith("decisions/0") and "NNNN" in index):
            continue
        assert relative in index, f"docs/INDEX.md does not list {relative}"


def test_every_adr_is_in_the_decisions_table() -> None:
    table = (REPO / "docs" / "decisions" / "README.md").read_text(encoding="utf-8")
    for adr in (REPO / "docs" / "decisions").glob("0*.md"):
        assert f"({adr.name})" in table, f"{adr.name} is not referenced by any decision"


def test_the_changelog_is_the_generated_one() -> None:
    changelog = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    assert changelog.startswith("# Changelog")
    assert "Gerado pelo git-cliff" in changelog


def test_every_screen_picture_is_explained_and_every_explained_picture_exists() -> None:
    screens = REPO / "docs" / "screens"
    readme = (screens / "README.md").read_text(encoding="utf-8")
    pictures = {path.relative_to(screens).as_posix() for path in screens.glob("*/*.webp")}
    referenced = set(re.findall(r"(?:\]\(|src=\")((?:desktop|mobile)/[^)\"]+\.webp)", readme))
    assert pictures
    assert pictures == referenced
    assert len(re.findall(r"^## \d+\. ", readme, flags=re.MULTILINE)) == len(
        list(screens.glob("desktop/*.webp"))
    )
