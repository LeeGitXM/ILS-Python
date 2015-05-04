'''
Created on Mar 29, 2015

@author: Pete
'''
import system

# Initialize the lab data viewer page with all of the parameters that are defined for 
# this page.  There is really only one component on this window - the template repeater.
# Once the repeater is configured, each component in the repeater knows how to configure itself.
def internalFrameActivated(rootContainer):
    print "In internalFrameActivated()"
     
    displayTableTitle = rootContainer.displayTableTitle
    print "The table being displayed is: ", displayTableTitle
    
    SQL = "select V.ValueName, V.ValueId, V.Description, V.DisplayDecimals "\
        " from LtValue V, LtDisplayTable T "\
        " where V.displayTableId = T.DisplayTableId "\
        " and T.DisplayTableTitle = '%s' "\
        " order by ValueName" % (displayTableTitle)
    print SQL
    pds = system.db.runQuery(SQL)
    for record in pds:
        print record["ValueName"], record["ValueId"], record["Description"], record["DisplayDecimals"]
    
    repeater=rootContainer.getComponent("Template Repeater")
    repeater.templateParams=pds


def configureLabDatumTable(container):
    valueName=container.ValueName
    valueDescription=container.Description
    displayDecimals=container.DisplayDecimals
    print "Configuring the Lab Datum Viewer table for ", valueName
    
    # We need to update the column attribute dataset because we change the column name for every parameter and this 
    # freaks out the table widget (same is true for the power table).
    table=container.getComponent("Table")
    columnAttributesData=table.columnAttributesData
    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "name", valueName)
    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "label", valueDescription)
    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "numberFormat", "#,##0.000000")
    table.columnAttributesData=columnAttributesData
    
    
    from ils.labData.common import fetchValueId
    valueId = fetchValueId(valueName)
    SQL = "select top 10 RawValue as '%s', SampleTime from LtHistory where ValueId = %i order by SampleTime desc" % (valueName, valueId)
    pds = system.db.runQuery(SQL)
    container.data=pds 

    header = [valueDescription]
    data = []
    for record in pds:
        val = record[valueName]
        if displayDecimals == 0:
            val = "%.0f" % (val)
        elif displayDecimals == 1:
            val = "%.1f" % (val)
        elif displayDecimals == 2:
            val = "%.2f" % (val)
        elif displayDecimals == 3:
            val = "%.3f" % (val)
        elif displayDecimals == 4:
            val = "%.4f" % (val)
        elif displayDecimals == 5:
            val = "%.5f" % (val)
        else:
            val = "%f" % (val)
            
        myDateString=system.db.dateFormat(record["SampleTime"], "HH:mm MM/d")
        
        val = "%s at %s" % (val, myDateString)
        data.append([val])
    
    ds = system.dataset.toDataSet(header, data)
    container.data=ds
    
    columnAttributesData=table.columnAttributesData
#    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "name", valueName)
    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "label", valueDescription)
#    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "numberFormat", "#,##0.000000")
    table.columnAttributesData=columnAttributesData
    
#    table=container.getComponent("Table")
#    columnAttributesData=table.columnAttributesData
#    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "name", valueName)
#    table.columnAttributesData=columnAttributesData
        