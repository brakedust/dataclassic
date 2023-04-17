from dataclasses import is_dataclass
import unittest
from dataclassic.doc_store import DocumentStore, Database, Find
from unittest import TestCase

from tests._test_setup import Shape, triangle, rectangle, pentagon, hexagon


class TestPostInit(TestCase):
    def setUp(self):
        db = Database("sqlite:///:memory:")
        shapes = DocumentStore("shapes", db, False, dtype=Shape)
        chairs = DocumentStore("chairs", db, False)
        return db, shapes, chairs

    def tearDown(self) -> None:
        pass

    def test_shapes(self):

        db, shapes, chairs = self.setUp()

        shapes.insert_many((triangle, rectangle, pentagon, hexagon))

        res = shapes.find(echo_sql=True)
        assert len(res) == 4
        assert isinstance(res[0], Shape)
        assert is_dataclass(res[0])

    def test_find_by_attribute(self):

        db, shapes, chairs = self.setUp()

        shapes.insert_many((triangle, rectangle, pentagon, hexagon))

        res = shapes.find("@sides > ?", (3,), echo_sql=True, dtype=Shape)

        assert len(res) == 3

        assert isinstance(res[0], Shape)

    def test_find2_by_attribute(self):

        db, shapes, chairs = self.setUp()

        shapes.insert_many((triangle, rectangle, pentagon, hexagon))

        res = shapes.find2({"$gt": {"sides": 3}}, echo_sql=True, dtype=Shape)

        assert len(res) == 3

        assert isinstance(res[0], Shape)

    def test_FindClass(self):

        db, shapes, chairs = self.setUp()

        f = Find(Shape).where("sides") > 3
        print(f)


if __name__ == "__main__":
    unittest.main()
