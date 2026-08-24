from nette.engine import check_files
from nette.rules.structure import MixedModule

DATA_TYPES = (
    "@dataclass\n"
    "class Account:\n"
    "    reference: str\n"
    "\n"
    "class Address(BaseModel):\n"
    "    name: str\n"
    "\n"
)
BEHAVIOUR = "def save(account):\n    return account.reference\n"


def check(file, thresholds=None):
    return check_files([file], rules=[MixedModule()], thresholds=thresholds)


def test_data_types_next_to_behaviour_are_flagged(write_file):
    file = write_file(DATA_TYPES + BEHAVIOUR)

    findings = check(file)

    assert [f.code for f in findings] == ["mixed-module"]
    assert "Account" in findings[0].grounds
    assert "Address" in findings[0].grounds
    assert "schemas.py" in findings[0].help


def test_a_module_of_pure_data_types_is_quiet(write_file):
    file = write_file(DATA_TYPES)

    assert check(file) == []


def test_a_module_of_pure_behaviour_is_quiet(write_file):
    file = write_file(BEHAVIOUR)

    assert check(file) == []


def test_one_data_type_next_to_its_use_case_is_quiet(write_file):
    file = write_file("@dataclass\nclass Command:\n    id: str\n\n" + BEHAVIOUR)

    assert check(file) == []


def test_a_destination_module_is_exempt(write_file):
    file = write_file(DATA_TYPES + BEHAVIOUR, name="schemas.py")

    assert check(file) == []


def test_a_class_with_methods_is_behaviour_not_data(write_file):
    file = write_file(
        DATA_TYPES + "class Store:\n    def save(self, account):\n        return account\n"
    )

    findings = check(file)

    assert [f.code for f in findings] == ["mixed-module"]


def test_an_enum_counts_as_a_data_type(write_file):
    file = write_file(
        "class Status(Enum):\n    OPEN = 1\n\n"
        "class Kind(str, Enum):\n    A = 'a'\n\n" + BEHAVIOUR
    )

    assert [f.code for f in check(file)] == ["mixed-module"]


def test_a_protocol_of_stubs_is_not_behaviour(write_file):
    file = write_file(
        DATA_TYPES
        + "class Sender(Protocol):\n"
        + "    def send(self, account) -> None:\n        ...\n"
    )

    assert check(file) == []


def test_a_class_body_that_runs_code_is_not_a_data_type(write_file):
    file = write_file(
        "class Account:\n    reference: str\n\n"
        "class Wired:\n    register('wired')\n    name: str\n\n" + BEHAVIOUR
    )

    assert check(file) == []


def test_a_module_inside_a_destination_package_is_exempt(tmp_path):
    package = tmp_path / "schemas"
    package.mkdir()
    file = package / "accounts.py"
    file.write_text(DATA_TYPES + BEHAVIOUR)

    assert check(file) == []


def test_a_private_data_type_is_a_local_detail_not_a_misplaced_type(write_file):
    file = write_file(
        DATA_TYPES + "@dataclass\nclass _Tally:\n    hits: int = 0\n\n" + BEHAVIOUR
    )

    findings = check(file, {"data_types_per_module": 3})

    assert findings == []


def test_the_threshold_is_configurable(write_file):
    file = write_file(DATA_TYPES + BEHAVIOUR)

    assert check(file, {"data_types_per_module": 3}) == []


def test_a_suppression_anywhere_in_the_file_silences_it(write_file):
    file = write_file(
        "# nette: allow(mixed-module) the command belongs next to its handler\n"
        + DATA_TYPES
        + BEHAVIOUR
    )

    assert check(file) == []
