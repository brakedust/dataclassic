from dataclassic.doc_store import DocumentStore, Database
from dataclassic.dataclasses import (
    dataclass,
    field,
    DataClassicValidationError,
    to_json,
    from_json,
)

# The validator gets the instance of the class
def RealShapeValidator(shape: "Shape"):
    "A shape must have at least three sides"
    return shape.sides > 2


@dataclass
class Shape:
    ID: str = field(converter=str)  # we can add an extra convert argument here
    sides: int = field(
        converter=int, validator=RealShapeValidator
    )  # we can also add a validator
    color: str = field(converter=str)


from dataclassic.dctables import DataClassTable

hexagon = Shape(ID="hexagon", sides=6, color="green")
triangle = Shape(
    ID="triangle", sides="3", color="red"
)  # type coercion will work here too.
rectangle = Shape(ID="rectangle", sides=4, color="blue")
pentagon = Shape(ID="pentagon", sides=5, color="red")

data = [triangle, rectangle, pentagon, hexagon]

t = DataClassTable(data, name="Shapes", dtype=Shape)

print(repr(t))