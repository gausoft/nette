from pathlib import Path

import pytest


@pytest.fixture
def write_file(tmp_path: Path):
    def _write(content: str, name: str = "mod.py") -> Path:
        file = tmp_path / name
        file.write_text(content)
        return file

    return _write
