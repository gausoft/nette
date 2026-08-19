from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nette import __version__
from nette.calibration import Profile
from nette.findings import Finding, Severity


class Cache:
    def __init__(self, location: Path) -> None:
        self._location = location

    def get(self, file: Path, config_key: str) -> list[Finding] | None:
        entry = self._entry_path(file, config_key)
        if not entry.exists():
            return None

        try:
            payload = json.loads(entry.read_text())
            return [_finding_from_dict(item) for item in payload]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            entry.unlink(missing_ok=True)
            return None

    def put(self, file: Path, config_key: str, findings: list[Finding]) -> None:
        entry = self._entry_path(file, config_key)
        entry.parent.mkdir(parents=True, exist_ok=True)

        payload = [_finding_to_dict(f) for f in findings]
        scratch = entry.with_suffix(".tmp")
        scratch.write_text(json.dumps(payload))
        scratch.replace(entry)

    def _entry_path(self, file: Path, config_key: str) -> Path:
        content_hash = hashlib.sha256(file.read_bytes()).hexdigest()
        key = hashlib.sha256(
            f"{__version__}:{config_key}:{file}:{content_hash}".encode()
        ).hexdigest()

        return self._location / f"{key}.json"


def config_key(
    thresholds: dict[str, int] | None,
    rule_codes: list[str],
    profile: Profile | None = None,
) -> str:
    material = json.dumps(
        {
            "thresholds": thresholds or {},
            "rules": sorted(rule_codes),
            "profile": profile.metrics if profile else None,
        },
        sort_keys=True,
    )

    return hashlib.sha256(material.encode()).hexdigest()


def _finding_to_dict(finding: Finding) -> dict:
    return {
        "code": finding.code,
        "message": finding.message,
        "grounds": finding.grounds,
        "help": finding.help,
        "severity": finding.severity.value,
        "file": str(finding.file),
        "line": finding.line,
        "column": finding.column,
        "end_line": finding.end_line,
        "end_column": finding.end_column,
        "fixable": finding.fixable,
    }


def _finding_from_dict(item: dict) -> Finding:
    return Finding(
        code=item["code"],
        message=item["message"],
        grounds=item["grounds"],
        help=item["help"],
        severity=Severity(item["severity"]),
        file=Path(item["file"]),
        line=item["line"],
        column=item["column"],
        end_line=item["end_line"],
        end_column=item["end_column"],
        fixable=item["fixable"],
    )
