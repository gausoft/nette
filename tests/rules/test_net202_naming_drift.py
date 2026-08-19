from nette.calibration import Profile
from nette.engine import check_files
from nette.rules.naming import NamingDrift

SNAKE_PROFILE = Profile(
    files_measured=40, metrics={"camel_case_function_rate": 0.01}
)
CAMEL_PROFILE = Profile(
    files_measured=40, metrics={"camel_case_function_rate": 0.8}
)

CAMEL_FUNCTIONS = (
    "def fetchUser():\n    return 1\n\n"
    "def parseOrder():\n    return 2\n\n"
    "def buildInvoice():\n    return 3\n"
)


def check(file, profile):
    return check_files([file], rules=[NamingDrift()], profile=profile)


def test_camel_functions_in_snake_repo_are_flagged(write_file):
    file = write_file(CAMEL_FUNCTIONS)

    findings = check(file, SNAKE_PROFILE)

    assert [f.code for f in findings] == ["NET202"]
    assert "fetchUser" in findings[0].message


def test_same_file_in_camel_repo_is_quiet(write_file):
    assert check(write_file(CAMEL_FUNCTIONS), CAMEL_PROFILE) == []


def test_snake_functions_are_always_quiet(write_file):
    file = write_file("def fetch_user():\n    return 1\n")

    assert check(file, SNAKE_PROFILE) == []


def test_without_profile_the_rule_stays_quiet(write_file):
    assert check(write_file(CAMEL_FUNCTIONS), None) == []
