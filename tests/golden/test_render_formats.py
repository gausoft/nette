import json
from pathlib import Path

from nette.findings import Finding, Severity
from nette.output import render

FINDINGS = [
    Finding(
        code="function-length",
        message="function `load` is hard to take in at one glance",
        grounds="it spans 120 lines of code; the configured limit is 100",
        help="split it by logical step, one step per function",
        severity=Severity.WARNING,
        file=Path("src/app.py"),
        line=10,
        column=0,
        end_line=140,
        end_column=0,
    ),
    Finding(
        code="parse-error",
        message="syntax error: invalid syntax",
        grounds="the file does not parse as Python",
        help="fix the syntax error before nette can judge this file",
        severity=Severity.ERROR,
        file=Path("src/broken.py"),
        line=3,
        column=4,
        end_line=3,
        end_column=4,
    ),
]
CLUSTER = [
    Finding(
        code="over-guarded",
        message="this file guards far more than the rest of the repo",
        grounds="9 of its 12 functions wrap code in try blocks",
        help="keep try blocks for real boundaries",
        severity=Severity.WARNING,
        file=Path("services/accounts") / name,
        line=line,
        column=0,
        end_line=line,
        end_column=0,
    )
    for name, line in (
        ("client.py", 1),
        ("client.py", 2),
        ("client.py", 3),
        ("client.py", 4),
        ("serializers.py", 5),
    )
]


def test_concise_is_one_line_per_finding():
    text = render(FINDINGS, format="concise")

    lines = text.splitlines()
    assert len(lines) == 2
    assert lines[0] == (
        "warning[function-length] src/app.py 10:1 "
        "function `load` is hard to take in at one glance"
    )


def test_full_shows_grounds_and_help():
    text = render(FINDINGS, format="full")

    assert "warning[function-length]" in text
    assert "src/app.py 10:1" in text
    assert "why: it spans 120 lines of code" in text
    assert "fix: split it by logical step" in text


def test_agent_format_is_versioned_json_with_instructions():
    payload = json.loads(render(FINDINGS, format="agent"))

    assert payload["schema_version"] == 1
    assert payload["summary"]["total"] == 2
    assert payload["summary"]["by_severity"] == {"error": 1, "warning": 1, "info": 0}

    first = payload["findings"][0]
    assert first["code"] == "function-length"
    assert first["file"] == "src/app.py"
    assert first["line"] == 10
    assert "src/app.py:10" in first["instruction"]
    assert first["fixable"] is False


def test_json_format_round_trips_all_fields():
    payload = json.loads(render(FINDINGS, format="json"))

    assert len(payload) == 2
    assert payload[0]["grounds"].startswith("it spans 120")
    assert payload[1]["severity"] == "error"


def test_empty_findings_render_cleanly():
    assert render([], format="concise") == ""
    assert json.loads(render([], format="agent"))["summary"]["total"] == 0


def test_unknown_format_is_rejected():
    try:
        render([], format="xml")
        raised = False
    except ValueError:
        raised = True
    assert raised
