# Copyright 2001-2007 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
from ils.common.util import isGatewayScope

"""
Logging package for Python. Based on PEP 282 and comments thereto in
comp.lang.python, and influenced by Apache's log4j system.

Should work under Python versions >= 1.5.2, except that source line
information is not available unless 'sys._getframe()' is.

Copyright (C) 2001-2007 Vinay Sajip. All Rights Reserved.

To use, simply 'import logging' and log away!
"""

import sys, os, types, datetime, time, string, cStringIO, traceback, system

try:
    import codecs
except ImportError:
    codecs = None

try:
    import thread
    import threading
except ImportError:
    thread = None

__author__  = "Vinay Sajip <vinay_sajip@red-dove.com>"
__status__  = "production"
__version__ = "0.5.0.2"
__date__    = "16 February 2007"

#---------------------------------------------------------------------------
#   Miscellaneous module data
#---------------------------------------------------------------------------

#
# _srcfile is used when walking the stack to check when we've got the first
# caller stack frame.
#
if hasattr(sys, 'frozen'): #support for py2exe
    _srcfile = "logging%s__init__%s" % (os.sep, __file__[-4:])
elif string.lower(__file__[-4:]) in ['.pyc', '.pyo']:
    _srcfile = __file__[:-4] + '.py'
else:
    _srcfile = __file__
_srcfile = os.path.normcase(_srcfile)

# next bit filched from 1.5.2's inspect.py
def currentframe():
    """Return the frame object for the caller's stack frame."""
    try:
        raise Exception
    except:
        return sys.exc_traceback.tb_frame.f_back

if hasattr(sys, '_getframe'): currentframe = lambda: sys._getframe(3)
# done filching

# _srcfile is only used in conjunction with sys._getframe().
# To provide compatibility with older versions of Python, set _srcfile
# to None if _getframe() is not available; this value will prevent
# findCaller() from being called.
#if not hasattr(sys, "_getframe"):
#    _srcfile = None

#
#_startTime is used as the base when calculating the relative time of events
#
_startTime = time.time()

#
#raiseExceptions is used to see if exceptions during handling should be
#propagated
#
raiseExceptions = 1

#
# If you don't want threading information in the log, set this to zero
#
logThreads = 1

#
# If you don't want process information in the log, set this to zero
#
logProcesses = 1

#---------------------------------------------------------------------------
#   Level related stuff
#---------------------------------------------------------------------------
#
# Default levels and level names, these can be replaced with any positive set
# of values having corresponding names. There is a pseudo-level, NOTSET, which
# is only really there as a lower limit for user-defined levels. Handlers and
# loggers are initialized with NOTSET so that they will log all messages, even
# at user-defined levels.
#

CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
TRACE = 5
NOTSET = 0
OFF = 0

_levelNames = {
    CRITICAL : 'CRITICAL',
    ERROR : 'ERROR',
    WARNING : 'WARNING',
    INFO : 'INFO',
    DEBUG : 'DEBUG',
    TRACE : 'TRACE',
    NOTSET : 'NOTSET',
    OFF: 'OFF',
    'CRITICAL' : CRITICAL,
    'ERROR' : ERROR,
    'WARN' : WARNING,
    'WARNING' : WARNING,
    'INFO' : INFO,
    'DEBUG' : DEBUG,
    'NOTSET' : NOTSET,
    'OFF': OFF
}

#
# Handler types for level configuration
#
IGNITION_HANDLER = 1
DATABASE_HANDLER = 2
CRASH_HANDLER = 3

#
# Level configuration attributes
#
LOGCFG_LEVEL = 1
LOGCFG_PRIORITY = 2
LOGCFG_RETENTION = 3

DEFAULT_RETENTION = {FATAL:24*365, ERROR:24*180, WARNING:24*30, INFO:24*10, DEBUG:24*5, TRACE:24}  # Retentions are in hours
DEFAULT_LEVEL_COMBO_CFG = {IGNITION_HANDLER: {LOGCFG_LEVEL:INFO,  LOGCFG_PRIORITY:10}, \
                           DATABASE_HANDLER: {LOGCFG_LEVEL:INFO, LOGCFG_PRIORITY:10, LOGCFG_RETENTION:DEFAULT_RETENTION}, \
                           CRASH_HANDLER:    {LOGCFG_LEVEL:TRACE, LOGCFG_PRIORITY:10}}

def getLevelName(level):
    """
    Return the textual representation of logging level 'level'.

    If the level is one of the predefined levels (CRITICAL, ERROR, WARNING,
    INFO, DEBUG) then you get the corresponding string. If you have
    associated levels with names using addLevelName then the name you have
    associated with 'level' is returned.

    If a numeric value corresponding to one of the defined levels is passed
    in, the corresponding string representation is returned.

    Otherwise, the string "Level %s" % level is returned.
    """
    return _levelNames.get(level, ("Level %s" % level))

def addLevelName(level, levelName):
    """
    Associate 'levelName' with 'level'.

    This is used when converting levels to text during message formatting.
    """
    _acquireLock()
    try:    #unlikely to cause an exception, but you never know...
        _levelNames[level] = levelName
        _levelNames[levelName] = level
    finally:
        _releaseLock()

#---------------------------------------------------------------------------
#   Thread-related stuff
#---------------------------------------------------------------------------

