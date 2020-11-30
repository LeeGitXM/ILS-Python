'''
imports require the ils-common jar file and the ILS Logger module
'''
#
import system
import com.ils.common.log.LogMaker as LogMaker
import ch.qos.logback.classic.spi.LoggingEvent as LoggingEvent
import java.util.Date as Date
import ch.qos.logback.classic.Level as Level

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
        self.logger = LogMaker.getLogger(self.name,self.projectName) 
        
    def trace(self, msg):
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.TRACE)
        self.apply(event)
        
    def tracef(self, msg, *args):
        msg = msg % tuple(args)   
        event = LoggingEvent() 
        event.setMessage(msg)
        event.setLevel(Level.TRACE)
        self.apply(event)

    def debug(self, msg):
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.DEBUG)
        self.apply(event)

    def debugf(self, msg, *args):
        msg = msg % tuple(args) 
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.DEBUG)     
        self.apply(event)

    def info(self, msg):
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.INFO)
        self.apply(event)
        
    def infof(self, msg, *args):
        msg = msg % tuple(args)
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.INFO)
        self.apply(event)

    def warning(self, msg):
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.WARN)
        self.apply(event)

    def warningf(self, msg, *args):
        msg = msg % tuple(args) 
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.WARN)
        self.apply(event)
    
    def error(self, msg, *args):
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.ERROR)
        self.apply(event)

    def errorf(self, msg, *args):
        msg = msg % tuple(args) 
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.ERROR)
        self.apply(event)

    def critical(self, msg):
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.FATAL)
        self.apply(event)

    def criticalf(self, msg, *args):
        msg = msg % tuple(args) 
        event = LoggingEvent()
        event.setMessage(msg)
        event.setLevel(Level.FATAL)
        self.apply(event)

    def apply(self, event):
        event.setTimeStamp(Date().getTime())
        event.getMDCPropertyMap().put(LogMaker.CLIENT_KEY,self.clientId)
        event.getMDCPropertyMap().put(LogMaker.PROJECT_KEY,self.projectName)
        self.logger.callAppenders(event)

