from __future__ import annotations

import ast
import json
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, Sequence

from nette.discovery import discover
from nette.parsing import SourceFile, parse_source

PROFILE_VERSION: Final = 1
CAMEL_CASE: Final = re.compile(r"^[a-z]+[A-Z]")
HIGHER_IS_STRICTER: Final = frozenset({"annotated_function_rate"})


@dataclass(frozen=True)
class Profile:
    files_measured: int
    metrics: dict[str, float]


@dataclass
class _Tally:
    files: int = 0
    lines: int = 0
    tries: int = 0
    functions: int = 0
    typed_scope_functions: int = 0
    annotated: int = 0
    guarded: int = 0
    camel: int = 0
    file_sizes: list[int] = field(default_factory=list)


def build_profile(root: Path) -> Profile:
    tally = _Tally()

    for file in discover([root]):
        source = parse_source(file)
        if source.tree is not None:
            _accumulate(source, tally)

    return _finalize(tally)


def _accumulate(source: SourceFile, tally: _Tally) -> None:
    tally.files += 1
    tally.lines += len(source.lines)
    tally.file_sizes.append(len(source.lines))
    typed_scope = not is_test_module(source.path)

    for node in ast.walk(source.tree):
        if isinstance(node, ast.Try):
            tally.tries += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tally.functions += 1
            tally.guarded += _contains_try(node)
            tally.camel += bool(CAMEL_CASE.match(node.name))
            if typed_scope:
                tally.typed_scope_functions += 1
                tally.annotated += is_annotated(node)


def _finalize(tally: _Tally) -> Profile:
    if tally.files == 0:
        return Profile(files_measured=0, metrics={})

    metrics: dict[str, float] = {}
    if tally.lines:
        metrics["try_per_kloc"] = round(1000 * tally.tries / tally.lines, 2)
    if tally.file_sizes:
        metrics["file_size_p90"] = float(_percentile_90(tally.file_sizes))
    if tally.functions:
        metrics["guarded_function_rate"] = round(tally.guarded / tally.functions, 2)
        metrics["camel_case_function_rate"] = round(tally.camel / tally.functions, 2)
    if tally.typed_scope_functions:
        metrics["annotated_function_rate"] = round(
            tally.annotated / tally.typed_scope_functions, 2
        )

    return Profile(files_measured=tally.files, metrics=metrics)


def _percentile_90(values: list[int]) -> float:
    if len(values) < 2:
        return float(values[0])

    return statistics.quantiles(values, n=10)[-1]


def ratchet(previous: Profile, current: Profile) -> Profile:
    metrics = dict(current.metrics)

    for name, was in previous.metrics.items():
        keep = max if name in HIGHER_IS_STRICTER else min
        metrics[name] = keep(metrics.get(name, was), was)

    return Profile(files_measured=current.files_measured, metrics=metrics)


def save_profile(profile: Profile, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": PROFILE_VERSION,
        "files_measured": profile.files_measured,
        "metrics": profile.metrics,
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def load_profile(source: Path) -> Profile | None:
    if not source.exists():
        return None

    payload = json.loads(source.read_text())

    return Profile(
        files_measured=payload["files_measured"],
        metrics=payload["metrics"],
    )


def group_by_profile(
    files: Sequence[Path], root: Path, location: Path
) -> list[tuple[Profile | None, list[Path]]]:
    grouped: dict[Path | None, list[Path]] = defaultdict(list)

    for file in files:
        grouped[_nearest_profile(file.resolve().parent, root.resolve(), location)].append(file)

    return [
        (load_profile(source) if source is not None else None, grouped[source])
        for source in sorted(grouped, key=lambda path: str(path or ""))
    ]


def _nearest_profile(directory: Path, root: Path, location: Path) -> Path | None:
    for candidate in (directory, *directory.parents):
        if not candidate.is_relative_to(root):
            break

        profile = candidate / location
        if profile.exists():
            return profile

    return None


def is_annotated(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if function.returns is not None:
        return True

    arguments = function.args
    named = (
        *arguments.posonlyargs,
        *arguments.args,
        *arguments.kwonlyargs,
        *(argument for argument in (arguments.vararg, arguments.kwarg) if argument),
    )

    return any(argument.annotation for argument in named)


def _contains_try(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    stack: list[ast.AST] = list(ast.iter_child_nodes(function))

    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(node, ast.Try):
            return True
        stack.extend(ast.iter_child_nodes(node))

    return False
