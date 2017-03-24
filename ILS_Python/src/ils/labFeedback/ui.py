'''
Created on Mar 22, 2017

@author: phass
'''
import system
from com.jidesoft.grid import Row

def internalFrameOpened(rootContainer):
    print "In internalFrameOpened"
    
    def initialize(rootContainer=rootContainer):
        print "Initializing in an asynchronous thread..."
        udtList = []
        
        # Collect all of the lab bias UDTs
        biasType = ["Exponential", "PID"]
        i = 0
        for udtParentType in ["Lab Bias/Lab Bias Exponential Filter", "Lab Bias/Lab Bias PID"]:
            
            udts = system.tag.browseTags(
                parentPath="[XOM]LabData", 
                tagType="UDT_INST", 
                udtParentType=udtParentType,
                recursive=True)
            
            print "...Discovered %d Bias UDTs..." % (len(udts))
            
            for udt in udts:
                print udt.path
                udtPath = udt.path        
                udtList.append([udtPath, biasType[i]])
    
            i = i + 1
            
        ds = system.dataset.toDataSet(["UDTPath", "UDTType"], udtList)
        rootContainer.udts = ds
        refresh(rootContainer, ds)
        print "...done initializing!"
        
    rootContainer.mode = "initializing"
    system.util.invokeAsynchronous(initialize)


def refresh(rootContainer, udtDS):
    print "Refreshing..."
    
    rootContainer.mode = "Refreshing!"
    data = []
    for row in range(udtDS.rowCount):
        udtPath = udtDS.getValueAt(row,"UDTPath")
        print udtPath
        udtType = udtDS.getValueAt(row, "UDTType")
        biasName = udtPath[udtPath.rfind("/") + 1:]
        print "Row %d: Bias name: <%s>" % (row, biasName)
        
        tagValues = system.tag.readAll([udtPath+"/labValue", udtPath+"/modelValue", udtPath+"/biasValue", udtPath+"/labSampleTime"])
        labValue = tagValues[0].value
        modelValue = tagValues[1].value
        biasValue = tagValues[2].value
        sampleTime = tagValues[3].value
        
        data.append([udtPath,biasName,udtType, labValue, modelValue, biasValue, sampleTime])
        
    header = ["Bias Path", "Bias Name", "Bias Type","Lab Value", "Model Value", "Bias Value", "Lab Sample Time"]
    ds = system.dataset.toDataSet(header, data)
    ds = system.dataset.sort(ds, "Bias Name")
    table = rootContainer.getComponent("Table")
    table.data = ds
    print "...done refreshing!"