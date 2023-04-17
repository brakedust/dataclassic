from dataclassic.pyarray import pyndarray
import pytest


def test_things():
    d = pyndarray([[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]])

    d1 = d.transpose()

    assert d1[:, 0] == pyndarray([1, 2, 3])
