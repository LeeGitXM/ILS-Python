'''
Created on Aug 29, 2020

@author: aedmw
'''
import system, datetime, string
from java.awt import Toolkit
from java.awt.datatransfer import StringSelection
from ils.dataset.util import toList, fromList
from ils.common.constants import CR, PERCENT, TAB
from ils.io.util import readTag, writeTag

from ils.log import getLogger
log = getLogger(__name__)

MAIN_SQL = 'SELECT id, timestamp, log_level, log_level_name, logger_name, log_message, module, function_name, line_number, project, scope, client_id,  process_id, thread, thread_name FROM (%s) T ORDER BY timestamp ASC'
SUB_SQL = "SELECT TOP %d * FROM log WHERE timestamp > '%s' AND timestamp < '%s' %s ORDER BY timestamp DESC"
DATE_FORMAT = "YYYY-MM-dd HH:mm:ss"
FILTER_LIST = ["client_id", "function_name", "log_level_name", "log_message", "logger_name","module", "process_id", "project", "scope", "thread", "thread_name"]
TAG_ROOT = "[Client]Logging"
INCLUDE = "include"
EXCLUDE = "exclude"
REALTIME = "Realtime"
HISTORICAL = "Historical"
MANUAL = "Manual"
DESCENDING = "Descending"

ORDER_TAGPATH = "[Client]Logging/Order"

PLAY_STATE = 0
PAUSE_STATE = 1
CLIENT_TAG_NAME = {"Exclude": "Excludes", "Include": "Includes", "Exclude Custom": "ExcludesCustom", "Include Custom": "IncludesCustom"}

def clientStartup():
    ''' Set the start and end date of the client tags synchronized with the manual times '''
    print "In %s.clientStartup()" % (__name__)
    now = system.date.now()
    writeTag("[Client]Logging/Historical Outer Start Time", system.date.addDays(now, -6))
    writeTag("[Client]Logging/Historical Start Time", system.date.addHours(now, -4))
    writeTag("[Client]Logging/Historical End Time", system.date.addHours(now, -2))
    writeTag("[Client]Logging/Historical Outer End Time", now)
    
    writeTag("[Client]Logging/Manual Start Time", system.date.addHours(now, -4))
    writeTag("[Client]Logging/Manual End Time", now)
    
    writeTag(ORDER_TAGPATH, DESCENDING)
    writeTag("[Client]Logging/Realtime Clear Time", system.date.addYears(system.date.now(), -5))
    writeTag("[Client]Logging/Realtime Units", "Minutes")
    writeTag("[Client]Logging/Realtime Value", 10)
    writeTag("[Client]Logging/Mode", "Realtime")

def internalFrameOpened(rootContainer):
    log.infof("In %s.IntenalFrameOpened()", __name__)
    rootContainer.getComponent("Date Time Control Container").getComponent("Realtime Container").state = PLAY_STATE

def resetAllFiltersAction(rootContainer):
    '''
    The logging UI uses client tags.  Client tags are a project resource and are created automatically for each client when it connects.
    This should be added to the client startup script to initialize the client tags, otherwise they will have whatever was in them when the 
    project was last saved by the designer.
    '''         
    resetAllFilters()
    update(rootContainer)
    
def resetAllFilters():
    '''
    The logging UI uses client tags.  Client tags are a project resource and are created automatically for each client when it connects.
    This should be added to the client startup script to initialize the client tags, otherwise they will have whatever was in them when the 
    project was last saved by the designer.
    ''' 
    emptyDataset = system.dataset.toDataSet([], [])
        
    for columnFilter in FILTER_LIST:
        tagPath = "[Client]Logging/Column Filters/" + columnFilter 
        writeTag(tagPath + "/Excludes", emptyDataset)
        writeTag(tagPath + "/ExcludesCustom", emptyDataset)
        writeTag(tagPath + "/Filter Mode", "No Filter")
        writeTag(tagPath + "/Includes", emptyDataset)
        writeTag(tagPath + "/IncludesCustom", emptyDataset)
        
    writeTag("[Client]Logging/Realtime Clear Time", system.date.addYears(system.date.now(), -5))
    
def copyToClipboardAction(event):
    '''
    Copy the VISIBLE rows of the power table to the clipboard so that the user can then paste it into an e-mail, notepad, their sock drawer, etc.
    '''
    log.tracef("In %s.copyToClipboardAction()", __name__)
    rootContainer = event.source.parent
    table = rootContainer.getComponent("Power Table")
    ds = table.viewDataset
    
    rows = []
    for row in range(ds.rowCount):
        vals = []
        for col in range(ds.columnCount):
            vals.append(str(ds.getValueAt(row,col)))
        rowTxt = TAB.join(vals)
        rows.append(rowTxt)
    
    txt = CR.join(rows)
    clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
    clipboard.setContents(StringSelection(txt), None)
    
