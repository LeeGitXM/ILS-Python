'''
Created on Aug 29, 2020

@author: aedmw
'''
import system, datetime, string
from ils.dataset.util import tagToList, listToTag, toList, fromList
from ils.common.util import escapeSqlQuotes
import ils.logging as logging
log = system.util.getLogger('com.ils.logging.viewer')    


MAIN_SQL = 'SELECT id, timestamp, log_level,  log_levelname, logger_name, module, function_name, log_message, project, scope, client_id, line_number,  process_id, thread, thread_name FROM (%s) T ORDER BY timestamp ASC'
SUB_SQL = "SELECT TOP 100 * FROM log WHERE timestamp > '%s' AND timestamp < '%s' %s ORDER BY timestamp DESC"
DATE_FORMAT = "YYYY-MM-dd HH:mm:ss"
FILTER_LIST = ["client_id", "function_name", "log_levelname", "log_message", "module", "process_id", "project", "scope"]
TAG_ROOT = "[Client]Logging"
INCLUDE = "include"
EXCLUDE = "exclude"

def internalFrameOpened(rootContainer):
    #from com.inductiveautomation.factorypmi.application.components.template import TemplateHolder 
    log.infof("In IntenalFrameOpened")

def resetAllFiltersAction(rootContainer):
    '''
    The logging UI uses client tags.  Client tags are a project resource and are created automatically for each client when it connects.
    This should be added to the client startup script to initialize the client tags, otherwise they will have whatever was in them when the 
    project was last saved by the designer.
    ''' 
    emptyDataset = system.dataset.toDataSet([], [])
        
    for columnFilter in FILTER_LIST:
        tagPath = "[Client]Logging/Column Filters/" + columnFilter 
        system.tag.write(tagPath + "/Excludes", emptyDataset)
        system.tag.write(tagPath + "/Filter Mode", "No Filter")
        system.tag.write(tagPath + "/Includes", emptyDataset)
        
    update(rootContainer)

def updateFilterAction(event, columnName, val, include_exclude):
    '''
    Called by the Popup menu on one of the filterable columns.
    '''
    rootContainer = event.source.parent
    columnName = columnName.rstrip()
    val = val.rstrip()
    include_exclude = string.lower(include_exclude)
    log.infof("In %s.updateFilterAction. <%s> - <%s> - <%s>", __name__, columnName, val, include_exclude)
    
    mode, includes, excludes = readFilter(columnName)
    
    mode = include_exclude
    
    if include_exclude == INCLUDE:
        if val not in includes:
            includes.append(val)
    else:
        if val not in excludes:
            excludes.append(val)

    writeFilter(columnName, mode, includes, excludes)
    update(rootContainer)

def clearFilterAction(event, columnName):
    '''
    Called by the Popup menu on one of the filterable columns.
    Set the mode to 'No Filter' and then clear the include and exclude lists.
    '''
    rootContainer = event.source.parent
    columnName = columnName.rstrip()
    log.infof("In %s.clearFilterAction. <%s>", __name__, columnName)
    writeFilter(columnName, "No Filter", [], [])
    update(rootContainer)
    
def readFilter(columnName):
    tagpaths = [
        "%s/Column Filters/%s/Excludes" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/Includes" % (TAG_ROOT, columnName),
        "%s/Column Filters/%s/Filter Mode" % (TAG_ROOT, columnName)
        ]
    
    qvs = system.tag.readAll(tagpaths)
    
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
    
    system.tag.writeAll(tagpaths, [excludes, includes, mode])

def update(rootContainer):
    '''
    Write the SQL query to show the data out the sql_query tag.
    This is a pretty clever SQL statement (thanks Daniel) that uses a subquery to get the rows that math the where clause and then the outer query that
    gets the top rows.  Unfortunately, SQL*Server can't figure out the the where clause with the top clause in the same statement.
    '''
    log.tracef("In update...")
    table = rootContainer.getComponent("Power Table")
    db = rootContainer.databaseConnection
    dateControl = rootContainer.getComponent("Date Time Control")
    startTime = system.date.format(dateControl.startTime, DATE_FORMAT)
    endTime = system.date.format(dateControl.endTime, DATE_FORMAT)    
    whereClause = getWhereClause()

    subquery = SUB_SQL % (startTime, endTime, whereClause)
    SQL = MAIN_SQL % subquery
    log.tracef(SQL)
    
    pds = system.db.runQuery(SQL, db)
    table.data = pds
        
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
    
        qvs = system.tag.readAll(tagpaths)
        
        excludes = toList(qvs[0].value)
        includes = toList(qvs[1].value)
        mode = qvs[2].value
        
        if mode == INCLUDE:
            selections = includes
            operator = " IN "
                
        elif mode == EXCLUDE:
            selections = excludes
            operator = " NOT IN "
        
        if len(selections) > 0:
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