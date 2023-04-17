import math
import copy
from itertools import chain, product
from functools import partial
import itertools

# def multirange_next(value_counts, counters):

#     if not value_counts:
#         return None

#     i = len(value_counts) - 1
#     while i > -1:

#         if counters[i] < value_counts[i]-1:
#             counters[i] += 1

#             return counters
#         else:
#             counters[i] = 0
#             i -= 1

# raise StopIteration


def multirange(*value_counts):
    """
    An generator that yields nested range values.  Values always start from 0 and
    increment by 1.

    Example:
        >>> for i,j in multirange(2,3):
        >>> print(i,j)
        0 0
        0 1
        0 2
        1 0
        1 1
        1 2
    """

    return (vals for vals in itertools.product(*[range(c) for c in value_counts]))
    # if len(value_counts) == 0:
    #     raise StopIteration


0
# counters = [0] * len(value_counts)
# while counters:
#     yield counters
#     counters = multirange_next(value_counts, counters)


def slice_to_range(myslice, myobj, idim=0):
    """
    Turns a slice object in an index iterator for myobj
    :param myslice:
    :param myobj:
    :return:
    """
    if isinstance(myslice, int):
        return [myslice]
    elif isinstance(myslice, slice):
        # start = 0 if myslice.start is None else myslice.start
        # stop = len(myobj) if myslice.stop is None else myslice.stop
        # stop = min(stop, len(myobj))
        # step = 1 if myslice.step is None else myslice.step
        obj_to_slice = myobj
        for dim in range(1, idim + 1):
            obj_to_slice = obj_to_slice[0]
        myrange = range(*myslice.indices(len(obj_to_slice)))
        return myrange
    elif isinstance(myslice, (list, tuple, set)):
        return myslice


class NANType:
    """
    A not a number type.  This should not be used directly.  The module instance NAN should be used.
    """

    instance = None

    def __init__(self):
        if NANType.instance is None:
            NANType.instance = self
        else:
            raise TypeError("You cannot create a NANType instance.\nUse the NAN object")

    def __str__(self):
        return "NaN"

    def __repr__(self):
        return "NAN"

    def __eq__(self, other):
        return False

    def __ne__(self, other):
        return True

    def __lt__(self, other):
        return False

    def __gt__(self, other):
        return False

    def __lte__(self, other):
        return False

    def __gte__(self, other):
        return False

    def __len__(self):
        return 0


if NANType.instance is None:
    NANType()

NAN = NANType.instance
NaN = NAN
nan = NAN


def isnan(x):
    return x in (NAN, None)


def eq(x, y):
    return x == y


def ne(x, y):
    return x != y


def gt(x, y):
    return x > y


def lt(x, y):
    return x < y


def gte(x, y):
    return x >= y


def lte(x, y):
    return x <= y


def array(x, *args, **kwargs):
    if not isinstance(x, pyndarray):
        return pyndarray(data=x)
    else:
        return x


