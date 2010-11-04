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
def _wrap(x, N):
    """Reduce integer x to N bits, wrapping in case of overflow.
   
    With B = 2^(N-1) the largest absolute value, (x+B) MOD 2^N - B is returned.
    For -B <= x < B, x remains unchanged.
    """
    if not isinstance(x, int):
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

def _unit_pulse(bits, length, scaled=False):
    """Return unit pulse as generator object."""
    if scaled:
        yield float((1 << bits-1) - 1) / (1 << bits-1)
    else:
        if bits < 2:
            raise ValueError('number of bits must be at least 2')
        if length < 1:
            raise ValueError('length must be at least 1')
        yield (1 << bits-1) - 1
    for i in range(length-1):
        yield 0

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
        if any([node is None for node in self._input_nodes]):
            raise RuntimeError("not all inputs are connected")
        input_values = [node.get_output() for node in self._input_nodes]
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
        elif not all([isinstance(x, _FilterComponent) for x in input_nodes]):
            raise TypeError("input nodes must be instance of _FilterComponent")
        else:
            self._input_nodes = input_nodes

    def get_output(self, verbose=False):
        raise NotImplementedError
        # must be overridden by child class

    def bits(self):
        """Return the number of bits."""
        return self._bits

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
                self._value = value
        except TypeError:
            raise
    
    def get_output(self, verbose=False):
        """Return the stored value."""
        value = self._value
        if verbose:
            msg = 'returning %i' % value
            return (value, msg)
        else:
            return value

class Add(_FilterComponent):
    """Adds two integer values using binary two's complement arithmetic."""

    def __init__(self, bits):
        """Set the number of bits for the inputs."""
        try:
            _FilterComponent.__init__(self, 2, bits)
        except (TypeError, ValueError):
            raise

    def get_output(self, verbose=False):
        """Return the sum of the input values using modular arithmetic."""
        try:
            input_values = self._get_input_values()
        except (RuntimeError, ValueError):
            raise
        S = sum(input_values)
        value = _wrap(S, self._bits)
        if verbose:
            if S != value:
                msg = 'OVERFLOW: %i wrapped to %i' % (S, value)
            else:
                msg = 'returning %i' % value
            return (value, msg)
        else:
            return value

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
            self._factor_bits = factor_bits

        if not isinstance(scale_bits, int):
            raise TypeError("scale_bits must be 'int'")
        elif scale_bits < 0:
            raise ValueError("scale_bits must not be negative")
        else:
            self._scale_bits = scale_bits

        self.set_factor(factor)

    def set_factor(self, factor, scaled=False):
        """Set the factor."""
        if scaled:
            factor = int(round((1 << self._scale_bits)*factor))
        if _test_overflow(factor, self._factor_bits):
            min_fact = -1 << self._factor_bits-1
            max_fact = (1 << self._factor_bits-1)-1 
            min_fact_sc = float(min_fact)/(1 << self._scale_bits)
            max_fact_sc = float(max_fact)/(1 << self._scale_bits)
            raise ValueError( \
                "factor must be in the range %i to %i (%.6f to %6f scaled)" \
                             % (min_fact, max_fact, min_fact_sc, max_fact_sc))
        else:
            self._factor = factor

    def get_output(self, verbose=False):
        """Return multiple of the input value using saturation arithmetic."""
        try:
            [input_value] = self._get_input_values()
        except (RuntimeError, ValueError):
            raise
        P = (input_value*self._factor) >> self._scale_bits
        value = _saturate(P, self._bits)
        if verbose:
            if P != value:
                msg = 'OVERFLOW: %i saturated to %i' % (P, value)
            else:
                msg = 'returning %i' % value
            return (value, msg)
        else:
            return value

    def factor(self, scaled=False):
        """Return the factor."""
        if scaled:
            return float(self._factor)/(1 << self._scale_bits)
        else:
            return self._factor

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

    def get_output(self, verbose=False):
        """Return current value."""
        value = self._value
        if verbose:
            msg = 'returning %i' % value
            return (value, msg)
        else:
            return value

class Filter():
    """This class makes a filter out of individual filter nodes."""
    def __init__(self, node_dict, adjacency_dict, in_node, out_node):
        """Connect nodes to a graph structure forming a filter.
        
        node_dict:      Dictionary of (name, _FilterComponent) pairs.

        adjacency_dict: Defines the connections between the nodes.

        in_node:        Key of the node in node_dict that serves as filter
                        input. The input node must be an instance of Const.

        out_node:       Key of the node in node_dict that serves as filter
                        output.
        """
        if not isinstance(node_dict, dict):
            raise TypeError('dict of filter nodes expected')
        elif not all([isinstance(node, _FilterComponent) \
                      for node in node_dict.values()]):
            raise TypeError('filter nodes must be _FilterComponent instances')
        if not isinstance(node_dict[in_node], Const):
            raise TypeError("input node must be Const instance")
        self._nodes = node_dict
        self._adjacency = adjacency_dict
        self._in_node = node_dict[in_node]
        self._out_node = node_dict[out_node]
        self._delay_nodes = filter(lambda x: isinstance(x, Delay), \
                                  self._nodes.values())
        self._mul_node_names = filter(lambda name: \
            isinstance(self._nodes[name], Multiply), self._nodes.keys())
               # (builtin function 'filter' has nothing to do with IIR filters)

        for (name, node) in self._nodes.iteritems():
            input_nodes = [self._nodes[n] for n in self._adjacency[name]]
            try:
                node.connect(input_nodes)
            except (TypeError, ValueError):
                raise

    def _update(self):
        """Update all Delay nodes."""
        for node in self._delay_nodes:
            node.sample()
        for node in self._delay_nodes:
            node.clk()

    def reset(self):
        """Reset internal filter state."""
        for node in self._delay_nodes:
            node.reset()

    def feed(self, input_value, scaled=False):
        """Feed new input value into the filter and return output value."""
        self._update()
        if scaled:
            input_value = int(input_value * (1 << self._in_node._bits-1))
        self._in_node.set_value(input_value)
        output_value = self._out_node.get_output()
        if scaled:
            output_value = float(output_value)/(1<<self._out_node._bits-1)
        return output_value

    def print_status(self):
        names = self._nodes.keys()
        maxlen = max([len(name) for name in names])
        for name in names:
            (value, msg) = self._nodes[name].get_output(verbose=True)
            print name.ljust(maxlen), msg

    def impulse_response(self, length, scaled=False):
        """Return the impulse response of the filter."""
        self.reset()
        return [self.feed(x, scaled) \
                for x in _unit_pulse(self._in_node._bits, length, scaled)]

    def factors(self, scaled=False):
        """Return names of the Multiply nodes with their factors."""
        return dict(zip(self._mul_node_names, \
                        [self._nodes[name].factor(scaled) \
                         for name in self._mul_node_names]))

    def factor_bits(self):
        """Return names of the Multiply nodes with their factor_bits."""
        return dict(zip(self._mul_node_names, \
                        [self._nodes[name]._factor_bits \
                         for name in self._mul_node_names]))

    def scale_bits(self):
        """Return names of the Multiply nodes with their scale_bits."""
        return dict(zip(self._mul_node_names, \
                        [self._nodes[name]._scale_bits \
                         for name in self._mul_node_names]))

    def set_factor(self, name, factor, scaled=False):
        """Set the factor of a Multiply node."""
        try:
            mul_node = self._nodes[name]
        except KeyError:
            raise KeyError('no node named %s' % name)
        if not isinstance(mul_node, Multiply):
            raise TypeError('node %s is not an instance of Multiply' % name)
        else:
            mul_node.set_factor(factor, scaled)


