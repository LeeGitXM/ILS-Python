'''
Created on May 16, 2017

@author: phass
'''

import system
from ils.common.config import getDatabaseClient, getTagProviderClient
from ils.io.util import splitTagPath

# Open transaction when window is opened
def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()..."
    refresh(rootContainer)

'''

'''
def refresh(rootContainer):
    print "...refreshing..."
    provider = getTagProviderClient()
    
    parentPath = "[%s]" % (provider)
#    parentPath = ""
    print "Browsing %s" % (parentPath)
    browseTags = system.tag.browseTags(parentPath=parentPath, udtParentType="Lab Data/Unit Parameter", recursive=True)

    header = ["Unit Parameter", "Number of Points", "Ignore Sample Time", "Value Source", "Sample Time Source"]
    vals = []
    for browseTag in browseTags:
        tagPath = browseTag.path
        tagName = browseTag.name
        fullTagPath = browseTag.fullPath
        print tagName, tagPath, fullTagPath
        
        qvs = system.tag.readAll([tagPath + "/numberOfPoints", tagPath + "/ignoreSampleTime"])
        numberOfPoints = qvs[0].value
        ignoreSampleTime = qvs[1].value

        if ignoreSampleTime == None:
            ignoreSampleTime = False
        
        valueExpression = system.tag.getAttribute(fullTagPath + "/rawValue", "Expression")
        sampleTimeExpression = system.tag.getAttribute(fullTagPath + "/sampleTime", "Expression")
        vals.append([fullTagPath, numberOfPoints, ignoreSampleTime, valueExpression, sampleTimeExpression])
    
    ds = system.dataset.toDataSet(header, vals)
    ds = system.dataset.sort(ds, "Unit Parameter")
    table = rootContainer.getComponent("Unit Parameter Power Table")
    table.data = ds
    print "Done!"
        

def updateTableAndUDT(table, rowIndex, colIndex, colName, oldValue, newValue):
    print "In %s.updateTableAndUDT" % (__name__)
    
    ds = table.data
    tagPath = ds.getValueAt(rowIndex, "Unit Parameter")
    
    if colName == "Unit Parameter":
        print "Unable to rename a tag"
        
    elif colName == "Number of Points":
        system.tag.write(tagPath + "/numberOfPoints", newValue)
        
    elif colName == "Ignore Sample Time":
        system.tag.write(tagPath + "/ignoreSampleTime", newValue)
        
    elif colName == "Value Source":
        if not(system.tag.exists(newValue)):
            system.gui.errorBox("Error: The value tag named <%s> does not exist!" % (newValue))
            return

        system.tag.editTag(tagPath, overrides={"rawValue": {"Expression":newValue}})
        
    elif colName == "Sample Time Source":
        if not(system.tag.exists(newValue)):
            system.gui.errorBox("Error: The sample time tag named <%s> does not exist!" % (newValue))
            return
        
        system.tag.editTag(tagPath, overrides={"sampleTime": {"Expression":newValue}})
        
    else:
        print "Unexpected column: ", colName
    

def updateBufferTable(unitParameterTable, rowIndex):
    db = getDatabaseClient()
    rootContainer = unitParameterTable.parent
    
    ds = unitParameterTable.data
    unitParameterTagName = ds.getValueAt(rowIndex, "Unit Parameter")
    print "Selected Unit Parameter: ", unitParameterTagName
    
    SQL = "select BufferIndex, RawValue, SampleTime, ReceiptTime "\
        " from TkUnitParameter P, TkUnitParameterBuffer B "\
        " where P.UnitParameterId = B.UnitParameterId "\
        " and UnitParameterTagName = '%s' " % (unitParameterTagName)

    pds = system.db.runQuery(SQL, database=db)
    table = rootContainer.getComponent("Unit Parameter Buffer Table")
    table.data = pds


def clearBufferTable(rootContainer):
    table = rootContainer.getComponent("Unit Parameter Buffer Table")
    ds = table.data
    from ils.common.util import clearDataset
    ds = clearDataset(ds)
    table.data = ds

