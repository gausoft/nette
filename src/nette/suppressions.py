from __future__ import annotations

import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Iterable

from nette.findings import Finding, Severity
from nette.parsing import SourceFile, parse_source

ALLOW_PATTERN: Final = re.compile(r"#\s*nette:\s*allow\(([a-z][a-z-]*)\)\s*(.*)")
MISSING_REASON_CODE: Final = "bare-allow"
UNUSED_ALLOW_CODE: Final = "unused-allow"


@dataclass(frozen=True)
class Allow:
    code: str
    line: int
    reason: str
    file: Path


def collect_allows(source: SourceFile) -> list[Allow]:
    allows = []

    for token in source.tokens:
        if token.type != tokenize.COMMENT:
            continue

        match = ALLOW_PATTERN.search(token.string)
        if match:
            allows.append(
                Allow(
                    code=match.group(1),
                    line=token.start[0],
                    reason=match.group(2).strip(),
                    file=source.path,
                )
            )

    return allows


def apply_allows(
    findings: list[Finding],
    source: SourceFile,
    *,
    file_scoped: frozenset[str],
    active: frozenset[str],
) -> list[Finding]:
    allows = collect_allows(source)
    if not allows:
        return findings

    used = {
        allow
        for allow in allows
        for finding in findings
        if _covers(allow, finding, file_scoped)
    }

    kept = [f for f in findings if not any(_covers(a, f, file_scoped) for a in allows)]
    kept.extend(_missing_reason_finding(a) for a in allows if not a.reason)
    kept.extend(
        _unused_finding(a)
        for a in allows
        if a.reason and a not in used and a.code in active
    )

    return kept


def list_allows(files: Iterable[Path]) -> list[Allow]:
    allows: list[Allow] = []

    for file in files:
        allows.extend(collect_allows(parse_source(file)))

    return allows


def _covers(allow: Allow, finding: Finding, file_scoped: frozenset[str]) -> bool:
    if allow.code != finding.code:
        return False

    if allow.code in file_scoped:
        return True

    return allow.line in (finding.line, finding.line - 1)


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


def _unused_finding(allow: Allow) -> Finding:
    return Finding(
        code=UNUSED_ALLOW_CODE,
        message=f"allow({allow.code}) suppresses nothing",
        grounds="the finding it exempted is gone, or the code it names moved away from this line",
        help="delete the marker, or move it back onto the line it should exempt",
        severity=Severity.WARNING,
        file=allow.file,
        line=allow.line,
        column=0,
        end_line=allow.line,
        end_column=0,
    )
