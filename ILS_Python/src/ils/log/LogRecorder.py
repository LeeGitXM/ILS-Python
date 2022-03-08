#
import system
from ch.qos.logback.classic import Level
import sys, os, traceback, threading, string, datetime

# These are the keys available for grouping log statements
CLIENT_KEY="client"
FUNCTION_KEY="function"
LINE_KEY="linenumber"
MODULE_KEY="module"
PROJECT_KEY="project"

class LogLevel(object):
    def __init__(self, name, levelNumber, retention):
        self.levelName = name
        self.levelNumber = levelNumber
        self.retention = retention
        
Error   = LogLevel('ERROR',   40, 24*180)
Warning = LogLevel('WARNING', 30, 24*30)
Info    = LogLevel('INFO',    20, 24*10)
Debug   = LogLevel('DEBUG',   10, 24*5)
Trace   = LogLevel('TRACE',    1, 24)

def getLogLevel(name, levelName):
    if levelName is None:
        return None
    if string.upper(levelName) == 'ERROR':
        return Error
    elif string.upper(levelName) == 'WARNING':
        return Warning
    elif string.upper(levelName) == 'INFO':
        return Info
    elif string.upper(levelName) == 'DEBUG':
        return Debug
    elif string.upper(levelName) == 'TRACE':
        return Trace
    else:
        raise Exception('getLogLevel(%s): Level Name "%s" invalid.' % (name, levelName))
    
class LogRecorder:
    '''
    Like the standard Ignition / Log4j loggers, the db logger has a long life.  It will survive as long as the client or gateway are alive.
    It is important to understand that the actual Java logger, created by Ignition, only needs to be created once. 
    Each client has its own pool of loggers.  Likewise, the gateway has its own pool of loggers.  Even if it is created in a button, the Java 
    logger will persist in the client's JVM.  This creates a problem because we are maintaining the level of the logger in this class based 
    on the level requested at the time it was created and it is not synchronized with Java logger.   The user can either use the Gateway 
    web page to change the mode of a gateway logger or the Client Diagnostics window to change the state of a client logger.  
    So if the logger was initially created at Info level in a button script, the user changes it to trace and presses the button again, 
    then the trace mode must prevail.
    '''
    def __init__(self, name, dbName="Logs", levelName=None, enableTraceThread=False):
        print "Creating a new LogRecorder <%s> level: <%s>" % (name, str(levelName))
        self.name = name
        self.dbName = dbName
        self.logLevel = getLogLevel(name, levelName)
        self.created = datetime.datetime.now()
        self.enableTraceThread = enableTraceThread
        
        # Standard call returns a LoggerEx which is itself a wrapper
        self.logger = system.util.getLogger(self.name)
        self.dbLogger = DB_Logger(self)
        
        # Set the level of the Ignition logger to match the requested level
        if levelName != None:
            self.setLevel()
        
    def trace(self, msg):
        self.logger.trace(msg)
        self.dbLogger.trace(msg)
        
    def tracef(self, msg, *args):
        try:
            msg = msg % tuple(args)
        except:
            msg = "Error in tracef() - not enough arguments in %s %s" % (msg, str(tuple(args)))
        self.logger.trace(msg)
        self.dbLogger.trace(msg)

    def debug(self, msg):
        self.logger.debug(msg)
        self.dbLogger.debug(msg)

    def debugf(self, msg, *args):
        try:
            msg = msg % tuple(args) 
        except:
            msg = "Error in debugf() - not enough arguments in %s %s" % (msg, str(tuple(args)))
        self.logger.debug(msg)
        self.dbLogger.debug(msg)

    def info(self, msg):
        self.logger.info(msg)
        self.dbLogger.info(msg)
        
    def infof(self, msg, *args):
        try:
            msg = msg % tuple(args)
        except:
            msg = "Error in infof() - not enough arguments in %s %s" % (msg, str(tuple(args)))
        self.logger.info(msg)
        self.dbLogger.info(msg)

    def warn(self, msg):
        self.logger.warn(msg)
        self.dbLogger.warn(msg)

    def warnf(self, msg, *args):
        try:
            msg = msg % tuple(args) 
        except:
            msg = "Error in warnf() - not enough arguments in %s %s" % (msg, str(tuple(args)))
        self.logger.warn(msg)
        self.dbLogger.warn(msg)
    
    def error(self, msg):
        self.logger.error(msg)
        self.dbLogger.error(msg)

    def errorf(self, msg, *args):
        try:
            msg = msg % tuple(args) 
        except:
            msg = "Error in errorf() - not enough arguments in %s %s" % (msg, str(tuple(args)))
        self.logger.error(msg)
        self.dbLogger.error(msg)
        
    def setLevel(self):
        ''' Set the level of the Ignition logger to match the level of the DB logger. '''
        levelName = self.logLevel.levelName
        print "... setting the level to: ", levelName
        self.logger.getLoggerSLF4J().setLevel(Level.toLevel(levelName))

    def printStack(self):
        try:
            raise Exception
        except:
            tb = sys.exc_info()[2]
            while 1:
                if not tb.tb_next:
                    break
                tb = tb.tb_next
            stack = []
            f = tb.tb_frame
            while f:
                stack.append(f)
                f = f.f_back
            stack.reverse(  )
            traceback.print_exc(  )
            print "Locals by frame, innermost last"
            for frame in stack:
                print
                print "Frame %s in %s at line %s" % (frame.f_code.co_name,
                                                     frame.f_code.co_filename,
                                                     frame.f_lineno)
                for key, value in frame.f_locals.items(  ):
                    print "\t%20s = " % key,
                    # We have to be VERY careful not to cause a new error in our error
                    # printer! Calling str(  ) on an unknown object could cause an
                    # error we don't want, so we must use try/except to catch it --
                    # we can't stop it from happening, but we can and should
                    # stop it from propagating if it does happen!
                    try:
                        print value
                    except:
                        print "<ERROR WHILE PRINTING VALUE>"
                    

