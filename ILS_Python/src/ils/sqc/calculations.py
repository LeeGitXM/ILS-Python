'''
Created on Oct 30, 2017

@author: Mike
'''
import system, math

def erf(x):
    const_a = 0.147
    exp_arg = -(x**2)*((4.0/math.pi + const_a*(x**2))/(1.0 + const_a*(x**2)))
    erf = sign(x) * math.sqrt(1 - math.exp(exp_arg))
    #print "erf = ", erf
    
    return erf
    
def sign(x):
    if x == 0.0:
        sign = 1.0
    else:
        sign = abs(x)/x
        
    return sign

def inverf(x):
    const_a = 0.147
    print "x = ", x
    arg1 = ((2.0/(math.pi * const_a))+(math.log(1.0 - x**2))/2.0)
    arg2 = math.log(1 - x**2)/const_a
    
    inverf = sign(x)*math.sqrt(math.sqrt(arg1**2 - arg2) - arg1)
    return inverf

def factorial(i, j):
    ans = 1
    for k in range(i, j):
        ans = ans * k
    
    return ans

def ncombr(n, k):
    nfact = factorial(1, n)
    kfact = factorial(1, k)
    nkfactorial = factorial(1, n - k)
    
    ans = nfact / (kfact * nkfactorial)
    
    return ans

def eventProbility(prob, payload):
    n = payload[0]
    #print "n = ", n
    m = payload[1]
    #print "m = ", m
    #print "range = ", range(n - m + 1)
    sum = 0.0
    for i in range(0, (n - m + 1)):
        sum = sum + ncombr(n, i) * (prob**(n - i))*((1 - prob)**i)
    
    #print "Sum Prob = ", sum
    return sum
    
def calculateConfidence(n, m, L):
    
    w = L/math.sqrt(2)
    p = 1 - 0.5*(1 + erf(w))
    #print "p = ", p
    
    combProb = eventProbility(p, [n, m])
    
    return 1 - combProb

def findBoundRoot(FunctionName, lowerBound, upperBound, tol, payload):
    maxiter = 100
    eps = 3.0e-8
    z = lowerBound
    b = upperBound
    
    fa = FunctionName(z, payload)
    print "fa = ", fa
    fb = FunctionName(b, payload)
    print "fb = ", fb
    if ((fa > 0.0) and (fb > 0.0)) or ((fa < 0.0) and (fb < 0.0)):
        print "Error: findBoundRoot - bounds do not bracket a root"
        return
    
    c = b
    fc = fb
    for iter in range(1, maxiter + 1):
        if ((fb > 0.0 and fc < 0.0) or (fb < 0.0 and fc < 0.0)):
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
    combProb = 1 - Conf
    
    sampleProb = findBoundRoot(eventProbility, 0.0, 1.0, 1.0e-3, [n, m])
    W = inverf(2.0*(1.0 - sampleProb) - 1.0)
    
    return W * math.sqrt(2.0)