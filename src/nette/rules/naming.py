from __future__ import annotations

import ast
import re
from typing import Final

from nette.rules.base import Context, Rule

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
EXEMPT_NAMES: Final = frozenset({"_", "self", "cls"})
CAMEL_CASE: Final = re.compile(r"^[a-z]+[A-Z]")
DRIFT_DEVIATION_FACTOR: Final = 10.0
MINIMUM_DRIFTING: Final = 2


class ShortNameLongScope(Rule):
    code = "short-name-long-scope"
    family = "naming"

    def visit_functiondef(self, node: ast.FunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def visit_asyncfunctiondef(self, node: ast.AsyncFunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def _measure(self, node: FunctionNode, ctx: Context) -> None:
        limit = ctx.threshold("short_name_scope")

        for name, binding, last_use in _short_name_spans(node):
            span = last_use - binding.lineno
            if span > limit:
                ctx.report(
                    binding,
                    message=f"name `{name}` lives too long to stay one letter",
                    grounds=(
                        f"it is bound at line {binding.lineno} and still used "
                        f"{span} lines later; the configured limit is {limit}"
                    ),
                    help="name the thing after what it holds (response, rate, row)",
                )


class NamingDrift(Rule):
    code = "naming-drift"
    family = "naming"
    scope = "file"
    baseline = "camel_case_function_rate"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        baseline = ctx.baseline()
        if baseline is None:
            return

        functions = [
            n
            for n in ast.walk(node)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        drifting = [f for f in functions if CAMEL_CASE.match(f.name)]

        if len(drifting) < MINIMUM_DRIFTING or not functions:
            return

        rate = len(drifting) / len(functions)
        if rate <= max(baseline * DRIFT_DEVIATION_FACTOR, 0.05):
            return

        names = ", ".join(f.name for f in drifting[:3])
        ctx.report(
            drifting[0],
            message=f"function names break the repo convention: {names}",
            grounds=(
                f"{len(drifting)} of {len(functions)} functions here are camelCase; "
                f"in this repo only {baseline:.0%} of functions are"
            ),
            help="rename to snake_case to match the rest of the codebase",
        )


def _short_name_spans(function: FunctionNode):
    bindings: dict[str, ast.Name] = {}
    last_uses: dict[str, int] = {}
    exempt: set[str] = set()

    for node in ast.walk(function):
        _collect(node, bindings, last_uses, exempt)

    for name, binding in bindings.items():
        if name in EXEMPT_NAMES or name in exempt:
            continue
        last_use = last_uses.get(name, binding.lineno)
        yield name, binding, last_use


def _collect(
    node: ast.AST,
    bindings: dict[str, ast.Name],
    last_uses: dict[str, int],
    exempt: set[str],
) -> None:
    if isinstance(node, (ast.For, ast.AsyncFor)):
        exempt.update(_target_names(node.target))
    elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
        for comp in node.generators:
            exempt.update(_target_names(comp.target))
    elif isinstance(node, ast.Name) and len(node.id) == 1:
        if isinstance(node.ctx, ast.Store) and node.id not in bindings:
            bindings[node.id] = node
        elif isinstance(node.ctx, ast.Load):
            last_uses[node.id] = max(last_uses.get(node.id, 0), node.lineno)


def _target_names(target: ast.expr) -> set[str]:
    return {
        node.id
        for node in ast.walk(target)
        if isinstance(node, ast.Name)
    }
