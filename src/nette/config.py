from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from nette.rules.base import DEFAULT_THRESHOLDS

KNOWN_KEYS: Final = frozenset({"select", "ignore", "thresholds", "output"})
KNOWN_OUTPUT_KEYS: Final = frozenset({"format"})


@dataclass(frozen=True)
class Config:
    select: tuple[str, ...] = ("NET",)
    ignore: tuple[str, ...] = ()
    thresholds: dict[str, int] = field(default_factory=dict)
    output_format: str = "full"

    def rule_enabled(self, code: str) -> bool:
        selected = any(code.startswith(prefix) for prefix in self.select)
        ignored = any(code.startswith(prefix) for prefix in self.ignore)

        return selected and not ignored


def load_config(root: Path) -> Config:
    section = _read_section(root)
    if not section:
        return Config()

    _reject_unknown(section.keys(), KNOWN_KEYS, "tool.nette")

    thresholds = dict(section.get("thresholds", {}))
    _reject_unknown(thresholds.keys(), DEFAULT_THRESHOLDS.keys(), "tool.nette.thresholds")

    output = section.get("output", {})
    _reject_unknown(output.keys(), KNOWN_OUTPUT_KEYS, "tool.nette.output")

    return Config(
        select=tuple(section.get("select", ("NET",))),
        ignore=tuple(section.get("ignore", ())),
        thresholds=thresholds,
        output_format=output.get("format", "full"),
    )


def _read_section(root: Path) -> dict:
    dedicated = root / "nette.toml"
    if dedicated.exists():
        return tomllib.loads(dedicated.read_text())

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        payload = tomllib.loads(pyproject.read_text())
        return payload.get("tool", {}).get("nette", {})

    return {}


def _reject_unknown(present, known, where: str) -> None:
    unknown = set(present) - set(known)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(f"unknown key in [{where}]: {names}")
