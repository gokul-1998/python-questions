# Predict the output of the following code snippet:
try:
    # Let's try to convert a word into a number. This will cause a ValueError.
    number = int("hello")
    print(f"The number is: {number}")

except ValueError:
    # This block catches the 'ValueError'.
    print("\nOops! You can't turn the word 'hello' into a number.")

print("Program finished.")