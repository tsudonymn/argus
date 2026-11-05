import importlib.resources
from pathlib import Path
import yaml
import pytest

PACKS_DIR = Path(str(importlib.resources.files("argus") / "packs"))
REQUIRED_PACKS = ["atomic-commit", "tdd", "solid", "code-quality", "pre-commit", "type-safety", "error-handling", "documentation-standards", "dependency-injection", "design-patterns", "refactoring", "testing-strategy", "testcontainers"]
VALID_CATEGORIES = {"workflow", "architecture", "quality", "process"}


@pytest.mark.parametrize("pack_name", REQUIRED_PACKS)
def test_pack_directory_exists(pack_name):
    assert (PACKS_DIR / pack_name).is_dir(), f"Pack directory missing: {pack_name}"


@pytest.mark.parametrize("pack_name", REQUIRED_PACKS)
def test_pack_has_pack_yml(pack_name):
    assert (PACKS_DIR / pack_name / "pack.yml").exists()


@pytest.mark.parametrize("pack_name", REQUIRED_PACKS)
def test_pack_yml_is_valid(pack_name):
    data = yaml.safe_load((PACKS_DIR / pack_name / "pack.yml").read_text())
    assert data["name"] == pack_name
    assert data["category"] in VALID_CATEGORIES
    assert isinstance(data.get("requires", []), list)
    assert isinstance(data.get("platforms", ["all"]), list)


@pytest.mark.parametrize("pack_name", REQUIRED_PACKS)
def test_pack_has_instructions(pack_name):
    instructions = PACKS_DIR / pack_name / "instructions.md"
    assert instructions.exists()
    assert len(instructions.read_text().strip()) > 100, "instructions.md is too short"


@pytest.mark.parametrize("pack_name", REQUIRED_PACKS)
def test_pack_name_matches_directory(pack_name):
    data = yaml.safe_load((PACKS_DIR / pack_name / "pack.yml").read_text())
    assert data["name"] == pack_name


def test_tdd_pack_documents_commits_after_green_and_refactor():
    text = (PACKS_DIR / "tdd" / "instructions.md").read_text()
    assert "RED → GREEN → Commit → REFACTOR → Commit" in text
    assert "Commit 1" in text
    assert "Commit 2" in text


def test_atomic_commit_pack_matches_tdd_commit_cycle():
    text = (PACKS_DIR / "atomic-commit" / "instructions.md").read_text()
    assert "RED → GREEN → COMMIT → REFACTOR → COMMIT" in text
    assert "STOP → RED" not in text
