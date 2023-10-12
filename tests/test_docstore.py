import pytest

from dataclassic import Database, DocumentStore, Find, is_dataclass
from tests._test_setup import Shape, hexagon, pentagon, rectangle, triangle


# class TestPostInit(TestCase):
def setUp():
    db = Database("sqlite:///:memory:")
    shapes = DocumentStore("shapes", db, False, dtype=Shape)
    chairs = DocumentStore("chairs", db, False)
    return db, shapes, chairs


def tearDown(self) -> None:
    pass


def test_shapes():
    db, shapes, chairs = setUp()

    shapes.insert_many((triangle, rectangle, pentagon, hexagon))

    res = shapes.find(echo_sql=True)
    assert len(res) == 4
    assert isinstance(res[0], Shape)
    assert is_dataclass(res[0])


def test_find_by_attribute():
    db, shapes, chairs = setUp()

    shapes.insert_many((triangle, rectangle, pentagon, hexagon))

    res = shapes.find("@sides > ?", (3,), echo_sql=True, dtype=Shape)

    assert len(res) == 3

    assert isinstance(res[0], Shape)


def test_find2_by_attribute():
    db, shapes, chairs = setUp()

    shapes.insert_many((triangle, rectangle, pentagon, hexagon))

    res = shapes.find2({"$gt": {"sides": 3}}, echo_sql=True, dtype=Shape)

    assert len(res) == 3

    assert isinstance(res[0], Shape)


def test_FindClass():
    db, shapes, chairs = setUp()

    f = Find(Shape).where("sides") > 3
    print(f)


if __name__ == "__main__":
    pytest()
