'''
Created on Apr 8, 2016

@author: ils
'''
import system, datetime
from ils.config.client import getHistoryTagProvider
from ils.config.common import getTagProvider

# Open transaction when window is opened
def internalFrameOpened(rootContainer):
    print "In internalFrameOpened()..."
    tagProvider=getTagProvider()
    
    # Browse for all of the Grade UDTs
    parentPath="[" + tagProvider + "]" + 'Site'
    filters = {"tagType":"UdtInstance", "typeId":"Grade", "recursive": True}
    gradeTags = system.tag.browse(parentPath,  filters)
    print "Found %i grade tags!" % (len(gradeTags))
    print gradeTags
    vals=[]
    for gradeTag in gradeTags.getResults():
        fullPath = str(gradeTag.get("fullPath"))
        print "Fullpath: ", fullPath
        unitName = system.tag.readBlocking([fullPath + "/unitName"])[0].value
        print "Unitname: ", unitName
        vals.append([fullPath, unitName])

    ds=system.dataset.toDataSet(["unit", "tag"], vals)
    dropdown=rootContainer.getComponent("Dropdown")
    dropdown.data = ds
    
    # Initialize the table
    header = ['Timestamp', 'Grade']
    vals=[]    
    ds = system.dataset.toDataSet(header, vals)
    table = rootContainer.getComponent("Power Table")
    table.data = ds
    

# Refresh when window is activated
def internalFrameActivated(rootContainer):
    print "In internaFrameActived()..."

 
# Refresh the grade history (this is called from a button or whenever the grade tag is changed.
def refresh(rootContainer):
    print "In refresh()..."

    dropdown=rootContainer.getComponent("Dropdown")
    gradeTag = dropdown.selectedStringValue
    historyTagProvider = getHistoryTagProvider()

    if gradeTag == "":
        print "Please select a grade tag first!"
        return
    
    print "Fetching history for: ", gradeTag
    
    ''' Strip off the tag provider and add the history tag provider '''
    
    gradeTag = gradeTag[gradeTag.find("]")+ 1:]
    print "Modified Grade Tag: ", gradeTag
    
    gradeTag = "[%s]%s/grade" % (historyTagProvider, gradeTag)
    print "Historical Grade Tag: ", gradeTag
    
    daysToFetch=30
    endTime = datetime.datetime.now()
    rangeHours = -1 * 24 * daysToFetch
    
    ds = system.tag.queryTagHistory(
                paths=[gradeTag],
                endTime=endTime, 
                rangeHours=rangeHours, 
                aggregationMode="LastValue",
                noInterpolation=True,
                includeBoundingValue=False
                )
    
    # Make a Dataset with standard column names (I don't know how to change the headers of a dataset)
    header = ['Timestamp', 'Grade']
    vals=[]
    pds = system.dataset.toPyDataSet(ds)
    for record in pds:
        vals.append([record[0], record[1]])
    
    ds = system.dataset.toDataSet(header, vals)
    ds = system.dataset.sort(ds, 0, False)
    table = rootContainer.getComponent("Power Table")
    table.data = ds

