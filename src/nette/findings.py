from __future__ import annotations

import enum
from dataclasses import dataclass
from pathlib import Path
from typing import Final


class Severity(enum.Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, order=False)
class Finding:
    code: str
    message: str
    grounds: str
    help: str
    severity: Severity
    file: Path
    line: int
    column: int
    end_line: int
    end_column: int
    fixable: bool = False

    def __lt__(self, other: "Finding") -> bool:
        return self._sort_key() < other._sort_key()

    def _sort_key(self) -> tuple[str, int, int, str]:
        return (str(self.file), self.line, self.column, self.code)


PARSE_ERROR_CODE: Final = "NET000"
