from abc import abstractmethod

import pytest
from pydantic import ValidationError

from pydantic_settings_ctapipe import Config, Configurable


def test_configurable_basic():
    class Foo(Configurable):
        class __config__(Config):
            option: int = 1

    foo = Foo()
    assert foo.config.option == 1

    config = Foo.__config__(option=2)
    foo = Foo(config=config)
    assert foo.config.option == 2

    with pytest.raises(ValidationError):
        config = Foo.__config__(option=2.5)


def test_configurable_nested():
    class Sub(Configurable):
        class __config__(Config):
            value: float = 2.0

    class Parent(Configurable):
        class __config__(Config):
            sub: Sub.__config__ = Sub.__config__()
            option: str = "foo"

        def __init__(self, config=None, parent=None):
            super().__init__(config=config, parent=parent)
            self.sub = Sub(config=self.config.sub, parent=self)

    # check with default config
    parent = Parent()
    # check config of the parent
    assert parent.config.option == "foo"
    assert parent.config.sub.value == 2.0

    # check it's correctly passed through
    assert parent.sub.config.value == 2.0

    # check parent relationship
    assert parent.sub.parent is parent

    # check with passed in config
    config = Parent.__config__(option="bar", sub=Sub.__config__(value=3.0))
    parent = Parent(config=config)
    assert parent.config.option == "bar"
    assert parent.config.sub.value == 3.0
    assert parent.sub.config.value == 3.0


def test_configurable_subclasses():
    """Test for the mechanism of configuring subclasses of an interface."""

    class Interface(Configurable):
        @abstractmethod
        def do_something(self):
            pass

    class Foo(Interface):
        class __config__(Config):
            value: int = 0

        def do_something(self):
            return self.config.value

    class Bar(Interface):
        class __config__(Config):
            value: int = 0

        def do_something(self):
            return self.config.value + 1

    class Component(Configurable):
        class __config__(Config):
            interface: Interface.configurable_subclasses() | None = None

        def __init__(self, config=None, parent=None):
            super().__init__(config=config, parent=parent)
            self.interface = Interface.from_config(self.config.interface, parent=self)

    assert len(Interface.non_abstract_subclasses()) == 2
    base = "pydantic_settings_ctapipe.tests.test_configurable.test_configurable_subclasses.<locals>"
    assert Interface.non_abstract_subclasses() == {
        f"{base}.Foo": Foo,
        f"{base}.Bar": Bar,
    }

    comp = Component()
    assert comp.interface is None

    config = Component.__config__(interface=Bar.__config__(value=1))
    component = Component(config=config)
    assert isinstance(component.interface, Bar)

    config = Component.__config__.model_validate(
        {"interface": {"cls": "Foo", "value": 3}}
    )
    component = Component(config=config)
    assert isinstance(component.interface, Foo)
    assert component.interface.config.value == 3.0
