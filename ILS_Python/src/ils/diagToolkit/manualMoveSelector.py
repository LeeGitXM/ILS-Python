'''
Created on Jan 11, 2019

@author: phass
'''

import system
from ils.common.config import getDatabaseClient
from com.jidesoft.grid import Row

def launcher(event):
    print "In %s.launcher()" % (__name__)
    
    username = system.security.getUsername()
    
    ''' Verify that the user is autorized to make an adhoc move '''
    ds = system.tag.read("Configuration/DiagnosticToolkit/manualChangeUsernames").value
    
    if ds == None:
        unauthorizedUserWarning(username)
        return
    
    authorized = False
    for row in range(ds.getRowCount()):
        user = ds.getValueAt(row,0)
        print row, user
        if user == username:
            authorized = True
    
    if not(authorized):
        unauthorizedUserWarning(username)
        return
    
    post = event.source.parent.post
    checkPost = event.source.parent.checkPost
    dict = {"post":post, "checkPost":checkPost}
    window = system.nav.openWindow("DiagToolkit/Manual Move Selector", dict)
    system.nav.centerWindow(window)

def unauthorizedUserWarning(username):
    system.gui.errorBox("You (%s) are not authorized to use the ADHOC MOVE action.  See your local AE to authorize you." % (username))
    return

def internalFrameOpened(rootContainer):
    print "In %s.internalFrameOpened()" % (__name__)
    post = rootContainer.post
    checkPost = rootContainer.checkPost
    
    db = getDatabaseClient()
    
    if post == "" or not(checkPost):
        SQL = "SELECT FinalDiagnosisName, FinalDiagnosisUUID, DiagramUUID, FinalDiagnosisId "\
            "FROM DtFinalDiagnosis "\
            "WHERE Constant = 0 "\
            "AND ManualMoveAllowed = 1 "\
            "ORDER BY FinalDiagnosisName"
    else:
        SQL = "SELECT FD.FinalDiagnosisName, FD.FinalDiagnosisUUID, FD.DiagramUUID, FD.FinalDiagnosisId "\
            "FROM DtFinalDiagnosis FD, DtFamily F, DtApplication A, TkUnit U, TkPost P "\
            "WHERE FD.FamilyId = F.FamilyId "\
            "AND F.ApplicationId = A.ApplicationId "\
            "AND A.UnitId = U.UnitId "\
            "AND U.PostId = P.PostId "\
            "AND P.Post = '%s' "\
            "AND FD.Constant = 0 "\
            "AND FD.ManualMoveAllowed = 1 "\
            "ORDER BY FD.FinalDiagnosisName" % (post)

    print SQL
    pds = system.db.runQuery(SQL, db)
    rootContainer.data = pds

def okAction(rootContainer):
    print "In %s.okAction()" % (__name__)
    
    component = rootContainer.getComponent("List")
    row = component.selectedIndex
    ds = component.data
    
    finalDiagnosisName = ds.getValueAt(row, "FinalDiagnosisName")
    finalDiagnosisUUID = ds.getValueAt(row, "FinalDiagnosisUUID")
    diagramUUID = ds.getValueAt(row, "DiagramUUID")
    finalDiagnosisId = ds.getValueAt(row, "FinalDiagnosisId")
    
    params = {"finalDiagnosisId": finalDiagnosisId, "finalDiagnosisName": finalDiagnosisName, "finalDiagnosisUUID": finalDiagnosisUUID, "diagramUUID": diagramUUID}
    window = system.nav.openWindow("DiagToolkit/Manual Move Entry", params)
    system.nav.centerWindow(window)