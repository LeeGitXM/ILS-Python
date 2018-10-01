'''
Created on Aug 9, 2018

@author: phass
'''
import system, time

def tagChangeA():
    print "Starting tagChangeA()"
    
    a = 23
    b = 26
    
    def longProcessaA(a=a, b=b):
        longProcess(a,b)

    system.util.invokeAsynchronous(longProcessaA)

def tagChangeB():
    print "Starting tagChangeB()"
    
    a = 134
    b = 789
    
    def longProcessaB(a=a, b=b):
        longProcess(a,b)

    system.util.invokeAsynchronous(longProcessaB)
        
def longProcess(a, b):
    print "A = ", a
    print "B = ", b
    time.sleep(2)
    print "All Done!"