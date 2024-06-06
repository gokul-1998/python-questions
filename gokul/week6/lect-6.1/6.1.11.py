# importing libraries
import time
import math
 
# decorator to calculate duration
# taken by any function.
def calculate_time(func):
     
    # added arguments inside the inner1,
    # if function takes any arguments,
    # can be added like this.
    def inner1(*args, **kwargs):
 
        # storing time before function execution
        begin = time.time()
         
        func(*args, **kwargs)
 
        # storing time after function execution
        end = time.time()
        print("Total time taken in : ", func.__name__, end - begin," seconds")
 
    return inner1
 
# this can be added to any function present,
# in this case to calculate a factorial
@calculate_time
def is_present(num,iter):
    print(num in iter)

list_start=time.time()
lis=list(range(10000000))
list_end=time.time()
print("list creation time",list_end-list_start)

set_start=time.time()
sett=set(range(10000000))
set_end=time.time()

print("set creation time",set_end-set_start)


is_present(-1,lis)
is_present(-1,sett)
