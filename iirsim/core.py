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

import math

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
class Filter():
    """This class makes a filter out of individual filter nodes."""
    def __init__(self, node_dict, adjacency_dict, in_node, out_node):
        """Connect nodes to a graph structure forming a filter.
        
        node_dict:      Dictionary of (name, _FilterNode) pairs.

        adjacency_dict: Defines the connections between the nodes.

        in_node:        Key of the node in node_dict that serves as filter
                        input. The input node must be an instance of Const.

        out_node:       Key of the node in node_dict that serves as filter
                        output.
        """
        if not isinstance(node_dict, dict):
            raise TypeError('dict of filter nodes expected')
        elif not all([isinstance(node, _FilterNode) \
                      for node in node_dict.values()]):
            raise TypeError('filter nodes must be _FilterNode instances')
        if not isinstance(node_dict[in_node], Const):
            raise TypeError("input node must be Const instance")
        self._nodes = node_dict
        self._adjacency = adjacency_dict
        self._in_node = node_dict[in_node]
        self._out_node = node_dict[out_node]
        self._delay_nodes = [node for node in self._nodes.values()
                             if isinstance(node, Delay)]
        self._mul_node_names = [name for name in self._nodes.keys()
                                if isinstance(self._nodes[name], Multiply)]

        for (name, node) in self._nodes.iteritems():
            input_nodes = [self._nodes[n] for n in self._adjacency[name]]
            try:
                node.connect(input_nodes)
            except (TypeError, ValueError):
                raise

    def _update(self, ideal=False):
        """Update all Delay nodes."""
        for node in self._delay_nodes:
            node.sample(ideal)
        for node in self._delay_nodes:
            node.clk()

    def reset(self):
        """Reset internal filter state."""
        self._in_node.reset()
        for node in self._delay_nodes:
            node.reset()

    def feed(self, input_value, norm=False, ideal=False):
        """Feed new input value into the filter and return output value."""
        self._update(ideal)
        if norm:
            input_value = input_value * (1 << self._in_node._bits-1)
        if not ideal:
            input_value = int(input_value)
        self._in_node.set_value(input_value, ideal)
        output_value = self._out_node.get_output(ideal)
        if norm:
            output_value = float(output_value)/(1<<self._out_node._bits-1)
        return output_value

    def print_status(self):
        """Print status message for all nodes."""
        names = self._nodes.keys()
        maxlen = max([len(name) for name in names])
        for name in names:
            (value, msg) = self._nodes[name].get_output(verbose=True)
            print name.ljust(maxlen), msg

    def unit_pulse(self, length, norm=False):
        """Return the first sample of the unit pulse."""
        return [x for x in _unit_pulse(self._in_node._bits, length, norm)]

    def response(self, data, length, norm=False, ideal=False):
        """Return the response to the input data."""
        self.reset()
        def gen_response():
            if length > len(data):
                for x in data:
                    yield self.feed(x, norm, ideal)
                for i in range(length-len(data)):
                    yield self.feed(0, norm, ideal)
            else:
                for i in range(length):
                    yield self.feed(data[i], norm, ideal)
        return [x for x in gen_response()]

    def impulse_response(self, length, norm=False, ideal=False):
        """Return the impulse response of the filter."""
        return self.response(self.unit_pulse(1, norm), length, norm, ideal)

    def bits(self):
        """Return the number of bits for all nodes."""
        bits_list = [node.bits() for node in self._nodes.itervalues()]
        if bits_list:
            test_bits = bits_list[0]
            if not all([bits == test_bits for bits in bits_list]):
                raise ValueError( \
                      'number of bits is not the same for all nodes')
            return test_bits

    def set_bits(self, bits):
        """Set the number of bits for all nodes."""
        for node in self._nodes.itervalues():
            node.set_bits(bits)

    def factor_bits(self):
        """Return names of the Multiply nodes with their factor_bits."""
        return dict(zip(self._mul_node_names, \
                        [self._nodes[name]._factor_bits \
                         for name in self._mul_node_names]))

    def norm_bits(self):
        """Return names of the Multiply nodes with their norm_bits."""
        return dict(zip(self._mul_node_names, \
                        [self._nodes[name]._norm_bits \
                         for name in self._mul_node_names]))

    def set_factor_bits(self, factorbits, normbits):
        """Set factor and normalization bits for all Multiply nodes."""
        for node in [self._nodes[name] for name in self._mul_node_names]:
            node.set_factor_bits(factorbits, normbits)

    def set_factor(self, name, factor, norm=False):
        """Set the factor of a Multiply node."""
        try:
            mul_node = self._nodes[name]
        except KeyError:
            raise KeyError('no node named %s' % name)
        if not isinstance(mul_node, Multiply):
            raise TypeError('node %s is not an instance of Multiply' % name)
        else:
            mul_node.set_factor(factor, norm)

    def factors(self, norm=False):
        """Return names of the Multiply nodes with their factors."""
        return dict((name, self._nodes[name].factor(norm))
                     for name in self._mul_node_names)

