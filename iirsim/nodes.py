import math
from .core import _test_int, _test_overflow, _wrap

# base class: _FilterNode
#--------------------------------------------------------------------
class _FilterNode():
    """Base class for Const, Delay, Add, Multiply"""

    # internally used methods
    def __init__(self, ninputs, bits):
        if not _test_int(ninputs):
            raise TypeError("number of inputs must be 'int'")
        elif ninputs < 0:
            raise ValueError("number of inputs must not be negative")
        else:
            self._input_nodes = [None for i in range(ninputs)]
            self._ninputs = ninputs
        self.set_bits(bits)

    def _get_input_values(self, ideal=False):
        if any([node is None for node in self._input_nodes]):
            raise RuntimeError("not all inputs are connected")
        input_values = [node.get_output(ideal) for node in self._input_nodes]
        if not ideal:
            if any([_test_overflow(value, self._bits) for value in input_values]):
                raise ValueError("input overflow")
        return input_values

    # public methods
    def connect(self, input_nodes):
        """Set the input nodes."""
        if not isinstance(input_nodes, list):
            raise TypeError("list of input nodes expected")
        elif not len(input_nodes) == self._ninputs:
            raise ValueError("number of input nodes must be %i" % self._ninputs)
        elif not all([isinstance(x, _FilterNode) for x in input_nodes]):
            raise TypeError("input nodes must be instance of _FilterNode")
        elif not all([node.bits() == self._bits for node in input_nodes]):
            raise ValueError("number of bits does not match")
        else:
            self._input_nodes = input_nodes

    def get_output(self, ideal=False, verbose=False):
        raise NotImplementedError
        # must be overridden by child class

    def bits(self):
        """Return the number of bits."""
        return self._bits

    def set_bits(self, bits):
        """Set the number of bits."""
        if not _test_int(bits):
            raise TypeError("number of bits must be 'int'")
        elif bits < 2:
            raise ValueError("number of bits must be at least 2")
        else:
            self._bits = bits

# Const, Add, Multiply, Delay are inherited from the _FilterNode base class
#--------------------------------------------------------------------
class Const(_FilterNode):
    """Stores a constant integer value that must be set explicitly."""

    def __init__(self, bits, value=0):
        """Set the number of bits and the initial value."""
        try:
            _FilterNode.__init__(self, 0, bits)
        except (TypeError, ValueError):
            raise
        try:
            self.set_value(value)
        except (TypeError, ValueError):
            raise

    def reset(self):
        """Set the stored value to 0."""
        self.set_value(0)

    def set_value(self, value, ideal=False):
        """Set the stored value."""
        if not ideal:
            if _test_overflow(value, self._bits):
                raise ValueError("input overflow")
        self._value = value

    def get_output(self, ideal=False):
        """Return the stored value."""
        value = self._value
        return value

class Add(_FilterNode):
    """Adds two integer values using binary two's complement arithmetic."""

    def __init__(self, bits):
        """Set the number of bits for the inputs."""
        try:
            _FilterNode.__init__(self, 2, bits)
        except (TypeError, ValueError):
            raise

    def get_output(self, ideal=False, verbose=False):
        """Return the sum of the input values using modular arithmetic."""
        try:
            input_values = self._get_input_values(ideal)
        except (RuntimeError, ValueError):
            raise
        S = sum(input_values)
        if not ideal:
            value = _wrap(S, self._bits)
        else:
            value = S
        if verbose:
            if S != value:
                msg = 'OVERFLOW: %i wrapped to %i' % (S, value)
            else:
                msg = 'returning %i' % value
            return (value, msg)
        else:
            return value

class Multiply(_FilterNode):
    """Multiplies the input value by a constant factor."""
    def __init__(self, bits, factor_bits, norm_bits, factor=0):
        """Set the number of bits for the input, the factor and the norm."""
        try:
            _FilterNode.__init__(self, 1, bits)
        except (TypeError, ValueError):
            raise

        if not _test_int(factor_bits):
            raise TypeError("factor_bits must be 'int'")
        elif factor_bits < 2:
            raise ValueError("factor_bits must be at least 2")
        else:
            self._factor_bits = factor_bits

        if not _test_int(norm_bits):
            raise TypeError("norm_bits must be 'int'")
        elif norm_bits < 0:
            raise ValueError("norm_bits must not be negative")
        else:
            self._norm_bits = norm_bits

        self.set_factor(factor)

    def set_factor(self, factor, norm=False):
        """Set the factor."""
        if norm:
            factor = int(round((1 << self._norm_bits)*factor))
        if _test_overflow(factor, self._factor_bits):
            min_fact = -1 << self._factor_bits-1
            max_fact = (1 << self._factor_bits-1)-1
            min_fact_sc = float(min_fact)/(1 << self._norm_bits)
            max_fact_sc = float(max_fact)/(1 << self._norm_bits)
            raise ValueError( \
                "factor must be in the range %i to %i (%.6f to %6f normalized)" \
                             % (min_fact, max_fact, min_fact_sc, max_fact_sc))
        else:
            self._factor = factor

    def set_factor_bits(self, factorbits, normbits):
        """Change the number of bits used for factor and factor norm."""
        old_factor = self.factor(norm=True)
        if factorbits < 2:
            raise ValueError("number of bits must be at least 2")
        else:
            self._factor_bits = factorbits
        if normbits < 0:
            raise ValueError("number of bits must be at least 0")
        else:
            self._norm_bits = normbits
        self.set_factor(old_factor, norm=True)

    def get_output(self, ideal=False, verbose=False):
        """Return multiple of the input value."""
        try:
            [input_value] = self._get_input_values(ideal)
        except (RuntimeError, ValueError):
            raise
        idealvalue = input_value*self._factor / 2.0**self._norm_bits
        if not ideal:
            #P = int(round(idealvalue)) # -> nearest
            P = int(math.floor(idealvalue)) # -> negative
            #P = int(math.ceil(idealvalue)) # -> positive
            #P = int(idealvalue) # -> zero
            value = _wrap(P, self._bits)
        else:
            value = idealvalue
        if verbose:
            if P != value:
                msg = 'OVERFLOW: %i wrapped to %i' % (P, value)
            else:
                msg = 'returning %i' % value
            return (value, msg)
        else:
            return value

    def factor(self, norm=False):
        """Return the factor."""
        if norm:
            return float(self._factor)/(1 << self._norm_bits)
        else:
            return self._factor

class Delay(_FilterNode):
    """Stores the input value."""
    def __init__(self, bits):
        """Set the number of bits for the input."""
        try:
            _FilterNode.__init__(self, 1, bits)
        except (TypeError, ValueError):
            raise
        self.reset()

    def reset(self):
        """Set current and next value to 0."""
        self._value = 0
        self._next_value = 0

    def clk(self):
        """Replace current value with next value."""
        self._value = self._next_value

    def sample(self, ideal=False):
        """Set input value as next value."""
        try:
            [input_value] = self._get_input_values(ideal)
            self._next_value = input_value
        except (RuntimeError, ValueError):
            raise

    def get_output(self, ideal=False, verbose=False):
        """Return current value."""
        value = self._value
        if not ideal:
            value = int(value)
        if verbose:
            msg = 'returning %i' % value
            return (value, msg)
        else:
            return value

