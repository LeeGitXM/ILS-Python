'''
Created on Aug 23, 2019

@author: phass
'''
import system, math
log = system.util.getLogger("com.ils.matrix.util")
import org.apache.commons.math3.linear.Array2DRowRealMatrix as Matrix

def fmin (x, fx, func):
    '''
    Subroutine taken from "Numerical Recipes in FORTRAN (2nd ed)", Chap. 9, Sec 7 on globally convergent methods for nonlinear system of equation solving.

   1. Calculates f = 1/2 * F(x) * F(x) at x.
   2. User supplies the named procedure fx_PROC that calculates the F(x) at a set of x's
    '''
    func(x, fx)
    nRows = fx.getRowDimension()
    
    test = 0.0
    for i in range(nRows):
        test = test + fx.getEntry(i, 0) ** 2
    test = 0.5 * test;
    
    return test


def fdjac (x, fx, func, tolEPS):
    '''
    Routine taken from "Numerical Recipes in FORTRAN (2nd ed)", Chap. 9, Sec 7 on globally convergent methods for nonlinear system of equation solving.

   1. Calculates the forward-difference approximation to the Jacobian (finite difference partial derviatives).
   2. Jacobian retuned is a square matrix.
   3. User supplies the named procedure fx_PROC that calculates F(x) at a set of x's.
   4. User must manage (transfer, delete) the created matrix "dfx_dx" when done using in the calling procedure.
   
   Arguments:
       x: class matrix {root solutions}
       fx:  class matrix {F(x) values}
       func: function to calculate F(x)}
       tolEPS: float {square root of machine precision}
    '''
    
    log.tracef("In %s.fdjac()...", __name__)
    nRows = x.getRowDimension()
    nCols = x.getColumnDimension()
    
    dfxDx = Matrix(nRows, nRows)
    xDx = Matrix(nRows, nCols)

    for i in range(nRows):
        val = x.getEntry(i, 0)
        xDx.setEntry(i, 0,val)

    fxDx = Matrix (nRows, nCols)
    
    '''
    Calculate the Jacobian (partial derivatives) for each x+dx.}
    '''
    for j in range(nRows):
        tol = tolEPS * abs(x.getEntry(j, 0))
        if tol == 0:
            tol = tolEPS
            
        xDx.setEntry(j, 0, x.getEntry(j, 0) + tol)
         
        ''' Reduce finite precision error in calculations '''
        tol = xDx.getEntry(j, 0) - x.getEntry(j, 0) 
    
        ''' Calculate F(x+dx) '''
        func(xDx, fxDx)
    
        ''' Reset x+dx back to x for next partial derivative '''
        xDx.setEntry(j, 0, x.getEntry(j, 0)) 
        
        for i  in range(nRows):
            ''' Forward difference partial derivative '''
            dfxDx.setEntry(i, j, fxDx.getEntry(i, 0) - fx.getEntry(i, 0) / tol)
    
    log.tracef("...leaving %s.fdjac()!", __name__)
    return dfxDx

