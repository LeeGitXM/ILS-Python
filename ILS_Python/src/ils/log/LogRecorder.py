
#
import sys, os, traceback, threading
import system

# These are the keys available for grouping log statements
CLIENT_KEY="client"
FUNCTION_KEY="function"
LINE_KEY="linenumber"
MODULE_KEY="module"
PROJECT_KEY="project"

#
# Level configuration attributes
#
LOGCFG_LEVEL = 1
LOGCFG_PRIORITY = 2
LOGCFG_RETENTION = 3

FATAL = "FATAL"
CRITICAL = 'CRITICAL'
ERROR = 'ERROR'
WARNING = 'WARNING'
INFO = 'INFO'
DEBUG = 'DEBUG'
TRACE = 'TRACE'

DEFAULT_RETENTION = {FATAL:24*365, ERROR:24*180, WARNING:24*30, INFO:24*10, DEBUG:24*5, TRACE:24}  # Retentions are in hours
LEVEL_NUMBER = {FATAL:50, ERROR:40, WARNING:30, INFO:20, DEBUG:10, TRACE:0}

# next bit filched from 1.5.2's inspect.py
def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_traceback.tb_frame.f_back

if hasattr(sys, '_getframe'): currentframe = lambda: sys._getframe(3)
# done filching

'''---------------------------------------------------------------------------
For a client, a LogRecorder instance is called every time a button is pressed, unless we find some way to cache it.
We do not create a new logger each time the log method is called.
It is important to understand that the actual Java logger, created by Ignition, only needs to be created once. 
Each client has its own pool of loggers.  In the gateway, they hang around forever.  
---------------------------------------------------------------------------'''
    
class LogRecorder:
    def __init__(self, name, dbName="Logs"):
        self.name = name
        
        # Standard call returns a LoggerEx which is itself a wrapper
        self.logger = system.util.getLogger(self.name)
        self.dbLogger = DB_Logger(self.logger, name, dbName)

    def trace(self, msg):
        self.logger.trace(msg)
        self.dbLogger.trace(msg)
        
    def tracef(self, msg, *args):
        try:
            msg = msg % tuple(args)
        except:
            msg = "Error in tracef() - not enough arguments in %s" % msg
        self.logger.trace(msg)
        self.dbLogger.trace(msg)

    def debug(self, msg):
        self.logger.debug(msg)
        self.dbLogger.debug(msg)

    def debugf(self, msg, *args):
        try:
            msg = msg % tuple(args) 
        except:
            msg = "Error in debugf() - not enough arguments in %s" % msg
        self.logger.debug(msg)
        self.dbLogger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)
        self.dbLogger.info(msg)
        
    def infof(self, msg, *args):
        try:
            msg = msg % tuple(args)
        except:
            msg = "Error in infof() - not enough arguments in %s" % msg
        self.logger.info(msg)
        self.dbLogger.info(msg)

    def warn(self, msg):
        self.logger.warn(msg)
        self.dbLogger.warn(msg)

    def warnf(self, msg, *args):
        try:
            msg = msg % tuple(args) 
        except:
            msg = "Error in warnf() - not enough arguments in %s" % msg
        self.logger.warn(msg)
        self.dbLogger.warn(msg)
    
    def error(self, msg):
        self.logger.error(msg)
        self.dbLogger.error(msg)

    def errorf(self, msg, *args):
        try:
            msg = msg % tuple(args) 
        except:
            msg = "Error in errorf() - not enough arguments in %s" % msg
        self.logger.error(msg)
        self.dbLogger.error(msg)

    def getLevelXX(self):
        level = str(self.logger.getLoggerSLF4J().getLevel())
        #print "LogRecorder: get level ",level
        return level
        
    def setLevelXX(self,level):
        print "LogRecorder: set level ",level
        #self.logger.getLoggerSLF4J().setLevel(Level.valueOf(level))
        self.logger.getLoggerSLF4J().setLevel(level)


