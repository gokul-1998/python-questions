# Execute the following code. Why do you think this happens?

P = list(range(10))
Q = P
Q[0] = 100
print(P == Q)
print(P is Q)

