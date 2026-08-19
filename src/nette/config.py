from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from nette.rules.base import DEFAULT_THRESHOLDS

KNOWN_KEYS: Final = frozenset({"select", "ignore", "thresholds", "output", "profile"})
KNOWN_FAMILIES: Final = frozenset(
    {"shape", "naming", "defensiveness", "structure", "engine"}
)
KNOWN_OUTPUT_KEYS: Final = frozenset({"format"})
KNOWN_FORMATS: Final = frozenset({"concise", "full", "agent", "json"})
KNOWN_PROFILES: Final = frozenset({"fastapi"})


@dataclass(frozen=True)
class Config:
    select: tuple[str, ...] = tuple(sorted(KNOWN_FAMILIES))
    ignore: tuple[str, ...] = ()
    thresholds: dict[str, int] = field(default_factory=dict)
    output_format: str = "full"
    framework: str | None = None

    def rule_enabled(self, code: str, family: str) -> bool:
        return {code, family}.isdisjoint(self.ignore) and not {code, family}.isdisjoint(
            self.select
        )


def load_config(root: Path) -> Config:
    section = _read_section(root)
    if not section:
        return Config()

    _reject_unknown(section.keys(), KNOWN_KEYS, "tool.nette")

    thresholds = dict(section.get("thresholds", {}))
    _reject_unknown(thresholds.keys(), DEFAULT_THRESHOLDS.keys(), "tool.nette.thresholds")
    _reject_bad_types(thresholds)

    output = section.get("output", {})
    _reject_unknown(output.keys(), KNOWN_OUTPUT_KEYS, "tool.nette.output")

    output_format = output.get("format", "full")
    if output_format not in KNOWN_FORMATS:
        raise ValueError(
            f"unknown output format {output_format!r}; "
            f"expected one of: {', '.join(sorted(KNOWN_FORMATS))}"
        )

    framework = section.get("profile")
    if framework is not None and framework not in KNOWN_PROFILES:
        raise ValueError(
            f"unknown framework profile {framework!r}; "
            f"expected one of: {', '.join(sorted(KNOWN_PROFILES))}"
        )

    return Config(
        select=_string_tuple(section.get("select", tuple(sorted(KNOWN_FAMILIES))), "select"),
        ignore=_string_tuple(section.get("ignore", ()), "ignore"),
        thresholds=thresholds,
        output_format=output_format,
        framework=framework,
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


def _string_tuple(value, key: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(
        isinstance(item, str) for item in value
    ):
        raise ValueError(f"{key} must be a list of strings, got {value!r}")

    return tuple(value)


def _reject_bad_types(thresholds: dict) -> None:
    for name, value in thresholds.items():
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"threshold {name} must be an integer, got {value!r}")
