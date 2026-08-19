from __future__ import annotations

import os
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
    for dirpath, dirnames, filenames in os.walk(root):
        parent = Path(dirpath)
        dirnames[:] = [name for name in dirnames if not _skipped(parent / name)]
        for name in filenames:
            if name.lower().endswith(".py"):
                yield parent / name


def _skipped(directory: Path) -> bool:
    name = directory.name
    if name.startswith(SKIPPED_DIR_PREFIXES) or name in SKIPPED_DIR_NAMES:
        return True

    return (directory / "pyvenv.cfg").exists()
