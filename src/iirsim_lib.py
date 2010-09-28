"""Utility to simulate IIR filters.

Contains classes that represent basic components of digital filters. Instances
of these classes can be connected to form a filter. They exchange 'int'
objects which represent two's complement binary numbers. 

Classes:
Const    -- Holds a constant value.
Delay    -- Stores its input value when triggered.
Add      -- Adds two values. Truncates the output if overflow occurs.
Multiply -- Multiplies a value by a constant factor. Limits the output if
            overflow occurs.

Class interface:
connect() (all except Const) -- Define input components.
get_output() (all)           -- Return the output value of the component by
                                either calling get_output() of the input
                                components recursively and performing the
                                appropriate arithmetic (Add, Multiply) or by
                                returning the currently stored value (Const,
                                Delay).
sample() (Delay)             -- Call get_output() recursively on the input
                                components and store the output as 'next
                                value'. *
clk() (Delay)                -- Replace currently stored value by 'next
                                value'. *
set_value() (Const)          -- Define currently stored value. This component
                                is meant to be used as external input for the
                                whole filter (i.e. to resolve the recursion).
set_factor() (Multiply)      -- Define the factor by which the input value is
                                multiplied when get_output() is called.

                                * Note:
                                sample() and clk() are implemented as separate
                                functions, because the 'next value' must be
                                saved for all Delay components before the
                                output values are replaced, in order to
                                simulate concurrency.
"""

# representing integer values as binary numbers
#--------------------------------------------------------------------
def truncate(x, N):
    """Truncate integer x to N bit two's complement number.
   
    With B = 2^(N-1) the largest absolute value, (x+B) MOD 2^N - B is returned.
    For -B <= x < B, x remains unchanged.
    """
    if type(x) is not int:
        raise TypeError("'int' object expected")
    B = 2**(N-1)
    return ((x+B) % 2**N) - B

def limit(x, N):
    """Limit integer x to N bit two's complement number.

    With B = 2^(N-1) the largest absolute value,
    B-1 is returned for x > B-1,
    -B  is returned for x < -B,
    for -B <= x < B, x remains unchanged.
    """
    if type(x) is not int:
        raise TypeError("'int' object expected")
    B = 2**(N-1)
    if x < -B:
        return -B
    elif x > B-1:
        return B-1
    else:
        return x

def test_overflow(x, N):
    """Test if integer x can be represented as N bit two's complement number."""
    if type(x) is not int:
        raise TypeError("'int' object expected")
    B = 2**(N-1)
    return (x < -B) or (x > B-1)


# basic components: Const, Add, Multiply, Delay
#--------------------------------------------------------------------
class Const():
    """Const(N) holds a constant N bit 2's complement number x:
-2^(N-1) <= x < +2^(N-1)"""
    def __init__(self, bits):
        self.bits = bits
        self.value = 0
        self.input_nodes = []

    def set_value(self, value):
        if test_overflow(value, self.bits):
            raise ValueError("input overflow")
        else:
            self.value = value
    
    def get_output(self):
        return self.value

class Add():
    """<bits> x <bits> --> <bits> adder"""
    def __init__(self, bits):
        self.bits = bits
        self.overflow = False
        self.input_nodes = [None, None]

    def connect(self, input_nodes):
        self.input_nodes = input_nodes

    def get_output(self):
        if any([node is None for node in self.input_nodes]):
            raise RuntimeError("not all inputs are connected")
        [valueA, valueB] = [node.get_output() for node in self.input_nodes]
        if (test_overflow(valueA, self.bits) or test_overflow(valueB, self.bits)):
            raise ValueError("input overflow")
        else:
            S = valueA + valueB
            self.overflow = test_overflow(S, self.bits)
            return truncate(S, self.bits)

class Multiply():
    """<data_bits> x <fact_bits> --> <data_bits> multiplier
where <data_bits> are taken <magn_bits> from the right (LSB)"""
    def __init__(self, data_bits, fact_bits, magn_bits):
        self.data_bits = data_bits
        self.fact_bits = fact_bits
        self.magn_bits = magn_bits
        self.factor = 0
        self.eff_factor_str = "0/%i" % 2**magn_bits
        self.overflow = False
        self.input_nodes = [None]

    def set_factor(self, factor):
        if test_overflow(factor, self.fact_bits):
            raise ValueError("input overflow")
        else:
            self.factor = factor
            self.eff_factor_str = "%i/%i" % (factor, 2**(self.magn_bits))

    def connect(self, input_node):
        self.input_nodes = [input_node]

    def get_output(self):
        [input_node] = self.input_nodes
        if input_node is None:
            raise RuntimeError("input is not connected")
        value = input_node.get_output()
        if test_overflow(value, self.data_bits):
            raise ValueError("input overflow")
        else:
            P = (value*self.factor) >> self.magn_bits
            self.overflow = test_overflow(P, self.data_bits)
            return limit(P, self.data_bits)

