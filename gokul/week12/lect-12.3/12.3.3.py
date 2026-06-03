# predic the output
from itertools import accumulate
l=[100,2,4,5,3,4]
subtract=list(accumulate(l,lambda x,y:x-y))
print(subtract)


# Notice something:

# while using accumulate function we don't have to put the iterable after lambda,instead we put it before than lambda

                        