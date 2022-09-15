import unittest
from tests._test_tools import Raises

# from dataclasses import dataclass
# from dataclassic.doc_store import DocumentStore, Database
from dataclassic import dataclass, field, DataClassicValidationError

from tests._test_setup import Shape, db, hexagon, triangle


@dataclass
class WeirdChair:

    top: Shape
    bottom: Shape


class WeirdChairTest(unittest.TestCase):
    def test_bad_chair(self):

        with Raises(DataClassicValidationError):
            bogus_shape = Shape(ID="madeUpAgon", sides=-2, color="yellow")

    def test_good_chair(self):
        chair = WeirdChair(top=hexagon, bottom=triangle)

    def test_coercion(self):

        my_shape = Shape(ID="madeUpAgon", sides="8", color="yellow")

        self.assertEqual(8, my_shape.sides)

    def test_default_coercion(self):
        @dataclass
        class Thing:
            a: float = None
            b: int = "11"

        t = Thing("10.5", "11")

        self.assertEqual(10.5, t.a)
        self.assertEqual(11, t.b)
