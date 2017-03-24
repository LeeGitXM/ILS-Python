'''
Created on Mar 21, 2017

@author: phass

This module contains a collection of scripts used
for conversion of legacy MS Access database tables
into the relational Recipe database

The source database has already been imported from MS*Access into MS*SQLServer.
There must be a valid Ignition database connection to the source database.
The data will be imported into the default database, so the traget database name is not needed on any insert statements.
The RecipeToolkit database schema must already exist!

'''

# Copyright 2014. ILS Automation. All rights reserved.

import system
from ils.dbManager.sql import getColumnNames, getTableNames

#from java.lang   import System

def internalFrameOpened(event):
#    print "recipe.convert.internalFrameOpened()"
    rootContainer = event.source.rootContainer
    
    ds =  system.db.getConnections()
    pds = system.dataset.toPyDataSet(ds)
    
    # Create a new dataset using only the Name column
    header = ["Connection Name"]
    names = [[""]]
        
    for row in pds:
        name = row['Name']
        n1 = []
        n1.append(name)
        names.append(n1)
    
    ds = system.dataset.toDataSet(['names'],names)
    
    dropdown = rootContainer.getComponent('SourceDropdown')
    dropdown.data = ds
    dropdown.selectedValue = -1
    
    dropdown = rootContainer.getComponent('SQCDropdown')
    dropdown.data = ds
    dropdown.selectedValue = -1
    
def internalFrameActivated(event):
#    print "recipe.convert.internalFrameActivated()"
    pass

# Read the database and write a create script to the specified path.
# The database is a direct import of a legacy MSAccess database.
# The ouput file creates and populates a schema for the Recipe Toolkit.
# The "sqlserver" attribute is a flag which determines if the output
# is compatible with SQL*Server.
def convert(recipedb,sqcdb):
    if recipedb!='None':

        txId = system.db.beginTransaction()
        postId = fetchDefaultPost()
        populateWriteLocations(recipedb, txId)
        families = populateRecipeFamilyTable(recipedb, postId, txId)
        vu = populateValueDefinitionTable(recipedb,families, txId)
        populateGradeMasterTable(recipedb,families,txId)
        populateMasterModifications(recipedb,families, txId)
        populateGradeDetail(recipedb,families,vu,txId)
        populateGradeModifications(recipedb,families,vu,txId)

        # Add on the SQC tables
        if sqcdb!='None' and sqcdb!='':
            populateFlyingSwitchTable(sqcdb,txId)
            populateWatchdogTable(sqcdb,txId)
            populateGainTable(sqcdb,families,txId)
            populateSQCTable(sqcdb,families,txId)
            populateEventTable(sqcdb,families,txId)

        print "Committing transactions!"
        system.db.commitTransaction(txId)    
        system.db.closeTransaction(txId)
        
    print "Conversion complete."
    
def fetchDefaultPost():
    SQL = "select min(PostId) from TkPost"
    postId = system.db.runScalarQuery(SQL)
    return postId

#
# There is often a bogus family set up in the unit table and the necessary support tables do not exist.
# Fetching from a table that does not exist throws an error, this will catch that error and return None.
def fetchRows(SQL, database):
    try:
        pds = system.db.runQuery(SQL,database)
    except:
        pds = None
            
    return pds

#
#  ====================================================================================
#
def populateFlyingSwitchTable(database,txId):
    print "Populating RtAllowedFlyingSwitch..."
    SQL = "SELECT Current_Grade,Next_Grade FROM Allowed_Flying_Switches"
    pds = system.db.runQuery(SQL,database)
    rows = 0
    for row in pds:
        grade1 = row['Current_Grade']
        grade2 = row['Next_Grade']
        SQL = "INSERT INTO RtAllowedFlyingSwitch(CurrentGrade,NextGrade) VALUES ('"+str(grade1)+"','"+str(grade2)+"')"
        system.db.runUpdateQuery(SQL, tx=txId)
        rows = rows + 1
    print "...inserted ", rows, " records into RtAllowedFlyingSwitch, committing..."
    system.db.commitTransaction(txId)    

