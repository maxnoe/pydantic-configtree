"""Command-line support."""

from abc import abstractmethod

from pydantic import AliasChoices, Field, FilePath
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from .logging import LogConfig
from .sources import CliConfigSettingsSource


class Tool(BaseSettings):
    """Base class for command-line tools."""

    model_config = SettingsConfigDict(
        env_prefix="CTAPIPE_",
        cli_hide_none_type=True,
        cli_shortcuts={
            "log_config.level": "log-level",
        },
        cli_exit_on_error=False,
    )

    config_files: list[FilePath] | None = Field(None, alias=AliasChoices("c", "config"))

    log_config: LogConfig = LogConfig()

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Customize configuration setting sources.

        Adds our custom config file source and removes dotenv and file secret sources.
        """
        return (
            init_settings,
            env_settings,
            CliConfigSettingsSource(settings_cls=settings_cls),
        )

    def setup(self):
        """Perform setup of the CLI tool."""

    @abstractmethod
    def run(self):
        """Run main functionality of the CLI tool."""

    def finish(self):
        """Run cleanup / exit steps."""

    def _setup_logging(self):
        pass

    def cli_cmd(self) -> None:
        """Entry point for pydantic_settings.CliApp."""
        self._setup_logging()

        self.setup()
        self.run()
        self.finish()
