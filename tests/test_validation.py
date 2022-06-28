import unittest
from tests._test_tools import Raises

# from dataclasses import dataclass
from dataclassic.doc_store import DocumentStore, Database
from dataclassic import dataclass, field, KoalaValidationError

from tests._test_setup import Shape, db, hexagon, triangle


@dataclass
class WeirdChair:

    top: Shape
    bottom: Shape


class WeirdChairTest(unittest.TestCase):
    def test_bad_chair(self):

        with Raises(KoalaValidationError):
            bogus_shape = Shape(ID="madeUpAgon", sides=-2, color="yellow")

    def test_good_chair(self):
        chair = WeirdChair(top=hexagon, bottom=triangle)

    def test_coercion(self):

        my_shape = Shape(ID="madeUpAgon", sides="8", color="yellow")

        self.assertEqual(8, my_shape.sides)
