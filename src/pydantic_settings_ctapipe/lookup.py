"""A lookup table for configuration values."""

from collections.abc import Sequence
from fnmatch import fnmatch
from typing import Any, Generic, TypeVar, get_args, get_origin

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, SchemaValidator, core_schema

ItemType = TypeVar("T")


class NotFoundType:
    """A sentinel value (like None but distinct)."""


NotFound = NotFoundType()


def _matches(definition, value):
    if isinstance(definition, str):
        return fnmatch(value, definition)
    return value == definition


class Lookup(Generic[ItemType]):
    """A lookup table for configuration values.

    The table is using a hierarchical index of arbitrary keys.

    Later keys take higher precedence.

    str index values are matched using fnmatch, all other types are compared
    for equality.
    """

    def __init__(self, entries: Sequence[tuple[str, Any, ItemType]]):
        self.entries: list[tuple[str, Any, ItemType]] = list(entries)

        self._lookup_table = {}
        for index_key, index_value, config_value in self.entries:
            if index_key not in self._lookup_table:
                self._lookup_table[index_key] = {}

            self._lookup_table[index_key][index_value] = config_value

        self._cache = {}

    def get(self, **kwargs) -> ItemType:
        """Look up a config value given an index."""
        # make kwargs dict contents hashable
        index_keys = tuple(kwargs.keys())
        index_values = tuple(kwargs.values())
        cache_key = index_keys, index_values

        # distinguish None found in cache from key not found
        if (value := self._cache.get(cache_key, NotFound)) is not NotFound:
            return value

        value = NotFound

        for index_key, index_value in kwargs.items():
            if (lookup := self._lookup_table.get(index_key)) is not None:
                for definition, config_value in lookup.items():
                    if _matches(definition, index_value):
                        value = config_value

        if value is NotFound:
            raise KeyError(f"No configuration found for lookup index {kwargs}")

        self._cache[cache_key] = value
        return value

    def __repr__(self):  # noqa: D105
        return f"Lookup({self.entries})"

    def __eq__(self, other):  # noqa: D105
        return isinstance(other, Lookup) and self.entries == other.entries

    # Required for Pydantic to parse from JSON or dict
    @classmethod
    def __get_pydantic_core_schema__(  # noqa: D105
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        origin = get_origin(source_type)
        if origin is None:
            origin = source_type
            item_type = Any
        else:
            item_type = get_args(source_type)[0]

        entries_schema = handler.generate_schema(list[tuple[str, Any, item_type]])

        type_schema = core_schema.is_instance_schema(cls)

        def validate(value):
            if isinstance(value, Lookup):
                entries = value.entries
            else:
                entries = value

            validator = SchemaValidator(entries_schema)
            entries = validator.validate_python(entries)
            return Lookup(entries)

        python_schema = core_schema.no_info_before_validator_function(
            validate,
            type_schema,
        )

        json_schema = core_schema.chain_schema(
            [
                entries_schema,
                core_schema.no_info_before_validator_function(
                    lambda entries: Lookup(entries), type_schema
                ),
            ]
        )

        return core_schema.json_or_python_schema(
            json_schema=json_schema,
            python_schema=python_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: v.entries,
                return_schema=entries_schema,
            ),
        )
