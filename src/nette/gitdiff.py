from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Final

HUNK: Final = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
DESTINATION: Final = "+++ "
PREFIX: Final = "b/"


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


def changed_lines(repo: Path, *, ref: str) -> dict[Path, list[tuple[int, int]]]:
    root = repo_root(repo)
    base = _merge_base(root, ref)

    ranges = _hunks(
        _git(
            root,
            "-c",
            "core.quotepath=false",
            "diff",
            "-U0",
            "--src-prefix=a/",
            "--dst-prefix=b/",
            "--diff-filter=d",
            base,
            "--",
            "*.py",
        ),
        root,
    )

    for name in _git(root, "ls-files", "--others", "--exclude-standard"):
        if name.endswith(".py"):
            ranges[root / name] = _whole(root / name)

    return ranges


def _whole(path: Path) -> list[tuple[int, int]]:
    try:
        lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return []

    return [(1, lines)] if lines else []


def _hunks(lines: list[str], root: Path) -> dict[Path, list[tuple[int, int]]]:
    ranges: dict[Path, list[tuple[int, int]]] = {}
    current: Path | None = None

    for line in lines:
        if line.startswith(DESTINATION):
            current = _destination(line[len(DESTINATION) :], root)
            if current is not None:
                ranges.setdefault(current, [])
            continue

        match = HUNK.match(line)
        if match is None or current is None:
            continue

        start = int(match.group(1))
        count = int(match.group(2)) if match.group(2) is not None else 1
        if count:
            ranges[current].append((start, start + count - 1))

    return ranges


def _destination(name: str, root: Path) -> Path | None:
    name = _unquote(name.split("\t", 1)[0])

    if not name.startswith(PREFIX):
        return None

    return root / name[len(PREFIX) :]


def _unquote(name: str) -> str:
    if not (name.startswith('"') and name.endswith('"')):
        return name

    escaped = name[1:-1].encode("utf-8").decode("unicode_escape")

    return escaped.encode("latin-1", "replace").decode("utf-8", "replace")


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
