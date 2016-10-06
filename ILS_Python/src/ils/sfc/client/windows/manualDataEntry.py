'''
Created on Jul 28, 2015

@author: rforbes
'''

from ils.sfc.common.util import isEmpty
import system.gui.warningBox
from ils.common.config import getDatabaseClient
 
def sendData(window):
    '''Send data to gateway. If configured, check that all values have been entered, and
       don't send and warn if they have not. Return true if data was sent.'''

    table = window.getRootContainer().getComponent('Power Table')
    dataset = table.data
    
    print "In %s" % (__name__)
    
    # anywhere units are specified, check if they also exist in recipe data
    for row in range(dataset.rowCount):
        units = dataset.getValueAt(row, 2)
        if not isEmpty(units):
            recipeUnits = dataset.getValueAt(row, 8)
            key = dataset.getValueAt(row, 5)
            if isEmpty(recipeUnits):
                system.gui.messageBox("Unit %s is specified but recipe data %s has no units. No conversion will be done." % (units, key), 'Warning')
     
    requireAllInputs = window.getRootContainer().data.getValueAt(0,'requireAllInputs')
    print "This window requires all inputs: %s" % (str(requireAllInputs))
    
    allInputsOk = True
    if requireAllInputs:
        for row in range(dataset.rowCount):
            print "Checking row ", row 
            value = dataset.getValueAt(row, "value")
            if (value == None) or (len(value.strip()) == 0):
                allInputsOk = False
                break

    if allInputsOk:
        print "All inputs are OK - sending data to the gateway!"
        saveData(window.rootContainer)    
        return True
    else:
        system.gui.messageBox("All inputs are required", "Warning")
        return False
    
def saveData(rootContainer):
    print "Saving the data..."
    database=getDatabaseClient()
    windowData = rootContainer.data
    windowId = windowData.getValueAt(0,0)
    print "The window id is: ", windowId

    table = rootContainer.getComponent('Power Table')
    ds = table.data
    pds = system.dataset.toPyDataSet(ds)
    for record in pds:
        val = record['value']
        rowNum = record['rowNum']
        SQL = "update SfcManualDataEntryTable set value = '%s' where windowId = '%s' and rowNum = %i" % (val, windowId, rowNum)
        system.db.runUpdateQuery(SQL, database=database)

    SQL = "update SfcManualDataEntry set complete = 1 where windowId = '%s'" % (windowId)
    system.db.runUpdateQuery(SQL, database=database)        
    print "--- Done ---"
    