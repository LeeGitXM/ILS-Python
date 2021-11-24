'''
Created on Aug 29, 2020

@author: aedmw
'''
import system, datetime, string
from ils.io.util import readTag, writeTag
from ils.dataset.util import toList, fromList

from ils.log.LogRecorder import LogRecorder
log = LogRecorder(__name__)

MAIN_SQL = 'SELECT id, timestamp, log_level, log_level_name, logger_name, log_message, module, function_name, line_number, project, scope, client_id,  process_id, thread, thread_name FROM (%s) T ORDER BY timestamp ASC'
SUB_SQL = "SELECT TOP %d * FROM log WHERE timestamp > '%s' AND timestamp < '%s' %s ORDER BY timestamp DESC"
DATE_FORMAT = "YYYY-MM-dd HH:mm:ss"
FILTER_LIST = ["client_id", "function_name", "log_level_name", "log_message", "logger_name","module", "process_id", "project", "scope"]
TAG_ROOT = "[Client]Logging"
INCLUDE = "include"
EXCLUDE = "exclude"
REALTIME = "Realtime"
HISTORICAL = "Historical"
MANUAL = "Manual"
DESCENDING = "Descending"

ORDER_TAGPATH = "[Client]Logging/Order"

def clientStartup():
    ''' Set the start and end date of the client tags synchronized with the manual times '''
    print "In %s.clientStartup()" % (__name__)
    now = system.date.now()
    writeTag("[Client]Logging/Historical Start Time", system.date.addHours(now, -4))
    writeTag("[Client]Logging/Historical End Time", now)
    writeTag("[Client]Logging/Historical Outer Start Time", system.date.addDays(now, -7))
    writeTag("[Client]Logging/Historical Outer End Time", now)
    writeTag("[Client]Logging/Manual Start Time", system.date.addHours(now, -4))
    writeTag("[Client]Logging/Manual End Time", now)
    writeTag(ORDER_TAGPATH, DESCENDING)
    writeTag("[Client]Logging/Realtime Clear Time", system.date.addDays(system.date.now(), -5))
    writeTag("[Client]Logging/Realtime Units", "Minutes")
    writeTag("[Client]Logging/Realtime Value", 10)
    writeTag("[Client]Logging/Mode", "Realtime")

def internalFrameOpened(rootContainer):
    log.infof("In %s.IntenalFrameOpened()", __name__)

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
        writeTag(tagPath + "/Filter Mode", "No Filter")
        writeTag(tagPath + "/Includes", emptyDataset)
        
    writeTag("[Client]Logging/Realtime Clear Time", system.date.addDays(system.date.now(), -5))

def updateFilterAction(table, columnName, val, include_exclude):
    '''
    Called by the Popup menu on one of the filterable columns.
    '''
    rootContainer = table.parent
    columnName = columnName.rstrip()
    val = val.rstrip()
    include_exclude = string.capitalize(include_exclude)
    log.tracef("In %s.updateFilterAction. <%s> - <%s> - <%s>", __name__, columnName, val, include_exclude)
    
    mode, includes, excludes = readFilter(columnName)
    
    mode = include_exclude
    
    if string.lower(include_exclude) == INCLUDE:
        if val not in includes:
            includes.append(val)
    else:
        if val not in excludes:
            excludes.append(val)

    writeFilter(columnName, mode, includes, excludes)
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
        
    whereClause = getWhereClause()

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
        
def getWhereClause():
    log.tracef("In getWhereClause")
    clauses = []
    for sqlFilter in FILTER_LIST:
        selections = []
        operator = ""
        
        tagpaths = [
            "%s/Column Filters/%s/Excludes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Includes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, sqlFilter)
            ]
    
        qvs = system.tag.readBlocking(tagpaths)
        
        excludes = toList(qvs[0].value)
        includes = toList(qvs[1].value)
        mode = string.lower(qvs[2].value)
        
        if mode == INCLUDE:
            selections = includes
            operator = " IN "
                
        elif mode == EXCLUDE:
            selections = excludes
            operator = " NOT IN "
        
        if len(selections) > 0 and mode in [INCLUDE, EXCLUDE]:
            terms = []
            for selection in selections:
                selection = "'" + str(escapeSqlQuotes(selection)) + "'"
                terms.append('%s' % (selection))
            txt = ", ".join(terms)
            clauses.append("%s %s (%s)" % (sqlFilter, operator, txt))
    
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
    
    filterModes = []
    filterValues = []
    
    for sqlFilter in FILTER_LIST:        
        tagpaths = [
            "%s/Column Filters/%s/Excludes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Includes" % (TAG_ROOT, sqlFilter),
            "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, sqlFilter)
            ]
    
        qvs = system.tag.readBlocking(tagpaths)
        
        excludes = toList(qvs[0].value)
        filterValues = appender(filterValues, sqlFilter, "Exclude", excludes)
        
        includes = toList(qvs[1].value)
        filterValues = appender(filterValues, sqlFilter, "Include", includes)
    
        mode = qvs[2].value
        filterModes.append([sqlFilter, mode])
        
    header = ["Filter", "Mode", "Value"]
    ds = system.dataset.toDataSet(header, filterValues)
    rootContainer.getComponent("Filters Table").data = ds
    
    header = ["Filter", "Mode"]
    ds = system.dataset.toDataSet(header, filterModes)
    rootContainer.getComponent("Filter Mode Table").data = ds
    
def deleteFilterValueAction(rootContainer):
    '''
    Delete the filter by figuring out what was selected from the table, updating the client tag, and then refreshing the table
    '''
    loggingPath = rootContainer.loggingPath
    table = rootContainer.getComponent("Filters Table")
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
    tagPath = "%s/%s/%ss" % (loggingPath, filterName, mode)
    ds = readTag(tagPath).value
    filterList = toList(ds)
    ''' Really no way it can't be in the list, but be safe '''
    if not val in filterList:
        system.gui.errorBox("Fliter value <%s> is not in the list of values <%s>" % (val, str(filterList)))
        return
    filterList.remove(val)
    
    ''' Write the updated list out to the client tag '''
    writeTag(tagPath, fromList(filterList))
    refreshFilterWindow(rootContainer)
    
def escapeSqlQuotes(txt):
    txt = string.replace(txt, "'", "''")
    return txt