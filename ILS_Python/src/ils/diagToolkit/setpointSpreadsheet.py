'''
Created on Sep 9, 2014

@author: ILS
'''

import system, string

def initialize(rootContainer):
    print "In ils.diagToolkit.setpointSpreadsheet.initialize()..."

    post = rootContainer.post
    repeater = rootContainer.getComponent("Template Repeater")
    
    from ils.diagToolkit.common import fetchActiveOutputsForPost
    pds = fetchActiveOutputsForPost(post)
    
    # Create the data structures that will be used to make the dataset the drives the template repeater
    header=['type','row','selected','id','command','commandValue','application','output','tag','setpoint','recommendation','finalSetpoint','status','downloadStatus']
    rows=[]
    # The data types for the column is set from the first row, so I need to put floats where I want floats, even though they don't show up for the header
    row = ['header',0,0,0,'Action',0,'','Outputs','',1.2,1.2,1.2,'','']
    rows.append(row)
    
    application = ""
    i = 1
    for record in pds:
        
        # If the record that we are processing is for a different application, or if this is the first row, then insert an application divider row
        if record['ApplicationName'] != application:
            # Remember the row number of the application because we will need to update the status if we encounter
            # any minimum change bound outputs
            applicationRowNumber = i
            minChangeBoundCounter = 0
             
            application = record['ApplicationName']
            applicationRow = ['app',i,0,0,'Active',0,application,'','',0,0,0,'','']
            print "App row: ", applicationRow
            rows.append(applicationRow)
            i = i + 1

        outputLimited = record['OutputLimited']
        outputLimitedStatus = record['OutputLimitedStatus']
        if outputLimitedStatus == 'Positive Incremental Bound':
            statusMessage='<HTML>CLAMPED<br>(+ Incr)'
        elif outputLimitedStatus == 'Negative Incremental Bound':
            statusMessage='<HTML>CLAMPED<br>(- Incr)'
        elif outputLimitedStatus == 'Positive Absolute Bound':
            statusMessage='<HTML>CLAMPED<br>(High)'
        elif outputLimitedStatus == 'Negative Absolute Bound':
            statusMessage='<HTML>CLAMPED<br>(Low)'
        elif outputLimitedStatus == 'Vector':
            statusMessage='<HTML>CLAMPED<br>(Vector)'
        elif outputLimitedStatus == 'Minimum Change Bound':
            statusMessage='<HTML>CLAMPED<br>(Min Change)'
            minChangeBoundCount = minChangeBoundCounter + 1
            if minChangeBoundCount == 1:
                applicationRow[12]="%i output < minimum change" % (minChangeBoundCount)
            else:
                applicationRow[12]="%i outputs < minimum change" % (minChangeBoundCount)
            rows[applicationRowNumber]=applicationRow
        else:
            statusMessage=''
        
        # Regardless of whether the quant output is incremental or absolute, the recommendation displayed on 
        # the setpoint spreadsheet is ALWAYS incremental.  In fact, the feedbackOutput that is stored in the 
        # QuantOutput table is always incremental.
        # If the recommended change is insignificant (< the minimum change) then don't display it, but we do 
        # want to update the status field of the Application line
        if outputLimitedStatus != 'Minimum Change Bound':
            row = ['row',i,0,record['QuantOutputId'],'GO',0,application,record['QuantOutputName'],record['TagPath'],record['CurrentSetpoint'],record['DisplayedRecommendation'],record['FinalSetpoint'],statusMessage,'']
            print "Output Row: ", row
            rows.append(row)
            i = i + 1

    print rows
    ds = system.dataset.toDataSet(header, rows)
    repeater.templateParams=ds
    repeater.selectedRow = -1

def writeFileCallback(rootContainer):
    print "In writeFileCallback()..."
    logFileName=system.file.openFile('*.log')
    writeFile(rootContainer, logFileName)

