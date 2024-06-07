# Execute the following code.
D = dict()

for x in range(-10, 10):
    for y in range(-10, 10):
        if x ** 2 + y ** 2 - 25 < 0:
            D[(x, y)] = 'in'
        elif x **2 + y ** 2 - 25 == 0:
            D[(x, y)] = 'on'
        else:
            D[(x, y)] = 'out'    
        
    # What do you think is happening here?
    # How many points are `in`, how many are `out` and how many are `on`?