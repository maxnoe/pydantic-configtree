from pydantic_configtree import Config
from pydantic_configtree.lookup import Lookup


def test_lookup():
    # Example usage with Pydantic settings
    class Settings(Config):
        option: Lookup[float]

    # Example data
    data = {
        "option": Lookup(
            [
                ("type", "*", 0.5),
                ("type", "LST", 5.0),
                ("type", "MST", 2.5),
                ("id", 1, 3.5),
                ("id", 5, 1.5),
            ]
        )
    }

    settings = Settings.model_validate(data)  # json.dumps(data))
    print(settings.option)
    print(settings.model_dump_json())

    # Test the behavior
    assert settings.option.get(type="LST", id=3) == 5.0  # type has match
    assert settings.option.get(type="ABC", id=1) == 3.5  # id has match
    assert settings.option.get(type="ABC", id=99) == 0.5  # type match on *
    assert settings.option.get(type="MST", id=3) == 2.5  # id has precedence over type
    assert settings.option.get(type="MST", id=5) == 1.5  # id has precedence over type


def test_lookup_quantity():
    import astropy.units as u

    from pydantic_configtree.astropy import AstropyQuantity

    class Settings(Config):
        option: Lookup[AstropyQuantity[u.m]]

    # Example data
    data = {
        "option": Lookup(
            [
                ("type", "*", 0.5 * u.cm),
                ("type", "LST", 5.0 * u.m),
                ("type", "MST", 2.5 * u.m),
                ("id", 1, 3.5 * u.m),
                ("id", 5, 1.5 * u.m),
            ]
        )
    }

    settings = Settings.model_validate(data)  # json.dumps(data))
    print(settings.option)
    print(settings.model_dump_json())

    # Test the behavior
    assert settings.option.get(type="LST", id=3) == 5.0 * u.m  # type has match
    assert settings.option.get(type="ABC", id=1) == 3.5 * u.m  # id has match
    assert settings.option.get(type="ABC", id=99) == 0.5 * u.cm  # type match on *
    assert (
        settings.option.get(type="MST", id=3) == 2.5 * u.m
    )  # id has precedence over type
    assert (
        settings.option.get(type="MST", id=5) == 1.5 * u.m
    )  # id has precedence over type
