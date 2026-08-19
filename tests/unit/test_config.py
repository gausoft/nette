import pytest

from nette.config import Config, load_config


def write_pyproject(tmp_path, body):
    (tmp_path / "pyproject.toml").write_text(body)
    return tmp_path


def test_defaults_when_no_config_file(tmp_path):
    config = load_config(tmp_path)

    assert config == Config()
    assert config.select == ("defensiveness", "engine", "naming", "shape", "structure")
    assert config.ignore == ()
    assert config.thresholds == {}
    assert config.output_format == "full"


def test_reads_tool_nette_section(tmp_path):
    write_pyproject(
        tmp_path,
        '[tool.nette]\n'
        'select = ["shape", "defensiveness"]\n'
        'ignore = ["return-count"]\n'
        '\n'
        '[tool.nette.thresholds]\n'
        'function_length = 80\n'
        '\n'
        '[tool.nette.output]\n'
        'format = "concise"\n',
    )

    config = load_config(tmp_path)

    assert config.select == ("shape", "defensiveness")
    assert config.ignore == ("return-count",)
    assert config.thresholds == {"function_length": 80}
    assert config.output_format == "concise"


def test_pyproject_without_nette_section_gives_defaults(tmp_path):
    write_pyproject(tmp_path, '[project]\nname = "x"\n')

    assert load_config(tmp_path) == Config()


def test_nette_toml_takes_precedence_over_pyproject(tmp_path):
    write_pyproject(tmp_path, '[tool.nette]\nignore = ["function-length"]\n')
    (tmp_path / "nette.toml").write_text('ignore = ["nesting-depth"]\n')

    config = load_config(tmp_path)

    assert config.ignore == ("nesting-depth",)


def test_unknown_key_is_rejected(tmp_path):
    write_pyproject(tmp_path, '[tool.nette]\nselct = ["NET"]\n')

    with pytest.raises(ValueError, match="selct"):
        load_config(tmp_path)


def test_unknown_threshold_is_rejected(tmp_path):
    write_pyproject(
        tmp_path,
        '[tool.nette.thresholds]\nfunction_lenght = 80\n',
    )

    with pytest.raises(ValueError, match="function_lenght"):
        load_config(tmp_path)


def test_config_filters_rules_by_family_and_name():
    config = Config(select=("shape",), ignore=("nesting-depth",))

    assert config.rule_enabled("function-length", "shape") is True
    assert config.rule_enabled("nesting-depth", "shape") is False
    assert config.rule_enabled("over-guarded", "defensiveness") is False
