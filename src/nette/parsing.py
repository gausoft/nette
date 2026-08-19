from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass
from pathlib import Path

from nette.findings import PARSE_ERROR_CODE, Finding, Severity


@dataclass(frozen=True)
class SourceFile:
    path: Path
    tree: ast.Module | None
    tokens: tuple[tokenize.TokenInfo, ...]
    lines: list[str]
    errors: tuple[Finding, ...] = ()


def parse_source(path: Path) -> SourceFile:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return SourceFile(
            path=path,
            tree=None,
            tokens=(),
            lines=lines,
            errors=(_syntax_error_finding(path, exc),),
        )

    tokens = tuple(tokenize.generate_tokens(io.StringIO(text).readline))

    return SourceFile(path=path, tree=tree, tokens=tokens, lines=lines)


def _syntax_error_finding(path: Path, exc: SyntaxError) -> Finding:
    line = exc.lineno or 1
    column = (exc.offset or 1) - 1

    return Finding(
        code=PARSE_ERROR_CODE,
        message=f"syntax error: {exc.msg}",
        grounds="the file does not parse as Python",
        help="fix the syntax error before nette can judge this file",
        severity=Severity.ERROR,
        file=path,
        line=line,
        column=column,
        end_line=line,
        end_column=column,
    )
