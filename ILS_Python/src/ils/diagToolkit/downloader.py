'''
Created on Jul 17, 2018

@author: phass
'''
import system, string, threading, time
from ils.io.util import getOuterUDT
from ils.io.api import write, writeRamp
from ils.queue.message import insertPostMessage

from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

class DownloadThread(threading.Thread):
    '''
    This inherits from a thread class, so it inherits a start method, which executes a run method.
    '''
    downloader = None
    quantOutputId = None
    tagPath = None
    newSetpoint = None
    writeConfirm = None
    valueType = None
    rampTime = None
    row = None
    valType = "SETPOINT RAMP"  #Presumably this should also support an output ramp??
    updateFrequency = 10
    
    def __init__(self, downloader, row, quantOutputId, tagPath, newSetpoint, rampTime, writeConfirm, valueType):
        log.infof("Initializing... (ramp time = %s)", str(rampTime))
        threading.Thread.__init__(self)
        self.downloader = downloader
        self.quantOutputId = quantOutputId
        self.tagPath = tagPath
        self.newSetpoint = newSetpoint
        self.writeConfirm = writeConfirm
        self.valueType = valueType
        self.rampTime = rampTime
        self.row = row
        
    def run(self):
        '''
        Be really careful with the handling of rampTime here.  It looks like None but it is really "None".  Not sure exactly who converted it to a text string...
        '''
        log.infof("Running download thread #%d for writing %s to %s (ramp time = %s)...", self.row, str(self.newSetpoint), self.tagPath, self.rampTime)
        
        if self.rampTime in ["", "None", None]:
            success, errorMessage = write(self.tagPath, self.newSetpoint, self.writeConfirm, self.valueType)
        else:
            success, errorMessage = writeRamp(self.tagPath, self.newSetpoint, self.valType, self.rampTime, self.updateFrequency, self.writeConfirm)
        
        if success:
            self.downloader.updateQuantOutputDownloadStatus(self.quantOutputId, "Success")
            self.downloader.logbookMessage += "confirmed\n"
            print "The write was successful"
        else:
            print "The write FAILED because: ", errorMessage
            self.downloader.updateQuantOutputDownloadStatus(self.quantOutputId, "Error")
            self.downloader.logbookMessage += "failed because of an error: %s\n" % (errorMessage)

        log.infof("...finished a download thread #%d for writing %s to %s!", self.row, str(self.newSetpoint), self.tagPath)

