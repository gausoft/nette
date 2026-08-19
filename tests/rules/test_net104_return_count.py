from nette.engine import check_files
from nette.rules.shape import ReturnCount


def check(file, threshold=None):
    thresholds = {"return_count": threshold} if threshold else {}
    return check_files([file], rules=[ReturnCount()], thresholds=thresholds)


def test_few_returns_is_quiet(write_file):
    file = write_file(
        "def ok(x):\n"
        "    if x:\n"
        "        return 1\n"
        "    return 0\n"
    )

    assert check(file) == []


def test_too_many_returns_is_flagged(write_file):
    file = write_file(
        "def scattered(x):\n"
        "    if x == 1:\n"
        "        return 1\n"
        "    if x == 2:\n"
        "        return 2\n"
        "    if x == 3:\n"
        "        return 3\n"
        "    if x == 4:\n"
        "        return 4\n"
        "    if x == 5:\n"
        "        return 5\n"
        "    return 0\n"
    )

    findings = check(file)

    assert [f.code for f in findings] == ["NET104"]
    assert "scattered" in findings[0].message
    assert "6" in findings[0].grounds


def test_nested_function_returns_not_attributed_to_parent(write_file):
    file = write_file(
        "def outer(x):\n"
        "    def inner(y):\n"
        "        if y == 1:\n"
        "            return 1\n"
        "        if y == 2:\n"
        "            return 2\n"
        "        return 0\n"
        "    return inner\n"
    )

    assert check(file) == []


def test_threshold_override(write_file):
    file = write_file(
        "def f(x):\n"
        "    if x:\n"
        "        return 1\n"
        "    return 0\n"
    )

    assert check(file, threshold=1) != []


def test_nested_helper_complexity_not_charged_to_parent(write_file):
    file = write_file(
        "def outer(x):\n"
        "    def helper(y):\n"
        "        if y == 1:\n"
        "            return 1\n"
        "        if y == 2:\n"
        "            return 2\n"
        "        if y == 3:\n"
        "            return 3\n"
        "        if y == 4:\n"
        "            return 4\n"
        "        if y == 5:\n"
        "            return 5\n"
        "        return 0\n"
        "    return helper(x)\n"
    )

    findings = check(file)

    assert all("outer" not in f.message for f in findings)
