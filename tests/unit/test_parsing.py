import ast

from nette.parsing import parse_source


def test_parse_returns_ast_tokens_and_lines(write_file):
    file = write_file("x = 1  # note\n")

    source = parse_source(file)

    assert isinstance(source.tree, ast.Module)
    assert source.lines == ["x = 1  # note"]
    assert any(tok.string == "# note" for tok in source.tokens)


def test_parse_failure_yields_error_finding_not_crash(write_file):
    file = write_file("def broken(:\n")

    source = parse_source(file)

    assert source.tree is None
    assert len(source.errors) == 1
    error = source.errors[0]
    assert error.code == "NET000"
    assert error.file == file
    assert error.line == 1


def test_parse_records_path(write_file):
    file = write_file("x = 1\n")

    assert parse_source(file).path == file