class Delay():
    """stores one <bits> bit number"""
    def __init__(self, bits):
        self.bits = bits
        self.value = 0
        self.next_value = 0
        self.input_nodes = [None]

    def connect(self, input_node):
        self.input_nodes = [input_node]

    def get_output(self):
        return self.value

    def sample(self):
        [input_node] = self.input_nodes
        if input_node is None:
            raise RuntimeError("input is not connected")
        value = input_node.get_output()
        if test_overflow(value, self.bits):
            raise ValueError("input overflow")
        else:
            self.next_value = value

    def clk(self):
        self.value = self.next_value

    def reset(self):
        self.value = 0
        self.next_value = 0

# wrapper
#--------------------------------------------------------------------
class Filter():
    def __init__(self, in_node, out_node):
        if in_node.__class__ is not Const:
            raise TypeError("input node must be a Const instance")
        self.in_node = in_node
        self.out_node = out_node
        self.nodes = []
        self.delay_nodes = []
        # build list of all nodes and list of delay nodes (which need the clock
        # signal) by depth-first-search beginning at output node
        node_stack = [out_node]
        while len(node_stack):
            node = node_stack.pop()
            if node not in self.nodes:
                self.nodes.append(node)
                if node.__class__ is Delay:
                    self.delay_nodes.append(node)
                for input_node in node.input_nodes:
                    node_stack.append(input_node)
        # build adjacency list (was: using the dictionary)
        # TODO using the list
        #self.adjacency = [None] * len(self.nodes)
        #for [node, index] in self.nodes.items():
        #    neighbor_index = \
        #        [self.nodes[neighbor] for neighbor in node.input_nodes]
        #    self.adjacency[index] = neighbor_index

    def clk(self):
        for node in self.delay_nodes:
            node.sample()
        for node in self.delay_nodes:
            node.clk()

    def reset(self):
        for node in self.delay_nodes:
            node.reset()

    def filter(self, input_values):
        for v in input_values:
            self.in_node.set_value(v)
            yield self.out_node.get_output()
            self.clk()
        self.in_node.set_value(0)
        # continue after input sequence is over (--> IIR)
        while True:
            yield self.out_node.get_output()
            self.clk()
        
# putting it all together
#--------------------------------------------------------------------

class directForm2():
# 2nd order direct form II
#
#                        b0 
# x[n] ----->(+)------+----->(+)-----> y[n]
#             A       |       A
#             |       V       |
#             |     [z-1]     |
#             |       |       |
#             |   a1  |  b1   |
#            (+)<-----+----->(+)
#             A       |       A
#             |       V       |
#             |     [z-1]     |
#             |       |       |
#             |   a2  |  b2   |
#             +-------+-------+
#
# y[n] = a1 y[n-1] + a2 y[n-2] + b0 x[n] + b1 x[n-1] + b2 x[n-2]

    def __init__(self, bits, mul_bits, factors):
        self.factors = factors #[b0, b1, b2, a1, a2]
        self.bits = bits
        self.mul_bits = mul_bits
        self.magn_bits = mul_bits-2

        C = Const(self.bits)
        A = [Add(self.bits) for i in range(4)]
        D = [Delay(self.bits) for i in range(2)]
        M = [Multiply(self.bits, self.mul_bits, self.magn_bits) for i in range(5)]
        [M[i].set_factor(self.factors[i]) for i in range(5)]
        # setting magn_bits of Multiply() to mul_bits-2 allows for effective
        # multiplication by approx. -2...2
        # e.g. mul_bits = 5 --> magn_bits = 3 --> -16/8 ... +15/8

        A[0].connect([C, A[2]])
        A[1].connect([M[0], A[3]])
        A[2].connect([M[3], M[4]])
        A[3].connect([M[1], M[2]])

        D[0].connect(A[0])
        D[1].connect(D[0])

        M[0].connect(A[0])
        M[1].connect(D[0])
        M[2].connect(D[1])
        M[3].connect(D[0])
        M[4].connect(D[1])

        F = Filter(C, A[1])
        self.filter = F.filter

    def idealfilter(self, input_values):
        [b0, b1, b2, a1, a2] = \
            map(lambda x: float(x)/2**self.magn_bits, self.factors)
        y1 = 0 # y[n-1]
        y2 = 0 # y[n-2]
        x1 = 0 # x[n-1]
        x2 = 0 # x[n-2]
        
        for x in input_values:
            y = a1*y1 + a2*y2 + b0*x + b1*x1 + b2*x2
            yield y
            x1, x2 = x, x1
            y1, y2 = y, y1
        x = 0
        # continue after input sequence is over (--> IIR)
        while True:
            y = a1*y1 + a2*y2 + b0*x + b1*x1 + b2*x2
            yield y
            x1, x2 = x, x1
            y1, y2 = y, y1

