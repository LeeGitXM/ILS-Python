'''
Created on May 16, 2017

@author: phass
'''

import system, time
from ils.common.config import getDatabaseClient, getTagProviderClient
from ils.io.util import splitTagPath, writeTag

from ils.log import getLogger
log = getLogger(__name__)

EDIT = "edit"
CREATE = "create"

# Open transaction when window is opened
def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()..."
    #refresh(rootContainer)
    
def internalFrameActivated(rootContainer):
    print "In internalFrameActivated()..."
    refresh(rootContainer)

def refresh(rootContainer):
    print "...refreshing..."
    provider = getTagProviderClient()
    
    path = "[%s]" % (provider)
    print "Browsing %s" % (path)
    filters = {'tagType':'UdtInstance', 'typeId':"Lab Data/Unit Parameter", 'recursive':True}
    results = system.tag.browse(path=path, filter=filters)

    header = ["Unit Parameter", "Filtered Value", "Number of Points", "Ignore Sample Time", "Value Source", "Sample Time Source"]
    vals = []
    for result in results:
        tagName = result['name']
        fullTagPath = str(result['fullPath'])

        qvs = system.tag.readBlocking(
                    [fullTagPath + "/numberOfPoints", 
                     fullTagPath + "/ignoreSampleTime",
                     fullTagPath + "/rawValue.sourceTagPath",
                     fullTagPath + "/sampleTime.sourceTagPath",
                     fullTagPath + "/filteredValue"
                    ])

        numberOfPoints = qvs[0].value
        ignoreSampleTime = qvs[1].value
        valueReference = qvs[2].value
        sampleTimeReference = qvs[3].value
        filteredValue = qvs[4].value

        if ignoreSampleTime == None:
            ignoreSampleTime = False

        vals.append([fullTagPath, filteredValue, numberOfPoints, ignoreSampleTime, valueReference, sampleTimeReference])
    
    ds = system.dataset.toDataSet(header, vals)
    ds = system.dataset.sort(ds, "Unit Parameter")
    table = rootContainer.getComponent("Unit Parameter Power Table")
    table.data = ds
    
    selectedRow = table.selectedRow
    time.sleep(0.25)
    table.selectedRow = -1
    time.sleep(0.25)
    table.selectedRow = selectedRow
    
    table = rootContainer.getComponent("Unit Parameter Buffer Table")
    system.db.refresh(table, "data")
    

def updateBufferTable(unitParameterTable, rowIndex):
    log.infof("In %s.updateBufferTable()...", __name__)
    rootContainer = unitParameterTable.parent
    
    ds = unitParameterTable.data
    unitParameterTagName = ds.getValueAt(rowIndex, "Unit Parameter")
    print "Selected Unit Parameter: ", unitParameterTagName
    
    vals = system.tag.readBlocking([unitParameterTagName + "/buffer"])
    buffer = vals[0].value
    
    table = rootContainer.getComponent("Unit Parameter Buffer Table")
    table.data = buffer


def clearBufferTable(rootContainer):
    table = rootContainer.getComponent("Unit Parameter Buffer Table")
    ds = table.data
    from ils.common.util import clearDataset
    ds = clearDataset(ds)
    table.data = ds


def createUnitParameter(event):
    '''
    This is called when they press the "+" button on the browser window
    '''
    log.infof("In %s.launchNewUnitParameterPopup()...", __name__)
    window = system.gui.getParentWindow(event)
    table = event.source.parent.getComponent("Unit Parameter Power Table")
    header = ["window", "table"]
    rows = [[window, table]]
    args = system.dataset.toDataSet(header, rows)
    payload = {"args": args, "mode": CREATE}
    window = system.nav.openWindow("Lab Data/Unit Parameter Popup", payload)
    system.nav.centerWindow(window)
    

