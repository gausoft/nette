from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from nette.discovery import discover
from nette.parsing import parse_source

PROFILE_VERSION: Final = 1


@dataclass(frozen=True)
class Profile:
    files_measured: int
    metrics: dict[str, float]


def build_profile(root: Path) -> Profile:
    total_lines = 0
    total_try = 0
    total_functions = 0
    annotated_functions = 0
    guarded_functions = 0
    files_measured = 0

    for file in discover([root]):
        source = parse_source(file)
        if source.tree is None:
            continue

        files_measured += 1
        total_lines += len(source.lines)

        for node in ast.walk(source.tree):
            if isinstance(node, ast.Try):
                total_try += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_functions += 1
                annotated_functions += _is_annotated(node)
                guarded_functions += _contains_try(node)

    if files_measured == 0:
        return Profile(files_measured=0, metrics={})

    metrics: dict[str, float] = {}
    if total_lines:
        metrics["try_per_kloc"] = round(1000 * total_try / total_lines, 2)
    if total_functions:
        metrics["annotated_function_rate"] = round(
            annotated_functions / total_functions, 2
        )
        metrics["guarded_function_rate"] = round(
            guarded_functions / total_functions, 2
        )

    return Profile(files_measured=files_measured, metrics=metrics)


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
