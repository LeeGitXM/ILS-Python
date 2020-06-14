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
            data.append(dataTokens(line, cols))

        i = i + 1

#    print "At the end"
#    print "Data: ", data
    
    dataset = system.dataset.toDataSet(tags, data)
    rootContainer.getComponent("Table").data = dataset


def dataTokens(txt, numColumns):
    '''
    This takes a comma delimited text string and validates the number of tokens
    If a token is a tag then the tagname is written to the array/sequence.
    I'd like to let comments through but I need the array I return to have the right number of elements so that it can conevt it to a dataset.
    '''

    # Ignore lines that begin with a # because it is a comment
    record = [""] * numColumns
    if txt[0] == "#":
        print "Found a comment"
        tokens = txt.split(',')
        record[0] =tokens[0]
    else:
        tokens = txt.split(',')
    
        # The first token should be blamk because the first column is always the datetime
        i = 0
    
        for token in tokens:
            if (token != "\n" and i <= numColumns):
                record[i] = token
            i = i + 1

        # If the number of tokens doesn't match the number of columns then the record is of no use.
#        if len(record) == numColumns:
#            data.append(record)

    print record
    return record

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