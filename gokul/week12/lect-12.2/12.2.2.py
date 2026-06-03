import functools
import operator
a = [1, 3, 5, 6, 2]

print(functools.reduce(operator.add, a))
print(functools.reduce(operator.mul, a)) 
print(functools.reduce(operator.add, ["geeks", "for", "geeks"]))