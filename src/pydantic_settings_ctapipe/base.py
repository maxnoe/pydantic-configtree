"""Core definitions."""

import logging
import weakref
from abc import ABCMeta
from inspect import isabstract
from typing import Annotated, Literal, Self, Union

from pydantic import Field, create_model, model_validator
from pydantic_settings import BaseSettings


class Config(BaseSettings):
    """Base pydantic model for configuration."""


class ConfigurableMeta(ABCMeta):
    """Metaclass for Configurable."""

    def __new__(cls, name, bases, dct):
        """Validate and create new Configurable class."""
        # create an empty config in case none is defined
        config_cls = dct.get("__config__", Config)

        # add field "cls" to config, needed to select correct element in Union via config
        module = dct.get("__module__")
        qualname = dct.get("__qualname__", name)
        if module is not None:
            fqdn = f"{module}.{qualname}"
        else:
            fqdn = name

        cls_type = Literal[name, fqdn]

        def autofill_cls(cls, values):
            values.setdefault("cls", fqdn)
            return values

        config_cls = create_model(
            config_cls.__qualname__,
            cls=cls_type,
            __base__=config_cls,
            __module__=module,
            __doc__=config_cls.__doc__,
            __validators__={
                "autofill_cls": model_validator(mode="before")(autofill_cls),
            },
        )

        # only validate concrete implementations, not the Configurable base class or abstract classes
        if not issubclass(config_cls, Config):
            raise TypeError(
                f"{name}.config_cls must be a subclass of {Config}, got: {config_cls.__bases__}"
            )

        dct["__config__"] = config_cls
        return super().__new__(cls, name, bases, dct)


class Configurable(metaclass=ConfigurableMeta):
    """Base class for all configurable classes."""

    def __init__(
        self,
        config: Config | None = None,
        parent: "Configurable | None" = None,
        name: str | None = None,
    ):
        self.name = name or self.__class__.__name__

        if config is None:
            config = self.__config__()
        elif not isinstance(config, self.__config__):
            raise TypeError(
                f"Expected an instance of {self.__config__!r}, got {config!r}"
            )

        self.config: self.__config__ = config
        self._parent = weakref.ref(parent) if parent is not None else None

        if self.parent is None:
            self.log = logging.getLogger(self.__class__.__module__).getChild(self.name)
        else:
            self.log = self.parent.log.getChild(self.name)

    @property
    def parent(self) -> "Configurable | None":
        """The parent class of this class in the config hierarchy."""
        if self._parent is None:
            return None
        return self._parent()

    @classmethod
    def configurable_subclasses(cls):
        """
        Union of non-abstract classes with discriminator annotation.

        Return a union that is suitable for use in Config classes to allow
        all non-abstract subclasses of this class to be configured
        """
        subclasses = _non_abstract_subclasses(cls)
        config_classes = tuple(cls.__config__ for cls in subclasses)
        union = Union.__getitem__(config_classes)
        return Annotated[union, Field(discriminator="cls")]

    @classmethod
    def non_abstract_subclasses(cls) -> dict[str, Self]:
        """Get a dictionary of non-abstract children of this Configurable."""
        return {
            f"{sub.__module__}.{sub.__qualname__}": sub
            for sub in _non_abstract_subclasses(cls)
        }

    @classmethod
    def from_config(cls, config, parent=None, name=None, **kwargs) -> Self:
        """Create a new instance by selecting the correct subclass based on the config object."""
        if config is None:
            return None

        subclasses = cls.non_abstract_subclasses()

        # first try by fqdn
        subcls = subclasses.get(config.cls)

        # fallback to name in case not found by fqdn
        if subcls is None:
            by_name = {v.__name__: v for v in subclasses.values()}
            subcls = by_name.get(config.cls)

        # error in case we still didn't find it
        if subcls is None:
            raise ValueError(f"{config.cls} is not a known subclass of {cls}")

        return subcls(config=config, parent=parent, name=name, **kwargs)


def _non_abstract_subclasses(base):
    non_abstract = []

    for subcls in base.__subclasses__():
        if not isabstract(subcls):
            non_abstract.append(subcls)

        # recurse
        non_abstract.extend(_non_abstract_subclasses(subcls))

    return non_abstract
