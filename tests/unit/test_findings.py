from pathlib import Path

from nette.findings import Finding, Severity


def make_finding(**overrides):
    defaults = dict(
        code="function-length",
        message="function too long",
        grounds="repo p90 is 34 lines, this one has 120",
        help="split by logical step",
        severity=Severity.WARNING,
        file=Path("pkg/mod.py"),
        line=3,
        column=0,
        end_line=40,
        end_column=0,
    )
    defaults.update(overrides)
    return Finding(**defaults)


def test_finding_is_immutable():
    finding = make_finding()
    try:
        finding.code = "NET999"
        raised = False
    except AttributeError:
        raised = True
    assert raised


def test_finding_not_fixable_by_default():
    assert make_finding().fixable is False


def test_findings_sort_by_file_then_line_then_column():
    later = make_finding(file=Path("b.py"), line=1, column=0)
    earlier = make_finding(file=Path("a.py"), line=9, column=2)
    same_file_later = make_finding(file=Path("a.py"), line=9, column=5)

    ordered = sorted([later, same_file_later, earlier])

    assert ordered == [earlier, same_file_later, later]
