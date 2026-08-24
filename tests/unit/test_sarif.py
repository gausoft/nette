import json
from pathlib import Path

from nette import __version__
from nette.findings import Finding, Severity
from nette.output import render


def finding(code="function-length", line=12, severity=Severity.WARNING, path="src/api.py"):
    return Finding(
        code=code,
        message="function `sync` is too long to take in at one glance",
        grounds="it spans 140 lines; the configured limit is 100",
        help="split it by responsibility",
        severity=severity,
        file=Path(path),
        line=line,
        column=0,
        end_line=line + 20,
        end_column=5,
    )


def sarif(findings):
    return json.loads(render(findings, format="sarif"))


def test_an_empty_run_is_still_a_valid_document():
    document = sarif([])

    assert document["version"] == "2.1.0"
    assert document["runs"][0]["tool"]["driver"]["name"] == "nette"
    assert document["runs"][0]["results"] == []


def test_the_driver_carries_the_installed_version():
    assert sarif([])["runs"][0]["tool"]["driver"]["version"] == __version__


def test_a_finding_becomes_a_result_with_its_region():
    region = sarif([finding()])["runs"][0]["results"][0]["locations"][0]["physicalLocation"]

    assert region["artifactLocation"]["uri"] == "src/api.py"
    assert region["region"] == {
        "startLine": 12,
        "startColumn": 1,
        "endLine": 32,
        "endColumn": 6,
    }


def test_the_message_carries_the_reason_and_the_fix():
    text = sarif([finding()])["runs"][0]["results"][0]["message"]["text"]

    assert "too long" in text and "140 lines" in text and "Fix: split it" in text


def test_every_rule_is_declared_once_and_indexed():
    document = sarif([finding(), finding(line=40), finding(code="nesting-depth")])
    rules = document["runs"][0]["tool"]["driver"]["rules"]
    results = document["runs"][0]["results"]

    assert [rule["id"] for rule in rules] == ["function-length", "nesting-depth"]
    for result in results:
        assert rules[result["ruleIndex"]]["id"] == result["ruleId"]


def test_severity_maps_to_the_sarif_vocabulary():
    levels = [
        sarif([finding(severity=severity)])["runs"][0]["results"][0]["level"]
        for severity in (Severity.ERROR, Severity.WARNING, Severity.INFO)
    ]

    assert levels == ["error", "warning", "note"]


def test_the_same_findings_render_the_same_bytes():
    findings = [finding(), finding(code="nesting-depth", line=3)]

    assert render(findings, format="sarif") == render(findings, format="sarif")