#-------------------------------------------------------------------------
# Function for basic filters (exclude or exclude column values)
#-------------------------------------------------------------------------

def updateFilterAction(table, rowIndex, columnName, val, include_exclude):
    '''
    Called by the Popup menu on one of the filterable columns.
    This is called from a popup menu on the power table when they right-click on a cell.
    I want to INCLUDE or EXCLUDE values from ALL of the selected rows in the selected column, this is especially.
    important for the INCLUDE filter because after the first include (if doing it one at a time) you can't see anything 
    else to include.  The caveat to all this is that you can launch a popup WITHOUT having selecting the row.  So
    make sure to make sure that the rowIndex is included in the list of selected rows. 
    '''
    rootContainer = table.parent
    columnName = columnName.rstrip()
    
    # None is really handled well, it goes deeper then this code here
    if val == None:
        return

    val = val.rstrip()
    filterMode = string.lower(include_exclude)
    log.tracef("In %s.updateFilterAction. <%s> - <%s>", __name__, columnName, filterMode)
    
    currentFilterMode, includes, excludes = readFilter(columnName)
    
    ''' Get the selected rows and make sure that the row that they clicked on is included '''
    ds = table.data
    rows = table.getSelectedRows()
    if rowIndex not in rows:
        rows.append(rowIndex)
    
    if len(rows) == 0:
        print "Warning, no rows are selected!"
    
    for row in rows:
        val = ds.getValueAt(row, columnName)
        print "%s: %s - %s - %s" % (include_exclude, columnName, row, val)
        if filterMode == INCLUDE:
            if val not in includes:
                includes.append(val)
        else:
            if val not in excludes:
                excludes.append(val)

    writeFilter(columnName, filterMode, includes, excludes)
    update(rootContainer)

def clearFilterAction(table, columnName):
    '''
    Called by the Popup menu on one of the filterable columns.
    Set the mode to 'No Filter' and then clear the include and exclude lists.
    '''
    rootContainer = table.parent
    columnName = columnName.rstrip()
    log.tracef("In %s.clearFilterAction. <%s>", __name__, columnName)
    writeFilter(columnName, "No Filter", [], [])
    update(rootContainer)
    
def setFilterMode(table, columnName, mode):
    '''
    Called by the Popup menu on one of the filterable columns.
    Set the mode to 'No Filter' and then clear the include and exclude lists.
    '''
    rootContainer = table.parent
    columnName = columnName.rstrip()
    log.tracef("In %s.setFilterMode. <%s> <%s>", __name__, columnName, mode)
    tagpath = "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, columnName)    
    writeTag(tagpath, mode)
    update(rootContainer)
    
def readFilter(columnName):
    tagpaths = [
        "%s/Column Filters/%s/Excludes" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/Includes" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, columnName)
        ]
    
    qvs = system.tag.readBlocking(tagpaths)
    
    excludes = toList(qvs[0].value)
    includes = toList(qvs[1].value)
    mode = qvs[2].value
    
    return mode, includes, excludes

def writeFilter(columnName, mode, includes, excludes):
    tagpaths = [
        "%s/Column Filters/%s/Excludes" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/Includes" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, columnName)
        ]
    
    excludes = fromList(excludes)
    includes = fromList(includes)
    
    system.tag.writeBlocking(tagpaths, [excludes, includes, mode])
    
#------------------------------------------------------------------------------
# A similar set of functions for dealing with the custom filters
#------------------------------------------------------------------------------
def updateCustomFilterAction(table, columnName, include_exclude):
    '''
    Called by the Popup menu on one of the filterable columns.
    This is called from a popup menu on the power table when they right-click on a cell.
    I want to INCLUDE or EXCLUDE values from ALL of the selected rows in the selected column, this is especially.
    important for the INCLUDE filter because after the first include (if doing it one at a time) you can't see anything 
    else to include.  The caveat to all this is that you can launch a popup WITHOUT having selecting the row.  So
    make sure to make sure that the rowIndex is included in the list of selected rows. 
    '''
    rootContainer = table.parent
    columnName = columnName.rstrip()

    filterMode = string.lower(include_exclude)
    log.infof("In %s.updateCustomFilterAction. <%s> - <%s>", __name__, columnName, filterMode)
    
    val = system.gui.inputBox("<HTML>Enter a string to <b>%s</b> from column %s, <br>(Remember to use %s as a wildcard.)" % (filterMode, columnName, PERCENT))
    
    if val == None:
        return
    
    currentFilterMode, customIncludes, customExcludes = readCustomFilter(columnName)
    
    print "Entered val:", val
    
    if filterMode == INCLUDE:
        if val not in customIncludes:
            customIncludes.append(val)
    else:
        if val not in customExcludes:
            customExcludes.append(val)

    writeCustomFilter(columnName, filterMode, customIncludes, customExcludes)
    update(rootContainer)