#
def populateGainTable(database,families,txId):
    print "Populating RtGainGrade..."
    # Insert into both the master and detail records
    rows = 0 
    for family in families.keys():
        table = family+"_Gains"
        familyId = families.get(family)
        columns = getColumnNames(database,table)
        for col in columns:
            col = col.lower()
            if col != "grade":
                pos = col.find('-gain')
                if pos>0:
                    colname = col[0:pos]
                    SQL = "INSERT INTO RtGain(RecipeFamilyId, Parameter) VALUES(%s, '%s')" % (familyId, colname.upper())
                    pid = system.db.runUpdateQuery(SQL, getKey=True, tx=txId)
                    SQL = "SELECT Grade,["+col+"] FROM "+table
                    pds = system.db.runQuery(SQL,database)
                    for row in pds:
                        if row[1]!=None and len(str(row[1]))>0:
                            SQL = "INSERT INTO RtGainGrade(ParameterId,Grade,Gain) VALUES("+str(pid)+","+str(row[0])+","+str(row[1])+")"
                            system.db.runUpdateQuery(SQL, tx=txId)
                            rows = rows + 1
    print "...inserted ", rows, " records into RtGainGrade, committing...!"
    system.db.commitTransaction(txId)    

#
def populateEventTable(database,families,txId):
    print "Populating RtEventParameters & RtEvents..."
    # Insert into both the master and detail records
    rows = 0 
    for family in families.keys():
        table = family+"_Events"
        familyId = families.get(family)
        columns = getColumnNames(database,table)
        for col in columns:
            col = col.lower()
            if col != "grade":
                colname = col
                SQL = "INSERT INTO RtEventParameter (RecipeFamilyId, Parameter) VALUES(%s, '%s')" % (str(familyId), colname.upper())
                pid = system.db.runUpdateQuery(SQL, getKey=True, tx=txId)
                SQL = "SELECT GRADE, %s FROM %s" % (col, table)
                pds = system.db.runQuery(SQL,database)
                for row in pds:
                    if row[1]!=None and len(str(row[1]))>0:
                        grade = row['GRADE']
                        value = row[1]
                        if value == "NaN":
                            SQL = "INSERT INTO RtEvent(ParameterId,Grade) VALUES (%s, '%s')" % (str(pid), str(grade))
                        else:
                            SQL = "INSERT INTO RtEvent(ParameterId,Grade,Value) VALUES (%s, '%s', %s)" % (str(pid), str(grade), str(value))
                        system.db.runUpdateQuery(SQL, tx=txId)
                        rows = rows + 1
    print "...inserted ", rows, " records into RtGainGrade, committing...!"
    system.db.commitTransaction(txId)    
        
# This is the detail table for grades
def populateGradeDetail(database,families,vu,txId):
    print "Populating RtGradeDetail..."

    # Query the Master tables for names of grade tables
    rows = 0
    for family in families.keys():
        print "   ...Family: ", family
        
        SQL = "select Unit_Master, Unit_Prefix from TYPE_UNIT_ROOT where Family_name = '%s'" % (family)
        pds = system.db.runQuery(SQL, database)
        if len(pds) == 0:
            print "** Could not find %s in TYPE_UNIT_ROOT **" % (family)
        
        record = pds[0]
        unitMaster = record["Unit_Master"]
        unitPrefix = record["Unit_Prefix"]
        
        SQL = "SELECT SUB_RECIPE FROM " + unitMaster
        
        masterpds = fetchRows(SQL,database)
        familyid = families.get(family)
        if masterpds != None:
            for masterrow in masterpds:
                sub = masterrow['SUB_RECIPE']
                table = unitPrefix + '_' + sub
                print "      ...",table
                SQL = "SELECT PRES,RECC,LOLIM,HILIM FROM "+table
                print SQL

                try:
                    pds = fetchRows(SQL,database)
                    if pds != None:
                        for row in pds:
                            pres = row['PRES']
                            recommend = row['RECC']
                            lowLimit  = row['LOLIM']
                            highLimit = row['HILIM']
                            sub = sub.lstrip("0")
                            key = str(familyid)+":"+str(pres)
                            vid = vu[key]
                            if vid==None:
                                print "populateGradeDetail.lookup failure on "+key
                            SQL = "INSERT INTO RtGradeDetail(RecipeFamilyId,Grade,ValueId,Version,RecommendedValue,LowLimit,HighLimit) "\
                                " VALUES ("+str(familyid)+",'"+sub+"',"+str(vid)+",0"
                            if recommend == None:
                                SQL=SQL+",NULL"
                            else:
                                SQL = SQL + ",'"+recommend+"'"
                            if lowLimit == None:
                                SQL=SQL+",NULL"
                            else:
                                SQL = SQL + ",'"+lowLimit+"'"
                            if highLimit == None:
                                SQL=SQL+",NULL)"
                            else:
                                SQL = SQL + ",'"+highLimit+"')"    

                            rows = rows + 1
                            system.db.runUpdateQuery(SQL, tx=txId)
                except:
                    print "Failed SQL: ", SQL
                    print "populateGradeDetail SQL failure looking for table "+table+".  The grade is defined in the MASTER table, but the grade table does not exist!"
            print "...inserted ", rows, " records into RtGradeDetail, committing...!"
            system.db.commitTransaction(txId)    
        

