# Predict the output
from functools import reduce
a=[5,3,9,1,6,8]

m=reduce(lambda x,y: x*y , a)
print(m)