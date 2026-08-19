from __future__ import annotations

import ast
from typing import Final

ROUTE_METHODS: Final = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "websocket"}
)
SIGNATURE_EXEMPT_RULES: Final = frozenset({"NET103"})


def is_route_endpoint(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(_is_route_decorator(d) for d in function.decorator_list)


def _is_route_decorator(decorator: ast.expr) -> bool:
    if not isinstance(decorator, ast.Call):
        return False

    callee = decorator.func

    return (
        isinstance(callee, ast.Attribute)
        and callee.attr in ROUTE_METHODS
        and isinstance(callee.value, ast.Name)
    )
