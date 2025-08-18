"""Extensions of pydantic-settings for ctapipe."""

from ._version import __version__
from .base import Config, Configurable

#: Version of the package
__version__ = __version__


__all__ = [
    "__version__",
    "Config",
    "Configurable",
]
