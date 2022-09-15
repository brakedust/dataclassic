from copy import deepcopy
from dataclassic.dataclasses import asdict
from .tables import DataTable
from .pyarray import pyndarray

from dataclassic.pyarray import (
    array,
    transpose,
    append,
    delete,
    pyndarray,
    min,
    max,
    mean,
    sum,
    var,
    std,
)

array_type = pyndarray
array_copy = deepcopy

SIG_DIGIT_COUNT = 6


def sigdigits(x, n, format_code="g"):
    """
    Rounds a number to the specified number of significant digits
    """
    try:
        fstring = "{0:1." + str(n - 1) + format_code + "}"
        return float(fstring.format(x))
    except ValueError:
        return str(x)


class DataClassTable:
    def __init__(self, data: list, name: str = None, dtype: type = None):

        self.name = name
        self.data = data

        if dtype is None:
            self.dtype = type(self._data[0])
        else:
            self.dtype = dtype

        self.metadata = {}

    @property
    def columns(self):

        return list(self.dtype.__dataclass_fields__.keys())

    @property
    def index(self):
        return list(range(len(self.data)))

    def __getitem__(self, args):
        """
        Gets on or more columns
        :param args:
        :return:
        """
        # if isinstance(args, slice):
        #    return DataTable(self.data[args], columns=self.columns)
        # if isinstance(args, int):
        #    return DataTable([self.data[args]], columns=self.columns)
        # else:
        return self.get_column(args)

    def get_column(self, col):

        return [getattr(x, col, None) for x in self.data]

    def __repr__(self):

        if self.name not in ("", None):
            retval = "Name: {0}\n".format(self.name)
        else:
            retval = ""

        if len(self.metadata) > 0:
            for k in self.metadata:
                retval += "{0}: {1}\n".format(k, self.metadata[k])

        columns = [str(c) for c in self.columns]
        colwidth1 = [len(cn) for cn in columns]
        colwidth2 = []
        for colname in self.columns:
            colwidth2.append(max([len(str(sigdigits(x, 5))) for x in self[colname]]))

        colwidth = array([colwidth1, colwidth2]).max(axis=0)
        colwidth = [cw + 2 for cw in colwidth]

        lindex = max([len(str(ind)) for ind in self.index])

        retval += " " * lindex
        for icol, item in enumerate(columns):
            fmt = "{0:>" + str(colwidth[icol]) + "}"
            retval += fmt.format(item)
        retval += "\n"

        # retval += "-" * colwidth * len(self.columns) + '\n'
        for irow, row in enumerate(self.data):
            fmt = "{0:>" + str(lindex) + "}"
            retval += fmt.format(self.index[irow])

            for icol, item in enumerate(asdict(row).values()):
                fmt = "{0:>" + str(colwidth[icol]) + "}"
                if isinstance(item, int):
                    retval += fmt.format(item)
                else:
                    retval += fmt.format(sigdigits(item, SIG_DIGIT_COUNT))
            retval += "\n"

        return retval


# class ColumnView:
#     def __init__(self, table: DataClassTable) -> pyndarray | DataTable:
#         self.table: DataClassTable = table

#     def __getitem__(self, columns):

#         if not isinstance(columns, (list, set, tuple)):
#             columns = [columns]

#         colnums = []
#         colnames = []

#         for col in columns:
#             if isinstance(col, str):
#                 colnames.append(col)
#                 colnums.append(self.table.columns.index(col))

#             elif isinstance(col, int):
#                 colnums.append(col)
#                 colnames.append(self.table.columns[col])
#             else:
#                 raise TypeError("col must be a str or an int - {0}".format(col))

#         if len(columns) > 1:
#             new_data_set = self.table.data[:, colnums]
#             return DataTable(new_data_set, columns=colnames)
#         else:
#             new_data_set = self.table.data[:, colnums[0]]

#             return new_data_set

#     def __setitem__(self, column, values=None, fillval=0):

#         # def set_column(self, column, values=None, fillval=0):
#         """
#         Sets the values for a given column
#         :param column:
#         :param values:
#         :return:
#         """

#         if values is None:
#             values = array([fillval] * len(self), dtype=object)

#         if not isinstance(values, array_type):
#             values = array(values)

#         if column in self.table.columns:
#             cindex = self.table.columns.index(column)

#             self.table.data[:, cindex] = values  # .reshape(len(values))
