# Predict the output
import functools
import operator
l=[98,4,5,6,7,3,2,]

v=functools.reduce(operator.sub,l)
print(v)


