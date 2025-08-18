import pytest
from astropy.time import Time
from pydantic import TypeAdapter, ValidationError


def test_time():
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
