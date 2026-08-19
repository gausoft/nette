from nette.engine import check_files
from nette.rules.naming import ShortNameLongScope


def check(file, threshold=None):
    thresholds = {"short_name_scope": threshold} if threshold else {}
    return check_files([file], rules=[ShortNameLongScope()], thresholds=thresholds)


def spread(name, lines):
    filler = "\n".join(f"    y{i} = {i}" for i in range(lines))
    return f"def f():\n    {name} = fetch()\n{filler}\n    return {name}\n"


def test_short_name_with_long_life_is_flagged(write_file):
    file = write_file(spread("r", 20))

    findings = check(file)

    assert [f.code for f in findings] == ["short-name-long-scope"]
    assert "`r`" in findings[0].message


def test_short_name_with_short_life_is_quiet(write_file):
    file = write_file(spread("r", 3))

    assert check(file) == []


def test_descriptive_name_with_long_life_is_quiet(write_file):
    file = write_file(spread("response", 20))

    assert check(file) == []


def test_loop_variable_of_short_loop_is_quiet(write_file):
    file = write_file(
        "def f(items):\n"
        "    total = 0\n"
        "    for i in range(10):\n"
        "        total += i\n"
        "    return total\n"
    )

    assert check(file) == []


def test_comprehension_target_is_quiet(write_file):
    file = write_file("def f(xs):\n    return [x * 2 for x in xs]\n")

    assert check(file) == []


def test_underscore_is_always_quiet(write_file):
    file = write_file(spread("_", 20))

    assert check(file) == []


def test_threshold_override(write_file):
    file = write_file(spread("r", 8))

    assert check(file) == []
    assert check(file, threshold=5) != []
