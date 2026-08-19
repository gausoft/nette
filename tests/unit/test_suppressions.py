from nette.engine import check_files
from nette.rules.shape import FunctionLength, ReturnCount
from nette.suppressions import list_allows

LONG_BODY = "\n".join(f"    x{i} = {i}" for i in range(101))


def check(file, rules=None):
    return check_files([file], rules=rules or [FunctionLength()])


def test_allow_with_reason_silences_the_finding(write_file):
    file = write_file(
        f"def big():  # nette: allow(function-length) generated parser table\n{LONG_BODY}\n"
    )

    assert check(file) == []


def test_allow_on_line_above_also_works(write_file):
    file = write_file(
        f"# nette: allow(function-length) generated parser table\ndef big():\n{LONG_BODY}\n"
    )

    assert check(file) == []


def test_allow_without_reason_is_itself_a_finding(write_file):
    file = write_file(f"def big():  # nette: allow(function-length)\n{LONG_BODY}\n")

    findings = check(file)

    assert [f.code for f in findings] == ["bare-allow"]
    assert "reason" in findings[0].message


def test_allow_for_another_code_does_not_silence(write_file):
    file = write_file(
        f"def big():  # nette: allow(return-count) wrong code\n{LONG_BODY}\n"
    )

    codes = [f.code for f in check(file)]

    assert "function-length" in codes


def test_list_allows_reports_all_markers(write_file):
    file = write_file(
        "# nette: allow(function-length) table generator output\n"
        "def a():\n"
        "    pass\n"
        "\n"
        "def b():  # nette: allow(return-count) state machine, clearest flat\n"
        "    pass\n"
    )

    allows = list_allows([file])

    assert [(a.code, a.line) for a in allows] == [("function-length", 1), ("return-count", 5)]
    assert allows[0].reason == "table generator output"
