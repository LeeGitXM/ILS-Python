'''
Created on Mar 22, 2017

@author: phass
'''
import system
from ils.common.util import formatDateTime
from ils.common.config import getTagProviderClient
log = system.util.getLogger("com.ils.labData.ui.configuration")

def internalFrameOpened(rootContainer):
    log.infof("In %s.internalFrameOpened()", __name__)

    
def internalFrameActivated(rootContainer):
    log.infof("In %s.internalFrameActivated()", __name__)
    refreshCallback(rootContainer)


def refreshCallback(rootContainer):
    log.infof("In %s.refreshCallback()...", __name__)
    tagProvider = getTagProviderClient()

    def refresh(rootContainer=rootContainer, tagProvider=tagProvider):
        log.infof("Refreshing in an asynchronous thread...")
        udtList = []
        
        # Collect all of the lab bias UDTs
        biasType = ["Exponential", "PID"]
        i = 0
        data = []
        for udtParentType in ["Lab Bias/Lab Bias Exponential Filter", "Lab Bias/Lab Bias PID"]:
            
            log.infof("Browsing for %s", udtParentType)
            
            if udtParentType == "Lab Bias/Lab Bias Exponential Filter":
                biasType = "Exponential"
            else:
                biasType = "PID"
            
            udts = system.tag.browseTags(
                parentPath="[%s]LabData" % (tagProvider), 
                tagType="UDT_INST", 
                udtParentType=udtParentType,
                recursive=True)
            
            log.infof("...Discovered %d Bias UDTs...", len(udts))
            
            for udt in udts:
                udtPath = udt.path
                udtType = udt.type    
                biasName = udtPath[udtPath.rfind("/") + 1:]
                rootPath = udtPath[:udtPath.rfind("/")]
                
                tagValues = system.tag.readAll([udtPath+"/labValue", udtPath+"/modelValue", udtPath+"/biasValue", udtPath+"/labSampleTime"])
                labValue = tagValues[0].value
                modelValue = tagValues[1].value
                biasValue = tagValues[2].value
                sampleTime = tagValues[3].value
                sampleTime = formatDateTime(sampleTime)
                
                data.append([udtPath, rootPath, biasName, biasType, labValue, modelValue, biasValue, str(sampleTime)])
    
            i = i + 1
            
        header = ["Bias Path", "Path", "Bias Name", "Bias Type","Lab Value", "Model Value", "Bias Value", "Lab Sample Time"]
        ds = system.dataset.toDataSet(header, data)
        ds = system.dataset.sort(ds, "Bias Name")
        table = rootContainer.getComponent("Table")
        table.data = ds
        rootContainer.mode = "done"
        
        log.infof("...done initializing!")
        
    rootContainer.mode = "initializing"
    system.util.invokeAsynchronous(refresh)


def createCallback(event):
    log.infof("In %s.createCallback()...", __name__)
    window = system.nav.openWindow('Lab Data/Lab Bias Configuration', {"mode": "create", "unit": "", "biasType": "", "biasName": ""})
    system.nav.centerWindow(window)


def deleteCallback(event):
    log.infof("In %s.deleteCallback()...", __name__)
    
    tagProvider = getTagProviderClient()
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Table")
    selectedRow = table.selectedRow
    if selectedRow < 0:
        system.gui.warningBox("Please select a row!")
        return
    
    ds = table.data
    biasPath = ds.getValueAt(selectedRow, "Bias Path")
    
    tagPath = "[" + tagProvider + "]" + biasPath
    log.infof("Deleting %s", tagPath)
    
    system.tag.removeTag(tagPath)
    refreshCallback(rootContainer)
    

def configureCallback(event):
    log.infof("In %s.configureCallback()...", __name__)
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Table")
    row = table.selectedRow
    ds = table.data
    
    path = ds.getValueAt(row, "Bias Path")
    biasName = ds.getValueAt(row, "Bias Name")
    biasType = ds.getValueAt(row, "Bias Type")
    
    # Extract the unit from the path
    log.infof("Path: %s", path)
    unit = path[8:]
    unit = unit[:unit.find("/")]
    
    log.infof("The unit is <%s>", unit)
    
    window = system.nav.openWindow('Lab Data/Lab Bias Configuration', {"mode": "edit", "unit": unit, "biasType": biasType, "biasName": biasName})
    system.nav.centerWindow(window)