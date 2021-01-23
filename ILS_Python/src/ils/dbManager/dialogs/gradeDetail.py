'''
Created on Mar 21, 2017

@author: phass

Scripts in support of the "Grade Detail" dialog
'''
import system
from ils.dbManager.ui import populateRecipeFamilyDropdown, populateGradeForFamilyDropdown, populateVersionForGradeDropdown
from ils.dbManager.userdefaults import get as getUserDefaults

log = system.util.getLogger("com.ils.recipe.ui")

def internalFrameOpened(rootContainer):
    print "In %s.InternalFrameOpened()" % (__name__)


def internalFrameActivated(rootContainer):
    print "In %s.InternalFrameActivated()" % (__name__)
    
    dropdown = rootContainer.getComponent("FamilyDropdown")
    populateRecipeFamilyDropdown(dropdown, includeAll=True)

    dropdown = rootContainer.getComponent("GradeDropdown")
    populateGradeForFamilyDropdown(dropdown)
          
    dropdown = rootContainer.getComponent("VersionDropdown")
    populateVersionForGradeDropdown(dropdown)
    
    requery(rootContainer)


# Re-query the database and update the screen accordingly.
# If we get an exception, then rollback the transaction.
def requery(rootContainer):
    print "In %s.requery()" % (__name__)
    table = rootContainer.getComponent("DatabaseTable")
    print table
    
    family = getUserDefaults("FAMILY")
    grade = getUserDefaults("GRADE")
    vers = getUserDefaults("VERSION")
    
    andWhere = ""
    if family not in ["ALL", "<Unit>", "<Family>"]:
        andWhere = " AND F.RecipeFamilyName = '"+family+"'"

    if grade not in ["ALL", "<Grade>"]:
        andWhere = andWhere+ " AND GM.Grade = '"+grade+"'"
            
    if vers not in [ "ALL", "<Version>"]:
        andWhere = andWhere+ " AND GM.Version = "+ str(vers)
        
    active = getUserDefaults("ACTIVE")
    if active:
        andWhere = andWhere+ " AND GM.Active = 1"    
    
    SQL = "SELECT F.RecipeFamilyId, F.RecipeFamilyName, GD.Grade, VD.ValueId, VD.PresentationOrder, "\
        " GD.Version, GM.Active, VD.Description, GD.RecommendedValue, GD.LowLimit, GD.HighLimit, GD.RowActive, VT.ValueType "\
        " FROM RtRecipeFamily F, RtGradeMaster GM, RtGradeDetail GD, RtValueDefinition VD, RtValueType VT "\
        " WHERE GD.RecipeFamilyId = F.RecipeFamilyId "\
        " AND GM.RecipeFamilyId = F.RecipeFamilyId "\
        " AND VD.RecipeFamilyId = F.RecipeFamilyId "\
        " AND GD.Grade = GM.Grade "\
        " AND GD.Version = GM.Version "\
        " AND GD.ValueId = VD.ValueId "\
        " AND VD.ValueTypeId = VT.ValueTypeId  %s "\
        " ORDER BY F.RecipeFamilyName,GM.Grade,VD.PresentationOrder,GM.Version" % (andWhere)
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
    print "In %s.update() - row:%d, col: %s, value: <%s> ..." % (__name__, row, colname, str(value))

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
            if colname == "RowActive":
                if value:
                    val = 1
                else:
                    val = 0
                
                SQL = "UPDATE RtGradeDetail SET RowActive = %d " \
                    " WHERE RecipeFamilyId=%d and Grade='%s' and Version = %d and ValueId = %d" \
                    % (val, familyid, str(gradeid), version, vid)
                print ""
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


def exportCallback(event):
    rootContainer = event.source.parent
    andWhere = ""
    
    entireTable = system.gui.confirm("<HTML>You can export the entire table or just the selected family, grade,  and active flag.  <br>Would you like to export the <b>entire</b> table?")
    if not(entireTable):
        family = getUserDefaults("FAMILY")
        if family not in ["ALL", "", "<Family>"]:
            andWhere = " AND F.RecipeFamilyName = '"+family+"'"
            
        grade = getUserDefaults("GRADE")
        if grade not in ["ALL", "", "<Grade>"]:
            andWhere = andWhere+ " AND GM.Grade = '"+grade+"'"    

        active = rootContainer.getComponent("ActiveOnlyCheckBox")
        if active.selected:
            andWhere = andWhere + " AND Active=1"
            
    SQL = "SELECT F.RecipeFamilyId,F.RecipeFamilyName,GD.Grade,VD.ValueId,VD.PresentationOrder, "\
        " GD.Version,GM.Active,VD.Description,GD.RecommendedValue,GD.LowLimit,GD.HighLimit, VT.ValueType "\
        " FROM RtRecipeFamily F, RtGradeMaster GM, RtGradeDetail GD, RtValueDefinition VD, RtValueType VT "\
        " WHERE GD.RecipeFamilyId = F.RecipeFamilyId "\
        " AND GM.RecipeFamilyId = F.RecipeFamilyId "\
        " AND VD.RecipeFamilyId = F.RecipeFamilyId "\
        " AND GD.Grade = GM.Grade "\
        " AND GD.Version = GM.Version "\
        " AND GD.ValueId = VD.ValueId "\
        " AND VD.ValueTypeId = VT.ValueTypeId  %s "\
        " ORDER BY F.RecipeFamilyName,GM.Grade,VD.PresentationOrder,GM.Version" % (andWhere)
    
    log.trace(SQL)

    pds = system.db.runQuery(SQL)
    csv = system.dataset.toCSV(pds)
    filePath = system.file.saveFile("GradeDetail.csv", "csv", "Comma Separated Values")
    if filePath:
        system.file.writeFile(filePath, csv)
