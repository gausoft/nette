from __future__ import annotations

import ast
from typing import Final

from nette.rules.base import Context, Rule

DEVIATION_FACTOR: Final = 3.0
MINIMUM_GUARDED_FUNCTIONS: Final = 3
MINIMUM_TRIES: Final = 3
FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


NAMED_GUARDS: Final = 5


class Defensiveness(Rule):
    code = "over-guarded"
    family = "defensiveness"
    scope = "file"
    baseline = "guarded_function_rate"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        baseline = ctx.baseline()
        if baseline is None:
            return

        functions = _functions(node)
        if not functions:
            return

        guarded = [f for f in functions if _contains_try(f)]
        if not _over_guarded(len(guarded), len(functions), baseline):
            return

        rate = len(guarded) / len(functions)

        ctx.report(
            guarded[0],
            message="this file guards far more than the rest of the repo",
            grounds=(
                f"{len(guarded)} of its {len(functions)} functions wrap code in try blocks "
                f"({rate:.0%}); the repo baseline is {baseline:.0%} of functions. "
                f"Guarded here: {_named(guarded)}"
            ),
            help=(
                "trust internal data and let unexpected errors surface; "
                "keep try blocks for real boundaries (I/O, parsing, network)"
            ),
        )


class GuardDensity(Rule):
    code = "guard-density"
    family = "defensiveness"
    scope = "file"
    baseline = "try_per_kloc"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        baseline = ctx.baseline()
        lines = len(ctx.source.lines)
        if baseline is None or not lines:
            return

        tries = [n for n in ast.walk(node) if isinstance(n, ast.Try)]
        density = 1000 * len(tries) / lines

        if len(tries) < MINIMUM_TRIES or density <= baseline * DEVIATION_FACTOR:
            return

        if _reported_by_over_guarded(node, ctx):
            return

        ctx.report(
            tries[0],
            message="this file stacks guards far tighter than the rest of the repo",
            grounds=(
                f"it wraps {len(tries)} try blocks in {lines} lines "
                f"({density:.0f} per 1000 lines); across this repo the rate is "
                f"{baseline} per 1000"
            ),
            help=(
                "guard the boundary call once, not every statement around it; "
                "a failure two lines after a successful read is the same failure"
            ),
        )


def _reported_by_over_guarded(node: ast.Module, ctx: Context) -> bool:
    if Defensiveness.code not in ctx.active_codes or ctx.profile is None:
        return False

    functions = _functions(node)
    guarded = [function for function in functions if _contains_try(function)]

    return bool(functions) and _over_guarded(
        len(guarded), len(functions), ctx.profile.metrics.get(Defensiveness.baseline)
    )


def _functions(node: ast.Module) -> list[FunctionNode]:
    return [n for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _over_guarded(guarded: int, functions: int, baseline: float | None) -> bool:
    if baseline is None or guarded < MINIMUM_GUARDED_FUNCTIONS:
        return False

    return guarded / functions > baseline * DEVIATION_FACTOR


def _named(guarded: list[FunctionNode]) -> str:
    names = [f"`{function.name}`" for function in guarded[:NAMED_GUARDS]]
    rest = len(guarded) - len(names)

    return ", ".join(names) + (f" and {rest} more" if rest else "")


def _contains_try(function: FunctionNode) -> bool:
    stack: list[ast.AST] = list(ast.iter_child_nodes(function))

    while stack:
        node = stack.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(node, ast.Try):
            return True
        stack.extend(ast.iter_child_nodes(node))

    return False
