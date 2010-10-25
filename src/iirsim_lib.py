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
set_bits()   -- Set the number of bits used for the input and output values..
"""

# internally used functions
#--------------------------------------------------------------------
def _truncate(x, N):
    """Truncate integer x to N bit two's complement number.
   
    With B = 2^(N-1) the largest absolute value, (x+B) MOD 2^N - B is returned.
    For -B <= x < B, x remains unchanged.
    """
    if not isinstance(x, int):
        raise TypeError("input value must be 'int'")
    B = 2**(N-1)
    return ((x+B) % 2**N) - B

def _limit(x, N):
    """Limit integer x to N bit two's complement number.

    With B = 2^(N-1) the largest absolute value,
    B-1 is returned for x > B-1,
    -B  is returned for x < -B,
    for -B <= x < B, x remains unchanged.
    """
    if not isinstance(x, int):
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
    if not isinstance(x, int):
        raise TypeError("input value must be 'int'")
    B = 2**(N-1)
    return (x < -B) or (x > B-1)

# base class: _FilterComponent
#--------------------------------------------------------------------
class _FilterComponent():
    """Base class for Const, Delay, Add, Multiply"""

    # internally used methods
    def __init__(self, ninputs, bits):
        if not isinstance(ninputs, int):
            raise TypeError("number of inputs must be 'int'")
        elif ninputs < 0:
            raise ValueError("number of inputs must not be negative")
        elif not isinstance(bits, int):
            raise TypeError("number of bits must be 'int'")
        elif bits < 1:
            raise ValueError("number of bits must be positive")
        else:
            self._input_nodes = [None for i in range(ninputs)]
            self._ninputs = ninputs
            self._bits = bits

    def _get_input_values(self):
        if any([node is None for node in self.input_nodes]):
            raise RuntimeError("not all inputs are connected")
        input_values = [node.get_output() for node in self.input_nodes]
        if any([_test_overflow(value, self._bits) for value in input_values]):
            raise ValueError("input overflow")
        return input_values
        
    # public methods
    def connect(self, input_nodes):
        if not isinstance(input_nodes, list):
            raise TypeError("list of input nodes expected")
        elif not len(input_nodes) == self._ninputs:
            raise ValueError("number of input nodes must be %i" % self._ninputs)
        elif not all([isinstance(x, _FilterComponent) for x in input_nodes]):
            raise TypeError("input nodes must be instance of _FilterComponent")
        else:
            self._input_nodes = input_nodes

    def set_bits(self, bits):
        raise NotImplementedError
        # TODO

    def get_output(self):
        raise NotImplementedError
        # must be overridden by child class

# Const, Add, Multiply, Delay are inherited from the _FilterComponent base class
#--------------------------------------------------------------------
class Const(_FilterComponent):
    """Stores a constant integer value that must be set explicitly."""

    def __init__(self, bits, value=0):
        """Set the number of bits and the initial value."""
        try:
            _FilterComponent.__init__(self, 0, bits)
        except (TypeError, ValueError):
            raise
        try:
            self.set_value(value)
        except (TypeError, ValueError):
            raise

    def set_value(self, value):
        """Set the stored value.

        For N the number of bits, valid inputs are integer numbers x where
        -B <= x < B, with B = 2^(N-1) the largest absolute value.
        """
        try:
            input_overflow = _test_overflow(value, self._bits)
            if input_overflow:
                raise ValueError("input overflow")
            else:
                self.value = value
        except TypeError:
            raise
    
    def get_output(self):
        """Return the stored value."""
        return self.value

class Add(_FilterComponent):
    """Adds two integer values using binary two's complement arithmetic."""

    def __init__(self, bits):
        """Set the number of bits for the inputs."""
        try:
            _FilterComponent.__init__(self, 2, bits)
        except (TypeError, ValueError):
            raise

    def get_output(self):
        """Return the sum of the input values, truncate if necessary."""
        try:
            input_values = self._get_input_values()
            S = sum(input_values)
            return _truncate(S, self._bits)
        except (RuntimeError, ValueError):
            raise

class Multiply(_FilterComponent):
    """Multiplies the input value by a constant factor."""
    def __init__(self, bits, factor_bits, scale_bits, factor=0):
        """Set the number of bits for the input, the factor and the scale."""
        try:
            _FilterComponent.__init__(self, 1, bits)
        except (TypeError, ValueError):
            raise

        if not isinstance(factor_bits, int):
            raise TypeError("factor_bits must be 'int'")
        elif factor_bits < 2:
            raise ValueError("factor_bits must be at least 2")
        else:
            self.factor_bits = factor_bits

        if not isinstance(scale_bits, int):
            raise TypeError("scale_bits must be 'int'")
        elif scale_bits < 0:
            raise ValueError("scale_bits must not be negative")
        else:
            self.scale_bits = scale_bits

        self.set_factor(factor)

    def set_factor(self, factor):
        """Set the factor."""
        if _test_overflow(factor, self.factor_bits):
            raise ValueError("input overflow")
        else:
            self._factor = factor

    def get_output(self):
        """Return multiple of the input value, limit if necessary."""
        try:
            [input_value] = self._get_input_values()
            P = (input_value*self._factor) >> self.scale_bits
            return _limit(P, self.data_bits)
        except (RuntimeError, ValueError):
            raise

class Delay(_FilterComponent):
    """Stores the input value."""
    def __init__(self, bits):
        """Set the number of bits for the input."""
        try:
            _FilterComponent.__init__(self, 1, bits)
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

    def sample(self):
        """Set input value as next value."""
        try:
            [input_value] = self._get_input_values()
            self._next_value = input_value
        except (RuntimeError, ValueError):
            raise

    def get_output(self):
        """Return current value."""
        return self._value

# wrapper
#--------------------------------------------------------------------
class Filter():
    def __init__(self, node_list, adjacency_list, in_node, out_node):
        """Connect nodes to a graph structure forming a filter.
        
        node_list:      List of _FilterNode instances.

        adjacency_list: Defines the connections between the nodes.

        in_node:        Index of the node in node_list that serves as filter
                        input. The input node must be an instance of Const.

        out_node:       Index of the node in node_list that serves as filter
                        output.
        """
        if not isinstance(node_list, list):
            raise TypeError('list of filter nodes expected')
        elif not all([isinstance(node, _FilterNode) for node in node_list]):
            raise TypeError('filter nodes must be _FilterNode instances')
        if not isinstance(node_list[in_node], Const):
            raise TypeError("input node must be Const instance")
        self.nodes = node_list
        self.in_node = node_list[in_node]
        self.out_node = node_list[out_node]
        self.delay_nodes = filter(lambda x: isinstance(x, Delay), self.nodes)
                           # this has nothing to do with IIR filters

        for n in range(len(self.nodes)):
            node = self.nodes[n]
            input_nodes = [self.nodes[i] for i in adjacency_list[n]]
            try:
                node.connect(input_nodes)
            except (TypeError, ValueError):
                raise

    def update(self):
        """Update all Delay nodes."""
        for node in self.delay_nodes:
            node.sample()
        for node in self.delay_nodes:
            node.clk()

    def reset(self):
        """Reset all Delay nodes."""
        for node in self.delay_nodes:
            node.reset()

    def feed(self, input_value):
        """Feed new input value into the filter and return output value."""
            self.update()
            self.in_node.set_value(input_value)
            return self.out_node.get_output()
        
