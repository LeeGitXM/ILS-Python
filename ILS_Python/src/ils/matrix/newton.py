'''
Created on Aug 22, 2019

@author: phass
'''
import system, math
import org.apache.commons.math3.linear.Array2DRowRealMatrix as Matrix
import org.apache.commons.math3.linear.LUDecomposition as LUDecomposition
import org.apache.commons.math3.linear.ArrayRealVector as Vector
from ils.matrix.util import fmin, fdjac, maxOfFirstColumn, lnsrch
from ils.sfc.common.util import logExceptionCause
from ils.log import getLogger
log = getLogger(__name__)

def solverGlobal(x, func, maxIterations):
    '''
    Subroutine taken from "Numerical Recipes in FORTRAN (2nd ed)", Chap. 9, Sec 7 on globally convergent methods for nonlinear system of equation solving.

   1. Given initial guesses for x, find the roots of a system of nonlinear equations F(x) = 0 using a GLOBALLY convergent Newton's method. Best convergence occurs when x's are scaled 0 to 1.
   2. User supplies the named procedure fx_PROC that calculates F(x) at a set of x's.
   3. Return of TRUE for check for converged indicates a solution was found BUT could be spurious.
    '''
    log.infof("Entering %s.solverGlobal()...", __name__)
    
    tolFx = 1.0e-12      # Tolerance on each F(x) at/near zero
    tolFmin = 1.0e-14 # Tolerance on func (fmin) at/near zero
    tolEPS = 1.0e-8      # Convergence on deltax at/near zero (typically, sqrt(machine precision))
    stepMx = 100.0      # Max step size in x per iteration
    
    checkConverge = False
    numIterations = 0
    
    nRows = x.getRowDimension()
    nCols = x.getColumnDimension()
    
    xOld = Matrix(nRows, nCols)
    fx = Matrix(nRows, nCols)
    g = Matrix(nRows, nCols)
    
    ''' Test for already at root solution for x's '''
    fNew = fmin(x, fx, func)
    log.tracef("   fMin(x) initially = %f", fNew)
    
    maxVal = maxOfFirstColumn(fx)
    
    if maxVal < 0.01 * tolFx:
        log.infof("   %f < tol (%f).  Initial guesses for x's are root solutions!", maxVal, 0.01 * tolFx)
        return checkConverge, numIterations
    
    test = 0.0
    for i in range(nRows):
        test = test + x.getEntry(i, 0) ** 2
    stepMax = stepMx * math.sqrt(test)
    log.tracef("stepMax = %f", stepMax)
    
    try:
        for iteration in range(1, maxIterations + 1):
            log.tracef("Starting iteration #%d...", iteration)
            
            '''  Jacobian (J) by finite difference partial derivatives (versus analytical). '''
            dfxDx = fdjac(x, fx, func, tolEPS)
            log.tracef("   dfxDx: %s", str(dfxDx))
            
            for i in range(nRows):
                test = 0.0
                for j in range(nRows):
                    test = test + dfxDx.getEntry(j, i) * fx.getEntry(j, 0)
                g.setEntry(i, 0, test)
            log.tracef("   g: %s", str(g))
        
        
            fxLU=Vector(nRows)
            for i in range(nRows):
                fxLU.setEntry(i, -1 * fx.getEntry(i, 0))
        
            log.tracef("   matrix input to LU decomposition is: %s", str(dfxDx))
            solver = LUDecomposition(dfxDx).getSolver()
            log.tracef("   vector input to LU decomposition is: %s", str(fxLU))
            dxLU = solver.solve(fxLU)
            log.tracef("   solver returned: %s", str(dxLU))
            
            dx = Matrix(nRows, nRows)
            for i in range(nRows):
                dx.setEntry(i, 0, dxLU.getEntry(i))
            
            for i in range(nRows):
                xOld.setEntry(i, 0, x.getEntry(i, 0))
            
            checkConverge, fNew = lnsrch (x, xOld, fNew, fx, func, g, dx, stepMax, tolEPS)
            log.tracef("   linear search returned %s - %f", str(checkConverge), fNew)
            
            test = 0.0
            for i in range(nRows):
                test = max(test, abs(fx.getEntry(i, 0)))
            log.tracef("   f(x) max = %f", test)
        
            if (test < tolFx):
                ''' Converged function values (at root solutions for x's) '''
                checkConverge = False
                log.infof("   %f < tol (%f) with checkConverge: %s - F(x) values at/near zero.", test, tolFx, str(checkConverge))
                return checkConverge, numIterations
                
            test = 0.0;
            for i in range(nRows):
                test = max(test, abs(g.getEntry(i, 0)) * max(1.0, abs(x.getEntry(i, 0))) / max(fNew, 0.5 * nRows))
            log.tracef("   deltaf * deltax (gradient) max = %f", test)
            
            rechk_convg = checkConverge;
            if (checkConverge):
                if (test < tolFmin):
                    checkConverge = True        # Gradient of f near zero (but could be spurious convergence)
                    log.tracef("   %f < tol (%f) with checkConverge: %s - Gradient near zero (could be spurious).", test, tolFmin, checkConverge)
                else:
                    checkConverge = False       # At root solutions for x's
                    log.tracef("   Roots found with checkConverge: %s - converged solution for x's!", str(checkConverge))
    
            if (rechk_convg and test < tolFmin):
                ''' fmin close to zero (may or may not be at root solutions of x's)'''
                return checkConverge, numIterations
    
            test = 0.0
            for i in range(nRows):
                test = max(test, abs(x.getEntry(i,0) - xOld.getEntry(i,0)) / max(1.0, abs(x.getEntry(i,0))))
    
            log.tracef("deltax / x max = %f", test)
            
            ''' deltax close to zero (small change in x not changing F(x) significantly) '''
            if (test < tolEPS):
                log.infof("   %f < tol %f with %s - deltax / x close to zero. Check solution!", test, tolEPS, str(checkConverge))
                return checkConverge, numIterations    
        
        checkConverge = True
        log.infof("   ...leaving %s.solverGlobal() because max iterations has been reached!", __name__)
    except:
        checkConverge = True
        logExceptionCause("Error in  %s.solverGlobal() with ERROR!" % (__name__), log)
        log.infof("   ...leaving %s.solverGlobal() with ERROR!", __name__)
    
    return checkConverge, numIterations

def solverLocal(x, func, maxIterations):
    
    checkConverge = True
    numIterations = 0
    
    return checkConverge, numIterations

def test(fx):
    print "In test()..."
    fx.setEntry(2,2, 88.19)