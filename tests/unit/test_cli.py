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


def test_allows_lists_markers(tmp_path):
    (tmp_path / "mod.py").write_text(
        "def f():  # nette: allow(NET101) generated table\n    pass\n"
    )

    result = run_nette("allows", ".", cwd=tmp_path)

    assert result.returncode == 0
    assert "NET101" in result.stdout
    assert "generated table" in result.stdout


def test_explain_prints_rule_doc(tmp_path):
    result = run_nette("explain", "NET101", cwd=tmp_path)

    assert result.returncode == 0
    assert "NET101" in result.stdout
    assert len(result.stdout.splitlines()) > 3


def test_explain_accepts_rule_name(tmp_path):
    result = run_nette("explain", "over-guarded", cwd=tmp_path)

    assert result.returncode == 0
    assert "over-guarded" in result.stdout


def test_explain_unknown_code_fails(tmp_path):
    result = run_nette("explain", "NET999", cwd=tmp_path)

    assert result.returncode == 2


def test_check_without_paths_judges_current_tree(tmp_path):
    (tmp_path / "big.py").write_text(LONG_FUNCTION)

    result = run_nette("check", "--format", "concise", cwd=tmp_path)

    assert result.returncode == 1
    assert "NET101" in result.stdout


def test_version_flag_reports_the_package_version(tmp_path):
    from nette import __version__

    result = run_nette("--version", cwd=tmp_path)

    assert result.returncode == 0
    assert __version__ in result.stdout


def test_timings_reports_per_rule_cost(tmp_path):
    (tmp_path / "mod.py").write_text("def f():\n    return 1\n")

    result = run_nette("check", ".", "--timings", cwd=tmp_path)

    assert "NET101" in result.stderr
    assert "ms" in result.stderr


def test_calibrate_refuses_to_relax_the_profile(tmp_path):
    (tmp_path / "mod.py").write_text("def f(x: int) -> int:\n    return x\n")
    run_nette("calibrate", ".", cwd=tmp_path)
    (tmp_path / "mod.py").write_text("def f(x):\n    return x\n")

    result = run_nette("calibrate", ".", cwd=tmp_path)

    profile = json.loads((tmp_path / ".nette" / "profile.json").read_text())
    assert profile["metrics"]["annotated_function_rate"] == 1.0
    assert "--reset to relax" in result.stdout


def test_calibrate_reset_accepts_the_looser_profile(tmp_path):
    (tmp_path / "mod.py").write_text("def f(x: int) -> int:\n    return x\n")
    run_nette("calibrate", ".", cwd=tmp_path)
    (tmp_path / "mod.py").write_text("def f(x):\n    return x\n")

    run_nette("calibrate", ".", "--reset", cwd=tmp_path)

    profile = json.loads((tmp_path / ".nette" / "profile.json").read_text())
    assert profile["metrics"]["annotated_function_rate"] == 0.0
