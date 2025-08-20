import json

import astropy.units as u
import pytest
from astropy.time import Time
from pydantic import BaseModel, TypeAdapter, ValidationError

from pydantic_settings_ctapipe.astropy import AstropyQuantity


def test_time_typeadapter():
    from pydantic_settings_ctapipe.astropy import AstropyTime

    ta = TypeAdapter(AstropyTime)

    t = Time.now()
    assert ta.validate_python(t) == t
    assert ta.validate_json(ta.dump_json(t)) == t

    with pytest.raises(ValidationError):
        ta.validate_python("2020-01-01T20:00:00")

    with pytest.raises(ValidationError):
        ta.validate_python(1755511106.116)

    with pytest.raises(ValidationError):
        ta.validate_json("1755511106.116")


def test_time_model():
    from pydantic_settings_ctapipe.astropy import AstropyTime

    class HasTime(BaseModel):
        timestamp: AstropyTime

    t = Time.now()
    data = HasTime(timestamp=t)
    assert data.timestamp == t

    # check that python model dump still contains astropy time
    assert data.model_dump()["timestamp"] == t

    # json should store ISOT UTC string
    parsed = json.loads(data.model_dump_json())
    assert parsed["timestamp"] == Time(t, precision=9).utc.isot


@pytest.mark.parametrize("q", [5.2 * u.m, 12.3456789 * u.ms])
def test_quantity(q):
    from pydantic_settings_ctapipe.astropy import AstropyQuantity

    ta = TypeAdapter(AstropyQuantity)

    assert ta.validate_python(q) == q
    assert type(ta.validate_python(q)) is u.Quantity
    assert (
        ta.validate_python({"value": q.value, "unit": q.unit.to_string("vounit")}) == q
    )
    assert ta.validate_python(str(q)) == q

    data_json = ta.dump_json(q)
    assert type(ta.validate_json(data_json)) is u.Quantity
    assert ta.validate_json(data_json) == q
    assert ta.validate_json(json.dumps(str(q))) == q


def test_quantity_with_unit():
    from pydantic_settings_ctapipe.astropy import AstropyQuantity

    ta = TypeAdapter(AstropyQuantity[u.m])

    assert ta.validate_python(5 * u.m) == 5 * u.m

    q = ta.validate_python(500 * u.cm)
    assert q.unit == u.m
    assert q.value == 5.0

    with pytest.raises(ValidationError):
        ta.validate_python(3 * u.s)


def test_dump_model_quantity():
    class Foo(BaseModel):
        q: AstropyQuantity[u.s] = 5 * u.s

    assert Foo().model_dump() == {"q": {"value": 5.0, "unit": "s"}}
    assert json.loads(Foo().model_dump_json()) == {"q": {"value": 5.0, "unit": "s"}}
