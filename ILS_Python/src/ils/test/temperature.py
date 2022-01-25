
def degreeConverter(degC):
        degF = degC * 9.0 / 5.0 + 32.0
        print "Converted ", degC, " to ", degF
        
        ones = int(degF % 10)       
        degF = (degF - ones) / 10
        tens = int(degF % 10)
        hundreds = int((degF - tens) / 10)
        print hundreds, "  ", tens, "  ", ones
        
testData = [0.0, 37.2, 44.647, 100.0]
for degC in testData:
    degreeConverter(degC)