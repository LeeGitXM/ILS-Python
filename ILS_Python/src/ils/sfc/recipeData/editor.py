'''
Created on Jan 2, 2017
These are all called from the designer while editing data.  
Currently, when editing recipe data in the Designer, we are alway editing the Production recipe data.
@author: phass
'''

import system
from ils.common.database import toDictList
from ils.common.config import getDatabaseClient 

def getRecipeDataList(stepUUID):
    print "Fetching recipe data for step %s" % (stepUUID)
    
    db = getDatabaseClient()
    recipeData = []
    pds = system.db.runQuery("select * from SfcRecipeDataSimpleValueView where stepUUID = '%s'" % (stepUUID), db)
    recipeData = toDictList(pds, recipeData)
    print "Fetched recipe data: ", recipeData
    
    return recipeData