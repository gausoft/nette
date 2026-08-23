import json
import subprocess
import sys

LONG_FUNCTION = "def big():\n" + "\n".join(f"    x{i} = {i}" for i in range(101)) + "\n"
GUARDED_FILE = "".join(
    f"def f{i}(d):\n    try:\n        return d['x']\n    except KeyError:\n        return None\n"
    for i in range(4)
)
CALM_PROFILE = json.dumps(
    {"version": 1, "files_measured": 50, "metrics": {"guarded_function_rate": 0.01}}
)


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
    assert "function-length" in result.stdout


def test_warning_findings_do_not_fail_when_errors_required(tmp_path):
    (tmp_path / "big.py").write_text(LONG_FUNCTION)

    result = run_nette(
        "check", ".", "--format", "concise", "--fail-on", "error", cwd=tmp_path
    )

    assert result.returncode == 0
    assert "function-length" in result.stdout


def test_syntax_error_fails_even_with_fail_on_error(tmp_path):
    (tmp_path / "broken.py").write_text("def broken(:\n")

    result = run_nette(
        "check", ".", "--format", "concise", "--fail-on", "error", cwd=tmp_path
    )

    assert result.returncode == 1
    assert "parse-error" in result.stdout


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
        "def f():  # nette: allow(function-length) generated table\n    pass\n"
    )

    result = run_nette("allows", ".", cwd=tmp_path)

    assert result.returncode == 0
    assert "function-length" in result.stdout
    assert "generated table" in result.stdout


def test_explain_prints_rule_doc(tmp_path):
    result = run_nette("explain", "function-length", cwd=tmp_path)

    assert result.returncode == 0
    assert "function-length" in result.stdout
    assert len(result.stdout.splitlines()) > 3


def test_explain_accepts_rule_name(tmp_path):
    result = run_nette("explain", "over-guarded", cwd=tmp_path)

    assert result.returncode == 0
    assert "over-guarded" in result.stdout


def test_explain_unknown_rule_fails(tmp_path):
    result = run_nette("explain", "no-such-rule", cwd=tmp_path)

    assert result.returncode == 2


def test_check_without_paths_judges_current_tree(tmp_path):
    (tmp_path / "big.py").write_text(LONG_FUNCTION)

    result = run_nette("check", "--format", "concise", cwd=tmp_path)

    assert result.returncode == 1
    assert "function-length" in result.stdout


def test_check_from_a_subdirectory_reads_the_root_config(tmp_path):
    (tmp_path / "nette.toml").write_text('ignore = ["function-length"]\n')
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (package / "big.py").write_text(LONG_FUNCTION)

    result = run_nette("check", ".", "--format", "concise", cwd=package)

    assert result.stdout == ""
    assert result.returncode == 0


def test_check_of_an_outside_path_uses_that_project_profile(tmp_path):
    project = tmp_path / "project"
    (project / ".nette").mkdir(parents=True)
    (project / ".nette" / "profile.json").write_text(CALM_PROFILE)
    (project / "mod.py").write_text(GUARDED_FILE)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()

    result = run_nette(
        "check", str(project / "mod.py"), "--format", "concise", cwd=elsewhere
    )

    assert "over-guarded" in result.stdout


def test_profile_flag_overrides_the_discovered_profile(tmp_path):
    (tmp_path / "mod.py").write_text(GUARDED_FILE)
    calm = tmp_path / "calm.json"
    calm.write_text(CALM_PROFILE)

    result = run_nette(
        "check", ".", "--profile", str(calm), "--format", "concise", cwd=tmp_path
    )

    assert "over-guarded" in result.stdout


def test_calibrate_from_a_subdirectory_writes_at_the_root(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    package = tmp_path / "src"
    package.mkdir()
    (package / "mod.py").write_text("def f(x: int) -> int:\n    return x\n")

    result = run_nette("calibrate", ".", cwd=package)

    assert result.returncode == 0
    assert (tmp_path / ".nette" / "profile.json").exists()
    assert not (package / ".nette").exists()


def test_paths_from_two_projects_are_refused(tmp_path):
    for name in ("one", "two"):
        project = tmp_path / name
        project.mkdir()
        (project / "nette.toml").write_text("ignore = []\n")
        (project / "mod.py").write_text("def f():\n    return 1\n")

    result = run_nette(
        "check", str(tmp_path / "one"), str(tmp_path / "two"), cwd=tmp_path
    )

    assert result.returncode == 2
    assert "different projects" in result.stderr


def test_a_path_that_does_not_exist_is_refused(tmp_path):
    result = run_nette("check", "nope.py", cwd=tmp_path)

    assert result.returncode == 2
    assert "no such path" in result.stderr


def test_a_profile_flag_pointing_nowhere_is_refused(tmp_path):
    (tmp_path / "mod.py").write_text("def f():\n    return 1\n")

    result = run_nette("check", ".", "--profile", "nope.json", cwd=tmp_path)

    assert result.returncode == 2
    assert "no such profile file" in result.stderr


def test_version_flag_reports_the_package_version(tmp_path):
    from nette import __version__

    result = run_nette("--version", cwd=tmp_path)

    assert result.returncode == 0
    assert __version__ in result.stdout


def test_timings_reports_per_rule_cost(tmp_path):
    (tmp_path / "mod.py").write_text("def f():\n    return 1\n")

    result = run_nette("check", ".", "--timings", cwd=tmp_path)

    assert "function-length" in result.stderr
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


def test_bad_config_is_a_diagnostic_not_a_traceback(tmp_path):
    (tmp_path / "mod.py").write_text("def f():\n    return 1\n")
    (tmp_path / "nette.toml").write_text('ignore = ["argument-conut"]\n')

    result = run_nette("check", ".", cwd=tmp_path)

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert "argument-count" in result.stderr


def test_unreadable_config_is_a_diagnostic_not_a_traceback(tmp_path):
    (tmp_path / "mod.py").write_text("def f():\n    return 1\n")
    (tmp_path / "nette.toml").write_text("ignore = [\n")

    result = run_nette("check", ".", cwd=tmp_path)

    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert result.stderr.startswith("error:")


def test_ignoring_an_engine_rule_actually_silences_it(tmp_path):
    (tmp_path / "broken.py").write_text("def broken(:\n")

    loud = run_nette("check", ".", "--format", "concise", cwd=tmp_path)
    assert "parse-error" in loud.stdout

    (tmp_path / "nette.toml").write_text('ignore = ["parse-error"]\n')
    quiet = run_nette("check", ".", "--format", "concise", cwd=tmp_path)

    assert quiet.stdout == ""
    assert quiet.returncode == 0
