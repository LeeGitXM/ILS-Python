'''
Created on Aug 22, 2019

@author: phass
'''

import system, math
from java.lang import Double
import java.lang.reflect.Array as Array
from ils.matrix.util import scalerMultiply
import org.apache.commons.math3.analysis.solvers.NewtonRaphsonSolver as NewtonRaphsonSolver
import org.apache.commons.math3.linear.LUDecomposition as LUDecomposition
import org.apache.commons.math3.linear.Array2DRowRealMatrix as Matrix
import org.apache.commons.math3.linear.ArrayRealVector as Vector

class MyFunc():
    
    def __init__(self,path):
        print "In __init__"
        
    def value(self, x):
        return math.cos(x)

def foo(x):
    y = x * x
    return y

def bar(x):
    y = x / 2.0
    return y


def testMatrixPassMain():
    print "Testing testMatrixPassMain()..."

    H = Matrix(5, 5)
    H.setEntry(2, 2, 23.5)
    print "val = %f" % (H.getEntry(2,2))
    testMatrixPassSub(H)
    print "...back in main..."
    print "val = %f" % (H.getEntry(2,2))
    
def testMatrixPassSub(H):
    print "Testing testMatrixPassSub()..."

    print "val = %f" % (H.getEntry(2,2))
    H.setEntry(2, 2, 45.9)
    print "val = %f" % (H.getEntry(2,2))
    

def testLuDecomposition():
    m = Matrix(3, 3)
    
    m.setEntry(0, 0, 4)
    m.setEntry(0, 1, 9)
    m.setEntry(0, 2, 11)
    
    m.setEntry(1, 0, 5)
    m.setEntry(1, 1, 3)
    m.setEntry(1, 2, 18)
    
    m.setEntry(2, 0, 8)
    m.setEntry(2, 1, 7)
    m.setEntry(2, 2, 33)
    print "M: ", m
    
    b=Vector(3)
    b.setEntry(0, 3.0)
    b.setEntry(1, 4.0)
    b.setEntry(2, 5.0)
    print "b: ", b
    
    
    solver = LUDecomposition(m).getSolver()
    solution = solver.solve(b)
    
    print "The solution is: ", solution
    
def testScalerMultiply():
    m = Matrix(3, 3)
    
    m.setEntry(0, 0, 4)
    m.setEntry(0, 1, 9)
    m.setEntry(0, 2, 11)
    
    m.setEntry(1, 0, 5)
    m.setEntry(1, 1, 3)
    m.setEntry(1, 2, 18)
    
    m.setEntry(2, 0, 8)
    m.setEntry(2, 1, 7)
    m.setEntry(2, 2, 33)
    print "M (before): ", m
    
    scalerMultiply(m, 2)
    print "M (after): ", m
    