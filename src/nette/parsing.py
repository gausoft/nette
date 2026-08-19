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
    try:
        with tokenize.open(path) as handle:
            text = handle.read()
    except (SyntaxError, UnicodeDecodeError) as exc:
        return SourceFile(
            path=path,
            tree=None,
            tokens=(),
            lines=[],
            errors=(_decode_error_finding(path, exc),),
        )

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


def _decode_error_finding(path: Path, exc: Exception) -> Finding:
    return Finding(
        code=PARSE_ERROR_CODE,
        message=f"cannot decode file: {exc}",
        grounds="the file is not readable as Python source text",
        help="fix the file encoding (or its coding declaration) so nette can read it",
        severity=Severity.ERROR,
        file=path,
        line=1,
        column=0,
        end_line=1,
        end_column=0,
    )
