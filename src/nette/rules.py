from __future__ import annotations

import ast

from nette.findings import Finding, Severity
from nette.parsing import SourceFile


class Rule:
    code: str = ""
    severity: Severity = Severity.WARNING


class Context:
    def __init__(self, source: SourceFile, rule: Rule) -> None:
        self.source = source
        self._rule = rule
        self._findings: list[Finding] = []

    def report(self, node: ast.AST, *, message: str, grounds: str, help: str) -> None:
        finding = Finding(
            code=self._rule.code,
            message=message,
            grounds=grounds,
            help=help,
            severity=self._rule.severity,
            file=self.source.path,
            line=node.lineno,
            column=node.col_offset,
            end_line=node.end_lineno or node.lineno,
            end_column=node.end_col_offset or node.col_offset,
        )
        self._findings.append(finding)

    @property
    def findings(self) -> list[Finding]:
        return self._findings
