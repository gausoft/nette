from __future__ import annotations

import ast
from typing import Final

ROUTE_METHODS: Final = frozenset(
    {"get", "post", "put", "patch", "delete", "head", "options", "websocket"}
)
SIGNATURE_EXEMPT_RULES: Final = frozenset({"argument-count"})


def is_route_endpoint(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(_is_route_decorator(d) for d in function.decorator_list)


def wears_decorator(
    function: ast.FunctionDef | ast.AsyncFunctionDef, names: tuple[str, ...]
) -> bool:
    worn = [_dotted(decorator) for decorator in function.decorator_list]

    return any(_matches(name, path) for name in names for path in worn if path)


def _matches(name: str, path: str) -> bool:
    return path == name or path.endswith(f".{name}")


def _dotted(decorator: ast.expr) -> str:
    node = decorator.func if isinstance(decorator, ast.Call) else decorator
    parts = []

    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value

    if isinstance(node, ast.Name):
        parts.append(node.id)

    return ".".join(reversed(parts))


def _is_route_decorator(decorator: ast.expr) -> bool:
    if not isinstance(decorator, ast.Call):
        return False

    callee = decorator.func

    return (
        isinstance(callee, ast.Attribute)
        and callee.attr in ROUTE_METHODS
        and isinstance(callee.value, ast.Name)
    )