class pyndarray:
    def __init__(self, data=None, shape=None, fill=0.0, allow_nan=True, name=None):
        """

        :type data: pyndarray, list, number
        :param data:
        :param shape:
        :param fill:
        :param allow_nan:
        :return:
        """
        self.shape = shape
        self.ndim = None
        self.allow_nan = allow_nan
        self._data = None
        self.name = name

        if data is None and shape is not None:
            self.ndim = len(self.shape)
            self._data = []

            self._data = [fill] * self.shape[-1]
            if self.ndim > 1:
                for idim in range(self.ndim - 2, -1, -1):
                    self._data = [
                        copy.deepcopy(self._data) for ix in range(self.shape[idim])
                    ]

        elif isinstance(data, pyndarray):
            self._data = copy.deepcopy(data)
            self.shape = copy.copy(data.shape)
            self.ndim = len(self.shape)

        elif isinstance(data, (float, int, str)):
            self._data = [data]
            self.shape = (1,)
            self.ndim = 1

        elif data is not None:
            if hasattr(data, "tolist"):
                self._data = data.tolist()
            else:
                self._data = copy.deepcopy(data)
            self.shape = []
            subarray = self._data
            while isinstance(subarray, (list, pyndarray)):
                self.shape.append(len(subarray))
                subarray = subarray[0]
            self.shape = tuple(self.shape)
            self.ndim = len(self.shape)
        else:
            raise ValueError(
                "You must specify either data for shape for creating a {0}".format(
                    type(self)
                )
            )

    def mapfill(self, mapfunc):
        """
        Fills the array calling mapfunc for each item.  The mapfunc should accept the value
        of the array, followed by the indexes of the items.  It is called like:
            mapfunc(self[indexes], *indexes)
        Where indexes is a tuple of the index values.

        :param mapfunc: a callable function
        :return: A new array
        """
        newobj = copy.deepcopy(self)

        for indexes in multirange(*self.shape):
            newobj[indexes] = mapfunc(self[indexes], *indexes)

        return newobj

    def index_fill(self):
        """
        Fills a copy of the array with a number that looks like its index.
        If ndim == 3 then the number is i*100 + j*10 + k
        :return:
        """

        def genindexnum(v, *args):
            return sum([10**i * a for i, a in enumerate(reversed(args))])

        return self.mapfill(genindexnum)

    def random_fill(self):
        """
        Fills a copy of the array with uniform random numbers
        :return:
        """
        import random

        def fillfunc(v, *args):
            return random.random()

        return self.mapfill(fillfunc)

    # @property
    # def ndim(self):
    #    return 2

    # @property
    # def shape(self):
    #    return (self.m, self.n)

    def reshape(self, new_shape, fill=0):
        """
        Reshapes the array.
        :param new_shape: *args - the new shape of the array
        :param fill: If the new array will have more elements, fill the new elements with this value
        :return:
        """

        newobj = pyndarray(shape=new_shape, fill=fill)

        flat_data = self.reduce_dimension()
        idata = 0
        try:
            for indexes in multirange(*new_shape):
                newobj[indexes] = flat_data[idata]
                idata += 1
        except IndexError:
            pass

        return newobj

    def where(self, mask):
        if self.ndim == 1:
            data = [self[i] for i in range(self.shape[0]) if mask[i]]
        elif self.ndim == 2:
            data = [
                [self[i, j] for j in range(self.shape[-1]) if mask[i, j]]
                for i in range(self.shape[-2])
            ]
        elif self.ndim == 3:
            data = [
                [
                    [self[i, j, k] for k in range(self.shape[-1]) if mask[i, j]]
                    for j in range(self.shape[-2])
                ]
                for i in range(self.shape[-3])
            ]
        elif self.ndim == 4:
            data = [
                [
                    [
                        [self[h, i, j, k] for k in range(self.shape[-1]) if mask[i, j]]
                        for j in range(self.shape[-2])
                    ]
                    for i in range(self.shape[-3])
                ]
                for h in range(self.shape[-4])
            ]
        a = pyndarray(data=data, allow_nan=self.allow_nan)

        return a

    def reduce_dimension(self):
        """
        Reduces this 2d array to a 1d list.
        """
        if self.ndim > 1:
            return pyndarray(data=list(chain(*self._data)))
        else:
            return pyndarray(self._data)

    def transpose(self):
        newobj = pyndarray(shape=tuple(reversed(self.shape)))

        for indexes in multirange(*self.shape):
            # print(indexes)
            new_indexes = tuple(reversed(indexes))
            newobj[new_indexes] = self[indexes]

        return newobj

    def __getitem__(self, args):
        if not hasattr(args, "__getitem__"):
            args = [args]

        if any(isinstance(arg, slice) for arg in args[:-1]):
            # if self.ndim == 1:
            #     newobj = self._data[args[0]]
            # else:

            def get_data_range(data, myranges):
                if len(myranges) == 1:
                    return [data[i] for i in myranges[0]]
                else:
                    return [get_data_range(data[i], myranges[1:]) for i in myranges[0]]

            ranges = [
                slice_to_range(arg, self._data, idim) for idim, arg in enumerate(args)
            ]
            # print('----')
            # print(self._data, ranges)
            newobj = get_data_range(self._data, ranges)

        elif len(args) == 2 and (
            isinstance(args[0], (tuple, list)) and isinstance(args[1], slice)
        ):
            new_data = [self._data[irow][args[1]] for irow in args[0]]
            return pyndarray(new_data)

        else:
            newobj = self._data
            for arg in args:
                try:
                    newobj = newobj[arg]
                except TypeError:
                    break

        if isinstance(newobj, list):
            if len(newobj) == 1:
                newobj = pyndarray(data=newobj[0])
            else:
                newobj = pyndarray(data=newobj)

            if newobj.is_column_vector():
                newobj = newobj.reduce_dimension()

        return newobj

    def is_column_vector(self):
        try:
            part1 = all(len(row) == 1 for row in iter(self))
            if part1:
                part2 = all(not (isinstance(row[0], list)) for row in iter(self))
                return part2
            else:
                return False

        except TypeError:
            return False

    def __iter__(self):
        return (self[i] for i in range(len(self._data)))

    def __setitem__(self, args, value):
        if not hasattr(args, "__getitem__"):
            args = [args]

        if any(isinstance(arg, slice) for arg in args):
            value = pyndarray(value)

            def set_data_range(data, myranges):
                if len(myranges) == 1:
                    return [data[i] for i in myranges[0]]
                else:
                    return [set_data_range(data[i], myranges[1:]) for i in myranges[0]]

            ranges = [tuple(slice_to_range(arg, self._data)) for arg in args]

            if self.ndim == 1:
                for inew, iself in enumerate(ranges[0]):
                    self._data[iself] = value[inew]

            elif self.ndim == 2:
                try:
                    new_value_iterator = multirange(*value.shape)
                    for inew, iself in enumerate(ranges[0]):
                        for jnew, jself in enumerate(ranges[1]):
                            v = next(new_value_iterator)
                            self._data[iself][jself] = value[v]
                except StopIteration:
                    pass

            elif self.ndim == 2:
                new_value_iterator = multirange(*value.shape)
                for inew, iself in enumerate(ranges[0]):
                    for jnew, jself in enumerate(ranges[1]):
                        for knew, kself in enumerate(ranges[1]):
                            v = next(new_value_iterator)
                            self._data[iself][jself][kself] = value[v]

        else:
            d = self._data
            for iarg in range(len(args) - 1):
                d = d[args[iarg]]
            d[args[-1]] = value

    def __repr__(self):
        # return 'pyndarray(data={0})'.format(repr(self._data))
        return self.__str__()

    def __str__(self):
        try:
            lines = []
            if self.ndim == 1:
                return (
                    "array(["
                    + " ".join("{0:>10}".format(self[j]) for j in range(self.shape[0]))
                    + "])"
                )
            else:
                gprev = None
                for indexes in multirange(*self.shape[:-1]):
                    lind = list(indexes)
                    if len(lind) > 1:
                        if lind[:-1] != gprev:
                            lines.append("Indexes={0}".format(lind[:-1]))
                            gprev = lind[:-1]

                    lines.append(
                        "["
                        + " ".join(
                            "{0:>10}".format(self[lind + [j]])
                            for j in range(self.shape[-1])
                        )
                        + "]"
                    )
                # lines.append(' '.join(str(self._data[i][j]) for j in range(self.shape[-1])))
            return "\n".join(lines)
        except:  # nopep8
            return str(self._data)

    def iterrows(self):
        return (self[i] for i in range(self.shape[0]))

    def itercolumns(self):
        return (self[:, j] for j in range(self.shape[1]))

    def itervals(self):
        for indexes in multirange(*self.shape):
            yield self[indexes]

    def __add__(self, other):
        # newobj = pyndarray(shape=self.shape)
        newobj = copy.deepcopy(self)

        if isinstance(other, (float, int, type(self[0, 0]))):
            for indexes in multirange(*self.shape):
                newobj[indexes] += other
        else:
            for indexes in multirange(*self.shape):
                newobj[indexes] += other[indexes]

        return newobj

    def __radd__(self, other):
        return self.__add__(other)

    def __sub__(self, other):
        # newobj = pyndarray(shape=self.shape)
        newobj = copy.deepcopy(self)

        if not hasattr(other, "__getitem__"):
            for indexes in multirange(*self.shape):
                newobj[indexes] -= other
        else:
            for indexes in multirange(*self.shape):
                newobj[indexes] -= other[indexes]

        return newobj

    def __rsub__(self, other):
        return self.__add__(other)

    def __mul__(self, other):
        # newobj = pyndarray(shape=self.shape)
        newobj = copy.deepcopy(self)

        if not hasattr(other, "__getitem__"):
            for indexes in multirange(*self.shape):
                newobj[indexes] *= other
        else:
            for indexes in multirange(*self.shape):
                newobj[indexes] *= other[indexes]

        return newobj

    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        # newobj = pyndarray(shape=self.shape)
        newobj = copy.deepcopy(self)

        if not hasattr(other, "__getitem__"):
            for indexes in multirange(*self.shape):
                try:
                    newobj[indexes] /= other
                except ZeroDivisionError as ex:
                    if self.allow_nan:
                        newobj[indexes] = NAN
                    else:
                        raise ex
        else:
            for indexes in multirange(*self.shape):
                try:
                    newobj[indexes] /= other[indexes]
                except ZeroDivisionError as ex:
                    if self.allow_nan:
                        newobj[indexes] = NAN
                    else:
                        raise ex

        return newobj

    def __div__(self, other):
        return self.__truediv__(other)

    def __abs__(self):
        newobj = pyndarray(shape=self.shape)

        for indexes in multirange(*self.shape):
            newobj[indexes] = abs(self[indexes])

        return newobj

    def __round__(self, n):
        newobj = pyndarray(shape=self.shape)

        for indexes in multirange(*self.shape):
            newobj[indexes] = round(self[indexes], n)

        return newobj

    def __eq__(self, other):
        return self.__compare_elements(other, eq)

    def __ne__(self, other):
        return self.__compare_elements(other, ne)

    def __lt__(self, other):
        return self.__compare_elements(other, lt)

    def __gt__(self, other):
        return self.__compare_elements(other, gt)

    def __le__(self, other):
        return self.__compare_elements(other, lte)

    def __ge__(self, other):
        return self.__compare_elements(other, gte)

    def __compare_elements(self, other, op):
        newobj = pyndarray(shape=self.shape, fill=False)

        if isinstance(other, (list, tuple, pyndarray)):
            for indexes in multirange(*self.shape):
                newobj[indexes] = op(self[indexes], other[indexes])
        else:
            for indexes in multirange(*self.shape):
                newobj[indexes] = op(self[indexes], other)

        return newobj

    def __neg__(self):
        newobj = copy.deepcopy(self)

        for indexes in multirange(*self.shape):
            newobj[indexes] *= -1

        return newobj

    def __mod__(self, other):
        newobj = copy.deepcopy(self)

        if not hasattr(other, "__getitem__"):
            for indexes in multirange(*self.shape):
                newobj[indexes] %= other
        else:
            for indexes in multirange(*self.shape):
                newobj[indexes] %= other[indexes]

        return newobj

    def __pow__(self, exponent):
        newobj = copy.deepcopy(self)

        if not hasattr(exponent, "__getitem__"):
            for indexes in multirange(*self.shape):
                newobj[indexes] = newobj[indexes] ** exponent
        else:
            for indexes in multirange(*self.shape):
                newobj[indexes] = newobj[indexes] ** exponent[indexes]

        return newobj

    def __len__(self):
        return len(self._data)

    def nelements(self):
        return product(*self.shape)

    def apply_func(self, func, axis):
        """
        Applies func to columns (if axis is 0) or to rows (if axis is 1).
        :param func:
        :param axis:
        :param name:
        :param args:
        :param kwargs:
        :return:
        """
        if self.ndim == 1:
            return func(self)
        if self.ndim == 2:
            if axis == 0:
                return array([func(self[:, j]) for j in range(self.shape[1])])
            elif axis == 1:
                return array([func(self[i, :]) for i in range(self.shape[0])])
            elif axis is None:
                return func([self[indexes] for indexes in multirange(*self.shape)])
        if self.ndim == 3:
            if axis == 0:
                return [
                    func(
                        [
                            self[(i_outer, i_inner[1], i_inner[2])]
                            for i_inner in multirange(*self.shape[1:3])
                        ]
                    )
                    for i_outer in range(self.shape[0])
                ]
            if axis == 1:
                return [
                    func(
                        [
                            self[(i_inner[0], i_outer, i_inner[2])]
                            for i_inner in multirange(*self.shape[0::2])
                        ]
                    )
                    for i_outer in range(self.shape[1])
                ]
            if axis == 2:
                return [
                    func(
                        [
                            self[(i_inner[0], i_inner[1], i_outer)]
                            for i_inner in multirange(*self.shape[0:2])
                        ]
                    )
                    for i_outer in range(self.shape[2])
                ]
            elif axis is None:
                return func([self[indexes] for indexes in multirange(*self.shape)])
        elif axis is None:
            return func([self[indexes] for indexes in multirange(*self.shape)])

    def mean(self, axis=None):
        """
        Computes the mean value of a column (axis=0) or row (axis=1)
        :param axis:
        :return:
        """
        return self.apply_func(mean, axis)

    def var(self, axis=0, ddof=1):
        func = partial(var, ddof=ddof)
        return self.apply_func(func, axis)

    def std(self, axis=0, ddof=1):
        func = partial(std, ddof=ddof)
        return self.apply_func(func, axis)

    def max(self, axis=0):
        return self.apply_func(max, axis)

    def min(self, axis=0):
        return self.apply_func(min, axis)

    def argmax(self):
        return self.index(max(self))

    def argmin(self):
        return self.index(min(self))

    def argsort(self, axis=0, i=0):
        if self.ndim == 1:
            return list(zip(*list(sorted(enumerate(self._data), key=lambda x: x[1]))))[
                0
            ]
        elif self.ndim == 2:
            if axis == 0:
                return list(
                    zip(*list(sorted(enumerate(self._data[:, i]), key=lambda x: x[1])))
                )[0]
            elif axis == 1:
                return list(
                    zip(*list(sorted(enumerate(self._data[i, :]), key=lambda x: x[1])))
                )[0]

    def sum(self, axis=0):
        return self.apply_func(sum, axis)

    def __and__(self, other):
        result = pyndarray(shape=self.shape, fill=NAN)

        for indexes in multirange(*self.shape):
            result[indexes] = self[indexes] and other[indexes]

        return result

    def __or__(self, other):
        result = pyndarray(shape=self.shape)

        for indexes in multirange(*self.shape):
            result[indexes] = self[indexes] or other[indexes]

        return result

    def all(self):
        for indexes in multirange(*self.shape):
            if not self[indexes]:
                return False
        return True

    def any(self):
        for indexes in multirange(*self.shape):
            if self[indexes]:
                return True
        return False


