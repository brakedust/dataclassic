import pytest

from dataclassic import DataTable, sample_table


def test_sort():
    t1 = sample_table()
    print(t1)

    t2 = sample_table()
    t2["b"] = [100 - i for i in range(9)]

    t2.columns = ["a", "bigger", "same"]
    t2["same"] = [x + 10 for x in t2["same"]]
    t2 = t2.sort("bigger")
    for i in range(len(t2) - 1):
        assert t2["bigger"][i] < t2["bigger"][i + 1]

    t2 = t2.sort("bigger", ascending=False)
    for i in range(len(t2) - 1):
        assert t2["bigger"][i] > t2["bigger"][i + 1]


def test_join():
    t1 = sample_table()
    print(t1)

    t2 = sample_table()
    new_column = [100 - i for i in range(9)]
    t2["b"] = new_column

    t2.columns = ["a", "bigger", "same"]
    t2["same"] = [x + 10 for x in t2["same"]]
    t2 = t2.sort("bigger")

    t3 = t1.join(t2, on="a")

    for i in range(len(t3)):
        assert t3["bigger"][i] == new_column[i]

    assert len(t3.columns) == (len(t1.columns) + len(t2.columns) - 1)


@pytest.mark.skip("feature not working")
def test_to_excel():
    t1 = sample_table()
    t1.to_excel("test.xlsx")
