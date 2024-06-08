## identify the private attribute


class Person:
    def __init__(self,name,age):
        self.name=name
        self.__age=age


class Student(Person):
    def __init__(self,name,age,roll):
        super().__init__(name,age)
        self.roll=roll

obj=Person("Gokul",20)
print(obj.name)
# to print the private attribute
print(obj._Person__age)
obj=Student("Gokul",20,1)
print(obj.name)
print(obj.roll)
print(obj._Person__age)