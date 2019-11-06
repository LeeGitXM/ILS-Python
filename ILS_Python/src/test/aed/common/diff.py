'''
Created on Nov 13, 2016

@author: Pete
'''

import system, os
log = system.util.getLogger("com.ils.aed.test.diff")

def diff(resultFilename, goldenFilename, dateColumn=False, verbose=False):

    def readFile(filename):
        i = 0
        data = []
        for line in open(filename):

            if (i == 0):
                header = line.split(',')

            else:
                tokens = line.split(',')
                data.append(tokens)    

            i = i + 1

        log.tracef("Header: %s", str(header))
        log.tracef("Data: %s", str(data))
        
        ds = system.dataset.toDataSet(header, data)
        return ds

    def compare(dsResult, dsGolden):    
        result = True
        explanation = []
        for row in range(dsResult.rowCount):
            resultData = ""
            goldData = ""
            for col in range(dsResult.columnCount):
                if (dateColumn and col > 0) or not(dateColumn): 
                    valResult = dsResult.getValueAt(row, col)
                    valGolden = dsGolden.getValueAt(row, col)
                    if resultData == "":
                        resultData = str(valResult)
                        goldData = str(valGolden)
                    else:
                        resultData = resultData + "," + str(valResult)
                        goldData = goldData + "," + str(valGolden)
                        
                    # Try to compare as floats, if that doesn't work, compare as strings
                    try:
                        floatResult = round(float(valResult) * 100000.0) / 100000.0
                        floatGolden = round(float(valGolden) * 100000.0) / 100000.0
                        if floatResult != floatGolden:
                            result = False
                            explanation.append("Row %i, Column %i (%s should have been %s) " % (row, col, str(valResult), str(valGolden))) 
                    except:
                        if valResult != valGolden:
                            result = False
                            explanation.append("Row %i, Column %i (%s should have been %s) " % (row, col, str(valResult), str(valGolden))) 
    
#            print resultData
#            print goldData
    
        return result, explanation
        
    #------------------------------------------------------

#    path = os.environ.get('DataOutputDirectory')
#    print "Path: ", path
#    print "Out file: ", outfile
#    print "Gold file: ", goldfile

    # Define the path to the results file in an O/S neutral way
#    resultPath = os.path.join(path,'pid')
#    resultPath = os.path.join(resultPath, 'out')
#    resultPath = os.path.join(resultPath, outfile)
#    print "Result path: ", resultPath

    # Define the path to the Golden file in an O/S neutral way
#    goldenPath = os.path.join(path,'pid')
#    goldenPath = os.path.join(goldenPath,'gold')
#    goldenPath = os.path.join(goldenPath, goldfile)
#    print "Golden path: ", goldenPath
    
    if not(system.file.fileExists(resultFilename)):
        txt="The result file (%s) does not exist!" % (resultFilename)
        log.error(txt)
        return False, txt

    if not(system.file.fileExists(goldenFilename)):
        txt="The golden file (%s) does not exist!" % (goldenFilename)
        log.error(txt)
        return False, txt

    dsResult = readFile(resultFilename)
    dsGolden = readFile(goldenFilename)
    
    if dsResult.rowCount != dsGolden.rowCount:
        log.error("The files have different numbers of rows!")
        log.error("  %s: %i rows" % (resultFilename, dsResult.rowCount))
        log.error("  %s: %i rows" % (goldenFilename, dsGolden.rowCount))
        return False, "The files have different numbers of rows!"

    if dsResult.columnCount != dsGolden.columnCount:
        print "The files have different numbers of columns!"
        print "  %s: %i columns" % (resultFilename, dsResult.columnCount)
        print "  %s: %i columns" % (goldenFilename, dsGolden.columnCount)
        return False, "The files have different numbers of columns!"

    log.info("Comparing the actual results to the golden file...")
    result, explanation = compare(dsResult, dsGolden)
    
#    print "Result ", result
    
    if not(result):
        print " "
        print "The output file (%s) did not match the gold file (%s)!" % (resultFilename, goldenFilename)
        for t in explanation:
            print t

    return result, explanation