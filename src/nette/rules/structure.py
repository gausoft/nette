from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final

from nette.rules.base import Context, Rule

SNAKE_CASE: Final = re.compile(r"^[a-z0-9_]+\.py$")
DUNDER: Final = re.compile(r"^__\w+__\.py$")
SIZE_DEVIATION_FACTOR: Final = 3.0
DATA_DESTINATIONS: Final = frozenset(
    {
        "schemas.py",
        "models.py",
        "enums.py",
        "dto.py",
        "types.py",
        "constants.py",
        "entities.py",
        "__init__.py",
    }
)
DATA_BASES: Final = frozenset(
    {"BaseModel", "TypedDict", "NamedTuple", "Enum", "IntEnum", "StrEnum", "Flag"}
)
DATA_DECORATORS: Final = frozenset({"dataclass", "define", "frozen", "attrs"})
FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


class FileNaming(Rule):
    code = "file-naming"
    family = "structure"
    scope = "file"

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
    scope = "file"
    baseline = "file_size_p90"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        baseline = ctx.baseline()
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


class MixedModule(Rule):
    code = "mixed-module"
    family = "structure"
    scope = "file"

    def visit_module(self, node: ast.Module, ctx: Context) -> None:
        if _is_destination(ctx.source.path):
            return

        data_types = [
            statement
            for statement in node.body
            if isinstance(statement, ast.ClassDef) and _is_data_type(statement)
        ]
        if len(data_types) < ctx.threshold("data_types_per_module") or not _has_behaviour(node):
            return

        named = ", ".join(f"`{data_type.name}`" for data_type in data_types)
        ctx.report(
            data_types[0],
            message="this module holds data types and behaviour at once",
            grounds=f"it declares {len(data_types)} pure data types ({named}) beside its logic",
            help=(
                "move the types to a sibling module of their own "
                "(schemas.py, models.py, enums.py) and import them here"
            ),
        )


def _is_destination(path: Path) -> bool:
    return path.name in DATA_DESTINATIONS or f"{path.parent.name}.py" in DATA_DESTINATIONS


def _is_data_type(node: ast.ClassDef) -> bool:
    if node.name.startswith("_") or _has_methods(node):
        return False

    return _data_decorated(node) or _data_based(node) or _annotated_only(node)


def _has_methods(node: ast.ClassDef) -> bool:
    return any(isinstance(statement, FunctionNode) for statement in node.body)


def _data_decorated(node: ast.ClassDef) -> bool:
    return any(_decorator_name(d) in DATA_DECORATORS for d in node.decorator_list)


def _decorator_name(decorator: ast.expr) -> str:
    if isinstance(decorator, ast.Call):
        decorator = decorator.func
    if isinstance(decorator, ast.Attribute):
        return decorator.attr
    if isinstance(decorator, ast.Name):
        return decorator.id

    return ""


def _data_based(node: ast.ClassDef) -> bool:
    return any(_base_name(base) in DATA_BASES for base in node.bases)


def _base_name(base: ast.expr) -> str:
    if isinstance(base, ast.Attribute):
        return base.attr
    if isinstance(base, ast.Name):
        return base.id

    return ""


def _annotated_only(node: ast.ClassDef) -> bool:
    fields = [statement for statement in node.body if not _is_inert(statement)]

    return bool(fields) and all(isinstance(field, ast.AnnAssign) for field in fields)


def _is_inert(statement: ast.stmt) -> bool:
    if isinstance(statement, ast.Pass):
        return True

    return isinstance(statement, ast.Expr) and _is_literal(statement.value)


def _is_literal(value: ast.expr) -> bool:
    return isinstance(value, ast.Constant) and isinstance(value.value, (str, type(...)))


def _has_behaviour(module: ast.Module) -> bool:
    for statement in module.body:
        if isinstance(statement, FunctionNode):
            return True
        if isinstance(statement, ast.ClassDef) and _runs_code(statement):
            return True

    return False


def _runs_code(node: ast.ClassDef) -> bool:
    methods = [s for s in node.body if isinstance(s, FunctionNode)]

    return bool(methods) and not all(_is_stub(method) for method in methods)


def _is_stub(function: FunctionNode) -> bool:
    return all(_is_inert(statement) for statement in function.body)


def _anchor(module: ast.Module) -> ast.AST:
    return module.body[0] if module.body else module