def readCustomFilter(columnName):
    tagpaths = [
        "%s/Column Filters/%s/ExcludesCustom" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/IncludesCustom" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, columnName)
        ]
    
    qvs = system.tag.readBlocking(tagpaths)
    
    excludes = toList(qvs[0].value)
    includes = toList(qvs[1].value)
    mode = qvs[2].value
    
    return mode, includes, excludes
    
def writeCustomFilter(columnName, mode, includes, excludes):
    tagpaths = [
        "%s/Column Filters/%s/ExcludesCustom" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/IncludesCustom" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, columnName)
        ]
    
    excludes = fromList(excludes)
    includes = fromList(includes)
    
    system.tag.writeBlocking(tagpaths, [excludes, includes, mode])

#--------------------------------------------------------------------------------
# Common functions for deal with all filters
#--------------------------------------------------------------------------------
def update(rootContainer):
    '''
    Write the SQL query to show the data out the sql_query tag.
    This is a pretty clever SQL statement (thanks Daniel) that uses a subquery to get the rows that math the where clause and then the outer query that
    gets the top rows.  Unfortunately, SQL*Server can't figure out the the where clause with the top clause in the same statement.
    '''
    log.tracef("In update...")
    table = rootContainer.getComponent("Power Table")
    
    container = rootContainer.getComponent("Date Time Control Container")
    mode = container.getComponent("Mode Dropdown").selectedStringValue
    if mode == HISTORICAL:
        startTime = container.getComponent("Historical Container").getComponent("Date Range").startDate
        endTime = container.getComponent("Historical Container").getComponent("Date Range").endDate
    elif mode == REALTIME:
        endTime = system.date.now()
        units = container.getComponent("Realtime Container").getComponent('Realtime Units Dropdown').selectedStringValue
        val = container.getComponent("Realtime Container").getComponent('Spinner').intValue
        clearTime = readTag("[Client]Logging/Realtime Clear Time").value
        log.tracef("The clear time is %s", str(clearTime))
        
        if units == "Days":
            startTime = system.date.addDays(endTime, -1 * val)
        elif units == "Hours":
            startTime = system.date.addHours(endTime, -1 * val)
        else:
            startTime = system.date.addMinutes(endTime, -1 * val)
            
        ''' Use the latest of the startTime and the startTime '''
        if system.date.isAfter(clearTime, startTime):
            log.tracef("...using the clear time...")
            startTime = clearTime

    elif mode == MANUAL:
        startTime = container.getComponent("Manual Container").getComponent("Start Popup Calendar").date
        endTime = container.getComponent("Manual Container").getComponent("End Popup Calendar").date
        
    else:
        system.gui.messageBox("Unexpected mode")
        return
    
    db = rootContainer.databaseConnection
    startTime = system.date.format(startTime, DATE_FORMAT)
    endTime = system.date.format(endTime, DATE_FORMAT)
        
    whereClause = getWhereClause(table)

    tagpath = "%s/Max Records" % (TAG_ROOT)
    maxRecords = readTag(tagpath).value
    subquery = SUB_SQL % (maxRecords, startTime, endTime, whereClause)
    SQL = MAIN_SQL % subquery
    log.tracef(SQL)
    
    startTime = system.date.now()
    pds = system.db.runQuery(SQL, db)
    endTime = system.date.now()
    queryTime = system.date.millisBetween(startTime, endTime)
    log.tracef("The query took %.3f ms", queryTime / 1000.0)
    ds = system.dataset.toDataSet(pds)
    
    order = readTag(ORDER_TAGPATH).value
    log.tracef("The order is: %s", order)
    if order == DESCENDING:
        ds = system.dataset.sort(ds, "timestamp", False)
    
    table.data = ds
        
