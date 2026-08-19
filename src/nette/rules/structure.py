from __future__ import annotations

import ast
import re
from typing import Final

from nette.rules.base import Context, Rule

SNAKE_CASE: Final = re.compile(r"^[a-z0-9_]+\.py$")
DUNDER: Final = re.compile(r"^__\w+__\.py$")
SIZE_DEVIATION_FACTOR: Final = 3.0


class FileNaming(Rule):
    code = "file-naming"
    family = "structure"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        name = ctx.source.path.name
        if SNAKE_CASE.match(name) or DUNDER.match(name):
            return

        ctx.report(
            _anchor(node),
            message=f"file name `{name}` breaks snake_case",
            grounds="Python module names are snake_case by convention (PEP 8)",
            help="rename the file to lowercase words separated by underscores",
        )


class FileSize(Rule):
    code = "file-size"
    family = "structure"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        if ctx.profile is None:
            return

        baseline = ctx.profile.metrics.get("file_size_p90")
        if baseline is None:
            return

        lines = len(ctx.source.lines)
        if lines <= baseline * SIZE_DEVIATION_FACTOR:
            return

        ctx.report(
            _anchor(node),
            message="this file is far bigger than the rest of the repo",
            grounds=(
                f"it has {lines} lines; 9 out of 10 files in this repo "
                f"stay under {baseline:.0f}"
            ),
            help="split it by responsibility, one concern per module",
        )


def _anchor(module: ast.Module) -> ast.AST:
    return module.body[0] if module.body else module
