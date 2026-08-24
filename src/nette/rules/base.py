from __future__ import annotations

import ast

from nette.calibration import Profile
from nette.findings import Finding, Severity
from nette.frameworks import SIGNATURE_EXEMPT_RULES, is_route_endpoint, wears_decorator
from nette.parsing import SourceFile

DEFAULT_THRESHOLDS: dict[str, int] = {
    "function_length": 100,
    "branch_density": 12,
    "nesting_depth": 5,
    "argument_count": 6,
    "return_count": 5,
    "short_name_scope": 15,
    "duplication_similarity": 85,
    "duplication_min_lines": 20,
    "data_types_per_module": 2,
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
        active_codes: frozenset[str] = frozenset(),
        exempt_decorated_by: tuple[str, ...] = (),
    ) -> None:
        self.source = source
        self.profile = profile
        self.framework = framework
        self.active_codes = active_codes
        self.exempt_decorated_by = exempt_decorated_by
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
        if self._rule.code not in SIGNATURE_EXEMPT_RULES:
            return False

        if self.framework == "fastapi" and is_route_endpoint(node):
            return True

        return wears_decorator(node, self.exempt_decorated_by)

    def report(self, node: ast.AST, *, message: str, grounds: str, help: str) -> None:
        line = getattr(node, "lineno", 1)
        column = getattr(node, "col_offset", 0)
        finding = Finding(
            code=self._rule.code,
            message=message,
            grounds=grounds,
            help=help,
            severity=self._rule.severity,
            file=self.source.path,
            line=line,
            column=column,
            end_line=getattr(node, "end_lineno", None) or line,
            end_column=getattr(node, "end_col_offset", None) or column,
        )
        self._findings.append(finding)

    @property
    def findings(self) -> list[Finding]:
        return self._findings
