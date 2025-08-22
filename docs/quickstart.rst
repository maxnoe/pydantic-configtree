Quickstart
==========

This module provides a way to build trees of configurable objects using `pydantic.BaseModel` for the
configuration.


Let's start with a simple class that is configurable:

.. code::

   >>> from pydantic_settings_ctapipe import Config, Configurable

   >>> class Foo(Configurable):
   ...
   ...     class __config__(Config):
   ...          option: int = 2
   ...
   ...     def do_stuff(self):
   ...         return self.config.option**2


   >>> f = Foo()
   >>> f.do_stuff()
   4

   >>> config = Foo.__config__(option=5)
   >>> f = Foo(config=config)
   >>> f.do_stuff()
   25


To build a tree, we include this class in a second one, defining the ``__config__`` class:
to have a field for ``Foo.__config__`` and passing it to our ``Foo`` instance in ``__init__``.
We pass ``parent=self`` and ``name="foo"`` to build the tree also in the other direction.

At the moment is mainly for logging, see :ref:`logging`.

.. code::

   >>> class Bar(Configurable):
   ...     class __config__(Config):
   ...         foo: Foo.__config__ = Foo.__config__()
   ...
   ...     def __init__(self, config=None, parent=None, name=None):
   ...         super().__init__(config=config, parent=parent, name=name)
   ...         self.foo = Foo(config=self.config.foo, parent=self, name="foo")
   ...
   ...     def do_stuff(self):
   ...         return self.foo.do_stuff() + 1
   >>> bar = Bar()
   >>> bar.do_stuff()
   5
   >>> bar = Bar(config={"foo": {"option": 5}})
   >>> bar.do_stuff()
   26


Polymorphism
------------

``Configurable`` implements logic for selecting a specific implementation
of an interface class via the configuration. This is achieved by injecting
a ``cls`` string option that allows the class name and the fully qualified name.
This allows differentiation between multiple pydantic models that would
be compatible with configuration.

.. code::

   >>> from abc import abstractmethod

   >>> class BinaryOperation(Configurable):
   ...
   ...     @abstractmethod
   ...     def compute(self, arg1, arg2):
   ...         pass
   ...
   >>> class Add(BinaryOperation):
   ...
   ...     def compute(self, arg1, arg2):
   ...         return arg1 + arg2
   ...
   >>> class Multiply(BinaryOperation):
   ...
   ...     def compute(self, arg1, arg2):
   ...         return arg1 * arg2
   ...
   >>> op = BinaryOperation.from_config({"cls": "Add"})
   >>> op.compute(3, 1)
   4
   >>> op = BinaryOperation.from_config({"cls": "Multiply"})
   >>> op.compute(3, 1)
   3


Which can be used in a parent class like this:

.. code::

   >>> class Example(Configurable):
   ...     class __config__(Config):
   ...         op: BinaryOperation.configurable_subclasses() = Add.__config__()
   ...
   ...     def __init__(self, config=None, parent=None, name=None):
   ...         super().__init__(config=config, parent=parent, name=name)
   ...         self.op = BinaryOperation.from_config(config=self.config.op, parent=self, name="op")

   >>> example = Example()
   >>> example.op.compute(1, 1)
   2
   >>> example = Example(config={"op": {"cls": "Multiply"}})
   >>> example.op.compute(1, 1)
   1



.. _logging:
Logging
-------

Each configurable has a `logging.Logger` instance, with the hierarchy of loggers reflecting the hierarchy of
the configuration tree:

.. code::

   >>> b = Bar()
   >>> b.log
   <Logger __main__.Bar (INFO)>
   >>> b.foo.log
   <Logger __main__.Bar.foo (INFO)>
