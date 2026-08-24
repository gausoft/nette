from __future__ import annotations

import json
from pathlib import Path
from typing import Final, Sequence

from nette import __version__
from nette.findings import Finding, Severity

SCHEMA: Final = "https://json.schemastore.org/sarif-2.1.0.json"
VERSION: Final = "2.1.0"
LEVELS: Final = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.INFO: "note",
}


def render_sarif(findings: Sequence[Finding]) -> str:
    return json.dumps(_document(findings), indent=2, sort_keys=True) + "\n"


def _document(findings: Sequence[Finding]) -> dict:
    return {
        "$schema": SCHEMA,
        "version": VERSION,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "nette",
                        "version": __version__,
                        "informationUri": "https://github.com/gausoft/nette",
                        "rules": _rules(findings),
                    }
                },
                "results": [_result(finding, _codes(findings)) for finding in findings],
            }
        ],
    }


def _codes(findings: Sequence[Finding]) -> list[str]:
    return sorted({finding.code for finding in findings})


def _rules(findings: Sequence[Finding]) -> list[dict]:
    described = {finding.code: finding for finding in reversed(list(findings))}

    return [
        {
            "id": code,
            "name": code,
            "shortDescription": {"text": described[code].message},
            "fullDescription": {"text": described[code].grounds},
            "help": {"text": described[code].help},
            "properties": {"problem.severity": described[code].severity.value},
        }
        for code in sorted(described)
    ]


def _result(finding: Finding, codes: list[str]) -> dict:
    return {
        "ruleId": finding.code,
        "ruleIndex": codes.index(finding.code),
        "level": LEVELS[finding.severity],
        "message": {"text": f"{finding.message}. {finding.grounds}. Fix: {finding.help}"},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": _uri(finding.file)},
                    "region": {
                        "startLine": finding.line,
                        "startColumn": finding.column + 1,
                        "endLine": finding.end_line,
                        "endColumn": finding.end_column + 1,
                    },
                }
            }
        ],
    }


def _uri(path: Path) -> str:
    try:
        relative = path.resolve().relative_to(Path.cwd())
    except ValueError:
        return path.as_posix()

    return relative.as_posix()
