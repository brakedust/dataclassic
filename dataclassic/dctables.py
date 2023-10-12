from copy import deepcopy
from typing import Callable

from dataclassic.dataclasses_ext import asdict
from dataclassic.pyarray import array, pyndarray, slice_to_range
from dataclassic.tables import DataTable

from .pyarray import pyndarray
from .tables import DataTable

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
        self.history = []

        if dtype is None:
            self.dtype = type(self.data[0])
        else:
            self.dtype = dtype

        self.metadata = {}

        self.loc = TableView(self)

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
        if isinstance(args, (list, tuple)):
            for c in args:
                if c not in self.columns:
                    raise KeyError(f"Column '{c}' not found in Columns: {self.columns}")
            return DataTable.from_column_dict({c: self.get_column(c) for c in args})
        elif isinstance(args, str):
            return self.get_column(args)

    def get_column(self, col) -> list:
        return [getattr(x, col, None) for x in self.data]

    def __repr__(self) -> str:
        if self.name not in ("", None):
            retval = "Name: {0}\n".format(self.name)
        else:
            retval = ""

        if len(self.metadata) > 0:
            for k in self.metadata:
                retval += "{0}: {1}\n".format(k, self.metadata[k])

        # get width of column names
        columns = [str(c) for c in self.columns]
        colwidth1 = [len(cn) for cn in columns]

        # get width of column values
        colwidth2 = []
        for colname in self.columns:
            colwidth2.append(max([len(str(sigdigits(x, 5))) for x in self[colname]]))

        # compute final width of columns for display
        colwidth = array([colwidth1, colwidth2]).max(axis=0)
        colwidth = [cw + 2 for cw in colwidth]

        lindex = max([len(str(ind)) for ind in self.index])

        retval += " " * lindex
        for width, item in zip(colwidth, columns):
            fmt = f"{{0:>{width}}}"
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

    def __len__(self):
        return len(self.data)

    def where(self, predicate: Callable):
        """
        Returns a new DataClassTable where the rows have been filtered
        """
        return DataClassTable(
            [row for row in self.data if predicate(row)],
            dtype=self.dtype,
            name=self.name,
        )

    def head(self, n=5):
        newtable = DataClassTable(
            data=self.data[:n],
            dtype=self.dtype,
            name=self.name,
        )
        newtable.history.append(f".head(n={n})")
        return newtable


class TableView:
    def __init__(self, table: DataClassTable):
        self.table: DataClassTable = table

    def __getitem__(self, args):
        if len(args) == 0 or len(args) > 2:
            return None
        elif (len(args)) == 1:
            irow = args[0]
            icol = None
        elif len(args) == 2:
            irow, icol = args

        if isinstance(irow, slice):
            irow = slice_to_range(irow, self.table.data, 0)
        if isinstance(icol, slice):
            icol = slice_to_range(icol, self.table.columns, 0)

        if icol is None:
            if irow is None:
                return None

            elif isinstance(irow, int):
                return self.table.data[irow]

            elif isinstance(irow, (list, tuple, set, range)):
                return [d for i, d in self.table.data if i in irow]
        elif isinstance(icol, int):
            colname = self.table.columns[icol]
            if irow is None:
                return self.table.get_column(colname)
            elif isinstance(irow, int):
                return getattr(self.table.data[irow], colname)
            elif isinstance(irow, (list, tuple, set, range)):
                return [getattr(self.table.data[jrow], colname) for jrow in irow]

        elif isinstance(icol, (list, tuple, set, range)):
            colnames = [self.table.columns[jcol] for jcol in icol]
            if irow is None:
                return [self.table.get_column(cn) for cn in colnames]
            elif isinstance(irow, int):
                return [getattr(self.table.data[irow], cn) for cn in colnames]
            elif isinstance(irow, (list, tuple, set, range)):
                return [
                    [getattr(self.table.data[jrow], cn) for cn in colnames]
                    for jrow in irow
                ]


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
