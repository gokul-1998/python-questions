# Predict the output of the following code:
# Hint given below as well.
try:
  # The code inside the 'try' block is where you put code that might cause an error.
  numerator = 10
  denominator = 0

  # This line will cause a ZeroDivisionError because we are dividing by zero.
  result = numerator / denominator

  print(f"The result is: {result}")

except ZeroDivisionError:
    # The code inside the 'except' block is what runs if the specific error happens.
  print("Oops! You can't divide a number by zero. That's a math rule!")


print("\nThe program continues to run after the try-except block.")
