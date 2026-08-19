from nette.engine import check_files
from nette.rules.shape import FunctionLength, ReturnCount
from nette.rules.structure import FileNaming, FileSize
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


def test_file_scoped_allow_works_far_from_the_anchor(write_file):
    file = write_file(
        "import os\n"
        "\n"
        "\n"
        "def a():\n"
        "    return os\n"
        "\n"
        "\n"
        "# nette: allow(file-naming) vendor file kept under its upstream name\n",
        name="BadName.py",
    )

    assert check(file, rules=[FileNaming()]) == []


def test_file_scoped_allow_survives_an_edit_that_moves_the_anchor(write_file):
    marked = "# nette: allow(file-naming) vendor file kept under its upstream name\n"
    before = write_file(f"{marked}def a():\n    pass\n", name="BadName.py")
    after = write_file(
        f"import os\n{marked}def a():\n    return os\n", name="BadNameEdited.py"
    )

    assert check(before, rules=[FileNaming()]) == []
    assert check(after, rules=[FileNaming()]) == []


def test_allow_that_suppresses_nothing_is_reported(write_file):
    file = write_file(
        "def small():  # nette: allow(function-length) no longer long\n    pass\n"
    )

    findings = check(file)

    assert [f.code for f in findings] == ["unused-allow"]
    assert "function-length" in findings[0].message


def test_allow_for_a_disabled_rule_is_not_reported_as_unused(write_file):
    file = write_file(
        "def small():  # nette: allow(return-count) rule not selected here\n    pass\n"
    )

    assert check(file) == []


def test_bare_allow_is_not_also_reported_as_unused(write_file):
    file = write_file("def small():  # nette: allow(function-length)\n    pass\n")

    assert [f.code for f in check(file)] == ["bare-allow"]


def test_allow_for_a_calibrated_rule_is_not_unused_without_a_profile(write_file):
    file = write_file(
        "# nette: allow(file-size) vendored table, split upstream first\n"
        "def a():\n    pass\n"
    )

    assert check(file, rules=[FileSize()]) == []


def test_a_marker_inside_a_string_is_not_a_suppression(write_file):
    file = write_file(
        "SAMPLE = \"def big():  # nette: allow(function-length) inside a string\"\n"
        f"def big():\n{LONG_BODY}\n"
    )

    assert [f.code for f in check(file)] == ["function-length"]


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
