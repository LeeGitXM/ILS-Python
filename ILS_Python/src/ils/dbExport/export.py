'''
Created on Mar 30, 2021

@author: phass
'''
import system, string

def exportCallback(event):
    print "In %s.exportCallback()" % (__name__)
    
    filename = event.source.parent.getComponent("Filename Field").text
    if filename == "":
        system.gui.warningBox("You must first specify a filename.")
        return

    system.file.writeFile(filename, "/*\n", False)
    system.file.writeFile(filename, "Export created on %s\n" % (system.date.format(system.date.now(), "MM/dd/yyyy hh:mm a")), True)
    system.file.writeFile(filename, "*/\n", True)
    
    table = event.source.parent.getComponent("String Column Table")
    ds = table.data
    stringColumns = []
    for row in range(ds.rowCount):
        val = str(string.upper(ds.getValueAt(row, 1)))
        stringColumns.append(val)
    print "The string columns are: ", stringColumns
    
    table = event.source.parent.getComponent("Date Column Table")
    ds = table.data
    dateColumns = []
    for row in range(ds.rowCount):
        val = str(string.upper(ds.getValueAt(row, 1)))
        dateColumns.append(val)
    print "The date columns are: ", dateColumns

    aList = event.source.parent.getComponent("Table List")
    ds = aList.data
    
    for row in range(ds.rowCount):
        tableName = ds.getValueAt(row, 0)

        exportTable(tableName, stringColumns, dateColumns, filename)
    print "DONE"
    
def exportTable(tableName, stringColumns, dateColumns, filename):
    system.file.writeFile(filename, "\n/*\n", True)
    system.file.writeFile(filename, "Table: %s\n" % (tableName), True)
    system.file.writeFile(filename, "*/\n\n", True)
    
    print "Exporting table: ", tableName
    
    SQL = "select * from %s" % (tableName)
    pds = system.db.runQuery(SQL)
    ds = system.dataset.toDataSet(pds)
    
    for row in range(ds.rowCount):
        cols = ""
        vals = ""
        for col in range(ds.columnCount):
            columnName = str(string.upper(ds.getColumnName(col)))
            if cols == "":
                cols = columnName
            else:
                cols = cols + ", " + columnName

            val = str(ds.getValueAt(row, columnName))
            if columnName in stringColumns:
                if vals == "":
                    if val in [None, "None"]:
                        vals = "''"
                    else:
                        vals = "'%s'" % (val)
                else:
                    if val in [None, "None"]:
                        vals = "%s, ''" % (vals)
                    else:
                        vals = "%s, '%s'" % (vals, val)
            elif columnName in dateColumns:
                dateval = system.date.format(system.date.now(), "yyyy-MM-dd HH:mm:ss")
                if vals == "":
                    vals = "'%s'" % (dateval)
                else:
                    vals = "%s, '%s'" % (vals, dateval)

            else:
                if vals == "":
                    vals = "%s" % (val)
                else:
                    vals = "%s, %s" % (vals, val)

        SQL = "Insert into %s (%s) VALUES (%s);\n" % (tableName, cols, vals)
        print SQL
        system.file.writeFile(filename, SQL, True)