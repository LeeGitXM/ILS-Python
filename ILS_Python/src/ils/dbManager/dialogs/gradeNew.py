'''
Created on Mar 21, 2017

@author: phass
'''

import system
from ils.common.error import notifyError
log = system.util.getLogger("com.ils.recipe.ui")

def internalFrameOpened(rootContainer):
    log.trace("InternalFrameOpened")

def internalFrameActivated(rootContainer):
    log.trace("InternalFrameActivated")

def createGrade(rootContainer):
    print "In createGrade..."
    newGrade = rootContainer.getComponent("GradeTextField").text
    oldGrade = rootContainer.oldGrade
    oldVersion = rootContainer.oldVersion
    familyName = rootContainer.familyName
    familyId = rootContainer.familyId
    
    tx = system.db.beginTransaction()
    
    try:
    
        if oldGrade == None:
            print "In createFirstGrade..."
            newGrade = rootContainer.getComponent("GradeTextField").text
            familyName = rootContainer.familyName
            familyId = rootContainer.familyId
                    
            print "Creating first grade: %s for family: %s/%s" % (newGrade, familyName, str(familyId))
    
            # Insert row into GradeMaster
            SQL="INSERT INTO RtGradeMaster(RecipeFamilyId,Grade,Version,Active) VALUES("+str(familyId)+",'"+newGrade+"',0,0)"
            system.db.runUpdateQuery(SQL,tx=tx)
    
            # Insert rows into GradeDetail - The new grade will have an initial version of 0 
            SQL="INSERT INTO RtGradeDetail(RecipeFamilyId,Grade,ValueId,Version) " \
                        "SELECT %s, '%s', ValueId, 0 FROM RtValueDefinition " \
                        " WHERE RecipeFamilyID=%s " % (str(familyId), newGrade, str(familyId))
            log.trace(SQL)
            rows=system.db.runUpdateQuery(SQL, tx=tx)
            log.info("Inserted %i rows into RtGradeDetail" % (rows))
                
            txt = "Created grade: %s for family %s!\nThe new grade will not be active, make sure to uncheck the 'Active' checkbox to see the grade." % (str(newGrade), str(familyName))
            system.gui.messageBox(txt)
        
        else:
            print "Creating grade: %s from grade %s for family: %s/%s" % (newGrade, oldGrade, familyName, str(familyId))
                
            # Check for duplicate
            SQL = "SELECT COUNT(*) FROM RtGradeMaster WHERE Grade='"+str(newGrade)+"' AND RecipeFamilyId="+str(familyId)
            count = system.db.runScalarQuery(SQL,tx=tx)
            if count==0:
                # Insert row into GradeMaster
                SQL="INSERT INTO RtGradeMaster(RecipeFamilyId,Grade,Version,Active) VALUES("+str(familyId)+",'"+newGrade+"',0,0)"
                system.db.runUpdateQuery(SQL,tx=tx)
                
                # Insert rows into GradeDetail - The new grade will have an initial version of 0 
                SQL="INSERT INTO RtGradeDetail(RecipeFamilyId,Grade,ValueId,Version,RecommendedValue,LowLimit,HighLimit) " \
                    "SELECT %s, '%s', ValueId, 0, RecommendedValue,LowLimit,HighLimit FROM RtGradeDetail " \
                    " WHERE RecipeFamilyID=%s and Grade='%s' and version=%i" % (str(familyId), newGrade, str(familyId), oldGrade, oldVersion)
                log.trace(SQL)
                rows=system.db.runUpdateQuery(SQL, tx=tx)
                log.trace("Inserted %i rows into RtGradeDetail" % (rows))
        
                txt = "Created grade: %s for family %s!\nThe new grade will not be active, make sure to uncheck the 'Active Only?' checkbox to see the grade." % (str(newGrade), str(familyName))
                system.gui.messageBox(txt)
            else:
                msg = "Grade " + newGrade + " exists. Create attempt ignored."
                system.gui.warningBox(msg)   
    except:
        system.db.rollbackTransaction(tx)
        notifyError(__name__, "Error creating a new grade - rolling back transactions")

    else:
        print "Committing!"
        system.db.commitTransaction(tx)

    system.db.closeTransaction(tx)