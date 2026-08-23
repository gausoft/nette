import subprocess
import sys
from pathlib import Path

LONG_FUNCTION = "def big():\n" + "\n".join(f"    x{i} = {i}" for i in range(101)) + "\n"


def run_nette(*args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "nette", *args], cwd=cwd, capture_output=True, text=True
    )


def git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.email=t@t.t", "-c", "user.name=t", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def repo_with_history(root: Path, commits: int) -> Path:
    git(root, "init", "-q")
    file = root / "big.py"

    for index in range(commits):
        file.write_text(LONG_FUNCTION + f"\n# revision {index}\n")
        git(root, "add", "-A")
        git(root, "commit", "-qm", f"change {index}")

    return file


def test_hotspots_rank_a_flagged_file_by_how_often_it_changed(tmp_path):
    repo_with_history(tmp_path, commits=3)

    result = run_nette("hotspots", cwd=tmp_path)

    assert result.returncode == 0
    assert "changes  findings  file" in result.stdout
    assert "big.py" in result.stdout
    assert result.stdout.splitlines()[-1].split()[0] == "3"


def test_a_clean_file_never_reaches_the_ranking(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "ok.py").write_text("def f():\n    return 1\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-qm", "clean")

    result = run_nette("hotspots", cwd=tmp_path)

    assert result.returncode == 0
    assert "no file changed" in result.stdout


def test_outside_a_git_repository_it_is_a_diagnostic(tmp_path):
    (tmp_path / "big.py").write_text(LONG_FUNCTION)

    result = run_nette("hotspots", cwd=tmp_path)

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert result.stderr.startswith("error:")
