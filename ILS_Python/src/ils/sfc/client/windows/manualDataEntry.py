'''
Created on Jul 28, 2015

This implements the save action for the manual data entry window.  The save updates the database table for the 
SfcManualDataEntryTable database table.  The gateway is reading the same table, when it sees the results then the block execution will complete.

@author: rforbes
'''

import system, string
from ils.sfc.common.util import isEmpty
from ils.common.config import getDatabaseClient, getTagProviderClient
from ils.sfc.recipeData.api import s88SetFromStep, s88SetFromStepWithUnits

def internalFrameOpened(rootContainer):
    db=getDatabaseClient()
    rootContainer.database = db
    print "In %s.InternalFrameOpened..." % (__name__)

    windowId = rootContainer.windowId
    print "The windowId is: ",windowId
    
    SQL = "select * from SfcWindow where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database=db)
    record=pds[0]
    rootContainer.title = record["title"]
    
    SQL = "select * from SfcManualDataEntry where windowId = '%s'" % (windowId)
    pds = system.db.runQuery(SQL, database=db)
    record=pds[0]
    requireAllInputs = record["requireAllInputs"]
    rootContainer.requireAllInputs = requireAllInputs
    
    header = record["header"]
    if header not in [None, ""]:
        rootContainer.header = header
 
def okCallback(rootContainer, timedOut=False):
    '''Save data to the database. If configured, check that all values have been entered, and
       don't send and warn if they have not. Return true if data was sent.'''

    table = rootContainer.getComponent('Power Table')
    dataset = table.data

    # anywhere units are specified, check if they also exist in recipe data
    for row in range(dataset.rowCount):
        units = dataset.getValueAt(row, "units")
        destination = dataset.getValueAt(row, "destination")
        if not isEmpty(units) and string.upper(destination) <> "TAGS":
            recipeUnits = dataset.getValueAt(row, 8)
            key = dataset.getValueAt(row, 5)
            if isEmpty(recipeUnits):
                system.gui.messageBox("Unit %s is specified but recipe data %s has no units. No conversion will be done." % (units, key), 'Warning')

    requireAllInputs = rootContainer.requireAllInputs
    print "This window requires all inputs: %s" % (str(requireAllInputs))
    
    allInputsOk = True
    if requireAllInputs:
        for row in range(dataset.rowCount):
            print "Checking row ", row 
            description = dataset.getValueAt(row, "description")
            if description not in ["", None]:
                value = dataset.getValueAt(row, "value")
                if (value == None) or (len(value.strip()) == 0):
                    allInputsOk = False
                    break

    if allInputsOk:
        print "All inputs are OK - saving data..."
        saveData(rootContainer, timedOut)
        return True
    else:
        system.gui.messageBox("All inputs are required", "Warning")
        return False

# This actually does the work of saving the data to the database.
def saveData(rootContainer, timedOut):
    print "In %s.saveData(), saving the data..." % (__name__)
    db=getDatabaseClient()
    provider=getTagProviderClient()
    windowId = rootContainer.windowId

    table = rootContainer.getComponent('Power Table')
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    for record in pds:
        description = record['description']
        if description not in ["", None]:
            val = record['value']
            rowNum = record['rowNum']
            units = record['units']
            keyAndAttribute = record['dataKey']
            stepUUID = record['targetStepUUID']
            destination = record['destination']
            valueType = record['type']
            
            print"  %s - %s - %s - %s - %s" % (destination, keyAndAttribute, val, units, valueType)
    
    #        value = parseValue(strValue, valueType)
            if string.upper(destination) == "TAG":
                print "Writing %s to %s" % (val, keyAndAttribute)
                tagPath = "[%s]%s" % (provider, keyAndAttribute)
                system.tag.write(tagPath, val)
            else:
                if isEmpty(units):
                    s88SetFromStep(stepUUID, keyAndAttribute, val, db)
                else:
                    s88SetFromStepWithUnits(stepUUID, keyAndAttribute, val, db, units)

    SQL = "update SfcManualDataEntry set complete = 1 where windowId = '%s'" % (windowId)
    system.db.runUpdateQuery(SQL, database=db)        
    print "--- Done ---"
