from nette.calibration import Profile
from nette.engine import check_files
from nette.rules.structure import FileSize

SMALL_FILES_PROFILE = Profile(files_measured=40, metrics={"file_size_p90": 150.0})


def make_module(lines):
    return "\n".join(f"x{i} = {i}" for i in range(lines)) + "\n"


def check(file, profile=SMALL_FILES_PROFILE):
    return check_files([file], rules=[FileSize()], profile=profile)


def test_file_far_above_repo_norm_is_flagged(write_file):
    file = write_file(make_module(500))

    findings = check(file)

    assert [f.code for f in findings] == ["file-size"]
    assert "150" in findings[0].grounds


def test_file_near_repo_norm_is_quiet(write_file):
    assert check(write_file(make_module(160))) == []


def test_without_profile_the_rule_stays_quiet(write_file):
    assert check(write_file(make_module(500)), profile=None) == []
