from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, Sequence

from nette.findings import Finding
from nette.parsing import parse_source
from nette.rules.base import Context, Rule


def check_files(
    files: Iterable[Path],
    *,
    rules: Sequence[Rule],
    thresholds: dict[str, int] | None = None,
) -> list[Finding]:
    findings: list[Finding] = []

    for file in files:
        findings.extend(_check_one(file, rules, thresholds))

    return sorted(findings)


def _check_one(
    file: Path,
    rules: Sequence[Rule],
    thresholds: dict[str, int] | None,
) -> list[Finding]:
    source = parse_source(file)
    if source.tree is None:
        return list(source.errors)

    contexts = [(rule, Context(source, rule, thresholds)) for rule in rules]

    for node in ast.walk(source.tree):
        handler_name = f"visit_{type(node).__name__.lower()}"
        for rule, ctx in contexts:
            handler = getattr(rule, handler_name, None)
            if handler is not None:
                handler(node, ctx)

    return [finding for _, ctx in contexts for finding in ctx.findings]
