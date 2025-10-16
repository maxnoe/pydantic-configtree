import json
import sys
from textwrap import dedent

import pytest
import tomlkit
import yaml
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict, SettingsError

from pydantic_configtree import Config, Configurable, Tool


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

    class __config__(Tool.__config__):
        """This is the help for the CLI."""

        value: int = 1
        component: Component.configurable_subclasses() = Foo.__config__(foo_option=2)

        model_config = SettingsConfigDict(
            env_prefix="TEST_TOOL_",
        )

    def setup(self):
        self.component = Component.from_config(
            config=self.config.component, parent=self
        )

    def run(self):
        print(self.config.model_dump_json())


def test_help(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["example-tool", "--help"])
    with pytest.raises(SystemExit) as e_info:
        ExampleTool()

    assert e_info.value.code == 0

    # help should include the docstring
    captured = capsys.readouterr()
    assert dedent(ExampleTool.__config__.__doc__).strip() in captured.out


@pytest.mark.parametrize("fmt", [".json", ".yml", ".yaml", ".toml"])
def test_single_config_file(capsys, tmp_path, fmt, monkeypatch):
    config = {"value": 2, "component": {"cls": "Bar", "common": 3, "bar_option": 4}}

    if fmt == ".json":
        config_dump = json.dumps(config)
    elif fmt == ".toml":
        config_dump = tomlkit.dumps(config)
    else:
        config_dump = yaml.safe_dump(config)

    config_path = tmp_path / ("config" + fmt)

    config_path.write_text(config_dump)

    monkeypatch.setattr(sys, "argv", ["example-tool", "-c", str(config_path)])
    tool = ExampleTool()
    tool.start()

    result_config = json.loads(capsys.readouterr().out)
    for k, v in config.items():
        assert result_config[k] == v


def test_invalid_value(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["example-tool", "--value=1.2"])
    with pytest.raises(ValidationError):
        ExampleTool()


def test_invalid_option(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["example-tool", "--non-existent-option=1.0"])
    with pytest.raises(SettingsError):
        ExampleTool()
