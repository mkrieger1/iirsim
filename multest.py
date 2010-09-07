#!/usr/bin/python

import IIRsim, optparse

def mul_test(data_bits, fact_bits, magn_bits, factor):
	m = IIRsim.Multiply(data_bits, fact_bits, magn_bits)
	m.set_factor(factor)

	print "# effective factor: %s" % m.eff_factor()
	for i in range(-2**(data_bits-1), 2**(data_bits-1)):
		print "%3i\t%3i" % (i, m.mul(i))


if __name__ == "__main__":
	parser = optparse.OptionParser()
	parser.add_option("--dbits", type="int", dest="data_bits")
	parser.add_option("--fbits", type="int", dest="fact_bits")
	parser.add_option("--mbits", type="int", dest="magn_bits")
	parser.add_option("--fact", type="int", dest="factor")
	(options, args) = parser.parse_args()

	DATA_BITS = options.data_bits
	FACT_BITS = options.fact_bits
	MAGN_BITS = options.magn_bits
	FACTOR = options.factor

	mul_test(DATA_BITS, FACT_BITS, MAGN_BITS, FACTOR)
