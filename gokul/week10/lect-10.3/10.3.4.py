# predict the output


class Student:
    def __init__(self,name,roll=None):
        self.name=name
        self.roll=roll


    def display(self):
        print(self.roll,self.name)

obj1=Student(1,"Gokul")
obj1.display()

obj2=Student(name="aswin")
obj2.display()

obj3=Student("Gokul")
obj3.display()

obj4=Student(roll=13)
obj4.display()