'''
Created on Feb 10, 2015

@author: rforbes
'''
def getEnclosingStepScope(adict):
    key = 'enclosingStepScope'
    if adict == None:
        return None
    elif key in adict:
        return adict[key]
    else:
        return None

def getRecipeScope(chartScope, stepScope, scope):
    from ils.sfc.common.constants import LOCAL_SCOPE, PREVIOUS_SCOPE, SUPERIOR_SCOPE
    if scope is LOCAL_SCOPE:
        return stepScope
    elif scope is PREVIOUS_SCOPE:
        return stepScope['previous']
    elif scope is SUPERIOR_SCOPE:
        return getEnclosingStepScope(chartScope)
    else: # search enclosing step scope
        enclosingStepScope = stepScope
        s88ScopeKey = 's88Level'
        while enclosingStepScope != None and s88ScopeKey in enclosingStepScope:
            if enclosingStepScope[s88ScopeKey] is scope:
                return enclosingStepScope
            else:
                chartScope = chartScope['parent']
                enclosingStepScope = getEnclosingStepScope(chartScope)
    return None

def pathGet(adict, path):
    '''get a value from a nested dictionary via a dot-separated path'''
    keys = path.split()
    value = adict
    for key in keys:
        value = value[key]
    return value

def pathSet(adict, path, value):
    '''set a value from a nested dictionary via a dot-separated path'''
    keys = path.split()
    numKeys = len(keys)
    subdict = adict
    for key in keys[0:numKeys-2]:
        subdict = value[key]
    subdict[keys[numKeys-1]] = value

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

