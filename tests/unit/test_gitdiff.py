import subprocess

import pytest

from nette.gitdiff import changed_files


@pytest.fixture
def repo(tmp_path):
    def git(*args):
        subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, capture_output=True
        )

    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (tmp_path / "old.py").write_text("def kept():\n    return 1\n")
    (tmp_path / "notes.txt").write_text("hello\n")
    git("add", ".")
    git("commit", "-q", "-m", "base")

    return tmp_path


def test_changed_files_lists_modified_and_new_python_files(repo):
    (repo / "old.py").write_text("def kept():\n    return 2\n")
    (repo / "new.py").write_text("def fresh():\n    return 3\n")
    (repo / "notes.txt").write_text("changed but not python\n")

    files = changed_files(repo, ref="HEAD")

    assert [f.name for f in files] == ["new.py", "old.py"]


def test_clean_tree_yields_nothing(repo):
    assert changed_files(repo, ref="HEAD") == []


def test_deleted_files_are_not_listed(repo):
    (repo / "old.py").unlink()

    assert changed_files(repo, ref="HEAD") == []
