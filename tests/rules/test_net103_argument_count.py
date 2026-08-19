from nette.engine import check_files
from nette.rules.shape import ArgumentCount


def check(file, threshold=None):
    thresholds = {"argument_count": threshold} if threshold else {}
    return check_files([file], rules=[ArgumentCount()], thresholds=thresholds)


def test_few_arguments_is_quiet(write_file):
    file = write_file("def ok(a, b, c):\n    return a\n")

    assert check(file) == []


def test_too_many_arguments_is_flagged(write_file):
    file = write_file("def crowded(a, b, c, d, e, f, g):\n    return a\n")

    findings = check(file)

    assert [f.code for f in findings] == ["NET103"]
    assert "crowded" in findings[0].message
    assert "7" in findings[0].grounds


def test_self_and_cls_do_not_count(write_file):
    file = write_file(
        "class C:\n"
        "    def method(self, a, b, c, d, e, f):\n"
        "        return a\n"
        "    @classmethod\n"
        "    def maker(cls, a, b, c, d, e, f):\n"
        "        return a\n"
    )

    assert check(file) == []


def test_default_arguments_do_not_count(write_file):
    file = write_file("def f(a, b, c=1, d=2, e=3, f=4, g=5):\n    return a\n")

    assert check(file) == []


def test_keyword_only_arguments_count(write_file):
    file = write_file("def f(a, b, c, *, d, e, f, g):\n    return a\n")

    assert [f.code for f in check(file)] == ["NET103"]


def test_threshold_override(write_file):
    file = write_file("def f(a, b, c):\n    return a\n")

    assert check(file, threshold=2) != []
