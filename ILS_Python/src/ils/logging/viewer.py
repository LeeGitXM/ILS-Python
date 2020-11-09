'''
Created on Aug 29, 2020

@author: aedmw
'''
import system, datetime
from ils.logging.util2 import xom1DDataSet
from ils.logging.ignition_tags import IgnitionTagsClass, IgnitionTagClass
import ils.logging as logging
log = logging.xomGetLogger('xom.logging.viewer')

class ColumnFilterClass(object):
    def __init__(self, parent, tagpath, column_name):
        self.parent = parent
        self.tagpath = tagpath
        self.column_name = column_name
        log.tracef("Creating FilterClass(%s, %s)", tagpath, column_name)
        prefix = '[Client]%s/Column Filters' % tagpath
        tag_list = [
                    {'python_name':'filter_mode',    'tagpath':'%s/%s/Filter Mode' % (prefix, column_name), 'type':'string', 'direction':'READ/WRITE'},
                    {'python_name':'includes',       'tagpath':'%s/%s/Includes' % (prefix, column_name), 'type':'dataset', 'direction':'READ/WRITE'},
                    {'python_name':'excludes',       'tagpath':'%s/%s/Excludes' % (prefix, column_name), 'type':'dataset', 'direction':'READ/WRITE'},
                    ]   
        self.tags = IgnitionTagsClass(tag_list)

    def viewFilterList(self):
        '''
        - Set value of Filter Viewer Custom Property 'ViewingDataset'
        - Pop up Filter Viewer popup window
        '''
        pass
    
    def getWhereClause(self, column_filter, operator):
        filters = xom1DDataSet(column_filter)
        filters_str = " AND %s %s (" % (self.column_name, operator)
        first_exp = True
        if len(filters) > 0:
            for i in filters:
                if not first_exp:
                    comma = ','
                else:
                    comma = ''
                if isinstance(i, str):
                    i = i.strip()
                filters_str += "%s'%s'" % (comma, i)
                first_exp = False
            filters_str += ') '
        else:
            filters_str = ''
        return filters_str
        
    def getWhereClauses(self):
        return_str = ''
        if self.tags.filter_mode.value.upper() == 'INCLUDES':
            if self.column_name == 'log_message':
                return_str = self.getWhereClause(self.tags.includes.value, 'LIKE')
            else:
                return_str = self.getWhereClause(self.tags.includes.value, 'IN')
        elif self.tags.filter_mode.value.upper() == 'EXCLUDES':
            return_str = self.getWhereClause(self.tags.excludes.value, 'NOT IN')
        return return_str

    def updateColumnFilter(self, filter_type, add_remove):
        filter_selection = xom1DDataSet(self.parent.tags.filter_selection.value)
        filter_mode_tag = self.tags.filter_mode
        filter_mode = self.tags.filter_mode.value
        if filter_type.upper() == 'INCLUDES':
            column_filter_tag = self.tags.includes
        elif filter_type.upper() == 'EXCLUDES':
            column_filter_tag = self.tags.excludes
        else:
            raise Exception('Unexpected filter_type=%s' % filter_type)
        column_filter = xom1DDataSet(column_filter_tag.value)
        
        if add_remove == 'add':
            if len(filter_selection) > 0:
                # Add the names in the Filter Selection dataset to the include/exclude list for this column
                for fs_row in filter_selection:
                    fs_row = fs_row.strip()
                    if fs_row == '':
                        continue
                    if fs_row not in column_filter:
                        column_filter.append(fs_row)
                column_filter_tag.value = column_filter.updateDataSet()
                column_filter_tag.write(force=True)
            else: # left button and empty Filter Selection, toggle Column Filter Mode
                if filter_type == filter_mode:
                    filter_mode = 'No Filter'
                else:
                    filter_mode = filter_type
                filter_mode_tag.value = filter_mode
                filter_mode_tag.write(force=True)
        else: # add_remove == 'remove'
            if len(filter_selection) == 0:
                column_filter.data = []
            else:                
                # Remove the names in the Filter Selection dataset from the include/exclude list for this column
                for fs_row in filter_selection:
                    fs_row = fs_row.strip()
                    if fs_row == '':
                        continue
                    if fs_row in column_filter:
                        column_filter.remove(fs_row)
            column_filter_tag.value = column_filter.updateDataSet()
            column_filter_tag.write(force=True)
        self.parent.clearFilterSelection()
            
