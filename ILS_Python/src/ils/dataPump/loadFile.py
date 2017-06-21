'''
Created on Jun 20, 2017

@author: phass
'''

import system

def loadFile(rootContainer, filename):    
    print "Filename: " + filename
    i = 0
    data = []
    for line in open(filename):
        
        if (i == 0):
            tags = tagTokens(line)
            cols = len(tags)
            print "Tags: ", tags
            print "*** There are %d columns ***" % (cols)
        else:
            data = dataTokens(line, data, cols)            

        i = i + 1

#    print "At the end"
#    print "Data: ", data
    
    dataset = system.dataset.toDataSet(tags, data)
    rootContainer.getComponent("Table").data = dataset

'''
This takes a comma delimited text string and validates each of the tokens as tags.
If a token is a tag then the tagname is written to the array/sequence
'''
def dataTokens(txt, data, maxColumns):

    # Ignore lines that begin with a # because it is a comment
    if (txt[0] != "#"):
        tokens = txt.split(',')
    
        # The first token should be blamk because the first column is always the datetime
        record = []
        i = 1
    
        for token in tokens:
            if (token != "" and token != "\n" and i <= maxColumns):
                record.append(token)
            i = i + 1

        # If the number of tokens doesn't match the number of columns then the record is of no use.
        if len(record) == maxColumns:
            data.append(record)

    return data

'''
This takes a comma delimited text string, does some formatting and adds it to the tag list
'''
def tagTokens(txt):
    import string
    
    tokens = txt.split(',')
    print "raw tokens: ", tokens

    tags = []
    
    for token in tokens:
        if (token != "" and token != "\n"):
            token = string.replace(token, '.', '/')
            tags.append(token)
    
    return tags