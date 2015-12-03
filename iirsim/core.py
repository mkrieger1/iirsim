"""Utility to simulate IIR filters.

Contains classes that represent basic components of digital filters. Instances
of these classes can be connected to each other, acting as nodes in a graph
structure, to form a filter. Input and output values are integers representing
two's complement binary numbers.

Classes (overview):
Const    -- Output is a constant value.
Delay    -- Output is the previously stored input value.
Add      -- Output is the sum of two input values.
Multiply -- Output is the input value multiplied by a constant factor.

Methods available for all classes:
connect()    -- Set the input node(s).
get_output() -- Return the output value by either calling get_output() of the
                input node(s) recursively and performing the appropriate
                arithmetic (Add, Multiply) or by returning the currently
                stored value (Const, Delay).
"""

# internally used functions
#--------------------------------------------------------------------
def _test_int(x):
    """Combined test for int type and long type."""
    return (isinstance(x, int) or isinstance(x, long))
    
def _wrap(x, N):
    """Reduce integer x to N bits, wrapping in case of overflow.
   
    With B = 2^(N-1) the largest absolute value, (x+B) MOD 2^N - B is returned.
    For -B <= x < B, x remains unchanged.
    """
    if not _test_int(x):
        raise TypeError("input value must be 'int'")
    B = 2**(N-1)
    return ((x+B) % 2**N) - B

def _saturate(x, N):
    """Reduce integer x to N bits, saturating in case of overflow.

    With B = 2^(N-1) the largest absolute value,
    B-1 is returned for x > B-1,
    -B  is returned for x < -B,
    for -B <= x < B, x remains unchanged.
    """
    if not _test_int(x):
        raise TypeError("input value must be 'int'")
    B = 2**(N-1)
    if x < -B:
        return -B
    elif x > B-1:
        return B-1
    else:
        return x

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