# The state of the diagnosis / recommendations are written to a file for various reasons, including from the toolbar button 
# and as part of a download request.  The contents of the file are not simply the lines of the spreadsheet, in order to keep
# the same format as the old platform, we need to query the database and get the data that was used to build the spreadsheet.
def writeFile(rootContainer, filepath):
    print "In writeFile() to ", filepath
    console = rootContainer.console

    exists=system.file.fileExists(filepath)
    if not(exists):
        print "Write some sort of new file header"

    from ils.diagToolkit.common import fetchApplicationsForConsole
    applicationPDS = fetchApplicationsForConsole(console)
    for applicationRecord in applicationPDS:
        application=applicationRecord['Application']
        system.file.writeFile(filepath, "    Application: %s\n" % (application), True)
        
        from ils.diagToolkit.common import fetchActiveDiagnosis
        finalDiagnosisPDS=fetchActiveDiagnosis(application)
        for finalDiagnosisRecord in finalDiagnosisPDS:
            family=finalDiagnosisRecord['Family']
            finalDiagnosis=finalDiagnosisRecord['FinalDiagnosis']
            finalDiagnosisId=finalDiagnosisRecord['FinalDiagnosisId']
            recommendationMultiplier=finalDiagnosisRecord['RecommendationMultiplier']
            recommendationErrorText=finalDiagnosisRecord['RecommendationErrorText']
            print "Final Diagnosis: ", finalDiagnosis, finalDiagnosisId, recommendationErrorText
            
            if recommendationMultiplier < 0.99 or recommendationMultiplier > 1.01:
                system.file.writeFile(filepath, "       Diagnosis -- %s (multiplier = %f)\n" % (finalDiagnosis, recommendationMultiplier), True)
            else:
                system.file.writeFile(filepath, "       Diagnosis -- %s\n" % (finalDiagnosis), True)

            if recommendationErrorText != None:
                system.file.writeFile(filepath, "       %s\n\n" % (recommendationErrorText), True) 

            from ils.diagToolkit.common import fetchSQCRootCauseForFinalDiagnosis
            rootCauseList=fetchSQCRootCauseForFinalDiagnosis(finalDiagnosis)
            for rootCause in rootCauseList:
                print "Root cause: ????", rootCause

            from ils.diagToolkit.common import fetchOutputsForFinalDiagnosis
            pds, outputs=fetchOutputsForFinalDiagnosis(application, family, finalDiagnosis)
            for record in outputs:
                print record
                quantOutput = record.get('QuantOutput','')
                tagPath = record.get('TagPath','')
                feedbackOutput=record.get('FeedbackOutput',0.0)
                feedbackOutputConditioned = record.get('FeedbackOutputConditioned',0.0)
                manualOverride=record.get('ManualOverride', False)
                outputLimited=record.get('OutputLimited', False)
                outputLimitedStatus=record.get('OutputLimitedStatus', '')
                print "Manual Override: ", manualOverride
                txt = "          the desired change in %s = %f" % (tagPath, feedbackOutput)
                if manualOverride:
                    txt = "%s  (manually specified)" % (txt)
                system.file.writeFile(filepath, txt + "\n", True)

                if outputLimited and feedbackOutput != 0.0:
                    txt = "          change to %s returnadjusted to %f because %s" % (quantOutput, feedbackOutputConditioned, outputLimitedStatus)

    print "Done!"

def detailsCallback(rootContainer):
    repeater=rootContainer.getComponent("Template Repeater")
    
    # Check if there is a selected row (could be an app or a quant output
    selectedRow=repeater.selectedRow
    if selectedRow < 0:
        system.gui.warningBox("Please select a row first")
        return
    
    # Get the quant output for the row
    ds = repeater.templateParams
    quantOutputId=ds.getValueAt(selectedRow, 'id')
    
    system.nav.openWindow('DiagToolkit/Recommendation Map', {'quantOutputId' : quantOutputId})
    system.nav.centerWindow('DiagToolkit/Recommendation Map')

# This is called when the operator selects a cell in the "Status" column
def statusCallback(event):
    label=event.source
    container=label.parent
    template=container.parent
    row=template.row

    window=system.gui.getParentWindow(event)
    rootContainer=window.rootContainer
    
    repeater=rootContainer.getComponent("Template Repeater")
    
    # Get the quant output for the row
    ds = repeater.templateParams
    quantOutputId=ds.getValueAt(row, 'id')

    # Fetch everything about the quant output from the database
    from ils.diagToolkit.common import fetchQuantOutput
    pds = fetchQuantOutput(quantOutputId)
    if len(pds) == 0:
        system.gui.warningBox("The Quant Output was not found")
        return
    
    if len(pds) > 1:
        system.gui.warningBox("Multiple quant outputs were found where only one was expected!")
        return

    # Format the information
    record=pds[0]
    quantOutput = record['QuantOutput']   
    outputLimited=record['OutputLimited']
    outputLimitedStatus=record['OutputLimitedStatus']
    mostNegativeIncrement=record['MostNegativeIncrement']
    mostPositiveIncrement=record['MostPositiveIncrement']
    minimumIncrement=record['MinimumIncrement']
    setpointHighLimit=record['SetpointHighLimit']
    setpointLowLimit=record['SetpointLowLimit']
    
    limitDetails = "The Output limit details are:\n  Max Positive Change: %f\n"\
            "  Max Negative Change: %f\n  Min Change: %f\n  Max Setpoint: %f\n  Min Setpoint: %f" \
            % (mostPositiveIncrement, mostNegativeIncrement, minimumIncrement, setpointHighLimit, setpointLowLimit)
    
    if outputLimited:
        if outputLimitedStatus == 'Vector':
            txt = "The output (%s) is %s limited!\n\nIt was reduced from %.2f to %.2f because the most bound output "\
                "could only use %.0f%% of its value" % (quantOutput, outputLimitedStatus, record['FeedbackOutput'], \
                                                    record['FeedbackOutputConditioned'], record['OutputPercent'])
        else:
            txt = "The output (%s) is %s limited!\n\n%s" % (quantOutput, outputLimitedStatus, limitDetails)
    else:
        txt = "The output (%s) is not limited!\n\n%s" % (quantOutput, limitDetails)
    
    title = "Output Details"

    system.gui.messageBox(txt, title)