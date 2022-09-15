"""
=================
dataclassic.dataclasses
=================

The dataclassic.dataclasses module provides a set of dataclass extensions via decorators.
These extenstions cover things like
    * Data validation and coercion
    * Doc strings for dataclass fields
    * Ability to instantiate object graphs from json and vice-versa

The data validation and coercion are implemented as a decorator named "post_init_coercion".
This decorator adds a __post_init__ function to the decorated class.  When a dataclass
instance is initialized it calls a __post_init__ method if it is defined.  The details
of the field are given using an extended version of the *field* function from dataclasses.
Additional information on each field is stored in the metadata entry of the field.



    from dataclassic.dataclasses import dataclass, field, DataClassicValidationError


    def RealShapeValidator(shape):
        return shape.sides > 2

    @dataclass
    class Shape:
        ID: str = field(converter=str)
        sides: int = field(
            converter=int,
            validator=RealShapeValidator,
            doc="Number of sides in the shape"
        )
        color: str = field(converter=str)


    hexagon = Shape(
        ID="hexagaon",
        sides=6,
        color="green"
    )
    triangle = Shape(
        ID="triangle",
        sides='3',
        color="red"
    )
    rectangle = Shape(ID="rectangle", sides=4, color="blue")
    pentagon = Shape(ID="pentagon", sides=5, color='red')

"""

import copy
import typing
from dataclasses import MISSING, dataclass as dataclass_
from dataclasses import field as field_
from dataclasses import fields, is_dataclass, Field
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from uuid import UUID

from functools import wraps

__all__ = [
    "post_init_coersion",
    "is_dataclass",
    "field",
    "fields",
    "asdict",
    "Unset",
    "MISSING",
    "dataclass",
]


class UnsetType:
    def __call__(self):
        return self

    def __repr__(self):
        return "<UNSET>"

    def __str__(self):
        return ""

    def __eq__(self, other):
        return isinstance(other, UnsetType)

    def __str__(self):
        return ""


Unset = UnsetType()


@wraps(field_)
def field(
    *,
    default=MISSING,
    default_factory=MISSING,
    repr=True,
    hash=None,
    init=True,
    compare=True,
    metadata=None,
    converter=None,
    validator=None,
    doc=None,
    exclude_from_tree=False,
    nargs=1,
) -> Field:

    metadata_ = {}  # if metadata is None else metadata
    if metadata:
        metadata_.update(metadata)
    metadata_["converter"] = converter
    metadata_["validator"] = validator
    metadata_["doc"] = doc
    metadata_["exclude_from_tree"] = exclude_from_tree
    metadata_["nargs"] = nargs

    return field_(
        default=default,
        default_factory=default_factory,
        repr=repr,
        hash=hash,
        init=init,
        compare=compare,
        metadata=metadata_,
    )


class DataClassicValidationError(Exception):
    pass


def is_generic_container(cls):

    if hasattr(cls, "__origin__"):
        return True

    if isinstance(cls, typing._GenericAlias):
        return True


def post_init_coersion(cls):
    def __post_init__(self):

        # print('running post init')
        for f in fields(self):
            current_value = getattr(self, f.name)
            if "converter" in f.metadata and f.metadata["converter"]:
                # if a converter funciton is defined run it
                if current_value is Unset:
                    continue

                current_value = f.metadata["converter"](current_value)
                setattr(self, f.name, current_value)

            if "validator" in f.metadata and f.metadata["validator"]:
                # if a validator function is defined, then run it
                if not f.metadata["validator"](self):
                    raise DataClassicValidationError(
                        f"Validation for {cls.__name__}.{f.name} failed."
                    )

            elif is_dataclass(f.type):
                if isinstance(current_value, dict):
                    setattr(self, f.name, f.type(**current_value))
                elif not isinstance(current_value, f.type):
                    raise ValueError(
                        f"Wrong item type: {type(current_value)}. Expected {f.type}"
                    )

            elif is_generic_container(f.type):

                subtype = f.type.__args__[-1]
                if f.type.__origin__ is list:
                    # handle generic lists
                    if len(current_value) == 0:
                        continue
                    elif isinstance(current_value[0], dict):
                        # print(current_value)
                        # print(subtype)
                        setattr(
                            self,
                            f.name,
                            [subtype(**item_data) for item_data in current_value],
                        )
                    else:
                        try:
                            setattr(
                                self,
                                f.name,
                                [
                                    item_data
                                    if isinstance(item_data, subtype)
                                    else subtype(item_data)
                                    for item_data in current_value
                                ],
                            )
                        except Exception as ex:
                            raise Exception(
                                f"Error parsing item in field [{f.name}] - {ex.args[0]}\n"
                                + f"All items must be of type [{subtype.__name__}] - items are "
                                + f"{ex.__traceback__.tb_frame.f_locals['current_value']}"
                            )

                elif f.type.__origin__ is dict:

                    if len(current_value) == 0:
                        continue

                    first_key = next(iter(current_value))
                    if isinstance(current_value[first_key], dict):
                        # print(current_value)
                        setattr(
                            self,
                            f.name,
                            {
                                key: subtype(**item_data)
                                for key, item_data in current_value.items()
                            },
                        )
                    else:
                        setattr(
                            self,
                            f.name,
                            {
                                key: item_data
                                if isinstance(item_data, subtype)
                                else subtype(item_data)
                                for key, item_data in current_value.items()
                            },
                        )

    setattr(cls, "__post_init__", __post_init__)

    # cls = dataclass(cls)

    return cls


