from __future__ import annotations

import ast
from pathlib import Path
from typing import Final

from nette.calibration import is_annotated
from nette.rules.base import Context, Rule

CONVENTION_FLOOR: Final = 0.6
DEVIATION_FACTOR: Final = 0.5
MINIMUM_FUNCTIONS: Final = 3
NAMED_FUNCTIONS: Final = 5
FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


class UnderAnnotated(Rule):
    code = "under-annotated"
    family = "annotations"
    scope = "file"
    baseline = "annotated_function_rate"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        baseline = ctx.baseline()
        if baseline is None or baseline < CONVENTION_FLOOR or _is_test_module(ctx.source.path):
            return

        functions = [
            n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if len(functions) < MINIMUM_FUNCTIONS:
            return

        bare = [function for function in functions if not is_annotated(function)]
        rate = 1 - len(bare) / len(functions)

        if rate >= baseline * DEVIATION_FACTOR:
            return

        ctx.report(
            bare[0],
            message="this file is far less annotated than the rest of the repo",
            grounds=(
                f"{len(bare)} of its {len(functions)} functions carry no type annotation "
                f"({rate:.0%} annotated); across this repo {baseline:.0%} of functions are. "
                f"Bare here: {_named(bare)}"
            ),
            help=(
                "annotate the parameters and the return type; "
                "an unannotated helper in a typed module is where the next type error hides"
            ),
        )


def _named(bare: list[FunctionNode]) -> str:
    names = [f"`{function.name}`" for function in bare[:NAMED_FUNCTIONS]]
    rest = len(bare) - len(names)

    return ", ".join(names) + (f" and {rest} more" if rest else "")


def _is_test_module(path: Path) -> bool:
    name = path.name

    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"
