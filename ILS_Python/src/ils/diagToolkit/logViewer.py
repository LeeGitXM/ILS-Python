'''
Created on Jul 26, 2016

@author: ils
'''

import system

def update(rootContainer):
    print "Updating..."
    
    table = rootContainer.getComponent('Power Table')
    
    startDate = rootContainer.getComponent('Date Range').startDate
    endDate = rootContainer.getComponent('Date Range').endDate

    SQL = "select LogId, Timestamp, ApplicationName, FamilyName, FamilyPriority, FinalDiagnosisName, FinalDiagnosisPriority, State, Active "\
        " from DtFinalDiagnosisLogView " \
        " where Timestamp > ? and Timestamp < ?" \
        " order by LogId DESC"


#    SQL = "select convert(varchar(50), Timestamp, 9), ApplicationName, FamilyName, FamilyPriority, FinalDiagnosisName, FinalDiagnosisPriority, Active "\
#        " from DtFinalDiagnosisLogView " \
#        " where Timestamp > ? and Timestamp < ?" \
#        " order by Timestamp DESC"

    print SQL
    
    pds = system.db.runPrepQuery(SQL, [startDate, endDate])
    table.data = pds