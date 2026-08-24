from pathlib import Path

from nette.calibration import is_test_module


def project(tmp_path: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text("[tool.nette]\n")

    return tmp_path


def test_a_name_that_follows_the_convention_is_a_test(tmp_path):
    root = project(tmp_path)

    for name in ("test_thing.py", "thing_test.py", "conftest.py", "tests.py"):
        assert is_test_module(root / name)


def test_a_file_under_the_tests_directory_is_a_test(tmp_path):
    root = project(tmp_path)
    (root / "tests" / "helpers").mkdir(parents=True)

    assert is_test_module(root / "tests" / "helpers" / "factory.py")


def test_a_project_living_under_a_directory_named_tests_is_not_all_tests(tmp_path):
    outside = tmp_path / "tests" / "myproject"
    outside.mkdir(parents=True)
    root = project(outside)
    (root / "src").mkdir()

    assert not is_test_module(root / "src" / "engine.py")


def test_a_shipped_package_named_testing_is_not_a_test(tmp_path):
    root = project(tmp_path)
    (root / "lib" / "testing").mkdir(parents=True)

    assert not is_test_module(root / "lib" / "testing" / "assertions.py")


def test_a_shipped_package_named_test_is_not_a_test(tmp_path):
    root = project(tmp_path)
    (root / "django" / "test").mkdir(parents=True)

    assert not is_test_module(root / "django" / "test" / "client.py")


def test_source_files_are_not_tests(tmp_path):
    root = project(tmp_path)
    (root / "src").mkdir()

    assert not is_test_module(root / "src" / "engine.py")
