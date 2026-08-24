from nette.config import Config
from nette.engine import check_files
from nette.rules.shape import ArgumentCount


WIDE = (
    "@celery.task(bind=True)\n"
    "def sync(self, a, b, c, d, e, f, g):\n"
    "    return a\n"
)


def check(file, exempt=()):
    return check_files([file], rules=[ArgumentCount()], exempt_decorated_by=exempt)


def test_a_wide_signature_is_flagged_without_the_exemption(write_file):
    file = write_file(WIDE)

    assert [f.code for f in check(file)] == ["argument-count"]


def test_the_exemption_silences_the_decorated_function(write_file):
    file = write_file(WIDE)

    assert check(file, exempt=("celery.task",)) == []


def test_a_bare_name_matches_the_tail_of_the_path(write_file):
    file = write_file(WIDE)

    assert check(file, exempt=("task",)) == []


def test_a_decorator_without_a_call_is_matched(write_file):
    file = write_file(
        "@click.command\ndef run(a, b, c, d, e, f, g):\n    return a\n"
    )

    assert check(file, exempt=("click.command",)) == []


def test_another_decorator_does_not_silence(write_file):
    file = write_file(WIDE)

    assert [f.code for f in check(file, exempt=("click.command",))] == ["argument-count"]


def test_the_config_reads_the_list(tmp_path):
    from nette.config import load_config

    (tmp_path / "pyproject.toml").write_text(
        '[tool.nette]\nexempt_decorated_by = ["celery.task", "click.command"]\n'
    )

    assert load_config(tmp_path).exempt_decorated_by == ("celery.task", "click.command")


def test_the_default_is_empty():
    assert Config().exempt_decorated_by == ()
