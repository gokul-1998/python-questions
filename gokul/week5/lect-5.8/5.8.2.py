# what should we add in the code so that the error is resolved

def myfunction1():
    
    x=x*2
    print("value of x in function 1",x)

def myfunction2():
    x=x*3
    print("value of x in function 2",x)

x=5
print("value of x before function call",x)
myfunction1()
print("value of x after function call 1",x)
myfunction2()
print("value of x after function call 2",x)
print("value of x after function call",x)