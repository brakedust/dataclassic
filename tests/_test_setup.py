import unittest

from dataclassic import (
    Database,
    DataClassicValidationError,
    DocumentStore,
    dataclass,
    field,
)
from tests._test_tools import Raises

# from dataclasses import dataclass


db = Database("sqlite:///:memory:")


def RealShapeValidator(shape):
    return shape.sides > 2


@dataclass
class Shape:
    ID: str = field(converter=str)
    sides: int = field(converter=int, validator=RealShapeValidator)
    color: str = field(converter=str)


hexagon = Shape(ID="hexagaon", sides=6, color="green")
triangle = Shape(ID="triangle", sides="3", color="red")
rectangle = Shape(ID="rectangle", sides=4, color="blue")
pentagon = Shape(ID="pentagon", sides=5, color="red")