class ColumnFiltersClass(object):
    def __init__(self, tagpath, db_name, column_names=['module','function_name','log_levelname','process_id','log_message']):
        self.tagpath = tagpath
        self.column_names = column_names
        self.db_name = db_name
        self.column_filters = {}
        log.tracef("Creating FiltersClass(%s, %s, %s)", tagpath, str(column_names), db_name)
        prefix = '[Client]%s' % tagpath
        tag_list = [
                    {'python_name':'sql_query',           'tagpath':'%s/SQL Query' % (prefix), 'type':'string', 'direction':'READ/WRITE'},
                    {'python_name':'start_time',          'tagpath':'%s/Start Time' % (prefix), 'type':'datetime', 'direction':'READ/WRITE'},
                    {'python_name':'start_time_on',       'tagpath':'%s/Start Time On' % (prefix), 'type':'boolean', 'direction':'READ/WRITE'},
                    {'python_name':'filter_selection',    'tagpath':'%s/Column Filters/Filter Viewer/Filter Selection' % (prefix), 'type':'string', 'direction':'READ/WRITE'},
                    ]
        self.tags = IgnitionTagsClass(tag_list)
        
        # Load Filter for each filtered column
        for column in column_names:
            self.column_filters[column] = ColumnFilterClass(self, tagpath, column)

    def getWhereClauses(self):
        '''
        Return the WHERE clauses for the Column Filters corresponding to their current Filter Modes.
        '''
        wc = ''
        for cf in self.column_filters.itervalues():
            wc += cf.getWhereClauses()
        return wc
    
    def writeSQL(self):
        '''
        Write the SQL query to show the data out the sql_query tag.
        '''
        where_clauses = self.getWhereClauses()
        if self.tags.start_time_on.value:
            start_time = "'%s'" % self.tags.start_time.value.strftime("%Y-%m-%d %H:%M:%S")
        else:
            start_time = "'2000-01-01 00:00:00'"       
        main_sql = 'SELECT id, timestamp, logger_name, module, function_name, line_number, log_levelname, log_level, ' + \
                    'log_message,  process_id, thread, thread_name FROM (%s) T ORDER BY timestamp ASC;'
        subquery = "SELECT TOP 100 * FROM log WHERE timestamp > %s %s ORDER BY timestamp DESC" % (start_time, where_clauses)
        sql = main_sql % subquery
        #print 'sql = %s' % sql
        self.tags.sql_query.value = sql
        self.tags.sql_query.write()
      
    def updateColumnFilter(self, event, column_name, filter_type, add_remove):
        '''
        Update the Column Filter corresponding to this event (when the "E" or "I" buttons are pressed).
        If add_remove == 'add', add the contents of Filter Selection tag to the Column Filter.
        If add_remove == 'remove', remove the contents of Filter Selection tag from the Column Filter.
        '''
        cf = self.column_filters[column_name]
        cf.updateColumnFilter(filter_type, add_remove)
        self.writeSQL()

    def clearFilterSelection(self):
        '''
        Clear the contents of the Filter Selection tag.
        '''
        for row in range(self.tags.filter_selection.value.getRowCount()):
            self.tags.filter_selection.value = system.dataset.deleteRow(self.tags.filter_selection.value, 0)
        self.tags.filter_selection.write(force=True)

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
          
def filterButtonAction(event):
    '''
    Called by the Mouse Click event handler on the filter "I" and "E" buttons.
    '''   
    root_path = event.source.parent.parent.loggingPath
    column_filters = ColumnFiltersClass(root_path, 'Logs')
    column_name = event.source.parent.columnName
    filter_type = event.source.filterType
    if event.button == event.BUTTON1:
        # Left-click adds the contents of the Filter Selection Tag to the current Column Filter (Includes/Excludes).
        column_filters.updateColumnFilter(event, column_name, filter_type, add_remove='add')
    else:
        # Right-click brings up the include/exclude list editor
        window = system.nav.openWindow('%s/Filter Viewer' % root_path, 
                                       {'dataPath' : '%s/%s' % (column_name, filter_type),
                                        'currentColumn' : '%s' % column_name,
                                        'currentFilterType' : '%s' % filter_type})
        system.nav.centerWindow(window)
    column_filters.writeSQL()

def filterViewerClearButtonAction(event):
    '''
    Called by the Mouse Click event handler on the Filter Viewer window Clear button.
    If the Filter Selection tag is not empty, clear entries matching those in this Column Filter.
    Otherwise, clear all entries in this Column Filter.
    '''   
    root_path = event.source.parent.loggingPath
    column_name = event.source.parent.currentColumn
    filter_type = event.source.parent.currentFilterType
    column_filters = ColumnFiltersClass(root_path, 'Logs')
    column_filters.updateColumnFilter(event, column_name, filter_type, add_remove='remove')
    
def addToFilterSelection(logging_path, event, value):
    '''
    Called by a Mouse Click event handler on the Power Table for the Log Viewer or Filter Viewer windows.
    '''
    tagname = '[Client]%s/Column Filters/Filter Viewer/Filter Selection' % logging_path
    ds = system.tag.read(tagname).value
    new_ds = system.dataset.addRow(ds, [value])
    system.tag.write(tagname, new_ds)
    
def addColumnFilterItem(event):
    '''
    Called by pressing the Enter key while in the "add item" text entry box of the Filter Viewer window.
    '''
    root_path = event.source.parent.loggingPath
    addToFilterSelection(root_path, event, event.source.text)
    column_filters = ColumnFiltersClass(root_path, 'Logs')
    column_name = event.source.parent.currentColumn
    filter_type = event.source.parent.currentFilterType
    column_filters.updateColumnFilter(event, column_name, filter_type, add_remove='add')
    # Clear entry box for next addition
    event.source.text = ''

def startTimeButton(event, update_time_only=False):
    '''
    Called by pressing the Start Time button.
    '''
    logging_path = event.source.parent.loggingPath
    column_filters = ColumnFiltersClass(logging_path, 'Logs')
    column_filters.updateStartTime(update_time_only)
    column_filters.tags.write()
    
def updateSQL(event):
    logging_path = event.source.parent.loggingPath
    column_filters = ColumnFiltersClass(logging_path, 'Logs')
    column_filters.writeSQL()
    


        