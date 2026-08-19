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
    assert error.code == "parse-error"
    assert error.file == file
    assert error.line == 1


def test_parse_records_path(write_file):
    file = write_file("x = 1\n")

    assert parse_source(file).path == file


def test_latin1_declared_encoding_is_honored(tmp_path):
    file = tmp_path / "legacy.py"
    file.write_bytes("# -*- coding: latin-1 -*-\nnom = 'caf\xe9'\n".encode("latin-1"))

    source = parse_source(file)

    assert source.tree is not None
    assert source.errors == ()


def test_undecodable_file_yields_finding_not_crash(tmp_path):
    file = tmp_path / "junk.py"
    file.write_bytes(b"\xff\xfe invalid \xff")

    source = parse_source(file)

    assert source.tree is None
    assert [f.code for f in source.errors] == ["parse-error"]
