from nette.engine import check_files
from nette.rules.shape import FunctionLength


def check(file, threshold=None):
    thresholds = {"function_length": threshold} if threshold else {}
    return check_files([file], rules=[FunctionLength()], thresholds=thresholds)


def test_short_function_is_quiet(write_file):
    file = write_file("def ok():\n    return 1\n")

    assert check(file) == []


def test_function_over_default_threshold_is_flagged(write_file):
    body = "\n".join(f"    x{i} = {i}" for i in range(101))
    file = write_file(f"def big():\n{body}\n")

    findings = check(file)

    assert [f.code for f in findings] == ["function-length"]
    assert "big" in findings[0].message
    assert "101" in findings[0].grounds
    assert findings[0].line == 1


def test_threshold_override_lowers_the_bar(write_file):
    file = write_file("def f():\n    a = 1\n    b = 2\n    c = 3\n")

    assert check(file, threshold=2) != []
    assert check(file, threshold=10) == []


def test_nested_function_measured_separately(write_file):
    inner_body = "\n".join(f"        y{i} = {i}" for i in range(101))
    file = write_file(f"def outer():\n    def inner():\n{inner_body}\n    return inner\n")

    findings = check(file)

    assert sorted(f.message for f in findings)[0].count("inner") == 1
