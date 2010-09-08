# helper functions
#--------------------------------------------------------------------
def truncate(value, bits):
    """truncate <value> to <bits> bit number in 2-s complement"""
    v = int(value)
    return ((v+2**(bits-1)) % 2**bits) - 2**(bits-1)

def clip(value, bits):
    """clip <value> to <bits> bit number in 2-s complement"""
    LO = -2**(bits-1)
    HI =  2**(bits-1)-1
    v = int(value)
    if v < LO:
        return LO
    elif v > HI:
        return HI
    else:
        return v

def test_overflow(value, bits):
    """test if <value> can be represented as <bits> bit number in 2-s
complement"""
    LO = -2**(bits-1)
    HI =  2**(bits-1)-1
    return (value < LO) or (value > HI)


# basic components: Const, Add, Multiply, Delay
#--------------------------------------------------------------------
class Const():
    """constant <bits> bit number"""
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
            return clip(P, self.data_bits)

class Delay():
    """stores one <bits> bit number"""
    def __init__(self, bits):
        self.bits = bits
        self.value = 0
        self.input_nodes = [None]

    def connect(self, input_node):
        self.input_nodes = [input_node]

    def get_output(self):
        return self.value

    def clk(self):
        [input_node] = self.input_nodes
        if input_node is None:
            raise RuntimeError("input is not connected")
        value = input_node.get_output()
        if test_overflow(value, self.bits):
            raise ValueError("input overflow")
        else:
            self.value = value

    def reset(self):
        self.value = 0

# wrapper
#--------------------------------------------------------------------
class Filter():
    def __init__(self, in_node, out_node):
        if in_node.__class__ is not Const:
            raise TypeError("input node must be a Const instance")
        self.in_node = in_node
        self.out_node = out_node
        self.nodes = {}
        # build dictionary of all nodes (use order of insertion as value)
        # by depth-first-search
        node_stack = [out_node]
        count = 0
        while len(node_stack):
            node = node_stack.pop()
            if node not in self.nodes:
                self.nodes[node] = count
                count += 1
                for input_node in node.input_nodes:
                    node_stack.append(input_node)
        # build adjacency list using the dictionary
        self.adjacency = [None] * len(self.nodes)
        for [node, index] in self.nodes.items():
            neighbor_index = \
                [self.nodes[neighbor] for neighbor in node.input_nodes]
            self.adjacency[index] = neighbor_index
        # build list of Delay nodes
        self.delay_nodes = []
        for node in self.nodes:
            if node.__class__ is Delay:
                self.delay_nodes.append(node)

    def filter(self, input_values):
        for v in input_values:
            self.in_node.set_value(v)
            yield self.out_node.get_output()
            for delay_node in self.delay_nodes:
                delay_node.clk()
        # continue after input sequence is over (--> IIR)
        self.in_node.set_value(0)
        while True:
            yield self.out_node.get_output()
            for delay_node in self.delay_nodes:
                delay_node.clk()
        
