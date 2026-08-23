import pytest

from nette.config import Config, find_root, load_config


def write_pyproject(tmp_path, body):
    (tmp_path / "pyproject.toml").write_text(body)
    return tmp_path


def test_defaults_when_no_config_file(tmp_path):
    config = load_config(tmp_path)

    assert config == Config()
    assert config.select == (
        "defensiveness",
        "duplication",
        "engine",
        "naming",
        "shape",
        "structure",
    )
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
    write_pyproject(tmp_path, '[tool.nette]\nselct = ["shape"]\n')

    with pytest.raises(ValueError, match="selct"):
        load_config(tmp_path)


def test_unknown_threshold_is_rejected(tmp_path):
    write_pyproject(
        tmp_path,
        '[tool.nette.thresholds]\nfunction_lenght = 80\n',
    )

    with pytest.raises(ValueError, match="function_lenght"):
        load_config(tmp_path)


def test_threshold_below_one_is_rejected(tmp_path):
    write_pyproject(tmp_path, "[tool.nette.thresholds]\nfunction_length = 0\n")

    with pytest.raises(ValueError, match="greater than zero"):
        load_config(tmp_path)


def test_percentage_threshold_above_one_hundred_is_rejected(tmp_path):
    write_pyproject(tmp_path, "[tool.nette.thresholds]\nduplication_similarity = 150\n")

    with pytest.raises(ValueError, match="percentage"):
        load_config(tmp_path)


def test_root_is_the_nearest_directory_holding_a_marker(tmp_path):
    package = tmp_path / "src" / "pkg"
    package.mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'x'\n")
    module = package / "mod.py"
    module.write_text("")

    assert find_root([module]) == tmp_path.resolve()
    assert find_root([package]) == tmp_path.resolve()


def test_root_falls_back_to_the_directory_when_no_marker_exists(tmp_path):
    alone = tmp_path / "alone"
    alone.mkdir()

    assert find_root([alone]) == alone.resolve()


def test_config_filters_rules_by_family_and_name():
    config = Config(select=("shape",), ignore=("nesting-depth",))

    assert config.rule_enabled("function-length", "shape") is True
    assert config.rule_enabled("nesting-depth", "shape") is False
    assert config.rule_enabled("over-guarded", "defensiveness") is False


def test_unknown_rule_name_is_rejected_with_a_suggestion(tmp_path):
    (tmp_path / "nette.toml").write_text('ignore = ["argument-conut"]\n')

    with pytest.raises(ValueError) as error:
        load_config(tmp_path)

    assert "argument-conut" in str(error.value)
    assert "argument-count" in str(error.value)


def test_nette_toml_accepts_the_pyproject_section_header(tmp_path):
    (tmp_path / "nette.toml").write_text('[tool.nette]\nignore = ["function-length"]\n')

    assert load_config(tmp_path).ignore == ("function-length",)


def test_engine_rules_can_be_named_in_config(tmp_path):
    (tmp_path / "nette.toml").write_text('ignore = ["bare-allow", "parse-error"]\n')

    assert load_config(tmp_path).ignore == ("bare-allow", "parse-error")


def test_nette_toml_refuses_to_mix_both_shapes(tmp_path):
    (tmp_path / "nette.toml").write_text(
        'ignore = ["function-length"]\n\n[tool.nette]\nprofile = "fastapi"\n'
    )

    with pytest.raises(ValueError, match="mixes"):
        load_config(tmp_path)


@pytest.mark.parametrize(
    "body",
    [
        'output = "concise"\n',
        "thresholds = 3\n",
        'profile = ["fastapi"]\n',
    ],
)
def test_wrong_shapes_raise_value_error_not_a_type_error(tmp_path, body):
    (tmp_path / "nette.toml").write_text(body)

    with pytest.raises(ValueError):
        load_config(tmp_path)
