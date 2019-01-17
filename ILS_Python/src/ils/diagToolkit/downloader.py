'''
Created on Jul 17, 2018

@author: phass
'''
import system, string, threading, time
from ils.io.util import getOuterUDT
from ils.io.api import write
from ils.queue.message import insertPostMessage
log = system.util.getLogger("com.ils.diagToolkit.downloader")

class DownloadThread(threading.Thread):
    downloader = None
    quantOutputId = None
    tagPath = None
    newSetpoint = None
    writeConfirm = None
    valueType = None
    
    def __init__(self, downloader, quantOutputId, tagPath, newSetpoint, writeConfirm, valueType):
        log.info("Initializing...")
        threading.Thread.__init__(self)
        self.downloader = downloader
        self.quantOutputId = quantOutputId
        self.tagPath = tagPath
        self.newSetpoint = newSetpoint
        self.writeConfirm = writeConfirm
        self.valueType = valueType
        
    def run(self):
        log.infof("Running download thread for writing %s to %s...", str(self.newSetpoint), self.tagPath)
        
        success, errorMessage = write(self.tagPath, self.newSetpoint, self.writeConfirm, self.valueType)
        
        if success:
            self.downloader.updateQuantOutputDownloadStatus(self.quantOutputId, "Success")
            self.downloader.logbookMessage += "confirmed\n"
            print "The write was successful"
        else:
            print "The write FAILED because: ", errorMessage
            self.downloader.updateQuantOutputDownloadStatus(self.quantOutputId, "Error")
            self.downloader.logbookMessage += "failed because of an error: %s\n" % (errorMessage)

        log.infof("...done!")

