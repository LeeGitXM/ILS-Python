'''
Created on Jan 2, 2017
These are all called from the designer while editing data.  
Currently, when editing recipe data in the Designer, we are alway editing the Production recipe data.

8/13/2019 - I'm not exactly sure how / if this is used.  It is referenced from Java, see PythonCall.java
                Maybe this was a work in progress or a prototype, but the only recipe editor is via Python 
@author: phass
'''

import system, string
from ils.common.database import toDictList
from ils.common.config import getDatabaseClient 

def getRecipeDataList(stepUUID):
    print "Fetching recipe data for step %s" % (stepUUID)
    
    db = getDatabaseClient()
    recipeData = []
    
    pds = system.db.runQuery("select * from SfcRecipeDataSimpleValueView where stepUUID = '%s'" % (stepUUID), db)
    if len(pds) > 0:
        print "Fetched %i simple value rows..." % (len(pds))
        pds = convertValues(pds)
        recipeData = toDictList(pds, recipeData)
    
    pds = system.db.runQuery("select * from SfcRecipeDataOutputView where stepUUID = '%s'" % (stepUUID), db)
    if len(pds) > 0:
        print "Fetched %i output rows..." % (len(pds))
        recipeData = toDictList(pds, recipeData)
    
    print "Fetched recipe data: ", recipeData
    
    return recipeData


# Consolidate the 4 value columns into a single one 
def convertValues(pds):
    
    ds = system.dataset.toDataSet(pds)
    vals = []
    for i in range(0,ds.rowCount):
        valueType = ds.getValueAt(i,"ValueType")
        val = ds.getValueAt(i,"%sVALUE" % string.upper(valueType))
        vals.append(str(val))
    ds = system.dataset.addColumn(ds, vals, "Value", basestring)
    pds = system.dataset.toPyDataSet(ds)
    return pds