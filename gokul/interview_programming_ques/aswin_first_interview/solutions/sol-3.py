# take a number as input, and print the below pattern


# IP : 3
# OP :
'''
  *
 * *
* * *
'''

# IP : 5
# OP :
'''
    *
   * *
  * * *
 * * * *
* * * * *
'''
n=3

for i in range(1,n+1):
    print(" "*(5-i),end="")
    print("* "*i)
