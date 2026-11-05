import json
from pathlib import Path

import yaml

from argus.adapters.opencode import OpenCodeAdapter
from argus.adapters.base import GENERATED_HEADER
from tests.adapters.conftest import stub_pack


def test_opencode_generates_agents_md():
    files = OpenCodeAdapter().generate([stub_pack("tdd")])
    assert Path("AGENTS.md") in [f.path for f in files]


def test_opencode_generates_opencode_json():
    files = OpenCodeAdapter().generate([stub_pack("tdd")])
    assert Path("opencode.json") in [f.path for f in files]


def test_opencode_json_is_valid_json():
    files = OpenCodeAdapter().generate([stub_pack("tdd")])
    oc_json = next(f for f in files if f.path == Path("opencode.json"))
    data = json.loads(oc_json.content)
    assert "$schema" in data


def test_opencode_json_uses_documented_instructions_array():
    files = OpenCodeAdapter().generate([stub_pack("tdd")])
    oc_json = next(f for f in files if f.path == Path("opencode.json"))
    assert json.loads(oc_json.content)["instructions"] == ["AGENTS.md"]


def test_opencode_generates_skill_per_pack():
    files = OpenCodeAdapter().generate([stub_pack("tdd"), stub_pack("solid")])
    paths = [f.path for f in files]
    assert Path(".opencode/skills/tdd/SKILL.md") in paths
    assert Path(".opencode/skills/solid/SKILL.md") in paths


def test_opencode_skill_frontmatter_declares_name_and_description():
    files = OpenCodeAdapter().generate([stub_pack("tdd")])
    skill = next(f for f in files if f.path == Path(".opencode/skills/tdd/SKILL.md"))
    assert skill.content.startswith("---\n")
    _, frontmatter, _ = skill.content.split("---\n", 2)
    data = yaml.safe_load(frontmatter)
    assert data["name"] == "tdd"
    assert data["description"] == "Use when applying tdd discipline"


def test_opencode_skill_frontmatter_is_before_generated_header_and_body():
    files = OpenCodeAdapter().generate([stub_pack("tdd")])
    skill = next(f for f in files if f.path == Path(".opencode/skills/tdd/SKILL.md"))
    assert skill.content.index("---\n") < skill.content.index(GENERATED_HEADER)
    assert "TDD instructions" in skill.content


def test_opencode_generates_command_for_pack_with_checklist():
    files = OpenCodeAdapter().generate([stub_pack("tdd", checklist="## Checklist")])
    assert Path(".opencode/commands/tdd.md") in [f.path for f in files]


def test_opencode_skips_command_for_pack_without_checklist():
    files = OpenCodeAdapter().generate([stub_pack("solid", checklist=None)])
    assert Path(".opencode/commands/solid.md") not in [f.path for f in files]


def test_agents_md_contains_only_instructions():
    files = OpenCodeAdapter().generate([stub_pack("tdd", checklist="## Checklist")])
    agents_md = next(f for f in files if f.path == Path("AGENTS.md"))
    assert "TDD instructions" in agents_md.content
    assert "## Checklist" not in agents_md.content