class Downloader():
    '''
    This class is created when we receive a serviceDownload message from the client.  This class creates a download thread for each output that needs to be 
    downloaded.  This class lives until all of the threads are done.
    '''
    post = None
    ds = None
    tagProvider = None
    db = None
    threads = None
    runningCount = None
    logbookMessage = ""
    downloadStatus = {}

    def __init__(self, post, ds, tagProvider, db):
        log.infof("In %s, creating a Downloader for %s...", __name__, post)
        self.post = post
        self.ds = ds
        self.tagProvider = tagProvider
        self.db = db
        self.threads = []
        self.runningCount = 0
        self.logbookMessage = ""

    def download(self):
        log.infof("Start Downloading...")
        
        diagToolkitWriteEnabled = system.tag.read("[" + self.tagProvider + "]/Configuration/DiagnosticToolkit/diagnosticToolkitWriteEnabled").value
        log.tracef("DiagToolkitWriteEnabled: %s", str(diagToolkitWriteEnabled))
    
        # First update the download status of every output we intend to write
        for row in range(self.ds.rowCount):
            rowType = self.ds.getValueAt(row, "type")
            if rowType == "row":
                command = self.ds.getValueAt(row, "command")
                downloadStatus = self.ds.getValueAt(row, "downloadStatus")
                if string.upper(command) == 'GO' and string.upper(downloadStatus) in ['', 'ERROR']:
                    quantOutputId = self.ds.getValueAt(row, "qoId")
                    self.updateQuantOutputDownloadStatus(quantOutputId, "Pending")
                
        '''
        Not sure what the purpose of this sleep is.  Not sure if there are database transactions that we want to give time to complete.
        This was 10 seconds, which is an eternity.  Changing to 1 second.  I think this was to make sure 
        '''
        time.sleep(1)
        
        ''' Now get to work on the download... '''
        for row in range(self.ds.rowCount):
            rowType = self.ds.getValueAt(row, "type")
            if rowType == "app":
                applicationName = self.ds.getValueAt(row, "application")
                
            elif rowType == "row":
                command = self.ds.getValueAt(row, "command")
                downloadStatus = self.ds.getValueAt(row, "downloadStatus")
                if string.upper(command) == 'GO' and string.upper(downloadStatus) in ['', 'ERROR']:        
                    quantOutput = self.ds.getValueAt(row, "output")
                    quantOutputId = self.ds.getValueAt(row, "qoId")
                    rampTime = self.ds.getValueAt(row, "ramp")
                    if rampTime == None:
                        print "*** It is None here ***"
                    tag = self.ds.getValueAt(row, "tag")
                    newSetpoint = self.ds.getValueAt(row, "finalSetpoint")
                    tagPath="[%s]%s" % (self.tagProvider, tag)
                    
                    if diagToolkitWriteEnabled:
                        log.infof( "Row %d - Downloading %s to Output %s - Tag %s, Ramp time: %s", row, str(newSetpoint), quantOutput, tagPath, str(rampTime))
                        
                        # From the tagpath determine if we are writing directly to an OPC tag or to a controller
                        UDTType, tagPath = getOuterUDT(tagPath)
                        
                        downloadThread = DownloadThread(self, row, quantOutputId, tagPath, newSetpoint, rampTime, writeConfirm=True, valueType='setpoint')
                        downloadThread.start()
                        self.threads.append(downloadThread)
                        self.runningCount = self.runningCount + 1

                    else:
                        print "...writes from symbolic ai are disabled..."
   
                        insertPostMessage(self.post, "Warning", "Write to %s-%s was skipped because writes from the diag toolkit are disabled." % (quantOutput, tagPath), self.db)
                        self.updateQuantOutputDownloadStatus(quantOutputId, "Error")
        
        ''' Now monitor the threads until they are done '''
        while self.runningCount > 0:
            self.runningCount = 0
            for thread in self.threads:
                if thread.isAlive():
                    self.runningCount = self.runningCount + 1
                    
            log.infof("There are %d threads still running", self.runningCount)
            time.sleep(1)
        
        log.infof("All of the downloads are complete")
        
        ''' Now make a logbook message for the download '''
#        self.downloadMessage()
        
