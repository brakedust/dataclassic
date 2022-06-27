from koala import pyarray


def test_things():

    d = pyarray.pyndarray([[1,2,3],[4,5,6],[7,8,9],[10,11,12]])

    d.transpose()