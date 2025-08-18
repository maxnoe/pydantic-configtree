import json

import pytest
from astropy.time import Time
from pydantic import BaseModel, TypeAdapter, ValidationError


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
