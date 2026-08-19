from nette.cache import Cache
from nette.engine import check_files
from nette.rules.shape import FunctionLength

LONG_FUNCTION = "def big():\n" + "\n".join(f"    x{i} = {i}" for i in range(101)) + "\n"


def check(file, cache, thresholds=None):
    return check_files(
        [file], rules=[FunctionLength()], thresholds=thresholds, cache=cache
    )


def test_warm_run_returns_same_findings(write_file, tmp_path):
    file = write_file(LONG_FUNCTION)
    cache = Cache(tmp_path / ".nette_cache")

    cold = check(file, cache)
    warm = check(file, cache)

    assert warm == cold
    assert [f.code for f in warm] == ["NET101"]


def test_warm_run_skips_analysis(write_file, tmp_path, monkeypatch):
    file = write_file(LONG_FUNCTION)
    cache = Cache(tmp_path / ".nette_cache")
    check(file, cache)

    import nette.engine as engine_module

    def explode(*args, **kwargs):
        raise AssertionError("analysis ran despite cache hit")

    monkeypatch.setattr(engine_module, "parse_source", explode)

    warm = check(file, cache)

    assert [f.code for f in warm] == ["NET101"]


def test_editing_the_file_invalidates_its_entry(write_file, tmp_path):
    file = write_file(LONG_FUNCTION)
    cache = Cache(tmp_path / ".nette_cache")
    check(file, cache)

    file.write_text("def small():\n    return 1\n")

    assert check(file, cache) == []


def test_changing_thresholds_invalidates(write_file, tmp_path):
    file = write_file("def f():\n    a = 1\n    b = 2\n    c = 3\n")
    cache = Cache(tmp_path / ".nette_cache")

    assert check(file, cache) == []
    assert check(file, cache, thresholds={"function_length": 2}) != []


def test_cache_persists_across_instances(write_file, tmp_path):
    file = write_file(LONG_FUNCTION)
    location = tmp_path / ".nette_cache"
    check(file, Cache(location))

    warm = check(file, Cache(location))

    assert [f.code for f in warm] == ["NET101"]


def test_no_cache_still_works(write_file):
    file = write_file(LONG_FUNCTION)

    findings = check_files([file], rules=[FunctionLength()])

    assert [f.code for f in findings] == ["NET101"]
