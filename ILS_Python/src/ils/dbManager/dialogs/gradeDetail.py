'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Grade Detail" dialog
'''

import system, time
from ils.dbManager.ui import populateRecipeFamilyDropdown, populateGradeForFamilyDropdown, populateVersionForGradeDropdown
from ils.common.util import getRootContainer
from ils.dbManager.sql import idForFamily
from ils.dbManager.userdefaults import get as getUserDefaults
from ils.common.error import notifyError

def internalFrameOpened(rootContainer):
    print "In %s.InternalFrameOpened()" % (__name__)
    
    dropdown = rootContainer.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown, includeAll=False)
    dropdown.setSelectedStringValue(getUserDefaults("FAMILY"))
            
    dropdown = rootContainer.getComponent("GradeDropdown")
    populateGradeForFamilyDropdown(dropdown)
    dropdown.setSelectedStringValue(getUserDefaults("GRADE"))
            
    dropdown = rootContainer.getComponent("VersionDropdown")
    populateVersionForGradeDropdown(dropdown)
    dropdown.setSelectedStringValue(str(getUserDefaults("VERSION")))
    
    activeCheckbox = rootContainer.getComponent("ActiveOnlyCheckBox")
    activeCheckbox.selected = getUserDefaults("ACTIVE")
    
    requery(rootContainer)

def internalFrameActivated(rootContainer):
    print "In %s.InternalFrameActivated()" % (__name__)
    requery(rootContainer)
    
    def work(rootContainer=rootContainer):
        time.sleep(2)
        print "Setting initialized to True"
        rootContainer.initialized = True
        
    system.util.invokeAsynchronous(work)

# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(component):
    print "In %s.requery()" % (__name__)
    container = getRootContainer(component)
    table = container.getComponent("DatabaseTable")
    
    family = getUserDefaults("FAMILY")
    grade = getUserDefaults("GRADE")
    vers = getUserDefaults("VERSION")
    
#    if family == "<Family>" or grade == "<Grade>" or vers == "Version":
#        print "bailing from update because they have not selected a family, grade, and version"
#        return
    
    where = ""
    if family not in ["ALL", "<Unit>", "<Family>"]:
        where = " AND F.RecipeFamilyName = '"+family+"'"

    if grade not in ["ALL", "<Grade>"]:
        where = where+ " AND GM.Grade = '"+grade+"'"
            
    if vers not in [ "ALL", "<Version>"]:
        where = where+ " AND GM.Version = "+ str(vers)
        
    active = getUserDefaults("ACTIVE")
    if active:
        where = where+ " AND GM.Active = 1"    
    
    SQL = "SELECT F.RecipeFamilyId,F.RecipeFamilyName,GD.Grade,VD.ValueId,VD.PresentationOrder, "\
        " GD.Version,GM.Active,VD.Description,GD.RecommendedValue,GD.LowLimit,GD.HighLimit, VT.ValueType "\
        " FROM RtRecipeFamily F, RtGradeMaster GM, RtGradeDetail GD, RtValueDefinition VD, RtValueType VT "\
        " WHERE GD.RecipeFamilyId = F.RecipeFamilyId "\
        " AND GM.RecipeFamilyId = F.RecipeFamilyId "\
        " AND VD.RecipeFamilyId = F.RecipeFamilyId "\
        " AND GD.Grade = GM.Grade "\
        " AND GD.Version = GM.Version "\
        " AND GD.ValueId = VD.ValueId %s "\
        " AND VD.ValueTypeId = VT.ValueTypeId "\
        " ORDER BY F.RecipeFamilyName,GM.Grade,VD.PresentationOrder,GM.Version" % (where)
    print SQL

    pds = system.db.runQuery(SQL)
    table.data = pds
    print "...fetched %d rows" % (len(pds))

    


# Called from the client startup script: View menu
# Note: No attempt is made at this point to reconcile with any tab strip
def showWindow():
    window = "DBManager/GradeDetail"
    system.nav.openWindowInstance(window)
    system.nav.centerWindow(window)

# Update database for a cell edit. We only allow edits of parameter value or 
# limits.
def update(table,row,colname,value):
    print "In %s.update() - row:%d, col: %s, value: <%s> ..." % (row, colname, str(value))

    ds = table.data
    #column is LowerLimit or UpperLimit. Others are not editable.
    familyid = ds.getValueAt(row,"RecipeFamilyId")
    gradeid = ds.getValueAt(row,"Grade")
    version = ds.getValueAt(row,"Version")
    vid = ds.getValueAt(row,"ValueId")
    valueType = ds.getValueAt(row,"ValueType")
    try:
        if value == "":
            msg = "Database Error."
            SQL = "UPDATE RtGradeDetail SET %s = NULL " \
                " WHERE RecipeFamilyId=%i and Grade='%s' and Version = %d and ValueId = %d" \
                % (colname, familyid, str(gradeid), version, vid)
        else:
            if valueType == "Float":
                msg = "Value must be a floating point number."
                value = float(value)
            elif valueType == "Integer":
                msg = "Value must be a floating point number."
                value = int(value)
    
            msg = "Database Error."
            SQL = "UPDATE RtGradeDetail SET %s = '%s' " \
                " WHERE RecipeFamilyId=%d and Grade='%s' and Version = %d and ValueId = %d" \
                % (colname, str(value), familyid, str(gradeid), version, vid)
        print "SQL: ", SQL
        rows = system.db.runUpdateQuery(SQL)
        print "Updated %d rows" % (rows)
    except:
        system.gui.warningBox(msg)
        ds = system.dataset.setValue(ds,row,colname,'')
        table.data = ds