def getWhereClause(table):
    log.tracef("In getWhereClause")
    clauses = []
    for sqlFilter in FILTER_LIST:
        tagpaths = [
            "%s/Column Filters/%s/Excludes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/ExcludesCustom" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Includes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/IncludesCustom" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, sqlFilter)
            ]
    
        qvs = system.tag.readBlocking(tagpaths)
        
        excludes = toList(qvs[0].value)
        excludesCustom = toList(qvs[1].value)
        includes = toList(qvs[2].value)
        includesCustom = toList(qvs[3].value)
        mode = string.lower(qvs[4].value)
        
        ''' Save the mode to a property of the table that is used to format the header to show columns that have a filter '''
        if string.upper(mode) == "NO FILTER":
            setattr(table, sqlFilter + "_filter_active", False)
        else:
            setattr(table, sqlFilter + "_filter_active", True)
        
        if mode == INCLUDE:
            if len(includes) > 0:
                terms = []
                for aFilter in includes:
                    aFilter = "'" + str(escapeSqlQuotes(aFilter)) + "'"
                    terms.append('%s' % (aFilter))
                txt = ", ".join(terms)
                clauses.append("%s IN (%s)" % (sqlFilter, txt))
                
            if len(includesCustom) > 0:
                terms = []
                for aFilter in includesCustom:
                    aFilter = "'" + str(escapeSqlQuotes(aFilter)) + "'"
                    clauses.append("%s LIKE (%s)" % (sqlFilter, aFilter))
        
        elif mode == EXCLUDE:        
            if len(excludes) > 0:
                terms = []
                for aFilter in excludes:
                    aFilter = "'" + str(escapeSqlQuotes(aFilter)) + "'"
                    terms.append('%s' % (aFilter))
                txt = ", ".join(terms)
                clauses.append("%s NOT IN (%s)" % (sqlFilter, txt))
                
            if len(excludesCustom) > 0:
                terms = []
                for aFilter in excludesCustom:
                    aFilter = "'" + str(escapeSqlQuotes(aFilter)) + "'"
                    clauses.append("%s NOT LIKE (%s)" % (sqlFilter, aFilter))
    
    #print "Clauses: ", clauses
    if len(clauses) > 0: 
        andWhere = "and " + " and ".join(clauses)
    else:
        andWhere = ""
    
    #print "andWhere: ", andWhere
    return andWhere

def updateStartTime(self, update_time_only):
    '''
    Called when the Start Time button is pressed.
    If left-clicked, the button is toggled:  
        When toggled on, set the Start Time tag to the current time and the Start Time On tag to True.
        When toggled off, set the Start Time On tag to False.
    If right-clicked, the time is updated but the state is not toggled.
    '''
    if update_time_only:
        self.tags.start_time.value = datetime.datetime.now()
    else:
        if self.tags.start_time_on.value:
            self.tags.start_time_on.value = False
        else:
            self.tags.start_time_on.value = True
            self.tags.start_time.value = datetime.datetime.now()
    self.writeSQL()

'''
Automation for the Filter Configuration Window.
'''

def refreshFilterWindow(rootContainer):

    ''' ------------------------------------------------------------'''
    def appender(filterValues, sqlFilter, mode, vals):
        for val in vals:
            filterValues.append([sqlFilter, mode, val])
        return filterValues
    ''' ------------------------------------------------------------ '''
    
    filterContainer = rootContainer.getComponent("Filter Configuration Container")
    filterModes = []
    filterValues = []
    
    for sqlFilter in FILTER_LIST:        
        tagpaths = [
            "%s/Column Filters/%s/Excludes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/ExcludesCustom" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Includes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/IncludesCustom" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, sqlFilter)
            ]
    
        qvs = system.tag.readBlocking(tagpaths)
        
        excludes = toList(qvs[0].value)
        filterValues = appender(filterValues, sqlFilter, "Exclude", excludes)
        
        excludes = toList(qvs[1].value)
        filterValues = appender(filterValues, sqlFilter, "Exclude Custom", excludes)
        
        includes = toList(qvs[2].value)
        filterValues = appender(filterValues, sqlFilter, "Include", includes)
        
        includes = toList(qvs[3].value)
        filterValues = appender(filterValues, sqlFilter, "Include Custom", includes)
    
        mode = qvs[4].value
        filterModes.append([sqlFilter, mode])
        
    header = ["Filter", "Mode", "Value"]
    ds = system.dataset.toDataSet(header, filterValues)
    filterContainer.getComponent("Filters Table").data = ds
    
    header = ["Filter", "Mode"]
    ds = system.dataset.toDataSet(header, filterModes)
    filterContainer.getComponent("Filter Mode Table").data = ds
    
