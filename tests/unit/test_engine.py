import ast

from nette.engine import check_files
from nette.findings import Severity
from nette.rules import Context, Rule


class FlagEveryFunction(Rule):
    code = "TST001"

    def visit_functiondef(self, node: ast.FunctionDef, ctx: Context) -> None:
        ctx.report(
            node,
            message=f"function {node.name} flagged",
            grounds="test rule",
            help="none",
        )


class CountCalls(Rule):
    code = "TST002"

    def visit_call(self, node: ast.Call, ctx: Context) -> None:
        ctx.report(node, message="call", grounds="test", help="none")


def test_rule_visits_matching_nodes(write_file):
    file = write_file("def alpha():\n    pass\n\ndef beta():\n    pass\n")

    findings = check_files([file], rules=[FlagEveryFunction()])

    assert [f.message for f in findings] == [
        "function alpha flagged",
        "function beta flagged",
    ]
    assert findings[0].code == "TST001"
    assert findings[0].file == file
    assert findings[0].line == 1


def test_multiple_rules_share_one_walk(write_file):
    file = write_file("def f():\n    print(1)\n")

    findings = check_files([file], rules=[FlagEveryFunction(), CountCalls()])

    assert sorted(f.code for f in findings) == ["TST001", "TST002"]


def test_syntax_error_becomes_finding(write_file):
    file = write_file("def broken(:\n", name="bad.py")

    findings = check_files([file], rules=[FlagEveryFunction()])

    assert [f.code for f in findings] == ["NET000"]
    assert findings[0].severity is Severity.ERROR


def test_findings_come_out_sorted_across_files(write_file, tmp_path):
    write_file("def one():\n    pass\n", name="b.py")
    write_file("def two():\n    pass\n", name="a.py")

    findings = check_files(sorted(tmp_path.glob("*.py")), rules=[FlagEveryFunction()])

    assert [f.file.name for f in findings] == ["a.py", "b.py"]


def test_rule_default_severity_is_warning(write_file):
    file = write_file("def f():\n    pass\n")

    findings = check_files([file], rules=[FlagEveryFunction()])

    assert findings[0].severity is Severity.WARNING
