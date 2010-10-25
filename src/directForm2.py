import iirsim_lib

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

    def __init__(self, bits, factor_bits, factors):
        self._factors = factors # [b0, b1, b2, a1, a2]
        self._bits = bits
        self._factor_bits = factor_bits
        self._scale_bits = factor_bits-2

        C = iirsim_lib.Const(self._bits)
        A = [iirsim_lib.Add(self._bits) for i in range(4)]
        D = [iirsim_lib.Delay(self._bits) for i in range(2)]
        M = [iirsim_lib.Multiply(self._bits, self._factor_bits, self._scale_bits) for i in range(5)]
        [M[i].set_factor(self._factors[i]) for i in range(5)]
        # setting scale_bits of Multiply() to factor_bits-2 allows for effective
        # multiplication by approx. -2...2
        # e.g. factor_bits = 5 --> scale_bits = 3 --> -16/8 ... +15/8

        # node list
        filter_nodes = [C] + A + D + M

        # adjacency list
        adjacency = [[] for i in range(len(filter_nodes))]

        adjacency[ 0] = []       # C
        adjacency[ 1] = [ 0,  3] # A0
        adjacency[ 2] = [ 7,  4] # A1
        adjacency[ 3] = [10, 11] # A2
        adjacency[ 4] = [ 8,  9] # A3
        adjacency[ 5] = [ 1]     # D0
        adjacency[ 6] = [ 5]     # D1
        adjacency[ 7] = [ 1]     # M0
        adjacency[ 8] = [ 5]     # M1
        adjacency[ 9] = [ 6]     # M2
        adjacency[10] = [ 5]     # M3
        adjacency[11] = [ 6]     # M4

        self._Filter = iirsim_lib.Filter(filter_nodes, adjacency, 0, 2)

    def filt(self, input_values):
        for x in input_values:
            yield self._Filter.feed(x)
        while True:
            yield self._Filter.feed(0)

    def idealfilt(self, input_values):
        [b0, b1, b2, a1, a2] = \
            map(lambda x: float(x)/2**self._scale_bits, self._factors)
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

