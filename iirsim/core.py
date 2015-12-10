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

    >>> map(int, _test_overflow(numpy.arange(-5, 5), 3))
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1]
    """
    limit = 1 << (N - 1)
    return (x < -limit) | (x >= limit)

def from_real(x, N, M=0):
    """
    Map x from the real interval [-r, r) to the range of N-bit two's complement
    numbers [-B, ..., B-1], rounding to the nearest possible value, where
    r = 2 ** M (default: 1.0),
    B = 2 ** (N - 1).

    >>> [from_real(x, 8) for x in [0.7, 0.8, 0.9, 1.0, 1.1]]
    [90, 102, 115, 127, 127]

    >>> list(from_real(numpy.linspace(0.6, 1.1, 10), 7))
    [38, 42, 46, 49, 53, 56, 60, 63, 63, 63]

    >>> list(from_real(numpy.linspace(0.3, 0.6, 10), 8, -1))
    [77, 85, 94, 102, 111, 119, 127, 127, 127, 127]

    >>> list(from_real(numpy.linspace(-4.5, -3.0, 10), 8, 2))
    [-128, -128, -128, -128, -123, -117, -112, -107, -101, -96]
    """
    y = x * (2 ** (N - 1 - M))
    return _saturate(numpy.rint(y).astype(int), N)
