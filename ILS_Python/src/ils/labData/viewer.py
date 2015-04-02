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
    
    SQL = "select V.ValueName, V.ValueId "\
        " from LtValue V, LtDisplayTable T "\
        " where V.displayTableId = T.DisplayTableId "\
        " and T.DisplayTableTitle = '%s' "\
        " order by ValueName" % (displayTableTitle)
    print SQL
    pds = system.db.runQuery(SQL)
    for record in pds:
        print record["ValueName"], record["ValueId"]
    
    repeater=rootContainer.getComponent("Template Repeater")
    repeater.templateParams=pds


def configureLabDatumTable(container):
    valueName=container.ValueName
    print "Configuring the Lab Datum Viewer table for ", valueName
    
    # We need to update the column attribute dataset because we change the column name for every parameter and this 
    # freaks out the table widget (same is true for the power table).
    table=container.getComponent("Table")
    columnAttributesData=table.columnAttributesData
    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "name", valueName)
    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "numberFormat", "#,##0.000000")
    table.columnAttributesData=columnAttributesData
    
    
    from ils.labData.common import fetchValueId
    valueId = fetchValueId(valueName)
    SQL = "select top 10 RawValue as '%s' from LtHistory where ValueId = %i order by SampleTime desc" % (valueName, valueId)
    pds = system.db.runQuery(SQL)
    container.data=pds 

    for record in pds:
        print record[valueName]
    
    table=container.getComponent("Table")
    columnAttributesData=table.columnAttributesData
    columnAttributesData=system.dataset.setValue(columnAttributesData, 0, "name", valueName)
    table.columnAttributesData=columnAttributesData
        