"""Logging support."""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import AliasChoices, BeforeValidator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseLogSettings(BaseSettings):
    """Base class for logging models."""

    model_config = SettingsConfigDict(
        nested_model_default_partial_update=True,
    )

    def model_dump(self, **kwargs):
        """Dump model with by_alias=True and exclude_none=True."""
        return super().model_dump(by_alias=True, exclude_none=True, **kwargs)

    def model_dump_json(self, **kwargs):
        """Dump model with by_alias=True and exclude_none=True."""
        return super().model_dump_json(by_alias=True, exclude_none=True, **kwargs)


def _parse_log_level(v):
    if isinstance(v, int):
        return v

    if isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            known_levels = logging.getLevelNamesMapping()
            value = known_levels.get(v.upper())
            if value is not None:
                return value

    raise ValueError(f"Invalid log level: {v}")


LogLevel = Annotated[int, BeforeValidator(_parse_log_level)]


class Formatter(BaseLogSettings):
    """Pydantic model for the configuration of a logging.Formatter."""

    model_config = SettingsConfigDict(populate_by_name=True)

    format: str | None = None
    datefmt: str | None = None
    style: str | None = None
    validate_: bool | None = Field(None, alias="validate")
    defaults: dict[str, Any] | None = None
    class_: str | None = Field(
        None,
        validation_alias=AliasChoices("class", "class_"),
        serialization_alias="class",
    )


class Filter(BaseLogSettings):
    """Pydantic model for the configuration of a logging.Filter."""

    name: str = ""


class Handler(BaseLogSettings):
    """Pydantic model for the configuration of a logging.Handler."""

    # all other kwargs are passed to ctor, so need to allow arbitrary data
    model_config = SettingsConfigDict(extra="allow", populate_by_name=True)

    class_: str | None = Field(
        validation_alias=AliasChoices("class", "class_"), serialization_alias="class"
    )
    level: LogLevel | None = None
    formatter: str | None = None
    filters: list[str] | None = None


class RootLogger(BaseLogSettings):
    """Pydantic model for the configuration the root logger."""

    level: LogLevel | None = None
    filters: list[str] | None = None
    handlers: list[str] | None = None


class Logger(RootLogger):
    """Pydantic model for the configuration of a single logger."""

    propagate: bool = True


class LogConfig(BaseLogSettings):
    """Model for logging configuration."""

    version: Literal[1] = 1
    formatters: dict[str, Formatter] | None = None
    handlers: dict[str, Handler] | None = None
    loggers: dict[str, Logger] | None = None
    root: RootLogger | None = None
    disable_existing_loggers: bool = False
    incremental: bool = True


class ISOFormatter(logging.Formatter):
    """Formatter properly formatting times as ISO8601 timestamps."""

    def formatTime(self, record, datefmt=None):  # noqa: N802
        """Format timestamps as ISO8601 with microsecond precision."""
        dt = datetime.fromtimestamp(record.created, tz=UTC)
        # convert to local time
        return dt.astimezone().strftime(datefmt)


DEFAULT_LOG_CONFIG = LogConfig(
    formatters={
        "default": Formatter(
            format="%(asctime)s %(levelname)s [%(name)s]: %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S.%f%z",
            class_="pydantic_configtree.logging.ISOFormatter",
        ),
    },
    handlers={
        "console": Handler(class_="logging.StreamHandler", formatter="default"),
    },
    root=RootLogger(handlers=["console"]),
    incremental=False,
)
