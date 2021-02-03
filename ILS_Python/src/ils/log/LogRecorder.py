'''
imports require the ils-common jar file and the ILS Logger module
'''
#
import os,sys
import system
import system.ils.log.properties as LogProps
import ch.qos.logback.classic.Level as Level
import org.slf4j.MDC as MDC
import com.ils.common.log.LogMaker as LogMaker

#---------------------------------------------------------------------------
#   The logging record
#---------------------------------------------------------------------------

class LogRecorder:
    def __init__(self,name):
        self.name = name
        self.projectName = system.util.getProjectName()
        if self.projectName=="":
            self.projectName = "Global"
        if self.projectName=="Global":
            self.scope = "Global"
            self.clientId = ""
        else:
            self.scope = "client"
            self.clientId = system.util.getClientId()
        
        #self.logger = LogProps.getLogger(self.name)
        # Standard call returns a LoggerEx which is itself a wrapper
        self.logger = system.util.getLogger(self.name)
        
    def trace(self, msg):
        self.setAttributes()
        self.logger.trace(msg)
        
    def tracef(self, msg, *args):
        self.setAttributes()
        msg = msg % tuple(args)
        self.logger.trace(msg)

    def debug(self, msg):
        self.setAttributes()
        self.logger.debug(msg)

    def debugf(self, msg, *args):
        self.setAttributes()
        msg = msg % tuple(args) 
        self.logger.debug(msg)

    def info(self, msg):
        self.setAttributes()
        self.logger.info(msg)
        
    def infof(self, msg, *args):
        self.setAttributes()
        msg = msg % tuple(args)
        self.logger.info(msg)

    def warn(self, msg):
        self.setAttributes()
        self.logger.warn(msg)

    def warnf(self, msg, *args):
        self.setAttributes()
        msg = msg % tuple(args) 
        self.logger.warn(msg)
    
    def error(self, msg):
        self.setAttributes()
        self.logger.error(msg)

    def errorf(self, msg, *args):
        self.setAttributes()
        msg = msg % tuple(args) 
        self.logger.error(msg)

    # Place attributes into the MDC specific to this message
    # MDC = Mapped Diagnostic Contexts
    def setAttributes(self):
        # Get a stack track and fill in line number, function and module
        self.findCaller()
        MDC.put(LogMaker.CLIENT_KEY,self.clientId)
        MDC.put(LogMaker.PROJECT_KEY,self.projectName)



    # next bit filched from 1.5.2's inspect.py
    def currentframe(self):
        """Return the frame object for the caller's stack frame."""
        try:
            raise Exception
        except:
            return sys.exc_traceback.tb_frame.f_back

    # Iterate over the stack trace to find the caller.
    # When we've found it, store results in the MDC
    def findCaller(self):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = self.currentframe().f_back
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            print filename, f.f_lineno, co.co_name
            if filename == __file__:
                f = f.f_back
                continue

            MDC.put(LogMaker.FUNCTION_KEY,co.co_name)
            MDC.put(LogMaker.LINE_KEY,str(f.f_lineno))
            MDC.put(LogMaker.MODULE_KEY,os.path.splitext(filename)[0])
            break

    def getLevel(self):
        level = str(self.logger.getLoggerSLF4J().getLevel())
        #print "LogRecorder: get level ",level
        return level
        
    def setLevel(self,level):
        #print "LogRecorder: set level ",level
        self.logger.getLoggerSLF4J().setLevel(Level.valueOf(level))