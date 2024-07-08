x=['a','b','c','a','b','a']

dicc={}

for i in x:
    if i not in dicc:
        dicc[i]=1
    else:
        dicc[i]+=1

#  what will be the output of the following code?