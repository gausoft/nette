from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def changed_files(repo: Path, *, ref: str) -> list[Path]:
    root = repo_root(repo)
    base = _merge_base(root, ref)

    tracked = _git(root, "diff", "--name-only", "--diff-filter=d", base)
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")

    names = {name for name in tracked + untracked if name.endswith(".py")}

    return sorted(root / name for name in names)


def repo_root(start: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return start

    return Path(result.stdout.strip())


def _merge_base(root: Path, ref: str) -> str:
    result = subprocess.run(
        ["git", "merge-base", ref, "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"warning: no merge base with {ref}, comparing against its tip instead",
            file=sys.stderr,
        )
        return ref

    return result.stdout.strip()


def _git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.splitlines()
