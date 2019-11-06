'''
Created on Nov 13, 2016

@author: Pete
'''

import system, string, time
logger = system.util.getLogger("com.ils.test.runner")

def simplePlayer(filename):
    logger.tracef("Starting a simplePlayer with <%s>...", filename)
    
    exists = system.file.fileExists(filename)
    if not(exists):
        logger.errorf("ERROR: file <%s> does not exist!", filename)
        return
    
    tags, data = load(filename)
    
    for record in data:
        for i in range(0, len(tags)):
            tag = tags[i]
            val = record[i]
            val = val.strip('\n')
            #print "  ...writing", val, " to ", tag
            system.tag.write(tag, val)
        time.sleep(60)
    logger.tracef("...simplePlayer is finished!")


def load(filename):
    # This takes a comma delimited text string, does some formatting and adds it to tha tag list
    
    #-------------------------------------------------------------------------------------
    def tagTokens(txt):
        tokens = txt.split(',')
        
        # The first token should be blank because the first column is always the datetime
        tags = []
        
        for token in tokens:
            if (token != "" and token != "\n"):
                token = string.replace(token, '.', '/')
                tags.append(token)
        
        return tags
    #-------------------------------------------------------------------------------------
    def dataTokens(txt, data, maxColumns):
        # Ignore lines that begin with a # because it is a comment
        if (txt[0] != "#"):
            tokens = txt.split(',')
        
            # The first token should be blamk because the first column is always the datetime
            record = []
            i = 0
        
            for token in tokens:
                if (token != "" and token != "\n" and i <= maxColumns):
                    record.append(token)
                i = i + 1
    
            # If the number of tokens doesn't match the number of columns then the record is of no use.
            if len(record) == maxColumns:
                data.append(record)
    
        return data
    #-------------------------------------------------------------------------------------    

    print "   ...loading data: " + filename
    
    i = 0
    data = []
    for line in open(filename):
        print line
        
        if (i == 0):
            tags = tagTokens(line)
            cols = len(tags)
            print "Tags: ", tags
            print "*** There are %i columns ***" % (cols)
        else:
            data = dataTokens(line, data, cols)            

        i = i + 1

    print "Data: ", data
    return tags, data
    
#
# Count the number of data lines in the file
def numLines(filename):
#    print "Filename: " + filename
    
    i = 0
    data = []
    for line in open(filename):
        i = i + 1

#    print "Data: ", data
    return i - 1

# Write the first row of data values to the tags, after that the writing is synchronized with the end of a cycle
def prime(tags, data):
    print "Priming the tag values..."
    record = data[0]
    for i in range(0, len(tags)):
        tag = tags[i]
        val = record[i]
        val = val.strip('\n')
#        print "  ...writing", val, " to ", tag
        system.tag.write(tag, val)

# Play the next datapoint from the caches datafile.
# Return True (finished) if there is no more data signalling that the test must be complete
def playNextPoint(cycle, results):
    print "Playing the next point..."
    tags = results.get("dataTags")
    data = results.get("data", [])
#    print "The tags are: ", tags
#    print "The data is:", data
    numPoints = len(data)
    if numPoints < cycle:
        print "No more data"
        return True
    
    datum = data[cycle - 1]
    print "The current datum is:", datum
    
    if len(datum) <> len(tags):
        print "Unable to play next datum because of a length mismatch between tag list and data. ", tags, datum
        return True

    for i in range(0, len(tags)):
        tagName = tags[i]
        val = datum[i]
        print "  ...writing %s to %s" % (str(val), tagName)
        system.tag.write(tagName, val)

    return False