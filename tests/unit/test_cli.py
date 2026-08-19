import json
import subprocess
import sys

LONG_FUNCTION = "def big():\n" + "\n".join(f"    x{i} = {i}" for i in range(101)) + "\n"


def run_nette(*args, cwd):
    return subprocess.run(
        [sys.executable, "-m", "nette", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


def test_check_clean_file_exits_zero(tmp_path):
    (tmp_path / "ok.py").write_text("def f():\n    return 1\n")

    result = run_nette("check", ".", cwd=tmp_path)

    assert result.returncode == 0


def test_check_reports_findings_and_exits_one(tmp_path):
    (tmp_path / "big.py").write_text(LONG_FUNCTION)

    result = run_nette("check", ".", "--format", "concise", cwd=tmp_path)

    assert result.returncode == 1
    assert "NET101" in result.stdout


def test_warning_findings_do_not_fail_when_errors_required(tmp_path):
    (tmp_path / "big.py").write_text(LONG_FUNCTION)

    result = run_nette(
        "check", ".", "--format", "concise", "--fail-on", "error", cwd=tmp_path
    )

    assert result.returncode == 0
    assert "NET101" in result.stdout


def test_syntax_error_fails_even_with_fail_on_error(tmp_path):
    (tmp_path / "broken.py").write_text("def broken(:\n")

    result = run_nette(
        "check", ".", "--format", "concise", "--fail-on", "error", cwd=tmp_path
    )

    assert result.returncode == 1
    assert "NET000" in result.stdout


def test_check_agent_format_emits_json(tmp_path):
    (tmp_path / "big.py").write_text(LONG_FUNCTION)

    result = run_nette("check", ".", "--format", "agent", cwd=tmp_path)

    payload = json.loads(result.stdout)
    assert payload["summary"]["total"] == 1


def test_calibrate_writes_profile(tmp_path):
    (tmp_path / "mod.py").write_text("def f(x: int) -> int:\n    return x\n")

    result = run_nette("calibrate", ".", cwd=tmp_path)

    assert result.returncode == 0
    profile = json.loads((tmp_path / ".nette" / "profile.json").read_text())
    assert profile["files_measured"] == 1
