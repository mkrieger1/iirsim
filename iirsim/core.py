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
    Reduce integer x to N bits in 2's complement, wrapping in case of overflow.

    >>> [_wrap(x, 3) for x in range(-5, 5)]
    [3, -4, -3, -2, -1, 0, 1, 2, 3, -4]
    """
    if not _test_int(x):
        raise TypeError("input value must be 'int'")
    B = 2**(N-1)
    return ((x+B) % 2**N) - B

def _saturate(x, N):
    """
    Reduce integer x to N bits in 2's complement, saturating in case of
    overflow.

    >>> [_saturate(x, 3) for x in range(-5, 5)]
    [-4, -4, -3, -2, -1, 0, 1, 2, 3, 3]
    """
    if not _test_int(x):
        raise TypeError("input value must be 'int'")
    B = 2**(N-1)
    return max(-B, min(B-1, x))

def _test_overflow(x, N):
    """Test if integer x can be represented as N bit two's complement number."""
    if not _test_int(x):
        raise TypeError("input value must be 'int'")
    B = 2**(N-1)
    return (x < -B) or (x > B-1)

def _unit_pulse(bits, length, norm=False):
    """Return unit pulse as generator object."""
    if norm:
        yield float((1 << bits-1) - 1) / (1 << bits-1)
    else:
        if bits < 2:
            raise ValueError('number of bits must be at least 2')
        if length < 1:
            raise ValueError('length must be at least 1')
        yield (1 << bits-1) - 1
    for i in range(length-1):
        yield 0