#
#_lock is used to serialize access to shared data structures in this module.
#This needs to be an RLock because fileConfig() creates Handlers and so
#might arbitrary user threads. Since Handler.__init__() updates the shared
#dictionary _handlers, it needs to acquire the lock. But if configuring,
#the lock would already have been acquired - so we need an RLock.
#The same argument applies to Loggers and Manager.loggerDict.
#
if thread:
    _lock = threading.RLock()
else:
    _lock = None

def _acquireLock():
    """
    Acquire the module-level lock for serializing access to shared data.

    This should be released with _releaseLock().
    """
    if _lock:
        _lock.acquire()

def _releaseLock():
    """
    Release the module-level lock acquired by calling _acquireLock().
    """
    if _lock:
        _lock.release()

#---------------------------------------------------------------------------
#   The logging record
#---------------------------------------------------------------------------

class LogRecord:
    """
    A LogRecord instance represents an event being logged.

    LogRecord instances are created every time something is logged. They
    contain all the information pertinent to the event being logged. The
    main information passed in is in msg and args, which are combined
    using str(msg) % args to create the message field of the record. The
    record also includes information such as when the record was created,
    the source line where the logging call was made, and any exception
    information to be logged.
    """
    def __init__(self, name, level, pathname, lineno,
                 msg, args, exc_info, func=None):
        """
        Initialize a logging record with interesting information.
        """
        ct = time.time()
        self.name = name
        self.msg = msg
        #
        # The following statement allows passing of a dictionary as a sole
        # argument, so that you can do something like
        #  logging.debug("a %(a)d b %(b)s", {'a':1, 'b':2})
        # Suggested by Stefan Behnel.
        # Note that without the test for args[0], we get a problem because
        # during formatting, we test to see if the arg is present using
        # 'if self.args:'. If the event being logged is e.g. 'Value is %d'
        # and if the passed arg fails 'if self.args:' then no formatting
        # is done. For example, logger.warn('Value is %d', 0) would log
        # 'Value is %d' instead of 'Value is 0'.
        # For the use case of passing a dictionary, this should not be a
        # problem.
        if args and (len(args) == 1) and args[0] and (type(args[0]) == types.DictType):
            args = args[0]
        self.args = args
        self.levelname = getLevelName(level)
        self.levelno = level
        self.pathname = pathname
        try:
            self.filename = os.path.basename(pathname)
            self.module = os.path.splitext(self.filename)[0]
        except:
            self.filename = pathname
            self.module = "Unknown module"
        self.exc_info = exc_info
        self.exc_text = None      # used to cache the traceback text
        self.lineno = lineno
        self.funcName = func
        self.timestamp = datetime.datetime.now()
        self.created = ct
        self.msecs = (ct - long(ct)) * 1000
        self.relativeCreated = (self.created - _startTime) * 1000
        if logThreads and thread:
            self.thread = thread.get_ident()
            self.threadName = threading.currentThread().getName()
        else:
            self.thread = None
            self.threadName = None
        if logProcesses and hasattr(os, 'getpid'):
            self.process = os.getpid()
        else:
            self.process = None
            
        '''
        A couple of things aded by Pete - project name. scope, and client id
        '''
        projectName = system.util.getProjectName()
        self.projectName = projectName
        
        if isGatewayScope():
            scope = "Gateway"
            clientId = ""
        else:
            scope = "Client"
            clientId = system.util.getClientId()
        self.scope = scope
        self.clientId = clientId

    def __str__(self):
        return '<LogRecord: %s, %s, %s, %s, "%s">'%(self.name, self.levelno,
            self.pathname, self.lineno, self.msg)

    def getMessage(self):
        """
        Return the message for this LogRecord.

        Return the message for this LogRecord after merging any user-supplied
        arguments with the message.
        """
        if not hasattr(types, "UnicodeType"): #if no unicode support...
            msg = str(self.msg)
        else:
            msg = self.msg
            if type(msg) not in (types.UnicodeType, types.StringType):
                try:
                    msg = str(self.msg)
                except UnicodeError:
                    msg = self.msg      #Defer encoding till later
        if self.args:
            msg = msg % self.args
        return msg

def makeLogRecord(dict):
    """
    Make a LogRecord whose attributes are defined by the specified dictionary,
    This function is useful for converting a logging event received over
    a socket connection (which is sent as a dictionary) into a LogRecord
    instance.
    """
    rv = LogRecord(None, None, "", 0, "", (), None, None)
    rv.__dict__.update(dict)
    return rv

#---------------------------------------------------------------------------
#   Formatter classes and functions
#---------------------------------------------------------------------------

