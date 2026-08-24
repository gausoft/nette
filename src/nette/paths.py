from __future__ import annotations

from pathlib import Path
from typing import Final, Sequence

ROOT_MARKERS: Final = ("nette.toml", "pyproject.toml", ".nette", ".git")


def find_root(paths: Sequence[Path]) -> Path:
    start = (paths[0] if paths else Path(".")).resolve()
    directory = start if start.is_dir() else start.parent

    for candidate in (directory, *directory.parents):
        if any((candidate / marker).exists() for marker in ROOT_MARKERS):
            return candidate

    return directory


def within_root(path: Path) -> tuple[str, ...]:
    resolved = path.resolve()
    root = find_root([resolved])

    try:
        return resolved.relative_to(root).parts
    except ValueError:
        return (resolved.name,)
