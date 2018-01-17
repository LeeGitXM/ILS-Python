"""
Created on Oct 31, 2014

@author: rforbes
"""

# I know Rob defined this somewhere else but I can't find it
# Need to devise a way for customer defined SFC windows, like istalon's Rate change review data screen to get added to this list. 
SFC_WINDOW_LIST = ["SFC/BusyNotification", "SFC/DialogMessage", "SFC/Input", "SFC/ManualDataEntry", "SFC/MonitorDownloads", "SFC/Notification", \
                   "SFC/ReviewData", "SFC/ReviewFlows", "SFC/SelectInput", "SFC/TimeDelayNotification", "SFC/YesNo", \
                   "Vistalon/SFC/Rate Change/Rate Change Review Data", "Test/SFC Use Case Tests/ReviewData"]

# Screen Positions
CENTER = "center"
TOP_LEFT = "topLeft"
TOP_CENTER = "topCenter"
TOP_RIGHT = "topRight"
BOTTOM_LEFT = "bottomLeft"
BOTTOM_CENTER = "bottomCenter"
BOTTOM_RIGHT = "bottomRight"
RIGHT = "right"
LEFT = "left"
TOP = "top"
BOTTOM = "bottom"

# Step Properties
ACK_REQUIRED = "ackRequired"
ACTIVATION_CALLBACK = "activationCallback"
ACTUAL_TIMING = "actualTiming"
ACTUAL_DATETIME = "actualDateTime"
ATTRIBUTE = "attribute"
AUTO_MODE = "autoMode"
AUTOMATIC = "automatic"
BUTTON = "button"
BUTTON_LABEL = "buttonLabel"
BUTTON_KEY = "buttonKey"
BUTTON_KEY_LOCATION = "buttonKeyLocation"
BY_NAME = "stepsByName"
CALLBACK = "callback"
CANCELED = "canceled"
CHART = "chart"
CHART_NAME = "chartName"
CHART_PROPERTIES = "chartProperties"
CHART_RUN_ID = "chartRunId"
CHOICES= "choices"
CHOICES_KEY = "choicesKey"
CHOICES_RECIPE_LOCATION = "choicesRecipeLocation"
CLASS = "class"
CLASS_NAME = "className"
CLIENT_ID = "clientId"
COLLECT_DATA_CONFIG = "collectDataConfig"
COMMAND = "callback"
COMPUTER = "computer"
CONFIG = "config"
CONFIRM_CONTROLLERS_CONFIG = "confirmControllersConfig"
CONTROL_PANEL_ID = "controlPanelId"
CONTROL_PANEL_NAME = "controlPanelName"
CONTROL_PANEL_WINDOW_PATH = "controlPanelWindowPath"
COUNT_ABSOLUTE = "absolute"
COUNT_INCREMENTAL = "incremental"
CREATE_TIME = "createTime"
CREATE = "create"
CUSTOM_WINDOW_PATH = "customWindowPath"
DATA = "data"
DATA_LOCATION = "dataLocation"
DATABASE = "database"
DEFAULT_MESSAGE_QUEUE = "SFC-Message-Queue"
DESCRIPTION = "description"
DELAY = "delay"
DELAY_UNIT = "delayUnit"
DIRECTORY = "directory"
DOWNLOAD = "download"
DOWNLOAD_STATUS = "downloadStatus"
DYNAMIC = "dynamic"
DISPLAY_MODE = "displayMode"
ENABLE_PAUSE = "enablePause"
ENABLE_RESUME = "enableResume"
ENABLE_CANCEL = "enableCancel"
ENABLE_RESET = "enableReset"
ENABLE_START = "enableStart"
ERROR_COUNT_KEY = "errorCountKey"
ERROR_COUNT_MODE = "errorCountMode"
ERROR_COUNT_SCOPE = "errorCountScope"
ERROR_COUNT_LOCAL = "errorCountLocal"
END_TIME = "endTime"
EXTENSION = "extension"
FAILURE = "Failure"
FETCH_MODE = "fetchMode"
FILEPATH = "filepath"
FILENAME = "filename"
GLOBAL = "global"
HANDLER = "handler"
HEADING1 = "heading1"
HEADING2 = "heading2"
HEADING3 = "heading3"
ID = "id"
IMMEDIATE = "Immediate"
INPUT = "input"
INSTANCE_ID = "instanceId"
IS_SFC_WINDOW = "isSfcWindow"
ISOLATION_MODE = "isolationMode"
KEY = "key"
KEY_MODE = "keyMode"
LOCATION = "location"
MESSAGE = "message"
MESSAGE_QUEUE = "msgQueue"
MESSAGE_ID = "msgId"
METHOD = "method"
MINIMUM_VALUE = "minimumValue"
MANUAL_DATA_CONFIG = "manualDataConfig"
MAXIMUM_VALUE = "maximumValue"
MONITOR = "monitor"
MONITOR_DOWNLOADS_CONFIG = "monitorDownloadsConfig"
MONITORING = "Monitoring"
MSG_QUEUE_WINDOW = "Queue/Message Queue"
MULTIPLE = "multiple"
NAME = "name"
NUMBER_OF_TIMEOUTS = "numberOfTimeouts"
NUMBER_OF_ERRORS = "numberOfErrors"
OK = "Ok"
ORIGINATOR = "originator"
OUTPUT_VALUE = "OutputValue"
OUTPUT_TYPE = "outputType"
PARENT = "parent"
PENDING = "Pending"
POSITION = "position"
POST_TO_QUEUE = "postToQueue"
POST_NOTIFICATION = "postNotification"
POSTING_METHOD = "postingMethod"
PRIMARY_CONFIG = "primaryConfig"
PRIMARY_REVIEW_DATA = "primaryReviewData" 
PRIMARY_REVIEW_DATA_WITH_ADVICE = "primaryReviewDataWithAdvice" 
PRIMARY_TAB_LABEL = "primaryTabLabel"; 
PRINT_FILE = "printFile"
PRIORITY = "priority"
PRIVATE = "private"
PROJECT = "project"
PROMPT = "prompt"
PUBLIC = "public"
PV_MONITOR_ACTIVE = "pvMonitorActive"
PV_MONITOR_CONFIG = "pvMonitorConfig"
PV_MONITOR_STATUS = "pvMonitorStatus"
PV_VALUE = "pvValue"
RECIPE = "recipe"
RECIPE_LOCATION = "recipeLocation" 
RECIPE_DATA = "recipeData"
RECIPE_DATA_TYPE = "recipeDataType"
REQUIRE_ALL_INPUTS = "requireAllInputs"
RESPONSE = "response"
RESPONSE_KEY_AND_ATTRIBUTE = "responseKeyAndAttribute";
RESULTS_MODE = "resultsMode" 
REVIEW_FLOWS = "reviewFlows"
SCALE = "scale"
SECONDARY_CONFIG = "secondaryConfig"
SECONDARY_REVIEW_DATA = "secondaryReviewData" 
SECONDARY_REVIEW_DATA_WITH_ADVICE = "secondaryReviewDataWithAdvice" 
SECONDARY_TAB_LABEL = "secondaryTabLabel"
SECURITY = "security"
SEMI_AUTOMATIC = "semiAutomatic"
SERVER = "server"
SESSION = "session"
SESSION_ID = "sessionId"
SESSIONS = "sessions"
SETPOINT = "setpoint"
SETPOINT_STATUS = "setpointStatus"
SHOW_PRINT_DIALOG = "showPrintDialog"
SINGLE = "single"
SQL = "sql"
START_TIME = "startTime"
STATIC = "static"
STATUS = "status"
STEP = "step"
STEP_ID = "stepId"
STEP_PROPERTIES = "stepProperties"
STEP_NAME = "name"
STRATEGY = "strategy"
SUCCESS = "Success"
SUM_FLOWS = "sumFlows"
TAG_PATH = "tagPath"
TAG = "tag"
STRATEGY = "strategy"
TABLE = "table"
TARGET_STEP_UUID = "targetStepUUID"
TARGET_VALUE = "targetValue"
TEST_CHART_PATHS = "testChartPaths"
TEST_PATTERN = "testPattern"
TEST_REPORT_FILE = "testReportFile"
TIMED_OUT = "timedOut"
TIMEOUT = "timeout"
TIMEOUT_TIME = "timeoutTime"
TIMEOUT_UNIT = "timeoutUnit"
TIMESTAMP = "timestamp"
TIMING = "timing"
UPDATE = "update"
UPDATE_OR_CREATE = "updateOrCreate"
UNITS = "units"
USER = "user"
VALUE = "value"
VALUE_TYPE = "valueType"
VIEW_FILE = "viewFile"
WAIT = "Wait"
WAITING_FOR_REPLY = "waitingForReply"
WINDOW = "window"
WINDOW_PATH = "windowPath"
WINDOW_ID = "windowId"
WINDOW_TITLE = "windowTitle"
WINDOW_HEADER = "windowHeader"
WINDOW_PROPERTIES = "windowProperties"
WRITE_CONFIRMED = "writeConfirmed"
WRITE_OUTPUT_CONFIG = "writeOutputConfig"
RECIPE_LOCATION = "recipeLocation"  

