from nette.engine import check_files
from nette.rules.shape import BranchDensity


def dispatcher(name: str, branches: int) -> str:
    chain = "\n".join(
        f"    {'if' if i == 0 else 'elif'} status == {i}:\n        return '{i}'"
        for i in range(branches)
    )
    return f"def {name}(status):\n{chain}\n    return None\n"


def check(file, thresholds=None):
    return check_files([file], rules=[BranchDensity()], thresholds=thresholds)


def test_a_flat_chain_over_the_limit_is_flagged(write_file):
    file = write_file(dispatcher("route", 13))

    findings = check(file)

    assert [f.code for f in findings] == ["branch-density"]
    assert "13" in findings[0].grounds
    assert "lookup table" in findings[0].help


def test_the_same_branches_split_in_two_functions_stay_quiet(write_file):
    file = write_file(dispatcher("first", 8) + "\n" + dispatcher("second", 8))

    assert check(file) == []


def test_a_long_function_without_branches_stays_quiet(write_file):
    body = "\n".join(f"    step_{i} = {i}" for i in range(200))
    file = write_file(f"def long(x):\n{body}\n    return x\n")

    assert check(file) == []


def test_branches_of_a_nested_function_belong_to_it(write_file):
    inner = "\n".join(
        f"        {'if' if i == 0 else 'elif'} x == {i}:\n            return {i}"
        for i in range(13)
    )
    file = write_file(f"def outer(x):\n    def inner(x):\n{inner}\n    return inner\n")

    findings = check(file)

    assert [f.message.split("`")[1] for f in findings] == ["inner"]


def test_match_cases_count_as_branches(write_file):
    cases = "\n".join(f"        case {i}:\n            return '{i}'" for i in range(13))
    file = write_file(f"def route(status):\n    match status:\n{cases}\n")

    assert [f.code for f in check(file)] == ["branch-density"]


def test_the_limit_is_configurable(write_file):
    file = write_file(dispatcher("route", 13))

    assert check(file, {"branch_density": 20}) == []
