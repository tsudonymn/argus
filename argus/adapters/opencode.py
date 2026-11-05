import json
from pathlib import Path

import yaml

from argus.adapters.base import GENERATED_HEADER, BaseAdapter, GeneratedFile, Pack
from argus.merger import JsonMerger


class OpenCodeAdapter(BaseAdapter):
    platform_id = "opencode"
    display_name = "OpenCode"

    def generate(self, packs: list[Pack]) -> list[GeneratedFile]:
        return [
            self._agents_md(packs),
            self._opencode_json(),
            *self._skills(packs),
            *self._commands(packs),
        ]

    def _opencode_json(self) -> GeneratedFile:
        config = {
            "$schema": "https://opencode.ai/config.json",
            "instructions": ["AGENTS.md"],
        }
        return GeneratedFile(
            path=Path("opencode.json"),
            content=json.dumps(config, indent=2),
            merger=JsonMerger(),
        )

    def _skills(self, packs: list[Pack]) -> list[GeneratedFile]:
        return [
            GeneratedFile(
                path=Path(f".opencode/skills/{pack.name}/SKILL.md"),
                content=self._skill_content(pack),
            )
            for pack in packs
        ]

    @staticmethod
    def _skill_content(pack: Pack) -> str:
        description = pack.manifest.get("description") or (
            f"Use when applying the {pack.name} standards"
        )
        frontmatter = yaml.safe_dump(
            {"name": pack.name, "description": description},
            sort_keys=False,
            allow_unicode=True,
        )
        return f"---\n{frontmatter}---\n\n{GENERATED_HEADER}{pack.instructions}"

    def _commands(self, packs: list[Pack]) -> list[GeneratedFile]:
        return [
            GeneratedFile(
                path=Path(f".opencode/commands/{pack.name}.md"),
                content=GENERATED_HEADER + pack.checklist,
            )
            for pack in packs
            if pack.checklist
        ]
