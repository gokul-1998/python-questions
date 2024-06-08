# predict the output


class Student:
    def __init__(self,name,roll):
        self.name=name
        self.roll=roll


    def display(self):
        print(self.roll,self.name)

obj1=Student(1,"Gokul")
obj2=Student(name="aswin",roll=12)

obj1.display()
obj2.display()