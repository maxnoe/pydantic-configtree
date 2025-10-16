"""pydantic type adapters for astropy types."""

from typing import Annotated, Any

from astropy.time import Time
from astropy.units import Quantity, Unit
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

__all__ = [
    "AstropyTime",
    "AstropyQuantity",
]


class _AstropyTimeTypeAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        from_string = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(lambda s: Time(s)),
            ]
        )

        return core_schema.json_or_python_schema(
            python_schema=core_schema.is_instance_schema(Time),
            json_schema=from_string,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda t: Time(t, precision=9).utc.isot,
            ),
        )


#: Type adapter for `astropy.time.Time`.
#:
#: JSON serialization is implemented from/to ISO UTC string.
AstropyTime = Annotated[
    Time,
    _AstropyTimeTypeAnnotation,
]


class AstropyQuantity:
    """
    Type adapter for `astropy.time.Time`.

    Serialization is implemented to a value/unit dict
    and parsing additionally supports plain strings.
    """

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        """Pydantic schema definition for astropy quantity."""
        dict_schema = core_schema.chain_schema(
            [
                core_schema.typed_dict_schema(
                    {
                        "value": core_schema.typed_dict_field(
                            core_schema.float_schema()
                        ),
                        "unit": core_schema.typed_dict_field(core_schema.str_schema()),
                    }
                ),
                core_schema.no_info_plain_validator_function(
                    lambda d: Quantity(d["value"], unit=d["unit"])
                ),
            ]
        )

        str_schema = core_schema.chain_schema(
            [
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(lambda s: Quantity(s)),
            ]
        )

        python_schema = core_schema.union_schema(
            [
                dict_schema,
                str_schema,
                core_schema.is_instance_schema(Quantity),
            ]
        )
        json_schema = core_schema.union_schema([dict_schema, str_schema])

        return core_schema.json_or_python_schema(
            python_schema=python_schema,
            json_schema=json_schema,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda q: {"value": q.value, "unit": q.unit.to_string("vounit")}
            ),
        )

    def __class_getitem__(cls, unit: Unit):
        """Implement support for AstropyQuantity[<unit>]."""

        class _QuantityWithUnit:
            @classmethod
            def __get_pydantic_core_schema__(cls, _source_type: Any, _handler: Any):
                base = AstropyQuantity.__get_pydantic_core_schema__(
                    _source_type, _handler
                )
                with_unit = core_schema.chain_schema(
                    [
                        base,
                        core_schema.no_info_plain_validator_function(
                            lambda q: q.to(unit)
                        ),
                    ]
                )
                with_unit["serialization"] = base["serialization"]
                return with_unit

        return Annotated[Quantity, _QuantityWithUnit]
