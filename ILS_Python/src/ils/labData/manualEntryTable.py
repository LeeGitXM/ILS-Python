'''
Created on Jul 24, 2023

@author: ils
'''

'''
Created on Apr 30, 2015

@author: Pete
'''
import system
from ils.io.util import readTag
from ils.config.client import getDatabase
from ils.log import getLogger
log = getLogger(__name__)

VALUE_ROW = 0
UPPER_LIMIT_ROW = 2
LOWER_LIMIT_ROW = 3
HISTORY_HEADER_ROW = 5

# Everything in this module runs in the client, so the use of loggers isn't too important since nothing will go 
# to the wrapper log anyway.
    
def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()...", __name__)
    
    dateFormat = readTag("Configuration/LabData/dateFormatLong").value
    rootContainer.formatString = dateFormat
    
    table = rootContainer.getComponent("Power Table")
    
    ''' 
    Set the date format from the configuration tags.  
    Set the format of the combo box and the Sample Time column of the table to the dateFormatLong.
    Set the the format of the last values to dateFormat.
    Setting the date format of a power table column is a little tricky since it can't be bound.  It needs to be done programatically 
    by setting the column attributes property of the table. 
    '''
    
    dateFormat = readTag("Configuration/LabData/dateFormatLong").value
    rootContainer.formatString = dateFormat
    ds = table.columnAttributesData
    ds = system.dataset.setValue(ds, 2, 1, dateFormat)
    table.columnAttributesData = ds
    
    db = getDatabase()
    txt = rootContainer.valueIds
    valueIds = txt.split(",")
    
    txt = rootContainer.valueNames
    valueNames = txt.split(",")
    
    if len(valueIds) < 2:
        print "This only works for 2 or more lab values"
        return
    
    valueId = str(valueIds[0])
    
    ''' Fetch the unit for the first lab value, by definition, all lab values from the chooser are from the same unit '''
    SQL = "select UnitName from TkUnit U, LtValue V "\
        " where V.UnitId = U.UnitId and V.ValueId = %s" % (str(valueId))
    unitName = system.db.runScalarQuery(SQL, database=db)
    if unitName == None:
        system.gui.errorBox("Error fetching the unit for this lab data!")
        return

    rootContainer.unitName = unitName    
    dateFormat = readTag("Configuration/LabData/dateFormat").value

    now = system.date.now()
    header = ["Lab Name", "Value", "Sample Time", "Upper Limit", "Lower Limit", "Last Value", "Previous Value", "ValueId", "StringValue"]
    data = []
    idx = 0
    for valueName in valueNames:
        row = [valueName, "", now]
        valueId = valueIds[idx]
                    
        SQL = "select StringValue from LtValue where ValueId = %s" % (str(valueId))
        stringValue = system.db.runScalarQuery(SQL, database=db)
        
        upperLimit = ""
        lowerLimit = ""
            
        if not(stringValue):
            log.tracef("...fetching validity limits for a numeric lab value...")
            
            ''' Fetch the validity limits and add to the table dataset '''
            SQL = "select UpperValidityLimit, LowerValidityLimit from LtLimit where ValueId = %s" % (str(valueId))
            pds = system.db.runQuery(SQL, database=db)
            for record in pds:
                # Validity Limits
                if record["UpperValidityLimit"] != None:
                    upperLimit = str(record["UpperValidityLimit"])
        
                if record["LowerValidityLimit"] != None:
                    lowerLimit = str(record["LowerValidityLimit"])
                    
        row.append(upperLimit)
        row.append(lowerLimit)
        
        ''' Fetch the history for each value '''
        lastVals = fetchRecentValues(valueId, stringValue, db, dateFormat)
        
        row.append(lastVals[0])
        row.append(lastVals[1])
        row.append(valueId)
        row.append(stringValue)
        
        data.append(row)
        idx = idx + 1
    
    ''' Make a dataset and add to the table. '''
    ds = system.dataset.toDataSet(header, data)
    table.data = ds

def updateSampleTime(rootContainer, sampleTime):
    log.infof("In %s.updateSampleTime() with %s", __name__, str(sampleTime))
    
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    for row in range(ds.rowCount):
        print "Row: ", row
        ds = system.dataset.setValue(ds, row, "Sample Time", sampleTime)
    table.data = ds
    
'''
Select the recent values for this lab datum
'''
def fetchRecentValues(valueId, stringValue, db, dateFormat):
    
    if stringValue:
        SQL = "select top 2 SampleTime, RawStringValue as 'RawValue' from LtHistory where ValueId = %s order by SampleTime DESC" % (valueId)
    else:
        SQL = "select top 2 SampleTime, RawValue from LtHistory where ValueId = %s order by SampleTime DESC" % (valueId)
        
    print SQL
    
    pds = system.db.runQuery(SQL, database=db)
    print "Fetched %d history records" % (len(pds))

    vals = []
    for record in pds:
        if record["RawValue"] == None or record["SampleTime"] == None:
            txt = ""
        else:
            sampleTime = record["SampleTime"]
            sampleTime = system.date.format(sampleTime, dateFormat)
            txt = "%s at %s" % (str(record["RawValue"]), sampleTime)
        vals.append(txt)
        
    while len(vals) < 2:
        vals.append("")
        
    print "Returning history: ", vals
    return vals
    

