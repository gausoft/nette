from __future__ import annotations

import subprocess
import sys
from collections import Counter
from pathlib import Path


def changed_files(repo: Path, *, ref: str) -> list[Path]:
    root = repo_root(repo)
    base = _merge_base(root, ref)

    tracked = _git(root, "diff", "--name-only", "--diff-filter=d", base)
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")

    names = {name for name in tracked + untracked if name.endswith(".py")}

    return sorted(root / name for name in names)


def change_counts(repo: Path, *, since: str) -> dict[Path, int]:
    root = repo_root(repo)

    try:
        records = _git_text(
            root,
            "log",
            f"--since={since}",
            "--name-only",
            "--pretty=format:",
            "-z",
            "--",
            "*.py",
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        raise ValueError(f"cannot read the git history of {root}: {error}") from error

    return Counter(root / name for name in records.split("\0") if name.endswith(".py"))


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


def _git_text(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout


def _git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )

    return result.stdout.splitlines()
