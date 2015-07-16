'''
Created on Feb 10, 2015

@author: rforbes
'''

from ils.sfc.gateway.api import s88Set, s88Get
class RecipeData:
    '''A convenient proxy to access a particular recipe data object via the s88Get/Set api'''
   
    def  __init__(self, _chartScope, _stepScope, _location, _key):
        self.chartScope = _chartScope
        self.stepScope = _stepScope
        self.location = _location
        self.key = _key
        
    def set(self, attribute, value):
        s88Set(self.chartScope, self.stepScope, self.key + '/' + attribute, value, self.location)
        
    def get(self, attribute):
        from ils.sfc.common.util import getTopChartRunId
        # print 'RecipeData.get', attribute, getTopChartRunId(self.chartScope)
        return s88Get(self.chartScope, self.stepScope, self.key + '/' + attribute, self.location)

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

def getSiblingKey(key, attribute):
    '''given a full key, e.g. foo.value, return a key for a sibling attribute; e.g. for attribute
    id, foo.id would be returned'''
    lastDotIndex = key.rfind(".")
    return key[0:lastDotIndex+1] + attribute

def splitKey(key):
    '''given a key, split it into the prefix and the final value attribute'''
    lastDotIndex = key.rfind(".")
    return key[0:lastDotIndex], key[lastDotIndex + 1:len(key)]

