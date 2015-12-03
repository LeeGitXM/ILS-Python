'''
Created on Oct 30, 2015

@author: rforbes
'''
class TestClass:
    def  __init__(self):
        # assign ctor args to instance vars (ivars need not be declared)
        #self.window = _window
        self.myName = 'Fred'
        pass
 
    def sayHi(self):
        print'Hi Rob! I made it! My name is %s' % (self.myName)