class Formatter:
    """
    Formatter instances are used to convert a LogRecord to text.

    Formatters need to know how a LogRecord is constructed. They are
    responsible for converting a LogRecord to (usually) a string which can
    be interpreted by either a human or an external system. The base Formatter
    allows a formatting string to be specified. If none is supplied, the
    default value of "%s(message)\\n" is used.

    The Formatter can be initialized with a format string which makes use of
    knowledge of the LogRecord attributes - e.g. the default value mentioned
    above makes use of the fact that the user's message and arguments are pre-
    formatted into a LogRecord's message attribute. Currently, the useful
    attributes in a LogRecord are described by:

    %(name)s            Name of the logger (logging channel)
    %(levelno)s         Numeric logging level for the message (DEBUG, INFO,
                        WARNING, ERROR, CRITICAL)
    %(levelname)s       Text logging level for the message ("DEBUG", "INFO",
                        "WARNING", "ERROR", "CRITICAL")
    %(pathname)s        Full pathname of the source file where the logging
                        call was issued (if available)
    %(filename)s        Filename portion of pathname
    %(module)s          Module (name portion of filename)
    %(lineno)d          Source line number where the logging call was issued
                        (if available)
    %(funcName)s        Function name
    %(created)f         Time when the LogRecord was created (time.time()
                        return value)
    %(asctime)s         Textual time when the LogRecord was created
    %(msecs)d           Millisecond portion of the creation time
    %(relativeCreated)d Time in milliseconds when the LogRecord was created,
                        relative to the time the logging module was loaded
                        (typically at application startup time)
    %(thread)d          Thread ID (if available)
    %(threadName)s      Thread name (if available)
    %(process)d         Process ID (if available)
    %(message)s         The result of record.getMessage(), computed just as
                        the record is emitted
    """

    converter = time.localtime

    def __init__(self, fmt=None, datefmt=None):
        """
        Initialize the formatter with specified format strings.

        Initialize the formatter either with the specified format string, or a
        default as described above. Allow for specialized date formatting with
        the optional datefmt argument (if omitted, you get the ISO8601 format).
        """
        if fmt:
            self._fmt = fmt
        else:
            self._fmt = "%(message)s"
        self.datefmt = datefmt

    def formatTime(self, record, datefmt=None):
        """
        Return the creation time of the specified LogRecord as formatted text.

        This method should be called from format() by a formatter which
        wants to make use of a formatted time. This method can be overridden
        in formatters to provide for any specific requirement, but the
        basic behaviour is as follows: if datefmt (a string) is specified,
        it is used with time.strftime() to format the creation time of the
        record. Otherwise, the ISO8601 format is used. The resulting
        string is returned. This function uses a user-configurable function
        to convert the creation time to a tuple. By default, time.localtime()
        is used; to change this for a particular formatter instance, set the
        'converter' attribute to a function with the same signature as
        time.localtime() or time.gmtime(). To change it for all formatters,
        for example if you want all logging times to be shown in GMT,
        set the 'converter' attribute in the Formatter class.
        """
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
            s = "%s,%03d" % (t, record.msecs)
        return s

    def formatException(self, ei):
        """
        Format and return the specified exception information as a string.

        This default implementation just uses
        traceback.print_exception()
        """
        sio = cStringIO.StringIO()
        traceback.print_exception(ei[0], ei[1], ei[2], None, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1:] == "\n":
            s = s[:-1]
        return s

    def format(self, record):
        """
        Format the specified record as text.

        The record's attribute dictionary is used as the operand to a
        string formatting operation which yields the returned string.
        Before formatting the dictionary, a couple of preparatory steps
        are carried out. The message attribute of the record is computed
        using LogRecord.getMessage(). If the formatting string contains
        "%(asctime)", formatTime() is called to format the event time.
        If there is exception information, it is formatted using
        formatException() and appended to the message.
        """
        record.message = record.getMessage()
        if string.find(self._fmt,"%(asctime)") >= 0:
            record.asctime = self.formatTime(record, self.datefmt)
        s = self._fmt % record.__dict__
        if record.exc_info:
            # Cache the traceback text to avoid converting it multiple times
            # (it's constant anyway)
            if not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)
        if record.exc_text:
            if s[-1:] != "\n":
                s = s + "\n"
            s = s + record.exc_text
        return s

#
#   The default formatter to use when no other is specified
#
_defaultFormatter = Formatter()

class BufferingFormatter:
    """
    A formatter suitable for formatting a number of records.
    """
    def __init__(self, linefmt=None):
        """
        Optionally specify a formatter which will be used to format each
        individual record.
        """
        if linefmt:
            self.linefmt = linefmt
        else:
            self.linefmt = _defaultFormatter

    def formatHeader(self, records):
        """
        Return the header string for the specified records.
        """
        return ""

    def formatFooter(self, records):
        """
        Return the footer string for the specified records.
        """
        return ""

    def format(self, records):
        """
        Format the specified records and return the result as a string.
        """
        rv = ""
        if len(records) > 0:
            rv = rv + self.formatHeader(records)
            for record in records:
                rv = rv + self.linefmt.format(record)
            rv = rv + self.formatFooter(records)
        return rv

class OneLineExceptionFormatter(Formatter):
    def formatException(self, exc_info):
        """
        Format an exception so that it prints on a single line.
        """
        result = Formatter.formatException(self, exc_info)
        return repr(result) # or format into one line however you want to

    def format(self, record):
        s = Formatter.format(self, record)
        if record.exc_text:
            s = s.replace('\n', '') + '|'
        return s
    
#---------------------------------------------------------------------------
#   Filter classes and functions
#---------------------------------------------------------------------------

