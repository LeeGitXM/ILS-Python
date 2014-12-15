'''
Created on Sep 9, 2014

@author: ILS
'''

import system
#
def initialize(rootContainer):
    print "In project.recipe.viewRecipe.initialize()..."

    console = rootContainer.console
    repeater = rootContainer.getComponent("Template Repeater")
    
    from ils.diagToolkit.common import fetchActiveOutputsForConsole
    pds = fetchActiveOutputsForConsole(console)
    
    # Create the data structures that will be used to make teh dataset the drives the template repeater
    header=['type','row','command','commandValue','application','output','tag','setpoint','recommendation','finalSetpoint','status','downloadStatus']
    rows=[]
    # The data types for the column is set from the first row, so I need to put floats where I want floats, even though they don't show up for the header
    row = ['header',0,'Action',0,'','Outputs','',1.2,1.2,1.2,'','']
    rows.append(row)
    
    application = ""
    i = 1
    for record in pds:
        
        # If the record that we are processing id for a different application, or if this is the first row, then insert an application divider row
        if record['Application'] != application:
            application = record['Application']
            row = ['app',i,'Active',0,application,'','',0,0,0,'','']
            print "App row: ", row
            rows.append(row)
            i = i + 1

        row = ['row',i,'Active',0,application,record['QuantOutput'],record['TagPath'],-99.9,record['FeedbackOutput'],0,'','']
        rows.append(row)
        i = i + 1

    print rows
    ds = system.dataset.toDataSet(header, rows)
    repeater.templateParams=ds