class DB_Logger():
    '''
    Logging handler that puts logs to the database.
    '''
    def __init__(self, logger, loggerName, dbName):
        self.logger = logger
        self.loggerName = loggerName
        
        '''
        Changing the state of this global tag will not update the enabled state of loggers that have already been made.
        This could be an issue for long lived loggers in gateway scope - but I don't expect this tag to be changed often, 
        a site will either use or won't use DB logging.
        '''
        tagPath = "Configuration/Common/dbLoggingEnabled"
        if system.tag.exists(tagPath):
            self.enabled = system.tag.read(tagPath).qv
        else:
            self.enabled = True
        
        self.dbName = dbName
        if self.isGatewayScope():
            self.scope = "gateway"
            self.clientId = ""
        else:
            self.scope = "client"
            self.clientId = system.util.getClientId()
                
        self.projectName = system.util.getProjectName()
        if self.projectName=="":
            self.projectName = "Global"
        
    def error(self, msg):
        ''' error messages are always logged '''
        if self.enabled:
            retention = DEFAULT_RETENTION.get(ERROR)
            levelNumber = LEVEL_NUMBER.get(ERROR)
            levelName = ERROR
            self.emit(msg, retention, levelNumber, levelName)
            
    def warn(self, msg):
        ''' warning messages are always logged '''
        if self.enabled:
            retention = DEFAULT_RETENTION.get(WARNING)
            levelNumber = LEVEL_NUMBER.get(WARNING)
            levelName = WARNING
            self.emit(msg, retention, levelNumber, levelName)        
        
    def info(self, msg):
        if self.enabled and self.logger.isInfoEnabled():
            retention = DEFAULT_RETENTION.get(INFO)
            levelNumber = LEVEL_NUMBER.get(INFO)
            levelName = INFO
            self.emit(msg, retention, levelNumber, levelName)
            
    def debug(self, msg):
        if self.enabled and self.logger.isDebugEnabled():
            retention = DEFAULT_RETENTION.get(DEBUG)
            levelNumber = LEVEL_NUMBER.get(DEBUG)
            levelName = DEBUG
            self.emit(msg, retention, levelNumber, levelName)

    def trace(self, msg):
        if self.enabled and self.logger.isTraceEnabled():
            retention = DEFAULT_RETENTION.get(TRACE)
            levelNumber = LEVEL_NUMBER.get(TRACE)
            levelName = TRACE
            self.emit(msg, retention, levelNumber, levelName)
        
    def formatDate(self, timestamp):
        ''' Format the timestamp to be compatible with SQL*Server '''
        return timestamp
    
    def emit(self, msg, retention, levelNumber, levelName):
        module, lineNumber, functionName = self.findCaller()
        threadName = self.getThreadName()
        
        retainUntil = self.formatDate(system.date.addHours(system.date.now(), retention))
        timestamp = self.formatDate(system.date.now())

        msg = self.filterSQL(msg)
        
        SQL = 'INSERT INTO log (project, scope, client_id, thread_name, module, logger_name, timestamp, log_level, log_level_name, log_message, function_name, line_number, retain_until) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)'
        values = [self.projectName, self.scope, self.clientId, threadName, module, self.loggerName, timestamp, levelNumber, levelName, msg, functionName, lineNumber, retainUntil]

        try:
            system.db.runPrepUpdate(SQL, values, self.dbName)
        except Exception, e:
            print 'Caught exception while DB logging: %s' % str(e)

    def isClientScope(self):
        ''' This utility lives elsewhere but is COPIED here to make logging self sufficient, otherwise we get a circular import problem. '''
        try:
            flags = system.util.getSystemFlags()
            clientScope = (flags & 4) > 0
        except:
            clientScope = False

        return clientScope

    def isGatewayScope(self):
        ''' This utility lives elsewhere but is COPIED here to make logging self sufficient, otherwise we get a circular import problem. '''
        try:
            flags = system.util.getSystemFlags()
            gatewayScope = (flags & 1) <= 0 and (flags & 4) <= 0
        except:
            gatewayScope = True
    
        return gatewayScope
    
    def filterSQL(self, msg):
        ''' There may be certain characters that cause issues with SQL*Server.  This filters them out '''
        msg = msg.replace('\'', '\'\'')
        return msg

    def findCaller(self):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        __normFile__ = os.path.normcase(__file__)

        f = currentframe().f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)

            if filename == __normFile__:
                f = f.f_back
                continue
        
            '''  If the call was from external Python the filename can be obnoxiously long, trim up to pylib '''
            if filename.find('pylib') > 0:
                filename = filename[filename.find('pylib')+6:]
            
            rv = (filename, f.f_lineno, co.co_name)
            break
        return rv
    
    def getThreadName(self):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        try:
            thread = threading.currentThread()
            threadName = thread.getName()
        except:
            threadName = "Unknown" 
        
        return threadName