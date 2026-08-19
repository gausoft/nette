import json

from nette.calibration import Profile, build_profile, load_profile, ratchet, save_profile


DEFENSIVE_HEAVY = (
    "def guarded(data):\n"
    "    try:\n"
    "        value = data['k']\n"
    "    except KeyError:\n"
    "        value = None\n"
    "    try:\n"
    "        other = int(value)\n"
    "    except (TypeError, ValueError):\n"
    "        other = 0\n"
    "    return other\n"
)

PLAIN = (
    "def direct(data):\n"
    "    return int(data['k'])\n"
)


def test_build_profile_measures_try_density(tmp_path):
    (tmp_path / "guarded.py").write_text(DEFENSIVE_HEAVY)
    (tmp_path / "plain.py").write_text(PLAIN)

    profile = build_profile(tmp_path)

    assert profile.files_measured == 2
    assert profile.metrics["try_per_kloc"] > 0


def test_build_profile_measures_annotation_rate(tmp_path):
    (tmp_path / "typed.py").write_text("def f(x: int) -> int:\n    return x\n")
    (tmp_path / "untyped.py").write_text("def g(x):\n    return x\n")

    profile = build_profile(tmp_path)

    assert profile.metrics["annotated_function_rate"] == 0.5


def test_build_profile_skips_unparseable_files(tmp_path):
    (tmp_path / "ok.py").write_text(PLAIN)
    (tmp_path / "broken.py").write_text("def broken(:\n")

    profile = build_profile(tmp_path)

    assert profile.files_measured == 1


def test_profile_round_trips_through_json(tmp_path):
    (tmp_path / "mod.py").write_text(DEFENSIVE_HEAVY)
    profile = build_profile(tmp_path)
    destination = tmp_path / ".nette" / "profile.json"

    save_profile(profile, destination)
    loaded = load_profile(destination)

    assert loaded == profile
    assert json.loads(destination.read_text())["version"] == 1


def test_load_missing_profile_returns_none(tmp_path):
    assert load_profile(tmp_path / "absent.json") is None


def test_empty_repo_yields_empty_profile(tmp_path):
    profile = build_profile(tmp_path)

    assert profile.files_measured == 0
    assert profile.metrics == {}


def test_ratchet_keeps_the_stricter_side_of_each_metric():
    previous = Profile(
        files_measured=10,
        metrics={"guarded_function_rate": 0.02, "annotated_function_rate": 1.0},
    )
    degraded = Profile(
        files_measured=12,
        metrics={"guarded_function_rate": 0.40, "annotated_function_rate": 0.30},
    )

    kept = ratchet(previous, degraded)

    assert kept.metrics == {"guarded_function_rate": 0.02, "annotated_function_rate": 1.0}
    assert kept.files_measured == 12


def test_ratchet_adopts_an_improved_metric():
    previous = Profile(files_measured=1, metrics={"file_size_p90": 300.0})
    improved = Profile(files_measured=1, metrics={"file_size_p90": 120.0})

    assert ratchet(previous, improved).metrics == {"file_size_p90": 120.0}


def test_ratchet_keeps_a_metric_the_new_measure_could_not_see():
    previous = Profile(files_measured=1, metrics={"try_per_kloc": 1.0})
    current = Profile(files_measured=1, metrics={"file_size_p90": 50.0})

    kept = ratchet(previous, current).metrics

    assert kept == {"try_per_kloc": 1.0, "file_size_p90": 50.0}