class Filter:
    """
    Filter instances are used to perform arbitrary filtering of LogRecords.

    Loggers and Handlers can optionally use Filter instances to filter
    records as desired. The base filter class only allows events which are
    below a certain point in the logger hierarchy. For example, a filter
    initialized with "A.B" will allow events logged by loggers "A.B",
    "A.B.C", "A.B.C.D", "A.B.D" etc. but not "A.BB", "B.A.B" etc. If
    initialized with the empty string, all events are passed.
    """
    def __init__(self, name=''):
        """
        Initialize a filter.

        Initialize with the name of the logger which, together with its
        children, will have its events allowed through the filter. If no
        name is specified, allow every event.
        """
        self.name = name
        self.nlen = len(name)

    def filter(self, record):
        """
        Determine if the specified record is to be logged.

        Is the specified record to be logged? Returns 0 for no, nonzero for
        yes. If deemed appropriate, the record may be modified in-place.
        """
        if self.nlen == 0:
            return 1
        elif self.name == record.name:
            return 1
        elif string.find(record.name, self.name, 0, self.nlen) != 0:
            return 0
        return (record.name[self.nlen] == ".")

class Filterer:
    """
    A base class for loggers and handlers which allows them to share
    common code.
    """
    def __init__(self):
        """
        Initialize the list of filters to be an empty list.
        """
        self.filters = []

    def addFilter(self, filter):
        """
        Add the specified filter to this handler.
        """
        if not (filter in self.filters):
            self.filters.append(filter)

    def removeFilter(self, filter):
        """
        Remove the specified filter from this handler.
        """
        if filter in self.filters:
            self.filters.remove(filter)

    def filter(self, record):
        """
        Determine if a record is loggable by consulting all the filters.

        The default is to allow the record to be logged; any filter can veto
        this and the record is then dropped. Returns a zero value if a record
        is to be dropped, else non-zero.
        """
        rv = 1
        for f in self.filters:
            if not f.filter(record):
                rv = 0
                break
        return rv

#---------------------------------------------------------------------------
#   Handler classes and functions
#---------------------------------------------------------------------------

_handlers = {}  #repository of handlers (for flushing when shutdown called)
_handlerList = [] # added to allow handlers to be removed in reverse of order initialized

class Handler(Filterer):
    """
    Handler instances dispatch logging events to specific destinations.

    The base handler class. Acts as a placeholder which defines the Handler
    interface. Handlers can optionally use Formatter instances to format
    records as desired. By default, no formatter is specified; in this case,
    the 'raw' message as determined by record.message is logged.
    """
    def __init__(self):
        """
        Initializes the instance - basically setting the formatter to None
        and the filter list to empty.
        """
        Filterer.__init__(self)
        self.level_cfg = None
        self.handler_type_name = ''
        self.formatter = None
        #get the module data lock, as we're updating a shared structure.
        _acquireLock()
        try:    #unlikely to raise an exception, but you never know...
            _handlers[self] = 1
            _handlerList.insert(0, self)
        finally:
            _releaseLock()
        self.createLock()

    def createLock(self):
        """
        Acquire a thread lock for serializing access to the underlying I/O.
        """
        if thread:
            self.lock = threading.RLock()
        else:
            self.lock = None

    def acquire(self):
        """
        Acquire the I/O thread lock.
        """
        if self.lock:
            self.lock.acquire()

    def release(self):
        """
        Release the I/O thread lock.
        """
        if self.lock:
            self.lock.release()

    #def setLevel(self, handler_type_name, level_cfg):
        '''
        Level is not stored on Handlers in my implementation.
        '''

    def format(self, record):
        """
        Format the specified record.

        If a formatter is set, use it. Otherwise, use the default formatter
        for the module.
        """
        if self.formatter:
            fmt = self.formatter
        else:
            fmt = _defaultFormatter
        return fmt.format(record)

    def emit(self, record):
        """
        Do whatever it takes to actually log the specified logging record.

        This version is intended to be implemented by subclasses and so
        raises a NotImplementedError.
        """
        raise NotImplementedError, 'emit must be implemented '\
                                    'by Handler subclasses'

    def handle(self, record, force=False):
        """
        Conditionally emit the specified logging record.

        Emission depends on filters which may have been added to the handler.
        Wrap the actual emission of the record with acquisition/release of
        the I/O thread lock. Returns whether the filter passed the record for
        emission.
        """
        rv = self.filter(record)
        if force or rv:
            self.acquire()
            try:
                self.emit(record, force)
            finally:
                self.release()
        return rv

    def setFormatter(self, fmt):
        """
        Set the formatter for this handler.
        """
        self.formatter = fmt

    def flush(self):
        """
        Ensure all logging output has been flushed.

        This version does nothing and is intended to be implemented by
        subclasses.
        """
        pass

    def close(self):
        """
        Tidy up any resources used by the handler.

        This version does removes the handler from an internal list
        of handlers which is closed when shutdown() is called. Subclasses
        should ensure that this gets called from overridden close()
        methods.
        """
        #get the module data lock, as we're updating a shared structure.
        _acquireLock()
        try:    #unlikely to raise an exception, but you never know...
            del _handlers[self]
            _handlerList.remove(self)
        finally:
            _releaseLock()

    def handleError(self, record):
        """
        Handle errors which occur during an emit() call.

        This method should be called from handlers when an exception is
        encountered during an emit() call. If raiseExceptions is false,
        exceptions get silently ignored. This is what is mostly wanted
        for a logging system - most users will not care about errors in
        the logging system, they are more interested in application errors.
        You could, however, replace this with a custom handler if you wish.
        The record which was being processed is passed in to this method.
        """
        if raiseExceptions:
            ei = sys.exc_info()
            traceback.print_exception(ei[0], ei[1], ei[2], None, sys.stderr)
            del ei

