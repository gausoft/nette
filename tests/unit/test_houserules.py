import pytest

from nette.engine import check_files
from nette.houserules import load_house_rules


FORBID_CALL = """
[[rule]]
id = "no-raw-getattr"
kind = "forbid-call"
call = "getattr"
message = "getattr on an internal object hides a typo until runtime"
why = "internal objects have known attributes"
fix = "access the attribute directly"
"""

NAME_MUST_MATCH = """
[[rule]]
id = "descriptive-test-names"
kind = "name-must-match"
target = "function"
pattern = "^test_[a-z_]+_when_[a-z_]+$"
message = "a test name should say the scenario"
why = "the name is what a failing run shows first"
fix = "rename to test_<action>_when_<condition>"
"""

IMPORT_BOUNDARY = """
[[rule]]
id = "services-do-not-import-api"
kind = "import-boundary"
from = "*services*"
forbid = "src.api"
message = "the service layer must not import the presentation layer"
why = "it makes the service untestable without the web framework"
fix = "pass what the service needs as an argument"
"""


def project(tmp_path, declaration):
    (tmp_path / "pyproject.toml").write_text("[tool.nette]\n")
    (tmp_path / ".nette").mkdir(exist_ok=True)
    (tmp_path / ".nette" / "rules.toml").write_text(declaration)

    return tmp_path


def judge(tmp_path, declaration, source, name="mod.py"):
    root = project(tmp_path, declaration)
    file = root / name
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(source)

    return check_files([file], rules=load_house_rules(root))


def test_no_rules_file_means_no_rules(tmp_path):
    assert load_house_rules(tmp_path) == []


def test_a_forbidden_call_is_reported(tmp_path):
    findings = judge(tmp_path, FORBID_CALL, "def f(row):\n    return getattr(row, 'x', None)\n")

    assert [f.code for f in findings] == ["no-raw-getattr"]
    assert "internal objects have known attributes" in findings[0].grounds
    assert findings[0].help == "access the attribute directly"


def test_another_call_is_left_alone(tmp_path):
    assert judge(tmp_path, FORBID_CALL, "def f(row):\n    return setattr(row, 'x', 1)\n") == []


def test_a_bare_name_matches_the_tail_of_a_dotted_call(tmp_path):
    findings = judge(tmp_path, FORBID_CALL, "def f(row):\n    return builtins.getattr(row, 'x')\n")

    assert [f.code for f in findings] == ["no-raw-getattr"]


def test_a_name_that_breaks_the_convention_is_reported(tmp_path):
    findings = judge(tmp_path, NAME_MUST_MATCH, "def test_thing():\n    assert True\n")

    assert [f.code for f in findings] == ["descriptive-test-names"]
    assert "test_thing" in findings[0].grounds


def test_a_name_that_follows_the_convention_is_quiet(tmp_path):
    source = "def test_sync_when_the_token_expired():\n    assert True\n"

    assert judge(tmp_path, NAME_MUST_MATCH, source) == []


def test_a_forbidden_import_is_reported(tmp_path):
    findings = judge(
        tmp_path, IMPORT_BOUNDARY, "from src.api.views import render\n", "services/billing.py"
    )

    assert [f.code for f in findings] == ["services-do-not-import-api"]


def test_a_file_outside_the_glob_is_left_alone(tmp_path):
    findings = judge(
        tmp_path, IMPORT_BOUNDARY, "from src.api.views import render\n", "web/handler.py"
    )

    assert findings == []


def test_a_sibling_module_is_not_under_the_forbidden_one(tmp_path):
    findings = judge(
        tmp_path, IMPORT_BOUNDARY, "import src.apiary\n", "services/billing.py"
    )

    assert findings == []


def test_a_missing_reason_is_rejected_by_name(tmp_path):
    broken = FORBID_CALL.replace('why = "internal objects have known attributes"\n', "")
    root = project(tmp_path, broken)

    with pytest.raises(ValueError, match="missing or not text: why"):
        load_house_rules(root)


def test_an_unknown_kind_is_rejected(tmp_path):
    broken = FORBID_CALL.replace('kind = "forbid-call"', 'kind = "forbid-vibes"')
    root = project(tmp_path, broken)

    with pytest.raises(ValueError, match="unknown kind"):
        load_house_rules(root)


def test_a_name_that_collides_with_a_built_in_rule_is_rejected(tmp_path):
    broken = FORBID_CALL.replace('id = "no-raw-getattr"', 'id = "function-length"')
    root = project(tmp_path, broken)

    with pytest.raises(ValueError, match="built-in"):
        load_house_rules(root)


def test_the_same_name_declared_twice_is_rejected(tmp_path):
    root = project(tmp_path, FORBID_CALL + FORBID_CALL)

    with pytest.raises(ValueError, match="twice"):
        load_house_rules(root)


def test_a_broken_file_names_itself(tmp_path):
    root = project(tmp_path, "this is not toml [[[")

    with pytest.raises(ValueError, match="rules.toml"):
        load_house_rules(root)


def test_a_bad_pattern_is_rejected(tmp_path):
    broken = NAME_MUST_MATCH.replace('pattern = "^test_[a-z_]+_when_[a-z_]+$"', 'pattern = "[["')
    root = project(tmp_path, broken)

    with pytest.raises(ValueError, match="bad pattern"):
        load_house_rules(root)


def test_a_rule_that_is_not_a_table_is_rejected(tmp_path):
    root = project(tmp_path, "rule = [42]\n")

    with pytest.raises(ValueError, match="must be a \\[\\[rule\\]\\] table"):
        load_house_rules(root)


def test_a_field_of_the_wrong_type_is_rejected(tmp_path):
    broken = NAME_MUST_MATCH.replace('pattern = "^test_[a-z_]+_when_[a-z_]+$"', "pattern = []")
    root = project(tmp_path, broken)

    with pytest.raises(ValueError, match="not text"):
        load_house_rules(root)


def test_an_id_that_is_not_text_is_rejected(tmp_path):
    broken = FORBID_CALL.replace('id = "no-raw-getattr"', "id = 42")
    root = project(tmp_path, broken)

    with pytest.raises(ValueError, match="not text"):
        load_house_rules(root)


def test_a_files_glob_of_the_wrong_type_is_rejected(tmp_path):
    broken = FORBID_CALL + "files = 7\n"
    root = project(tmp_path, broken)

    with pytest.raises(ValueError, match="files must be text"):
        load_house_rules(root)


def test_an_unreadable_file_names_itself(tmp_path):
    root = project(tmp_path, FORBID_CALL)
    (root / ".nette" / "rules.toml").chmod(0o000)

    try:
        with pytest.raises(ValueError, match="cannot be read"):
            load_house_rules(root)
    finally:
        (root / ".nette" / "rules.toml").chmod(0o644)


def test_importing_the_package_then_the_module_is_caught(tmp_path):
    findings = judge(
        tmp_path, IMPORT_BOUNDARY, "from src import api\n", "services/billing.py"
    )

    assert [f.code for f in findings] == ["services-do-not-import-api"]
