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
GUARDED_PROFILE = json.dumps(
    {"version": 1, "files_measured": 50, "metrics": {"guarded_function_rate": 0.9}}
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


def test_init_writes_the_profile_and_ignores_the_cache(tmp_path):
    (tmp_path / "mod.py").write_text("def f(x: int) -> int:\n    return x\n")

    result = run_nette("init", cwd=tmp_path)

    assert result.returncode == 0
    assert json.loads((tmp_path / ".nette" / "profile.json").read_text())["files_measured"] == 1
    assert (tmp_path / ".nette" / ".gitignore").read_text().strip() == "cache/"
    assert "nette agent-rules" in result.stdout


def test_init_keeps_an_existing_profile(tmp_path):
    (tmp_path / "mod.py").write_text("def f(x):\n    return x\n")
    (tmp_path / ".nette").mkdir()
    (tmp_path / ".nette" / "profile.json").write_text(CALM_PROFILE)

    result = run_nette("init", cwd=tmp_path)

    assert result.returncode == 0
    assert "keeping it" in result.stdout
    assert json.loads((tmp_path / ".nette" / "profile.json").read_text())["files_measured"] == 50


def test_init_refuses_a_path_that_does_not_exist(tmp_path):
    result = run_nette("init", "nope", cwd=tmp_path)

    assert result.returncode == 2
    assert "no such path" in result.stderr
    assert not (tmp_path / ".nette").exists()


def test_init_keeps_what_the_cache_ignore_file_already_says(tmp_path):
    (tmp_path / "mod.py").write_text("def f():\n    return 1\n")
    (tmp_path / ".nette").mkdir()
    (tmp_path / ".nette" / ".gitignore").write_text("scratch/\n")

    run_nette("init", cwd=tmp_path)

    assert (tmp_path / ".nette" / ".gitignore").read_text().split() == ["scratch/", "cache/"]


def test_every_subcommand_is_dispatchable():
    from nette.cli import COMMANDS, _parse_args

    for command in COMMANDS:
        arguments = [command, "function-length"] if command == "explain" else [command]
        assert _parse_args(arguments).command in COMMANDS


def test_agent_rules_prints_a_pasteable_block(tmp_path):
    result = run_nette("agent-rules", cwd=tmp_path)

    assert result.returncode == 0
    assert result.stdout.startswith("## Readability checks with nette")
    assert "nette check --diff --format agent" in result.stdout
    assert "nette: allow(" in result.stdout


def test_a_subtree_profile_overrides_the_repo_one(tmp_path):
    (tmp_path / ".nette").mkdir()
    (tmp_path / ".nette" / "profile.json").write_text(CALM_PROFILE)
    (tmp_path / "domain.py").write_text(GUARDED_FILE)
    boundary = tmp_path / "adapters"
    (boundary / ".nette").mkdir(parents=True)
    (boundary / ".nette" / "profile.json").write_text(GUARDED_PROFILE)
    (boundary / "outbound.py").write_text(GUARDED_FILE)

    result = run_nette("check", ".", "--format", "concise", cwd=tmp_path)

    assert "domain.py" in result.stdout
    assert "outbound.py" not in result.stdout


def test_calibrate_local_writes_inside_the_subtree(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    boundary = tmp_path / "adapters"
    boundary.mkdir()
    (boundary / "outbound.py").write_text(GUARDED_FILE)

    result = run_nette("calibrate", "adapters", "--local", cwd=tmp_path)

    assert result.returncode == 0
    assert (boundary / ".nette" / "profile.json").exists()
    assert not (tmp_path / ".nette").exists()


def test_calibrate_local_refuses_a_file(tmp_path):
    (tmp_path / "mod.py").write_text("def f():\n    return 1\n")

    result = run_nette("calibrate", "mod.py", "--local", cwd=tmp_path)

    assert result.returncode == 2
    assert "needs a directory" in result.stderr


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


LEGACY_FILE = "".join(
    f"def helper_{index}(a, b, c, d, e, f, g, h):\n    return a\n\n\n" for index in range(6)
)


def commit_legacy(tmp_path):
    for args in (
        ["init", "-q", "-b", "main"],
        ["config", "user.email", "t@t"],
        ["config", "user.name", "t"],
    ):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    (tmp_path / "legacy.py").write_text(LEGACY_FILE)
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "base"], cwd=tmp_path, check=True, capture_output=True
    )

    lines = (tmp_path / "legacy.py").read_text().splitlines()
    lines[1] = "    return b"
    (tmp_path / "legacy.py").write_text("\n".join(lines) + "\n")


def test_diff_judges_the_changed_lines_not_the_whole_legacy_file(tmp_path):
    commit_legacy(tmp_path)

    result = run_nette("check", "--diff", "--format", "concise", ".", cwd=tmp_path)

    assert result.stdout.count("argument-count") == 1
    assert "helper_0" in result.stdout


def test_whole_files_restores_the_file_wide_verdict(tmp_path):
    commit_legacy(tmp_path)

    result = run_nette(
        "check", "--diff", "--whole-files", "--format", "concise", ".", cwd=tmp_path
    )

    assert result.stdout.count("argument-count") == 6


def test_a_file_scoped_finding_survives_a_change_anywhere_in_the_file(tmp_path):
    commit_legacy(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.nette]\nselect = ["structure"]\n[tool.nette.thresholds]\n'
    )
    (tmp_path / "Bad-Name.py").write_text("def f():\n    return 1\n")

    result = run_nette("check", "--diff", "--format", "concise", ".", cwd=tmp_path)

    assert "file-naming" in result.stdout


def test_calibrate_says_when_the_profile_lands_above_the_measured_tree(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.nette]\n")
    inner = tmp_path / "vendored"
    inner.mkdir()
    (inner / "mod.py").write_text("def f(a: int) -> int:\n    return a\n")

    result = run_nette("calibrate", "vendored", cwd=tmp_path)

    assert result.returncode == 0
    assert "is the project root here" in result.stderr
    assert "pyproject.toml" in result.stderr


def test_calibrate_stays_quiet_when_the_profile_sits_with_the_files(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[tool.nette]\n")
    (tmp_path / "mod.py").write_text("def f(a: int) -> int:\n    return a\n")

    result = run_nette("calibrate", ".", cwd=tmp_path)

    assert "is the project root here" not in result.stderr
