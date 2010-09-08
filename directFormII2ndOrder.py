# System 2. Ordnung in direkter Form II
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

from IIRsim import *

BITS = 9
MUL_BITS = 9

b0 = 255
b1 = 0
b2 = 0
a1 = 0
a2 = 0
factors = [b0, b1, b2, a1, a2]

C = Const(BITS)
A = [Add(BITS) for i in range(4)]
D = [Delay(BITS) for i in range(2)]
M = [Multiply(BITS, MUL_BITS, MUL_BITS-2) for i in range(5)]
[M[i].set_factor(factors[i]) for i in range(5)]

A[0].connect(C, A[2])
A[1].connect(M[0], A[3])
A[2].connect(M[3], M[4])
A[3].connect(M[1], M[2])

D[0].connect(A[0])
D[1].connect(D[0])

M[0].connect(A[0])
M[1].connect(D[0])
M[2].connect(D[1])
M[3].connect(D[0])
M[4].connect(D[1])

F = Filter(C, A[1])