class StreamHandler(Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """
    def __init__(self, strm=None):
        """
        Initialize the handler.

        If strm is not specified, sys.stderr is used.
        """
        Handler.__init__(self)
        if strm is None:
            strm = sys.stderr
        self.stream = strm
        self.formatter = None

    def flush(self):
        """
        Flushes the stream.
        """
        self.stream.flush()

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline
        [N.B. this may be removed depending on feedback]. If exception
        information is present, it is formatted using
        traceback.print_exception and appended to the stream.
        """
        try:
            msg = self.format(record)
            fs = "%s\n"
            if not hasattr(types, "UnicodeType"): #if no unicode support...
                self.stream.write(fs % msg)
            else:
                try:
                    self.stream.write(fs % msg)
                except UnicodeError:
                    self.stream.write(fs % msg.encode("UTF-8"))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

class FileHandler(StreamHandler):
    """
    A handler class which writes formatted logging records to disk files.
    """
    def __init__(self, filename, mode='a', encoding=None):
        """
        Open the specified file and use it as the stream for logging.
        """
        if codecs is None:
            encoding = None
        if encoding is None:
            stream = open(filename, mode)
        else:
            stream = codecs.open(filename, mode, encoding)
        StreamHandler.__init__(self, stream)
        #keep the absolute path, otherwise derived classes which use this
        #may come a cropper when the current directory changes
        self.baseFilename = os.path.abspath(filename)
        self.mode = mode

    def close(self):
        """
        Closes the stream.
        """
        self.flush()
        self.stream.close()
        StreamHandler.close(self)

#---------------------------------------------------------------------------
#   Manager classes and functions
#---------------------------------------------------------------------------

class PlaceHolder:
    """
    PlaceHolder instances are used in the Manager logger hierarchy to take
    the place of nodes for which no loggers have been defined. This class is
    intended for internal use only and not as part of the public API.
    """
    def __init__(self, alogger):
        """
        Initialize with the specified logger being a child of this placeholder.
        """
        #self.loggers = [alogger]
        self.loggerMap = { alogger : None }

    def append(self, alogger):
        """
        Add the specified logger as a child of this placeholder.
        """
        #if alogger not in self.loggers:
        if not self.loggerMap.has_key(alogger):
            #self.loggers.append(alogger)
            self.loggerMap[alogger] = None

#
#   Determine which class to use when instantiating loggers.
#
_loggerClass = None

def setLoggerClass(klass):
    """
    Set the class to be used when instantiating a logger. The class should
    define __init__() such that only a name argument is required, and the
    __init__() should call Logger.__init__()
    """
    if klass != Logger:
        if not issubclass(klass, Logger):
            raise TypeError, "logger not derived from logging.Logger: " + \
                            klass.__name__
    global _loggerClass
    _loggerClass = klass

def getLoggerClass():
    """
    Return the class to be used when instantiating a logger.
    """

    return _loggerClass

class Manager:
    """
    There is [under normal circumstances] just one Manager instance, which
    holds the hierarchy of loggers.
    """
    def __init__(self, rootnode):
        """
        Initialize the manager with the root node of the logger hierarchy.
        """
        self.root = rootnode
        self.disable = 0
        self.emittedNoHandlerWarning = 0
        self.loggerDict = {}

    def getLogger(self, name):
        """
        Get a logger with the specified name (channel name), creating it
        if it doesn't yet exist. This name is a dot-separated hierarchical
        name, such as "a", "a.b", "a.b.c" or similar.

        If a PlaceHolder existed for the specified name [i.e. the logger
        didn't exist but a child of it did], replace it with the created
        logger and fix up the parent/child references which pointed to the
        placeholder to now point to the logger.
        """
        rv = None
        _acquireLock()
        try:
            if self.loggerDict.has_key(name):
                rv = self.loggerDict[name]
                if isinstance(rv, PlaceHolder):
                    ph = rv
                    rv = _loggerClass(name)
                    rv.manager = self
                    self.loggerDict[name] = rv
                    self._fixupChildren(ph, rv)
                    self._fixupParents(rv)
            else:
                rv = _loggerClass(name)
                rv.manager = self
                self.loggerDict[name] = rv
                self._fixupParents(rv)
        finally:
            _releaseLock()
        return rv

    def _fixupParents(self, alogger):
        """
        Ensure that there are either loggers or placeholders all the way
        from the specified logger to the root of the logger hierarchy.
        """
        name = alogger.name
        i = string.rfind(name, ".")
        rv = None
        while (i > 0) and not rv:
            substr = name[:i]
            if not self.loggerDict.has_key(substr):
                self.loggerDict[substr] = PlaceHolder(alogger)
            else:
                obj = self.loggerDict[substr]
                if isinstance(obj, Logger):
                    rv = obj
                else:
                    assert isinstance(obj, PlaceHolder)
                    obj.append(alogger)
            i = string.rfind(name, ".", 0, i - 1)
        if not rv:
            rv = self.root
        alogger.parent = rv

    def _fixupChildren(self, ph, alogger):
        """
        Ensure that children of the placeholder ph are connected to the
        specified logger.
        """
        name = alogger.name
        namelen = len(name)
        for c in ph.loggerMap.keys():
            #The if means ... if not c.parent.name.startswith(nm)
            #if string.find(c.parent.name, nm) <> 0:
            if c.parent.name[:namelen] != name:
                alogger.parent = c.parent
                c.parent = alogger

#---------------------------------------------------------------------------
#   Logger classes and functions
#---------------------------------------------------------------------------

class Logger(Filterer):
    """
    Instances of the Logger class represent a single logging channel. A
    "logging channel" indicates an area of an application. Exactly how an
    "area" is defined is up to the application developer. Since an
    application can have any number of areas, logging channels are identified
    by a unique string. Application areas can be nested (e.g. an area
    of "input processing" might include sub-areas "read CSV files", "read
    XLS files" and "read Gnumeric files"). To cater for this natural nesting,
    channel names are organized into a namespace hierarchy where levels are
    separated by periods, much like the Java or Python package namespace. So
    in the instance given above, channel names might be "input" for the upper
    level, and "input.csv", "input.xls" and "input.gnu" for the sub-levels.
    There is no arbitrary limit to the depth of nesting.
    """
    def __init__(self, name):
        """
        Initialize the logger with a name and an optional level.
        """
        print "Creating a new Logger named ", name
        Filterer.__init__(self)
        self.name = name
        self.parent = None
        self.propagate = 1
        self.handlers = []
        self.disabled = 0
        self.level_combo_cfg = None

    def setLevelComboConfig(self, level_combo_cfg):
        """
        Set the logging level of this logger.
        level is a tuple that consists of (log_level, log_level_priority)
        """
        if not isinstance(level_combo_cfg, dict):
            raise Exception('Expected dictionary for level_combo_cfg, got %s' % str(level_combo_cfg))
        self.level_combo_cfg = level_combo_cfg

    def setRootLevel(self, level_combo_cfg):
        setRootLevel(level_combo_cfg)
        
    def trace(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'TRACE'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.trace("Houston, we have a %s", "thorny problem", exc_info=1)
        """
        if self.manager.disable >= TRACE:
            return
        if TRACE >= self.getEffectiveLevel():
            apply(self._log, (TRACE, msg, args), kwargs)
        
    def tracef(self, msg, *args):        
        if self.manager.disable >= TRACE:
            return
        if TRACE >= self.getEffectiveLevel():
            apply(self._log, (TRACE, msg % tuple(args), None))

    def debug(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'DEBUG'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.debug("Houston, we have a %s", "thorny problem", exc_info=1)
        """
        if self.manager.disable >= DEBUG:
            return
        if DEBUG >= self.getEffectiveLevel():
            apply(self._log, (DEBUG, msg, args), kwargs)

    def debugf(self, msg, *args):
        if self.manager.disable >= DEBUG:
            return
        if DEBUG >= self.getEffectiveLevel():
            apply(self._log, (DEBUG, msg % tuple(args), None))

    def info(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'INFO'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.info("Houston, we have a %s", "interesting problem", exc_info=1)
        """
        if self.manager.disable >= INFO:
            return
        if INFO >= self.getEffectiveLevel():
            apply(self._log, (INFO, msg, args), kwargs)

    def infof(self, msg, *args):
        if self.manager.disable >= INFO:
            return
        if INFO >= self.getEffectiveLevel():
            apply(self._log, (INFO, msg % tuple(args), None))

    def warning(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'WARNING'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.warning("Houston, we have a %s", "bit of a problem", exc_info=1)
        """
        if self.manager.disable >= WARNING:
            return
        if self.isEnabledFor(WARNING):
            apply(self._log, (WARNING, msg, args), kwargs)

    warn = warning

    def warningf(self, msg, *args):
        if self.manager.disable >= WARNING:
            return
        if self.isEnabledFor(WARNING):
            apply(self._log, (WARNING, msg % tuple(args), None))

    warnf = warningf
    
    def error(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'ERROR'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.error("Houston, we have a %s", "major problem", exc_info=1)
        """
        if self.manager.disable >= ERROR:
            return
        if self.isEnabledFor(ERROR):
            apply(self._log, (ERROR, msg, args), kwargs)

    def errorf(self, msg, *args):
        if self.manager.disable >= ERROR:
            return
        if self.isEnabledFor(ERROR):
            apply(self._log, (ERROR, msg % tuple(args), None))

    def exception(self, msg, *args):
        """
        Convenience method for logging an ERROR with exception information.
        """
        # Original:
        #apply(self.error, (msg,) + args, {'exc_info': 1})
        self._log(ERROR, msg, args, exc_info=1)

    def critical(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'CRITICAL'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.critical("Houston, we have a %s", "major disaster", exc_info=1)
        """
        if self.manager.disable >= CRITICAL:
            return
        if CRITICAL >= self.getEffectiveLevel():
            apply(self._log, (CRITICAL, msg, args), kwargs)

    def criticalf(self, msg, *args):
        if self.manager.disable >= CRITICAL:
            return
        if CRITICAL >= self.getEffectiveLevel():
            apply(self._log, (CRITICAL, msg % tuple(args), None))

    fatal = critical
    fatalf = criticalf
    
    def log(self, level, msg, *args, **kwargs):
        """
        Log 'msg % args' with the integer severity 'level'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.log(level, "We have a %s", "mysterious problem", exc_info=1)
        """
        if type(level) != types.IntType:
            if raiseExceptions:
                raise TypeError, "level must be an integer"
            else:
                return
        if self.manager.disable >= level:
            return
        if self.isEnabledFor(level):
            apply(self._log, (level, msg, args), kwargs)

    def findCaller(self):
        """
        Find the stack frame of the caller so that we can note the source
        file name, line number and function name.
        """
        f = currentframe().f_back
        rv = "(unknown file)", 0, "(unknown function)"
        while hasattr(f, "f_code"):
            co = f.f_code
            filename = os.path.normcase(co.co_filename)
            if filename == _srcfile:
                f = f.f_back
                continue
            rv = (filename, f.f_lineno, co.co_name)
            break
        return rv

    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
        """
        A factory method which can be overridden in subclasses to create
        specialized LogRecords.
        """
        rv = LogRecord(name, level, fn, lno, msg, args, exc_info, func)
        
        # DMWebb extra;
        rv.effective_combo_levels = self.getEffectiveComboLevel()
        
        if extra:
            for key in extra:
                if (key in ["message", "asctime"]) or (key in rv.__dict__):
                    raise KeyError("Attempt to overwrite %r in LogRecord" % key)
                rv.__dict__[key] = extra[key]
        return rv

    def _log(self, level, msg, args, exc_info=None, extra=None):
        """
        Low-level logging routine which creates a LogRecord and then calls
        all the handlers of this logger to handle the record.
        """
        if _srcfile:
            fn, lno, func = self.findCaller()
        else:
            fn, lno, func = "(unknown file)", 0, "(unknown function)"
        if exc_info:
            if type(exc_info) != types.TupleType:
                exc_info = sys.exc_info()
        record = self.makeRecord(self.name, level, fn, lno, msg, args, exc_info, func, extra)
        self.handle(record)

    def handle(self, record):
        """
        Call the handlers for the specified record.

        This method is used for unpickled records received from a socket, as
        well as those created locally. Logger-level filtering is applied.
        """
        if (not self.disabled) and self.filter(record):
            self.callHandlers(record)

    def addHandler(self, hdlr):
        """
        Add the specified handler to this logger.
        """
        if not (hdlr in self.handlers):
            self.handlers.append(hdlr)

    def removeHandler(self, hdlr):
        """
        Remove the specified handler from this logger.
        """
        if hdlr in self.handlers:
            #hdlr.close()
            hdlr.acquire()
            try:
                self.handlers.remove(hdlr)
            finally:
                hdlr.release()

    def callHandlers(self, record):
        """
        Pass a record to all relevant handlers.

        Loop through all handlers for this logger and its parents in the
        logger hierarchy. If no handler was found, output a one-off error
        message to sys.stderr. Stop searching up the hierarchy whenever a
        logger with the "propagate" attribute set to zero is found - that
        will be the last logger whose handlers are called.
        """
        c = self
        found = 0
        while c:
            for hdlr in c.handlers:
                found = found + 1
                hdlr.handle(record)
            if not c.propagate:
                c = None    #break out
            else:
                c = c.parent
        if (found == 0) and raiseExceptions and not self.manager.emittedNoHandlerWarning:
            sys.stderr.write("No handlers could be found for logger"
                             " \"%s\"\n" % self.name)
            self.manager.emittedNoHandlerWarning = 1

    def getLocalLogger(self, frame=None, level=0):
        '''
        Go up the stack trace looking for a local variable called 'log'.
        If found, return it.
        
        NOTE:  This was an experiment that so far hasn't worked...
        '''
        import inspect
        if frame == None:
            frame = inspect.currentframe()
            locals = frame.f_locals
            globals = frame.f_globals
            code = frame.f_code
            if 'log' in locals:
                print 'level=%d, found local log' % level
                return locals['log']
        try:
            self.getLocalLogger(frame=frame.f_back, level=level+1)
        except:
            # Will throw an exception when can't go up any more
            pass
        finally:
            del frame
        
    def getEffectiveLevel(self):
        """
        Get the effective level for this logger.

        Loop through this logger and its parents in the logger hierarchy.
        Find the lowest level closest to root in the hierarchy which has the highest level_priority.
        """
        winning_priority = 0
        winning_level = 9999
        combo_eff = self.getEffectiveComboLevel()
        for type_name in self.level_combo_cfg.iterkeys():
            level_cfg = combo_eff[type_name]
            if level_cfg[LOGCFG_PRIORITY] >= winning_priority and level_cfg[LOGCFG_LEVEL] < winning_level:
                winning_priority = level_cfg[LOGCFG_PRIORITY]
                winning_level = level_cfg[LOGCFG_LEVEL]
        
        #print 'getEffectiveLevel: winning_level=%d, winning_priority=%d' % (winning_level, winning_priority)
        return winning_level

    def getEffectiveComboLevel(self):
        """
        """
        combo_eff = {}
        for type_name in self.level_combo_cfg.iterkeys():
            eff = self.getEffectiveLevelForType(type_name)
            combo_eff[type_name] = eff
        
        #print 'getEffectiveComboLevel: %s' % combo_eff
        return combo_eff

    def getEffectiveLevelForType(self, handler_type):
        """
        Get the effective level configuration for this type of logger.
        Example handler types = IGNITION_HANDLER, DATABASE_HANDLER, CRASH_HANDLER
        Loop through this logger and its parents in the logger hierarchy.
        Find the lowest level closest to root in the hierarchy which has the highest level_priority.
        """
        c = self
        winning_priority = 0
        winning_level = 9999
        winning_retention = None
        while c:  # loop up Loggers hierarchy
            # compare the Logger's level configuration
            if handler_type in c.level_combo_cfg:
                if c.level_combo_cfg[handler_type][LOGCFG_PRIORITY] > winning_priority:
                    winning_priority = c.level_combo_cfg[handler_type][LOGCFG_PRIORITY]
                    if c.level_combo_cfg[handler_type].has_key(LOGCFG_RETENTION):
                        winning_retention = c.level_combo_cfg[handler_type][LOGCFG_RETENTION]
                    if c.level_combo_cfg[handler_type][LOGCFG_LEVEL] < winning_level:
                        winning_level = c.level_combo_cfg[handler_type][LOGCFG_LEVEL]
            if not c.propagate:
                c = None    #break out
            else:
                c = c.parent
        #print 'type=%d, winning_level=%d, winning_priority=%d, winning_retention=%s' % \
        #     (handler_type, winning_level, winning_priority, winning_retention)
        return {LOGCFG_LEVEL:winning_level, LOGCFG_PRIORITY:winning_priority, LOGCFG_RETENTION:winning_retention}

    def isEnabledFor(self, level):
        """
        Is this logger enabled for level 'level'?
        """
        #print 'level=%d, disable=%d, effective_level=%d' % (level, self.manager.disable, self.getEffectiveLevel())
        if self.manager.disable >= level:
            return 0
        return level >= self.getEffectiveLevel()

class RootLogger(Logger):
    """
    A root logger is not that different to any other logger, except that
    it must have a logging level and there is only one instance of it in
    the hierarchy.
    """
    def __init__(self):
        """
        Initialize the logger with the name "root".
        """
        Logger.__init__(self, "root")
        self.setLevelComboConfig(DEFAULT_LEVEL_COMBO_CFG)
        
_loggerClass = Logger

root = RootLogger()
Logger.root = root
Logger.manager = Manager(Logger.root)

#---------------------------------------------------------------------------
# Configuration classes and functions
#---------------------------------------------------------------------------

BASIC_FORMAT = "%(levelname)s:%(name)s:%(message)s"

#---------------------------------------------------------------------------
# Utility functions at module level.
# Basically delegate everything to the root logger.
#---------------------------------------------------------------------------

def getLogger(name=None):
    """
    Return a logger with the specified name, creating it if necessary.

    If no name is specified, return the root logger.
    """
    if name:
        return Logger.manager.getLogger(name)
    else:
        return root

def xomGetLogger(name=None, level_combo_cfg=DEFAULT_LEVEL_COMBO_CFG):
    """
    Return a logger with the specified name, creating it if necessary.
    Add the DB Handler to the root logger if not already there.
    """
    if not name:
        raise Exception('Must provide name')

    log = Logger.manager.getLogger(name)
    log.setLevelComboConfig(level_combo_cfg)

    # Ignition Handler setup
    import ils.logging.handlers
    ih = ils.logging.handlers.IgnitionHandler(name)
    log.addHandler(ih)
    log.has_ignition_handler = True

    root = getLogger()
    if not hasattr(root, 'has_db_handler'):    
        # DB Handler setup
        dbh = ils.logging.handlers.DBHandler(db_name='Logs')
        #olef = OneLineExceptionFormatter('%(asctime)s|%(levelname)s|%(message)s|', '%d/%m/%Y %H:%M:%S')
        #dbh.setFormatter(olef)
        root.addHandler(dbh)
        root.has_db_handler = True
        
    if not hasattr(root, 'has_crash_handler'):    
        # Crash Handler setup
        ch = ils.logging.handlers.CrashHandler(capacity=10000, target=dbh)
        root.addHandler(ch)
        root.has_crash_handler = True
        
    return log

def setRootLevel(level_combo_cfg):
    root = getLogger()
    root.setLevelComboConfig(level_combo_cfg)
    
def disable(level):
    """
    Disable all logging calls less severe than 'level'.
    """
    root.manager.disable = level

def shutdown(handlerList=_handlerList):
    """
    Perform any cleanup actions in the logging system (e.g. flushing
    buffers).

    Should be called at application exit.
    """
    for h in handlerList[:]:
        #errors might occur, for example, if files are locked
        #we just ignore them if raiseExceptions is not set
        try:
            h.flush()
            h.close()
        except:
            if raiseExceptions:
                raise
            #else, swallow

#Let's try and shutdown automatically on application exit...
try:
    import atexit
    atexit.register(shutdown)
except ImportError: # for Python versions < 2.0
    def exithook(status, old_exit=sys.exit):
        try:
            shutdown()
        finally:
            old_exit(status)

    sys.exit = exithook

'''
Added by Pete to investigate how this works...
'''
def getManager():
    """
    Return a logger with the specified name, creating it if necessary.

    If no name is specified, return the root logger.
    """
    return Logger.manager
