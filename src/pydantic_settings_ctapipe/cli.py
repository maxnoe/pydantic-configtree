"""Command-line support."""

import logging.config
from abc import abstractmethod

from pydantic import AliasChoices, Field, FilePath
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from .base import Config, Configurable
from .logging import DEFAULT_LOG_CONFIG, LogConfig
from .sources import CliConfigSettingsSource

__all__ = [
    "Tool",
]


class Tool(Configurable):
    """Base class for command-line tools."""

    class __config__(Config):
        config_files: list[FilePath] | None = Field(
            None, alias=AliasChoices("c", "config")
        )
        log_config: LogConfig = LogConfig()

        model_config = SettingsConfigDict(
            env_prefix="CTAPIPE_",
            cli_parse_args=True,
            cli_exit_on_error=False,
            cli_hide_none_type=True,
            cli_shortcuts={
                "log_config.root.level": "log-level",
            },
        )

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
        # we always make a basic setup with the default logging config
        logging.config.dictConfig(DEFAULT_LOG_CONFIG.model_dump())

        # then apply the configured logging here, which by default will be "incremental"
        # but can also completely replace the existing config if incremental=False is passed
        logging.config.dictConfig(self.config.log_config.model_dump())
        self.log = logging.getLogger(
            self.config.model_config["cli_prog_name"] or self.__class__.__name__
        )

    def start(self):
        """Entry point for pydantic_settings.CliApp."""
        self._setup_logging()

        self.setup()
        self.run()
        self.finish()
