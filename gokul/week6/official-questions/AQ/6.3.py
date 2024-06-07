# Execute the following code. Why do you think this happens?

A = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]

B = A.copy()

B[0][0] = 100

print(A == B)

print(A is B)