class ArrayView(pyndarray):
    def __init__(self, x, myslice):
        self._referenced_array = x
        self._referenced_slice = myslice

    @property
    def _data(self):
        return self._referenced_array[self._referenced_slice]

    @_data.setter
    def _data(self, value):
        self._referenced_array[self._referenced_slice] = value


######################################
# primitive functions
######################################
def mean(x):
    return sum(x) / len(x)


def var(x, ddof=1, mn=None):
    if mn is None:
        mn = mean(x)
    return sum([(xi - mn) ** 2 for xi in x]) / (len(x) - ddof)


def std(x, ddof=1, mn=None):
    return math.sqrt(var(x, ddof, mn))


def product(*args):
    result = 1
    for arg in args:
        result *= arg
    return result


min = min

max = max

sum = sum


##########################################
# array functions
#########################################


def transpose(x):
    """
    Transposes a pyndarray
    :type x: pyndarray
    :param x:
    :return: the transposed pyndarray
    """
    return x.transpose()


def append(x, y, axis=0):
    """
    Concatenates pyndarrays x and y
    :type x: pyndarray
    :param x:
    :type y: pyndarray
    :param y:
    :rtype: pyndarray
    :return:
    """
    x, y = array(x), array(y)
    if axis == 0:
        data = x._data + y._data
        return pyndarray(data=data)
    elif axis == 1:
        d2 = [xr + yr for xr, yr in zip(x._data, y._data)]
        return pyndarray(d2)


