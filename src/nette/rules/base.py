from __future__ import annotations

import ast

from nette.calibration import Profile
from nette.findings import Finding, Severity
from nette.frameworks import SIGNATURE_EXEMPT_RULES, is_route_endpoint
from nette.parsing import SourceFile

DEFAULT_THRESHOLDS: dict[str, int] = {
    "function_length": 100,
    "nesting_depth": 5,
    "argument_count": 6,
    "return_count": 5,
    "short_name_scope": 15,
}


class Rule:
    code: str = ""
    family: str = ""
    scope: str = "function"
    baseline: str = ""
    severity: Severity = Severity.WARNING


class Context:
    def __init__(
        self,
        source: SourceFile,
        rule: Rule,
        thresholds: dict[str, int] | None = None,
        profile: Profile | None = None,
        framework: str | None = None,
    ) -> None:
        self.source = source
        self.profile = profile
        self.framework = framework
        self._rule = rule
        self._thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
        self._findings: list[Finding] = []

    def threshold(self, name: str) -> int:
        return self._thresholds[name]

    def baseline(self) -> float | None:
        if self.profile is None:
            return None

        return self.profile.metrics.get(self._rule.baseline)

    def signature_exempt(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        return (
            self.framework == "fastapi"
            and self._rule.code in SIGNATURE_EXEMPT_RULES
            and is_route_endpoint(node)
        )

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
