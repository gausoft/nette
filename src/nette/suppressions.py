from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable

from nette.findings import Finding, Severity
from nette.parsing import SourceFile, parse_source

ALLOW_PATTERN: Final = re.compile(r"#\s*nette:\s*allow\(([a-z][a-z-]*)\)\s*(.*)")
MISSING_REASON_CODE: Final = "bare-allow"


@dataclass(frozen=True)
class Allow:
    code: str
    line: int
    reason: str
    file: Path


def collect_allows(source: SourceFile) -> list[Allow]:
    allows = []

    for index, text in enumerate(source.lines, start=1):
        match = ALLOW_PATTERN.search(text)
        if match:
            allows.append(
                Allow(
                    code=match.group(1),
                    line=index,
                    reason=match.group(2).strip(),
                    file=source.path,
                )
            )

    return allows


def apply_allows(findings: list[Finding], source: SourceFile) -> list[Finding]:
    allows = collect_allows(source)
    if not allows:
        return findings

    kept = [f for f in findings if not _is_allowed(f, allows)]
    kept.extend(_missing_reason_finding(a) for a in allows if not a.reason)

    return kept


def list_allows(files: Iterable[Path]) -> list[Allow]:
    allows: list[Allow] = []

    for file in files:
        allows.extend(collect_allows(parse_source(file)))

    return allows


def _is_allowed(finding: Finding, allows: list[Allow]) -> bool:
    return any(
        allow.code == finding.code
        and allow.line in (finding.line, finding.line - 1)
        for allow in allows
    )


def _missing_reason_finding(allow: Allow) -> Finding:
    return Finding(
        code=MISSING_REASON_CODE,
        message=f"allow({allow.code}) has no reason",
        grounds="a suppression without a rationale cannot be told apart from a dodge",
        help=f"write the reason after the marker: # nette: allow({allow.code}) <why>",
        severity=Severity.WARNING,
        file=allow.file,
        line=allow.line,
        column=0,
        end_line=allow.line,
        end_column=0,
    )
