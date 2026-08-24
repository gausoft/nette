import subprocess

import pytest

from nette.gitdiff import changed_files, changed_lines


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


def test_changed_lines_reports_the_touched_ranges(repo):
    (repo / "old.py").write_text(
        "def kept():\n    return 1\n\n\ndef added():\n    return 2\n"
    )

    ranges = changed_lines(repo, ref="HEAD")

    assert ranges[repo / "old.py"] == [(3, 6)]


def test_changed_lines_covers_a_new_file_entirely(repo):
    (repo / "new.py").write_text("def fresh():\n    return 3\n")

    ranges = changed_lines(repo, ref="HEAD")

    assert ranges[repo / "new.py"] == [(1, 2)]


def test_changed_lines_reports_several_hunks(repo):
    body = "".join(f"    step_{index} = {index}\n" for index in range(20))
    (repo / "old.py").write_text("def kept():\n" + body + "    return 1\n")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "grow"], cwd=repo, check=True, capture_output=True
    )

    lines = (repo / "old.py").read_text().splitlines()
    lines[1] = "    step_0 = 99"
    lines[18] = "    step_17 = 99"
    (repo / "old.py").write_text("\n".join(lines) + "\n")

    ranges = changed_lines(repo, ref="HEAD")

    assert ranges[repo / "old.py"] == [(2, 2), (19, 19)]


def test_changed_lines_on_a_clean_tree_is_empty(repo):
    assert changed_lines(repo, ref="HEAD") == {}


def test_deleted_lines_alone_list_the_file_with_no_range(repo):
    (repo / "old.py").write_text("def kept():\n")

    assert changed_lines(repo, ref="HEAD") == {repo / "old.py": []}


def test_changed_lines_handles_a_non_ascii_path(repo, git):
    (repo / "accentué.py").write_text("def a():\n    return 1\n")
    git("add", ".")
    git("commit", "-q", "-m", "accents")
    (repo / "accentué.py").write_text("def a():\n    return 2\n")

    ranges = changed_lines(repo, ref="HEAD")

    assert ranges[repo / "accentué.py"] == [(2, 2)]


def test_changed_lines_handles_a_path_with_a_space(repo, git):
    (repo / "with space.py").write_text("def a():\n    return 1\n")
    git("add", ".")
    git("commit", "-q", "-m", "space")
    (repo / "with space.py").write_text("def a():\n    return 2\n")

    ranges = changed_lines(repo, ref="HEAD")

    assert ranges[repo / "with space.py"] == [(2, 2)]


def test_changed_lines_survives_a_repo_configured_without_diff_prefixes(repo, git):
    git("config", "diff.noprefix", "true")
    (repo / "old.py").write_text("def kept():\n    return 2\n")

    ranges = changed_lines(repo, ref="HEAD")

    assert ranges[repo / "old.py"] == [(2, 2)]


def test_a_file_emptied_by_deletions_is_still_listed_with_no_range(repo):
    (repo / "old.py").write_text("")

    assert changed_lines(repo, ref="HEAD") == {repo / "old.py": []}