#
# Create the table holding the current recipes
#
def populateGradeMasterTable(database,families,txId):
    print "Populating RtGradeMaster..."
    # Query each of the unit Master tables
    
    for family in families.keys():
        rows = 0
        print "  Family: ", family
        
        # Get the name of the master table from the Type_Unit_Root table
        SQL = "select Unit_Master from TYPE_UNIT_ROOT where Family_name = '%s'" % (family)
        unitMaster = system.db.runScalarQuery(SQL, database)
        if unitMaster == None:
            print "** Could not find %s in TYPE_UNIT_ROOT **" % (family)
        
        SQL = "SELECT SUB_RECIPE FROM " + unitMaster
        pds = fetchRows(SQL,database)
        if pds != None:
            for row in pds:
                grade = row['SUB_RECIPE']
                grade = grade.lstrip("0")
                SQL = "INSERT INTO RtGradeMaster(RecipeFamilyId,Grade,Version) VALUES ("+str(families.get(family))+",'"+grade+"',0)"
                system.db.runUpdateQuery(SQL, tx=txId)
                rows = rows + 1
            print "  ...inserted %i records into RtGradeMaster for %s!" % (rows, family)
        else:
            print "  ** No Grade Master rows found for %s **" % (family)
    print "   ... committing RtGradeMaster..."
    system.db.commitTransaction(txId)


# Query the list of system tables and create a table of recipe families.
def populateWriteLocations(database, txId):
    print "Populating TkWriteLocations..."
    # Loop through the unit root table
    SQL = 'SELECT Alias, Description FROM WriteLocations'
    pds = system.db.runQuery(SQL,database)
    #project.recipe.misc.dumpDataset(pds)
    families = {}
    i=0
    for row in pds:
        alias = row['Alias']

        SQL = "select count(*) from TkWriteLocation where Alias = '%s'" % (alias)
        cnt = system.db.runScalarQuery(SQL, tx=txId)
        if cnt == 0:
            SQL = "INSERT INTO TkWriteLocation(Alias,ServerName,ScanClass)"\
                " VALUES('%s','%s','Fast')" % (alias, alias)        
            system.db.runUpdateQuery(SQL, tx=txId)    
            i=i+1
            print "   Inserted %s into TkWriteLocation" % (alias)
        else:
            print "   %s already exists in TkWriteLocation" % (alias)
    print "...inserted ", i, " records into TkWriteLocation, committing..."
    system.db.commitTransaction(txId)
    return families


# Query the list of system tables and create a table of recipe families.
def populateRecipeFamilyTable(database, postId, txId):
    print "Populating RtRecipeFamilyRoot..."
    # Loop through the unit root table
    SQL = 'SELECT Family_Name,Unit_Prefix,Unit_Prefix_Alias,Comment FROM Type_Unit_Root'
    pds = system.db.runQuery(SQL,database)
    #project.recipe.misc.dumpDataset(pds)
    families = {}
    i=0
    for row in pds:
        family = row['Family_Name']
        unit   = row['Unit_Prefix']
        if unit==None:
            unit=family.upper()
        alias  = row['Unit_Prefix_Alias']
        if alias==None:
            alias=family.title()
        comment= row['Comment']
        if comment==None:
            comment = ''
        SQL = "INSERT INTO RtRecipeFamily(RecipeFamilyName,PostId,RecipeUnitPrefix,RecipeNameAlias,Comment)"\
            " VALUES('%s',%s,'%s','%s','%s')" % (family,str(postId), unit, alias, comment)        
        index = system.db.runUpdateQuery(SQL, getKey=True, tx=txId)    
        families[family] = index
        index = index+1
        i=i+1
    print families
    print "...inserted ", i, " records into RtRecipeFamily, committing..."
    system.db.commitTransaction(txId)
    return families

