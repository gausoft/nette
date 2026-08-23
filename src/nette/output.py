from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Final, Sequence

from nette.findings import Finding, Severity

SCHEMA_VERSION: Final = 1
WORST_FILES: Final = 3


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


def _summary(findings: Sequence[Finding]) -> str:
    if not findings:
        return ""

    by_directory: dict[Path, list[Finding]] = defaultdict(list)
    for finding in findings:
        by_directory[finding.file.parent].append(finding)

    files = {finding.file for finding in findings}
    lines = [f"{len(findings)} findings in {len(files)} files", ""]

    for directory, group in sorted(
        by_directory.items(), key=lambda item: (-len(item[1]), str(item[0]))
    ):
        touched = Counter(finding.file for finding in group)
        lines.append(f"{directory or '.'}  {len(group)} findings in {len(touched)} files")
        lines.extend(_worst(touched))

    return "\n".join(lines)


def _worst(touched: Counter[Path]) -> list[str]:
    ranked = sorted(touched.items(), key=lambda item: (-item[1], item[0].name))

    return [f"  {file.name}  {count}" for file, count in ranked[:WORST_FILES]]


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
    "summary": _summary,
    "agent": _agent,
    "json": _json,
}
