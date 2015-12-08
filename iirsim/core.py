import numpy

# internally used functions
#--------------------------------------------------------------------
def _test_int(x):
    """
    Test if x is of one of the integer types.

    >>> _test_int(3)
    True
    >>> _test_int(3L)
    True
    >>> _test_int(3.0)
    False
    """
    return isinstance(x, (int, long))

def _wrap(x, N):
    """
    Reduce integer (array) x to N bits in two's complement, wrapping in case of
    overflow.

    >>> [_wrap(x, 3) for x in range(-5, 5)]
    [3, -4, -3, -2, -1, 0, 1, 2, 3, -4]

    >>> import numpy
    >>> list(_wrap(numpy.arange(-5, 5), 3))
    [3, -4, -3, -2, -1, 0, 1, 2, 3, -4]
    """
    offset = 1 << (N - 1)
    mask = (1 << N) - 1
    return ((x + offset) & mask) - offset

def _saturate(x, N):
    """
    Reduce integer (array) x to N bits in two's complement, saturating in case
    of overflow.

    >>> [_saturate(x, 3) for x in range(-5, 5)]
    [-4, -4, -3, -2, -1, 0, 1, 2, 3, 3]

    >>> import numpy
    >>> list(_saturate(numpy.arange(-5, 5), 3))
    [-4, -4, -3, -2, -1, 0, 1, 2, 3, 3]
    """
    limit = 1 << (N - 1)
    return numpy.clip(x, -limit, limit - 1)

def _test_overflow(x, N):
    """
    Test if integer (array) x cannot be represented as an N bit two's complement
    number.

    >>> [int(_test_overflow(x, 3)) for x in range(-5, 5)]
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1]

    >>> import numpy
    >>> map(int, _test_overflow(numpy.arange(-5, 5), 3))
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    """
    limit = 1 << (N - 1)
    return (x < -limit) | (x >= limit)