# Populate the two SQC tables at the same time
def populateSQCTable(database,families,txId):
    print "Populating RtSQCParameter..."
    # Populate from the various limits tables. 
    names = getTableNames(database)
    for table in names:
        if table.lower().find("limits") >= 0:
            for family in families.keys():
                if table.lower().find(family[0:3].lower()) >= 0:
                    rows = 0
                    columns = getColumnNames(database,table)
                    for col in columns:
                        index = col.find("_LL")
                        if index<0:
                            index = col.find("_LO")
                        if index>0:
                            root = col[0:index]
                            SQL = "INSERT INTO RtSQCParameter(RecipeFamilyId,Parameter) VALUES("+str(families.get(family))+",'"+root+"')"
                            pid = system.db.runUpdateQuery(SQL, getKey=True, tx=txId)
                            
                            # Look for the low limit, assume a corresponding high limit exists
                            usuffix = "_ULIMIT"
                            lsuffix = "_LLIMIT"
                            index = col.find(lsuffix)
                            if index<0:
                                usuffix = "_HILIM"
                                lsuffix = "_LOLIM"
                                index = col.find(lsuffix)
                            if index<0:
                                usuffix = "_HL"
                                lsuffix = "_LL"
                                index = col.find(lsuffix)
                            if index>0:
                                root = col[0:index]
                                SQL = "SELECT grade,"+root+lsuffix+","+root+usuffix+" FROM "+table
                                try:
                                    pds = system.db.runQuery(SQL,database)
                                    for row in pds:
                                        grade = row['grade']
                                        ll    = row[root+lsuffix]
                                        if str(ll)=='NaN':
                                            ll = None
                                        ul    = row[root+usuffix]
                                        if str(ul)=='NaN':
                                            ul = None
                                        if grade != None:
                                            SQL = "INSERT INTO RtSQCLimit(ParameterId,Grade,UpperLimit,LowerLimit) VALUES(?,?,?,?)"
                                            rows = rows + 1
                                            system.db.runPrepUpdate(SQL,[pid,grade,ul,ll],tx=txId)
                                        else:
                                            print "Create SQCLimit: No grade in master for "+family+":"+str(grade)
                                except:
                                    print "Create SQCLimit: No matching lower limit in SQC table for "+family+":"+str(grade)+":"+root
                
                    print "...inserted ", rows, " SQC limit records for ", family
    print "   ...committing SQC Limits..."
    system.db.commitTransaction(txId)            
    
#  Each row describes a kind of setting that is part of a recipe step (sub-recipe).
def createValueDefinitionInsert(familyid,order,row,txId):
    
    SQL = "INSERT INTO RtValueDefinition(RecipeFamilyId,PresentationOrder,Description,StoreTag,CompareTag,ChangeLevel,ModeAttribute,ModeValue,WriteLocationId) VALUES("
    SQL = SQL+str(familyid)+","+str(order)
 
    if row["DSCR"]==None:
        SQL = SQL+',NULL'
    else:
        SQL = SQL+",'"+row["DSCR"]+"'"
        
    if row["STAG"]==None:
        SQL = SQL+',NULL'
    else:
        SQL = SQL+",'"+row["STAG"]+"'"
        
    if row["CTAG"]==None:
        SQL = SQL+',NULL'
    else:
        SQL = SQL+",'"+row["CTAG"]+"'"
        
    if row["CHG_LEV"]==None:
        SQL = SQL+',NULL'
    else:
        SQL = SQL+",'"+row["CHG_LEV"]+"'"
        
    if row["MODATTR"]==None:
        SQL = SQL+',NULL'
    else:
        SQL = SQL+",'"+row["MODATTR"]+"'"
        
    if row["MODATTR_VAL"]==None:
        SQL = SQL+',NULL'
    else:
        SQL = SQL+",'"+row["MODATTR_VAL"]+"'"

    if row["WRITE_LOC"]==None:
        SQL = SQL+",NULL)"
    elif row["WRITE_LOC"]=='LocalG2':
        writeLocationId=lookupWriteLocation('LOCAL',txId)
        SQL = SQL+","+str(writeLocationId)+")"
    else:
        writeLocationId=lookupWriteLocation(row["WRITE_LOC"],txId)
        SQL = SQL+","+str(writeLocationId)+")"

    return SQL

