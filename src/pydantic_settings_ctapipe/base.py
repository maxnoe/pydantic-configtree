"""Core definitions."""

from pydantic_settings import BaseSettings


class ConfigurableMeta(type):
    """Metaclass for all Configurable."""

    def __new__(cls, name, bases, dct):
        """Validate and create new Configurable class."""
        config_cls = dct.get("config_cls")

        # only validate concrete implementations, not the Configurable base class
        if len(bases) > 0:
            if config_cls is None:
                raise TypeError(f"Class {name} must define a config_cls")

            if not issubclass(config_cls, BaseSettings):
                raise TypeError(
                    f"{name}.config_cls must be a subclass of {BaseSettings}, got: {config_cls}"
                )

        return super().__new__(cls, name, bases, dct)


class Configurable(metaclass=ConfigurableMeta):
    """Base class for all configurable classes."""

    #: the BaseSettings derived pydantic model to configure this class
    config_cls: type[BaseSettings] | None = None

    def __init__(self, settings: BaseSettings | None = None):
        if self.config_cls is not None:
            if settings is None:
                settings = self.config_cls()

            elif not isinstance(settings, self.config_cls):
                raise TypeError(
                    f"Expected an instance of {self.config_cls!r}, got {settings!r}"
                )

        self.settings = settings
