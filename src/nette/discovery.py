from __future__ import annotations

from pathlib import Path
from typing import Final, Iterable

SKIPPED_DIR_PREFIXES: Final = (".",)
SKIPPED_DIR_NAMES: Final = frozenset({"__pycache__", "node_modules"})


def discover(paths: Iterable[Path]) -> list[Path]:
    found: set[Path] = set()

    for path in paths:
        if path.is_file():
            found.add(path)
        else:
            found.update(_walk(path))

    return sorted(found)


def _walk(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        relative = path.relative_to(root)
        if any(_skipped(part) for part in relative.parts[:-1]):
            continue
        yield path


def _skipped(dirname: str) -> bool:
    return dirname.startswith(SKIPPED_DIR_PREFIXES) or dirname in SKIPPED_DIR_NAMES
