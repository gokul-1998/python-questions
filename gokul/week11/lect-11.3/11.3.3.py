# map(function, iterable)    ;  map denotion

# Predict the output
def square(n):
    return n ** 2
squares = map(square, range(1, 10, 2))
print(list(squares))

#Note: We have to use list function or any other function to store the output in that format otherwise it shows the location.
