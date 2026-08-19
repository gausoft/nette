import sysconfig
from pathlib import Path

import pytest

from nette.discovery import discover
from nette.engine import check_files
from nette.findings import Severity
from nette.rules.shape import SHAPE_RULES

STDLIB = Path(sysconfig.get_paths()["stdlib"])
EXEMPLARY_MODULES = [
    "dataclasses.py",
    "graphlib.py",
    "textwrap.py",
    "statistics.py",
]
WARNING_BUDGET_PER_KLOC = 6.0


@pytest.mark.parametrize("module", EXEMPLARY_MODULES)
def test_exemplary_stdlib_has_no_error_findings(module):
    findings = _check(STDLIB / module)

    errors = [f for f in findings if f.severity is Severity.ERROR]
    assert errors == []


@pytest.mark.parametrize("module", EXEMPLARY_MODULES)
def test_exemplary_stdlib_warning_noise_stays_low(module):
    file = STDLIB / module

    findings = _check(file)

    kloc = len(file.read_text().splitlines()) / 1000
    budget = max(3, WARNING_BUDGET_PER_KLOC * kloc)
    assert len(findings) <= budget, [
        f"{f.code} {f.file.name}:{f.line} {f.message}" for f in findings
    ]


def test_nette_own_source_is_clean():
    src = Path(__file__).parent.parent.parent / "src"

    findings = check_files(discover([src]), rules=_rules())

    assert findings == []


def _check(file: Path):
    return check_files([file], rules=_rules())


def _rules():
    return [rule() for rule in SHAPE_RULES]
