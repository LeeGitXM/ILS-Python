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
        from ils.sfc.gateway.util import getTopChartRunId
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
    colonIndex = string.find(':', lbIndex)
    if lbIndex != -1 and rbIndex != -1 and colonIndex != -1 and rbIndex > colonIndex:
        return string[lbIndex : rbIndex+1]
    else:
        return None

def substituteScopeReferences(chartProperties, stepProperties, sql):
    ''' Substitute for scope variable references, e.g. '{local:selected-emp.value}'
    '''
    from ils.sfc.gateway.api import s88Get, readTag
    from ils.sfc.common.constants import TAG, CHART, STEP
    # really wish Python had a do-while loop...
    while True:
        ref = findBracketedScopeReference(sql)
        if ref != None:
            location, key = parseBracketedScopeReference(ref)
            location = location.lower()
            if location == TAG:
                value = readTag(chartProperties, key)
            elif location == CHART:
                value = chartProperties.get(key, "<not found>")
            elif location == STEP:
                value = stepProperties.get(key, "<not found>")
            else:
                value = s88Get(chartProperties, stepProperties, key, location)
            sql = sql.replace(ref, str(value))
        else:
            break
    return sql

def getSiblingKey(key, attribute):
    '''given a full key, e.g. foo.value, return a key for a sibling attribute; e.g. for attribute
    id, foo.id would be returned'''
    lastDotIndex = key.rfind(".")
    if lastDotIndex == -1:
        lastDotIndex = key.rfind("/")
    return key[0:lastDotIndex+1] + attribute

def splitKey(key):
    '''given a key, split it into the prefix and the final value attribute'''
    lastDotIndex = key.rfind(".")
    return key[0:lastDotIndex], key[lastDotIndex + 1:len(key)]

def browseRecipeData(chartProperties, stepProperties, location):
    '''Get a dictionary of key/value info for
    all recipe data in the given scope. '''
    from ils.sfc.gateway.api import s88GetFullTagPath
    from system.tag import browseTags, read
    fullTagPath = s88GetFullTagPath(chartProperties, stepProperties, '', location)
    browseTags = browseTags(fullTagPath)
    data = dict()
    for browseTag in browseTags:
        tagName = browseTag.name
        tagValue = read(browseTag.fullPath + '/value').value
        data[str(browseTag.fullPath)] = str(tagValue)
    return data
        
def isInt(value):
    try:
        int(value)
        return True
    except:
        return False

def getKeyValues(keyName, database):
    '''Get the individual key values for the given key index'''
    import system
    sql = "select KeyValue from SfcRecipeDataKeyMaster master, SfcRecipeDataKeyDetail detail where \
        master.KeyName = '%s' and detail.KeyId = master.KeyId order by KeyIndex asc" % (keyName)
    results = system.db.runQuery(sql, database)
    keys = []
    for row in results:
        keys.append(row[0])
    return keys

def getIndexFromKey(tagPath, keyAttribute, indexValue, database):
    '''get a numeric index from a string key'''
    import system
    # Get the name of the key from the recipe data UDT:
    keyPath = getSiblingKey(tagPath, keyAttribute)
    print 'sibling key path', keyPath
    keyName = system.tag.read(keyPath).value
    print 'keyName', keyName
    # Get the possible values of that key from the database:
    keyValues = getKeyValues(keyName, database)
    print 'keyValues', keyValues
    # find the location of the given key value in that list:
    index = keyValues.index(indexValue)
    print 'index of', indexValue, ' in ', keyValues, ' is ', index
    return index
    
def parseIndices(indexedPath, database):  
    '''Parse out the indices of a keyed reference, resolve symbolic indices to integers if necessary,
       and return the tag path of the dataset and integer row, and column indices'''
    import system
    lbracket = indexedPath.index('(');
    try:
        comma = indexedPath.index(',', lbracket)
    except:
        comma = -1
    rbracket = indexedPath.index(')', lbracket);
    tagPath = indexedPath[0:lbracket]
    if comma != -1:
        rowKey = indexedPath[lbracket+1:comma].strip()
        colKey = indexedPath[comma+1:rbracket].strip()
    else:
        rowKey = indexedPath[lbracket+1:rbracket].strip()  
        colKey = None
    print 'tagPath', tagPath, 'rowKey', rowKey, 'colKey', colKey
    
    if isInt(rowKey):
        rowIndex = int(rowKey)
    else:
        rowIndex = getIndexFromKey(tagPath, "rowKey", rowKey, database)
    
    if colKey == None:
        colIndex = None
    elif isInt(colKey):
        colIndex = int(colKey)
    else:
        colIndex = getIndexFromKey(tagPath, "columnKey", colKey, database)
    return tagPath, rowIndex, colIndex

def getIndexedValue(indexedPath, database):
    import system
    tagPath, rowIndex, colIndex = parseIndices(indexedPath, database)
    arrayOrDataset = system.tag.read(tagPath).value
    if colIndex != None:
        return arrayOrDataset.getValueAt(rowIndex, colIndex)
    else:
        return arrayOrDataset[rowIndex]

def setIndexedValue(indexedPath, value, database):
    import system
    tagPath, rowIndex, colIndex = parseIndices(indexedPath, database)    
    arrayOrDataset = system.tag.read(tagPath).value
    if colIndex != None:
        newValue = system.dataset.setValue(arrayOrDataset, rowIndex, colIndex, value)
    else:
        arrayOrDataset[rowIndex] = value
        newValue = arrayOrDataset
    system.tag.writeSynchronous(tagPath, newValue)