'''
This is called when the operator presses the 'Enter' button on the Manual Entry screen
'''
def enterCallback(rootContainer, db=""):
    log.infof("In %s.enterCallback()", __name__)
    
    dateFormat = readTag("Configuration/LabData/dateFormat").value
    unitName = rootContainer.unitName
    
    from ils.config.client import getTagProvider
    provider = getTagProvider()
    
    sampleTime = rootContainer.getComponent("Group").getComponent("Sample Time").date
    
    table = rootContainer.getComponent("Power Table")
    ds = table.data
    rows = ds.getRowCount()
    
    '''
    Iterate through the table in two passes.
    The first pass validates the values versus the limits
    The second pass, if all of the values are valid, stores the values in the database
    '''
    
    for phase in [1, 2]:
        log.infof("Starting Phase #%d", phase)
        valid = True
        
        for row in range(0,rows):
            log.infof("Handling row %d", row)
            sampleValue = ds.getValueAt(row,1)
            sampleTime = ds.getValueAt(row,2)
            valueId = ds.getValueAt(row, "ValueId")
            stringValue = ds.getValueAt(row, "StringValue")
            
            if sampleValue != "":
                valueName = ds.getValueAt(row, 0)
                
                upperLimit = ds.getValueAt(row, 3)
                lowerLimit = ds.getValueAt(row, 4)
                
                log.infof("Value Id: %s - Value: %s", valueId, sampleValue) 
                if phase == 1:
                    if sampleValue != "":
                        if lowerLimit != "":
                            if float(sampleValue) < float(lowerLimit):
                                valid = False
            
                        if upperLimit != "":
                            if float(sampleValue) > float(upperLimit):
                                valid = False
            
                        if not(valid):
                            system.gui.messageBox("Lab Value <%s> (%s) is outside the legal limits" % (valueName, str(sampleValue)))
                            return

                else:                
                    ''' Store the value in the database (not the historian) '''
                    from ils.labData.scanner import insertHistoryValue
                    
                    ''' For Boo's work I don't believe there is the notion of a grade, not sure how this should be handled generically '''
                    grade = None
                    insertHistoryValue(valueName, int(valueId), sampleValue, sampleTime, grade, stringValue, log, db)
                    
                    ''' Store the value in the Lab Data UDT memory tags, which are local to Ignition '''
                    from ils.labData.scanner import updateTags
                    tags, tagValues = updateTags(provider, unitName, valueName, sampleValue, sampleTime, True, True, [], [], log)
                    
                    log.infof("Writing %s to %s", str(tagValues), str(tags))
                    system.tag.writeBlocking(tags, tagValues)

                    ''' Update the external historian (pHD or Pi) '''
                    updateHistorian(valueId, valueName, sampleValue, sampleTime, provider, db)

                    ''' Clear the values and refresh the history '''
                    ds = system.dataset.setValue(ds, row, 1, "")
                    lastVal = ds.getValueAt(row, 5)
                    
                    sampleTimeTxt = system.date.format(sampleTime, dateFormat)
                    txt = "%s at %s" % (str(sampleValue), sampleTimeTxt)
                    
                    ds = system.dataset.setValue(ds, row, 5, txt)
                    ds = system.dataset.setValue(ds, row, 6, lastVal)
                    
    table.data = ds


def updateHistorian(valueId, valueName, sampleValue, sampleTime, provider, db):
    # If the lab datum is "local" then write the value to PHD, the destination is ALWAYS the historian so use an HDA write. 
    SQL = "select LV.ItemId, PHD.InterfaceName "\
        " from LtLocalValue LV, LtHdaInterface PHD "\
        " where LV.ValueId = %s "\
        " and LV.InterfaceId = PHD.InterfaceId" % (str(valueId))
 
    pds = system.db.runQuery(SQL, database=db)
    if len(pds) != 0:
        record = pds[0]
        itemId = record["ItemId"]
        serverName = record["InterfaceName"]
        
        # Check if writing is enabled
        labDataWriteEnabled= readTag("[" + provider + "]Configuration/LabData/labDataWriteEnabled").value
        globalWriteEnabled = readTag("[" + provider + "]Configuration/Common/writeEnabled").value
        writeEnabled = labDataWriteEnabled and globalWriteEnabled
        
        if writeEnabled and itemId not in ["", None] and serverName not in ["", None]:
            log.infof("Writing %s at %s for %s to %s - %s..." % (str(sampleValue), str(sampleTime), valueName, serverName, itemId))
            returnQuality = system.opchda.insertReplace(serverName, itemId, sampleValue, sampleTime, 192)
            log.infof("...the returnQuality is: %s", str(returnQuality))
        else:
            log.infof("*** Skipping *** Write of value %s for %s because writes are not enabled or the itemId is Null" % (str(sampleValue), valueName))
     