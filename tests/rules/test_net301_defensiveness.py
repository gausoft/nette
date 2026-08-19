from nette.calibration import Profile
from nette.engine import check_files
from nette.rules.defensiveness import Defensiveness


CALM_PROFILE = Profile(files_measured=50, metrics={"guarded_function_rate": 0.05})
GUARDED_PROFILE = Profile(files_measured=50, metrics={"guarded_function_rate": 0.6})

DEFENSIVE_FILE = (
    "def a(d):\n"
    "    try:\n"
    "        return d['x']\n"
    "    except KeyError:\n"
    "        return None\n"
    "\n"
    "def b(d):\n"
    "    try:\n"
    "        return d['y']\n"
    "    except KeyError:\n"
    "        return None\n"
    "\n"
    "def c(d):\n"
    "    try:\n"
    "        return d['z']\n"
    "    except KeyError:\n"
    "        return None\n"
)


def check(file, profile):
    return check_files([file], rules=[Defensiveness()], profile=profile)


def test_defensive_file_in_calm_repo_is_flagged(write_file):
    file = write_file(DEFENSIVE_FILE)

    findings = check(file, CALM_PROFILE)

    assert [f.code for f in findings] == ["NET301"]
    assert "5%" in findings[0].grounds


def test_same_file_in_guarded_repo_is_quiet(write_file):
    file = write_file(DEFENSIVE_FILE)

    assert check(file, GUARDED_PROFILE) == []


def test_without_profile_the_rule_stays_quiet(write_file):
    file = write_file(DEFENSIVE_FILE)

    assert check(file, None) == []


def test_plain_file_is_always_quiet(write_file):
    file = write_file("def f(d):\n    return d['x']\n")

    assert check(file, CALM_PROFILE) == []
