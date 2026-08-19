from nette.discovery import discover


def test_discover_finds_python_files_recursively(tmp_path):
    (tmp_path / "a.py").write_text("")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("")
    (tmp_path / "notes.txt").write_text("")

    files = discover([tmp_path])

    assert [f.name for f in files] == ["a.py", "b.py"]


def test_discover_accepts_single_file(tmp_path):
    file = tmp_path / "one.py"
    file.write_text("")

    assert discover([file]) == [file]


def test_discover_skips_hidden_and_cache_dirs(tmp_path):
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "x.py").write_text("")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "y.py").write_text("")
    (tmp_path / "real.py").write_text("")

    files = discover([tmp_path])

    assert [f.name for f in files] == ["real.py"]


def test_discover_returns_sorted_deduplicated(tmp_path):
    (tmp_path / "z.py").write_text("")
    (tmp_path / "a.py").write_text("")

    files = discover([tmp_path, tmp_path / "a.py"])

    assert [f.name for f in files] == ["a.py", "z.py"]
