from __future__ import annotations

import json
from typing import Callable, Final, Sequence

from nette.findings import Finding, Severity

SCHEMA_VERSION: Final = 1


def render(findings: Sequence[Finding], *, format: str) -> str:
    renderer = _RENDERERS.get(format)
    if renderer is None:
        known = ", ".join(sorted(_RENDERERS))
        raise ValueError(f"unknown output format {format!r}; expected one of: {known}")

    return renderer(findings)


def _location(finding: Finding) -> str:
    return f"{finding.file} {finding.line}:{finding.column + 1}"


def _concise(findings: Sequence[Finding]) -> str:
    return "\n".join(
        f"{f.severity.value}[{f.code}] {_location(f)} {f.message}" for f in findings
    )


def _full(findings: Sequence[Finding]) -> str:
    blocks = [
        (
            f"{f.severity.value}[{f.code}] {_location(f)}\n"
            f"  {f.message}\n"
            f"  why: {f.grounds}\n"
            f"  fix: {f.help}"
        )
        for f in findings
    ]

    return "\n\n".join(blocks)


def _agent(findings: Sequence[Finding]) -> str:
    by_severity = {level.value: 0 for level in Severity}
    for finding in findings:
        by_severity[finding.severity.value] += 1

    payload = {
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "total": len(findings),
            "by_severity": by_severity,
            "fixable": sum(f.fixable for f in findings),
        },
        "findings": [
            {
                "code": f.code,
                "severity": f.severity.value,
                "file": str(f.file),
                "line": f.line,
                "column": f.column,
                "message": f.message,
                "grounds": f.grounds,
                "fixable": f.fixable,
                "instruction": (
                    f"{f.severity.value}: {f.message} ({f.grounds}). "
                    f"To resolve: edit {f.file}:{f.line} - {f.help}."
                ),
            }
            for f in findings
        ],
    }

    return json.dumps(payload, indent=2)


def _json(findings: Sequence[Finding]) -> str:
    payload = [
        {
            "code": f.code,
            "message": f.message,
            "grounds": f.grounds,
            "help": f.help,
            "severity": f.severity.value,
            "file": str(f.file),
            "line": f.line,
            "column": f.column,
            "end_line": f.end_line,
            "end_column": f.end_column,
            "fixable": f.fixable,
        }
        for f in findings
    ]

    return json.dumps(payload, indent=2)


_RENDERERS: Final[dict[str, Callable[[Sequence[Finding]], str]]] = {
    "concise": _concise,
    "full": _full,
    "agent": _agent,
    "json": _json,
}