def editUnitParameter(event):
    '''
    This is called when they press the "+" button on the browser window
    '''
    log.infof("In %s.launchNewUnitParameterPopup()...", __name__)

    table = event.source.parent.getComponent("Unit Parameter Power Table")
    
    row = table.selectedRow
    data = table.data
    
    unitParameterName = data.getValueAt(row, "Unit Parameter")
    numberOfPoints = data.getValueAt(row, "Number Of Points")
    ignoreSampleTime = data.getValueAt(row, "Ignore Sample Time")
    valueSource = data.getValueAt(row, "Value Source")
    sampleTimeSource = data.getValueAt(row, "Sample Time Source")
    
    payload = {"mode": EDIT, "unitParameterName": unitParameterName, "numberOfPoints": numberOfPoints, "ignoreSampleTime": ignoreSampleTime, "valueSource": valueSource, "sampleTimeSource": sampleTimeSource}

    window = system.nav.openWindow("Lab Data/Unit Parameter Popup", payload)
    system.nav.centerWindow(window)


def saveNewUnitParameter(event):
    '''
    This is called when they press the "Save" button on the popup 
    '''
    
    log.infof("In %s.saveNewUnitParameter()", __name__)
    rootContainer = event.source.parent
    mode = rootContainer.mode
    
    log.infof("Validating...")
    unitParameterName = rootContainer.getComponent("Unit Parameter").text
    if unitParameterName == "":
        system.gui.errorBox("The unit parameter name is required!")
        return
    
    if mode == CREATE and system.tag.exists(unitParameterName):
        system.gui.errorBox("Error: A tag named %s already exists!" % (unitParameterName))
        return
    
    valueSourceTagPath = rootContainer.getComponent("Value Source").text
    if not(system.tag.exists(valueSourceTagPath)):
        system.gui.errorBox("Error: The value tag named <%s> does not exist!" % (valueSourceTagPath))
        return

    numberOfPoints = rootContainer.getComponent("Number Of Points").intValue
    ignoreSampleTime = rootContainer.getComponent("Ignore Sample Time").selected
    
    log.infof("Creating/updating UDT...")
    
    parentPath, tagName = splitTagPath(unitParameterName)
    print "The parent path is <%s>" % (parentPath)
    
    if ignoreSampleTime:
        sampleTimeSourceTagPath = ""
    else:
        sampleTimeSourceTagPath = rootContainer.getComponent("Sample Time Source").text
        if not(system.tag.exists(sampleTimeSourceTagPath)):
            system.gui.errorBox("Error: The value tag named <%s> does not exist!" % (sampleTimeSourceTagPath))
            return
        
    tag = {
           "name": tagName,
           "tagType": "UdtInstance",
           "typeId": "Lab Data/Unit Parameter",
           "tags": [
                {"name": "ignoreSampleTime", "value": ignoreSampleTime},
                {"name": "numberOfPoints", "value": numberOfPoints},
                {"name": "sampleTime", "sourceTagPath": sampleTimeSourceTagPath},
                {"name": "rawValue", "sourceTagPath": valueSourceTagPath}
                ]
           }
    print "Tag Configuration: ", tag
        
    result = system.tag.configure(parentPath, tags=[tag])
    print "Result: ", result
        
    print "Done!"    
    system.nav.closeParentWindow(event)


def deleteUnitParameter(event):
    '''
    This is called when they press the "Delete" button on the browser window
    '''
    log.infof("In %s.deleteUnitParameter()", __name__)

    rootContainer = event.source.parent
    table = rootContainer.getComponent("Unit Parameter Power Table")
    row = table.selectedRow
    ds = table.data
    unitParameterTagPath = ds.getValueAt(row, 0)
    print "Deleting ", unitParameterTagPath
    
    '''
    The tag should exist, we built the table by browsing tags, but just in case check if it exists before deleting it
    '''
    tagExists = system.tag.exists(unitParameterTagPath)
    if tagExists:
        system.tag.deleteTags([unitParameterTagPath])
    
    ''' Update the UI '''
    refresh(rootContainer)

def setRoot(event):
    '''
    This is called by the propertyChange event handler on all 3 of the tag fields on the window.
    '''
    print "In %s.setRoot" % (__name__)
    tagPath = event.newValue
    
    configuration = system.tag.getConfiguration(tagPath, False)
    print configuration
    tagDict = configuration[0]
    tagType = tagDict.get("tagType", "Unknown")
    print "Tag type: ", tagType
    
    if str(tagType) in ["Unknown"]:
        print "...bailing..."
        return 
    
    folder = tagDict.get("path", "")
    
    rootContainer = event.source.parent
    rootContainer.folder = folder