myVar = 128


class MyClass:
    def __init__(self, localVar):
        pass

    @property
    def localVar(self):
        return myVar

    @localVar.setter
    def localVar(self, v):
        myVar = v


testClass = MyClass(myVar)
print(testClass.localVar)
myVar -= 100
print(testClass.localVar)
