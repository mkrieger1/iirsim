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

    def set_value(self, value):
        if test_overflow(value):
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

    def get_output(self):
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
        self.input_node = None

    def set_factor(self, factor):
        if test_overflow(factor, self.fact_bits):
            raise ValueError("input overflow")
        else:
            self.factor = factor
            self.eff_factor_str = "%i/%i" % (factor, 2**(self.magn_bits))

    def get_output(self):
        value = self.input_node.get_output()
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
        self.input_node = None

    def get_output(self):
        return self.value

    def clk(self):
        value = self.input_node.get_output()
        if test_overflow(value, self.bits):
            raise ValueError("input overflow")
        else:
            self.value = value

