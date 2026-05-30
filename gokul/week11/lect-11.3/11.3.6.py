# Filter function:
#   filter(function, iterable) . It is denotion of filter function.

# predict the output:
 # find even numbers from the given list:
# l=[1,2,3,4,5,6,7,8,9,10,11,14]
def is_even(n):
    if n %2 ==0:
        return n
l=[1,2,3,4,5,6,7,8,9]
even=list(filter(is_even,l))
print(even)
