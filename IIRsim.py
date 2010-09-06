def unitpulse(N):
	"""return unit pulse of length N: [1, 0, 0, ... 0]"""
	if N > 0:
		return [1]+(N-1)*[0]

def truncate(value, bits):
	"""limit <value> to <bits> bit number in 2-s complement"""
	v = int(value)
	return ((v+2**(bits-1)) % 2**bits) - 2**(bits-1)

class Add():
	"""<bits> x <bits> --> <bits> adder"""
	def __init__(self, bits):
		self.bits = bits
		self.LO = -2**(bits-1)
		self.HI = 2**(bits-1)-1
		self.overflow = False

	def add(self, valueA, valueB):
		self.overflow = False
		A = truncate(valueA, self.bits)
		B = truncate(valueB, self.bits)
		S = A + B
		if (S < self.LO) or (S > self.HI):
			self.overflow = True
		return truncate(S, self.bits)

class Multiply():
	"""<data_bits> x <coef_bits> --> <data_bits> multiplier"""
	def __init__(self, data_bits, coef_bits):
		self.data_bits = data_bits
		self.coef_bits = coef_bits