# Shared error counter for multiple Write Output blocks
SHARED_ERROR_COUNT_KEY = "globalErrorCountKey"
SHARED_ERROR_COUNT_LOCATION = "globalErrorCountLocation"

# Some standard client responses
YES_RESPONSE = "Yes"
NO_RESPONSE = "No"

# The name of the second unit is really defined in the database,
# so this constant should agree with that. Likewise for type:
SECOND= "SEC"
MINUTE= "MIN"
TIME_UNIT_TYPE = "TIME"

# symbols for TimeDelayStep "units"
# nothing to do with unit conversion units
DELAY_UNIT_SECOND = "SEC";
DELAY_UNIT_MINUTE = "MIN";
DELAY_UNIT_HOUR = "HR";

# standard Ignition scopes:
CHART_SCOPE = "chartScope"
STEP_SCOPE = "stepScope"

#Recipe scopes:
LOCAL_SCOPE = "local"
PRIOR_SCOPE = "prior"
SUPERIOR_SCOPE ="superior"
PHASE_SCOPE ="phase"
OPERATION_SCOPE = "operation"
GLOBAL_SCOPE = "global"
TAG_SCOPE = "tag"

# Chart states and status 
DEACTIVATED = "deactivated";
ACTIVATED = "activated";
RESUMED = "resumed";
RUNNING = "Running"
PAUSED = "Paused"
ABORTED = "Aborted"
CANCELED = "Canceled"
STOPPED = "Stopped"

