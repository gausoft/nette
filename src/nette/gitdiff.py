from __future__ import annotations

import subprocess
from pathlib import Path


def changed_files(repo: Path, *, ref: str) -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=d", ref],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    tracked = result.stdout.splitlines()

    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    names = {name for name in tracked + untracked if name.endswith(".py")}

    return sorted(repo / name for name in names)
