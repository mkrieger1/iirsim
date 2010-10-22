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
        self.factors = factors # [b0, b1, b2, a1, a2]
        self.bits = bits
        self.factor_bits = factor_bits
        self.scale_bits = factor_bits-2

        C = Const(self.bits)
        A = [Add(self.bits) for i in range(4)]
        D = [Delay(self.bits) for i in range(2)]
        M = [Multiply(self.bits, self.mul_bits, self.magn_bits) for i in range(5)]
        [M[i].set_factor(self.factors[i]) for i in range(5)]
        # setting scale_bits of Multiply() to factor_bits-2 allows for effective
        # multiplication by approx. -2...2
        # e.g. factor_bits = 5 --> scale_bits = 3 --> -16/8 ... +15/8

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

