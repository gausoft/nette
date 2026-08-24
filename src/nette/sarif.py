from __future__ import annotations

import json
from pathlib import Path
from typing import Final, Sequence
from urllib.parse import quote

from nette import __version__
from nette.config import find_root
from nette.findings import Finding, Severity

SCHEMA: Final = "https://json.schemastore.org/sarif-2.1.0.json"
VERSION: Final = "2.1.0"
LEVELS: Final = {
    Severity.ERROR: "error",
    Severity.WARNING: "warning",
    Severity.INFO: "note",
}


def render_sarif(findings: Sequence[Finding]) -> str:
    ordered = sorted(findings)
    root = _root(ordered)
    codes = {code: index for index, code in enumerate(sorted({f.code for f in ordered}))}

    return json.dumps(_document(ordered, root, codes), indent=2, sort_keys=True) + "\n"


def _document(findings: Sequence[Finding], root: Path, codes: dict[str, int]) -> dict:
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
                        "rules": _rules(findings, codes),
                    }
                },
                "results": [_result(finding, root, codes) for finding in findings],
            }
        ],
    }


def _rules(findings: Sequence[Finding], codes: dict[str, int]) -> list[dict]:
    described = {finding.code: finding for finding in reversed(list(findings))}

    return [
        {
            "id": code,
            "name": code,
            "shortDescription": {"text": described[code].help},
            "properties": {"problem.severity": described[code].severity.value},
        }
        for code in sorted(codes)
    ]


def _result(finding: Finding, root: Path, codes: dict[str, int]) -> dict:
    return {
        "ruleId": finding.code,
        "ruleIndex": codes[finding.code],
        "level": LEVELS[finding.severity],
        "message": {"text": f"{finding.message}. {finding.grounds}. Fix: {finding.help}"},
        "locations": [
            {
                "physicalLocation": {
                    "artifactLocation": {"uri": _uri(finding.file, root)},
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


def _root(findings: Sequence[Finding]) -> Path:
    if not findings:
        return Path.cwd()

    return find_root([findings[0].file])


def _uri(path: Path, root: Path) -> str:
    try:
        relative = path.resolve().relative_to(root)
    except ValueError:
        relative = path

    return quote(relative.as_posix())
