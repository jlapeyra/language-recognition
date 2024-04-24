

class Super1:
    def info(self): return "super 1"
    
class Super2:
    def what(self): print(self.info())

class Sub(Super1, Super2):
    pass

Sub().what()