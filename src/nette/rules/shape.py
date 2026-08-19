from __future__ import annotations

import ast

from nette.rules.base import Context, Rule

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef

NESTING_NODES = (
    ast.If,
    ast.For,
    ast.While,
    ast.With,
    ast.Try,
    ast.AsyncFor,
    ast.AsyncWith,
)


class FunctionLength(Rule):
    code = "function-length"
    family = "shape"

    def visit_functiondef(self, node: ast.FunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def visit_asyncfunctiondef(self, node: ast.AsyncFunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def _measure(self, node: FunctionNode, ctx: Context) -> None:
        limit = ctx.threshold("function_length")
        length = _code_line_count(node)

        if length > limit:
            ctx.report(
                node,
                message=f"function `{node.name}` is hard to take in at one glance",
                grounds=f"it spans {length} lines of code; the configured limit is {limit}",
                help="split it by logical step, one step per function",
            )


class NestingDepth(Rule):
    code = "nesting-depth"
    family = "shape"

    def visit_functiondef(self, node: ast.FunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def visit_asyncfunctiondef(self, node: ast.AsyncFunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def _measure(self, node: FunctionNode, ctx: Context) -> None:
        limit = ctx.threshold("nesting_depth")
        depth = _max_depth(node)

        if depth > limit:
            ctx.report(
                node,
                message=f"function `{node.name}` nests too deeply to follow",
                grounds=f"it reaches {depth} levels of nesting; the configured limit is {limit}",
                help="flatten with early returns, or extract the inner block",
            )


class ArgumentCount(Rule):
    code = "argument-count"
    family = "shape"

    def visit_functiondef(self, node: ast.FunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def visit_asyncfunctiondef(self, node: ast.AsyncFunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def _measure(self, node: FunctionNode, ctx: Context) -> None:
        if ctx.signature_exempt(node):
            return

        limit = ctx.threshold("argument_count")
        count = _required_argument_count(node)

        if count > limit:
            ctx.report(
                node,
                message=f"function `{node.name}` takes too many arguments to call safely",
                grounds=f"it takes {count} required arguments; the configured limit is {limit}",
                help="group related arguments into a dataclass, or split the function",
            )


class ReturnCount(Rule):
    code = "return-count"
    family = "shape"

    def visit_functiondef(self, node: ast.FunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def visit_asyncfunctiondef(self, node: ast.AsyncFunctionDef, ctx: Context) -> None:
        self._measure(node, ctx)

    def _measure(self, node: FunctionNode, ctx: Context) -> None:
        limit = ctx.threshold("return_count")
        count = _own_return_count(node)

        if count > limit:
            ctx.report(
                node,
                message=f"function `{node.name}` exits from too many places",
                grounds=f"it has {count} return statements; the configured limit is {limit}",
                help="converge the branches toward one or two exit points",
            )


SCOPE_BOUNDARIES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)


def _max_depth(function: FunctionNode) -> int:
    def walk(node: ast.AST, depth: int) -> int:
        deepest = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, SCOPE_BOUNDARIES):
                continue
            child_depth = depth + isinstance(child, NESTING_NODES)
            deepest = max(deepest, walk(child, child_depth))
        return deepest

    return walk(function, 0)


def _code_line_count(function: FunctionNode) -> int:
    covered: set[int] = set()
    body = function.body

    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]

    for statement in body:
        covered.update(range(statement.lineno, (statement.end_lineno or statement.lineno) + 1))

    return len(covered)


def _required_argument_count(function: FunctionNode) -> int:
    args = function.args
    positional = [*args.posonlyargs, *args.args]

    if positional and positional[0].arg in ("self", "cls"):
        positional = positional[1:]

    required_positional = len(positional) - len(args.defaults)
    required_keyword = sum(1 for default in args.kw_defaults if default is None)

    return max(required_positional, 0) + required_keyword


def _own_return_count(function: FunctionNode) -> int:
    count = 0
    stack: list[ast.AST] = list(ast.iter_child_nodes(function))

    while stack:
        node = stack.pop()
        if isinstance(node, SCOPE_BOUNDARIES):
            continue
        if isinstance(node, ast.Return):
            count += 1
        stack.extend(ast.iter_child_nodes(node))

    return count


SHAPE_RULES = (FunctionLength, NestingDepth, ArgumentCount, ReturnCount)
