import system, math
# Common constant used in error function (erf) and inverse error function (inverf)
const_a = 0.147

def erf(x):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        This is an approximation to the error function that is used in calculating the cumulative distribution
        function for the normal distribution.  The constant of 0.147 was chosen to reduce the maximum error 
        in the range of -4 to 4 standard deviations to 0.000012.
        
    Change Log:
    """
    exp_arg = -(x**2)*((4.0/math.pi + const_a*(x**2))/(1.0 + const_a*(x**2)))
    erf = sign(x) * math.sqrt(1 - math.exp(exp_arg))
    
    return erf
    
def sign(x):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        Simple sign function that seems to be missing from Jython 2.5.  Return the sign of the given number.
        Value of 0.0 is arbitrarily given a positive sign.
        
    Change Log:
    """
    if x == 0.0:
        sign = 1.0
    else:
        sign = abs(x)/x
    
    return sign

def inverf(x):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        This is the inverse function of the error function given above.
        
    Change Log:
    """
    arg1 = ((2.0/(math.pi * const_a))+(math.log(1.0 - x**2))/2.0)
    arg2 = math.log(1 - x**2)/const_a
    
    inverf = sign(x)*math.sqrt(math.sqrt(arg1**2 - arg2) - arg1)
    return inverf

def factorial(i, j):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        Factorial function as Jython 2.5 did not seem to have one.
        
    Change Log:
    """
    ans = 1
    for k in range(i, j + 1):
        ans = ans * k
    
    return ans

def ncombr(n, k):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        Function to calculate the number of combinations of k objects out of a possible n.  This is combinations and not
        permutations - order does not matter.
        
    Change Log:
    """
    nfact = factorial(1, n)
    kfact = factorial(1, k)
    nkfactorial = factorial(1, n - k)
    
    ans = nfact / (kfact * nkfactorial)
    
    return ans

def eventProbility(prob, payload):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        Calculates the one-sided probability of a value being outside of the limits that correspond to a probability prob.
        Only the first two values in the payload are required.
        
    Change Log:
    """
    # Get the population (n) and out-of-range points (m).
    n = payload[0]
    m = payload[1]
    
    # Inductive proof can be used to prove the following formula.
    sum = 0.0
    for i in range(0, (n - m + 1)):
        sum = sum + ncombr(n, i) * (prob**(n - i))*((1 - prob)**i)
        
    return sum
    
def calculateConfidence(n, m, L):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        Given m out of n test and the desired number of standard deviations (L), calculate the confidence that this test will not
        be true as a result of normal variation.  Note that this is assuming a one-sided test as the SQC-Blocks in the 
        Diagnostic toolkit assume that directionality can be inferred.
        
    Change Log:
    """
    # The factor of root(2) is a result of the normal distribution cumulative distribution function.
    w = L/math.sqrt(2)
    
    # 0.5(1 + erf(w)) is the probability of a point being less then the given limit (L) - call it P.  We need 1 - P meaning
    #  we need the probability of a violation.
    p = 1 - 0.5*(1 + erf(w))
    
    # Calculate the cumulative probability that results in the various combinations of test violation.
    cumProb = eventProbility(p, [n, m])
    
    # The cumProb is the probability of a violation so the confidence is that number from one.
    return 1 - cumProb

def findBoundRoot(FunctionName, lowerBound, upperBound, tol, maxiter, eps, payload):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        This is a fairly efficient bisection method for finding bounded roots that was translated from an old FORTRAN book.
        Hence the use of fairly ambiguous variable names.  The variables tol and eps are tuning constants with tol being the main
        knob (see code below).  Tol is the consistent tolerance whereas eps in used as a weighting on the currently held end point.
        An eps value of 3.0e-8 has been seen consistently.  Clearly tol must be greater than the given eps value.
        
    Change Log:
    """
    z = lowerBound
    b = upperBound
    
    fa = FunctionName(z, payload)
    fb = FunctionName(b, payload)
    
    if ((fa > 0.0) and (fb > 0.0)) or ((fa < 0.0) and (fb < 0.0)):
        print "Error: findBoundRoot - bounds do not bracket a root"
        return
    
    c = b
    fc = fb
    for iter in range(1, maxiter + 1):
        if ((fb > 0.0 and fc > 0.0) or (fb < 0.0 and fc < 0.0)):
            c = z
            fc = fa
            d = b - z
            e = d
            
        if (abs(fc) < abs(fb)):
            z = b
            b = c
            c = z 
            fa = fb
            fb = fc
            fc = fa
        
        tol1 = 2 * eps * abs(b) + 0.5*tol
        xm = 0.5 * (c - b)
        if (abs(xm) <= tol1 or fb == 0.0):
            return b
        
        if (abs(e) >= tol1 and abs(fa) > abs(fb)):
            s = fb/fa
            if (z == c):
                p = 2 * xm * s
                q = 1 - s
            else:
                q = fa/fc
                r = fb/fc
                p = s * (2*xm*q*(q - r) - (b - z)*(r - 1))
                q = (q - 1)* (r - 1)* (s - 1)
                
            if (p > 0.0):
                q = -q
            
            p = abs(p)
            if (2*p < min(3*xm*q - abs(tol1*q), abs(e*q))):
                e = d
                d = p/q
            else:
                d = xm
                e = d
        else:
            d = xm
            e = d
            
        z = b
        fa = fb
        if (abs(d) > tol1):
            b = b + d
        else:
            b = b + sign(xm)*tol1
            
        fb = FunctionName(b, payload)
        
    print "findBoundRoot: Exceeded maximum iterations!"
    return b

def calculateStdDev(n, m, Conf):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        Given the m out of n test with a desired confidence, calculate the required number of standard deviations from the
        target.  Note that this uses a root-finding function so there will be some error associated with the calculation
        even above that of the approximations that are used for the normal distribution function.
        
    Change Log:
    """
    # Given confidence is that a test violation means a data shift and is not a result of normal variation.  To calculate the
    # number of standard deviations, we need the opposite probability.  Note this is a one-sided test as directionality is
    # is assumed.
    cumProb = 1.0 - Conf
    
    # Use the probability objective function with probability bounded between 0 and 1.  Tuning of root finding was by trial
    # and error with the value for eps taken directly from the FORTRAN package with no change.
    sampleProb = findBoundRoot(probabilityObjFunc, 0.0, 1.0, 1.0e-5, 1000, 3.0e-8, [n, m, cumProb])
    W = inverf(2.0*(1.0 - sampleProb) - 1.0)
    
    # Must remember the root(2) scaling as a result of the cumulative probability function for the normal distribution.
    return W * math.sqrt(2.0)

def probabilityObjFunc(p, payload):
    """
    Originator:  Michael J. Kurtz
    Date:        Oct. 31, 2017
    
    Description:
        Need to setup the objective function for finding the probabilities that corresponds to a given confidence.  The 
        confidence is converted to a desired probability which is then used to obtain a function whose roots will be 
        event probabilities.  Note that if there was to exist multiple roots, no attempt is made to find them all and 
        then reason to the "correct" one.
        
    Change Log:
    """
    desiredProb = payload[2]
    val = desiredProb - eventProbility(p, payload)
    
    return val