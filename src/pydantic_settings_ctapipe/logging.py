"""Logging support."""

import logging

from pydantic import field_validator
from pydantic_settings import BaseSettings


class LogConfig(BaseSettings):
    """Model for logging configuration."""

    level: int = logging.WARNING

    @field_validator("level", mode="before")
    @classmethod
    def _parse_log_level(cls, v):
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
