'''
Created on Sep 13, 2016

@author: ils

This is used exclusively by the SQA Final Test and should NOT be used (or at least
modified for any other purpose).
'''

def diff(resultFilename, goldenFilename, logger, dateColumn=False, verbose=False):
    import system

    def readFile(filename):
        logger.tracef("   ...reading the file %s...", filename)
        i = 0
        data = []

        contents = system.file.readFileAsString(filename, "US-ASCII")
        records = contents.split('\n')    
        for line in records:
            if (i == 0):
                header = line.split(',')
                logger.tracef("  Header: %s - %d", line, len(header))
            else:
                tokens = line.split(',')
                logger.tracef("  Line: %s - %d", line, len(tokens))
                data.append(tokens)    

            i = i + 1
        
        ds = system.dataset.toDataSet(header, data)
        logger.trace("   ...done loading file!")
        return ds

    def compare(dsResult, dsGolden):
        logger.trace("   ...comparing the datasets...")
        result = True
        explanation = []
        for row in range(dsResult.rowCount):
            logger.trace("Row: %s" % (row))
            resultData = ""
            goldData = ""
            for col in range(dsResult.columnCount):
                if (dateColumn and col > 0) or not(dateColumn): 
                    valResult = dsResult.getValueAt(row, col)
                    valGolden = dsGolden.getValueAt(row, col)
                    #print "Comparing ", valResult, " to ", valGolden
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

    logger.infof("Comparing results: ")
    
    logger.tracef( "...checking if <%s> exists..." % (resultFilename))
    if not(system.file.fileExists(resultFilename)):
        logger.warn( "The result file (%s) does not exist!" % (resultFilename))
        return False, "The result file (%s) does not exist!" % (resultFilename)

    logger.tracef( "...checking if <%s> exists..." % (goldenFilename))
    if not(system.file.fileExists(goldenFilename)):
        logger.warn( "The golden file (%s) does not exist!" % (goldenFilename))
        return False, "The golden file (%s) does not exist!" % (goldenFilename)

    logger.tracef( "...reading <%s>..." % (resultFilename))
    dsResult = readFile(resultFilename)
    
    logger.tracef( "...reading <%s>..." % (goldenFilename))
    dsGolden = readFile(goldenFilename)
    
    logger.trace("   ...performing gross file comparisons...")
     
    if     dsResult.rowCount != dsGolden.rowCount:
        logger.warn("The files have different numbers of rows!")
        logger.warn("  %s: %i rows" % (resultFilename, dsResult.rowCount))
        logger.warn("  %s: %i rows" % (goldenFilename, dsGolden.rowCount))
        return False, "The files have different numbers of rows!"

    if     dsResult.columnCount != dsGolden.columnCount:
        logger.warn("The files have different numbers of columns!")
        logger.warn("  %s: %i columns" % (resultFilename, dsResult.columnCount))
        logger.warn("  %s: %i columns" % (goldenFilename, dsGolden.columnCount))
        return False, "The files have different numbers of columns!"

    result, explanation = compare(dsResult, dsGolden)
    
#    print "Result ", result
    
    if not(result):
        logger.warn("The output file (%s) did not match the gold file (%s)!" % (resultFilename, goldenFilename))
        for t in explanation:
            logger.warn(t)

    return result, explanation