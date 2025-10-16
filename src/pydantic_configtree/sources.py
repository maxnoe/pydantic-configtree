"""Additional SettingsSource implementations."""

from pathlib import Path
from typing import Any

from pydantic_settings import BaseSettings
from pydantic_settings.sources import (
    InitSettingsSource,
    JsonConfigSettingsSource,
    TomlConfigSettingsSource,
    YamlConfigSettingsSource,
)


class CliConfigSettingsSource(InitSettingsSource):
    """A SettingsSource that loads config files assuming the CLI has an option for config files.

    Supports loading YAML, JSON and TOML files.
    """

    def __init__(self, settings_cls: type[BaseSettings]):
        super().__init__(settings_cls=settings_cls, init_kwargs={})

    def __call__(self) -> dict[str, Any]:  # noqa: D102
        # check if we got config files on the CLI, c is the first alias
        # of the config_files field in Tool which is what is used in state
        config_files = self.current_state.get("c", [])

        config = {}

        if len(config_files) > 0:
            for config_file in config_files:
                config_file = Path(config_file).expanduser()

                if not config_file.is_file():
                    continue

                if config_file.suffix == ".toml":
                    source = TomlConfigSettingsSource(
                        self.settings_cls, toml_file=config_file
                    )
                    new_config = source.toml_data
                elif config_file.suffix == ".json":
                    source = JsonConfigSettingsSource(
                        self.settings_cls, json_file=config_file
                    )
                    new_config = source.json_data
                elif config_file.suffix in {".yml", ".yaml"}:
                    source = YamlConfigSettingsSource(
                        self.settings_cls, yaml_file=config_file
                    )
                    new_config = source.yaml_data
                else:
                    raise ValueError(
                        f"Config file path {config_file} has unsupported format: {config_file.suffix}"
                    )

                config.update(new_config)

        super().__init__(self.settings_cls, config)
        return super().__call__()
