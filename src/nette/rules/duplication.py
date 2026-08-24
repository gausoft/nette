from __future__ import annotations

import ast
import difflib
from typing import Iterator, Sequence

from nette.calibration import is_test_module
from nette.rules.base import Context, Rule
from nette.rules.shape import body_statements, code_line_count

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


class DuplicatedSibling(Rule):
    code = "duplicated-sibling"
    family = "duplication"
    scope = "function"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        if is_test_module(ctx.source.path):
            return

        similarity = ctx.threshold("duplication_similarity") / 100
        min_lines = ctx.threshold("duplication_min_lines")

        for group in _sibling_groups(node):
            shapes = [
                (f, _shape(f)) for f in group if code_line_count(f) >= min_lines
            ]

            for index, (function, shape) in enumerate(shapes):
                twin, ratio = _closest(shape, shapes[:index], similarity)
                if twin is None:
                    continue

                ctx.report(
                    function,
                    message=(
                        f"`{function.name}` is a near-copy of `{twin.name}` "
                        "in the same scope"
                    ),
                    grounds=(
                        f"the two share {ratio:.0%} of their structure over "
                        f"{code_line_count(function)} lines; only names and values differ"
                    ),
                    help=(
                        "extract what they share into one function and pass "
                        "what differs as arguments"
                    ),
                )


def _sibling_groups(module: ast.Module) -> Iterator[list[FunctionNode]]:
    yield _functions(module.body)

    for node in ast.walk(module):
        if isinstance(node, ast.ClassDef):
            yield _functions(node.body)


def _functions(body: Sequence[ast.stmt]) -> list[FunctionNode]:
    return [node for node in body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _shape(function: FunctionNode) -> tuple[str, ...]:
    return tuple(
        type(node).__name__
        for statement in body_statements(function)
        for node in ast.walk(statement)
    )


def _closest(
    shape: tuple[str, ...],
    earlier: Sequence[tuple[FunctionNode, tuple[str, ...]]],
    similarity: float,
) -> tuple[FunctionNode | None, float]:
    best: FunctionNode | None = None
    best_ratio = 0.0

    for candidate, other in earlier:
        matcher = difflib.SequenceMatcher(None, shape, other, autojunk=False)
        floor = max(similarity, best_ratio)
        if matcher.real_quick_ratio() < floor or matcher.quick_ratio() < floor:
            continue

        ratio = matcher.ratio()
        if ratio > best_ratio:
            best, best_ratio = candidate, ratio

    if best_ratio < similarity:
        return None, 0.0

    return best, best_ratio
