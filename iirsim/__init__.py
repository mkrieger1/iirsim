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

from nodes import Const, Add, Multiply, Delay
from filter import Filter
from cfg import load_filter, save_filter

__all__ = ['Const', 'Add', 'Multiply', 'Delay', 'Filter',
           'load_filter', 'save_filter']
