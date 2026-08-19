from __future__ import annotations

import ast
from typing import Final

from nette.rules.base import Context, Rule

DEVIATION_FACTOR: Final = 3.0
MINIMUM_GUARDED_FUNCTIONS: Final = 3
FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


class Defensiveness(Rule):
    code = "NET301"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        if ctx.profile is None:
            return

        baseline = ctx.profile.metrics.get("guarded_function_rate")
        if baseline is None:
            return

        functions = [
            n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if not functions:
            return

        guarded = [f for f in functions if _contains_try(f)]
        if len(guarded) < MINIMUM_GUARDED_FUNCTIONS:
            return

        rate = len(guarded) / len(functions)

        if rate > baseline * DEVIATION_FACTOR:
            ctx.report(
                guarded[0],
                message="this file guards far more than the rest of the repo",
                grounds=(
                    f"{len(guarded)} of its {len(functions)} functions wrap code in try blocks "
                    f"({rate:.0%}); the repo baseline is {baseline:.0%} of functions"
                ),
                help=(
                    "trust internal data and let unexpected errors surface; "
                    "keep try blocks for real boundaries (I/O, parsing, network)"
                ),
            )


def _contains_try(function: FunctionNode) -> bool:
    return any(isinstance(node, ast.Try) for node in ast.walk(function))
