# This example uses functools.reduce() with built-in functions from operator module to perform sum, product and string concatenation on lists
# Now performing sum using operator function
import functools
import operator
l=[2,3,4,7,8]
su=functools.reduce(operator.add, l)
print(su)