def lookupWriteLocation(alias, txId):
    SQL = "select writeLocationId from TkWriteLocation where Alias = '%s'" % (alias)
    writeLocationId = system.db.runScalarQuery(SQL, tx=txId)
    if writeLocationId == None:
        print "Unable to find the alias <%s> in TkWriteLocation" % (alias)
    return writeLocationId
    
# No editor required for this table. We simply insert the current datetime    
def populateWatchdogTable(database,txId):
    print "Populating RtWatchdog..."
    SQL = "SELECT index_key,time_stamp FROM Watchdog"
    pds = system.db.runQuery(SQL,database)
    rows = 0
    for row in pds:
        key = row['index_key']
        ts  = row['time_stamp']
        timecol = "current_timestamp"
        SQL = "INSERT INTO RtWatchdog(Observation,Timestamp) VALUES ("+str(key)+","+timecol+")"
        system.db.runUpdateQuery(SQL, tx=txId)
        rows = rows + 1
    print "...inserted ", rows, " records into RtWatchdog, committing..."
    system.db.commitTransaction(txId)

# These are the grade details corresponding to proposed modifications
# Simply insert them into the Grade detail table with version 1
def populateGradeModifications(database,families,vu,txId):
    print "Inserting Grade modifications..."
    # Query the Master tables for names of grades tables
    for family in families:
        rows = 0
        print "   ", family, "..."
        SQL = "SELECT SUB_RECIPE FROM "+family+"_Master_MOD"
        masterpds = fetchRows(SQL,database)
        if masterpds != None:
            for masterrow in masterpds:
                sub = masterrow['SUB_RECIPE']
                table = family+'_'+sub+"_MOD"
            
                SQL = "SELECT PRES,RECC,LOLIM,HILIM FROM "+table
                try:
                    pds = system.db.runQuery(SQL,database)
                    for row in pds:
                        pres      = row['PRES']
                        recommend = row['RECC']
                        lowLimit  = row['LOLIM']
                        highLimit = row['HILIM']
                        sub = sub.ltrim("0")
                        vid = vu[key]
                        if vid==NULL:
                            print "createGradeTable.lookup failure on "+key
                        SQL = "INSERT INTO RtGradeDetail(RecipeFamilyId,Grade,ValueId,Version,RecommendedValue,LowLimit,HighLimit) VALUES ("+str(families.get(family))+",'"+sub+"',"+str(vid)+",1"
                        if recommend == None or str(recommend).lower()=="nan":
                            SQL=SQL+",NULL"
                        else:
                            SQL = SQL + ",'"+recommend+"'"
                        if lowLimit == None or str(lowLimit).lower()=="nan":
                            SQL=SQL+",NULL"
                        else:
                            SQL = SQL + ",'"+lowLimit+"'"
                        if highLimit == None or str(highLimit).lower()=="nan":
                            SQL=SQL+",NULL)"
                        else:
                            SQL = SQL + ",'"+highLimit+"')"    
                        system.db.runUpdateQuery(SQL, tx=txId)
                        rows = rows + 1
                # Ignore missing tables
                except:
                    pass
        print "      ...inserted ", rows, " grade modification records into RtGradeDetail, committing..."
        system.db.commitTransaction(txId)
                
