import subprocess

import pytest

from nette.gitdiff import changed_files


@pytest.fixture
def git(tmp_path):
    def run(*args):
        subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, capture_output=True
        )

    return run


@pytest.fixture
def repo(tmp_path, git):
    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (tmp_path / "old.py").write_text("def kept():\n    return 1\n")
    (tmp_path / "theirs.py").write_text("def theirs():\n    return 1\n")
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


def test_diff_against_a_branch_ignores_what_moved_on_that_branch(repo, git):
    git("checkout", "-q", "-b", "feature")
    (repo / "mine.py").write_text("def mine():\n    return 1\n")
    git("add", ".")
    git("commit", "-q", "-m", "mine")

    git("checkout", "-q", "main")
    (repo / "theirs.py").write_text("def theirs():\n    return 2\n")
    git("add", ".")
    git("commit", "-q", "-m", "theirs")
    git("checkout", "-q", "feature")

    files = changed_files(repo, ref="main")

    assert [f.name for f in files] == ["mine.py"]


def test_diff_against_a_branch_still_sees_uncommitted_work(repo, git):
    git("checkout", "-q", "-b", "feature")
    (repo / "old.py").write_text("def kept():\n    return 9\n")

    files = changed_files(repo, ref="main")

    assert [f.name for f in files] == ["old.py"]


def test_unrelated_history_falls_back_to_the_ref_tip(repo, git, capsys):
    git("checkout", "-q", "--orphan", "other")
    git("rm", "-q", "-rf", ".")
    (repo / "only.py").write_text("def only():\n    return 1\n")
    git("add", ".")
    git("commit", "-q", "-m", "orphan")

    files = changed_files(repo, ref="main")

    assert [f.name for f in files] == ["only.py"]
    assert "no merge base with main" in capsys.readouterr().err


def test_paths_are_resolved_from_the_repo_root_not_the_calling_directory(repo):
    package = repo / "pkg"
    package.mkdir()
    (repo / "old.py").write_text("def kept():\n    return 4\n")

    files = changed_files(package, ref="HEAD")

    assert [f.name for f in files] == ["old.py"]
    assert all(f.exists() for f in files)
