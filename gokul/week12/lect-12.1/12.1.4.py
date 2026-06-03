# How to do square and then some of the numbers of the list
from functools import reduce
l=[2,3,4,5,6] 
s=reduce(lambda x,y: (x**2)+(y**2),l)
print(s)

# Predict the output 
# In simple words redunce() function iterate over the same list until it'll come to the end.
# When it iterate over the list like it selects 2 as x and 3 as y after iterating over x it makes y as x and the next value as y 
# This repeats and beside python stores all the value 