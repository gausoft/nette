from nette.engine import check_files
from nette.rules.duplication import DuplicatedSibling


def sender(name: str, target: str, steps: int = 22) -> str:
    body = "\n".join(f"    part_{i} = {target}[{i}] + '{name}'" for i in range(steps))
    return f"def {name}(payload):\n{body}\n    return {target}\n"


def loops(name: str, steps: int = 22) -> str:
    body = "\n".join(
        f"    for item_{i} in payload:\n        if item_{i}:\n            yield item_{i}"
        for i in range(steps)
    )
    return f"def {name}(payload):\n{body}\n"


def check(file, thresholds=None):
    return check_files([file], rules=[DuplicatedSibling()], thresholds=thresholds)


def test_near_identical_siblings_are_flagged_once_and_name_the_twin(write_file):
    file = write_file(sender("send_password_reset", "ticket") + "\n" + sender("send_email_change", "order"))

    findings = check(file)

    assert [f.code for f in findings] == ["duplicated-sibling"]
    assert "`send_email_change`" in findings[0].message
    assert "`send_password_reset`" in findings[0].message
    assert findings[0].line == 26


def test_three_clones_report_two_findings_not_three_pairs(write_file):
    file = write_file(
        sender("a", "x") + "\n" + sender("b", "y") + "\n" + sender("c", "z")
    )

    assert len(check(file)) == 2


def test_short_twins_stay_quiet(write_file):
    file = write_file(sender("a", "x", steps=4) + "\n" + sender("b", "y", steps=4))

    assert check(file) == []


def test_differently_shaped_functions_stay_quiet(write_file):
    file = write_file(sender("a", "x") + "\n" + loops("b"))

    assert check(file) == []


def test_methods_of_the_same_class_are_compared(write_file):
    body = "\n".join(f"        part_{i} = payload[{i}]" for i in range(22))
    file = write_file(
        "class Sender:\n"
        f"    def send_sms(self, payload):\n{body}\n        return payload\n"
        f"    def send_mail(self, payload):\n{body}\n        return payload\n"
    )

    assert [f.code for f in check(file)] == ["duplicated-sibling"]


def test_a_method_and_a_module_function_are_not_siblings(write_file):
    method_body = "\n".join(f"        part_{i} = payload[{i}]" for i in range(22))
    file = write_file(
        f"class Sender:\n    def send(self, payload):\n{method_body}\n"
        + "\n"
        + sender("send_again", "payload")
    )

    assert check(file) == []


def test_the_closest_earlier_twin_is_named_on_a_tie(write_file):
    file = write_file(
        sender("first", "x") + "\n" + sender("second", "y") + "\n" + sender("third", "z")
    )

    findings = check(file)

    assert [f.message.split("`")[3] for f in findings] == ["first", "first"]


def test_similarity_threshold_is_configurable(write_file):
    file = write_file(sender("a", "x") + "\n" + sender("b", "y"))

    assert check(file, {"duplication_similarity": 100}) != []
    assert check(file, {"duplication_min_lines": 40}) == []
