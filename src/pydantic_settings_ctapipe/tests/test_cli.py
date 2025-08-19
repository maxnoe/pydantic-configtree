import json
from textwrap import dedent

import pytest
import tomlkit
import yaml
from pydantic import ValidationError
from pydantic_settings import CliApp, SettingsConfigDict, SettingsError

from pydantic_settings_ctapipe import Config, Configurable, Tool


class Component(Configurable):
    class __config__(Config):
        common: int = 1


class Foo(Component):
    class __config__(Component.__config__):
        foo_option: int = 2


class Bar(Component):
    class __config__(Component.__config__):
        bar_option: int = 2


class ExampleTool(Tool):
    """
    An example CLI tool.

    This computes stuff.
    """

    value: int = 1
    component: Component.configurable_subclasses() = Foo.__config__(foo_option=2)

    model_config = SettingsConfigDict(
        env_prefix="TEST_TOOL_",
    )

    def setup(self):
        self._component = Component.from_config(config=self.component, parent=self)

    def run(self):
        print(f"{self.model_dump_json()}")


def test_help(capsys):
    with pytest.raises(SystemExit):
        CliApp.run(ExampleTool, ["--help"])

    captured = capsys.readouterr()

    # help should include the docstring
    assert dedent(ExampleTool.__doc__).strip() in captured.out


@pytest.mark.parametrize("fmt", [".json", ".yml", ".yaml", ".toml"])
def test_single_config_file(capsys, tmp_path, fmt):
    config = {"value": 2, "component": {"cls": "Bar", "common": 3, "bar_option": 4}}

    if fmt == ".json":
        config_dump = json.dumps(config)
    elif fmt == ".toml":
        config_dump = tomlkit.dumps(config)
    else:
        config_dump = yaml.safe_dump(config)

    config_path = tmp_path / ("config" + fmt)

    config_path.write_text(config_dump)

    CliApp.run(ExampleTool, ["-c", str(config_path)])

    result_config = json.loads(capsys.readouterr().out)
    for k, v in config.items():
        assert result_config[k] == v


def test_invalid_value():
    with pytest.raises(ValidationError):
        CliApp.run(ExampleTool, ["--value=1.2"])


def test_invalid_option():
    with pytest.raises(SettingsError):
        CliApp.run(ExampleTool, ["--non-existent-option=1.0"])