# Append the MasterTable with possible modifications
# Create a table that holds the current version
def populateMasterModifications(database,families,txId):
    # Query each of the unit Master Modification tables
    # The current design allows only one modification per grade.
    print "Inserting Master Modifications in RtGradeMaster..."
    rows = 0
    for family in families.keys():
        
        # Get the name of the master table from the Type_Unit_Root table
        SQL = "select Unit_Master from TYPE_UNIT_ROOT where Family_name = '%s'" % (family)
        unitMaster = system.db.runScalarQuery(SQL, database)
        if unitMaster == None:
            print "** Could not find %s in TYPE_UNIT_ROOT **" % (family)
            
        SQL = "SELECT SUB_RECIPE FROM " + unitMaster+"_MOD"
        pds = fetchRows(SQL,database)
        if pds != None:
            for row in pds:
                grade = row['SUB_RECIPE']
                grade = grade.lstrip("0")
                SQL = "INSERT INTO RtGradeMaster(RecipeFamilyId,Grade,Version,Timestamp,Active) VALUES ("+str(families.get(family))+",'"+grade+"',1,current_timestamp,0)"
                system.db.runUpdateQuery(SQL, tx=txId)
                rows = rows + 1
    print "   ...inserted ", rows, " master modification records into RtGradeMaster, committing..."
    system.db.commitTransaction(txId)
    
    # Update the GradeMaster table setting the active version as the max
    print "Setting the RtGradeMaster active flag..."
    SQL = "UPDATE RtGradeMaster SET Active = 1 WHERE Version =   "\
        "(Select Max(Version) FROM RtGradeMaster GM2 WHERE "\
        " RtGradeMaster.RecipeFamilyId=GM2.RecipeFamilyId AND RtGradeMaster.Grade=GM2.Grade)"
    system.db.runUpdateQuery(SQL, tx=txId)
    system.db.commitTransaction(txId)
    print "   ...done!"
            
# Query the list of system tables and create a table of processing units.
# Populate the table
def populateValueDefinitionTable(database,families,txId):
    import system
    
    print "Populating RtValueDefinition..."
    # Loop through the full definition tables
    # Insert rows into the combined table
    values = {}
    rows = 0
    for family in families.keys():
        print "Loading ", family
        
        # Get the name of the full def table from the Type_Unit_Root table
        SQL = "select Unit_Def from TYPE_UNIT_ROOT where Family_name = '%s'" % (family)
        unitDef = system.db.runScalarQuery(SQL, database)
        if unitDef == None:
            print "** Could not find %s in TYPE_UNIT_ROOT **" % (family)
        
        SQL = "SELECT PRES, DSCR, STAG, CTAG, CHG_LEV, MODATTR, MODATTR_VAL, WRITE_LOC FROM " + unitDef
        pds = fetchRows(SQL,database)
        order = 0
        familyid = families.get(family)
        if pds != None:
            for row in pds:
                key = str(familyid)+":"+str(row[0])
                SQL = createValueDefinitionInsert(familyid,order,row, txId)
                pk = system.db.runUpdateQuery(SQL, getKey=True, tx=txId)
                values[key] = pk
                order = order+1
                rows = rows + 1
        else:
            print " No value definition rows found for ", family  
    print "...inserted ", rows, " records into RtValueDefinition, committing..."
    system.db.commitTransaction(txId)
    return values

# Modify the timestamp into a form that SQL*Server recognizes
def scrubDatetime(dt):
    # Strip off the day of week
    index = dt.find(' ')
    ts = ""
    if( index>0 ):
        dt = dt[index+1:]
    # Find year
    year = '2014'
    index = dt.rfind(' ')
    if index>0:
        year = dt[index+1:]
        dt = dt[0:index]
    # Strip off Timezone
    index = dt.rfind(' ')
    if index>0:
        dt = dt[0:index]
    # Find month
    month = "Jan"
    index = dt.find(' ')
    if index>0:
        mon = dt[0:index]
        dt = dt[index+1:]
    # Find day of month
    dom = "01"
    index = dt.find(' ')
    if index>0:
        dom = dt[0:index]
        dt = dt[index+1:]
    # Put it all to gether
    ts = month+" "+dom+" "+year+" "+dt+".000"
    return ts

# Called from the client startup script: Tool menu
def showWindow():
    window = "Migration/MakeRecipeDatabase"
    system.nav.openWindow(window)
    system.nav.centerWindow(window)