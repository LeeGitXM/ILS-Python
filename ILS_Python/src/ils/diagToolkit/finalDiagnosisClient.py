'''
Created on Jun 30, 2015

@author: Pete
'''
import system

# Not sure if this is used in production, but it is neded for testing
def postDiagnosisEntry(application, family, finalDiagnosis, UUID, diagramUUID, database=""):
    print "Sending a message to post a diagnosis entry..."
    projectName=system.util.getProjectName()
    payload={"application": application, "family": family, "finalDiagnosis": finalDiagnosis, "UUID": UUID, "diagramUUID": diagramUUID, "database": database}
    system.util.sendMessage(projectName, "postDiagnosisEntry", payload, "G")
    