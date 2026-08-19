from nette.engine import check_files
from nette.rules.structure import FileNaming


def check(file):
    return check_files([file], rules=[FileNaming()])


def test_snake_case_file_is_quiet(write_file):
    assert check(write_file("x = 1\n", name="user_repository.py")) == []


def test_camel_case_file_is_flagged(write_file):
    findings = check(write_file("x = 1\n", name="UserRepository.py"))

    assert [f.code for f in findings] == ["file-naming"]
    assert "UserRepository.py" in findings[0].message


def test_dashes_are_flagged(write_file):
    assert [f.code for f in check(write_file("x = 1\n", name="user-repo.py"))] == ["file-naming"]


def test_dunder_files_are_quiet(write_file):
    assert check(write_file("", name="__init__.py")) == []