def deleteFilterValueAction(rootContainer):
    '''
    Delete the filter by figuring out what was selected from the table, updating the client tag, and then refreshing the table
    '''
    filterContainer = rootContainer.getComponent("Filter Configuration Container")
    loggingPath = rootContainer.loggingPath
    table = filterContainer.getComponent("Filters Table")
    if table.selectedRow < 0:
        system.gui.messageBox("Please select a filter value to delete.")
        return
    
    ''' Get the filter mode and value from the selected row in the table '''
    selectedRow = table.selectedRow
    ds = table.data
    filterName = ds.getValueAt(selectedRow, 0)
    mode = ds.getValueAt(selectedRow, 1)
    val = ds.getValueAt(selectedRow, 2)
    
    ''' Read the dataset from the client tag and remove the desired row '''
    clientTag = CLIENT_TAG_NAME.get(mode, None)
    tagPath = "%s/%s/%s" % (loggingPath, filterName, clientTag)
    ds = readTag(tagPath).value
    filterList = toList(ds)
    ''' Really no way it can't be in the list, but be safe '''
    if not val in filterList:
        system.gui.errorBox("Filter value <%s> is not in the list of values <%s>" % (val, str(filterList)))
        return
    filterList.remove(val)
    
    ''' Write the updated list out to the client tag '''
    writeTag(tagPath, fromList(filterList))
    refreshFilterWindow(rootContainer)
    
def filterEdited(table, rowIndex, columnIndex, colName, oldValue, newValue):
    ''' Update the client tag, from which the SQL is built. '''
    filterContainer = table.parent
    rootContainer = filterContainer.parent
    loggingPath = table.parent.parent.loggingPath
    table = filterContainer.getComponent("Filters Table")

    ''' Get the filter mode and value from the selected row in the table '''
    ds = table.data
    filterName = ds.getValueAt(rowIndex, 0)
    mode = ds.getValueAt(rowIndex, 1)
    
    ''' Read the dataset from the client tag and remove the desired row '''
    clientTag = CLIENT_TAG_NAME.get(mode, None)
    tagPath = "%s/%s/%s" % (loggingPath, filterName, clientTag)
    ds = readTag(tagPath).value
    filterList = toList(ds)
    
    ''' Really no way it can't be in the list, but be safe '''
    if not oldValue in filterList:
        system.gui.errorBox("Filter value <%s> is not in the list of values <%s>" % (oldValue, str(filterList)))
        filterList.append(newValue)
    else:
        ''' This is a bit brute force but we need to be careful to maintain the order in the list. '''
        newList = []
        for val in filterList:
            if val == oldValue:
                newList.append(newValue)
            else:
                newList.append(val)
        
        filterList = newList
    
    ''' Write the updated list out to the client tag '''
    writeTag(tagPath, fromList(filterList))
    refreshFilterWindow(rootContainer)
    
    ''' Update the Filter Value table on the filter config window. ''' 
    table.data = system.dataset.setValue(table.data, rowIndex, columnIndex, newValue)
    
def escapeSqlQuotes(txt):
    txt = string.replace(txt, "'", "''")
    return txt

def updateDebugTable(event):
    '''
    For debug use only, this provides a way to see the client tags from a client.
    This populates a table in the Test container.
    '''
    log.tracef("In updateDebugTable")
    vals = []
    
    for sqlFilter in FILTER_LIST:    
        tagpaths = [
            "%s/Column Filters/%s/Excludes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/ExcludesCustom" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Includes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/IncludesCustom" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, sqlFilter)
            ]
    
        qvs = system.tag.readBlocking(tagpaths)
        
        excludes = toList(qvs[0].value)
        excludesCustom = toList(qvs[1].value)
        includes = toList(qvs[2].value)
        includesCustom = toList(qvs[3].value)
        mode = string.lower(qvs[4].value)
        
        for aFilter in includes:
            vals.append([sqlFilter, mode, "include", aFilter])
        for aFilter in includesCustom:
            vals.append([sqlFilter, mode, "includeCustom", aFilter])
        for aFilter in excludes:
            vals.append([sqlFilter, mode, "exclude", aFilter])
        for aFilter in excludesCustom:
            vals.append([sqlFilter, mode, "excludeCustom", aFilter])

    #print "Clauses: ", clauses
    table = event.source.parent.getComponent("Power Table")
    
    if len(vals) > 0: 
        ds = system.dataset.toDataSet(["Column", "Mode", "Type", "Filter"], vals)
    else:
        ds = table.data
        ds = system.dataset.clearDataset(ds)
        
    table.data = ds
    