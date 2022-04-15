'''
Created on Mar 10, 2019

@author: phass
'''

import system
from ils.sfc.recipeData.core import fetchRecipeDataTypeId, fetchValueTypeId
from ils.common.cast import determineType, toBit
from ils.common.error import catchError

from ils.log import getLogger
log = getLogger(__name__)

def createDynamicRecipe(stepId, recipeDataType, key, db, val=None):
    log.infof("Creating dynamic recipe data for step: %d, type: %s, key: %s", stepId, recipeDataType, key)
    
    recipeDataId = None
    
    '''
    There is an annoying disconnect between the constants in Java and the constants in Python.  I have two seperate constants files and the
    class names for recipe data are not in sync!  So I will avoind using constants in this code which gets the value from Java and processes in Python.
    
    public static final String ARRAY = "array";
    public static final String INPUT = "input";
    public static final String OUTPUT_RAMP = "outputRamp";
    public static final String SQC = "sqc";
    '''

    if recipeDataType == "simpleValue":
        # If they didn't pass a value then assume a float.
        if val == None:
            val = 1.1
        recipeDataId = createSimpleValue(stepId, key, val, db)
    elif recipeDataType == "recipe":
        recipeDataId = createRecipe(stepId, key, db)
    else:
        log.errorf("Unexpected recipe data type: <%s> in %s.createDynamicRecipe()", recipeDataType, __name__)
        
    return recipeDataId

def createSimpleValue(stepId, key, val, db):
    log.infof("Creating a simple value, key: %s, value: %s", key, str(val))
   
#    valueType = simpleValueContainer.getComponent("Value Type Dropdown").selectedStringValue
#    valueTypeId = simpleValueContainer.getComponent("Value Type Dropdown").selectedValue
    
    tx = system.db.beginTransaction(db)
    
    try:
        recipeDataTypeId = fetchRecipeDataTypeId("Simple Value", db)
        
        recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, tx)
        
        valueType, val = determineType(val)
        valueTypeId = fetchValueTypeId(valueType, db)
        
        if valueType == "Float":
            SQL = "Insert into SfcRecipeDataValue (FloatValue) values (%f)" % (val)
        elif valueType == "Integer":
            SQL = "Insert into SfcRecipeDataValue (IntegerValue) values (%d)" % (val)
        elif valueType == "String":
            SQL = "Insert into SfcRecipeDataValue (StringValue) values ('%s')" % (val)
        elif valueType == "Boolean":
            val = toBit(val)
            SQL = "Insert into SfcRecipeDataValue (BooleanValue) values (%d)" % (val)
        
        print SQL
        valueId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
        
        SQL = "Insert into SfcRecipeDataSimpleValue (RecipeDataId, ValueTypeId, ValueId) values (%d, %d, %d)" % (recipeDataId, valueTypeId, valueId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=tx)

        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        catchError("%s.createSimpleValue()" % (__name__), "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
        return None
    
    print "Done!"
    return recipeDataId
    
def createRecipe(stepId, key, db):
    tx = system.db.beginTransaction(db)
    
    try:
        print "Inserting a recipe..."
        
        recipeDataTypeId = fetchRecipeDataTypeId("Recipe", db)
        recipeDataId = insertRecipeData(stepId, key, recipeDataTypeId, tx)
        
        SQL = "Insert into SfcRecipeDataRecipe (RecipeDataId, PresentationOrder) values (%d, 0)" % (recipeDataId)
        print SQL
        system.db.runUpdateQuery(SQL, tx=tx)
        system.db.commitTransaction(tx)
        system.db.closeTransaction(tx) 
    except:
        catchError("%s.createSimpleValue()" % (__name__), "Caught an error, rolling back transactions")
        system.db.rollbackTransaction(tx)
        system.db.closeTransaction(tx) 
        return None
    
    print "Done!"
    return recipeDataId

def insertRecipeData(stepId, key, recipeDataTypeId, tx):
    SQL = "insert into SfcRecipeData (StepId, RecipeDataKey, RecipeDataTypeId, Description) "\
            "values (%s, '%s', %d, 'Auto Created')" % (stepId, key, recipeDataTypeId)
    print SQL
    recipeDataId = system.db.runUpdateQuery(SQL, getKey=True, tx=tx)
    return recipeDataId