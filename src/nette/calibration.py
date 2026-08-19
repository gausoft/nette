from __future__ import annotations

import ast
import json
import re
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from nette.discovery import discover
from nette.parsing import SourceFile, parse_source

PROFILE_VERSION: Final = 1
CAMEL_CASE: Final = re.compile(r"^[a-z]+[A-Z]")


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

    for node in ast.walk(source.tree):
        if isinstance(node, ast.Try):
            tally.tries += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            tally.functions += 1
            tally.annotated += _is_annotated(node)
            tally.guarded += _contains_try(node)
            tally.camel += bool(CAMEL_CASE.match(node.name))


def _finalize(tally: _Tally) -> Profile:
    if tally.files == 0:
        return Profile(files_measured=0, metrics={})

    metrics: dict[str, float] = {}
    if tally.lines:
        metrics["try_per_kloc"] = round(1000 * tally.tries / tally.lines, 2)
    if tally.file_sizes:
        metrics["file_size_p90"] = float(_percentile_90(tally.file_sizes))
    if tally.functions:
        metrics["annotated_function_rate"] = round(tally.annotated / tally.functions, 2)
        metrics["guarded_function_rate"] = round(tally.guarded / tally.functions, 2)
        metrics["camel_case_function_rate"] = round(tally.camel / tally.functions, 2)

    return Profile(files_measured=tally.files, metrics=metrics)


def _percentile_90(values: list[int]) -> float:
    if len(values) < 2:
        return float(values[0])

    return statistics.quantiles(values, n=10)[-1]


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


def _is_annotated(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    if function.returns is not None:
        return True
    return any(arg.annotation for arg in function.args.args)


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
