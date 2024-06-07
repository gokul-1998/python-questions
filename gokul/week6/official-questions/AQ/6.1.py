# Execute the following code. Why do you think this happens?

def remove():
    L.pop()

    
L = list(range(5))
print('before:', L)
remove()
print('after:', L)