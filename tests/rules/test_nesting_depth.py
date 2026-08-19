from nette.engine import check_files
from nette.rules.shape import NestingDepth


def check(file, threshold=None):
    thresholds = {"nesting_depth": threshold} if threshold else {}
    return check_files([file], rules=[NestingDepth()], thresholds=thresholds)


def test_flat_function_is_quiet(write_file):
    file = write_file("def ok():\n    if True:\n        return 1\n    return 0\n")

    assert check(file) == []


def test_depth_over_default_threshold_is_flagged(write_file):
    file = write_file(
        "def deep():\n"
        "    for a in range(1):\n"
        "        if a:\n"
        "            for b in range(2):\n"
        "                if b:\n"
        "                    while b:\n"
        "                        if a:\n"
        "                            pass\n"
    )

    findings = check(file)

    assert [f.code for f in findings] == ["nesting-depth"]
    assert "deep" in findings[0].message


def test_one_finding_per_function_not_per_level(write_file):
    file = write_file(
        "def deep():\n"
        "    for a in range(1):\n"
        "        if a:\n"
        "            for b in range(2):\n"
        "                if b:\n"
        "                    while b:\n"
        "                        if a:\n"
        "                            for c in range(3):\n"
        "                                pass\n"
    )

    assert len(check(file)) == 1


def test_threshold_override(write_file):
    file = write_file(
        "def f():\n"
        "    if 1:\n"
        "        if 2:\n"
        "            pass\n"
    )

    assert check(file, threshold=1) != []
    assert check(file) == []
