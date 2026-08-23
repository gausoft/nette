import json
from pathlib import Path

from nette.calibration import Profile, group_by_profile, save_profile

PROFILE_PATH = Path(".nette/profile.json")


def write_profile(directory: Path, rate: float) -> Path:
    save_profile(
        Profile(files_measured=10, metrics={"guarded_function_rate": rate}),
        directory / PROFILE_PATH,
    )
    return directory / PROFILE_PATH


def test_the_nearest_profile_wins_over_the_root_one(tmp_path):
    write_profile(tmp_path, 0.10)
    boundary = tmp_path / "adapters"
    boundary.mkdir()
    write_profile(boundary, 0.80)
    outside = tmp_path / "domain"
    outside.mkdir()

    groups = group_by_profile(
        [boundary / "outbound.py", outside / "accounts.py"], tmp_path, PROFILE_PATH
    )

    rates = {
        profile.metrics["guarded_function_rate"]: [f.name for f in files]
        for profile, files in groups
    }
    assert rates == {0.80: ["outbound.py"], 0.10: ["accounts.py"]}


def test_without_any_profile_the_group_carries_none(tmp_path):
    (tmp_path / "mod.py").write_text("")

    groups = group_by_profile([tmp_path / "mod.py"], tmp_path, PROFILE_PATH)

    assert groups == [(None, [tmp_path / "mod.py"])]


def test_the_walk_stops_at_the_project_root(tmp_path):
    write_profile(tmp_path, 0.10)
    project = tmp_path / "project"
    project.mkdir()

    groups = group_by_profile([project / "mod.py"], project, PROFILE_PATH)

    assert groups == [(None, [project / "mod.py"])]


def test_files_sharing_a_profile_are_grouped_once(tmp_path):
    write_profile(tmp_path, 0.10)

    groups = group_by_profile(
        [tmp_path / "a.py", tmp_path / "b.py"], tmp_path, PROFILE_PATH
    )

    assert len(groups) == 1
    assert [f.name for f in groups[0][1]] == ["a.py", "b.py"]


def test_a_profile_outside_the_root_is_never_read(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    write_profile(outside, 0.9)
    project = tmp_path / "outside" / "project"
    project.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(project)

    groups = group_by_profile([linked / "mod.py"], linked, PROFILE_PATH)

    assert groups == [(None, [linked / "mod.py"])]


def test_a_local_profile_is_readable_where_it_was_written(tmp_path):
    path = write_profile(tmp_path / "adapters", 0.8)

    assert json.loads(path.read_text())["metrics"]["guarded_function_rate"] == 0.8