def lnsrch (x, xOld, fOld, fx, func, g, dx, stepMax, tol_EPS):
    '''
    { Subroutine taken from "Numerical Recipes in FORTRAN (2nd ed)", Chap. 9, Sec 7 on globally convergent methods for nonlinear system of equation solving.

   1. Given initial guesses for x, F(x), the gradient (deltaf or g) at x, and delta x (dx), find new x along the direction (slope).
   2. Use line search method for xnew = xold + lamda*deltax. Quadratic convergence.
   3. chk_convg is normally FALSE on a normal exit. TRUE indicates spurious convergence possible (round off error, etc giving false indication of convergence). If TRUE, user needs to verify solution really found.
   4. User supplies the named procedure PROC that returns the vector of functions ( F(x) ) at x.
   
   Arguments:
       x: class matrix {root solutions}, 
       xold: class matrix {previous root solutions}, 
       fold: float {func at previous x's}, 
       fx: class matrix {current F(x) values}, 
       fx_PROC: symbol {procedure to calculate F(x)}, 
       g: class matrix {gradient}, 
       dx: class matrix {deltax}, 
       stepmax: float {max step of x}, 
       tol_EPS: float {precision in x for converge})
    Returns:
        truth-value {check for convergence}
        float {func at new x's})
    '''
    
    log.tracef("Entering %s.lnsrch()...", __name__)
    maxIterations = 100     # Not sure what this should be, the old system would run for up to 5 minutes.
    tolALF = 1.e-4  # 0 < alf < 1

    nRows = x.getRowDimension()
    step = 0.0
    for i in range(nRows):
        step = step + dx.getEntry(i, 0) ** 2
    step = math.sqrt(step)
    log.tracef("Step: %f", step)

    ''' Limit deltax step size '''
    if (step > stepMax):
        log.tracef("Recalculating dx (deltax's) due to step %f > stepMax %f", step, stepMax)
        scalerMultiply (dx, stepMax / step)

    slope = 0.0;
    for i in range(nRows):
        slope = slope + g.getEntry(i, 0) * dx.getEntry(i, 0)

    if slope > 0:
        log.tracef("Slope (%f) > 0, roundoff error. Check initial guesses.", slope)

    ''' Calculate lambda minimum (to know convergence on deltax).  '''
    lamMin = 0.0
    for i in range(nRows):
        lamMin = max (lamMin, abs(dx.getEntry(i, 0)) / max(abs(xOld.getEntry(i, 0)), 1.0))
    
    lamMin = tol_EPS / lamMin
    log.tracef("Lam(min): ", lamMin)

    ''' 
    Linesearch solving for f(xnew) <= f(xold) + alpha*deltaf*(xnew - xold). 
    Alpha is a fraction used to control the rate of decrease of f subject to the initial rate of decrease deltaf*deltax.}
    Lambda initially starts at 1. Limits are 0.1*lambda(old) <= lambda <= 0.5*lambda(old) for each move.
    '''
    lam1 = 1.0
    lam2 = 0.0
    fnew = 0.0
    fnew2 = 0.0
    
    j = 0   # Used to count loops through convergence
    while (j < maxIterations):
        log.tracef("iteration: %d, lam1: %f, lam2: %f.", j, lam1, lam2)
        
        for i in range(nRows):
            x.setEntry(i, 0, xOld.getEntry(i, 0) + lam1 * dx.getEntry(i, 0))
        
        fNew = fmin (x, fx, func)

        ''' Converged on deltax but could be spurious (check)  '''
        if (lam1 < lamMin):
            for i in range(nRows):
                x.setEntry(i, 0, xOld.getEntry(i, 0))
        
            log.tracef("lam %f < lam_min %f.", lam1, lamMin)
            log.tracef("Leaving %s.lnsrch() - check for spurious convergence.", __name__)
            return True, fNew
        
        elif (fnew <= fOld + tolALF * lam1 * slope):
            ''' Solution found for deltax! '''
            log.tracef("fmin %f <= %f", fnew, (fOld + tolALF * lam1 * slope))
            log.tracef("Leaving %s.lnsrch() - Converged solution at fmin %f", __name__, fNew)
            return False, fNew

        else:
            ''' Find new lambda for next step along gradient.  '''
            if lam1 == 1.0:
                ''' First pass backtracking '''
                temp_lam = -1.0 * slope / (2.0 * (fnew - fOld - slope))
            else: 
                ''' Subsequent passes backtracking '''
                temp1_rhs = fnew - fOld - lam1 * slope
                temp2_rhs = fnew2 - fOld - lam2 * slope
                temp_a = (temp1_rhs / (lam1*lam1) - temp2_rhs / (lam2 * lam2)) / (lam1 - lam2)
                temp_b = (-1.0 * lam2 * temp1_rhs / (lam1 * lam1) + lam1 * temp2_rhs / (lam2 * lam2)) / (lam1 - lam2);
                log.tracef("rhs1 = %f, rhs2 = %f, a = %f, b = %f", temp1_rhs, temp2_rhs, temp_a, temp_b)

            if temp_a == 0.0:
                '''  Protect against divide by zero  '''
                temp_lam = -1.0 * slope / (2.0 * temp_b)
            else:
                temp = temp_b*temp_b - 3.0 * temp_a * slope
                if (temp < 0):
                    temp_lam = 0.5*lam1
                elif (temp_b < 0):
                    temp_lam = (-1.0 * temp_b + math.sqrt(temp)) / (3.0 * temp_a)
                else:
                    temp_lam = -1.0 * slope / (temp_b + math.sqrt(temp))

                temp_lam = min(0.5*lam1, temp_lam)
               
            log.tracef("temp_lam: %f", temp_lam)
            
            fnew2 = fnew
            lam2 = lam1

        ''' Calculate new lambda. Enforce lambda between 0.1*lambda and 0.5*lambda. '''
        lam1 = max(0.1 * lam1, temp_lam)
        
        j = j + 1

    log.tracef("...leaving %s.lnsrch()!", __name__)

def maxOfFirstColumn(x):
    nRows = x.getRowDimension()
    
    maxVal = 0.0
    for i in range(nRows):
        maxVal = max(maxVal, x.getEntry(i, 0))
    return maxVal

def scalerMultiply(m, x):
    nRows = m.getRowDimension()
    nCols = m.getColumnDimension()
    
    for i in range(nRows):
        for j in range(nCols):
            m.setEntry(i, j, m.getEntry(i, j) * x)