from __future__ import annotations

import ast
import re
import tomllib
from fnmatch import fnmatch
from pathlib import Path
from typing import Final

from nette.findings import Severity
from nette.frameworks import dotted_name
from nette.paths import within_root
from nette.rules import KNOWN_RULE_CODES
from nette.rules.base import Context, Rule

RULES_PATH: Final = Path(".nette/rules.toml")
FAMILY: Final = "local"
REQUIRED: Final = ("id", "kind", "message", "why", "fix")
KINDS: Final = frozenset({"forbid-call", "name-must-match", "import-boundary"})
TARGETS: Final = frozenset({"function", "class"})
FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef


class HouseRule(Rule):
    family = FAMILY
    scope = "function"
    severity = Severity.WARNING

    def __init__(self, declaration: dict) -> None:
        self.code = declaration["id"]
        self.message = declaration["message"]
        self.why = declaration["why"]
        self.fix = declaration["fix"]
        self.files = declaration.get("files", "")
        self.fingerprint = repr(sorted(declaration.items()))

    def concerns(self, ctx: Context) -> bool:
        if not self.files:
            return True

        return fnmatch("/".join(within_root(ctx.source.path)), self.files)

    def flag(self, node: ast.AST, ctx: Context, grounds: str) -> None:
        ctx.report(node, message=self.message, grounds=grounds, help=self.fix)


class ForbidCall(HouseRule):
    def __init__(self, declaration: dict) -> None:
        super().__init__(declaration)
        self.call = declaration["call"]

    def visit_call(self, node: ast.Call, ctx: Context) -> None:
        called = dotted_name(node.func)
        if not self.concerns(ctx) or not _matches(self.call, called):
            return

        self.flag(node, ctx, f"`{called}` is called here. {self.why}")


class NameMustMatch(HouseRule):
    def __init__(self, declaration: dict) -> None:
        super().__init__(declaration)
        self.target = declaration["target"]
        self.pattern = re.compile(declaration["pattern"])

    def visit_functiondef(self, node: FunctionNode, ctx: Context) -> None:
        if self.target == "function":
            self._judge(node, ctx)

    def visit_asyncfunctiondef(self, node: FunctionNode, ctx: Context) -> None:
        if self.target == "function":
            self._judge(node, ctx)

    def visit_classdef(self, node: ast.ClassDef, ctx: Context) -> None:
        if self.target == "class":
            self._judge(node, ctx)

    def _judge(self, node: FunctionNode | ast.ClassDef, ctx: Context) -> None:
        if not self.concerns(ctx) or self.pattern.match(node.name):
            return

        self.flag(node, ctx, f"`{node.name}` does not match `{self.pattern.pattern}`. {self.why}")


class ImportBoundary(HouseRule):
    def __init__(self, declaration: dict) -> None:
        super().__init__(declaration)
        self.files = declaration["from"]
        self.forbid = declaration["forbid"]

    def visit_import(self, node: ast.Import, ctx: Context) -> None:
        self._judge(node, ctx, [alias.name for alias in node.names])

    def visit_importfrom(self, node: ast.ImportFrom, ctx: Context) -> None:
        module = node.module or ""
        reached = [module] + [
            f"{module}.{alias.name}" if module else alias.name for alias in node.names
        ]
        self._judge(node, ctx, reached)

    def _judge(self, node: ast.AST, ctx: Context, modules: list[str]) -> None:
        if not self.concerns(ctx):
            return

        crossed = next((m for m in modules if _under(m, self.forbid)), "")
        if crossed:
            self.flag(node, ctx, f"this file imports `{crossed}`. {self.why}")


KIND_CLASSES: Final = {
    "forbid-call": (ForbidCall, ("call",)),
    "name-must-match": (NameMustMatch, ("target", "pattern")),
    "import-boundary": (ImportBoundary, ("from", "forbid")),
}


def load_house_rules(root: Path) -> list[HouseRule]:
    source = root / RULES_PATH
    if not source.exists():
        return []

    try:
        payload = tomllib.loads(source.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"{source}: {error}") from error
    except OSError as error:
        raise ValueError(f"{source}: cannot be read, {error}") from error

    declarations = payload.get("rule", [])
    if not isinstance(declarations, list):
        raise ValueError(f"{source}: expected a list of [[rule]] tables")

    rules = [_build(declaration, source) for declaration in declarations]
    _reject_duplicates(rules, source)

    return rules


def _build(declaration: object, source: Path) -> HouseRule:
    if not isinstance(declaration, dict):
        raise ValueError(f"{source}: every rule must be a [[rule]] table, got {declaration!r}")

    where = f"{source}: rule {declaration.get('id', '<unnamed>')!r}"
    _require(declaration, REQUIRED, where)

    kind = declaration["kind"]
    if kind not in KINDS:
        raise ValueError(f"{where}: unknown kind {kind!r}, expected one of {sorted(KINDS)}")

    rule_class, extra = KIND_CLASSES[kind]
    _require(declaration, extra, where)
    _require_text(declaration, "files", where)

    if kind == "name-must-match" and declaration["target"] not in TARGETS:
        raise ValueError(f"{where}: target must be one of {sorted(TARGETS)}")

    try:
        return rule_class(declaration)
    except re.error as error:
        raise ValueError(f"{where}: bad pattern, {error}") from error


def _require(declaration: dict, keys: tuple[str, ...], where: str) -> None:
    missing = [
        key
        for key in keys
        if not isinstance(declaration.get(key), str) or not declaration[key].strip()
    ]
    if missing:
        raise ValueError(f"{where}: missing or not text: {', '.join(missing)}")


def _require_text(declaration: dict, key: str, where: str) -> None:
    if key in declaration and not isinstance(declaration[key], str):
        raise ValueError(f"{where}: {key} must be text, got {declaration[key]!r}")


def _reject_duplicates(rules: list[HouseRule], source: Path) -> None:
    seen: set[str] = set()

    for rule in rules:
        if rule.code in KNOWN_RULE_CODES:
            raise ValueError(f"{source}: {rule.code!r} is the name of a built-in rule")
        if rule.code in seen:
            raise ValueError(f"{source}: {rule.code!r} is declared twice")
        seen.add(rule.code)


def _matches(wanted: str, called: str) -> bool:
    if not called:
        return False

    if "." in wanted:
        return called == wanted

    return called == wanted or called.endswith(f".{wanted}")


def _under(module: str, forbidden: str) -> bool:
    return module == forbidden or module.startswith(f"{forbidden}.")