class Downloader():
    post = None
    ds = None
    tagProvider = None
    db = None
    threads = None
    runningCount = None
    logbookMessage = ""
    
    def __init__(self, post, ds, tagProvider, db):
        self.post = post
        self.ds = ds
        self.tagProvider = tagProvider
        self.db = db
        self.threads = []
        self.runningCount = 0
        self.logbookMessage = "<HTML>Download performed for the following:<UL>"

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
        This was 10 seconds, which is an eternity.  Changing to 1 second.
        '''
        print "Sleeping..."
        time.sleep(1)
        print "Waking up..."
        
        ''' Now get to work on the download... '''
        for row in range(self.ds.rowCount):
            rowType = self.ds.getValueAt(row, "type")
            if rowType == "app":
                applicationName = self.ds.getValueAt(row, "application")
                self.logbookMessage += "<LI>Application: %s<UL>" % applicationName
                firstOutputRow = True
                
            elif rowType == "row":
                command = self.ds.getValueAt(row, "command")
                downloadStatus = self.ds.getValueAt(row, "downloadStatus")
                if string.upper(command) == 'GO' and string.upper(downloadStatus) in ['', 'ERROR']:
                    if firstOutputRow:
                        # When we encounter the first output row, write out information about the Final diagnosis and violated SQC rules
                        firstOutputRow = False
                        self.logbookMessage += self.constructDownloadLogbookMessage(applicationName)
        
        
                    quantOutput = self.ds.getValueAt(row, "output")
                    quantOutputId = self.ds.getValueAt(row, "qoId")
                    tag = self.ds.getValueAt(row, "tag")
                    newSetpoint = self.ds.getValueAt(row, "finalSetpoint")
                    tagPath="[%s]%s" % (self.tagProvider, tag)
    
                    self.logbookMessage += "      download of %s to the value %f was " % (tagPath, newSetpoint)
                    
                    if diagToolkitWriteEnabled:
                        print "Row %i - Downloading %s to Output %s - Tag %s" % (row, str(newSetpoint), quantOutput, tagPath)
                        
                        # From the tagpath determine if we are writing directly to an OPC tag or to a controller
                        UDTType, tagPath = getOuterUDT(tagPath)
                        
                        downloadThread = DownloadThread(self, quantOutputId, tagPath, newSetpoint, writeConfirm=True, valueType='setpoint')
                        downloadThread.start()
                        self.threads.append(downloadThread)
                        self.runningCount = self.runningCount + 1

                    else:
                        print "...writes from the diagnostic toolkit are disabled..."
                        insertPostMessage(self.post, "Warning", "Write to %s-%s was skipped because writes from the diag toolkit are disabled." % (quantOutput, tagPath), self.db)
                        self.updateQuantOutputDownloadStatus(quantOutputId, "Error")
                        self.logbookMessage += "failed because diag toolkit writes are disabled\n"
        
        ''' Now monitor the threads until they are done '''
        while self.runningCount > 0:
            self.runningCount = 0
            for thread in self.threads:
                if thread.isAlive():
                    self.runningCount = self.runningCount + 1
                    
            log.infof("There are %d threads still running", self.runningCount)
            time.sleep(1)
        
        log.infof("All of the dowwnloads are complete")
        
        from ils.common.operatorLogbook import insertForPost
        log.tracef("Logging logbook message: %s", self.logbookMessage)
        insertForPost(self.post, self.logbookMessage, self.db)


    def updateQuantOutputDownloadStatus(self, quantOutputId, downloadStatus):
        SQL = "update DtQuantOutput set DownloadStatus = '%s' where QuantOutputId = %i " % (downloadStatus, quantOutputId)
        log.trace(SQL)
        system.db.runUpdateQuery(SQL, self.db)
        
    def constructDownloadLogbookMessage(self, applicationName):
        from ils.diagToolkit.common import fetchSQCRootCauseForFinalDiagnosis
        from ils.diagToolkit.common import fetchHighestActiveDiagnosis
        pds = fetchHighestActiveDiagnosis(applicationName, self.db)
        txt = ""
        
        # If there are more than on final diagnosis active, then print the individual recommendation contributions from each
        # recommendation and then a summary at the end
        if len(pds) > 1:
            print "The individual contributions from each diagnosis are:"
            txt += "    The individual contributions from each diagnosis are:\n"
            finalDiagnosisIds = []
            for finalDiagnosisRecord in pds:
                finalDiagnosisName=finalDiagnosisRecord['FinalDiagnosisName']
                finalDiagnosisId=finalDiagnosisRecord['FinalDiagnosisId']
                finalDiagnosisIds.append(finalDiagnosisId)
                multiplier=finalDiagnosisRecord['Multiplier']
                recommendationErrorText=finalDiagnosisRecord['RecommendationErrorText']
                
                if multiplier < 0.99 or multiplier > 1.01:
                    txt += "       Diagnosis -- %s (multiplier = %f)\n" % (finalDiagnosisName, multiplier)
                else:
                    txt += "       Diagnosis -- %s\n" % (finalDiagnosisName)
        
                if recommendationErrorText != None:
                    txt += "       %s\n\n" % (recommendationErrorText) 
    
                rootCauseList=fetchSQCRootCauseForFinalDiagnosis(finalDiagnosisName)
                for rootCause in rootCauseList:
                    txt += "      %s\n" % (rootCause)
    
                recPDS = self.fetchRecommendationsForFinalDiagnosis(finalDiagnosisId) 
                for record in recPDS:
                    print record["QuantOutputName"], record["TagPath"], record["Recommendation"], record["AutoRecommendation"], record["ManualRecommendation"], record["AutoOrManual"]
                    txt += "          the desired change in %s = %f\n" % (record["TagPath"], record["AutoRecommendation"])
            
            # Now print the summary
            txt += "\n    The combined recommendations are:\n"    
            pds = self.fetchOutputsForListOfFinalDiagnosis(finalDiagnosisIds)
            for record in pds:
                quantOutputName = record['QuantOutputName']
                quantOutputId = record['QuantOutputId']
                print "%s - %s" % (str(quantOutputId), quantOutputName)
                tagPath = record['TagPath']
                feedbackOutput=record['FeedbackOutput']
                feedbackOutputConditioned = record['FeedbackOutputConditioned']
                manualOverride=record['ManualOverride']
                outputLimited=record['OutputLimited']
                outputLimitedStatus=record['OutputLimitedStatus']
                print "Manual Override: ", manualOverride
                txt += "          the desired change in %s = %s" % (tagPath, str(feedbackOutput))
                if manualOverride:
                    txt += "%s  (manually specified)" % (txt)
                txt += "\n"
    
                if outputLimited and feedbackOutput != 0.0:
                    txt = "          change to %s adjusted to %s because %s" % (quantOutputName, str(feedbackOutputConditioned), outputLimitedStatus)
            
        else:
            
            for finalDiagnosisRecord in pds:
                family=finalDiagnosisRecord['FamilyName']
                finalDiagnosis=finalDiagnosisRecord['FinalDiagnosisName']
                finalDiagnosisId=finalDiagnosisRecord['FinalDiagnosisId']
                multiplier=finalDiagnosisRecord['Multiplier']
                recommendationErrorText=finalDiagnosisRecord['RecommendationErrorText']
                print "Final Diagnosis: ", finalDiagnosis, finalDiagnosisId, recommendationErrorText
                    
                if multiplier < 0.99 or multiplier > 1.01:
                    txt += "<LI>Diagnosis -- %s (multiplier = %f)" % (finalDiagnosis, multiplier)
                else:
                    txt += "<LI>Diagnosis -- %s" % (finalDiagnosis)
        
                if recommendationErrorText != None:
                    txt += "<UL><LI>%s</UL>" % (recommendationErrorText) 
        
                rootCauseList=fetchSQCRootCauseForFinalDiagnosis(finalDiagnosis)
                for rootCause in rootCauseList:
                    txt += "      %s\n" % (rootCause)
        
                from ils.diagToolkit.common import fetchActiveOutputsForFinalDiagnosis
                pds, outputs=fetchActiveOutputsForFinalDiagnosis(applicationName, family, finalDiagnosis)
                txt += "<UL>"
                for record in outputs:
                    print record
                    quantOutput = record.get('QuantOutput','')
                    tagPath = record.get('TagPath','')
                    feedbackOutput=record.get('FeedbackOutput',0.0)
                    feedbackOutputConditioned = record.get('FeedbackOutputConditioned',0.0)
                    manualOverride=record.get('ManualOverride', False)
                    outputLimited=record.get('OutputLimited', False)
                    outputLimitedStatus=record.get('OutputLimitedStatus', '')
                    if feedbackOutput <> None:
                        txt += "<LI>the desired change in %s = %s" % (tagPath, str(feedbackOutput))
                        if manualOverride:
                            txt += "%s  (manually specified)" % (txt)
            
                        if outputLimited and feedbackOutput != 0.0:
                            txt += "          change to %s adjusted to %s because %s\n" % (tagPath, str(feedbackOutputConditioned), outputLimitedStatus)
                txt += "</UL>"
        return txt
    
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
        
'''
===============================================================================================
'''
def serviceDownload(post, ds, tagProvider, db):
    # iterate through each row of the dataset that is marked to go and download it.
    log.info("Starting to download...")
    