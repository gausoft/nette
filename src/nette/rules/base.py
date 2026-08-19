from __future__ import annotations

import ast

from nette.calibration import Profile
from nette.findings import Finding, Severity
from nette.parsing import SourceFile

DEFAULT_THRESHOLDS: dict[str, int] = {
    "function_length": 100,
    "nesting_depth": 5,
    "argument_count": 6,
    "return_count": 5,
}


class Rule:
    code: str = ""
    severity: Severity = Severity.WARNING


class Context:
    def __init__(
        self,
        source: SourceFile,
        rule: Rule,
        thresholds: dict[str, int] | None = None,
        profile: Profile | None = None,
    ) -> None:
        self.source = source
        self.profile = profile
        self._rule = rule
        self._thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
        self._findings: list[Finding] = []

    def threshold(self, name: str) -> int:
        return self._thresholds[name]

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
