from __future__ import annotations

import ast
from typing import Final

from nette.rules.base import Context, Rule

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef
EXEMPT_NAMES: Final = frozenset({"_", "self", "cls"})


class ShortNameLongScope(Rule):
    code = "NET201"

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