# Message statuses
MSG_STATUS_INFO = "Info"
MSG_STATUS_WARNING = "Warning"
MSG_STATUS_ERROR = "Error"

# Default window paths
REVIEW_DATA_WINDOW = "reviewDataWindow"

#Step scope internal status
_STATUS = "_status"
ACTIVATE = "Activate"
PAUSE = "Pause"
RESUME = "Resume"
CANCEL = "Cancel"

#Step States
DEACTIVATED = "deactivated"
ACTIVATED = "activated"
PAUSED = "paused"
CANCELLED = "cancelled"

#colors
WHITE = "white"
YELLOW = "yellow"
ORANGE = "orange"
RED = "red"
GREEN = "0,128,0"

# Write Output / PV Monitoring / Download Monitor STEP column status
STEP_PENDING = "pending"
STEP_APPROACHING = "approaching"
STEP_DOWNLOADING = "downloading"
STEP_SUCCESS = "success"
STEP_FAILURE = "failure"

# Write Output / PV Monitoring / Download Monitor PV column status
PV_MONITORING = "monitoring"
PV_WARNING = "warning"
PV_OK_NOT_PERSISTENT = "ok not persistent"
PV_OK = "ok"
PV_BAD_NOT_CONSISTENT = "bad not consistent"
PV_ERROR = "error"
PV_NOT_MONITORED = "not monitored"

# Write Output / PV Monitoring / Download Monitor SETPOINT column status
SETPOINT_OK = "ok"
SETPOINT_PROBLEM = "problem"

# the default sleep increment for loops, in seconds
SLEEP_INCREMENT = 5

# tag value types -- TODO: remove--duplicate with Java
DATE_TIME = "date/time"
STRING = "string"
INT = "int"
FLOAT = "float"
BOOLEAN = "boolean"
# DATE = "date"

# SFC data step types
PHASE_STEP = "Phase"
OPERATION_STEP = "Operation"
UNIT_PROCEDURE_STEP = "Global"

# Timer commands
PAUSE_TIMER = "pause"
STOP_TIMER = "stop"
START_TIMER = "start"
RESUME_TIMER = "resume"
CLEAR_TIMER = "clear"

# Timer States
TIMER_RUNNING = "running"
TIMER_STOPPED = "stopped"
TIMER_CLEARED = "cleared"
TIMER_PAUSED = "paused"

# Step Properties
TIMER_KEY = "timerKey"
TIMER_LOCATION = "timerLocation"
TIMER_SET = "timerSet"
TIMER_CLEAR = "timerClear";