'''
This is called when they press the "+" button on the browser window
'''
def launchNewUnitParameterPopup(event):
    print "Launching the new unit parameter popup"
    window = system.gui.getParentWindow(event)
    table = event.source.parent.getComponent("Unit Parameter Power Table")
    header = ["window", "table"]
    rows = [[window, table]]
    args = system.dataset.toDataSet(header, rows)
    payload = {"args": args}
    window = system.nav.openWindow("Lab Data/Unit Parameter Popup", payload)
    system.nav.centerWindow(window)

'''
This is called when they press the "Save" button on the popup 
'''
def saveNewUnitParameter(event):
    rootContainer = event.source.parent
    
    print "Validating..."
    unitParameterName = rootContainer.getComponent("Unit Parameter").text
    
    if system.tag.exists(unitParameterName):
        system.gui.errorBox("Error: A tag named %s already exists!" % (unitParameterName))
        return
    
    valueSourceTag = rootContainer.getComponent("Value Source").text
    if not(system.tag.exists(valueSourceTag)):
        system.gui.errorBox("Error: The value tag named <%s> does not exist!" % (valueSourceTag))
        return
    
    sampleTimeSourceTag = rootContainer.getComponent("Sample Time Source").text
    if not(system.tag.exists(sampleTimeSourceTag)):
        system.gui.errorBox("Error: The value tag named <%s> does not exist!" % (sampleTimeSourceTag))
        return

    numberOfPoints = rootContainer.getComponent("Number Of Points").intValue
    ignoreSampleTime = rootContainer.getComponent("Ignore Sample Time").selected
    
    print "Creating UDT..."
    
    rawValueExpression = "{%s}" % (valueSourceTag)
    parentPath, tagName = splitTagPath(unitParameterName)
    
    if ignoreSampleTime:
        sampleTimeExpression = ""
        system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
            attributes={"UDTParentType": "Lab Data/Unit Parameter"}, 
            overrides={"numberOfPoints": {"Value":numberOfPoints}, 
                       "rawValue": {"Expression":rawValueExpression},
                       "ignoreSampleTime": {"Value":ignoreSampleTime}
                       })
    else:
        sampleTimeExpression = "{%s}" % (sampleTimeSourceTag)
        system.tag.addTag(parentPath=parentPath, name=tagName, tagType="UDT_INST", 
            attributes={"UDTParentType": "Lab Data/Unit Parameter"}, 
            overrides={"numberOfPoints": {"Value":numberOfPoints}, 
                       "rawValue": {"Expression":rawValueExpression},
                       "sampleTime": {"Expression":sampleTimeExpression},
                       "ignoreSampleTime": {"Value":ignoreSampleTime}
                       })
    
    print "Updating table..."
    
    args = rootContainer.args
    table = args.getValueAt(0, "table")
    
    ds = table.data
    ds = system.dataset.addRow(ds, 0, [unitParameterName, numberOfPoints, ignoreSampleTime, rawValueExpression, sampleTimeExpression])
    table.data = ds
    
    system.nav.closeParentWindow(event)

'''
This is called when they press the "Delete" button on the browser window
'''
def deleteUnitParameter(event):
    db = getDatabaseClient()
    print "Launching the new unit parameter popup"
    table = event.source.parent.getComponent("Unit Parameter Power Table")
    row = table.selectedRow
    ds = table.data
    unitParameterTagPath = ds.getValueAt(row, 0)
    print "Deleting ", unitParameterTagPath
    
    '''
    The tag should exist, we built the table by browsing tags, but just in case check if it exists before deleting it
    '''
    tagExists = system.tag.exists(unitParameterTagPath)
    if tagExists:
        system.tag.removeTag(unitParameterTagPath)
    
    '''
    Clean up the TkUnitParameter and TkUnitParameterBuffer tables.
    '''
    SQL = "delete from TkUnitParameter where UnitParameterTagName = '%s'" % (unitParameterTagPath)
    rows = system.db.runUpdateQuery(SQL, db)
    print "Deleted %d rows from TkUnitParameter" % (rows)
    
    '''
    Update the UI - delete the row from the table
    '''
    ds = system.dataset.deleteRow(ds, row)
    table.data = ds
    