@wraps(dataclass_)
def dataclass(cls, **kwargs):
    cls = post_init_coersion(cls)
    return dataclass_(cls, **kwargs)


def get_schema(cls):
    """
    Returns the JSON schema for this object type
    """
    d = {
        "description": cls.__doc__.replace("\n", " ").strip() if cls.__doc__ else "",
        "title": cls.__name__,
        "properties": {},
    }

    for _field in fields(cls):
        name = _field.name
        t = _field.type
        # for name, t in self._fields.items():
        d["properties"][name] = {}
        d["properties"][name]["type"] = JSON_SCHEMA_TYPES.get(t, t.__name__)
        if "doc" in _field.metadata:
            d["properties"][name]["description"] = (
                _field.metadata["doc"].replace("\n", " ").strip()
            )

        fmt = JSON_SCHEMA_FORMATS.get(t.dtype)
        if fmt is not None:
            d["properties"][name]["format"] = fmt

    return d
    # setattr(cls, "__post_init__", __post_init__)
    # # cls.load_yaml = load_yaml
    # # cls.save_yaml = save_yaml

    # cls = dataclass(cls)

    # return cls


def asdict(obj, *, dict_factory=dict, skip_fields=None):
    if skip_fields is None:
        skip_fields = tuple()
    if not is_dataclass(obj):
        raise TypeError("asdict() should be called on dataclass instances")
    retval = _asdict_inner(obj, dict_factory, skip_fields=skip_fields)
    return retval


def _asdict_inner(obj, dict_factory, skip_fields):
    if is_dataclass(obj):
        result = []
        for f in fields(obj):
            if f.name in skip_fields:
                continue
            val = getattr(obj, f.name)
            if val is Unset:
                continue
            value = _asdict_inner(val, dict_factory, skip_fields)
            result.append((f.name, value))
        return dict_factory(result)
    elif isinstance(obj, tuple) and hasattr(obj, "_fields"):
        return type(obj)(*[_asdict_inner(v, dict_factory, skip_fields) for v in obj])
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_asdict_inner(v, dict_factory, skip_fields) for v in obj)
    elif isinstance(obj, dict):
        return type(obj)(
            (
                _asdict_inner(k, dict_factory, skip_fields),
                _asdict_inner(v, dict_factory, skip_fields),
            )
            for k, v in obj.items()
            if v is not None and v is not Unset
        )
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, date):
        return str(obj)
    else:
        return copy.deepcopy(obj)


JSON_SCHEMA_TYPES = {
    int: "integer",
    str: "string",
    float: "float",
    bool: "boolean",
    list: "array",
    None: "null",
    dict: "object",
    UUID: "string",
    datetime: "string",
    "date": "string",
    timedelta: "string",
    Path: "string",
}

JSON_SCHEMA_FORMATS = {UUID: "UUID", datetime: "date-time"}


def to_json(dc_obj):
    from json import dumps

    return dumps(asdict(dc_obj))


def from_json(json_string: str, dtype):

    from json import loads

    data = loads(json_string)
    return dtype(**data)
