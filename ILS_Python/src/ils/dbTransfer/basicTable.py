'''
Created on Aug 21, 2020

@author: phass
'''

import system
from ils.dbTransfer.constants import STRING, FLOAT, INTEGER, BOOLEAN, LOOKUP, LOOKUP_FOLDER, LOOKUP_WITH_TWO_KEYS
from ils.dbTransfer.common import getLookupId, getLookupIdWithTwoKeys
from ils.common.util import clearDataset, escapeSqlQuotes

class BasicTable():
    log = None
    columnsToUpdate = None
    tableName = None
    tableStructure = None


    def __init__(self, tableStructure):
        ''' Set any default properties.  For this abstract class there aren't many (yet). '''
        from ils.log import getLogger
        self.log = getLogger(__name__)
        self.log.tracef("Initializing a %s", __name__)
        self.tableStructure = tableStructure
        
        self.columnsToUpdate = tableStructure.get("columnsToCompareAndUpdate", None)
        if self.columnsToUpdate == None:
            system.gui.errorBox("Unknown columns to update!")
            
        self.primaryKey = self.tableStructure.get("primaryKey", None)
        if self.primaryKey == None:
            system.gui.errorBox("Unknown primary Key!")
            return
        
        self.tableName = tableStructure.get("table", None)
    
    
    def insert(self, extraSourceRows, dsSource, dbDestination):
        self.log.tracef("In %s.insert()...", __name__)
        for row in extraSourceRows:
            columnNames = []
            columnValues = []
            for columnDict in self.columnsToUpdate:
                columnName = columnDict.get("columnName", None)
                insert = columnDict.get("insert", True)
                if not(insert):
                    self.log.tracef("skipping column: %s because it is not marked to insert", columnName)
                else:
                    dataType = columnDict.get("dataType", None)
                    self.log.tracef("   ...columnName: %s, dataType: %s", columnName, dataType)
                    if columnName == None or dataType == None:
                        system.gui.errorBox("Invalid columnsToUpdate structure: %s" % (str(columnDict)))
                        return
                    
                    self.log.tracef("    Column: %s, Data Type: %s",  columnName, dataType)
                    
                    sourceValue = dsSource.getValueAt(row, columnName)
                    
                    if sourceValue in [None]:
                        self.log.tracef("        Skipping the insert of a NULL value into a column that hopefully allows NULL values...")
                    else:
                        if dataType == STRING:
                            columnNames.append(columnName)
                            if sourceValue == None:
                                columnValues.append("NULL")
                            else:
                                sourceValue = escapeSqlQuotes(sourceValue)
                                columnValues.append("'%s'" % (sourceValue))
                        
                        elif dataType in [FLOAT, INTEGER]:
                            columnNames.append(columnName)
                            if sourceValue == None:
                                columnValues.append("NULL")
                            else:
                                columnValues.append("%s" % (str(sourceValue)))
                        
                        elif dataType == BOOLEAN:
                            columnNames.append(columnName)
                            if sourceValue == None:
                                columnValues.append("NULL")
                            elif sourceValue == True:
                                columnValues.append("1")
                            else:
                                columnValues.append("0")
                        
                        elif dataType == LOOKUP_WITH_TWO_KEYS:
                            self.log.tracef("Looking for %s, a %s lookup with two keys...", sourceValue, columnName)
                            
                            lookupId, idColumnName = getLookupIdWithTwoKeys(columnName, dsSource, row, dbDestination)
                            if lookupId == None:
                                system.gui.errorBox("Unable to find %s, a %s, in %s" % (sourceValue, columnName, dbDestination))
                                return
                            columnNames.append(idColumnName)
                            columnValues.append("%s" % (str(lookupId)))
                            
                            # If we are inserting recipe data, and there is a folder, we need to know the step id in the destination system.  It will save us some work if we save it.
                            stepId = lookupId
                            
                        elif dataType == LOOKUP:
                            self.log.tracef("   ...looking for %s, a %s lookup...", sourceValue, columnName)
                            
                            lookupId, idColumnName = getLookupId(columnName, sourceValue, dbDestination)
                            if lookupId == None:
                                system.gui.errorBox("Unable to find %s, a %s, in %s" % (sourceValue, columnName, dbDestination))
                                return
                            columnNames.append(idColumnName)
                            columnValues.append("%s" % (str(lookupId)))
                            
                        else:
                            system.gui.errorBox("Unsupported column datatype: %s" % (dataType))
                            return 
                    
            ''' Now put together an insert statement '''
            SQL = "INSERT into %s (%s) values (%s)" % (self.tableName, ",".join(columnNames), ",".join(columnValues))
            self.log.tracef("SQL: %s", SQL)
            system.db.runUpdateQuery(SQL, database=dbDestination)


    def update(self, numSourceRows, dsSource, dbSource, dsDestination, dbDestination):
        columnsToUpdate = self.tableStructure.get("columnsToCompareAndUpdate", None)

        for sourceRow in range(numSourceRows):
            destinationRow = sourceRow
            dataIsTheSame = True
            columnValues = []
            
            for columnDict in columnsToUpdate:
                columnName = columnDict.get("columnName", None)
                dataType = columnDict.get("dataType", None)
                if columnName == None or dataType == None:
                    system.gui.errorBox("Invalid columnsToUpdate structure: %s" % (str(columnDict)))
                    return
                
                self.log.tracef("Row: %d, Column: %s, Data Type: %s",  sourceRow, columnName, dataType)
                
                sourceValue = dsSource.getValueAt(sourceRow, columnName)
                destinationValue = dsDestination.getValueAt(destinationRow, columnName)
                
                self.log.tracef("   comparing %s to %s...", str(sourceValue), str(destinationValue))
                if sourceValue <> destinationValue:
                    dataIsTheSame = False
                    self.log.tracef("  *** Found a mismatch ***")
                    if dataType == STRING:
                        if sourceValue == None:
                            columnValues.append("%s = NULL" % (columnName))
                        else:
                            sourceValue = escapeSqlQuotes(sourceValue)
                            columnValues.append("%s = '%s'" % (columnName, sourceValue))
                    elif dataType in [FLOAT, INTEGER]:
                        columnValues.append("%s = %s" % (columnName, str(sourceValue)))
                    elif dataType == BOOLEAN:
                        if sourceValue == None:
                            columnValues.append("%s = NULL" % (columnName))
                        elif sourceValue == True:
                            columnValues.append("%s = 1" % (columnName))
                        else:
                            columnValues.append("%s = 0" % (columnName))
                    elif dataType == LOOKUP:
                        lookupId, idColumnName = getLookupId(columnName, sourceValue, dbDestination)
                        if lookupId == None:
                            system.gui.errorBox("Unable to find %s, a %s, in %s" % (sourceValue, columnName, dbDestination))
                            return
                        columnValues.append("%s = '%s'" % (idColumnName, lookupId))
                    else:
                        system.gui.errorBox("Unsupported column datatype: %s" % (dataType))
                        return 
        
                if not(dataIsTheSame):
                    primaryKeyValue = dsDestination.getValueAt(destinationRow, self.primaryKey)
                    vals = ",".join(columnValues)
                    SQL = "update %s set %s where %s = %d" % (self.tableName, vals, self.primaryKey, primaryKeyValue)
                    system.db.runUpdateQuery(SQL, database=dbDestination)
        
        
    def delete(self, ds, selectedRow, db):
        self.log.tracef("In %s.delete()...", __name__)
        
        primaryKeyVal = ds.getValueAt(selectedRow, self.primaryKey)
        SQL = "delete from %s where %s = %d" % (self.tableName, self.primaryKey, primaryKeyVal)
        rows = system.db.runUpdateQuery(SQL, database=db)
        self.log.tracef("Deleted %d rows", rows)