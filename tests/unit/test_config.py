import pytest

from nette.config import Config, load_config


def write_pyproject(tmp_path, body):
    (tmp_path / "pyproject.toml").write_text(body)
    return tmp_path


def test_defaults_when_no_config_file(tmp_path):
    config = load_config(tmp_path)

    assert config == Config()
    assert config.select == ("NET",)
    assert config.ignore == ()
    assert config.thresholds == {}
    assert config.output_format == "full"


def test_reads_tool_nette_section(tmp_path):
    write_pyproject(
        tmp_path,
        '[tool.nette]\n'
        'select = ["NET1", "NET3"]\n'
        'ignore = ["NET104"]\n'
        '\n'
        '[tool.nette.thresholds]\n'
        'function_length = 80\n'
        '\n'
        '[tool.nette.output]\n'
        'format = "concise"\n',
    )

    config = load_config(tmp_path)

    assert config.select == ("NET1", "NET3")
    assert config.ignore == ("NET104",)
    assert config.thresholds == {"function_length": 80}
    assert config.output_format == "concise"


def test_pyproject_without_nette_section_gives_defaults(tmp_path):
    write_pyproject(tmp_path, '[project]\nname = "x"\n')

    assert load_config(tmp_path) == Config()


def test_nette_toml_takes_precedence_over_pyproject(tmp_path):
    write_pyproject(tmp_path, '[tool.nette]\nignore = ["NET101"]\n')
    (tmp_path / "nette.toml").write_text('ignore = ["NET102"]\n')

    config = load_config(tmp_path)

    assert config.ignore == ("NET102",)


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


def test_config_filters_rules():
    config = Config(select=("NET1",), ignore=("NET102",))

    assert config.rule_enabled("NET101") is True
    assert config.rule_enabled("NET102") is False
    assert config.rule_enabled("NET301") is False
