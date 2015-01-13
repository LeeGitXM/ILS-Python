'''
Created on Sep 9, 2014

@author: ILS
'''

import system, string
#
def initialize(rootContainer):
    print "In ils.diagToolkit.setpointSpreadsheet.initialize()..."

    console = rootContainer.console
    repeater = rootContainer.getComponent("Template Repeater")
    
    from ils.diagToolkit.common import fetchActiveOutputsForConsole
    pds = fetchActiveOutputsForConsole(console)
    
    # Create the data structures that will be used to make the dataset the drives the template repeater
    header=['type','row','selected','command','commandValue','application','output','tag','setpoint','recommendation','finalSetpoint','status','downloadStatus']
    rows=[]
    # The data types for the column is set from the first row, so I need to put floats where I want floats, even though they don't show up for the header
    row = ['header',0,0,'Action',0,'','Outputs','',1.2,1.2,1.2,'','']
    rows.append(row)
    
    application = ""
    i = 1
    for record in pds:
        
        # If the record that we are processing is for a different application, or if this is the first row, then insert an application divider row
        if record['Application'] != application:
            application = record['Application']
            row = ['app',i,0,'Active',0,application,'','',0,0,0,'','']
            print "App row: ", row
            rows.append(row)
            i = i + 1

        print "Tag:", record['TagPath']
        qv=system.tag.read(record['TagPath'])
        print qv.value, qv.quality
        row = ['row',i,0,'Active',0,application,record['QuantOutput'],record['TagPath'],qv.value,record['FeedbackOutput'],0,'','']
        print "Output Row: ", row
        rows.append(row)
        i = i + 1

    print rows
    ds = system.dataset.toDataSet(header, rows)
    repeater.templateParams=ds

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
                    txt = "          change to %s adjusted to %f because %s" % (quantOutput, feedbackOutputConditioned, outputLimitedStatus)

    print "Done!"

def detailsCallback(rootContainer):
    title = "Output Details"
    txt = "Foo and bar"
    system.gui.messageBox(txt, title)