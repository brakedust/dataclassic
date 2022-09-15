.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black



=======================================
dataclassic
=======================================

*Currently in alpha**

A Python library for makeing `dataclass`es even more awesome.  dataclassic brings

    * Type coercion and validation through an automatic `__post_init__` function
    * A nosql style document store built on SQLITE
    * Ability to define a CLI for a program using `dataclasses`
    * [Coming soon] tables of dataclass objects


Type Coercion and Validation
==============================




(No)SQLITE Document Store
==============================


Define your CLI with `dataclass`es
===================================


Tables of `dataclass`es
==================================


Examples
==================================

.. code:: Python

    from dataclassic.doc_store import DocumentStore, Database
    from dataclassic.dataclasses import dataclass, field, DataClassicValidationError

    db = Database("sqlite:///:memory:")


    def RealShapeValidator(shape):
        return shape.sides > 2

    @dataclass
    class Shape:
        ID: str = field(converter=str)
        sides: int = field(converter=int, validator=RealShapeValidator)
        color: str = field(converter=str)



Contributing
===============



Please use `black` to format your code.