def delete(x, indexes, axis=None):
    """
    Deletes the specified row or column (or higher dimension) from the array x.

    If axis is None, the array is flattened then the specified indexes are removed.

    :type x: pyndarray
    :param x:
    :type indexes: iterable
    :param indexes:
    :type axis: int
    :param axis:
    :rtype: pyndarray
    :return:
    """
    x = array(x)
    if not hasattr(indexes, "__iter__"):
        indexes = (indexes,)
    if axis is None:
        return array(
            [xi for i, xi in enumerate(multirange(*x.shape)) if i not in indexes]
        )
    else:

        def inner_delete(y, del_ind, inner_axis, actual_axis):
            if inner_axis != actual_axis:
                aa = actual_axis + 1
                return [
                    inner_delete(y[i], del_ind, inner_axis, aa) for i in range(len(y))
                ]
            else:
                return [yi for i, yi in enumerate(y) if i not in del_ind]

        data = copy.deepcopy(x._data)
        data = inner_delete(data, indexes, axis, 0)
        return pyndarray(data)


def eye(m):
    """
    Creates and m X m identity matrix
    :param m:
    :return:
    """
    ident = pyndarray(shape=(m, m))
    for i in range(m):
        ident[i, i] = 1

    return ident


if __name__ == "__main__":
    x = pyndarray(shape=(3, 6))
    y = pyndarray(shape=(10, 5)).random_fill()
    y = y * 2 - 1
    print(x)
    print()
    y = round(y, 4)
    print(y)

    print("mapfill")
    z = y.index_fill()
    print(z)

    print("Single item access")
    print(y[1, 2])

    print("Row slicing")
    print(str(y[1:5, 1]))

    print("Column Slicing")
    print(y[1, 1:5])

    print("Slicing in both directions")
    print(y[1:5, 1:5])
    print()
    print(y + y)
    print("add")
    print(y + 10)
    print("radd")
    print(10 + y)
    print("mul")
    print(y * 10)
    print("div")
    print(y / 100000)
    print()
    print(y / y)
    print("abs")
    print(abs(y))
    print("round")
    print(round(y, 2))
    print("equality")
    print(y == y)
    print(z == y)
    print("pow")
    print(z**2)
    print("division by 0")
    print(z / z)

    print("Transpose")
    print(y[:, 0] == y.transpose()[0, :])
