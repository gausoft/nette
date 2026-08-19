from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Sequence

from nette.findings import Finding
from nette.parsing import parse_source
from nette.rules import Context, Rule


def check_files(files: Iterable[Path], *, rules: Sequence[Rule]) -> list[Finding]:
    findings: list[Finding] = []

    for file in files:
        findings.extend(_check_one(file, rules))

    return sorted(findings)


def _check_one(file: Path, rules: Sequence[Rule]) -> list[Finding]:
    source = parse_source(file)
    if source.tree is None:
        return list(source.errors)

    contexts = [(rule, Context(source, rule)) for rule in rules]
    handlers = [
        (getattr(rule, f"visit_{type(node).__name__.lower()}", None), node, ctx)
        for node in ast.walk(source.tree)
        for rule, ctx in contexts
    ]

    for handler, node, ctx in handlers:
        if handler is not None:
            handler(node, ctx)

    return [finding for _, ctx in contexts for finding in ctx.findings]
