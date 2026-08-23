from nette.calibration import Profile
from nette.engine import check_files
from nette.rules.defensiveness import GuardDensity


CALM_PROFILE = Profile(
    files_measured=50, metrics={"try_per_kloc": 4.0, "guarded_function_rate": 0.05}
)
DEFENSIVE_PROFILE = Profile(
    files_measured=50, metrics={"try_per_kloc": 60.0, "guarded_function_rate": 0.6}
)

STACKED_FILE = (
    "def sync(rows):\n"
    "    seen = []\n"
    "    try:\n"
    "        first = rows[0]\n"
    "    except IndexError:\n"
    "        first = None\n"
    "    seen.append(first)\n"
    "\n"
    "    try:\n"
    "        second = rows[1]\n"
    "    except IndexError:\n"
    "        second = None\n"
    "    seen.append(second)\n"
    "\n"
    "    try:\n"
    "        third = rows[2]\n"
    "    except IndexError:\n"
    "        third = None\n"
    "    seen.append(third)\n"
    "\n"
    "    return seen\n"
)


def check(file, profile):
    return check_files([file], rules=[GuardDensity()], profile=profile)


def test_stacked_guards_in_one_function_are_flagged(write_file):
    file = write_file(STACKED_FILE)

    findings = check(file, CALM_PROFILE)

    assert [f.code for f in findings] == ["guard-density"]
    assert "3 try blocks" in findings[0].grounds


def test_grounds_compare_to_the_repo_rate(write_file):
    file = write_file(STACKED_FILE)

    grounds = check(file, CALM_PROFILE)[0].grounds

    assert "4.0 per 1000" in grounds


def test_stacked_guards_in_a_defensive_repo_are_quiet(write_file):
    file = write_file(STACKED_FILE)

    assert check(file, DEFENSIVE_PROFILE) == []


def test_two_guards_are_quiet(write_file):
    file = write_file(
        "def sync(rows):\n"
        "    try:\n"
        "        a = rows[0]\n"
        "    except IndexError:\n"
        "        a = None\n"
        "    try:\n"
        "        b = rows[1]\n"
        "    except IndexError:\n"
        "        b = None\n"
        "    return a, b\n"
    )

    assert check(file, CALM_PROFILE) == []


def test_file_over_guarded_across_functions_is_left_to_over_guarded(write_file):
    file = write_file(
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

    assert check(file, CALM_PROFILE) == []


def test_guards_spread_over_a_long_file_are_quiet(write_file):
    body = "".join(f"    row_{index} = index\n" for index in range(300))
    file = write_file(
        "def sync():\n"
        "    try:\n"
        "        first = load()\n"
        "    except OSError:\n"
        "        first = None\n"
        "    try:\n"
        "        second = load()\n"
        "    except OSError:\n"
        "        second = None\n"
        "    try:\n"
        "        third = load()\n"
        "    except OSError:\n"
        "        third = None\n" + body + "    return first, second, third\n"
    )

    assert check(file, CALM_PROFILE) == []


def test_without_profile_the_rule_is_silent(write_file):
    file = write_file(STACKED_FILE)

    assert check(file, None) == []
