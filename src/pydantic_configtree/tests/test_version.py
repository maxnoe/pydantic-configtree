from packaging.version import Version


def test_version():
    from pydantic_configtree import __version__

    parsed = Version(__version__)
    assert parsed > Version("0.0.0dev0")