#        from ils.common.operatorLogbook import insertForPost
#        log.tracef("Logging logbook message: %s", self.logbookMessage)
#        insertForPost(self.post, self.logbookMessage, self.db)


    def updateQuantOutputDownloadStatus(self, quantOutputId, downloadStatus):
        ''' Update the database, which will drive th GUI om the client '''
        print "Updating the download status for %s to %s" % (str(quantOutputId), downloadStatus)
        
        SQL = "update DtQuantOutput set DownloadStatus = '%s' where QuantOutputId = %i " % (downloadStatus, quantOutputId)
        log.trace(SQL)
        system.db.runUpdateQuery(SQL, self.db)
        
        self.downloadStatus[quantOutputId] = downloadStatus
        return
    
        ds = self.ds
        for row in range(ds.getRowCount()):
            if ds.getValueAt(row, "qoid") == quantOutputId:
                print "...updating row %s..." % (str(row))
                ds = system.dataset.setValue(ds, row, "downloadStatus", downloadStatus)
        self.ds = ds
        
    def downloadMessage(self, messageType="download"):
        '''
        Because this is a pretty complicated logbook message I am formatting it using HTML, but be careful to keep the HTML pretty simple.
        I tried to use a tabl to display the quant output contribution for multiple final diagnosis but the report viewer widget didn't support it
        even though I could put the same HTML into chrome and it looked great!
        '''
        from ils.diagToolkit.common import fetchSQCRootCauseForFinalDiagnosis
        from ils.diagToolkit.common import fetchHighestActiveDiagnosis
        print "============================================================================="
        log.tracef("In %s.downloadMessage(), messageType: %s", __name__, str(messageType))
        print "The download status dictionary is: ", self.downloadStatus

        noteText = ""
        fdText = "" 
        ds = self.ds
        if string.upper(messageType) == "DOWNLOAD":
            self.logbookMessage = "<HTML>Download performed for the following:<UL>"
        elif string.upper(messageType) == "NO_DOWNLOAD":
            self.logbookMessage = "<HTML>Download <b>NOT</b> performed for the following:<UL>"
        elif string.upper(messageType) == "WAIT":
            self.logbookMessage = "<HTML>Wait for more data requested before acting on the following:<UL>"
        
        ''' print out the contents of the repeater dataset for debugging '''
        for row in range(ds.getRowCount()):
            txt = ""
            for col in range(ds.getColumnCount()):
                txt += "%s ," % (ds.getValueAt(row,col))
            print row, txt
        
        ''' Process the contents of the repeater row by row'''
        for row in range(ds.getRowCount()):
            rowType = self.ds.getValueAt(row, "type")
            if rowType == "app":
                applicationName = self.ds.getValueAt(row, "application")
                log.tracef("Handling an application - %s", applicationName)
                
                pds = fetchHighestActiveDiagnosis(applicationName, self.db)
                log.tracef("There are %d high active diagnosis for this application", len(pds))

                if fdText != "" or noteText != "":
                    self.logbookMessage += fdText
                    self.logbookMessage += noteText
                    noteText = ""
                    fdText = ""
                    
                ''' Multiple diagnosis have contributed so list the contributions by final diagnosis '''
                
                outputs = getOutputsForApplication(ds, applicationName)
                
                if len(pds) > 1:
                    fdText = "<LI>Application: %s (Multiple final diagnosis have contributed to the move)<UL>" % applicationName
                    log.tracef("There are multiple diagnosis that contributed to this application.")
                elif len(pds) == 1:
                    fdText = "<LI>Application: %s<UL>" % applicationName
                    log.tracef("There is a SINGLE diagnosis.")
                else:
                    fdText = "<LI>Application: %s<UL> No Active Applications" % applicationName
                    log.tracef("There are no active diagnosis.")

                finalDiagnosisRecommendations = {}
                finalDiagnosisIds = []
                for finalDiagnosisRecord in pds:
                    print "...working..."
                    finalDiagnosisId = finalDiagnosisRecord['FinalDiagnosisId']
                    recommendationPDS = self.fetchRecommendationsForFinalDiagnosis(finalDiagnosisId)
                    finalDiagnosisName = finalDiagnosisRecord['FinalDiagnosisName']
                    finalDiagnosisIds.append(finalDiagnosisId)
                    multiplier=finalDiagnosisRecord['Multiplier']
                    recommendationErrorText=finalDiagnosisRecord['RecommendationErrorText']
                    
                    if multiplier < 0.99 or multiplier > 1.01:
                        fdText += "<LI>Diagnosis -- %s (multiplier = %f)" % (finalDiagnosisName, multiplier)
                    else:
                        fdText += "<LI>Diagnosis -- %s" % (finalDiagnosisName)
            
                    if recommendationErrorText != None:
                        fdText += "%s" % (recommendationErrorText) 
        
                    rootCauseList=fetchSQCRootCauseForFinalDiagnosis(finalDiagnosisName)
                    for rootCause in rootCauseList:
                        fdText += "%s" % (rootCause)
            
                    ''' Start an embedded list of individual recommendations for this Final Diagnosis '''
                    fdText += "<UL>"
                    
                    recommendationPDS = self.fetchRecommendationsForFinalDiagnosis(finalDiagnosisId)

                    for recRecord in recommendationPDS:
                        outputName = recRecord["QuantOutputName"]
                        tagPath = recRecord["TagPath"]
                        autoRecommendation = recRecord["AutoRecommendation"]
                        fdText += "<li>desired change in %s = %f</li>" % (tagPath, autoRecommendation)
                    fdText += "</UL>"
                fdText += "</UL>"
                
                print "Done processing an APP row: ", fdText

                writeResultsText = "<LI>Download Results:<UL>"
                
            elif rowType == "row":
                log.tracef("Handling a row...")
                command = self.ds.getValueAt(row, "command")
                downloadStatus = self.ds.getValueAt(row, "downloadStatus")
                log.tracef("...command: %s, download status: %s", command, downloadStatus)
                if string.upper(command) == 'GO' and string.upper(downloadStatus) in ['', 'ERROR', 'SUCCESS']:

                    qoId = self.ds.getValueAt(row, "qoid")
                    log.tracef("Processing Quant Output: %d", qoId)
                    record = self.fetchQuantOutput(qoId)
                    
                    quantOutputName = record['QuantOutputName']
                    quantOutputId = record['QuantOutputId']
                    print "%s - %s" % (str(quantOutputId), quantOutputName)
                    tagPath = record['TagPath']
                    feedbackOutput=record['FeedbackOutput']
                    feedbackOutputManual=record['FeedbackOutputManual']
                    feedbackOutputConditioned = record['FeedbackOutputConditioned']
                    manualOverride=record['ManualOverride']
                    outputLimited=record['OutputLimited']
                    outputLimitedStatus=record['OutputLimitedStatus']
                    print "Manual Override: ", manualOverride
                    
                    if manualOverride or (outputLimited and feedbackOutput != 0.0):
                        if manualOverride:
                            noteText += "<LI>Desired change for %s was manually changed to %.4f" % (quantOutputName, feedbackOutputManual)
    
                        if outputLimited and feedbackOutput != 0.0:
                            noteText += "<LI>%s was adjusted to %s because %s" % (quantOutputName, str(feedbackOutputConditioned), outputLimitedStatus)
                        
                    ''' There is a combined section for the results of the write '''
                    if string.upper(messageType) == "DOWNLOAD":
                        tag = self.ds.getValueAt(row, "tag")
                        newSetpoint = self.ds.getValueAt(row, "finalSetpoint")
                        tagPath="[%s]%s" % (self.tagProvider, tag)
                        writeResultsText += "<LI>download of %.4f to %s was %s" % (newSetpoint, tagPath, downloadStatus)
            
        self.logbookMessage += fdText
        if noteText != "":
            self.logbookMessage += "<li>Notes</lu>"
            self.logbookMessage += "<ul>"
            self.logbookMessage += noteText
            self.logbookMessage += "</ul>"       
                
        if string.upper(messageType) == "DOWNLOAD":
            self.logbookMessage += writeResultsText
            
        print self.logbookMessage
        print "============================================================================="

    
    '''
    Fetch the outputs for a final diagnosis and return them as a list of dictionaries
    I'm not sure who the clients for this will be so I am returning all of the attributes of a quantOutput.  This includes the attributes 
    that are used when calculating/managing recommendations and the output of those recommendations.
    '''
    def fetchRecommendationsForFinalDiagnosis(self, finalDiagnosisId):
        SQL = "select QO.QuantOutputName, QO.TagPath, QO.MostNegativeIncrement, QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, "\
            " QO.SetpointLowLimit, L.LookupName FeedbackMethod, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, QO.IncrementalOutput, "\
            " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.QuantOutputId, QO.IgnoreMinimumIncrement, "\
            " R.Recommendation, R.AutoRecommendation, R.ManualRecommendation, R.AutoOrManual "\
            " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, DtRecommendation R, Lookup L "\
            " where L.LookupTypeCode = 'FeedbackMethod'"\
            " and L.LookupId = QO.FeedbackMethodId "\
            " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
            " and RD.QuantOutputId = QO.QuantOutputId "\
            " and RD.RecommendationDefinitionId = R.RecommendationDefinitionId "\
            " and FD.FinalDiagnosisId = %s "\
            " order by QuantOutputName"  % ( str(finalDiagnosisId))
        log.trace(SQL)
        pds = system.db.runQuery(SQL, self.db)
        return pds

    '''
    Fetch the outputs for a final diagnosis and return them as a list of dictionaries
    I'm not sure who the clients for this will be so I am returning all of the attributes of a quantOutput.  This includes the attributes 
    that are used when calculating/managing recommendations and the output of those recommendations.
    '''
    def fetchOutputsForListOfFinalDiagnosis(self, finalDiagnosisIdList):
        ids = ','.join(str(t) for t in finalDiagnosisIdList)
        SQL = "select distinct QO.QuantOutputName, QO.QuantOutputId, QO.TagPath, QO.MostNegativeIncrement, QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, "\
            " QO.SetpointLowLimit, L.LookupName FeedbackMethod, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, QO.IncrementalOutput, "\
            " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.QuantOutputId, QO.IgnoreMinimumIncrement "\
            " from DtFinalDiagnosis FD, DtRecommendationDefinition RD, DtQuantOutput QO, Lookup L "\
            " where L.LookupTypeCode = 'FeedbackMethod'"\
            " and L.LookupId = QO.FeedbackMethodId "\
            " and FD.FinalDiagnosisId = RD.FinalDiagnosisId "\
            " and RD.QuantOutputId = QO.QuantOutputId "\
            " and QO.Active = 1 "\
            " and FD.FinalDiagnosisId in (%s) "\
            " order by QuantOutputName"  % ( ids )
        print SQL
        log.trace(SQL)
        pds = system.db.runQuery(SQL, self.db)
        return pds
    
    def fetchQuantOutput(self, qoId):
        SQL = "select distinct QO.QuantOutputName, QO.QuantOutputId, QO.TagPath, QO.MostNegativeIncrement, QO.MostPositiveIncrement, QO.MinimumIncrement, QO.SetpointHighLimit, "\
            " QO.SetpointLowLimit, L.LookupName FeedbackMethod, QO.OutputLimitedStatus, QO.OutputLimited, QO.OutputPercent, QO.IncrementalOutput, "\
            " QO.FeedbackOutput, QO.FeedbackOutputManual, QO.FeedbackOutputConditioned, QO.ManualOverride, QO.QuantOutputId, QO.IgnoreMinimumIncrement "\
            " from DtQuantOutput QO, Lookup L "\
            " where L.LookupTypeCode = 'FeedbackMethod'"\
            " and L.LookupId = QO.FeedbackMethodId "\
            " and QO.QuantOutputId = %d" % ( qoId )
        print SQL
        log.trace(SQL)
        pds = system.db.runQuery(SQL, self.db)
        
        ''' This better only return 1 row '''
        return pds[0]

def getOutputsForApplication(ds, applicationName):
    outputs = []
    for row in range(ds.getRowCount()):        
        rowType = ds.getValueAt(row, "type")
        if rowType == "app":
            foundApplication = False
            if applicationName == ds.getValueAt(row, "application"):
                foundApplication = True
        elif rowType == "row":
            if foundApplication:
                outputs.append(ds.getValueAt(row, "output"))
    
    print "The outputs for %s are %s" % (applicationName, outputs)
    return outputs
        
'''
===============================================================================================
'''
def serviceDownload(post, ds, tagProvider, db):
    # iterate through each row of the dataset that is marked to go and download it.
    log.info("Starting to download...")
    