from nette.calibration import Profile
from nette.engine import check_files
from nette.rules.annotations import UnderAnnotated


TYPED_PROFILE = Profile(files_measured=50, metrics={"annotated_function_rate": 0.92})
UNTYPED_PROFILE = Profile(files_measured=50, metrics={"annotated_function_rate": 0.2})

BARE_FILE = (
    "def load(path):\n"
    "    return path\n"
    "\n"
    "def parse(raw):\n"
    "    return raw\n"
    "\n"
    "def store(row):\n"
    "    return row\n"
)

TYPED_FILE = (
    "def load(path: str) -> str:\n"
    "    return path\n"
    "\n"
    "def parse(raw: str) -> str:\n"
    "    return raw\n"
    "\n"
    "def store(row: str) -> str:\n"
    "    return row\n"
)


def check(file, profile):
    return check_files([file], rules=[UnderAnnotated()], profile=profile)


def test_bare_file_in_typed_repo_is_flagged(write_file):
    file = write_file(BARE_FILE)

    findings = check(file, TYPED_PROFILE)

    assert [f.code for f in findings] == ["under-annotated"]
    assert "92%" in findings[0].grounds


def test_finding_names_the_bare_functions(write_file):
    file = write_file(BARE_FILE)

    grounds = check(file, TYPED_PROFILE)[0].grounds

    assert "`load`" in grounds and "`parse`" in grounds and "`store`" in grounds


def test_typed_file_in_typed_repo_is_quiet(write_file):
    file = write_file(TYPED_FILE)

    assert check(file, TYPED_PROFILE) == []


def test_half_annotated_file_is_quiet(write_file):
    file = write_file(
        "def load(path: str) -> str:\n"
        "    return path\n"
        "\n"
        "def parse(raw: str) -> str:\n"
        "    return raw\n"
        "\n"
        "def store(row):\n"
        "    return row\n"
    )

    assert check(file, TYPED_PROFILE) == []


def test_bare_file_in_untyped_repo_is_quiet(write_file):
    file = write_file(BARE_FILE)

    assert check(file, UNTYPED_PROFILE) == []


def test_short_file_is_quiet(write_file):
    file = write_file("def load(path):\n    return path\n")

    assert check(file, TYPED_PROFILE) == []


def test_return_annotation_alone_counts_as_annotated(write_file):
    file = write_file(
        "def load(path) -> str:\n"
        "    return path\n"
        "\n"
        "def parse(raw) -> str:\n"
        "    return raw\n"
        "\n"
        "def store(row) -> str:\n"
        "    return row\n"
    )

    assert check(file, TYPED_PROFILE) == []


def test_without_profile_the_rule_is_silent(write_file):
    file = write_file(BARE_FILE)

    assert check(file, None) == []


def test_test_modules_are_exempt(write_file):
    for name in ("test_thing.py", "thing_test.py", "conftest.py"):
        assert check(write_file(BARE_FILE, name), TYPED_PROFILE) == []


def test_dunder_and_nested_functions_count_once(write_file):
    file = write_file(
        "class Row:\n"
        "    def __init__(self, raw):\n"
        "        self.raw = raw\n"
        "\n"
        "    def value(self):\n"
        "        def inner(x):\n"
        "            return x\n"
        "        return inner(self.raw)\n"
    )

    findings = check(file, TYPED_PROFILE)

    assert [f.code for f in findings] == ["under-annotated"]
    assert "3 of its 3" in findings[0].grounds
