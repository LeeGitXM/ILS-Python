'''
Created on Feb 10, 2015

@author: rforbes
'''

def parseBracketedScopeReference(bracketedRef):
    '''
    Break a bracked reference into location and key--e.g. {local:selected-emp.val} gets
    broken into 'local' and 'selected-emp.val'
    '''   
    colonIndex = bracketedRef.index(':')
    location = bracketedRef[1 : colonIndex].strip()
    key = bracketedRef[colonIndex + 1 : len(bracketedRef) - 1].strip()
    return location, key

def findBracketedScopeReference(string):
    '''
     Find the first bracketed reference in the string, e.g. {local:selected-emp.val}
     or return None if not found
     '''
    lbIndex = string.find('{')
    rbIndex = string.find('}')
    colonIndex = string.find(':')
    if lbIndex != -1 and rbIndex != -1 and colonIndex != -1 and colonIndex > lbIndex and rbIndex > colonIndex:
        return string[lbIndex : rbIndex+1]
    else:
        return None

def substituteScopeReferences(chartProperties, stepProperties, sql):
    ''' Substitute for scope variable references, e.g. 'local:selected-emp.val'
    '''
    from ils.sfc.gateway.api import s88Get
    # really wish Python had a do-while loop...
    while True:
        ref = findBracketedScopeReference(sql)
        if ref != None:
            location, key = parseBracketedScopeReference(ref)
            value = s88Get(chartProperties, stepProperties, key, location)
            sql = sql.replace(ref, str(value))
        else:
            break
    return sql