class DB_Logger():
    '''
    Logging handler that puts logs to the database.
    '''
    def __init__(self, parent):
        print "Creating a new DB_Logger()"
        self.parent = parent
        '''
        Changing the state of this global tag will not update the enabled state of loggers that have already been made.
        This could be an issue for long lived loggers in gateway scope - but I don't expect this tag to be changed often, 
        a site will either use or won't use DB logging.
        '''
        tagPath = "[XOM]Configuration/Common/dbLoggingEnabled"
        if system.tag.exists(tagPath):
            self.enabled = system.tag.read(tagPath).qv
        else:
            self.enabled = True
        
        if self.isGatewayScope():
            self.scope = "gateway"
            self.clientId = ""
        else:
            self.scope = "client"
            self.clientId = system.util.getClientId()
                
        self.projectName = system.util.getProjectName()
        if not self.projectName:
            self.projectName = "Global"
        
    def error(self, msg):
        if self.logMe(Error):
            self.emit(msg, Error)
            
    def warn(self, msg):
        if self.logMe(Warning):
            self.emit(msg, Warning)
        
    def info(self, msg):
        if self.logMe(Info):
            self.emit(msg, Info)
            
    def debug(self, msg):
        if self.logMe(Debug):
            self.emit(msg, Debug)

    def trace(self, msg):
        if self.logMe(Trace):
            self.emit(msg, Trace)

    def logMe(self, msgLevel):
        ''' 
        Return True if the logger level matches the msgLevel.
        Before we do anything, make sure that the log level of this logger is the same as the level of the Java logger. 
        '''
        effLevel = self.parent.logger.getLoggerSLF4J().getEffectiveLevel()        
        if effLevel.toString() != self.parent.logLevel.levelName:
            ''' Update the level of THIS logger '''
            self.parent.logLevel = getLogLevel(self.parent.name, effLevel.toString())
        
        if self.parent.enableTraceThread:  # Don't check if feature off for efficiency
            if self.logMeThreadLevel():
                return True
        if not self.enabled:
            return False

        if self.parent.logLevel is None:
            # Use system level if not set locally
            if msgLevel.levelName == 'INFO':
                if self.parent.logger.isInfoEnabled():
                    return True
            if msgLevel.levelName == 'DEBUG':
                if self.parent.logger.isDebugEnabled():
                    return True
            if msgLevel.levelName == 'TRACE':
                if self.parent.logger.isTraceEnabled():
                    return True
            return False
        else:
            if msgLevel.levelName == 'ERROR' or msgLevel.levelName == 'WARNING':
                return True
            if msgLevel.levelNumber >= self.parent.logLevel.levelNumber:
                return True
        return False
            
    def logMeThreadLevel(self):
        frame = sys._getframe(3)  # current frame
        while frame.f_back:
            frame = frame.f_back
            if '__THREAD_LOG' in frame.f_locals.keys():
                return True
        return False
    
    def formatDate(self, timestamp):
        ''' Format the timestamp to be compatible with SQL*Server '''
        return timestamp
    
    def emit(self, msg, logLevel):
        module, lineNumber, functionName = self.findCaller()
        threadName = self.getThreadName()
        retainUntil = self.formatDate(system.date.addHours(system.date.now(), logLevel.retention))
        timestamp = self.formatDate(system.date.now())
        msg = self.filterSQL(msg)
        SQL = '''INSERT INTO log (project, scope, client_id, thread_name, module, logger_name, timestamp, log_level, log_level_name, log_message, 
                                function_name, line_number, retain_until) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)'''
        values = [self.projectName, self.scope, self.clientId, threadName, module, self.parent.name, timestamp, logLevel.levelNumber, logLevel.levelName, msg, 
                  functionName, lineNumber, retainUntil]

        try:
            system.db.runPrepUpdate(SQL, values, self.parent.dbName)
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
        currentFrame = sys._getframe(3)
        topFilename = os.path.normcase(currentFrame.f_code.co_filename)
        f = currentFrame.f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == topFilename:
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